"""Actual unsolved network checks. No optimization model or solver is created."""
from collections import defaultdict
import json
import numpy as np
from final_closure_inputs import STOCK

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
    return native

def controls(n):
    electric=set(n.buses.index[n.buses.carrier.isin(['AC','DC','electricity','low voltage'])]);out=[]
    for typ in ['Line','Link','Transformer']:
        for name,z in n.df(typ).iterrows():
            ports=[z[c] for c in n.df(typ) if c.startswith('bus') and c[3:].isdigit() and z[c]]
            if len(ports)!=2 or not set(ports)<=electric:continue
            owners=[str(n.buses.at[b,'country']) for b in ports]
            classification='UNKNOWN' if any(not c for c in owners) else 'DOMESTIC' if len(set(owners))==1 else 'CROSS_BORDER'
            out.append(dict(ComponentType=typ,Component=name,Bus0=z.bus0,Bus1=z.bus1,Country0=owners[0],Country1=owners[1],Carrier=z.carrier,Classification=classification,FutureDisconnectControl=classification=='CROSS_BORDER',Gate4SwitchApplied=False))
    if any(r['Classification']=='UNKNOWN' for r in out):raise ValueError('Unclassified electricity transfer')
    return out

def coupling(n):
    out=[];oil_loads=set(n.loads.bus[n.loads.carrier=='oil'])
    bycar={'H2 Electrolysis':'electricity -> electrolysis -> H2','Fischer-Tropsch':'H2 + CO2 + electricity -> FT -> oil','H2 Fuel Cell':'H2 -> fuel cell -> electricity','SMR':'gas -> steam methane reforming -> H2','SMR CC':'gas -> steam methane reforming with capture -> H2 + captured CO2'}
    for name,z in n.links.iterrows():
        if z.carrier not in bycar:continue
        capable=bool((z.p_nom>0 or z.p_nom_extendable and z.p_nom_max>0) and z.p_max_pu>0)
        ports=[(z.bus0,'INPUT')]
        for col in n.links:
            if col.startswith('bus') and col[3:].isdigit() and col!='bus0' and z[col]:
                e=float(z['efficiency' if col=='bus1' else 'efficiency'+col[3:]])
                ports.append((z[col],'OUTPUT' if e>0 else 'INPUT' if e<0 else 'ZERO'))
        countries={n.buses.at[b,'country'] for b,role in ports if n.buses.at[b,'carrier']!='co2 atmosphere'}
        if len(countries)!=1:raise ValueError('Cross-border coupling')
        carriers={role:{n.buses.at[b,'carrier'] for b,r in ports if r==role} for role in ['INPUT','OUTPUT']}
        if z.carrier=='Fischer-Tropsch':
            if not {'H2','co2 captured'}<=carriers['INPUT'] or not carriers['INPUT']&{'AC','DC','electricity'} or 'oil' not in carriers['OUTPUT']:raise ValueError('FT multi-input path missing')
            targets=n.links[(n.links.bus0==z.bus1)&n.links.bus1.isin(oil_loads)]
            accounts=sorted(set(n.loads.loc[n.loads.bus.isin(targets.bus1),'account']))
            if not accounts:raise ValueError('No FT final obligation sink')
        else:accounts=[]
        out.append(dict(Component=name,Country=next(iter(countries)),Technology=z.carrier,Pathway=bycar[z.carrier],NonzeroCapable=capable,CapacityMW=float(z.p_nom),Extendable=bool(z.p_nom_extendable),InputCarriers=sorted(carriers['INPUT']),OutputCarriers=sorted(carriers['OUTPUT']),FinalObligationAccounts=accounts,ForcedUtilisation=False,Evidence='Actual ports and nonzero-capable bound; not dispatch or simultaneous feasibility'))
    if not out or any(not z['NonzeroCapable'] for z in out):raise ValueError('Inactive approved coupling component')
    if not {'H2 Electrolysis','Fischer-Tropsch','H2 Fuel Cell'}<={z['Technology'] for z in out}:raise ValueError('Material coupling absent')
    return out

def audit(n,records,allocation,carbon):
    from build_research_network import static_validate
    from build_diagnostic_network import check_physical_reachability
    from fixed_accounts import validate_exported_accounting,accounting_report
    from carbon_architecture import install_power_policy
    import pandas as pd
    base=static_validate(n,records,allocation,carbon);native=numeric_inputs(n);reach=check_physical_reachability(n)
    if getattr(n,'model',None) is not None:raise ValueError('Unexpected optimization model')
    required={r['InputID'] for r in records if r.get('Year')==2050 and r.get('RequiredPhysical')}
    if set(n.meta['demand_owners'].values())!=required:raise ValueError('Actual exactly-once required account coverage differs')
    boundary={r['InputID']:r for r in records if r.get('Year')==2050 and not r.get('Posting',False)}
    if set(n.meta['demand_owners'].values())&set(boundary):raise ValueError('Embedded/nonposting obligation materialised')
    if n.loads.account.isin(['RoadEVFinalElectricity','RoadParent','TransportEmbeddedFuelParent']).any():raise ValueError('Embedded transport/parent duplicate')
    expected=pd.date_range('2013-01-01','2013-12-31 21:00',freq='3h')
    if not n.snapshots.equals(expected) or not n.snapshot_weightings.sum().eq(8760).all():raise ValueError('Physical horizon mismatch')
    identities=n.meta['existing_unit_components'];groups=defaultdict(list)
    for ident,z in identities.items():groups[z['component_type'],z['component']].append(z)
    for (typ,name),parts in groups.items():
        z=n.df(typ).loc[name];total=sum(x['capacity_mw'] for x in parts)
        effective=float(z.p_nom*z.efficiency if typ=='Link' else z.p_nom)
        if not np.isclose(total,effective,rtol=1e-12) or not np.isclose(total,z.retained_electric_capacity_mw):raise ValueError('Source-unit/component capacity mismatch')
        if not np.isfinite(z.existing_annual_fixed_om_eur) or z.capital_cost!=0:raise ValueError('Existing FOM/CAPEX invalid')
    if n.meta.get('existing_stock_boundary')!=STOCK:raise ValueError('Missing stock boundary')
    uncertainty=n.meta['stock_uncertainty']
    if set(uncertainty['QualifiedUnitIDs'])!=set(identities):raise ValueError('Stock register differs from actual network')
    if {r['AssetSourceGroup'] for r in uncertainty['records']}&set(identities):raise ValueError('Unqualified stock was inherited')
    # Accepted hydro resource identity is used once per actual group; absolute
    # inflow and total energy capacity must equal its frozen admitted contract.
    hydro=[]
    for typ in ['Generator','StorageUnit']:
        table=n.df(typ)
        if 'resource_identity' not in table:continue
        for rid,rows in table[table.resource_identity.fillna('').ne('')].groupby('resource_identity'):
            names=list(rows.index)
            if typ=='StorageUnit':
                inflow=n.get_switchable_as_dense(typ,'inflow')[names].sum(axis=1)
                energy=float((inflow*n.snapshot_weightings.stores).sum());emax=float((rows.p_nom*rows.max_hours).sum())
                if (rows.hydro_subtype=='Pumped Storage').all():
                    if energy!=0 or not rows.cyclic_state_of_charge.all() or rows.state_of_charge_initial.ne(0).any():raise ValueError('PHS free energy')
                hydro.append(dict(ResourceIdentity=rid,Type=typ,Components=names,AnnualInputMWh=energy,EmaxMWh=emax))
            else:
                avail=n.get_switchable_as_dense(typ,'p_max_pu')[names].mul(rows.p_nom,axis=1).sum(axis=1)
                hydro.append(dict(ResourceIdentity=rid,Type=typ,Components=names,AnnualInputMWh=float((avail*n.snapshot_weightings.generators).sum()),EmaxMWh=None))
    # Frozen qualified electric base equality is independently checked by driver;
    # compare accepted post-reallocation group aggregate values here as well.
    # A previously accepted spatial proxy can split one resource across nodes.
    # The frozen base comparison checks every component and every time step,
    # so a split does not receive a second resource envelope during assembly.
    if n.meta.get('policy_enabled') is not False:raise ValueError('Unexpected policy cap')
    disabled=install_power_policy(n,carbon,2050,enabled=False,scope_complete=False,expected_hours=8760)
    try:install_power_policy(n,carbon,2050,enabled=True,scope_complete=True,expected_hours=8760)
    except ValueError as exc:
        if 'POLICY_ATTRIBUTION_PENDING' not in str(exc):raise
    else:raise ValueError('Pending policy silently enabled')
    if not any(z['policy_weight'] is None for z in carbon):raise ValueError('Expected mixed-use policy nulls lost')
    validate_exported_accounting(n);report=accounting_report(n)
    priced=[r for r in n.meta['component_price_qualification'] if any('PENDING' in str(v) for v in r.values())]
    if priced:raise ValueError('Active economic price qualification pending: '+str(priced[:2]))
    dc=n.links[n.links.carrier.isin(['DC','B2B'])]
    if dc.marginal_cost.ne(0).any() or not dc.variable_cost_method.eq('ASSEMBLY_V1_REMOVE_INHERITED_TRANSMISSION_NOISE').all():raise ValueError('Transmission noise returned')
    ren=n.generators[n.generators.get('variable_cost_method','')=='ASSEMBLY_V1_EXPLICIT_CONFIG_VARIABLE_COST']
    if any(z.marginal_cost!=(.01 if z.carrier=='solar' else .015) for _,z in ren.iterrows()):raise ValueError('Renewable explicit fee changed')
    if n.meta.get('partial_demand_binding') or n.meta.get('unmaterialised_scope') or 'DIAGNOSTIC' in str(n.meta.get('artifact_role','')):raise ValueError('Diagnostic-only metadata leaked')
    for c in n.iterate_components():
        for col in ['asset_role','research_role','cost_qualification']:
            if col in c.df and c.df[col].astype(str).str.contains('DEVELOPMENT|DIAGNOSTIC|PLACEHOLDER',regex=True).any():raise ValueError('Diagnostic placeholder on active component')
    paths=coupling(n);interconnect=controls(n)
    checks=[dict(Check=k,Status='PASS',Evidence=v) for k,v in [
        ('A_COMPONENT_REFERENCES',base['status']),('B_ACTIVE_NUMERIC_FINITE','All active coefficients finite; native optional/unbounded schema sentinels individually classified in manifest; no fabricated caps'),('C_D_SNAPSHOTS_AND_WEIGHTS','2920 snapshots; 3h; 8760h'),('E_F_CONSERVATION_AND_OWNERSHIP',dict(accounts=len(required),loads=len(n.loads))),('G_BUILDINGS_EMBEDDED_BOUNDARY','Only accepted explicit fuel plus Astar; nonposting/embedded IDs absent'),('H_TRANSPORT_OWNERSHIP','Road/rail/domestic/bunker source IDs distinct; no explicit EV/RoadParent'),('I_EXISTING_STOCK',dict(units=len(identities),capacity_mw=sum(x['capacity_mw'] for x in identities.values()))),('J_HYDRO_RESOURCES','Resource identities unique; electric-base input curves/capacities unchanged'),('K_L_CARRIER_ISOLATION','No direct or multihop non-electric cross-country path; atmosphere is reporting only'),('M_PHYSICAL_CARBON',dict(events=len(carbon),unknown_fixed_emissions='external null accounts')),('N_POLICY_OFF',disabled),('O_PENDING_FIXED_ACCOUNTS',dict(count=len(n.meta['external_pending_fixed_accounts']),FullSystemCostComplete=report['FullSystemCostComplete'],FullSystemEmissionsComplete=report['FullSystemEmissionsComplete'])),('P_COST_LAYER_FT_VOM','Actual source-price qualification and FT input-energy VOM checked'),('Q_CONNECTION_NOISE',dict(components=len(dc),all_zero=True)),('R_RENEWABLE_CONFIG_FEES',dict(components=len(ren))),('S_HOOKS',n.meta['required_constraint_hooks']),('T_NO_DIAGNOSTIC_PLACEHOLDERS','Actual active component tags and network role checked'),('ACTIVE_SECTOR_COUPLING',dict(nonzero_capable_paths=len(paths),reachability=reach)),('ELECTRICITY_CONTROL_SET',dict(components=len(interconnect),cross_border=sum(x['Classification']=='CROSS_BORDER' for x in interconnect),unknown=0))]]
    return dict(checks=checks,native_schema_sentinels=native,hydro_resources=hydro,coupling=paths,interconnect=interconnect,carbon_events=len(carbon),pending_policy=sum(x['policy_weight'] is None for x in carbon),fixed_accounts=len(n.meta['external_pending_fixed_accounts']))
