import xarray as xr, numpy as np, json
ds = xr.open_dataset("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/integrated_2920_3h_unsolved.nc")
names = ds["loads_i"].values; ps = ds["loads_p_set"].values; car = ds["loads_carrier"].values
m = (np.abs(ps) > 0) & (np.abs(ps) < 1e-9)
rows = sorted([(str(n), float(p), str(c)) for n, p, c in zip(names[m], ps[m], car[m])], key=lambda r: r[1])
print(len(rows)); 
for r in rows: print(f"{r[1]:.3e}  {r[2]:<22} {r[0]}")
tv = set(ds["loads_t_p_set_i"].values) if "loads_t_p_set_i" in ds else set()
print("with time series:", sum(1 for r in rows if r[0] in tv))
