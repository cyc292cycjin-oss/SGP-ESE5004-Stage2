"""Default: read-only preflight. Execution needs a later explicit authorisation."""
from pathlib import Path
import argparse,json,subprocess,datetime
import psutil
from gate5_resources import current_evidence,budget,admission,host_read,process_tree_sample,cgroup_memory,sha
DAILY_SHA='7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd'
def authorize(path,root,run_id):
    if not path:raise ValueError('No new real-run authorization; preflight only')
    a=json.loads(Path(path).read_text())
    expected=budget(current_evidence(root))
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    if not (a.get('resource_plan_accepted') is True and a.get('real_gate5_authorized') is True and a.get('run_id')==run_id and a.get('max_attempts')==1 and a.get('input_sha256')==DAILY_SHA and a.get('code_sha')==head and a.get('accepted_budget')==expected and a.get('human_decision_reference')):
        raise ValueError('Resource plan and this exact future run require an explicit, current human authorization receipt')
    return a

def main():
    p=argparse.ArgumentParser();p.add_argument('--host-report',required=True);p.add_argument('--output',required=True);p.add_argument('--execute',action='store_true');p.add_argument('--authorization');args=p.parse_args()
    root=Path(__file__).resolve().parents[1];e=current_evidence(root)
    host=host_read(args.host_report);vm=psutil.virtual_memory();tree=process_tree_sample(include_pss=True)
    r=admission(e,host,vm.available,tree['process_tree_rss_bytes'],cgroup_memory())
    source=root/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc'
    if sha(source)!=DAILY_SHA:raise ValueError('Frozen input hash changed')
    r.update(observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),latest_run=e,host=host,linux=dict(memory=vm._asdict(),swap=psutil.swap_memory()._asdict(),process_tree=tree,disk=psutil.disk_usage(root)._asdict(),swaps=Path('/proc/swaps').read_text(),container_related_processes=[dict(pid=p.info['pid'],name=p.info['name']) for p in psutil.process_iter(['pid','name']) if any(s in (p.info['name'] or '').lower() for s in ['docker','containerd','podman'])]),frozen_input_sha256=DAILY_SHA,mode='PREFLIGHT_ONLY' if not args.execute else 'EXPLICIT_EXECUTION_REQUEST',solver_runs_this_round=0,authorization='PENDING_NOT_GRANTED_BY_THIS_SCRIPT',solver_budget=dict(time_limit=10800,wall_guard=14400,threads=2),code_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),code_sha256={name:sha(root/'scripts_project'/name) for name in ['gate5_resources.py','gate5_memory_preflight.py','Get-Gate5HostResources.ps1','Invoke-Gate5MemoryReadiness.ps1']})
    Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(dict(status=r['status'],reasons=r['reasons'],mode=r['mode'],solver_runs=0),indent=2))
    if not args.execute:return 0 if r['status']=='PASS' else 2
    authorize(args.authorization,root,'gate5_20261006_05')
    if r['status']!='PASS':raise ValueError('Resource preflight failed; no run launched')
    # Only imported after authorization + preflight. No variables built before.
    from run_gate5_stable_inventory import run
    return run(root,root/'results_project/validation/gate5_20261006_05',10800,14400,Path(args.host_report),Path(args.authorization))
if __name__=='__main__':raise SystemExit(main())
