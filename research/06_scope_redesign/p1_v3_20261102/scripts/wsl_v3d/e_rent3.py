"""V3 supplement 07, input to the predictions (read-only, no solver): EV battery storage rent and cross-day use in the solved V1 / V2 / V3 of the first screening (floor 0.1),
same formula as scripts/wsl_v3e/e2_soc.py (rent = sum_t lambda_t * w_obj * (e_{t-1} - e_t) / w_store, cyclic). V1 / V2 reproduce supplement 06 (1.952 / 2.021 bn); V3 is new.
Also: the battery energy above a 0.8 floor in the old solutions (how much of the old use fits in the new 0.2 band). Writes evidence/dmax/EV_RENT_SCREEN_V1_V2_V3.json."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

X = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z/full_unpacked/export")
OUT = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/dmax"); OUT.mkdir(parents=True, exist_ok=True)
NETS = {"V1": X / "V1/integrated_DFX_365X24H_solved.nc", "V2": X / "V2/no_new_xb_DFX_365X24H_solved.nc", "V3": X / "V3/disconnected_DFX_365X24H_solved.nc"}


def tframe(ds, comp, attr, cols):
    v = f"{comp}_t_{attr}"; names = ds[v + "_i"].values.astype(str); pos = {s: i for i, s in enumerate(names)}
    return pd.DataFrame(ds[v].values[:, [pos[c] for c in cols]], columns=cols)


res = {}
for label, path in NETS.items():
    ds = xr.open_dataset(path)
    st = sorted(s for s in ds["stores_i"].values.astype(str) if s.endswith(" EV battery store")); nodes = [s[: -len(" EV battery store")] for s in st]
    e_nom = pd.Series(ds["stores_e_nom"].values, index=ds["stores_i"].values.astype(str))[st]
    e = tframe(ds, "stores", "e", st); w_st = float(ds["snapshots_stores"].values[0]); w_obj = float(ds["snapshots_objective"].values[0])
    lam = tframe(ds, "buses", "marginal_price", [f"{n} EV battery" for n in nodes]); lam.columns = st
    prev = e.shift(1); prev.iloc[0] = e.iloc[-1]; de = e - prev
    rent = float((lam * w_obj * (-de) / w_st).sum().sum())
    E = e.sum(axis=1); En = float(e_nom.sum()); Ep = E.shift(1); Ep.iloc[0] = E.iloc[-1]
    res[label] = dict(stores=len(st), e_nom_twh=En / 1e6, storage_rent_bn_eur=rent / 1e9, ev_battery_price_mean=float(lam.to_numpy().mean()),
                      throughput_twh=float(de.clip(lower=0).to_numpy().sum()) / 1e6, system_cross_day_positive_twh=float((E - Ep).clip(lower=0).sum()) / 1e6,
                      system_soc_min=float(E.min() / En), system_soc_max=float(E.max() / En), store_days_below_08_share_enom=float(((e / e_nom) < 0.8 - 1e-6).mul(e_nom, axis=1).to_numpy().sum() / (En * len(e))))
    ds.close(); print(label, json.dumps(res[label]))
(OUT / "EV_RENT_SCREEN_V1_V2_V3.json").write_text(json.dumps(res, indent=1) + "\n")
