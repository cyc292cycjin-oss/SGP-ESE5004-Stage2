"""Review section 2.2 on the 56-snapshot smoke (Gurobi): B16, ledger identity, Owen, GATES_V6, the source link outside every cross-border account; against the one-way smoke. Writes evidence/LEDGER_CHECK_179_SMOKE.json."""
import json
from pathlib import Path
import pandas as pd
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"); R, O = M / "smoke_s4", M / "smoke_s3"
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence")
SRC, LINE = "dedicated plant source", "dedicated plant line"; out = {}
for r in ("integrated", "no_new_xb"):
    d = R / r; o_ = O / r
    g = json.loads((d / "V5_GATES.json").read_text()); g0 = json.loads((o_ / "V5_GATES.json").read_text()); v = json.loads((d / "V6_ACCEPTANCE.json").read_text()); p = json.loads((d / "PRECISION.json").read_text()); p0 = json.loads((o_ / "PRECISION.json").read_text()); w = json.loads((d / "m12_owen/OWEN.json").read_text())
    L = pd.read_csv(d / "COUNTRY_COST_LEDGER_DETAIL.csv"); F = pd.read_csv(d / "cross_border_flows.csv"); A = pd.read_csv(d / "ALLOCATION_LINES.csv"); a = json.loads((d / "m12_owen/RHS_AUDIT.json").read_text()); a0 = json.loads((o_ / "m12_owen/RHS_AUDIT.json").read_text())
    fail = lambda x: sorted(k for k, z in x.items() if isinstance(z, dict) and z.get("passed") is False)
    has = lambda t, s: int(t.astype(str).apply(lambda c: c.str.contains(s, regex=False)).any(axis=1).sum())
    out[r] = dict(b16_relative=p["c_prices"]["b16"]["relative_error"], b16_relative_one_way=p0["c_prices"]["b16"]["relative_error"], b16_passed=p["c_prices"]["b16"]["passed"], c1=dict(a=p["grade"]["a"], b=p["grade"]["b"], c=p["grade"]["c"]), v5_failed=fail(g), v5_failed_one_way=fail(g0), v6_label=v.get("label"), g2={k: (v["G2"].get(k) or {}).get("passed") for k in ("G2_1", "G2_2", "G2_3")}, b11=(g.get("B11") or {}).get("passed"),
                  owen_usable=w.get("usable_for_allocation"), owen_identity_relative=w["identity"]["relative_error"], rhs_rows_by_class=a["owen_premise"]["nonzero_rhs_rows_by_class"], rhs_rows_by_class_one_way=a0["owen_premise"]["nonzero_rhs_rows_by_class"], rhs_premise_passed=a["owen_premise"]["passed"],
                  ledger_rows_source_carrier=has(L, SRC), ledger_rows_plant_line=has(L, LINE), ledger_rows_plant_line_one_way=has(pd.read_csv(o_ / "COUNTRY_COST_LEDGER_DETAIL.csv"), LINE), cross_border_flow_rows_source=has(F, SRC), cross_border_flow_rows_plant_line=has(F, LINE), allocation_rows_source=has(A, SRC), allocation_rows_plant_line=has(A, LINE))
    print(r, json.dumps(out[r], default=str)[:900])
ben = pd.read_csv(R / "M12_BENEFIT/BENEFIT.csv"); out["benefit_sum_bn"] = float(ben.owen_benefit_eur.sum()) / 1e9
x = json.loads((E / "smoke_s4/V3_SMOKE_RESULT.json").read_text()); out["b6_bn"] = (x["no_new_xb"]["objective_eur"] - x["integrated"]["objective_eur"]) / 1e9; print(out["benefit_sum_bn"], out["b6_bn"], {k: x["integrated"].get(k) for k in ("process_seconds", "wall_seconds", "solve_seconds", "ledger_relative_error")}, {k: x["no_new_xb"].get(k) for k in ("process_seconds", "wall_seconds", "solve_seconds", "ledger_relative_error")})
(E / "LEDGER_CHECK_179_SMOKE.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
