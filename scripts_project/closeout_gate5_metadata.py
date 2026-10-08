"""Evidence-gated metadata-only derivative. No model build or solver calls.

Run only AFTER native qualification, dynamic checks and exact export/readback
have completed. Keep the accepted source NetCDF and all receipts immutable.
"""
import argparse,copy,gc,hashlib,json,os,shutil
from pathlib import Path
from unittest.mock import patch
import netCDF4,numpy as np

ACCOUNTING_KEYS=('PricedObjective','KnownFixedCostIncludedInPricedObjective','KnownFixedCostToAddToPricedObjective')
RECEIPTS=('native_result/NATIVE_QUALIFICATION.json','GATE5_DYNAMIC_CHECKS.json','GATE5_DYNAMIC_DETAIL.json',
          'EXPORT_RECOVERY_RESULT.json','CLOUD_GATE5_RUN_MANIFEST.json','EXIT_STATUS.json')

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()

def read(path):return json.loads(Path(path).read_text())

def require(ok,message):
    if not ok:raise ValueError(message)

def verified_evidence(folder,parent):
    folder=Path(folder);index=read(folder/'RECOVERY_RESULT_SHA256.json')
    delivery=read(folder/'DELIVERY_MANIFEST.json')
    require(sha(folder/'RECOVERY_RESULT_SHA256.json')==delivery['source_result_index_sha256'],'Evidence index changed')
    for rel in RECEIPTS:require(sha(folder/rel)==index['files'][rel],'Receipt hash mismatch: '+rel)
    q,checks,detail,recovery,run,exit_status=[read(folder/p) for p in RECEIPTS]
    digest=sha(parent)
    require(digest==run['result_sha256']==recovery['export']['sha256']==index['files'][Path(parent).name],'Parent network hash mismatch')
    require(q['model_status']=='Optimal' and q['network_writeback_qualified'] is True and q['native_getSolution_calls']==1,'Native qualification failed')
    require(run['gate5_pass'] is True and run['solver_runs']==1 and run['dynamic_checks']=='PASS' and run['export_roundtrip']=='PASS','Run acceptance failed')
    require(recovery['status']=='PASS' and recovery['solver_runs']==0 and recovery['native_getSolution_calls']==0 and recovery['export']['status']=='PASS','Recovery acceptance failed')
    require(exit_status['exit_code']==0,'Recovery exit failed')
    require(checks and len(checks)==recovery['dynamic_check_count'] and all(r['Status']=='PASS' for r in checks),'Existing dynamic evidence failed')
    require(any('OBJECTIVE_RECONCILIATION' in r['Check'] and r['Status']=='PASS' for r in checks),'No accepted objective reconciliation')
    require(detail['objective_reconciliation']==recovery['objective_reconciliation'],'Objective receipts differ')
    require(q['objective']==run['objective']==detail['objective_reconciliation']['actual'],'Qualified objective differs')
    return dict(qualification=q,checks=checks,detail=detail,recovery=recovery,run=run),{rel:dict(path=str((folder/rel).resolve()),sha256=sha(folder/rel)) for rel in RECEIPTS}

def reconcile_metadata(original,objective,evidence,references,parent_sha):
    m=copy.deepcopy(original);report=evidence['detail']['accounting_report'];old=m['accounting_report']
    require(set(old)==set(report),'Accounting schema changed')
    for key in old:
        if key not in ACCOUNTING_KEYS:require(old[key]==report[key],'Unexpected accounting difference: '+key)
    require(np.isfinite(objective) and objective==report['PricedObjective']==evidence['qualification']['objective'],'Stored objective mismatch')
    require(report['KnownFixedCostIncludedInPricedObjective'] is True and report['KnownFixedCostToAddToPricedObjective']==0.,'FOM not verified once')
    require(report['KnownFixedCost']==evidence['detail']['objective_reconciliation']['known_fixed_once'],'FOM receipts differ')
    for key in ['scientific_results_allowed','formal_phase5_allowed','gate6_allowed','policy_enabled','FullSystemCostComplete','FullSystemEmissionsComplete','full_system_cost_complete','full_system_emissions_complete','solver_allowed']:
        require(m[key] is False,'Boundary must remain false: '+key)
    require(len(m['external_pending_fixed_accounts'])==807,'Frozen pending-account count changed')
    require(sum(x['policy_weight'] is None for x in m['physical_carbon_map'])==200,'Frozen pending-policy weights changed')
    require(all(x['UnitPriceEUR2020PerMWh'] is None for x in old['PendingFixedCostTerms']),'Unknown fixed prices changed')
    require(all(x['PhysicalCO2_tPerMWh'] is None for x in old['PendingFixedPhysicalEmissions']),'Unknown fixed emissions changed')
    require('current_result_qualification' not in m,'Already closed metadata requires a new explicit lineage decision')
    inherited=['artifact_role','asset_role','source_is_solved','reference_source_is_solved','input_only_extraction','static_validation',
               'gate5_allowed','ready_for_gate5_reduced_validation_solve','parent_gate4_sha256','temporal_reduction']
    m['parent_input_and_delivery_state']=dict(parent_delivery_sha256=parent_sha,parent_metadata_sha256=hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),
        inherited_state={k:copy.deepcopy(original[k]) for k in inherited if k in original},
        prior_accounting_state={k:old[k] for k in ACCOUNTING_KEYS},
        meaning='Inherited source/static facts describe the frozen input and prior delivery, not current result qualification.')
    for key in ACCOUNTING_KEYS:m['accounting_report'][key]=report[key]
    m.update(artifact_role='GATE5_VALIDATION_SOLVED_DYNAMIC_VALIDATED',validation_checks_passed=True,
             gate5_allowed=False,ready_for_gate5_reduced_validation_solve=False)
    r=evidence['recovery']
    m['current_result_qualification']=dict(status='PASS',native_status=evidence['qualification']['model_status'],
        dynamic_status=evidence['run']['dynamic_checks'],dynamic_check_count=len(evidence['checks']),
        export_readback_status=r['export']['status'],compared_nonempty_frames=r['export']['compared_nonempty_frames'],
        parent_delivery_sha256=parent_sha,source_run_id=r['source_run_id'],source_solve_code_sha=r['source_solve_code_sha'],
        postsolve_code_sha=r['postsolve_code_sha'],frozen_input_sha256=r['input_sha256'],receipts=references,
        metadata_only_derivative=True,additional_solver_calls=0,additional_presolve_calls=0,additional_getSolution_calls=0,
        prior_one_solve_authorization_consumed=True,new_solve_authorized=False,gate6_authorized=False,formal_phase5_authorized=False)
    return m

def value_digest(value):
    a=np.asarray(value);h=hashlib.sha256();h.update(str(a.dtype).encode());h.update(str(a.shape).encode())
    if a.dtype.kind in 'OUS':h.update(json.dumps(a.tolist(),ensure_ascii=False,default=str).encode())
    else:
        a=a.copy()
        if a.dtype.kind=='f':a[np.isnan(a)]=np.nan
        h.update(a.tobytes(order='C'))
    return h.hexdigest()

def netcdf_science_signature(path):
    """All names/order/dtypes/values/dimensions/attrs, excluding only root meta."""
    with netCDF4.Dataset(path) as ds:
        ds.set_auto_maskandscale(False)
        require(not ds.groups,'Unexpected grouped network format')
        result=dict(dimensions=[(k,len(v),v.isunlimited()) for k,v in ds.dimensions.items()],
            attrs=[(k,value_digest(ds.getncattr(k))) for k in ds.ncattrs() if k!='meta'],variables=[])
        for name,v in ds.variables.items():
            chunks=[value_digest(v[...])] if not v.ndim else [value_digest(v[i:i+32]) for i in range(0,v.shape[0],32)]
            result['variables'].append(dict(name=name,dtype=str(v.dtype),dimensions=v.dimensions,shape=v.shape,
                attrs=[(k,value_digest(v.getncattr(k))) for k in v.ncattrs()],chunks=chunks))
        return result

def network_signatures(path):
    import pypsa
    from finish_gate5_lossless import frame_signature
    n=pypsa.Network(path)
    signatures={'snapshot_weightings':frame_signature(n.snapshot_weightings)}
    for c in n.iterate_components():
        # Static tables have mixed object columns; never hash object pointers.
        table=dict(index=value_digest(c.df.index.to_numpy()),columns=value_digest(c.df.columns.to_numpy()),
                   dtypes=list(c.df.dtypes.astype(str)),values=[value_digest(c.df[k].to_numpy()) for k in c.df])
        signatures[c.name+'.static']=hashlib.sha256(json.dumps(table,sort_keys=True).encode()).hexdigest()
        for attr,frame in c.pnl.items():
            if not frame.empty:signatures[c.name+'.'+attr]=frame_signature(frame)
    del n;gc.collect()
    return signatures

def closeout(parent,evidence_folder,output):
    import highspy
    parent=Path(parent);output=Path(output);temporary=output.with_name(output.stem+'.partial.nc')
    require(not output.exists() and not temporary.exists(),'Refuse to overwrite an existing output')
    evidence,refs=verified_evidence(evidence_folder,parent);parent_sha=sha(parent)
    with netCDF4.Dataset(parent) as n:
        old=json.loads(n.getncattr('meta'));objective=float(n.getncattr('network_objective'))
    updated=reconcile_metadata(old,objective,evidence,refs,parent_sha)
    expected=netcdf_science_signature(parent)
    try:
        with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO SOLVER')) as run,patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')) as pre,patch.object(highspy.Highs,'getSolution',side_effect=AssertionError('NO SOLUTION RETRIEVAL')) as get:
            before=network_signatures(parent)
            shutil.copy2(parent,temporary)
            with netCDF4.Dataset(temporary,'r+') as n:n.setncattr('meta',json.dumps(updated,ensure_ascii=False,allow_nan=False))
            require(netcdf_science_signature(temporary)==expected,'Scientific NetCDF arrays or non-meta attributes changed')
            after=network_signatures(temporary);require(before==after,'Existing PyPSA frame signatures changed')
            with netCDF4.Dataset(temporary) as n:require(json.loads(n.getncattr('meta'))==updated,'Metadata readback changed')
            require(sha(parent)==parent_sha,'Parent changed')
            require(run.call_count==pre.call_count==get.call_count==0,'Forbidden native API call')
        require(not output.exists(),'Output appeared during verification');temporary.rename(output)
    finally:
        if temporary.exists():temporary.unlink()
    changes={k:dict(before=old.get(k),after=updated[k]) for k in updated if old.get(k)!=updated[k]}
    # The full accounting ledger is preserved; keep this receipt small and explicit.
    changes['accounting_report']={k:dict(before=old['accounting_report'][k],after=updated['accounting_report'][k]) for k in ACCOUNTING_KEYS}
    return dict(status='PASS',parent_path=str(parent),parent_sha256=parent_sha,derived_path=str(output),derived_sha256=sha(output),
        changes=changes,scientific_data_unchanged=True,netcdf_variables_compared=len(expected['variables']),
        network_frame_count=len(before),frame_signatures=before,netcdf_science_signature_sha256=hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest(),
        objective_before=objective,objective_after=objective,existing_dynamic_receipts_reused=True,dynamic_checks_reexecuted=0,
        solver_calls=0,presolve_calls=0,getSolution_calls=0,model_builds=0,original_evidence_preserved=True,
        qualification_receipts=refs,scientific_results_allowed=False,FullSystemCostComplete=False,FullSystemEmissionsComplete=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--evidence',required=True);p.add_argument('--output',required=True);p.add_argument('--receipt',required=True);a=p.parse_args()
    require(not Path(a.receipt).exists(),'Receipt already exists')
    result=closeout(a.parent,a.evidence,a.output)
    Path(a.receipt).write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['changes','frame_signatures','qualification_receipts']},indent=2))
