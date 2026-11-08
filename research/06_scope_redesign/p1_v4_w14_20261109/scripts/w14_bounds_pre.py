"""V4 W14 section 4 (decision 214 item 5; written and committed BEFORE any v4 HPC solve): alarm lines of the change of the objective (incl. the constant term)
of the v4 main 2920x3h networks against the v3.1 2920x3h HPC solves F1 / F2 (work/p1_v3_20261102/hpc_results_v31/unpacked/export/F1, F2: DUALS_BY_CONSTRAINT.nc,
solved networks). The alarm line is a necessary condition ("violated -> something is wrong"), not a pass gate. Nothing is solved.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w14_bounds_pre.py

Change set v3.1 -> v4 (every differing component table / time series of the two unsolved networks, enumerated by this script; anything it cannot classify
is listed under 'unclassified' and makes the line void):
  right-hand side (V(b) convex; the v3.1 duals y are a subgradient: dV_LP >= y'(b_v4 - b_v31); signed raw duals of DUALS_BY_CONSTRAINT.nc, linopy convention
  (<= rows y <= 0, >= rows y >= 0, rows in EUR with the snapshot weight inside):
    loads (static p_set and series; loads present on one side only)          Bus-nodal_balance / Bus-meshed-nodal_balance: rhs = load
    Store e_initial (non-cyclic pools; removed pools -> 0)                     Store-energy_balance at the first snapshot: rhs = -e_initial
    fixed Store e_nom (pools, EV batteries)                                    Store-fix-e-upper / -lower: rhs = e_max_pu * e_nom / e_min_pu * e_nom
    fixed Generator / Link p_nom (process-emission sources, EV chargers,      <comp>-fix-p-upper / -lower: rhs = p_max_pu * p_nom / p_min_pu * p_nom
      ships, transit rail)
    fixed StorageUnit p_nom (TH PHS)                                           p_dispatch-upper (p_max_pu p_nom), p_store-upper (-p_min_pu p_nom), state_of_charge-upper (max_hours p_nom)
    StorageUnit inflow series                                                  StorageUnit-energy_balance: rhs = -elapsed_h * inflow
    annual caps n.meta external_annual_caps (domestic gas production)         ResearchImportAnnual-<generator>: sum_t w p <= cap
  structure (dual extension, so that the extended v3.1 duals stay dual-feasible for the v4 LP; weak duality then keeps the bound):
    new final-energy buses fed only by new meter links (mc_k, eta_1 > 0) from existing buses: y_f(t) = min_k (w_t mc_k + y_bus0(t) - sum_j>=2 eta_j y_bus_j(t)) / eta_1
      (every new link then has a non-negative reduced cost); the loads on them are priced at y_f
    new storage unit (TH2 4 reservoir of D2a, fixed 608.2 MW, zero cost): -min(p_nom * sum_t max(y_bus,0) * p_max_pu, (sum_t eh inflow) * max_t max(y_bus / w, 0))
      (capacity or energy bound of what the unit can be worth at the v3.1 prices; D2a rule)
    removed generators / links / stores (restrictions: the v4 feasible set is the v3.1 one with these variables at 0) -> 0; a removed fixed component with
      p_min_pu > 0 would be a right-hand side change and is listed
    new links between existing buses: reduced cost at the v3.1 duals listed (a negative one would void the extension)
  cost class (V(c) concave): upper bound of the class from the v3.1 solution x: sum dc * w * x (first-order, exact as an upper bound while the feasible set is
    unchanged); lower bound 0 when every dc >= 0 on variables >= 0 (LNG import +0.7907 EUR/MWh, trunk Stores 0 -> 6.267 EUR/MWh: both only rise)
  coefficient class (link efficiencies: gas-delivery fugitive factor efficiency2, methanolisation efficiency3 / 4): first-order estimate only, UNBOUNDED:
    FO = - sum_t d(eta_j) * p0(t) * y_bus_j(t)
  constant term: the exact change of the objective constant (fixed-capacity capital / fixed O&M terms) = constant(v4 receipt) - constant(v3.1 receipt); the
    constant does not depend on the snapshots (checked: v3.1 2920x3h receipt = v3.1 local 56-snapshot receipt), the v4 value is that of the D2c smoke receipt
    (the 56-snapshot networks are identical to the W14 package networks, W14 section 2.3).
Composition (D1 / D2a rule, decision 214 item 5): alarm line dV >= dConst + LB_rhs + LB_structure + LB_cost(0) - tol - 2 |FO_coefficient|; tol = 1e-6 x |V_v31|
(barrier 1e-6). The first-order estimate dConst + LB_rhs + LB_structure + UB_cost + FO is INFERENCE (the convexity excess of large changes is not in it).
Writes evidence/W14_BOUNDS_PRE.json and tables/W14_BOUNDS_PRE.csv.
"""
from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

W = Path(__file__).resolve().parents[1]
E31 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_results_v31/unpacked/export")
PKG31 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks")
B = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/main")
SMOKE31 = Path("/home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31")
SMOKE_D2C = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2c/smoke56")
RUNS = {"F1": ("integrated", "v4d2c_F1"), "F2": ("no_new_xb", "v4d2c_F2")}


def jl(p: Path) -> dict:
    return json.loads(p.read_text())


def const_of(rec: dict) -> float:
    return float(((rec.get("scaling") or {}).get("objective_constants") or {}).get("total_eur") or 0.0)


class Duals:
    """the duals are read variable by variable, each in ONE contiguous read (.values of the whole variable), then indexed in memory: fancy indexing of the
    NetCDF variable itself re-reads chunks over the /mnt/d (9p) mount many times (first attempt: 21 GB read for one run)"""
    def __init__(self, path: Path, snapshots: pd.DatetimeIndex):
        self.D = xr.open_dataset(path); self.sn = snapshots; self._cache = {}

    def full(self, var: str) -> pd.DataFrame:
        if var not in self._cache:
            x = self.D[var]; td = [d for d in x.dims if d.endswith("snapshot")][0]; cd = [d for d in x.dims if not d.endswith("snapshot")][0]
            v = np.asarray(x.values); v = v if x.dims.index(td) == 0 else v.T
            self._cache[var] = pd.DataFrame(v, index=self.sn, columns=[str(c) for c in x[cd].values])
        return self._cache[var]

    def frame(self, var: str, names) -> pd.DataFrame:
        """T x names of a per-snapshot dual (0 where a name has no row)"""
        names = list(names)
        if var not in self.D.data_vars:
            return pd.DataFrame(0.0, index=self.sn, columns=names)
        return self.full(var).reindex(columns=names).fillna(0.0)

    def scalar(self, var: str) -> float | None:
        return float(self.D[var].values) if var in self.D.data_vars else None

    def bus_frame(self) -> pd.DataFrame:
        a = self.full("Bus-nodal_balance"); b = self.full("Bus-meshed-nodal_balance")
        assert not set(a.columns) & set(b.columns)
        return pd.concat([a, b], axis=1)


def solved_ts(S: xr.Dataset, key: str, names, sn) -> pd.DataFrame:
    """time series of the solved v3.1 network (PyPSA NetCDF: <list>_t_<attr> with dims snapshots x <list>_t_<attr>_i), one contiguous read of the variable"""
    names = list(names)
    if key not in S.data_vars or not names:
        return pd.DataFrame(0.0, index=sn, columns=names)
    x = S[key]; cd = [d for d in x.dims if d != "snapshots"][0]
    v = np.asarray(x.transpose("snapshots", cd).values)
    return pd.DataFrame(v, index=sn, columns=[str(c) for c in x[cd].values]).reindex(columns=names).fillna(0.0)


def dense(n: pypsa.Network, comp: str, attr: str, names) -> pd.DataFrame:
    """T x names of a static-or-series attribute (series override the static value)"""
    df = n.df(comp); pnl = n.pnl(comp)
    names = list(names)
    out = pd.DataFrame({k: np.full(len(n.snapshots), float(df.at[k, attr])) for k in names}, index=n.snapshots)
    if attr in pnl and len(pnl[attr].columns):
        cols = [k for k in names if k in pnl[attr].columns]
        if cols:
            out.loc[:, cols] = pnl[attr][cols].to_numpy()
    return out


def changed_rows(A: pd.DataFrame, Bn: pd.DataFrame, col: str) -> list:
    idx = A.index.intersection(Bn.index)
    x, y = pd.to_numeric(A.loc[idx, col], errors="coerce"), pd.to_numeric(Bn.loc[idx, col], errors="coerce")
    m = ~((x == y) | (x.isna() & y.isna()))
    return list(m.index[m])


def changed_series(a: pypsa.Network, b: pypsa.Network, comp: str, attr: str) -> list:
    ta, tb = a.pnl(comp).get(attr, pd.DataFrame()), b.pnl(comp).get(attr, pd.DataFrame())
    common = set(a.df(comp).index) & set(b.df(comp).index)
    cols = sorted((set(ta.columns) | set(tb.columns)) & common)
    return [c for c in cols if c not in ta.columns or c not in tb.columns or not np.array_equal(ta[c].to_numpy(), tb[c].to_numpy(), equal_nan=True)]


HANDLED = {   # (component, column) of the static diff -> class
    ("Load", "p_set"): "rhs", ("Load", "source_account_id"): "label", ("Store", "e_initial"): "rhs", ("Store", "e_nom"): "rhs", ("Store", "marginal_cost"): "cost",
    ("Generator", "marginal_cost"): "cost", ("Generator", "p_nom"): "rhs", ("Link", "p_nom"): "rhs", ("Link", "efficiency"): "coef", ("Link", "efficiency2"): "coef",
    ("Link", "efficiency3"): "coef", ("Link", "efficiency4"): "coef", ("Link", "fugitive_factor_id"): "label", ("StorageUnit", "p_nom"): "rhs",
    ("StorageUnit", "existing_annual_fixed_om_eur"): "constant", ("StorageUnit", "retained_electric_capacity_mw"): "label", ("StorageUnit", "source_group_capacity_mw"): "label",
    ("StorageUnit", "source_unit_id"): "label"}
HANDLED_SERIES = {("Load", "p_set"): "rhs", ("StorageUnit", "inflow"): "rhs"}


def run(rid: str) -> tuple[dict, list]:
    sc, d2c = RUNS[rid]
    a = pypsa.Network(str(PKG31 / f"{sc}_2920_3h_unsolved.nc")); b = pypsa.Network(str(B / sc / f"{sc}_2920_3h_unsolved.nc"))
    E = E31 / rid; solved = sorted(E.glob("*_solved.nc"))[0]
    rec31 = jl(E / "SOLVE_RECEIPT.json"); V31 = float(rec31["objective"])
    sn = a.snapshots; w = a.snapshot_weightings.objective.to_numpy(float); eh = a.snapshot_weightings.stores.to_numpy(float)
    assert a.snapshots.equals(b.snapshots) and a.snapshot_weightings.equals(b.snapshot_weightings)
    Dl = Duals(E / "DUALS_BY_CONSTRAINT.nc", sn); S = xr.open_dataset(solved)
    Y = Dl.bus_frame()   # y_bus (EUR per MW per snapshot, weight inside)
    rows, unclassified, notes = [], [], []

    def add(cls, term, item, country, value, qty=None, unit=None, detail=None):
        rows.append(dict(run=rid, cls=cls, term=term, item=str(item), country=str(country), value_eur=float(value), quantity=qty, unit=unit, detail=detail))

    # ---- enumerate every difference and check that it is handled
    for comp in ("Bus", "Carrier", "Generator", "Link", "Line", "Load", "Store", "StorageUnit"):
        A, Bn = a.df(comp), b.df(comp)
        for col in sorted(set(A.columns) | set(Bn.columns)):
            if col not in A.columns or col not in Bn.columns:
                unclassified.append(f"{comp}.{col}: column only in one network"); continue
            ch = changed_rows(A, Bn, col)
            if ch and (comp, col) not in HANDLED:
                unclassified.append(f"{comp}.{col}: {len(ch)} rows ({ch[:3]})")
        for attr in sorted(set(a.pnl(comp)) | set(b.pnl(comp))):
            ch = changed_series(a, b, comp, attr)
            if ch and (comp, attr) not in HANDLED_SERIES:
                unclassified.append(f"{comp}_t.{attr}: {len(ch)} columns ({ch[:3]})")
    caps_a, caps_b = a.meta.get("external_annual_caps", {}), b.meta.get("external_annual_caps", {})

    # ---- constant term (exact)
    c31 = const_of(rec31); c31s = const_of(jl(SMOKE31 / rid / "SOLVE_RECEIPT.json")); c4 = const_of(jl(SMOKE_D2C / d2c / "SOLVE_RECEIPT.json"))
    add("constant", "objective constant", "fixed-capacity capital / fixed O&M", "ASEAN", c4 - c31, detail=dict(v31_2920=c31, v31_56=c31s, v4_56=c4, v31_constant_snapshot_independent=abs(c31 - c31s) <= 1e-6 * abs(c31)))
    if abs(c31 - c31s) > 1e-6 * abs(c31):
        notes.append("v3.1 objective constant differs between 2920x3h and 56 snapshots - the v4 constant from the smoke receipt is not exact")

    # ---- loads (existing buses: v3.1 duals; new buses: dual extension)
    newbus = sorted(set(b.buses.index) - set(a.buses.index))
    yext = {}
    feed = {f: [k for k in b.links.index[b.links.bus1 == f] if float(b.links.at[k, "efficiency"]) > 0] for f in newbus}
    other = {}
    for f in newbus:
        att = dict(gens=list(b.generators.index[b.generators.bus == f]), stores=list(b.stores.index[b.stores.bus == f]), sus=list(b.storage_units.index[b.storage_units.bus == f]),
                   out_links=list(b.links.index[b.links.bus0 == f]) + [k for j in (2, 3, 4) if f"bus{j}" in b.links.columns for k in b.links.index[b.links[f"bus{j}"] == f]])
        if any(att.values()) or not feed[f]:
            other[f] = att
    pending = [f for f in newbus if f not in other]
    for _ in range(10):
        left = []
        for f in pending:
            cand, ok = [], True
            for k in feed[f]:
                L = b.links.loc[k]; b0 = L.bus0
                if b0 not in Y.columns and b0 not in yext:
                    ok = False; break
                y0 = (Y[b0] if b0 in Y.columns else yext[b0]).to_numpy()
                val = w * float(L.marginal_cost) + y0
                for j in (2, 3, 4):
                    bj = L.get(f"bus{j}", ""); ej = float(L.get(f"efficiency{j}", 0.0) or 0.0)
                    if isinstance(bj, str) and bj and ej != 0.0:
                        if bj not in Y.columns and bj not in yext:
                            ok = False; break
                        val = val - ej * (Y[bj] if bj in Y.columns else yext[bj]).to_numpy()
                if not ok:
                    break
                cand.append(val / float(L.efficiency))
            if ok:
                yext[f] = pd.Series(np.min(np.vstack(cand), axis=0), index=sn)
            else:
                left.append(f)
        pending = left
        if not pending:
            break
    unresolved = sorted(set(pending) | set(other))
    if unresolved:
        unclassified.append(f"new buses without a dual extension: {unresolved[:10]} ({ {f: other.get(f) for f in unresolved[:3]} })")
    la, lb = set(a.loads.index), set(b.loads.index)
    union = sorted(la | lb)
    assert (a.loads.sign == -1).all() and (b.loads.sign == -1).all(), "load sign"
    Pa = dense(a, "Load", "p_set", sorted(la)); Pb = dense(b, "Load", "p_set", sorted(lb))
    for l in union:
        pa = Pa[l].to_numpy() if l in la else np.zeros(len(sn)); pb = Pb[l].to_numpy() if l in lb else np.zeros(len(sn))
        d = pb - pa
        if not np.any(d):
            continue
        bus = b.loads.at[l, "bus"] if l in lb else a.loads.at[l, "bus"]
        car = b.loads.at[l, "carrier"] if l in lb else a.loads.at[l, "carrier"]
        bt = b if bus in b.buses.index else a; cty = bt.buses.at[bus, "country"]
        if bus in Y.columns:
            add("rhs", "load", car, cty, float((Y[bus].to_numpy() * d).sum()), qty=float((d * w).sum()), unit="MWh/a", detail=("new load" if l not in la else ("removed load" if l not in lb else None)))
        elif bus in yext:
            add("structure", "load on a new final-energy bus (dual extension)", car, cty, float((yext[bus].to_numpy() * d).sum()), qty=float((d * w).sum()), unit="MWh/a")
        else:
            unclassified.append(f"load {l} on bus {bus} without a dual")
    # new links between existing buses: reduced cost check
    newlinks = sorted(set(b.links.index) - set(a.links.index))
    for k in newlinks:
        L = b.links.loc[k]
        if L.bus1 in yext or L.bus1 in newbus:
            continue
        unclassified.append(f"new link {k} between existing buses (reduced cost not checked)")

    # ---- stores: e_initial (first-snapshot energy balance), fixed e_nom bounds
    stA, stB = a.stores, b.stores
    ebd = Dl.frame("Store-energy_balance", sorted(set(stA.index) | set(stB.index)))
    for s in sorted(set(stA.index) | set(stB.index)):
        ea = float(stA.at[s, "e_initial"]) if s in stA.index else 0.0; eb_ = float(stB.at[s, "e_initial"]) if s in stB.index else 0.0
        st = stB if s in stB.index else stA
        if ea != eb_:
            if bool(st.at[s, "e_cyclic"]):
                unclassified.append(f"store {s}: e_initial changed on a cyclic store")
            else:
                y0 = float(ebd[s].iloc[0]) if s in ebd.columns else 0.0
                add("rhs", "store initial energy", st.at[s, "carrier"], st.at[s, "country"] if "country" in st.columns else "", -y0 * (eb_ - ea), qty=eb_ - ea, unit="MWh",
                    detail=dict(dual_t0=y0, removed=s not in stB.index))
    fixs = [s for s in sorted(set(stA.index) | set(stB.index)) if not bool((stB if s in stB.index else stA).at[s, "e_nom_extendable"])]
    chg = [s for s in fixs if (s not in stB.index) or (s not in stA.index) or float(stA.at[s, "e_nom"]) != float(stB.at[s, "e_nom"])]
    if chg:
        yu = Dl.frame("Store-fix-e-upper", chg); yl = Dl.frame("Store-fix-e-lower", chg)
        for s in chg:
            def rhs(n, attr):
                return dense(n, "Store", attr, [s])[s].to_numpy() * float(n.stores.at[s, "e_nom"]) if s in n.stores.index else np.zeros(len(sn))
            du, dl = rhs(b, "e_max_pu") - rhs(a, "e_max_pu"), rhs(b, "e_min_pu") - rhs(a, "e_min_pu")
            st = stB if s in stB.index else stA
            add("rhs", "fixed store e_nom (upper)", st.at[s, "carrier"], st.at[s, "country"] if "country" in st.columns else "", float((yu[s].to_numpy() * du).sum()), qty=float(st.at[s, "e_nom"]) - (float(stA.at[s, "e_nom"]) if s in stA.index else 0.0), unit="MWh")
            if np.any(dl):
                add("rhs", "fixed store e_nom (lower, e_min_pu)", st.at[s, "carrier"], st.at[s, "country"] if "country" in st.columns else "", float((yl[s].to_numpy() * dl).sum()))
    # ---- fixed generators / links: p_nom (and pu) changes
    for comp, var in (("Generator", "Generator"), ("Link", "Link")):
        A, Bn = a.df(comp), b.df(comp)
        common = A.index.intersection(Bn.index)
        fixed = [k for k in common if not bool(Bn.at[k, "p_nom_extendable"])]
        ch = [k for k in fixed if float(A.at[k, "p_nom"]) != float(Bn.at[k, "p_nom"])]
        if not ch:
            continue
        yu = Dl.frame(f"{var}-fix-p-upper", ch); yl = Dl.frame(f"{var}-fix-p-lower", ch)
        mu, ml = dense(b, comp, "p_max_pu", ch), dense(b, comp, "p_min_pu", ch); mua, mla = dense(a, comp, "p_max_pu", ch), dense(a, comp, "p_min_pu", ch)
        for k in ch:
            du = mu[k].to_numpy() * float(Bn.at[k, "p_nom"]) - mua[k].to_numpy() * float(A.at[k, "p_nom"])
            dl = ml[k].to_numpy() * float(Bn.at[k, "p_nom"]) - mla[k].to_numpy() * float(A.at[k, "p_nom"])
            bus = Bn.at[k, "bus"] if comp == "Generator" else Bn.at[k, "bus0"]
            cty = b.buses.at[bus, "country"] if bus in b.buses.index else ""
            add("rhs", f"fixed {comp.lower()} p_nom", Bn.at[k, "carrier"], cty, float((yu[k].to_numpy() * du).sum() + (yl[k].to_numpy() * dl).sum()), qty=float(Bn.at[k, "p_nom"]) - float(A.at[k, "p_nom"]), unit="MW")
        # removed fixed components with a forced lower bound would be a rhs change, not a restriction
    for comp in ("Generator", "Link"):
        A, Bn = a.df(comp), b.df(comp)
        for k in sorted(set(A.index) - set(Bn.index)):
            if not bool(A.at[k, "p_nom_extendable"]) and float(dense(a, comp, "p_min_pu", [k])[k].max()) > 0:
                unclassified.append(f"removed fixed {comp} {k} with p_min_pu > 0")
            else:
                notes.append(f"removed {comp} {k}: restriction (term 0)") if len(notes) < 40 else None
    for s in sorted(set(stA.index) - set(stB.index)):
        notes.append(f"removed Store {s}: its energy moved to 0 (store initial energy / e_nom terms), then a restriction")
    # ---- storage units: fixed p_nom changes, inflow series, new units
    suA, suB = a.storage_units, b.storage_units
    ch = [k for k in suA.index.intersection(suB.index) if not bool(suB.at[k, "p_nom_extendable"]) and float(suA.at[k, "p_nom"]) != float(suB.at[k, "p_nom"])]
    if ch:
        yd = Dl.frame("StorageUnit-fix-p_dispatch-upper", ch); ys = Dl.frame("StorageUnit-fix-p_store-upper", ch); yc = Dl.frame("StorageUnit-fix-state_of_charge-upper", ch)
        for k in ch:
            dp = float(suB.at[k, "p_nom"]) - float(suA.at[k, "p_nom"])
            v = (yd[k].to_numpy() * dense(b, "StorageUnit", "p_max_pu", [k])[k].to_numpy() * dp).sum() + (ys[k].to_numpy() * (-dense(b, "StorageUnit", "p_min_pu", [k])[k].to_numpy()) * dp).sum() \
                + (yc[k].to_numpy() * float(suB.at[k, "max_hours"]) * dp).sum()
            add("rhs", "fixed storage unit p_nom", suB.at[k, "carrier"], b.buses.at[suB.at[k, "bus"], "country"], float(v), qty=dp, unit="MW")
    chi = changed_series(a, b, "StorageUnit", "inflow")
    if chi:
        ysu = Dl.frame("StorageUnit-energy_balance", chi)
        for k in chi:
            ia = a.storage_units_t.inflow[k].to_numpy() if k in a.storage_units_t.inflow.columns else np.zeros(len(sn))
            ib = b.storage_units_t.inflow[k].to_numpy() if k in b.storage_units_t.inflow.columns else np.zeros(len(sn))
            add("rhs", "storage unit inflow", suB.at[k, "carrier"], b.buses.at[suB.at[k, "bus"], "country"], float((ysu[k].to_numpy() * (-eh * (ib - ia))).sum()), qty=float((eh * (ib - ia)).sum()), unit="MWh/a")
    for k in sorted(set(suB.index) - set(suA.index)):
        bus = suB.at[k, "bus"]; yb = Y[bus].to_numpy() if bus in Y.columns else None
        if yb is None or not (float(suB.at[k, "marginal_cost"]) == 0.0 and not bool(suB.at[k, "p_nom_extendable"])):
            unclassified.append(f"new storage unit {k} (bus {bus}) not of the handled kind"); continue
        pmax = dense(b, "StorageUnit", "p_max_pu", [k])[k].to_numpy()
        cap_bound = float(suB.at[k, "p_nom"]) * float((np.maximum(yb, 0.0) * pmax).sum())
        inflow = b.storage_units_t.inflow[k].to_numpy() if k in b.storage_units_t.inflow.columns else np.zeros(len(sn))
        energy = float((eh * inflow).sum()) + float(suB.at[k, "state_of_charge_initial"])
        en_bound = energy * float(np.max(np.maximum(yb / w, 0.0)))
        add("structure", "new storage unit (capacity / energy bound)", suB.at[k, "carrier"], b.buses.at[bus, "country"], -min(cap_bound, en_bound), qty=float(suB.at[k, "p_nom"]), unit="MW",
            detail=dict(capacity_bound_eur=cap_bound, energy_bound_eur=en_bound, inflow_mwh=energy))
    # ---- annual caps (gas production)
    for g in sorted(set(caps_a) | set(caps_b)):
        ca_, cb_ = caps_a.get(g), caps_b.get(g)
        if ca_ == cb_:
            continue
        y = Dl.scalar(f"ResearchImportAnnual-{g}")
        if ca_ is None or cb_ is None or y is None:
            unclassified.append(f"annual cap {g}: present on one side or no v3.1 dual ({ca_} -> {cb_})"); continue
        add("rhs", "annual cap (domestic gas production)", "gas production", b.generators.at[g, "country"], y * (float(cb_) - float(ca_)), qty=float(cb_) - float(ca_), unit="MWh/a", detail=dict(dual=y))
    # ---- cost class
    for comp, key, pkey in (("Generator", "marginal_cost", "generators_t_p"), ("Store", "marginal_cost", "stores_t_p"), ("Link", "marginal_cost", "links_t_p0"), ("StorageUnit", "marginal_cost", "storage_units_t_p_dispatch")):
        A, Bn = a.df(comp), b.df(comp)
        ch = changed_rows(A, Bn, key)
        if not ch:
            continue
        X = solved_ts(S, pkey, ch, sn)
        for k in ch:
            dc = float(Bn.at[k, key]) - float(A.at[k, key]); x = X[k].to_numpy()
            if (x < -1e-6).any() and dc < 0:
                unclassified.append(f"cost change {comp} {k} on a variable that takes negative values")
            bus = Bn.at[k, "bus"] if comp != "Link" else Bn.at[k, "bus0"]
            add("cost", f"{comp.lower()} marginal cost", Bn.at[k, "carrier"], b.buses.at[bus, "country"] if bus in b.buses.index else "", dc * float((w * x).sum()), qty=dc, unit="EUR/MWh",
                detail=dict(dispatch_mwh=float((w * x).sum()), min_dispatch=float(x.min())))
    # ---- coefficient class (first-order only)
    A, Bn = a.links, b.links
    common = A.index.intersection(Bn.index)
    effc = {j: changed_rows(A, Bn, "efficiency" if j == 1 else f"efficiency{j}") for j in (1, 2, 3, 4)}
    allk = sorted(set().union(*effc.values()))
    if allk:
        P0 = solved_ts(S, "links_t_p0", allk, sn)
        for j, ks in effc.items():
            col = "efficiency" if j == 1 else f"efficiency{j}"
            for k in ks:
                bj = Bn.at[k, f"bus{j}"]; de = float(Bn.at[k, col]) - float(A.at[k, col])
                if bj not in Y.columns:
                    unclassified.append(f"efficiency change {k} on bus {bj} without a dual"); continue
                add("coef", f"link {col}", Bn.at[k, "carrier"], b.buses.at[Bn.at[k, "bus0"], "country"], -float((de * P0[k].to_numpy() * Y[bj].to_numpy()).sum()), qty=de, unit="-",
                    detail=dict(bus=bj, p0_mwh=float((w * P0[k].to_numpy()).sum())))
    R = pd.DataFrame(rows)
    by = R.groupby("cls").value_eur.sum().to_dict()
    tol = 1e-6 * abs(V31)
    lb = by.get("constant", 0.0) + by.get("rhs", 0.0) + by.get("structure", 0.0)
    cost_lb = float(R[(R.cls == "cost") & (R.value_eur < 0)].value_eur.sum()) if len(R[R.cls == "cost"]) else 0.0
    fo = by.get("coef", 0.0)
    alarm = lb + cost_lb - tol - 2 * abs(fo)
    res = dict(run=rid, scenario=sc, v31_objective_eur=V31, v31_objective_lp_eur=float(rec31.get("objective_lp", V31 - c31)), v31_solved_network=str(solved),
               v31_duals=str(E / "DUALS_BY_CONSTRAINT.nc"), v31_network=str(PKG31 / f"{sc}_2920_3h_unsolved.nc"), v4_network=str(B / sc / f"{sc}_2920_3h_unsolved.nc"),
               by_class_eur=by, constant_change_eur=by.get("constant", 0.0), rhs_lower_bound_eur=by.get("rhs", 0.0), structure_lower_bound_eur=by.get("structure", 0.0),
               cost_class_upper_bound_eur=by.get("cost", 0.0), cost_class_lower_bound_eur=cost_lb, coefficient_first_order_eur=fo, tolerance_eur=tol,
               lower_bound_eur=lb + cost_lb, alarm_line_eur=alarm, alarm_objective_eur=V31 + alarm,
               first_order_estimate_eur=lb + by.get("cost", 0.0) + fo, unclassified=unclassified, n_unclassified=len(unclassified), notes=notes[:60],
               new_buses_extended=len(yext), new_buses=len(newbus), new_links=len(newlinks))
    print(rid, json.dumps({k: v for k, v in res.items() if k not in ("notes",)}, default=float)[:2500], flush=True)
    del a, b, S, Dl, Y; gc.collect()
    return res, rows


def main():
    out, allrows = {}, []
    for rid in RUNS:
        r, rows = run(rid); out[rid] = r; allrows += rows
    R = pd.DataFrame(allrows)
    agg = R.groupby(["run", "cls", "term", "item", "country"], as_index=False).agg(value_eur=("value_eur", "sum"), n=("value_eur", "size"))
    (W / "tables").mkdir(exist_ok=True); (W / "evidence").mkdir(exist_ok=True)
    agg.to_csv(W / "tables/W14_BOUNDS_PRE.csv", index=False, float_format="%.6g", lineterminator="\n")
    out["status"] = "registered before any v4 HPC solve (W14 section 4); EXACT rule, numbers from the v3.1 2920x3h HPC solutions"
    out["method"] = __doc__
    (W / "evidence/W14_BOUNDS_PRE.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
