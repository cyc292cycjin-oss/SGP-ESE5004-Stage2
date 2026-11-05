import xarray as xr, numpy as np
for fn in ["integrated_2920_3h_unsolved.nc", "no_new_xb_2920_3h_unsolved.nc"]:
    ds = xr.open_dataset("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/" + fn)
    idx = list(ds["stores_i"].values)
    for name in [s for s in idx if "extra-ASEAN" in str(s)]:
        i = idx.index(name)
        rec = {k: ds["stores_" + k].values[i] for k in ["bus", "carrier", "e_nom_extendable", "e_nom", "e_nom_max", "e_nom_min", "e_min_pu", "e_max_pu", "e_initial", "e_cyclic", "capital_cost", "marginal_cost"] if "stores_" + k in ds}
        print(fn[:12], name, rec)
