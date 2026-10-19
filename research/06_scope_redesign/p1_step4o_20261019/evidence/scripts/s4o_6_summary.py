"""S4O-6 batch summary (READ ONLY, Python only): the downloaded per-run exports of the S4O-6 batch (disconnected, disconnected_gap, integrated_nze),
the S4N pilot integrated run (light package) and the L23 first batch (L23_C9_SUMMARY.json):
  * per run: termination, objective, LP size, barrier iterations / seconds / work units, restarts (primal residual > 1e3 x the previous iteration),
    peak RSS, C1 grade / acceptance (decision 120), failing gates (numerical information);
  * B6 = this batch's disconnected - S4N pilot integrated (decision 121), country ledger differences; NZE - pilot integrated; comparison with L23
    (SCREENING_UNVERIFIED) and with the pilot; pilot consistency (PILOT_CONSISTENCY.json).

    python s4o_6_summary.py <batch export dir (unpacked, one folder per run)> <pilot light dir> <L23_C9_SUMMARY.json> <batch dir with BATCH_REFERENCE.json / PILOT_CONSISTENCY.json> <out json> <out md>
"""
import json, re, sys
from pathlib import Path

import pandas as pd

EX, PL, L23, BD, OUT, MD = map(Path, sys.argv[1:7])
PAT = re.compile(r"^\s*(\d+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+(\d+)s\s*$")


def jl(p):
    return json.loads(Path(p).read_text()) if Path(p).exists() else None


def log_info(p):
    rows, it = [], None
    for line in Path(p).read_text(errors="ignore").splitlines():
        m = PAT.match(line)
        if m:
            rows.append((int(m.group(1)), float(m.group(4)), int(m.group(7)), float(m.group(2)), float(m.group(3))))
        mm = re.match(r"Barrier (?:solved model in|performed) (\d+) iterations (?:and|in) ([\d.]+) seconds \(([\d.]+) work units\)", line)
        if mm:
            it = dict(iterations=int(mm.group(1)), seconds=float(mm.group(2)), work_units=float(mm.group(3)))
    jumps, mn = [], None
    for k, (i, pr, s, po, do) in enumerate(rows):
        if k and pr > 1e3 * rows[k - 1][1]:   # restart = sudden jump against the previous iteration (not the slow descent after it)
            jumps.append(dict(iteration=i, seconds=s, primal_residual=pr, before=rows[k - 1][1], min_before=mn[1], min_iteration=mn[0]))
        if mn is None or pr < mn[1]:
            mn = (i, pr)
    last = rows[-1] if rows else None
    return dict(barrier=it, restarts=jumps, last=dict(iteration=last[0], primal_objective=last[3], dual_objective=last[4], primal_residual=last[1], seconds=last[2]) if last else None)


def ledger(d):
    p = Path(d) / "COUNTRY_COST_LEDGER.csv"
    return (pd.read_csv(p, index_col=0)["total"] / 1e9) if p.exists() else None


runs = {}
for r in ("disconnected", "disconnected_gap", "integrated_nze"):
    d = EX / r
    if not (d / "SOLVE_RECEIPT.json").exists():
        runs[r] = dict(present=False); continue
    rec, pr, g = jl(d / "SOLVE_RECEIPT.json"), jl(d / "PRECISION.json") or {}, jl(d / "V5_GATES.json") or {}
    a, b, c = pr.get("a_total_cost") or {}, pr.get("b_primal_violations") or {}, pr.get("c_prices") or {}
    runs[r] = dict(present=True, termination=rec.get("termination_condition"), objective=rec.get("objective"), objective_lp=rec.get("objective_lp"),
                   profile=rec.get("solver_profile"), parameters=rec.get("solver_parameters"), lp=rec.get("lp", {}) and {k: rec["lp"][k] for k in ("num_row", "num_col", "nnz")},
                   solve_seconds=rec.get("solve_seconds"), peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30, log=log_info(d / "GUROBI_LOG_SCRUBBED.txt"),
                   input_network_sha256=(rec.get("input_network") or {}).get("sha256"),
                   c1=dict(grade=pr.get("grade"), acceptance=pr.get("acceptance"), reference=(pr.get("reference") or {}).get("source", "")[:120],
                           a_diff_bn=a.get("returned_difference_bn"), a_relative=a.get("returned_relative"), b_rows_over_budget=b.get("rows_over_budget"),
                           b_first_order_cost_eur=b.get("first_order_cost_eur_all_rows"), b_row_max_ratio=b.get("row_max_ratio"),
                           b_worst=max(((k, v["first_order_cost_bn"] / v["threshold_bn"]) for k, v in (b.get("country_check") or {}).items()), key=lambda t: t[1], default=None),
                           c_b16=(c.get("b16") or {}).get("relative_error"),
                           c_worst=max(((k, v["S_plus_R_bn"] / v["threshold_bn"]) for k, v in (c.get("country_check") or {}).items()), key=lambda t: t[1], default=None),
                           biomass_dominant=(b.get("biomass_pools_BN_SG_VN") or {}).get("dominant")),
                   gates=dict(all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"), failing=sorted(k for k, v in g.items() if isinstance(v, dict) and v.get("passed") is False)))
prec_pilot = jl(PL / "PILOT_PRECISION.json") or {}
rec_pilot = jl(PL / "export_integrated/SOLVE_RECEIPT.json")
pilot = dict(objective=rec_pilot.get("objective"), termination=rec_pilot.get("termination_condition"), profile=rec_pilot.get("solver_profile"),
             input_network_sha256=(rec_pilot.get("input_network") or {}).get("sha256"), c1_grade=prec_pilot.get("grade"))
li = ledger(PL / "export_integrated")
res = dict(runs=runs, pilot_integrated=pilot, pilot_consistency=jl(BD / "PILOT_CONSISTENCY.json"), batch_reference=jl(BD / "BATCH_REFERENCE.json"))
L = jl(L23) or {}
if runs["disconnected"].get("present"):
    b6 = runs["disconnected"]["objective"] - pilot["objective"]
    ld = ledger(EX / "disconnected")
    idx = li.index.union(ld.index)
    diff = (ld.reindex(idx).fillna(0) - li.reindex(idx).fillna(0)).round(4)
    l23d = (L.get("ledger_difference") or {}).get("total_bn_eur", {})
    res["B6"] = dict(definition="this batch's disconnected STEPS (S4O-6) - S4N pilot integrated STEPS (decision 121)", eur=b6, bn=b6 / 1e9, relative=b6 / pilot["objective"],
                     disconnected_termination=runs["disconnected"]["termination"], l23_bn=((L.get("B6") or {}).get("difference") or 0) / 1e9,
                     l23_disconnected_objective=((L.get("B6") or {}).get("objective") or {}).get("disconnected"), l23_integrated_objective=((L.get("B6") or {}).get("objective") or {}).get("integrated"))
    res["country_difference_bn"] = {k: dict(s4o=float(diff[k]), l23=l23d.get(k)) for k in diff.index}
if runs["integrated_nze"].get("present"):
    dn = runs["integrated_nze"]["objective"] - pilot["objective"]
    ln = ledger(EX / "integrated_nze"); idx = li.index.union(ln.index)
    res["NZE_minus_integrated"] = dict(definition="this batch's integrated NZE - S4N pilot integrated STEPS", eur=dn, bn=dn / 1e9, relative=dn / pilot["objective"],
                                       nze_termination=runs["integrated_nze"]["termination"], l23_bn=((L.get("nze_vs_integrated") or {}).get("objective_difference_eur") or 0) / 1e9,
                                       by_country_bn=(ln.reindex(idx).fillna(0) - li.reindex(idx).fillna(0)).round(4).to_dict())
OUT.write_text(json.dumps(res, indent=1, default=str))
# markdown
M = ["# S4O-6 整批汇总（只读）", "", "| 运行 | 终止 | 目标 EUR | barrier 迭代 / 秒 / WU | 重启（迭代） | 峰值 RSS | C1 分级 / 验收 | 不通过的门槛（信息） |", "|---|---|---|---|---|---|---|---|"]
for r, v in runs.items():
    if not v.get("present"):
        M.append(f"| {r} | 未运行 | | | | | | |"); continue
    bb = v["log"]["barrier"] or {}
    M.append(f"| {r} | {v['termination']} | {v['objective']:,.2f} | {bb.get('iterations')} / {bb.get('seconds')} / {bb.get('work_units')} | {', '.join(str(j['iteration']) for j in v['log']['restarts']) or '无'} | "
             f"{v['peak_rss_gib']:.1f} GiB | {v['c1']['grade']['grade']} / {v['c1']['acceptance']['accepted']} | {', '.join(v['gates']['failing'])} |")
if "B6" in res:
    M += ["", f"- **B6（本批不互联 − 试点一体化）：{res['B6']['bn']:.4f} bn EUR**（相对 {res['B6']['relative']:.4f}）；L23（筛查未验证）{res['B6']['l23_bn']:.4f} bn", "",
          "| 国 / 实体 | 不互联 − 一体化 bn（S4O） | L23 bn |", "|---|---|---|"]
    M += [f"| {k} | {v['s4o']:.4f} | {v['l23'] if v['l23'] is not None else '—'} |" for k, v in res["country_difference_bn"].items()]
if "NZE_minus_integrated" in res:
    M += ["", f"- **NZE − 一体化（本批 NZE − 试点一体化）：{res['NZE_minus_integrated']['bn']:.4f} bn EUR**（相对 {res['NZE_minus_integrated']['relative']:.4f}）；L23 {res['NZE_minus_integrated']['l23_bn']:.4f} bn"]
MD.write_text("\n".join(M) + "\n", encoding="utf-8")
print(json.dumps({k: res[k] for k in ("B6", "NZE_minus_integrated") if k in res}, default=str)[:1500])
