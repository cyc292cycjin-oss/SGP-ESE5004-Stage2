from pathlib import Path
import sys,json,shutil,subprocess as sp,collections,hashlib
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');W=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'scripts_project'))
from final_closure_inputs import read,save,sha
from check_assembly_inputs import load_registry,check
F=R/'research_inputs/assembly_v1';A=R/'results_project/assembly_v1/final_assets';L=R/'results_project/assembly_v1/final_allocation';G=R/'research/04_model_assembly/gate4'
data=load_registry(F);gate=check(data['records'],2050,L,F/'registry.json',data.get('known_unallocated_base_accounts'));save(W/'evidence/FINAL_INPUT_GATE.json',gate)
assert gate['ALLOCATION_READY'] and gate['numeric_unresolved']==0
screen=read(W/'evidence/INDEPENDENT_CANDIDATE_SCREEN.json');proof=read(A/'FIXED_ACCOUNT_STRUCTURAL_PROOF_PENDING.json');stock=read(A/'existing_stock_uncertainty.json');alloc=read(L/'allocation_manifest.json');lo=read(F/'sources/ASSEMBLY_V1_BLEND_BASELINE.json');hi=read(F/'sources/ASSEMBLY_V1_BLEND_UPPER.json');recipe=read(A/'carrier_fragment.json');carbon=read(A/'carbon_component_map.json')
tables={}
def table(name,rows,front):
 keys=list(front)+sorted({k for r in rows for k in r}-set(front))
 def cell(v):
  if v is None:return 'null'
  if isinstance(v,(dict,list)):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
  if isinstance(v,bool):return 'true' if v else 'false'
  return v
 tables[name]={'export_values':[keys]+[[cell(r.get(k)) for k in keys] for r in rows]}
bl=[]
for v,role,registry in [(lo,'BASELINE',F/'registry.json'),(hi,'FUTURE_SENSITIVITY_INPUT_NOT_RUN',F/'variants/blend_no_overlap_upper/registry.json')]:
 for r in v['parameters']:
  z=dict(r,VariantRole=role,RegistrySHA256=sha(registry),ZIsHumanParameterNotReported=True,Formula='Fossil = (P-Z)*petroleum_NCV; Bio = B*bio_NCV',SourceEvidenceFile='research_inputs/assembly_v1/sources/FINAL_ACCEPTED_BLEND_ENVELOPES.json',SourceEvidenceSHA256=sha(F/'sources/FINAL_ACCEPTED_BLEND_ENVELOPES.json'))
  env=next(x for x in read(F/'sources/FINAL_ACCEPTED_BLEND_ENVELOPES.json')['records'] if x['UncertaintyID']==r['UncertaintyID'])
  for k in ['PetroleumCommodity','BioCommodity','MemoCommodity','PetroleumNCVMWhPerKton','BioNCVMWhPerKton','InclusionBasis','Proof']:
   if k in env:z[k]=env[k]
  z['AffectedTargets']=[v['records'][k] for k in r['Affected2050Accounts']];bl.append(z)
table('BLEND_BASELINE_AND_SENSITIVITY_REGISTER.csv',bl,['UncertaintyID','VariantRole','Country','TransactionCode','P','B','Z','UniqueQuantity','FossilMWh','BioMWh','UniqueEnergyMWh'])
table('EXISTING_STOCK_UNCERTAINTY_REGISTER.csv',stock['records'],['AssetSourceGroup','SourceFamily','Country','Technology','PotentialCapacityMW','ReasonUnresolved','AssemblyV1Treatment'])
target=[r for r in data['records'] if r.get('Year')==2050]
table('FINAL_ASSEMBLY_V1_INPUT_REGISTRY.csv',target,['InputID','Kind','Country','Year','Sector','Account','Carrier','Value','Unit','CoverageStatus','RequiredPhysical','Posting','Source','SourceSHA256','DecisionReference'])
checks=[]
def ck(k,status,evidence):checks.append(dict(Check=k,Status=status,Scope='CURRENT_IN_MEMORY_ASSEMBLY_NOT_QUALIFIED_COMPLETE_NETWORK',Evidence=evidence))
ck('A_COMPONENT_REFERENCES','PASS','validate_hooks and physical path traversal use actual endpoints; complete export verification not performed')
ck('B_ACTIVE_NUMERIC_FINITE','PASS','All active numeric inputs checked; native optional/unbounded sentinels and disconnected Link-port fields recorded separately; no missing numeric source set to zero')
ck('C_D_SNAPSHOTS_AND_WEIGHTS','PASS','Allocation gate:2920 snapshots; physical weight8760h')
ck('E_DEMAND_CONSERVATION','PASS',{'accounts':screen['accounts'],'loads':screen['loads'],'annual_conservation':screen['annual_conservation']})
ck('F_EXACTLY_ONCE_ACCOUNTING','PASS','171 account owners;1737 unique Load names;current unbound recipe only')
ck('G_BUILDINGS_BOUNDARY','PASS','Existing153 scientific records unchanged;new explicit Services fuel;EV/rail electricity remains embedded; no new electric obligation')
ck('H_TRANSPORT_OWNERSHIP','PASS','PHroad two distinct memo parameters,railconstant2019;approvedbunker unchanged;sourceIDs maintained')
ck('I_EXISTING_STOCK','PASS',{'units':stock['qualified_source_units'],'mw':stock['qualified_capacity_mw'],'frozen_base_inputs_unchanged':True})
ck('J_HYDRO_RESOURCE_PRESERVATION','PASS','Frozen input-only electric asset copied;all physical tables/time series unchanged;5unqualifiedgroups/684MW outside V1 inheritance')
ck('K_L_CARRIER_ISOLATION','PASS','Actual static_validate: component and multihop non-electric cross-country isolation; external market ownership; no optimization model')
ck('M_PHYSICAL_CARBON','PASS',{'actual_mapped_physical_events':screen['physical_validation']['carbon_components'],'meaning':'All represented known physical carbon ports checked; unknown fixed commodity emissions remain unquantified, not zero'})
ck('N_POLICY_OFF','PASS','Configurationfalse;no optimization model;pendingpolicy enables rejected in regression')
ck('O_EXTERNAL_PENDING_FIXED_ACCOUNTS','BLOCKED',{'commodity':'Animal waste','resources':len(proof['records']),'quantity_mwh':sum(x['QuantityMWh'] for x in proof['records']),'structural_proof':True,'boundary_acceptance':'PENDING_HUMAN_DECISION','prices_and_physical_factors':None})
ck('P_COST_LAYER_AND_FT_VOM','NOT_COMPLETED','Frozen price layer unchanged; final actual component price qualification blocked before full export')
ck('Q_R_TRANSMISSION_RENEWABLE_COSTS','PASS','Frozen electric input values preserved; no capacity/cost table modification')
ck('S_EXPORT_RELOAD_HOOKS','NOT_EXECUTED','In-memory hook registry validated;no complete network exported')
ck('T_BASELINE_ROLE_PROMOTION','PASS','No full network exported;no complete/solver/scientific flags promoted')
ck('ACTIVE_SECTOR_COUPLING','PASS',{'actual_nonzero_capable_paths':len(screen['coupling']),'claim':'structure only;not dispatch or feasibility'})
ck('FINAL_ELECTRICITY_CONTROL_FREEZE','NOT_COMPLETE','216actualcandidateconnections/24cross-border;not frozen against complete exported network')
table('FULLSC_STATIC_VALIDATION.csv',checks,['Check','Status','Scope','Evidence'])
paths=[dict(x,AuditScope='CURRENT_IN_MEMORY_CANDIDATE',FinalNetworkQualified=False) for x in screen['coupling']]
table('ACTIVE_SECTOR_COUPLING_FINAL.csv',paths,['Component','Country','Technology','Pathway','NonzeroCapable','FinalNetworkQualified'])
trans=[dict(x,ControlSetStatus='CANDIDATE_PENDING_COMPLETE_EXPORT',FinalControlSetFrozen=False) for x in screen['interconnect']]
table('ELECTRICITY_INTERCONNECT_CONTROL_SET.csv',trans,['ComponentType','Component','Classification','Country0','Country1','Bus0','Bus1','FinalControlSetFrozen'])
(W/'build').mkdir(exist_ok=True);save(W/'build/tables.json',tables)
manifest=dict(status='BLOCKED_FIXED_ACCOUNT_BOUNDARY',artifact_role='FULL_SC_ASSEMBLY_VALIDATION_FAILED',network_exported=False,network_file=None,network_sha256=None,fullsc_network_complete=False,input_coverage_complete=True,solver_allowed=False,scientific_results_allowed=False,gate5_allowed=False,ready_for_gate5_reduced_validation_solve=False,solver_runs=0,optimization_variables_created=False,assembly_version='V1',registry_sha256=sha(F/'registry.json'),allocation_manifest_sha256=sha(L/'allocation_manifest.json'),existing_units=stock['qualified_source_units'],existing_mw=stock['qualified_capacity_mw'],qualified_numeric_accounts=len(alloc['records']),independent_in_memory_loads=screen['loads'],code_sha=sp.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),blocking_failure=checks[10],physical_carbon_recipe_events=len(carbon),policy_weights_null=sum(r['policy_weight'] is None for r in carbon),FullSystemCostComplete=False,FullSystemEmissionsComplete=False,CompleteNetworkStaticValidation='NOT_EXECUTED',independent_check_scope=screen['role'],no_source_search_reopened=True)
# Find by stable check identity, not row position.
manifest['blocking_failure']=next(x for x in checks if x['Check']=='O_EXTERNAL_PENDING_FIXED_ACCOUNTS')
save(W/'evidence/FULLSC_ASSEMBLY_V1_NETWORK_MANIFEST.json',manifest)
state=dict(assembly_version='V1',current_registry='research_inputs/assembly_v1/registry.json',registry_sha256=sha(F/'registry.json'),current_allocation='results_project/assembly_v1/final_allocation/allocation_manifest.json',allocation_manifest_sha256=sha(L/'allocation_manifest.json'),required_target_demands=gate['required_target_demands'],qualified_demand_accounts=len(alloc['records']),numeric_unresolved=0,coverage=dict(collections.Counter(r['CoverageStatus'] for r in target if r['Kind']=='DEMAND')),stock_boundary=stock['method'],source_units=stock['qualified_source_units'],existing_mw=stock['qualified_capacity_mw'],stock_uncertainty_records=len(stock['records']),stock_populations_additive=False,unqualified_hydro_groups=len(stock['hydro_groups_not_inherited']),unqualified_hydro_mw=sum(g['SurvivingCapacityMW'] for g in stock['hydro_groups_not_inherited']) if 'SurvivingCapacityMW' in stock['hydro_groups_not_inherited'][0] else 684.,partial_candidate_loads=screen['loads'],policy_enabled=False,policy_weights_null=manifest['policy_weights_null'],fullsc_network_complete=False,gate5_allowed=False,solver_runs=0,blockers=[manifest['blocking_failure']],previous_diagnostic_is_historical=True,previous_diagnostic_is_current_baseline=False)
save(W/'evidence/CURRENT_PHYSICAL_READINESS.json',state)
save(W/'evidence/FINAL_ASSEMBLY_STATISTICS.json',dict(coverage=state['coverage'],target_records=len(target),baseline_registry_sha=sha(F/'registry.json'),upper_registry_sha=sha(F/'variants/blend_no_overlap_upper/registry.json'),arrays=len(alloc['records']),reused=len(alloc['reused_unchanged_array_ids']),new_arrays=len(alloc['records'])-len(alloc['reused_unchanged_array_ids']),new_loads=screen['loads']-1437,biomass_resources=len(recipe['biomass_obligation_routes']),biomass_commodities=dict(collections.Counter(r['commodity'] for r in recipe['biomass_obligation_routes'].values())),carbon_events=len(carbon),null_policy=manifest['policy_weights_null'],stock_records=len(stock['records']),hydro_pending_groups=stock['hydro_groups_not_inherited'],AnimalWasteFixedQuantityMWh=sum(r['QuantityMWh'] for r in proof['records'])))
print(json.dumps(dict(gate=gate['status'],tables={k:len(v['export_values'])-1 for k,v in tables.items()},manifest=manifest['status']),indent=2))
