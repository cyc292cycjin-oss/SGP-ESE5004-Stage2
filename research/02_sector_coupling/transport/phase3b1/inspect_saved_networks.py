"""Read existing NetCDF evidence with xarray; no PyPSA import, workflow or solver."""
from pathlib import Path
import json,hashlib,math
import xarray as xr
import numpy as np
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
prior=ROOT/'research/00_source_provenance'
sha=lambda b:hashlib.sha256(b).hexdigest()
members=json.loads((prior/'RESULTS_MEMBER_HASHES.json').read_text())
cases=[('AUTHOR_REFERENCE',prior/e['path'].replace('\\','/'),e['sha256']) for e in members]
orig=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean')
name='elec_s_50_ec_lv2.0__3h_2030_0.071'
cases += [('TUTORIAL_PRE_STRIP',orig/f'results/baseline-aims-3H-tutorial/prenetworks/{name}_pre_adjusted.nc',None),('TUTORIAL_FINAL',orig/f'results/baseline-aims-3H-tutorial/postnetworks/{name}.nc',None)]
def plain(v):
    if isinstance(v,np.ndarray):return plain(v.tolist())
    if isinstance(v,np.generic):return plain(v.item())
    if isinstance(v,(list,tuple)):return [plain(x) for x in v]
    if isinstance(v,dict):return {str(k):plain(x) for k,x in v.items()}
    if isinstance(v,float) and not math.isfinite(v):return 'NaN' if math.isnan(v) else str(v)
    return v
out=[]
terms=['transport','shipping','kerosene','BEV','V2G','Li ion','Fischer','H2 Electrolysis','SMR','ammonia','Haber','methanol','co2 atmosphere']
for role,p,expected in cases:
    digest=sha(p.read_bytes());assert expected is None or digest==expected
    with xr.open_dataset(p) as ds:
        meta=json.loads(ds.attrs.get('meta','{}'))
        config={k:meta.get(k) for k in ['git_commit','sector','final_adjustment','demand_data','scenario','co2','wildcards']}
        counts={};selected={}
        for comp in ['buses','loads','links','stores','generators']:
            cs=ds.get(comp+'_carrier')
            if cs is None:continue
            carriers=cs.values.astype(str);names=ds[comp+'_i'].values.astype(str)
            vals,cnt=np.unique(carriers,return_counts=True);counts[comp]=dict(zip(vals.tolist(),cnt.tolist()))
            rows=[]
            for idx,(name,carrier) in enumerate(zip(names,carriers)):
                if not any(t.lower() in (name+' '+carrier).lower() for t in terms):continue
                row={'name':name,'carrier':carrier}
                for field in ['bus','bus0','bus1','bus2','bus3','p_nom','p_nom_extendable','e_nom','e_nom_extendable','e_cyclic','efficiency','efficiency2','efficiency3','capital_cost','marginal_cost','p_set']:
                    var=comp+'_'+field
                    if var in ds:row[field]=plain(ds[var].values[idx])
                rows.append(row)
            selected[comp]=rows
        load_records=[]
        for carrier in counts['loads']:
            if not any(t.lower() in carrier.lower() for t in ['transport','shipping','kerosene']):continue
            names=ds.loads_i.values[ds.loads_carrier.values==carrier]
            dyn_names=set(ds.get('loads_t_p_set_i',xr.DataArray([])).values.tolist())
            for n in names:
                bus=str(ds.loads_bus.sel(loads_i=n).item())
                country=str(ds.buses_country.sel(buses_i=bus).item()) if 'buses_country' in ds else bus[:2]
                if n in dyn_names:
                    profile=ds.loads_t_p_set.sel(loads_t_p_set_i=n)
                    weighted=float((profile*ds.snapshots_generators).sum());vmin=float(profile.min());vmax=float(profile.max())
                    mode='TIME_SERIES'
                else:
                    static=float(ds.loads_p_set.sel(loads_i=n)) if 'loads_p_set' in ds else 0
                    weighted=static*float(ds.snapshots_generators.sum());vmin=vmax=static;mode='STATIC'
                row=dict(name=str(n),carrier=carrier,country=country,mode=mode)
                if 'emissions' in carrier:
                    row.update(weighted_tCO2=weighted,min_tCO2_per_h=vmin,max_tCO2_per_h=vmax)
                else:row.update(weighted_MWh=weighted,min_MW=vmin,max_MW=vmax)
                load_records.append(row)
        rec=dict(role=role,path=str(p),sha256=digest,snapshots=ds.sizes.get('snapshots'),weights={n:float(ds[n].sum()) for n in ['snapshots_objective','snapshots_generators','snapshots_stores']},config=config,component_counts=counts,selected_components=selected,transport_loads=load_records,global_constraints={n:plain(ds[n].values) for n in ds.variables if n.startswith('global_constraints_')})
        out.append(rec)
        print(json.dumps(dict(role=role,file=p.name,transport_load_count=len(load_records))))
(R/'evidence/NETWORK_TRANSPORT_EVIDENCE.json').write_text(json.dumps(plain(out),indent=2,default=str,allow_nan=False))
