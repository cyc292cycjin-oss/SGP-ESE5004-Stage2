"""Read saved author NetCDF metadata and static tables, never call a solver."""
from pathlib import Path
import json, hashlib, xarray as xr, numpy as np
ROOT=Path(__file__).resolve().parent
def plain(x):
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    if isinstance(x,np.ndarray):return plain(x.tolist())
    if isinstance(x,np.generic):return plain(x.item())
    return x
def main():
    out=[]
    for entry in json.loads((ROOT/'RESULTS_MEMBER_HASHES.json').read_text()):
        p=ROOT/entry['path'].replace('\\','/')
        with xr.open_dataset(p) as ds:
            attrs=plain(ds.attrs)
            if 'meta' in attrs:
                try:attrs['meta_decoded']=json.loads(attrs['meta'])
                except Exception:pass
            selected={n:plain(ds[n].values) for n in ds.variables if n.startswith('global_constraints_')}
            counts={}
            for component in ['buses','generators','links','stores','loads','storage_units','lines']:
                key=component+'_carrier'
                if key in ds:
                    a,n=np.unique(ds[key].values,return_counts=True);counts[component]=dict(zip(a.tolist(),n.tolist()))
            weight={n:float(ds[n].sum()) for n in ['snapshots_objective','snapshots_generators','snapshots_stores'] if n in ds}
            loads={}
            if 'loads_t_p_set' in ds:
                for carrier in np.unique(ds['loads_carrier'].values):
                    names=ds['loads_i'].values[ds['loads_carrier'].values==carrier]
                    cols=[v for v in ds['loads_t_p_set_i'].values if v in names]
                    vals=ds['loads_t_p_set'].sel(loads_t_p_set_i=cols)
                    static_names=[v for v in names if v not in cols]
                    static=float(ds['loads_p_set'].sel(loads_i=static_names).sum()) if 'loads_p_set' in ds else 0.
                    loads[str(carrier)]={'time_series_count':len(cols),'static_count':len(static_names),'static_MW':static,'weighted_MWh':float((vals*ds['snapshots_generators']).sum())+static*weight['snapshots_generators']}
            rec={'member':entry['member'],'sha256':entry['sha256'],'attrs':attrs,'sizes':dict(ds.sizes),'global_constraints':selected,'components_by_carrier':counts,'snapshot_weightings':weight,'loads_time_series':loads,'variables':list(ds.variables)}
            out.append(rec)
    (ROOT/'RESULTS_NETWORK_EVIDENCE.json').write_text(json.dumps(out,indent=2,default=str))
    for e in out:
        print(e['member']); print(json.dumps({'attrkeys':list(e['attrs']),'simpleattrs':{k:v for k,v in e['attrs'].items() if k not in ['meta','meta_decoded']},'global_constraints':e['global_constraints']},indent=2,default=str))
if __name__=='__main__':main()
