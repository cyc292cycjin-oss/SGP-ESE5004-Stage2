"""Synthetic metadata/serialization gates only; no physical validation claim."""
import copy,json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
import highspy,netCDF4,numpy as np,pandas as pd,pypsa
from closeout_gate5_metadata import closeout,sha,netcdf_science_signature,verified_evidence
from finish_gate5_lossless import export_complete_timeseries

def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v)+'\n')
def fixture(folder):
 n=pypsa.Network();n.set_snapshots(pd.date_range('2050-01-01',periods=2,freq='h'));n.add('Bus','b')
 for name in ['z','零']:n.add('Generator',name,bus='b',p_nom=2.)
 n.generators_t.p=pd.DataFrame([[np.nextafter(1.,2.),-0.],[2.,-0.]],index=n.snapshots,columns=n.generators.index)
 n.generators['p_nom_opt']=[1.,2.];n.objective=12.5
 report=dict(PricedObjective=None,KnownFixedCost=2.,KnownFixedCostIncludedInPricedObjective=None,KnownFixedCostToAddToPricedObjective=None,
  FullSystemCostComplete=False,FullSystemEmissionsComplete=False,PendingFixedCostTerms=[dict(FixedAccountID=str(i),UnitPriceEUR2020PerMWh=None) for i in range(807)],
  PendingFixedPhysicalEmissions=[dict(FixedAccountID=str(i),PhysicalCO2_tPerMWh=None) for i in range(807)])
 n.meta=dict(artifact_role='GATE5_VALIDATION_SOLVED_DYNAMIC_PENDING',accounting_report=report,external_pending_fixed_accounts=[dict(id=i) for i in range(807)],
  physical_carbon_map=[dict(policy_weight=None) for _ in range(200)],static_validation=dict(status='PASS',optimization_variables_created=False),
  gate5_allowed=True,ready_for_gate5_reduced_validation_solve=True,source_is_solved=False,asset_role='SOURCE_UNSOLVED',**{k:False for k in ['scientific_results_allowed','formal_phase5_allowed','gate6_allowed','policy_enabled','FullSystemCostComplete','FullSystemEmissionsComplete','full_system_cost_complete','full_system_emissions_complete','solver_allowed']})
 parent=folder/'source.nc';export_complete_timeseries(n,parent)
 report=copy.deepcopy(report);report.update(PricedObjective=12.5,KnownFixedCostIncludedInPricedObjective=True,KnownFixedCostToAddToPricedObjective=0.)
 q=dict(model_status='Optimal',network_writeback_qualified=True,native_getSolution_calls=1,objective=12.5)
 checks=[dict(Check='OBJECTIVE_RECONCILIATION_KNOWN_FOM_ONCE',Status='PASS')]
 detail=dict(accounting_report=report,objective_reconciliation=dict(capital=3.,variable=7.5,known_fixed_once=2.,actual=12.5))
 recovery=dict(status='PASS',solver_runs=0,native_getSolution_calls=0,dynamic_check_count=1,objective_reconciliation=detail['objective_reconciliation'],
  export=dict(status='PASS',sha256=sha(parent),compared_nonempty_frames=1),source_run_id='SYNTHETIC_ONLY',source_solve_code_sha='mock-solve',postsolve_code_sha='mock-export',input_sha256='mock-input')
 run=dict(result_sha256=sha(parent),gate5_pass=True,solver_runs=1,dynamic_checks='PASS',export_roundtrip='PASS',objective=12.5)
 for rel,value in [('native_result/NATIVE_QUALIFICATION.json',q),('GATE5_DYNAMIC_CHECKS.json',checks),('GATE5_DYNAMIC_DETAIL.json',detail),('EXPORT_RECOVERY_RESULT.json',recovery),('CLOUD_GATE5_RUN_MANIFEST.json',run),('EXIT_STATUS.json',dict(exit_code=0))]:put(folder/rel,value)
 reindex(folder)
 return parent
def reindex(folder):
 files={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file() and p.name not in ['RECOVERY_RESULT_SHA256.json','DELIVERY_MANIFEST.json']}
 put(folder/'RECOVERY_RESULT_SHA256.json',dict(files=files))
 put(folder/'DELIVERY_MANIFEST.json',dict(source_result_index_sha256=sha(folder/'RECOVERY_RESULT_SHA256.json')))
def expect_failure(fn):
 try:fn()
 except ValueError:return
 raise AssertionError('Expected fail-closed rejection')
def run_tests():
 checks=[]
 with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')),patch.object(highspy.Highs,'getSolution',side_effect=AssertionError('NO RETRIEVAL')):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);source=fixture(base);digest=sha(source);out=base/'derived.nc'
   result=closeout(source,base,out);assert result['status']=='PASS' and sha(source)==digest
   assert netcdf_science_signature(source)==netcdf_science_signature(out)
   with netCDF4.Dataset(out) as ds:m=json.loads(ds.meta)
   assert m['accounting_report']['PricedObjective']==12.5 and m['accounting_report']['KnownFixedCostIncludedInPricedObjective'] is True
   assert not m['gate5_allowed'] and not m['gate6_allowed'] and not m['formal_phase5_allowed']
   assert m['source_is_solved'] is False and m['asset_role']=='SOURCE_UNSOLVED' and m['static_validation']==m['parent_input_and_delivery_state']['inherited_state']['static_validation']
   checks.append('only_current_status_updated_science_signed_zero_dtype_order_and_parent_unchanged')
   expect_failure(lambda:closeout(source,base,out));checks.append('existing_output_never_overwritten')
   # Receipt tampering must fail before any derivative exists.
   p=base/'GATE5_DYNAMIC_CHECKS.json';put(p,[dict(Check='OBJECTIVE_RECONCILIATION',Status='FAIL')])
   expect_failure(lambda:closeout(source,base,base/'bad.nc'));assert not (base/'bad.nc').exists();checks.append('tampered_receipt_rejected')
   reindex(base);expect_failure(lambda:closeout(source,base,base/'bad.nc'));checks.append('hashed_failed_dynamic_receipt_rejected')
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);source=fixture(base);p=base/'GATE5_DYNAMIC_DETAIL.json';d=json.loads(p.read_text());d['accounting_report']['KnownFixedCostIncludedInPricedObjective']=False;put(p,d);reindex(base)
   expect_failure(lambda:closeout(source,base,base/'bad.nc'));checks.append('FOM_relation_not_inferred_or_added_twice')
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);source=fixture(base);import closeout_gate5_metadata as module
   actual=module.netcdf_science_signature;calls=0
   def corrupted_signature(path):
    nonlocal calls
    calls+=1
    if str(path).endswith('.partial.nc'):
     with netCDF4.Dataset(path,'r+') as ds:ds.variables['generators_t_p'][0,0]=np.nextafter(ds.variables['generators_t_p'][0,0],np.inf)
    return actual(path)
   with patch.object(module,'netcdf_science_signature',corrupted_signature):expect_failure(lambda:closeout(source,base,base/'bad.nc'))
   assert not (base/'bad.nc').exists() and not (base/'bad.partial.nc').exists();checks.append('one_ULP_change_rejected_no_valid_looking_partial_left')
 return dict(status='PASS',scope='SYNTHETIC_METADATA_ENGINEERING_ONLY',checks=checks,solver_calls=0,presolve_calls=0,getSolution_calls=0,model_builds=0)
if __name__=='__main__':Path(sys.argv[1]).write_text(json.dumps(run_tests(),indent=2)+'\n')
