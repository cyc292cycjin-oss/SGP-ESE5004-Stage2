"""Independent partial-network diagnostic. Never relaxes the full-model gate.

Uses current selected stock/contracts, an input-only electric base, an unbound
carrier recipe, and every qualified allocation exactly once. No model variables
are created and no solver is invoked. Persisted hooks are checked, not executed.
"""
from pathlib import Path
from collections import defaultdict
from copy import deepcopy
import argparse,json,hashlib,subprocess
import numpy as np
from check_assembly_inputs import load_registry,check,ACCEPTED
from build_research_network import pinned,load_unbound_recipe,static_validate
from assembly_components import merge_input_components,bind_loads,validate_hooks
from carrier_architecture import Fragment,to_pypsa_fragment

ROLE='DIAGNOSTIC_PARTIAL_UNSOLVED'
GUARDS=dict(artifact_role=ROLE,fullsc_network_complete=False,input_coverage_complete=False,solver_allowed=False,scientific_results_allowed=False,gate5_allowed=False)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def current_readiness(repo,allocation,root):
    folder=repo/'research_inputs/assembly_v1';data=load_registry(folder)
    gate=check(data['records'],2050,allocation,folder/'registry.json',data.get('known_unallocated_base_accounts'))
    stock=read(root/'SELECTED_ASSET_SURVIVAL_2050.json');contract=read(root/'SELECTED_INTEGRATION_CONTRACT.json')
    current=repo/'research/04_model_assembly/gate4/CURRENT_GATE4_SELECTED_MANIFEST.json'
    prior=read(current);coverage_path=repo/'research/04_model_assembly/gate4/evidence/selected/SOURCE_COVERAGE_ACCOUNT_MAP_CURRENT.json';coverage=read(coverage_path)
    missing=set(gate['unresolved_input_ids']);lookup={r['InputID']:r for r in data['records']}
    cov=[]
    for row in coverage['rows']:
        x=deepcopy(row);targets=x.get('PreviousTargets',x.get('PendingTargets',[]));x['PendingTargets']=sorted(missing&set(targets));x['RemainingPhysicalTargets']=len(x['PendingTargets']);x['CurrentStatus']='PENDING' if x['PendingTargets'] else 'SOURCE_SCOPE_NO_ADDITIONAL_FINAL_LOAD' if set(targets)&set(gate.get('source_scope_input_ids',[])) else 'CLOSED_EXISTING_SOURCE_RULE';cov.append(x)
    covered={t for x in cov for t in x['PendingTargets']}
    if covered!=missing:raise ValueError('Current source-to-target coverage map incomplete')
    groups=[x for x in contract['hydro_group_qualification']['groups'] if x['Status']=='PENDING']
    units=stock['unit_evidence']['records'];pending=[u for u in units if u['SurvivalStatus'].startswith('UNRESOLVED') or u['SurvivalStatus']=='SURVIVES_2050' and u['AssetID'] in {p['AssetID'] for p in contract['hydro_group_qualification']['pending']}]
    inventory=defaultdict(lambda:dict(count=0,capacity_mw=0.,source_ids=[]))
    for u in pending:
        k=(u['AssetID'].split(':')[0],u['Country'],u['Technology'],u['SurvivalStatus']);z=inventory[k];z['count']+=1;z['capacity_mw']+=u['OriginalCapacity'];z['source_ids'].append(u['AssetID'])
    inventory_rows=[dict(source_family=k[0],country=k[1],technology=k[2],status=k[3],**v) for k,v in sorted(inventory.items())]
    pins={str(p.relative_to(repo)):sha(p) for p in [folder/'registry.json',folder/'manifest.json',root/'SELECTED_ASSET_SURVIVAL_2050.json',root/'SELECTED_INTEGRATION_CONTRACT.json',current,coverage_path,allocation/'allocation_manifest.json',allocation/'allocations.npz']}
    qualified=[r for r in data['records'] if r['Year']==2050 and r['Kind']=='DEMAND' and r['AssemblyStatus']==ACCEPTED]
    return dict(**GUARDS,status='FULLSC_NETWORK_NOT_COMPLETE',source_pins=pins,input_gate=gate,source_scope_interpretations=[r for r in data['records'] if r.get('Classification')=='SOURCE_SCOPE_NO_ADDITIONAL_FINAL_LOAD'],qualified_demand_accounts=len(qualified),pending_physical_targets=len(missing),pending_source_combinations=sum(bool(x['PendingTargets']) and x['MappingRowType']=='ORIGINAL_SOURCE_COMBINATION' for x in cov),other_pending_target_accounts=sum(len(x['PendingTargets']) for x in cov if x['MappingRowType']!='ORIGINAL_SOURCE_COMBINATION'),pending_hydro_groups=len(groups),pending_hydro_mw=sum(x['SurvivingCapacityMW'] for x in groups),hydro_groups=groups,unmaterialised_demands=[lookup[k] for k in sorted(missing)],unmaterialised_inventory=pending,inventory_scopes=inventory_rows,inventory_scopes_not_additive='GEM/GPD identities may overlap; parent reconciliation rows are not extra stock. No combined uncertain-MW total.',coverage_map=cov,inventory_coverage_decision=contract['InventoryCoverage'],prior_selected_manifest=prior,solver_runs=0,constraint_hook_state='REGISTERED_AND_VALIDATED_NOT_EXECUTED'),data,qualified

def verify_guards(n):
    if any(n.meta.get(k)!=v for k,v in GUARDS.items()):raise ValueError('Diagnostic guard lost or changed')
    if n.meta.get('policy_enabled') is not False:raise ValueError('Diagnostic policy must be disabled')
    if getattr(n,'model',None) is not None:raise ValueError('Diagnostic must not contain optimization variables')

def assert_input_only(n):
    if len(n.loads) or n.meta.get('demand_owners'):raise ValueError('Electric base contains bound demand')
    if n.meta.get('source_is_solved') is not False or n.meta.get('input_only_extraction') is not True:raise ValueError('Base input provenance missing')
    for c in n.iterate_components():
        if not c.df.index.is_unique:raise ValueError('Nonunique '+c.name)
        if any(len(frame.columns) for attr,frame in c.pnl.items() if 'Output' in str(c.attrs.at[attr,'status'])):raise ValueError('Solved output leaked')

def compare_roundtrip(before,after):
    import pandas as pd
    if before.meta!=after.meta:raise ValueError('Diagnostic metadata changed in NetCDF roundtrip')
    if not before.snapshots.equals(after.snapshots):raise ValueError('Snapshots lost')
    pd.testing.assert_frame_equal(before.snapshot_weightings,after.snapshot_weightings.reindex(columns=before.snapshot_weightings.columns),check_dtype=False,check_freq=False)
    for c in before.iterate_components():
        other=after.df(c.name)
        if set(c.df.index)!=set(other.index):raise ValueError('Component identity changed '+c.name)
        # PyPSA may reconstruct default columns and reorder them on import.
        pd.testing.assert_frame_equal(c.df.sort_index(),other.reindex(index=c.df.index,columns=c.df.columns).sort_index(),check_dtype=False,check_names=False,check_freq=False,rtol=1e-12,atol=1e-12)
        for attr,frame in c.pnl.items():
            if len(frame.columns):pd.testing.assert_frame_equal(frame,after.pnl(c.name)[attr].reindex(columns=frame.columns),check_dtype=False,check_names=False,check_freq=False,rtol=1e-12,atol=1e-12)

def normalise_optional_strings(n):
    """Use PyPSA NetCDF's empty-string representation for absent string tags.

    Never touches numeric unknowns or JSON null fixed-cost/carbon parameters.
    Required Load and source-unit identities are checked independently.
    """
    changed={}
    for c in n.iterate_components():
        for col in c.df:
            s=c.df[col]
            if s.dtype==object and s.isna().any() and all(isinstance(x,str) for x in s.dropna()):
                changed[c.name+'.'+col]=int(s.isna().sum());c.df[col]=s.fillna('')
    return changed

def check_physical_reachability(n):
    """Structural input-to-load reachability, not dispatch/capacity feasibility."""
    import networkx as nx
    g=nx.DiGraph();g.add_nodes_from(n.buses.index);sources=set()
    for name,z in n.generators.iterrows():
        if (z.p_nom>0 or z.p_nom_extendable and z.p_nom_max>0) and z.p_max_pu>0:sources.add(z.bus)
    for _,z in n.stores.iterrows():
        if z.e_initial>0:sources.add(z.bus)
    for name,z in n.storage_units.iterrows():
        if name in n.storage_units_t.inflow and (n.storage_units_t.inflow[name]>0).any() or z.inflow>0:sources.add(z.bus)
    for _,z in n.links.iterrows():
        if not (z.p_nom>0 or z.p_nom_extendable and z.p_nom_max>0):continue
        ports={int(c[3:]):z[c] for c in n.links if c.startswith('bus') and c[3:].isdigit() and z[c]}
        inputs=[ports[0]]+[b for i,b in ports.items() if i and z['efficiency' if i==1 else 'efficiency'+str(i)]<0]
        outputs=[b for i,b in ports.items() if i and z['efficiency' if i==1 else 'efficiency'+str(i)]>0]
        for b in inputs:
            for target in outputs:g.add_edge(b,target)
        if z.p_min_pu<0 and len(ports)==2:g.add_edge(ports[1],ports[0])
    for table in [n.lines,n.transformers]:
        for _,z in table.iterrows():
            if z.s_nom>0 or z.s_nom_extendable and z.s_nom_max>0:g.add_edge(z.bus0,z.bus1);g.add_edge(z.bus1,z.bus0)
    reached=set(sources)
    for b in sources:reached.update(nx.descendants(g,b))
    missing=[name for name,z in n.loads.iterrows() if z.bus not in reached]
    if missing:raise ValueError('No structural supply path for Load '+','.join(missing[:8]))
    for name,ident in n.meta['demand_owners'].items():
        if n.loads.at[name,'source_account_id']!=ident:raise ValueError('Load source_account_id lost')
    return dict(loads_reachable=len(n.loads),source_buses=len(sources),interpretation='Necessary graph reachability only; does not establish joint multi-input, capacity or temporal feasibility')

def build(repo,allocation,assets,output,report,readiness):
    import pypsa,yaml
    from fixed_accounts import qualify_fixed_accounts,accounting_report
    from price_basis import qualify_network_costs
    config=yaml.safe_load((repo/'configs/research/baseline.yaml').read_text())
    if config['research_carbon']['policy_enabled'] or config['research_assembly']['solver_allowed']:raise ValueError('Unapproved policy or solve configuration')
    root=assets.parent;state,data,qualified=current_readiness(repo,allocation,root);save(readiness,state)
    bundle=read(assets)
    if bundle.get('source_is_solved') is not False or bundle.get('solver_allowed') is not False:raise ValueError('Asset bundle guard missing')
    n=pypsa.Network(pinned(root,bundle['electric_base']));assert_input_only(n)
    original_units=deepcopy(n.meta['existing_unit_components']);original_capacity=sum(u['capacity_mw'] for u in original_units.values())
    original_fom=n.meta['existing_annual_fixed_om_eur']
    raw=load_unbound_recipe(pinned(root,bundle['carrier_fragment']))
    if raw.get('policy_enabled') is not False:raise ValueError('Fragment policy changed')
    f=Fragment();f.buses=raw['buses'];f.components=raw['components'];f.markets=raw.get('markets',{})
    sub=to_pypsa_fragment(f,list(n.snapshots),list(n.snapshot_weightings.generators),component_ids=list(f.components))
    merge_input_components(n,sub)
    n.meta.update(**GUARDS,policy_enabled=False,target_year=2050,weather_year=2013,constraint_hook_state='REGISTERED_AND_VALIDATED_NOT_EXECUTED',biomass_obligation_routes=raw.get('biomass_obligation_routes',{}),approved_coupling_paths=raw['approved_coupling_paths'],required_constraint_hooks=sorted(set(n.meta.get('required_constraint_hooks',[]))|{'install_fragment_constraints'}))
    n.meta['unmaterialised_scope']=dict(readiness_sha256=sha(readiness),demand_ids=[r['InputID'] for r in state['unmaterialised_demands']],inventory_scopes=state['inventory_scopes'],missing_is_zero=False,pending_hydro_groups=state['hydro_groups'],source_scope_interpretations=state['source_scope_interpretations'],carrier_qualification_blockers=raw.get('qualification_blockers',[]),inventory_coverage=state['inventory_coverage_decision'])
    m=read(allocation/'allocation_manifest.json')
    if {r['InputID'] for r in m['records']}!={r['InputID'] for r in qualified}:raise ValueError('Every and only qualified account must be bound')
    with np.load(allocation/m['arrays_file'],allow_pickle=False) as z:bind_loads(n,qualified,m,z,raw['demand_destinations'])
    layer_path=pinned(root,bundle['price_layer']);qualify_network_costs(n,read(layer_path),layer_path)
    qualify_fixed_accounts(n)
    if n.meta['external_pending_fixed_accounts']!=read(pinned(root,bundle['external_fixed_accounts'])):raise ValueError('Fixed ledger changed on combination')
    n.meta['accounting_report']=accounting_report(n)
    n.meta['qualification_dimensions'].update(physical_integrity='DIAGNOSTIC_MATERIALISED_SCOPE_ONLY',input_coverage='INCOMPLETE',full_cost_report=False,full_physical_emissions_report=False,policy_constraint_qualification='DISABLED_WITH_PENDING_ATTRIBUTION')
    carbon=read(pinned(root,bundle['carbon_map']));n.meta['physical_carbon_map']=carbon
    n.meta['netcdf_optional_string_normalisation']=normalise_optional_strings(n)
    validate_hooks(n);verify_guards(n);before=static_validate(n,qualified,allocation,carbon);paths=check_physical_reachability(n)
    if original_units!=n.meta['existing_unit_components'] or original_fom!=n.meta['existing_annual_fixed_om_eur']:raise ValueError('Inherited stock/cost changed on merge')
    output.parent.mkdir(parents=True,exist_ok=True);n.export_to_netcdf(output)
    actual=pypsa.Network(output);verify_guards(actual);compare_roundtrip(n,actual);after=static_validate(actual,qualified,allocation,carbon)
    if before!=after or paths!=check_physical_reachability(actual):raise ValueError('Static results changed on roundtrip')
    n.meta['existing_unit_components']=original_units
    checks=[dict(Check=k,Status='PASS',Scope=scope,Evidence=v) for k,scope,v in [
        ('UNIQUE_COMPONENTS_AND_ENDPOINTS','MATERIALISED_SCOPE',dict(buses=len(n.buses),generators=len(n.generators),links=len(n.links),stores=len(n.stores),storage_units=len(n.storage_units))),
        ('EXACTLY_ONCE_ACCOUNT_BINDING','QUALIFIED_ACCOUNTS',dict(accounts=len(qualified),loads=len(n.loads),unique_array_keys=len({r['ArrayKey'] for r in m['records']}))),
        ('ANNUAL_DEMAND_COUNTRY_CONSERVATION','QUALIFIED_ACCOUNTS','2920 snapshots; 3h weights; source_account_id/carrier/sector/country retained'),
        ('EXISTING_STOCK_PRESERVED','QUALIFIED_STOCK',dict(source_units=len(original_units),capacity_mw=original_capacity)),
        ('NON_ELECTRIC_COUNTRY_ISOLATION','MATERIALISED_PATHS','No direct or multihop physical cross-country fuel pool'),
        ('STRUCTURAL_SUPPLY_REACHABILITY','NECESSARY_GRAPH_CONDITION_ONLY',paths),
        ('ELECTRIC_BORDER_CLASSIFICATION','MATERIALISED_TOPOLOGY',after['electricity_border_controls']),
        ('FIXED_ACCOUNT_EXCLUSIVITY','ACTUAL_COMBINED_NETWORK',dict(records=len(n.meta['external_pending_fixed_accounts']),unknown_values='null; outside priced objective')),
        ('CARBON_EVENT_IDENTITY_AND_POLICY','MATERIALISED_EVENTS',dict(events=len(carbon),pending_policy=sum(r['policy_weight'] is None for r in carbon),policy_enabled=False)),
        ('REQUIRED_HOOKS_RETAINED','REGISTRATION_NOT_EXECUTION',n.meta['required_constraint_hooks']),
        ('NETCDF_ROUNDTRIP','ALL_STATIC_AND_DYNAMIC_INPUTS_AND_META','Every component field, input series, weight and metadata compared'),
        ('DIAGNOSTIC_GUARDS','PERSISTED_AND_RELOADED',GUARDS),
        ('FULL_MODEL_GATE_STILL_CLOSED','UNCHANGED_FULL_ENTRY',state['input_gate']['status'])]]
    result=dict(**GUARDS,status='DIAGNOSTIC_STATIC_VALIDATION_PASS',network_exported=True,network_sha256=sha(output),network_file=str(output),code_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),pypsa_version=pypsa.__version__,solver_runs=0,optimization_variables_created=False,constraint_hook_state='REGISTERED_AND_VALIDATED_NOT_EXECUTED',checks=checks,source_pins=state['source_pins'],asset_bundle_sha256=sha(assets),asset_inputs={k:bundle[k] for k in ['electric_base','carrier_fragment','carbon_map','external_fixed_accounts','price_layer']},readiness_sha256=sha(readiness),qualified_accounts=len(qualified),loads=len(n.loads),source_units=len(original_units),existing_mw=original_capacity,carbon_events=len(carbon),pending_policy=sum(r['policy_weight'] is None for r in carbon),fixed_accounts=len(n.meta['external_pending_fixed_accounts']),price_qualification=n.meta['qualification_dimensions'],FullSystemCostComplete=False,FullSystemEmissionsComplete=False)
    save(report,result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    for name in ['allocation','assets','output','report','readiness']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();result=build(**vars(a));print(json.dumps({k:v for k,v in result.items() if k not in ['checks','source_pins','asset_inputs']},indent=2))
