"""Update a qualified inventory interpretation and NetCDF metadata, never rebuild.

Physical tables, time series, demand arrays and production registry are invariant.
"""
from pathlib import Path
from collections import Counter
import argparse,copy,json,subprocess,hashlib,shutil
import pypsa,pandas as pd
from netCDF4 import Dataset
from asset_lifetime_override import load_overrides,apply_override,FILE as OVERRIDE_FILE
from asset_survival import select_asset
from build_diagnostic_network import current_readiness,verify_guards,normalise_optional_strings
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save_legacy_manifest(p,x):
 # Existing manifests contain IEEE Infinity for inherited unbounded candidate
 # limits. Preserve that established representation; do not turn it into zero/null.
 Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=True)+'\n')
def change_meta(path,meta):
 with Dataset(path,'a') as ds:ds.setncattr('meta',json.dumps(meta,ensure_ascii=False,allow_nan=False))
def meta(path):
 with Dataset(path) as ds:return json.loads(ds.getncattr('meta'))
def compare_physical(old,new):
 normalise_optional_strings(old);normalise_optional_strings(new)
 if set(old.buses.index)!=set(new.buses.index):raise ValueError('Bus ownership set changed')
 for comp in old.iterate_components():
  a,b=comp.df,new.df(comp.name)
  if set(a.index)!=set(b.index) or set(a.columns)!=set(b.columns):raise ValueError('Component set changed')
  pd.testing.assert_frame_equal(a.sort_index().sort_index(axis=1),b.sort_index().sort_index(axis=1),check_dtype=False,check_names=False,check_exact=True)
  for attr,frame in comp.pnl.items():
   other=new.pnl(comp.name)[attr]
   pd.testing.assert_frame_equal(frame.sort_index().sort_index(axis=1),other.sort_index().sort_index(axis=1),check_dtype=False,check_names=False,check_freq=False,check_exact=True)
 pd.testing.assert_frame_equal(old.snapshot_weightings.sort_index(),new.snapshot_weightings.sort_index(),check_exact=True,check_freq=False)
 return True
def refresh(repo,prior,output):
 root=repo/'results_project/assembly_v1';a=root/'assets';g=repo/'research/04_model_assembly/gate4';output.mkdir(parents=True,exist_ok=True)
 original=read(a/'SELECTED_ASSET_SURVIVAL_2050.json');expected=read(prior/'production_assets/SELECTED_ASSET_SURVIVAL_2050.json');assert original==expected,'Unknown stock drift or refresh already applied'
 protected=[repo/'research_inputs/assembly_v1/registry.json',repo/'research_inputs/assembly_v1/manifest.json',root/'allocation/allocations.npz',root/'allocation/allocation_manifest.json',a/'SELECTED_INTEGRATION_CONTRACT.json',a/'carrier_fragment_2050_unsolved.nc',a/'carrier_fragment.json',a/'carbon_component_map.json',a/'external_pending_fixed_accounts.json',a/'model_cost_layer.json']
 before_hash={str(p):sha(p) for p in protected};decisions=load_overrides(repo);stock=copy.deepcopy(original);changes=[]
 for i,u in enumerate(stock['unit_evidence']['records']):
  updated=apply_override(u,decisions)
  if updated==u:continue
  z=select_asset(updated)
  if u['RetainedCapacity2050'] not in [None,0] or z['RetainedCapacity2050']!=0:raise ValueError('Metadata refresh cannot change actual integrated capacity')
  stock['unit_evidence']['records'][i]=z;changes.append(dict(AssetID=u['AssetID'],Before=u,After=z))
 if not changes:raise ValueError('No authorised inventory qualification change')
 stock['unit_evidence']['status_counts']=dict(Counter(u['SurvivalStatus'] for u in stock['unit_evidence']['records']));stock['asset_specific_lifetime_decisions']=decisions;stock['selected_closure_inputs'][str(repo/OVERRIDE_FILE)]=sha(repo/OVERRIDE_FILE)
 save(output/'STOCK_BEFORE.json',original);save(a/'SELECTED_ASSET_SURVIVAL_2050.json',stock)
 reportpath=a/'SELECTED_CLOSURE_IMPLEMENTATION.json';review=read(reportpath);save(output/'SELECTED_IMPLEMENTATION_BEFORE.json',review)
 for c in changes:
  r=next(x for x in review['gpd'] if x['AssetID']==c['AssetID']);z=c['After'];r.update(Lifetime=z['Lifetime'],ConditionalSurvivingMW=z['RetainedCapacity2050'],FinalSelectionStatus=z['SurvivalStatus'],PendingReason='Outside2050 under accepted historicalAvion25y proxy, not an observed retirement',LifetimeDecisionReference=z['LifetimeDecisionReference'],LifetimeMethodID=z['LifetimeMethodID'])
 review['asset_specific_lifetime_changes']=changes;review['inputs']=stock['selected_closure_inputs'];save(reportpath,review)
 currentpath=g/'CURRENT_GATE4_SELECTED_MANIFEST.json';cm=read(currentpath);save(output/'CURRENT_MANIFEST_BEFORE.json',cm)
 cm.update(base_git_commit='6d81675909bb94dba8d2317fd8c642258c5193a8',current_lifetime_decision=OVERRIDE_FILE,source_recovery='No new downloads. Prior originalUN tables recovered, reporting status unresolved. Ten compatiblememo-pair envelopes are analysis only.',technology_update='Avion remains OCGT100MW, dependable97 separately;25y2016cohort proxy yields2041model retirement, no2050 inherited stock; no performance/OM approval',new_original_documents=[],new_existing_capacity_mw=0,new_numeric_demand_accounts=0)
 save(currentpath,cm)
 unresolved=sum(u['SurvivalStatus'].startswith('UNRESOLVED') for u in stock['unit_evidence']['records']);producer=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
 basepath=a/'electric_base_2050_unsolved.nc';oldbase=pypsa.Network(basepath);oldbasehash=sha(basepath);bm=meta(basepath);bm['unresolved_existing_asset_ages']=unresolved;bm['inventory_qualification_refresh']=dict(method=decisions['records'][0]['MethodID'],code_sha=producer,physical_inputs_changed=False,prior_network_sha256=oldbasehash);change_meta(basepath,bm);newbase=pypsa.Network(basepath);compare_physical(oldbase,newbase)
 bundlepath=a/'asset_bundle.json';bundle=read(bundlepath);save(output/'ASSET_BUNDLE_BEFORE.json',bundle);bundle['electric_base']['sha256']=sha(basepath);save(bundlepath,bundle)
 for name in ['ELECTRIC_BASE_ASSET_MANIFEST.json','GATE3_PRODUCTION_FRAGMENT_MANIFEST.json']:
  path=a/name;m=read(path);shutil.copyfile(path,output/('PRIOR_'+name));oldinputs=copy.deepcopy(m['inputs'])
  for rel in list(m['inputs']):
   p=Path(rel);p=p if p.is_absolute() else repo/p;m['inputs'][rel]=sha(p)
  m['qualification_refresh']=dict(code_sha=producer,method=decisions['records'][0]['MethodID'],old_build_code_sha=m['code_sha'],original_build_inputs=oldinputs,prior_delivery=str(prior),original_manifest_sha256=sha(output/('PRIOR_'+name)),inputs_meaning='Current effective source/qualification pins after metadata refresh; original physical-build inputs retained above',physical_components_rebuilt=False,current_unresolved_units=unresolved)
  if name.startswith('ELECTRIC'):
   m['sha256']=sha(basepath);m['raw_asset_inventory_summary']['unresolved_unit_records']=unresolved;m['inputs'][OVERRIDE_FILE]=sha(repo/OVERRIDE_FILE)
  save_legacy_manifest(path,m)
 state,_,_=current_readiness(repo,root/'allocation',a);readiness=root/'CURRENT_PHYSICAL_READINESS.json';save(readiness,state)
 diagpath=root/'research_2050_diagnostic_partial_unsolved.nc';priorhash=sha(diagpath);oldnet=pypsa.Network(diagpath);verify_guards(oldnet);dm=meta(diagpath)
 dm['unresolved_existing_asset_ages']=unresolved;dm['inventory_qualification_refresh']=bm['inventory_qualification_refresh'];scope=dm['unmaterialised_scope'];scope.update(readiness_sha256=sha(readiness),inventory_scopes=state['inventory_scopes'],source_reporting_status=state['source_reporting_status'])
 change_meta(diagpath,dm);newnet=pypsa.Network(diagpath);verify_guards(newnet);compare_physical(oldnet,newnet)
 assert dm==newnet.meta,'Metadata failed readback'
 manifestpath=root/'DIAGNOSTIC_NETWORK_MANIFEST.json';m=read(manifestpath);save(output/'DIAGNOSTIC_MANIFEST_BEFORE.json',m)
 m.update(network_sha256=sha(diagpath),readiness_sha256=sha(readiness),source_pins=state['source_pins'],asset_bundle_sha256=sha(bundlepath),asset_inputs={k:bundle[k] for k in m['asset_inputs']},qualification_refresh=dict(code_sha=producer,physical_assembly_code_sha=m['code_sha'],prior_network_sha256=priorhash,inventory_changes=[c['AssetID'] for c in changes],operation='NETCDF_METADATA_ONLY_NO_COMPONENT_REBUILD',physical_inputs_bitwise_equal_by_named_components=True,optimization_variables_created=False,prior_checks='Physical checks retained for unchanged inputs; updated guards/inventory/meta revalidated this round'))
 save(manifestpath,m)
 assert all(sha(Path(p))==h for p,h in before_hash.items()),'Protected demand/price/resource/fragment data changed'
 assert state['pending_physical_targets']==read(prior/'diagnostic_network/CURRENT_PHYSICAL_READINESS.json')['pending_physical_targets']
 for name in ['CURRENT_PHYSICAL_READINESS.json','DIAGNOSTIC_NETWORK_MANIFEST.json']:shutil.copyfile(root/name,output/name)
 save(output/'QUALIFICATION_REFRESH_RECEIPT.json',dict(code_sha=producer,changes=changes,unresolved_units_before=sum(u['SurvivalStatus'].startswith('UNRESOLVED') for u in original['unit_evidence']['records']),unresolved_units_after=unresolved,physical_inputs_equal_by_names=True,protected_file_hashes=before_hash,old_base_network_sha256=oldbasehash,new_base_network_sha256=sha(basepath),old_diagnostic_sha256=priorhash,new_diagnostic_sha256=sha(diagpath),component_rebuilds=0,solver_runs=0,source_qualified_input_count=state['qualified_demand_accounts'],pending_physical_targets=state['pending_physical_targets']))
 print(json.dumps(dict(changed_inventory=[c['AssetID'] for c in changes],pending_physical_targets=state['pending_physical_targets'],physical_network_rebuilds=0,solver_runs=0,unresolved_units_after=unresolved)))
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ['repo','prior','output']:p.add_argument('--'+n,type=Path,required=True)
 refresh(**vars(p.parse_args()))
