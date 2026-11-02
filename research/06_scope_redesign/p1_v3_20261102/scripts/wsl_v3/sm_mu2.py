"""Where is the capacity bound of a ship link in the LP? Non-extendable links, coordinates of Link-fix-p-upper, column bounds of Link-p, raw Pi and RC."""
import logging, sys, json
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
from pathlib import Path
import numpy as np, pandas as pd, pypsa, xarray as xr
logging.disable(logging.WARNING)
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke_r2")
sc = "integrated"; d = R / sc
n = pypsa.Network(d / f"{sc}_SMOKE_TEST_ONLY_solved.nc")
L = n.links; ship = L.index[L.carrier.isin(["oil non-fossil ship", "methanol ship", "ammonia ship", "liquid transit rail"])]
print("extendable among ships", int(L.loc[ship, "p_nom_extendable"].sum()), "non-extendable links", int((~L.p_nom_extendable).sum()), "p_nom_min/max sample", L.loc[ship[:2], ["p_nom", "p_min_pu", "p_max_pu"]].to_dict("index"))
print("non-extendable by carrier", L[~L.p_nom_extendable].carrier.astype(str).value_counts().head(12).to_dict())
ds = xr.open_dataset(d / "DUALS_BY_CONSTRAINT.nc")
a = ds["Link-fix-p-upper"]; print("dims", a.dims, {k: a[k].values[:4].tolist() for k in a.dims})
print("coords", list(ds.coords)[:12])
idx = pd.read_csv(d / "DUALS_INDEX.csv"); print(idx[idx.constraint.str.startswith("Link")].to_string()[:900])
print("lp files", sorted(p.name for p in (d / "lp").iterdir())[:16], "solution", sorted(p.name for p in (d / "solution").iterdir())[:8])
ms = n.links_t["mu_lower"].reindex(columns=ship); print("mu_lower ships nonzero", int((ms.abs().to_numpy() > 0).sum()), "abs max", float(ms.abs().max().max()))
