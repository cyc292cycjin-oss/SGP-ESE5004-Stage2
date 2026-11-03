"""V3 supplement 06, read-only probe: netCDF variable names for the EV pieces in the networks the diagnosis reads."""
import sys
import xarray as xr
for p in sys.argv[1:]:
    ds = xr.open_dataset(p)
    print("==", p.split("/")[-1], "snapshots", ds.sizes.get("snapshots"))
    keys = [k for k in ds.variables if k.startswith(("stores_t", "snapshots", "links_t_p_max_pu", "loads_t", "buses_t", "stores_e_nom", "stores_e_min", "stores_e_cyc", "stores_t_e")) or k in ("stores_i",)]
    print(" ", sorted(keys)[:60])
    st = [s for s in ds["stores_i"].values.astype(str) if "EV battery" in s]
    print("  EV stores", len(st), st[:3])
    for v in ("stores_t_e_min_pu", "stores_t_e"):
        if v in ds:
            dim = [d for d in ds[v].dims if d != "snapshots"][0]
            names = ds[dim].values.astype(str)
            print(" ", v, ds[v].shape, "EV cols", sum("EV battery" in s for s in names))
    ds.close()
