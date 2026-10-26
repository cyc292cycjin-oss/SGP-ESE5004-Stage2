"""DFX (demand fix, v2 networks; instruction v3 F6, 2026-10-26): run table, registered limits and read-only helpers of the DFX 365x24h screening
runner research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/run_dfx.sh. Two runs on the v2 365x24h networks built at commit 72083fde
(SHA256 / bytes registered below = RUN_PLAN_DFX.md section 1): V1 integrated, V2 disconnected, profile formal_barrier_1e6_t16 (Threads 16; the
profile chosen by the third batch and used by the fourth). Never calls a solver; reads solve results and never changes them (writes only its own
JSON / Markdown outputs). The third-batch helpers (m10_batch3_summary.py: run_state, build_check, ledger / Owen readers) are reused with THIS
run table (the module constants of m10_batch3_summary are replaced at import time; nothing of the third batch is rewritten).

    python scripts_project/dfx_batch.py runtable                 -> "RID|scenario|base|set|profile|costs" per run (the runner's table)
    python scripts_project/dfx_batch.py schedule                 -> "phase|lane A rids|lane B rids" (one phase: V1 | V2)
    python scripts_project/dfx_batch.py limits                   -> "RID|time_limit_s|wall_cap_s" per run (registered values; single source for the runner)
    python scripts_project/dfx_batch.py base-check --nets <networks> --out <json>   (the two 365x24h networks against the build receipts AND the registered SHA256 / bytes)
    python scripts_project/dfx_batch.py build-check --dir <OUT/V1> --repo <code>   (dry run: LP built, parameters = profile + registered TimeLimit, registered input)
    python scripts_project/dfx_batch.py stop-class --dir <OUT/V1>                   -> STOP_CLASS.json; prints "<class> <action>" (both runs are batch reference runs)
    python scripts_project/dfx_batch.py summary --out-dir <OUT> [--reference <BATCH3_REFERENCE_VALUES.json>]  -> OUT/DFX_SUMMARY.json / .md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import m10_batch3_summary as m10  # noqa: E402
from m10_batch3_summary import COUNTRIES, bn, jl, ledger_totals, owen_main, postproc_errors, sha, unusable_runs  # noqa: E402

SCRIPT = "scripts_project/dfx_batch.py"
T16 = "formal_barrier_1e6_t16"
LABEL = "DFX_365X24H"
# Pre-registered run table (RUN_PLAN_DFX.md section 2): the two v2 365x24h base networks themselves (no variant), profile T16 of the third batch.
RUNS = {
    "V1": dict(scenario="integrated", base="integrated_365_24h", set="", profile=T16, costs="integrated", role="本批参照（一体化，v2 需求）、Owen 分摊"),
    "V2": dict(scenario="disconnected", base="disconnected_365_24h", set="", profile=T16, costs="disconnected", role="本批参照（不互联，v2 需求）、B6 = V2 − V1"),
}
SCHEDULE = [("1", ["V1"], ["V2"])]
STOP_ALWAYS = ("V1", "V2")   # both runs are the batch reference: G2 failed / no returned solution / C1 (a) failed -> STOP (RUN_PLAN_DFX 3.3)
# Registered limits (RUN_PLAN_DFX.md section 3.1, user amendment 2026-10-27 before any v2 365x24h solve): TimeLimit V1 21,600 s (6 h), V2 10,800 s (3 h);
# wall cap = TimeLimit + 1,200 s. (First registration: 3 x the third-batch R3 / R4 solve wall clock = 14,646 / 4,269 s.)
TIME_LIMIT_S = {"V1": 21600, "V2": 10800}
WALL_MARGIN_S = 1200
LICENCE_GAP_S = 330
PARALLEL_MIN_CORES = 33   # 2 x Threads 16 + 1 core for the post-processing of the lane that ends first (RUN_PLAN_DFX 3.2)
# Registered inputs (RUN_PLAN_DFX.md section 1; v2 builds at commit 72083fde, results_project/dfx_v3/builds_v2)
REGISTERED_SHA = {"integrated_365_24h_unsolved.nc": "82928a4c9151a6a176ac8c81bf56bbe41867e16ba0d059ce2ad8c6e78e59f6b2",
                  "disconnected_365_24h_unsolved.nc": "5c75bfa0e338fde4104deb41cdcaa72dddcf7b3782e6ad8ca1f4fb6c15cfbd5c"}
REGISTERED_BYTES = {"integrated_365_24h_unsolved.nc": 31292240, "disconnected_365_24h_unsolved.nc": 30620986}
BUILD_COMMIT = "72083fde6bffd89580869af6dd00885a8d76721f"

# NOTE: the third-batch module is never modified (no monkeypatching of its RUNS / SCHEDULE: an earlier draft did so at import time and broke the
# third-batch and fourth-batch stand-in tests collected in the same pytest process). Only its table-free helpers are imported; run_state is local.


def run_state(out: Path, rid: str) -> dict:
    """Per-run state (the third-batch run_state with the DFX table): receipt, C1, GATES_V6 (final + provisional), Owen usability, stop class."""
    d = out / rid; rec = jl(d / "SOLVE_RECEIPT.json") or {}; prec = jl(d / "PRECISION.json") or {}; acc = jl(d / "V6_ACCEPTANCE.json") or {}
    prov = jl(d / "V6_ACCEPTANCE_PROVISIONAL.json"); owen = jl(d / "m12_owen" / "OWEN.json") or {}; oreg = jl(d / "m12_owen" / "OWEN_REGRADE_BATCH_REFERENCE.json")
    run = jl(d / "RUN.json") or {}
    if (d / ".ended").exists():
        state = "ended"
    elif (d / ".started").exists():
        state = "started_not_ended"
    elif run:
        state = "prepared"
    else:
        state = "not_started"
    if rec.get("stop_before_solve"):
        state = "built_stopped_before_solve"
    g = prec.get("grade") or {}; src = str((prec.get("reference") or {}).get("source") or ""); sc = jl(d / "STOP_CLASS.json")
    return dict(rid=rid, role=RUNS[rid]["role"], profile=RUNS[rid]["profile"], set=RUNS[rid]["set"], state=state, network=run.get("network"), network_sha256=run.get("network_sha256"),
                stop_class=(dict(cls=sc.get("cls"), action=sc.get("action"), failed_checks=sc.get("failed_checks")) if sc else None),
                termination=rec.get("termination_condition") or (Path(d / ".cond").read_text().strip() if (d / ".cond").exists() else None), objective=rec.get("objective"),
                solve_seconds=rec.get("solve_seconds"), peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30 or None,
                c1=dict(grade=g.get("grade"), a=g.get("a"), b=g.get("b"), c=g.get("c"), reference=("batch" if src.startswith("this batch") else ("default" if src else None)),
                        regrades=len(prec.get("grade_history") or [])) if prec else None,
                v6=acc.get("label"), v6_provisional=(prov or {}).get("label"),
                g1=dict((k, (acc.get("G1") or {}).get(k)) for k in ("a", "b", "c")) if acc else None,
                g2=dict((k, ((acc.get("G2") or {}).get(k) or {}).get("passed")) for k in ("G2_1", "G2_2", "G2_3")) if acc else None,
                owen_usable=((oreg or {}).get("new") or {}).get("usable_for_allocation", owen.get("usable_for_allocation")) if owen else None,
                postproc_errors=[f"{e['step']}:exit={e['exit']}" for e in postproc_errors(out) if e["rid"] == rid])


def base_check(nets: Path, registered: bool = True) -> dict:
    """The two 365x24h v2 networks against their build receipts (daily_network.sha256, 365 snapshots, code_sha = build commit) and - in a formal
    run - the registered SHA256 / bytes of RUN_PLAN_DFX.md section 1. registered=False (runner stand-in tests on synthetic files only, with
    ALLOW_UNREGISTERED=1) keeps the receipt checks and records the registered comparison as information."""
    rows = {}
    for sc in ("integrated", "disconnected"):
        f = nets / f"{sc}_365_24h_unsolved.nc"; rec = jl(nets / f"{sc}_BUILD_RECEIPT.json") or {}; daily = rec.get("daily_network") or {}
        have = sha(f) if f.exists() else None; size = f.stat().st_size if f.exists() else None
        reg_ok = bool(have) and have == REGISTERED_SHA[f.name] and size == REGISTERED_BYTES[f.name]
        rec_ok = bool(have) and have == daily.get("sha256") and rec.get("code_sha") == BUILD_COMMIT and int(daily.get("snapshots") or 0) == 365
        rows[f.name] = dict(file=str(f), bytes=size, sha256=have, receipt_sha256=daily.get("sha256"), receipt_snapshots=daily.get("snapshots"), receipt_code_sha=rec.get("code_sha"),
                            registered_sha256=REGISTERED_SHA[f.name], registered_bytes=REGISTERED_BYTES[f.name], receipt_equal=rec_ok, registered_equal=reg_ok,
                            equal=rec_ok and (reg_ok or not registered))
    no_2920 = sorted(p.name for p in nets.glob("*_2920_3h_*"))
    return dict(script=SCRIPT, networks=rows, all_equal=all(v["equal"] for v in rows.values()) and not no_2920, files_2920x3h_present=no_2920,
                registered_checked=registered, build_commit=BUILD_COMMIT, solver_runs=0)


def stop_class(d: Path) -> dict:
    """Class of a run whose GATES_V6 label is not ACCEPTED_* (the third-batch classes, RUN_PLAN_DFX 3.3): g2 (a G2 check failed; without a
    solution only input SHA256 + configuration subset), nosol (no returned solution), c1a (C1 (a) failed or not computable), ref_dependent
    (only (b) / (c): never a stop). DFX: V1 and V2 are both batch reference runs, so g2 / nosol / c1a stop the batch."""
    rid = d.name; acc = jl(d / "V6_ACCEPTANCE.json"); run = jl(d / "RUN.json") or {}; rec = jl(d / "SOLVE_RECEIPT.json") or {}
    sol = (d / "solution" / "X.npy").exists() and bool(rec.get("solution"))
    failed, label = [], (acc or {}).get("label")
    if acc is None:
        cls, failed = "g2", ["V6_ACCEPTANCE.json missing or unreadable"]
    elif label in ("ACCEPTED_LAYER1", "ACCEPTED_LAYER2"):
        cls = "accepted"
    else:
        G2 = acc.get("G2") or {}
        if sol:
            failed = [k for k in ("G2_1", "G2_2", "G2_3") if not (G2.get(k) or {}).get("passed")]
        else:
            if (rec.get("input_network") or {}).get("sha256"):
                sha_ok = bool((G2.get("G2_1") or {}).get("sha256_equal"))
            else:
                sha_ok = bool(run.get("network_sha256")) and run.get("network_sha256") == run.get("registered_sha256")
            sub_ok = bool((G2.get("G2_2") or {}).get("passed")) if "config_subset" in rec else True
            failed = [k for k, ok in (("G2_1_input_sha256", sha_ok), ("G2_2", sub_ok)) if not ok]
        if failed:
            cls = "g2"
        elif not sol:
            cls = "nosol"
        elif not (acc.get("G1") or {}).get("a"):
            cls = "c1a"
        else:
            cls = "ref_dependent"
    action = "stop" if (cls == "g2" or (cls in ("nosol", "c1a") and rid in STOP_ALWAYS)) else ("unusable" if cls in ("nosol", "c1a") else "none")
    res = dict(script=SCRIPT, rid=rid, label=label, solution_returned=sol, cls=cls, action=action, failed_checks=failed,
               g2_checked=("all" if sol else "input only (no solution: network SHA256, configuration subset)"),
               rule="RUN_PLAN_DFX 3.3: G2 failed -> stop; V1 / V2 are both batch reference runs: no solution / C1 (a) failed -> stop; C1 (b) / (c) only -> no stop", solver_runs=0)
    (d / "STOP_CLASS.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def b6_gate(out: Path) -> dict | None:
    """B6 = V2 - V1 (gate_b6_cost of v5_gates, as the third batch's R2 - R1)."""
    i, d = run_state(out, "V1"), run_state(out, "V2")
    if i["objective"] is None or d["objective"] is None:
        return None
    sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "v5"))
    from v5_gates import gate_b6_cost
    g = gate_b6_cost(float(i["objective"]), float(d["objective"]), "integrated", "disconnected")
    return dict(g, b6_bn=bn(g["difference"]), runs=dict(integrated="V1", disconnected="V2"), labels=dict(V1=i["v6"], V2=d["v6"]))


def comparison(out: Path, runs: dict, b6: dict | None, ref: dict | None) -> dict | None:
    """Description only (RUN_PLAN_DFX 3.4 items 5-6; never an acceptance criterion). Main reference (user amendment 2026-10-27) = the third-batch
    R3 / R4 (same profile formal_barrier_1e6_t16, optimal); R1 / R2 (profile formal_barrier, the values of the stage reports) listed alongside:
    objective, B6, Owen dual-form allocation at the main alpha, ledger totals; and the realised delta B6 against the registered first-order prediction."""
    if not ref:
        return None
    r = ref.get("batch3") or {}; fo = ref.get("first_order") or {}
    obj = {"V1": runs["V1"]["objective"], "V2": runs["V2"]["objective"]}; oe = r.get("objective_eur") or {}
    pairs = {"main": r.get("main_runs") or {}, "alternative": r.get("alternative_runs") or {}}
    res = dict(reference_file=ref.get("source"), main_runs=pairs["main"], alternative_runs=pairs["alternative"], batch3_objective_eur=oe,
               batch3_b6_bn=r.get("b6_bn"), batch3_b6_alternative_bn=r.get("b6_alternative_bn"), objective_difference_bn={},
               first_order=dict(predicted_delta_b6_bn=fo.get("delta_b6_bn"), predicted_b6_bn=fo.get("predicted_b6_bn"), predicted_b6_alternative_bn=fo.get("predicted_b6_alternative_bn"),
                                delta_c_integrated_bn=fo.get("delta_c_integrated_bn"), delta_c_disconnected_bn=fo.get("delta_c_disconnected_bn"), by_country_bn=fo.get("by_country_bn"), note=fo.get("note")))
    for tag, pair in pairs.items():
        for v, sc in (("V1", "integrated"), ("V2", "disconnected")):
            b3 = pair.get(sc)
            if b3 and obj[v] is not None and oe.get(b3) is not None:
                res["objective_difference_bn"][f"{v}_minus_{b3}"] = bn(obj[v] - oe[b3])
    if b6:
        if r.get("b6_bn") is not None:
            res["delta_b6_bn"] = b6["b6_bn"] - r["b6_bn"]
            res["delta_b6_minus_first_order_bn"] = (res["delta_b6_bn"] - fo["delta_b6_bn"]) if fo.get("delta_b6_bn") is not None else None
        if r.get("b6_alternative_bn") is not None:
            res["delta_b6_alternative_bn"] = b6["b6_bn"] - r["b6_alternative_bn"]
    ow = {rid: owen_main(out / rid) for rid in RUNS}; ro = r.get("owen_alpha_main_eur") or {}
    res["owen_dual_form_alpha_main_bn"] = {rid: {p: bn(v.get(p, 0.0)) for p in COUNTRIES + ("BUNKER",)} for rid, v in ow.items() if v}
    led = {rid: ledger_totals(out / rid) for rid in RUNS}; rl = r.get("ledger_total_eur") or {}
    res["owen_difference_vs_batch3_bn"] = {}; res["ledger_difference_vs_batch3_bn"] = {}
    for tag, pair in pairs.items():
        for v, sc in (("V1", "integrated"), ("V2", "disconnected")):
            b3 = pair.get(sc)
            if b3 and ow.get(v) and ro.get(b3):
                res["owen_difference_vs_batch3_bn"][f"{v}_minus_{b3}"] = {p: bn(ow[v].get(p, 0.0) - ro[b3].get(p, 0.0)) for p in COUNTRIES + ("BUNKER",)}
            if b3 and led.get(v) and rl.get(b3):
                res["ledger_difference_vs_batch3_bn"][f"{v}_minus_{b3}"] = {c: bn(led[v].get(c, 0.0) - rl[b3].get(c, 0.0)) for c in COUNTRIES + ("ASEAN",)}
    return res


def summary(out: Path, reference: Path | None = None) -> dict:
    runs = {rid: run_state(out, rid) for rid in RUNS}
    ben = jl(out / "M12_BENEFIT" / "BENEFIT.json"); ref = jl(reference) if reference else None
    stop = (out / "STOP").read_text().split() if (out / "STOP").exists() else []
    safe = (out / "STOP_SAFE").read_text().strip() if (out / "STOP_SAFE").exists() else None
    b6 = b6_gate(out)
    res = dict(script=SCRIPT, out=str(out), runs=runs, unusable=unusable_runs(out), B6=b6,
               benefit=(dict(computable=ben.get("computable", True), b6_bn=bn(ben.get("b6_eur")), negative_benefit=(ben.get("owen") or {}).get("negative_benefit"), reason=ben.get("reason")) if ben else None),
               comparison=comparison(out, runs, b6, ref), stop_not_accepted=stop, stop_safe=safe, postproc_errors=postproc_errors(out), solver_runs=0)
    (out / "DFX_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    (out / "DFX_SUMMARY.md").write_text(markdown(res))
    return res


def _f(x, fmt="{:.4f}"):
    return "—" if x is None else fmt.format(x)


def markdown(r: dict) -> str:
    pe = ", ".join("{} {} exit={}".format(e["rid"], e["step"], e["exit"]) for e in (r.get("postproc_errors") or []))
    L = ["# DFX 365×24h 筛查汇总（run_dfx.sh 自动生成；只读，未调用求解器）", "",
         f"- 停批（RUN_PLAN_DFX 3.3：任一运行 G2 不通过；V1 / V2 无返回解或 C1 (a) 不通过）：{', '.join(r['stop_not_accepted']) or '无'}；安全停止：{r['stop_safe'] or '无'}",
         f"- 后处理步骤异常或超时（只记录，不改变调度；可用 `POST_ONLY=1` 补做）：{pe or '无'}", "",
         "## 运行", "", "| 运行 | 作用 | 档案 | 状态 | 终止 | 目标 bn | 求解 s | 峰值 GiB | C1 abc | C1 参照 | 重评次数 | GATES_V6 | 临时标签 | Owen 可用 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for rid, v in r["runs"].items():
        c1 = v["c1"] or {}; abc = "".join("1" if c1.get(k) else "0" for k in ("a", "b", "c")) if c1 else "—"
        L.append(f"| {rid} | {v['role']} | {v['profile']} | {v['state']} | {v['termination'] or '—'} | {_f(bn(v['objective']))} | {_f(v['solve_seconds'], '{:.0f}')} | "
                 f"{_f(v['peak_rss_gib'], '{:.2f}')} | {abc} | {c1.get('reference') or '—'} | {c1.get('regrades', '—')} | {v['v6'] or '—'} | {v['v6_provisional'] or '—'} | {v['owen_usable']} |")
    b6 = r["B6"]
    L += ["", "## B6（V2 − V1）", "", (f"- B6 = {b6['b6_bn']:.4f} bn EUR2020（门槛 `B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED`：{b6['passed']}；标签 V1 {b6['labels']['V1']}，V2 {b6['labels']['V2']}）"
                                          if b6 else "- 不可计算（V1 或 V2 无目标值）")]
    if r["benefit"]:
        L.append(f"- M12 受益与比例规则对照：{'B6 ' + _f(r['benefit']['b6_bn']) + ' bn；负受益 ' + str(r['benefit']['negative_benefit']) if r['benefit']['computable'] else '不可计算：' + str(r['benefit']['reason'])}（`M12_BENEFIT/`）")
    c = r.get("comparison")
    L += ["", "## 与第三批及一阶预测的对比（只描述，不作验收依据；RUN_PLAN_DFX 3.4 第 5–6 项；主参照 R3 / R4 同档案 optimal，R1 / R2 并列）", ""]
    if c:
        od = c["objective_difference_bn"]; fo = c["first_order"]; m = c.get("main_runs") or {}; a = c.get("alternative_runs") or {}
        L += [f"- 主参照 B6（{m.get('disconnected', '?')} − {m.get('integrated', '?')}）{_f(c['batch3_b6_bn'])} bn；本批 B6 {_f((b6 or {}).get('b6_bn'))} bn；ΔB6 实际 {_f(c.get('delta_b6_bn'), '{:+.4f}')} bn，一阶预测 {_f(fo.get('predicted_delta_b6_bn'), '{:+.4f}')} bn，差 {_f(c.get('delta_b6_minus_first_order_bn'), '{:+.4f}')} bn",
              f"- 并列参照 B6（{a.get('disconnected', '?')} − {a.get('integrated', '?')}）{_f(c.get('batch3_b6_alternative_bn'))} bn；ΔB6 对其 {_f(c.get('delta_b6_alternative_bn'), '{:+.4f}')} bn",
              "- 目标值差（bn）：" + "；".join(f"{k.replace('_minus_', ' − ')} {v:+.4f}" for k, v in od.items()) + f"（一阶 ΔC_一体化 {_f(fo.get('delta_c_integrated_bn'), '{:+.4f}')}，ΔC_不互联 {_f(fo.get('delta_c_disconnected_bn'), '{:+.4f}')}）"]
        for key, row in (c.get("owen_difference_vs_batch3_bn") or {}).items():
            L.append(f"- Owen 对偶形式（α 主值）分摊差 {key.replace('_minus_', ' − ')}：" + ", ".join(f"{p} {v:+.3f}" for p, v in row.items()))
        if fo.get("by_country_bn"):
            L.append("- 一阶预测的分国受益变化（bn EUR）：" + ", ".join(f"{p} {v:+.3f}" for p, v in fo["by_country_bn"].items()))
    else:
        L.append("- 未提供第三批参照文件（`--reference`）")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("runtable"); sub.add_parser("schedule"); sub.add_parser("limits")
    b = sub.add_parser("base-check"); b.add_argument("--nets", type=Path, required=True); b.add_argument("--out", type=Path, required=True); b.add_argument("--no-registered", action="store_true")
    k = sub.add_parser("build-check"); k.add_argument("--dir", type=Path, required=True); k.add_argument("--repo", type=Path, required=True)
    q = sub.add_parser("stop-class"); q.add_argument("--dir", type=Path, required=True)
    s = sub.add_parser("summary"); s.add_argument("--out-dir", type=Path, required=True); s.add_argument("--reference", type=Path, default=None)
    a = ap.parse_args()
    if a.cmd == "runtable":
        for rid, r in RUNS.items():
            print("|".join([rid, r["scenario"], r["base"], r["set"], r["profile"], r["costs"]]))
    elif a.cmd == "schedule":
        for phase, la, lb in SCHEDULE:
            print("|".join([phase, ",".join(la), ",".join(lb)]))
    elif a.cmd == "limits":
        for rid, tl in TIME_LIMIT_S.items():
            print("|".join([rid, str(tl), str(tl + WALL_MARGIN_S)]))
    elif a.cmd == "base-check":
        r = base_check(a.nets, registered=not a.no_registered); a.out.write_text(json.dumps(r, indent=1) + "\n")
        print("all_equal" if r["all_equal"] else "DIFFERENT:" + ",".join(k for k, v in r["networks"].items() if not v["equal"]) + (":2920x3h_present" if r["files_2920x3h_present"] else ""))
        sys.exit(0 if r["all_equal"] else 1)
    elif a.cmd == "build-check":
        r = m10.build_check(a.dir, a.repo)
        print(json.dumps(dict(passed=r["passed"], failed=[k for k, v in r["checks"].items() if not v], lp=r["lp"], peak_rss_gib=round(r["peak_rss_gib"], 2)), default=str)); sys.exit(0 if r["passed"] else 1)
    elif a.cmd == "stop-class":
        r = stop_class(a.dir); print(r["cls"], r["action"])
    else:
        r = summary(a.out_dir, a.reference)
        print(json.dumps(dict(B6_bn=(r["B6"] or {}).get("b6_bn"), runs={k: v["state"] for k, v in r["runs"].items()}, delta_b6_bn=(r["comparison"] or {}).get("delta_b6_bn")), default=str))


if __name__ == "__main__":
    main()
