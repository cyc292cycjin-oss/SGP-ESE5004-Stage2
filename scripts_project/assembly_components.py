"""Shared production/synthetic assembly mechanics; no solver or scientific defaults."""
from copy import deepcopy
import numpy as np

def check_global_constraints(n):
    """Every GlobalConstraint must be reviewed. S1: carbon caps are not GlobalConstraints; the
    per-country net-zero limit is the research_country_net_zero hook (country_carbon.py) so
    that every atmosphere Store, not an aggregate carrier coefficient, carries the policy."""
    approved=n.meta.get('approved_global_constraints',[])
    for name,r in n.global_constraints.iterrows():
        attr=str(r.get('carrier_attribute','')).lower()
        if ('co2' in attr or 'carbon' in attr) and r['type']=='primary_energy':
            raise ValueError('Carrier-coefficient carbon cap would double count Link atmosphere ports (U4); use the country hook')
        if name not in approved:raise ValueError('Unreviewed system constraint '+name)
    return True

def merge_input_components(n,sub):
    if len(sub.loads) or sub.meta.get('partial_demand_binding'):raise ValueError('Bound development fragment cannot enter final assembly')
    if not n.snapshots.equals(sub.snapshots) or set(n.snapshot_weightings)!=set(sub.snapshot_weightings):raise ValueError('Fragment time boundary mismatch')
    # NetCDF may reorder named weight columns. Compare each physical meaning,
    # not serialization order; unequal weights still fail exactly.
    aligned=sub.snapshot_weightings.reindex(columns=n.snapshot_weightings.columns)
    if not n.snapshot_weightings.equals(aligned):raise ValueError('Fragment time boundary mismatch')
    # Import carrier/bus definitions before their dependent components.
    priority={'Carrier':0,'Bus':1,'LineType':2,'TransformerType':3}
    for comp in sorted(sub.iterate_components(),key=lambda c:(priority.get(c.name,4),c.name)):
        duplicate=comp.df.index.intersection(n.df(comp.name).index)
        if comp.name in ['LineType','TransformerType']:
            if not comp.df.loc[duplicate].equals(n.df(comp.name).loc[duplicate]):raise ValueError('Conflicting equipment type library')
            continue
        if len(duplicate) and comp.name not in ['Bus','Carrier']:raise ValueError('Duplicate base/fragment component '+comp.name)
        for k in duplicate:
            if comp.name=='Bus' and any(comp.df.at[k,col]!=n.buses.at[k,col] for col in ['country','carrier']):raise ValueError('Mismatched physical attachment identity')
            if comp.name=='Carrier' and comp.df.at[k,'co2_emissions']!=n.carriers.at[k,'co2_emissions']:raise ValueError('Carrier carbon-factor mismatch')
        table=comp.df.loc[comp.df.index.difference(n.df(comp.name).index)]
        if len(table):n.import_components_from_dataframe(table,comp.name)
        for attr,frame in comp.pnl.items():
            if not len(frame.columns):continue
            if 'Output' in str(comp.attrs.at[attr,'status']):raise ValueError('Solved fragment output rejected')
            if len(frame.columns.intersection(n.pnl(comp.name)[attr].columns)):raise ValueError('Duplicate time-series component')
            n.import_series_from_dataframe(frame,comp.name,attr)
    for key,value in sub.meta.items():
        if key not in n.meta:n.meta[key]=deepcopy(value)
        elif isinstance(value,dict) and isinstance(n.meta[key],dict):
            collision=set(value)&set(n.meta[key])
            if any(value[k]!=n.meta[key][k] for k in collision):raise ValueError('Conflicting constraint metadata '+key)
            n.meta[key].update(deepcopy(value))
        elif key=='required_constraint_hooks':n.meta[key]=sorted(set(n.meta[key])|set(value))
        elif n.meta[key]!=value:raise ValueError('Conflicting fragment metadata '+key)
    return n

def bind_loads(n,records,manifest,arrays,destinations):
    if len(n.loads) or n.meta.get('demand_owners'):raise ValueError('Demand may be bound only once')
    lookup={r['InputID']:r for r in records};n.meta['demand_owners']={};n.meta['demand_identity']={}
    for ar in manifest['records']:
        r=lookup[ar['InputID']]
        for j,node in enumerate(ar['Nodes']):
            values=arrays[ar['ArrayKey']][:,j]
            if not np.any(values):continue
            key=r['InputID']+'@'+node;dest=destinations[key]
            if not isinstance(dest,dict):raise ValueError('Destination lacks explicit carrier/account contract')
            bus=dest['bus']
            if dest['source_carrier']!=r['Carrier'] or dest['account']!=r['Account']:raise ValueError('Demand destination incompatible with source fuel/account')
            if bus not in n.buses.index or n.buses.at[bus,'country']!=r['Country']:raise ValueError('Missing/misowned demand destination')
            # S1: a demand may sit on the physical carrier bus itself (electricity, H2, heat, ...)
            # or on a legacy '<carrier> final energy' interface; the old electricity/final-energy
            # whitelist blocked sector Loads (S2 will add them through this same single binding).
            expected={'electricity':['AC','DC','electricity','low voltage']}.get(dest['carrier'],[dest['carrier'],dest['carrier']+' final energy'])
            if n.buses.at[bus,'carrier'] not in expected:raise ValueError('Destination physical carrier mismatch')
            if dest['carrier'] not in n.carriers.index:n.add('Carrier',dest['carrier'],co2_emissions=0.)
            n.add('Load',key,bus=bus,carrier=dest['carrier'],p_set=values)
            for col,val in [('sector',dest['sector']),('account',r['Account']),('source_account_id',r['InputID']),('country',r['Country']),('demand_owner_kind','REGISTRY')]:n.loads.loc[key,col]=val
            n.meta['demand_owners'][key]=r['InputID'];n.meta['demand_identity'][key]=dict(carrier=dest['carrier'],sector=dest['sector'],account=r['Account'],country=r['Country'],owner_kind='REGISTRY')

def register_upstream_loads(n,names,function,sector):
    """S1-1: every Load created by an upstream prepare_sector_network function is written
    into the single demand ownership table exactly once (owner = the upstream function)."""
    n.meta.setdefault('demand_owners',{});n.meta.setdefault('demand_identity',{})
    for name in names:
        if name not in n.loads.index:raise ValueError('Upstream Load missing: '+name)
        if name in n.meta['demand_owners']:raise ValueError('Demand bound twice: '+name)
        z=n.loads.loc[name];country=n.buses.at[z.bus,'country']
        if country not in {'BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN'}:raise ValueError('Upstream Load without country: '+name)
        owner='UPSTREAM:'+function+':'+name
        for col,val in [('sector',sector),('account','UPSTREAM:'+function),('source_account_id',owner),('country',country),('demand_owner_kind','UPSTREAM_FUNCTION')]:n.loads.loc[name,col]=val
        n.meta['demand_owners'][name]=owner;n.meta['demand_identity'][name]=dict(carrier=str(z.carrier),sector=sector,account='UPSTREAM:'+function,country=country,owner_kind='UPSTREAM_FUNCTION')
    return list(names)

def validate_hooks(n):
    from carrier_architecture import install_fragment_constraints
    if not callable(install_fragment_constraints):raise ValueError('Missing constraint hook implementation')
    if n.meta.get('store_power_rules') and 'install_fragment_constraints' not in n.meta.get('required_constraint_hooks',[]):raise ValueError('Storage-direction hook contract lost')
    for name,rule in n.meta.get('store_power_rules',{}).items():
        if name not in n.stores.index or rule not in ['charge_only','discharge_only']:raise ValueError('Invalid persisted Store hook')
    for name in n.meta.get('external_annual_caps',{}):
        if name not in n.generators.index:raise ValueError('Annual cap points to missing source')
    # S1 adds the per-country net-zero hook and the existing cross-border FOM hook.
    allowed={'install_fragment_constraints','research_battery_inverter_capacity_equality','research_existing_assets','research_country_net_zero','research_cross_border_existing_fom',
             'research_co2_storage_cap','research_gap_diagnostic',  # S2: national storage cap; gap diagnostic replaces the hard net-zero limit (decisions 49, 53)
             'research_new_hydro_inflow','research_nuclear_national_cap',  # S4B-2 (decisions 78, 79): new-reservoir inflow tied to built capacity; nuclear plan caps (sensitivity)
             'research_bunker_net_zero',  # S4C-3 (decision 88): ASEAN international bunker account, net zero on its own
             'research_apg_corridor_cap',  # S4F-1 (decision 96): APG / AIMS plan caps per project group (apg_plans sensitivity)
             'research_lossy_bidirectional_sync'}  # S4J-2 (decision 105 a): reverse capacity = forward capacity of the split lossy links (PyPSA-Eur Link-bidirectional_sync); the S4J-3 hook research_b2b_follows_dc is withdrawn (decision 107 a)
    if set(n.meta.get('required_constraint_hooks',[]))-allowed:raise ValueError('Unknown required physical hook')
    if n.meta.get('existing_unit_components'):
        if 'research_existing_assets' not in n.meta.get('required_constraint_hooks',[]):raise ValueError('Existing cost/resource hook lost')
        total=0.;seen=set()
        for ident in n.meta['existing_unit_components'].values():
            row=n.df(ident['component_type']).loc[ident['component']]
            if row.asset_role!='existing_survivor' or row.p_nom_extendable or row.capital_cost!=0:raise ValueError('Existing capital ownership lost')
            key=(ident['component_type'],ident['component'])
            if key not in seen:total+=float(row.existing_annual_fixed_om_eur);seen.add(key)
        if not np.isclose(total,n.meta['existing_annual_fixed_om_eur']):raise ValueError('Existing fixed OM lost')
    for pair in n.meta.get('battery_inverter_pairs',[]):
        a,b=pair['charger'],pair['discharger']
        if a not in n.links.index or b not in n.links.index or n.links.at[a,'bus1']!=n.links.at[b,'bus0']:raise ValueError('Battery coupling identity lost')
        if not n.links.at[a,'p_nom_extendable'] or not n.links.at[b,'p_nom_extendable']:raise ValueError('Battery nominal variable missing')
    return True

def install_research_constraint_hooks(n,execution_context=None):
    """Future optimisation must call this after variables exist; never solves."""
    if n.meta.get('artifact_role')=='DIAGNOSTIC_PARTIAL_UNSOLVED':raise ValueError('Diagnostic partial network cannot install optimization constraints')
    from gate6_execution_context import PROTECTED_ROLES,checked
    if execution_context is not None:
        checked(execution_context).permit_hooks(n)
    elif n.meta.get('solver_allowed') is False or n.meta.get('artifact_role') in PROTECTED_ROLES or 'gate6_execution_record' in n.meta:
        raise ValueError('Explicit next-gate authorization required before optimization hooks')
    validate_hooks(n)
    from carrier_architecture import install_fragment_constraints
    install_fragment_constraints(n)
    if n.meta.get('existing_unit_components'):
        from integrate_surviving_assets import install_existing_asset_constraints
        install_existing_asset_constraints(n)
    for i,pair in enumerate(n.meta.get('battery_inverter_pairs',[])):
        a,b=pair['charger'],pair['discharger'];eff=float(n.links.at[b,'efficiency'])
        n.model.add_constraints(n.model['Link-p_nom'].sel({'Link-ext':a})-eff*n.model['Link-p_nom'].sel({'Link-ext':b})==0,name='ResearchBatteryNominal-'+str(i))
    hooks=set(n.meta.get('required_constraint_hooks',[]))
    if 'research_country_net_zero' in hooks:
        from country_carbon import add_country_net_zero
        add_country_net_zero(n,n.snapshots)
    if 'research_cross_border_existing_fom' in hooks:
        from scenario_network import install_existing_cross_border_fom
        install_existing_cross_border_fom(n)
    if 'research_co2_storage_cap' in hooks:
        from s2_layers import install_co2_storage_cap
        install_co2_storage_cap(n)
    if 'research_gap_diagnostic' in hooks:
        from s2_layers import install_gap_diagnostic
        install_gap_diagnostic(n)
    if 'research_new_hydro_inflow' in hooks:
        from s4b_candidates import install_new_hydro_inflow_tie
        install_new_hydro_inflow_tie(n)
    if 'research_nuclear_national_cap' in hooks:
        from s4b_candidates import install_nuclear_national_cap
        install_nuclear_national_cap(n)
    if 'research_bunker_net_zero' in hooks:
        from s4c_layers import install_bunker_net_zero
        install_bunker_net_zero(n)
    if 'research_apg_corridor_cap' in hooks:
        from s4f_layers import install_apg_corridor_cap
        install_apg_corridor_cap(n)
    if 'research_lossy_bidirectional_sync' in hooks:
        from s4j_layers import install_lossy_bidirectional_sync
        install_lossy_bidirectional_sync(n)
