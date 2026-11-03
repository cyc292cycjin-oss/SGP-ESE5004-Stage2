"""V3 supplement 07 rerun (review EVDIAG section 2.2 item 10, "EV battery trajectory: the floor holds, cross-day transfer <= 1.59 TWh"), read-only on the solved networks
of the full pack, no solver. Per run V1 / V2 / V3 of the rerun, beside the same runs of the first screening (floor 0.1):
  floor values; every store and day end e / e_nom >= floor - 1e-6; energy above the floor summed over the 96 stores <= 0.2 x e_nom (1.587 TWh) + 1e-3 MWh every day;
  e_nom-weighted share of store-days at the floor (<= floor + 1e-4); annual throughput = sum of the positive day-to-day changes of every store (cyclic);
  storage rent sum_t lambda_t * w_obj * (e_{t-1} - e_t) / w_store (same formula as scripts/wsl_v3e/e2_soc.py).
Writes <out>/EV_TRAJECTORY_RERUN.json.   python v3r_ev.py <rerun full_unpacked/export> <first full_unpacked/export> <out dir>"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

NEW, OLD, OUT = map(Path, sys.argv[1:4]); OUT.mkdir(parents=True, exist_ok=True)
FILES = dict(V1="V1/integrated_DFX_365X24H_solved.nc", V2="V2/no_new_xb_DFX_365X24H_solved.nc", V3="V3/disconnected_DFX_365X24H_solved.nc")


def tframe(ds, comp, attr, cols):
    v = f"{comp}_t_{attr}"; names = ds[v + "_i"].values.astype(str); pos = {s: i for i, s in enumerate(names)}
    return pd.DataFrame(ds[v].values[:, [pos[c] for c in cols]], columns=cols)


def ev(path):
    ds = xr.open_dataset(path)
    st = sorted(s for s in ds["stores_i"].values.astype(str) if s.endswith(" EV battery store")); nodes = [s[: -len(" EV battery store")] for s in st]
    e_nom = pd.Series(ds["stores_e_nom"].values, index=ds["stores_i"].values.astype(str))[st]; En = float(e_nom.sum())
    e = tframe(ds, "stores", "e", st); lo = tframe(ds, "stores", "e_min_pu", st); w_st = float(ds["snapshots_stores"].values[0]); w_obj = float(ds["snapshots_objective"].values[0])
    lam = tframe(ds, "buses", "marginal_price", [f"{n} EV battery" for n in nodes]); lam.columns = st
    soc = e / e_nom; slack = soc - lo; prev = e.shift(1); prev.iloc[0] = e.iloc[-1]; de = e - prev
    above = (e - lo * e_nom).sum(axis=1); floor_level = float(np.unique(lo.to_numpy()).max())
    band = (1 - floor_level) * En
    at_floor = (slack <= 1e-4).mul(e_nom, axis=1).to_numpy().sum() / (En * len(e))
    r = dict(file=str(path.name), stores=len(st), days=int(len(e)), store_weight_h=w_st, floor_values=sorted({round(float(x), 10) for x in np.unique(lo.to_numpy())}),
             e_nom_twh=En / 1e6, band_above_floor_twh=band / 1e6, min_soc_minus_floor=float(slack.to_numpy().min()), violations_1e6=int((slack.to_numpy() < -1e-6).sum()),
             above_floor_max_twh=float(above.max()) / 1e6, above_floor_min_twh=float(above.min()) / 1e6, above_floor_within_band=bool((above <= band + 1e-3).all()),
             store_days_at_floor_share_enom=float(at_floor), soc_min=float(soc.to_numpy().min()), soc_max=float(soc.to_numpy().max()),
             throughput_twh=float(de.clip(lower=0).to_numpy().sum()) / 1e6, band_cycles=float(de.clip(lower=0).to_numpy().sum() / band) if band > 0 else None,
             system_cross_day_positive_twh=float((above - above.shift(1).fillna(above.iloc[-1])).clip(lower=0).sum()) / 1e6,
             storage_rent_bn_eur=float((lam * w_obj * (-de) / w_st).to_numpy().sum()) / 1e9, ev_battery_price_mean=float(lam.to_numpy().mean()))
    ds.close(); return r


res = {}
for rid, f in FILES.items():
    res[rid] = dict(rerun=ev(NEW / f), first_screening=ev(OLD / f))
    n = res[rid]["rerun"]; o = res[rid]["first_screening"]
    print(rid, "floor", n["floor_values"], "viol", n["violations_1e6"], "min slack %.2e" % n["min_soc_minus_floor"], "above max %.4f <= %.4f" % (n["above_floor_max_twh"], n["band_above_floor_twh"]),
          n["above_floor_within_band"], "at floor %.3f" % n["store_days_at_floor_share_enom"], "throughput %.2f (first %.2f)" % (n["throughput_twh"], o["throughput_twh"]),
          "rent %.3f (first %.3f)" % (n["storage_rent_bn_eur"], o["storage_rent_bn_eur"]))
res["passed"] = all(v["rerun"]["floor_values"] == [0.8] and v["rerun"]["violations_1e6"] == 0 and v["rerun"]["above_floor_within_band"] for v in res.values() if isinstance(v, dict) and "rerun" in v)
res["prediction_throughput_10_60_twh"] = {rid: 10 <= res[rid]["rerun"]["throughput_twh"] <= 60 for rid in FILES}
print("passed", res["passed"], "throughput in 10-60 TWh:", res["prediction_throughput_10_60_twh"])
(OUT / "EV_TRAJECTORY_RERUN.json").write_text(json.dumps(res, indent=1) + "\n")
