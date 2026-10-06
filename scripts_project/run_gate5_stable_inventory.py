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
from fixed_inventory_scaling import FixedInventoryScaling,physical_checks
from inventory_audit import audit

DAILY_SHA='7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd'


def result_route(status,condition):
    """Only a natively qualified primal reaches PyPSA mapping and dynamic checks."""
    return dict(run_dynamic_checks=status=='ok',optimal=condition=='optimal',
        failure_status='FAILED_PRIMAL_QUALIFICATION' if status!='ok' and condition=='optimal' else ('FAILED_INFEASIBLE' if condition=='infeasible' else 'FAILED_'+condition.upper()))


def monitor_phase(tail,solve_seen):
    solve_seen=solve_seen or 'IPX' in tail or 'ipm' in tail.lower() or 'Iter' in tail
    return ('solve' if solve_seen else 'presolve'),solve_seen


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


def run(root,out,time_limit=3600,wall_guard=7200):
    if (time_limit,wall_guard) not in [(3600,7200),(10800,14400)]:raise ValueError('Unapproved numerical budget')
    os.chdir(root);out.mkdir(parents=True,exist_ok=False)
    manifest=out/'GATE5_VALIDATION_RUN_MANIFEST.json'
    receipt=dict(run_id=out.name,gate='GATE5',role='VALIDATION_ONLY',status='PREFLIGHT',start_time=now(),solver_runs=0,
        objective=None,result_network=None,dynamic_checks='NOT_RUN',gate6_runs=0,formal_phase5_runs=0,
        input_path='results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc',input_sha256=DAILY_SHA,
        original_failed_runs=['gate5_20261006_01','gate5_20261006_02','gate5_20261006_03'],io_api='direct',adapter='PROJECT_STREAMED_FLOAT64',
        formulation='REVERSIBLE_POWER_OF_TWO_FIXED_INVENTORY_NORMALISATION',
        solver_options={'threads':2,'time_limit':time_limit,'solver':'ipm','run_crossover':'on'},wall_guard_seconds=wall_guard,
        execution='NEW_FROM_FROZEN_INPUT_NOT_CHECKPOINT_RESUME',pid=os.getpid(),
        crossover_reason='Local largest-group KKT/postsolve probe failed without crossover and passed with standard crossover; no feasibility tolerance or presolve changes',
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
        solve_seen=False
        with (out/'RESOURCE_MONITOR.jsonl').open('a',buffering=1) as f:
            while not stop.wait(2):
                s=stage['name'];log=out/'gate5_solver.log'
                if s=='presolve_or_solve' and log.exists():
                    with log.open('rb') as source:source.seek(max(0,log.stat().st_size-4096));tail=source.read().decode(errors='replace')
                    s,solve_seen=monitor_phase(tail,solve_seen)
                mem=psutil.virtual_memory();record=dict(time=now(),elapsed_s=time.monotonic()-started,stage=s,rss_bytes=psutil.Process().memory_info().rss,available_bytes=mem.available,**({'progress':stage.get('detail')} if s=='handoff' else {}))
                f.write(json.dumps(record)+'\n')
                if mem.available<512*1024**2 or time.monotonic()-started>wall_guard:
                    receipt.update(status='STOPPED_RESOURCE_GUARD',stop_reason=f'512 MiB available-memory / {wall_guard} s wall guard',end_time=now());save();os._exit(3)
    t=threading.Thread(target=monitor,daemon=True);t.start()
    try:
        if subprocess.check_output(['git','status','--porcelain'],text=True).strip():raise ValueError('Clean tree required')
        if sys.version_info[:3]!=(3,11,13) or pypsa.__version__!='0.30.3' or linopy.__version__!='0.5.5' or highspy.Highs().version()!='1.11.0':raise ValueError('Frozen environment mismatch')
        source=root/receipt['input_path']
        if sha(source)!=DAILY_SHA:raise ValueError('Daily input hash changed')
        synth=json.loads((root/'results_project/validation/precision_synthetic_20261006_03/PRECISION_REGRESSION_RESULTS.json').read_text())
        if synth.get('status')!='PASS':raise ValueError('Synthetic prerequisites not passed')
        for prerequisite in ['inventory_local_20261006_02/LOCAL_NUMERICAL_REGRESSION_RESULTS.json','inventory_mapping_20261006_01/MAPPING_REGRESSION_RESULTS.json']:
            if json.loads((root/'results_project/validation'/prerequisite).read_text()).get('status')!='PASS':raise ValueError('Stable formulation prerequisite not passed: '+prerequisite)
        qpath=root/'research/04_model_assembly/final_validation/GATE5_RESULT_QUALIFICATION_TESTS.json'
        qtest=json.loads(qpath.read_text())
        if qtest.get('status')!='PASS' or qtest.get('solver_runs')!=0:raise ValueError('Mock result qualification prerequisite failed')
        for name,hash_value in qtest['tested_code_sha256'].items():
            if sha(root/'scripts_project'/name)!=hash_value:raise ValueError('Qualification test code hash stale: '+name)
        receipt['qualification_tests_sha256']=sha(qpath)
        previous=json.loads((root/'results_project/validation/gate5_20261006_03/GATE5_VALIDATION_RUN_MANIFEST.json').read_text())
        required_bytes=(previous['peak_rss_mib']+512)*1024**2
        receipt['memory_preflight']=dict(required_available_bytes=required_bytes,available_bytes=psutil.virtual_memory().available,basis='Observed run03 process peak + existing 512 MiB reserve')
        if psutil.virtual_memory().available<required_bytes:raise MemoryError('Preflight: insufficient available RAM for observed run03 peak plus reserve')
        receipt['environment']=dict(python=sys.version,pypsa=pypsa.__version__,linopy=linopy.__version__,highs=highspy.Highs().version(),ram_bytes=psutil.virtual_memory().total,platform=platform.platform())
        progress('input_validation');n=pypsa.Network(source)
        if len(n.snapshots)!=365 or len(n.loads)!=1737 or n.loads.source_account_id.nunique()!=171:raise ValueError('Accepted input dimensions changed')
        validate_hooks(n);check_global_constraints(n);validate_exported_accounting(n)
        if len(n.meta['external_pending_fixed_accounts'])!=807:raise ValueError('Fixed ledger changed')
        identity=audit(n,root)
        prior=json.loads((root/'results_project/validation/inventory_local_20261006_02/FORMULATION_MAPPING_AND_ROUNDING_AUDIT.json').read_text())
        if identity!=prior:raise ValueError('Pre-solve source identity or predeclared original-unit bound changed')
        dump(out/'FORMULATION_MAPPING_AND_ROUNDING_AUDIT.json',identity)
        screen=fixed_screen(n);dump(out/'ALL_FIXED_RESOURCE_PRECISION_SCREEN.json',screen)
        receipt.update(fixed_resource_groups=len(screen),fixed_resource_stores=sum(len(r['resources']) for r in screen),annual_hours=float(n.snapshot_weightings.stores.sum()),loads=1737,accounts=171,snapshots=365,policy_enabled=False)
        progress('model_build');save();n.optimize.create_model();model=n.model;before=set(model.constraints)
        install_research_constraint_hooks(n);hooks=hook_receipt(n,before);dump(out/'CONSTRAINT_ATTACHMENT_RECEIPT.json',hooks)
        if len(hooks['research_constraint_names'])!=1003:raise ValueError('Research hook group count changed')
        transformation=FixedInventoryScaling(n,identity)
        receipt.update(status='MODEL_READY',variables=int(model.nvars),constraints=int(model.ncons));save()
        certificate=json.loads((root/'research/04_model_assembly/final_validation/EXACT_LP_CONTRADICTION_ROWS.json').read_text())
        factors={k:v['factor'] for k,v in certificate.items()}
        labels=list(map(int,certificate))+[3459209,3459210]
        def before_run(h,transfer):
            if n.model is not model or transfer['status']!='PASS':raise ValueError('Same model/fidelity precondition failed')
            progress('presolve_or_solve');receipt.update(status='SOLVING',solver_runs=1,solve_start_time=now(),solver_transfer_status='PASS',nnz=transfer['nnz']);save()
            print('GATE5 FIDELITY_PASS; starting one real retry',flush=True)
        progress('handoff')
        with audited_direct_backend(out/'SOLVER_TRANSFER_FIDELITY.json',progress=progress,before_run=before_run,certificate_labels=labels,certificate_factors=factors,transformation=transformation),research_scalar_assignment(out/'FOM_SCALAR_ASSIGNMENT_DIAGNOSTIC.json'):
            status,condition=n.optimize.solve_model(solver_name='highs',solver_options=receipt['solver_options'],io_api='direct',log_fn=out/'gate5_solver.log')
        receipt.update(solver_status=status,termination_condition=condition,solve_end_time=now())
        qualification=json.loads((out/'SOLVER_TRANSFER_FIDELITY.json').read_text())
        receipt.update(native_solution_qualification=qualification['native_solution_qualification'],network_writeback_qualified=qualification['network_writeback_qualified'],original_scale_mapping_status=qualification['original_scale_mapping_status'])
        if n.model is not model:raise ValueError('Model replaced during solve')
        route=result_route(status,condition)
        if not route['run_dynamic_checks']:
            receipt.update(status=route['failure_status'],objective=None,result_network=None,dynamic_checks='NOT_RUN',gate6_status='NOT_RUN_PREDECESSOR_FAILED',end_time=now());save();return 2
        progress('postsolve_export');receipt.update(status='OPTIMAL_DYNAMIC_PENDING' if route['optimal'] else 'FEASIBLE_CANDIDATE_DYNAMIC_PENDING',objective=float(n.objective));save()
        # Preserve primal state before any previously unexercised dynamic checker.
        n.meta.update(artifact_role='GATE5_VALIDATION_SOLVED_DYNAMIC_PENDING',scientific_results_allowed=False,formal_phase5_allowed=False,solver_allowed=False,constraint_hook_state='INSTALLED_AND_SOLVED_ON_SAME_MODEL')
        result=out/'research_2050_gate5_24h_validation_solved.nc';n.export_to_netcdf(result)
        receipt.update(result_network=str(result.relative_to(root)),result_sha256=sha(result));save()
        progress('dynamic_checks')
        from validation_dynamics import dynamic_checks
        checks,detail=dynamic_checks(n)
        strict=physical_checks(n,identity);dump(out/'FIXED_ORIGINAL_UNIT_CHECKS.json',strict)
        checks+=strict
        reread=pypsa.Network(result)
        if reread.meta!=n.meta:raise ValueError('Solved export metadata changed')
        for typ in ['Generator','Link','Line','Transformer','Store','StorageUnit','Load']:
            for attr,frame in n.pnl(typ).items():
                if not frame.empty and not frame.equals(reread.pnl(typ)[attr]):raise ValueError('Solved time series changed at export: '+typ+'.'+attr)
        if not all(r['Status']=='PASS' for r in physical_checks(reread,identity)):raise ValueError('Readback original-unit fixed checks failed')
        receipt['export_roundtrip']='PASS'
        dump(out/'GATE5_DYNAMIC_CHECKS.json',checks);dump(out/'GATE5_DYNAMIC_DETAIL.json',detail)
        dynamic_passed=all(r['Status']=='PASS' for r in checks);passed=dynamic_passed and route['optimal']
        receipt.update(status='PASS' if passed else ('FAILED_DYNAMIC_CHECKS' if not dynamic_passed else 'VALIDATION_FEASIBLE_NOT_OPTIMAL'),dynamic_checks='PASS' if dynamic_passed else 'FAIL',gate6_status='NOT_RUN_HUMAN_REVIEW_REQUIRED' if passed else 'NOT_RUN_PREDECESSOR_FAILED',end_time=now());save();return 0 if passed else 2
    except Exception as e:
        transfer_receipt=out/'SOLVER_TRANSFER_FIDELITY.json'
        if transfer_receipt.exists():
            q=json.loads(transfer_receipt.read_text()).get('native_solution_qualification')
            if q:
                receipt['native_solution_qualification']=q
                receipt['termination_condition']=q['linopy_termination_condition']
        receipt.update(status='FAILED_ENGINEERING' if receipt['solver_runs'] else 'NOT_RUN_PREFLIGHT_FAILED',error_type=type(e).__name__,stop_reason=str(e),end_time=now())
        (out/'failure_traceback.txt').write_text(traceback.format_exc());save();raise
    finally:
        stop.set();t.join(timeout=3);save()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--time-limit',type=int,default=3600);p.add_argument('--wall-guard',type=int,default=7200);a=p.parse_args();raise SystemExit(run(Path(__file__).resolve().parents[1],Path(a.output).resolve(),a.time_limit,a.wall_guard))
