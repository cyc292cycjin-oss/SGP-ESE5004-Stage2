"""DFX v3 F5.5: summary JSON of the local 56-snapshot smoke (results_project/dfx_v3/smoke_v2): receipts, GATES_V6, C1, Owen, stop-class, B6. Read-only."""
import json
import re
from pathlib import Path

R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/smoke_v2")
st = (R / "STATUS.txt").read_text()
res = dict(status_lines=st.splitlines(), runs={}, gurobi_calls=[])
for sc in ("integrated", "disconnected"):
    d = R / sc; rec = json.load(open(d / "SOLVE_RECEIPT.json")); acc = json.load(open(d / "V6_ACCEPTANCE.json")); prec = json.load(open(d / "PRECISION.json"))
    owen = json.load(open(d / "m12_owen" / "OWEN.json")); cls = json.load(open(d / "STOP_CLASS.json")); prov = json.load(open(d / "V6_ACCEPTANCE_PROVISIONAL.json")) if (d / "V6_ACCEPTANCE_PROVISIONAL.json").exists() else None
    stats = rec.get("solver_stats") or {}
    g = prec.get("grade") or {}
    res["runs"][sc] = dict(termination=rec.get("termination_condition"), status=rec.get("status"), objective=rec.get("objective"), solve_seconds=rec.get("solve_seconds"),
                           peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30, snapshots=rec["input_network"]["snapshots"], truncated_to=rec["input_network"].get("truncated_to"),
                           input_sha256=rec["input_network"]["sha256"], profile=rec.get("solver_profile"), parameters=rec.get("solver_parameters"),
                           bar_iter_count=stats.get("bar_iter_count", stats.get("BarIterCount")), work=stats.get("work", stats.get("Work")),
                           v6_label=acc.get("label"), v6_provisional=(prov or {}).get("label"), g1={k: (acc.get("G1") or {}).get(k) for k in ("a", "b", "c")},
                           g2={k: (v or {}).get("passed") for k, v in (acc.get("G2") or {}).items()}, g2_1_registered=((acc.get("G2") or {}).get("G2_1") or {}).get("registered_sha256"),
                           c1=dict(grade=g.get("grade"), a=g.get("a"), b=g.get("b"), c=g.get("c"), reference=(prec.get("reference") or {}).get("source"), regrades=len(prec.get("grade_history") or [])),
                           owen=dict(usable=owen.get("usable_for_allocation"), premise_failed=owen.get("premise_failed"), alpha_main=owen.get("alpha_main"), main_form=owen.get("main_form")),
                           stop_class=dict(cls=cls.get("cls"), action=cls.get("action")),
                           post_exits={m.group(1): m.group(2) for m in re.finditer(r"^(VIOLATIONS|C1|M12|OWEN|REGRADE|OWEN_REGRADE)_" + sc + r":.*?exit=(\d+)", st, re.M)})
    for m in re.finditer(r"^SOLVE_" + sc + r":(\S+?Z):", st, re.M):
        res["gurobi_calls"].append(dict(scenario=sc, start_utc=m.group(1)))
ben = json.load(open(R / "M12_BENEFIT" / "BENEFIT.json")) if (R / "M12_BENEFIT" / "BENEFIT.json").exists() else None
res["b6_56_snapshots_bn"] = (res["runs"]["disconnected"]["objective"] - res["runs"]["integrated"]["objective"]) / 1e9
res["m12_benefit"] = dict(b6_bn=(ben or {}).get("b6_eur", 0) / 1e9 if ben else None, computable=(ben or {}).get("computable"))
res["batch_reference"] = (R / "BATCH_REFERENCE.json").exists()
res["all_optimal"] = all(v["termination"] == "optimal" for v in res["runs"].values())
res["all_accepted"] = all(v["v6_label"] in ("ACCEPTED_LAYER1", "ACCEPTED_LAYER2") for v in res["runs"].values())
res["chain_exit_zero"] = all(all(x == "0" for x in v["post_exits"].values()) for v in res["runs"].values())
(R / "SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps({k: v for k, v in res.items() if k not in ("status_lines",)}, indent=1, default=str)[:3500])
