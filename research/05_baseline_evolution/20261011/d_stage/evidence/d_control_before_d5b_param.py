"""D-stage Windows-side control. SSH settings are imported unchanged from the C09 control (fixed known_hosts,
key referenced by path, never read or printed). Never retries a start.

    python d_control.py d1_deploy     # upload D-1 release + SHA verify + admission; 0 builds, 0 solver calls
    python d_control.py d1_start      # the single 2920 build (build-only, detached); max 1 build, 0 optimize
    python d_control.py d1_observe    # read-only snapshot of the D-1 run
    python d_control.py d1_fetch      # light receipts archive only (arrays stay on the cloud)
"""
from pathlib import Path
import sys, json, time, subprocess, shlex, hashlib, os
W = Path(__file__).resolve().parent
sys.path.insert(0, str(W.parent / 'c09_exact_decomposition_20261013'))
from c09_control import SSH, PY, remote, sha

INCOMING = '/root/autodl-tmp/SGP/incoming'


def save(name, obj):
    (W / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def load(name): return json.loads((W / name).read_text(encoding='utf-8'))


def d1_deploy():
    assert not (W / 'D1_DEPLOYMENT_RECEIPT.json').exists(), 'ALREADY_DEPLOYED'
    d = load('D1_RELEASE_DELIVERY.json'); blob = (W / 'D1_RELEASE.tar.gz').read_bytes()
    assert len(blob) == d['archive_bytes'] and hashlib.sha256(blob).hexdigest() == d['archive_sha256'], 'LOCAL_ARCHIVE_SHA'
    code = f'''from pathlib import Path,PurePosixPath
import sys,os,hashlib,json,tarfile,io,socket
assert socket.gethostname()=='autodl-container-21104cb00b-43be1fed'
root=Path({d['remote_control']!r});assert root.parent==Path({INCOMING!r}) and not root.exists()
assert not list(Path('/root/autodl-tmp/SGP/runs').glob('d1_build2920_*'))
b=sys.stdin.buffer.read({d['archive_bytes']}+1);assert len(b)=={d['archive_bytes']} and hashlib.sha256(b).hexdigest()=={d['archive_sha256']!r}
root.mkdir()
with (root/'D1_RELEASE.tar.gz').open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
 members=t.getmembers();assert len(members)=={d['payload_files']} and len(set(m.name for m in members))==len(members)
 for m in members:
  p=PurePosixPath(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts and p.parts[0]=='release'
 for m in members:
  p=root/m.name;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(t.extractfile(m).read());f.flush();os.fsync(f.fileno())
sys.path.insert(0,str(root/'release'))
from d1_launch import verify_release,admission
verify_release({d['release_manifest_sha256']!r});admit=admission()
from c02_common import write
rec={{'status':'D1_RELEASE_SHA_VERIFIED','remote_release':str(root/'release'),'manifest_sha256':{d['release_manifest_sha256']!r},'file_count':len(members),'admission':admit,'builds':0,'native_calls':0}}
write(root/'D1_DEPLOYMENT_RECEIPT.json',rec);print(json.dumps(rec))'''
    rec = remote(code, 300, blob)
    save('D1_DEPLOYMENT_RECEIPT.json', rec)
    print(json.dumps({'status': rec['status'], 'remote_release': rec['remote_release'], 'disk_free': rec['admission']['resources']['disk_free'], 'builds': 0, 'native_calls': 0}, indent=2))


def d1_start():
    assert (W / 'D1_DEPLOYMENT_RECEIPT.json').exists(), 'DEPLOY_FIRST'
    assert not (W / 'D1_START_ATTEMPT.json').exists(), 'D1_START_ALREADY_ATTEMPTED_NO_RETRY'
    d = load('D1_RELEASE_DELIVERY.json')
    save('D1_START_ATTEMPT.json', {'epoch': time.time(), 'manifest_sha256': d['release_manifest_sha256'], 'no_retry': True, 'max_builds': 1, 'max_optimize_calls': 0})
    args = [PY, '-B', d['remote_release'] + '/d1_launch.py', 'start', d['release_manifest_sha256']]
    r = subprocess.run(SSH + [shlex.join(args)], capture_output=True, timeout=300)
    (W / 'D1_START_STDOUT.txt').write_bytes(r.stdout); (W / 'D1_START_STDERR.txt').write_bytes(r.stderr)
    assert r.returncode == 0, 'D1_START_FAILED_OR_AMBIGUOUS_NO_RETRY ' + r.stderr.decode(errors='replace')[-1500:]
    save('D1_LAUNCH_RECEIPT.json', json.loads(r.stdout)); print(r.stdout.decode())


def d1_observe():
    a = load('D1_LAUNCH_RECEIPT.json'); d = load('D1_RELEASE_DELIVERY.json')
    code = f'''from pathlib import Path
import sys,json,time
sys.path.insert(0,{d['remote_release']!r})
from c02_common import read
from d_production_control import alive
run=Path({a['run']!r});control=Path({d['remote_control']!r});out={{'run_id':run.name,'observed_epoch':time.time(),'receipts':{{}},'live':{{}}}}
for n in ['PHASE.json','BUILD_STATUS.json','BUILD_RESULT.json','D1_BUILD_GATES.json','WORKER_FAILURE.json','WORKER_EXIT.json','SUPERVISOR_EXIT.json','SUPERVISOR_ERROR.json','GUARD_EXIT.json','STOP_REQUEST.json','artifacts/D1_SEMANTIC_FAILURE.json']:
 p=run/n
 if p.exists():
  z=read(p)
  if n=='D1_BUILD_GATES.json':z={{k:z[k] for k in ('status','gates','dimensions','label_coverage','scheme_A_slack_MWh')}}
  out['receipts'][n]=z
for n in ['PROCESS_IDENTITY.json','SUPERVISOR_IDENTITY.json','GUARD_READY.json']:
 p=run/n
 if p.exists():z=read(p);out['live'][n]={{'identity':z,'live':alive(z)}}
p=run/'RESOURCE.jsonl'
if p.exists():
 with p.open('rb') as f:f.seek(max(0,p.stat().st_size-8192));lines=f.read().splitlines()
 for line in reversed(lines):
  try:out['resource']={{k:v for k,v in json.loads(line).items() if k!='cgroup'}};break
  except Exception:pass
for suffix in ['_LIGHT_EVIDENCE_RECEIPT.json','_LIGHT_EVIDENCE_FAILURE.json']:
 p=control/(run.name+suffix)
 if p.exists():out[suffix]=read(p)
print(json.dumps(out))'''
    value = remote(code, 60)
    snap = W / 'monitor_snapshots'; snap.mkdir(exist_ok=True)
    (snap / ('D1_' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    r = value['receipts']
    print(json.dumps({'run_id': value['run_id'], 'phase': r.get('PHASE.json'), 'build_status': r.get('BUILD_STATUS.json'), 'build_result': r.get('BUILD_RESULT.json'),
                      'gates': (r.get('D1_BUILD_GATES.json') or {}).get('gates'), 'errors': {k: x for k, x in r.items() if 'FAILURE' in k or 'STOP_' in k or 'ERROR' in k},
                      'resource': value.get('resource'), 'light': value.get('_LIGHT_EVIDENCE_RECEIPT.json')}, indent=2, ensure_ascii=False)[:8000])


def d1_fetch():
    a = load('D1_LAUNCH_RECEIPT.json'); d = load('D1_RELEASE_DELIVERY.json'); rid = a['run_id']
    rec = remote(f'''import json;print(open({d['remote_control'] + '/' + rid + '_LIGHT_EVIDENCE_RECEIPT.json'!r}).read())''', 60)
    out = W / (rid + '_LIGHT_EVIDENCE.tar.gz'); part = out.with_name(out.name + '.partial')
    assert not out.exists(), 'ALREADY_FETCHED'
    with open(part, 'wb') as f:
        p = subprocess.Popen(SSH + ['cat ' + shlex.quote(rec['archive'])], stdout=f, stderr=subprocess.PIPE); p.wait(timeout=1800)
    assert p.returncode == 0, 'FETCH_FAILED'
    assert part.stat().st_size == rec['bytes'] and sha(part) == rec['sha256'], 'FETCH_SHA_MISMATCH_PARTIAL_KEPT'
    os.replace(part, out)
    save('D1_FETCH_RECEIPT.json', {'status': 'LOCAL_ARCHIVE_SHA_VERIFIED', 'path': str(out), 'bytes': rec['bytes'], 'sha256': rec['sha256'], 'members': rec['members'], 'end_epoch': time.time()})
    print('LOCAL_ARCHIVE_SHA_VERIFIED', out)


def _upload_release(tag, tarname, expected_files):
    """Upload a small release tar into a new incoming directory; verify size/SHA/member safety. Returns remote control dir."""
    blob = (W / tarname).read_bytes(); h = hashlib.sha256(blob).hexdigest(); root = INCOMING + '/' + tag + '_' + h[:8]
    code = f'''from pathlib import Path,PurePosixPath
import sys,os,hashlib,json,tarfile,io,socket
assert socket.gethostname()=='autodl-container-21104cb00b-43be1fed'
root=Path({root!r});assert root.parent==Path({INCOMING!r}) and not root.exists()
b=sys.stdin.buffer.read({len(blob)}+1);assert len(b)=={len(blob)} and hashlib.sha256(b).hexdigest()=={h!r}
root.mkdir()
with (root/{tarname!r}).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
 members=t.getmembers();assert len(members)=={expected_files}
 for m in members:
  p=PurePosixPath(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts and p.parts[0]=='release'
  q=root/m.name;q.parent.mkdir(parents=True,exist_ok=True)
  with q.open('xb') as f:f.write(t.extractfile(m).read());f.flush();os.fsync(f.fileno())
print(json.dumps({{'root':str(root),'sha256':{h!r},'files':len(members)}}))'''
    return remote(code, 300, blob)


def d2_start():
    """D-2 read-only block job on the D-1 CSC (no solver, no build). Detached with a fixed 3 h timeout; never restarted."""
    assert not (W / 'D2_START_ATTEMPT.json').exists(), 'D2_START_ALREADY_ATTEMPTED_NO_RETRY'
    d1 = load('D1_LAUNCH_RECEIPT.json'); assert load('D1_FETCH_RECEIPT.json')['status'] == 'LOCAL_ARCHIVE_SHA_VERIFIED'
    save('D2_START_ATTEMPT.json', {'epoch': time.time(), 'd1_run': d1['run'], 'no_retry': True, 'solver_calls': 0})
    up = _upload_release('d2_block2920_122_20261013', 'D2_RELEASE.tar.gz', 4)
    out = '/root/autodl-tmp/SGP/runs/d2_block2920_' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    code = f'''import subprocess,json,os,sys
from pathlib import Path
names={{'d1_build.py','d1_worker.py','d5_native.py','d5_worker.py','d2_job.py','c09_native.py'}}
import psutil
assert not [p.pid for p in psutil.process_iter(['cmdline']) if any(Path(s).name in names for s in (p.info['cmdline'] or []))],'ACTIVE_TASK'
assert not Path({out!r}).exists()
log=open({up['root'] + '/d2_job.log'!r},'xb')
p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30s','10800s',{PY!r},'-B',{up['root'] + '/release/d2_job.py'!r},{d1['run']!r},{out!r}],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({{'pid':p.pid,'out':{out!r},'release':{up['root']!r},'timeout_seconds':10800}}))'''
    rec = remote(code, 120); rec['upload'] = up; save('D2_LAUNCH_RECEIPT.json', rec); print(json.dumps(rec, indent=2))


def d2_observe():
    a = load('D2_LAUNCH_RECEIPT.json')
    code = f'''import json,os
from pathlib import Path
o=Path({a['out']!r});r={{}}
for n in ['D2_STATUS.json','D2_FAILURE.json','D2_CLOUD_READONLY_CHECKS.json','block/BLOCK_RECEIPT.json']:
 p=o/n
 if p.exists():r[n]=json.loads(p.read_text())
try:os.kill({a['pid']},0);alive=True
except OSError:alive=False
log=Path({a['release'] + '/d2_job.log'!r});tail=log.read_text(errors='replace').splitlines()[-15:] if log.exists() else []
print(json.dumps({{'receipts':r,'alive':alive,'log_tail':tail}}))'''
    v = remote(code, 60); snap = W / 'monitor_snapshots'; snap.mkdir(exist_ok=True)
    (snap / ('D2_' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '.json')).write_text(json.dumps(v, indent=1) + '\n')
    r = v['receipts']; c = r.get('D2_CLOUD_READONLY_CHECKS.json')
    print(json.dumps({'alive': v['alive'], 'status': r.get('D2_STATUS.json'), 'failure': r.get('D2_FAILURE.json'),
                      'result': {k: c[k] for k in ('status', 'requirements', 'main_problem')} if c else None, 'log_tail': v['log_tail'][-5:]}, indent=1)[:6000])


def d2_fetch():
    a = load('D2_LAUNCH_RECEIPT.json')
    v = remote(f'''import json;from pathlib import Path
o=Path({a['out']!r});print(json.dumps({{'checks':json.loads((o/'D2_CLOUD_READONLY_CHECKS.json').read_text()),'receipt_text':(o/'block/BLOCK_RECEIPT.json').read_text()}}))''', 120)
    (W / 'evidence').mkdir(exist_ok=True)
    save('evidence/D2_CLOUD_READONLY_CHECKS.json', v['checks']); (W / 'evidence' / 'D2_BLOCK_RECEIPT.json').write_text(v['receipt_text'])
    assert hashlib.sha256(v['receipt_text'].encode()).hexdigest() == v['checks']['expected_for_D5']['block_receipt_sha256'], 'BLOCK_RECEIPT_SHA'
    print(v['checks']['status'])


def d5_deploy():
    assert not (W / 'D5_DEPLOYMENT_RECEIPT.json').exists(), 'ALREADY_DEPLOYED'
    d = load('D5_RELEASE_DELIVERY.json'); up = _upload_release('d5_main2920_122_20261013', 'D5_RELEASE.tar.gz', d['payload_files'])
    assert up['root'] == d['remote_control'] and up['sha256'] == d['archive_sha256']
    code = f'''import sys,json
sys.path.insert(0,{d['remote_release']!r})
from d5_checks import verify_release,admission
verify_release({d['release_manifest_sha256']!r});admit=admission()
from c02_common import write
rec={{'status':'D5_RELEASE_SHA_VERIFIED','remote_release':{d['remote_release']!r},'manifest_sha256':{d['release_manifest_sha256']!r},'admission':admit,'native_calls':0}}
write(__import__('pathlib').Path({d['remote_control']!r})/'D5_DEPLOYMENT_RECEIPT.json',rec);print(json.dumps(rec))'''
    rec = remote(code, 300); save('D5_DEPLOYMENT_RECEIPT.json', rec)
    print(json.dumps({'status': rec['status'], 'run_disk_free': rec['admission']['resources_run_disk']['disk_free'], 'data_disk_free': rec['admission']['resources_data_disk']['disk_free'], 'native_calls': 0}, indent=2))


def d5_start():
    """THE ONLY D-stage optimize authorization use. Run only after the user's explicit '开始'. Never retried."""
    assert (W / 'D5_DEPLOYMENT_RECEIPT.json').exists(), 'DEPLOY_FIRST'
    assert not (W / 'D5_START_ATTEMPT.json').exists(), 'D5_START_ALREADY_ATTEMPTED_NO_RETRY'
    d = load('D5_RELEASE_DELIVERY.json')
    save('D5_START_ATTEMPT.json', {'epoch': time.time(), 'manifest_sha256': d['release_manifest_sha256'], 'no_retry': True})
    args = [PY, '-B', d['remote_release'] + '/d5_launch.py', 'start', d['release_manifest_sha256']]
    r = subprocess.run(SSH + [shlex.join(args)], capture_output=True, timeout=600)
    (W / 'D5_START_STDOUT.txt').write_bytes(r.stdout); (W / 'D5_START_STDERR.txt').write_bytes(r.stderr)
    assert r.returncode == 0, 'D5_START_FAILED_OR_AMBIGUOUS_NO_RETRY ' + r.stderr.decode(errors='replace')[-1200:]
    save('D5_LAUNCH_RECEIPT.json', json.loads(r.stdout)); print(r.stdout.decode())


def d5_observe():
    a = load('D5_LAUNCH_RECEIPT.json'); d = load('D5_RELEASE_DELIVERY.json'); run = a['run']
    code = f'''from pathlib import Path
import sys,json,time
sys.path.insert(0,{d['remote_release']!r})
from c02_common import read
from d_production_control import alive
run=Path({run!r});control=Path({d['remote_control']!r});out={{'run_id':run.name,'observed_epoch':time.time(),'receipts':{{}},'live':{{}}}}
names=['PHASE.json','WLS_ENVIRONMENT.json','NATIVE_VERSION.json','IMMUTABLE_INPUTS.json','D5_BLOCK_VERIFICATION.json','D5_MAIN_PROBLEM_IDENTITY.json','NATIVE_TRANSFER.json','D5_PARAMETER_DIFF.json','D5_NATIVE_OPTIMIZE_ENTERED.json','NATIVE_CALL_EXIT.json','raw/NATIVE_RETURN.json','raw/RAW_DURABLE.json','raw/vectors/RAW_RECEIPT.json','D5_MERGE.json','postprocess/POSTPROCESS_RECEIPT.json','postprocess/KKT.json','POSTPROCESS_NOT_RUN.json','NATIVE_WORKER_FAILURE.json','WORKER_FAILURE.json','WORKER_EXIT.json','SUPERVISOR_EXIT.json','SUPERVISOR_ERROR.json','GUARD_EXIT.json','STOP_REQUEST.json','CLOUD_SEAL_COMPLETE.json']
for n in names:
 p=run/n
 if p.exists():
  z=read(p)
  if n=='D5_PARAMETER_DIFF.json':z={{k:z[k] for k in ['status','count','differences','unauthorized']}}
  if n=='D5_BLOCK_VERIFICATION.json':z.pop('block_receipt',None)
  if n=='IMMUTABLE_INPUTS.json':z.pop('core',None)
  out['receipts'][n]=z
for n in ['PROCESS_IDENTITY.json','SUPERVISOR_IDENTITY.json','GUARD_READY.json']:
 p=run/n
 if p.exists():z=read(p);out['live'][n]={{'identity':z,'live':alive(z)}}
p=run/'gurobi.log'
if p.exists():out['log']={{'bytes':p.stat().st_size,'mtime':p.stat().st_mtime,'tail':p.read_text(errors='replace').splitlines()[-16:]}}
p=run/'RESOURCE.jsonl'
if p.exists():
 with p.open('rb') as f:f.seek(max(0,p.stat().st_size-8192));lines=f.read().splitlines()
 for line in reversed(lines):
  try:out['resource']={{k:v for k,v in json.loads(line).items() if k!='cgroup'}};break
  except Exception:pass
for suffix in ['_ARCHIVE_RECEIPT.json','_SEAL_GUARD_RECEIPT.json']:
 p=control/(run.name+suffix)
 if p.exists():
  z=read(p);z.pop('samples',None);out[suffix]=z
print(json.dumps(out))'''
    value = remote(code, 60); snap = W / 'monitor_snapshots'; snap.mkdir(exist_ok=True)
    (snap / ('D5_' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    r = value['receipts']
    print(json.dumps({'run_id': value['run_id'], 'phase': r.get('PHASE.json'), 'log_tail': (value.get('log') or {}).get('tail'),
                      'native': r.get('raw/NATIVE_RETURN.json'), 'post': (r.get('postprocess/POSTPROCESS_RECEIPT.json') or {}).get('gates'),
                      'errors': {k: x for k, x in r.items() if 'FAILURE' in k or 'STOP_' in k or 'ERROR' in k}, 'resource': value.get('resource'),
                      'archive': value.get('_ARCHIVE_RECEIPT.json')}, indent=2, ensure_ascii=False))


def d5_fetch():
    a = load('D5_LAUNCH_RECEIPT.json'); d = load('D5_RELEASE_DELIVERY.json'); rid = a['run_id']
    rec = remote(f'''import json;print(open({d['remote_control'] + '/' + rid + '_ARCHIVE_RECEIPT.json'!r}).read())''', 60)
    out = W / (rid + '_NEW_RESULTS.tar.gz'); part = out.with_name(out.name + '.partial')
    assert not out.exists(), 'ALREADY_FETCHED'
    save('D5_FETCH_WINDOW.json', {'start_epoch': time.time(), 'archive': rec['archive'], 'bytes': rec['bytes'], 'sha256': rec['sha256'], 'max_seconds': 3600})
    with open(part, 'wb') as f:
        p = subprocess.Popen(SSH + ['cat ' + shlex.quote(rec['archive'])], stdout=f, stderr=subprocess.PIPE); p.wait(timeout=3600)
    assert p.returncode == 0, 'FETCH_FAILED'
    assert part.stat().st_size == rec['bytes'] and sha(part) == rec['sha256'], 'FETCH_SHA_MISMATCH_PARTIAL_KEPT'
    os.replace(part, out)
    save('D5_FETCH_RECEIPT.json', {'status': 'LOCAL_ARCHIVE_SHA_VERIFIED', 'path': str(out), 'bytes': rec['bytes'], 'sha256': rec['sha256'], 'end_epoch': time.time()})
    print('LOCAL_ARCHIVE_SHA_VERIFIED', out)


if __name__ == '__main__':
    {'d5_start': d5_start, 'd5_observe': d5_observe, 'd5_fetch': d5_fetch, 'd1_deploy': d1_deploy, 'd1_start': d1_start, 'd1_observe': d1_observe, 'd1_fetch': d1_fetch,
     'd2_start': d2_start, 'd2_observe': d2_observe, 'd2_fetch': d2_fetch, 'd5_deploy': d5_deploy}[sys.argv[1]]()
