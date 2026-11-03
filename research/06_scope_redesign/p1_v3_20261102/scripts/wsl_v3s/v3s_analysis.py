"""V3 screening result analysis (read-only on the recovered light pack; V3_SCREEN_AUTODL_INSTRUCTION.md section 3): run table (network SHA256 against the
registered value, termination, objective, iterations, times, peak memory, C1 (a)(b)(c), GATES_V6, decision 120 `accepted`), failed project gates against the
pre-announcement of RUN_PLAN_SCREEN_V3.md section 8, full-year B8, B6 = V2 - V1 (EUR and USD2020, fx 1.139954 USD/EUR) beside the v2 screening (DFX) and the
56-snapshot smoke, Owen dual-form benefit (11 countries + BUNKER) beside the v2 screening, the revision bridge v2 (DFX V1) -> V4 -> V5 -> V1 and V3 - V2.
Writes <out>/V3_SCREEN_RESULTS.json and V3_SCREEN_TABLES.md.
    python v3s_analysis.py <light_unpacked dir> <DFX_PHASE4_RESULTS.json> <out dir>"""
import json
import re
import sys
from pathlib import Path

FX = 1.139954
P = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "BUNKER")
RUNS = ("V1", "V2", "V4", "V5", "V3")
NAME = dict(V1="integrated", V2="no_new_xb", V3="disconnected", V4="bridge 160-162", V5="bridge 160-164")
PRE_ANNOUNCED = ("A1_A2", "A1_A2_S4B", "A3", "A3_S4B", "B1", "B2", "B3", "B3_S4B", "B15")   # RUN_PLAN_SCREEN_V3.md section 8
V2_SCREEN_V1_EUR = 270785244510.473; V2_SCREEN_B6_BN = 14.615313032144318; SMOKE_B6_BN = 12.5665   # DFX phase 4; V3 supplement 05 smoke
lp, dfxp, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
E = lp / "export"; dfx = json.loads(dfxp.read_text(encoding="utf-8"))


def jl(p):
    p = Path(p)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def iters(rid):
    for name in ("GUROBI_LOG_SCRUBBED.txt", "solve_log_scrubbed.txt"):
        f = E / rid / name
        if f.exists():
            t = f.read_text(encoding="utf-8", errors="ignore")
            m = re.findall(r"Barrier (?:solved model in|performed) (\d+) iterations and ([\d.]+) seconds", t)
            st = re.findall(r"^(Optimal objective|Sub-optimal termination|Time limit reached|Numerical trouble|Model is infeasible)[^\n]*", t, re.M)
            return dict(barrier_iterations=int(m[-1][0]) if m else None, barrier_seconds=float(m[-1][1]) if m else None, final_line=st[-1] if st else None,
                        restart_mentions=len(re.findall(r"(?i)restart", t)))
    return {}


def peak_gib(rid):
    f = E / rid / "solve_time.txt"
    if f.exists():
        m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", f.read_text(encoding="utf-8", errors="ignore"))
        if m:
            return int(m.group(1)) / 1048576
    return None


def failed_gates(rid):
    g = jl(E / rid / "V5_GATES.json") or {}
    return sorted(k for k, v in g.items() if isinstance(v, dict) and v.get("passed") is False), g


runs = {}
for rid in RUNS:
    if not (E / rid).exists():
        continue
    rec = jl(E / rid / "SOLVE_RECEIPT.json") or {}; run = jl(E / rid / "RUN.json") or {}; prec = jl(E / rid / "PRECISION.json") or {}
    acc = jl(E / rid / "V6_ACCEPTANCE.json") or {}; prov = jl(E / rid / "V6_ACCEPTANCE_PROVISIONAL.json") or {}; owen = jl(E / rid / "m12_owen" / "OWEN.json") or {}
    oreg = jl(E / rid / "m12_owen" / "OWEN_REGRADE_BATCH_REFERENCE.json") or {}
    g = prec.get("grade") or {}; fg, gates = failed_gates(rid)
    b8 = gates.get("B8") or {}
    runs[rid] = dict(network=NAME[rid], scenario=rec.get("scenario"), termination=rec.get("termination_condition"), objective_eur=rec.get("objective"),
                     objective_lp_eur=rec.get("objective_lp"), solve_seconds=rec.get("solve_seconds"), peak_gib=peak_gib(rid), time_limit=run.get("time_limit"),
                     network_sha256=run.get("network_sha256"), registered_sha256=run.get("registered_sha256"),
                     sha_equal=(run.get("network_sha256") == run.get("registered_sha256")) if run.get("network_sha256") else None, **iters(rid),
                     c1=dict(grade=g.get("grade"), a=g.get("a"), b=g.get("b"), c=g.get("c"), reference=(prec.get("reference") or {}).get("source")),
                     decision120_accepted=(prec.get("acceptance") or {}).get("accepted"), v6=acc.get("label"), v6_provisional=prov.get("label"),
                     g2={k: (v or {}).get("passed") for k, v in (acc.get("G2") or {}).items()}, failed_gates=fg,
                     failed_not_announced=[x for x in fg if x not in PRE_ANNOUNCED and x != "B8"], b8_passed=b8.get("passed"),
                     owen_usable=((oreg.get("new") or {}).get("usable_for_allocation", owen.get("usable_for_allocation"))))
summ = jl(E / "batch" / "DFX_SUMMARY.json") or {}
o = {r: (runs.get(r) or {}).get("objective_eur") for r in RUNS}
b6 = (o["V2"] - o["V1"]) if (o.get("V1") is not None and o.get("V2") is not None) else None
res = dict(script="scripts/wsl_v3s/v3s_analysis.py", fx_usd_per_eur=FX, runs=runs, summary_b6=summ.get("B6"), summary_bridge=summ.get("bridge"),
           summary_stop=dict(stop=summ.get("stop_not_accepted"), stop_safe=summ.get("stop_safe"), postproc_errors=summ.get("postproc_errors"), unusable=summ.get("unusable")))
if b6 is not None:
    res["b6"] = dict(eur=b6, bn_eur=b6 / 1e9, bn_usd2020=b6 * FX / 1e9, v2_screen_bn=V2_SCREEN_B6_BN, minus_v2_screen_bn=b6 / 1e9 - V2_SCREEN_B6_BN,
                     smoke_56_bn=SMOKE_B6_BN, minus_smoke_bn=b6 / 1e9 - SMOKE_B6_BN)
bn = lambda x: None if x is None else x / 1e9
steps = [("v2 (DFX V1)", V2_SCREEN_V1_EUR), ("V4 (160-162)", o.get("V4")), ("V5 (160-164)", o.get("V5")), ("V1 (all, v3)", o.get("V1"))]
res["bridge"] = dict(objective_bn={k: bn(v) for k, v in steps},
                     step_bn={f"{steps[i][0]} -> {steps[i + 1][0]}": (bn(steps[i + 1][1]) - bn(steps[i][1])) if steps[i + 1][1] is not None and steps[i][1] is not None else None for i in range(3)},
                     v3_minus_v2_bn=(bn(o["V3"]) - bn(o["V2"])) if o.get("V3") is not None and o.get("V2") is not None else None,
                     v5_minus_v1_bn=(bn(o["V5"]) - bn(o["V1"])) if o.get("V5") is not None and o.get("V1") is not None else None)
ben = jl(E / "batch" / "M12_BENEFIT" / "BENEFIT.json") or {}; ow = ben.get("owen") or {}
dfx_rows = {r["player"]: r for r in dfx.get("owen_table", [])}
rows = []
for p in P:
    b = (ow.get("benefit_eur") or {}).get(p); a1 = (ow.get("allocation_integrated_eur") or {}).get(p); a2 = (ow.get("allocation_disconnected_eur") or {}).get(p)
    iv = (ow.get("benefit_interval_eur") or {}).get(p)
    r = dict(player=p, V1_share_bn=bn(a1), V2_share_bn=bn(a2), benefit_bn=bn(b), v2_screen_benefit_bn=(dfx_rows.get(p) or {}).get("benefit_bn"),
             interval_bn=[bn(x) for x in iv] if isinstance(iv, (list, tuple)) else iv)
    r["minus_v2_screen_bn"] = (r["benefit_bn"] - r["v2_screen_benefit_bn"]) if r["benefit_bn"] is not None and r["v2_screen_benefit_bn"] is not None else None
    rows.append(r)
res["owen_table"] = rows; res["owen_usable"] = ow.get("usable"); res["negative_benefit"] = ow.get("negative_benefit"); res["negative_in_interval"] = ow.get("negative_somewhere_in_interval")
res["owen_sum_bn"] = bn(ow.get("sum_players_eur")) if not isinstance(ow.get("sum_players_eur"), dict) else ow.get("sum_players_eur")
for f in ("ID_LEDGER_DECOMPOSITION.csv", "VN_BIOMASS_BALANCE.json", "LA_EXPORT_UTILISATION.csv"):
    res.setdefault("screen_tables", {})[f] = (E / "batch" / f).exists()
(out / "V3_SCREEN_RESULTS.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
f = lambda x, s="{:.3f}": "—" if x is None else s.format(x)
L = ["| 运行 | 网络 | SHA256 = 登记 | 终止 | 目标 bn EUR | Gurobi bn | barrier 次 / s | 求解 s | 峰值 GiB | C1 abc | GATES_V6（终 / 临时） | 第 120 项 | 失败闸门 | 预告外 | B8 |",
     "|---|---|---|---|---:|---:|---|---:|---:|---|---|---|---|---|---|"]
for rid, v in runs.items():
    c = v["c1"]; abc = "".join("1" if c.get(k) else "0" for k in "abc")
    L.append(f"| {rid} | {v['network']} | {v['sha_equal']} | {v['termination']} | {f(bn(v['objective_eur']), '{:.4f}')} | {f(bn(v['objective_lp_eur']), '{:.4f}')} | "
             f"{v.get('barrier_iterations') or '—'} / {f(v.get('barrier_seconds'), '{:.0f}')} | {f(v['solve_seconds'], '{:.0f}')} | {f(v['peak_gib'], '{:.2f}')} | {abc} | "
             f"{v['v6']} / {v['v6_provisional']} | {v['decision120_accepted']} | {', '.join(v['failed_gates']) or '—'} | {', '.join(v['failed_not_announced']) or '—'} | {v['b8_passed']} |")
L += ["", "| 参与者 | V1 份额 | V2 份额 | 受益 V2−V1 | α 区间 | v2 筛查受益 | 差 |", "|---|---:|---:|---:|---|---:|---:|"]
for r in rows:
    iv = r["interval_bn"]; ivs = f"{iv[0]:.3f}–{iv[1]:.3f}" if isinstance(iv, list) and len(iv) == 2 and None not in iv else "—"
    L.append(f"| {r['player']} | {f(r['V1_share_bn'])} | {f(r['V2_share_bn'])} | {f(r['benefit_bn'], '{:+.3f}')} | {ivs} | {f(r['v2_screen_benefit_bn'], '{:+.3f}')} | {f(r['minus_v2_screen_bn'], '{:+.3f}')} |")
(out / "V3_SCREEN_TABLES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print(json.dumps(dict(b6=res.get("b6"), bridge=res["bridge"], stop=res["summary_stop"], negative=res["negative_benefit"],
                      runs={k: {x: v[x] for x in ("termination", "objective_eur", "solve_seconds", "barrier_iterations", "peak_gib", "v6", "decision120_accepted", "failed_gates", "failed_not_announced", "b8_passed", "sha_equal")} for k, v in runs.items()}), indent=1, default=str, ensure_ascii=False))
print("\n".join(L))
