"""D-6 云端只读严格下界作业（不调用求解器、不建模；固定超时、不重启）。

python d6_launch.py start     # 上传 release_d6（1 个文件）并以 timeout 4 h 分离启动
python d6_launch.py observe   # 只读快照
python d6_launch.py fetch     # 拉回 JSON 结果（界数组 npz 留在云端）
"""
from pathlib import Path
import sys, json, time, io, tarfile, hashlib
W = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(W))
import d_control as dc
from c09_control import remote, PY


def start():
    assert not (W / 'D6_START_ATTEMPT.json').exists(), 'D6_START_ALREADY_ATTEMPTED_NO_RETRY'
    src = (W / 'release_d6/d6_bound.py').read_bytes(); buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as t:
        ti = tarfile.TarInfo('release/d6_bound.py'); ti.size = len(src); ti.mtime = 0; t.addfile(ti, io.BytesIO(src))
    (W / 'D6_RELEASE.tar.gz').write_bytes(buf.getvalue())
    d1 = json.loads((W / 'D1_LAUNCH_RECEIPT.json').read_text())['run']; d5 = json.loads((W / 'D5_LAUNCH_RECEIPT.json').read_text())['run']
    blk = json.loads((W / 'release_d5/D5_EXPECTED.json').read_text())['block_dir']
    dc.save('D6_START_ATTEMPT.json', {'epoch': time.time(), 'no_retry': True, 'solver_calls': 0, 'd6_bound_sha256': hashlib.sha256(src).hexdigest()})
    up = dc._upload_release('d6_bound2920_122_20261013', 'D6_RELEASE.tar.gz', 1)
    out = '/root/autodl-tmp/SGP/runs/d6_bound2920_' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    code = f'''import subprocess,json
from pathlib import Path
assert not Path({out!r}).exists()
log=open({up['root'] + '/d6_job.log'!r},'xb')
p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30s','14400s',{PY!r},'-B',{up['root'] + '/release/d6_bound.py'!r},{d1!r},{d5!r},{blk!r},{out!r},'0.001','1'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({{'pid':p.pid,'out':{out!r},'release':{up['root']!r},'timeout_seconds':14400}}))'''
    rec = remote(code, 120); rec['upload'] = up; dc.save('D6_LAUNCH_RECEIPT.json', rec); print(json.dumps(rec, indent=1))


def observe():
    a = json.loads((W / 'D6_LAUNCH_RECEIPT.json').read_text())
    v = remote(f'''import json,os
from pathlib import Path
o=Path({a['out']!r});r={{}}
for n in ['D6_STATUS.json','D6_STORAGE_AGGREGATION.json','D6_BOUND_SUMMARY.json']:
 p=o/n
 if p.exists():r[n]=json.loads(p.read_text())
import psutil
alive=any('d6_bound.py' in ' '.join(q.info['cmdline'] or []) for q in psutil.process_iter(['cmdline']))
lg=Path({a['release'] + '/d6_job.log'!r});print(json.dumps({{'receipts':r,'alive':alive,'log_tail':lg.read_text(errors='replace').splitlines()[-8:] if lg.exists() else []}}))''', 60)
    print(json.dumps(v, indent=1)[:4000]); return v


def fetch():
    a = json.loads((W / 'D6_LAUNCH_RECEIPT.json').read_text())
    v = remote(f'''import json;from pathlib import Path
o=Path({a['out']!r});print(json.dumps({{p.name:p.read_text() for p in o.glob('D6_*.json')}}))''', 120)
    for k, txt in v.items(): (W / 'evidence' / k).write_bytes(txt.encode())
    print(sorted(v))


if __name__ == '__main__':
    {'start': start, 'observe': observe, 'fetch': fetch}[sys.argv[1]]()
