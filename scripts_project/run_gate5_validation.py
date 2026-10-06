"""Authorized Gate5 only. Never starts Gate6 or formal experiments."""
import argparse, hashlib, json, os, subprocess, time, traceback, resource
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import pypsa
from validation_temporal import daily_validation_network,FROZEN_SHA
from assembly_components import install_research_constraint_hooks,validate_hooks,check_global_constraints
from fixed_accounts import validate_exported_accounting

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def dump(p,obj):Path(p).write_text(json.dumps(obj,indent=2,default=str,allow_nan=False)+'\n')

def hook_receipt(n,before):
    m=n.model;after=set(m.constraints);required=set()
    required.update('ResearchStoreDirection-'+x for x in n.meta.get('store_power_rules',{}))
    required.update('ResearchImportAnnual-'+x for x in n.meta.get('external_annual_caps',{}))
    required.update('ResearchExistingResource-'+k for k,v in n.meta.get('existing_resource_groups',{}).items() if v['candidates'])
    required.update('ResearchBatteryNominal-'+str(i) for i in range(len(n.meta.get('battery_inverter_pairs',[]))))
    if not required.issubset(after) or after-before!=required:raise ValueError('Missing/unexpected research constraint attachment')
    if 'GlobalConstraint-lv_limit' not in after:raise ValueError('Native lv_limit missing from actual model')
    if n._research_existing_assets_model is not m:raise ValueError('Known FOM attached to a different model')
    v=m['Research-existing-FOM-constant'];label=int(v.labels.item())
    coef=float(m.objective.expression.coeffs.where(m.objective.expression.vars==label,0).sum())
    if not np.isclose(coef,n.meta['existing_annual_fixed_om_eur'],rtol=1e-12):raise ValueError('Known fixed FOM is missing or counted twice')
    rows=[]
    for name in sorted(required|{'GlobalConstraint-lv_limit'}):
        c=m.constraints[name];active=c.labels.values>=0
        if not active.any():raise ValueError('Empty required constraint '+name)
        if not np.isfinite(c.rhs.values[active]).all():raise ValueError('Nonfinite constraint rhs '+name)
        if name.startswith('ResearchStoreDirection') and c.labels.size!=len(n.snapshots):raise ValueError('Store direction snapshot coverage lost')
        if not ((c.vars.values>=0)&(c.coeffs.values!=0)).any():raise ValueError('Required constraint has no variables '+name)
        rows.append(dict(Name=name,Dimensions=dict(c.sizes),ActiveRows=int(active.sum()),VariableTerms=int(((c.vars.values>=0)&(c.coeffs.values!=0)).sum()),Status='ATTACHED_TO_SOLVE_MODEL'))
    return dict(native_constraints=sorted(before),research_constraint_names=sorted(required),constraints=rows,known_fom_coefficient=coef,model_variable_count=int(m.nvars),model_constraint_count=int(m.ncons),policy_enabled=False)

def run(root,out):
    os.chdir(root);out.mkdir(parents=True,exist_ok=False)
    receipt=dict(run_id=out.name,gate='GATE5',role='VALIDATION_ONLY',start_time=now(),status='STARTED',solver_runs=0,formal_phase5_runs_executed=0,gate6_started=False,input_sha256=FROZEN_SHA,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    manifest=out/'GATE5_VALIDATION_RUN_MANIFEST.json'
    def save():receipt['peak_rss_mib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024;dump(manifest,receipt)
    save()
    try:
        if subprocess.check_output(['git','status','--porcelain'],text=True).strip():raise ValueError('Validation run requires clean working tree')
        if pypsa.__version__!='0.30.3':raise ValueError('Frozen PyPSA changed')
        source=root/'results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc'
        if sha(source)!=FROZEN_SHA:raise ValueError('Gate4 SHA mismatch')
        original=pypsa.Network(source);n,integrals=daily_validation_network(original)
        dump(out/'TEMPORAL_INTEGRAL_CHECKS.json',integrals)
        validate_hooks(n);check_global_constraints(n);validate_exported_accounting(n)
        path=out/'research_2050_gate5_24h_validation_input.nc';n.export_to_netcdf(path)
        loaded=pypsa.Network(path)
        if loaded.meta!=n.meta:raise ValueError('Derived input meta roundtrip changed')
        for c in n.iterate_components():
            pd.testing.assert_frame_equal(c.df.sort_index(axis=0).sort_index(axis=1),loaded.df(c.name).sort_index(axis=0).sort_index(axis=1),check_dtype=False,check_exact=False,rtol=1e-12,atol=1e-12)
            for attr,f in c.pnl.items():
                if len(f.columns):pd.testing.assert_frame_equal(f.sort_index(axis=1),loaded.pnl(c.name)[attr].sort_index(axis=1),check_freq=False)
        n=loaded;del original,loaded
        receipt.update(status='INPUT_READY',validation_input_sha256=sha(path),snapshots=len(n.snapshots),account_count=n.loads.source_account_id.nunique(),loads=len(n.loads),annual_hours=float(n.snapshot_weightings.generators.sum()),policy_enabled=False)
        save();print('GATE5 INPUT_READY',flush=True)
        n.optimize.create_model();model=n.model;before=set(model.constraints)
        install_research_constraint_hooks(n)
        hooks=hook_receipt(n,before);dump(out/'CONSTRAINT_ATTACHMENT_RECEIPT.json',hooks)
        receipt.update(status='MODEL_READY',variables=hooks['model_variable_count'],constraints=hooks['model_constraint_count']);save()
        print('GATE5 MODEL_READY '+str((model.nvars,model.ncons)),flush=True)
        # solve_model solves the existing Linopy model. Do not call n.optimize(...).
        if n.model is not model:raise ValueError('Optimization model changed before solve')
        receipt.update(status='SOLVING',solver='highs',solver_options={'threads':2,'time_limit':3600,'solver':'ipm','run_crossover':'off'},solver_runs=1,solve_start_time=now());save()
        status,condition=n.optimize.solve_model(solver_name='highs',solver_options=receipt['solver_options'],problem_fn=str(out/'gate5_problem.lp'),log_fn=str(out/'gate5_solver.log'),keep_files=True)
        receipt.update(solver_status=status,termination_condition=condition,solve_end_time=now())
        if n.model is not model:raise ValueError('Solve API replaced research model')
        if (status,condition)!=('ok','optimal'):
            receipt.update(status='FAIL_SOLVE',gate5_reduced_solve='FAIL',gate5_engineering_validation='FAIL',stop_reason='Nonoptimal termination; no downstream gate');save();return 2
        from validation_dynamics import dynamic_checks
        checks,detail=dynamic_checks(n);dump(out/'GATE5_DYNAMIC_CHECKS.json',checks);dump(out/'GATE5_DYNAMIC_DETAIL.json',detail)
        passed=all(r['Status']=='PASS' for r in checks)
        n.meta.update(artifact_role='GATE5_VALIDATION_SOLVED',scientific_results_allowed=False,formal_phase5_allowed=False,validation_checks_passed=passed,constraint_hook_state='INSTALLED_AND_SOLVED_ON_SAME_MODEL',solver_allowed=False)
        solved=out/'research_2050_gate5_24h_validation_solved.nc';n.export_to_netcdf(solved)
        receipt.update(status='PASS' if passed else 'FAIL_DYNAMIC',gate5_reduced_solve='PASS',gate5_engineering_validation='PASS' if passed else 'FAIL',result_sha256=sha(solved),end_time=now())
        save();return 0 if passed else 2
    except Exception as e:
        receipt.update(status='FAIL',stop_reason=str(e),error_type=type(e).__name__,end_time=now(),gate5_reduced_solve='FAIL',gate5_engineering_validation='FAIL')
        (out/'failure_traceback.txt').write_text(traceback.format_exc());save();raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
    root=Path(__file__).resolve().parents[1];raise SystemExit(run(root,Path(args.output).resolve()))
