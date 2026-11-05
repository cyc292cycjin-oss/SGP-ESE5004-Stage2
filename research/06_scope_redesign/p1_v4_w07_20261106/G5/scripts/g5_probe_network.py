"""G5 step 1: snapshot clock of the v3.1 F1 network and structure of the industry loads (read-only, no solve).

    python g5_probe_network.py --network <integrated_2920_3h_unsolved.nc> --solar1h <profile_solar_..._1h.nc> --out <G5 dir>/evidence

Checks (VERIFIED if they pass):
  1. snapshots: count, first / last, step, tz flag, weights.
  2. solar p_max_pu: mean daily cycle per country in snapshot hours; the hour of solar noon in UTC is 12 - lon/15, so a UTC index puts the
     peak at 03-06 h for 95-126 E; a local-clock index would put it at 11-13 h.
  3. the 1-hour solar profile (atlite, ERA5) gives the same test at 1-hour resolution per bus with its longitude.
  4. electricity loads with time series: mean daily cycle per country; evening peak at local 18-21 h -> snapshot hour 10-14 if UTC.
  5. industry loads: carriers, name patterns, p_set, buses (static or time series).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def frame(ds, comp: str, cols) -> pd.DataFrame:
    idx = ds[f"{comp}_i"].values
    return pd.DataFrame({c: ds[f"{comp}_{c}"].values for c in cols if f"{comp}_{c}" in ds}, index=[str(x) for x in idx])


def ts(ds, comp: str, attr: str) -> pd.DataFrame:
    k = f"{comp}_t_{attr}"
    if k not in ds:
        return pd.DataFrame()
    t = ds[k].to_pandas()
    t.columns = [str(c) for c in ds[f"{k}_i"].values]
    return t


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--solar1h", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True); a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    R = dict(network=str(a.network), network_sha256=sha256(a.network), solar1h=str(a.solar1h), solar1h_sha256=sha256(a.solar1h))
    ds = xr.open_dataset(a.network)
    sn = pd.DatetimeIndex(ds["snapshots_snapshot"].values)
    w = ds["snapshots_generators"].values if "snapshots_generators" in ds else None
    R["snapshots"] = dict(n=len(sn), first=str(sn[0]), last=str(sn[-1]), step_h=float((sn[1] - sn[0]) / pd.Timedelta("1h")), tz=str(sn.tz),
                          weight_sum_h=float(np.sum(w)) if w is not None else None, attrs_snapshot=dict(ds["snapshots_snapshot"].attrs))
    B = frame(ds, "buses", ["carrier", "country", "x", "y"])
    # 2. solar in the network
    G = frame(ds, "generators", ["bus", "carrier", "p_nom"])
    pm = ts(ds, "generators", "p_max_pu")
    sol = [g for g in G.index[G.carrier == "solar"] if g in pm.columns]
    rows = []
    for c in sorted(B.country.dropna().unique()):
        gs = [g for g in sol if B.at[G.at[g, "bus"], "country"] == c]
        if not gs:
            continue
        prof = pm[gs].mean(axis=1); prof.index = sn
        cyc = prof.groupby(sn.hour).mean()
        lon = float(B.loc[[G.at[g, "bus"] for g in gs], "x"].astype(float).mean())
        rows.append(dict(country=c, solar_generators=len(gs), mean_lon=lon, peak_snapshot_hour=int(cyc.idxmax()), utc_solar_noon_h=12 - lon / 15,
                         cycle=";".join(f"{h}:{v:.3f}" for h, v in cyc.items())))
    S = pd.DataFrame(rows); S.to_csv(a.out / "G5_SOLAR_PEAK_HOUR_NETWORK.csv", index=False, float_format="%.4f")
    # 3. 1-hour solar profile (atlite)
    p1 = xr.open_dataset(a.solar1h)
    R["solar1h_vars"] = {k: list(p1[k].dims) for k in p1.data_vars}
    var = "profile" if "profile" in p1 else list(p1.data_vars)[0]
    pr = p1[var]
    tdim = [d for d in pr.dims if "time" in d][0]
    t1 = pd.DatetimeIndex(p1[tdim].values)
    other = [d for d in pr.dims if d != tdim]
    prof1 = pr.mean(dim=[d for d in other if d != "bus"]) if len(other) > 1 else pr
    P1 = prof1.to_pandas()
    if P1.index.name != tdim:
        P1 = P1.T
    rows1 = []
    for b in P1.columns:
        cyc = P1[b].groupby(t1.hour).mean()
        nb = str(b).split("|")[0]   # profile columns are "<network bus>|<resource class>"
        x = float(B.at[nb, "x"]) if nb in B.index else np.nan
        rows1.append(dict(bus=str(b), country=B.at[nb, "country"] if nb in B.index else "", lon=x, peak_hour_1h=int(cyc.idxmax()),
                          utc_solar_noon_h=12 - x / 15 if x == x else np.nan,
                          centroid_hour=float((cyc * (cyc.index + 0.5)).sum() / cyc.sum())))
    S1 = pd.DataFrame(rows1); S1.to_csv(a.out / "G5_SOLAR_PEAK_HOUR_1H.csv", index=False, float_format="%.4f")
    R["solar1h"] = dict(var=var, dims=list(pr.dims), time_first=str(t1[0]), time_last=str(t1[-1]), n_time=len(t1), tz=str(t1.tz),
                        buses=len(rows1), centroid_minus_noon_median_h=float((S1.centroid_hour - S1.utc_solar_noon_h).median()),
                        centroid_minus_noon_p05_p95=[float((S1.centroid_hour - S1.utc_solar_noon_h).quantile(q)) for q in (0.05, 0.95)])
    # 4/5. loads
    L = frame(ds, "loads", ["bus", "carrier", "p_set"])
    L["country"] = [B.at[b, "country"] if b in B.index else "" for b in L.bus]
    L["bus_carrier"] = [B.at[b, "carrier"] if b in B.index else "" for b in L.bus]
    lt = ts(ds, "loads", "p_set")
    L["has_ts"] = L.index.isin(lt.columns)
    car = L.groupby(["carrier", "bus_carrier", "has_ts"]).agg(n=("bus", "size"), twh_static=("p_set", lambda s: float(s.astype(float).sum() * 8760 / 1e6))).reset_index()
    car.to_csv(a.out / "G5_LOAD_CARRIERS.csv", index=False, float_format="%.4f")
    L.to_csv(a.out / "G5_LOADS_ALL.csv", float_format="%.6f")
    ele = [l for l in lt.columns if L.at[l, "bus_carrier"] == "AC"]
    rows = []
    for c in sorted(L.country.unique()):
        ls_ = [l for l in ele if L.at[l, "country"] == c]
        if not ls_:
            continue
        s = lt[ls_].sum(axis=1); s.index = sn
        cyc = s.groupby(sn.hour).mean()
        rows.append(dict(country=c, ts_loads=len(ls_), carriers=";".join(sorted(L.loc[ls_, "carrier"].unique())), peak_snapshot_hour=int(cyc.idxmax()),
                         trough_snapshot_hour=int(cyc.idxmin()), peak_over_mean_3h=float(s.max() / s.mean()), twh=float((s * 3).sum() / 1e6)))
    pd.DataFrame(rows).to_csv(a.out / "G5_ELEC_LOAD_CYCLE.csv", index=False, float_format="%.4f")
    R["loads"] = dict(total=len(L), with_ts=int(L.has_ts.sum()), ts_carriers=sorted(L[L.has_ts].carrier.unique().tolist()), carriers=int(L.carrier.nunique()))
    R["meta_keys"] = sorted(json.loads(ds.attrs.get("meta", "{}")).keys()) if isinstance(ds.attrs.get("meta"), str) else None
    (a.out / "G5_PROBE_NETWORK.json").write_text(json.dumps(R, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(R, indent=1, default=str)[:3000])
    print(S.drop(columns="cycle").to_string())
    print(pd.DataFrame(rows).to_string())
    print(car.to_string())


if __name__ == "__main__":
    main()
