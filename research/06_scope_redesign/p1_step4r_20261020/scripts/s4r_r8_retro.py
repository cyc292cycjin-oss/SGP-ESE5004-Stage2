"""S4R R8: retro-evaluation of every historical run under GATES_V6 (definition committed first; this script applies it, read-only,
Python only, from the exported indicator files - no solver, no network reload, no LP rebuild). Runs without the needed export are
marked 'not computable'. Output GATES_RETRO_COMPARISON.csv / .md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4r_paths import OUT, REPO, WORK, dump_json, md_table  # noqa: E402

K = 10.0
RUNS = {
    "L23 integrated": WORK / "p1_l23_run1_20261019/evidence/c9/early/integrated",
    "L23 disconnected": WORK / "p1_l23_run1_20261019/evidence/c9/early/disconnected",
    "L23 disconnected_gap": WORK / "p1_l23_run1_20261019/evidence/c9/early/disconnected_gap",
    "S4M-2 A integrated (56x3h)": REPO / "results_project/s4m/s4m2/solves/s4m_A_integrated",
    "S4M-2 A disconnected (56x3h)": REPO / "results_project/s4m/s4m2/solves/s4m_A_disconnected",
    "S4M-2 A integrated_nze (56x3h)": REPO / "results_project/s4m/s4m2/solves/s4m_A_integrated_nze",
    "S4M-S2 A integrated rerun (56x3h)": REPO / "results_project/s4m/s4ms2/solves/s4m_A_integrated_rerun",
    "S4N pilot integrated (365x24h)": WORK / "p1_step4n_20261019/cloud_results/20261019T072454Z_5125/unpacked/s4n_pilot_light_20261019T072454Z_5125/export_integrated",
    "S4N C2 cal integrated (56x3h, 1e-5 t32)": WORK / "p1_step4n_20261019/evidence/s4n_c2/cal_integrated",
    "S4N C2 cal disconnected (56x3h)": WORK / "p1_step4n_20261019/evidence/s4n_c2/cal_disconnected",
    "S4N C2 cal integrated_nze (56x3h)": WORK / "p1_step4n_20261019/evidence/s4n_c2/cal_integrated_nze",
    "S4O-6 disconnected (365x24h)": WORK / "p1_step4o_20261019/cloud_results/20261019T162951Z_6896/full/unpacked/disconnected",
    "S4O-6 disconnected_gap (365x24h)": WORK / "p1_step4o_20261019/cloud_results/20261019T162951Z_6896/full/unpacked/disconnected_gap",
    "S4O-6 integrated_nze (365x24h)": WORK / "p1_step4o_20261019/cloud_results/20261019T162951Z_6896/full/unpacked/integrated_nze",
    "S4Q T8 integrated (56x3h, 1e-6)": Path("/home/jin/s4q_local/pkg/runs/20261020T001252Z_564/export/integrated"),
    "S4Q T8 disconnected (56x3h, 1e-6)": Path("/home/jin/s4q_local/pkg/runs/20261020T001252Z_564/export/disconnected"),
    "S4Q T8 integrated_nze (56x3h, 1e-6)": Path("/home/jin/s4q_local/pkg/runs/20261020T001252Z_564/export/integrated_nze"),
    "S4Q T16 integrated (56x3h, 1e-6)": Path("/home/jin/s4q_local/pkg/runs/20261020T004641Z_8849/export/integrated"),
    "S4Q T16 disconnected (56x3h, 1e-6)": Path("/home/jin/s4q_local/pkg/runs/20261020T004641Z_8849/export/disconnected"),
    "S4Q T16 integrated_nze (56x3h, 1e-6)": Path("/home/jin/s4q_local/pkg/runs/20261020T004641Z_8849/export/integrated_nze"),
}
PILOT_PRECISION_S4O = WORK / "p1_step4o_20261019/cloud_results/20261019T162951Z_6896/top/pilot_integrated/PRECISION.json"
S4Q_SHADOW = {"S4Q T8": Path("/home/jin/s4q_local/judge_shadow/t8"), "S4Q T16": Path("/home/jin/s4q_local/judge_shadow/t16")}


def jl(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


def first(*paths):
    for p in paths:
        if p and Path(p).exists():
            return Path(p)
    return None


def evaluate(name, d: Path):
    r = {"run": name, "dir": str(d), "exists": d.exists()}
    rec = jl(first(d / "SOLVE_RECEIPT.json"))
    gates = jl(first(d / "V5_GATES.json"))
    kkt = jl(first(d / "kkt_summary.json", d / "v5/kkt_summary.json"))
    prec = jl(first(d / "PRECISION.json"))
    if name.startswith("S4N pilot") and prec is None:
        prec = jl(PILOT_PRECISION_S4O)
    if name.startswith("S4Q") and prec is None:
        key = "S4Q T8" if "T8" in name else "S4Q T16"; sc = name.split()[2]
        prec = jl(S4Q_SHADOW[key] / sc / "PRECISION.json")
    inter = jl(first(d / "INTERIOR_CHECKS.json"))
    # --- profile tolerances
    params = {}
    if rec:
        params = rec.get("solver_parameters") or rec.get("run", {}).get("solver_parameters") or {}
        if not params:
            for k in ("profile_parameters", "gurobi_parameters", "parameters"):
                if isinstance(rec.get(k), dict):
                    params = rec[k]; break
    if not params and prec:
        params = prec.get("solver_parameters", {})
    eb = float(params.get("BarConvTol", 1e-8)); ef = float(params.get("FeasibilityTol", 1e-6)); eo = float(params.get("OptimalityTol", 1e-6))
    ed = max(eo, eb)
    r.update(profile=(rec or {}).get("solver_profile") or (prec or {}).get("solver_profile") or params.get("_profile", ""), barconvtol=eb, feasibilitytol=ef, optimalitytol=eo,
             termination=(rec or {}).get("termination_condition") or (rec or {}).get("run", {}).get("termination_condition") or (prec or {}).get("termination") or "",
             objective=(rec or {}).get("objective") or (rec or {}).get("run", {}).get("objective") or (prec or {}).get("objective"))
    # --- V5 labels
    if gates:
        r["v5_all_passed_solver_tolerances"] = gates.get("all_passed_solver_tolerances")
        r["v5_failed_gates"] = ";".join(k for k, v in gates.items() if isinstance(v, dict) and v.get("passed") is False)
        a = gates.get("A1_A2_S4B", {})
        r["v5_dual_sign_normalized_max"] = a.get("dual_sign_normalized_max"); r["v5_stationarity_normalized_max"] = a.get("stationarity_normalized_max")
        r["v5_row_max_ratio_to_budget"] = a.get("row_max_ratio_to_budget"); r["v5_row_fail_count"] = a.get("row_fail_count"); r["v5_dual_sign_fail_count"] = a.get("dual_sign_fail_count")
        r["v5_relative_gap"] = a.get("relative_gap", (kkt or {}).get("relative_gap")); r["v5_complementarity_over_scale"] = a.get("complementarity_over_scale")
        b16 = gates.get("B16_LEDGER", {}); r["b16_relative_error"] = b16.get("relative_error")
        for g in ("B2", "B14", "B15", "B12", "B1_S4B", "B3_S4B", "A3_S4B", "A5_S4B", "A4"):
            r[f"v5_{g}_passed"] = gates.get(g, {}).get("passed")
    else:
        r["v5_all_passed_solver_tolerances"] = None; r["v5_failed_gates"] = "not computable (no V5_GATES.json)"
    # --- V6 G1 (C1)
    if prec and prec.get("computable", True):
        r["g1a"] = prec.get("a_total_cost", {}).get("passed"); r["g1b"] = prec.get("b_primal_violations", {}).get("passed"); r["g1c"] = prec.get("c_prices", {}).get("passed")
        r["g1a_relative"] = prec.get("a_total_cost", {}).get("returned_relative"); r["g1a_bn"] = prec.get("a_total_cost", {}).get("returned_difference_bn")
        r["g1_reference"] = str(prec.get("reference", {}).get("source", ""))[:80]
    else:
        r["g1a"] = r["g1b"] = r["g1c"] = None; r["g1_reference"] = "not computable (no PRECISION.json)"
    # --- V6 G2 (structural) from exports available
    a4 = (gates or {}).get("A4", {}); r["g2_1_network_identity"] = a4.get("passed") if gates else None
    b12 = (gates or {}).get("B12", {}).get("checks", {}) if gates else {}
    r["g2_2_config_subset_hash"] = "not computable (subset hash not exported; V5 B12 whole-config = %s)" % ((gates or {}).get("B12", {}).get("passed") if gates else None)
    r["g2_3_results_complete"] = bool(rec) and bool(gates) and (kkt is not None)
    # --- V6 diagnostics D2 (dual residual with profile-dependent budget) and D3
    ds = r.get("v5_dual_sign_normalized_max"); st = r.get("v5_stationarity_normalized_max")
    if ds is not None:
        r["d2_dual_sign_ratio_v5_budget"] = ds / (K * eo); r["d2_dual_sign_ratio_v6_budget"] = ds / (K * ed)
        r["d2_stationarity_ratio_v6_budget"] = (st or 0.0) / (K * ed)
        r["d2_within_v6"] = bool(ds <= K * ed and (st or 0.0) <= K * ed)
    else:
        r["d2_within_v6"] = None
    gap = r.get("v5_relative_gap"); r["d3_gap_ratio"] = (gap / (10 * eb)) if gap is not None else None; r["d3_within"] = (gap <= 10 * eb) if gap is not None else None
    rr = r.get("v5_row_max_ratio_to_budget"); r["d1_within"] = (rr <= 1.0) if rr is not None else None
    # D7 / D9 / D10 with tolerance: recompute from gate payloads where values are present
    def tol_check(gate_key, value_key, cap_key):
        g = (gates or {}).get(gate_key)
        if not g:
            return None
        worst = 0.0; n = 0
        items = g.get("terminals") if gate_key == "B14" else (list(g.get("countries", {}).values()) if gate_key == "B2" else g.get("short", []))
        if not isinstance(items, list):
            return None
        for it in items:
            if not isinstance(it, dict):
                continue
            v = it.get(value_key); c = it.get(cap_key)
            if v is None or c is None:
                continue
            n += 1; budget = float(c) * (1 + K * ef) + 1e-3
            worst = max(worst, float(v) / budget if budget else 0.0)
        return dict(items=n, worst_ratio=worst, within=worst <= 1.0)
    for gk, vk, ck, lab in (("B14", "p_nom_opt", "p_nom_max", "d9_terminal"), ("B2", "final_level_t", "cap_t", "d7_storage")):
        t = tol_check(gk, vk, ck)
        r[f"{lab}_within_v6"] = t["within"] if t else None; r[f"{lab}_worst_ratio"] = t["worst_ratio"] if t else None
    r["d10_production_v5_passed"] = r.get("v5_B15_passed")
    # --- V6 label
    if r["g1a"] is None:
        r["v6_label"] = "not computable (C1 missing)"
    else:
        core = bool(r["g1a"]) and bool(r["g1b"]) and (r["g2_1_network_identity"] is not False) and bool(r["g2_3_results_complete"])
        r["v6_label"] = ("ACCEPTED_LAYER2" if (core and bool(r["g1c"])) else "ACCEPTED_LAYER1" if core else "NOT_ACCEPTED") + " (G2.2 pending)"
    return r


def main():
    rows = [evaluate(n, d) for n, d in RUNS.items()]
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "GATES_RETRO_COMPARISON.csv", index=False)
    cols = ["run", "profile", "barconvtol", "termination", "v5_all_passed_solver_tolerances", "v5_failed_gates", "g1a", "g1b", "g1c", "v6_label", "d2_dual_sign_ratio_v5_budget", "d2_dual_sign_ratio_v6_budget", "d2_within_v6", "d3_gap_ratio", "d1_within", "d9_terminal_within_v6", "d7_storage_within_v6"]
    md = ["# R8 历史运行重评：V5 标签 vs GATES_V6（只用已导出指标；G2.2 配置子集哈希未导出 → 全部标 pending；G1 缺 PRECISION 的运行标不可计算）", "",
          md_table(df[cols].fillna("—"), "{:,.3g}"), "",
          "- D2 比值 = 对偶符号误差归一化最大值 / 预算；V5 预算 = 10 × OptimalityTol = 1e-5；V6 预算 = 10 × max(OptimalityTol, BarConvTol)。比值 ≤ 1 为在预算内。",
          "- 未重新加载任何求解后网络、未重建 LP（原则 7）。"]
    (OUT / "GATES_RETRO_COMPARISON.md").write_text("\n".join(md), encoding="utf-8")
    print(df[cols].to_string())


if __name__ == "__main__":
    main()
