"""S3B R4.4 (decision 69): companion checks for barrier solutions without crossover.

* cleanup thresholds (reporting only): per variable group g (component x attribute), tau_g = cleanup_factor x BarConvTol x max|x_g|
  (cleanup_factor 10). Reason: at barrier termination the relative primal-dual gap is <= BarConvTol, so complementarity noise on a
  variable that should sit at its bound is bounded by the same relative tolerance times the scale of its group; the factor 10 covers
  presolve/postsolve and unscaling. A floor of 1e-6 (native unit) avoids a zero threshold in empty groups. Values with |x| < tau_g are
  reported as 0; the stored solution is not changed.
* simultaneous charge and discharge in the same snapshot: StorageUnits (p_store and p_dispatch both > tau), battery / home battery
  charger-discharger pairs on the same battery bus (both p0 > tau); Stores with a single p variable (H2 Store Tank, gas, ammonia,
  methanol, CO2) cannot charge and discharge at once (structurally zero), reported as such.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

GROUPS = [("Generator", "p_nom_opt", None), ("Link", "p_nom_opt", None), ("Line", "s_nom_opt", None), ("StorageUnit", "p_nom_opt", None), ("Store", "e_nom_opt", None),
          ("Generator", None, "p"), ("Link", None, "p0"), ("Line", None, "p0"), ("StorageUnit", None, "p_dispatch"), ("StorageUnit", None, "p_store"),
          ("StorageUnit", None, "state_of_charge"), ("Store", None, "p"), ("Store", None, "e")]


def _values(n, typ, static, series):
    if static:
        df = n.df(typ)
        ext = df[[c for c in df.columns if c.endswith("_extendable")][0]] if any(c.endswith("_extendable") for c in df.columns) else pd.Series(True, index=df.index)
        return df.loc[ext, static].astype(float).to_numpy()
    p = n.pnl(typ).get(series)
    return p.to_numpy(dtype=float).ravel() if p is not None and p.size else np.array([])


def cleanup_thresholds(n, barconvtol, factor=10.0, floor=1e-6):
    rows = {}
    for typ, static, series in GROUPS:
        v = _values(n, typ, static, series)
        key = f"{typ}.{static or series}"
        if v.size == 0:
            rows[key] = dict(tau=floor, max_abs=0.0, below=0, below_share_of_abs_sum=0.0); continue
        a = np.abs(v[np.isfinite(v)]); mx = float(a.max()) if a.size else 0.0
        tau = max(floor, factor * barconvtol * mx)
        small = (a > 0) & (a < tau)
        rows[key] = dict(tau=tau, max_abs=mx, nonzero=int((a > 0).sum()), below=int(small.sum()), below_share_of_abs_sum=float(a[small].sum() / a.sum()) if a.sum() > 0 else 0.0)
    return dict(rule=f"tau_g = {factor} x BarConvTol x max|x_g| (floor {floor})", barconvtol=barconvtol, factor=factor, groups=rows)


def apply_cleanup(n, thr):
    """Zero |x| < tau in place (use on a copy for reporting only)."""
    g = thr["groups"]
    for typ, static, series in GROUPS:
        tau = g[f"{typ}.{static or series}"]["tau"]
        if static:
            df = n.df(typ); col = df[static].astype(float); df.loc[col.abs() < tau, static] = 0.0
        else:
            p = n.pnl(typ).get(series)
            if p is not None and p.size:
                n.pnl(typ)[series] = p.where(p.abs() >= tau, 0.0)
    return n


def simultaneous_charge_discharge(n, thr):
    w = n.snapshot_weightings.stores
    out = {}
    su = n.storage_units
    if len(su):
        ps, pd_ = n.storage_units_t.p_store.reindex(columns=su.index, fill_value=0.0), n.storage_units_t.p_dispatch.reindex(columns=su.index, fill_value=0.0)
        tau = max(thr["groups"]["StorageUnit.p_store"]["tau"], thr["groups"]["StorageUnit.p_dispatch"]["tau"])
        both = (ps > tau) & (pd_ > tau); mn = np.minimum(ps, pd_).where(both, 0.0)
        by = {c: dict(instances=int(both[d.index].to_numpy().sum()), max_mw=float(mn[d.index].to_numpy().max(initial=0.0)), energy_mwh=float(mn[d.index].mul(w, axis=0).to_numpy().sum())) for c, d in su.groupby("carrier")}
        out["StorageUnit"] = dict(tau_mw=tau, instances=int(both.to_numpy().sum()), max_simultaneous_mw=float(mn.to_numpy().max(initial=0.0)), energy_mwh=float(mn.mul(w, axis=0).to_numpy().sum()), by_carrier=by)
    L = n.links; p0 = n.links_t.p0
    tau = thr["groups"]["Link.p0"]["tau"]
    for kind in ["battery", "home battery"]:
        ch = L[L.carrier == f"{kind} charger"]; dis = L[L.carrier == f"{kind} discharger"]
        inst = 0; mx = 0.0; en = 0.0; pairs = 0
        for name, z in ch.iterrows():
            d = dis[dis.bus0 == z.bus1]
            if not len(d):
                continue
            pairs += 1
            a = p0[name] if name in p0 else pd.Series(0.0, index=n.snapshots); b = p0[d.index[0]] if d.index[0] in p0 else pd.Series(0.0, index=n.snapshots)
            both = (a > tau) & (b > tau); mn = np.minimum(a, b).where(both, 0.0)
            inst += int(both.sum()); mx = max(mx, float(mn.max())); en += float((mn * w).sum())
        out[kind] = dict(pairs=pairs, tau_mw=tau, instances=inst, max_simultaneous_mw=mx, energy_mwh=en)
    single = n.stores.carrier.value_counts().to_dict()
    out["Store_single_p"] = dict(carriers=single, note="one p variable per Store: simultaneous charge and discharge is structurally impossible (H2 Store Tank, gas/ammonia/methanol/CO2 stores, battery energy stores behind charger/discharger links)")
    return out
