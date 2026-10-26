"""DFX phase 4 result analysis (read-only on the recovered light pack): run table, B6 (EUR and USD2020, fx 1.139954 USD/EUR), Owen dual-form
allocation (alpha main) of V1 / V2 and the country benefit V2 - V1, alongside the third batch (main R3 / R4, alongside R1 / R2), objective and benefit
differences against the registered first-order prediction (description only; RUN_PLAN_DFX 3.4 items 5-6), Gurobi iteration counts from the scrubbed
logs. Writes <out>/DFX_PHASE4_RESULTS.json and DFX_PHASE4_TABLES.md.
    python phase4_analysis.py <light_unpacked dir> <BATCH3_REFERENCE_VALUES.json> <out dir>"""
import json
import re
import sys
from pathlib import Path

FX = 1.139954
P = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "BUNKER")
lp, refp, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
E = lp / "export"; ref = json.loads(refp.read_text()); b3 = ref["batch3"]; fo = ref["first_order"]


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def iters(rid):
    for name in ("GUROBI_LOG_SCRUBBED.txt", "solve_log_scrubbed.txt"):
        f = E / rid / name
        if f.exists():
            t = f.read_text(errors="ignore")
            m = re.findall(r"Barrier (?:solved model in|performed) (\d+) iterations", t)
            st = re.findall(r"^(Optimal objective|Sub-optimal termination|Time limit reached|Numerical trouble|Model is infeasible)[^\n]*", t, re.M)
            restart = len(re.findall(r"(?i)restart", t))
            return dict(barrier_iterations=int(m[-1]) if m else None, final_line=st[-1] if st else None, restart_mentions=restart, source=name)
    return {}


summ = jl(E / "batch" / "DFX_SUMMARY.json") or {}
runs = {}
for rid in ("V1", "V2"):
    rec = jl(E / rid / "SOLVE_RECEIPT.json") or {}; acc = jl(E / rid / "V6_ACCEPTANCE.json") or {}; prov = jl(E / rid / "V6_ACCEPTANCE_PROVISIONAL.json") or {}
    prec = jl(E / rid / "PRECISION.json") or {}; sc = jl(E / rid / "STOP_CLASS.json") or {}; owen = jl(E / rid / "m12_owen" / "OWEN.json") or {}
    oreg = jl(E / rid / "m12_owen" / "OWEN_REGRADE_BATCH_REFERENCE.json") or {}; run = jl(E / rid / "RUN.json") or {}
    g = prec.get("grade") or {}
    runs[rid] = dict(scenario=rec.get("scenario"), termination=rec.get("termination_condition"), status=rec.get("status"), objective_eur=rec.get("objective"),
                     solve_seconds=rec.get("solve_seconds"), peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30, time_limit=run.get("time_limit"), wall_cap_s=run.get("wall_cap_s"),
                     input_sha256=(rec.get("input_network") or {}).get("sha256"), registered_sha256=run.get("registered_sha256"), **iters(rid),
                     c1=dict(grade=g.get("grade"), a=g.get("a"), b=g.get("b"), c=g.get("c"), reference=(prec.get("reference") or {}).get("source"), regrades=len(prec.get("grade_history") or [])),
                     v6=acc.get("label"), v6_provisional=prov.get("label"), g2={k: (v or {}).get("passed") for k, v in (acc.get("G2") or {}).items()},
                     stop_class=dict(cls=sc.get("cls"), action=sc.get("action")) if sc else None,
                     owen_usable=((oreg.get("new") or {}).get("usable_for_allocation", owen.get("usable_for_allocation"))),
                     owen_alpha_main_eur={k: v for k, v in ((owen.get("allocation_eur") or {}).get(str(owen.get("alpha_main", 0.5))) or {}).items() if k != "SHARED"})
o1, o2 = runs["V1"]["objective_eur"], runs["V2"]["objective_eur"]
b6 = (o2 - o1) if (o1 is not None and o2 is not None) else None
res = dict(script="scripts/wsl_dfx4/phase4_analysis.py", fx_usd_per_eur=FX, runs=runs,
           b6=dict(eur=b6, bn_eur=b6 / 1e9 if b6 is not None else None, bn_usd2020=b6 * FX / 1e9 if b6 is not None else None,
                   gate=(summ.get("B6") or {}).get("passed"), labels=(summ.get("B6") or {}).get("labels")),
           batch3=dict(main_b6_bn=b3["b6_bn"], alternative_b6_bn=b3["b6_alternative_bn"], objective_eur=b3["objective_eur"]))
if b6 is not None:
    res["delta"] = dict(b6_vs_R3R4_bn=b6 / 1e9 - b3["b6_bn"], b6_vs_R1R2_bn=b6 / 1e9 - b3["b6_alternative_bn"], first_order_delta_b6_bn=fo["delta_b6_bn"],
                        actual_minus_first_order_bn=(b6 / 1e9 - b3["b6_bn"]) - fo["delta_b6_bn"], predicted_b6_bn=fo["predicted_b6_bn"],
                        V1_minus_R3_bn=(o1 - b3["objective_eur"]["R3"]) / 1e9, V2_minus_R4_bn=(o2 - b3["objective_eur"]["R4"]) / 1e9,
                        V1_minus_R1_bn=(o1 - b3["objective_eur"]["R1"]) / 1e9, V2_minus_R2_bn=(o2 - b3["objective_eur"]["R2"]) / 1e9,
                        first_order_dC_integrated_bn=fo["delta_c_integrated_bn"], first_order_dC_disconnected_bn=fo["delta_c_disconnected_bn"])
a = b3["owen_alpha_main_eur"]; w1, w2 = runs["V1"]["owen_alpha_main_eur"], runs["V2"]["owen_alpha_main_eur"]
ben = jl(E / "batch" / "M12_BENEFIT" / "BENEFIT.json") or {}
rows = []
for p in P:
    r = dict(player=p, V1_share_bn=(w1.get(p) / 1e9 if p in w1 else None), V2_share_bn=(w2.get(p) / 1e9 if p in w2 else None))
    r["benefit_bn"] = (r["V2_share_bn"] - r["V1_share_bn"]) if (r["V1_share_bn"] is not None and r["V2_share_bn"] is not None) else None
    bb = ((ben.get("owen") or {}).get("benefit_eur") or {}).get(p); r["benefit_m12_bn"] = bb / 1e9 if bb is not None else None
    r["R3_share_bn"] = a["R3"][p] / 1e9; r["R4_share_bn"] = a["R4"][p] / 1e9; r["benefit_R3R4_bn"] = (a["R4"][p] - a["R3"][p]) / 1e9
    r["R1_share_bn"] = a["R1"][p] / 1e9; r["benefit_R1R2_bn"] = (a["R2"][p] - a["R1"][p]) / 1e9
    r["benefit_change_vs_R3R4_bn"] = (r["benefit_bn"] - r["benefit_R3R4_bn"]) if r["benefit_bn"] is not None else None
    r["first_order_benefit_change_bn"] = fo["by_country_bn"].get(p)
    rows.append(r)
res["owen_table"] = rows; res["m12_benefit_negative"] = (ben.get("owen") or {}).get("negative_benefit"); res["summary_stop"] = dict(stop=summ.get("stop_not_accepted"), stop_safe=summ.get("stop_safe"), postproc_errors=summ.get("postproc_errors"))
(out / "DFX_PHASE4_RESULTS.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
f = lambda x, s="{:.3f}": "—" if x is None else s.format(x)
L = ["| 运行 | 终止 | 目标 bn EUR | 求解 s | barrier 次数 | 峰值 GiB | C1 abc | 参照 | GATES_V6（终 / 临时） | 分级 | Owen 可用 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for rid, v in runs.items():
    c = v["c1"]; abc = "".join("1" if c.get(k) else "0" for k in "abc")
    L.append(f"| {rid} | {v['termination']} | {f(v['objective_eur'] / 1e9 if v['objective_eur'] else None, '{:.4f}')} | {f(v['solve_seconds'], '{:.0f}')} | {v.get('barrier_iterations') or '—'} | {f(v['peak_rss_gib'], '{:.2f}')} | {abc} | {'批' if str(c.get('reference') or '').startswith('this batch') else '缺省'} | {v['v6']} / {v['v6_provisional']} | {(v['stop_class'] or {}).get('cls', '—')} | {v['owen_usable']} |")
L += ["", "| 参与者 | V1 份额 | V2 份额 | 受益 V2−V1 | R3 份额 | 受益 R4−R3 | 受益 R2−R1 | 受益变化（对 R3/R4） | 一阶预测变化 |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    L.append(f"| {r['player']} | {f(r['V1_share_bn'])} | {f(r['V2_share_bn'])} | {f(r['benefit_bn'])} | {f(r['R3_share_bn'])} | {f(r['benefit_R3R4_bn'])} | {f(r['benefit_R1R2_bn'])} | {f(r['benefit_change_vs_R3R4_bn'], '{:+.3f}')} | {f(r['first_order_benefit_change_bn'], '{:+.3f}')} |")
(out / "DFX_PHASE4_TABLES.md").write_text("\n".join(L) + "\n")
print(json.dumps(dict(b6=res["b6"], delta=res.get("delta"), runs={k: {x: v[x] for x in ("termination", "objective_eur", "solve_seconds", "barrier_iterations", "peak_rss_gib", "v6", "owen_usable")} for k, v in runs.items()}), indent=1, default=str))
print("\n".join(L))
