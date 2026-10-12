from pathlib import Path
import json,time,os,sys,hashlib
ROOT=Path('/root/autodl-tmp/SGP');run=ROOT/'runs/c02r_c03_daily122_20261012T044259Z_25e62c10'
sys.path.insert(0,str(ROOT/'incoming/c02r_c03_122_20261012_13a5b85e/release'))
from c02_common import resources
from production_control import alive
r={'run_id':run.name,'observed_epoch':time.time(),'receipts':{},'processes':{},'resources':resources(run)}
for name in ['PHASE.json','BUILD_STATUS.json','BUILD_RESULT.json','BRIDGE_RECEIPT.json','NATIVE_TRANSFER.json','EFFECTIVE_MODEL_PARAMETERS.json','C03_NATIVE_OPTIMIZE_ENTERED.json','NATIVE_CALL_EXIT.json','NATIVE_WORKER_EXIT.json','NATIVE_WORKER_FAILURE.json','WORKER_FAILURE.json','WORKER_EXIT.json','GUARD_READY.json','GUARD_HEARTBEAT.json','SUPERVISOR_HEARTBEAT.json','GUARD_EXIT.json','SUPERVISOR_EXIT.json','SUPERVISOR_ERROR.json','STOP_REQUEST.json','CLOUD_SEAL_COMPLETE.json','POSTPROCESS_NOT_RUN.json']:
    p=run/name
    if p.exists():r['receipts'][name]=json.loads(p.read_text())
for name in ['PROCESS_IDENTITY.json','SUPERVISOR_IDENTITY.json','GUARD_READY.json']:
    p=run/name
    if p.exists():
        i=json.loads(p.read_text());r['processes'][name]={'identity':i,'alive':alive(i)}
for rel in ['raw/NATIVE_RETURN.json','raw/RAW_DURABLE.json','raw/vectors/RAW_RECEIPT.json','postprocess/POSTPROCESS_RECEIPT.json','bridge/BRIDGE_RECEIPT.json']:
    p=run/rel
    if p.exists():r['receipts'][rel]=json.loads(p.read_text())
for name in ['worker.stdout.log','gurobi.log','guard.stdout.log']:
    p=run/name
    if p.exists():
        with p.open('rb') as f:f.seek(max(0,p.stat().st_size-6000));tail=f.read().decode('utf8','replace')
        r[name]={'mtime':p.stat().st_mtime,'bytes':p.stat().st_size,'tail':tail}
p=run/'RESOURCE.jsonl'
if p.exists():
    rows=[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
    if rows:r['sampled_resources']={'count':len(rows),'first':rows[0],'last':rows[-1],'max_rss':max(v['rss_bytes'] for v in rows),'min_disk':min(v['disk_free_bytes'] for v in rows),'min_cgroup_headroom':min(v['cgroup_headroom_bytes'] for v in rows)}
print(json.dumps(r,ensure_ascii=False,indent=2))
