"""Gate6-only postsolve; one native read, then evidence-gated metadata finalization."""
import copy,json,os,shutil
from pathlib import Path
import netCDF4,numpy as np
from gate5_resources import sha
from lossless_gate5_lifecycle import qualify_and_store,release_native,reload_map_validate,trim
from finish_gate5_lossless import export_sequential
from closeout_gate5_metadata import netcdf_science_signature,network_signatures
from inventory_audit_3h import prefix_check

def write(path,value):
    path=Path(path);temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)

def accepted_metadata(old,q,checks,detail,exported,refs,parent_sha):
    if not q.get('network_writeback_qualified') or q.get('linopy_termination_condition')!='optimal' or q.get('native_getSolution_calls')!=1:raise ValueError('Native optimal qualification required')
    if not checks or not all(r['Status']=='PASS' for r in checks):raise ValueError('Dynamics not accepted')
    if not any('OBJECTIVE_RECONCILIATION' in r['Check'] for r in checks):raise ValueError('Objective reconciliation missing')
    if exported.get('status')!='PASS' or exported.get('sha256')!=parent_sha:raise ValueError('Export not accepted')
    account=detail['accounting_report'];obj=detail['objective_reconciliation']
    if not np.isfinite(q['objective']) or q['objective']!=obj['actual'] or q['objective']!=account['PricedObjective']:raise ValueError('Priced objective differs')
    if account['KnownFixedCostIncludedInPricedObjective'] is not True or account['KnownFixedCostToAddToPricedObjective']!=0 or obj['known_fixed_once']!=account['KnownFixedCost']:raise ValueError('FOM not counted once')
    m=copy.deepcopy(old)
    keys=('PricedObjective','KnownFixedCostIncludedInPricedObjective','KnownFixedCostToAddToPricedObjective')
    if set(account)!=set(m['accounting_report']):raise ValueError('Accounting schema changed')
    for k in account:
        if k not in keys and account[k]!=m['accounting_report'][k]:raise ValueError('Fixed accounting boundary changed: '+k)
    for k in ['scientific_results_allowed','policy_enabled','FullSystemCostComplete','FullSystemEmissionsComplete','full_system_cost_complete','full_system_emissions_complete']:
        if m[k] is not False:raise ValueError('Scientific boundary changed: '+k)
    if len(m['external_pending_fixed_accounts'])!=807 or sum(t['policy_weight'] is None for t in m['physical_carbon_map'])!=200:raise ValueError('Pending ledgers changed')
    if any(t['UnitPriceEUR2020PerMWh'] is not None or t['PhysicalCO2_tPerMWh'] is not None for t in m['external_pending_fixed_accounts']):raise ValueError('Unknown terms changed')
    m['gate6_parent_state']=dict(parent_sha256=parent_sha,inherited_state={k:copy.deepcopy(m.get(k)) for k in ['artifact_role','asset_role','source_is_solved','static_validation','input_only_extraction']},accounting={k:m['accounting_report'][k] for k in keys})
    for k in keys:m['accounting_report'][k]=account[k]
    m.update(artifact_role='GATE6_BASELINE_3H_VALIDATION_SOLVED_DYNAMIC_VALIDATED',formal_phase5_allowed=False,solver_allowed=False,gate6_allowed=False)
    m['current_result_qualification']=dict(status='PASS',gate='GATE6',scenario='BASELINE',dynamic_status='PASS',export_readback_status='PASS',
        native_status=q['model_status'],receipts=refs,parent_sha256=parent_sha,metadata_only_derivative=True,new_solve_authorized=False)
    return m

def finalize(parent,output,q,checks,detail,exported,refs):
    parent=Path(parent);output=Path(output);temp=output.with_suffix('.partial.nc')
    if output.exists() or temp.exists():raise FileExistsError('Non-overwrite final output')
    digest=sha(parent)
    with netCDF4.Dataset(parent) as ds:
        old=json.loads(ds.getncattr('meta'))
        if float(ds.getncattr('network_objective'))!=q['objective']:raise ValueError('Network objective changed')
    updated=accepted_metadata(old,q,checks,detail,exported,refs,digest)
    before=netcdf_science_signature(parent);frames=network_signatures(parent)
    try:
        shutil.copy2(parent,temp)
        with netCDF4.Dataset(temp,'r+') as ds:ds.setncattr('meta',json.dumps(updated,ensure_ascii=False,allow_nan=False))
        if before!=netcdf_science_signature(temp) or frames!=network_signatures(temp):raise ValueError('Metadata finalization changed science')
        with netCDF4.Dataset(temp) as ds:
            if json.loads(ds.getncattr('meta'))!=updated:raise ValueError('Metadata readback differs')
        if sha(parent)!=digest:raise ValueError('Parent mutated')
        temp.rename(output)
    finally:
        if temp.exists():temp.unlink()
    return dict(status='PASS',parent_sha256=digest,sha256=sha(output),scientific_data_unchanged=True,result_network=str(output))

def consume(owner,out,record,identity,progress):
    out=Path(out);progress('solution_retrieval')
    q=qualify_and_store(owner[0],out/'native_result',out/'mapping',record)
    release_native(owner);progress('native_released')
    if not q['network_writeback_qualified']:return dict(status='FAILED_NATIVE_QUALIFICATION',qualification=q,result_network=None)
    # The same frozen input is rebuilt only in a future separately authorized execution.
    progress('postsolve_rebuild_mapping')
    n,checks,detail=reload_map_validate(record['input_path'],record['input_sha256'],out/'mapping',out/'native_result',record,q,identity)
    # A full-prefix check is independent of the local one-step state equations.
    for group in identity['groups']:
        for store in group['stores']:
            prefix=prefix_check(float(n.stores.at[store,'e_initial']),n.stores_t.p[store].to_numpy(),n.stores_t.e[store].to_numpy(),n.snapshot_weightings.stores.to_numpy(),group['original_energy_error_bound_mwh'])
            checks.append(dict(Check='GATE6_ORIGINAL_3H_PREFIX:'+store,Status=prefix['status'],Detail=prefix,Unit='MWh'))
    write(out/'GATE6_DYNAMIC_CHECKS.json',checks);write(out/'GATE6_DYNAMIC_DETAIL.json',detail)
    if not checks or not all(r['Status']=='PASS' for r in checks):return dict(status='FAILED_DYNAMIC_CHECKS',qualification=q,result_network=None)
    if q['linopy_termination_condition']!='optimal':return dict(status='QUALIFIED_FEASIBLE_NOT_OPTIMAL',qualification=q,result_network=None)
    model=n.model
    for k,v in list(vars(n).items()):
        if v is model:setattr(n,k,None)
    del model,v;trim()
    n.meta.update(artifact_role='GATE6_BASELINE_3H_QUALIFIED_EXPORT_PENDING',formal_phase5_allowed=False,solver_allowed=False)
    progress('export_readback');no=[n];del n
    parent=out/'gate6_baseline_3h_accepted_arrays.nc'
    exported=export_sequential(no,parent,identity);write(out/'GATE6_EXPORT_READBACK.json',exported)
    refs={p:sha(out/p) for p in ['native_result/NATIVE_QUALIFICATION.json','GATE6_DYNAMIC_CHECKS.json','GATE6_DYNAMIC_DETAIL.json','GATE6_EXPORT_READBACK.json','GATE6_INPUT_LOCK.json']}
    progress('metadata_finalization')
    result=finalize(parent,out/'gate6_baseline_3h_validation_solved.nc',q,checks,detail,exported,refs)
    write(out/'GATE6_METADATA_RECONCILIATION.json',result)
    return dict(result,qualification=q,dynamic_checks='PASS',export_readback='PASS',scientific_results_allowed=False)
