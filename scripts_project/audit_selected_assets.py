"""Actual development-network validation; reads input-only contracts and exports."""
from pathlib import Path
import sys,json,hashlib,subprocess as sp,collections,copy
import numpy as np,pandas as pd,pypsa
import argparse
parser=argparse.ArgumentParser(description='Read-only actual selected-asset regression; NO SOLVER')
for key in ['repo','source-config','prior-delivery','output']:parser.add_argument('--'+key,type=Path,required=True)
args=parser.parse_args();R=args.repo.resolve();A=R/'results_project/assembly_v1/assets';E=args.output.resolve();E.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(R/'scripts_project'))
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
cfg=read(args.source_config);ref=pypsa.Network(cfg['source_reference']);n=pypsa.Network(A/'electric_base_2050_unsolved.nc');f=pypsa.Network(A/'carrier_fragment_2050_unsolved.nc');prior=pypsa.Network(args.prior_delivery/'production_assets/electric_base_2050_unsolved.nc')
contract=read(A/'SELECTED_INTEGRATION_CONTRACT.json');report=read(A/'SELECTED_CLOSURE_IMPLEMENTATION.json');stock=read(A/'SELECTED_ASSET_SURVIVAL_2050.json');identity=n.meta['existing_unit_components'];old=prior.meta['existing_unit_components'];assert set(old)<=set(identity)
for k,r in old.items():assert identity[k]['capacity_mw']==r['capacity_mw'] and identity[k]['node']==r['node']
assert len(identity)==len(set(identity))
new={k:v for k,v in identity.items() if k not in old};capacities=collections.defaultdict(float);units={u['AssetID']:u for u in stock['unit_evidence']['records']}
for k,r in new.items():capacities[units[k]['Technology']]+=r['capacity_mw']
for typ in ['Line','GlobalConstraint']:
 pd.testing.assert_frame_equal(n.df(typ),prior.df(typ))
for k in n.links.index[n.links.carrier.isin(['DC','B2B'])]:
 for attr in ['bus0','bus1','p_nom','p_nom_min','p_nom_max','p_nom_extendable','efficiency','capital_cost','p_min_pu','p_max_pu']:
  a,b=n.links.at[k,attr],prior.links.at[k,attr];assert a==b or pd.isna(a) and pd.isna(b),(k,attr)
 assert n.links.at[k,'marginal_cost']==0
for k in n.generators.index[n.generators.asset_role=='new_build_candidate']:
 for attr in ['capital_cost','marginal_cost','p_nom_max','efficiency','lifetime']:assert n.generators.at[k,attr]==prior.generators.at[k,attr]
# All unchanged hydro groups retain actual input arrays and Emax, not just labels.
affected={u for r in report['hydro'] for u in r['RecipientUnits']}
for k,r in old.items():
 if units[k]['Technology']!='Hydro' or k in affected:continue
 typ=r['component_type'];a=n.df(typ).loc[identity[k]['component']];b=prior.df(typ).loc[r['component']]
 for col in ['p_nom','efficiency','marginal_cost'] if typ=='Generator' else ['p_nom','max_hours','efficiency_store','efficiency_dispatch','cyclic_state_of_charge']:assert a[col]==b[col]
 for attr,df in prior.pnl(typ).items():
  if r['component'] in df:np.testing.assert_array_equal(n.pnl(typ)[attr][identity[k]['component']],df[r['component']])
from selected_closure import validate_allocated_resources,resource_profile
validate_allocated_resources(contract,ref,identity)
resource_checks=[]
for rid in sorted({r['ResourceIdentity'] for r in report['hydro']}):
 rs=[r for r in report['hydro'] if r['ResourceIdentity']==rid];sumv=np.zeros(len(n.snapshots));Emax=0.
 for row in rs:
  u=row['RecipientUnits'][0];p=contract['performance'][u];spec=next(iter(p['Profiles'].values()));t=next(t for t in spec['ResourceTerms'] if t['ResourceIdentity']==rid);v=resource_profile(dict(spec,ResourceTerms=[t],NormalisationMW=1.),ref);sumv+=v;Emax+=row['AllocatedEmaxMWh']
  comp=identity[u];typ=comp['component_type'];name=comp['component'];actual=n.pnl(typ)['p_max_pu' if typ=='Generator' else 'inflow'][name].to_numpy();expected=resource_profile(spec,ref);np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-10)
  if typ=='StorageUnit':assert np.isclose(n.storage_units.at[name,'p_nom']*n.storage_units.at[name,'max_hours'],sum(q['AllocatedEmaxMWh'] for q in report['hydro'] if q['RecipientNode']==row['RecipientNode'] and q['PoolID']==row['PoolID']),rtol=1e-12)
 t=dict(t,AllocationShare=1.);base=resource_profile(dict(spec,ResourceTerms=[t],NormalisationMW=1.),ref)
 np.testing.assert_allclose(sumv,base,rtol=1e-12,atol=1e-8);assert np.isclose(Emax,rs[0]['OriginalEmaxMWh'],rtol=1e-12,atol=1e-8)
 resource_checks.append(dict(ResourceIdentity=rid,MaximumSnapshotErrorMW=float(np.max(abs(sumv-base))),BeforeAnnualMWh=float(base@n.snapshot_weightings.generators.to_numpy()),AfterAnnualMWh=float(sumv@n.snapshot_weightings.generators.to_numpy()),BeforeEmaxMWh=rs[0]['OriginalEmaxMWh'],AfterEmaxMWh=Emax,RoundtripVerified=True))
for r in report['gpd']:
 if r['AssetID'] in identity:r.update(ActualIntegratedMW=identity[r['AssetID']]['capacity_mw'],Component=identity[r['AssetID']]['component'],Node=identity[r['AssetID']]['node'],PendingReason=None)
save(E/'GPD_ACTUAL_REVIEW.json',report['gpd']);save(E/'HYDRO_RESOURCE_ACTUAL_CHECKS.json',resource_checks);save(E/'RETIREMENT_BOUNDS.json',report['retirement_bounds']);save(E/'HYDRO_IMPLEMENTATION.json',report['hydro'])
from fixed_accounts import validate_exported_accounting,accounting_report
validate_exported_accounting(f);assert len(f.loads)==1436;assert len(read(A/'external_pending_fixed_accounts.json'))==471
previous=args.prior_delivery
assert sha(A/'external_pending_fixed_accounts.json')==sha(previous/'production_assets/external_pending_fixed_accounts.json')
oldprice=read(previous/'production_assets/model_cost_layer.json');newprice=read(A/'model_cost_layer.json')
for key in set(oldprice)|set(newprice):
 if key=='source_inputs':
  canonical=lambda d:{str((R/Path(k)).resolve()):v for k,v in d.items()}
  assert canonical(oldprice[key])==canonical(newprice[key])
 else:assert oldprice[key]==newprice[key],key
save(E/'PRICE_LAYER_PRESERVATION.json',dict(all_price_values_identical=True,rows=len(newprice['rows']),all_non_source_path_fields_identical=True,source_paths_resolve_to_same_file_and_hash=True,old_sha256=sha(previous/'production_assets/model_cost_layer.json'),new_sha256=sha(A/'model_cost_layer.json'),change='DAG source path spelling absolute to relative; no numerical conversion'))
assert sha(R/'results_project/assembly_v1/allocation/allocations.npz')==sha(previous/'actual_allocation/allocations.npz')
from allocate_assembly_inputs import verify_allocation
registry=read(R/'research_inputs/assembly_v1/registry.json');verify_allocation(R/'results_project/assembly_v1/allocation',registry['records'],R/'research_inputs/assembly_v1/registry.json')
from rebuild_assembly_targets import derive
assert derive(R/'research_inputs/assembly_v1')['accepted_count']==152
from build_research_network import load_unbound_recipe
recipe=load_unbound_recipe(A/'carrier_fragment.json');assert not any(r['type']=='Load' for r in recipe['components'].values())
carbon=read(A/'carbon_component_map.json');assert sum(r['policy_weight'] is None for r in carbon)==200
assert len({(r['component_type'],r['component']) for r in carbon})==len(carbon)
ft=f.links[f.links.carrier=='Fischer-Tropsch'];assert len(ft)==100
ftvom=next(r['ModelValue'] for r in newprice['rows'] if r['TechnologyYear']==2050 and r['Technology']=='Fischer-Tropsch' and r['Parameter']=='VOM')
np.testing.assert_allclose(ft.marginal_cost,ft.efficiency*float(ftvom),rtol=1e-12)
for typ,table in [('Generator',n.generators),('Link',n.links),('StorageUnit',n.storage_units)]:
 for name,z in table[table.get('asset_role',pd.Series(index=table.index,dtype=str))=='existing_survivor'].iterrows():assert z.capital_cost==0 and z.existing_fixed_om_eur_per_mw_year>0
bound=[r for r in report['retirement_bounds'] if r['Status']=='RETIREMENT_PROVEN_BY_COMMISSIONING_UPPER_BOUND'];unknown=[u for u in stock['unit_evidence']['records'] if u['AssetID'].startswith('GEM:') and u['SurvivalStatus']=='UNRESOLVED_COMMISSIONING']
summary=dict(prior_units=len(old),prior_mw=sum(r['capacity_mw'] for r in old.values()),actual_units=len(identity),actual_mw=sum(r['capacity_mw'] for r in identity.values()),added_units=len(new),added_by_technology_mw=dict(capacities),hydro_total_mw=sum(r['capacity_mw'] for k,r in identity.items() if units[k]['Technology']=='Hydro'),qualified_hydro_groups=sum(g['Status']!='PENDING' for g in contract['hydro_group_qualification']['groups']),pending_hydro_groups=sum(g['Status']=='PENDING' for g in contract['hydro_group_qualification']['groups']),pending_original_hydro_mw=sum(g['SurvivingCapacityMW'] for g in contract['hydro_group_qualification']['groups'] if g['Status']=='PENDING'),resource_identities_checked=len(resource_checks),gpd_conditional_mw=sum(r['ConditionalSurvivingMW'] or 0 for r in report['gpd']),gpd_actual_mw=sum(r['ActualIntegratedMW'] for r in report['gpd']),gpd_duplicate_mw=sum(r['ConditionalSurvivingMW'] or 0 for r in report['gpd'] if r['IdentityStatus']=='DUPLICATE_EXISTING_GEM_SITE'),upper_bound_proven_records=len(bound),upper_bound_proven_mw=sum(r['CapacityMW'] for r in bound),gem_still_missing_year_records=len(unknown),gem_still_missing_year_mw=sum(r['OriginalCapacity'] for r in unknown),demand_accounts=152,development_loads=len(f.loads),fixed_pending_accounts=471,price_records=len(read(A/'model_cost_layer.json')['rows']),physical_carbon_events=len(carbon),policy_pending=200,policy_enabled=False,fullsc_network_complete=False,solver_runs=0,gate5_allowed=False)
save(E/'ACTUAL_VALIDATION_SUMMARY.json',summary);save(E/'CURRENT_ACCOUNTING_REPORT.json',accounting_report(f));print(json.dumps(summary,indent=2))
cmd=[sys.executable,'scripts_project/check_assembly_inputs.py','--repo','.', '--allocation','results_project/assembly_v1/allocation','--output',str(E/'FINAL_INPUT_GATE.json')]
with (E/'FINAL_INPUT_GATE.log').open('w') as log:ret=sp.run(cmd,cwd=R,stdout=log,stderr=sp.STDOUT)
assert ret.returncode==2;assert not (R/'results_project/assembly_v1/research_fullsc_2050_unsolved.nc').exists()
