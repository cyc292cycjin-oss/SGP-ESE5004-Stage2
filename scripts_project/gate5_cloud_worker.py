"""Durable supervisor and evidence collector; exactly one guarded child run."""
import argparse,csv,datetime,json,os,shutil,subprocess,sys,traceback
from pathlib import Path
from gate5_resources import sha
from gate5_cloud_resources import validate_run_path
from gate5_cloud_preflight import json_write,require


def collect(out,exit_code,identity):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    p=out/'GATE5_VALIDATION_RUN_MANIFEST.json'
    raw=json.loads(p.read_text()) if p.exists() else {}
    qpath=out/'native_result/NATIVE_QUALIFICATION.json'
    q=json.loads(qpath.read_text()) if qpath.exists() else raw.get('native_solution_qualification',{})
    qualified=q.get('network_writeback_qualified') is True
    checks=out/'GATE5_DYNAMIC_CHECKS.json';detail=out/'GATE5_DYNAMIC_DETAIL.json'
    rows=json.loads(checks.read_text()) if qualified and checks.exists() else []
    objective=json.loads(detail.read_text()).get('objective_reconciliation',{}) if qualified and detail.exists() else {}
    network=Path(raw['result_network']) if raw.get('result_network') else None
    exported=bool(network and network.is_file() and sha(network)==raw.get('result_sha256'))
    objective_check=next((r for r in rows if 'OBJECTIVE_RECONCILIATION' in str(r)),{})
    passed=(exit_code==0 and raw.get('status')=='PASS' and qualified and
            q.get('linopy_termination_condition')=='optimal' and raw.get('dynamic_checks')=='PASS' and raw.get('export_roundtrip')=='PASS'
            and exported and bool(rows) and all(r.get('Status')=='PASS' for r in rows) and bool(objective) and objective_check.get('Status')=='PASS')
    result=dict(raw,**identity)
    result.update(worker_exit_code=exit_code,qualified_primal=qualified,gate5_pass=passed,
                  objective=raw.get('objective') if qualified else None,
                  result_network=raw.get('result_network') if qualified else None,
                  dynamic_checks=raw.get('dynamic_checks','NOT_RUN') if qualified else 'NOT_RUN',
                  solver_runs=raw.get('solver_runs',0),gate6_runs=0,integrated_runs=0,disconnected_runs=0,
                  ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    json_write(out/'CLOUD_GATE5_RUN_MANIFEST.json',result)
    json_write(out/'EXIT_STATUS.json',dict(exit_code=exit_code,solver_runs=result['solver_runs'],gate5_pass=passed))
    fields=list(dict.fromkeys(k for r in rows for k in r)) or ['Check','Status','Reason']
    with (out/'CLOUD_GATE5_DYNAMIC_CHECKS.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        writer.writerows(rows or [dict(Check='DYNAMIC_VALIDATION',Status='NOT_RUN',Reason='No completed qualified dynamic validation receipt')])
    with (out/'CLOUD_GATE5_OBJECTIVE_RECONCILIATION.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['Component','Value','Unit','Status']);writer.writeheader()
        if objective:
            for key,value in objective.items():writer.writerow(dict(Component=key,Value=value,Unit='EUR2020/year',Status='RECORDED'))
            residual=objective['actual']-sum(objective[k] for k in ['capital','variable','known_fixed_once'])
            check=next((r for r in rows if 'OBJECTIVE_RECONCILIATION' in str(r)),{})
            writer.writerow(dict(Component='reconciliation_residual',Value=residual,Unit='EUR2020/year',Status=check.get('Status','UNKNOWN')))
        else:writer.writerow(dict(Component='objective_reconciliation',Value='',Unit='EUR2020/year',Status='NOT_RUN'))
    return result


def validate_dispatch(root,authorization,preflight):
    a=json.loads(Path(authorization).read_text());p=json.loads(Path(preflight).read_text())
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    require(p.get('status')=='PASS' and p.get('solver_runs')==0,'Cloud preflight has not passed without solving')
    require(p.get('code_sha')==a.get('code_sha')==head,'Preflight/authorization/code mismatch')
    require(p.get('input_sha256')==a.get('input_sha256'),'Input authorization mismatch')
    require(a.get('max_attempts')==1 and a.get('real_gate5_authorized') is True,'One real run is not authorized')
    require(a.get('cloud_preflight_sha256')==sha(preflight),'Preflight receipt changed')
    return a


def main(authorization,preflight):
    root=Path(__file__).resolve().parents[1]
    a=validate_dispatch(root,authorization,preflight)
    out=root.parent/'runs'/a['run_id'];cloud_root=validate_run_path(out)
    require(not out.exists(),'Run directory already exists')
    supervision=cloud_root/'evidence'/(a['run_id']+'_supervisor');supervision.mkdir(exist_ok=False)
    identity=dict(code_sha=a['code_sha'],input_sha256=a['input_sha256'],authorization_id=a['authorization_id'],
                  authorization_sha256=sha(authorization),preflight_sha256=sha(preflight),run_id=a['run_id'])
    json_write(supervision/'WORKER_MANIFEST.json',dict(identity,worker_pid=os.getpid(),status='STARTING',solver_runs=0))
    code=125
    try:
        command=[sys.executable,str(root/'scripts_project/run_gate5_stable_inventory.py'),'--resource-mode','cloud',
                 '--output',str(out),'--execution-authorization',str(authorization),'--time-limit','10800','--wall-guard','14400']
        with (supervision/'runner_stdout.log').open('w') as log:
            child=subprocess.Popen(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            json_write(supervision/'WORKER_MANIFEST.json',dict(identity,worker_pid=os.getpid(),runner_pid=child.pid,status='RUNNING'))
            code=child.wait()
    except Exception:
        (supervision/'worker_failure_traceback.txt').write_text(traceback.format_exc())
    finally:
        out.mkdir(exist_ok=True)
        for p in supervision.iterdir():
            if p.is_file():shutil.copyfile(p,out/p.name)
        shutil.copyfile(authorization,out/'EXECUTION_AUTHORIZATION.json')
        pf=Path(preflight).parent
        for p in pf.glob('CLOUD_*.json'):shutil.copyfile(p,out/p.name)
        result=collect(out,code,identity)
        json_write(supervision/'EXIT_STATUS.json',dict(exit_code=code,solver_runs=result['solver_runs'],gate5_pass=result['gate5_pass']))
        hashes={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='RESULT_SHA256.json'}
        json_write(out/'RESULT_SHA256.json',dict(files=hashes,solver_runs=result['solver_runs']))
    return 0 if result['gate5_pass'] else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--authorization',required=True);parser.add_argument('--preflight',required=True)
    args=parser.parse_args();raise SystemExit(main(args.authorization,args.preflight))
