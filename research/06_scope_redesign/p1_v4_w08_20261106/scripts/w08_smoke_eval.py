"""W08 section 5: evaluation of the four 56-snapshot runs against the criteria registered in SMOKE56_V4.md section 1 (no solver).

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_smoke_eval.py

Reads results_project/v4w08/smoke56/<run>/ (SOLVE_RECEIPT.json, V5_GATES.json, PRECISION.json, V6_ACCEPTANCE.json, COUNTRY_COST_LEDGER.csv,
M12_BENEFIT) and evidence/W08_first_order.json; writes tables/W08_SMOKE56_RESULTS.csv, evidence/W08_smoke56.json (licence-free fields only).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
RUN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56")
RUNS = ["v31_F1", "v4_F1", "v4_F2", "v4iid_F1"]
V31_SMOKE = {"F1": 329705565613.54376, "F2": 342268691264.84}   # V3.1 local regression smoke (RUN_PLAN_HPC_V3.md section 15; drill receipts)
V31_B6 = 12563125651.0
UNION = {"A1_A2", "A1_A2_S4B", "A3", "A3_S4B", "B1", "B3", "B8"}   # failed gates of the v3 / v3.1 local smoke (RUN_PLAN_V3.md sections 24-25)


def jl(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def main():
    fo = json.loads((W / "evidence/W08_first_order.json").read_text())["pairs"]
    rows, ev = [], {}
    for rid in RUNS:
        d = RUN / rid
        r = jl(d / "SOLVE_RECEIPT.json")
        if r is None:
            rows.append(dict(run=rid, status="not run")); continue
        g = jl(d / "V5_GATES.json") or {}
        gates = {k: v.get("passed") for k, v in g.items() if isinstance(v, dict) and "passed" in v}
        failed = sorted(k for k, v in gates.items() if v is False)
        p = jl(d / "PRECISION.json") or {}
        v6 = jl(d / "V6_ACCEPTANCE.json") or {}
        bar = " ".join(r.get("gurobi_log_stats", {}).get("lines", {}).get("barrier", []))
        m = re.search(r"in (\d+) iterations and ([0-9.]+) seconds", bar)
        rec = dict(run=rid, network_sha256=r["input_network"]["sha256"], termination=r.get("termination_condition"), status=r.get("status"),
                   objective_eur=r.get("objective"), objective_lp_eur=r.get("objective_lp"), barrier_iterations=int(m.group(1)) if m else None,
                   barrier_seconds=float(m.group(2)) if m else None, solve_seconds=r.get("solve_seconds"), peak_rss_gib=(r.get("peak_rss_bytes") or 0) / 2**30,
                   gates_failed=";".join(failed), gates_failed_outside_v31_union=";".join(sorted(set(failed) - UNION - ({"B12"} if rid == "v31_F1" else set()))),
                   A1_A2=gates.get("A1_A2"), A1_A2_S4B=gates.get("A1_A2_S4B"), B12=gates.get("B12"), B16_LEDGER=gates.get("B16_LEDGER"),
                   C1_a=(p.get("grade") or {}).get("a"), C1_b=(p.get("grade") or {}).get("b"), C1_c=(p.get("grade") or {}).get("c"),
                   C1_accepted=(p.get("acceptance") or {}).get("accepted"), V6_label=v6.get("label"))
        rows.append(rec); ev[rid] = dict(rec, gates=gates)
    R = pd.DataFrame(rows).set_index("run")
    crit = {}
    if "objective_eur" in R.columns and pd.notna(R.at["v31_F1", "objective_eur"]):
        o0 = float(R.at["v31_F1", "objective_eur"])
        crit["R0_vs_v31_smoke_rel"] = o0 / V31_SMOKE["F1"] - 1.0
        crit["R0_within_1e-6"] = abs(crit["R0_vs_v31_smoke_rel"]) <= 1e-6
        for rid, base in (("v4_F1", o0), ("v4_F2", V31_SMOKE["F2"]), ("v4iid_F1", o0)):
            if rid not in R.index or pd.isna(R.at[rid, "objective_eur"]):
                continue
            dlt = float(R.at[rid, "objective_eur"]) - base; f = fo[rid]
            lo, hi = f["band_eur"]
            crit[rid] = dict(delta_vs_v31_eur=dlt, base="R0 (v3.1 F1 rerun)" if base == o0 else "v3.1 F2 local regression smoke (registered)",
                             first_order_eur=f["first_order_delta_eur"], band_eur=[lo, hi], within_band=bool(lo <= dlt <= hi),
                             ratio_to_first_order=dlt / f["first_order_delta_eur"] if f["first_order_delta_eur"] else None,
                             first_order_raw_dual_eur=f["first_order_delta_raw_dual_eur"])
        if {"v4_F1", "v4_F2"} <= set(R.index) and pd.notna(R.at["v4_F2", "objective_eur"]):
            crit["B6_v4_eur"] = float(R.at["v4_F2", "objective_eur"]) - float(R.at["v4_F1", "objective_eur"])
            crit["B6_v31_eur"] = V31_B6
    ben = RUN / "M12_BENEFIT"
    if ben.exists():
        crit["m12_benefit_files"] = sorted(p.name for p in ben.iterdir())[:20]
    out = R.reset_index()
    (W / "tables").mkdir(exist_ok=True)
    out.to_csv(W / "tables/W08_SMOKE56_RESULTS.csv", index=False, float_format="%.12g", lineterminator="\n")
    (W / "evidence/W08_smoke56.json").write_text(json.dumps(dict(runs=ev, criteria=crit), indent=1, default=str) + "\n")
    pd.set_option("display.width", 250)
    print(out.drop(columns=["network_sha256"]).to_string())
    print(json.dumps(crit, indent=1, default=str))


if __name__ == "__main__":
    main()
