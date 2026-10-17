"""S1 scenario builder: frozen electric base + upstream hydrogen library + research carrier
recipe + nuclear/site candidates + per-country atmosphere + cross-border switches.

    python scripts_project/scenario_network.py --repo . --scenario integrated --output results_project/s1/integrated

Builds the 2920x3h network, validates it statically (build_research_network.static_validate_s1),
exports it, derives the exact 365x24h daily network (daily_resolution) and writes receipts.
No solver. Every input is pinned by SHA256; the frozen electric base is never modified.
"""
from pathlib import Path
import argparse,copy,hashlib,json,platform,subprocess,sys,time
import numpy as np
import pandas as pd
import pypsa
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
from carrier_architecture import COUNTRIES,to_pypsa_fragment,rename_legacy_bus,LEGACY_SEPARATOR,atmosphere_bus,ATMOSPHERE_CARRIER,finite
from assembly_components import merge_input_components,bind_loads,validate_hooks,check_global_constraints
from country_carbon import add_country_atmosphere,reconnect_atmosphere_ports,fix_u4,validate_country_attribution,install_metadata as install_carbon_metadata,emission_registry
from sector_adapter import load_upstream,build_options,inject,add_hydrogen,spatial_nodes,dc_to_ac
from s1_candidates import add_nuclear,add_site_candidates,confirm_extendable,apply_cost_scaling,PENDING
from build_research_assets import build_fragment
from daily_resolution import to_daily
from network_checks import assert_input_only,compare_roundtrip,normalise_optional_strings

ELECTRIC_BASE_SHA='6772c6742b000368f9e7c5db2cd22ca798dec525be65131032eadf06e2b417f7'
XB_FOM_HOOK='research_cross_border_existing_fom'
EXTENDABLE_REQUIRED=('H2 turbine','H2 Fuel Cell','H2 Store Tank','battery','battery charger','home battery','home battery charger')
TRANSPORT_CARRIERS={'AC':'electricity','DC':'electricity','B2B':'electricity','H2 pipeline':'H2','gas pipeline':'gas','CO2 pipeline':'co2'}
MARITIME_TRADE_CARRIERS={'CO2 ship','CO2 transit ship','CO2 transit rail'}  # S4D-2 (decision 92): maritime trade between countries, kept in both scenarios like the liquid fuels (decisions 18, 44); not cross-border network; S4E-2 (95 c): Lao transit then ship; S4F-2 (97 c): Lao rail transit into the Vietnamese store (the trade class of decision 92, not network)
SKELETON='INTERIM_S1_SKELETON'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str)+'\n')
def git_head(repo):
    try:return subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    except Exception:return None
def config_sha(cfg):return hashlib.sha256(json.dumps(cfg,sort_keys=True,default=str).encode()).hexdigest()

def jsonable(x):
    """Metadata must survive the NetCDF JSON round trip bit-for-bit: string keys, lists, no NaN, native floats/ints."""
    import math
    def conv(o):
        if isinstance(o,dict):return {str(k):conv(v) for k,v in o.items()}
        if isinstance(o,(list,tuple,set)):return [conv(v) for v in o]
        if isinstance(o,(np.integer,)):return int(o)
        if isinstance(o,(np.floating,float)):
            o=float(o);return None if math.isnan(o) else o
        if isinstance(o,(np.bool_,)):return bool(o)
        if isinstance(o,(str,int,bool)) or o is None:return o
        return str(o)
    return json.loads(json.dumps(conv(x),sort_keys=True))  # sorted keys: PyPSA iterates component sets, so insertion order is not reproducible

def rename_legacy_buses(n):
    """'<node> :: <carrier>' -> '<node> <carrier>' on every bus and every port column."""
    mapping={b:rename_legacy_bus(b) for b in n.buses.index if LEGACY_SEPARATOR in b}
    if not mapping:return mapping
    if set(mapping.values())&set(n.buses.index):raise ValueError('Bus rename collision')
    n.buses.rename(index=mapping,inplace=True)
    for typ in ['Generator','Load','Store','StorageUnit','Link','Line','Transformer']:
        df=n.df(typ)
        for col in [c for c in df if c=='bus' or (c.startswith('bus') and c[3:].isdigit())]:
            df[col]=df[col].map(lambda x:mapping.get(x,x))
    return mapping

def tag_cross_border(n):
    """Every Line/Link/Transformer gets border_class in {domestic, cross_border} from buses.country (S1-6); S4D-2: links of a
    MARITIME_TRADE_CARRIERS carrier between two countries get maritime_trade (not network, outside B5 and the cross-border switches)."""
    atmo=set(n.buses.index[n.buses.carrier==ATMOSPHERE_CARRIER]);summary={}
    regional=set(n.buses.index[n.buses.country=='ASEAN'])
    atmo|=regional  # S3-2 (decision 18): regional commodity pools (ASEAN oil/ammonia/methanol) are not network-constrained; ports to them do not make a component cross-border
    for typ in ['Line','Link','Transformer']:
        df=n.df(typ)
        if not len(df):continue
        cls=[];tc=[]
        for name,z in df.iterrows():
            ports=[z[c] for c in df if c.startswith('bus') and c[3:].isdigit() and z[c] and z[c] not in atmo]
            countries={str(n.buses.at[b,'country']) for b in ports}
            if not ports and all(z[c] in regional for c in df if c.startswith('bus') and c[3:].isdigit() and z[c]):countries={'ASEAN'}  # S4C-3 (decision 88): the international bunker meters link regional buses only -> domestic (regional)
            if not countries or '' in countries or 'nan' in countries:raise ValueError('Port without country: '+typ+' '+name)
            cls.append(('maritime_trade' if str(z.carrier) in MARITIME_TRADE_CARRIERS else 'cross_border') if len(countries)>1 else 'domestic');tc.append(TRANSPORT_CARRIERS.get(str(z.carrier),'local'))
        df['border_class']=cls;df['transport_carrier']=tc
        summary[typ]=dict(domestic=int(cls.count('domestic')),cross_border=int(cls.count('cross_border')),maritime_trade=int(cls.count('maritime_trade')),cross_border_by_carrier={k:int(((df.border_class=='cross_border')&(df.transport_carrier==k)).sum()) for k in sorted(set(tc))})
    return summary

def existing_cross_border_fom(n,corridors,costs):
    """Annual FOM of the existing (2025) cross-border capacity, from the frozen cost rows that also
    price new capacity: FOM% x investment [EUR/MW/km] x length x capacity (+ inverter pair for DC)."""
    rows=[];total=0.
    for _,r in corridors.iterrows():
        typ=r.component_type;name=str(r.component);z=n.df(typ).loc[name];cap=float(r.capacity_2025_mw);length=float(z.length)
        if typ=='Line':tech=[('HVAC overhead',length)]
        else:
            u=float(r.subsea_share);tech=[('HVDC overhead',length*(1-u)),('HVDC submarine',length*u),('HVDC inverter pair',1.)]
        fom=sum(float(costs.at[t,'FOM'])/100.*float(costs.at[t,'investment'])*km*cap for t,km in tech)
        rows.append(dict(component_type=typ,component=name,capacity_2025_mw=cap,length_km=length,annual_fom_eur=fom,cost_rows=[t for t,_ in tech]));total+=fom
    return total,rows

def apply_cross_border_switches(n,switches,corridors,existing_cfg,costs):
    """research.cross_border.{electricity,H2,gas,co2}: keep (with 2025 lower bound) or remove."""
    ledger={}
    xb_lines=set(n.lines.index[n.lines.border_class=='cross_border'])
    xb_elec_links=set(n.links.index[(n.links.border_class=='cross_border')&(n.links.transport_carrier=='electricity')])
    actual={('Line',x) for x in xb_lines}|{('Link',x) for x in xb_elec_links}
    expected={(r.component_type,str(r.component)) for _,r in corridors.iterrows()}
    if actual!=expected:raise ValueError('Existing cross-border electricity set differs from the corridor table: '+str(sorted(actual^expected))[:300])
    if switches['electricity']:
        checks=[]
        for _,r in corridors.iterrows():
            typ=r.component_type;name=str(r.component);z=n.df(typ).loc[name];nom='s_nom' if typ=='Line' else 'p_nom'
            cap=float(r.capacity_2025_mw)
            # The frozen reference carries the 2025 capacity as the extendable lower bound (s_nom_min); s_nom itself may differ by float noise.
            if not z[nom+'_extendable'] or float(z[nom+'_min'])!=cap or not np.isclose(float(z[nom]),cap,rtol=1e-9,atol=1e-6):raise ValueError('Existing cross-border edge lacks the 2025 lower bound: '+name)
            checks.append(dict(component_type=typ,component=name,capacity_2025_mw=cap,lower_bound_mw=float(z[nom+'_min']),nominal_mw=float(z[nom]),extendable=True,capex_on_existing_mw='EXCLUDED_BY_PYPSA_OBJECTIVE_CONSTANT'))
        fom_total,fom_rows=(existing_cross_border_fom(n,corridors,costs) if existing_cfg['fom_on_existing'] else (0.,[]))
        n.meta['existing_cross_border_fom_eur']=fom_total;n.meta['existing_cross_border_fom_ledger']=fom_rows
        if fom_total:n.meta['required_constraint_hooks']=sorted(set(n.meta.get('required_constraint_hooks',[]))|{XB_FOM_HOOK})
        ledger['electricity']=dict(switch=True,kept=len(checks),edges=checks,existing_annual_fom_eur=fom_total)
    else:
        n.mremove('Line',sorted(xb_lines));n.mremove('Link',sorted(xb_elec_links))
        n.meta['existing_cross_border_fom_eur']=0.;n.meta['existing_cross_border_fom_ledger']=[]
        ledger['electricity']=dict(switch=False,removed=sorted(xb_lines)+sorted(xb_elec_links),removed_count=len(actual))
    xb_h2=sorted(n.links.index[(n.links.border_class=='cross_border')&(n.links.carrier=='H2 pipeline')])
    if switches['H2']:ledger['H2']=dict(switch=True,kept=len(xb_h2),pipelines=xb_h2)
    else:n.mremove('Link',xb_h2);ledger['H2']=dict(switch=False,removed=xb_h2,removed_count=len(xb_h2))
    for k,carrier in [('gas','gas pipeline'),('co2','CO2 pipeline')]:
        count=int(((n.links.border_class=='cross_border')&(n.links.carrier==carrier)).sum()) if 'border_class' in n.links else 0
        if count:raise ValueError('Unexpected '+carrier+' components in S1')
        ledger[k]=dict(switch=bool(switches[k]),components=0,note='no '+k+' network before step '+('2' if k=='co2' else '3'))
    n.meta['research_cross_border']=dict(switches={k:bool(v) for k,v in switches.items()},ledger=ledger)
    return ledger

def install_existing_cross_border_fom(n):
    """Hook: existing cross-border transmission FOM once, as a fixed-at-1 column (same device as existing-asset FOM)."""
    if getattr(n,'_research_xb_fom_model',None) is n.model:raise ValueError('Cross-border FOM hook already installed')
    cost=float(n.meta.get('existing_cross_border_fom_eur',0.))
    if cost:
        one=n.model.add_variables(lower=1.,upper=1.,name='Research_existing_cross_border_FOM_constant')
        n.model.objective+=one*cost
    n._research_xb_fom_model=n.model

def set_transmission_limit(n,cfg):
    """Decision 45 as a parameter. Default inherits the frozen lv2.0 constant unchanged."""
    if 'lv_limit' not in n.global_constraints.index:raise ValueError('Reference transmission volume limit missing')
    lv=n.global_constraints.loc['lv_limit'];carriers=lv.carrier_attribute.split(', ')
    lines=n.lines[n.lines.carrier.isin(carriers)];links=n.links[n.links.carrier.isin(carriers)]
    existing=float((lines.s_nom*lines.length).sum()+(links.p_nom*links.length).sum())
    mode=cfg['volume_limit_mode']
    if mode=='inherit_reference_constant':constant=float(lv.constant)
    elif mode=='factor_of_existing':constant=float(cfg['volume_limit_factor'])*existing;n.global_constraints.at['lv_limit','constant']=constant
    else:raise ValueError('Unknown transmission volume limit mode')
    return dict(mode=mode,constant_mwkm=constant,existing_volume_mwkm=existing,implied_factor=(constant/existing if existing else None),carriers=carriers,type=str(lv['type']))

def bind_astar(n,repo,allocation):
    """S1 transitional demand: electricity (AEO8 BAS Astar, cooling embedded) only; other sectors return in S2."""
    reg_path=repo/'research_inputs/assembly_v1/registry.json';registry=json.loads(reg_path.read_text());records=registry['records']
    am=json.loads((allocation/'allocation_manifest.json').read_text())
    if am['input_registry_sha256']!=sha(reg_path):raise ValueError('Allocation belongs to another registry')
    lookup={r['InputID']:r for r in records};astar=[ar for ar in am['records'] if lookup[ar['InputID']]['Account']=='Astar']
    if len(astar)!=11 or {lookup[a['InputID']]['Country'] for a in astar}!=set(COUNTRIES):raise ValueError('Astar allocation must cover 11 countries')
    dest={}
    for ar in astar:
        for node in ar['Nodes']:dest[ar['InputID']+'@'+node]=dict(bus=node,carrier='electricity',sector='Astar',account='Astar',source_carrier=lookup[ar['InputID']]['Carrier'])
    with np.load(allocation/am['arrays_file'],allow_pickle=False) as z:bind_loads(n,records,dict(am,records=astar),z,dest)
    w=n.snapshot_weightings.generators;by={}
    for ar in astar:
        r=lookup[ar['InputID']];cols=[k for k,v in n.meta['demand_owners'].items() if v==ar['InputID']]
        actual=float((n.loads_t.p_set[cols].sum(axis=1)*w).sum())
        if not np.isclose(actual,float(r['Value']),rtol=1e-10,atol=1e-6):raise ValueError('Astar annual demand not conserved for '+r['Country'])
        by[r['Country']]=dict(annual_mwh=actual,registry_mwh=float(r['Value']),loads=len(cols))
    return dict(scope='electricity_only_astar',status=SKELETON,loads=int(len(n.loads)),by_country=by,total_twh=sum(v['annual_mwh'] for v in by.values())/1e6,allocation_manifest_sha256=sha(allocation/'allocation_manifest.json'),registry_sha256=sha(reg_path))

def component_inventory(n):
    out={}
    for typ in ['Generator','Link','Store','StorageUnit','Line','Bus','Load']:
        df=n.df(typ)
        if not len(df):continue
        if 'country' not in df:df=df.assign(country='')
        rows=[]
        for (carrier,country),g in df.groupby(['carrier',df.country.fillna('')]):
            rec=dict(carrier=str(carrier),country=str(country),count=int(len(g)))
            for nom in ['p_nom','s_nom','e_nom']:
                if nom in g:rec[nom+'_mw_or_mwh']=float(g[nom].sum());rec[nom+'_extendable']=int(g[nom+'_extendable'].sum()) if nom+'_extendable' in g else None
            if 'border_class' in g:rec['cross_border']=int((g.border_class=='cross_border').sum())
            if 's1_candidate_status' in g:rec['data_pending']=int((g.s1_candidate_status==PENDING).sum())
            rows.append(rec)
        out[typ]=rows
    return out

def build_scenario(repo,scenario,output,electric_base,costs,price_layer,allocation,hydro_decisions,cost_layer=True,daily=True):
    repo=Path(repo);output=Path(output);output.mkdir(parents=True,exist_ok=True);t0=time.time()
    from phase4_static import config
    from price_basis import load_table,qualify_network_costs
    from build_research_network import static_validate_s1
    cfg=config(repo,scenario);R=cfg['research']
    if R['scenario']!=scenario:raise ValueError('Scenario identity does not match the composed config')
    if sha(electric_base)!=ELECTRIC_BASE_SHA:raise ValueError('Frozen electric base identity changed')
    n=pypsa.Network(str(electric_base));assert_input_only(n)
    if n.meta.get('asset_qualification')!='SOURCE_QUALIFIED_ELECTRIC_BASE_UNSOLVED':raise ValueError('Electric base is not the source-qualified asset')
    base_meta=copy.deepcopy(n.meta)
    rename_map=rename_legacy_buses(n)
    costs_table,layer=load_table(price_layer,2050,costs)
    corridors=pd.read_csv(repo/R['existing_cross_border_electricity']['corridors_file'],float_precision='round_trip')
    # 1. upstream hydrogen library (must precede the research recipe: upstream drops any prior H2 carrier components)
    psn=load_upstream(repo);nodes=spatial_nodes(n);options=build_options(cfg['sector'],R['hydrogen'])
    injected=inject(psn,n,options,nodes,COUNTRIES,output/'empty_gas_pipelines.csv',cfg['research_assembly']['demand_scenario'])
    h2=add_hydrogen(psn,n,costs_table,nodes,dc_to_ac(n))
    # 2. research carrier recipe (fuel pools, external supply, SMR/SMR CC/FT, OCGT/CCGT, national atmosphere)
    f,carbon,fragment_manifest=build_fragment(repo,n,costs,output,price_layer,cc_fraction=cfg['sector']['cc_fraction'])
    sub=to_pypsa_fragment(f,list(n.snapshots),list(n.snapshot_weightings.generators),component_ids=list(f.components))
    merge_input_components(n,sub)
    add_country_atmosphere(n);moves=reconnect_atmosphere_ports(n);u4=fix_u4(n)
    # 3. candidates (S1-4)
    nuclear=add_nuclear(n,costs_table,R['nuclear'],nodes)
    sites=add_site_candidates(n,costs_table,R['site_candidates'],nodes,hydro_decisions)
    extendable=confirm_extendable(n,EXTENDABLE_REQUIRED)
    # 4. network and scenario switches (S1-6)
    tags=tag_cross_border(n)
    xb=apply_cross_border_switches(n,R['cross_border'],corridors,R['existing_cross_border_electricity'],costs_table)
    lv=set_transmission_limit(n,R['transmission'])
    # 5. per-country carbon (S1-5)
    carbon_meta=install_carbon_metadata(n,R['carbon'])
    # 6. demand (interim: electricity only)
    demand=bind_astar(n,repo,allocation)
    # 7. cost scaling layer (decision 41)
    scaling=apply_cost_scaling(n,R['cost_scaling']) if cost_layer else None
    qualify_network_costs(n,layer,price_layer)
    n.meta.update(**jsonable(dict(artifact_role='S1_SCENARIO_UNSOLVED',asset_role='S1_SCENARIO_UNSOLVED',stage='S1',skeleton_status=SKELETON,scenario=scenario,solver_allowed=False,scientific_results_allowed=False,
                  fullsc_network_complete=False,input_coverage_complete=False,research_config=R,research_config_sha256=config_sha(R),fuel_bus_rename_map=rename_map,atmosphere_port_moves=moves,u4_zeroed_carriers=u4,
                  upstream_adapter=injected,upstream_add_hydrogen=h2,candidate_ledger=dict(nuclear=nuclear,sites=sites,extendable=extendable),cross_border_tags=tags,transmission_limit=lv,demand_binding=demand,
                  electric_base_sha256=ELECTRIC_BASE_SHA,physical_carbon_map=carbon,  # cost-scaling ledger stays in the receipt so an all-1.0 layer leaves the file hash unchanged
                  interim_notice='INTERIM_S1_SKELETON: electricity demand only; results carry no scientific meaning')))
    for key in ['research_carbon','research_cross_border','existing_cross_border_fom_ledger','existing_cross_border_fom_eur']:
        if key in n.meta:n.meta[key]=jsonable(n.meta[key])
    n.meta['required_constraint_hooks']=sorted(set(n.meta.get('required_constraint_hooks',[]))|{'install_fragment_constraints'})
    n.meta['qualification_dimensions']=dict(n.meta.get('qualification_dimensions',{}),physical_integrity='S1_STATIC_VALIDATION',input_coverage='ELECTRICITY_ONLY_INTERIM',price_usability='SEE_COMPONENT_PRICE_QUALIFICATION')
    normalise=normalise_optional_strings(n)
    static=static_validate_s1(n,cfg,corridors)
    inventory=component_inventory(n)
    path=output/f'{scenario}_2920_3h_unsolved.nc';n.export_to_netcdf(path)
    back=pypsa.Network(str(path));compare_roundtrip(n,back)
    receipt=dict(status='S1_SCENARIO_BUILT_STATIC_PASS',scenario=scenario,skeleton_status=SKELETON,network=dict(file=str(path),sha256=sha(path),bytes=path.stat().st_size,snapshots=int(len(n.snapshots)),components={c.name:int(len(c.df)) for c in n.iterate_components()}),
                 inputs={'electric_base':dict(path=str(electric_base),sha256=ELECTRIC_BASE_SHA),'costs':dict(path=str(costs),sha256=sha(costs)),'price_layer':dict(path=str(price_layer),sha256=sha(price_layer)),'allocation_manifest':dict(path=str(allocation/'allocation_manifest.json'),sha256=sha(allocation/'allocation_manifest.json')),'corridors':dict(path=str(repo/R['existing_cross_border_electricity']['corridors_file']),sha256=sha(repo/R['existing_cross_border_electricity']['corridors_file'])),'registry':dict(sha256=sha(repo/'research_inputs/assembly_v1/registry.json')),'upstream_module':dict(path='scripts/prepare_sector_network.py',sha256=sha(repo/'scripts/prepare_sector_network.py'))},
                 research_config_sha256=config_sha(R),cross_border_switches=R['cross_border'],cross_border=xb,transmission_limit=lv,demand=demand,upstream=h2,adapter=injected,candidates=dict(nuclear=len(nuclear),sites=len(sites),extendable=extendable),
                 rename_map_count=len(rename_map),atmosphere_moves=len(moves),u4_zeroed_carriers=u4,static_validation=static,inventory=inventory,optional_string_normalisation=normalise,cost_scaling=dict(enabled=cost_layer,ledger=scaling),
                 code_sha=git_head(repo),environment=dict(python=platform.python_version(),pypsa=pypsa.__version__),base_meta_asset_qualification=base_meta.get('asset_qualification'),build_seconds=time.time()-t0,solver_runs=0)
    if daily:
        d,ledger=to_daily(n);dpath=output/f'{scenario}_365_24h_unsolved.nc';d.export_to_netcdf(dpath)
        dback=pypsa.Network(str(dpath));compare_roundtrip(d,dback)
        receipt['daily_network']=dict(file=str(dpath),sha256=sha(dpath),bytes=dpath.stat().st_size,snapshots=int(len(d.snapshots)),weights_sum={k:float(d.snapshot_weightings[k].sum()) for k in d.snapshot_weightings},aggregation=ledger)
    save(output/f'{scenario}_BUILD_RECEIPT.json',receipt)
    return n,receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=HERE.parent);p.add_argument('--scenario',required=True,choices=['integrated','disconnected','baseline']);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--electric-base',type=Path,default=None);p.add_argument('--costs',type=Path,default=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/costs_2050_sec.csv'))
    p.add_argument('--price-layer',type=Path,default=None);p.add_argument('--allocation',type=Path,default=None);p.add_argument('--no-cost-layer',action='store_true');p.add_argument('--no-daily',action='store_true')
    a=p.parse_args();repo=a.repo.resolve()
    eb=a.electric_base or repo/'results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc'
    pl=a.price_layer or repo/'results_project/assembly_v1/final_assets/model_cost_layer.json'
    al=a.allocation or repo/'results_project/assembly_v1/final_allocation'
    hydro=json.loads((repo/'research_inputs/asset_survival/hydro_decisions.json').read_text())
    n,r=build_scenario(repo,a.scenario,a.output,eb,a.costs,pl,al,hydro,cost_layer=not a.no_cost_layer,daily=not a.no_daily)
    print(json.dumps(dict(status=r['status'],network=r['network']['sha256'],daily=r.get('daily_network',{}).get('sha256'),components=r['network']['components'],seconds=round(r['build_seconds'],1))))
