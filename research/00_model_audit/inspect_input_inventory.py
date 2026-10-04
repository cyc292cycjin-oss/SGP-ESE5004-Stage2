"""Targeted inventory and stage comparison, read-only against model repository."""
import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
import xarray as xr
root,out=map(Path,sys.argv[1:3])
patterns=['data/demand/forecasts_on_historical_period.parquet','data/demand/unsd/data/*','data/energy_totals_DF_2030.csv','data/unsd_transactions.csv','data/AL_production.csv','data/industry/*','resources/industrial_database.csv','resources/ammonia_production.csv','resources/baseline-aims-3H-tutorial/powerplants*.csv','resources/baseline-aims-3H-tutorial/demand_profiles.csv','resources/baseline-aims-3H-tutorial/demand/*.csv','resources/baseline-aims-3H-tutorial/gas_networks/*','resources/baseline-aims-3H-tutorial/renewable_profiles/*','data/osm-plus-prebuilt/0.1.1/*.csv','data/transmission_projects/AIMS/*','data/transmission_projects/ID_SuperGrid/*','cutouts/asean-2013-era5*.nc']
records=[]
for pattern in patterns:
    paths=list(root.glob(pattern))
    if not paths: records.append({'pattern':pattern,'exists':False})
    for p in sorted(paths):
        if not p.is_file(): continue
        r={'file':str(p.relative_to(root)),'bytes':p.stat().st_size}
        if p.stat().st_size<10000000:
            b=p.read_bytes();r['sha256']=hashlib.sha256(b).hexdigest()
            if p.suffix=='.csv':
                dst=out/'input_snapshot'/p.relative_to(root);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
        else:r['sha256']=None;r['hash_reason']='Large file inventoried only; full archival hash pending'
        records.append(r)
stages=[]
for p in sorted((root/'results/baseline-aims-3H-tutorial').glob('prenetworks*/*2030*.nc')):
    with xr.open_dataset(p) as d:
        r={'file':str(p.relative_to(root)),'loads':{}}
        if 'loads_carrier' in d:
            for car in sorted(set(d.loads_carrier.values.tolist())):
                ids=d.loads_i.values[d.loads_carrier.values==car].tolist()
                r['loads'][car]={'count':len(ids)}
                if 'loads_p_set' in d:r['loads'][car]['static_p_set_sum']=float(d.loads_p_set.sel(loads_i=ids).sum())
                if 'loads_t_p_set' in d:
                    col=list(set(ids)&set(d.loads_t_p_set_i.values.tolist()))
                    r['loads'][car]['dynamic_values_sum']=float(d.loads_t_p_set.sel(loads_t_p_set_i=col).sum())
        stages.append(r)
(out/'INPUT_INVENTORY.json').write_text(json.dumps({'files':records,'stages_2030':stages},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(records),'stages':len(stages)}))
