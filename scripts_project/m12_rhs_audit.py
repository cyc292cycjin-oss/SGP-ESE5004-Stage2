"""M12 C2 (item 133): right-hand-side attribution audit of the LP behind the Owen allocation. The LP is BUILT with linopy (same model as
s2_solve.py up to the LP export: l23_violation_analysis.build_model) and NEVER solved; no solver is called.

For every constraint family the rows are classified by the owner of their right-hand side - a country (component bus country / Load.country /
name suffix), a cross-border pair "A|B" (two halves, each country holding the full right), the bunker account (12th player), SHARED (no owner:
ASEAN pool components) or unresolved - and rows whose VARIABLES belong to more than one player are counted (coupling rows: their duals move value
between players, so the market-settlement form equals Owen's y'b only if they are homogeneous or internal). Owen's premise needs every non-zero
right-hand side to have an owner; the SHARED / unresolved rows are listed with a meaning and a proposed attribution for the reviewer.

Optional dual form (Owen 1975: phi_i = y' b_i + constants_i): with the run's duals - DUALS_BY_CONSTRAINT.nc (rows only) or the exported arrays
lp/ + solution/{Pi,RC} (rows and column bounds) - the products multiplier x active bound are summed by owner and compared with the
market-settlement allocation of m12_allocation.py. Nodal-balance right-hand sides (loads) are split by the loads' owners.

    PYTHONHASHSEED=0 python scripts_project/m12_rhs_audit.py audit --repo . --network <unsolved nc> --scenario integrated --out <dir>
        [--truncate N] [--duals <DUALS_BY_CONSTRAINT.nc> | --solve-dir <dir with lp/ and solution/>] [--allocation <ALLOCATION.json>] [--tag T]
    python scripts_project/m12_rhs_audit.py loo --full <dir>/RHS_BY_FAMILY_OWNER.csv --variant <dir>/RHS_BY_FAMILY_OWNER.csv --removed VN --out <dir>
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import resource
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from m12_allocation import BUNKER, COUNTRIES, PLAYERS, SHARED, entity_code, fold, sha   # noqa: E402

SCRIPT = "scripts_project/m12_rhs_audit.py"
COMP_TYPES = ("Bus", "Line", "Link", "Generator", "Store", "StorageUnit", "Load", "Transformer")
NODAL = ("Bus-nodal_balance", "Bus-meshed-nodal_balance")
UNRESOLVED = "-"
CC_SUFFIX = re.compile(r"-(%s)$" % "|".join(COUNTRIES))
CLASSES = ("country", "cross_border_pair", "bunker", "shared", "unresolved")

# meaning of the families (for the report)
FAMILY_NOTES = {
    "Bus-nodal_balance": "节点平衡（市场行）；右端项 = 负荷（按负荷所属国拆分）",
    "Bus-meshed-nodal_balance": "网状母线节点平衡（同上）",
    "Generator-ext-p_nom-lower": "可扩建发电机容量下限 p_nom_min（存量 / 规划下限）",
    "Generator-ext-p_nom-upper": "可扩建发电机容量上限 p_nom_max（资源潜力、进口码头上限）",
    "Generator-fix-p-lower": "不可扩建发电机出力下限 p_nom × p_min_pu",
    "Generator-fix-p-upper": "不可扩建发电机出力上限 p_nom × p_max_pu（存量容量 × 可用率）",
    "Generator-ext-p-lower": "可扩建发电机出力下限（齐次）", "Generator-ext-p-upper": "可扩建发电机出力上限（齐次）",
    "Line-ext-s_nom-lower": "线路容量下限（存量）", "Line-ext-s_nom-upper": "线路容量上限（走廊上限）",
    "Line-ext-s-lower": "线路潮流下限（齐次）", "Line-ext-s-upper": "线路潮流上限（齐次）",
    "Line-loss_proxy-pos": "交流损耗代理（齐次）", "Line-loss_proxy-neg": "交流损耗代理（齐次）", "Line-ext-loss_upper": "损耗上限（齐次）",
    "Link-ext-p_nom-lower": "可扩建链路容量下限（存量 / 跨境存量）", "Link-ext-p_nom-upper": "可扩建链路容量上限",
    "Link-ext-p-lower": "链路流量下限（齐次）", "Link-ext-p-upper": "链路流量上限（齐次）",
    "Link-fix-p-lower": "不可扩建链路流量下限 p_nom × p_min_pu", "Link-fix-p-upper": "不可扩建链路流量上限 p_nom × p_max_pu",
    "Kirchhoff-Voltage-Law": "基尔霍夫电压定律回路约束（齐次，回路可跨国）",
    "Store-energy_balance": "储能能量平衡；首时段右端项 = 非循环 Store 的 e_initial（生物质池等固定资源）",
    "Store-ext-e_nom-lower": "储能容量下限", "Store-ext-e_nom-upper": "储能容量上限（封存潜力等）",
    "Store-ext-e-lower": "储能水平下限（齐次）", "Store-ext-e-upper": "储能水平上限（齐次）",
    "Store-fix-e-lower": "不可扩建储能水平下限 e_nom × e_min_pu", "Store-fix-e-upper": "不可扩建储能水平上限 e_nom × e_max_pu",
    "StorageUnit-energy_balance": "抽蓄 / 水库能量平衡；右端项 = 入流", "StorageUnit-ext-p_nom-lower": "储能单元容量下限", "StorageUnit-ext-p_nom-upper": "储能单元容量上限",
    "ResearchBatteryNominal": "电池充放容量耦合（齐次）", "ResearchImportAnnual": "国产气年产量上限（名为 Import，实为国内产量）",
    "ResearchStoreDirection": "Store 只充 / 只放（齐次）", "research_new_hydro_inflow": "新建水电入流",
    "research_lossy_bidirectional_sync": "有损双向链路正反向容量相等（齐次）", "research_country_co2_limit": "国家净零（末时段国家大气 Store ≤ 上限）",
    "research_co2_storage_cap": "国家年封存上限（接收国的封存能力，他国船运 CO2 也计入）", "research_bunker_co2_limit": "燃料舱净零（东盟燃料舱账户）",
    "research_asean_co2_limit": "东盟整体 CO2 上限（主配置未启用）", "research_gap_co2_limit": "差额诊断 CO2 上限（带松弛；遍历全部 11 国）",
    "research_nuclear_national_cap": "国家核电上限", "research_apg_corridor_cap": "跨境项目组容量上限", "ResearchExistingResource": "存量资源组",
}
PROPOSALS = {
    "shared": "东盟池（ASEAN oil / oil non-fossil / methanol / ammonia）的无主组件：区域外进口（固定价格）与池储罐。提议 (a) 归入燃料舱参与者"
              "（第 12 个参与者）；或 (b) 按各国在该池的净购买量比例分到国家；或 (c) 维持现状，残差单列（现行账本：池盈余为恒等式差项）。",
    "unresolved": "右端项非零、但无法由组件母线 / 名称后缀 / 变量确定所有者的行：逐行列出，交审阅端决定。",
}


def family(name: str) -> str:
    """constraint name -> family: research hooks lose their per-instance suffix (component name or country)."""
    if re.match(r"^(Research[A-Za-z]+|research_[a-z_]+)-", name):
        return name.split("-")[0]
    return CC_SUFFIX.sub("", name)


def owner_class(code: str) -> str:
    if code in COUNTRIES:
        return "country"
    if "|" in code:
        return "cross_border_pair"
    if code == BUNKER:
        return "bunker"
    if code == SHARED:
        return "shared"
    return "unresolved"


# ----------------------------------------------------------------------------------------------------------------------------- owners
class Owners:
    """owner codes of buses, components and loads (s4d_ledger rules via m12_allocation.entity_code) and an integer code table."""

    def __init__(self, n):
        from s4d_ledger import bus_entities, owners
        ent = bus_entities(n); own = owners(n, ent)
        self.maps = {"Bus": ent.map(entity_code).astype(str)}
        for t, s in own.items():
            self.maps[t] = s.astype(str).map(entity_code)
        if len(n.df("Transformer")):
            self.maps["Transformer"] = pd.Series([entity_code(ent[b]) for b in n.df("Transformer").bus0], index=n.df("Transformer").index)
        self.comp = {}
        for t, s in self.maps.items():
            if t != "Bus":
                for k in s.index:
                    self.comp.setdefault(str(k), t)
        self.codes = {UNRESOLVED: 0}

    def code(self, s: str) -> int:
        return self.codes.setdefault(str(s), len(self.codes))

    def inv(self) -> dict:
        return {v: k for k, v in self.codes.items()}

    def by_name(self, name: str) -> str | None:
        """scalar / non-component constraints and variables: owner from the name."""
        if name == "research_bunker_co2_limit":
            return BUNKER
        m_ = CC_SUFFIX.search(name)
        if m_ and (name.startswith("research_") or name.startswith("Research")):
            return m_.group(1)
        if "-" in name:
            t = self.comp.get(name.split("-", 1)[1])
            if t is not None:
                return str(self.maps[t][name.split("-", 1)[1]])
        return None

    def array(self, name: str, lab) -> np.ndarray:
        """owner code (int) for every element of a linopy label array (component dimension, else the name; UNRESOLVED = 0)."""
        arr = np.asarray(lab.values)
        dims = list(lab.dims); comp = [d for d in dims if str(d).split("-")[0] in COMP_TYPES]
        if comp:
            d = comp[0]; t = str(d).split("-")[0]
            vals = pd.Index(map(str, lab.coords[d].values))
            cv = self.maps[t].reindex(vals).fillna(UNRESOLVED).to_numpy() if t in self.maps else np.full(len(vals), UNRESOLVED, dtype=object)
            vec = np.array([self.code(c) for c in cv], dtype=np.int32)
            shape = [1] * arr.ndim; shape[dims.index(d)] = len(vec)
            return np.array(np.broadcast_to(vec.reshape(shape), arr.shape))
        o = self.by_name(name)
        return np.full(arr.shape, self.code(o) if o is not None else 0, dtype=np.int32)


def load_split(n, O: Owners) -> dict:
    """per bus: DataFrame snapshots x owner of the loads' p_set (for the nodal right-hand sides)."""
    d = n.loads
    if not len(d):
        return {}
    ps = n.get_switchable_as_dense("Load", "p_set")
    own = O.maps["Load"].reindex(d.index).fillna(UNRESOLVED)
    out = {}
    for b, idx in d.groupby("bus").groups.items():
        idx = list(idx)
        out[str(b)] = ps[idx].T.groupby(own.reindex(idx).to_numpy()).sum().T
    return out


def objective_constants(n, O: Owners) -> dict:
    """objective constants by owner: existing fixed O&M moved out of the LP (existing_annual_fixed_om_eur of the components and the existing
    cross-border FOM ledger) minus PyPSA's constant capital_cost x p_nom of the extendable components (the LP charges p_nom_opt)."""
    from s4d_ledger import NOM
    out = {}
    for t, nom in NOM.items():
        d = n.df(t)
        if not len(d):
            continue
        c = -(d[nom] * d.capital_cost).where(d[nom + "_extendable"], 0.0)
        if "existing_annual_fixed_om_eur" in d:
            c = c + pd.to_numeric(d.existing_annual_fixed_om_eur, errors="coerce").fillna(0.0)
        for k, v in c.groupby(O.maps[t].reindex(d.index).fillna(UNRESOLVED)).sum().items():
            out[str(k)] = out.get(str(k), 0.0) + float(v)
    for _, r in pd.DataFrame(n.meta.get("existing_cross_border_fom_ledger", [])).iterrows():
        k = str(O.maps[r.component_type][r.component]); out[k] = out.get(k, 0.0) + float(r.annual_fom_eur)
    return dict(by_owner=out, total=float(sum(out.values())))


# ----------------------------------------------------------------------------------------------------------------------------- duals
def lp_array_duals(solve_dir: Path, vown: np.ndarray, O: Owners):
    """row multipliers by linopy label from the exported arrays, and the column-bound terms rc x active bound by owner."""
    clab = np.load(solve_dir / "lp" / "clabels.npy"); vlab = np.load(solve_dir / "lp" / "vlabels.npy")
    pi = np.load(solve_dir / "solution" / "Pi.npy"); rc = np.load(solve_dir / "solution" / "RC.npy")
    piL = np.full(int(clab.max()) + 1, np.nan); piL[clab] = pi

    def dual_of(name, lab):
        L = np.asarray(lab.values)
        return np.where(L >= 0, piL[np.clip(L, 0, len(piL) - 1)], np.nan)
    lo, hi = np.load(solve_dir / "lp" / "col_lower.npy"), np.load(solve_dir / "lp" / "col_upper.npy")
    b = np.where(rc > 0, lo, np.where(rc < 0, hi, 0.0)); bad = ~np.isfinite(b)
    term = np.where(bad, 0.0, rc * np.where(bad, 0.0, b))
    oc = vown[np.clip(vlab, 0, len(vown) - 1)]; inv = O.inv()
    cols = {inv[int(k)]: float(v) for k, v in pd.Series(term).groupby(oc).sum().items() if v != 0}
    info = dict(columns=int(len(vlab)), nonzero_bound_terms=int((term != 0).sum()), sign_error_columns=int(bad.sum()))
    return dual_of, cols, info


def nc_duals(path: Path):
    import xarray as xr
    ds = xr.open_dataset(path)

    def dual_of(name, lab):
        if name not in ds:
            return None
        d = ds[name]
        d = d.rename({k: str(k).split("|", 1)[1] for k in d.dims if "|" in str(k)})
        d = d.reindex({k: lab.coords[k].values for k in lab.dims if k in d.dims and k in lab.coords})
        return np.asarray(d.transpose(*lab.dims).values, dtype=float)
    return dual_of


# ----------------------------------------------------------------------------------------------------------------------------- audit
def decompose(solve_dir: Path, rown: np.ndarray, rfam: np.ndarray, fams: dict, vown: np.ndarray, inv: dict) -> dict:
    """exact decomposition of (market form - dual form) by owner from the exported arrays (A, c, X, Pi, RC, bounds):
        market_p - dual_p = sum_{non-nodal rows r} [pi_r (A x_p)_r - 1(r owned by p) pi_r b_r]     (coupling transfers + row complementarity)
                          + sum_{j in p} rc_j (x_j - bound_j)                                      (column complementarity)
                          + sum_{j in p} (c_j - a_j' pi - rc_j) x_j                                (stationarity residual)
    by family of the rows; KVL rows (homogeneous, lines of several owners) give the loop-flow transfer."""
    import scipy.sparse as sp
    lp = solve_dir / "lp"; meta = json.loads((lp / "MATH_PROBLEM.json").read_text())
    Z = {k: np.load(lp / (k + ".npy")) for k in ("cost", "col_lower", "col_upper", "row_lower", "row_upper", "start", "index", "value", "clabels", "vlabels")}
    x, pi, rc = (np.load(solve_dir / "solution" / (k + ".npy")) for k in ("X", "Pi", "RC"))
    A = sp.csc_matrix((Z["value"], Z["index"], Z["start"]), shape=(meta["num_row"], meta["num_col"]))
    ro = rown[Z["clabels"]]; rf = rfam[Z["clabels"]]; co = vown[np.clip(Z["vlabels"], 0, len(vown) - 1)]
    finv = {v: k for k, v in fams.items()}
    nodal = np.isin(rf, [fams[f] for f in NODAL if f in fams])
    Ac = A.tocoo(); rr, cc, vv = Ac.row, Ac.col, Ac.data
    keep = ~nodal[rr]
    t = pi[rr[keep]] * vv[keep] * x[cc[keep]]
    T = pd.DataFrame(dict(f=rf[rr[keep]], o=co[cc[keep]], t=t)).groupby(["f", "o"]).t.sum()
    lo, hi = Z["row_lower"], Z["row_upper"]
    b = np.where(pi > 0, lo, np.where(pi < 0, hi, 0.0)); b = np.where(np.isfinite(b), b, 0.0)
    Dr = pd.DataFrame(dict(f=rf, o=ro, t=pi * b))[~nodal].groupby(["f", "o"]).t.sum()
    cl, cu = Z["col_lower"], Z["col_upper"]
    bc = np.where(rc > 0, cl, np.where(rc < 0, cu, 0.0))
    K = np.where(np.isfinite(bc), rc * (x - np.where(np.isfinite(bc), bc, 0.0)), rc * x)
    S = (Z["cost"] - A.T @ pi - rc) * x
    by_f = {}
    for (f, o), v in T.items():
        by_f.setdefault(finv[int(f)], {}); by_f[finv[int(f)]][inv[int(o)]] = by_f[finv[int(f)]].get(inv[int(o)], 0.0) + float(v)
    for (f, o), v in Dr.items():
        by_f.setdefault(finv[int(f)], {}); by_f[finv[int(f)]][inv[int(o)]] = by_f[finv[int(f)]].get(inv[int(o)], 0.0) - float(v)
    Ks = {inv[int(k)]: float(v) for k, v in pd.Series(K).groupby(co).sum().items()}
    Ss = {inv[int(k)]: float(v) for k, v in pd.Series(S).groupby(co).sum().items()}
    pred = {}
    for d in list(by_f.values()) + [Ks, Ss]:
        for k, v in d.items():
            pred[k] = pred.get(k, 0.0) + v
    fam_tot = {f: float(sum(abs(v) for v in d.values())) for f, d in by_f.items()}
    return dict(by_family_raw={f: d for f, d in by_f.items() if fam_tot[f] > 1.0}, column_complementarity_raw=Ks, stationarity_raw=Ss,
                predicted_market_minus_dual_raw=pred, predicted_market_minus_dual_alpha_half=fold(pred),
                kvl_alpha_half=fold(by_f.get("Kirchhoff-Voltage-Law", {})), stationarity_alpha_half=fold(Ss), column_complementarity_alpha_half=fold(Ks),
                rows_other_families_alpha_half=fold({k: sum(d.get(k, 0.0) for f, d in by_f.items() if f != "Kirchhoff-Voltage-Law") for k in set().union(*by_f.values())} if by_f else {}),
                abs_sum_by_family_eur=dict(sorted(fam_tot.items(), key=lambda kv: -kv[1])[:15]))


def audit(repo: Path, network: Path, scenario: str, out: Path, truncate, duals: Path | None, solve_dir: Path | None, allocation: Path | None, tag: str,
          solved: Path | None = None, register_dir: Path | None = None) -> dict:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=True)
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise SystemExit("PYTHONHASHSEED=0 required (constraint label order of the meshed buses depends on it; s4m_duals)")
    from l23_violation_analysis import build_model
    logging.disable(logging.WARNING)
    n, m, cfg = build_model(repo, network, scenario, truncate, "M12_RHS_AUDIT")
    t_build = time.time() - t0; rss_build = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2
    O = Owners(n)
    top = max(int(np.asarray(m.variables[v].labels).max()) for v in m.variables) + 1
    vown = np.zeros(top, dtype=np.int32)
    for v in m.variables:
        lab = m.variables[v].labels; arr = np.asarray(lab.values).ravel(); oc = O.array(v, lab).ravel()
        ok = (arr >= 0) & (arr < top); vown[arr[ok]] = oc[ok]
    dual_of, rc_terms, col_info = None, {}, {}
    xsol = None   # primal values by variable label (exported X, or the solved network's line flows for the KVL transfer)
    if solve_dir is not None:
        dual_of, rc_terms, col_info = lp_array_duals(solve_dir, vown, O)
        vlab = np.load(solve_dir / "lp" / "vlabels.npy"); xsol = np.full(top, np.nan); xsol[vlab] = np.load(solve_dir / "solution" / "X.npy")
    elif duals is not None:
        dual_of = nc_duals(duals)
        if solved is not None and "Line-s" in m.variables:
            import pypsa
            ns = pypsa.Network(str(solved)); xsol = np.full(top, np.nan)
            lab = m.variables["Line-s"].labels.transpose("snapshot", [d for d in m.variables["Line-s"].labels.dims if d != "snapshot"][0])
            dl = lab.dims[1]
            p0 = ns.lines_t.p0.reindex(index=lab.coords["snapshot"].values, columns=list(map(str, lab.coords[dl].values)))
            Lb = np.asarray(lab.values); ok = Lb >= 0; xsol[Lb[ok]] = p0.to_numpy()[ok]
            del ns
    # rows-only duals (DUALS_BY_CONSTRAINT.nc): the reduced costs of the columns with finite non-zero bounds (StorageUnit-spill <= inflow) are
    # rebuilt from stationarity, rc_j = c_j - a_j' y, over the non-nodal rows
    nc_mode = dual_of is not None and solve_dir is None
    isB = np.zeros(top, dtype=bool); bnd_lo = np.zeros(top); bnd_hi = np.zeros(top); aty = np.zeros(top)
    if nc_mode:
        for v in m.variables:
            V_ = m.variables[v]; lab = np.asarray(V_.labels).ravel()
            lo_ = np.broadcast_to(np.asarray(V_.lower, float), V_.labels.shape).ravel(); hi_ = np.broadcast_to(np.asarray(V_.upper, float), V_.labels.shape).ravel()
            sel = (lab >= 0) & ((np.isfinite(lo_) & (lo_ != 0)) | (np.isfinite(hi_) & (hi_ != 0)))
            isB[lab[sel]] = True; bnd_lo[lab[sel]] = lo_[sel]; bnd_hi[lab[sel]] = hi_[sel]
    loads = load_split(n, O)
    fam_rows, owner_rows, shared_rows, coupling, missing_duals, nodal_special = [], [], [], {}, [], []
    dual_terms = {}
    ctop = max(int(np.asarray(m.constraints[c].labels).max()) for c in m.constraints) + 1
    rown = np.zeros(ctop, dtype=np.int32); rfam = np.full(ctop, -1, dtype=np.int32); fams: dict = {}
    kvl = {}   # KVL loop transfer by owner of the line variables (needs the duals and the solved flows)
    nodal = dict(rows_with_load=0, max_abs_ratio_dev=0.0, rows_rhs_without_load=0, rhs_sign=None)

    def add_dual(o, v):
        dual_terms[o] = dual_terms.get(o, 0.0) + float(v)
    for name in m.constraints:
        con = m.constraints[name]; fam = family(name)
        lab, rhs_da = con.labels, con.rhs
        if name in NODAL:
            bdim = [d for d in lab.dims if str(d).startswith("Bus")][0]
            lab = lab.transpose("snapshot", bdim); rhs_da = rhs_da.broadcast_like(lab).transpose("snapshot", bdim)
        else:
            rhs_da = rhs_da.broadcast_like(lab).transpose(*lab.dims)
        L = np.asarray(lab.values); valid = L >= 0; rhs = np.asarray(rhs_da.values, dtype=float)
        oc = O.array(name, lab); inv = O.inv()
        n_coup, combos = 0, {}
        if name not in NODAL:   # coupling: owners of the variables of every row; unresolved row owners take the unique variable owner
            V = np.asarray(con.vars.transpose(*lab.dims, "_term").values) if "_term" in con.vars.dims else np.asarray(con.vars.values)[..., None]
            Vo = np.where(V >= 0, vown[np.clip(V, 0, top - 1)], -1)
            lo_ = np.where(Vo >= 0, Vo, np.iinfo(np.int32).max).min(axis=-1); hi_ = Vo.max(axis=-1)
            cm = valid & (hi_ >= 0) & (lo_ != hi_); n_coup = int(cm.sum())
            if n_coup:
                k_, c_ = np.unique(np.stack([lo_[cm], hi_[cm]], axis=1), axis=0, return_counts=True)
                combos = {f"{inv[int(a)]} + {inv[int(b)]}": int(c) for (a, b), c in zip(k_, c_)}
            fix = valid & (oc == 0) & (hi_ >= 0) & (lo_ == hi_)
            oc = np.where(fix, hi_, oc)
            if nc_mode and isB.any():
                mB = (V >= 0) & isB[np.clip(V, 0, top - 1)]
                if mB.any():
                    yv = dual_of(name, lab)
                    if yv is not None:
                        Cc = np.asarray(con.coeffs.transpose(*lab.dims, "_term").values) if "_term" in con.coeffs.dims else np.asarray(con.coeffs.values)[..., None]
                        prod = Cc * np.nan_to_num(np.broadcast_to(np.asarray(yv, float), L.shape))[..., None]
                        np.add.at(aty, V[mB], prod[mB])
        nz = valid & np.isfinite(rhs) & (rhs != 0)
        rown[L[valid]] = oc[valid]; rfam[L[valid]] = fams.setdefault(fam, len(fams))
        y = dual_of(name, lab) if dual_of is not None else None
        if dual_of is not None and y is None and nz.any():
            missing_duals.append(name)
        if name == "Kirchhoff-Voltage-Law" and y is not None and xsol is not None:
            Vk = np.asarray(con.vars.transpose(*lab.dims, "_term").values); Ck = np.asarray(con.coeffs.transpose(*lab.dims, "_term").values)
            okv = Vk >= 0; xv = np.where(okv, xsol[np.clip(Vk, 0, top - 1)], 0.0)
            tk = np.nan_to_num(np.asarray(y, float))[..., None] * np.where(okv, Ck * xv, 0.0)
            ok_o = np.where(okv, vown[np.clip(Vk, 0, top - 1)], 0)
            for k, v in pd.Series(tk.ravel()).groupby(ok_o.ravel()).sum().items():
                if v != 0:
                    kvl[inv[int(k)]] = kvl.get(inv[int(k)], 0.0) + float(v)
            kvl["_flows_missing_terms"] = int((okv & ~np.isfinite(xsol[np.clip(Vk, 0, top - 1)])).sum())
        cls_v = pd.Series(oc[valid]).map(lambda c: owner_class(inv[int(c)])).value_counts() if valid.any() else pd.Series(dtype=int)
        cls_n = pd.Series(oc[nz]).map(lambda c: owner_class(inv[int(c)])).value_counts() if nz.any() else pd.Series(dtype=int)
        top_c = dict(sorted(combos.items(), key=lambda kv: -kv[1])[:5])
        fam_rows.append(dict(constraint=name, family=fam, rows=int(valid.sum()), rhs_nonzero_rows=int(nz.sum()), coupling_rows=n_coup, coupling_top=json.dumps(top_c),
                             **{f"rows_{k}": int(cls_v.get(k, 0)) for k in CLASSES}, **{f"rhs_nonzero_{k}": int(cls_n.get(k, 0)) for k in CLASSES}))
        if n_coup:
            coupling[name] = dict(family=fam, rows=n_coup, homogeneous=bool(nz.sum() == 0), top=top_c)
        if not nz.any():
            continue
        if name in NODAL:   # right-hand side = loads: split by the loads' owners (sign checked against the loads)
            buses = list(map(str, lab.coords[bdim].values)); snaps = lab.coords["snapshot"].values
            ncls = {k: 0 for k in CLASSES + ("country_split_by_load",)}
            for j, b in enumerate(buses):
                r = np.where(nz[:, j], rhs[:, j], 0.0)
                if not r.any():
                    continue
                yj = None if y is None else np.nan_to_num(np.asarray(y)[:, j])
                ls = loads.get(b)
                lo_own = [str(o) for o in ls.columns if np.abs(ls[o].to_numpy()).sum() > 0] if ls is not None else []
                bo = inv[int(oc[0, j])]; k_ = int((r != 0).sum())
                if not lo_own:
                    ncls[owner_class(bo)] += k_
                elif len(lo_own) == 1:
                    ncls[owner_class(lo_own[0])] += k_
                else:
                    ncls["country_split_by_load" if all(o in COUNTRIES for o in lo_own) else "unresolved"] += k_
                if owner_class(bo) != "country" or len(lo_own) > 1 or (lo_own and lo_own[0] != bo):
                    nodal_special.append(dict(constraint=name, bus=b, bus_owner=bo, load_owners=lo_own, rows=k_))
                tot = ls.sum(axis=1).reindex(snaps).fillna(0.0).to_numpy() if ls is not None else np.zeros(len(r))
                has = tot != 0
                ratio = np.where(has, r / np.where(has, tot, 1.0), 0.0)
                if has.any():
                    nodal["rows_with_load"] += int(has.sum()); sg = float(np.sign(np.median(ratio[has])))
                    nodal["rhs_sign"] = nodal["rhs_sign"] or sg
                    nodal["max_abs_ratio_dev"] = max(nodal["max_abs_ratio_dev"], float(np.max(np.abs(ratio[has] - sg))))
                rest = np.where(has, 0.0, r)
                if rest.any():   # right-hand side not explained by loads: the bus owner
                    o_ = inv[int(oc[0, j])]; nodal["rows_rhs_without_load"] += int((rest != 0).sum())
                    owner_rows.append(dict(family=fam, owner=o_, rhs_sum=float(rest.sum()), rows=int((rest != 0).sum())))
                    if yj is not None:
                        add_dual(o_, (yj * rest).sum())
                if ls is not None and has.any():
                    for o_ in ls.columns:
                        part = ls[o_].reindex(snaps).fillna(0.0).to_numpy() * ratio
                        if part.any():
                            owner_rows.append(dict(family=fam, owner=str(o_), rhs_sum=float(part.sum()), rows=int((part != 0).sum())))
                            if yj is not None:
                                add_dual(str(o_), (yj * part).sum())
            fam_rows[-1].update({f"rhs_nonzero_{k}": v for k, v in ncls.items()})   # nodal rows classified by the owners of their loads
            continue
        ocs = oc[nz]; rs = rhs[nz]
        for k, v in pd.DataFrame(dict(o=ocs, r=rs)).groupby("o").r.agg(["sum", "size"]).iterrows():
            owner_rows.append(dict(family=fam, owner=inv[int(k)], rhs_sum=float(v["sum"]), rows=int(v["size"])))
        if y is not None:
            t_ = np.nan_to_num(np.asarray(y, dtype=float)[nz] * rs)
            for k, v in pd.Series(t_).groupby(ocs).sum().items():
                add_dual(inv[int(k)], v)
        badc = [c for c in np.unique(ocs) if owner_class(inv[int(c)]) in ("shared", "unresolved")]
        if badc:
            mask = nz & np.isin(oc, badc)
            cdims = [i for i, d in enumerate(lab.dims) if str(d).split("-")[0] in COMP_TYPES]
            comps = sorted(set(np.asarray(lab.coords[lab.dims[cdims[0]]].values).astype(str)[np.unique(np.nonzero(mask)[cdims[0]])]))[:40] if cdims else [name]
            cl = sorted({owner_class(inv[int(c)]) for c in badc})
            shared_rows.append(dict(constraint=name, family=fam, rows=int(mask.sum()), rhs_sum=float(rhs[mask].sum()), owners=sorted(inv[int(c)] for c in badc),
                                    components=comps, dual_term=(float(np.nansum(np.asarray(y, float)[mask] * rhs[mask])) if y is not None else None),
                                    meaning=FAMILY_NOTES.get(fam, ""), proposal=PROPOSALS["shared" if "shared" in cl else "unresolved"]))
    if nc_mode and isB.any():
        ov = np.asarray(m.objective.expression.vars).ravel(); ocf = np.asarray(m.objective.expression.coeffs).ravel()
        cost = np.zeros(top); okc = ov >= 0; np.add.at(cost, ov[okc], ocf[okc])
        Bl = np.flatnonzero(isB); rcB = cost[Bl] - aty[Bl]
        bb = np.where(rcB > 0, bnd_lo[Bl], np.where(rcB < 0, bnd_hi[Bl], 0.0)); tB = np.where(np.isfinite(bb), rcB * np.where(np.isfinite(bb), bb, 0.0), 0.0)
        inv = O.inv()
        rc_terms = {inv[int(k)]: float(v) for k, v in pd.Series(tB).groupby(vown[Bl]).sum().items() if v != 0}
        col_info = dict(columns_with_finite_nonzero_bounds=int(len(Bl)), source="rc rebuilt from stationarity rc = c - A'y over the non-nodal rows (rows-only duals)",
                        nonzero_terms=int((tB != 0).sum()))
    F = pd.DataFrame(fam_rows).fillna(0)
    R = (pd.DataFrame(owner_rows).groupby(["family", "owner"], as_index=False).agg(rhs_sum=("rhs_sum", "sum"), rows=("rows", "sum"))
         if owner_rows else pd.DataFrame(columns=["family", "owner", "rhs_sum", "rows"]))
    R["owner_class"] = R.owner.map(owner_class)
    F.to_csv(out / "RHS_FAMILIES.csv", index=False); R.to_csv(out / "RHS_BY_FAMILY_OWNER.csv", index=False)
    agg = {"constraints": ("constraint", "size"), "rows": ("rows", "sum"), "rhs_nonzero_rows": ("rhs_nonzero_rows", "sum"), "coupling_rows": ("coupling_rows", "sum")}
    for k in CLASSES + ("country_split_by_load",):
        if f"rhs_nonzero_{k}" not in F:
            F[f"rhs_nonzero_{k}"] = 0
        agg[f"rhs_nonzero_{k}"] = (f"rhs_nonzero_{k}", "sum")
    famsum = F.groupby("family").agg(**agg).reset_index()
    famsum["meaning"] = famsum.family.map(FAMILY_NOTES).fillna("")
    famsum.to_csv(out / "RHS_FAMILY_SUMMARY.csv", index=False)
    res = dict(script=SCRIPT, tag=tag, network=str(network), network_sha256=sha(network), scenario=scenario, truncate=truncate, snapshots=int(len(n.snapshots)),
               model=dict(constraints=len(list(m.constraints)), rows=int(F.rows.sum()), variables=int(len(list(m.variables))), build_seconds=t_build, peak_rss_gib_after_build=rss_build),
               families=famsum.to_dict(orient="records"), shared_or_unresolved=shared_rows, coupling=coupling, nodal_rhs_by_load_owner=nodal,
               nodal_buses_not_single_country=nodal_special,
               owen_premise=dict(nonzero_rhs_rows_by_class={k: int(F[f"rhs_nonzero_{k}"].sum()) for k in CLASSES + ("country_split_by_load",)},
                                 coupling_families_nonhomogeneous=sorted({v["family"] for v in coupling.values() if not v["homogeneous"]}),
                                 coupling_families_homogeneous=sorted({v["family"] for v in coupling.values() if v["homogeneous"]})),
               solver_runs=0)
    if dual_of is not None:
        const = objective_constants(n, O)
        tot = dict(dual_terms)
        for src in (rc_terms, const["by_owner"]):
            for k, v in src.items():
                tot[k] = tot.get(k, 0.0) + v
        ph = fold(tot)
        dual = dict(source=str(solve_dir or duals), rows_by_owner=dual_terms, columns_by_owner=rc_terms, columns=col_info, constants=const, missing_duals=missing_duals,
                    raw_by_owner=tot, allocation_alpha_half=ph, total=float(sum(tot.values())),
                    note="Owen dual form: sum of multiplier x active bound by owner (+ column bounds, + objective constants by owner); pairs folded with alpha 0.5")
        if allocation is not None:
            A = json.loads(Path(allocation).read_text())
            mk = A["allocation_eur"]["0.5"]; raw_m = A["raw_by_owner_eur"]
            dual.update(market_form_allocation_alpha_half=mk, market_minus_dual_eur={p: float(mk[p] - ph.get(p, 0.0)) for p in list(PLAYERS) + [SHARED]},
                        market_minus_dual_pairs_eur={k: float(v - tot.get(k, 0.0)) for k, v in raw_m.items() if "|" in k},
                        objective=A["objective"], dual_total_minus_objective_eur=float(dual["total"] - A["objective"]))
        if kvl:
            dual["kvl_loop_transfer_raw"] = kvl; dual["kvl_loop_transfer_alpha_half"] = fold({k: v for k, v in kvl.items() if not k.startswith("_")})
        if solve_dir is not None:
            dual["decomposition"] = decompose(solve_dir, rown, rfam, fams, vown, O.inv())
            if "market_minus_dual_eur" in dual:
                pr = dual["decomposition"]["predicted_market_minus_dual_alpha_half"]
                dual["decomposition"]["check_max_abs_dev_eur"] = float(max(abs(dual["market_minus_dual_eur"][p] - pr.get(p, 0.0)) for p in PLAYERS))
        res["dual_form"] = dual
    res["seconds"] = time.time() - t0
    res["peak_rss_gib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2
    (out / "RHS_AUDIT.json").write_text(json.dumps(res, indent=1, default=str))
    if register_dir is not None:   # run pipeline: register the outputs in the run's EXPORTS.json (paths relative to the run dir)
        p = Path(register_dir) / "EXPORTS.json"; ex = json.loads(p.read_text()) if p.exists() else {}
        for f in ("RHS_AUDIT.json", "RHS_FAMILIES.csv", "RHS_BY_FAMILY_OWNER.csv", "RHS_FAMILY_SUMMARY.csv"):
            q = out / f
            ex[str(q.relative_to(register_dir))] = dict(bytes=q.stat().st_size, sha256=sha(q), source="m12_rhs_audit.py (M12 C2 / Owen dual form, item 133)")
        p.write_text(json.dumps(ex, indent=1))
    return res


def loo_compare(full: Path, variant: Path, removed: list, out: Path) -> dict:
    """b(N - i) = b(N) restricted to the remaining owners, family by family: right-hand-side sums by (family, owner) of the full and the
    leave-one-out LP; any owner code naming a removed country left in the variant, and any change of a remaining owner's rights, is listed."""
    out.mkdir(parents=True, exist_ok=True)
    A = pd.read_csv(full); B = pd.read_csv(variant)
    # a bus leaves the meshed AC sub-network when a neighbour is removed: its balance row moves between the two nodal families, the right is the same
    merge = lambda D: D.assign(family=D.family.where(~D.family.isin(NODAL), "Bus-nodal_balance (both families)")).groupby(["family", "owner"], as_index=False).agg(   # noqa: E731
        rhs_sum=("rhs_sum", "sum"), rows=("rows", "sum"))
    A, B = merge(A), merge(B)
    A["owner_class"] = A.owner.map(owner_class); B["owner_class"] = B.owner.map(owner_class)
    gone = lambda o: any(c in str(o).split("|") for c in removed)   # noqa: E731
    left = B[B.owner.map(gone)]
    A2 = A[~A.owner.map(gone)].set_index(["family", "owner"]); B2 = B.set_index(["family", "owner"])
    j = A2[["rhs_sum", "rows"]].join(B2[["rhs_sum", "rows"]], how="outer", lsuffix="_full", rsuffix="_variant").fillna(0.0)
    j["rel_dev"] = (j.rhs_sum_variant - j.rhs_sum_full).abs() / j.rhs_sum_full.abs().clip(lower=1e-9)
    diff = j[(j.rel_dev > 1e-9) | (j.rows_full != j.rows_variant)].reset_index()
    rem = A[A.owner.map(gone)].groupby(["family", "owner"], as_index=False).agg(rhs_sum=("rhs_sum", "sum"), rows=("rows", "sum"))
    res = dict(script=SCRIPT, full=str(full), variant=str(variant), removed=removed, rows_naming_removed_country_in_variant=int(len(left)),
               variant_owners_naming_removed=left.to_dict(orient="records")[:50], removed_rights=rem.to_dict(orient="records"),
               remaining_rights_changed=diff.to_dict(orient="records"), remaining_rights_changed_count=int(len(diff)),
               passed=bool(len(left) == 0 and len(diff) == 0))
    (out / "LOO_RHS_CHECK.json").write_text(json.dumps(res, indent=1, default=str))
    return res


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit"); a.add_argument("--repo", type=Path, default=HERE.parent); a.add_argument("--network", type=Path, required=True)
    a.add_argument("--scenario", default="integrated"); a.add_argument("--out", type=Path, required=True); a.add_argument("--truncate", type=int, default=None)
    a.add_argument("--duals", type=Path, default=None); a.add_argument("--solve-dir", type=Path, default=None); a.add_argument("--allocation", type=Path, default=None)
    a.add_argument("--tag", default=""); a.add_argument("--solved", type=Path, default=None, help="solved network: line flows for the KVL loop transfer (with --duals)")
    a.add_argument("--register-dir", type=Path, default=None, help="run dir whose EXPORTS.json gets the outputs")
    lo = sub.add_parser("loo"); lo.add_argument("--full", type=Path, required=True); lo.add_argument("--variant", type=Path, required=True)
    lo.add_argument("--removed", nargs="+", required=True); lo.add_argument("--out", type=Path, required=True)
    x = ap.parse_args()
    if x.cmd == "audit":
        res = audit(x.repo, x.network, x.scenario, x.out, x.truncate, x.duals, x.solve_dir, x.allocation, x.tag, x.solved, x.register_dir)
        print(json.dumps(dict(model=res["model"], owen_premise=res["owen_premise"], seconds=round(res["seconds"]), peak_rss_gib=round(res["peak_rss_gib"], 2),
                              market_minus_dual=(res.get("dual_form") or {}).get("market_minus_dual_eur")), default=str))
    else:
        res = loo_compare(x.full, x.variant, x.removed, x.out)
        print(json.dumps(dict(passed=res["passed"], left=res["rows_naming_removed_country_in_variant"], changed=res["remaining_rights_changed_count"])))


if __name__ == "__main__":
    main()
