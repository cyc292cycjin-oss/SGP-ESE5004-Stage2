"""V3 supplement 07 rerun, result analysis (read-only on the recovered light pack; review EVDIAG section 2.2 item 10): run table of V1 / V2 / V3 (network SHA256
against the registered value, termination, objective, iterations, times, peak memory, C1 (a)(b)(c), GATES_V6, decision 120 `accepted`, failed gates against the
pre-announcement of RUN_PLAN_SCREEN_V3.md section 8, full-year B8); old / new table (first screening against this rerun: V1, V2, V3 objectives, B6, V3 - V2, Owen
benefit of the 12 participants); the full revision bridge v2 (DFX V1) -> V4 -> V5 (first screening, networks unchanged) -> new V1; the predictions of
RUN_PLAN_V3.md section 23.3 judged on the registered numbers. Writes <out>/V3R_RESULTS.json and V3R_TABLES.md.
    python v3r_analysis.py <light_unpacked dir> <first-screening V3_SCREEN_RESULTS.json> <out dir>"""
import json
import re
import sys
from pathlib import Path

FX = 1.139954
P = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "BUNKER")
RUNS = ("V1", "V2", "V3")
NAME = dict(V1="integrated", V2="no_new_xb", V3="disconnected")
REG = dict(V1="a0273602016003fc4318cdd993b69716772c700cd2f9d079059fabcdde099c8b", V2="f9f4057b9972b2d7c8ab8b574c2d90c306000ae44eb2697ad80a6c0dc3554861",
           V3="f889c3ba1dee0ce48dc9c5d6aa165b3dd2a436bc16a92230616a091436d89974")   # RUN_PLAN_V3.md section 23.1
PRE_ANNOUNCED = ("A1_A2", "A1_A2_S4B", "A3", "A3_S4B", "B1", "B2", "B3", "B3_S4B", "B15")
V2_SCREEN_V1_EUR = 270785244510.473   # DFX phase 4 (v2 integrated 365x24h)
lp, oldp, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
E = lp / "export"; old = json.loads(oldp.read_text(encoding="utf-8"))
bn = lambda x: None if x is None else x / 1e9


def jl(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
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
    m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", f.read_text(encoding="utf-8", errors="ignore")) if f.exists() else None
    return int(m.group(1)) / 1048576 if m else None


runs = {}
for rid in RUNS:
    if not (E / rid).exists():
        continue
    rec = jl(E / rid / "SOLVE_RECEIPT.json") or {}; run = jl(E / rid / "RUN.json") or {}; prec = jl(E / rid / "PRECISION.json") or {}
    acc = jl(E / rid / "V6_ACCEPTANCE.json") or {}; prov = jl(E / rid / "V6_ACCEPTANCE_PROVISIONAL.json") or {}; owen = jl(E / rid / "m12_owen" / "OWEN.json") or {}
    oreg = jl(E / rid / "m12_owen" / "OWEN_REGRADE_BATCH_REFERENCE.json") or {}; g = prec.get("grade") or {}; gates = jl(E / rid / "V5_GATES.json") or {}
    fg = sorted(k for k, v in gates.items() if isinstance(v, dict) and v.get("passed") is False)
    runs[rid] = dict(network=NAME[rid], scenario=rec.get("scenario"), termination=rec.get("termination_condition"), objective_eur=rec.get("objective"), objective_lp_eur=rec.get("objective_lp"),
                     solve_seconds=rec.get("solve_seconds"), peak_gib=peak_gib(rid), time_limit=run.get("time_limit"), network_sha256=run.get("network_sha256"),
                     sha_equal_registered=run.get("network_sha256") == REG[rid] == run.get("registered_sha256"), **iters(rid),
                     c1=dict(grade=g.get("grade"), a=g.get("a"), b=g.get("b"), c=g.get("c"), reference=(prec.get("reference") or {}).get("source")),
                     decision120_accepted=(prec.get("acceptance") or {}).get("accepted"), v6=acc.get("label"), v6_provisional=prov.get("label"),
                     g2={k: (v or {}).get("passed") for k, v in (acc.get("G2") or {}).items()}, failed_gates=fg, failed_not_announced=[x for x in fg if x not in PRE_ANNOUNCED],
                     b8_passed=(gates.get("B8") or {}).get("passed"), owen_usable=((oreg.get("new") or {}).get("usable_for_allocation", owen.get("usable_for_allocation"))))
summ = jl(E / "batch" / "DFX_SUMMARY.json") or {}
o = {r: (runs.get(r) or {}).get("objective_eur") for r in RUNS}; oo = {r: v["objective_eur"] for r, v in old["runs"].items()}
res = dict(script="scripts/wsl_v3r/v3r_analysis.py", fx_usd_per_eur=FX, runs=runs, summary_b6=summ.get("B6"), summary_bridge=summ.get("bridge"),
           summary_stop=dict(stop=summ.get("stop_not_accepted"), stop_safe=summ.get("stop_safe"), postproc_errors=summ.get("postproc_errors"), unusable=summ.get("unusable")))
diff = lambda a, b: (a - b) if a is not None and b is not None else None
b6n, b6o = diff(o.get("V2"), o.get("V1")), diff(oo["V2"], oo["V1"]); svn, svo = diff(o.get("V3"), o.get("V2")), diff(oo["V3"], oo["V2"])
res["old_new"] = dict(objective_bn={r: dict(first=bn(oo[r]), rerun=bn(o.get(r)), change=bn(diff(o.get(r), oo[r]))) for r in RUNS},
                      b6_bn=dict(first=bn(b6o), rerun=bn(b6n), change=bn(diff(b6n, b6o)), rerun_usd2020=None if b6n is None else b6n * FX / 1e9),
                      v3_minus_v2_bn=dict(first=bn(svo), rerun=bn(svn), change=bn(diff(svn, svo))))
steps = [("v2 (DFX V1)", V2_SCREEN_V1_EUR), ("V4 (160-162, first screening)", oo["V4"]), ("V5 (160-164, first screening)", oo["V5"]), ("V1 (all, rerun)", o.get("V1"))]
res["bridge"] = dict(objective_bn={k: bn(v) for k, v in steps}, step_bn={f"{steps[i][0]} -> {steps[i + 1][0]}": bn(diff(steps[i + 1][1], steps[i][1])) for i in range(3)},
                     total_v2_to_v3_bn=bn(diff(o.get("V1"), V2_SCREEN_V1_EUR)), total_first_screening_bn=bn(oo["V1"] - V2_SCREEN_V1_EUR),
                     v5_minus_v1_bn=dict(first=bn(oo["V5"] - oo["V1"]), rerun=bn(diff(oo["V5"], o.get("V1")))))
ben = jl(E / "batch" / "M12_BENEFIT" / "BENEFIT.json") or {}; ow = ben.get("owen") or {}; oldrows = {r["player"]: r for r in old["owen_table"]}; rows = []
for p in P:
    b = bn((ow.get("benefit_eur") or {}).get(p)); ob = (oldrows.get(p) or {}).get("benefit_bn")
    iv = (ow.get("benefit_interval_eur") or {}).get(p); ivb = [bn(iv["min"]), bn(iv["max"])] if isinstance(iv, dict) else ([bn(x) for x in iv] if isinstance(iv, (list, tuple)) else None)
    rows.append(dict(player=p, V1_share_bn=bn((ow.get("allocation_integrated_eur") or {}).get(p)), V2_share_bn=bn((ow.get("allocation_disconnected_eur") or {}).get(p)),
                     benefit_bn=b, interval_bn=ivb, first_benefit_bn=ob, change_bn=diff(b, ob), sign_same=None if b is None or ob is None else (b > 0) == (ob > 0)))
res["owen_table"] = rows; res["owen_usable"] = ow.get("usable"); res["negative_benefit"] = ow.get("negative_benefit"); res["negative_in_interval"] = ow.get("negative_somewhere_in_interval")
res["owen_sum_bn"] = bn(ow.get("sum_players_eur")) if not isinstance(ow.get("sum_players_eur"), dict) else ow.get("sum_players_eur")
for f in ("ID_LEDGER_DECOMPOSITION.csv", "VN_BIOMASS_BALANCE.json", "LA_EXPORT_UTILISATION.csv"):
    res.setdefault("screen_tables", {})[f] = (E / "batch" / f).exists()
# predictions, RUN_PLAN_V3.md section 23.3 (registered numbers only; the EV trajectory rows come from v3r_ev.py on the full pack)
inr = lambda x, lo, hi: None if x is None else lo <= x <= hi
v1, v2 = bn(o.get("V1")), bn(o.get("V2")); b6, sv = bn(b6n), bn(svn); ev = bn(diff(oo["V5"], o.get("V1"))); tot = bn(diff(o.get("V1"), V2_SCREEN_V1_EUR))
pred = [("V1 objective 265.1-267.6 bn (structural floor 263.5966)", v1, inr(v1, 265.1, 267.6)), ("V1 most likely 266.7-267.1 bn", v1, inr(v1, 266.7, 267.1)),
        ("V5 - V1 positive 1.14-3.61 bn", ev, inr(ev, 1.14, 3.61)), ("V5 - V1 most likely 1.6-2.1 bn", ev, inr(ev, 1.6, 2.1)),
        ("B6 positive 14.25-14.80 bn", b6, inr(b6, 14.25, 14.80)), ("B6 change -0.10 to +0.45 bn", bn(diff(b6n, b6o)), inr(bn(diff(b6n, b6o)), -0.10, 0.45)),
        ("B6 rise more likely", bn(diff(b6n, b6o)), None if b6 is None else b6n > b6o), ("V2 objective 279.3-282.4 bn", v2, inr(v2, 279.3, 282.4)),
        ("V3 - V2 positive 1.05-1.60 bn", sv, inr(sv, 1.05, 1.60)), ("V3 - V2 rise more likely", bn(diff(svn, svo)), None if svn is None else svn > svo),
        ("bridge v2 -> v3 total -3.2 to -5.7 bn", tot, inr(tot, -5.7, -3.2)), ("bridge total most likely -3.7 to -4.1 bn", tot, inr(tot, -4.1, -3.7)),
        ("Owen signs as the first screening (11 countries +, BUNKER -)", [r["player"] for r in rows if r["sign_same"] is False], all(r["sign_same"] for r in rows) if rows and all(r["sign_same"] is not None for r in rows) else None),
        ("structural: new objectives not below the first screening", {r: bn(diff(o.get(r), oo[r])) for r in RUNS}, all(o.get(r) is not None and o[r] >= oo[r] * (1 - 1e-6) for r in RUNS))]
res["predictions"] = [dict(item=a, actual=b, met=c) for a, b, c in pred]
(out / "V3R_RESULTS.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
f = lambda x, s="{:.4f}": "—" if x is None else s.format(x)
L = ["| 运行 | 网络 | SHA256 = 登记 | 终止 | 目标 bn EUR | Gurobi bn | barrier 次 / s | 求解 s | 峰值 GiB | C1 abc | GATES_V6（终 / 临时） | 第 120 项 | 失败闸门 | 预告外 | B8 |",
     "|---|---|---|---|---:|---:|---|---:|---:|---|---|---|---|---|---|"]
for rid, v in runs.items():
    c = v["c1"]; abc = "".join("1" if c.get(k) else "0" for k in "abc")
    L.append(f"| {rid} | {v['network']} | {v['sha_equal_registered']} | {v['termination']} | {f(bn(v['objective_eur']))} | {f(bn(v['objective_lp_eur']))} | {v.get('barrier_iterations') or '—'} / "
             f"{f(v.get('barrier_seconds'), '{:.0f}')} | {f(v['solve_seconds'], '{:.0f}')} | {f(v['peak_gib'], '{:.2f}')} | {abc} | {v['v6']} / {v['v6_provisional']} | {v['decision120_accepted']} | "
             f"{', '.join(v['failed_gates']) or '—'} | {', '.join(v['failed_not_announced']) or '—'} | {v['b8_passed']} |")
on = res["old_new"]
L += ["", "| 项（bn EUR） | 第一次筛查 | 重跑 | 变化 |", "|---|---:|---:|---:|"] + [f"| {r} 目标值 | {f(v['first'])} | {f(v['rerun'])} | {f(v['change'], '{:+.4f}')} |" for r, v in on["objective_bn"].items()]
L += [f"| B6 = V2 − V1 | {f(on['b6_bn']['first'])} | {f(on['b6_bn']['rerun'])} | {f(on['b6_bn']['change'], '{:+.4f}')} |", f"| V3 − V2 | {f(on['v3_minus_v2_bn']['first'])} | {f(on['v3_minus_v2_bn']['rerun'])} | {f(on['v3_minus_v2_bn']['change'], '{:+.4f}')} |"]
L += ["", "| 参与者 | V1 份额 | V2 份额 | 受益（重跑） | α 区间 | 第一次筛查 | 变化 | 符号相同 |", "|---|---:|---:|---:|---|---:|---:|---|"]
for r in rows:
    iv = r["interval_bn"]; ivs = f"{iv[0]:+.3f} – {iv[1]:+.3f}" if iv and None not in iv else "—"
    L.append(f"| {r['player']} | {f(r['V1_share_bn'], '{:.3f}')} | {f(r['V2_share_bn'], '{:.3f}')} | {f(r['benefit_bn'], '{:+.3f}')} | {ivs} | {f(r['first_benefit_bn'], '{:+.3f}')} | {f(r['change_bn'], '{:+.3f}')} | {r['sign_same']} |")
L += ["", "| 修订桥步骤 | 变化 bn |", "|---|---:|"] + [f"| {k} | {f(v, '{:+.4f}')} |" for k, v in res["bridge"]["step_bn"].items()] + [f"| 合计 v2 → v3 | {f(res['bridge']['total_v2_to_v3_bn'], '{:+.4f}')} |"]
L += ["", "| 预测（第 23.3 节） | 实际 | 符合 |", "|---|---|---|"] + [f"| {p['item']} | {p['actual'] if not isinstance(p['actual'], float) else f(p['actual'], '{:+.4f}')} | {p['met']} |" for p in res["predictions"]]
(out / "V3R_TABLES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print(json.dumps(dict(old_new=on, bridge=res["bridge"], stop=res["summary_stop"], negative=res["negative_benefit"], predictions=[(p["item"][:40], p["met"]) for p in res["predictions"]]), indent=1, default=str, ensure_ascii=False))
print("\n".join(L))
