"""One authorized Gate5 retry from the byte-identical accepted daily input."""
import argparse, json, os, sys, time, threading, traceback, platform, subprocess, resource
from pathlib import Path
from decimal import Decimal, getcontext
from collections import defaultdict
import numpy as np
import pandas as pd
import psutil, pypsa, linopy, highspy
from run_gate5_validation import sha,now,dump,hook_receipt
from assembly_components import install_research_constraint_hooks,validate_hooks,check_global_constraints
from fixed_accounts import validate_exported_accounting
from precision_handoff import audited_direct_backend,research_scalar_assignment

DAILY_SHA='7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd'


def fixed_screen(n):
    getcontext().prec = 100
    groups=defaultdict(list); rows=[]
    for name,r in n.meta['biomass_obligation_routes'].items():groups[tuple(sorted(r['buses']))].append(name)
    demand=n.get_switchable_as_dense('Load','p_set'); weights=n.snapshot_weightings.stores
    for buses,stores in groups.items():
        ids=n.loads.index[n.loads.bus.isin(buses)]
        q=demand[ids].sum(axis=1)
        required=sum((Decimal.from_float(float(x))*Decimal.from_float(float(w)) for x,w in zip(q,weights)),Decimal(0))
        available=sum((Decimal.from_float(float(n.stores.at[s,'e_initial'])) for s in stores),Decimal(0))
        rows.append(dict(final_buses=list(buses),resources=stores,source_binary64_required_mwh=str(required),source_binary64_available_mwh=str(available),source_binary64_difference_mwh=str(required-available),floating_difference_mwh=float(q.mul(weights).sum()-n.stores.loc[stores,'e_initial'].sum()),scope='Necessary annual accounting screen; not solver feasibility proof'))
    return rows


def run(root,out):
    os.chdir(root);out.mkdir(parents=True,exist_ok=False)
    manifest=out/'GATE5_VALIDATION_RUN_MANIFEST.json'
    receipt=dict(run_id=out.name,gate='GATE5',role='VALIDATION_ONLY',status='PREFLIGHT',start_time=now(),solver_runs=0,
        objective=None,result_network=None,dynamic_checks='NOT_RUN',gate6_runs=0,formal_phase5_runs=0,
        input_path='results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc',input_sha256=DAILY_SHA,
        original_failed_run='gate5_20261006_01',io_api='direct',adapter='PROJECT_STREAMED_FLOAT64',
        solver_options={'threads':2,'time_limit':3600,'solver':'ipm','run_crossover':'off'},
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    stage={'name':'preflight'}; stop=threading.Event(); started=time.monotonic()
    def save():
        receipt['peak_rss_mib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
        dump(manifest,receipt)
    def progress(name,detail=None):
        stage['name']=name
        if detail:stage['detail']=detail
        if psutil.virtual_memory().available<512*1024**2:raise MemoryError('Available memory below approved 512 MiB guard')
    def monitor():
        with (out/'RESOURCE_MONITOR.jsonl').open('a',buffering=1) as f:
            while not stop.wait(2):
                s=stage['name'];log=out/'gate5_solver.log'
                if s=='presolve_or_solve' and log.exists():
                    with log.open('rb') as source:source.seek(max(0,log.stat().st_size-4096));tail=source.read().decode(errors='replace')
                    s='solve' if ('IPX' in tail or 'ipm' in tail.lower() or 'Iter' in tail) else 'presolve'
                mem=psutil.virtual_memory();record=dict(time=now(),elapsed_s=time.monotonic()-started,stage=s,rss_bytes=psutil.Process().memory_info().rss,available_bytes=mem.available,**({'progress':stage.get('detail')} if s=='handoff' else {}))
                f.write(json.dumps(record)+'\n')
                if mem.available<512*1024**2 or time.monotonic()-started>7200:
                    receipt.update(status='STOPPED_RESOURCE_GUARD',stop_reason='512 MiB available-memory / 7200 s wall guard',end_time=now());save();os._exit(3)
    t=threading.Thread(target=monitor,daemon=True);t.start()
    try:
        if subprocess.check_output(['git','status','--porcelain'],text=True).strip():raise ValueError('Clean tree required')
        if sys.version_info[:3]!=(3,11,13) or pypsa.__version__!='0.30.3' or linopy.__version__!='0.5.5' or highspy.Highs().version()!='1.11.0':raise ValueError('Frozen environment mismatch')
        source=root/receipt['input_path']
        if sha(source)!=DAILY_SHA:raise ValueError('Daily input hash changed')
        synth=json.loads((root/'results_project/validation/precision_synthetic_20261006_03/PRECISION_REGRESSION_RESULTS.json').read_text())
        if synth.get('status')!='PASS':raise ValueError('Synthetic prerequisites not passed')
        receipt['environment']=dict(python=sys.version,pypsa=pypsa.__version__,linopy=linopy.__version__,highs=highspy.Highs().version(),ram_bytes=psutil.virtual_memory().total,platform=platform.platform())
        progress('input_validation');n=pypsa.Network(source)
        if len(n.snapshots)!=365 or len(n.loads)!=1737 or n.loads.source_account_id.nunique()!=171:raise ValueError('Accepted input dimensions changed')
        validate_hooks(n);check_global_constraints(n);validate_exported_accounting(n)
        if len(n.meta['external_pending_fixed_accounts'])!=807:raise ValueError('Fixed ledger changed')
        screen=fixed_screen(n);dump(out/'ALL_FIXED_RESOURCE_PRECISION_SCREEN.json',screen)
        receipt.update(fixed_resource_groups=len(screen),fixed_resource_stores=sum(len(r['resources']) for r in screen),annual_hours=float(n.snapshot_weightings.stores.sum()),loads=1737,accounts=171,snapshots=365,policy_enabled=False)
        progress('model_build');save();n.optimize.create_model();model=n.model;before=set(model.constraints)
        install_research_constraint_hooks(n);hooks=hook_receipt(n,before);dump(out/'CONSTRAINT_ATTACHMENT_RECEIPT.json',hooks)
        if len(hooks['research_constraint_names'])!=1003:raise ValueError('Research hook group count changed')
        receipt.update(status='MODEL_READY',variables=int(model.nvars),constraints=int(model.ncons));save()
        certificate=json.loads((root/'research/04_model_assembly/final_validation/EXACT_LP_CONTRADICTION_ROWS.json').read_text())
        factors={k:v['factor'] for k,v in certificate.items()}
        labels=list(map(int,certificate))+[3459209,3459210]
        def before_run(h,transfer):
            if n.model is not model or transfer['status']!='PASS':raise ValueError('Same model/fidelity precondition failed')
            progress('presolve_or_solve');receipt.update(status='SOLVING',solver_runs=1,solve_start_time=now(),solver_transfer_status='PASS',nnz=transfer['nnz']);save()
            print('GATE5 FIDELITY_PASS; starting one real retry',flush=True)
        progress('handoff')
        with audited_direct_backend(out/'SOLVER_TRANSFER_FIDELITY.json',progress=progress,before_run=before_run,certificate_labels=labels,certificate_factors=factors),research_scalar_assignment():
            status,condition=n.optimize.solve_model(solver_name='highs',solver_options=receipt['solver_options'],io_api='direct',log_fn=out/'gate5_solver.log')
        receipt.update(solver_status=status,termination_condition=condition,solve_end_time=now())
        if n.model is not model:raise ValueError('Model replaced during solve')
        if (status,condition)!=('ok','optimal'):
            receipt.update(status='FAILED_INFEASIBLE' if condition=='infeasible' else 'FAILED_'+condition.upper(),objective=None,result_network=None,dynamic_checks='NOT_RUN',gate6_status='NOT_RUN_PREDECESSOR_FAILED',end_time=now());save();return 2
        progress('postsolve_export');receipt.update(status='OPTIMAL_DYNAMIC_PENDING',objective=float(n.objective));save()
        # Preserve primal state before any previously unexercised dynamic checker.
        n.meta.update(artifact_role='GATE5_VALIDATION_SOLVED_DYNAMIC_PENDING',scientific_results_allowed=False,formal_phase5_allowed=False,solver_allowed=False,constraint_hook_state='INSTALLED_AND_SOLVED_ON_SAME_MODEL')
        result=out/'research_2050_gate5_24h_validation_solved.nc';n.export_to_netcdf(result)
        receipt.update(result_network=str(result.relative_to(root)),result_sha256=sha(result));save()
        progress('dynamic_checks')
        from validation_dynamics import dynamic_checks
        checks,detail=dynamic_checks(n);dump(out/'GATE5_DYNAMIC_CHECKS.json',checks);dump(out/'GATE5_DYNAMIC_DETAIL.json',detail)
        passed=all(r['Status']=='PASS' for r in checks)
        receipt.update(status='PASS' if passed else 'FAILED_DYNAMIC_CHECKS',dynamic_checks='PASS' if passed else 'FAIL',gate6_status='NOT_RUN_FORMAL_CONFIG_PENDING',end_time=now());save();return 0 if passed else 2
    except Exception as e:
        receipt.update(status='FAILED_ENGINEERING' if receipt['solver_runs'] else 'NOT_RUN_PREFLIGHT_FAILED',error_type=type(e).__name__,stop_reason=str(e),end_time=now())
        (out/'failure_traceback.txt').write_text(traceback.format_exc());save();raise
    finally:
        stop.set();t.join(timeout=3);save()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();raise SystemExit(run(Path(__file__).resolve().parents[1],Path(a.output).resolve()))
