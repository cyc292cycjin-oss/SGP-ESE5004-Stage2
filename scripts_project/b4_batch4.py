"""B4P (fourth-batch preparation, 2026-10-26; instruction A4): run table and read-only helpers of the fourth-batch runner
research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh. Two runs on the FULL 2920x3h networks of the M08b supplement-01 build
(commit ec80668f; SHA256 registered below): F1 integrated, F2 disconnected, profile formal_barrier_1e6_t16 (PROFILE_CHOICE.json of the third
batch, Threads 16). Never calls a solver; reads solve results and never changes them (writes only its own JSON / Markdown outputs).

    python scripts_project/b4_batch4.py runtable                                -> "RID|scenario|base|set|profile|costs" per run
    python scripts_project/b4_batch4.py base-check --nets <networks> --out <json> (the two 2920x3h networks against the build receipts AND the registered SHA256)
    python scripts_project/b4_batch4.py build-check --dir <OUT/F1> --repo <code>   (dry run: LP built, parameters = profile + TimeLimit; split build or --stop-before-solve)
    python scripts_project/b4_batch4.py receipt-state --receipt <SOLVE_RECEIPT.json>  -> post_solve | split_built | stopped_before_solve | pre_solve | missing | unreadable
    python scripts_project/b4_batch4.py stop-class --dir <OUT/F1>              -> STOP_CLASS.json; prints "<class> <action>" (fourth batch: any class but accepted / ref_dependent stops)
    python scripts_project/b4_batch4.py projection --dir <OUT/F1> --time-limit 259200 --iterations 450 --out <json>   (early speed check, RUN_PLAN_B4 3.4)
    python scripts_project/b4_batch4.py p1 --monitor <MONITOR_F1.csv> --quota-gib 240 --cores 72 --out <json> [--threshold 0.40 --min-cores 33 --window-s 3600]
    python scripts_project/b4_batch4.py memstat [--cgroup-root /sys/fs/cgroup] [--out <json>]   -> anon memory (no file cache) / quota (RUN_PLAN_B4 3.3)
    python scripts_project/b4_batch4.py summary --out-dir <OUT> [--batch3 <third-batch export dir with R1/, R2/>] [--reference-values <REFERENCE_VALUES.json>]  -> OUT/BATCH4_SUMMARY.json / .md
    python scripts_project/b4_batch4.py hpc-plan                                -> the registered limits and PBS jobs of RUN_PLAN_HPC.md (make_pbs.sh, hpr_consistency.py)

HPR (2026-10-27; RUN_PLAN_HPC.md; user decisions B1-B4): the fourth batch runs on the NUS Atlas cluster (PBS Pro) in TWO jobs (F1, F2) plus a
batch-level job. Re-registered here: the v2 2920x3h networks of the DFX build 72083fde (B2), TimeLimit 864,000 s and the derived wall clock (B1),
the PBS resources (B3); the split solve and the profile are unchanged (B4). The thresholds of RUN_PLAN_B4 section 3 are unchanged.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from m10_batch3_summary import COUNTRIES, ITER, bn, jl, ledger_totals, owen_main, postproc_errors, sha, unusable_runs   # noqa: E402

SCRIPT = "scripts_project/b4_batch4.py"
T16 = "formal_barrier_1e6_t16"
LABEL = "BATCH4_2920X3H"
# Pre-registered run table (RUN_PLAN_B4.md section 2): the two base networks themselves (no variant), the third batch's chosen profile.
RUNS = {
    "F1": dict(scenario="integrated", base="integrated_2920_3h", set="", profile=T16, costs="integrated", role="一体化 2920×3h：c(N)、Owen 分摊、B6 基准", iterations_reference=450),
    "F2": dict(scenario="disconnected", base="disconnected_2920_3h", set="", profile=T16, costs="disconnected", role="不互联 2920×3h：B6 = F2 − F1", iterations_reference=250),
}
STOP_ALWAYS = ("F1", "F2")   # both runs are the batch: no returned solution / C1 (a) failed -> recorded unusable AND the batch stops (instruction A4: "第四批只有两个运行")
# Registered inputs (HPR, user decision B2 of 2026-10-27; RUN_PLAN_HPC.md section 1): the v2 2920x3h networks of the DFX build, commit 72083fde.
# Superseded (B4P instruction section 0, M08b supplement 01 builds ec80668f): bca20fc0... 64,106,133 B / b401a687... 63,439,167 B - kept in RUN_PLAN_B4.md.
REGISTERED_SHA = {"integrated_2920_3h_unsolved.nc": "08879f0bede119d77160cdb3f5f3c69dba302540b256b64efa4f16adbbefb271",
                  "disconnected_2920_3h_unsolved.nc": "d90ca99220d448c894c43c071b7e38f8c74e0a101b72878a4bdd941c37b164e7"}
REGISTERED_BYTES = {"integrated_2920_3h_unsolved.nc": 63873447, "disconnected_2920_3h_unsolved.nc": 63202193}
BUILD_COMMIT = "72083fde6bffd89580869af6dd00885a8d76721f"
# Registered limits (HPR, user decision B1; RUN_PLAN_HPC.md section 2) - run_batch4.sh carries the same values as R_TL / R_WALL / R_GAP (asserted equal by
# tests/research/test_hpr_two_jobs.py and by preflight.sh); the other timeouts are the B4P values (RUN_PLAN_B4 3.1 / 3.6, unchanged).
TIME_LIMIT_S = 864000               # 240 h, F1 = F2 (was 259,200 s in RUN_PLAN_B4)
WALL_MARGIN_S = 7200                # B4P 3.1 item 2: 2 x 3,600 s for the LP read and the array write-out of process 2
WALL_CAP_S = TIME_LIMIT_S + WALL_MARGIN_S   # 871,200 s
LICENCE_GAP_S = 330
WAIT_START_MAX_S = 7200             # RUN_PLAN_HPC 4: F2 waits at most this long for F1's Gurobi start marker (F1 process 1 <= 3,600 s + gap + preflight)
BUILD_TIMEOUT_S = 3600; ASSIGN_TIMEOUT_S = 32400; POST_TIMEOUT_S = 10800; PACK_TIMEOUT_S = 7200; POST_MEM_NEED_GIB = 100
POST_ESTIMATE_S = 3900              # per-run post-processing estimate (B4P 6.1: violations / C1 / Owen ~20 min each at 2920, M12 ~1 min)
JOB_OVERHEAD_S = 1800               # job body: records, preflight sections, exports
# Registered PBS jobs (HPR, user decision B3 + RUN_PLAN_HPC.md sections 2-3 and 9): the single source of make_pbs.sh and hpr_consistency.py
HPC_JOBS = {
    "F1": dict(name="hpr_f1", queue="parallel", ncpus=48, mem_gb=300, walltime="255:00:00", mode="formal", rid="F1", depends="", wait_start_of=""),
    "F2": dict(name="hpr_f2", queue="parallel", ncpus=48, mem_gb=250, walltime="257:00:00", mode="formal", rid="F2", depends="after:F1", wait_start_of="F1"),
    "batch": dict(name="hpr_batch", queue="parallel", ncpus=12, mem_gb=120, walltime="12:00:00", mode="batch", rid="batch", depends="afterany:F1:F2", wait_start_of=""),
    "smoke56": dict(name="hpr_smoke56", queue="parallel", ncpus=17, mem_gb=32, walltime="04:00:00", mode="smoke56", rid="all", depends="", wait_start_of=""),
    "build_only_f1": dict(name="hpr_build_only_f1", queue="parallel", ncpus=48, mem_gb=300, walltime="02:30:00", mode="build_only", rid="F1", depends="", wait_start_of=""),
    "install": dict(name="hpr_install", queue="serial", ncpus=1, mem_gb=8, walltime="02:00:00", mode="install", rid="", depends="", wait_start_of=""),
}
SMOKE = dict(truncate=56, time_limit_s=3000, wall_cap_s=3600)   # the 56-snapshot smoke of the job bodies (RUN_PLAN_HPC 9; local H4 drill = the same)
# Expected 56-snapshot smoke results of the v2 2920x3h networks (DFX F5.5 local smoke at commit 896828fd, profile T16, TimeLimit 3,000 s: objective with the
# constant term, barrier iterations); the HPR H4 drill must reproduce them bitwise on this machine, the HPC smoke within a relative 1e-6 (RUN_PLAN_HPC 9)
SMOKE_EXPECTED_OBJECTIVE = {"F1": 340661983874.5359, "F2": 352091303417.9458}
SMOKE_EXPECTED_ITERATIONS = {"F1": 113, "F2": 139}
QUEUE_LIMITS = dict(parallel=dict(mem_gb=540, ncpus_max=96, walltime_h=720, user_cores=96, user_jobs=8), serial=dict(mem_gb=15, ncpus_max=1, walltime_h=720))   # HPC_FACTS_20261026.md
B4P_HIGH_PEAK_GIB = dict(F1=160, F2=149)   # B4P A1 high estimates of the Gurobi process (RUN_PLAN_B4 section 4); H-P4: mem >= 1.25 x


def walltime_s(w: str) -> int:
    h, m, s = (int(x) for x in w.split(":"))
    return h * 3600 + m * 60 + s


def walltime_components() -> dict:
    """RUN_PLAN_HPC.md section 2: the terms of the PBS walltime of F1 / F2 and the registered (rounded-up) values."""
    f1 = LICENCE_GAP_S + BUILD_TIMEOUT_S + WALL_CAP_S + ASSIGN_TIMEOUT_S + 2 * POST_ESTIMATE_S + JOB_OVERHEAD_S
    return dict(terms=dict(runner_start_gap_s=LICENCE_GAP_S, process1_timeout_s=BUILD_TIMEOUT_S, process2_wall_cap_s=WALL_CAP_S, process3_timeout_s=ASSIGN_TIMEOUT_S,
                           post_processing_x2_s=2 * POST_ESTIMATE_S, job_overhead_s=JOB_OVERHEAD_S, f2_wait_start_max_s=WAIT_START_MAX_S),
                sum_f1_s=f1, sum_f2_s=f1 + WAIT_START_MAX_S, registered_f1_s=walltime_s(HPC_JOBS["F1"]["walltime"]), registered_f2_s=walltime_s(HPC_JOBS["F2"]["walltime"]),
                projection_limit_s=PROJECTION_FRACTION * TIME_LIMIT_S)
# Pre-registered stop thresholds (RUN_PLAN_B4.md section 3); the runner reads them from here (single source)
MEMORY_STOP_FRACTION = 0.80         # cgroup anon memory > 80 % of the quota -> STOP_SAFE:MEMORY
PROJECTION_FRACTION = 0.80          # projected total > 80 % of TimeLimit -> STOP_SAFE:PROJECTION
PROJECTION_AFTER_ITERATION = 20     # projection from the average of iterations 11-20
P1_THRESHOLD = 0.40                 # F1 peak within the first P1_WINDOW_S <= 40 % of the quota (and cores >= P1_MIN_CORES) -> F2 in parallel
P1_MIN_CORES = 33
P1_WINDOW_S = 3600


def base_check(nets: Path, registered: bool = True) -> dict:
    """The two full 2920x3h networks against their build receipts (network.sha256, code_sha = build commit) and - in a formal run - the registered
    SHA256 / bytes of the B4P instruction. registered=False (--no-registered: the runner passes it only with ALLOW_UNREGISTERED=1, i.e. stand-in
    tests on synthetic network files) keeps the receipt checks and records the registered comparison as information."""
    rows = {}
    for sc in ("integrated", "disconnected"):
        f = nets / f"{sc}_2920_3h_unsolved.nc"; rec = jl(nets / f"{sc}_BUILD_RECEIPT.json") or {}
        have = sha(f) if f.exists() else None
        reg_ok = bool(have) and have == REGISTERED_SHA[f.name] and f.exists() and f.stat().st_size == REGISTERED_BYTES[f.name]
        rec_ok = bool(have) and have == (rec.get("network") or {}).get("sha256") and rec.get("code_sha") == BUILD_COMMIT
        rows[f.name] = dict(file=str(f), bytes=(f.stat().st_size if f.exists() else None), sha256=have, receipt_sha256=(rec.get("network") or {}).get("sha256"),
                            receipt_code_sha=rec.get("code_sha"), registered_sha256=REGISTERED_SHA[f.name], registered_bytes=REGISTERED_BYTES[f.name],
                            receipt_equal=rec_ok, registered_equal=reg_ok, equal=rec_ok and (reg_ok or not registered))
    return dict(script=SCRIPT, networks=rows, all_equal=all(v["equal"] for v in rows.values()), registered_checked=registered, build_commit=BUILD_COMMIT, solver_runs=0)


def receipt_state(p: Path) -> str:
    if not p.exists():
        return "missing"
    r = jl(p)
    if r is None:
        return "unreadable"
    if r.get("stop_before_solve"):
        return "stopped_before_solve"
    if "termination_condition" in r and "finished_epoch" in r:
        return "post_solve"
    if (r.get("split") or {}).get("stage") == "build":
        return "split_built"
    return "pre_solve"


def build_check(d: Path, repo: Path) -> dict:
    """A dry run of a fourth-batch run: LP built and exported, parameters = registered profile + TimeLimit, input = the registered network, G2.2
    subset hash equal before the solve, no solver log; the receipt is a --stop-before-solve receipt (BUILD_ONLY) or a split build receipt."""
    import yaml
    run = jl(d / "RUN.json") or {}; rec = jl(d / "SOLVE_RECEIPT.json") or {}
    prof = yaml.safe_load((Path(repo) / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"].get(run.get("profile"), {})
    want = dict(prof, TimeLimit=float(run.get("time_limit") or 0))
    inp = rec.get("input_network") or {}; lp = rec.get("lp") or {}; cs = rec.get("config_subset") or {}; sp = rec.get("split") or {}
    snaps = int(run.get("truncate") or 0) or 2920
    state = receipt_state(d / "SOLVE_RECEIPT.json")
    checks = dict(no_solve=(state in ("stopped_before_solve", "split_built")) and rec.get("optimize_calls") == 0 and "termination_condition" not in rec,
                  no_solver_log=not (d / "gurobi.linopy.log").exists(),
                  parameters_equal_profile=rec.get("solver_parameters") == want, profile=rec.get("solver_profile") == run.get("profile"),
                  scenario=rec.get("scenario") == run.get("scenario"), network_sha256=inp.get("sha256") == run.get("network_sha256"),
                  registered_sha256_equal=run.get("registered_sha256") == inp.get("sha256"), snapshots=inp.get("snapshots") == snaps,
                  g2_2_subset_equal=bool(cs.get("network")) and cs.get("network") == cs.get("current"),
                  lp_built=int(lp.get("num_row") or 0) > 0 and int(lp.get("num_col") or 0) > 0, lp_exported=(d / "lp" / "MATH_PROBLEM.json").exists(),
                  output_is_run_dir=Path(run.get("output", "")).resolve() == d.resolve(), costs_table_exists=Path(run.get("costs_table", "")).exists())
    if state == "split_built":
        pf = Path(sp.get("problem_file") or ""); checks["problem_file"] = pf.exists() and pf.stat().st_size == sp.get("problem_bytes")
    res = dict(script=SCRIPT, rid=run.get("rid"), passed=all(checks.values()), checks=checks, receipt_state=state, profile=run.get("profile"), parameters=rec.get("solver_parameters"),
               lp=dict(num_row=lp.get("num_row"), num_col=lp.get("num_col"), nnz=lp.get("nnz"), build_seconds=lp.get("build_seconds")),
               problem_bytes=sp.get("problem_bytes"), write_seconds=sp.get("write_seconds"), peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30,
               network=run.get("network"), network_sha256=inp.get("sha256"), solver_runs=0)
    (d / "BUILD_CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


def stop_class(d: Path) -> dict:
    """Class of a run whose GATES_V6 label is not ACCEPTED_* (RUN_PLAN_B4.md section 3.5; the third-batch classes): g2 (a G2 check failed; without
    a solution only input SHA256 + configuration subset), nosol (solution/X.npy missing or no solution counts in the receipt), c1a (C1 (a) failed
    or not computable), ref_dependent (only (b)/(c)). Fourth batch: g2 / nosol / c1a stop the batch for BOTH runs (recorded UNUSABLE too for
    nosol / c1a); ref_dependent never stops. post_solve_errors of the receipt are information (B4P A3.1: they never change the class)."""
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
    if cls == "g2":
        action = "stop"
    elif cls in ("nosol", "c1a"):
        action = "stop_unusable" if rid in STOP_ALWAYS else "unusable"
    else:
        action = "none"
    res = dict(script=SCRIPT, rid=rid, label=label, solution_returned=sol, cls=cls, action=action, failed_checks=failed,
               post_solve_errors=[e.get("step") for e in (rec.get("post_solve_errors") or [])], gurobi_status=((rec.get("split") or {}).get("gurobi_status_name")),
               g2_checked=("all" if sol else "input only (no solution: network SHA256, configuration subset)"),
               rule="RUN_PLAN_B4 3.5: G2 failed -> stop; no solution / C1 (a) failed -> recorded unusable and the batch stops (two runs only); (b)/(c) only -> no stop", solver_runs=0)
    (d / "STOP_CLASS.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def iteration_times(log: Path) -> list[tuple[int, int]]:
    """(iteration, log seconds) of every barrier iteration line of a Gurobi log (the time column counts from the start of optimize, presolve included)."""
    out = []
    if not log.exists():
        return out
    for line in log.read_text(errors="ignore").splitlines():
        m = ITER.match(line)
        if m:
            out.append((int(m.group(1)), int(m.group(4))))
    return out


def projection(d: Path, time_limit: float, iterations: int, now_s: float | None = None) -> dict:
    """Early speed check (RUN_PLAN_B4.md 3.4): once iteration 20 is logged, projected total = mean seconds per iteration over iterations 11-20
    (log time at 20 minus log time at 10, over 10) x the reference iteration count + the time used so far (latest log time, or now_s when
    given); exceeded when the projection is above PROJECTION_FRACTION x TimeLimit. Silent barrier restarts keep the iteration counter, so the
    check is computed once, at the first 20 iterations."""
    it = iteration_times(d / "gurobi.linopy.log"); by = {}
    for i, t in it:
        by.setdefault(i, t)   # first occurrence (a restart would log the counter again)
    res = dict(script=SCRIPT, rid=d.name, time_limit_s=float(time_limit), reference_iterations=int(iterations), fraction=PROJECTION_FRACTION,
               limit_s=PROJECTION_FRACTION * float(time_limit), iterations_logged=len(by), after_iteration=PROJECTION_AFTER_ITERATION, written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    if PROJECTION_AFTER_ITERATION not in by or 10 not in by:
        return dict(res, ready=False, exceeded=False)
    avg = (by[PROJECTION_AFTER_ITERATION] - by[10]) / 10.0; elapsed = float(now_s) if now_s is not None else float(max(by.values()))
    proj = avg * iterations + elapsed
    return dict(res, ready=True, seconds_per_iteration_11_20=avg, time_at_10_s=by[10], time_at_20_s=by[20], elapsed_s=elapsed, projected_total_s=proj,
                exceeded=bool(proj > PROJECTION_FRACTION * float(time_limit)))


def p1_decision(monitor: Path, quota_gib: float, cores: int, threshold: float = P1_THRESHOLD, min_cores: int = P1_MIN_CORES, window_s: int = P1_WINDOW_S) -> dict:
    """P1 probe (RUN_PLAN_B4.md 3.2): the peak memory of F1 within the first window (cgroup anon when the monitor has it, else the process-group
    RSS) against threshold x quota, and the core count against min_cores -> F2 in parallel or after F1."""
    import csv
    rows = list(csv.DictReader(open(monitor))) if monitor.exists() else []
    win = [r for r in rows if r.get("elapsed_s") and float(r["elapsed_s"]) <= window_s]
    col = "cgroup_anon_gib" if win and win[0].get("cgroup_anon_gib") not in (None, "") else "rss_gib_group"
    vals = [float(r[col]) for r in win if r.get(col) not in (None, "")]
    peak = max(vals) if vals else None; covered = max(float(r["elapsed_s"]) for r in win) if win else 0.0
    parallel = bool(peak is not None and covered >= window_s * 0.95 and peak <= threshold * quota_gib and cores >= min_cores)
    return dict(script=SCRIPT, monitor=str(monitor), rows=len(win), window_s=window_s, covered_s=covered, column=col, peak_gib=peak, quota_gib=quota_gib, threshold=threshold,
                threshold_gib=threshold * quota_gib, cores=cores, min_cores=min_cores, parallel=parallel,
                reason=("peak within threshold and cores sufficient" if parallel else ("window not covered" if covered < window_s * 0.95 else ("peak above threshold" if peak is None or peak > threshold * quota_gib else "cores below minimum"))),
                written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


def memstat(cgroup_root: Path) -> dict:
    """Container memory: anon (cgroup v2 memory.stat 'anon'; v1 memory.stat 'total_rss' / 'rss') - the file cache is reclaimable and is NOT counted
    (M10S1 lesson) - and the quota (memory.max / memory.limit_in_bytes; none when unlimited). Three layouts (HPR): a cgroup v2 directory
    (memory.stat + memory.max; the root or a PBS job directory), a cgroup v1 JOB directory (memory.stat + memory.limit_in_bytes, as
    /sys/fs/cgroup/memory/<job path> on PBS Pro) and the v1 root layout (memory/memory.stat + memory/memory.limit_in_bytes)."""
    anon = used = limit = None; src = None
    v2 = cgroup_root / "memory.stat"; v1 = cgroup_root / "memory" / "memory.stat"
    layouts = ((v2, ("anon", "total_rss", "rss"), (cgroup_root / "memory.max", cgroup_root / "memory.limit_in_bytes"), (cgroup_root / "memory.current", cgroup_root / "memory.usage_in_bytes")),
               (v1, ("total_rss", "rss"), (cgroup_root / "memory" / "memory.limit_in_bytes",), (cgroup_root / "memory" / "memory.usage_in_bytes",)))
    for p, keys, lims, curs in layouts:
        if p.exists():
            vals = {}
            for line in p.read_text().splitlines():
                k, _, v = line.partition(" ")
                if k in keys and v.strip().isdigit():
                    vals[k] = int(v)
            for k in keys:
                if k in vals:
                    anon = vals[k]; src = f"{p}:{k}"; break
            cur = next((c for c in curs if c.exists()), None); used = int(cur.read_text().strip()) if cur else None
            lim = next((l for l in lims if l.exists()), None)
            if lim:
                t = lim.read_text().strip(); limit = None if t in ("max", "") or len(t) >= 19 else int(t)
            break
    frac = (anon / limit) if (anon is not None and limit) else None
    return dict(script=SCRIPT, source=src, anon_bytes=anon, used_bytes=used, limit_bytes=limit, anon_gib=(anon / 2**30 if anon is not None else None),
                limit_gib=(limit / 2**30 if limit else None), fraction=frac, stop_fraction=MEMORY_STOP_FRACTION, stop=bool(frac is not None and frac > MEMORY_STOP_FRACTION),
                written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


def run_state(out: Path, rid: str) -> dict:
    d = out / rid; rec = jl(d / "SOLVE_RECEIPT.json") or {}; prec = jl(d / "PRECISION.json") or {}; acc = jl(d / "V6_ACCEPTANCE.json") or {}
    prov = jl(d / "V6_ACCEPTANCE_PROVISIONAL.json"); owen = jl(d / "m12_owen" / "OWEN.json") or {}; oreg = jl(d / "m12_owen" / "OWEN_REGRADE_BATCH_REFERENCE.json")
    run = jl(d / "RUN.json") or {}; sc = jl(d / "STOP_CLASS.json"); sp = rec.get("split") or {}
    state = "ended" if (d / ".ended").exists() else ("started_not_ended" if (d / ".started").exists() else ("prepared" if run else "not_started"))
    if receipt_state(d / "SOLVE_RECEIPT.json") in ("stopped_before_solve", "split_built") and "termination_condition" not in rec:
        state = "built_no_solve"
    g = prec.get("grade") or {}; src = str((prec.get("reference") or {}).get("source") or "")
    return dict(rid=rid, role=RUNS[rid]["role"], profile=RUNS[rid]["profile"], state=state, network=run.get("network"), network_sha256=run.get("network_sha256"),
                stop_class=(dict(cls=sc.get("cls"), action=sc.get("action"), failed_checks=sc.get("failed_checks")) if sc else None),
                termination=rec.get("termination_condition") or (Path(d / ".cond").read_text().strip() if (d / ".cond").exists() else None), objective=rec.get("objective"),
                gurobi_status=sp.get("gurobi_status_name"), iterations=sp.get("bar_iter_count"), solve_seconds=rec.get("solve_seconds"),
                peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30 or None, solve_peak_rss_gib=((sp.get("peak_rss_bytes") or 0) / 2**30 or None),
                max_mem_used_gb=sp.get("max_mem_used_gb"), post_solve_errors=[e.get("step") for e in (rec.get("post_solve_errors") or [])],
                c1=dict(grade=g.get("grade"), a=g.get("a"), b=g.get("b"), c=g.get("c"), reference=("batch" if src.startswith("this batch") else ("default" if src else None)),
                        regrades=len(prec.get("grade_history") or [])) if prec else None,
                v6=acc.get("label"), v6_provisional=(prov or {}).get("label"),
                g1=dict((k, (acc.get("G1") or {}).get(k)) for k in ("a", "b", "c")) if acc else None,
                g2=dict((k, ((acc.get("G2") or {}).get(k) or {}).get("passed")) for k in ("G2_1", "G2_2", "G2_3")) if acc else None,
                owen_usable=((oreg or {}).get("new") or {}).get("usable_for_allocation", owen.get("usable_for_allocation")) if owen else None,
                postproc_errors=[f"{e['step']}:exit={e['exit']}" for e in postproc_errors(out) if e["rid"] == rid])


def b6(out: Path) -> dict | None:
    i, d = run_state(out, "F1"), run_state(out, "F2")
    if i["objective"] is None or d["objective"] is None:
        return None
    sys.path.insert(0, str(HERE / "v5"))
    from v5_gates import gate_b6_cost
    g = gate_b6_cost(float(i["objective"]), float(d["objective"]), "integrated", "disconnected")
    li, ld = ledger_totals(out / "F1"), ledger_totals(out / "F2"); oi, od = owen_main(out / "F1"), owen_main(out / "F2")
    return dict(g, b6_bn=bn(g["difference"]), relative=(float(d["objective"]) - float(i["objective"])) / abs(float(i["objective"])), runs=dict(integrated="F1", disconnected="F2"),
                labels=dict(F1=i["v6"], F2=d["v6"]), usable=bool(i["v6"] and d["v6"] and i["v6"] != "NOT_ACCEPTED" and d["v6"] != "NOT_ACCEPTED"),
                ledger_total_difference_bn=({c: bn(ld.get(c, 0.0) - li.get(c, 0.0)) for c in COUNTRIES + ("ASEAN",)} if (li and ld) else None),
                owen_dual_form_benefit_bn=({p: bn(od.get(p, 0.0) - oi.get(p, 0.0)) for p in COUNTRIES + ("BUNKER",)} if (oi and od) else None))


def batch3_comparison(b3: Path | None, out: Path) -> dict | None:
    """Information only (RUN_PLAN_B4 3.7): the third batch's 365x24h R1 / R2 beside F1 / F2 (objective, B6, Owen main values) - 'resolution effect'."""
    if not b3 or not (b3 / "R1" / "SOLVE_RECEIPT.json").exists():
        return None
    r1, r2 = jl(b3 / "R1" / "SOLVE_RECEIPT.json") or {}, jl(b3 / "R2" / "SOLVE_RECEIPT.json") or {}
    f1, f2 = run_state(out, "F1"), run_state(out, "F2")
    rows = dict(R1=dict(objective_bn=bn(r1.get("objective")), termination=r1.get("termination_condition"), owen_main_bn={k: bn(v) for k, v in owen_main(b3 / "R1").items()}),
                R2=dict(objective_bn=bn(r2.get("objective")), termination=r2.get("termination_condition"), owen_main_bn={k: bn(v) for k, v in owen_main(b3 / "R2").items()}),
                F1=dict(objective_bn=bn(f1["objective"]), termination=f1["termination"], owen_main_bn={k: bn(v) for k, v in owen_main(out / "F1").items()}),
                F2=dict(objective_bn=bn(f2["objective"]), termination=f2["termination"], owen_main_bn={k: bn(v) for k, v in owen_main(out / "F2").items()}))
    b6_3 = bn(r2.get("objective") - r1.get("objective")) if r1.get("objective") is not None and r2.get("objective") is not None else None
    b6_4 = bn(f2["objective"] - f1["objective"]) if f1["objective"] is not None and f2["objective"] is not None else None
    return dict(source=str(b3), runs=rows, b6_365x24h_bn=b6_3, b6_2920x3h_bn=b6_4, note="description only: the resolution effect (365x24h daily vs 2920x3h); no judgement, no threshold")


def reference_comparison(out: Path, ref_file: Path | None) -> dict | None:
    """HPR (RUN_PLAN_HPC 7.4; description only, never a criterion): F1 / F2 beside the reference pairs of REFERENCE_VALUES.json - the third batch's
    365x24h R3 / R4 (main) and R1 / R2 (alternative) and the DFX v2 365x24h V1 / V2 - as numbers only (objective, B6, Owen dual-form alpha-main
    shares): objective differences, delta B6, Owen benefit differences per participant. The reference file holds values, never result files."""
    if not ref_file or not Path(ref_file).exists():
        return None
    ref = jl(Path(ref_file)) or {}; f1, f2 = run_state(out, "F1"), run_state(out, "F2")
    ow = {rid: owen_main(out / rid) for rid in RUNS}; parts = COUNTRIES + ("BUNKER",)
    b6_bn = bn(f2["objective"] - f1["objective"]) if f1["objective"] is not None and f2["objective"] is not None else None
    res = dict(reference_file=str(ref_file), source=ref.get("source"), b6_2920x3h_bn=b6_bn, objective_2920x3h_eur=dict(F1=f1["objective"], F2=f2["objective"]),
               owen_dual_form_alpha_main_bn={rid: {p: bn(v.get(p, 0.0)) for p in parts} for rid, v in ow.items() if v}, pairs={},
               note="description only: resolution (2920x3h vs 365x24h) and demand version (v2 vs v1) effects; no judgement, no threshold")
    for key, pair in (ref.get("references") or {}).items():
        i, d = pair.get("integrated") or {}, pair.get("disconnected") or {}
        row = dict(label=pair.get("label"), runs=dict(integrated=i.get("rid"), disconnected=d.get("rid")), b6_bn=pair.get("b6_bn"), objective_eur=dict(integrated=i.get("objective_eur"), disconnected=d.get("objective_eur")),
                   objective_difference_bn={}, delta_b6_bn=None, owen_benefit_difference_bn=None, owen_share_difference_bn={})
        if f1["objective"] is not None and i.get("objective_eur") is not None:
            row["objective_difference_bn"][f"F1_minus_{i.get('rid')}"] = bn(f1["objective"] - i["objective_eur"])
        if f2["objective"] is not None and d.get("objective_eur") is not None:
            row["objective_difference_bn"][f"F2_minus_{d.get('rid')}"] = bn(f2["objective"] - d["objective_eur"])
        if b6_bn is not None and pair.get("b6_bn") is not None:
            row["delta_b6_bn"] = b6_bn - pair["b6_bn"]
        ri, rd = i.get("owen_alpha_main_eur") or {}, d.get("owen_alpha_main_eur") or {}
        if ow.get("F1") and ri:
            row["owen_share_difference_bn"][f"F1_minus_{i.get('rid')}"] = {p: bn(ow["F1"].get(p, 0.0) - ri.get(p, 0.0)) for p in parts}
        if ow.get("F2") and rd:
            row["owen_share_difference_bn"][f"F2_minus_{d.get('rid')}"] = {p: bn(ow["F2"].get(p, 0.0) - rd.get(p, 0.0)) for p in parts}
        if ow.get("F1") and ow.get("F2") and ri and rd:
            row["owen_benefit_difference_bn"] = {p: bn((ow["F2"].get(p, 0.0) - ow["F1"].get(p, 0.0)) - (rd.get(p, 0.0) - ri.get(p, 0.0))) for p in parts}
        res["pairs"][key] = row
    return res


def summary(out: Path, batch3: Path | None = None, reference_values: Path | None = None) -> dict:
    runs = {rid: run_state(out, rid) for rid in RUNS}
    ben = jl(out / "M12_BENEFIT" / "BENEFIT.json")
    stop = (out / "STOP").read_text().split() if (out / "STOP").exists() else []
    safe = (out / "STOP_SAFE").read_text().strip() if (out / "STOP_SAFE").exists() else None
    p1 = jl(out / "P1_DECISION.json"); proj = {rid: jl(out / f"PROJECTION_{rid}.json") for rid in RUNS}
    res = dict(script=SCRIPT, out=str(out), runs=runs, unusable=unusable_runs(out), B6=b6(out),
               benefit=(dict(computable=ben.get("computable", True), b6_bn=bn(ben.get("b6_eur")), negative_benefit=(ben.get("owen") or {}).get("negative_benefit"), reason=ben.get("reason")) if ben else None),
               batch3_comparison=batch3_comparison(batch3, out), reference_comparison=reference_comparison(out, reference_values),
               p1=p1, projection={k: ({x: v.get(x) for x in ("ready", "exceeded", "projected_total_s", "seconds_per_iteration_11_20")} if v else None) for k, v in proj.items()},
               stop_not_accepted=stop, stop_safe=safe, postproc_errors=postproc_errors(out), solver_runs=0, written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    (out / "BATCH4_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    (out / "BATCH4_SUMMARY.md").write_text(markdown(res))
    return res


def _f(x, fmt="{:.4f}"):
    return "—" if x is None else fmt.format(x)


def markdown(r: dict) -> str:
    un = ", ".join(f"{k}（{v}）" for k, v in r["unusable"].items())
    pe = ", ".join("{} {} exit={}".format(e["rid"], e["step"], e["exit"]) for e in (r.get("postproc_errors") or []))
    L = ["# 第四批汇总（run_batch4.sh 自动生成；只读，未调用求解器）", "",
         f"- 停批（RUN_PLAN_B4 3.5）：{', '.join(r['stop_not_accepted']) or '无'}；安全停止：{r['stop_safe'] or '无'}；不可用：{un or '无'}",
         f"- 后处理步骤异常或超时（只记录；`POST_ONLY=1` 补做）：{pe or '无'}",
         f"- P1 探针：{json.dumps({k: (r['p1'] or {}).get(k) for k in ('parallel', 'peak_gib', 'threshold_gib', 'cores', 'reason')}, ensure_ascii=False) if r.get('p1') else '未记录'}",
         f"- 早期测速：{json.dumps(r.get('projection'), ensure_ascii=False)}", "",
         "## 运行", "", "| 运行 | 作用 | 档案 | 状态 | Gurobi 状态 | 终止 | 迭代 | 目标 bn | 求解 s | 求解进程峰值 GiB | Gurobi MaxMemUsed GB | C1 abc | GATES_V6 | 求解后异常 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for rid, v in r["runs"].items():
        c1 = v["c1"] or {}; abc = "".join("1" if c1.get(k) else "0" for k in ("a", "b", "c")) if c1 else "—"
        L.append(f"| {rid} | {v['role']} | {v['profile']} | {v['state']} | {v['gurobi_status'] or '—'} | {v['termination'] or '—'} | {v['iterations'] if v['iterations'] is not None else '—'} | {_f(bn(v['objective']))} | "
                 f"{_f(v['solve_seconds'], '{:.0f}')} | {_f(v['solve_peak_rss_gib'] or v['peak_rss_gib'], '{:.2f}')} | {_f(v['max_mem_used_gb'], '{:.1f}')} | {abc} | {v['v6'] or '—'} | {', '.join(v['post_solve_errors']) or '无'} |")
    b = r["B6"]
    L += ["", "## B6（F2 − F1）与 Owen 对偶形式受益", ""]
    if b:
        L.append(f"- B6 = {b['b6_bn']:.4f} bn EUR2020（相对 {b['relative']:+.3e}；门槛 `B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED`：{b['passed']}；标签 F1 {b['labels']['F1']}，F2 {b['labels']['F2']}；可用 {b['usable']}）")
        if b.get("ledger_total_difference_bn"):
            L.append("- 分国账本差（F2 − F1，bn）：" + ", ".join(f"{k} {v:+.3f}" for k, v in b["ledger_total_difference_bn"].items()))
        if b.get("owen_dual_form_benefit_bn"):
            L.append("- Owen 对偶形式受益（F2 份额 − F1 份额，α 主值，bn）：" + ", ".join(f"{k} {v:+.3f}" for k, v in b["owen_dual_form_benefit_bn"].items()))
    else:
        L.append("- 不可计算（F1 或 F2 无目标值）")
    if r["benefit"]:
        L.append(f"- M12 受益与比例规则对照：{'B6 ' + _f(r['benefit']['b6_bn']) + ' bn；负受益 ' + str(r['benefit']['negative_benefit']) if r['benefit']['computable'] else '不可计算：' + str(r['benefit']['reason'])}（`M12_BENEFIT/`）")
    c = r.get("batch3_comparison")
    L += ["", "## 与第三批 365×24h 同名结果的对比（只描述，分辨率影响的证据；不判定）", ""]
    if c:
        L += [f"- 来源：{c['source']}", f"- B6：365×24h {_f(c['b6_365x24h_bn'])} bn；2920×3h {_f(c['b6_2920x3h_bn'])} bn", "", "| 运行 | 目标 bn | 终止 |", "|---|---|---|"]
        L += [f"| {k} | {_f(v['objective_bn'])} | {v['termination'] or '—'} |" for k, v in c["runs"].items()]
    else:
        L.append("- 未提供第三批导出目录（--batch3），或 F1 / F2 未完成")
    rc = r.get("reference_comparison")
    L += ["", "## 与登记参照值的对比（REFERENCE_VALUES.json：第三批 365×24h R3 / R4 主、R1 / R2 并列；DFX v2 365×24h V1 / V2；只描述，不判定）", ""]
    if rc:
        L += [f"- 本批 B6（F2 − F1）：{_f(rc['b6_2920x3h_bn'])} bn EUR", "", "| 参照 | 运行 | 参照 B6 bn | ΔB6（本批 − 参照）bn | 目标值差 bn | Owen 受益差（本批受益 − 参照受益，bn）|", "|---|---|---|---|---|---|"]
        for k, v in rc["pairs"].items():
            od = ", ".join(f"{a} {b:+.4f}" for a, b in v["objective_difference_bn"].items()) or "—"
            ob = ", ".join(f"{p} {x:+.3f}" for p, x in (v["owen_benefit_difference_bn"] or {}).items()) or "—"
            L.append(f"| {v['label'] or k} | {v['runs']['integrated']} / {v['runs']['disconnected']} | {_f(v['b6_bn'])} | {_f(v['delta_b6_bn'], '{:+.4f}')} | {od} | {ob} |")
    else:
        L.append("- 未提供参照值文件（--reference-values），或 F1 / F2 未完成")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("runtable")
    b = sub.add_parser("base-check"); b.add_argument("--nets", type=Path, required=True); b.add_argument("--out", type=Path, required=True)
    b.add_argument("--no-registered", action="store_true", help="tests / stand-ins only: skip the registered SHA256 / bytes comparison (receipt checks kept)")
    k = sub.add_parser("build-check"); k.add_argument("--dir", type=Path, required=True); k.add_argument("--repo", type=Path, required=True)
    rs = sub.add_parser("receipt-state"); rs.add_argument("--receipt", type=Path, required=True)
    q = sub.add_parser("stop-class"); q.add_argument("--dir", type=Path, required=True)
    pj = sub.add_parser("projection"); pj.add_argument("--dir", type=Path, required=True); pj.add_argument("--time-limit", type=float, required=True); pj.add_argument("--iterations", type=int, required=True)
    pj.add_argument("--out", type=Path, required=True); pj.add_argument("--now", type=float, default=None, help="seconds used so far (default: latest log time)")
    p1 = sub.add_parser("p1"); p1.add_argument("--monitor", type=Path, required=True); p1.add_argument("--quota-gib", type=float, required=True); p1.add_argument("--cores", type=int, required=True)
    p1.add_argument("--out", type=Path, required=True); p1.add_argument("--threshold", type=float, default=P1_THRESHOLD); p1.add_argument("--min-cores", type=int, default=P1_MIN_CORES); p1.add_argument("--window-s", type=int, default=P1_WINDOW_S)
    ms = sub.add_parser("memstat"); ms.add_argument("--cgroup-root", type=Path, default=Path("/sys/fs/cgroup")); ms.add_argument("--out", type=Path, default=None)
    s = sub.add_parser("summary"); s.add_argument("--out-dir", type=Path, required=True); s.add_argument("--batch3", type=Path, default=None)
    s.add_argument("--reference-values", type=Path, default=None, help="HPR: REFERENCE_VALUES.json (third batch R3 / R4, R1 / R2; DFX V1 / V2) - description only")
    sub.add_parser("hpc-plan")
    a = ap.parse_args()
    if a.cmd == "runtable":
        for rid, r in RUNS.items():
            print("|".join([rid, r["scenario"], r["base"], r["set"], r["profile"], r["costs"]]))
    elif a.cmd == "base-check":
        r = base_check(a.nets, registered=not a.no_registered); a.out.write_text(json.dumps(r, indent=1) + "\n")
        print("all_equal" if r["all_equal"] else "DIFFERENT:" + ",".join(k for k, v in r["networks"].items() if not v["equal"])); sys.exit(0 if r["all_equal"] else 1)
    elif a.cmd == "build-check":
        r = build_check(a.dir, a.repo)
        print(json.dumps(dict(passed=r["passed"], failed=[k for k, v in r["checks"].items() if not v], lp=r["lp"], receipt_state=r["receipt_state"], peak_rss_gib=round(r["peak_rss_gib"], 2)), default=str)); sys.exit(0 if r["passed"] else 1)
    elif a.cmd == "receipt-state":
        print(receipt_state(a.receipt))
    elif a.cmd == "stop-class":
        r = stop_class(a.dir); print(r["cls"], r["action"])
    elif a.cmd == "projection":
        r = projection(a.dir, a.time_limit, a.iterations, a.now); a.out.write_text(json.dumps(r, indent=1) + "\n")
        print(json.dumps({k: r.get(k) for k in ("ready", "exceeded", "seconds_per_iteration_11_20", "projected_total_s", "limit_s")}))
        sys.exit(3 if r.get("exceeded") else (0 if r.get("ready") else 1))
    elif a.cmd == "p1":
        r = p1_decision(a.monitor, a.quota_gib, a.cores, a.threshold, a.min_cores, a.window_s); a.out.write_text(json.dumps(r, indent=1) + "\n")
        print(json.dumps({k: r.get(k) for k in ("parallel", "peak_gib", "threshold_gib", "covered_s", "reason")})); sys.exit(0 if r["parallel"] else 1)
    elif a.cmd == "memstat":
        r = memstat(a.cgroup_root)
        if a.out:
            a.out.write_text(json.dumps(r, indent=1) + "\n")
        print(json.dumps({k: r.get(k) for k in ("anon_gib", "limit_gib", "fraction", "stop")})); sys.exit(3 if r["stop"] else 0)
    elif a.cmd == "summary":
        r = summary(a.out_dir, a.batch3, a.reference_values); print(json.dumps(dict(B6_bn=(r["B6"] or {}).get("b6_bn"), runs={k: v["state"] for k, v in r["runs"].items()}), default=str))
    elif a.cmd == "hpc-plan":   # HPR: machine-readable registration for make_pbs.sh / hpr_consistency.py (RUN_PLAN_HPC.md sections 2-3, 9)
        print(f"LIMITS|{TIME_LIMIT_S}|{WALL_CAP_S}|{LICENCE_GAP_S}|{WAIT_START_MAX_S}|{BUILD_TIMEOUT_S}|{ASSIGN_TIMEOUT_S}|{POST_TIMEOUT_S}|{PACK_TIMEOUT_S}|{POST_MEM_NEED_GIB}")
        print(f"SMOKE|{SMOKE['truncate']}|{SMOKE['time_limit_s']}|{SMOKE['wall_cap_s']}")
        print(f"STOP|{MEMORY_STOP_FRACTION}|{PROJECTION_FRACTION}|{RUNS['F1']['iterations_reference']}|{RUNS['F2']['iterations_reference']}")
        for key, j in HPC_JOBS.items():
            print("|".join(["JOB", key, j["name"], j["queue"], str(j["ncpus"]), str(j["mem_gb"]), j["walltime"], j["mode"], j["rid"], j["depends"], j["wait_start_of"]]))
        for k, v in REGISTERED_SHA.items():
            print(f"NETWORK|{k}|{v}|{REGISTERED_BYTES[k]}|{BUILD_COMMIT}")


if __name__ == "__main__":
    main()
