"""只读：v4 与 v5 陆上风电剖面文件中 SG2 0 的类别、p_nom_max 与平均容量因子。用法：python 67d_sg.py"""
from pathlib import Path

import xarray as xr

R = Path("/home/jin/wt_v5_x20/research_inputs")
for f in sorted((R / "renewable_v5").glob("profiles_calibrated_gwa_v5_c*_3h.nc")) + sorted(R.glob("**/profiles_calibrated_modern_c*_3h.nc"))[:4]:
    ds = xr.open_dataset(f)
    print("==", f.relative_to(R), list(ds.data_vars)[:20], dict(ds.sizes))
    for v in ds.data_vars:
        da = ds[v]
        dims = [d for d in da.dims if "bus" in d or "node" in d or "generator" in d or "name" in d]
        if not dims:
            continue
        idx = [str(x) for x in da[dims[0]].values]
        hit = [x for x in idx if x.startswith("SG")]
        if hit and ("onwind" in v or "onwind" in " ".join(hit) or v in ("p_nom_max", "potential", "profile")):
            sub = da.sel({dims[0]: [h for h in da[dims[0]].values if str(h).startswith("SG")]})
            print(v, dims, hit[:8], sub.mean([d for d in sub.dims if d not in dims]).values.round(4).tolist()[:8] if sub.ndim > 1 else sub.values.round(4).tolist()[:8])
    ds.close()
