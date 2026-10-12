"""C09 Windows-side control: deploy / start / observe / fetch. Never retries a start.

Run from this folder on the Windows machine:
    python c09_control.py deploy     # upload + SHA verify + 122 admission, 0 solver calls
    python c09_control.py start      # the ONLY optimize authorization use (one call, detached)
    python c09_control.py observe    # read-only snapshot, repeat as needed
    python c09_control.py fetch      # after cloud seal: stream new-results archive, SHA verify
SSH settings are identical to the C07 control (same key path and pinned known_hosts);
this script never reads or prints the key.
"""
from pathlib import Path
import sys, json, time, subprocess, shlex, hashlib, os

W = Path(__file__).resolve().parent
SSH = [r'C:\Windows\System32\OpenSSH\ssh.exe', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'UserKnownHostsFile=D:/ResearchWorkspaces/ASEAN/work/c02_daily_build_20261012/122_known_hosts',
       '-o', 'HostKeyAlgorithms=ssh-ed25519', '-o', 'KexAlgorithms=curve25519-sha256',
       '-i', 'C:/Users/20122/.ssh/gate5_autodl_20261007', '-p', '40516', 'root@connect.westb.seetacloud.com']
PY = '/root/autodl-tmp/SGP/env/gate5/bin/python3.11'
D = json.loads((W / 'RELEASE_DELIVERY.json').read_text())


def save(name, obj):
    p = W / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def remote(code, timeout=60, data=None):
    r = subprocess.run(SSH + [PY + ' -B -c ' + shlex.quote(code)], input=data, capture_output=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError('REMOTE_FAILED ' + r.stderr.decode(errors='replace')[-1500:])
    return json.loads(r.stdout)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def deploy():
    assert not (W / 'DEPLOYMENT_RECEIPT.json').exists(), 'ALREADY_DEPLOYED'
    blob = (W / 'C09_RELEASE.tar.gz').read_bytes()
    assert len(blob) == D['archive_bytes'] and hashlib.sha256(blob).hexdigest() == D['archive_sha256'], 'LOCAL_ARCHIVE_SHA'
    code = f'''from pathlib import Path,PurePosixPath
import sys,os,hashlib,json,tarfile,io,socket
assert socket.gethostname()=='autodl-container-21104cb00b-43be1fed'
root=Path({D['remote_control']!r});assert root.parent==Path('/root/autodl-tmp/SGP/incoming') and not root.exists()
assert not list(Path('/root/autodl-tmp/SGP/runs').glob('c09*'))
assert not Path('/root/autodl-tmp/SGP/c09_claims').exists()
b=sys.stdin.buffer.read({D['archive_bytes']}+1);assert len(b)=={D['archive_bytes']} and hashlib.sha256(b).hexdigest()=={D['archive_sha256']!r}
root.mkdir()
with (root/'C09_RELEASE.tar.gz').open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
 members=t.getmembers();assert len(members)=={D['payload_files']} and len(set(m.name for m in members))==len(members)
 for m in members:
  p=PurePosixPath(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts and p.parts[0]=='release'
 for m in members:
  p=root/m.name;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(t.extractfile(m).read());f.flush();os.fsync(f.fileno())
sys.path.insert(0,str(root/'release'))
from c09_checks import verify_release,admission
verify_release({D['release_manifest_sha256']!r});admit=admission()
from c02_common import write
rec={{'status':'C09_RELEASE_SHA_VERIFIED','remote_release':str(root/'release'),'manifest_sha256':{D['release_manifest_sha256']!r},'file_count':len(members),'admission':admit,'native_calls':0}}
write(root/'DEPLOYMENT_RECEIPT.json',rec);print(json.dumps(rec))'''
    rec = remote(code, 180, blob)
    save('DEPLOYMENT_RECEIPT.json', rec)
    print(json.dumps({'status': rec['status'], 'remote_release': rec['remote_release'], 'native_calls': 0}, indent=2))


def start():
    assert (W / 'DEPLOYMENT_RECEIPT.json').exists(), 'DEPLOY_FIRST'
    assert not (W / 'START_ATTEMPT.json').exists(), 'START_ALREADY_ATTEMPTED_NO_RETRY'
    save('START_ATTEMPT.json', {'epoch': time.time(), 'manifest_sha256': D['release_manifest_sha256'], 'no_retry': True})
    args = [PY, '-B', D['remote_release'] + '/c09_launch.py', 'start', D['release_manifest_sha256']]
    r = subprocess.run(SSH + [shlex.join(args)], capture_output=True, timeout=120)
    (W / 'START_STDOUT.txt').write_bytes(r.stdout); (W / 'START_STDERR.txt').write_bytes(r.stderr)
    assert r.returncode == 0, 'START_FAILED_OR_AMBIGUOUS_NO_RETRY ' + r.stderr.decode(errors='replace')[-1200:]
    save('LAUNCH_RECEIPT.json', json.loads(r.stdout)); print(r.stdout.decode())


def observe():
    a = json.loads((W / 'LAUNCH_RECEIPT.json').read_text()); run = a['run']
    code = f'''from pathlib import Path
import sys,json,time
sys.path.insert(0,{D['remote_release']!r})
from c02_common import read
from production_control import alive
run=Path({run!r});control=Path({D['remote_control']!r});out={{'run_id':run.name,'observed_epoch':time.time(),'receipts':{{}},'live':{{}}}}
names=['PHASE.json','WLS_ENVIRONMENT.json','NATIVE_VERSION.json','C09_BLOCK_VERIFICATION.json','C09_MAIN_PROBLEM_IDENTITY.json','NATIVE_TRANSFER.json','C09_PARAMETER_DIFF.json','C09_NATIVE_OPTIMIZE_ENTERED.json','NATIVE_CALL_EXIT.json','raw/NATIVE_RETURN.json','raw/RAW_DURABLE.json','raw/vectors/RAW_RECEIPT.json','C09_MERGE.json','postprocess/POSTPROCESS_RECEIPT.json','postprocess/KKT.json','POSTPROCESS_NOT_RUN.json','NATIVE_WORKER_FAILURE.json','WORKER_FAILURE.json','WORKER_EXIT.json','SUPERVISOR_EXIT.json','GUARD_EXIT.json','STOP_REQUEST.json','CLOUD_SEAL_COMPLETE.json']
for n in names:
 p=run/n
 if p.exists():
  z=read(p)
  if n=='C09_PARAMETER_DIFF.json':z={{k:z[k] for k in ['status','count','differences','unauthorized']}}
  if n=='C09_BLOCK_VERIFICATION.json':z.pop('block_receipt',None)
  out['receipts'][n]=z
for n in ['PROCESS_IDENTITY.json','SUPERVISOR_IDENTITY.json','GUARD_READY.json']:
 p=run/n
 if p.exists():
  z=read(p);out['live'][n]={{'identity':z,'live':alive(z)}}
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
    value = remote(code, 60)
    snap = W / 'monitor_snapshots'; snap.mkdir(exist_ok=True)
    (snap / (time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    r = value['receipts']
    print(json.dumps({'run_id': value['run_id'], 'phase': r.get('PHASE.json'), 'log_tail': (value.get('log') or {}).get('tail'),
                      'native': r.get('raw/NATIVE_RETURN.json'), 'post': (r.get('postprocess/POSTPROCESS_RECEIPT.json') or {}).get('gates'),
                      'errors': {k: x for k, x in r.items() if 'FAILURE' in k or 'STOP_' in k}, 'archive': value.get('_ARCHIVE_RECEIPT.json')},
                     indent=2, ensure_ascii=False))


def fetch():
    a = json.loads((W / 'LAUNCH_RECEIPT.json').read_text()); rid = a['run_id']
    rel = D['remote_release'].rsplit('/', 1)[0]
    rec = remote(f'''import json;print(open({rel + '/' + rid + '_ARCHIVE_RECEIPT.json'!r}).read())''', 60)
    out = W / (rid + '_NEW_RESULTS.tar.gz'); part = out.with_name(out.name + '.partial')
    assert not out.exists(), 'ALREADY_FETCHED'
    save('FETCH_WINDOW.json', {'start_epoch': time.time(), 'archive': rec['archive'], 'bytes': rec['bytes'], 'sha256': rec['sha256'], 'max_seconds': 3600})
    with open(part, 'wb') as f:
        p = subprocess.Popen(SSH + ['cat ' + shlex.quote(rec['archive'])], stdout=f, stderr=subprocess.PIPE)
        p.wait(timeout=3600)
    assert p.returncode == 0, 'FETCH_FAILED'
    assert part.stat().st_size == rec['bytes'] and sha(part) == rec['sha256'], 'FETCH_SHA_MISMATCH_PARTIAL_KEPT'
    os.replace(part, out)
    save('FETCH_RECEIPT.json', {'status': 'LOCAL_ARCHIVE_SHA_VERIFIED', 'path': str(out), 'bytes': rec['bytes'], 'sha256': rec['sha256'], 'end_epoch': time.time()})
    print('LOCAL_ARCHIVE_SHA_VERIFIED', out)


if __name__ == '__main__':
    {'deploy': deploy, 'start': start, 'observe': observe, 'fetch': fetch}[sys.argv[1]]()
