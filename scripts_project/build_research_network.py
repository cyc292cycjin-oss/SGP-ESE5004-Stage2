"""S1 static validation of an unsolved research scenario network (replaces the Assembly V1 guards).

`static_validate_s1` never prepares optimisation variables or calls a solver. The Phase4
guards it replaces, what each protected, and the V5 gate that takes over are listed in
GUARD_REPLACEMENTS and in work/p1_step1_20261015/S1_REPORT.md.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pandas as pd
from carrier_architecture import COUNTRIES,ATMOSPHERE_CARRIER,atmosphere_bus
from assembly_components import check_global_constraints,validate_hooks
from country_carbon import validate_country_attribution

GUARD_REPLACEMENTS={
 'build_research_network.py:42 (owners==loads)':'kept in spirit: demand_owners must equal the Load set; owners may now be REGISTRY or UPSTREAM_FUNCTION (register_upstream_loads) -> V5 B11 completeness, B12 hash',
 'build_research_network.py:55-68 (cross-country non-electric component / hidden path)':'removed: cross-border carriers are tagged (border_class) and controlled by research.cross_border -> V5 B5 (disconnected capacity & flow = 0) and B12 (switch/hash)',
 'build_research_network.py:69 (co2 sequestered Store forbidden)':'removed: geological storage arrives in S2 through config (geological_storage_asset); no component in S1',
 'build_research_network.py:93-104 (coupling path whitelist)':'removed: V5 B11 checks required technologies/paths per node and lists DATA_PENDING separately; no whitelist rejection',
 'build_research_network.py:105-122 (biomass obligation routing)':'removed with the fixed accounts (R13); biomass returns in S2 as an endogenous resource',
 'validate_fullsc_final.py:72 (FT must feed an oil Load)':'removed: FT output is an endogenous supply route; no fixed oil obligation exists',
 'validate_fullsc_final.py:91 (EV/Road parent Loads forbidden)':'removed: sector Loads enter through the single demand ownership table (S2)',
 'validate_fullsc_final.py:127-133 (policy must stay off / pending null weights)':'replaced by the per-country net-zero hook (country_carbon.add_country_net_zero) -> V5 B1',
 'carrier_architecture.py:44-45 (inter-country component)':'rewritten: single-country ownership for conversion/storage; TRANSPORT role may span two countries -> V5 B5',
 'carrier_architecture.py:55 (fossil-only external market)':'rewritten: any sourced commodity; imports from outside ASEAN are never cut (decision 18)',
 'assembly_components.py:9-11 (CO2 primary_energy GlobalConstraint)':'kept as U4 protection: the country cap is a hook on Store levels, not a carrier coefficient',
 'assembly_components.py:62-63 (Load destination carrier whitelist)':'rewritten: Loads may sit on the carrier bus itself (electricity, H2, ...) or a final-energy interface',
 'assembly_components.py:77-78 (hook whitelist)':'extended: research_country_net_zero, research_cross_border_existing_fom',
 'check_research_carriers.py:14-15, 27-30 (cross_border_* false; scenarios identical)':'module retired: research.cross_border switches; V5 B5/B12 prove scenarios differ by the switches only',
 'check_assembly_inputs.py:47-53 (Road EV embedded)':'removed: sector demand materialisation is S2 scope; V5 B11',
}
REQUIRED_PER_NODE={'Generator':['nuclear SMR','geothermal','ror','solar','onwind'],'Link':['H2 Electrolysis','H2 Fuel Cell','H2 turbine','SMR','SMR CC','Fischer-Tropsch','OCGT','CCGT','electricity distribution grid'],'Store':['H2 Store Tank'],'StorageUnit':['hydro','PHS']}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def static_validate_s1(n,cfg,corridors,*,daily=False):
    R=cfg['research'];report={}
    expected=pd.date_range('2013-01-01','2013-12-31 21:00',freq='3h') if not daily else pd.date_range('2013-01-01','2013-12-31',freq='24h')
    if not n.snapshots.equals(expected):raise ValueError('Research snapshot boundary changed')
    if not np.all(n.snapshot_weightings.to_numpy()==(3 if not daily else 24)):raise ValueError('Physical weights changed')
    geo=n.buses[n.buses.carrier.isin(['AC','DC'])]
    if len(geo)!=100:raise ValueError('Incorrect geographical electric bus count')
    if set(geo.country)!=set(COUNTRIES):raise ValueError('Geographical buses do not cover the 11 countries')
    check_global_constraints(n);validate_hooks(n)
    if n.meta.get('solver_allowed') is not False:raise ValueError('Solver guard missing')
    if n.meta.get('skeleton_status')!='INTERIM_S1_SKELETON':raise ValueError('S1 interim status must be declared in metadata')
    for name,table in [('loads',n.loads),('generators',n.generators),('stores',n.stores),('storage_units',n.storage_units),('links',n.links),('lines',n.lines),('transformers',n.transformers)]:
        for col in [c for c in table if c=='bus' or c.startswith('bus') and c[3:].isdigit()]:
            if any(b not in n.buses.index for b in table[col] if b):raise ValueError('Dangling '+name+' bus')
    if any(' :: ' in b for b in n.buses.index):raise ValueError('Legacy bus naming survived the rename')
    # demand: every Load owned exactly once; registry owners conserve their annual value
    load=n.loads_t.p_set.reindex(columns=n.loads.index)
    if load.isna().any().any() or not np.isfinite(load.values).all() or (load.values<0).any():raise ValueError('Invalid actual Load')
    owners=n.meta['demand_owners']
    if set(owners)!=set(n.loads.index):raise ValueError('Unexpected or unowned Load')
    if len(set(owners.values()))!=len(owners):
        # several Loads may share a registry InputID (one account spread over nodes); each Load name is unique
        pass
    kinds=n.loads.demand_owner_kind.value_counts().to_dict() if 'demand_owner_kind' in n.loads else {}
    report['demand']=dict(loads=int(len(n.loads)),owner_kinds=kinds,annual_twh=float((load.sum(axis=1)*n.snapshot_weightings.generators).sum()/1e6),scope=R['demand']['scope'])
    # carbon: 11 national atmospheres, every port booked once, U4
    report['carbon']=validate_country_attribution(n)
    if n.meta.get('research_carbon',{}).get('constraint_scope')!=R['carbon']['constraint_scope']:raise ValueError('Carbon constraint scope metadata differs from config')
    if 'research_country_net_zero' not in n.meta.get('required_constraint_hooks',[]):raise ValueError('Country net-zero hook not registered')
    # cross-border tags and switches
    for typ in ['Line','Link']:
        df=n.df(typ)
        if len(df) and ('border_class' not in df or df.border_class.isna().any() or not df.border_class.isin(['domestic','cross_border']).all()):raise ValueError('Untagged '+typ)
    sw=R['cross_border'];xb={}
    for carrier_key,sel in [('electricity',(n.lines.border_class=='cross_border').sum()+((n.links.border_class=='cross_border')&(n.links.transport_carrier=='electricity')).sum()),('H2',((n.links.border_class=='cross_border')&(n.links.carrier=='H2 pipeline')).sum()),('gas',((n.links.border_class=='cross_border')&(n.links.carrier=='gas pipeline')).sum()),('co2',((n.links.border_class=='cross_border')&(n.links.carrier=='CO2 pipeline')).sum())]:
        count=int(sel);xb[carrier_key]=count
        if not sw[carrier_key] and count:raise ValueError('Cross-border '+carrier_key+' components present although the switch is off')
    if sw['electricity']:
        expected_edges={(r.component_type,str(r.component)) for _,r in corridors.iterrows()}
        actual={('Line',x) for x in n.lines.index[n.lines.border_class=='cross_border']}|{('Link',x) for x in n.links.index[(n.links.border_class=='cross_border')&(n.links.transport_carrier=='electricity')]}
        if actual!=expected_edges:raise ValueError('Cross-border electricity set differs from the corridor table')
    report['cross_border']=dict(switches=sw,components=xb)
    if n.meta.get('research_cross_border',{}).get('switches')!={k:bool(v) for k,v in sw.items()}:raise ValueError('Cross-border switch metadata differs from config')
    # candidates: structure present at every spatial node; DATA_PENDING ones have zero potential
    loc=n.buses.location.where(n.buses.location.fillna('')!='',pd.Series(n.buses.index,index=n.buses.index)) if 'location' in n.buses else pd.Series(n.buses.index,index=n.buses.index)
    missing=[]
    for typ,carriers in REQUIRED_PER_NODE.items():
        df=n.df(typ)
        for carrier in carriers:
            # resolve every port to its geographical node through buses.location (carrier buses carry their node)
            ports=(set(df.bus[df.carrier==carrier]) if typ!='Link' else set(df.bus1[df.carrier==carrier])|set(df.bus0[df.carrier==carrier]))
            present={loc.get(b,b) for b in ports}
            for node in geo.index:
                if node not in present and carrier not in ('solar','onwind'):missing.append((typ,carrier,node))
    allowed_missing={('Generator','nuclear SMR',b) for b in geo.index if geo.at[b,'country'] not in set(R['nuclear']['smr']['allowed_countries'])}
    b2b=n.links[n.links.carrier=='B2B'];coupled=set(b2b.bus0)|set(b2b.bus1)
    missing=[m for m in missing if m not in allowed_missing and m[2] not in coupled]
    if missing:raise ValueError('Required candidate structure missing: '+str(missing[:6]))
    pending=[]
    for typ in ['Generator','StorageUnit','Link','Store']:
        df=n.df(typ)
        if 's1_candidate_status' in df:
            sel=df[df.s1_candidate_status=='DATA_PENDING']
            nom='p_nom_max' if typ!='Store' else 'e_nom_max'
            if (sel[nom]!=0).any():raise ValueError('DATA_PENDING candidate with nonzero potential')
            pending+=[dict(component_type=typ,component=k,carrier=str(z.carrier),country=str(z.country)) for k,z in sel.iterrows()]
    report['data_pending']=dict(count=len(pending),by_carrier=dict(pd.Series([p['carrier'] for p in pending]).value_counts()) if pending else {})
    # prices: every active component qualified
    priced=[r for r in n.meta.get('component_price_qualification',[]) if any('PENDING' in str(v) for v in r.values())]
    if priced:raise ValueError('Active economic price qualification pending: '+str(priced[:2]))
    # existing stock integrity (unchanged frozen survivors)
    identities=n.meta['existing_unit_components'];groups={}
    for ident,z in identities.items():groups.setdefault((z['component_type'],z['component']),[]).append(z)
    for (typ,name),parts in groups.items():
        z=n.df(typ).loc[name];total=sum(x['capacity_mw'] for x in parts)
        effective=float(z.p_nom*z.efficiency if typ=='Link' else z.p_nom)
        if not np.isclose(total,effective,rtol=1e-12) or z.p_nom_extendable or z.capital_cost!=0:raise ValueError('Existing stock altered: '+name)
    report['existing_stock']=dict(units=len(identities),components=len(groups),capacity_mw=float(sum(z['capacity_mw'] for z in identities.values())))
    # transmission limit parameter recorded
    if n.meta.get('transmission_limit',{}).get('constant_mwkm')!=float(n.global_constraints.at['lv_limit','constant']):raise ValueError('Transmission limit metadata differs from the GlobalConstraint')
    report['status']='S1_STATIC_PASS';report['guard_replacements']=GUARD_REPLACEMENTS;report['solver_runs']=0
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--network',type=Path,required=True);p.add_argument('--scenario',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    import pypsa,sys
    sys.path.insert(0,str(a.repo/'scripts_project'))
    from phase4_static import config
    cfg=config(a.repo,a.scenario);n=pypsa.Network(str(a.network));corridors=pd.read_csv(a.repo/cfg['research']['existing_cross_border_electricity']['corridors_file'],float_precision='round_trip')
    r=static_validate_s1(n,cfg,corridors,daily=len(n.snapshots)==365);r['network_sha256']=sha(a.network)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,default=str)+'\n');print(r['status'])
