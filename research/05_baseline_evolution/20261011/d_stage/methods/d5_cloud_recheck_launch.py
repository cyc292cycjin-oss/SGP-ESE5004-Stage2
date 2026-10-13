"""在 122 上以独立进程运行 d5_local_v4_recheck.py（只读，不调用求解器；固定超时 2 h、不重启）。
原因：D-1 冻结 CSC 拉回本机的带宽约 0.17 MB/s（3.2 GB 需 5 h 以上）；本地拉取继续并行，完成后再做本机复核补充。
python d5_cloud_recheck_launch.py start | observe | fetch
"""
from pathlib import Path
import sys, json, time, io, tarfile, hashlib
W = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(W))
import d_control as dc
from c09_control import remote, PY


def start():
    assert not (W / 'D5_RECHECK_START_ATTEMPT.json').exists(), 'NO_RETRY'
    src = (W / 'methods/d5_local_v4_recheck.py').read_bytes(); buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as t:
        ti = tarfile.TarInfo('release/d5_local_v4_recheck.py'); ti.size = len(src); ti.mtime = 0; t.addfile(ti, io.BytesIO(src))
    (W / 'D5_RECHECK_RELEASE.tar.gz').write_bytes(buf.getvalue())
    d1 = json.loads((W / 'D1_LAUNCH_RECEIPT.json').read_text())['run']; d5 = json.loads((W / 'D5_LAUNCH_RECEIPT.json').read_text())['run']
    rel = json.loads((W / 'D5_RELEASE_DELIVERY.json').read_text())['remote_release']; blk = json.loads((W / 'release_d5/D5_EXPECTED.json').read_text())['block_dir']
    dc.save('D5_RECHECK_START_ATTEMPT.json', {'epoch': time.time(), 'no_retry': True, 'solver_calls': 0, 'script_sha256': hashlib.sha256(src).hexdigest()})
    up = dc._upload_release('d5_recheck2920_122_20261013', 'D5_RECHECK_RELEASE.tar.gz', 1)
    work = '/root/sgp_d_stage/recheck_' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()); out = work + '/D5_CLOUD_V4_RECHECK.json'
    code = f'''import subprocess,json,os
from pathlib import Path
w=Path({work!r});w.mkdir(parents=True,exist_ok=False);(w/'inp').mkdir()
os.symlink({d1!r},w/'inp'/'d1');os.symlink({blk!r},w/'inp'/'d2_block')
log=open(w/'recheck.log','xb')
p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30s','7200s',{PY!r},'-B',{up['root'] + '/release/d5_local_v4_recheck.py'!r},{rel!r},{d5 + '/cloud_run' if False else d5!r},str(w/'inp'),{out!r}],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({{'pid':p.pid,'work':str(w),'out':{out!r},'timeout_seconds':7200}}))'''
    rec = remote(code, 120); rec['upload'] = up; dc.save('D5_RECHECK_LAUNCH_RECEIPT.json', rec); print(json.dumps(rec, indent=1))


def observe():
    a = json.loads((W / 'D5_RECHECK_LAUNCH_RECEIPT.json').read_text())
    v = remote(f'''import json
from pathlib import Path
w=Path({a['work']!r});o=Path({a['out']!r})
print(json.dumps({{'done':o.exists(),'log':(w/'recheck.log').read_text(errors='replace').splitlines()[-12:]}}))''', 60)
    print(json.dumps(v, indent=1)); return v


def fetch():
    a = json.loads((W / 'D5_RECHECK_LAUNCH_RECEIPT.json').read_text())
    v = remote(f'''import json;print(json.dumps({{'t':open({a['out']!r}).read()}}))''', 60)
    (W / 'evidence/D5_CLOUD_V4_RECHECK.json').write_bytes(v['t'].encode()); print(v['t'][:3000])


if __name__ == '__main__':
    {'start': start, 'observe': observe, 'fetch': fetch}[sys.argv[1]]()
