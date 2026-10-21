"""M08b supplement 01: details of the second smoke for the report (read-only, from the copied evidence)."""
import json
from pathlib import Path

E = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021/evidence/smoke_s01")
res = json.loads((E / "M08B_SMOKE_RESULT.json").read_text())
for sc in ("integrated", "disconnected"):
    rec = json.loads((E / sc / "SOLVE_RECEIPT.json").read_text()); v6 = json.loads((E / sc / "V6_ACCEPTANCE.json").read_text())
    prec = json.loads((E / sc / "PRECISION.json").read_text()); r = res[sc]
    lp = rec.get("lp") or {}
    diag = v6.get("diagnostics") or {}
    within = {k: (v.get("within_budget") if isinstance(v, dict) else v) for k, v in diag.items()} if isinstance(diag, dict) else diag
    print(sc, dict(cond=r["termination_condition"], solve_s=round(r["solve_seconds"], 1), peak_gib=round(r["peak_rss_gib"], 2), lp=(lp.get("num_col"), lp.get("num_row")),
                   objective_bn=round(r["objective_eur"] / 1e9, 3), c1_grade=r["c1_grade"], c1_accepted=r["c1_accepted"],
                   a_rel=(prec.get("a_total_cost") or {}).get("returned_relative"), a_b_c=[(prec.get(k) or {}).get("passed") for k in ("a_total_cost", "b_primal_violations", "c_prices")],
                   g2={k: v.get("passed") for k, v in v6["G2"].items()}, g21_equal=v6["G2"]["G2_1"]["sha256_equal"], readback=v6["G2"]["G2_1"]["readback"],
                   lng_gw=round(r["lng_p_nom_opt_gw"], 1), lng_n=r["lng_terminals"], ov=r["methane_overflow_loads"], missing=r["report_files_missing"], truncated=r["truncated_to"]))
    print(" diag:", within if len(str(within)) < 1500 else str(within)[:1500])
print("B6", res["B6"]["b6_bn_eur"], "rel", res["B6"]["b6_eur"] / res["integrated"]["objective_eur"], res["B6"]["gate"].get("passed") if isinstance(res["B6"]["gate"], dict) else res["B6"]["gate"])
