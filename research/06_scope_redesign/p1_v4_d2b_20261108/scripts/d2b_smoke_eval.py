"""V4 D2b section 6.2: evaluation of the two 56-snapshot runs against the criteria registered in SMOKE56_D2B.md section 1 (no solver; copy of the D2a
scripts/d2a_smoke_eval.py smoke mode, reference = the D2a smoke runs).

    <env python> scripts/d2b_smoke_eval.py     # v4d2b_F1 / F2 vs the D2a runs and the alarm lines -> tables/D2B_SMOKE56_RESULTS.csv, evidence/D2B_smoke56.json

Reads results_project/v4d2b/smoke56/<run>/ (SOLVE_RECEIPT.json, V5_GATES.json, PRECISION.json, V6_ACCEPTANCE.json), the D2a smoke receipts and
evidence/D2B_BOUNDS_PRE.json. Licence-free fields only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
RP = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
UNION = {"A1_A2", "A1_A2_S4B", "A3", "A3_S4B", "B1", "B3", "B8"}   # failed gates of the v3 / v3.1 local smoke (RUN_PLAN_V3.md sections 24-25), as in D2a
SMOKE = {"v4d2b_F1": ("R1_v4d2b_F1", RP / "v4d2a/smoke56/v4d2a_F1", "integrated"), "v4d2b_F2": ("R2_v4d2b_F2", RP / "v4d2a/smoke56/v4d2a_F2", "no_new_xb")}


def jl(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def run_record(d: Path) -> dict | None:
    r = jl(d / "SOLVE_RECEIPT.json")
    if r is None:
        return None
    g = jl(d / "V5_GATES.json") or {}
    gates = {k: v.get("passed") for k, v in g.items() if isinstance(v, dict) and "passed" in v}
    failed = sorted(k for k, v in gates.items() if v is False)
    p = jl(d / "PRECISION.json") or {}; v6 = jl(d / "V6_ACCEPTANCE.json") or {}
    bar = " ".join(r.get("gurobi_log_stats", {}).get("lines", {}).get("barrier", []))
    m = re.search(r"in (\d+) iterations and ([0-9.]+) seconds", bar)
    return dict(network_sha256=r["input_network"]["sha256"], termination=r.get("termination_condition"), status=r.get("status"), objective_eur=r.get("objective"),
                objective_lp_eur=r.get("objective_lp"), barrier_iterations=int(m.group(1)) if m else None, barrier_seconds=float(m.group(2)) if m else None,
                solve_seconds=r.get("solve_seconds"), peak_rss_gib=(r.get("peak_rss_bytes") or 0) / 2**30, gates_failed=";".join(failed),
                gates_failed_outside_v31_union=";".join(sorted(set(failed) - UNION)), C1_a=(p.get("grade") or {}).get("a"), C1_b=(p.get("grade") or {}).get("b"),
                C1_c=(p.get("grade") or {}).get("c"), C1_accepted=(p.get("acceptance") or {}).get("accepted"), V6_label=v6.get("label"), gates=gates)


def main():
    rows, ev, crit = [], {}, {}
    pre = json.loads((W / "evidence/D2B_BOUNDS_PRE.json").read_text())
    for rid, (key, refdir, sc) in SMOKE.items():
        rec = run_record(RP / "v4d2b/smoke56" / rid)
        if rec is None:
            rows.append(dict(run=rid, status="not run")); continue
        r1 = jl(refdir / "SOLVE_RECEIPT.json"); g1 = jl(refdir / "V5_GATES.json") or {}
        failed1 = sorted(k for k, v in g1.items() if isinstance(v, dict) and v.get("passed") is False)
        dV = float(rec["objective_eur"]) - float(r1["objective"]); b = pre[key]
        rec.update(run=rid, d2a_objective_eur=float(r1["objective"]), dV_eur=dV, dV_lp_eur=float(rec["objective_lp_eur"]) - float(r1["objective_lp"]),
                   rhs_lower_bound_eur=b["rhs_lower_bound_eur"], cost_first_order_upper_bound_eur=b["terms"]["cost_first_order_upper_bound_eur"], alarm_line_eur=b["alarm_line_eur"],
                   above_alarm_line=bool(dV >= b["alarm_line_eur"]), dV_minus_lower_bound_eur=dV - b["rhs_lower_bound_eur"], gates_failed_d2a=";".join(failed1))
        crit[rid] = dict(optimal=rec["termination"] == "optimal", accepted_layer2=rec["V6_label"] == "ACCEPTED_LAYER2",
                         failed_in_v31_union=rec["gates_failed_outside_v31_union"] == "", above_alarm_line=rec["above_alarm_line"])
        crit[rid]["all"] = all(crit[rid].values())
        rows.append({k: v for k, v in rec.items() if k != "gates"}); ev[rid] = rec
    R = pd.DataFrame(rows).set_index("run")
    if {"v4d2b_F1", "v4d2b_F2"} <= set(R.index) and "objective_eur" in R.columns:
        b6 = float(R.at["v4d2b_F2", "objective_eur"]) - float(R.at["v4d2b_F1", "objective_eur"]); b6a = float(R.at["v4d2b_F2", "d2a_objective_eur"]) - float(R.at["v4d2b_F1", "d2a_objective_eur"])
        crit["B6_regression_only"] = dict(d2b_eur=b6, d2a_eur=b6a, change_eur=b6 - b6a)
    (W / "tables").mkdir(exist_ok=True); (W / "evidence").mkdir(exist_ok=True)
    R.reset_index().to_csv(W / "tables/D2B_SMOKE56_RESULTS.csv", index=False, float_format="%.12g", lineterminator="\n")
    (W / "evidence/D2B_smoke56.json").write_text(json.dumps(dict(runs=ev, criteria=crit), indent=1, default=str) + "\n")
    pd.set_option("display.width", 250)
    print(R.drop(columns=[c for c in ("network_sha256",) if c in R.columns]).T.to_string())
    print(json.dumps(crit, indent=1, default=str))


if __name__ == "__main__":
    main()
