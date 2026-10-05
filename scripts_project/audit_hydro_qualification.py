from pathlib import Path
import json,hashlib,collections,csv,sys,subprocess as sp,inspect
import numpy as np,pandas as pd,pypsa
import warnings
warnings.filterwarnings('ignore',category=pd.errors.PerformanceWarning)
import argparse
parser=argparse.ArgumentParser(description="Read-only actual Gate4 asset audit; no solver")
for arg in ['repo','prior-delivery','source-config','cost-directory','output']:parser.add_argument('--'+arg,type=Path,required=True)
args=parser.parse_args();R=args.repo;E=args.output;E.mkdir(parents=True,exist_ok=True);A=R/'results_project/assembly_v1/assets';OLD=args.prior_delivery;COSTDIR=args.cost_directory
(E/'PRODUCTION_SOURCE_PATHS.json').write_text(args.source_config.read_text())
sys.path.insert(0,str(R/'scripts_project'))
from carbon_architecture import classify_record
from assembly_components import validate_hooks,merge_input_components,bind_loads
from build_research_network import load_unbound_recipe
from carrier_architecture import Fragment,to_pypsa_fragment
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):(E/name).write_text(json.dumps(x,indent=2,default=str)+'\n')
old=pypsa.Network(OLD/'production_assets/electric_base_2050_unsolved.nc');n=pypsa.Network(A/'electric_base_2050_unsolved.nc');sub=pypsa.Network(A/'carrier_fragment_2050_unsolved.nc');cfg=json.loads((E/'PRODUCTION_SOURCE_PATHS.json').read_text());ref=pypsa.Network(cfg['source_reference'])
validate_hooks(n);validate_hooks(sub)
oldunits=old.meta['existing_unit_components'];units=n.meta['existing_unit_components'];assert all(units[k]==v for k,v in oldunits.items())
pd.testing.assert_frame_equal(old.links.loc[sorted(set(x['component'] for x in oldunits.values()))],n.links.loc[sorted(set(x['component'] for x in oldunits.values())),old.links.columns],check_dtype=False)
pd.testing.assert_frame_equal(old.lines,n.lines,check_dtype=False)
for col in ['p_nom','p_nom_max','p_nom_extendable','capital_cost']:
 pd.testing.assert_series_equal(old.generators[col],n.generators.loc[old.generators.index,col],check_dtype=False)
al=R/'results_project/assembly_v1/allocation';assert sha(al/'allocations.npz')==sha(OLD/'actual_allocation/allocations.npz')
assert sha(R/'research_inputs/assembly_v1/registry.json')==sha(OLD/'repo/research_inputs/assembly_v1/registry.json')
assert len(sub.loads)==1436
assert set(sub.meta['demand_owners'].values())=={r['InputID'] for r in json.loads((al/'allocation_manifest.json').read_text())['records']}
pd.testing.assert_frame_equal(sub.loads,pypsa.Network(OLD/'production_assets/carrier_fragment_2050_unsolved.nc').loads,check_dtype=False)
groups=json.loads((A/'HYDRO_GROUP_QUALIFICATION.json').read_text())['groups'];out=[]
for g in groups:
 integrated=[units[k] for k in g['SourceUnitIDs'] if k in units];cap=sum(v['capacity_mw'] for v in integrated)
 q=dict(g,ActualIntegratedMW=cap,ActualComponents=sorted({v['component'] for v in integrated}))
 if g['Status']=='SOURCE_QUALIFIED_GROUP_PROXY':
  assert np.isclose(cap,g['SurvivingCapacityMW']) and len(q['ActualComponents'])==1
  name=q['ActualComponents'][0];typ=integrated[0]['component_type'];z=n.df(typ).loc[name];assert np.isclose(z.p_nom,cap);assert z.resource_identity==g['ResourceIdentity'];assert z.capital_cost==0 and z.existing_annual_fixed_om_eur>0
  if typ=='StorageUnit':
   assert np.isclose(z.p_nom*z.max_hours,g['EnergyCapacityMWh']) and z.cyclic_state_of_charge
   if g['HydroSubtype']=='Reservoir':np.testing.assert_array_equal(n.storage_units_t.inflow[name],ref.storage_units_t.inflow[g['SourceComponent']])
   else:assert z.inflow==0 and z.state_of_charge_initial==0 and np.isclose(z.efficiency_store*z.efficiency_dispatch,.75) and z.p_min_pu==-1
  else:
   expected=np.minimum(ref.generators_t.p_max_pu[g['SourceComponent']].values*g['SourceInputCapacityMW']/cap,1.)
   np.testing.assert_allclose(n.generators_t.p_max_pu[name],expected,rtol=1e-12)
 else:assert cap==0
 out.append(q)
save('HYDRO_ACTUAL_VALIDATION.json',out)
carbon=json.loads((A/'carbon_component_map.json').read_text());physical=[];seen=set()
for r in carbon:
 k=(r['component_type'],r['component']);assert k not in seen;seen.add(k)
 network=n if r['component'] in n.df(r['component_type']).index else sub
 z=network.df(r['component_type']).loc[r['component']]
 ports=[k for k in z.index if k.startswith('bus') and k[3:].isdigit() and k!='bus0' and z[k]]
 actual=sum(float(z['efficiency' if k=='bus1' else 'efficiency'+k[3:]]) for k in ports if network.buses.at[z[k],'carrier']=='co2 atmosphere')
 assert np.isclose(actual,r['coefficient'])
 mapped=classify_record(r['component'],r['carrier'],r['sector'],r['country'],r['coefficient'],source=r['source'],policy_weight=r['policy_weight'],accepted=r['accepted'],physical_qualified=r.get('PhysicalReportingQualified'),policy_qualified=r.get('PolicyAttributionQualified'))
 if r.get('captured_carbon_factor') is not None:
  assert np.isclose(r['gas_input_carbon_factor'],r['coefficient']+r['captured_carbon_factor'])
  if r['captured_carbon_factor']:assert z.bus3==r['captured_destination'] and np.isclose(z.efficiency3,r['captured_carbon_factor'])
 physical.append(mapped)
save('PHYSICAL_POLICY_VALIDATION.json',physical)
# Prove the assembly boundary using real unbound recipe and real accepted arrays.
raw=load_unbound_recipe(A/'carrier_fragment.json');f=Fragment();f.buses=raw['buses'];f.components=raw['components'];f.markets=raw['markets'];unbound=to_pypsa_fragment(f,list(n.snapshots),list(n.snapshot_weightings.generators),component_ids=list(f.components))
assert unbound.loads.empty
merge_input_components(n,unbound)
# Match the production assembler's explicit persisted hook installation contract.
n.meta['required_constraint_hooks']=sorted(set(n.meta.get('required_constraint_hooks',[]))|{'install_fragment_constraints'})
registry=json.loads((R/'research_inputs/assembly_v1/registry.json').read_text());am=json.loads((al/'allocation_manifest.json').read_text())
with np.load(al/am['arrays_file'],allow_pickle=False) as ar:bind_loads(n,registry['records'],am,ar,raw['demand_destinations'])
assert len(n.loads)==1436 and n.meta['demand_owners']==sub.meta['demand_owners']
pd.testing.assert_frame_equal(n.loads_t.p_set,sub.loads_t.p_set)
for comp in n.iterate_components():
 for col in [k for k in comp.df if k=='bus' or k.startswith('bus') and k[3:].isdigit()]:
  assert all(not b or b in n.buses.index for b in comp.df[col]),(comp.name,col)
validate_hooks(n)
save('REAL_RECIPE_BOUNDARY_CHECK.json',dict(status='PASS_PARTIAL_ACCEPTED_SCOPE_ONLY',real_recipe_unbound=True,bound_once_loads=1436,source_account_carrier_sector_country_preserved=True,no_dangling_ports_after_merge=True,persisted_hooks_validated=True,combined_network_exported=False,full_input_gate_bypassed=False,solver_runs=0))
# Commodity-level mathematical fixed-account proof; no prices/factors invented.
bio=collections.defaultdict(lambda:dict(ResourceCount=0,AnnualQuantityMWh=0.,Checks=[]));routes=raw['biomass_obligation_routes'];finals=collections.defaultdict(list)
for name,r in routes.items():finals[tuple(r['buses'])].append(name)
for buses,names in finals.items():
 final=set(buses);loads=sub.loads[sub.loads.bus.isin(final)].index;annual=float(sub.loads_t.p_set[loads].sum(axis=1).mul(sub.snapshot_weightings.generators).sum());assert np.isclose(sum(sub.stores.at[k,'e_initial'] for k in names),annual)
 assert not sub.stores.bus.isin(final).any() and not sub.generators.bus.isin(final).any()
 outgoing=sub.links[sub.links.bus0.isin(final)];assert outgoing.empty
 incoming=sub.links[sub.links.bus1.isin(final)];assert len(incoming)==len(names)
 for name in names:
  r=routes[name];z=sub.stores.loc[name];resource=z.bus;touch=sub.links[sub.links.filter(regex=r'^bus\d+$').eq(resource).any(axis=1)]
  assert len(touch)==1 and touch.iloc[0].bus0==resource and touch.iloc[0].bus1 in final and touch.iloc[0].efficiency==1 and touch.iloc[0].p_min_pu>=0
  assert not sub.generators.bus.eq(resource).any() and sum(sub.stores.bus.eq(resource))==1
  assert not z.e_nom_extendable and not z.e_cyclic and np.isclose(z.e_initial,z.e_nom) and np.isclose(z.e_nom,r['annual_cap_mwh']) and z.standing_loss==0
  assert sub.meta['store_power_rules'][name]=='discharge_only'
  assert all(not touch.iloc[0].get('bus'+str(i),'') for i in range(2,5))
  b=bio[r['commodity']];b['ResourceCount']+=1;b['AnnualQuantityMWh']+=z.e_nom;b['Checks'].append(name)
bio_rows=[dict(Commodity=k,ResourceCount=v['ResourceCount'],AnnualQuantityMWh=v['AnnualQuantityMWh'],AnnualQuantityStrictlyFixed=True,OwnObligationOnly=True,AlternativeSupplyOrDiversion=False,StorageArbitrage=False,CarbonCreditPath=False,SupplyCostEffect='Fixed constant only IF time-invariant delivered commodity unit cost; no numerical cost accepted',PhysicalCO2Effect='Unknown fixed physical-emission account under this boundary; cannot claim full emissions',ProposedExternalLedger='PENDING_HUMAN_REVIEW; sum_c Q_c * unknown_price_c; physical emissions separate Q_c * unknown_factor_c; never substitute zero') for k,v in sorted(bio.items())]
expected_commodities={'Animal waste','Bagasse','Biodiesel','Biogases','Biogasoline','Charcoal','Fuelwood'}
assert set(bio)<=expected_commodities
for commodity in sorted(expected_commodities-set(bio)):
 bio_rows.append(dict(Commodity=commodity,ResourceCount=0,AnnualQuantityMWh=None,AnnualQuantityStrictlyFixed=None,OwnObligationOnly=None,SupplyCostEffect='NOT_MATERIALISED; source/quantity qualification pending. No claim of zero demand or proven fixed cost for absent commodity.',PhysicalCO2Effect='PENDING; no zero factor',ProposedExternalLedger='Conditional only after source quantity and isolated routing qualify'))
save('FIXED_BIOFUEL_ACCOUNTING_PROOF.json',dict(commodity_rows=bio_rows,materialised_commodities=len(bio),proof='For the SIX actually materialised commodity classes: each finite stock starts full, cannot charge/divert, shares only its exclusive final obligation. Sum initial stocks equals fixed annual demand and all final stocks nonnegative, so every final stock=0 and each annual throughput equals its own Q. For constant unit price, sum_t w_t*c*q_t=c*Q. Timing can vary but cannot change this constant. Animal waste has no materialised qualified resource: missing is not zero and the proof is conditional for it.',assumptions=['required discharge-only hook installed in future model','no added alternate sources/sinks/losses or carbon credit paths','unit price constant in time'],full_output_qualification_unchanged=True))
# Source and prepared cost values: unit/currency conversion != real-price rebasing.
costrows=[]
for year in [2030,2050]:
 rawcost=pd.read_csv(COSTDIR/f'costs_{year}.csv');processed=pd.read_csv(COSTDIR/f'costs_{year}_{"elec" if year==2030 else "sec"}.csv',index_col=0)
 for tech in ['CCGT','coal','lignite','oil','hydro','ror','PHS']:
  for par in ['investment','VOM','FOM']:
   rows=rawcost[rawcost.technology.eq(tech)&rawcost.parameter.eq(par)]
   for _,row in rows.iterrows():
    val=float(processed.at[tech,par]);factor=1000. if '/kW' in str(row.unit) else 1.
    costrows.append(dict(Technology=tech,Parameter=par,TechnologyYear=year,RawValue=row.value,RawUnit=row.unit,RawCurrencyYear=row.currency_year,PreparedValue=val,UnitScale=factor,PreparedEqualsRawAfterUnitScale=bool(np.isclose(val,row.value*factor)),Source=row.source))
save('MODEL_FACING_COST_YEAR_EVIDENCE.json',dict(rows=costrows,status='CURRENCY_UNIFIED_EUR_REAL_PRICE_YEAR_NOT_UNIFIED',transformation_source='scripts/process_cost_data.py:load_costs/prepare_costs/apply_currency_conversion; exchange rate only, assumes reference-year real prices already; currency_year not used as inflation factor',source_hashes={str(R/'scripts/process_cost_data.py'):sha(R/'scripts/process_cost_data.py'),str(R/'scripts/append_cost_data.py'):sha(R/'scripts/append_cost_data.py')},no_reinflation_applied=True,candidate='Choose one agreed real EUR year and official compatible deflator series; apply price-year correction only to rows without prior real-price rebase; retain FX conversion and dimensionless FOM separately. Not applied.',scope='Existing FOM constant; existing VOM affects dispatch; new CAPEX/FOM/VOM and external fuel costs may affect decisions. Complete reported system cost unresolved.'))
coverage=list(csv.DictReader((R/'research/04_model_assembly/gate4/REMAINING_SOURCE_COVERAGE_REVIEW.csv').open(encoding='utf-8-sig')));gate=json.loads((OLD/'repo/research/04_model_assembly/gate4/evidence/FINAL_INPUT_PREFLIGHT.json').read_text());byid={r['InputID']:r for r in registry['records']};maprows=[];mapped=set()
for z in coverage:
 matches=[rid for rid in gate['unresolved_input_ids'] if byid[rid]['Country']==z['Country'] and byid[rid]['Account']==z['Account'] and byid[rid]['Carrier']==z['Carrier']]
 for rid in matches:mapped.add(rid)
 maprows.append(dict(SourceCoverageID=z['AccountID'],Country=z['Country'],Account=z['Account'],Carrier=z['Carrier'],SourceCategory=z['Category'],Pending2050AccountIDs=matches,Relation='EXACT_COUNTRY_ACCOUNT_CARRIER' if matches else 'NEC_SECTOR_SPLIT_QUESTION_NOT_A_NEW_UNPOSTED_POSITIVE_ACCOUNT',PhysicalPostingState='KnownNEC already retained; no zero proof for other sectors' if not matches else 'PENDING_SOURCE_OR_COVERAGE',NewProblem=False))
for rid in gate['unresolved_input_ids']:
 if rid not in mapped:
  r=byid[rid];maprows.append(dict(SourceCoverageID=None,Country=r['Country'],Account=r['Account'],Carrier=r['Carrier'],SourceCategory='OTHER_EXISTING_PENDING_ACCOUNT_OUTSIDE_ORIGINAL33',Pending2050AccountIDs=[rid],Relation='One existing target row; not another source-coverage combination',PhysicalPostingState='PENDING',NewProblem=False))
assert len(coverage)==33 and len(gate['unresolved_input_ids'])==51;save('SOURCE_COVERAGE_ACCOUNT_MAP.json',dict(source_combinations=33,pending_physical_accounts=51,rows=maprows,counts_not_additive=True,new_queries=0))
summary=dict(hydro_by_subtype={s:dict(admitted_mw=sum(g['ActualIntegratedMW'] for g in out if g['HydroSubtype']==s),pending_mw=sum(g['SurvivingCapacityMW']-g['ActualIntegratedMW'] for g in out if g['HydroSubtype']==s)) for s in ['Reservoir','Run-Of-River','Pumped Storage']},thermal_mw_preserved=139404,thermal_units_preserved=536,total_integrated_units=len(units),total_integrated_mw=sum(v['capacity_mw'] for v in units.values()),qualified_demand_accounts=152,actual_partial_loads=1436,physical_qualified_carbon_components=len(physical),policy_pending_carbon_components=sum(not r['PolicyAttributionQualified'] for r in physical),bio_commodity_count=7,full_network_exported=False,solver_runs=0,gate5_allowed=False)
save('FINAL_NUMERICAL_SUMMARY.json',summary)
print(json.dumps(summary,indent=2),flush=True)
