"""Read-only static NetCDF port audit. No PyPSA Network, LP or solver imports.
Uses stored Bus.country, then exact Bus.location references; never name prefixes.
Does not read optimized capacity/dispatch, Load time series, CSC or raw solutions.
"""
import csv, hashlib, json, math, subprocess
from pathlib import Path
from collections import Counter, defaultdict
import netCDF4
import numpy as np

ROOT=Path('/mnt/d/ResearchWorkspaces/ASEAN')
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
OUT=ROOT/'work/a05_cross_border_audit_20261011'
ELECTRIC={'AC','DC','electricity','low voltage'}
DEFAULT_DIR=Path('/home/jin/miniforge3/envs/pypsa-earth/lib/python3.11/site-packages/pypsa/component_attrs')
def sha(b): return hashlib.sha256(b).hexdigest()
def clean(v):
    if isinstance(v,np.generic): v=v.item()
    if isinstance(v,float) and not math.isfinite(v): return 'Infinity' if v>0 else '-Infinity' if v<0 else None
    if isinstance(v,dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    return v
def save(name,data):
    (OUT/name).write_text(json.dumps(clean(data),ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
DEFAULTS={};DEFAULT_EVIDENCE={}
for typ in ['buses','links','lines','generators','stores','loads','storage_units','transformers']:
    p=DEFAULT_DIR/(typ+'.csv'); data=p.read_bytes(); DEFAULT_EVIDENCE[typ]={'path':str(p),'sha256':sha(data)}
    DEFAULTS[typ]={}
    for row in csv.DictReader(data.decode().splitlines()):
        v=row['default']; t=row['type']
        if v in ['n/a','NaN','nan']: v=None
        elif t=='boolean': v=v.lower()=='true'
        elif t in ['float','int','static or series']:
            try:v=float(v)
            except ValueError:pass
        DEFAULTS[typ][row['attribute']]=v

def static_table(n,typ):
    if typ+'_i' not in n.variables:return {},set()
    ids=n[typ+'_i'][:].tolist();rows={str(x):{'id':str(x)} for x in ids};stored=set()
    for name in n.variables:
        if not name.startswith(typ+'_') or name==typ+'_i' or '_t_' in name:continue
        a=n[name]
        if a.dimensions!=(typ+'_i',):continue
        field=name[len(typ)+1:];stored.add(field)
        vals=a[:].tolist()
        for i,v in zip(ids,vals):rows[str(i)][field]=v
    return rows,stored
def attr(typ,row,key):
    v=row.get(key,DEFAULTS[typ].get(key))
    if key in ['p_nom_extendable','s_nom_extendable','e_nom_extendable','e_cyclic']:return bool(v)
    return v
def model(label,path,identity):
    with netCDF4.Dataset(path,'r') as n:
        assert n.network_pypsa_version=='0.30.3'
        tables={};stored={}
        for typ in DEFAULTS:tables[typ],stored[typ]=static_table(n,typ)
        buses=tables['buses']; countries={};origin={}
        for b,v in buses.items():
            c=v.get('country','')
            if c:countries[b]=c;origin[b]='stored Bus.country'
        for _ in range(len(buses)):
            additions={b:countries[v['location']] for b,v in buses.items() if b not in countries and v.get('location') in countries}
            if not additions:break
            for b,c in additions.items():countries[b]=c;origin[b]='exact Bus.location -> known Bus.country'
        def port(b,position,coefficient):
            v=buses[b]
            return {'port':position,'bus':b,'country':countries.get(b),'country_basis':origin.get(b,'UNRESOLVED_GLOBAL_OR_UNASSIGNED'),'location':v.get('location',''),'carrier':v.get('carrier',''),'unit':v.get('unit',DEFAULTS['buses'].get('unit')),'coefficient_positive_flow':coefficient}
        # These two version-specific carrier labels are confirmed by the frozen
        # carbon-account constructors. Countryless atmosphere is reporting,
        # unlike the upstream withdrawable 'co2 stored' feedstock pool.
        atmosphere={b for b,v in buses.items() if v.get('carrier') in ['co2','co2 atmosphere'] and not countries.get(b)}
        records=[];cross=[];pool_edges=defaultdict(list);profiles={};byclass=Counter();parent={}
        def find(x):
            parent.setdefault(x,x)
            if parent[x]!=x:parent[x]=find(parent[x])
            return parent[x]
        def union(x,y):parent[find(x)]=find(y)
        for typ in ['links','lines','transformers']:
            for aid,row in tables[typ].items():
                ps=[]
                for i in range(5):
                    b=row.get('bus'+str(i),'')
                    if not b:continue
                    coefficient=-1 if i==0 else (1 if typ!='links' else attr(typ,row,'efficiency' if i==1 else 'efficiency'+str(i)))
                    if coefficient is None or coefficient==0:continue
                    ps.append(port(b,i,coefficient))
                energy=[p for p in ps if p['bus'] not in atmosphere]
                cc=sorted({p['country'] for p in energy if p['country']})
                unknown=[p['bus'] for p in energy if not p['country']]
                all_elec=all(p['carrier'] in ELECTRIC for p in energy)
                kind=('CROSS_BORDER_ELECTRIC' if all_elec else 'CROSS_BORDER_NON_ELECTRIC_OR_MIXED') if len(cc)>1 else ('GLOBAL_POOL_INTERFACE' if unknown else 'DOMESTIC_ELECTRIC' if all_elec else 'DOMESTIC_CONVERSION_OR_RESOURCE_LINK')
                if not energy:kind='REPORTING_ONLY_OR_EMPTY'
                byclass[typ+':'+kind]+=1
                nominal='s_nom' if typ in ['lines','transformers'] else 'p_nom'
                fields=[nominal,nominal+'_min',nominal+'_max',nominal+'_extendable','capital_cost','length','build_year','lifetime']
                fields+=['p_min_pu','p_max_pu','marginal_cost','efficiency','efficiency2','efficiency3'] if typ=='links' else ['s_max_pu','r','x','num_parallel','type']
                vals={k:attr(typ,row,k) for k in fields if k in row or k in DEFAULTS[typ]}
                rec={'component':typ,'id':aid,'carrier':row.get('carrier',''),'classification':kind,'countries':cc,'ports':ps,'parameters':clean(vals),'defaulted_fields':[k for k in vals if k not in stored[typ]],'source_component':row.get('source_component')}
                records.append(rec)
                if kind.startswith('CROSS_BORDER'):cross.append(rec)
                for b in unknown:pool_edges[b].append({'component':typ,'id':aid,'countries':cc,'carrier':row.get('carrier',''),'pool_port':[p for p in ps if p['bus']==b][0]})
                ne=[p['bus'] for p in energy if p['carrier'] not in ELECTRIC]
                for b in ne:find(b)
                for b in ne[1:]:union(ne[0],b)
                key=typ+':'+row.get('carrier','')
                if key not in profiles:profiles[key]={'count':0,'classification_counts':Counter(),'countries':set(),'parameter_values':defaultdict(set),'example':rec}
                pr=profiles[key];pr['count']+=1;pr['classification_counts'][kind]+=1;pr['countries'].update(cc)
                for k,v in vals.items():pr['parameter_values'][k].add(json.dumps(clean(v),sort_keys=True))
        for pr in profiles.values():
            pr['countries']=sorted(pr['countries'])
            pr['parameter_values']={k: {'distinct_count':len(v),'values':sorted([json.loads(x) for x in v],key=str) if len(v)<=16 else None,'numeric_min':min([json.loads(x) for x in v if isinstance(json.loads(x),(int,float))],default=None),'numeric_max':max([json.loads(x) for x in v if isinstance(json.loads(x),(int,float))],default=None)} for k,v in pr['parameter_values'].items()}
        comps=defaultdict(list)
        for b in parent:comps[find(b)].append(b)
        multic=[]
        for bs in comps.values():
            cs=sorted({countries[b] for b in bs if b in countries})
            if len(cs)>1:multic.append({'buses':sorted(bs),'countries':cs})
        pools=[]
        for b,edges in pool_edges.items():
            pools.append({'bus':port(b,0,None),'attached_countries':sorted({c for e in edges for c in e['countries']}),'incident_assets':edges,'stores':[{k:attr('stores',s,k) for k in ['id','carrier','e_nom','e_nom_min','e_nom_max','e_nom_extendable','e_initial','e_cyclic','e_min_pu','e_max_pu','marginal_cost']} for s in tables['stores'].values() if s.get('bus')==b],'generators':[{k:attr('generators',s,k) for k in ['id','carrier','p_nom','p_nom_min','p_nom_max','p_nom_extendable','p_min_pu','p_max_pu','marginal_cost']} for s in tables['generators'].values() if s.get('bus')==b]})
        suppliers=[]
        for g in tables['generators'].values():
            if g.get('research_role')=='EXTERNAL_SUPPLY' or buses[g['bus']].get('carrier') in ['gas','oil','coal','lignite','H2','NH3','methanol']:
                suppliers.append({'id':g['id'],'bus':port(g['bus'],0,1),**{k:attr('generators',g,k) for k in ['carrier','p_nom','p_nom_min','p_nom_max','p_nom_extendable','p_min_pu','p_max_pu','capital_cost','marginal_cost','research_role','source_identity','price_qualification']}})
        loads=Counter();hloads=[]
        for x in tables['loads'].values():
            loads[buses[x['bus']].get('carrier','')]+=1
            if buses[x['bus']].get('carrier') in ['H2','NH3','methanol']:hloads.append({'id':x['id'],'bus':port(x['bus'],0,-1),'carrier':x.get('carrier')})
        hydrogen_links=[r for r in records if any(p['carrier']=='H2' for p in r['ports'])]
        hydrogen_stores=[{'id':s['id'],'bus':port(s['bus'],0,1),**{k:attr('stores',s,k) for k in ['e_nom','e_nom_min','e_nom_max','e_nom_extendable','e_initial','e_cyclic','e_min_pu','e_max_pu','capital_cost','marginal_cost']}} for s in tables['stores'].values() if buses[s['bus']].get('carrier')=='H2']
        global_constraints={k:n[k][:].tolist() for k in n.variables if k.startswith('global_constraints_') and '_t_' not in k}
        dynamic=[]
        for k in n.variables:
            if any(t in k for t in ['links_t_p_min_pu','links_t_p_max_pu','links_t_efficiency','lines_t_s_max_pu']):
                index=k if k.endswith('_i') else k+'_i'
                ids=n[index][:].tolist() if index in n.variables else []
                dynamic.append({'field':k,'shape':n[k].shape,'cross_border_affected_ids':sorted(set(ids)&{r['id'] for r in cross}),'values_not_read':True})
        out={'label':label,'source':{'path':str(path),'bytes_now':path.stat().st_size,'sha256_from_existing_verified_manifest':identity,'hash_policy':'Reused prior verified SHA; no repeated full NetCDF hash','pypsa_version':n.network_pypsa_version},'component_counts':{k:len(v) for k,v in tables.items()},'bus_carrier_counts':dict(Counter(x.get('carrier','') for x in buses.values())),'unresolved_buses':[port(b,0,None) for b in buses if b not in countries],'atmosphere_reporting_buses':sorted(atmosphere),'classification_counts':dict(byclass),'cross_border_assets':cross,'carrier_profiles':profiles,'global_pool_interfaces':pools,'non_electric_graph':{'excludes_electric_and_atmosphere':True,'components':len(comps),'multi_country_components':multic},'external_or_fuel_generators':suppliers,'load_bus_carriers':dict(loads),'direct_h2_nh3_methanol_loads':hloads,'hydrogen_link_carrier_counts':dict(Counter(r['carrier'] for r in hydrogen_links)),'hydrogen_link_examples':{r['carrier']:r for r in hydrogen_links},'hydrogen_store_count':len(hydrogen_stores),'hydrogen_store_examples':hydrogen_stores[:2],'global_constraints':global_constraints,'branch_dynamic_bound_fields':dynamic,'electrical_asset_signatures':{r['component']+':'+r['id']:{'ports':[p['bus'] for p in r['ports']],'parameters':r['parameters']} for r in records if r['component']=='lines' or r['carrier'] in ['DC','B2B']},'stored_static_fields':{k:sorted(v) for k,v in stored.items()}}
        return clean(out)

idx=json.loads((ROOT/'research/00_source_provenance/RESULTS_MEMBER_HASHES.json').read_text())
models=[model('FROZEN_FULL_SC_2050',ROOT/'outputs/phase4_gate4_final_closure_20261006/complete_network/research_fullsc_2050_assembly_v1_unsolved.nc','238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d')]
for i in idx:
    label='PAPER_'+('2025' if '2025' in i['path'] else '2050')
    models.append(model(label,ROOT/'research/00_source_provenance'/i['path'].replace('\\','/'),i['sha256']))
save('A05_CROSS_BORDER_ASSET_INVENTORY.json',{'schema':'A05_STATIC_PORT_AUDIT_V1','no_solver_no_model_assembly':True,'cost_semantics':'NetCDF static input costs; not optimized capacities or SCOPE_V3 LP objective coefficients','defaults':DEFAULT_EVIDENCE,'models':models})
current,old=models[0],next(m for m in models if m['label']=='PAPER_2025')
cs,os=current['electrical_asset_signatures'],old['electrical_asset_signatures']
diff={'current_only':sorted(set(cs)-set(os)),'paper2025_only':sorted(set(os)-set(cs)),'common_count':len(set(cs)&set(os)),'port_changes':{k:{'old':os[k]['ports'],'current':cs[k]['ports']} for k in cs.keys()&os.keys() if cs[k]['ports']!=os[k]['ports']},'parameter_changes':{k:{f:{'old':os[k]['parameters'].get(f),'current':cs[k]['parameters'].get(f)} for f in set(cs[k]['parameters'])|set(os[k]['parameters']) if cs[k]['parameters'].get(f)!=os[k]['parameters'].get(f)} for k in sorted(cs.keys()&os.keys())}}
save('A05_ELECTRICITY_INPUT_DIFF.json',diff)
configs=[]
for stem in ['baseline-aims-3H_2025','decarbonize-aims-3H_2050']:
    p=ROOT/'research/00_source_provenance/effective_config'/(stem+'.json');x=json.loads(p.read_text());s=x['sector']
    configs.append({'path':str(p),'sha256':sha(p.read_bytes()),'git_commit':x.get('git_commit'),'wildcards':x.get('wildcards'),'final_adjustment':x.get('final_adjustment'),'foresight':x.get('foresight'),'sector':{k:s.get(k,'KEY_ABSENT') for k in ['hydrogen','gas','oil','coal','lignite','ammonia','co2_network','biomass_transport','international_bunkers','shipping_hydrogen_share','H2_liquefaction','solid_biomass_potential','biogas_potential']}})
save('A05_SAFE_EFFECTIVE_CONFIG.json',configs)
print(json.dumps({'files':[(p.name,p.stat().st_size) for p in OUT.glob('A05_*.json')],'summary':[{k:m[k] for k in ['label','component_counts','classification_counts','load_bus_carriers','hydrogen_link_carrier_counts','hydrogen_store_count']} for m in models],'electric_diff':{k:v for k,v in diff.items() if k!='parameter_changes'}},ensure_ascii=False,indent=2))
