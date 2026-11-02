"""Are the ship capacity duals real zeros? Check the raw Pi of the Link-fix-p-upper rows for the ship and transit links, and the reduced costs on the flow variables."""
import json, logging, sys
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
from pathlib import Path
import numpy as np, pandas as pd, pypsa, xarray as xr
logging.disable(logging.WARNING)
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke_r2")
for sc in ("integrated", "no_new_xb"):
    d = R / sc
    n = pypsa.Network(d / f"{sc}_SMOKE_TEST_ONLY_solved.nc")
    L = n.links; ship = L.index[L.carrier.isin(["oil non-fossil ship", "methanol ship", "ammonia ship", "liquid transit rail"])]
    print("==", sc, "links_t keys", [k for k in n.links_t if len(n.links_t[k].columns)][:12])
    mu = n.links_t["mu_upper"]
    print(" mu_upper columns", len(mu.columns), "ship columns present", len(mu.columns.intersection(ship)), "nonzero overall", int((mu.abs().to_numpy() > 0).sum()), "abs max overall", float(mu.abs().max().max()) if len(mu.columns) else None)
    idx = pd.read_csv(d / "DUALS_INDEX.csv")
    print(" DUALS_INDEX", list(idx.columns)[:8], [x for x in idx.iloc[:, 0].astype(str) if "Link" in x][:12])
    ds = xr.open_dataset(d / "DUALS_BY_CONSTRAINT.nc")
    names = [v for v in ds.data_vars if "Link" in str(v)]
    print(" duals vars", names[:12])
    for v in names:
        if "fix" in str(v) and "upper" in str(v):
            a = ds[v]; dim = [x for x in a.dims if x != "snapshot"][0]
            names_in = pd.Index(a[dim].values.astype(str)); sel = names_in.intersection(ship)
            sub = a.sel({dim: sel}).values
            print(" ", v, a.shape, "ship rows", len(sel), "nan", int(np.isnan(sub).sum()), "exact zero", int((sub == 0).sum()), "nonzero", int((sub != 0).sum()), "abs max", float(np.nanmax(np.abs(sub))) if sub.size else None,
                  "others abs max", float(np.nanmax(np.abs(a.values))), "others nonzero", int(np.nansum(a.values != 0)))
    p0 = n.links_t.p0[ship]
    print(" flows: active links", int((p0.abs().max() > 1).sum()), "max MW", float(p0.max().max()), "reverse flow min", float(p0.min().min()), "util top", (p0.max() / L.p_nom[ship]).sort_values(ascending=False).head(3).round(4).to_dict())
    print(" caps MW", L.loc[ship].groupby(L.carrier.astype(str)).p_nom.agg(["min", "max"]).round(0).to_dict("index"))
