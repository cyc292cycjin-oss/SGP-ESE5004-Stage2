"""Check only three absent finite-upper-bound families from saved network/schema."""
from pathlib import Path
import json, csv, io, hashlib
import numpy as np
import xarray as xr
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02_daily_build_20261012')
schema=json.loads((W/'CLOUD_BOUND_DEFAULTS.json').read_text(encoding='utf-8-sig'))
net=W/'cloud_evidence/daily_365_unsolved.nc'
assert hashlib.sha256(net.read_bytes()).hexdigest()=='b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2'
ds=xr.open_dataset(net);rows=[]
for s in schema['rows']:
    comp,field=s['component'],s['field'];default=next(csv.DictReader(io.StringIO(s['header']+'\n'+s['line'])))['default']
    assert float(default)==np.inf
    mask=np.asarray(ds[comp+'_'+field.replace('_max','_extendable')].values,dtype=bool)
    key=comp+'_'+field
    values=np.asarray(ds[key].values,dtype=float) if key in ds else np.full(len(mask),float(default))
    assert np.isposinf(values[mask]).all()
    rows.append({'component':comp,'field':field,'extendable_assets':int(mask.sum()),'persisted_in_NetCDF':key in ds,
       'schema_default':default,'finite_upper_bounds':int(np.isfinite(values[mask]).sum()),
       'expected_active_upper_rows':0,'reason':'All extendable assets have +Inf nominal upper bound, including schema defaults omitted in NetCDF serialization.',
       'schema_evidence':s})
out={'status':'THREE_ZERO_ROW_FAMILIES_EXPLAINED_FROM_SAVED_NETWORK_AND_ACTUAL_CLOUD_SCHEMA',
     'NetCDF_sha256':hashlib.sha256(net.read_bytes()).hexdigest(),'rows':rows,'new_model_builds':0,'optimizer_calls':0,
     'limit':'Explains only these three label families, not full matrix feasibility or row coefficients.'}
(W/'C02_ZERO_ROW_BOUNDARY_CHECK.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['component','extendable_assets','persisted_in_NetCDF','finite_upper_bounds']} for r in rows]))
