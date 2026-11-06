"""V4 D1 section 7.3: evaluation of the two 56-snapshot runs against the criteria registered in SMOKE56_D1.md section 1 (no solver).

    <env python> scripts/d1_smoke_eval.py

Reads results_project/v4d1/smoke56/<run>/ (SOLVE_RECEIPT.json, V5_GATES.json, PRECISION.json, V6_ACCEPTANCE.json) and the W08 smoke receipts and solved
networks (trunk Store dispatch for the realised change), evidence/D1_BOUNDS_PRE.json; writes tables/D1_SMOKE56_RESULTS.csv, evidence/D1_smoke56.json
(licence-free fields only).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
RUN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d1/smoke56")
W08 = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56")
RUNS = {"v4d1_F1": ("R1_v4d1_F1", "v4_F1", "integrated"), "v4d1_F2": ("R2_v4d1_F2", "v4_F2", "no_new_xb")}
UNION = {"A1_A2", "A1_A2_S4B", "A3", "A3_S4B", "B1", "B3", "B8"}   # failed gates of the v3 / v3.1 local smoke (RUN_PLAN_V3.md sections 24-25)
TRUNK = [f"{c} biomass oil_palm_trunk" for c in ("ID", "KH", "MY", "PH", "TH")]


def jl(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def trunk_energy(net: Path) -> dict:
    import pypsa
    n = pypsa.Network(str(net)); w = n.snapshot_weightings.objective
    return {s: float((n.stores_t.p[s] * w).sum()) for s in TRUNK}


def main():
    pre = json.loads((W / "evidence/D1_BOUNDS_PRE.json").read_text())
    rows, ev, crit = [], {}, {}
    for rid, (key, w08, sc) in RUNS.items():
        d = RUN / rid
        r = jl(d / "SOLVE_RECEIPT.json")
        if r is None:
            rows.append(dict(run=rid, status="not run")); continue
        g = jl(d / "V5_GATES.json") or {}
        gates = {k: v.get("passed") for k, v in g.items() if isinstance(v, dict) and "passed" in v}
        failed = sorted(k for k, v in gates.items() if v is False)
        p = jl(d / "PRECISION.json") or {}
        v6 = jl(d / "V6_ACCEPTANCE.json") or {}
        r8 = jl(W08 / w08 / "SOLVE_RECEIPT.json")
        g8 = jl(W08 / w08 / "V5_GATES.json") or {}
        failed8 = sorted(k for k, v in g8.items() if isinstance(v, dict) and v.get("passed") is False)
        bar = " ".join(r.get("gurobi_log_stats", {}).get("lines", {}).get("barrier", []))
        m = re.search(r"in (\d+) iterations and ([0-9.]+) seconds", bar)
        dV = float(r["objective"]) - float(r8["objective"])
        b = pre[key]; lo, hi = b["registered_interval_eur"]
        solved = next(iter(sorted(d.glob("*_SMOKE_TEST_ONLY_solved.nc"))), None)
        te = trunk_energy(solved) if solved else {}
        rec = dict(run=rid, network_sha256=r["input_network"]["sha256"], termination=r.get("termination_condition"), status=r.get("status"),
                   objective_eur=r.get("objective"), objective_lp_eur=r.get("objective_lp"), w08_objective_eur=r8["objective"], dV_eur=dV,
                   dV_lp_eur=float(r["objective_lp"]) - float(r8["objective_lp"]), upper_bound_eur=b["upper_bound_eur"], registered_low_eur=lo, registered_high_eur=hi,
                   within_registered=bool(lo <= dV <= hi), dV_over_upper=dV / b["upper_bound_eur"],
                   trunk_energy_d1_mwh=sum(te.values()) if te else None, trunk_energy_w08_mwh=sum(b["trunk_energy_weighted_mwh"].values()),
                   barrier_iterations=int(m.group(1)) if m else None, barrier_seconds=float(m.group(2)) if m else None, solve_seconds=r.get("solve_seconds"),
                   peak_rss_gib=(r.get("peak_rss_bytes") or 0) / 2**30, gates_failed=";".join(failed), gates_failed_w08=";".join(failed8),
                   gates_failed_outside_v31_union=";".join(sorted(set(failed) - UNION)), C1_a=(p.get("grade") or {}).get("a"), C1_b=(p.get("grade") or {}).get("b"),
                   C1_c=(p.get("grade") or {}).get("c"), C1_accepted=(p.get("acceptance") or {}).get("accepted"), V6_label=v6.get("label"))
        rows.append(rec); ev[rid] = dict(rec, gates=gates, trunk_energy_by_store_mwh=te)
        crit[rid] = dict(optimal=r.get("termination_condition") == "optimal", accepted_layer2=v6.get("label") == "ACCEPTED_LAYER2",
                         failed_in_v31_union=not (set(failed) - UNION), dV_in_registered_interval=bool(lo <= dV <= hi))
        crit[rid]["all"] = all(crit[rid].values())
    R = pd.DataFrame(rows).set_index("run")
    if {"v4d1_F1", "v4d1_F2"} <= set(R.index) and "objective_eur" in R.columns:
        b6 = float(R.at["v4d1_F2", "objective_eur"]) - float(R.at["v4d1_F1", "objective_eur"])
        b6w = float(R.at["v4d1_F2", "w08_objective_eur"]) - float(R.at["v4d1_F1", "w08_objective_eur"])
        crit["B6_regression_only"] = dict(d1_eur=b6, w08_eur=b6w, change_eur=b6 - b6w)
    out = R.reset_index()
    (W / "tables").mkdir(exist_ok=True)
    out.to_csv(W / "tables/D1_SMOKE56_RESULTS.csv", index=False, float_format="%.12g", lineterminator="\n")
    (W / "evidence/D1_smoke56.json").write_text(json.dumps(dict(runs=ev, criteria=crit), indent=1, default=str) + "\n")
    pd.set_option("display.width", 250)
    print(out.drop(columns=["network_sha256"]).T.to_string())
    print(json.dumps(crit, indent=1, default=str))


if __name__ == "__main__":
    main()
