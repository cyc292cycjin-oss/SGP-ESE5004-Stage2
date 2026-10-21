"""S4Q-3 (decision 123 point (5); criteria FIXED BEFOREHAND, not adjusted): level-1 verdict of the BarConvTol 1e-6 candidate on two iteration paths
(formal_barrier_1e6 = Threads 8, formal_barrier_1e6_t16 = Threads 16) against profile A (S4M-2, Threads 8), same S4M-1 networks (2920x3h builds,
--truncate 56). READ ONLY: no solver call, the run folders are not changed (C1 is re-graded on SHADOW copies of PRECISION.json / EXPORTS.json).

Per path (both must pass for level 1):
  1. every run optimal (termination recorded) and decision 119 (a)(b)(c) all passed - C1 per-country tolerance of (b)(c) = the S4M-2 56x3h
     "disconnected - integrated" difference by country (s4o_c1_precision.py regrade with that reference);
  2. per scenario against profile A: objective relative difference <= 1e-5; B16 <= 1e-6;
  3. per country the "disconnected - integrated" difference changes by <= max(1 %, 0.01 bn) against profile A (decision-107 implementation
     s4n_c2_compare.py: 11 countries + ASEAN_BUNKER; ASEAN_POOL reported alongside);
  4. NZE country settlement totals (every ledger entity, total) change by <= max(1 %, 0.01 bn) against profile A NZE.
Information only: iterations, barrier seconds, work units and their ratios to profile A; relative gap; nodal prices (AC, H2, gas, solid biomass);
country CO2 shadow prices; BN / SG / VN biomass shadow prices (all from s4n_c2_compare.py); the differences between the two paths.

    PYTHONHASHSEED=0 python s4q_judge.py --repo <code> --s4m2 <S4M-2 solves> --builds <S4M-1 builds> --ref-duals-integrated <S4M-S2 re-run folder>
        --path t8=<run folder> --path t16=<run folder> --shadow <dir> --out <dir>
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

SCEN = ("integrated", "disconnected", "integrated_nze")
LEDGER_ENTITIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "ASEAN_BUNKER", "ASEAN_POOL")
STD = dict(objective_rel_tol=1e-5, b16_tol=1e-6, pct=0.01, floor_bn=0.01, source="S4Q-3 = decision 123 point (5), fixed beforehand (not adjusted)")
PROFILE_OF = dict(t8="formal_barrier_1e6", t16="formal_barrier_1e6_t16")


def jl(p: Path) -> dict:
    return json.loads(p.read_text()) if p.exists() else {}


def tol(ref_bn: float) -> float:
    return max(STD["pct"] * abs(ref_bn), STD["floor_bn"])


def ledger(d: Path) -> pd.Series:
    t = pd.read_csv(d / "COUNTRY_COST_LEDGER.csv", index_col=0)["total"] / 1e9
    return t.reindex(list(LEDGER_ENTITIES))


def s4m2_reference(C1, s4m2: Path) -> dict:
    r = C1.reference_from_ledgers(s4m2 / "s4m_A_integrated", s4m2 / "s4m_A_disconnected")
    r["source"] = ("S4M-2 56x3h profile A (Threads 8): disconnected - integrated ledger difference (s4m_A_disconnected minus s4m_A_integrated, "
                   "COUNTRY_COST_LEDGER.csv total) - S4Q-3 fixed reference of the C1 (b)(c) per-country tolerance")
    return r


def c1_on_shadow(C1, run: Path, shadow: Path, ref: dict) -> dict:
    """copy PRECISION.json (+ EXPORTS.json) to the shadow folder and re-grade there with the S4M-2 reference; the run folder is not changed."""
    shadow.mkdir(parents=True, exist_ok=True)
    for f in ("PRECISION.json", "EXPORTS.json"):
        if (run / f).exists():
            shutil.copy2(run / f, shadow / f)
    pipe = jl(run / "PRECISION.json")
    if not pipe:
        return dict(available=False)
    res = C1.regrade(shadow, ref)
    a_ = res.get("a_total_cost") or {}; b_ = res.get("b_primal_violations") or {}; c_ = res.get("c_prices") or {}
    worst = lambda chk, key: max(((c, v[key] / v["threshold_bn"]) for c, v in (chk or {}).items()), key=lambda t: t[1], default=(None, None))
    return dict(available=True, computable=res.get("computable", True), termination=res.get("termination"),
                pipeline_grade=(pipe.get("grade") or {}).get("grade"), pipeline_abc=[(pipe.get("grade") or {}).get(k) for k in "abc"],
                pipeline_reference=((pipe.get("reference") or {}).get("source") or "")[:80],
                grade=res["grade"], acceptance=res["acceptance"],
                a_returned_difference_bn=a_.get("returned_difference_bn"), a_returned_relative=a_.get("returned_relative"), a_basis=a_.get("basis"),
                a_log_returned_iteration=(a_.get("returned_iteration_by_log") or {}).get("iteration"), a_log_relative=(a_.get("returned_iteration_by_log") or {}).get("relative_difference"),
                b_rows_over_budget=b_.get("rows_over_budget"), b_first_order_cost_eur=b_.get("first_order_cost_eur_all_rows"),
                b_worst_country=worst(b_.get("country_check"), "first_order_cost_bn"), b_biomass_BN_SG_VN_dominant=(b_.get("biomass_pools_BN_SG_VN") or {}).get("dominant"),
                c_b16=(c_.get("b16") or {}).get("relative_error"), c_worst_country_S_plus_R=worst(c_.get("country_check"), "S_plus_R_bn"),
                gates_information=res.get("gates_information"))


def compare(tool: Path, repo: Path, s4m2: Path, run: Path, builds: Path, ref_duals: Path, out: Path, tag: str) -> dict:
    env = dict(os.environ, PYTHONHASHSEED="0"); env.pop("GRB_LICENSE_FILE", None)
    oj, om = out / f"COMPARE_{tag}_VS_S4M2.json", out / f"COMPARE_{tag}_VS_S4M2.md"
    cmd = [sys.executable, str(tool), "--repo", str(repo), "--ref", str(s4m2), "--cal", str(run), "--cal-tag", "", "--builds", str(builds),
           "--ref-duals-integrated", str(ref_duals), "--out-json", str(oj), "--out-md", str(om)]
    p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"s4n_c2_compare.py failed for {tag}: {p.stderr[-2000:]}")
    return json.loads(oj.read_text())


def consistency(run: Path, s4m2: Path, cfg_profiles: dict, prof: str) -> dict:
    out = {}
    for sc in SCEN:
        r, a = jl(run / sc / "SOLVE_RECEIPT.json"), jl(s4m2 / f"s4m_A_{sc}" / "SOLVE_RECEIPT.json")
        ri, ai = r.get("input_network") or {}, a.get("input_network") or {}
        par = {k: v for k, v in (r.get("solver_parameters") or {}).items() if k != "TimeLimit"}
        out[sc] = dict(network_sha256=ri.get("sha256"), same_network_as_S4M2=bool(ri.get("sha256") and ri.get("sha256") == ai.get("sha256")),
                       truncated_to=ri.get("truncated_to"), s4m2_truncated_to=ai.get("truncated_to"), solver_profile=r.get("solver_profile"),
                       parameters_equal_profile=bool(r.get("solver_profile") == prof and par == cfg_profiles[prof]),
                       time_limit=(r.get("solver_parameters") or {}).get("TimeLimit"), s4m2_time_limit=(a.get("solver_parameters") or {}).get("TimeLimit"),
                       retry=r.get("retry"), optimize_calls=r.get("optimize_calls"))
    return out


def judge_path(tag: str, run: Path, cmp_: dict, c1: dict, s4m2: Path) -> dict:
    runs = cmp_["runs"]
    k1 = {sc: dict(termination=runs[f"cal_{sc}"]["termination"], optimal=runs[f"cal_{sc}"]["termination"] == "optimal",
                   a=c1[sc]["acceptance"]["a"] if c1[sc].get("available") else False, b=c1[sc]["acceptance"]["b"] if c1[sc].get("available") else False,
                   c=c1[sc]["acceptance"]["c"] if c1[sc].get("available") else False) for sc in SCEN}
    for v in k1.values():
        v["passed"] = bool(v["optimal"] and v["a"] and v["b"] and v["c"])
    k2 = {sc: dict(objective_rel_diff=cmp_["objective_rel_diff"][sc], objective_signed_rel_diff=(runs[f"cal_{sc}"]["objective"] / runs[f"ref_{sc}"]["objective"] - 1),
                   objective_abs_diff_bn=(runs[f"cal_{sc}"]["objective"] - runs[f"ref_{sc}"]["objective"]) / 1e9, b16=cmp_["b16_cal"][sc]) for sc in SCEN}
    for v in k2.values():
        v["passed"] = bool(v["objective_rel_diff"] is not None and v["objective_rel_diff"] <= STD["objective_rel_tol"] and v["b16"] is not None and v["b16"] <= STD["b16_tol"])
    k3 = dict(cmp_["country_differences"])
    li_r, ld_r, li_c, ld_c = (ledger(d) for d in (s4m2 / "s4m_A_integrated", s4m2 / "s4m_A_disconnected", run / "integrated", run / "disconnected"))
    dr, dc = float(ld_r["ASEAN_POOL"] - li_r["ASEAN_POOL"]), float(ld_c["ASEAN_POOL"] - li_c["ASEAN_POOL"])
    pool = dict(ref_diff_bn=dr, cal_diff_bn=dc, change_bn=dc - dr, tolerance_bn=tol(dr), within=bool(abs(dc - dr) <= tol(dr)), note="information (not in the decision-107 entity set)")
    ln_r, ln_c = ledger(s4m2 / "s4m_A_integrated_nze"), ledger(run / "integrated_nze")
    k4 = {e: dict(ref_total_bn=float(ln_r[e]), cal_total_bn=float(ln_c[e]), change_bn=float(ln_c[e] - ln_r[e]), tolerance_bn=tol(float(ln_r[e])),
                  within=bool(abs(ln_c[e] - ln_r[e]) <= tol(float(ln_r[e])))) for e in LEDGER_ENTITIES}
    crit = dict(c1_optimal_and_c1_abc=bool(all(v["passed"] for v in k1.values())), c2_objective_and_b16=bool(all(v["passed"] for v in k2.values())),
                c3_country_differences=bool(all(v["within"] for v in k3.values())), c4_nze_entity_totals=bool(all(v["within"] for v in k4.values())))
    crit["path_passed"] = bool(all(crit.values()))
    eff = {}
    for sc in SCEN:
        r, a = runs[f"cal_{sc}"], runs[f"ref_{sc}"]
        ratio = lambda k: (r.get(k) / a.get(k)) if (r.get(k) is not None and a.get(k)) else None
        kkt = jl(run / sc / "v5" / "kkt_summary.json")
        eff[sc] = dict(iterations=r.get("barrier_iterations"), barrier_seconds=r.get("barrier_seconds"), work_units=r.get("barrier_work_units"), solve_seconds=r.get("solve_seconds"),
                       peak_rss_gib=r.get("peak_rss_gib"), ref_iterations=a.get("barrier_iterations"), ref_barrier_seconds=a.get("barrier_seconds"), ref_work_units=a.get("barrier_work_units"),
                       ratio_iterations=ratio("barrier_iterations"), ratio_barrier_seconds=ratio("barrier_seconds"), ratio_work_units=ratio("barrier_work_units"),
                       kkt_relative_gap=kkt.get("relative_gap"), kkt_absolute_gap_eur=kkt.get("absolute_gap"),
                       gates_all_passed_excl_B12=r.get("all_passed_solver_tolerances_excl_B12"), gates_failed_excl_B12=r.get("failed_gates_excluding_B12"))
    return dict(run_folder=str(run), criteria=crit, criterion_1=k1, criterion_2=k2, criterion_3=k3, criterion_3_asean_pool_information=pool, criterion_4=k4,
                c1_s4m2_reference=c1, efficiency_information=eff, information=cmp_.get("information"), B6_bn_eur=cmp_.get("B6_bn_eur"),
                nze_minus_integrated_bn_eur=cmp_.get("nze_minus_integrated_bn_eur"))


def between_paths(P: dict, paths: dict) -> dict:
    """information: path 2 (t16) - path 1 (t8)."""
    a, b = P["t8"], P["t16"]; ra, rb = Path(paths["t8"]), Path(paths["t16"])
    obj = {sc: dict(t8=a["criterion_2"][sc]["objective_abs_diff_bn"], t16=b["criterion_2"][sc]["objective_abs_diff_bn"]) for sc in SCEN}
    out = dict(objective={}, country_difference_t16_minus_t8_bn={}, nze_entity_total_t16_minus_t8_bn={})
    for sc in SCEN:
        oa, ob = jl(ra / sc / "SOLVE_RECEIPT.json").get("objective"), jl(rb / sc / "SOLVE_RECEIPT.json").get("objective")
        out["objective"][sc] = dict(t8=oa, t16=ob, rel_diff_t16_vs_t8=((ob / oa - 1) if (oa and ob) else None), abs_diff_bn=((ob - oa) / 1e9 if (oa and ob) else None),
                                    vs_A_bn=obj[sc])
    for e in LEDGER_ENTITIES:
        da = float(ledger(ra / "disconnected")[e] - ledger(ra / "integrated")[e]); db = float(ledger(rb / "disconnected")[e] - ledger(rb / "integrated")[e])
        out["country_difference_t16_minus_t8_bn"][e] = dict(t8=da, t16=db, diff=db - da)
        out["nze_entity_total_t16_minus_t8_bn"][e] = float(ledger(rb / "integrated_nze")[e] - ledger(ra / "integrated_nze")[e])
    return out


def markdown(R: dict) -> str:
    L = ["# S4Q-3 判定（第 123 项第 (5) 点；事先固定，未调整）", "",
         f"- 参照：S4M-2 档案 A（Threads 8）三次运行；C1 (b)(c) 分国参照 = S4M-2 56×3h \"不互联 − 一体化\"差额（影子目录重评，运行目录未改）。",
         f"- **第一级：{'通过' if R['level1_passed'] else '不通过'}**（Threads 8 路径 {R['paths']['t8']['criteria']['path_passed']}，Threads 16 路径 {R['paths']['t16']['criteria']['path_passed']}）", ""]
    for tag in ("t8", "t16"):
        p = R["paths"][tag]; c = p["criteria"]
        L += [f"## 路径 {tag}（`{PROFILE_OF[tag]}`）", "",
              f"判据：1 {c['c1_optimal_and_c1_abc']}；2 {c['c2_objective_and_b16']}；3 {c['c3_country_differences']}；4 {c['c4_nze_entity_totals']} → **{c['path_passed']}**", "",
              "| 情景 | 终止 | C1 (a)(b)(c) | 目标相对差 | 目标差 bn | B16 | 迭代（A） | barrier s（A） | WU（A） | WU 比 | KKT 相对间隙 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for sc in SCEN:
            k1, k2, e = p["criterion_1"][sc], p["criterion_2"][sc], p["efficiency_information"][sc]
            L.append(f"| {sc} | {k1['termination']} | {int(k1['a'])}{int(k1['b'])}{int(k1['c'])} | {k2['objective_signed_rel_diff']:+.2e} | {k2['objective_abs_diff_bn']:+.5f} | {k2['b16']:.1e} | "
                     f"{e['iterations']}（{e['ref_iterations']}） | {e['barrier_seconds']}（{e['ref_barrier_seconds']}） | {e['work_units']}（{e['ref_work_units']}） | "
                     f"{(e['ratio_work_units'] or float('nan')):.3f} | {(e['kkt_relative_gap'] or float('nan')):.2e} |")
        L += ["", "| 实体 | 判据 3：A 差额 bn | 本路径差额 bn | 变化 bn | 容差 bn | 通过 | 判据 4：NZE A total bn | 本路径 bn | 变化 bn | 容差 bn | 通过 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for e in LEDGER_ENTITIES:
            v3 = p["criterion_3"].get(e) or (p["criterion_3_asean_pool_information"] if e == "ASEAN_POOL" else None); v4 = p["criterion_4"][e]
            s3 = (f"{v3['ref_diff_bn']:.4f} | {v3['cal_diff_bn']:.4f} | {v3['change_bn']:+.5f} | {v3['tolerance_bn']:.4f} | {v3['within']}{'（信息）' if e == 'ASEAN_POOL' else ''}") if v3 else "— | — | — | — | —"
            L.append(f"| {e} | {s3} | {v4['ref_total_bn']:.4f} | {v4['cal_total_bn']:.4f} | {v4['change_bn']:+.5f} | {v4['tolerance_bn']:.4f} | {v4['within']} |")
        L += ["", "C1（S4M-2 参照）：" + "；".join(f"{sc} (a) {v['a_returned_difference_bn']:+.5f} bn / {v['a_returned_relative']:.2e}，(b) 最差 {v['b_worst_country'][0]} {v['b_worst_country'][1]:.1%}，(c) B16 {v['c_b16']:.1e}、最差 {v['c_worst_country_S_plus_R'][0]} {v['c_worst_country_S_plus_R'][1]:.1%} → {v['grade']['grade']}"
                                          for sc, v in p["c1_s4m2_reference"].items() if v.get("available") and v.get("computable", True)), ""]
    bp = R["between_paths"]
    L += ["## 两种路径之间（只作信息，t16 − t8）", "", "| 情景 | 目标 t8 | 目标 t16 | 相对差 | 差 bn |", "|---|---|---|---|---|"]
    L += [f"| {sc} | {v['t8']} | {v['t16']} | {v['rel_diff_t16_vs_t8']:+.2e} | {v['abs_diff_bn']:+.5f} |" for sc, v in bp["objective"].items()]
    L += ["", "每国差额（不互联 − 一体化）t16 − t8（bn）：" + "，".join(f"{e} {v['diff']:+.5f}" for e, v in bp["country_difference_t16_minus_t8_bn"].items()), ""]
    return "\n".join(L) + "\n"


def main():
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser()
    for k in ("repo", "s4m2", "builds", "ref-duals-integrated", "shadow", "out"):
        ap.add_argument("--" + k, type=Path, required=True)
    ap.add_argument("--path", action="append", required=True, help="t8=<run folder> / t16=<run folder>")
    ap.add_argument("--compare-tool", type=Path, default=None)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import s4o_c1_precision as C1
    paths = dict(p.split("=", 1) for p in a.path)
    assert set(paths) == {"t8", "t16"}, paths
    tool = a.compare_tool or (a.repo / "research/06_scope_redesign/p1_step4n_20261019/scripts/s4n_c2_compare.py")
    a.out.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((a.repo / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"]
    ref = s4m2_reference(C1, a.s4m2); (a.out / "S4M2_C1_REFERENCE.json").write_text(json.dumps(ref, indent=1))
    R = dict(standard=STD, c1_reference=ref, profiles={t: dict(name=PROFILE_OF[t], parameters=cfg[PROFILE_OF[t]]) for t in paths}, profile_A=cfg["formal_barrier"], paths={}, consistency={})
    for tag, run in paths.items():
        run = Path(run)
        c1 = {sc: c1_on_shadow(C1, run / sc, a.shadow / tag / sc, ref) for sc in SCEN}
        cmp_ = compare(tool, a.repo, a.s4m2, run, a.builds, a.ref_duals_integrated, a.out, tag)
        R["paths"][tag] = judge_path(tag, run, cmp_, c1, a.s4m2)
        R["consistency"][tag] = consistency(run, a.s4m2, cfg, PROFILE_OF[tag])
    R["between_paths"] = between_paths(R["paths"], paths)
    R["level1_passed"] = bool(all(R["paths"][t]["criteria"]["path_passed"] for t in ("t8", "t16")))
    (a.out / "S4Q3_JUDGE.json").write_text(json.dumps(R, indent=1, default=lambda o: o.item() if isinstance(o, np.generic) else str(o)))
    (a.out / "S4Q3_JUDGE.md").write_text(markdown(R))
    print(json.dumps(dict(level1_passed=R["level1_passed"], criteria={t: R["paths"][t]["criteria"] for t in R["paths"]}), default=str))


if __name__ == "__main__":
    main()
