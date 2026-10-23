"""M10P (instruction sections 2-5; items 133, 138-141; supplement 01): run table, schedule and read-only helpers of the third-batch runner
research/06_scope_redesign/p1_m10p_20261022/cloud_package/run_batch3.sh. Never calls a solver; reads solve results and never changes them
(writes only its own JSON / Markdown outputs).

    python scripts_project/m10_batch3_summary.py runtable                       -> "RID|scenario|base|set|profile|costs" per run (the runner's table)
    python scripts_project/m10_batch3_summary.py schedule                       -> "phase|lane A rids|lane B rids" per phase (comma-separated)
    python scripts_project/m10_batch3_summary.py base-check --nets <networks> --out <json>
    python scripts_project/m10_batch3_summary.py variants-expected --variants <OUT/variants> --out <EXPECTED_VARIANTS.json>
    python scripts_project/m10_batch3_summary.py variants-check --variants <OUT/variants> --expected <EXPECTED_VARIANTS.json> --rid R5
    python scripts_project/m10_batch3_summary.py build-check --dir <OUT/R1> --repo <code>   (dry run: LP built, parameters, paths)
    python scripts_project/m10_batch3_summary.py stop-class --dir <OUT/R5>      -> OUT/R5/STOP_CLASS.json; prints "<class> <action>" (graded stop rule)
    python scripts_project/m10_batch3_summary.py level2 --out-dir <OUT>         -> OUT/LEVEL2.json (input of gates_v6.py select-profile)
    python scripts_project/m10_batch3_summary.py summary --out-dir <OUT>        -> OUT/BATCH3_SUMMARY.json / .md (B6, sensitivity differences, ...)
    python scripts_project/m10_batch3_summary.py p1 --dir <probe dir> --log <scrubbed Gurobi log> --out <P1_SUMMARY.json>
      (2920x3h probe parser; P1 left the third batch - supplement 01 item 3 - and is kept for the memory probe at the start of the fourth batch)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = "scripts_project/m10_batch3_summary.py"
A, T16 = "formal_barrier", "formal_barrier_1e6_t16"
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
# Pre-registered run table (RUN_PLAN.md section 2). set = the one m08a_variants.py --set of a variant run ("" = the base network itself);
# costs = the build whose costs_active_research.csv the run gets (s2_solve --costs-table; --costs of the country-WACC variants).
RUNS = {
    "R1": dict(scenario="integrated", base="integrated_365_24h", set="", profile=A, costs="integrated", role="本批参照（一体化）、Owen 分摊、c(N)"),
    "R2": dict(scenario="disconnected", base="disconnected_365_24h", set="", profile=A, costs="disconnected", role="本批参照（不互联）、B6"),
    "R3": dict(scenario="integrated", base="integrated_365_24h", set="", profile=T16, costs="integrated", role="第二级容差验证，对 R1（第 127 项）"),
    "R4": dict(scenario="disconnected", base="disconnected_365_24h", set="", profile=T16, costs="disconnected", role="第二级容差验证，对 R2（第 127 项）"),
    "R5": dict(scenario="integrated", base="integrated_365_24h", set="coalition.remove_countries=[VN]", profile=A, costs="integrated", role="去 VN 复核（第 133、139 项）"),
    "R6": dict(scenario="integrated", base="integrated_365_24h", set="coalition.remove_countries=[TH]", profile=A, costs="integrated", role="去 TH 复核（第 133、139 项）"),
    "R7": dict(scenario="integrated", base="integrated_365_24h", set="coalition.remove_countries=[LA]", profile=A, costs="integrated", role="去 LA 复核（第 133、139 项）"),
    "R8": dict(scenario="disconnected", base="disconnected_365_24h", set="disconnected.co2_shipping_intra_asean=forbid", profile=A, costs="disconnected", role="敏感性 b1：禁止区内 CO2 跨境运输（第 132 项）"),
    "R9": dict(scenario="disconnected", base="integrated_365_24h", set="cross_border.stock_mode=keep_stock_no_new", profile=A, costs="integrated", role="敏感性：不互联保留存量（第 132 项 2a）"),
    "R10": dict(scenario="integrated", base="integrated_365_24h", set="finance.wacc_mode=country_specific", profile=A, costs="integrated", role="敏感性：分国 WACC，一体化（第 132 项第 5 项）"),
    "R11": dict(scenario="disconnected", base="disconnected_365_24h", set="finance.wacc_mode=country_specific", profile=A, costs="disconnected", role="敏感性：分国 WACC，不互联（第 132 项第 5 项）"),
}
# Pre-registered order (RUN_PLAN.md section 3.2; supplement 01 item 1): per phase two lanes, each lane one run after the other; the lanes run side
# by side when the largest Threads of lane A plus that of lane B fit the container cores (phase 2: T16 + A = 24 <= 25), otherwise as one lane
# taking the runs of A and B in turn. R3 and R4 (Threads 16) share a lane, so two T16 sessions never run at the same time.
SCHEDULE = [("1", ["R1"], ["R2"]), ("2", ["R3", "R4"], ["R5", "R6"]), ("3", ["R7", "R9", "R11"], ["R8", "R10"])]
STOP_ALWAYS = ("R1", "R2")   # graded stop rule: no returned solution / C1 (a) failed stops the batch only for the batch reference runs
LOO = {"R5": "VN", "R6": "TH", "R7": "LA"}
SENSITIVITY = [("R8", "R2", "b1：禁止区内 CO2 跨境运输（不互联）"), ("R9", "R2", "不互联保留存量"), ("R10", "R1", "分国 WACC（一体化）"), ("R11", "R2", "分国 WACC（不互联）")]
INFORMATION_PAIRS = [("R11", "R10", "分国 WACC 下的 B6（信息项，不在事先登记的判定中）")]
LEVEL2 = {"integrated": ("R3", "R1"), "disconnected": ("R4", "R2")}
BASE_RECEIPT = {"integrated_365_24h": ("integrated", "daily_network"), "disconnected_365_24h": ("disconnected", "daily_network")}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jl(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def bn(x):
    return None if x is None else float(x) / 1e9


# --------------------------------------------------------------------------------------------- inputs and variants
def base_check(nets: Path) -> dict:
    """Base networks of the package against their build receipts (daily_network SHA256 for 365x24h, network SHA256 for 2920x3h)."""
    rows = {}
    for base, (scen, key) in BASE_RECEIPT.items():
        f = nets / f"{base}_unsolved.nc"; rec = jl(nets / f"{scen}_BUILD_RECEIPT.json") or {}
        want = (rec.get(key) or {}).get("sha256"); got = sha(f) if f.exists() else None
        rows[base] = dict(file=f.name, sha256=got, receipt_sha256=want, receipt=f"{scen}_BUILD_RECEIPT.json:{key}", equal=bool(got and got == want))
    return dict(script=SCRIPT, networks=rows, all_equal=all(r["equal"] for r in rows.values()))


def variant_receipt(vdir: Path, rid: str) -> dict | None:
    rs = sorted((vdir / rid).glob("*_VARIANT_RECEIPT.json"))
    return jl(rs[0]) if len(rs) == 1 else None


def variants_expected(vdir: Path) -> dict:
    out = {}
    for rid, r in RUNS.items():
        if not r["set"]:
            continue
        v = variant_receipt(vdir, rid)
        if v is None:
            continue
        out[rid] = dict(set=r["set"], base_file=Path(v["base"]["path"]).name, base_sha256=v["base"]["sha256"], output_file=Path(v["output"]["path"]).name,
                        output_sha256=v["output"]["sha256"], output_bytes=v["output"].get("bytes"), scenario=v["output"].get("scenario"),
                        research_config_sha256=v.get("research_config_sha256"), research_config_subset_sha256=v.get("research_config_subset_sha256"),
                        stale_config=(v.get("base") or {}).get("stale_config"))
    return out


def variants_check(vdir: Path, expected: dict, rid: str) -> dict:
    v = variant_receipt(vdir, rid); e = (expected or {}).get(rid)
    if v is None or e is None:
        return dict(rid=rid, equal=False, reason="variant receipt missing" if v is None else "no expected entry")
    f = Path(v["output"]["path"])
    file_ok = f.exists() and sha(f) == v["output"]["sha256"]
    eq = dict(output_sha256=v["output"]["sha256"] == e["output_sha256"], base_sha256=v["base"]["sha256"] == e["base_sha256"],
              output_file=f.name == e["output_file"], file_equals_receipt=file_ok, not_stale=not (v.get("base") or {}).get("stale_config"))
    return dict(rid=rid, equal=all(eq.values()), checks=eq, output_sha256=v["output"]["sha256"], expected_sha256=e["output_sha256"], file=str(f))


# --------------------------------------------------------------------------------------------- dry-run build check
def build_check(d: Path, repo: Path) -> dict:
    """A run of the local dry run (s2_solve --stop-before-solve): LP built and exported, parameters = registered profile + TimeLimit, the input
    network = the one registered for the run, GATES_V6 G2.2 subset hash equal already before the solve, outputs inside the run folder, no solver log."""
    import yaml
    run = jl(d / "RUN.json") or {}; rec = jl(d / "SOLVE_RECEIPT.json") or {}
    prof = yaml.safe_load((Path(repo) / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"].get(run.get("profile"), {})
    want = dict(prof, TimeLimit=float(run.get("time_limit") or 0))
    inp = rec.get("input_network") or {}; lp = rec.get("lp") or {}; cs = rec.get("config_subset") or {}
    snaps = int(run.get("truncate") or 0) or (2920 if "2920_3h" in str(run.get("network")) else 365)
    checks = dict(stopped_before_solve=bool(rec.get("stop_before_solve")) and rec.get("optimize_calls") == 0 and "termination_condition" not in rec,
                  no_solver_log=not (d / "gurobi.linopy.log").exists(),
                  parameters_equal_profile=rec.get("solver_parameters") == want, profile=rec.get("solver_profile") == run.get("profile"),
                  scenario=rec.get("scenario") == run.get("scenario"), network_sha256=inp.get("sha256") == run.get("network_sha256"),
                  registered_sha256_equal=run.get("registered_sha256") == inp.get("sha256"), snapshots=inp.get("snapshots") == snaps,
                  g2_2_subset_equal=bool(cs.get("network")) and cs.get("network") == cs.get("current"),
                  lp_built=int(lp.get("num_row") or 0) > 0 and int(lp.get("num_col") or 0) > 0, lp_exported=(d / "lp" / "MATH_PROBLEM.json").exists(),
                  output_is_run_dir=Path(run.get("output", "")).resolve() == d.resolve(),
                  costs_table_exists=Path(run.get("costs_table", "")).exists())
    res = dict(script=SCRIPT, rid=run.get("rid"), passed=all(checks.values()), checks=checks, profile=run.get("profile"), parameters=rec.get("solver_parameters"),
               lp=dict(num_row=lp.get("num_row"), num_col=lp.get("num_col"), nnz=lp.get("nnz"), build_seconds=lp.get("build_seconds")),
               peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30, network=run.get("network"), network_sha256=inp.get("sha256"), solver_runs=0)
    (d / "BUILD_CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


# --------------------------------------------------------------------------------------------- graded stop rule (supplement 01 item 2)
def stop_class(d: Path) -> dict:
    """Class of a run whose GATES_V6 label is not ACCEPTED_* (RUN_PLAN.md section 3.3; supplement 01 item 2):
      g2             a G2 check failed: with a returned solution every G2 check; without one only the checks that need no solution - input network
                     SHA256 = registered value, configuration subset hash (the pre-solve receipt holds both; a run ended before its receipt was
                     written falls back to the runner's SHA256 in RUN.json and has no subset hash to check). V6_ACCEPTANCE.json missing or
                     unreadable counts as g2;
      nosol          no returned solution (solution/X.npy missing: wall-clock kill, solver failure, out of memory, no solution at the time limit);
      c1a            solution returned, C1 (a) failed or C1 not computable;
      ref_dependent  only C1 (b) / (c) failed (item 138 D12: no stop).
    action: g2 -> stop (any run); nosol / c1a -> stop for R1, R2 (the batch reference would be missing), unusable for R3-R11 (recorded, the batch
    goes on); otherwise none."""
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
    if cls == "g2" or (cls in ("nosol", "c1a") and rid in STOP_ALWAYS):
        action = "stop"
    elif cls in ("nosol", "c1a"):
        action = "unusable"
    else:
        action = "none"
    res = dict(script=SCRIPT, rid=rid, label=label, solution_returned=sol, cls=cls, action=action, failed_checks=failed,
               g2_checked=("all" if sol else "input only (no solution: network SHA256, configuration subset)"),
               rule="supplement 01 item 2: G2 failed -> stop (any run); no solution / C1 (a) failed -> stop for R1, R2, unusable for R3-R11", solver_runs=0)
    (d / "STOP_CLASS.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def unusable_runs(out: Path) -> dict:
    p = out / "UNUSABLE"
    return dict(x.split()[:2] for x in p.read_text().splitlines() if len(x.split()) >= 2) if p.exists() else {}


def postproc_errors(out: Path) -> list:
    """M10A: post-processing steps that crashed or timed out (runner file POSTPROC_ERRORS: '<rid> <step> exit=<n> <utc>'); recorded only - the
    schedule never changed because of them; redo with POST_ONLY=1. Missing C1 / GATES_V6 inputs are judged by the registered rules as before."""
    p = out / "POSTPROC_ERRORS"
    rows = []
    for x in (p.read_text().splitlines() if p.exists() else []):
        f = x.split()
        if len(f) >= 3:
            rows.append(dict(rid=f[0], step=f[1], exit=f[2].replace("exit=", ""), utc=(f[3] if len(f) > 3 else None)))
    return rows


# --------------------------------------------------------------------------------------------- per-run state
def run_state(out: Path, rid: str, d: Path | None = None) -> dict:
    """d: the run folder when it is not out/<rid> (M10R --summary-s1 --use: a re-post-processed folder of --repost)."""
    d = Path(d) if d else out / rid; rec = jl(d / "SOLVE_RECEIPT.json") or {}; prec = jl(d / "PRECISION.json") or {}; acc = jl(d / "V6_ACCEPTANCE.json") or {}
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


def ledger_totals(d: Path) -> dict:
    p = d / "COUNTRY_COST_LEDGER.csv"
    if not p.exists():
        return {}
    with open(p) as f:
        rows = list(csv.DictReader(f))
    key = next(iter(rows[0])) if rows else None
    out = {}
    for r in rows:
        try:
            out[r[key]] = float(r["total"])
        except (KeyError, TypeError, ValueError):
            continue
    out["ASEAN"] = sum(v for k, v in out.items() if str(k).startswith("ASEAN") and k != "ASEAN")
    return out


def owen_main(d: Path) -> dict:
    o = jl(d / "m12_owen" / "OWEN.json") or {}
    return dict((o.get("allocation_eur") or {}).get(str(o.get("alpha_main", 0.5)), {})) if o else {}


def pair_difference(out: Path, new: str, base: str, title: str, dirs: dict | None = None) -> dict:
    """new - base: objective, country ledger totals, Owen dual-form allocation (alpha main); usable only when both runs are accepted (a run recorded
    unusable by the graded stop rule is NOT_ACCEPTED). dirs: {rid: folder} overrides of the run folders (M10R --summary-s1 --use)."""
    dirs = dirs or {}; dn, db = dirs.get(new, out / new), dirs.get(base, out / base)
    a, b = run_state(out, new, dn), run_state(out, base, db); un = unusable_runs(out)
    res = dict(new=new, base=base, title=title, new_label=a["v6"], base_label=b["v6"], unusable=sorted(r for r in (new, base) if r in un),
               usable=bool(a["v6"] and b["v6"] and a["v6"] != "NOT_ACCEPTED" and b["v6"] != "NOT_ACCEPTED"),
               reposted=sorted(r for r in (new, base) if r in dirs))
    if a["objective"] is None or b["objective"] is None:
        return dict(res, computable=False, reason="objective missing (run not finished or not solved)")
    la, lb = ledger_totals(Path(dn)), ledger_totals(Path(db))
    oa, ob = owen_main(Path(dn)), owen_main(Path(db))
    led = {c: bn(la.get(c, 0.0) - lb.get(c, 0.0)) for c in COUNTRIES + ("ASEAN",)} if (la and lb) else None
    ow = {p: bn(oa.get(p, 0.0) - ob.get(p, 0.0)) for p in COUNTRIES + ("BUNKER",)} if (oa and ob) else None
    return dict(res, computable=True, objective_difference_bn=bn(a["objective"] - b["objective"]), relative=(a["objective"] - b["objective"]) / abs(b["objective"]),
                ledger_total_difference_bn=led, owen_dual_form_difference_bn=ow)


# --------------------------------------------------------------------------------------------- batch steps
def level2(out: Path) -> dict:
    """LEVEL2.json for gates_v6.py select-profile: both scenarios always present (a missing run gives no C1 flags and no objective, i.e. the
    candidate fails and profile A stays - pre-registered rule 3: the 1e-5 profile is never a fallback)."""
    res = {}
    for sc, (cand, ref) in LEVEL2.items():
        c, r = run_state(out, cand), run_state(out, ref)
        flags = c["g1"] or {k: False for k in ("a", "b", "c")}
        res[sc] = dict(candidate=dict(profile=T16, run=cand, objective=c["objective"], precision={k: bool(flags.get(k)) for k in ("a", "b", "c")}, label=c["v6"]),
                       reference=dict(profile=A, run=ref, objective=r["objective"], label=r["v6"]))
    return res


def b6_gate(out: Path) -> dict | None:
    i, d = run_state(out, "R1"), run_state(out, "R2")
    if i["objective"] is None or d["objective"] is None:
        return None
    sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "v5"))
    from v5_gates import gate_b6_cost
    g = gate_b6_cost(float(i["objective"]), float(d["objective"]), "integrated", "disconnected")
    return dict(g, b6_bn=bn(g["difference"]), runs=dict(integrated="R1", disconnected="R2"), labels=dict(R1=i["v6"], R2=d["v6"]))


def summary(out: Path, use: dict | None = None, into: Path | None = None, name: str = "BATCH3_SUMMARY") -> dict:
    """use: {rid: folder} - runs taken from a re-post-processed folder (M10R --repost); into / name: where the summary is written (the batch's
    BATCH3_SUMMARY.json / .md in out are never rewritten by a supplement summary)."""
    dirs = {k: Path(v) for k, v in (use or {}).items()}
    runs = {rid: run_state(out, rid, dirs.get(rid)) for rid in RUNS}
    loo = jl(out / "M12_LOO" / "LOO_CHECK.json"); ben = jl(out / "M12_BENEFIT" / "BENEFIT.json")
    pc = jl(out / "PROFILE_CHOICE.json")
    stop = (out / "STOP").read_text().split() if (out / "STOP").exists() else []
    safe = (out / "STOP_SAFE").read_text().strip() if (out / "STOP_SAFE").exists() else None
    reposts = {rid: dict((jl(d / "REPOST.json") or {}), label_after=runs[rid]["v6"], folder=str(d), repost_check=jl(d / "REPOST_CHECK.json")) for rid, d in dirs.items()}
    res = dict(script=SCRIPT, out=str(out), name=name, runs=runs, unusable=unusable_runs(out), B6=b6_gate(out),
               sensitivity=[pair_difference(out, *p, dirs=dirs) for p in SENSITIVITY], information=[pair_difference(out, *p, dirs=dirs) for p in INFORMATION_PAIRS],
               level2=jl(out / "LEVEL2.json"), profile_choice=pc,
               loo=(dict(computable=loo.get("computable", True), all_passed=(loo.get("check") or {}).get("all_passed"),
                         indivisible_cost_sign=(loo.get("check") or {}).get("indivisible_cost_sign"),
                         countries={c: dict(margin_bn=bn(v.get("margin")), tolerance_bn=bn(v.get("tolerance")), passed=v.get("passed"),
                                            market_form_passed=v.get("market_form_passed"), same_profile_and_resolution=(v.get("same_profile_and_resolution") or {}).get("profile"))
                                    for c, v in ((loo.get("check") or {}).get("countries") or {}).items()}, reason=loo.get("reason")) if loo else None),
               benefit=(dict(computable=ben.get("computable", True), b6_bn=bn(ben.get("b6_eur")), negative_benefit=(ben.get("owen") or {}).get("negative_benefit"),
                             reason=ben.get("reason")) if ben else None),
               stop_not_accepted=stop, stop_safe=safe, postproc_errors=postproc_errors(out), reposts=reposts, solver_runs=0)
    dst = Path(into) if into else out
    (dst / f"{name}.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    (dst / f"{name}.md").write_text(markdown(res))
    return res


def _strip(o, drop=("seconds", "solve_dir", "network", "out", "written_utc", "script", "label", "repo", "path", "time", "utc", "source", "into")):
    if isinstance(o, dict):
        return {k: _strip(v, drop) for k, v in o.items() if k not in drop}
    return [_strip(v, drop) for v in o] if isinstance(o, list) else o


def repost_check(src: Path, new: Path) -> dict:
    """M10R --repost consistency check: the violation analysis of the repost must equal the original (unchanged code), C1 (a) / (b) numbers must
    equal the original PRECISION.json; B16 / C1 (c) / label before and after are recorded. Written to <new>/REPOST_CHECK.json."""
    va_s, va_n = jl(src / "VIOLATIONS.json"), jl(new / "VIOLATIONS.json")
    ps, pn = jl(src / "PRECISION.json") or {}, jl(new / "PRECISION.json") or {}

    def ab(p):
        a = p.get("a_total_cost") or {}; b = p.get("b_primal_violations") or {}
        return dict(a=[a.get("returned_difference_bn"), a.get("returned_relative")], b={c: v.get("first_order_cost_bn") for c, v in (b.get("country_check") or {}).items()})
    gs, gn = (jl(src / "V5_GATES.json") or {}).get("B16_LEDGER") or {}, (jl(new / "V5_GATES.json") or {}).get("B16_LEDGER") or {}
    res = dict(script=SCRIPT, rid=new.name, source=str(src), repost=str(new),
               violations_equal=bool(va_s is not None and va_n is not None and _strip(va_s) == _strip(va_n)), violations_present=[va_s is not None, va_n is not None],
               c1_ab_equal=bool(ps and pn and ab(ps) == ab(pn)), c1_ab=dict(before=ab(ps), after=ab(pn)),
               c1_c=dict(before=((ps.get("grade") or {}).get("c")), after=((pn.get("grade") or {}).get("c"))),
               b16=dict(before=dict(passed=gs.get("passed"), relative_error=gs.get("relative_error"), error=gs.get("error")), after=dict(passed=gn.get("passed"), relative_error=gn.get("relative_error"), error=gn.get("error"))),
               label_before=(jl(src / "V6_ACCEPTANCE.json") or {}).get("label"), label_after=(jl(new / "V6_ACCEPTANCE.json") or {}).get("label"), solver_runs=0)
    (new / "REPOST_CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


def _f(x, fmt="{:.4f}"):
    return "—" if x is None else fmt.format(x)


def markdown(r: dict) -> str:
    un = ", ".join(f"{k}（{v}）" for k, v in r["unusable"].items())
    pe = ", ".join("{} {} exit={}".format(e["rid"], e["step"], e["exit"]) for e in (r.get("postproc_errors") or []))
    rp = "；".join(f"{k}（{v.get('label_before')} → {v.get('label_after')}，{v.get('folder')}）" for k, v in (r.get("reposts") or {}).items())
    L = [f"# 第三批汇总{'（补做 S1：' + r['name'] + '）' if r.get('name', 'BATCH3_SUMMARY') != 'BATCH3_SUMMARY' else ''}（M10P 运行脚本自动生成；只读，未调用求解器）", "",
         f"- 停批（分级停批规则，补充 01 第 2 项：任一运行 G2 不通过；R1、R2 无返回解或 C1 (a) 不通过）：{', '.join(r['stop_not_accepted']) or '无'}；安全停止：{r['stop_safe'] or '无'}",
         f"- 事后修复的代码缺陷、重做后处理的运行（M10R `--repost`；求解未重做）：{rp or '无'}",
         f"- 记为不可用、继续其余运行（R3–R11 无返回解 nosol 或 C1 (a) 不通过 c1a）：{un or '无'}",
         f"- 后处理步骤异常或超时（M10A；只记录，不改变调度；可用 `POST_ONLY=1` 补做）：{pe or '无'}", "",
         "## 运行", "", "| 运行 | 作用 | 档案 | 状态 | 终止 | 目标 bn | 求解 s | 峰值 GiB | C1 abc | C1 参照 | 重评次数 | GATES_V6 | 临时标签 | Owen 可用 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for rid, v in r["runs"].items():
        c1 = v["c1"] or {}
        abc = "".join("1" if c1.get(k) else "0" for k in ("a", "b", "c")) if c1 else "—"
        L.append(f"| {rid} | {v['role']} | {v['profile']} | {v['state']} | {v['termination'] or '—'} | {_f(bn(v['objective']))} | {_f(v['solve_seconds'], '{:.0f}')} | "
                 f"{_f(v['peak_rss_gib'], '{:.2f}')} | {abc} | {c1.get('reference') or '—'} | {c1.get('regrades', '—')} | {v['v6'] or '—'} | {v['v6_provisional'] or '—'} | {v['owen_usable']} |")
    b6 = r["B6"]
    L += ["", "## B6（R2 − R1）", "", (f"- B6 = {b6['b6_bn']:.4f} bn EUR2020（门槛 `B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED`：{b6['passed']}；标签 R1 {b6['labels']['R1']}，R2 {b6['labels']['R2']}）"
                                          if b6 else "- 不可计算（R1 或 R2 无目标值）")]
    if r["benefit"]:
        L.append(f"- M12 受益与比例规则对照：{'B6 ' + _f(r['benefit']['b6_bn']) + ' bn；负受益 ' + str(r['benefit']['negative_benefit']) if r['benefit']['computable'] else '不可计算：' + str(r['benefit']['reason'])}（`M12_BENEFIT/`）")
    L += ["", "## 敏感性差额（新 − 基准；两边都非 NOT_ACCEPTED 才可用）", "", "| 对比 | 内容 | 可用 | 目标差 bn | 相对 | 分国账本差 bn（11 国 + ASEAN） | Owen 对偶形式差 bn |", "|---|---|---|---|---|---|---|"]
    for p in r["sensitivity"] + r["information"]:
        if not p.get("computable"):
            L.append(f"| {p['new']} − {p['base']} | {p['title']} | {p['usable']} | 不可计算 | — | {p.get('reason')} | — |"); continue
        led = ", ".join(f"{k} {v:+.3f}" for k, v in (p["ledger_total_difference_bn"] or {}).items())
        ow = ", ".join(f"{k} {v:+.3f}" for k, v in (p["owen_dual_form_difference_bn"] or {}).items())
        L.append(f"| {p['new']} − {p['base']} | {p['title']} | {p['usable']} | {p['objective_difference_bn']:+.4f} | {p['relative']:+.2e} | {led or '—'} | {ow or '—'} |")
    pc = r["profile_choice"] or {}
    L += ["", "## 第二级比较与第四批档案（事先登记规则 3）", "", f"- 选择：**{pc.get('profile', '—')}**；理由：{pc.get('reason', '—')}"]
    for sc, v in (pc.get("level2") or {}).items():
        L.append(f"- {sc}：C1 {v.get('c1')}，目标相对差 {_f(v.get('objective_rel_diff'), '{:.2e}')}，通过 {v.get('passed')}")
    lo = r["loo"]
    L += ["", "## 去一国检查（R1 = c(N)，R5–R7）", ""]
    if lo and lo.get("countries"):
        L += [f"- 全部通过：{lo['all_passed']}；不可分成本符号：{lo['indivisible_cost_sign']}", "", "| 国 | 余量 bn | 容差 bn | 通过 | 市场形式通过 | 同档案 |", "|---|---|---|---|---|---|"]
        L += [f"| {c} | {_f(v['margin_bn'])} | {_f(v['tolerance_bn'])} | {v['passed']} | {v['market_form_passed']} | {v['same_profile_and_resolution']} |" for c, v in lo["countries"].items()]
    else:
        L.append(f"- 不可计算或未运行：{(lo or {}).get('reason', '无去一国结果')}")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------------------------- 2920x3h probe (fourth batch; supplement 01 item 3)
ITER = re.compile(r"^\s*(\d+)\s+([-+]?\d\.\d+e[+-]\d+)\s+([-+]?\d\.\d+e[+-]\d+)\s+\S+\s+\S+\s+\S+\s+(\d+)s\s*$")


def p1_summary(d: Path, log: Path | None) -> dict:
    """P1: LP build time (receipt), model / presolve / ordering lines and barrier iteration times of the scrubbed Gurobi log, peak memory of the
    monitor (process group RSS, container cgroup) and of the s2_solve sampler; how the run ended (wall-clock kill, out of memory, finished)."""
    rec = jl(d / "SOLVE_RECEIPT.json") or {}; run = jl(d / "RUN.json") or {}
    res = dict(script=SCRIPT, rid="P1", network=run.get("network"), profile=run.get("profile"), wall_cap_s=run.get("wall_cap_s"), time_limit_s=run.get("time_limit"),
               ended=(Path(d / ".cond").read_text().strip() if (d / ".cond").exists() else None), lp=rec.get("lp"),
               lp_build_seconds=(rec.get("lp") or {}).get("build_seconds"), solver_runs_by_this_script=0)
    lines = Path(log).read_text(errors="ignore").splitlines() if (log and Path(log).exists()) else []
    its = []
    for ln in lines:
        m = re.match(r"Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros", ln)
        if m:
            res["model"] = dict(rows=int(m.group(1)), columns=int(m.group(2)), nonzeros=int(m.group(3)))
        m = re.match(r"Presolve time: ([\d.]+)s", ln)
        if m:
            res["presolve_seconds"] = float(m.group(1))
        m = re.match(r"Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros", ln)
        if m:
            res["presolved"] = dict(rows=int(m.group(1)), columns=int(m.group(2)), nonzeros=int(m.group(3)))
        m = re.match(r"Ordering time: ([\d.]+)s", ln)
        if m:
            res["ordering_seconds"] = float(m.group(1))
        m = re.match(r"\s*Factor NZ\s*:\s*(\S+)(?: \(roughly ([\d.]+ [KMGT]B) of memory\))?", ln)
        if m:
            res["factor_nz"] = m.group(1); res["factor_memory_estimate"] = m.group(2)
        m = re.match(r"\s*Factor Ops\s*:\s*(\S+)(?: \(roughly ([^)]*)\))?", ln)
        if m:
            res["factor_ops"] = m.group(1); res["factor_ops_note"] = m.group(2)
        m = ITER.match(ln)
        if m:
            its.append((int(m.group(1)), int(m.group(4))))
        m = re.match(r"Barrier solved model in (\d+) iterations and ([\d.]+) seconds", ln)
        if m:
            res["barrier_solved"] = dict(iterations=int(m.group(1)), seconds=float(m.group(2)))
    res["barrier_iterations_logged"] = len(its)
    if its:
        res["first_iteration_time_s"] = its[0][1]; res["last_iteration"] = dict(iteration=its[-1][0], time_s=its[-1][1])
        steps = [b[1] - a[1] for a, b in zip(its, its[1:]) if b[0] == a[0] + 1]
        if steps:
            res["seconds_per_iteration_median"] = statistics.median(steps); res["seconds_per_iteration_mean"] = sum(steps) / len(steps)
            res["extrapolation_note"] = ("INFERENCE: the pilot 365x24h integrated needed 408 iterations (S4N); at the median step a 2920x3h run of "
                                         f"300 / 400 / 500 iterations would take ~{300 * res['seconds_per_iteration_median'] / 3600:.1f} / "
                                         f"{400 * res['seconds_per_iteration_median'] / 3600:.1f} / {500 * res['seconds_per_iteration_median'] / 3600:.1f} h after the first iteration")
    mon = d.parent / "MONITOR_P1.csv"
    if mon.exists():
        with open(mon) as f:
            rows = list(csv.DictReader(f))

        def mx(k):
            v = [float(r[k]) for r in rows if r.get(k) not in (None, "")]
            return max(v) if v else None
        res.update(peak_rss_gib_monitor=mx("rss_gib_group"), peak_cgroup_gib_monitor=mx("cgroup_mem_used_gib"), cgroup_limit_gib=mx("cgroup_mem_limit_gib"),
                   monitor_samples=len(rows), monitor_last_elapsed_s=mx("elapsed_s"))
    res["peak_rss_gib_sampler"] = (rec.get("peak_rss_bytes") or 0) / 2**30 or None
    tm = d / "solve.err"
    if tm.exists():
        m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", tm.read_text(errors="ignore"))
        res["peak_rss_gib_time"] = int(m.group(1)) / 1048576 if m else None
    return res


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("runtable"); sub.add_parser("schedule")
    b = sub.add_parser("base-check"); b.add_argument("--nets", type=Path, required=True); b.add_argument("--out", type=Path, required=True)
    e = sub.add_parser("variants-expected"); e.add_argument("--variants", type=Path, required=True); e.add_argument("--out", type=Path, required=True)
    c = sub.add_parser("variants-check"); c.add_argument("--variants", type=Path, required=True); c.add_argument("--expected", type=Path, required=True); c.add_argument("--rid", required=True)
    k = sub.add_parser("build-check"); k.add_argument("--dir", type=Path, required=True); k.add_argument("--repo", type=Path, required=True)
    q = sub.add_parser("stop-class"); q.add_argument("--dir", type=Path, required=True)
    for name in ("level2", "summary"):
        s = sub.add_parser(name); s.add_argument("--out-dir", type=Path, required=True)
        if name == "summary":   # M10R --summary-s1: runs from re-post-processed folders, written elsewhere under another name
            s.add_argument("--use", action="append", default=[], help="RID=<folder> (a --repost output) instead of <out-dir>/RID")
            s.add_argument("--into", type=Path, default=None); s.add_argument("--name", default="BATCH3_SUMMARY")
    rc = sub.add_parser("repost-check"); rc.add_argument("--src", type=Path, required=True); rc.add_argument("--new", type=Path, required=True)
    p = sub.add_parser("p1"); p.add_argument("--dir", type=Path, required=True); p.add_argument("--log", type=Path, default=None); p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.cmd == "runtable":
        for rid, r in RUNS.items():
            print("|".join([rid, r["scenario"], r["base"], r["set"], r["profile"], r["costs"]]))
    elif a.cmd == "schedule":
        for phase, la, lb in SCHEDULE:
            print("|".join([phase, ",".join(la), ",".join(lb)]))
    elif a.cmd == "base-check":
        r = base_check(a.nets); a.out.write_text(json.dumps(r, indent=1) + "\n")
        print("all_equal" if r["all_equal"] else "DIFFERENT:" + ",".join(k for k, v in r["networks"].items() if not v["equal"])); sys.exit(0 if r["all_equal"] else 1)
    elif a.cmd == "variants-expected":
        r = variants_expected(a.variants); a.out.write_text(json.dumps(r, indent=1, sort_keys=True) + "\n"); print(len(r), "variants")
    elif a.cmd == "variants-check":
        r = variants_check(a.variants, jl(a.expected), a.rid)
        print(("equal" if r["equal"] else "DIFFERENT") + f":{r.get('output_sha256', '')}:expected={r.get('expected_sha256', '')}:{r.get('reason', '')}"); sys.exit(0 if r["equal"] else 1)
    elif a.cmd == "build-check":
        r = build_check(a.dir, a.repo)
        print(json.dumps(dict(passed=r["passed"], failed=[k for k, v in r["checks"].items() if not v], lp=r["lp"], peak_rss_gib=round(r["peak_rss_gib"], 2)), default=str)); sys.exit(0 if r["passed"] else 1)
    elif a.cmd == "stop-class":
        r = stop_class(a.dir); print(r["cls"], r["action"])
    elif a.cmd == "level2":
        r = level2(a.out_dir); (a.out_dir / "LEVEL2.json").write_text(json.dumps(r, indent=1) + "\n"); print(json.dumps({k: v["candidate"]["precision"] for k, v in r.items()}))
    elif a.cmd == "summary":
        use = dict(u.split("=", 1) for u in a.use)
        if any(k not in RUNS for k in use):
            raise SystemExit(f"--use: unknown run id in {sorted(use)}")
        r = summary(a.out_dir, use or None, a.into, a.name); print(json.dumps(dict(B6_bn=(r["B6"] or {}).get("b6_bn"), runs={k: v["state"] for k, v in r["runs"].items()}, reposts=sorted(use)), default=str))
    elif a.cmd == "repost-check":
        r = repost_check(a.src, a.new)
        print(f"violations_equal={r['violations_equal']}:c1_ab_equal={r['c1_ab_equal']}:c1_c={r['c1_c']['before']}->{r['c1_c']['after']}:b16={r['b16']['before']['passed']}->{r['b16']['after']['passed']}:label={r['label_before']}->{r['label_after']}")
    else:
        r = p1_summary(a.dir, a.log); a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(r, indent=1, default=str) + "\n")
        print(json.dumps({k: r.get(k) for k in ("ended", "lp_build_seconds", "presolve_seconds", "barrier_iterations_logged", "seconds_per_iteration_median", "peak_rss_gib_monitor")}))


if __name__ == "__main__":
    main()
