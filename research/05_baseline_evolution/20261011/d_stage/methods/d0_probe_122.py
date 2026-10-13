"""D-0 read-only probe of instance 122 (no writes, no solver, no build). Uses the fixed C09 SSH settings."""
from pathlib import Path
import sys, json, time
C9 = Path(__file__).resolve().parents[2] / 'c09_exact_decomposition_20261013'
sys.path.insert(0, str(C9))
from c09_control import remote

W = Path(__file__).resolve().parents[1]
code = r'''
import json,os,shutil,socket,hashlib,subprocess,time
from pathlib import Path
import psutil
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
S=Path('/root/autodl-tmp/SGP');out={'hostname':socket.gethostname(),'epoch':time.time()}
du=shutil.disk_usage('/root/autodl-tmp');out['disk']={'total':du.total,'used':du.used,'free':du.free}
cg=Path('/sys/fs/cgroup/memory');out['cgroup']={k:int((cg/k).read_text()) for k in ('memory.limit_in_bytes','memory.usage_in_bytes','memory.max_usage_in_bytes')}
out['host_available']=psutil.virtual_memory().available;out['cpu_affinity']=len(os.sched_getaffinity(0))
q=int(Path('/sys/fs/cgroup/cpu/cpu.cfs_quota_us').read_text());p=int(Path('/sys/fs/cgroup/cpu/cpu.cfs_period_us').read_text());out['cpu_quota']=q/p if q>0 else None
procs=[]
for pr in psutil.process_iter(['pid','name','cmdline','memory_info','create_time']):
    cl=' '.join(pr.info['cmdline'] or [])
    if any(k in cl for k in ('python','gurobi','sshd: root@notty')) and pr.info['pid']!=os.getpid():
        procs.append({'pid':pr.info['pid'],'cmd':cl[:200],'rss':pr.info['memory_info'].rss if pr.info['memory_info'] else None,'start':pr.info['create_time']})
out['processes']=procs
base=S/'worktrees/gate6_capture_20261008T200734Z/results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc'
out['base_network']={'path':str(base),'exists':base.exists(),'bytes':base.stat().st_size if base.exists() else None,'sha256':sha(base) if base.exists() else None}
out['runs']=sorted(x.name for x in (S/'runs').iterdir())
out['incoming']=sorted(x.name for x in (S/'incoming').iterdir())
r=subprocess.run(['du','-sb']+[str(x) for x in sorted(S.iterdir())],capture_output=True,text=True,timeout=240)
out['du']=[l.split('\t') for l in r.stdout.splitlines()]
hits=[]
for pat in ('GATE6_3H_ROUNDING_AUDIT.json','EFFECTIVE_PERTURBATION_LEDGER.csv','V4_APPROVED.json','EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json'):
    for f in (S/'incoming').glob('*/**/'+pat):hits.append({'path':str(f),'sha256':sha(f)})
out['payload_copies']=hits
print(json.dumps(out))
'''
value = remote(code, 300)
(W / 'evidence').mkdir(exist_ok=True)
(W / 'evidence' / 'D0_122_PROBE.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
v = dict(value); v['du'] = value['du']; v['payload_copies'] = len(value['payload_copies'])
print(json.dumps(v, indent=1)[:6000])
