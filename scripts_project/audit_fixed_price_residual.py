"""Read-only Gate4 actual-network and residual-source evidence audit; no solver."""
from pathlib import Path
import argparse,json,hashlib,collections,warnings
import numpy as np,pandas as pd,pypsa,xarray as xr
warnings.filterwarnings('ignore',category=pd.errors.PerformanceWarning)
from fixed_accounts import qualify_fixed_accounts,validate_exported_accounting,accounting_report
from price_basis import qualify_network_costs
from build_research_network import load_unbound_recipe
from assembly_components import merge_input_components,bind_loads,validate_hooks
from carrier_architecture import Fragment,to_pypsa_fragment

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(repo,prior_delivery,source_config,output):
 R=repo;A=R/'results_project/assembly_v1/assets';E=output;E.mkdir(parents=True,exist_ok=True);old=prior_delivery
 def save(name,x):(E/name).write_text(json.dumps(x,indent=2,default=str,allow_nan=False)+'\n')
 cfg=json.loads(source_config.read_text());base=pypsa.Network(A/'electric_base_2050_unsolved.nc');sub=pypsa.Network(A/'carrier_fragment_2050_unsolved.nc');previous=pypsa.Network(old/'production_assets/electric_base_2050_unsolved.nc');previous_sub=pypsa.Network(old/'production_assets/carrier_fragment_2050_unsolved.nc')
 assert base.meta['existing_unit_components']==previous.meta['existing_unit_components']
 def unchanged_table(prior,current):
  # PyPSA adds global multiport schemas while reading another Network. Empty
  # unused ports can therefore be present in one readback and absent in another.
  # Compare only when the omitted values are exactly the component defaults.
  current=current.copy()
  for col in prior.columns.difference(current.columns):
   if col.startswith('bus') and col[3:].isdigit() and prior[col].eq('').all():current[col]=''
   elif col.startswith('efficiency') and col[10:].isdigit() and prior[col].eq(1.).all():current[col]=1.
   else:raise ValueError('Non-default source input column disappeared: '+col)
  pd.testing.assert_frame_equal(prior,current.loc[prior.index,prior.columns],check_dtype=False)
 for typ in ['Generator','Link','StorageUnit','Store','Line']:
  prior=previous.df(typ);unchanged_table(prior,base.df(typ))
  for attr,d in previous.pnl(typ).items():
   if attr not in base.pnl(typ) and d.empty:continue
   pd.testing.assert_frame_equal(d,base.pnl(typ)[attr],check_dtype=False)
 for typ in ['Generator','Link','Store','Load']:
  prior=previous_sub.df(typ).copy()
  if typ=='Link':
   # Explicit engineering fix: the prior FT Link omitted known output-basis VOM.
   # This is not a price rebase or a physical/quantity change.
   ids=prior.index[prior.carrier.eq('Fischer-Tropsch')]
   rawcost=pd.read_csv(Path(cfg['source_costs2050']),index_col=0)
   assert prior.loc[ids,'marginal_cost'].eq(0.).all()
   prior.loc[ids,'marginal_cost']=float(rawcost.at['Fischer-Tropsch','VOM'])*prior.loc[ids,'efficiency']
  unchanged_table(prior,sub.df(typ))
 pd.testing.assert_frame_equal(sub.loads_t.p_set,previous_sub.loads_t.p_set)
 al=R/'results_project/assembly_v1/allocation'
 assert sha(al/'allocations.npz')==sha(old/'actual_allocation/allocations.npz')
 assert sha(R/'research_inputs/assembly_v1/registry.json')==sha(old/'repo/research_inputs/assembly_v1/registry.json')
 carbon=json.loads((A/'carbon_component_map.json').read_text());oldcarbon=json.loads((old/'production_assets/carbon_component_map.json').read_text());assert carbon==oldcarbon
 assert len(carbon)==1595 and sum(r['policy_weight'] is None for r in carbon)==200
 validate_exported_accounting(sub);ledger=qualify_fixed_accounts(sub)
 assert ledger==json.loads((A/'external_pending_fixed_accounts.json').read_text())
 raw=load_unbound_recipe(A/'carrier_fragment.json');f=Fragment();f.buses=raw['buses'];f.components=raw['components'];f.markets=raw['markets'];frag=to_pypsa_fragment(f,list(base.snapshots),list(base.snapshot_weightings.generators),component_ids=list(f.components));merge_input_components(base,frag)
 base.meta.update(biomass_obligation_routes=raw['biomass_obligation_routes'],required_constraint_hooks=sorted(set(base.meta['required_constraint_hooks'])|{'install_fragment_constraints'}))
 registry=json.loads((R/'research_inputs/assembly_v1/registry.json').read_text());am=json.loads((al/'allocation_manifest.json').read_text())
 with np.load(al/am['arrays_file'],allow_pickle=False) as arrays:bind_loads(base,registry['records'],am,arrays,raw['demand_destinations'])
 layer=json.loads((A/'model_cost_layer.json').read_text());prices=qualify_network_costs(base,layer,A/'model_cost_layer.json');merged=qualify_fixed_accounts(base);assert merged==ledger;validate_hooks(base);validate_exported_accounting(base)
 totals=collections.defaultdict(float)
 for r in ledger:totals[r['Commodity']]+=r['QuantityMWh']
 save('ACTUAL_FIXED_ACCOUNT_VALIDATION.json',dict(status='PASS_ACTUAL_PARTIAL_ACCEPTED_SCOPE',fixed_rows=len(ledger),commodity_totals_mwh=dict(totals),unbound_recipe_bound_once=True,full_input_gate_bypassed=False,complete_network_exported=False,loads=len(base.loads),registry_sha256=sha(R/'research_inputs/assembly_v1/registry.json'),arrays_sha256=sha(al/'allocations.npz'),electric_component_values_and_timeseries_unchanged=True,carrier_physics_and_demand_unchanged=True,explicit_engineering_cost_fix='100 FT Links now charge known VOM per MWh_FT times output efficiency on input dispatch; prior omission corrected',physical_carbon_records=len(carbon),policy_pending_records=200,solver_runs=0))
 save('ACTUAL_COMPONENT_PRICE_QUALIFICATION.json',prices);save('ACTUAL_ACCOUNTING_REPORT.json',accounting_report(base))
 # Scope-limited residual hydro trace: only the 12 groups still pending.
 groups=json.loads((A/'HYDRO_GROUP_QUALIFICATION.json').read_text())['groups'];pending=[g for g in groups if g['Status']=='PENDING'];assert len(groups)==70 and len(pending)==12
 stock=json.loads((A/'ASSET_SURVIVAL_2050.json').read_text());units={u['AssetID']:u for u in stock['unit_evidence']['records']};contract=json.loads((R/'research_inputs/asset_survival/integration_contract.json').read_text());plants=pd.read_csv(cfg['source_powerplants']);ref=pypsa.Network(cfg['source_reference'])
 rawprofile=Path(cfg['source_powerplants']).parent/'renewable_profiles/profile_hydro.nc';profile=xr.open_dataarray(rawprofile);parent_ids=set(map(str,profile.plant.values));rawhours=len(profile.time)
 assigned={g.get('SourceComponent') for g in groups if g['Status']!='PENDING'};hydro=[];residual=[]
 for g in pending:
  members=[units[k] for k in g['SourceUnitIDs']];parents=sorted({u['ParentAssetID'] for u in members});mappings=[dict(AssetID=u['AssetID'],**contract['mapping'][str(u['OriginalMappedBus'])]) for u in members]
  prefix=g['Node'].rsplit(' ',1)[0];carrier='hydro' if g['HydroSubtype']=='Reservoir' else 'ror';typ='StorageUnit' if carrier=='hydro' else 'Generator'
  candidates=[name for name,z in ref.df(typ).iterrows() if z.carrier==carrier and z.bus.rsplit(' ',1)[0]==prefix and ref.buses.at[z.bus,'country']==g['Country']]
  ids=[str(plants.iloc[int(p.split(':')[1])]['Unnamed: 0']) for p in parents]
  q=dict(**g,OriginalUnitBusMapping=mappings,OriginalParentIDs=parents,RawProfileParentIDs=ids,RawProfileMissingIDs=sorted(set(ids)-parent_ids),RawProfileHours=rawhours,RawProfileSHA256=sha(rawprofile),RawProfileStart=str(profile.time.values[0]),RawProfileEnd=str(profile.time.values[-1]),CompatibleRegionReferenceCandidates=candidates,AlreadyAssignedCandidates=[k for k in candidates if k in assigned],Original100NodeResourceAssignmentRecovered=False,ClosedThisRound=False,RequiredEvidence='2013 full-year source hydro profile for listed original parent/plant IDs and original100-node/basin coverage; short cache cannot be repeated',CandidateMethod='If author mapping cannot be recovered: review explicit re-partition of compatible SAME_REGION/SAME_AC_GROUP source envelope among old+pending turbines, conserving total water and Emax; currently UNAPPROVED, not implemented')
  hydro.append(q);residual.append(dict(ResidualID='HYDRO:'+g['Node']+':'+g['HydroSubtype'],Family='HYDRO_ANNUAL_INPUT',Country=g['Country'],TechnologyOrAccount=g['HydroSubtype'],BaseCapacityMW=g['SurvivingCapacityMW'],SourceIDs=g['SourceUnitIDs'],ParentIDs=parents,Classification='SOURCE_PRESENT_TRANSFORMATION_INCOMPLETE_AND_GROUP_DECISION_REQUIRED',SourceState='RAW_SHORT_PROFILE_AND_REFERENCE_GROUPS_EXIST_NO_UNIQUE_ANNUAL_ATTRIBUTION',Required=q['RequiredEvidence'],Candidate=q['CandidateMethod'],ApprovalStatus='PENDING',ClosedThisRound=False))
 profile.close();save('HYDRO_RESIDUAL_EXACT_TRACE.json',hydro)
 # Inventory groups are disjoint by unit status; unmatched parents are related,
 # not summed with unit-level amounts. Explicit links preserve overlap.
 missing=collections.defaultdict(list)
 for u in units.values():
  if u['SurvivalStatus'].startswith('UNRESOLVED'):missing[(u['Country'],u['Technology'],u['SurvivalStatus'])].append(u)
 for (country,tech,state),rs in sorted(missing.items()):
  residual.append(dict(ResidualID=f'UNITS:{country}:{tech}:{state}',Family='INVENTORY_UNIT_STATUS',Country=country,TechnologyOrAccount=tech,BaseCapacityMW=sum(u['OriginalCapacity'] for u in rs),SourceIDs=[u['AssetID'] for u in rs],ParentIDs=sorted({u['ParentAssetID'] for u in rs}),Classification='ONE_GROUP_SOURCE_OR_COVERAGE_DECISION',SourceState=state,Required='Verified commissioning/retirement or observed-existing status for listed frozen unit IDs; source files and exact rows in ASSET_SURVIVAL_2050.json. Do not resend229 already recovered parent years.',Candidate='Grouped evidence or explicit treatment of unresolved inventory; no assumed years/zero/extension',ApprovalStatus='PENDING',ClosedThisRound=False))
 parents=collections.defaultdict(list)
 for p in stock['unit_evidence']['parent_reconciliation']:
  if not p['CapacityReconciled']:parents[(p['Country'],p['Technology'])].append(p)
 for (country,tech),rs in sorted(parents.items()):
  residual.append(dict(ResidualID=f'PARENTS:{country}:{tech}',Family='PARENT_LINK_OR_CAPACITY_CONFLICT',Country=country,TechnologyOrAccount=tech,BaseCapacityMW=sum(p['ParentCapacity'] for p in rs),ParentCount=len(rs),ParentIDs=[p['ParentAssetID'] for p in rs],SourceIDs=sorted({i for p in rs for i in p['SourceIDs']}),Classification='SOURCE_PRESENT_LINK_OR_CAPACITY_RECONCILIATION_REQUIRED',SourceState='FROZEN_PARENT_VS_RAW_UNIT_DIFFERENCE',Required='Resolve listed parent projectID mapping/capacity against frozen raw-unit roster; no capacity normalisation',Candidate='Source-linked correction or one grouped inventory treatment decision',ApprovalStatus='PENDING',NonAdditiveWithUnitGroups=True,ClosedThisRound=False))
 # Exact previously unsuccessful memo requests. No new network request here.
 memos=[('ID','ZD','5222',t) for t in ['121','1221','1235']]+[('PH','ZD','5222',t) for t in ['121','1221','1222','1232','1235']]+[('PH','ZG','5212','1221'),('VN','ZG','5212','1221')]
 use={'121':'IndustryFinalEnergy','1221':'RoadResidualFuel','1222':'RailNonElectric','1232':'ServicesFuel','1235':'AgricultureFinalEnergy'}
 for country,commodity,code,t in memos:
  residual.append(dict(ResidualID=f'MEMO:{country}:2019:{code}:{t}',Family='BIOFUEL_BLEND_MEMO',Country=country,TechnologyOrAccount=use[t],Commodity=commodity,Year=2019,SDMXCommodity=code,Transaction=t,Classification='EXISTING_QUERY_NO_MATCHING_TRANSACTION_RETURNED',SourceState='NO_NEW_LEAD_NO_REPEAT_QUERY',Required=f'Official2019 {country} {commodity}/{code} transaction{t}, compatible parent vintage, unit, footnote and inclusion relation; parent already cached',OfficialEntry='https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY/',Receipt='UNSD_TARGETED_RETRIEVAL_RECEIPT.json',Candidate='Source memo or explicit official inclusion metadata; no legal blend proxy',ApprovalStatus='PENDING',ClosedThisRound=False))
 coverage=json.loads((R/'research/04_model_assembly/gate4/evidence/SOURCE_COVERAGE_ACCOUNT_MAP.json').read_text())
 seen=set()
 for q in coverage['rows']:
  key=q.get('SourceCoverageID') or '|'.join(q['Pending2050AccountIDs']);rid='COVERAGE:'+key
  if rid in seen:continue
  seen.add(rid)
  linked=[r['ResidualID'] for r in residual if r['Family']=='BIOFUEL_BLEND_MEMO' and r['Country']==q['Country'] and r['TechnologyOrAccount']==q['Account']]
  if q['SourceCategory']=='OTHER_EXISTING_PENDING_ACCOUNT_OUTSIDE_ORIGINAL33':
   linked=linked or [r['ResidualID'] for r in residual if r['Family']=='BIOFUEL_BLEND_MEMO' and r['Country']==q['Country']]
   classification='SOURCE_PRESENT_TRANSFORMATION_BLOCKED_BY_COUNTRY_BLEND_GUARD'
   required='Cached positive parents already exist. Resolve linked country blend memo/inclusion evidence, then rerun eligible carrier de-duplication. Do not request these cached parents again.'
   candidate='No new quantity method: existing approved projection applies after source overlap qualification'
  elif q['SourceCategory']=='KNOWN_NEC_ENERGY_RETAINED_SECTOR_SPLIT_UNRESOLVED':
   classification='ONE_COVERAGE_BOUNDARY_DECISION_REQUIRED'
   required='Known NEC energy already retained once; decide explicit sector coverage for this unreported combination or provide a mutually exclusive source split. NEC is not zero evidence.'
   candidate='Keep NEC obligation, review partial coverage scope without dropping positive energy; unapproved exclusion not executed'
  else:
   classification='SOURCE_FAMILY_ABSENT_IN_CACHE' if q['SourceCategory']=='SOURCE_FAMILY_NOT_PRESENT_IN_CACHED_EXPORT' else 'CACHED_QUERY_NO_MATCHING_TRANSACTION'
   required=f"Official2019 {q['Country']} {q['Account']} {q['Carrier']} source-use transaction or source-bounded zero proof; source-family/transaction distinction retained"
   candidate='Targeted source completion or one explicit coverage decision; no zero from an empty filter'
  residual.append(dict(ResidualID=rid,Family='SOURCE_COVERAGE_ACCOUNT',Country=q['Country'],TechnologyOrAccount=q['Account'],Carrier=q['Carrier'],RelatedResidualIDs=linked,Pending2050AccountIDs=q['Pending2050AccountIDs'],SourceCoverageID=q.get('SourceCoverageID'),Classification=classification,SourceState=q['SourceCategory'],Required=required,Candidate=candidate,ApprovalStatus='PENDING',ClosedThisRound=False))
 assert len({r['ResidualID'] for r in residual})==len(residual)
 save('RESIDUAL_PHYSICAL_MAPPING.json',dict(rows=residual,hydro_groups=70,qualified_hydro_groups=58,pending_hydro_groups=12,pending_hydro_units=16,pending_hydro_mw=1454.,source_combinations=33,pending_accounts=51,memos=10,new_source_queries=0,new_closed_physical_gaps=0,non_additive_families=True))
 save('NUMERICAL_SUMMARY.json',dict(existing_units=len(base.meta['existing_unit_components']),existing_mw=sum(r['capacity_mw'] for r in base.meta['existing_unit_components'].values()),hydro_mw=47182,accepted_accounts=len(am['records']),loads=len(base.loads),fixed_account_rows=len(ledger),fixed_commodities=len(totals),price_row_status=dict(collections.Counter(r['Status'] for r in layer['rows'])),pending_price_components=[r for r in prices if any('PENDING' in str(v) for v in r.values())],hydro_total_groups=70,hydro_qualified_groups=58,hydro_pending_groups=12,closed_hydro_groups=0,solver_runs=0,fullsc_network_complete=False,gate5_allowed=False))
 print('Actual audit passed:',len(ledger),'fixed resource rows;',len(prices),'priced component scopes;',len(hydro),'hydro groups remain.')

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for arg in ['repo','prior-delivery','source-config','output']:p.add_argument('--'+arg,type=Path,required=True)
 audit(**vars(p.parse_args()))
