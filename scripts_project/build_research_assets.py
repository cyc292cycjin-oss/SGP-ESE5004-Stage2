"""Build real Gate4 development assets without optimisation or solved capacities.

Source inputs are allowlisted. Unresolved asset-age and carbon-origin decisions
remain explicit in manifests and prevent qualification as the full research model.

S1 (2026-10-15): `build_fragment` no longer creates fixed final-energy accounts or
metering Links (R13); hydrogen conversion/storage comes from the upstream library
(sector_adapter.add_hydrogen); emissions are booked per country (country_carbon).
`build_electric` is unchanged; the frozen electric base is consumed by scenario_network.
"""
from pathlib import Path
import argparse,hashlib,json,platform,subprocess,sys
import numpy as np
import pandas as pd
import pypsa
from carrier_architecture import Fragment,bus_name,external_import,to_pypsa_fragment,atmosphere_bus,ATMOSPHERE_CARRIER

REF_SHA='06152be56ee41f64bfdca42fd24aeaf363ab61f931fec7b5e4bc12f6d6456ecb'
COST2050_SHA='bbcc639010a6775255730278eaa6e21ba56867d0610d3a011adc3eb60d0065f5'
ELECTRIC_COST2030_SHA='cff738dbd6077a810a4f9aaf925362522d54ddc09e3d1e6cf705a20bdc7e5ee2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,default=str)+'\n')
def version(repo):return subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
def clean_table(n,typ,index):
    # Input attributes only; *_opt, dispatch, duals, objective are never copied.
    attrs=n.component_attrs[typ];columns=[c for c in n.df(typ) if c in attrs.index and 'Input' in str(attrs.at[c,'status'])]
    return n.df(typ).loc[index,columns].copy()
def copy_input(n,out,typ,index,table=None):
    d=clean_table(n,typ,index) if table is None else table
    if not len(d):return
    out.import_components_from_dataframe(d,typ)
    for attr,df in n.pnl(typ).items():
        if attr in n.component_attrs[typ].index and 'Input' in str(n.component_attrs[typ].at[attr,'status']):
            cols=df.columns.intersection(index)
            if len(cols):out.import_series_from_dataframe(df[cols],typ,attr)
def export_checked(n,path):
    n.export_to_netcdf(path);r=pypsa.Network(path)
    if len(r.snapshots)!=2920 or not np.all(r.snapshot_weightings.to_numpy()==3):raise ValueError('Asset time boundary lost')
    if r.meta!=n.meta:raise ValueError('Asset metadata did not roundtrip')
    for c in r.iterate_components():
        for attr,d in c.pnl.items():
            if c.attrs.at[attr,'status']=='Output' and len(d.columns):raise ValueError('Solved time output leaked')
        for col in [x for x in c.df if x=='bus' or x.startswith('bus') and x[3:].isdigit()]:
            if any(x and x not in r.buses.index for x in c.df[col]):raise ValueError('Dangling asset port')
    return r
def build_electric(repo,reference,costs,oldcosts,output,survival=None,integration_contract=None,price_layer=None):
    if sha(reference)!=REF_SHA:raise ValueError('Reference input identity changed')
    if sha(costs)!=COST2050_SHA or sha(oldcosts)!=ELECTRIC_COST2030_SHA:raise ValueError('Frozen processed cost identity changed')
    output.mkdir(parents=True,exist_ok=True);s=pypsa.Network(reference)
    c=pd.read_csv(costs,index_col=0);old=pd.read_csv(oldcosts,index_col=0)
    layer=None
    if price_layer:
        from price_basis import load_table
        c,layer=load_table(price_layer,2050,costs)
    from phase4_static import config
    cfg=config(repo,'baseline')
    # Processed sector costs must represent one full physical year, not six days.
    expected=(c['discount rate']/(1-(1+c['discount rate'])**(-c.lifetime))+c.FOM/100)*c.investment
    valid=np.isfinite(expected)&np.isfinite(c.fixed)
    if not np.allclose(c.loc[valid,'fixed'],expected[valid]):raise ValueError('Unqualified annual cost scaling')
    n=pypsa.Network();n.set_snapshots(s.snapshots);n.snapshot_weightings=s.snapshot_weightings.copy()
    geo=s.buses.index[s.buses.carrier.isin(['AC','DC'])]
    if len(geo)!=100:raise ValueError('Expected100 source geographical buses')
    buses=clean_table(s,'Bus',geo);buses['country']=s.buses.loc[geo,'country'];buses['location']=geo
    n.import_components_from_dataframe(buses,'Bus');n.import_components_from_dataframe(clean_table(s,'Carrier',s.carriers.index),'Carrier')
    # Physical CO2 is attached later through explicit fuel/atmosphere interfaces.
    n.carriers['co2_emissions']=0.
    pending=[];ledger=[];cost_trace=[]
    lines=clean_table(s,'Line',s.lines.index)
    for name,z in lines.iterrows():
        if z.bus0 not in geo or z.bus1 not in geo:raise ValueError('Dangling electric line')
        t=s.line_types.loc[z['type']]
        # Recompute impedance from physical input type/length/parallel circuits.
        lines.loc[name,['r','x','b']]=[t.r_per_length*z.length/z.num_parallel,t.x_per_length*z.length/z.num_parallel,2*np.pi*t.f_nom*t.c_per_length*1e-9*z.length*z.num_parallel]
        lines.loc[name,'capital_cost']=z.length*c.at['HVAC overhead','fixed']
    n.import_components_from_dataframe(lines,'Line')
    # Preserve the legitimate transmission volume constraint as an input. Carbon
    # policy constraints are never copied from a decarbonised result.
    gc=clean_table(s,'GlobalConstraint',s.global_constraints.index)
    for name,z in gc.iterrows():
        if z['type'] not in ['transmission_volume_expansion_limit','transmission_expansion_cost_limit']:
            raise ValueError('Unapproved reference GlobalConstraint '+name)
    if len(gc):n.import_components_from_dataframe(gc,'GlobalConstraint')
    links=s.links.index[s.links.carrier.isin(['DC','B2B'])]
    d=clean_table(s,'Link',links)
    for name,z in d.iterrows():
        u=float(z.get('underwater_fraction',0));d.loc[name,'capital_cost']=z.length*(u*c.at['HVDC submarine','fixed']+(1-u)*c.at['HVDC overhead','fixed'])+c.at['HVDC inverter pair','fixed']
    copy_input(s,n,'Link',links,d)
    # Renewable candidates: no inherited endogenous investment. Source limits and
    # exogenous profiles are copied; target-year cost parameters are recomputed.
    renewable={'solar','onwind','offwind-ac','offwind-dc','solar rooftop'}
    chosen=s.generators.index[s.generators.carrier.isin(renewable)&s.generators.p_nom_extendable]
    d=clean_table(s,'Generator',chosen)
    d['asset_role']='new_build_candidate';d['source_component']=d.index
    for name,z in d.iterrows():
        tech={'solar':'solar-utility','solar rooftop':'solar-rooftop','offwind-ac':'offwind','offwind-dc':'offwind'}.get(z.carrier,z.carrier)
        newcost=c.at[tech,'fixed']
        if z.carrier.startswith('offwind'):
            ac=z.carrier;station=old.at[ac+'-station','capital_cost'];conn=z.capital_cost-old.at['offwind','capital_cost']-station
            ratios=[c.at[ac+'-connection-'+k,'fixed']/old.at[ac+'-connection-'+k,'capital_cost'] for k in ['submarine','underground']]
            if conn < -1e-8 or not np.isclose(ratios[0],ratios[1],rtol=1e-9):raise ValueError('Cannot identify2050 offshore connection cost from input-only composite '+str((name,conn,ratios)))
            conn=max(0.,conn) # floating subtraction of exactly zero input connection cost
            newcost+=c.at[ac+'-station','fixed']+conn*ratios[0]
            cost_trace.append(dict(component=name,old_electric_cost_year=2030,old_connection_cost=float(conn),common_connection_multiplier=float(ratios[0]),new2050_cost=float(newcost),rule='2050 offshore plant +2050 station + input connection composite * common unit-cost ratio; no optimised quantity'))
        if z.carrier=='onwind' and not np.isclose(z.capital_cost,old.at['onwind','capital_cost']):raise ValueError('Reference electricity cost-year premise not verified')
        d.loc[name,['p_nom','p_nom_min','build_year','capital_cost','lifetime','efficiency']]=[0,0,2050,newcost,c.at[tech,'lifetime'],c.at[tech,'efficiency']]
        d.loc[name,'marginal_cost']=cfg['costs']['marginal_cost'].get(z.carrier.split('-')[0],0. if z.carrier=='solar rooftop' else c.at[tech,'VOM'])
        if z.bus.endswith(' low voltage'):d.loc[name,'bus']=z.bus[:-12]
    # Low-voltage identity is retained by an explicit distribution asset below.
    lv=s.buses.index[s.buses.carrier=='low voltage']
    if len(lv):
        b=clean_table(s,'Bus',lv);b['country']=[s.buses.at[x[:-12],'country'] for x in lv];n.import_components_from_dataframe(b,'Bus')
        for name in chosen:
            if s.generators.at[name,'bus'] in lv:d.loc[name,'bus']=s.generators.at[name,'bus']
    copy_input(s,n,'Generator',chosen,d)
    # Reference component names/capacities are inventory evidence only. Active
    # stock comes from unit-first qualification below, never grouped build years.
    for typ in ['Generator','StorageUnit']:
        src=s.df(typ);ids=src.index[(~src.p_nom_extendable)&src.bus.isin(geo)]
        for name,z in clean_table(s,typ,ids).iterrows():
            ledger.append(dict(type=typ,component=name,source_p_nom=float(z.p_nom),build_year=float(z.build_year),lifetime=float(z.lifetime),status='REFERENCE_INPUT_INVENTORY_NOT_USED_AS_AGE_EVIDENCE'))
    # Distribution and battery input technologies are already in the frozen model.
    accepted_links={'electricity distribution grid':'electricity distribution grid','battery charger':'battery inverter','battery discharger':'battery inverter','home battery charger':'home battery inverter','home battery discharger':'home battery inverter'}
    for carrier,tech in accepted_links.items():
        ids=s.links.index[s.links.carrier==carrier];d=clean_table(s,'Link',ids)
        needed=set(d.bus0)|set(d.bus1)
        bidx=pd.Index([b for b in needed if b not in n.buses.index]);b=clean_table(s,'Bus',bidx)
        if len(b):
            b['country']=[s.buses.at[s.buses.at[x,'location'],'country'] if s.buses.at[x,'location'] in geo else next(s.buses.at[g,'country'] for g in geo if x.startswith(g+' ')) for x in bidx];n.import_components_from_dataframe(b,'Bus')
        d['build_year']=2050;d['p_nom']=0.;d['p_nom_min']=0.;d['lifetime']=c.at[tech,'lifetime'];d['marginal_cost']=0.
        d['asset_role']='new_build_candidate';d['source_component']=d.index
        d['capital_cost']=0. if 'discharger' in carrier else c.at[tech,'fixed']
        if 'battery' in carrier:d['efficiency']=np.sqrt(c.at[tech,'efficiency'])
        copy_input(s,n,'Link',ids,d)
    for carrier,tech in [('battery','battery storage'),('home battery','home battery storage')]:
        ids=s.stores.index[s.stores.carrier==carrier];d=clean_table(s,'Store',ids)
        d['build_year']=2050;d['e_nom']=0.;d['e_nom_min']=0.;d['capital_cost']=c.at[tech,'fixed'];d['lifetime']=c.at[tech,'lifetime'];d['marginal_cost']=0.
        d['asset_role']='new_build_candidate';d['source_component']=d.index
        copy_input(s,n,'Store',ids,d)
    n.meta=dict(asset_role='ELECTRIC_BASE_DEVELOPMENT_UNSOLVED',target_year=2050,weather_year=2013,solver_allowed=False,fullsc_network_complete=False,source_is_solved=False,reference_source_is_solved=True,input_only_extraction=True,asset_time_boundary='ASSEMBLY_V1_2050_SINGLE_YEAR_SURVIVING_ASSETS',unresolved_existing_asset_ages=len(pending),resource_occupancy_status='PENDING_SURVIVOR_MAPPING_TOTAL_LIMIT_ACCOUNTING',required_constraint_hooks=['research_battery_inverter_capacity_equality'],approved_global_constraints=list(n.global_constraints.index),approved_coupling_paths=[])
    pairs=[]
    for name,z in n.links[n.links.carrier.isin(['battery charger','home battery charger'])].iterrows():
        other=n.links[n.links.carrier.isin(['battery discharger','home battery discharger'])&n.links.bus0.eq(z.bus1)]
        if len(other)!=1:raise ValueError('Unpaired battery inverter')
        pairs.append(dict(charger=name,discharger=other.index[0],equation='p_nom_charger = efficiency_discharger * p_nom_discharger'))
    n.meta['battery_inverter_pairs']=pairs
    from integrate_surviving_assets import integrate_survivors,approved
    raw=json.loads(survival.read_text()) if survival else {}
    evidence=raw.get('unit_evidence')
    if evidence is None:raise ValueError('Unit-first source qualification required; aggregated ages are not a substitute')
    contract=json.loads(integration_contract.read_text()) if integration_contract else {}
    integrated=integrate_survivors(n,evidence,contract,profile_network=s)
    unresolved=[r for r in evidence['records'] if r['SurvivalStatus'].startswith('UNRESOLVED')]
    coverage_complete=all(p['CapacityReconciled'] for p in evidence['parent_reconciliation']) and not unresolved and approved(contract.get('InventoryCoverage',{}))
    qualified=coverage_complete and not integrated['pending_qualified_units']
    n.meta['unresolved_existing_asset_ages']=len(unresolved)
    n.meta['resource_occupancy_status']='QUALIFIED_SHARED_ENVELOPES' if qualified else 'PENDING_COMPLETE_STOCK_AND_RESOURCE_QUALIFICATION'
    n.meta['asset_qualification']='SOURCE_QUALIFIED_ELECTRIC_BASE_UNSOLVED' if qualified else 'DEVELOPMENT_ONLY_PENDING_SURVIVOR_QUALIFICATION'
    from selected_closure import apply_cost_choices
    apply_cost_choices(n,s,json.loads((repo/'research_inputs/asset_survival/selected_closure_decisions.json').read_text()))
    if layer:
        from price_basis import qualify_network_costs
        qualify_network_costs(n,layer,price_layer)
    path=output/'electric_base_2050_unsolved.nc';actual=export_checked(n,path)
    manifest=dict(status='DEVELOPMENT_ASSET_BUILT_SURVIVOR_QUALIFICATION_PENDING',file=path.name,sha256=sha(path),target_year=2050,geographical_nodes=100,snapshots=2920,physical_hours=8760,components={c.name:len(c.df) for c in actual.iterate_components()},inputs={str(p):sha(p) for p in [reference,costs,oldcosts]},code_sha=version(repo),builder_sha256=sha(__file__),environment={'python':platform.python_version(),'pypsa':pypsa.__version__},source_allowlist='Input attributes only; reference p_nom_opt/s_nom_opt, dispatch, duals, objective excluded',cost_trace=cost_trace,existing_asset_inventory=ledger,unresolved_age_records=pending,solver_runs=0,fullsc_network_complete=False)
    if survival:
        raw=json.loads(survival.read_text());manifest['inputs'][str(survival)]=sha(survival)
        manifest['raw_asset_inventory_summary']={'source_parent_rows':len(raw['records']),'source_unit_rows':len(evidence['records']),'unresolved_unit_records':len(unresolved),'explicit2050_survivors':sum(r['SurvivalStatus']=='SURVIVES_2050' for r in evidence['records']),'numerical_lifetime_acceptance':'Only explicit lifetime decision table or verified retirement records; candidate results excluded'}
    if integration_contract:manifest['inputs'][str(integration_contract)]=sha(integration_contract)
    manifest.update(status=n.meta['asset_qualification'],survivor_integration=integrated,unit_first_selection=True,conditional_stock_materialised=False)
    manifest['implementation_sha256']={f:sha(repo/'scripts_project'/f) for f in ['build_research_assets.py','integrate_surviving_assets.py','unit_asset_survival.py','asset_survival.py','trace_asset_survival.py','selected_closure.py','apply_selected_stock.py']}
    manifest['qualification_dimensions']=n.meta.get('qualification_dimensions',{})
    if price_layer:manifest['inputs'][str(price_layer)]=sha(price_layer)
    save(output/'ELECTRIC_BASE_ASSET_MANIFEST.json',manifest);return n,manifest

# S1: hydrogen conversion and storage are supplied by the upstream library
# (sector_adapter.add_hydrogen); the fragment must not duplicate them.
UPSTREAM_SUPPLIED=('H2 Electrolysis','H2 Fuel Cell','H2 Store Tank','H2 turbine','H2 pipeline')

def build_fragment(repo,base,costs,output,price_layer=None,cc_fraction=None):
    """Research carrier recipe for one target year: fuel pools, external fossil supply, gas power
    candidates, SMR/SMR CC/FT with explicit per-country atmosphere ports. No Load, no fixed
    account, no metering Link (S1-2). Returns (fragment, carbon_map, manifest)."""
    c=pd.read_csv(costs,index_col=0)
    layer=None
    if price_layer:
        from price_basis import load_table
        c,layer=load_table(price_layer,2050,costs)
    source=sha(costs);geo=base.buses[base.buses.carrier.isin(['AC','DC'])];f=Fragment()
    for country in sorted(set(geo.country)):f.bus(atmosphere_bus(country),ATMOSPHERE_CARRIER,country,None,role='ATMOSPHERE')
    for node,z in geo.iterrows():
        f.bus(node,z.carrier,z.country,node)
        for fuel in ['gas','oil','coal','lignite','H2','co2 captured']:f.bus(bus_name(node,fuel),fuel,z.country,node)
    carbon=[];allow=[]
    def event(key,sector,factor):
        r=f.components[key];carbon.append(dict(component_type=r['type'],component=r['name'],carrier=r['carrier'],sector=sector,country=r['country'],coefficient=factor,atmosphere=atmosphere_bus(r['country']),source=source,physical_reporting=True,attribution='COUNTRY_OF_EMITTER'))
    if cc_fraction is None:
        from phase4_static import config
        cc_fraction=float(config(repo,'baseline')['sector']['cc_fraction'])
    cc=float(cc_fraction)
    if not 0<=cc<=1:raise ValueError('Invalid source capture fraction')
    for node,z in geo.iterrows():
        country=z.country
        for fuel in ['gas','oil','coal','lignite']:
            external_import(f,node,fuel,'frozen-price:'+fuel,dict(price=float(c.at[fuel,'fuel']),price_unit='EUR/MWh_fuel',source_sha256=source,source_year=2050,basis='Frozen prepared cost fuel basis; no additional currency conversion',capacity_mw=None,annual_cap_mwh=None,unlimited_annual_accepted=True,unlimited_capacity_accepted=True),accepted=True)
        def link(label,carrier,ports,coeff,tech,costfactor=1):
            inputs=[ports[0]]+[b for b,k in zip(ports[1:],coeff) if k<0];outputs=[b for b,k in zip(ports[1:],coeff) if k>0]
            pars=dict(bus_order=ports,p_nom_extendable=True,p_min_pu=0.,build_year=2050,lifetime=float(c.at[tech,'lifetime']),capital_cost=float(c.at[tech,'fixed'])*costfactor,marginal_cost=float(c.at[tech,'VOM'])*costfactor)
            pars.update({('efficiency' if i==1 else 'efficiency'+str(i)):float(k) for i,k in enumerate(coeff,1)})
            return f.add('Link',node+' '+label,country,carrier,inputs=inputs,outputs=outputs,params=pars,accepted=True,source=source)
        h=bus_name(node,'H2');gas=bus_name(node,'gas');oil=bus_name(node,'oil');co2=bus_name(node,'co2 captured');atmo=atmosphere_bus(country)
        k=link('SMR','SMR',[gas,h,atmo],[c.at['SMR','efficiency'],c.at['gas','CO2 intensity']],'SMR');event(k,'HydrogenProduction',float(c.at['gas','CO2 intensity']))
        k=link('SMR CC','SMR CC',[gas,h,atmo,co2],[c.at['SMR CC','efficiency'],c.at['gas','CO2 intensity']*(1-cc),c.at['gas','CO2 intensity']*cc],'SMR CC');event(k,'HydrogenProduction',float(c.at['gas','CO2 intensity'])*(1-cc))
        carbon[-1].update(captured_carbon_factor=float(c.at['gas','CO2 intensity'])*cc,captured_destination=co2,capture_source='effective sector.cc_fraction')
        allow+=['steam_methane_reforming']
        link('FT','Fischer-Tropsch',[h,oil,co2,node],[c.at['Fischer-Tropsch','efficiency'],-c.at['oil','CO2 intensity']*c.at['Fischer-Tropsch','efficiency'],-c.at['Fischer-Tropsch','electricity-input']/c.at['Fischer-Tropsch','hydrogen-input']],'Fischer-Tropsch',c.at['Fischer-Tropsch','efficiency']);allow+=['FT']
        for powertech in ['OCGT','CCGT']:
            eff=float(c.at[powertech,'efficiency']);factor=float(c.at['gas','CO2 intensity'])
            k=link(powertech,powertech,[gas,node,atmo],[eff,factor],powertech,eff)
            f.components[k]['params']['marginal_cost']=float(c.at[powertech,'VOM'])*eff
            event(k,'Power',factor)
    raw=dict(artifact_role='UNBOUND_CARRIER_RECIPE',stage='S1',buses=f.buses,components=f.components,markets=f.markets,approved_coupling_paths=sorted(set(allow)),upstream_supplied_carriers=list(UPSTREAM_SUPPLIED),fixed_accounts='RETIRED_S1_2',metering_links='RETIRED_S1_2',demand_binding='scenario_network.bind_astar (electricity only in S1)')
    save(output/'carrier_fragment.json',raw);save(output/'carbon_component_map.json',carbon)
    manifest=dict(status='S1_CARRIER_RECIPE_BUILT',target_year=2050,geographical_nodes=int(len(geo)),buses=len(f.buses),components=len(f.components),carbon_events=len(carbon),files={p.name:sha(p) for p in [output/'carrier_fragment.json',output/'carbon_component_map.json']},inputs={str(costs):source},code_sha=version(repo),builder_sha256=sha(__file__),environment={'python':platform.python_version(),'pypsa':pypsa.__version__},solver_runs=0)
    if price_layer:manifest['inputs'][str(price_layer)]=sha(price_layer)
    save(output/'S1_CARRIER_FRAGMENT_MANIFEST.json',manifest)
    return f,carbon,manifest

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    for k in ['reference','costs','oldcosts','output','survival']:p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--integration-contract',type=Path)
    p.add_argument('--price-layer',type=Path,required=True)
    a=p.parse_args();n,m=build_electric(a.repo,a.reference,a.costs,a.oldcosts,a.output,a.survival,a.integration_contract,a.price_layer);f,carbon,fm=build_fragment(a.repo,n,a.costs,a.output,a.price_layer)
    print(json.dumps(dict(electric=m['status'],fragment=fm['status'],solver_runs=0)))
if __name__=='__main__':main()
