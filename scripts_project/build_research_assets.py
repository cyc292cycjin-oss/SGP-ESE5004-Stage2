"""Build real Gate4 development assets without optimisation or solved capacities.

Source inputs are allowlisted. Unresolved asset-age and carbon-origin decisions
remain explicit in manifests and prevent qualification as the full research model.
"""
from pathlib import Path
import argparse,hashlib,json,platform,subprocess,sys
import numpy as np
import pandas as pd
import pypsa
from carrier_architecture import Fragment,bus_name,external_import,to_pypsa_fragment

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
def build_electric(repo,reference,costs,oldcosts,output,survival=None):
    if sha(reference)!=REF_SHA:raise ValueError('Reference input identity changed')
    if sha(costs)!=COST2050_SHA or sha(oldcosts)!=ELECTRIC_COST2030_SHA:raise ValueError('Frozen processed cost identity changed')
    output.mkdir(parents=True,exist_ok=True);s=pypsa.Network(reference)
    c=pd.read_csv(costs,index_col=0);old=pd.read_csv(oldcosts,index_col=0)
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
    # Existing fixed input assets are retained in an explicit unresolved inventory
    # when build_year/lifetime are not supplied. They cannot qualify2050 by rename.
    for typ in ['Generator','StorageUnit']:
        src=s.df(typ);ids=src.index[(~src.p_nom_extendable)&src.bus.isin(geo)]
        d=clean_table(s,typ,ids)
        for name,z in d.iterrows():
            # Exported component build years can be grouped/imputed. They are
            # never evidence of observed commissioning. Raw-ID evidence is the
            # sole source of active existing capacity, handled separately.
            known=False
            survives=known and z.build_year<=2050<z.build_year+z.lifetime
            ledger.append(dict(type=typ,component=name,source_p_nom=float(z.p_nom),build_year=float(z.build_year),lifetime=float(z.lifetime),status='SURVIVES_2050' if survives else 'RETIRED_BEFORE_2050' if known else 'AGE_UNRESOLVED'))
            if known and not survives:d=d.drop(name);continue
            if not known:
                pending.append(dict(type=typ,component=name,OriginalCapacity=float(z.p_nom),country=str(s.buses.at[z.bus,'country']),technology=z.carrier,reason='Missing verified real commissioning/retirement age; capacity retained in inventory, NOT asserted active or zero'))
                d=d.drop(name);continue
            tech=z.carrier
            if tech in c.index:
                d.loc[name,'capital_cost']=0 if tech=='hydro' else c.at[tech,'fixed']
                d.loc[name,'marginal_cost']=c.at[tech,'marginal_cost']
        copy_input(s,n,typ,d.index,d)
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
    n.meta['asset_qualification']='DEVELOPMENT_ONLY_PENDING_SURVIVOR_QUALIFICATION'
    path=output/'electric_base_2050_unsolved.nc';actual=export_checked(n,path)
    manifest=dict(status='DEVELOPMENT_ASSET_BUILT_SURVIVOR_QUALIFICATION_PENDING',file=path.name,sha256=sha(path),target_year=2050,geographical_nodes=100,snapshots=2920,physical_hours=8760,components={c.name:len(c.df) for c in actual.iterate_components()},inputs={str(p):sha(p) for p in [reference,costs,oldcosts]},code_sha=version(repo),builder_sha256=sha(__file__),environment={'python':platform.python_version(),'pypsa':pypsa.__version__},source_allowlist='Input attributes only; reference p_nom_opt/s_nom_opt, dispatch, duals, objective excluded',cost_trace=cost_trace,existing_asset_inventory=ledger,unresolved_age_records=pending,solver_runs=0,fullsc_network_complete=False)
    if survival:
        raw=json.loads(survival.read_text());manifest['inputs'][str(survival)]=sha(survival)
        manifest['raw_asset_inventory_summary']={'source_rows':len(raw['records']),'observed_existing_rows':sum(r['AssetClass']=='OBSERVED_EXISTING' for r in raw['records']),'explicit2050_survivors':sum(r['SurvivalStatus']=='SURVIVES_2050' for r in raw['records']),'numerical_lifetime_acceptance':'PENDING; no automatic uptake of default/imputed ages'}
        if any(r['SurvivalStatus']=='SURVIVES_2050' for r in raw['records']):raise ValueError('Verified survivors now exist: source-qualified100-node mapping and existing-performance/O&M layer must be materialised before this development builder is rerun')
    save(output/'ELECTRIC_BASE_ASSET_MANIFEST.json',manifest);return n,manifest

def build_fragment(repo,base,costs,allocation,output):
    c=pd.read_csv(costs,index_col=0);source=sha(costs);geo=base.buses[base.buses.carrier.isin(['AC','DC'])];f=Fragment()
    f.bus('ReportingCO2 atmosphere','co2 atmosphere','',None,role='ATMOSPHERE')
    for node,z in geo.iterrows():
        f.bus(node,z.carrier,z.country,node)
        for fuel in ['gas','oil','coal','lignite','H2','co2 captured']:f.bus(bus_name(node,fuel),fuel,z.country,node)
    carbon=[];pending=[];routes={};dest={};allow=[]
    def event(key,sector,factor,policy,accepted=True):
        r=f.components[key];carbon.append(dict(component_type=r['type'],component=r['name'],carrier=r['carrier'],sector=sector,country=r['country'],coefficient=factor,policy_weight=policy,accepted=accepted,source=source,physical_reporting=True,policy_assignment_status='SOURCE_ROLE_DETERMINED' if accepted else 'PENDING_MIXED_USE_ATTRIBUTION'))
    for node,z in geo.iterrows():
        country=z.country
        for fuel in ['gas','oil','coal','lignite']:
            external_import(f,node,fuel,'frozen-price:'+fuel,dict(price=float(c.at[fuel,'fuel']),price_unit='EUR/MWh_fuel',source_sha256=source,source_year=2050,basis='Frozen prepared cost fuel basis; no additional currency conversion',capacity_mw=None,annual_cap_mwh=None,unlimited_annual_accepted=True,unlimited_capacity_accepted=True),accepted=True)
        def link(label,carrier,ports,coeff,tech,costfactor=1):
            inputs=[ports[0]]+[b for b,k in zip(ports[1:],coeff) if k<0];outputs=[b for b,k in zip(ports[1:],coeff) if k>0]
            pars=dict(bus_order=ports,p_nom_extendable=True,p_min_pu=0.,build_year=2050,lifetime=float(c.at[tech,'lifetime']),capital_cost=float(c.at[tech,'fixed'])*costfactor)
            pars.update({('efficiency' if i==1 else 'efficiency'+str(i)):float(k) for i,k in enumerate(coeff,1)})
            return f.add('Link',node+' '+label,country,carrier,inputs=inputs,outputs=outputs,params=pars,accepted=True,source=source)
        h=bus_name(node,'H2');gas=bus_name(node,'gas');oil=bus_name(node,'oil');co2=bus_name(node,'co2 captured');atmo='ReportingCO2 atmosphere'
        link('electrolysis','H2 Electrolysis',[node,h],[c.at['electrolysis','efficiency']],'electrolysis');allow.append('electrolysis')
        k=link('SMR','SMR',[gas,h,atmo],[c.at['SMR','efficiency'],c.at['gas','CO2 intensity']],'SMR');event(k,'Other',float(c.at['gas','CO2 intensity']),None,False)
        # Capture fraction read from effective frozen configuration, not inferred.
        from phase4_static import config
        cc=float(config(repo,'baseline')['sector']['cc_fraction']) if node==geo.index[0] else cc
        k=link('SMR CC','SMR CC',[gas,h,atmo,co2],[c.at['SMR CC','efficiency'],c.at['gas','CO2 intensity']*(1-cc),c.at['gas','CO2 intensity']*cc],'SMR CC');event(k,'Other',float(c.at['gas','CO2 intensity'])*(1-cc),None,False)
        link('fuel cell','H2 Fuel Cell',[h,node],[c.at['fuel cell','efficiency']],'fuel cell',c.at['fuel cell','efficiency'])
        allow.append('fuel_cell')
        link('FT','Fischer-Tropsch',[h,oil,co2,node],[c.at['Fischer-Tropsch','efficiency'],-c.at['oil','CO2 intensity']*c.at['Fischer-Tropsch','efficiency'],-c.at['Fischer-Tropsch','electricity-input']/c.at['Fischer-Tropsch','hydrogen-input']],'Fischer-Tropsch',c.at['Fischer-Tropsch','efficiency']);allow+=['FT','steam_methane_reforming']
        for powertech in ['OCGT','CCGT']:
            eff=float(c.at[powertech,'efficiency']);factor=float(c.at['gas','CO2 intensity'])
            k=link(powertech,powertech,[gas,node,atmo],[eff,factor],powertech,eff)
            f.components[k]['params']['marginal_cost']=float(c.at[powertech,'VOM'])*eff
            event(k,'Power',factor,1.)
        tech='hydrogen storage tank type 1 including compressor'
        f.add('Store',node+' H2 tank',country,'H2',inputs=[h],outputs=[h],role='STORAGE',params=dict(e_nom_extendable=True,e_cyclic=True,capital_cost=float(c.at[tech,'fixed']),build_year=2050,lifetime=float(c.at[tech,'lifetime'])),accepted=True,source=source)
    # Bind qualified obligation interfaces to source commodity identities; no Load
    # is created here, and incomplete obligations are never converted to zero.
    registry=json.loads((repo/'research_inputs/assembly_v1/registry.json').read_text());records={r['InputID']:r for r in registry['records']}
    reconstruction=json.loads((repo/'research_inputs/assembly_v1/sources/BASE_RECONSTRUCTION.json').read_text())
    am=json.loads((allocation/'allocation_manifest.json').read_text());arrays=np.load(allocation/am['arrays_file'],allow_pickle=False)
    if am['input_registry_sha256']!=sha(repo/'research_inputs/assembly_v1/registry.json'):raise ValueError('Allocation belongs to old registry')
    for ar in am['records']:
        r=records[ar['InputID']];sector='Buildings' if r['Account'] in ['ResidentialFuel','ServicesFuel'] else 'Industry' if r['Account']=='IndustryFinalEnergy' else 'Agriculture' if r['Account']=='AgricultureFinalEnergy' else r['Account'].replace('Bunker','').replace('Fuel','') if 'Shipping' in r['Account'] or 'Aviation' in r['Account'] else 'Transport'
        for j,node in enumerate(ar['Nodes']):
            annual=float((arrays[ar['ArrayKey']][:,j]*arrays['weights']).sum())
            if annual<=0:continue
            key=r['InputID']+'@'+node
            if r['Account']=='Astar':
                dest[key]=dict(bus=node,carrier='electricity',sector='Astar',account=r['Account'],source_carrier=r['Carrier']);continue
            fuel=r['Carrier'];final=key+' :: final obligation';f.bus(final,fuel+' final energy',r['Country'],node)
            dest[key]=dict(bus=final,carrier=fuel,sector=sector,account=r['Account'],source_carrier=fuel)
            if fuel in ['oil','gas','coal']:
                factor=float(c.at[fuel,'CO2 intensity']);pars=dict(bus_order=[bus_name(node,fuel),final,'ReportingCO2 atmosphere'],efficiency=1.,efficiency2=factor,p_nom_extendable=True,p_min_pu=0.)
                k=f.add('Link',key+' final-fuel meter',r['Country'],fuel+' final-energy accounting',inputs=[bus_name(node,fuel)],outputs=[final,'ReportingCO2 atmosphere'],role='FUEL_CARBON_METER',params=pars,accepted=True,source=source);event(k,sector,factor,0.)
            elif fuel=='biomass':
                raw=[z for z in reconstruction['selected_rows'] if z['Country']==r['Country'] and z['Account']==r['Account'] and z['Carrier']=='biomass']
                total=sum(float(z['MWh']) for z in raw)
                if total<=0:raise ValueError('Missing positive commodity composition')
                for zraw in raw:
                    commodity=zraw['Commodity'];val=annual*float(zraw['MWh'])/total;resource=key+' :: '+commodity
                    f.bus(resource,commodity,r['Country'],node)
                    store=key+' '+commodity+' fixed resource'
                    # No unsupported fossil-neutrality/CO2 factor or commodity
                    # cost is silently borrowed from the solid-biomass pool.
                    f.add('Store',store,r['Country'],commodity,outputs=[resource],role='FINITE_RESOURCE',params=dict(e_nom=val,e_initial=val,e_cyclic=False,p_min_pu=0.),accepted=True,source=zraw['RowID'])
                    f.add('Link',key+' '+commodity+' final-energy meter',r['Country'],commodity+' obligation metering',inputs=[resource],outputs=[final],role='FUEL_CARBON_METER',params=dict(efficiency=1.,p_nom_extendable=True,p_min_pu=0.),accepted=True,source=zraw['RowID'])
                    routes[store]=dict(buses=[final],commodity=commodity,source_row=zraw['RowID'],annual_cap_mwh=val,input_id=r['InputID'])
                    pending.append(dict(component=store,commodity=commodity,reason='Commodity-specific supply-cost and carbon-origin/physical-factor qualification pending; developer asset cannot supply extra power/H2'))
            else:raise ValueError('Unmapped qualified fuel '+fuel)
    arrays.close()
    raw=dict(buses=f.buses,components=f.components,markets=f.markets,demand_destinations=dest,biomass_obligation_routes=routes,approved_coupling_paths=sorted(set(allow)),qualification_blockers=['Mixed-use SMR/CC policy attribution pending','Commodity-specific biomass cost and carbon-origin/factor evidence pending'] if pending else ['Mixed-use SMR/CC policy attribution pending'])
    save(output/'carrier_fragment.json',raw);save(output/'demand_destinations.json',dest);save(output/'carbon_component_map.json',carbon)
    n=to_pypsa_fragment(f,list(base.snapshots),list(base.snapshot_weightings.generators),component_ids=list(f.components))
    n.meta.update(target_year=2050,asset_role='GATE3_PRODUCTION_FRAGMENT_DEVELOPMENT',fullsc_network_complete=False,biomass_obligation_routes=routes,required_constraint_hooks=['install_fragment_constraints'],unbound_required_demands=sum(r.get('Year')==2050 and r.get('Kind')=='DEMAND' and r.get('Classification')=='UNRESOLVED' for r in records.values()))
    path=output/'carrier_fragment_2050_unsolved.nc';actual=export_checked(n,path)
    manifest=dict(status='PRODUCTION_FRAGMENT_INSTANTIATED_CARBON_AND_COST_QUALIFICATION_PENDING',target_year=2050,geographical_nodes=100,components={x.name:len(x.df) for x in actual.iterate_components()},files={p.name:sha(p) for p in [path,output/'carrier_fragment.json',output/'demand_destinations.json',output/'carbon_component_map.json']},code_sha=version(repo),builder_sha256=sha(__file__),inputs={str(costs):source,str(allocation/'allocation_manifest.json'):sha(allocation/'allocation_manifest.json')},environment={'python':platform.python_version(),'pypsa':pypsa.__version__},loads=0,demand_interfaces=len(dest),carbon_events=len(carbon),pending_mixed_carbon_events=sum(not x['accepted'] for x in carbon),pending_bio_qualification=pending,solver_runs=0,fullsc_network_complete=False)
    save(output/'GATE3_PRODUCTION_FRAGMENT_MANIFEST.json',manifest)
    return manifest
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    for k in ['reference','costs','oldcosts','allocation','output','survival']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();n,m=build_electric(a.repo,a.reference,a.costs,a.oldcosts,a.output,a.survival);f=build_fragment(a.repo,n,a.costs,a.allocation,a.output)
    save(a.output/'asset_bundle.json',dict(status='DEVELOPMENT_ASSETS_BUILT_FULLSC_NOT_COMPLETE',source_is_solved=False,electric_base=dict(file=m['file'],sha256=m['sha256']),carrier_fragment=dict(file='carrier_fragment.json',sha256=f['files']['carrier_fragment.json']),carbon_map=dict(file='carbon_component_map.json',sha256=f['files']['carbon_component_map.json']),solver_allowed=False))
    print(json.dumps(dict(electric=m['status'],fragment=f['status'],solver_runs=0)))
if __name__=='__main__':main()
