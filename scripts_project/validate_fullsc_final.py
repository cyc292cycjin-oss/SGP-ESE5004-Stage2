"""Actual unsolved network checks. No optimization model or solver is created.

S1: `controls` reports every tagged transport edge (electricity, H2, gas, CO2);
`coupling` reports conversion pathways without the retired fixed-obligation sink rule;
`audit` runs the S1 static validation plus numeric and reachability checks.
"""
from collections import defaultdict
import json
import numpy as np

def numeric_inputs(n):
    """Active numeric coefficients must be finite; schema sentinels are explicit.

    Native unbounded limits / optional unset controls are not numerical source
    observations. Never replace them with zero or a fabricated large capacity.
    """
    native=[]
    unbounded={'p_nom_max','s_nom_max','e_nom_max','lifetime','v_ang_min','v_ang_max','max_growth','v_mag_pu_max'}
    optional={'ramp_limit_up','ramp_limit_down','state_of_charge_set','investment_period'}
    existing_only={'source_group_capacity_mw','retained_electric_capacity_mw','existing_fixed_om_eur_per_mw_year','existing_annual_fixed_om_eur'}
    for c in n.iterate_components():
        for col in c.df.select_dtypes(include='number'):
            # Unsolved output slots/default type-library fields are not inputs.
            if col in c.attrs.index and 'Output' in str(c.attrs.at[col,'status']) and 'Input' not in str(c.attrs.at[col,'status']):continue
            v=c.df[col];bad=~np.isfinite(v)
            if not bad.any():continue
            if col in unbounded and not v[bad].isna().any():
                if col!='v_ang_min' and (v[bad]<0).any():raise ValueError('Invalid negative unbounded limit')
                native.append(dict(ComponentType=c.name,Attribute=col,Count=int(bad.sum()),Meaning='PYPSA_NATIVE_UNBOUNDED_NOT_NUMERIC_SOURCE_DATA'));continue
            if c.name=='Link' and col.startswith('efficiency') and col[10:].isdigit() and v[bad].isna().all():
                port='bus'+col[10:]
                if port in c.df and c.df.loc[bad,port].fillna('').eq('').all():
                    native.append(dict(ComponentType=c.name,Attribute=col,Count=int(bad.sum()),Meaning='NON_APPLICABLE_UNCONNECTED_LINK_PORT'));continue
            if col in optional and v[bad].isna().all():
                native.append(dict(ComponentType=c.name,Attribute=col,Count=int(bad.sum()),Meaning='PYPSA_NATIVE_OPTIONAL_CONTROL_UNSET'));continue
            if col in existing_only and v[bad].isna().all():
                active=c.df.get('asset_role',__import__('pandas').Series('',index=c.df.index)).eq('existing_survivor')
                if col=='source_group_capacity_mw':active &= c.df.get('hydro_subtype',__import__('pandas').Series('',index=c.df.index)).isin(['Reservoir','Run-Of-River'])
                if (bad&active).any():raise ValueError('Missing required existing input '+c.name+'.'+col)
                native.append(dict(ComponentType=c.name,Attribute=col,Count=int(bad.sum()),Meaning='NON_APPLICABLE_OTHER_ASSET_ROLE'));continue
            raise ValueError('Nonfinite active/unrecognized input '+c.name+'.'+col+': '+','.join(v.index[bad][:3]))
        for attr,frame in c.pnl.items():
            if len(frame.columns) and not np.isfinite(frame.to_numpy()).all():raise ValueError('Nonfinite actual time series '+c.name+'.'+attr)
    return sorted(native,key=lambda r:(r['ComponentType'],r['Attribute'],r['Meaning']))

def controls(n):
    """Every two-port transport edge with its border class and transport carrier (S1-6 tags)."""
    out=[]
    for typ in ['Line','Link','Transformer']:
        df=n.df(typ)
        if not len(df) or 'border_class' not in df:continue
        for name,z in df.iterrows():
            if z.get('transport_carrier','local')=='local':continue
            out.append(dict(ComponentType=typ,Component=name,Bus0=z.bus0,Bus1=z.bus1,Country0=str(n.buses.at[z.bus0,'country']),Country1=str(n.buses.at[z.bus1,'country']),Carrier=z.carrier,TransportCarrier=z.transport_carrier,Classification=z.border_class.upper(),Extendable=bool(z.get('s_nom_extendable',z.get('p_nom_extendable',False)))))
    if any(not r['Country0'] or not r['Country1'] for r in out):raise ValueError('Unclassified transport edge')
    return out

PATHWAYS={'H2 Electrolysis':'electricity -> electrolysis -> H2','H2 Fuel Cell':'H2 -> fuel cell -> electricity','H2 turbine':'H2 -> turbine (OCGT proxy) -> electricity','SMR':'gas -> steam methane reforming -> H2 + CO2','SMR CC':'gas -> SMR with capture -> H2 + captured CO2','Fischer-Tropsch':'H2 + CO2 + electricity -> FT -> oil','OCGT':'gas -> OCGT -> electricity + CO2','CCGT':'gas -> CCGT -> electricity + CO2'}

def coupling(n):
    out=[]
    for name,z in n.links.iterrows():
        if z.carrier not in PATHWAYS:continue
        capable=bool((z.p_nom>0 or z.p_nom_extendable and z.p_nom_max>0) and z.p_max_pu>0)
        ports=[(z.bus0,'INPUT')]
        for col in n.links:
            if col.startswith('bus') and col[3:].isdigit() and col!='bus0' and z[col]:
                e=float(z['efficiency' if col=='bus1' else 'efficiency'+col[3:]])
                ports.append((z[col],'OUTPUT' if e>0 else 'INPUT' if e<0 else 'ZERO'))
        countries={n.buses.at[b,'country'] for b,role in ports if n.buses.at[b,'carrier']!='co2 atmosphere'}
        if len(countries)!=1:raise ValueError('Conversion asset spans countries: '+name)
        carriers={role:{n.buses.at[b,'carrier'] for b,r in ports if r==role} for role in ['INPUT','OUTPUT']}
        out.append(dict(Component=name,Country=next(iter(countries)),Technology=z.carrier,Pathway=PATHWAYS[z.carrier],NonzeroCapable=capable,CapacityMW=float(z.p_nom),Extendable=bool(z.p_nom_extendable),InputCarriers=sorted(carriers['INPUT']),OutputCarriers=sorted(carriers['OUTPUT'])))
    if not out or any(not z['NonzeroCapable'] for z in out):raise ValueError('Inactive conversion pathway component')
    required={'H2 Electrolysis','H2 Fuel Cell','H2 turbine','SMR','SMR CC','Fischer-Tropsch','OCGT','CCGT'}
    if not required<={z['Technology'] for z in out}:raise ValueError('S1 conversion pathway missing')
    return out

def audit(n,cfg,corridors):
    from build_research_network import static_validate_s1
    from network_checks import check_physical_reachability
    base=static_validate_s1(n,cfg,corridors,daily=len(n.snapshots)==365);native=numeric_inputs(n);reach=check_physical_reachability(n)
    if getattr(n,'model',None) is not None:raise ValueError('Unexpected optimization model')
    paths=coupling(n);interconnect=controls(n)
    dc=n.links[n.links.carrier.isin(['DC','B2B'])]
    if dc.marginal_cost.ne(0).any():raise ValueError('Transmission noise returned')
    checks=[dict(Check=k,Status='PASS',Evidence=v) for k,v in [
        ('A_STATIC_S1',base['status']),('B_ACTIVE_NUMERIC_FINITE','All active coefficients finite; native optional/unbounded schema sentinels individually classified'),('C_D_SNAPSHOTS_AND_WEIGHTS',dict(snapshots=int(len(n.snapshots)),hours=float(n.snapshot_weightings.generators.sum()))),
        ('E_DEMAND_OWNERSHIP',base['demand']),('I_EXISTING_STOCK',base['existing_stock']),('M_COUNTRY_CARBON',dict(ports=base['carbon']['emission_ports'],countries=base['carbon']['ports_by_country'])),
        ('R_REACHABILITY',reach),('S_HOOKS',n.meta['required_constraint_hooks']),('X_CROSS_BORDER',base['cross_border']),('ACTIVE_SECTOR_COUPLING',dict(pathways=len(paths))),('TRANSPORT_CONTROL_SET',dict(components=len(interconnect),cross_border=sum(x['Classification']=='CROSS_BORDER' for x in interconnect)))]]
    return dict(checks=checks,native_schema_sentinels=native,coupling=paths,interconnect=interconnect,data_pending=base['data_pending'],static=base)
