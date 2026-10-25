"""SYNTHETIC_TEST_ONLY stand-ins for the B4P fourth-batch runner (run_batch4.sh), on top of m10p_fake_pipeline.py (va / c1 / m12 / m12a / ledger /
variants reused): s2_solve.py in single mode (the m10p solve), in split mode (--split-stage build / assign) and b4_split_solve.py (split-solve).
No solver, no model. Every call appends one line to <FAKE_OUT>/CALLS.txt.
Hooks (plus m10p's FAKE_SLEEP_<rid>, FAKE_OBJ_<rid>, FAKE_TERM_<rid>, FAKE_NOSOL_<rid>, FAKE_C1_<rid>, FAKE_SUBSET_<rid>, FAKE_IGNORE_TERM_<rid>, ...):
  FAKE_GUROBI_STATUS_<rid>  OPTIMAL (default) | SUBOPTIMAL | MEM_LIMIT | TIME_LIMIT_NOSOL   (split-solve: MEM_LIMIT / TIME_LIMIT_NOSOL return no solution)
  FAKE_ITERS_<rid>          barrier iteration lines written to gurobi.linopy.log before "solving" (default 25), FAKE_ITER_S_<rid> log seconds each (default 1)
  FAKE_MEM_SPIKE_<rid>      "<after s>:<anon bytes>": after that many seconds the stand-in rewrites $CGROUP_ROOT/memory.stat (anon <bytes>) - memory-stop drill
  FAKE_POST_ERROR_<rid>=1   the assign stage records a post_solve_errors entry (termination status and solution kept; exit 4, as s2_solve.py)
"""
import json
import os
import signal
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import m10p_fake_pipeline as F   # noqa: E402

STATUS = {"OPTIMAL": (2, "optimal", "ok"), "SUBOPTIMAL": (13, "suboptimal", "ok"), "MEM_LIMIT": (17, "internal_solver_error", "error"), "TIME_LIMIT_NOSOL": (9, "time_limit", "ok")}


def pre_receipt(argv, out: Path, net: Path):
    import yaml
    prof = F.arg("--solver-profile", argv); tl = float(F.arg("--time-limit", argv))
    params = dict(yaml.safe_load((F.ROOT / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"][prof], TimeLimit=tl)
    snaps = int(F.arg("--truncate", argv) or 0) or 2920
    rid = out.name
    return dict(input_network=dict(path=str(net), sha256=F.sha(net), snapshots=snaps, truncated_to=(int(F.arg("--truncate", argv)) if F.arg("--truncate", argv) else None)),
                scenario=F.arg("--scenario", argv), solver_profile=prof, solver_parameters=params, lp=dict(num_col=10, num_row=20, nnz=30, build_seconds=0.1),
                config_subset=dict(network="s" * 64, current=("t" if os.environ.get(f"FAKE_SUBSET_{rid}") == "differ" else "s") * 64),
                optimize_calls=0, costs_table=F.arg("--costs-table", argv), label=F.arg("--label", argv), started_epoch=time.time())


def solved_outputs(out: Path, rec: dict, argv):
    """The solved files of a run (as the m10p solve): solution arrays, ledger, solved network, EXPORTS, V5_GATES."""
    (out / "solution").mkdir(exist_ok=True)
    for k, n in (("X", 10), ("Pi", 20), ("RC", 10)):
        np.save(out / "solution" / f"{k}.npy", np.zeros(n))
    led = "entity,total\n" + "".join(f"{c},{1e9 * (2 if rec['scenario'] == 'disconnected' else 1)}\n" for c in ("BN", "VN", "ASEAN_BUNKER"))
    (out / "COUNTRY_COST_LEDGER.csv").write_text(led)
    (out / f"{rec['scenario']}_{F.arg('--label', argv)}_solved.nc").write_bytes(b"solved")
    (out / "EXPORTS.json").write_text("{}"); F.register(out, "COUNTRY_COST_LEDGER.csv")
    b16 = dict(gate="B16_LEDGER", passed=False, error="'59'") if os.environ.get(f"FAKE_B16_FAIL_{out.name}") == "1" else dict(passed=True, relative_error=1e-10)
    (out / "V5_GATES.json").write_text(json.dumps(dict(A4=dict(passed=True, status="EXACT_SEMANTIC_ROUNDTRIP"), B16_LEDGER=b16, acceptance_basis="barconvtol", all_passed_barconvtol=b16["passed"])))
    rec.update(solution=dict(X=dict(count=10), Pi=dict(count=20), RC=dict(count=10)), exports=json.loads((out / "EXPORTS.json").read_text()))


def solve(argv):
    stage = F.arg("--split-stage", argv)
    if stage is None:
        return F.solve(argv)
    out = Path(F.arg("--output", argv)); net = Path(F.arg("--network", argv)); rid = out.name; out.mkdir(parents=True, exist_ok=True)
    (out / "lp").mkdir(exist_ok=True); (out / "lp" / "MATH_PROBLEM.json").write_text("{}")
    for k, n in (("vlabels", 10), ("clabels", 20)):
        np.save(out / "lp" / f"{k}.npy", np.arange(n))
    if stage == "build":
        rec = pre_receipt(argv, out, net); sp = out / "split"; sp.mkdir(exist_ok=True)
        (sp / "problem.lp").write_bytes(b"\\ fake problem\nminimize\nend\n")
        info = dict(stage="build", problem_file=str(sp / "problem.lp"), problem_bytes=(sp / "problem.lp").stat().st_size, problem_sha256=F.sha(sp / "problem.lp"), write_seconds=0.01,
                    solver_parameters=rec["solver_parameters"], log_file=str(out / "gurobi.linopy.log"), label=rec["label"], scenario=rec["scenario"])
        (sp / "SPLIT_BUILD.json").write_text(json.dumps(info))
        rec.update(split=dict(stage="build", problem_file=info["problem_file"], problem_bytes=info["problem_bytes"], problem_sha256=info["problem_sha256"], write_seconds=0.01),
                   decision="SPLIT_BUILT_" + rec["label"], peak_rss_bytes=2**30, finished_epoch=time.time())
        (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))
        F.call(f"build {rid} {rec['solver_profile']} {rec['solver_parameters']['TimeLimit']} {os.environ.get('GRB_LICENSE_FILE')} split"); return 0
    # assign: the result of the split-solve stand-in mapped back
    rec = json.loads((out / "SOLVE_RECEIPT.json").read_text()); split = json.loads((out / "split" / "SPLIT_SOLVE.json").read_text())
    rec.update(optimize_calls=1, split=dict(stage="assign", solve_process="fake b4_split_solve", **{k: split.get(k) for k in ("gurobi_status_code", "gurobi_status_name", "fingerprint", "bar_iter_count", "runtime_s", "max_mem_used_gb", "peak_rss_bytes", "solve_seconds", "sol_count")}))
    status, cond = split["linopy_status"], split["termination_condition"]
    rec.update(status=status, termination_condition=cond, solve_seconds=split.get("solve_seconds"), solve_finished_epoch=time.time(), finished_epoch=time.time(), post_solve_complete=False,
               decision=("SOLVED_" + rec["label"]) if status == "ok" else "STOP_INFEASIBLE_OR_FAILED_NO_RELAXATION")
    (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))   # A3.1: the termination status is on disk first
    if status != "ok" or not split.get("solution_available"):
        rec.update(peak_rss_bytes=2**30, finished_epoch=time.time(), post_solve_complete=True); (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))
        F.call(f"assign {rid} {cond} nosolution {os.environ.get('GRB_LICENSE_FILE')}"); return 2
    rec["objective"] = float(split["objective"]); solved_outputs(out, rec, argv)
    errors = []
    if os.environ.get(f"FAKE_POST_ERROR_{rid}") == "1":
        errors.append(dict(step="co2_flows", error="RuntimeError", detail="injected post-solve failure (drill)", traceback=""))
    rec.update(gates=dict(A4=True, B16_LEDGER=True), peak_rss_bytes=2**31, finished_epoch=time.time(), post_solve_errors=errors, post_solve_complete=(not errors))
    (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))
    F.call(f"assign {rid} {cond} {os.environ.get('GRB_LICENSE_FILE')} post_errors={len(errors)}"); return 0 if not errors else 4


def split_solve(argv):
    d = Path(F.arg("--run-dir", argv)); rid = d.name; sp = d / "split"; t0 = time.time()
    build = json.loads((sp / "SPLIT_BUILD.json").read_text()); params = build["solver_parameters"]
    code, cond, lstat = STATUS[os.environ.get(f"FAKE_GUROBI_STATUS_{rid}", "OPTIMAL")]
    iters = int(os.environ.get(f"FAKE_ITERS_{rid}", "25")); it_s = float(os.environ.get(f"FAKE_ITER_S_{rid}", "1"))
    with open(d / "gurobi.linopy.log", "w") as f:
        f.write("Gurobi Optimizer version 12.0.3 (fake)\nOptimize a model with 20 rows, 10 columns and 30 nonzeros\nModel fingerprint: 0xfa4efa4e\nBarrier statistics:\n Factor NZ  : 1.000e+03\n Factor Ops : 1.000e+04\n\n")
        f.write("Iter       Primal          Dual         Primal    Dual     Compl     Time\n")
        for i in range(iters):
            f.write(f"{i:4d}   1.00000000e+11  1.00000000e+11  1.00e-03 1.00e-03  1.00e-03  {int(10 + (i + 1) * it_s)}s\n")
        f.write(f"\nBarrier solved model in {iters} iterations and {10 + iters * it_s:.2f} seconds (1.00 work units)\nOptimal objective 1.00000000e+11\n")
    res = dict(stage="solve", run_dir=str(d), solver_parameters=params, protect_parameters={}, started_epoch=t0, optimize_calls=1, fingerprint="0xfa4efa4e", num_vars=10, num_constrs=20, num_nzs=30)
    (sp / "SPLIT_SOLVE.json").write_text(json.dumps(res))
    if "--remove-lp" in argv and Path(build["problem_file"]).exists():
        Path(build["problem_file"]).unlink(); res["problem_removed_after_read"] = True
    if os.environ.get(f"FAKE_IGNORE_TERM_{rid}") == "1":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    sleep = float(os.environ.get(f"FAKE_SLEEP_{rid}", os.environ.get("FAKE_SLEEP", "0.2"))); spike = os.environ.get(f"FAKE_MEM_SPIKE_{rid}")
    t = 0.0
    while t < sleep:
        time.sleep(min(0.5, sleep - t)); t += 0.5
        if spike and t >= float(spike.split(":")[0]):
            root = Path(os.environ["CGROUP_ROOT"]); (root / "memory.stat").write_text(f"anon {int(spike.split(':')[1])}\nfile 0\n"); spike = None
    have = cond in ("optimal", "suboptimal")
    res.update(gurobi_status_code=code, gurobi_status_name=os.environ.get(f"FAKE_GUROBI_STATUS_{rid}", "OPTIMAL").replace("_NOSOL", ""), termination_condition=cond, linopy_status=lstat,
               runtime_s=sleep, work_units=1.0, bar_iter_count=iters, sol_count=(1 if have else 0), max_mem_used_gb=1.0, mem_used_gb=0.5, solution_available=have,
               objective=(float(os.environ.get(f"FAKE_OBJ_{rid}", "3e11" if build.get("scenario") == "disconnected" else "2e11")) if have else None))
    if have:
        nv = len(np.load(d / "lp" / "vlabels.npy")) if (d / "lp" / "vlabels.npy").exists() else 10   # the real process-1 label vectors (local dry run) or the stand-in's
        nc = len(np.load(d / "lp" / "clabels.npy")) if (d / "lp" / "clabels.npy").exists() else 20
        for k, n in (("X", nv), ("Pi", nc), ("RC", nv)):
            np.save(sp / f"{k}_raw.npy", np.zeros(n))
        res["arrays"] = {k: dict(file=f"{k}_raw.npy", count=n, absent_labels=0) for k, n in (("X", nv), ("Pi", nc), ("RC", nv))}
    elif lstat == "ok":
        res["linopy_status"] = "warning"; res["status_note"] = "no solution (SolCount 0)"
    res.update(solve_seconds=time.time() - t0, finished_epoch=time.time(), peak_rss_bytes=2**30)
    (sp / "SPLIT_SOLVE.json").write_text(json.dumps(res))
    F.call(f"gurobi {rid} {build.get('solver_profile', '-')} {params['TimeLimit']} {t0:.2f} {time.time():.2f} {os.environ.get('GRB_LICENSE_FILE')} omp={os.environ.get('OMP_NUM_THREADS')} tmp={os.environ.get('TMPDIR')} status={res['gurobi_status_name']}")
    return 0


def main():
    mode, argv = sys.argv[1], sys.argv[2:]
    if mode == "solve":
        return solve(argv)
    if mode == "split-solve":
        return split_solve(argv)
    sys.argv = [sys.argv[0], mode, *argv]
    return F.main()


if __name__ == "__main__":
    sys.exit(main())
