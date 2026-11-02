"""Review section 2.2 read-out on the HiGHS path check (8 snapshots: no economic reading): B16, country ledger, Owen, GATES_V6 close on the new structure; the source link is LA and outside every cross-border account. Against path_check4 (same check on the networks of supplement 04). Writes evidence/LEDGER_CHECK_180.json."""
import json
from pathlib import Path
import pandas as pd
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"); R, O = M / "path_check6", M / "path_check5"
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence")
SRC, LINE = "dedicated plant source", "dedicated plant line"; out = {}
ben = pd.read_csv(R / "M12_BENEFIT/BENEFIT.csv"); old = pd.read_csv(O / "M12_BENEFIT/BENEFIT.csv")
for r in ("integrated", "no_new_xb"):
    d = R / r; o_ = O / r
    g = json.loads((d / "V5_GATES.json").read_text()); g0 = json.loads((o_ / "V5_GATES.json").read_text()); v = json.loads((d / "V6_ACCEPTANCE.json").read_text()); p = json.loads((d / "PRECISION.json").read_text()); p0 = json.loads((o_ / "PRECISION.json").read_text()); w = json.loads((d / "m12_owen/OWEN.json").read_text()); w0 = json.loads((o_ / "m12_owen/OWEN.json").read_text())
    led = json.loads((d / "LEDGER_IDENTITY.json").read_text()); L = pd.read_csv(d / "COUNTRY_COST_LEDGER_DETAIL.csv"); F = pd.read_csv(d / "cross_border_flows.csv"); A = pd.read_csv(d / "ALLOCATION_LINES.csv")
    fail = lambda x: sorted(k for k, z in x.items() if isinstance(z, dict) and z.get("passed") is False)
    has = lambda t, s: int(t.astype(str).apply(lambda c: c.str.contains(s, regex=False)).any(axis=1).sum())
    if r == "integrated":
        print("owen keys", sorted(w)[:30]); print("ledger keys", sorted(led)[:20]); print("detail cols", list(L.columns))
    out[r] = dict(objective_eur=p.get("a_total_cost", {}).get("objective") if isinstance(p.get("a_total_cost"), dict) else None,
                  b16_relative=(p.get("c_prices") or {}).get("b16", {}).get("relative_error"), b16_relative_previous=(p0.get("c_prices") or {}).get("b16", {}).get("relative_error"), b16_passed=(p.get("c_prices") or {}).get("b16", {}).get("passed"),
                  ledger_identity={k: led.get(k) for k in ("relative_error", "difference", "passed") if k in led},
                  v5_failed=fail(g), v5_failed_previous=fail(g0), new_failures=sorted(set(fail(g)) - set(fail(g0))), b5=(g.get("B5") or {}).get("passed"), b13=(g.get("B13") or {}).get("passed"), b11=(g.get("B11") or {}).get("passed"), b12=(g.get("B12") or {}).get("passed"),
                  v6_label=v.get("label"), g2={k: (v["G2"].get(k) or {}).get("passed") for k in ("G2_1", "G2_2", "G2_3")},
                  owen_usable=w.get("usable_for_allocation"), owen_usable_previous=w0.get("usable_for_allocation"), owen_unresolved=w.get("unresolved") if "unresolved" in w else (w.get("classes") or {}).get("unresolved"),
                  ledger_rows_source_carrier=has(L, SRC), ledger_rows_plant_line=has(L, LINE), cross_border_flow_rows_source=has(F, SRC), cross_border_flow_rows_plant_line=has(F, LINE), allocation_rows_source=has(A, SRC), allocation_rows_plant_line=has(A, LINE))
    a_ = json.loads((d / "m12_owen/RHS_AUDIT.json").read_text())["owen_premise"]; a0 = json.loads((o_ / "m12_owen/RHS_AUDIT.json").read_text())["owen_premise"]
    out[r].update(owen_identity_relative=w["identity"]["relative_error"], owen_identity_difference_eur=w["identity"]["difference"], rhs_rows_by_class=a_["nonzero_rhs_rows_by_class"], rhs_rows_by_class_previous=a0["nonzero_rhs_rows_by_class"], rhs_premise_passed=a_["passed"])
    print(r, json.dumps(out[r], indent=0, default=str)[:1500])
out["benefit"] = dict(sum_bn=float(ben.owen_benefit_eur.sum()) / 1e9, b6_bn=None, players=int(len(ben)))
x = json.loads((R / "no_new_xb/SOLVE_RECEIPT.json").read_text()); y = json.loads((R / "integrated/SOLVE_RECEIPT.json").read_text())
ob = lambda r: r.get("objective", r.get("objective_value"))
if ob(x) is not None and ob(y) is not None:
    out["benefit"]["b6_bn"] = (float(ob(x)) - float(ob(y))) / 1e9
print(out["benefit"]); print(ben.round(0).head(14).to_string()); print("eval", (R / "eval.log").read_text()[-400:])
print((R / "LA_EXPORT_UTILISATION.csv").read_text()[:700])
(E / "LEDGER_CHECK_180.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
