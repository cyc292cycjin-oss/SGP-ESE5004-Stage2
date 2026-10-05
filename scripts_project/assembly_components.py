"""Shared production/synthetic assembly mechanics; no solver or scientific defaults."""
from copy import deepcopy
import numpy as np

def check_global_constraints(n):
    approved=n.meta.get('approved_global_constraints',[])
    for name,r in n.global_constraints.iterrows():
        attr=str(r.get('carrier_attribute','')).lower()
        if ('co2' in attr or 'carbon' in attr) and r['type']=='primary_energy':
            raise ValueError('Unapproved carbon policy constraint')
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
            expected={'electricity':['AC','DC','electricity','low voltage']}.get(dest['carrier'],[dest['carrier']+' final energy'])
            if n.buses.at[bus,'carrier'] not in expected:raise ValueError('Destination physical carrier mismatch')
            if dest['carrier'] not in n.carriers.index:n.add('Carrier',dest['carrier'],co2_emissions=0.)
            n.add('Load',key,bus=bus,carrier=dest['carrier'],p_set=values)
            for col,val in [('sector',dest['sector']),('account',r['Account']),('source_account_id',r['InputID']),('country',r['Country'])]:n.loads.loc[key,col]=val
            n.meta['demand_owners'][key]=r['InputID'];n.meta['demand_identity'][key]=dict(carrier=dest['carrier'],sector=dest['sector'],account=r['Account'],country=r['Country'])

def validate_hooks(n):
    from carrier_architecture import install_fragment_constraints
    if not callable(install_fragment_constraints):raise ValueError('Missing constraint hook implementation')
    if n.meta.get('store_power_rules') and 'install_fragment_constraints' not in n.meta.get('required_constraint_hooks',[]):raise ValueError('Storage-direction hook contract lost')
    for name,rule in n.meta.get('store_power_rules',{}).items():
        if name not in n.stores.index or rule not in ['charge_only','discharge_only']:raise ValueError('Invalid persisted Store hook')
    for name in n.meta.get('external_annual_caps',{}):
        if name not in n.generators.index:raise ValueError('Annual cap points to missing source')
    allowed={'install_fragment_constraints','research_battery_inverter_capacity_equality','research_existing_assets'}
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

def install_research_constraint_hooks(n):
    """Future optimisation must call this after variables exist; never solves."""
    validate_hooks(n)
    from carrier_architecture import install_fragment_constraints
    install_fragment_constraints(n)
    if n.meta.get('existing_unit_components'):
        from integrate_surviving_assets import install_existing_asset_constraints
        install_existing_asset_constraints(n)
    for i,pair in enumerate(n.meta.get('battery_inverter_pairs',[])):
        a,b=pair['charger'],pair['discharger'];eff=float(n.links.at[b,'efficiency'])
        n.model.add_constraints(n.model['Link-p_nom'].sel({'Link-ext':a})-eff*n.model['Link-p_nom'].sel({'Link-ext':b})==0,name='ResearchBatteryNominal-'+str(i))
