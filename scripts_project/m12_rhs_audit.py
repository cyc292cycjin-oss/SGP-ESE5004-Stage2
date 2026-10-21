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

Supplement 01 D1 (item 136): the dual form is the MAIN value of the Owen allocation (OWEN.json / .csv / .md): alpha 0 / 0.5 / 1, the per-player
interval, the length split; the market-settlement form (current ledger) side by side, the difference split into the KVL loop transfer and the
residual (exported arrays: row / column complementarity and stationarity by owner; rows-only duals: KVL from the solved line flows, the rest
is the residual). C1 (c) extended to the dual form; item 138 (M12b) puts its acceptance on the C1 scale: |sum of the 12 players - c(N)| <= 0.01 bn
and every player's residual impact <= max(1 % of the player's reference difference, 0.01 bn) (was: relative 1e-6, residual information only).

    PYTHONHASHSEED=0 python scripts_project/m12_rhs_audit.py audit --repo . --network <unsolved nc> --scenario integrated --out <dir>
        [--truncate N] [--duals <DUALS_BY_CONSTRAINT.nc> | --solve-dir <dir with lp/ and solution/>] [--allocation <ALLOCATION.json>] [--tag T]
    python scripts_project/m12_rhs_audit.py loo --full <dir>/RHS_BY_FAMILY_OWNER.csv --variant <dir>/RHS_BY_FAMILY_OWNER.csv --removed VN --out <dir>
    python scripts_project/m12_rhs_audit.py regrade --owen <OWEN.json> --out <json> [--precision <PRECISION.json>]   (item 138, input unchanged)
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
from m12_allocation import (ALPHA_GRID, BUNKER, COUNTRIES, PLAYERS, SHARED, alpha_interval, bn, c1_thresholds_eur, dual_acceptance, entity_code,   # noqa: E402,F401
                            fold, sha)

SCRIPT = "scripts_project/m12_rhs_audit.py"
OWEN_FILES = ("OWEN.json", "OWEN.csv", "OWEN.md")
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
# Supplement 01 D3 (item 136): the pool surplus of the ASEAN pools' ownerless components (extra-ASEAN imports at fixed prices, pool tanks) stays a
# separately reported residual (option a: KKT-residual size, no right-hand side). RULE: a total cap on extra-ASEAN imports (or any other row
# whose right-hand side belongs to no player) must get an owner BEFORE the run - otherwise its rent falls into SHARED, the 12 players no longer
# sum to c(N) and the audit sets owen_premise.passed = False (OWEN outputs flagged premise_failed, not usable for the allocation).
PROPOSALS = {
    "shared": "右端项不属于任何参与者的行（例如区域外进口总量上限）：按补充 01 D3，必须在运行前确定归属（分到国家，或作为燃料舱参与者的一部分），"
              "否则 Owen 前提不成立（owen_premise.passed = False，OWEN 输出标 premise_failed）。东盟池无主组件（无右端项）的池盈余维持残差单列（D3 方案 a）。",
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
    cross-border FOM ledger) minus PyPSA's constant capital_cost x p_nom of the extendable components (the LP charges p_nom_opt).
    pair_components: the same by "<type>:<component>" for the cross-border (pair-owned) components (length split, supplement 01 D2)."""
    from s4d_ledger import NOM
    out, comp = {}, {}
    for t, nom in NOM.items():
        d = n.df(t)
        if not len(d):
            continue
        c = -(d[nom] * d.capital_cost).where(d[nom + "_extendable"], 0.0)
        if "existing_annual_fixed_om_eur" in d:
            c = c + pd.to_numeric(d.existing_annual_fixed_om_eur, errors="coerce").fillna(0.0)
        ow = O.maps[t].reindex(d.index).fillna(UNRESOLVED)
        for k, v in c.groupby(ow).sum().items():
            out[str(k)] = out.get(str(k), 0.0) + float(v)
        for x in ow.index[ow.str.contains("|", regex=False)]:
            if c[x] != 0:
                comp[f"{t}:{x}"] = (str(ow[x]), comp.get(f"{t}:{x}", ("", 0.0))[1] + float(c[x]))
    for _, r in pd.DataFrame(n.meta.get("existing_cross_border_fom_ledger", [])).iterrows():
        k = str(O.maps[r.component_type][r.component]); out[k] = out.get(k, 0.0) + float(r.annual_fom_eur)
        if "|" in k:
            key = f"{r.component_type}:{r.component}"; comp[key] = (k, comp.get(key, ("", 0.0))[1] + float(r.annual_fom_eur))
    return dict(by_owner=out, total=float(sum(out.values())), pair_components={k: dict(pair=p, eur=v) for k, (p, v) in sorted(comp.items())})


def length_split(tot: dict, pair_comp: dict, shares: pd.DataFrame | None) -> dict:
    """dual form split by in-country length (rule (v), sensitivity of supplement 01 D2): every cross-border component's value (y'b of its
    pair rows + its objective constants) split with its length share (s4d_ledger.load_length_shares; component or its "-reversed" twin;
    missing -> 0.5 as in the ledger); a pair's value not attributable to a component (column-bound terms) split 0.5."""
    sh = {}
    if shares is not None and len(shares):
        for _, r in shares.iterrows():
            sh[f"{r.component_type}:{r.component}"] = {str(r.country_a): float(r.share_a), str(r.country_b): float(r.share_b)}
    raw = {k: v for k, v in tot.items() if "|" not in k}
    done, detail = {}, {}
    for key, v in pair_comp.items():
        pr, a, b = v["pair"], *v["pair"].split("|")
        s = sh.get(key) or (sh.get(key[: -len("-reversed")]) if key.endswith("-reversed") else None)
        sa = float(s[a]) if s and set(s) == {a, b} else 0.5
        raw[a] = raw.get(a, 0.0) + sa * v["eur"]; raw[b] = raw.get(b, 0.0) + (1 - sa) * v["eur"]
        done[pr] = done.get(pr, 0.0) + v["eur"]
        d = detail.setdefault(pr, dict(components=0, with_length_share=0, eur=0.0, first_country_eur=0.0))
        d["components"] += 1; d["with_length_share"] += int(bool(s)); d["eur"] += v["eur"]; d["first_country_eur"] += sa * v["eur"]
    for pr, v in tot.items():
        if "|" in pr:
            rest = v - done.get(pr, 0.0); a, b = pr.split("|")
            raw[a] = raw.get(a, 0.0) + 0.5 * rest; raw[b] = raw.get(b, 0.0) + 0.5 * rest
            detail.setdefault(pr, dict(components=0, with_length_share=0, eur=0.0, first_country_eur=0.0))["not_by_component_eur_split_half"] = rest
    return dict(allocation=fold(raw), by_pair=detail)


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
          solved: Path | None = None, register_dir: Path | None = None, precision: Path | None = None) -> dict:
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
    pair_rows = {}   # "<type>:<component>" -> y'b of its cross-border pair rows
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
            pm = np.array([owner_class(inv[int(c)]) == "cross_border_pair" for c in ocs], dtype=bool)
            cd = [i for i, dd in enumerate(lab.dims) if str(dd).split("-")[0] in COMP_TYPES]
            if pm.any() and cd:   # cross-border rows by component (length split of the dual form, supplement 01 D2)
                ct = str(lab.dims[cd[0]]).split("-")[0]
                names = np.asarray(lab.coords[lab.dims[cd[0]]].values).astype(str)[np.nonzero(nz)[cd[0]]]
                for (nm_, oc_), v_ in pd.DataFrame(dict(n=names[pm], o=ocs[pm], t=t_[pm])).groupby(["n", "o"]).t.sum().items():
                    key = f"{ct}:{nm_}"
                    pair_rows[key] = dict(pair=inv[int(oc_)], eur=pair_rows.get(key, {}).get("eur", 0.0) + float(v_))
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
    from m12_allocation import bunker_standalone
    res["bunker_standalone"] = bunker_standalone(n)   # supplement 01 D10 (arithmetic on the built network: same snapshots and weights as the LP)
    pc_ = res["owen_premise"]["nonzero_rhs_rows_by_class"]
    res["owen_premise"].update(passed=bool(pc_["shared"] == 0 and pc_["unresolved"] == 0),
                               rule="supplement 01 D3: passed = no non-zero right-hand side that is SHARED or unresolved (every right has an owner)")
    if dual_of is not None:
        const = objective_constants(n, O)
        tot = dict(dual_terms)
        for src in (rc_terms, const["by_owner"]):
            for k, v in src.items():
                tot[k] = tot.get(k, 0.0) + v
        ph = fold(tot)
        pairs_ = {k: v for k, v in tot.items() if "|" in k}
        pc = {k: dict(v) for k, v in pair_rows.items()}
        for k, v in const["pair_components"].items():
            pc[k] = dict(pair=v["pair"], eur=pc.get(k, {}).get("eur", 0.0) + v["eur"])
        from s4d_ledger import load_length_shares
        ls = length_split(tot, pc, load_length_shares())
        dual = dict(source=str(solve_dir or duals), rows_by_owner=dual_terms, columns_by_owner=rc_terms, columns=col_info, constants=const, missing_duals=missing_duals,
                    raw_by_owner=tot, allocation_alpha_half=ph, total=float(sum(tot.values())),
                    allocation_by_alpha={f"{al:g}": fold(tot, al) for al in ALPHA_GRID}, pair_values=pairs_,
                    interval=alpha_interval({k: v for k, v in tot.items() if "|" not in k}, pairs_),
                    length_split=ls["allocation"], length_split_by_pair=ls["by_pair"], pair_components=pc,
                    note="Owen dual form: sum of multiplier x active bound by owner (+ column bounds, + objective constants by owner); pairs folded with alpha 0.5")
        A = json.loads(Path(allocation).read_text()) if allocation is not None else None
        if A is not None and not A.get("computable", True):
            A = None
        if A is not None:
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
        rec = json.loads((Path(solve_dir) / "SOLVE_RECEIPT.json").read_text()) if solve_dir is not None and (Path(solve_dir) / "SOLVE_RECEIPT.json").exists() else {}
        obj = A["objective"] if A is not None else rec.get("objective")
        res["owen"] = owen_summary(res, A, solve_dir, None if obj is None else float(obj), precision)
    res["seconds"] = time.time() - t0
    res["peak_rss_gib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2
    (out / "RHS_AUDIT.json").write_text(json.dumps(res, indent=1, default=str))
    if "owen" in res:
        write_owen(res, out)
    if register_dir is not None:   # run pipeline: register the outputs in the run's EXPORTS.json (paths relative to the run dir)
        p = Path(register_dir) / "EXPORTS.json"; ex = json.loads(p.read_text()) if p.exists() else {}
        for f in ("RHS_AUDIT.json", "RHS_FAMILIES.csv", "RHS_BY_FAMILY_OWNER.csv", "RHS_FAMILY_SUMMARY.csv") + OWEN_FILES:
            q = out / f
            if not q.exists():
                continue
            ex[str(q.relative_to(register_dir))] = dict(bytes=q.stat().st_size, sha256=sha(q), source="m12_rhs_audit.py (M12 C2 / Owen dual form, item 133)")
        p.write_text(json.dumps(ex, indent=1))
    return res


# ----------------------------------------------------------------------------------------------------------------------------- Owen outputs (main value)
def reference_of(precision: Path | None) -> tuple[dict, str]:
    """reference of the C1 (b)(c) per-entity thresholds: the run's PRECISION.json (after any regrade), else the L23 default."""
    from s4o_c1_precision import L23_REFERENCE
    p = Path(precision) if precision is not None else None
    ref = (json.loads(p.read_text()).get("reference") or {}) if p is not None and p.exists() else {}
    if ref.get("differences_bn"):
        return ref, f"{p}: {str(ref.get('source', ''))[:120]}"
    return L23_REFERENCE, "L23 default reference (s4o_c1_precision.L23_REFERENCE)"


def owen_summary(res: dict, A: dict | None, solve_dir: Path | None, objective: float | None, precision: Path | None = None) -> dict:
    """Owen allocation with the dual form y'b as the main value (supplement 01 D1). The market-settlement form (ALLOCATION.json, the current
    ledger) is reported next to it; market - dual = KVL loop transfer (zero-sum over the line owners) + residual (KKT residuals of the returned
    solution). C1 (c) extended to the dual form, accepted on the C1 scale (item 138): identity |sum_players phi - c(N)| <= 0.01 bn and every
    player's residual impact <= its C1 (b) per-country threshold."""
    from m12_allocation import _fx, precision_context
    d = res["dual_form"]; by_a = d["allocation_by_alpha"]; main = by_a["0.5"]
    ps = float(sum(main[p] for p in PLAYERS)); sh = float(main.get(SHARED, 0.0))
    ident = dict(objective=objective, players_sum=ps, shared=sh,
                 note="C1 (c) extended to the dual form: sum of the 11 countries + BUNKER (y'b + column bounds + objective constants) = objective; "
                      "accepted within 0.01 bn (item 138), the relative error is information")
    if objective is not None:
        rel = abs(ps - objective) / max(1.0, abs(objective))
        ident.update(difference=ps - objective, relative_error=rel, relative_error_incl_shared=abs(ps + sh - objective) / max(1.0, abs(objective)))
    else:
        ident.update(note="objective unknown (no ALLOCATION.json / SOLVE_RECEIPT.json): identity not checked")
    pp = Path(precision) if precision is not None else (Path(solve_dir) / "PRECISION.json" if solve_dir is not None else None)
    ref, ref_src = reference_of(pp)
    thr = c1_thresholds_eur(ref)   # bunker: the ASEAN entity of C1 (bunker account)
    fx = (A or {}).get("report_currency") or _fx()
    out = dict(main_form="owen_dual_form", decision="supplement 01 D1 (item 136): main value = Owen dual form y'b; market-settlement form reported alongside",
               tag=res.get("tag"), network=res.get("network"), network_sha256=res.get("network_sha256"), duals=d.get("source"), alpha_main=0.5,
               alpha_definition="alpha = share of the FIRST country (alphabetical) of a cross-border pair (row values y'b of the pair rows and the pair's objective constants)",
               allocation_eur=by_a, interval_eur=d["interval"], pair_values_eur=d["pair_values"], fx_per_eur2020=fx["fx_per_eur2020"],
               length_split_eur=d.get("length_split"), length_split_by_pair=d.get("length_split_by_pair"),
               alpha_note="supplement 01 D2: main alpha 0.5 (interior-point centre, same-proportion rule); length split (rule (v)) as sensitivity; full [0, 1] interval",
               allocation_usd2020_alpha_half={p: main.get(p, 0.0) * fx["fx_per_eur2020"] for p in list(PLAYERS) + [SHARED]}, identity=ident)
    prec = precision_context(solve_dir, precision) if (solve_dir is not None or precision is not None) else dict(available=False)
    resid, kvl, parts, diff, unexpl, method = None, None, {}, None, None, "no market-settlement allocation given"
    if A is not None:
        mk = A["allocation_eur"]["0.5"]; ks = list(PLAYERS) + [SHARED]
        diff = {p: float(mk.get(p, 0.0) - main.get(p, 0.0)) for p in ks}
        dec = d.get("decomposition")
        if dec:
            kvl = dec["kvl_alpha_half"]
            parts = dict(row_complementarity_other_families=dec["rows_other_families_alpha_half"], column_complementarity=dec["column_complementarity_alpha_half"],
                         stationarity=dec["stationarity_alpha_half"])
            resid = {p: float(sum(v.get(p, 0.0) for v in parts.values())) for p in ks}
            unexpl = {p: diff[p] - kvl.get(p, 0.0) - resid[p] for p in ks}
            method = "exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)"
        elif d.get("kvl_loop_transfer_alpha_half"):
            kvl = d["kvl_loop_transfer_alpha_half"]; resid = {p: diff[p] - kvl.get(p, 0.0) for p in ks}
            method = "rows-only duals: KVL transfer from the solved line flows (p0; the loss proxy makes p0 differ slightly from the LP variable), residual = difference - KVL"
        else:
            resid = dict(diff); method = "rows-only duals without solved flows: KVL not separated (the residual includes the loop transfer)"
        out["market_form"] = dict(allocation_alpha_half_eur=mk, interval_eur=A.get("interval_eur"), identity=A.get("identity"),
                                  note="market-settlement form = current ledger (s4d_ledger): asset costs + net purchases at the nodal duals - net rent share")
        out["market_minus_dual"] = dict(total_eur=diff, kvl_loop_transfer_eur=kvl, residual_eur=resid, residual_parts_eur=parts, unexplained_eur=unexpl, method=method)
    acc = dual_acceptance(ps, objective, resid, thr)
    ident.update(passed=acc["identity_passed"], tolerance_eur=acc["identity_tolerance_eur"])
    out["dual_acceptance"] = acc
    out["c1_c_dual"] = dict(identity_passed=acc["identity_passed"], residual_passed=acc["residual_passed"], passed=acc["passed"], c1_c_passed=prec.get("c_passed"),
                            precision=prec, threshold_source=ref_src, threshold_eur=thr, residual_impact_eur=resid, within_threshold=acc["residual_within"],
                            note="residual impact = market form - dual form - KVL transfer of the player (KKT residuals of the returned solution); "
                                 "item 138: deciding together with the identity (both on the C1 scale)")
    pr = res.get("owen_premise") or {}
    out["premise"] = dict(passed=pr.get("passed"), nonzero_rhs_rows_by_class=pr.get("nonzero_rhs_rows_by_class"), rule=pr.get("rule"),
                          coupling_families_homogeneous=pr.get("coupling_families_homogeneous"), coupling_families_nonhomogeneous=pr.get("coupling_families_nonhomogeneous"),
                          shared_or_unresolved_rows=res.get("shared_or_unresolved", [])[:20])
    out["premise_failed"] = pr.get("passed") is False
    out["usable_for_allocation"] = bool(acc["passed"] and (prec.get("c_passed") is not False) and not out["premise_failed"])
    bs = res.get("bunker_standalone") or {}
    if bs.get("computable"):   # D10: core condition of the bunker player against its strict standalone cost
        phb = float(main.get(BUNKER, 0.0)); hi = float((d["interval"].get(BUNKER) or {}).get("max", phb))
        out["bunker_standalone"] = dict(strict_standalone_cost_eur=bs["total_eur"], owen_dual_alpha_half_eur=phb, owen_dual_interval_max_eur=hi,
                                        margin_eur=bs["total_eur"] - phb, passed=bool(phb <= bs["total_eur"] + thr[BUNKER]),
                                        passed_at_interval_max=bool(hi <= bs["total_eur"] + thr[BUNKER]), tolerance_eur=thr[BUNKER],
                                        by_bus={b: dict(energy_twh=v.get("energy_twh"), cost_eur=v.get("cost_eur"), chosen=v.get("chosen"),
                                                        unit_cost_min=v.get("unit_cost_min"), unit_cost_max=v.get("unit_cost_max"),
                                                        excluded=[e["meter"] for e in v.get("excluded", [])]) for b, v in bs["by_bus"].items()},
                                        notes=bs.get("notes"), definition=bs.get("definition"),
                                        interpretation="supplement 01 D10: the bunker has no resource and cannot opt out; the core condition is checked against its "
                                                       "strict standalone cost (extra-ASEAN non-fossil imports only). A negative benefit (integrated - disconnected) "
                                                       "is a pecuniary externality of the liquid-fuel pool prices on a pure price taker, not a breach of "
                                                       "individual rationality.")
    else:
        out["bunker_standalone"] = dict(computable=False, reason=bs.get("reason", "not computed"))
    return out


def write_owen(res: dict, out: Path) -> None:
    """OWEN.json / .csv / .md (main value of the Owen allocation)."""
    o = res["owen"]; al = o["allocation_eur"]; it = o["interval_eur"]; md = o.get("market_minus_dual") or {}; mk = (o.get("market_form") or {}).get("allocation_alpha_half_eur") or {}
    c1 = o["c1_c_dual"]
    (out / "OWEN.json").write_text(json.dumps(dict(script=SCRIPT, **o), indent=1, default=str))
    rows = []
    for p in list(PLAYERS) + [SHARED]:
        r = dict(player=p, **{f"owen_dual_alpha_{k}_eur": v.get(p, 0.0) for k, v in al.items()})
        r.update(owen_dual_alpha_0_5_usd2020=o["allocation_usd2020_alpha_half"].get(p), length_split_eur=(o.get("length_split_eur") or {}).get(p),
                 interval_min_eur=(it.get(p) or {}).get("min"), interval_max_eur=(it.get(p) or {}).get("max"),
                 market_form_alpha_0_5_eur=mk.get(p), market_minus_dual_eur=(md.get("total_eur") or {}).get(p), kvl_transfer_eur=(md.get("kvl_loop_transfer_eur") or {}).get(p),
                 residual_eur=(md.get("residual_eur") or {}).get(p), c1_threshold_eur=c1["threshold_eur"].get(p))
        rows.append(r)
    pd.DataFrame(rows).set_index("player").to_csv(out / "OWEN.csv")
    idt = o["identity"]; acc = o.get("dual_acceptance") or {}
    L = ["# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）", ""]
    if o.get("premise_failed"):
        L += [f"> **⚠ premise_failed：存在无主（SHARED）或无法归属的非零右端项（{o['premise']['nonzero_rhs_rows_by_class']}），Owen 前提不成立；"
              "须先确定归属再运行（补充 01 D3），本分摊不可用。**", ""]
    L += [f"- 运行：{o.get('tag')}；网络 `{o.get('network')}`（SHA256 `{str(o.get('network_sha256'))[:12]}…`）；对偶 `{o.get('duals')}`。",
         f"- Owen 前提（右端项全部有主）：**{o['premise']['passed']}**。",
         f"- 恒等式（C1 (c) 对偶形式扩展，第 138 项 C1 同口径）：11 国 + 燃料舱 = {bn(idt['players_sum'])} bn，目标值 {bn(idt.get('objective'))} bn，"
         f"差 {bn(idt.get('difference'))} bn（|差| ≤ 0.01 bn：**{idt['passed']}**；相对误差 {idt.get('relative_error', float('nan')):.2e} 仅供参考）；共享 {bn(idt['shared'])} bn。",
         f"- 残差影响 ≤ C1 (b) 阈值 max(差额 1 %, 0.01 bn)：**{acc.get('residual_passed')}**"
         + (f"（未通过：{', '.join(acc['residual_failed'])}）" if acc.get("residual_failed") else "") + f"；对偶形式验收：**{acc.get('passed')}**。",
         f"- C1 (c)（运行本身）：{c1['c1_c_passed']}；分摊可用：**{o['usable_for_allocation']}**。阈值来源：{c1['threshold_source']}。",
         f"- 差额方法：{md.get('method', '—')}。", "",
         "| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        p = r["player"]
        L.append(f"| {p} | **{bn(r['owen_dual_alpha_0.5_eur'])}** | {bn(r['owen_dual_alpha_0_eur'])} | {bn(r['owen_dual_alpha_1_eur'])} | {bn(r['length_split_eur'])} | {bn(r['interval_min_eur'])} | "
                 f"{bn(r['interval_max_eur'])} | {bn(r['owen_dual_alpha_0_5_usd2020'])} | {bn(r['market_form_alpha_0_5_eur'])} | {bn(r['market_minus_dual_eur'])} | "
                 f"{bn(r['kvl_transfer_eur'])} | {bn(r['residual_eur'])} | {bn(r['c1_threshold_eur'])} |")
    L += ["", "区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。"]
    b = o.get("bunker_standalone") or {}
    if "strict_standalone_cost_eur" in b:
        L += ["", "## 燃料舱参与者：严格单独成本（补充 01 D10）", "",
              f"- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **{bn(b['strict_standalone_cost_eur'])} bn**；"
              f"Owen 对偶形式份额 {bn(b['owen_dual_alpha_half_eur'])} bn；余量 {bn(b['margin_eur'])} bn；份额 ≤ 单独成本：**{b['passed']}**。"]
        L += [f"- {k}：{bn(v['cost_eur'])} bn，{v['energy_twh']:.2f} TWh，单位成本 {v['unit_cost_min']:.2f}–{v['unit_cost_max']:.2f} EUR/MWh，路线 {v['chosen']}；排除 {v['excluded']}"
              for k, v in b["by_bus"].items()]
        L += [f"- {x}" for x in (b.get("notes") or [])]
    (out / "OWEN.md").write_text("\n".join(L) + "\n")


def regrade_owen(owen: Path, out: Path, precision: Path | None = None) -> dict:
    """item 138: re-grade an existing OWEN.json with the C1-scale dual acceptance (the input file is not changed). Thresholds from the given
    PRECISION.json reference, else the ones stored in the file (c1_c_dual.threshold_eur, the reference the audit saw)."""
    o = json.loads(Path(owen).read_text()); idt = o.get("identity") or {}; c1 = o.get("c1_c_dual") or {}
    if precision is not None:
        ref, src = reference_of(Path(precision)); thr = c1_thresholds_eur(ref)
    else:
        thr, src = {p: float(v) for p, v in (c1.get("threshold_eur") or {}).items() if p in PLAYERS}, f"stored in {owen}: {str(c1.get('threshold_source'))[:120]}"
    acc = dual_acceptance(idt.get("players_sum"), idt.get("objective"), c1.get("residual_impact_eur"), thr)
    prem_failed = bool(o.get("premise_failed"))
    res = dict(script=SCRIPT, owen=str(owen), owen_sha256=sha(Path(owen)), tag=o.get("tag"), network=o.get("network"), threshold_source=src,
               old=dict(rule="supplement 01 D1: |sum - c(N)| / c(N) <= 1e-6 (residual information only)", identity_relative_error=idt.get("relative_error"),
                        identity_passed=idt.get("passed"), usable_for_allocation=o.get("usable_for_allocation")),
               new=dict(acc, c1_c_passed=c1.get("c1_c_passed"), premise_failed=prem_failed,
                        usable_for_allocation=bool(acc["passed"] and c1.get("c1_c_passed") is not False and not prem_failed)))
    res["verdict_changed"] = res["old"]["usable_for_allocation"] != res["new"]["usable_for_allocation"]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(res, indent=1, default=str))
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
    a.add_argument("--precision", type=Path, default=None, help="PRECISION.json when it is not in the solve dir (older runs; rows-only duals)")
    lo = sub.add_parser("loo"); lo.add_argument("--full", type=Path, required=True); lo.add_argument("--variant", type=Path, required=True)
    lo.add_argument("--removed", nargs="+", required=True); lo.add_argument("--out", type=Path, required=True)
    g = sub.add_parser("regrade"); g.add_argument("--owen", type=Path, required=True); g.add_argument("--out", type=Path, required=True)
    g.add_argument("--precision", type=Path, default=None, help="PRECISION.json whose reference sets the C1 (b) thresholds (default: the stored ones)")
    x = ap.parse_args()
    if x.cmd == "audit":
        res = audit(x.repo, x.network, x.scenario, x.out, x.truncate, x.duals, x.solve_dir, x.allocation, x.tag, x.solved, x.register_dir, x.precision)
        print(json.dumps(dict(model=res["model"], owen_premise=res["owen_premise"], seconds=round(res["seconds"]), peak_rss_gib=round(res["peak_rss_gib"], 2),
                              market_minus_dual=(res.get("dual_form") or {}).get("market_minus_dual_eur")), default=str))
    elif x.cmd == "regrade":
        res = regrade_owen(x.owen, x.out, x.precision)
        print(json.dumps(dict(old=res["old"]["usable_for_allocation"], new=res["new"]["usable_for_allocation"], identity_passed=res["new"]["identity_passed"],
                              residual_failed=res["new"]["residual_failed"])))
    else:
        res = loo_compare(x.full, x.variant, x.removed, x.out)
        print(json.dumps(dict(passed=res["passed"], left=res["rows_naming_removed_country_in_variant"], changed=res["remaining_rights_changed_count"])))


if __name__ == "__main__":
    main()
