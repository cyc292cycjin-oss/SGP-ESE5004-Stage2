import rasterio, numpy as np, json, xarray as xr
thr = 400 * 8760 * 6
with rasterio.open("/home/jin/m08a_offshore_work/shipdensity_asean_cutout_extent.tif") as r:
    a = r.read(1); T = r.transform
print("dtype", a.dtype, "nodata", r.nodata, "shape", a.shape, "max", a.max())
for q in (thr, thr / 10, thr / 100, 400 * 8760, 400 * 6, 400):
    print(f"> {q:>12.0f}: {int((a > q).sum())} pixels")
ys, xs = np.nonzero(a > thr)
pts = [rasterio.transform.xy(T, int(y), int(x)) for y, x in zip(ys[:40], xs[:40])]
print("first exceeding pixels (lon, lat):", [(round(p[0], 3), round(p[1], 3)) for p in pts[:15]])
lons = np.array([rasterio.transform.xy(T, int(y), int(x))[0] for y, x in zip(ys, xs)]); lats = np.array([rasterio.transform.xy(T, int(y), int(x))[1] for y, x in zip(ys, xs)])
print("bbox of exceeding pixels", lons.min() if len(lons) else None, lons.max() if len(lons) else None, lats.min() if len(lats) else None, lats.max() if len(lats) else None)
p95 = np.percentile(a[a > 0], [50, 90, 99, 99.9, 99.99])
print("percentiles of positive pixels", p95)
A = json.load(open("/home/jin/wt_m08a_20261021/research_inputs/renewable_v5/offshore_m08a/OFFSHORE_PROFILES_LOG_pypsa_eur_v2025_07.json"))["potential_mw_by_country"]
B = json.load(open("/home/jin/m08a_offshore_work/no_ship_lanes/OFFSHORE_PROFILES_LOG_pypsa_eur_v2025_07_no_ship_lanes.json"))["potential_mw_by_country"]
for t in A:
    print(t, {c: round(B[t][c] - A[t][c], 1) for c in A[t] if abs(B[t][c] - A[t][c]) > 0})
av1 = xr.open_dataset("/home/jin/wt_m08a_20261021/research_inputs/renewable_v5/offshore_m08a/AVAILABILITY_pypsa_eur_v2025_07.nc")
av2 = xr.open_dataset("/home/jin/m08a_offshore_work/no_ship_lanes/AVAILABILITY_pypsa_eur_v2025_07_no_ship_lanes.nc")
for v in av1.data_vars:
    d = (av2[v] - av1[v]).values
    print(v, "max cell-share difference", float(np.abs(d).max()), "cells differing", int((np.abs(d) > 0).sum()))
