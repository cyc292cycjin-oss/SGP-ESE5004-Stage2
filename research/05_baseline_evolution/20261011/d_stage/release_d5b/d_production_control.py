"""Linux process protection (D-stage copy of the C07/C09 module; only phase_deadline reads phase budgets from the authorization). No solver imports and no network operations.

The supervisor monitors resources. A separately detached guard owns all signals,
absolute phase deadlines and supervisor-loss handling. Neither starts a retry.
"""
from pathlib import Path
import os,sys,json,time,signal,subprocess,hashlib,shutil,math
import psutil
HERE=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()

def put(p,value):
 p=Path(p);tmp=p.with_name(p.name+'.'+str(os.getpid())+'.tmp')
 with open(tmp,'x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,allow_nan=False,indent=2);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
 if sys.platform!='win32':
  fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)

def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def ident(pid,run):
 p=psutil.Process(pid)
 return dict(pid=pid,create_time=p.create_time(),pgid=os.getpgid(pid),sid=os.getsid(pid),command_sha256=hashlib.sha256(json.dumps(p.cmdline()).encode()).hexdigest(),run_id=run)
def alive(i):
 try:return psutil.Process(i['pid']).status()!=psutil.STATUS_ZOMBIE and ident(i['pid'],i['run_id'])==i
 except (psutil.NoSuchProcess,ProcessLookupError):return False
def event(root,kind,**details):
 with open(Path(root)/'GUARD_EVENTS.jsonl','a',encoding='utf8') as f:f.write(json.dumps(dict(epoch=time.time(),event=kind,**details))+'\n');f.flush();os.fsync(f.fileno())
def request(root,reason):
 p=Path(root)/'STOP_REQUEST.json'
 try:
  with p.open('x') as f:json.dump(dict(reason=reason,epoch=time.time()),f);f.flush();os.fsync(f.fileno())
 except FileExistsError:pass

def resources(pid,root,limits,require_cgroup=True):
 from c02_common import resources as current
 r=current(root);p=psutil.Process(pid);rss=cpu=0
 for q in [p,*p.children(recursive=True)]:
  try:rss+=q.memory_info().rss;cpu+=sum(q.cpu_times()[:2])
  except psutil.NoSuchProcess:pass
 reason='RSS' if rss>=limits['rss_bytes'] else 'DISK' if r['disk_free']<limits['disk_free_bytes'] else 'CGROUP' if r['memory_headroom']<limits['cgroup_headroom_bytes'] else None
 return dict(epoch=time.time(),rss_bytes=rss,cpu_seconds=cpu,disk_free_bytes=r['disk_free'],cgroup_headroom_bytes=r['memory_headroom'],cgroup=r['ancestors'],effective_memory_limit=r['effective_memory_limit'],reason=reason)


def group(i):
 found=[]
 for p in psutil.process_iter(['pid','status']):
  try:
   if p.info['status']!=psutil.STATUS_ZOMBIE and os.getpgid(p.pid)==i['pgid'] and os.getsid(p.pid)==i['sid']:found.append(ident(p.pid,i['run_id']))
  except (psutil.NoSuchProcess,ProcessLookupError,PermissionError):pass
 return found

def signal_owned(expected,seen,sig,root):
 """Individual revalidated PIDs only; no killall/pkill or unverified group signal."""
 live={r['pid']:r for r in group(expected)}
 live.update({pid:r for pid,r in seen.items() if alive(r)})
 live=list(live.values())
 for item in live:
  if seen.get(item['pid'])!=item:raise RuntimeError('unverified residual identity; refuse signal')
 for item in live:
  if alive(item):os.kill(item['pid'],sig);event(root,'SIGNAL',signal=int(sig),identity=item)

def limits_valid(a):
 keys=['load_absolute_deadline_epoch','native_absolute_deadline_epoch','raw_absolute_deadline_epoch','post_absolute_deadline_epoch','absolute_deadline_epoch']
 values=[a[k] for k in keys]
 if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in values) or not time.time()<values[0]<values[1]<values[2]<values[3]<values[4]:raise ValueError('fixed absolute phase deadlines required')
 for k in ('native_exit_grace_seconds','term_grace_seconds','raw_save_seconds','supervisor_lease_seconds'):
  if not math.isfinite(a[k]) or a[k]<=0:raise ValueError('finite preservation budget required')
 if values[2]-values[1]<a['native_exit_grace_seconds']+a['term_grace_seconds']+a['raw_save_seconds']:raise ValueError('native exit/raw reservation overlaps')
 for v in a['resource_limits'].values():
  if not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0:raise ValueError('invalid resource limit')
 if a['soft_memory_limit_decimal_gb']*1e9>=a['resource_limits']['rss_bytes']:raise ValueError('native memory limit must leave external guard headroom')

def phase_deadline(stage,a):
 phase=stage.get('phase','BUILD');entered=stage['entered_epoch']
 if phase=='BUILD':return min(entered+a['build_phase_seconds'],a['build_absolute_deadline_epoch'])
 if phase=='BRIDGE':return min(entered+a['bridge_phase_seconds'],a['load_absolute_deadline_epoch'])
 if phase=='NATIVE':return min(entered+a['maximum_native_seconds'],a['native_absolute_deadline_epoch'])
 if phase=='RAW_SAVE':return min(entered+a['raw_save_seconds'],a['raw_absolute_deadline_epoch'])
 if phase=='POSTPROCESS':return min(entered+a['post_phase_seconds'],a['post_absolute_deadline_epoch'])
 if phase in ('DONE','FAILED'):return a['post_absolute_deadline_epoch']
 raise ValueError('unknown protected phase '+phase)


def current_stage(root,started):
 root=Path(root)
 stage=read(root/'PHASE.json') if (root/'PHASE.json').exists() else {'phase':'LOADING','entered_epoch':started}
 # Native return receipt is persisted BEFORE raw-save phase publication.
 if stage['phase']=='NATIVE' and (root/'NATIVE_CALL_EXIT.json').exists():
  stage={'phase':'RAW_SAVE','entered_epoch':read(root/'NATIVE_CALL_EXIT.json')['returned_utc_epoch']}
 return stage

def launch_seal(root,a):
 remaining=a['absolute_deadline_epoch']-time.time()
 if remaining<=a['term_grace_seconds']:
  put(Path(root)/'LOCAL_SYNC_PENDING.json',{'reason':'NO_CLOSEOUT_BUDGET','source_preserved':True});return None
 raise RuntimeError('D stage seals through its own launcher; production_backup is not shipped')
 with open(Path(root)/'closeout.stdout.log','xb') as log:
  return subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)

def stop_blocks_stage(root,phase):
 p=Path(root)/'STOP_REQUEST.json'
 if not p.exists():return False
 # Preserve the old stop receipt. Only a completed native-only timeout may
 # transition to the separately bounded postprocess budget. Resources, loss of
 # supervision and every other stop still block immediately.
 if phase=='POSTPROCESS' and read(p).get('reason')=='PHASE_DEADLINE_NATIVE':
  durable=Path(root)/'raw/RAW_DURABLE.json'
  if (Path(root)/'NATIVE_CALL_EXIT.json').exists() and durable.exists() and read(durable).get('complete') is True:return False
 return True

def guardian(config):
 cfg=read(config);root=Path(cfg['root']);a=cfg['authorization'];expected=cfg['worker'];parent=cfg['supervisor'];seen={expected['pid']:expected}
 started=time.time();stop_at=None;term_at=None;fail=None;lastphase=None
 try:
  if not alive(expected):raise ValueError('worker identity before release')
  put(root/'GUARD_READY.json',ident(os.getpid(),a['run_id']))
  while True:
   live=group(expected)
   # New descendants may only be adopted while the verified leader exists.
   if alive(expected):
    descendants={p.pid for p in psutil.Process(expected['pid']).children(recursive=True)}|{expected['pid']}
    for pid in descendants:
     try:seen[pid]=ident(pid,a['run_id'])
     except (psutil.NoSuchProcess,ProcessLookupError):pass
    for item in live:
     if item['pid'] in descendants:seen[item['pid']]=item
   live=list({**{r['pid']:r for r in live},**{pid:r for pid,r in seen.items() if alive(r)}}.values())
   if not live:break
   now=time.time();stage=current_stage(root,started)
   if stage['phase']!=lastphase:event(root,'PHASE_OBSERVED',phase=stage['phase']);lastphase=stage['phase']
   put(root/'GUARD_HEARTBEAT.json',{'epoch':now})
   heartbeat=read(root/'SUPERVISOR_HEARTBEAT.json') if (root/'SUPERVISOR_HEARTBEAT.json').exists() else {'epoch':started}
   supervisor_lost=not alive(parent) or now-heartbeat['epoch']>a['supervisor_lease_seconds']
   resource_reason=None
   if alive(expected):
    try:resource_reason=resources(expected['pid'],root,a['resource_limits'],cfg['require_cgroup'])['reason']
    except Exception:resource_reason='RESOURCE_MONITOR_UNAVAILABLE'
   if supervisor_lost:request(root,'SUPERVISOR_LOST')
   if resource_reason:request(root,resource_reason)
   deadline=phase_deadline(stage,a)
   if now>=deadline:request(root,'PHASE_DEADLINE_'+stage['phase'])
   requested=stop_blocks_stage(root,stage['phase'])
   if not requested:stop_at=None
   if requested and stop_at is None:stop_at=now;event(root,'STOP_REQUEST_OBSERVED',phase=stage['phase'])
   # Raw preservation gets its fixed budget even if a previous native stop exists.
   # Emergency resources and absolute hard deadline always take precedence.
   emergency=resource_reason in ('RSS','DISK','CGROUP','RESOURCE_MONITOR_UNAVAILABLE')
   if not alive(expected):force=True;reason='LEADER_EXITED_RESIDUALS'
   elif now>=a['absolute_deadline_epoch']:force=True;reason='HARD_DEADLINE'
   elif emergency:force=stop_at is not None and now-stop_at>=a['term_grace_seconds'];reason=resource_reason
   elif stage['phase']=='RAW_SAVE':force=now>=deadline;reason='RAW_BUDGET_EXHAUSTED'
   elif stage['phase']=='NATIVE':force=requested and now-stop_at>=a['native_exit_grace_seconds'];reason='NATIVE_EXIT_GRACE_EXHAUSTED'
   else:force=requested and (now>=deadline or supervisor_lost or now-stop_at>=a['term_grace_seconds']);reason='STOP_OUTSIDE_NATIVE'
   if force:
    newest=current_stage(root,started)
    if not emergency and newest['phase']=='RAW_SAVE' and time.time()<phase_deadline(newest,a) and now<a['absolute_deadline_epoch']:
     time.sleep(cfg.get('sample_seconds',.25));continue
    if term_at is None:
     event(root,'TERMINATE_REASON',reason=reason,raw_complete=(root/'raw/RAW_DURABLE.json').exists());signal_owned(expected,seen,signal.SIGTERM,root);term_at=now
    elif now-term_at>=a['term_grace_seconds'] or now>=a['absolute_deadline_epoch']:
     signal_owned(expected,seen,signal.SIGKILL,root)
   time.sleep(cfg.get('sample_seconds',.25))
 except Exception as e:
  fail=type(e).__name__;request(root,'GUARD_EXCEPTION')
  # Only verified owned identities; a mismatch stays a manual attention event.
  try:signal_owned(expected,seen,signal.SIGTERM,root);time.sleep(min(a['term_grace_seconds'],2));signal_owned(expected,seen,signal.SIGKILL,root)
  except Exception:event(root,'IDENTITY_REFUSAL_MANUAL_ATTENTION')
 finally:
  residual=list({**{r['pid']:r for r in group(expected)},**{pid:r for pid,r in seen.items() if alive(r)}}.values())
  # A stalled supervisor itself must not outlive its lease after owned work ends.
  heartbeat=read(root/'SUPERVISOR_HEARTBEAT.json') if (root/'SUPERVISOR_HEARTBEAT.json').exists() else {'epoch':started}
  if alive(parent) and (time.time()>=a['absolute_deadline_epoch'] or time.time()-heartbeat['epoch']>a['supervisor_lease_seconds']):
   event(root,'STOP_STALLED_SUPERVISOR',identity=parent);os.kill(parent['pid'],signal.SIGTERM)
   until=min(time.time()+a['term_grace_seconds'],a['absolute_deadline_epoch'])
   while alive(parent) and time.time()<until:time.sleep(.05)
   if alive(parent):os.kill(parent['pid'],signal.SIGKILL)
  put(root/'GUARD_EXIT.json',{'error':fail,'residual_live_pids':[r['pid'] for r in residual],'seen_identities':list(seen.values()),'epoch':time.time(),'native_state':'USE_NATIVE_CALL_EXIT_AND_RAW_RECEIPTS_ONLY','retry':False})
  if cfg.get('launch_closeout') and not residual and not alive(parent):
   try:launch_seal(root,a) # fallback still respects the same total deadline
   except Exception:pass # immutable run bytes remain, no retry or re-solve

def supervise(command,root,a,require_cgroup=True,launch_closeout=False):
 """Called by gated production launcher; also tested with dedicated fake processes."""
 root=Path(root);root.mkdir(exist_ok=False,parents=True)
 # Fail before worker launch if resource monitoring cannot function.
 resources(os.getpid(),root,a['resource_limits'],require_cgroup)
 put(root/'AUTHORIZATION.json',a);put(root/'SUPERVISOR_IDENTITY.json',ident(os.getpid(),a['run_id']))
 put(root/'LOCAL_SYNC_PENDING.json',{'status':'LOCAL_SYNC_PENDING','reason':'RUN_NOT_CLOSED','cloud_originals_preserved':True,'retry_solve':False})
 put(root/'SUPERVISOR_HEARTBEAT.json',{'epoch':time.time()})
 with open(root/'worker.stdout.log','xb') as log:
  worker=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:
  for _ in range(500):
   if (root/'WORKER_READY.json').exists() or worker.poll() is not None:break
   time.sleep(.01)
  expected=ident(worker.pid,a['run_id']);assert expected['pid']==expected['pgid']==expected['sid']
  cfg={'root':str(root),'authorization':a,'worker':expected,'supervisor':ident(os.getpid(),a['run_id']),'require_cgroup':require_cgroup,'launch_closeout':launch_closeout}
  put(root/'GUARD_CONFIG.json',cfg)
  with open(root/'guard.stdout.log','xb') as log:guard=subprocess.Popen([sys.executable,str(HERE/'d_production_control.py'),'guard',str(root/'GUARD_CONFIG.json')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  for _ in range(500):
   if (root/'GUARD_READY.json').exists() or guard.poll() is not None:break
   time.sleep(.01)
  if not (root/'GUARD_READY.json').exists():raise RuntimeError('independent guard failed before release')
  # Release only after a separate live guard owns this exact process identity.
  put(root/'PROCESS_IDENTITY.json',expected)
  while worker.poll() is None:
   if guard.poll() is not None:raise RuntimeError('independent guard lost')
   heartbeat=read(root/'GUARD_HEARTBEAT.json') if (root/'GUARD_HEARTBEAT.json').exists() else {'epoch':time.time()}
   if time.time()-heartbeat['epoch']>a['supervisor_lease_seconds']:raise RuntimeError('independent guard stalled')
   put(root/'SUPERVISOR_HEARTBEAT.json',{'epoch':time.time()})
   r=resources(worker.pid,root,a['resource_limits'],require_cgroup)
   with open(root/'RESOURCE.jsonl','a') as f:f.write(json.dumps(r)+'\n')
   if r['reason']:request(root,r['reason'])
   time.sleep(.25)
  guard.wait(timeout=max(10,a['term_grace_seconds']+5))
  if read(root/'GUARD_EXIT.json')['residual_live_pids']:raise RuntimeError('residuals block closeout')
  put(root/'SUPERVISOR_EXIT.json',{'epoch':time.time(),'worker_exit_code':worker.returncode,'worker_and_guard_exited':True,'residual_live_pids':[],'retry':False})
  if launch_closeout:
   process=launch_seal(root,a)
   if process:process.wait() # no writes to source after seal starts
 except Exception as e:
  request(root,'SUPERVISOR_EXCEPTION');put(root/'SUPERVISOR_ERROR.json',{'error':type(e).__name__,'epoch':time.time(),'retry':False})
  # Independent guard handles supervisor loss; if guard itself failed use identities.
  if 'guard' not in locals() or guard.poll() is not None or type(e).__name__=='RuntimeError' and 'stalled' in str(e):
   if 'expected' in locals() and alive(expected):
    seen={r['pid']:r for r in group(expected)}
    signal_owned(expected,seen,signal.SIGTERM,root);time.sleep(a['term_grace_seconds']);signal_owned(expected,seen,signal.SIGKILL,root)
    worker.wait(timeout=5)
  raise

if __name__=='__main__':
 if len(sys.argv)!=3 or sys.argv[1]!='guard':raise SystemExit('guard entry requires exact config')
 guardian(sys.argv[2])
