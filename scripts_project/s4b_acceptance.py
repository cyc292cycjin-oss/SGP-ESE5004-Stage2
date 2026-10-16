"""S4B-0 (decision 71, option 1): acceptance budgets tied to the Gurobi tolerances, with row-activity relative terms.

Design correction made after the S3B results (stated in the S4B report): the S3B R4.4 budgets (scripts_project/v5/v5_gates.gate_a1_a2_interior)
took the primal relative term 1e-7 = 10 x BarConvTol and the dual budget 1e-6 = 100 x BarConvTol, while Gurobi stops a barrier run when the
scaled model is feasible to FeasibilityTol and dual feasible to OptimalityTol (both 1e-6, not set in the profiles); and rows whose right-hand
side is 0 (the per-country net-zero rows: final atmosphere level <= 0) had no relative term at all, because their only variable is the final
level (~1e-3 t) although the level is the sum of the year's CO2 flows (1e8-1e9 t). The frozen V4 algebra (v5/kkt_algebra.py) and the V4 physics
checks (validation_dynamics.py) are not changed; the old gates stay in V5_GATES.json for comparison.

New budgets (research.solver.interior; factor k = solver_tol_factor = 10, option 1 "10 x 1e-6"):
  A1/A2 primal  row i:    |violation_i| <= 1e-3 + k x FeasibilityTol x ref_i,  ref_i = max(|finite bounds|, sum_j |a_ij x_j|, A_i)
                column j: |violation_j| <= 1e-3 + k x FeasibilityTol x max(|x_j|, |finite bounds|, A_j)
                A_i = the country's annual gross CO2 flow for the net-zero rows (research_country_co2_limit-*, research_gap_co2_limit-*);
                A_i = A_j = pool capacity e_nom for every Store row of the finite biomass pools (energy balance and the level bounds
                Store-fix-e-lower / -upper) and their level columns; otherwise 0.
  A1/A2 dual    stationarity |c_j - a_j' pi - rc_j| / max(1, |c_j| + |a_j|'|pi| + |rc_j|) <= k x OptimalityTol (V4 normalisation);
                dual sign: rows (multiplier at a nonexistent bound) / max(1, |pi_i|) (V4); columns: the error is the reduced cost of a column
                without that bound (in practice the free Link-p flows, whose rc must be 0, i.e. a dual residual) and is measured on the same
                column dual-activity scale as stationarity. This column scale was chosen after seeing the S3B / S4A values (the V4 form
                error / max(1, |rc|) is absolute for |rc| < 1); the V4 form is reported alongside and the choice is listed for the user.
  A1/A2 gap     relative primal-dual gap and complementarity_l1 / scale <= gap_factor x BarConvTol (unchanged, from the V4 summary).
  A3 / A5       every V4 physics check with 1e-3 + k x FeasibilityTol x |reference| (was 1e-7); COUNTRY_CO2_CAP reference = gross CO2 flow;
                Store energy / state checks of the finite biomass pools reference = max(|value|, pool capacity).
  B1            final atmosphere level <= cap + 1e-3 + k x FeasibilityTol x gross CO2 flow (was 1e-3 + 1e-7 x max(1, |cap|)).
  B3            used <= e_nom x (1 + k x FeasibilityTol) + 1e-3 and min level >= -(1e-3 + k x FeasibilityTol x e_nom) (was 1e-9 relative / 1e-3 absolute).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from carrier_architecture import COUNTRIES, atmosphere_bus

ABS_FLOOR = 1e-3   # V4 physical absolute floor in each equation (native unit), unchanged


def budgets(interior: dict, barconvtol: float) -> dict:
    k = float(interior.get("solver_tol_factor", 10)); ft = float(interior.get("feasibility_tol", 1e-6)); ot = float(interior.get("optimality_tol", 1e-6))
    g = float(interior.get("gap_factor", 10))
    return dict(basis="solver_tolerances", factor=k, feasibility_tol=ft, optimality_tol=ot, primal_relative=k * ft, dual_normalized=k * ot, absolute_floor=ABS_FLOOR,
                gap=g * barconvtol, barconvtol=barconvtol, decision="71 (option 1)", column_dual_sign_scale=str(interior.get("column_dual_sign_scale", "stationarity_scale")))


def country_gross_co2_flows(n) -> dict:
    """Annual gross CO2 throughput of each national atmosphere (t): sum over every atmosphere port of sum_t w_t |flow_t|."""
    from country_carbon import emission_registry
    w = n.snapshot_weightings.stores
    out = {c: 0.0 for c in sorted(COUNTRIES)}
    for r in emission_registry(n):
        flow = n.links_t["p" + r["port"][3:]][r["component"]]
        out[r["country"]] += float((flow.abs() * w).sum())
    return out


def pool_capacities(n) -> dict:
    if "research_role" not in n.stores:
        return {}
    s = n.stores[n.stores.research_role == "FINITE_RESOURCE"]
    return {str(k): float(v) for k, v in s.e_nom.items()}


# ------------------------------------------------------------------ linopy label maps (row / column groups and special references)
def label_groups(m, labels: np.ndarray, kind: str):
    """Array of group names (constraint / variable name) per exported row / column, from the linopy labels."""
    store = m.constraints if kind == "row" else m.variables
    top = int(labels.max()) + 1 if len(labels) else 0
    gid = np.full(top, -1, dtype=np.int64); names = []
    for i, name in enumerate(store):
        lab = np.asarray(store[name].labels).ravel(); lab = lab[(lab >= 0) & (lab < top)]
        gid[lab] = i; names.append(name)
    idx = gid[labels]
    return np.array([names[i] if i >= 0 else "?" for i in idx], dtype=object)


def special_references(m, n, row_labels: np.ndarray, col_labels: np.ndarray, gross: dict, pools: dict):
    """Row / column references A_i, A_j (decision 71): net-zero rows -> gross CO2 flow; biomass-pool energy balances and levels -> e_nom."""
    row_ref = np.zeros(len(row_labels)); col_ref = np.zeros(len(col_labels))
    rpos = {int(l): i for i, l in enumerate(row_labels)}; cpos = {int(l): i for i, l in enumerate(col_labels)}
    tagged = dict(net_zero_rows={}, pool_rows=0, pool_cols=0)
    for c in sorted(COUNTRIES):
        for name in (f"research_country_co2_limit-{c}", f"research_gap_co2_limit-{c}"):
            if name in m.constraints:
                for l in np.asarray(m.constraints[name].labels).ravel():
                    if int(l) in rpos:
                        row_ref[rpos[int(l)]] = max(row_ref[rpos[int(l)]], gross.get(c, 0.0)); tagged["net_zero_rows"][name] = gross.get(c, 0.0)
    if pools:
        # every Store row of a pool: energy balance and the level bounds of fixed stores (Store-fix-e-lower / -upper), whatever the store dimension name
        for cname in [c for c in m.constraints if str(c).startswith("Store-")]:
            lab = m.constraints[cname].labels
            dims = [d for d in lab.dims if str(d).startswith("Store")]
            if not dims:
                continue
            d = dims[0]; present = set(map(str, lab.coords[d].values)); hit = 0
            for s, cap in pools.items():
                if s in present:
                    for l in np.asarray(lab.sel({d: s})).ravel():
                        if int(l) in rpos:
                            row_ref[rpos[int(l)]] = max(row_ref[rpos[int(l)]], cap); tagged["pool_rows"] += 1; hit += 1
            if hit:
                tagged.setdefault("pool_row_groups", {})[str(cname)] = hit
        if "Store-e" in m.variables:
            lab = m.variables["Store-e"].labels
            for s, cap in pools.items():
                if s in lab.coords["Store"].values:
                    for l in np.asarray(lab.sel(Store=s)).ravel():
                        if int(l) in cpos:
                            col_ref[cpos[int(l)]] = max(col_ref[cpos[int(l)]], cap); tagged["pool_cols"] += 1
    return row_ref, col_ref, tagged


# ------------------------------------------------------------------ A1 / A2
def gate_a1_a2_solver_tol(lp_dir, sol_dir, B: dict, row_ref=None, col_ref=None, row_group=None, col_group=None, kkt_summary=None, top=12):
    import scipy.sparse as sp
    lp_dir, sol_dir = Path(lp_dir), Path(sol_dir); meta = json.loads((lp_dir / "MATH_PROBLEM.json").read_text())
    a = {k: np.load(lp_dir / (k + ".npy")) for k in ["cost", "col_lower", "col_upper", "row_lower", "row_upper", "start", "index", "value"]}
    x, pi, rc = [np.load(sol_dir / (k + ".npy")) for k in ["X", "Pi", "RC"]]
    nc, nr = meta["num_col"], meta["num_row"]
    A = sp.csc_matrix((a["value"], a["index"], a["start"]), shape=(nr, nc))
    absA = abs(A)
    act = A @ x; mag = absA @ np.abs(x)
    lo, hi = a["row_lower"], a["row_upper"]; lf, uf = np.isfinite(lo), np.isfinite(hi)
    rv = np.zeros(nr); rv[lf] = np.maximum(lo[lf] - act[lf], 0); rv[uf] = np.maximum(rv[uf], act[uf] - hi[uf])
    rref = np.maximum.reduce([np.where(lf, np.abs(lo), 0.0), np.where(uf, np.abs(hi), 0.0), mag, (row_ref if row_ref is not None else np.zeros(nr))])
    rtol = ABS_FLOOR + B["primal_relative"] * rref
    cl, cu = a["col_lower"], a["col_upper"]; clf, cuf = np.isfinite(cl), np.isfinite(cu)
    cv = np.zeros(nc); cv[clf] = np.maximum(cl[clf] - x[clf], 0); cv[cuf] = np.maximum(cv[cuf], x[cuf] - cu[cuf])
    cref = np.maximum.reduce([np.abs(x), np.where(clf, np.abs(cl), 0.0), np.where(cuf, np.abs(cu), 0.0), (col_ref if col_ref is not None else np.zeros(nc))])
    ctol = ABS_FLOOR + B["primal_relative"] * cref
    aty = A.T @ pi; absaty = absA.T @ np.abs(pi)
    resid = a["cost"] - aty - rc; scale = np.maximum(1.0, np.abs(a["cost"]) + absaty + np.abs(rc)); stat = np.abs(resid) / scale
    cs = np.where(~clf, np.maximum(rc, 0), 0) + np.where(~cuf, np.maximum(-rc, 0), 0)
    cs_v4 = cs / np.maximum(1.0, np.abs(rc))   # V4 normalisation (absolute for |rc| < 1)
    # a column dual-sign error is a reduced cost where the column has no bound (free Link-p flows: rc must be 0), i.e. a dual residual; it is
    # measured on the column's dual activity like the stationarity residual (V4 scale max(1, |c| + |a|'|pi| + |rc|)); decision 71 relative term
    cs_n = cs / scale if B.get("column_dual_sign_scale", "stationarity_scale") == "stationarity_scale" else cs_v4
    rs =np.where(~lf, np.maximum(pi, 0), 0) + np.where(~uf, np.maximum(-pi, 0), 0); rs_n = rs / np.maximum(1.0, np.abs(pi))
    dt = B["dual_normalized"]
    out = dict(gate="A1_A2_SOLVER_TOLERANCES", budgets=B, row_fail_count=int((rv > rtol).sum()), column_fail_count=int((cv > ctol).sum()),
               row_violation_max=float(rv.max(initial=0)), column_violation_max=float(cv.max(initial=0)),
               row_max_ratio_to_budget=float((rv / rtol).max(initial=0)), column_max_ratio_to_budget=float((cv / ctol).max(initial=0)),
               stationarity_normalized_max=float(stat.max(initial=0)), stationarity_fail_count=int((stat > dt).sum()),
               dual_sign_normalized_max=float(max(cs_n.max(initial=0), rs_n.max(initial=0))), dual_sign_fail_count=int((cs_n > dt).sum() + (rs_n > dt).sum()),
               dual_sign_fail_columns=int((cs_n > dt).sum()), dual_sign_fail_rows=int((rs_n > dt).sum()),
               dual_sign_v4_normalisation=dict(columns_max=float(cs_v4.max(initial=0)), columns_fail=int((cs_v4 > dt).sum()), note="V4 error / max(1, |rc|), reported for comparison"))
    # ratios at k = 1 (FeasibilityTol / OptimalityTol themselves) for the reader
    rtol1 = ABS_FLOOR + B["feasibility_tol"] * rref; ctol1 = ABS_FLOOR + B["feasibility_tol"] * cref
    out["at_factor_1"] = dict(row_fail_count=int((rv > rtol1).sum()), column_fail_count=int((cv > ctol1).sum()), stationarity_fail_count=int((stat > B["optimality_tol"]).sum()),
                              dual_sign_fail_count=int((cs_n > B["optimality_tol"]).sum() + (rs_n > B["optimality_tol"]).sum()))

    def worst(viol, tol, grp, k):
        if not len(viol):
            return []
        r = viol / tol; idx = np.argsort(-r)[:k]
        return [dict(index=int(i), group=(str(grp[i]) if grp is not None else None), violation=float(viol[i]), budget=float(tol[i]), ratio=float(r[i])) for i in idx if r[i] > 0]
    out["worst_rows"] = worst(rv, rtol, row_group, top); out["worst_columns"] = worst(cv, ctol, col_group, top)
    sidx = np.argsort(-stat)[:top]; out["worst_stationarity"] = [dict(index=int(i), group=(str(col_group[i]) if col_group is not None else None), normalized=float(stat[i])) for i in sidx if stat[i] > 0]
    out["worst_dual_sign_rows"] = [dict(index=int(i), group=(str(row_group[i]) if row_group is not None else None), normalized=float(rs_n[i]), multiplier=float(pi[i])) for i in np.argsort(-rs_n)[:top] if rs_n[i] > 0]
    out["worst_dual_sign_columns"] = [dict(index=int(i), group=(str(col_group[i]) if col_group is not None else None), normalized=float(cs_n[i]), reduced_cost=float(rc[i])) for i in np.argsort(-cs_n)[:top] if cs_n[i] > 0]
    if row_group is not None:
        fails = pd.Series(row_group[rv > rtol]).value_counts().to_dict(); out["row_fails_by_group"] = {str(k): int(v) for k, v in fails.items()}
        out["dual_sign_row_fails_by_group"] = {str(k): int(v) for k, v in pd.Series(row_group[rs_n > dt]).value_counts().head(20).to_dict().items()}
    if col_group is not None:
        out["column_fails_by_group"] = {str(k): int(v) for k, v in pd.Series(col_group[cv > ctol]).value_counts().to_dict().items()}
        out["stationarity_fails_by_group"] = {str(k): int(v) for k, v in pd.Series(col_group[stat > dt]).value_counts().head(20).to_dict().items()}
        out["dual_sign_column_fails_by_group"] = {str(k): int(v) for k, v in pd.Series(col_group[cs_n > dt]).value_counts().head(20).to_dict().items()}
    k = kkt_summary or {}
    sc = max(1.0, abs(float(k.get("primal_objective", 0.0))), abs(float(k.get("dual_objective_numeric", 0.0))))
    gap = float(k.get("relative_gap", float("nan"))); comp = float(k.get("complementarity_l1", float("nan"))) / sc
    crit = dict(primal_rows_within_budget=out["row_fail_count"] == 0, primal_columns_within_budget=out["column_fail_count"] == 0,
                dual_stationarity=out["stationarity_fail_count"] == 0, dual_sign=out["dual_sign_fail_count"] == 0,
                relative_gap=bool(gap <= B["gap"]), complementarity=bool(comp <= B["gap"]))
    out.update(criteria=crit, relative_gap=gap, complementarity_over_scale=comp, passed=bool(all(crit.values())), scale=dict(num_col=nc, num_row=nr, nnz=int(A.nnz)))
    return out


# ------------------------------------------------------------------ A3 / A5 (V4 physics with the new tolerance)
def dynamic_checks_solver_tol(n, rel, gross, pools, extra_known_objective=0.0):
    """validation_dynamics.dynamic_checks with lim = 1e-3 + rel x |reference| (decision 71) and the gross-flow / pool-capacity references."""
    rows = []; weights = n.snapshot_weightings; h = weights.stores

    def check(name, residual, scale=1., unit="MW"):
        a_ = np.asarray(residual, dtype=float); s = np.asarray(scale, dtype=float)
        finite = bool(np.isfinite(a_).all()); maximum = float(np.max(np.abs(a_))) if a_.size else 0.
        lim = ABS_FLOOR + rel * np.abs(s)
        ok = finite and bool(np.all(np.abs(a_) <= lim))
        ratio = float(np.max(np.abs(a_) / lim)) if a_.size else 0.0
        rows.append(dict(Check=name, Status="PASS" if ok else "FAIL", MaxAbsoluteResidual=maximum, MaxRatioToBudget=ratio, Unit=unit, Tolerance=f"1e-3 + {rel:g}*abs(reference)"))

    def dense(c, attr):
        return n.get_switchable_as_dense(c, attr)
    balance = pd.DataFrame(0., index=n.snapshots, columns=n.buses.index); magnitude = balance.copy()
    for typ in ["Generator", "Load", "Store", "StorageUnit"]:
        df = n.df(typ); p = n.pnl(typ).p.reindex(columns=df.index) * df.sign
        for bus, ids in df.groupby("bus").groups.items():
            balance[bus] += p[ids].sum(axis=1); magnitude[bus] += p[ids].abs().sum(axis=1)
    for typ in ["Link", "Line", "Transformer"]:
        df = n.df(typ)
        for col in [x for x in df if x.startswith("bus") and x[3:].isdigit()]:
            port = "p" + col[3:]; p = n.pnl(typ)[port]
            for bus, ids in df[df[col] != ""].groupby(col).groups.items():
                balance[bus] -= p[ids].sum(axis=1); magnitude[bus] += p[ids].abs().sum(axis=1)
    check("BUS_BALANCES", balance, magnitude)
    check("ALL_FIXED_DEMANDS", n.loads_t.p - dense("Load", "p_set"), dense("Load", "p_set"))
    for col in [x for x in n.links if x.startswith("bus") and x[3:].isdigit() and x != "bus0"]:
        ids = n.links.index[n.links[col] != ""]; suffix = col[3:]; eff = "efficiency" + ("" if suffix == "1" else suffix)
        check("LINK_MULTIPORT_" + suffix, n.links_t["p" + suffix][ids] + n.links_t.p0[ids] * dense("Link", eff)[ids], n.links_t.p0[ids])
    pool_cols = [s for s in pools if s in n.stores.index]
    for typ, state, initial, cyclic in [("Store", "e", "e_initial", "e_cyclic"), ("StorageUnit", "state_of_charge", "state_of_charge_initial", "cyclic_state_of_charge")]:
        df = n.df(typ); ts = n.pnl(typ); end = ts[state].reindex(columns=df.index); prev = end.shift(1)
        prev.iloc[0] = np.where(df[cyclic], end.iloc[-1], df[initial])
        decay = (1 - dense(typ, "standing_loss")).pow(h, axis=0)
        if typ == "Store":
            rhs = prev * decay - ts.p.mul(h, axis=0)
        else:
            rhs = prev * decay + (ts.p_store * dense(typ, "efficiency_store") - ts.p_dispatch / dense(typ, "efficiency_dispatch") + dense(typ, "inflow") - ts.spill.reindex(columns=df.index, fill_value=0)).mul(h, axis=0)
        scale = np.maximum(end.abs(), rhs.abs())
        if typ == "Store" and pool_cols:
            for s_ in pool_cols:
                scale[s_] = np.maximum(scale[s_], pools[s_])
        check(typ.upper() + "_STATE_EQUATIONS_CYCLIC_AND_INITIAL", end - rhs, scale, "MWh")
    for typ, nom in [("Generator", "p_nom"), ("Link", "p_nom"), ("Line", "s_nom"), ("StorageUnit", "p_nom"), ("Store", "e_nom")]:
        df = n.df(typ); cap = df[nom + "_opt"]; ext = df[nom + "_extendable"]
        check(typ + "_NOMINAL_LOWER", np.minimum(cap[ext] - df.loc[ext, nom + "_min"], 0), cap[ext])
        fin = df[nom + "_max"].replace(np.inf, np.nan).notna() & ext
        check(typ + "_NOMINAL_UPPER", np.maximum(cap[fin] - df.loc[fin, nom + "_max"], 0), cap[fin])
        check(typ + "_FIXED_CAPACITY", cap[~ext] - df.loc[~ext, nom], df.loc[~ext, nom])
        if typ in ["Generator", "Link"]:
            flow = n.pnl(typ)["p" if typ == "Generator" else "p0"]
            check(typ + "_DISPATCH_UPPER", np.maximum(flow - dense(typ, "p_max_pu") * cap, 0), flow)
            check(typ + "_DISPATCH_LOWER", np.minimum(flow - dense(typ, "p_min_pu") * cap, 0), flow)
        elif typ == "Line":
            check("TRANSMISSION_THERMAL_BOUNDS", np.maximum(n.lines_t.p0.abs() - dense("Line", "s_max_pu") * cap, 0), n.lines_t.p0)
        elif typ == "Store":
            sc = n.stores_t.e.abs()
            for s_ in pool_cols:
                sc[s_] = np.maximum(sc[s_], pools[s_])
            check("STORE_ENERGY_UPPER", np.maximum(n.stores_t.e - dense(typ, "e_max_pu") * cap, 0), sc, "MWh")
            check("STORE_ENERGY_LOWER", np.minimum(n.stores_t.e - dense(typ, "e_min_pu") * cap, 0), sc, "MWh")
        else:
            check("STORAGE_UNIT_ENERGY_UPPER", np.maximum(n.storage_units_t.state_of_charge - cap * df.max_hours, 0), n.storage_units_t.state_of_charge, "MWh")
            check("STORAGE_UNIT_ENERGY_LOWER", np.minimum(n.storage_units_t.state_of_charge, 0), n.storage_units_t.state_of_charge, "MWh")
            check("STORAGE_UNIT_CHARGE_BOUND", np.maximum(n.storage_units_t.p_store + cap * dense(typ, "p_min_pu"), 0), n.storage_units_t.p_store)
            check("STORAGE_UNIT_DISCHARGE_BOUND", np.maximum(n.storage_units_t.p_dispatch - cap * dense(typ, "p_max_pu"), 0), n.storage_units_t.p_dispatch)
    for name, rule in n.meta.get("store_power_rules", {}).items():
        v = n.stores_t.p[name]; check("DIRECTION:" + name, np.minimum(v, 0) if rule == "discharge_only" else np.maximum(v, 0), v)
    for pair in n.meta.get("battery_inverter_pairs", []):
        a_, b_ = pair["charger"], pair["discharger"]; check("BATTERY_CAPACITY:" + a_, n.links.at[a_, "p_nom_opt"] - n.links.at[b_, "p_nom_opt"] * n.links.at[b_, "efficiency"], n.links.at[a_, "p_nom_opt"])
    for key, g in n.meta.get("existing_resource_groups", {}).items():
        used = sum(n.df(x["ComponentType"]).at[x["Name"], "p_nom_opt"] * x["CapacityToMW"] for x in g["candidates"])
        check("RESOURCE_LIMIT:" + key, max(0., used - g["new_build_limit_mw"]), g["new_build_limit_mw"])
    for name, cap in n.meta.get("external_annual_caps", {}).items():
        check("IMPORT_ANNUAL:" + name, max(0., float(n.generators_t.p[name] @ weights.generators) - cap), cap, "MWh")
    if "lv_limit" in n.global_constraints.index:
        lv = n.global_constraints.loc["lv_limit"]; carriers = lv.carrier_attribute.split(", "); volume = 0.
        for typ, nom in [("Line", "s_nom_opt"), ("Link", "p_nom_opt")]:
            d = n.df(typ); d = d[d.carrier.isin(carriers) & d[nom.replace("_opt", "_extendable")]]; volume += float((d[nom] * d.length).sum())
        check("LV_LIMIT", max(0., volume - float(lv.constant)), float(lv.constant), "MW km")
    carbon = n.meta.get("research_carbon"); levels = None
    if carbon:
        levels = {c: float(n.stores_t.e[atmosphere_bus(c)].iloc[-1]) for c in sorted(COUNTRIES)}
        if carbon["constraint_scope"] == "per_country":
            for c, v in levels.items():
                check("COUNTRY_CO2_CAP:" + c, max(0., v - float(carbon["country_cap_tco2"][c])), max(1., abs(float(carbon["country_cap_tco2"][c])), gross.get(c, 0.0)), "tCO2")
        else:
            check("ASEAN_CO2_CAP", max(0., sum(levels.values()) - float(carbon["asean_total_cap_tco2"])), max(1., abs(float(carbon["asean_total_cap_tco2"])), sum(gross.values())), "tCO2")
    capital = 0.; variable = 0.
    for typ, nom in [("Generator", "p_nom"), ("Link", "p_nom"), ("Line", "s_nom"), ("StorageUnit", "p_nom"), ("Store", "e_nom")]:
        d = n.df(typ); ext = d[nom + "_extendable"]; capital += float(((d.loc[ext, nom + "_opt"] - d.loc[ext, nom]) * d.loc[ext, "capital_cost"]).sum())
    for typ, flow in [("Generator", "p"), ("Link", "p0"), ("Store", "p"), ("StorageUnit", "p_dispatch")]:
        variable += float((n.pnl(typ)[flow] * dense(typ, "marginal_cost")).sum(axis=1) @ weights.objective)
    known = float(n.meta.get("existing_annual_fixed_om_eur", 0.)) + float(n.meta.get("existing_cross_border_fom_eur", 0.)) + float(extra_known_objective); expected = capital + variable + known
    check("OBJECTIVE_RECONCILIATION_KNOWN_FOM_ONCE", float(n.objective) - expected, expected, "EUR2020/year")
    return rows, dict(objective_reconciliation={"capital": capital, "variable": variable, "known_fixed_once": known, "actual": float(n.objective)}, country_co2_levels_tco2=levels)


def gate_a3_a5_solver_tol(n, B, gross, pools, known_terms=None, ignore_checks=()):
    extra = float(sum((known_terms or {}).values()))
    rows, details = dynamic_checks_solver_tol(n, B["primal_relative"], gross, pools, extra_known_objective=extra)
    failed = [r for r in rows if r["Status"] != "PASS" and not any(r["Check"].startswith(p) for p in ignore_checks)]
    diag = [r for r in rows if r["Status"] != "PASS" and any(r["Check"].startswith(p) for p in ignore_checks)]
    fom = next((r for r in rows if r["Check"] == "OBJECTIVE_RECONCILIATION_KNOWN_FOM_ONCE"), None)
    top = sorted(rows, key=lambda r: -r["MaxRatioToBudget"])[:12]
    a3 = dict(gate="A3_PHYSICS_SOLVER_TOLERANCES", passed=not failed, checks=len(rows), failed=[dict(check=r["Check"], residual=r["MaxAbsoluteResidual"], ratio=r["MaxRatioToBudget"]) for r in failed][:20],
              diagnostic_expected_failures=[dict(check=r["Check"], residual=r["MaxAbsoluteResidual"]) for r in diag],
              largest_ratio_checks=[dict(check=r["Check"], residual=r["MaxAbsoluteResidual"], ratio=r["MaxRatioToBudget"], status=r["Status"]) for r in top], budgets=B)
    a5 = dict(gate="A5_FOM_ONCE_SOLVER_TOLERANCES", passed=bool(fom and fom["Status"] == "PASS"), reconciliation=details["objective_reconciliation"], ratio=(fom or {}).get("MaxRatioToBudget"))
    return a3, a5


def gate_b1_solver_tol(n, B, gross):
    from country_carbon import emission_report
    rep = emission_report(n); cfg = n.meta["research_carbon"]; rows = {}; ok = True
    for c in sorted(COUNTRIES):
        cap = float(cfg["country_cap_tco2"][c]); level = rep["store_final_level"][c]
        tol = ABS_FLOOR + B["primal_relative"] * max(1.0, abs(cap), gross.get(c, 0.0))
        within = level <= cap + tol if cfg["constraint_scope"] == "per_country" else True
        rows[c] = dict(final_level_tco2=level, cap_tco2=cap, gross_co2_flow_t=gross.get(c, 0.0), tolerance_t=tol, ratio_to_budget=max(0.0, level - cap) / tol, within_cap=bool(within))
        ok &= bool(within)
    if cfg["constraint_scope"] == "asean_total":
        ok &= rep["asean_total"] <= float(cfg["asean_total_cap_tco2"]) + ABS_FLOOR + B["primal_relative"] * sum(gross.values())
    ok &= bool(rep["every_tonne_booked_once"])
    return dict(gate="B1_COUNTRY_NET_ZERO_SOLVER_TOLERANCES", passed=bool(ok), countries=rows, every_tonne_booked_once=rep["every_tonne_booked_once"], budgets=B)


def gate_b3_solver_tol(n, B):
    rows = []; ok = True; rel = B["primal_relative"]
    if "research_role" in n.stores:
        for name, z in n.stores[n.stores.research_role == "FINITE_RESOURCE"].iterrows():
            e = n.stores_t.e[name]; used = float(z.e_initial - e.iloc[-1]); refill = bool((n.stores_t.p[name] < -1e-6).any())
            cap = float(z.e_nom); over = used - cap * (1 + rel) - ABS_FLOOR; low = float(e.min()) + ABS_FLOOR + rel * cap
            within = over <= 0 and low >= 0
            rows.append(dict(store=name, country=str(z.country), potential_mwh=cap, used_mwh=used, min_level_mwh=float(e.min()), share_used=(used / cap if cap else None),
                             within=bool(within), refilled=refill))
            ok &= bool(within and not refill)
    return dict(gate="B3_BIOMASS_WITHIN_POTENTIAL_SOLVER_TOLERANCES", passed=bool(ok), stores=len(rows), failing=[r for r in rows if not r["within"] or r["refilled"]][:20], budgets=B)


def evaluate(n, lp_dir, sol_dir, out_dir, interior: dict, barconvtol: float, m=None, row_labels=None, col_labels=None, gap=False, known_terms=None):
    """All decision-71 gates for one solved run; returns {A1_A2_S4B, A3_S4B, A5_S4B, B1_S4B, B3_S4B}."""
    B = budgets(interior, barconvtol); gross = country_gross_co2_flows(n); pools = pool_capacities(n)
    lp_dir = Path(lp_dir); rl = row_labels if row_labels is not None else np.load(lp_dir / "clabels.npy"); cl = col_labels if col_labels is not None else np.load(lp_dir / "vlabels.npy")
    row_ref = col_ref = row_group = col_group = None; tagged = None
    if m is not None:
        row_ref, col_ref, tagged = special_references(m, n, rl, cl, gross, pools)
        row_group = label_groups(m, rl, "row"); col_group = label_groups(m, cl, "col")
    ks = Path(out_dir) / "kkt_summary.json"; kkt = json.loads(ks.read_text()) if ks.exists() else {}
    res = {}
    res["A1_A2_S4B"] = gate_a1_a2_solver_tol(lp_dir, sol_dir, B, row_ref, col_ref, row_group, col_group, kkt)
    res["A1_A2_S4B"]["special_references"] = tagged
    a3, a5 = gate_a3_a5_solver_tol(n, B, gross, pools, known_terms=known_terms, ignore_checks=("COUNTRY_CO2_CAP:",) if gap else ())
    res["A3_S4B"] = a3; res["A5_S4B"] = a5
    if not gap:
        res["B1_S4B"] = gate_b1_solver_tol(n, B, gross)
    res["B3_S4B"] = gate_b3_solver_tol(n, B)
    res["country_gross_co2_flow_t"] = gross
    return res


S4B_MAIN_SET = ("A1_A2_S4B", "A3_S4B", "A4", "A5_S4B", "A6", "B1_S4B", "B2", "B3_S4B", "B8", "B11", "B12", "B13", "B14", "B15")
S3B_SET = ("A1_A2", "A3", "A4", "A5", "A6", "B1", "B2", "B3", "B8", "B11", "B12", "B13", "B14", "B15")


def all_passed(gates: dict, basis: str) -> bool:
    keys = S4B_MAIN_SET if basis == "solver_tolerances" else S3B_SET
    return all(gates[k]["passed"] for k in keys if k in gates and isinstance(gates[k], dict) and "passed" in gates[k])
