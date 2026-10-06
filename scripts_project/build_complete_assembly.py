"""Apply explicit stock completeness boundary and prepare complete unsolved inputs.

Reuses the frozen input-only electric asset; regenerates unbound carrier recipe
for changed demands. No solved capacities, dispatch or optimization variables.
"""
from pathlib import Path
from copy import deepcopy
import argparse,json,hashlib,shutil,subprocess
from final_closure_inputs import read,save,sha,DECISION,STOCK

def qualify_stock(n,stock,contract):
    identities=n.meta['existing_unit_components'];byid={r['AssetID']:r for r in stock['unit_evidence']['records']}
    if len(byid)!=len(stock['unit_evidence']['records']):raise ValueError('Duplicate source-unit identity')
    for ident,z in identities.items():
        r=byid[ident]
        if r['SurvivalStatus']!='SURVIVES_2050' or r['RetainedCapacity2050']!=z['capacity_mw']:raise ValueError('Inherited unit is not a qualified survivor')
        row=n.df(z['component_type']).loc[z['component']]
        if row.asset_role!='existing_survivor' or row.p_nom_extendable or row.capital_cost!=0:raise ValueError('Existing role/cost altered')
    hydro=contract['hydro_group_qualification']['groups'];pending={u for g in hydro if g['Status']=='PENDING' for u in g['SourceUnitIDs']}
    if pending&set(identities):raise ValueError('Unqualified hydro resource inherited')
    known_duplicates={r['AssetID'] for r in byid.values() if 'DUPLICATE' in r.get('SurvivalStatus','')}
    unresolved=[]
    for ident,r in byid.items():
        if ident in identities or r['SurvivalStatus']=='NOT_ACTIVE_2050' or ident in known_duplicates:continue
        if not (r['SurvivalStatus'].startswith('UNRESOLVED') or r['SurvivalStatus']=='SURVIVES_2050'):continue
        unresolved.append(dict(AssetSourceGroup=ident,SourceFamily=ident.split(':')[0],Country=r['Country'],Technology=r['Technology'],PotentialCapacityMW=r['OriginalCapacity'],ReasonUnresolved='UNRESOLVED_HYDRO_RESOURCE_STOCK' if ident in pending else r['SurvivalStatus']+'; '+str(r.get('IdentityReview','performance/resource qualification not complete')),PossibleOverlapWithQualifiedStock='POSSIBLE_UNTIL_IDENTITY_ESTABLISHED' if ident.startswith('GPD:') else 'Source IDs distinct; cross-source overlap retained separately',MissingEvidence='Compatible accepted natural resource input' if ident in pending else 'Identity/status/year/capacity/performance/resource contract as applicable; see preserved source record',AssemblyV1Treatment='UNRESOLVED_EXISTING_STOCK_NOT_INHERITED_IN_ASSEMBLY_V1',FutureSensitivityRole='PHASE5_OR_LATER_STOCK_COVERAGE_SENSITIVITY',HistoricalSurvivalStatus=r['SurvivalStatus'],HistoricalRetainedCapacity2050=r.get('RetainedCapacity2050'),Source=r['Source'],SourceVersion=r['SourceVersion'],DecisionReference=DECISION+'#C'))
    return dict(method=STOCK,DecisionReference=DECISION+'#C',qualified_source_units=len(identities),qualified_capacity_mw=sum(z['capacity_mw'] for z in identities.values()),records=unresolved,hydro_groups_not_inherited=[deepcopy(g) for g in hydro if g['Status']=='PENDING'],GEM_GPD_NOT_ADDITIVE=True,MissingIsZero=False,QualifiedUnitIDs=sorted(identities))

def prepare(repo,source_assets,allocation,output,costs):
    import pypsa
    from build_diagnostic_network import assert_input_only
    from build_research_assets import build_fragment
    from assembly_components import validate_hooks
    from netCDF4 import Dataset
    decisions=read(repo/'research_inputs/assembly_v1/sources/ASSEMBLY_V1_FINAL_DECISIONS.json')
    if decisions['DecisionReference']!=DECISION or decisions['Decisions']['C']!=STOCK:raise ValueError('Stock boundary not authorized')
    output.mkdir(parents=True,exist_ok=True)
    base_path=source_assets/'electric_base_2050_unsolved.nc'
    for name in ['electric_base_2050_unsolved.nc','SELECTED_ASSET_SURVIVAL_2050.json','SELECTED_INTEGRATION_CONTRACT.json']:
        rel='results_project/assembly_v1/assets/'+name
        if sha(source_assets/name)!=decisions['SourcePins'][rel]:raise ValueError('Frozen qualified stock source changed')
        shutil.copyfile(source_assets/name,output/name)
    for name in ['model_cost_layer.json','ELECTRIC_BASE_ASSET_MANIFEST.json']:shutil.copyfile(source_assets/name,output/name)
    n=pypsa.Network(base_path);assert_input_only(n);validate_hooks(n)
    uncertainty=qualify_stock(n,read(output/'SELECTED_ASSET_SURVIVAL_2050.json'),read(output/'SELECTED_INTEGRATION_CONTRACT.json'))
    save(output/'existing_stock_uncertainty.json',uncertainty)
    prior_meta=deepcopy(n.meta)
    n.meta.update(asset_role='SOURCE_QUALIFIED_ELECTRIC_BASE_UNSOLVED',asset_qualification='SOURCE_QUALIFIED_ELECTRIC_BASE_UNSOLVED',existing_stock_boundary=STOCK,stock_boundary_decision=DECISION+'#C',stock_uncertainty=uncertainty,resource_occupancy_status='QUALIFIED_INHERITED_STOCK_ONLY_UNRESOLVED_OUTSIDE_V1',unresolved_existing_asset_ages=0,unresolved_existing_assets_outside_v1=len(uncertainty['records']))
    n.meta['historical_stock_qualification']=dict(unresolved_existing_asset_ages=prior_meta['unresolved_existing_asset_ages'],prior_asset_role=prior_meta['asset_role'])
    n.meta['qualification_dimensions'].update(physical_integrity='QUALIFIED_STOCK_BOUNDARY_APPLIED',input_coverage='FINAL_COMBINED_VALIDATION_REQUIRED')
    with Dataset(output/'electric_base_2050_unsolved.nc','a') as ds:ds.setncattr('meta',json.dumps(n.meta))
    current=pypsa.Network(output/'electric_base_2050_unsolved.nc')
    from refresh_diagnostic_qualification import compare_physical,save_legacy_manifest
    compare_physical(n,current)
    manifest=read(output/'ELECTRIC_BASE_ASSET_MANIFEST.json');manifest.update(status='SOURCE_QUALIFIED_ELECTRIC_BASE_UNSOLVED',sha256=sha(output/'electric_base_2050_unsolved.nc'),stock_boundary=dict(method=STOCK,DecisionReference=DECISION+'#C',uncertainty_file='existing_stock_uncertainty.json',sha256=sha(output/'existing_stock_uncertainty.json'),code_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),physical_components_changed=False))
    save_legacy_manifest(output/'ELECTRIC_BASE_ASSET_MANIFEST.json',manifest)
    f=build_fragment(repo,current,costs,allocation,output,output/'model_cost_layer.json')
    save(output/'asset_bundle.json',dict(status='SOURCE_QUALIFIED_2050_UNSOLVED',source_is_solved=False,solver_allowed=False,stock_boundary=STOCK,stock_boundary_decision=DECISION+'#C',electric_base=dict(file='electric_base_2050_unsolved.nc',sha256=sha(output/'electric_base_2050_unsolved.nc')),carrier_fragment=dict(file='carrier_fragment.json',sha256=f['files']['carrier_fragment.json']),carbon_map=dict(file='carbon_component_map.json',sha256=f['files']['carbon_component_map.json']),external_fixed_accounts=dict(file='external_pending_fixed_accounts.json',sha256=sha(output/'external_pending_fixed_accounts.json')),accounting=dict(file='accounting_qualification.json',sha256=sha(output/'accounting_qualification.json')),price_layer=dict(file='model_cost_layer.json',sha256=sha(output/'model_cost_layer.json')),stock_uncertainty=dict(file='existing_stock_uncertainty.json',sha256=sha(output/'existing_stock_uncertainty.json')),registry_sha256=sha(repo/'research_inputs/assembly_v1/registry.json'),allocation_manifest_sha256=sha(allocation/'allocation_manifest.json')))
    return uncertainty
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['repo','source-assets','allocation','output','costs']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z=prepare(**vars(a));print(json.dumps({k:v for k,v in z.items() if k not in ['records','hydro_groups_not_inherited','QualifiedUnitIDs']}))
