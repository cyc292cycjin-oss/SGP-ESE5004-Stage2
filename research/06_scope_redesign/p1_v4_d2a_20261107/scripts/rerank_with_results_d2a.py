#!/usr/bin/env python3
"""V4 D2a section 4 (decision 219): copy of the V4 W10 rerank_with_results.py (work/p1_v4_w10_20261106, unchanged) with the W10 stage-2 method corrections -
CO2 storage cap duals read from the Store e_nom bound as well (duplicate limit), S-B shipping rows out of the ranking in S-A runs, a bias column (cost = upper,
right-hand side = lower, coefficient = indefinite), notches refreshed from this branch's registry (--registry-ranges), memory / solver guard before any network
read, Store e_nom bound duals supplemented from the duals file alone. First-order impact of the in-use grade-C parameters on B6 and Owen.

For one or more sets of solved results (each set = an integrated run F1 and a no_new_xb run F2 with their export folders) the script
  1. extracts what the envelope theorem needs from every solved network (dispatch, capacities, nodal prices, bound duals, global-constraint
     duals, cost breakdown, Owen allocation) into a cache keyed by the SHA256 of the solved network (re-runs reuse it);
  2. evaluates, for every row of C_GRADE_INVENTORY.csv, the first-order change of the objective of F1 and F2 for the registered (or proposed)
     notch in both directions: dZ = quantity x unit-cost change (cost rows), = constraint dual x right-hand-side change (capacity / potential
     rows), = - sum(price x flow) x efficiency change (efficiency rows), = sum(price x load change) (route-share rows);
     dB6 = dZ(F2) - dZ(F1); the Owen effect by country = dZ(F1) attributed to the country of the component / load / constraint (INFERENCE);
  3. flags the estimates that first order cannot be trusted with (bound status would change inside the notch, candidate would enter,
     investment in F1 and F2 differs strongly, zero-slack / degenerate dual, large or regime-changing notch, discrete rules);
  4. ranks by |dB6| in the reference set, reports the rank in every other set and the stability, writes the W10 tables.

Read only. No solver, no network build. Needs the pypsa-earth environment (pypsa, xarray, pandas).

usage:
  python rerank_with_results.py --set s07=<F1 dir>,<F2 dir> [--set smoke=<F1>,<F2> ...] --reference s07 \
      --inventory C_GRADE_INVENTORY.csv --repo /home/jin/wt_v4_w10 --cache cache --out <dir>
A run dir holds '*_solved.nc', DUALS_BY_CONSTRAINT.nc, NODAL_PRICES.csv, COMPONENT_COST_BREAKDOWN.csv, costs_active_research.csv,
RUN.json and m12_owen/OWEN.csv (the export folder of scripts_project/s2_solve.py / dfx_batch.py / b4_batch4.py).
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA = "v4-w10-first-order-v1"   # cache schema unchanged (the W15 extracts are reused); D2a adds stores_enom_upper.csv next to them
BIAS = {"cost": "dZ upper bound (first order at the solution; V(c) concave: V(c+dc) <= V(c) + x*dc)",
        "rhs": "dZ lower bound (V(b) convex; the dual is a subgradient: V(b+db) >= V(b) + y*db)",
        "coefficient": "indefinite (matrix coefficient / regime change: no one-sided bound)",
        "discrete": "indefinite (discrete alternative: first order = fixed capacities)", "none": ""}
MECH_CLASS = {"store_mc": "cost", "link_mc": "cost", "gen_mc": "cost", "gen_mc_rel": "cost", "gen_cc": "cost", "gen_cc_part": "cost", "aeo8_factor": "cost",
              "store_cc": "cost", "store_cc_factor": "cost", "line_length_cc": "cost", "typhoon": "cost", "lao_rail": "cost", "new_store_bus_value": "rhs",
              "store_pot": "rhs", "store_pot_scale": "rhs", "gen_pnom_max": "rhs", "su_pnom_max": "rhs", "scalar_rhs": "rhs", "link_pnom_fixed": "rhs",
              "store_enom_fixed": "rhs", "store_floor": "rhs", "ev_fleet": "rhs", "line_existing": "rhs", "fixed_emission_scale": "rhs", "new_capacity_rc": "rhs",
              "transport_shift": "rhs", "shipping_shift": "rhs", "agri_shift": "rhs", "ev_load_scale": "rhs",
              "link_eff": "coefficient", "link_eff_km": "coefficient", "gen_cf": "coefficient", "meoh_eff": "coefficient", "hb_eff": "coefficient", "unbuilt_check": "coefficient",
              "wacc_mode": "discrete", "gas_alloc": "discrete", "discrete": "discrete", "zero": "none", "demand_I2": "none"}
MIN_FREE_GIB = 8.0


def _guard_before_network_read(what: str) -> None:
    """D2a 4.4: a solved network is read only when no local Gurobi process runs and >= 8 GiB are available."""
    import subprocess
    try:
        ps = subprocess.run(["ps", "-eo", "args="], capture_output=True, text=True).stdout
    except Exception:
        ps = ""
    busy = [l for l in ps.splitlines() if ("gurobi_cl" in l or "s2_solve.py" in l) and "grep" not in l]
    if busy:
        raise SystemExit(f"refusing to read {what}: a solver process is running ({busy[0][:80]})")
    try:
        avail = next(int(l.split()[1]) for l in open("/proc/meminfo") if l.startswith("MemAvailable")) / 1048576.0
    except Exception:
        avail = float("nan")
    if not (avail >= MIN_FREE_GIB):
        raise SystemExit(f"refusing to read {what}: {avail:.1f} GiB available < {MIN_FREE_GIB} GiB")


def supplement_store_bounds(run_dir: Path, cache_dir: Path) -> Path:
    """D2a 4.1: Store e_nom upper-bound duals (Store-ext-e_nom-upper, raw linopy sign) from DUALS_BY_CONSTRAINT.nc alone -> cache stores_enom_upper.csv."""
    out = cache_dir / "stores_enom_upper.csv"
    if out.exists():
        return out
    import xarray as xr
    ds = xr.open_dataset(run_files(run_dir)["duals"])
    s = _dual1d(ds, "Store-ext-e_nom-upper"); ds.close()
    pd.DataFrame(dict(mu_enom_upper=s)).rename_axis("Store").to_csv(out)
    return out
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
TOL_EXHAUSTED = 1e-4      # e_end / e_initial below this = resource exhausted
TOL_BUILT = 1.0           # MW (or t, MWh) of new capacity below this = unbuilt
NOT_RANKED = ("zero", "discrete", "demand_I2")


def sha256(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def af(r: float, life: float) -> float:
    if not (life and life > 0):
        return float("nan")
    return r / (1.0 - (1.0 + r) ** (-life)) if r > 0 else 1.0 / life


# ------------------------------------------------------------------------------------------------------------------------------
# 1. extraction
# ------------------------------------------------------------------------------------------------------------------------------
def run_files(run_dir: Path) -> dict:
    nc = sorted(glob.glob(str(run_dir / "*_solved.nc")))
    if len(nc) != 1:
        raise SystemExit(f"{run_dir}: expected exactly one *_solved.nc, found {len(nc)}")
    f = dict(nc=Path(nc[0]), duals=run_dir / "DUALS_BY_CONSTRAINT.nc", prices=run_dir / "NODAL_PRICES.csv", ccb=run_dir / "COMPONENT_COST_BREAKDOWN.csv",
             costs=run_dir / "costs_active_research.csv", run=run_dir / "RUN.json", owen=run_dir / "m12_owen" / "OWEN.csv")
    missing = [k for k, p in f.items() if not Path(p).exists() and k not in ("owen", "run")]
    if missing:
        raise SystemExit(f"{run_dir}: missing {missing}")
    return f


def _dual2d(ds, name, T):
    """(T x components) DataFrame of a per-snapshot dual (raw linopy sign), or None."""
    if name not in ds:
        return None
    da = ds[name]
    snap = [d for d in da.dims if d.endswith("|snapshot")]
    comp = [d for d in da.dims if not d.endswith("|snapshot")]
    if len(snap) != 1 or len(comp) != 1:
        return None
    da = da.transpose(snap[0], comp[0])
    vals = np.nan_to_num(da.values.astype(float))
    if vals.shape[0] != T:
        raise SystemExit(f"dual {name}: {vals.shape[0]} snapshots, network has {T}")
    return pd.DataFrame(vals, columns=[str(x) for x in da[comp[0]].values])


def _dual1d(ds, name):
    if name not in ds:
        return pd.Series(dtype=float)
    da = ds[name]
    if da.ndim != 1:
        return pd.Series(dtype=float)
    return pd.Series(np.nan_to_num(da.values.astype(float)), index=[str(x) for x in da[da.dims[0]].values])


def extract(run_dir: Path, cache_root: Path) -> Path:
    import pypsa
    import xarray as xr
    f = run_files(run_dir)
    key = sha256(f["nc"])
    out = cache_root / (key[:16] + "_" + SCHEMA.rsplit("-", 1)[-1])
    if (out / "DONE").exists():
        supplement_store_bounds(run_dir, out)
        return out
    out.mkdir(parents=True, exist_ok=True)
    _guard_before_network_read(str(f["nc"]))
    n = pypsa.Network(str(f["nc"]))
    T = len(n.snapshots)
    w = n.snapshot_weightings.objective.to_numpy(float)
    wst = n.snapshot_weightings.stores.to_numpy(float)
    ds = xr.open_dataset(f["duals"])
    # nodal prices EUR/MWh = balance dual / objective weight (Bus-nodal_balance and Bus-meshed-nodal_balance cover disjoint buses)
    parts = [x for x in (_dual2d(ds, "Bus-nodal_balance", T), _dual2d(ds, "Bus-meshed-nodal_balance", T)) if x is not None]
    lam = pd.concat(parts, axis=1)
    lam = lam.loc[:, ~lam.columns.duplicated()].div(w, axis=0).fillna(0.0)
    pr = pd.read_csv(f["prices"])   # cross-check of the time-weighted mean against the exported NODAL_PRICES.csv
    chk = pd.DataFrame(dict(exported=pd.to_numeric(pr.set_index("bus")["mean"], errors="coerce"),
                            from_duals=pd.Series((lam.to_numpy() * w[:, None]).sum(0) / w.sum(), index=lam.columns))).dropna()
    price_check = dict(buses=int(len(chk)), max_abs_diff=float((chk.exported - chk.from_duals).abs().max()) if len(chk) else None,
                       max_rel_diff=float(((chk.exported - chk.from_duals).abs() / chk.exported.abs().clip(lower=1.0)).max()) if len(chk) else None)
    bc = n.buses.country.astype(str).replace({"nan": ""})

    def lam_of(buses: pd.Series) -> np.ndarray:
        return lam.reindex(columns=[str(b) for b in buses]).fillna(0.0).to_numpy()

    def country(df, bus_col="bus"):
        c = df["country"].astype(str).replace({"nan": ""}) if "country" in df else pd.Series("", index=df.index)
        alt = df[bus_col].map(bc).fillna("")
        return c.where(c.isin(COUNTRIES), alt)

    # generators
    G = n.generators
    p = n.generators_t.p.reindex(columns=G.index, fill_value=0.0).to_numpy(float)
    pmax = n.get_switchable_as_dense("Generator", "p_max_pu").reindex(columns=G.index).to_numpy(float)
    du = pd.concat([x for x in (_dual2d(ds, "Generator-ext-p-upper", T), _dual2d(ds, "Generator-fix-p-upper", T)) if x is not None], axis=1)
    du = du.reindex(columns=G.index, fill_value=0.0).to_numpy(float)
    avail = (np.abs(du) * pmax).sum(0)
    g = pd.DataFrame(dict(carrier=G.carrier, bus=G.bus, country=country(G), p_nom=G.p_nom, p_nom_opt=G.p_nom_opt, p_nom_max=G.p_nom_max,
                          ext=G.p_nom_extendable, capital_cost=G.capital_cost, marginal_cost=G.marginal_cost,
                          energy=(p * n.snapshot_weightings.generators.to_numpy(float)[:, None]).sum(0), value=(p * lam_of(G.bus) * w[:, None]).sum(0),
                          avail_value_per_mw=avail, cf_value=avail * G.p_nom_opt.to_numpy(float),
                          mu_pnom_upper=np.abs(_dual1d(ds, "Generator-ext-p_nom-upper").reindex(G.index).fillna(0.0).to_numpy()),
                          cf_hours=(pmax * n.snapshot_weightings.generators.to_numpy(float)[:, None]).sum(0)))
    g["new_cap"] = np.where(g.ext, (g.p_nom_opt - g.p_nom).clip(lower=0.0), 0.0)
    g["rc_per_mw"] = np.where(g.ext, g.capital_cost - g.avail_value_per_mw, np.nan)
    g.to_csv(out / "generators.csv")
    del p, pmax, du
    # links
    K = n.links
    p0 = n.links_t.p0.reindex(columns=K.index, fill_value=0.0).to_numpy(float)
    pmaxk = n.get_switchable_as_dense("Link", "p_max_pu").reindex(columns=K.index).to_numpy(float)
    duk = pd.concat([x for x in (_dual2d(ds, "Link-ext-p-upper", T), _dual2d(ds, "Link-fix-p-upper", T)) if x is not None], axis=1)
    duk = duk.reindex(columns=K.index, fill_value=0.0).to_numpy(float)
    availk = (np.abs(duk) * pmaxk).sum(0)
    k = pd.DataFrame(dict(carrier=K.carrier, bus0=K.bus0, bus1=K.bus1, country=country(K, "bus0"), country1=K.bus1.map(bc).fillna(""),
                          p_nom=K.p_nom, p_nom_opt=K.p_nom_opt, ext=K.p_nom_extendable, capital_cost=K.capital_cost, marginal_cost=K.marginal_cost,
                          efficiency=K.efficiency, length=K.length, flow0=(p0 * w[:, None]).sum(0), flow0_pos=(np.clip(p0, 0, None) * w[:, None]).sum(0),
                          avail_value_per_mw=availk, mu_pnom_upper=np.abs(_dual1d(ds, "Link-ext-p_nom-upper").reindex(K.index).fillna(0.0).to_numpy())))
    k["route_km"] = K["route_km"] if "route_km" in K else np.nan
    for j in (1, 2, 3, 4):
        b = f"bus{j}"
        if b in K:
            k[b] = K[b].astype(str)
            if j > 1:
                k[f"efficiency{j}"] = K[f"efficiency{j}"] if f"efficiency{j}" in K else np.nan
            k[f"v{j}"] = (p0 * lam_of(K[b].astype(str)) * w[:, None]).sum(0)
    k["new_cap"] = np.where(k.ext, (k.p_nom_opt - k.p_nom).clip(lower=0.0), 0.0)
    k["rc_per_mw"] = np.where(k.ext, k.capital_cost - k.avail_value_per_mw, np.nan)
    k.to_csv(out / "links.csv")
    del p0, pmaxk, duk
    # stores
    S = n.stores
    ps = n.stores_t.p.reindex(columns=S.index, fill_value=0.0).to_numpy(float)
    es = n.stores_t.e.reindex(columns=S.index, fill_value=0.0).to_numpy(float)
    emax = n.get_switchable_as_dense("Store", "e_max_pu").reindex(columns=S.index).to_numpy(float)
    emin = n.get_switchable_as_dense("Store", "e_min_pu").reindex(columns=S.index).to_numpy(float)
    dis = np.clip(ps, 0, None)
    lamS = lam_of(S.bus)
    den = (dis * w[:, None]).sum(0)
    rent = np.where(den > 0, ((lamS - S.marginal_cost.to_numpy(float)[None, :]) * dis * w[:, None]).sum(0) / np.where(den > 0, den, 1.0), np.nan)
    duf = _dual2d(ds, "Store-fix-e-upper", T); dlf = _dual2d(ds, "Store-fix-e-lower", T); due = _dual2d(ds, "Store-ext-e-upper", T)
    duf = (duf if duf is not None else pd.DataFrame(index=range(T))).reindex(columns=S.index, fill_value=0.0).to_numpy(float)
    dlf = (dlf if dlf is not None else pd.DataFrame(index=range(T))).reindex(columns=S.index, fill_value=0.0).to_numpy(float)
    due = (due if due is not None else pd.DataFrame(index=range(T))).reindex(columns=S.index, fill_value=0.0).to_numpy(float)
    s = pd.DataFrame(dict(carrier=S.carrier, bus=S.bus, country=country(S), e_nom=S.e_nom, e_nom_opt=S.e_nom_opt, ext=S.e_nom_extendable,
                          e_initial=S.e_initial, capital_cost=S.capital_cost, marginal_cost=S.marginal_cost, discharge=(dis * wst[:, None]).sum(0),
                          e_end=es[-1, :], rent=rent, d_enom_fixed=(duf * emax).sum(0) + (dlf * emin).sum(0),
                          floor_value=(dlf * (emin > 0)).sum(0) * S.e_nom.to_numpy(float), avail_value_per_unit=(np.abs(due) * emax).sum(0),
                          lam_bus_mean=(lamS * w[:, None]).sum(0) / w.sum()))
    s["new_cap"] = np.where(s.ext, (s.e_nom_opt - s.e_nom).clip(lower=0.0), 0.0)
    s["rc_per_unit"] = np.where(s.ext, s.capital_cost - s.avail_value_per_unit, np.nan)
    s.to_csv(out / "stores.csv")
    pd.DataFrame(dict(mu_enom_upper=_dual1d(ds, "Store-ext-e_nom-upper").reindex(S.index).fillna(0.0))).rename_axis("Store").to_csv(out / "stores_enom_upper.csv")   # D2a 4.1
    del ps, es, emax, emin, dis, lamS, duf, dlf, due
    # storage units
    U = n.storage_units
    pmu = n.get_switchable_as_dense("StorageUnit", "p_max_pu").reindex(columns=U.index).to_numpy(float)
    duu = pd.concat([x for x in (_dual2d(ds, "StorageUnit-ext-p_dispatch-upper", T), _dual2d(ds, "StorageUnit-fix-p_dispatch-upper", T)) if x is not None], axis=1)
    duu = duu.reindex(columns=U.index, fill_value=0.0).to_numpy(float)
    u = pd.DataFrame(dict(carrier=U.carrier, bus=U.bus, country=country(U), p_nom=U.p_nom, p_nom_opt=U.p_nom_opt, p_nom_max=U.p_nom_max, ext=U.p_nom_extendable,
                          capital_cost=U.capital_cost, avail_value_per_mw=(np.abs(duu) * pmu).sum(0),
                          mu_pnom_upper=np.abs(_dual1d(ds, "StorageUnit-ext-p_nom-upper").reindex(U.index).fillna(0.0).to_numpy())))
    u["new_cap"] = np.where(u.ext, (u.p_nom_opt - u.p_nom).clip(lower=0.0), 0.0)
    u["rc_per_mw"] = np.where(u.ext, u.capital_cost - u.avail_value_per_mw, np.nan)
    u.to_csv(out / "storage_units.csv")
    # lines
    L = n.lines
    smx = n.get_switchable_as_dense("Line", "s_max_pu").reindex(columns=L.index).to_numpy(float)
    dlu = pd.concat([x for x in (_dual2d(ds, "Line-ext-s-upper", T), _dual2d(ds, "Line-fix-s-upper", T)) if x is not None], axis=1).reindex(columns=L.index, fill_value=0.0).to_numpy(float)
    dll = pd.concat([x for x in (_dual2d(ds, "Line-ext-s-lower", T), _dual2d(ds, "Line-fix-s-lower", T)) if x is not None], axis=1).reindex(columns=L.index, fill_value=0.0).to_numpy(float)
    l = pd.DataFrame(dict(bus0=L.bus0, bus1=L.bus1, country0=L.bus0.map(bc), country1=L.bus1.map(bc), s_nom=L.s_nom, s_nom_min=L.s_nom_min, s_nom_max=L.s_nom_max,
                          s_nom_opt=L.s_nom_opt, ext=L.s_nom_extendable, capital_cost=L.capital_cost, length=L.length,
                          congestion_value_per_mw=((np.abs(dlu) + np.abs(dll)) * smx).sum(0),
                          dual_snom_lower=_dual1d(ds, "Line-ext-s_nom-lower").reindex(L.index).fillna(0.0).to_numpy(),
                          dual_snom_upper=_dual1d(ds, "Line-ext-s_nom-upper").reindex(L.index).fillna(0.0).to_numpy()))
    l["new_cap"] = np.where(l.ext, (l.s_nom_opt - l.s_nom).clip(lower=0.0), 0.0)
    l.to_csv(out / "lines.csv")
    # loads and buses
    Ld = n.loads
    pset = n.get_switchable_as_dense("Load", "p_set").reindex(columns=Ld.index).to_numpy(float)
    ld = pd.DataFrame(dict(carrier=Ld.carrier, bus=Ld.bus, country=Ld.bus.map(bc).fillna(""), energy=(pset * w[:, None]).sum(0),
                           value=(pset * lam_of(Ld.bus) * w[:, None]).sum(0)))
    ld.to_csv(out / "loads.csv")
    bus = pd.DataFrame(dict(carrier=n.buses.carrier, country=bc, lam_mean=(lam.reindex(columns=n.buses.index).fillna(0.0).to_numpy() * w[:, None]).sum(0) / w.sum()))
    bus.to_csv(out / "buses.csv")
    scal = {v: float(np.nan_to_num(ds[v].values)) for v in ds.data_vars if ds[v].ndim == 0}
    # cost breakdown, costs, Owen, meta
    ccb = pd.read_csv(f["ccb"])
    caps = pd.concat([g[["new_cap", "country"]].assign(component="Generator"), k[["new_cap", "country"]].assign(component="Link"),
                      s[["new_cap", "country"]].assign(component="Store"), u[["new_cap", "country"]].assign(component="StorageUnit"),
                      l[["new_cap"]].assign(country=l.country0, component="Line")])
    caps.index.name = "name"; caps = caps.reset_index()
    ccb = ccb.merge(caps.rename(columns={"country": "bus_country"}), on=["component", "name"], how="left")
    keep = [c for c in ("component", "name", "carrier", "country", "bus_country", "cost_row", "discount_rate", "capital_cost", "lifetime_component", "lifetime_row",
                        "extendable", "investment", "fom_pct", "annuity_factor", "scaling_implied", "match_rule", "new_cap") if c in ccb]
    ccb[keep].to_csv(out / "ccb.csv", index=False)
    import shutil
    shutil.copy(f["costs"], out / "costs.csv")
    if f["owen"].exists():
        shutil.copy(f["owen"], out / "owen.csv")
    gasm = (n.meta.get("research_gas_network") or {}).get("production") or {}
    meta = dict(schema=SCHEMA, run_dir=str(run_dir), nc=str(f["nc"]), nc_sha256=key, duals_sha256=sha256(f["duals"]), prices_sha256=sha256(f["prices"]),
                objective=float(n.objective), objective_constant=float(getattr(n, "objective_constant", float("nan")) or float("nan")), snapshots=T,
                weight_sum=float(w.sum()), weight_first=float(w[0]), run=json.loads(Path(f["run"]).read_text()) if Path(f["run"]).exists() else {},
                ship_cost_basis=str((n.meta.get("research_liquids") or {}).get("ship_cost_basis")),
                ev=dict((n.meta.get("research_ev") or {}).items()) if isinstance(n.meta.get("research_ev"), dict) else {},
                gas_production={c: dict(cap_mwh=v.get("cap_mwh"), shares=v.get("shares")) for c, v in gasm.items() if isinstance(v, dict)},
                price_check_vs_NODAL_PRICES=price_check, scalars=scal, extracted_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    (out / "meta.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    (out / "DONE").write_text(key + "\n")
    ds.close()
    return out


class X:
    """Loaded extract of one solved run."""

    def __init__(self, d: Path):
        self.dir = d
        rd = lambda name, **kw: pd.read_csv(d / name, **kw)
        self.g = rd("generators.csv", index_col=0); self.k = rd("links.csv", index_col=0, low_memory=False); self.s = rd("stores.csv", index_col=0)
        self.u = rd("storage_units.csv", index_col=0); self.l = rd("lines.csv", index_col=0); self.ld = rd("loads.csv", index_col=0)
        self.b = rd("buses.csv", index_col=0); self.ccb = rd("ccb.csv", low_memory=False); self.costs = rd("costs.csv", index_col=0)
        self.owen = rd("owen.csv") if (d / "owen.csv").exists() else None
        self.enom_upper = rd("stores_enom_upper.csv", index_col=0).mu_enom_upper if (d / "stores_enom_upper.csv").exists() else pd.Series(dtype=float)   # D2a 4.1
        self.meta = json.loads((d / "meta.json").read_text())
        self.sc = self.meta["scalars"]
        for df in (self.g, self.k, self.s, self.u, self.ld):
            if "country" in df:
                df["country"] = df["country"].fillna("").astype(str)
        self.k["route_km"] = pd.to_numeric(self.k.get("route_km"), errors="coerce")
        self.l.index = self.l.index.astype(str)


# ------------------------------------------------------------------------------------------------------------------------------
# 2. first-order mechanisms
# ------------------------------------------------------------------------------------------------------------------------------
def fnum(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def by_country(values: pd.Series, countries: pd.Series) -> dict:
    out = {}
    for c, v in zip(countries.fillna("").astype(str), values.astype(float)):
        if v == 0 or not math.isfinite(v):
            continue
        key = c if c in COUNTRIES else ("BUNKER" if "bunker" in c.lower() else "SHARED")
        out[key] = out.get(key, 0.0) + float(v)
    return out


def addc(*ds):
    out = {}
    for d in ds:
        for k_, v in d.items():
            out[k_] = out.get(k_, 0.0) + v
    return out


def sel(df, carrier=None, country=None, name_regex=None):
    m = pd.Series(True, index=df.index)
    if carrier is not None:
        m &= df["carrier"].isin(carrier if isinstance(carrier, list) else [carrier])
    if country:
        m &= df["country"] == country
    if name_regex:
        m &= df.index.to_series().astype(str).str.contains(name_regex, regex=True)
    return df[m]


class Ctx:
    def __init__(self, reg: pd.DataFrame, repo: Path):
        self.reg = reg
        self.repo = repo
        self.rv = lambda pid: fnum(reg.loc[pid, "value"]) if pid in reg.index else None
        self.typhoon = pd.read_csv(repo / "research_inputs/renewable_v5/TYPHOON_EXPOSURE_BY_NODE.csv")
        self.wacc = pd.read_csv(repo / "research_inputs/finance_v5/COUNTRY_WACC_REAL_M08A.csv").set_index("country").wacc_real.astype(float).to_dict()
        import yaml
        cfg = yaml.safe_load((repo / "configs/research/baseline.yaml").read_text())
        sh = ((cfg.get("research") or {}).get("s3") or {}).get("shipping") or {}
        self.ship_oil_eff = float(sh.get("shipping_oil_efficiency", 0.40)); self.ship_meoh_eff = float(sh.get("shipping_methanol_efficiency", 0.46))
        self.uniform_rate = float(((cfg.get("research") or {}).get("finance") or {}).get("uniform_discount_rate", 0.07))


def oil_final_bus_lam(x: X, node: str, bunker: bool) -> float:
    """Mean price of an oil final-energy bus at the node: bunker meter (aviation international) or a country meter (other sectors)."""
    b = x.b
    cands = b.index[(b.carrier == "oil final energy") & b.index.str.startswith(node + " ")]
    if bunker:
        pick = [c for c in cands if "international" in c]
    else:
        pick = [c for c in cands if "international" not in c]
    if not pick:
        pick = list(cands)
    return float(b.loc[pick, "lam_mean"].mean()) if pick else float("nan")


def evaluate(row: pd.Series, x: X, ctx: Ctx) -> dict:
    """{'low': (dZ, by_country), 'high': (dZ, by_country), 'flags': [...], 'basis': str}"""
    mech = json.loads(row["mech_json"])
    kind = mech["mech"]
    v = fnum(mech.get("value_in_network", row["value"]))
    nl, nh = fnum(row["notch_low"]), fnum(row["notch_high"])
    flags = []
    res = {}

    def deltas():
        return [("low", nl), ("high", nh)]

    if kind in NOT_RANKED:
        return dict(low=(0.0, {}), high=(0.0, {}), flags=([f"discrete"] if kind == "discrete" else []), basis=mech.get("reason", kind), indicator=indicator(mech, row, x, ctx), bias=MECH_CLASS.get(kind, "none"))
    if kind == "store_mc":
        st = sel(x.s, name_regex=mech["name_regex"])
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            d = nv - v; dz = st.discharge * d
            res[lab] = (float(dz.sum()), by_country(dz, st.country))
            for _, r in st.iterrows():
                ex = r.e_initial > 0 and r.e_end / r.e_initial < TOL_EXHAUSTED
                if ex and d > 0 and (not math.isfinite(r.rent) or d > r.rent):
                    flags.append("bound_switch: cost rise above the scarcity rent of an exhausted pool")
                if (not ex) and d < 0 and r.e_end > 0:
                    flags.append("bound_switch: cost cut on a pool with unused potential (use may rise)")
        basis = f"discharge {st.discharge.sum():.4g} MWh x dcost"
    elif kind in ("store_pot", "store_pot_scale"):
        st = sel(x.s, name_regex=mech["name_regex"])
        for lab, nv in deltas():
            if nv is None or v is None or v == 0:
                res[lab] = (0.0, {}); continue
            if kind == "store_pot":
                dpot = pd.Series(nv - v, index=st.index)
            else:
                dpot = st.e_initial * mech["share"] * (nv / v - 1.0)
            ex = (st.e_initial > 0) & (st.e_end / st.e_initial.where(st.e_initial > 0, 1.0) < TOL_EXHAUSTED)
            rent = st.rent.fillna(0.0).clip(lower=0.0)
            dz = -rent.where(ex, 0.0) * dpot
            res[lab] = (float(dz.sum()), by_country(dz, st.country))
            if ((~ex) & (dpot < -st.e_end)).any():
                flags.append("bound_switch: cut exceeds the unused potential (pool would become binding)")
            if (ex & (rent < 1e-6) & (st.marginal_cost <= 0)).any():
                flags.append("degenerate: exhausted zero-cost pool with zero rent")
        basis = f"pools {len(st)}, exhausted {int(((st.e_initial > 0) & (st.e_end / st.e_initial.where(st.e_initial > 0, 1) < TOL_EXHAUSTED)).sum())}, rent {st.rent.max():.4g} EUR/MWh max"
    elif kind == "new_store_bus_value":
        lamb = float(x.b.lam_mean.get(mech["bus"], 0.0))
        for lab, nv in deltas():
            d = (nv or 0.0) - (v or 0.0)
            dz = -max(lamb, 0.0) * d
            res[lab] = (dz, {"LA": dz} if dz else {})
        flags.append("new_resource: value = mean bus price (resource not in the network)")
        basis = f"mean price of {mech['bus']} {lamb:.4g} EUR/MWh"
    elif kind in ("store_cc", "store_cc_factor"):
        st = sel(x.s, carrier=mech["carrier"])
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            if kind == "store_cc":
                dcc = pd.Series((nv - v) * mech.get("scale", 1.0), index=st.index)
            else:
                dcc = st.capital_cost * (nv / v - 1.0)
            dz = st.new_cap * dcc
            parts = [(dz, st.country)]
            if kind == "store_cc_factor" and mech.get("extra"):
                se = sel(x.s, carrier=mech["extra"]["carrier"]); dze = se.new_cap * mech["extra"]["base_part"] * (nv / v - 1.0); parts.append((dze, se.country))
                if ((se.new_cap < TOL_BUILT) & (se.rc_per_unit.fillna(np.inf) < (mech["extra"]["base_part"] * abs(nv / v - 1.0)))).any():
                    flags.append("would_enter: unbuilt sink within the cost change")
            res[lab] = (float(sum(p_.sum() for p_, _ in parts)), addc(*[by_country(p_, c_) for p_, c_ in parts]))
            unb = st[(st.new_cap < TOL_BUILT)]
            if len(unb) and (unb.rc_per_unit.fillna(np.inf) < dcc.reindex(unb.index).abs()).any() and (dcc < 0).any():
                flags.append("would_enter: unbuilt store within the cost cut")
        basis = f"new capacity {st.new_cap.sum():.4g} x dcc"
    elif kind == "scalar_rhs":
        dual_g = float(x.sc.get(mech["constraint"], 0.0)); sc = mech.get("scale", 1.0)
        stn = mech.get("store")
        dual_s = float(x.enom_upper.get(stn, 0.0)) if stn else 0.0   # D2a 4.1 (decision 219): the same limit as the Store e_nom upper bound; the barrier dual sits there
        dual = dual_g + dual_s
        for lab, nv in deltas():
            d = 0.0 if (nv is None or v is None) else (nv - v) * sc
            dz = dual * d
            res[lab] = (dz, {mech["constraint"].rsplit("-", 1)[-1]: dz} if dz else {})
        if stn and stn in x.s.index:
            r = x.s.loc[stn]
            cap = (v or 0.0) * sc
            if cap > 0 and r.e_nom_opt >= cap * (1 - 1e-6) and abs(dual) < 1e-9:
                flags.append("degenerate: injection cap binding with zero dual (zero slack)")
            if abs(dual_s) > 1e-9:
                flags.append(f"duplicate_bound: dual read as global row {dual_g:.4g} + Store e_nom bound {dual_s:.4g} EUR/t (D2a 4.1)")
        basis = f"dual {dual:.4g} EUR/t (global row {dual_g:.4g} + store e_nom bound {dual_s:.4g})"
    elif kind == "lao_rail":
        unit, loading = ctx.rv("co2_land_transport_rail_unit_cost"), ctx.rv("co2_land_transport_rail_loading_cost")
        kk = x.k[x.k.index.str.contains(r"^LA2 \d+ co2 transit", regex=True)]
        lt = x.k[x.k.carrier == "liquid transit rail"]
        for lab, nv in deltas():
            if nv is None:
                res[lab] = (0.0, {}); continue
            dmc = []
            for nm in kk.index:
                node = re.match(r"^(LA2 \d+)", nm).group(1).replace(" ", "_")
                land = ctx.rv(f"co2_lao_transit_land_cost_{node}") or 0.0
                km = (land - loading) / unit if unit else 0.0
                dmc.append((nv - unit) * km if mech["role"] == "unit" else (nv - loading))
            dz1 = kk.flow0_pos * pd.Series(dmc, index=kk.index)
            dmc2 = []
            for nm, r in lt.iterrows():
                key = "ammonia" if "ammonia" in nm else ("methanol" if "methanol" in nm else "oil")
                m_t = ctx.rv(f"liquid_ship_mwh_per_t_{key}")
                km = r.route_km if math.isfinite(r.route_km) else 0.0
                dmc2.append(((nv - unit) * km if mech["role"] == "unit" else (nv - loading)) / m_t)
            dz2 = lt.flow0_pos * pd.Series(dmc2, index=lt.index)
            res[lab] = (float(dz1.sum() + dz2.sum()), addc(by_country(dz1, kk.country), by_country(dz2, lt.country)))
        basis = f"LA CO2 transit {kk.flow0_pos.sum():.4g} t, liquid transit {lt.flow0_pos.sum():.4g} MWh"
    elif kind == "link_mc":
        kk = x.k
        if "carrier" in mech:
            kk = kk[kk.carrier.isin(mech["carrier"])]
        if "name_regex" in mech:
            kk = kk[kk.index.str.contains(mech["name_regex"], regex=True)]
        if mech.get("transit_carrier_match"):
            key = mech["transit_carrier_match"]
            keep = (kk.carrier != "liquid transit rail") | kk.index.str.contains(" oil " if key == "oil" else f" {key} ")
            kk = kk[keep]
        fixed, ckm = ctx.rv("co2_ship_chain_fixed_cost"), ctx.rv("co2_ship_chain_per_km_cost")
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            fm = mech["formula"]
            if fm == "const":
                dmc = pd.Series(nv - v, index=kk.index)
            elif fm == "route_km":
                dmc = (nv - v) * kk.route_km.fillna(0.0)
            elif fm in ("co2_per_km", "co2_route_factor"):
                land = pd.Series([ctx.rv("co2_lao_transit_land_cost_" + re.match(r"^(LA2 \d+)", nm).group(1).replace(" ", "_")) or 0.0 if nm.startswith("LA2 ") and "transit" in nm else 0.0
                                  for nm in kk.index], index=kk.index)
                shippart = (kk.marginal_cost - fixed - land).clip(lower=0.0)
                dmc = shippart / ckm * (nv - v) if fm == "co2_per_km" else shippart * (nv / v - 1.0)
            elif fm == "inverse_rel":
                dmc = kk.marginal_cost * (v / nv - 1.0)
                if mech.get("transit_carrier_match") and x.meta.get("ship_cost_basis") != "ieaghg":
                    # mc of the ship links in this run is the S-B cost; the heating value acts on the S-A main cost (decision 187)
                    key = mech["transit_carrier_match"]
                    sa = (ctx.rv(f"liquid_ship_fixed_ieaghg_{key}") or 0.0) + (ctx.rv(f"liquid_ship_ckm_ieaghg_{key}") or 0.0) * kk.route_km.fillna(0.0)
                    dmc = dmc.where(kk.carrier == "liquid transit rail", sa * (v / nv - 1.0))
            else:
                raise ValueError(fm)
            dz = kk.flow0_pos * dmc
            res[lab] = (float(dz.sum()), by_country(dz, kk.country))
        if mech.get("basis") and x.meta.get("ship_cost_basis") and mech["basis"] != x.meta.get("ship_cost_basis"):
            flags.append(f"basis_inactive_in_run: row basis {mech['basis']}, run basis {x.meta.get('ship_cost_basis')} (flows of this run used)")
        basis = f"links {len(kk)}, flow {kk.flow0_pos.sum():.4g}"
    elif kind == "link_eff_km":
        kk = x.k[x.k.carrier.isin(mech["carrier"])]
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            deta = -(nv - v) * kk.route_km.fillna(0.0)
            dz = -kk.v1 * deta
            res[lab] = (float(dz.sum()), by_country(dz, kk.country))
        if x.meta.get("ship_cost_basis") != mech.get("basis"):
            flags.append(f"basis_inactive_in_run: row basis {mech.get('basis')}, run basis {x.meta.get('ship_cost_basis')}")
        basis = f"output value {kk.v1.sum():.4g} EUR"
    elif kind == "link_eff":
        kk = x.k[x.k.carrier.isin(mech["carrier"])]
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            dz = -kk[f"v{mech.get('port', 1)}"] * (nv - v)
            res[lab] = (float(dz.sum()), by_country(dz, kk.country))
        basis = f"sum(price x flow) at port {mech.get('port', 1)} {kk['v' + str(mech.get('port', 1))].sum():.4g} EUR"
    elif kind == "link_pnom_fixed":
        kk = x.k[x.k.carrier.isin(mech["carrier"]) & (~x.k.ext.astype(bool))]
        if mech.get("bus1_prefix"):
            kk = kk[kk.bus1.astype(str).str.startswith(mech["bus1_prefix"])]
        for lab, nv in deltas():
            if nv is None:
                res[lab] = (0.0, {}); continue
            rel = nv if mech.get("relative_notch") else (nv / v - 1.0 if v else 0.0)
            dz = -kk.avail_value_per_mw * kk.p_nom * rel
            res[lab] = (float(dz.sum()), by_country(dz, kk.country))
        basis = f"capacity value {(kk.avail_value_per_mw * kk.p_nom).sum():.4g} EUR per +100 %"
    elif kind in ("store_enom_fixed", "store_floor", "ev_fleet"):
        st = x.s[x.s.carrier.isin(["EV battery"])]
        ch = x.k[x.k.carrier == "BEV charger"]
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            if kind == "store_enom_fixed":
                dz = st.d_enom_fixed * st.e_nom * (nv / v - 1.0); res[lab] = (float(dz.sum()), by_country(dz, st.country))
            elif kind == "store_floor":   # e >= e_nom x v at the restriction snapshots: dZ/dv = sum(dual_lower) x e_nom
                dz = st.floor_value * (nv - v); res[lab] = (float(dz.sum()), by_country(dz, st.country))
            else:
                rel = (nv / v) ** mech.get("exponent", -1.0) - 1.0
                dz1 = st.d_enom_fixed * st.e_nom * rel; dz2 = -ch.avail_value_per_mw * ch.p_nom * rel
                res[lab] = (float(dz1.sum() + dz2.sum()), addc(by_country(dz1, st.country), by_country(dz2, ch.country)))
        basis = f"EV stores {len(st)}, d e_nom sum {(st.d_enom_fixed * st.e_nom).sum():.4g}, charger value {(ch.avail_value_per_mw * ch.p_nom).sum():.4g}"
    elif kind in ("gen_mc", "gen_mc_rel"):
        gg = x.g[x.g.carrier.isin(mech["carrier"])]
        for lab, nv in deltas():
            if nv is None:
                res[lab] = (0.0, {}); continue
            dmc = gg.marginal_cost * nv if kind == "gen_mc_rel" else pd.Series(nv - (v or 0.0), index=gg.index)
            dz = gg.energy * dmc
            res[lab] = (float(dz.sum()), by_country(dz, gg.country))
            unb = gg[(gg.energy < TOL_BUILT)]
            if len(unb):
                lamb = x.b.lam_mean.reindex(unb.bus).fillna(0.0).to_numpy()
                gap = unb.marginal_cost.to_numpy() - lamb
                if (gap < dmc.reindex(unb.index).abs().to_numpy()).any() and (dmc < 0).any():
                    flags.append("would_enter: unused supply whose cost gap to the bus price is below the cut")
        basis = f"energy {gg.energy.sum():.4g} MWh"
    elif kind in ("gen_cc", "gen_cc_part", "aeo8_factor"):
        if kind == "aeo8_factor":
            c_ = x.ccb[x.ccb.cost_row.isin(mech["rows"])]
            names = set(c_.name)
            gg = x.g[x.g.index.isin(names)]
        else:
            gg = x.g[x.g.carrier.isin(mech["carrier"]) & x.g.ext.astype(bool)]
        cc = x.ccb.set_index("name")
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            if kind == "gen_cc":
                dcc = pd.Series(nv - v, index=gg.index)
            elif kind == "aeo8_factor":
                dcc = gg.capital_cost * (nv / v - 1.0)
            elif mech["part"] == "investment":
                dcc = gg.capital_cost * (nv / v - 1.0)
            else:
                a_ = cc.reindex(gg.index)
                inv_eff = gg.capital_cost / (pd.to_numeric(a_.annuity_factor, errors="coerce") + pd.to_numeric(a_.fom_pct, errors="coerce") / 100.0)
                dcc = inv_eff * (nv - v) / 100.0
            dz = gg.new_cap * dcc
            res[lab] = (float(dz.sum()), by_country(dz, gg.country))
            unb = gg[gg.new_cap < TOL_BUILT]
            if len(unb) and (dcc < 0).any() and (unb.rc_per_mw < dcc.reindex(unb.index).abs()).any():
                flags.append("would_enter: unbuilt candidate within the cost cut")
        basis = f"new capacity {gg.new_cap.sum():.4g} MW, min rc of unbuilt {gg.loc[gg.new_cap < TOL_BUILT, 'rc_per_mw'].min() if (gg.new_cap < TOL_BUILT).any() else float('nan'):.4g} EUR/MW/a"
    elif kind == "gen_pnom_max":
        gg = x.g[x.g.carrier.isin(mech["carrier"]) & x.g.ext.astype(bool)]
        if mech.get("country"):
            gg = gg[gg.country == mech["country"]]
        for lab, nv in deltas():
            if nv is None or v is None or v == 0:
                res[lab] = (0.0, {}); continue
            dcap = gg.p_nom_max * (nv / v - 1.0)
            dz = -gg.mu_pnom_upper * dcap
            res[lab] = (float(dz.sum()), by_country(dz, gg.country))
            if ((gg.mu_pnom_upper < 1e-9) & (gg.p_nom_max + dcap < gg.p_nom_opt - 1e-6)).any():
                flags.append("bound_switch: cap cut below the optimal capacity of a non-binding candidate")
        basis = f"binding caps {(gg.mu_pnom_upper > 1e-9).sum()}/{len(gg)}, mu x cap {(gg.mu_pnom_upper * gg.p_nom_max).sum():.4g}"
    elif kind == "su_pnom_max":
        uu = x.u[x.u.carrier.isin(mech["carrier"]) & x.u.ext.astype(bool)]
        if mech.get("country"):
            uu = uu[uu.country == mech["country"]]
        for lab, nv in deltas():
            if nv is None or v is None or v == 0:
                res[lab] = (0.0, {}); continue
            dcap = uu.p_nom_max * (nv / v - 1.0)
            dz = -uu.mu_pnom_upper * dcap
            res[lab] = (float(dz.sum()), by_country(dz, uu.country))
            if ((uu.mu_pnom_upper < 1e-9) & (uu.p_nom_max + dcap < uu.p_nom_opt - 1e-6)).any():
                flags.append("bound_switch: cap cut below the optimal capacity of a non-binding candidate")
        basis = f"binding caps {(uu.mu_pnom_upper > 1e-9).sum()}/{len(uu)}, built {uu.new_cap.sum():.4g} MW"
    elif kind == "gen_cf":
        gg = x.g[x.g.carrier.isin(mech["carrier"])]
        if mech.get("country"):
            gg = gg[gg.country == mech["country"]]
        for lab, nv in deltas():
            if nv is None or (v is None and not mech.get("relative_notch")):
                res[lab] = (0.0, {}); continue
            rel = mech["eps"] * (nv if mech.get("relative_notch") else (nv / v - 1.0))
            dz = -gg.cf_value * rel
            res[lab] = (float(dz.sum()), by_country(dz, gg.country))
            if abs(rel) > 0.2:
                flags.append(f"large_change: |dCF/CF| = {abs(rel):.0%} (elasticity extrapolated)")
            unb = gg[gg.ext.astype(bool) & (gg.new_cap < TOL_BUILT)]
            if rel > 0 and len(unb) and (unb.rc_per_mw < unb.avail_value_per_mw * rel).any():
                flags.append("would_enter: unbuilt wind candidate becomes profitable within the CF change")
        basis = f"cf value {gg.cf_value.sum():.4g} EUR, built {gg.p_nom_opt.sum():.4g} MW"
    elif kind == "new_capacity_rc":
        gpool = x.g[x.g.carrier.isin(mech["carrier"]) & x.g.ext.astype(bool)]
        upool = x.u[x.u.carrier.isin(mech["carrier"]) & x.u.ext.astype(bool)]
        if mech.get("country"):
            gpool, upool = gpool[gpool.country == mech["country"]], upool[upool.country == mech["country"]]
        pool = pd.concat([gpool[["country", "p_nom_max", "mu_pnom_upper", "rc_per_mw", "capital_cost", "new_cap"]], upool[["country", "p_nom_max", "mu_pnom_upper", "capital_cost", "new_cap"]]])
        binding = pool[pool.mu_pnom_upper > 1e-9]
        val = float((binding.mu_pnom_upper * binding.p_nom_max).sum() / binding.p_nom_max.sum()) if len(binding) and binding.p_nom_max.sum() > 0 else 0.0
        cty = mech.get("country") or "SHARED"
        for lab, nv in deltas():
            d = (nv or 0.0) - (v or 0.0)
            dz = -val * d if len(pool) else 0.0
            res[lab] = (dz, {cty: dz} if dz else {})
        if not len(pool):
            flags.append("not_representable: no candidate of this carrier in the country (DATA_PENDING -> p_nom_max 0); needs a candidate build and a solve")
        else:
            rc = gpool.rc_per_mw[gpool.new_cap < TOL_BUILT]
            if len(rc) and float((rc / gpool.capital_cost.reindex(rc.index)).min()) < 0.05:
                flags.append("would_enter: unbuilt candidates of this carrier within 5 % of entry (knife edge)")
            if not len(binding):
                flags.append("no_binding_candidate: existing candidates not at their cap; added potential has no first-order value")
        basis = f"candidates {len(pool)} (binding {len(binding)}), capacity-weighted cap dual {val:.4g} EUR/MW/a"
    elif kind == "line_existing":
        ll = x.l[x.l.index.isin(mech["names"])]
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            d = nv - v
            dzdx = np.where(ll.ext.astype(bool), -ll.capital_cost + ll.dual_snom_lower + ll.dual_snom_upper, -ll.congestion_value_per_mw)
            dz = pd.Series(dzdx * d, index=ll.index)
            half = dz / 2.0
            res[lab] = (float(dz.sum()), addc(by_country(half, ll.country0), by_country(half, ll.country1)))
            if ll.ext.astype(bool).any() and ((ll.s_nom_opt < ll.s_nom + max(d, 0.0)) & ll.ext.astype(bool)).any():
                flags.append("bound_switch: stock above the optimal capacity (lower bound would bind)")
        basis = "; ".join(f"{i}: ext {bool(r.ext)}, s_nom {r.s_nom:.4g}, opt {r.s_nom_opt:.4g}, cc {r.capital_cost:.4g}, cong {r.congestion_value_per_mw:.4g}" for i, r in ll.iterrows())
    elif kind == "line_length_cc":
        ll = x.l[x.l.index.isin(mech["names"]) & x.l.ext.astype(bool)]
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            dz = ll.new_cap * ll.capital_cost * (nv / v - 1.0)
            half = dz / 2.0
            res[lab] = (float(dz.sum()), addc(by_country(half, ll.country0), by_country(half, ll.country1)))
        basis = f"new capacity {ll.new_cap.sum():.4g} MW"
    elif kind == "wacc_mode":
        c_ = x.ccb.copy()
        c_["new_cap"] = pd.to_numeric(c_.new_cap, errors="coerce").fillna(0.0)
        c_ = c_[(c_.new_cap > 0) & (pd.to_numeric(c_.discount_rate, errors="coerce").round(6) == round(ctx.uniform_rate, 6))]
        life = pd.to_numeric(c_.lifetime_row, errors="coerce").fillna(pd.to_numeric(c_.lifetime_component, errors="coerce"))
        a0 = pd.to_numeric(c_.annuity_factor, errors="coerce"); fom = pd.to_numeric(c_.fom_pct, errors="coerce").fillna(0.0) / 100.0
        cty = c_.bus_country.fillna(c_.country).fillna("").astype(str)
        lines = x.l
        r_new = []
        for (comp, nm, cy) in zip(c_.component, c_.name, cty):
            if comp == "Line" and nm in lines.index:
                a, b = lines.at[nm, "country0"], lines.at[nm, "country1"]
                r_new.append(0.5 * (ctx.wacc.get(a, ctx.uniform_rate) + ctx.wacc.get(b, ctx.uniform_rate)))
            elif comp == "Link" and nm in x.k.index and x.k.at[nm, "country"] != x.k.at[nm, "country1"] and x.k.at[nm, "country1"] in COUNTRIES:
                r_new.append(0.5 * (ctx.wacc.get(x.k.at[nm, "country"], ctx.uniform_rate) + ctx.wacc.get(x.k.at[nm, "country1"], ctx.uniform_rate)))
            else:
                r_new.append(ctx.wacc.get(cy, ctx.uniform_rate))
        a1 = pd.Series([af(r, L_) for r, L_ in zip(r_new, life)], index=c_.index)
        ratio = ((a1 + fom) / (a0 + fom)).replace([np.inf, -np.inf], np.nan).fillna(1.0)
        dz = c_.new_cap * pd.to_numeric(c_.capital_cost, errors="coerce").fillna(0.0) * (ratio - 1.0)
        res["low"] = (0.0, {}); res["high"] = (float(dz.sum()), by_country(dz, cty))
        flags.append("discrete_alternative: country-specific WACC changes every annuity at once (first order = fixed capacities)")
        basis = f"components {len(c_)}, new capex {(c_.new_cap * pd.to_numeric(c_.capital_cost, errors='coerce')).sum():.4g} EUR/a"
    elif kind == "typhoon":
        t = ctx.typhoon[ctx.typhoon[mech.get("threshold_col", "flag_ge_1")].astype(str).str.lower() == "true"]
        pairs = set(zip(t.node.astype(str), t.tech.astype(str)))
        gg = x.g[x.g.carrier.isin(["onwind", "offwind-ac", "offwind-dc", "offwind-float"]) & x.g.ext.astype(bool)]
        node = gg.index.to_series().str.replace(r" (onwind|offwind-ac|offwind-dc|offwind-float).*$", "", regex=True)
        tech = gg.carrier.replace({"offwind-float": "offwind-dc"})
        exp = pd.Series([(a, b) in pairs for a, b in zip(node, tech)], index=gg.index)
        ge = gg[exp]
        for lab, nv in deltas():
            if nv is None:
                res[lab] = (0.0, {}); continue
            dz = ge.new_cap * ge.capital_cost * (nv - (v or 0.0)) / 100.0
            res[lab] = (float(dz.sum()), by_country(dz, ge.country))
        if (ge.new_cap > TOL_BUILT).any():
            flags.append("bound_switch: built exposed wind may be replaced (first order = fixed capacity)")
        basis = f"exposed node-techs {len(ge)}, built {ge.new_cap.sum():.4g} MW"
    elif kind == "gas_alloc":
        c = mech["country"]; gm = (x.meta.get("gas_production") or {}).get(c) or {}
        cap = float(gm.get("cap_mwh") or 0.0); sh = gm.get("shares") or {}
        el = x.ld[(x.ld.carrier == "electricity") & (x.ld.country == c)]
        if cap <= 0 or not len(el):
            res["low"] = res["high"] = (0.0, {}); basis = "no production cap"
        else:
            alt = (el.groupby(el.bus.astype(str)).energy.sum() / el.energy.sum()).to_dict()
            nodes = sorted(set(alt) | set(sh))
            val = {}
            for nd in nodes:
                dname = f"ResearchImportAnnual-{nd} gas production"
                if dname in x.sc:
                    val[nd] = abs(x.sc[dname])
                else:
                    gp = x.g[(x.g.carrier == "gas production")]
                    mc = float(gp.marginal_cost.median()) if len(gp) else 0.0
                    val[nd] = max(float(x.b.lam_mean.get(f"{nd} gas", 0.0)) - mc, 0.0)
                    flags.append("proxy: node without a wellhead, value = mean gas price - production cost")
            dz = -sum(cap * (alt.get(nd, 0.0) - sh.get(nd, 0.0)) * val[nd] for nd in nodes)
            res["low"] = (0.0, {}); res["high"] = (dz, {c: dz} if dz else {})
            basis = f"cap {cap:.4g} MWh, nodes {len(nodes)}"
        flags.append("discrete_alternative: allocation rule switch (gem_fields -> load_shares)")
    elif kind in ("transport_shift", "shipping_shift", "agri_shift", "ev_load_scale"):
        res, basis = route_shift(kind, mech, row, x, ctx, nl, nh, v, flags)
    elif kind == "hb_eff":
        kk = x.k[x.k.carrier == "Haber-Bosch"]
        h, e_, m = ctx.rv("share_MWh_H2_per_tNH3_electrolysis"), ctx.rv("share_MWh_elec_per_tNH3_electrolysis"), ctx.rv("share_MWh_NH3_per_tNH3")
        port_el = port_of(kk, -e_ / h)
        for lab, nv in deltas():
            if nv is None:
                res[lab] = (0.0, {}); continue
            if mech["what"] == "h2":
                d1, d_el = m / nv - m / h, -e_ / nv + e_ / h
            elif mech["what"] == "el":
                d1, d_el = 0.0, -(nv - e_) / h
            else:
                d1, d_el = (nv - m) / h, 0.0
            dz = -(kk.v1 * d1 + (kk[f"v{port_el}"] * d_el if port_el else 0.0))
            res[lab] = (float(dz.sum()), by_country(dz, kk.country))
        basis = f"HB flow {kk.flow0_pos.sum():.4g} MWh_H2, electricity port bus{port_el}"
    elif kind == "meoh_eff":
        kk = x.k[x.k.carrier == "methanolisation"]
        a, b, c = ctx.rv("share_MWh_MeOH_per_MWh_H2"), ctx.rv("share_MWh_MeOH_per_tCO2"), ctx.rv("share_MWh_MeOH_per_MWh_e")
        pe, pc = port_of(kk, -a / c), port_of(kk, -a / b)
        for lab, nv in deltas():
            if nv is None:
                res[lab] = (0.0, {}); continue
            a1, b1, c1 = (nv, b, c) if mech["what"] == "h2" else ((a, nv, c) if mech["what"] == "co2" else (a, b, nv))
            d1, de, dc = a1 - a, -a1 / c1 + a / c, -a1 / b1 + a / b
            dz = -(kk.v1 * d1 + (kk[f"v{pe}"] * de if pe else 0.0) + (kk[f"v{pc}"] * dc if pc else 0.0))
            if mech["what"] == "h2":
                dz = dz + kk.new_cap * kk.capital_cost * (a1 / a - 1.0)
            res[lab] = (float(dz.sum()), by_country(dz, kk.country))
        basis = f"methanolisation flow {kk.flow0_pos.sum():.4g} MWh_H2, ports el bus{pe}, co2 bus{pc}"
    elif kind == "unbuilt_check":
        gg = x.g[x.g.carrier.isin(mech["carrier"]) & x.g.ext.astype(bool)]
        built = gg.new_cap.sum()
        rcmin = float(gg.rc_per_mw.min()) if len(gg) else float("nan")
        for lab, nv in deltas():
            if nv is None or v is None:
                res[lab] = (0.0, {}); continue
            if mech["what"] == "efficiency":
                dcost = (gg.marginal_cost * (v / nv - 1.0) * gg.cf_hours).min()
            else:
                life0 = v; dcost = (gg.capital_cost * (af(ctx.uniform_rate, nv) / af(ctx.uniform_rate, life0) - 1.0)).min()
            dz = float((gg.new_cap * 0).sum())
            if built > TOL_BUILT:
                dz = float((gg.new_cap * (gg.marginal_cost * (v / nv - 1.0) * gg.cf_hours if mech["what"] == "efficiency" else gg.capital_cost * (af(ctx.uniform_rate, nv) / af(ctx.uniform_rate, v) - 1.0))).sum())
            res[lab] = (dz, {})
            if built <= TOL_BUILT and math.isfinite(rcmin) and dcost < 0 and -dcost > rcmin:
                flags.append("would_enter: unbuilt candidate becomes profitable within the change")
        basis = f"built {built:.4g} MW, min rc {rcmin:.4g} EUR/MW/a"
    elif kind == "fixed_emission_scale":
        gg = x.g[x.g.carrier.isin(mech["carrier"]) & (x.g.country == mech["country"])]
        dual = abs(float(x.sc.get(f"research_country_co2_limit-{mech['country']}", 0.0)))
        for lab, nv in deltas():
            if nv is None or v is None or v == 0:
                res[lab] = (0.0, {}); continue
            dz = dual * gg.energy.sum() * (nv / v - 1.0)
            res[lab] = (float(dz), {mech["country"]: float(dz)} if dz else {})
        flags.append("upper_bound: all plastic-burning CO2 of the country assumed proportional to the share")
        basis = f"plastic CO2 {gg.energy.sum():.4g} t, CO2 dual {dual:.4g} EUR/t"
    else:
        raise ValueError(f"unknown mechanism {kind} ({row['param_id']})")
    for lab in ("low", "high"):
        res.setdefault(lab, (0.0, {}))
    if kind in ("store_pot", "store_pot_scale", "gen_pnom_max", "su_pnom_max", "scalar_rhs", "link_pnom_fixed", "store_enom_fixed", "ev_fleet", "line_existing") and v:
        rels = [abs((nv_ - v) / v) for nv_ in (nl, nh) if nv_ is not None] if not mech.get("relative_notch") else [abs(nv_) for nv_ in (nl, nh) if nv_ is not None]
        if kind == "store_pot_scale":
            rels = [r_ * mech.get("share", 1.0) for r_ in rels]
        if rels and max(rels) >= 0.5 and (abs(res["low"][0]) + abs(res["high"][0])) > 0:
            flags.append(f"large_change: notch {max(rels):.0%} of the value on a binding bound (first order ignores the falling marginal value)")
    return dict(low=res["low"], high=res["high"], flags=sorted(set(flags)), basis=basis, indicator="", bias=MECH_CLASS.get(kind, "coefficient"))


def port_of(kk: pd.DataFrame, target: float):
    for j in (2, 3, 4):
        col = f"efficiency{j}"
        if col in kk and len(kk) and np.isclose(pd.to_numeric(kk[col], errors="coerce").median(), target, rtol=0.02):
            return j
    return None


def route_shift(kind, mech, row, x: X, ctx: Ctx, nl, nh, v, flags):
    res = {}
    ice, el_eff, fc = ctx.rv("share_transport_ice_efficiency"), ctx.rv("share_transport_electric_efficiency"), ctx.rv("share_transport_fuel_cell_efficiency")
    oil_to_el = ice / el_eff; oil_to_h2 = ice / fc
    ev = x.ld[x.ld.carrier == "land transport EV"]
    st = x.s[x.s.carrier == "EV battery"]; ch = x.k[x.k.carrier == "BEV charger"]
    node_of = lambda b: str(b).rsplit(" EV battery", 1)[0]
    fleet_val = lambda rel: (st.d_enom_fixed * st.e_nom * rel, -ch.avail_value_per_mw * ch.p_nom * rel)

    def h2_lam(node):
        return float(x.b.lam_mean.get(f"{node} H2", float("nan")))

    for lab, nv in (("low", nl), ("high", nh)):
        if nv is None:
            res[lab] = (0.0, {}); continue
        if kind == "transport_shift":
            s_ = abs(nv)
            if s_ == 0:
                res[lab] = (0.0, {}); continue
            dz_ev = -s_ * ev.value
            e_oil = s_ * ev.energy / oil_to_el
            if mech["to"] == "oil":
                lamt = pd.Series([oil_final_bus_lam(x, node_of(b), bunker=False) for b in ev.bus], index=ev.index)
                dz_t = e_oil * lamt
            else:
                lamt = pd.Series([h2_lam(node_of(b)) for b in ev.bus], index=ev.index)
                dz_t = e_oil * oil_to_h2 * lamt
            f1, f2 = fleet_val(-s_)
            dz = dz_ev + dz_t.fillna(0.0)
            res[lab] = (float(dz.sum() + f1.sum() + f2.sum()), addc(by_country(dz, ev.country), by_country(f1, st.country), by_country(f2, ch.country)))
            if s_ >= 0.2:
                flags.append(f"large_change: {s_:.0%} of land transport moved between carriers (prices held fixed)")
        elif kind == "shipping_shift":
            s_ = abs(nv)
            if s_ == 0:
                res[lab] = (0.0, {}); continue
            sh = x.ld[x.ld.carrier == "shipping methanol"]
            conv_m = ctx.ship_oil_eff / ctx.ship_meoh_eff
            nodes = [str(b).rsplit(" shipping methanol final", 1)[0] for b in sh.bus]
            intl = sh.index.to_series().str.contains("international").to_numpy()
            dz_m = -s_ * sh.value
            e_oil = s_ * sh.energy / conv_m
            if mech["to"] == "oil":
                lamt = pd.Series([oil_final_bus_lam(x, nd, bunker=bool(i)) for nd, i in zip(nodes, intl)], index=sh.index)
                dz_t = e_oil * lamt
            else:
                fce = float(pd.to_numeric(x.costs.loc["fuel cell", "efficiency"], errors="coerce")) if "fuel cell" in x.costs.index else 0.5
                lamt = pd.Series([h2_lam(nd) for nd in nodes], index=sh.index)
                dz_t = e_oil * ctx.ship_oil_eff / fce * lamt
            dz = dz_m + dz_t.fillna(0.0)
            cty = pd.Series(np.where(intl, "BUNKER", sh.country), index=sh.index)
            res[lab] = (float(dz.sum()), by_country(dz, cty))
            if s_ >= 0.2:
                flags.append(f"large_change: {s_:.0%} of shipping moved between carriers (prices held fixed)")
        elif kind == "agri_shift":
            el = x.ld[x.ld.carrier == "agriculture machinery electric"]
            oil = x.ld[x.ld.bus.astype(str).str.endswith("agriculture oil final")]
            w_ = mech["what"]
            if v is None or v == 0:
                res[lab] = (0.0, {}); continue
            if w_ == "electric_share":
                r_el, r_oil = (nv - v) / v, -(nv - v) / 0.5
            elif w_ == "oil_share":
                r_el, r_oil = -(nv - v) / 0.5, (nv - v) / v
            elif w_ == "fuel_efficiency":
                r_el, r_oil = nv / v - 1.0, 0.0
            else:
                r_el, r_oil = v / nv - 1.0, 0.0
            dz1 = el.value * r_el; dz2 = oil.value * r_oil
            res[lab] = (float(dz1.sum() + dz2.sum()), addc(by_country(dz1, el.country), by_country(dz2, oil.country)))
            flags.append("inference: agriculture machinery shares applied to the whole agriculture oil final load")
        elif kind == "ev_load_scale":
            if v is None or v == 0:
                res[lab] = (0.0, {}); continue
            if mech["what"] == "el_eff":
                rel = v / nv - 1.0
                dz = ev.value * rel
                res[lab] = (float(dz.sum()), by_country(dz, ev.country))
            else:
                rel = nv / v - 1.0
                dz = ev.value * rel; f1, f2 = fleet_val(rel)
                res[lab] = (float(dz.sum() + f1.sum() + f2.sum()), addc(by_country(dz, ev.country), by_country(f1, st.country), by_country(f2, ch.country)))
    basis = f"EV load {ev.energy.sum():.4g} MWh, value {ev.value.sum():.4g} EUR"
    return res, basis


def indicator(mech, row, x: X, ctx: Ctx) -> str:
    ind = mech.get("indicator")
    if ind == "co2_dual_times_range":
        c = mech.get("country"); dual = abs(float(x.sc.get(f"research_country_co2_limit-{c}", 0.0)))
        lo, hi = fnum(row["sensitivity_low"]), fnum(row["sensitivity_high"])
        if lo is not None and hi is not None:
            return f"|CO2 dual {c}| x |high - low| = {dual * abs(hi - lo):.4g} EUR"
    if ind == "lng_new_capacity":
        gg = x.g[x.g.carrier == "LNG import"]
        return f"new LNG terminal capacity {gg.new_cap.sum():.4g} MW, annuity {(gg.new_cap * gg.capital_cost).sum():.4g} EUR/a"
    if ind == "unbuilt_rc":
        gg = x.g[x.g.carrier.isin(mech.get("carrier", [])) & x.g.ext.astype(bool)]
        if len(gg):
            return f"built {gg.new_cap.sum():.4g} MW; min reduced cost / capital cost {float((gg.rc_per_mw / gg.capital_cost).min()):.3f}"
    if ind == "solar_cap_binding":
        gg = x.g[(x.g.carrier == "solar") & x.g.ext.astype(bool)]
        return f"binding solar caps {(gg.mu_pnom_upper > 1e-9).sum()}/{len(gg)}, sum(mu x cap) {(gg.mu_pnom_upper * gg.p_nom_max).sum():.4g} EUR per +100 %"
    return ""


# ------------------------------------------------------------------------------------------------------------------------------
# 3. ranking and tables
# ------------------------------------------------------------------------------------------------------------------------------
def evaluate_set(inv: pd.DataFrame, x1: X, x2: X, ctx: Ctx, label: str) -> pd.DataFrame:
    rows = []
    for _, r in inv.iterrows():
        e1 = evaluate(r, x1, ctx); e2 = evaluate(r, x2, ctx)
        best = None
        for lab in ("low", "high"):
            z1, c1 = e1[lab]; z2, c2 = e2[lab]
            db6 = z2 - z1
            cand = dict(direction=lab, dZ_F1=z1, dZ_F2=z2, dB6=db6, owen=c1)
            if best is None or abs(db6) > abs(best["dB6"]) + 1e-9 or (abs(db6) == abs(best["dB6"]) and abs(z1) > abs(best["dZ_F1"])):
                best = cand
        z1l, z2l = e1["low"][0], e2["low"][0]; z1h, z2h = e1["high"][0], e2["high"][0]
        oc = best["owen"]
        omax = max(oc.items(), key=lambda kv: abs(kv[1])) if oc else ("", 0.0)
        # investment difference between F1 and F2 for capex-type rows
        flags = sorted(set(e1["flags"]) | set(f"F2:{f}" for f in e2["flags"] if f not in e1["flags"]))
        mech = json.loads(r["mech_json"])["mech"]
        if mech in ("gen_cc", "gen_cc_part", "store_cc", "store_cc_factor", "line_length_cc", "aeo8_factor", "wacc_mode", "typhoon") and abs(best["dZ_F1"]) + abs(best["dZ_F2"]) > 0:
            a, b = abs(best["dZ_F1"]), abs(best["dZ_F2"])
            if max(a, b) > 0 and abs(a - b) / max(a, b) > 0.5:
                flags.append("investment_F1_F2_differs: affected new capacity differs by > 50 % between F1 and F2")
        bias = e1.get("bias", "coefficient")
        rows.append(dict(param_id=r["param_id"], set=label, mechanism=mech, bias_class=bias, bias_dZ=BIAS.get(bias, ""), bias_dB6=("indefinite (difference of two one-sided bounds)" if bias in ("cost", "rhs") else BIAS.get(bias, "")),
                         dZ_F1_low=z1l, dZ_F2_low=z2l, dB6_low=z2l - z1l, dZ_F1_high=z1h, dZ_F2_high=z2h,
                         dB6_high=z2h - z1h, direction_max=best["direction"], dZ_F1=best["dZ_F1"], dZ_F2=best["dZ_F2"], dB6=best["dB6"], abs_dB6=abs(best["dB6"]),
                         abs_dZ_max=max(abs(best["dZ_F1"]), abs(best["dZ_F2"])), owen_max_country=omax[0], owen_max_eur=omax[1],
                         owen_by_country=json.dumps({k_: round(v_, 2) for k_, v_ in sorted(oc.items())}), flags=" | ".join(flags),
                         basis_F1=e1["basis"], basis_F2=e2["basis"], indicator_F1=e1.get("indicator", ""), indicator_F2=e2.get("indicator", "")))
    return pd.DataFrame(rows)


def ranked_universe(inv: pd.DataFrame) -> pd.Series:
    mj = inv.mech_json.map(json.loads)
    return (~inv.mechanism.isin(NOT_RANKED)) & (~mj.map(lambda m: bool(m.get("duplicate_of")) or bool(m.get("scenario_choice")))) & (inv.side != "demand")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--set", action="append", required=True, help="label=F1_dir,F2_dir (repeatable)")
    ap.add_argument("--reference", required=True, help="label of the set closest to the 2920x3h runs")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--repo", required=True, help="worktree with research_inputs/ and configs/")
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--registry-ranges", action="store_true", help="D2a 4.4: refresh the notches of the 'registered sensitivity range' rows from the repo registry")
    a = ap.parse_args()
    repo, cache, out = Path(a.repo), Path(a.cache), Path(a.out)
    cache.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    inv = pd.read_csv(a.inventory, dtype=str, keep_default_na=False)
    reg = pd.read_csv(repo / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    if a.registry_ranges:   # D2a 4.4: the branch registry's (physics-corrected) ranges replace the inventory notches of the registered-range rows
        upd = []
        for i, r in inv.iterrows():
            if not str(r.notch_basis).startswith("registered sensitivity range") or r.param_id not in reg.index:
                continue
            lo, hi = reg.at[r.param_id, "sensitivity_low"], reg.at[r.param_id, "sensitivity_high"]
            same = lambda x, y: (fnum(x) is not None and fnum(y) is not None and abs(fnum(x) - fnum(y)) <= 1e-9 * max(1.0, abs(fnum(y))))   # noqa: E731
            if lo != "" and hi != "" and not (same(lo, r.notch_low) and same(hi, r.notch_high)):
                upd.append(dict(param_id=r.param_id, notch_low_w10=r.notch_low, notch_high_w10=r.notch_high, notch_low_d2a=lo, notch_high_d2a=hi, value=r.value, registry_value=reg.at[r.param_id, "value"]))
                inv.at[i, "notch_low"] = lo; inv.at[i, "notch_high"] = hi
                inv.at[i, "notch_basis"] = r.notch_basis + " refreshed from the D2a registry (physics-corrected range)"
        pd.DataFrame(upd).to_csv(out / "INVENTORY_RANGE_UPDATES.csv", index=False, lineterminator="\n")
        inv.to_csv(out / "C_GRADE_INVENTORY_D2A.csv", index=False, lineterminator="\n")
        print(f"[registry-ranges] {len(upd)} notch pairs refreshed", flush=True)
    ctx = Ctx(reg, repo)
    sets, extracts = {}, {}
    for s_ in a.set:
        lab, dirs = s_.split("=", 1)
        d1, d2 = [Path(p) for p in dirs.split(",")]
        sets[lab] = (d1, d2)
        e1 = extract(d1, cache); e2 = extract(d2, cache)
        extracts[lab] = (e1, e2)
        print(f"[extract] {lab}: F1 {e1.name}, F2 {e2.name}", flush=True)
    if a.reference not in sets:
        raise SystemExit("--reference must be one of the set labels")
    frames = []
    for lab, (e1, e2) in extracts.items():
        x1, x2 = X(e1), X(e2)
        df = evaluate_set(inv, x1, x2, ctx, lab)
        df["B6_base"] = x2.meta["objective"] - x1.meta["objective"]
        frames.append(df)
        print(f"[evaluate] {lab}: B6 base {df.B6_base.iloc[0] / 1e9:.4f} bn", flush=True)
    long = pd.concat(frames, ignore_index=True)
    uni = ranked_universe(inv).to_numpy()
    univ_ids = set(inv.param_id[uni])
    long["ranked"] = long.param_id.isin(univ_ids)
    # D2a 4.2 (decision 219): S-B shipping rows whose cost basis is not the run's basis leave the ranking (their first order is evaluated on S-A flows)
    inactive = sorted(set(long.param_id[(long.set == a.reference) & long["flags"].str.contains("basis_inactive_in_run")]))
    long.loc[long.param_id.isin(inactive), "ranked"] = False
    pd.DataFrame(dict(param_id=inactive, reason="basis_inactive_in_run: S-B shipping parameter (td_tanker basis); the reference runs use the S-A ieaghg basis, so the row's quantity is not active in the LP (decision 219)")).to_csv(out / "INACTIVE_BASIS_ROWS.csv", index=False, lineterminator="\n")
    print(f"[inactive-basis] {len(inactive)} rows left the ranking: {inactive}", flush=True)
    # D2a 4.1: every scalar research cap duplicated by a Store e_nom upper bound in the reference run, reported
    x1 = X(extracts[a.reference][0]); dup = []
    for cname, dual in x1.sc.items():   # the limit duplicated by a Store e_nom bound with the SAME right-hand side: the national CO2 storage cap (W15 7.5); the national
        if not cname.startswith("research_co2_storage_cap-"):   # CO2 limit rows (research_country_co2_limit-*) carry their own non-zero duals and are not duplicates
            continue
        cc = cname.rsplit("-", 1)[-1]; stn = f"co2 sequestered {cc}"
        if stn in x1.enom_upper.index:
            dup.append(dict(constraint=cname, store=stn, dual_global_row=float(dual), dual_store_e_nom_upper=float(x1.enom_upper.get(stn, 0.0)), dual_total=float(dual) + float(x1.enom_upper.get(stn, 0.0)),
                            degenerate_duplicate=bool(abs(float(dual)) < 1e-9 and abs(float(x1.enom_upper.get(stn, 0.0))) > 1e-9), country=cc, run=a.reference))
    pd.DataFrame(dup).to_csv(out / "DUPLICATE_BOUNDS.csv", index=False, lineterminator="\n")
    print(f"[duplicate-bounds] {len(dup)} cap rows with a Store e_nom bound dual in the reference run", flush=True)
    for lab in sets:
        m = (long.set == lab) & long.ranked
        long.loc[m, "rank"] = long.loc[m, "abs_dB6"].rank(ascending=False, method="first")
    wide = inv.set_index("param_id")[["family_201", "side", "value", "unit", "country", "status", "notch_low", "notch_high", "notch_basis", "mechanism", "active_in_main"]].copy()
    ref = long[long.set == a.reference].set_index("param_id")
    for c in ("bias_class", "bias_dZ", "bias_dB6", "direction_max", "dZ_F1", "dZ_F2", "dB6", "abs_dB6", "abs_dZ_max", "owen_max_country", "owen_max_eur", "owen_by_country", "dZ_F1_low", "dZ_F2_low", "dB6_low",
              "dZ_F1_high", "dZ_F2_high", "dB6_high", "flags", "basis_F1", "basis_F2", "indicator_F1", "indicator_F2", "rank", "ranked"):
        wide[c] = ref[c]
    for lab in sets:
        if lab == a.reference:
            continue
        o = long[long.set == lab].set_index("param_id")
        wide[f"dB6_{lab}"] = o["dB6"]; wide[f"rank_{lab}"] = o["rank"]; wide[f"flags_{lab}"] = o["flags"]
    wide = wide.reset_index().sort_values(["ranked", "abs_dB6"], ascending=[False, False])
    # stability
    stab = {}
    refr = wide[wide.ranked].set_index("param_id")["rank"]
    for lab in sets:
        if lab == a.reference:
            continue
        o = wide[wide.ranked].set_index("param_id")[f"rank_{lab}"]
        stab[lab] = dict(spearman=float(refr.corr(o, method="spearman")), top_overlap=int(len(set(refr[refr <= a.top].index) & set(o[o <= a.top].index))),
                         top=a.top, moved_out=sorted(set(refr[refr <= a.top].index) - set(o[o <= a.top].index)))
        unstable = (refr <= a.top) & (o > 2 * a.top) | (o <= a.top) & (refr > 2 * a.top)
        wide.loc[wide.param_id.isin(unstable[unstable].index), "flags"] = wide.loc[wide.param_id.isin(unstable[unstable].index), "flags"].fillna("") + f" | rank_unstable_vs_{lab}"
    wide.to_csv(out / "IMPACT_FIRST_ORDER.csv", index=False, lineterminator="\n")
    long.to_csv(out / "IMPACT_FIRST_ORDER_BY_SET.csv", index=False, lineterminator="\n")
    top = wide[wide.ranked].head(a.top)
    top.to_csv(out / "TOP30.csv", index=False, lineterminator="\n")
    unrel_flags = ("bound_switch", "would_enter", "investment_F1_F2_differs", "degenerate", "large_change", "discrete", "rank_unstable", "new_resource", "upper_bound", "proxy",
                   "not_representable")
    scen = inv.param_id[inv.mech_json.map(lambda s: bool(json.loads(s).get("scenario_choice")))]
    wide.loc[wide.param_id.isin(scen), "flags"] = wide.loc[wide.param_id.isin(scen), "flags"].fillna("") + " | scenario_choice: regime-changing registered range, not ranked"
    unrel = wide[wide["flags"].fillna("").str.contains("|".join(unrel_flags + ("scenario_choice",))) | wide.mechanism.isin(["discrete"])].copy()
    unrel["reason"] = unrel["flags"].fillna("").str.replace(r"basis_inactive_in_run[^|]*\|?", "", regex=True)
    unrel.to_csv(out / "UNRELIABLE_FIRST_ORDER.csv", index=False, lineterminator="\n")
    summ = dict(schema=SCHEMA + "+d2a", generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), reference=a.reference, d2a=dict(inactive_basis_rows=inactive, duplicate_bound_rows=len(dup), registry_ranges=bool(a.registry_ranges)),
                sets={lab: dict(F1=str(d1), F2=str(d2), F1_extract=extracts[lab][0].name, F2_extract=extracts[lab][1].name) for lab, (d1, d2) in sets.items()},
                inventory_sha256=sha256(a.inventory), registry_sha256=sha256(repo / "research_inputs/registry_v5/DATA_REGISTRY.csv"),
                ranked_rows=int(wide.ranked.sum()), unreliable_rows=int(len(unrel)), stability=stab,
                b6_base={lab: float(long[long.set == lab].B6_base.iloc[0]) for lab in sets}, solver_calls=0, network_builds=0)
    (out / "RERANK_SUMMARY.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps({k_: summ[k_] for k_ in ("reference", "ranked_rows", "unreliable_rows", "stability", "b6_base")}, indent=1))


if __name__ == "__main__":
    main()
