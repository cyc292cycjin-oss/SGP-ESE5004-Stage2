"""Per-country atmosphere accounting and the 2050 net-zero limit (S1-5; decisions 9, 10).

One `co2 atmosphere {ISO2}` Bus + Store per country replaces upstream's single
`co2 atmosphere`. Every atmosphere port of a Link is booked in the atmosphere of the
country that owns the Link's physical ports, so each tonne is attributed exactly once.
The cap is an extra_functionality hook on the final-snapshot Store level, never a
carrier-coefficient GlobalConstraint (upstream U4 double counting).
"""
from collections import defaultdict
import numpy as np
import pandas as pd
from carrier_architecture import COUNTRIES,ATMOSPHERE_CARRIER,LEGACY_ATMOSPHERE,atmosphere_bus,finite

HOOK='research_country_net_zero'
SCOPES=('per_country','asean_total')

def add_country_atmosphere(n,countries=COUNTRIES):
    if ATMOSPHERE_CARRIER not in n.carriers.index:n.add('Carrier',ATMOSPHERE_CARRIER,co2_emissions=0.)
    added=[]
    for c in sorted(countries):
        b=atmosphere_bus(c)
        if b not in n.buses.index:
            n.add('Bus',b,carrier=ATMOSPHERE_CARRIER);n.buses.loc[b,'country']=c
            if 'location' in n.buses:n.buses.loc[b,'location']=''
        if b not in n.stores.index:
            n.add('Store',b,bus=b,carrier=ATMOSPHERE_CARRIER,e_nom_extendable=True,e_min_pu=-1.,e_initial=0.,e_cyclic=False,capital_cost=0.,marginal_cost=0.)
            n.stores.loc[b,'country']=c;n.stores.loc[b,'research_role']='ATMOSPHERE'
        added.append(b)
    return added

def atmosphere_buses(n):return set(n.buses.index[n.buses.carrier==ATMOSPHERE_CARRIER])

def port_columns(df):return [c for c in df if c=='bus' or (c.startswith('bus') and c[3:].isdigit())]

def component_country(n,typ,name):
    """Owner country = country of the component's non-atmosphere physical ports (unique)."""
    df=n.df(typ);z=df.loc[name];atmo=atmosphere_buses(n)
    countries={str(n.buses.at[z[c],'country']) for c in port_columns(df) if z[c] and z[c] not in atmo}
    if len(countries)!=1:raise ValueError('Ambiguous emitter country for '+typ+' '+name+': '+str(sorted(countries)))
    return countries.pop()

def reconnect_atmosphere_ports(n,legacy=LEGACY_ATMOSPHERE):
    """Move every port on the legacy global reporting bus to the emitter's national atmosphere."""
    moves=[]
    if legacy not in n.buses.index:return moves
    for col in port_columns(n.links):
        for name in list(n.links.index[n.links[col]==legacy]):
            target=atmosphere_bus(component_country(n,'Link',name));n.links.at[name,col]=target
            moves.append(dict(component_type='Link',component=name,port=col,before=legacy,after=target))
    for typ in ['Generator','Load','StorageUnit']:
        if (n.df(typ).bus==legacy).any():raise ValueError('Non-Link component on the legacy atmosphere bus: '+typ)
    for name in list(n.stores.index[n.stores.bus==legacy]):
        if n.stores.at[name,'carrier']!=ATMOSPHERE_CARRIER:raise ValueError('Foreign Store on the legacy atmosphere bus: '+name)
        n.remove('Store',name);moves.append(dict(component_type='Store',component=name,port='bus',before=legacy,after='REMOVED_REPLACED_BY_NATIONAL_STORES'))
    n.remove('Bus',legacy);moves.append(dict(component_type='Bus',component=legacy,port='',before=legacy,after='REMOVED'))
    return moves

def fix_u4(n):
    """Upstream U4: a Carrier CO2 intensity that is not zeroed double counts the Link port booking.
    The research layer books every tonne through explicit atmosphere ports, so every carrier
    intensity used by Generators must be zero. Returns the carriers that were zeroed."""
    changed=[]
    for c in n.carriers.index[n.carriers.co2_emissions.fillna(0.)!=0]:
        n.carriers.at[c,'co2_emissions']=0.;changed.append(str(c))
    return changed

def emission_registry(n):
    """Every atmosphere port exactly once with its owner country and physical coefficient."""
    atmo=atmosphere_buses(n);rows=[]
    for col in port_columns(n.links):
        for name in n.links.index[n.links[col].isin(atmo)]:
            if col=='bus0':raise ValueError('Atmosphere cannot be a Link input: '+name)
            bus=n.links.at[name,col];country=str(n.buses.at[bus,'country']);owner=component_country(n,'Link',name)
            if owner!=country:raise ValueError('Emission booked in a foreign atmosphere: '+name)
            eff='efficiency' if col=='bus1' else 'efficiency'+col[3:]
            k=finite(n.links.at[name,eff],nonnegative=False)
            rows.append(dict(component_type='Link',component=name,port=col,atmosphere=bus,country=country,carrier=str(n.links.at[name,'carrier']),asset_role=str(n.links.at[name,'asset_role']) if 'asset_role' in n.links else '',coefficient_t_per_mwh_input=k,direction='EMISSION' if k>0 else 'REMOVAL' if k<0 else 'ZERO'))
    for typ in ['Generator','Load','StorageUnit']:
        hit=n.df(typ).index[n.df(typ).bus.isin(atmo)]
        if len(hit):raise ValueError('Non-Link component attached to an atmosphere bus: '+typ+' '+','.join(hit[:3]))
    for name in n.stores.index[n.stores.bus.isin(atmo)]:
        if n.stores.at[name,'carrier']!=ATMOSPHERE_CARRIER:raise ValueError('Foreign Store on atmosphere bus: '+name)
    keys=[(r['component_type'],r['component']) for r in rows]
    if len(keys)!=len(set(keys)):raise ValueError('A component books carbon through more than one atmosphere port')
    return rows

def validate_country_attribution(n,countries=COUNTRIES):
    """Structural proof that every tonne has one owner: buses, stores, ports, U4."""
    atmo=atmosphere_buses(n);expected={atmosphere_bus(c) for c in countries}
    if atmo!=expected:raise ValueError('Atmosphere bus set differs from the 11 countries: '+str(sorted(atmo^expected)))
    for b in sorted(atmo):
        stores=n.stores.index[n.stores.bus==b]
        if len(stores)!=1 or not n.stores.at[stores[0],'e_nom_extendable'] or n.stores.at[stores[0],'e_min_pu']!=-1 or n.stores.at[stores[0],'e_cyclic'] or n.stores.at[stores[0],'e_initial']!=0:raise ValueError('Atmosphere Store contract broken at '+b)
        if n.buses.at[b,'country']!=b.split()[-1]:raise ValueError('Atmosphere bus country tag wrong: '+b)
    gens=n.generators.carrier.map(n.carriers.co2_emissions).fillna(0.)
    if (gens!=0).any():raise ValueError('U4: Generator carriers with nonzero CO2 intensity: '+','.join(sorted(set(n.generators.carrier[gens!=0]))[:5]))
    if (n.carriers.co2_emissions.fillna(0.)!=0).any():raise ValueError('U4: carrier CO2 intensity must be zero; ports book the tonnes')
    reg=emission_registry(n)
    by=defaultdict(int)
    for r in reg:by[r['country']]+=1
    return dict(atmosphere_buses=len(atmo),emission_ports=len(reg),ports_by_country=dict(sorted(by.items())),registry=reg)

def install_metadata(n,carbon_cfg):
    scope=carbon_cfg['constraint_scope']
    if scope not in SCOPES:raise ValueError('Unknown CO2 constraint scope')
    caps={c:finite(v,nonnegative=False) for c,v in carbon_cfg['country_cap_tco2'].items()}
    if set(caps)!=set(COUNTRIES):raise ValueError('country_cap_tco2 must list all 11 countries')
    n.meta['research_carbon']=dict(constraint_scope=scope,country_cap_tco2=caps,asean_total_cap_tco2=finite(carbon_cfg['asean_total_cap_tco2'],nonnegative=False),hook=HOOK,method='final-snapshot Store level of each national atmosphere <= cap; removals allowed via e_min_pu=-1')
    n.meta['required_constraint_hooks']=sorted(set(n.meta.get('required_constraint_hooks',[]))|{HOOK})
    return n.meta['research_carbon']

def add_country_net_zero(n,sns):
    """extra_functionality hook: final-snapshot atmosphere level per country <= configured cap."""
    if getattr(n,'_research_country_net_zero_model',None) is n.model:raise ValueError('Country net-zero hook already installed')
    cfg=n.meta['research_carbon'];m=n.model;e=m['Store-e'];last=sns[-1]
    stores=[atmosphere_bus(c) for c in sorted(COUNTRIES)]
    if any(s not in n.stores.index for s in stores):raise ValueError('National atmosphere Store missing')
    if cfg['constraint_scope']=='per_country':
        for ct in sorted(COUNTRIES):
            m.add_constraints(e.sel(snapshot=last,Store=atmosphere_bus(ct))<=float(cfg['country_cap_tco2'][ct]),name='research_country_co2_limit-'+ct)
    elif cfg['constraint_scope']=='asean_total':
        expr=sum(e.sel(snapshot=last,Store=s) for s in stores)
        m.add_constraints(expr<=float(cfg['asean_total_cap_tco2']),name='research_asean_co2_limit')
    else:raise ValueError('Unknown CO2 constraint scope')
    n._research_country_net_zero_model=m

def emission_report(n):
    """Post-solve: tonnes per country by source carrier; reconciled with the Store level once."""
    w=n.snapshot_weightings.stores;reg=emission_registry(n);rows=[];by_country=defaultdict(float)
    for r in reg:
        flow=n.links_t['p'+r['port'][3:]][r['component']]  # PyPSA port flow; negative = delivered to the atmosphere bus
        tonnes=float((-flow*w).sum());rows.append(dict(r,annual_tco2=tonnes));by_country[r['country']]+=tonnes
    store_level={c:float(n.stores_t.e[atmosphere_bus(c)].iloc[-1]) for c in sorted(COUNTRIES)}
    recon={c:dict(sum_of_ports=by_country.get(c,0.),store_final_level=store_level[c],difference=by_country.get(c,0.)-store_level[c],cap=n.meta['research_carbon']['country_cap_tco2'][c]) for c in sorted(COUNTRIES)}
    exactly_once=all(abs(v['difference'])<=1e-3+1e-7*max(abs(v['sum_of_ports']),abs(v['store_final_level'])) for v in recon.values())
    by_source=defaultdict(float)
    for r in rows:by_source[r['country']+'|'+r['carrier']]+=r['annual_tco2']
    return dict(ports=rows,by_country=dict(sorted(by_country.items())),by_country_source={k:v for k,v in sorted(by_source.items())},store_final_level=store_level,reconciliation=recon,every_tonne_booked_once=exactly_once,asean_total=sum(by_country.values()))
