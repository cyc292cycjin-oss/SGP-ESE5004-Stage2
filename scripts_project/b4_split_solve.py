"""B4P (fourth-batch preparation, 2026-10-26; user supplement 2 "split-process solve"): PROCESS 2 of the split solve - gurobipy only.

Process 1 (scripts_project/s2_solve.py --split-stage build) builds the linopy model and writes the LP problem file exactly as linopy
Model.solve(io_api=None) would before calling the solver, plus the label vectors (lp/vlabels.npy, lp/clabels.npy) and split/SPLIT_BUILD.json.
This process reads that file with gurobipy, sets the registered profile parameters the way linopy's Gurobi solver does (every solver option
in order, then LogFile), calls optimize() ONCE and writes the raw result for process 3 (s2_solve.py --split-stage assign):
  split/X_raw.npy, Pi_raw.npy, RC_raw.npy   in the order of lp/vlabels.npy / lp/clabels.npy (a label absent from the solver model -> NaN, as
                                            linopy's reindex); values in the LP units (process 3 applies the registered unscaling)
  split/SPLIT_SOLVE.json                    Gurobi status code / name, the linopy termination condition and status (same CONDITION_MAP and
                                            status classes as linopy 0.5.5 solvers.py / constants.py), objective, BarIterCount, Runtime, Work,
                                            MaxMemUsed / MemUsed (GB), Fingerprint, dimensions, SolCount, wall seconds, peak RSS of this process
  gurobi.linopy.log                         the Gurobi log in the run folder (same file name as the single-process path)
No PyPSA / linopy / xarray import: the process holds the Gurobi model and the result arrays only. One optimize() call; never retried.

    GRB_LICENSE_FILE=<licence> python scripts_project/b4_split_solve.py --run-dir <run folder of process 1> [--remove-lp]
        [--probe-ordering-only | --probe-iterations K]   measurement only (SMOKE_TEST_ONLY runs): BarIterLimit 0 (presolve, ordering, barrier statistics,
                                           no iterations) or K barrier iterations (per-iteration seconds and the memory with the factor allocated)
        [--protect KEY=VALUE ...]          run-protection parameters outside the profile (e.g. SoftMemLimit=<GB>), recorded separately in the receipt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import threading
import time
import traceback
from pathlib import Path

import numpy as np

SCRIPT = "scripts_project/b4_split_solve.py"
# linopy 0.5.5 solvers.py Gurobi._solve CONDITION_MAP (Gurobi status code -> termination condition) and constants.py status classes
CONDITION_MAP = {1: "unknown", 2: "optimal", 3: "infeasible", 4: "infeasible_or_unbounded", 5: "unbounded", 6: "other", 7: "iteration_limit",
                 8: "terminated_by_limit", 9: "time_limit", 10: "optimal", 11: "user_interrupt", 12: "other", 13: "suboptimal", 14: "unknown",
                 15: "terminated_by_limit", 16: "internal_solver_error", 17: "internal_solver_error"}
STATUS_CLASS = {"ok": ("optimal", "time_limit", "iteration_limit", "terminated_by_limit", "suboptimal"),
                "warning": ("unbounded", "infeasible", "infeasible_or_unbounded", "other"),
                "error": ("internal_solver_error", "error"),
                "aborted": ("user_interrupt", "resource_interrupt", "licensing_problems"),
                "unknown": ("unknown",)}
GUROBI_STATUS_NAME = {1: "LOADED", 2: "OPTIMAL", 3: "INFEASIBLE", 4: "INF_OR_UNBD", 5: "UNBOUNDED", 6: "CUTOFF", 7: "ITERATION_LIMIT", 8: "NODE_LIMIT",
                      9: "TIME_LIMIT", 10: "SOLUTION_LIMIT", 11: "INTERRUPTED", 12: "NUMERIC", 13: "SUBOPTIMAL", 14: "INPROGRESS", 15: "USER_OBJ_LIMIT",
                      16: "WORK_LIMIT", 17: "MEM_LIMIT"}
CHUNK = 1_000_000


def linopy_status(condition: str) -> str:
    for status, conds in STATUS_CLASS.items():
        if condition in conds:
            return status
    return "unknown"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def save(p: Path, x) -> None:
    def conv(o):
        if isinstance(o, np.generic):
            return o.item()
        raise TypeError(type(o).__name__)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2, ensure_ascii=False, default=conv) + "\n")


class Sampler(threading.Thread):
    """RSS of this process (and children) every second -> split/RESOURCE_SOLVE.jsonl; peak kept (as s1_solve.Sampler)."""

    def __init__(self, path: Path, interval: float = 1.0):
        super().__init__(daemon=True)
        import psutil
        self.path = Path(path); self.interval = interval; self.peak = 0; self.stop = threading.Event(); self.proc = psutil.Process()

    def run(self) -> None:
        with self.path.open("a") as f:
            while not self.stop.wait(self.interval):
                rss = self.proc.memory_info().rss
                for ch in self.proc.children(recursive=True):
                    try:
                        rss += ch.memory_info().rss
                    except Exception:
                        pass
                self.peak = max(self.peak, rss); f.write(json.dumps(dict(epoch=time.time(), rss=rss, peak=self.peak)) + "\n"); f.flush()


def values_by_label(objs, m, attr: str, prefix: str, labels: np.ndarray, top: int) -> tuple[np.ndarray, int]:
    """attr of the solver objects (Vars / Constrs) placed by their linopy label (name = <prefix><label>), returned in the order of `labels`;
    labels absent from the solver model -> NaN. Chunked so that at most CHUNK names / values are held at once."""
    by_label = np.full(top + 1, np.nan)
    n = len(objs); absent = 0
    for i in range(0, n, CHUNK):
        chunk = objs[i:i + CHUNK]
        names = m.getAttr("VarName" if prefix == "x" else "ConstrName", chunk); vals = m.getAttr(attr, chunk)
        if any(not s.startswith(prefix) for s in names[:1000]):
            raise ValueError(f"solver object names do not carry the linopy prefix {prefix!r}: {names[:3]}")
        lab = np.fromiter((int(s[1:]) for s in names), dtype=np.int64, count=len(names))
        if lab.max(initial=-1) > top:
            raise ValueError("a solver label exceeds the exported label range")
        by_label[lab] = np.asarray(vals, dtype=float)
    out = by_label[labels]
    absent = int(np.isnan(out).sum())
    return out, absent


def parse_kv(items: list[str]) -> dict:
    out = {}
    for it in items or []:
        k, v = it.split("=", 1)
        try:
            out[k] = int(v)
        except ValueError:
            out[k] = float(v)
    return out


def main(a) -> int:
    rd = Path(a.run_dir).resolve(); sp = rd / "split"; lp = rd / "lp"
    build = json.loads((sp / "SPLIT_BUILD.json").read_text())
    receipt = json.loads((rd / "SOLVE_RECEIPT.json").read_text())
    problem = Path(build["problem_file"])
    if not problem.is_absolute():
        problem = sp / problem
    params = dict(build["solver_parameters"])
    protect = parse_kv(a.protect); measure = parse_kv(a.measure)
    if (a.probe_ordering_only or a.probe_iterations is not None or measure) and receipt.get("label") != "SMOKE_TEST_ONLY":
        print("REFUSED: --probe-ordering-only / --probe-iterations / --measure are measurements of a SMOKE_TEST_ONLY run only"); return 2
    if (sp / "SPLIT_SOLVE.json").exists():
        print("REFUSED: split/SPLIT_SOLVE.json exists - the solve of this run has already been made (never repeated)"); return 2
    res = dict(script=SCRIPT, stage="solve", run_dir=str(rd), problem_file=str(problem), problem_bytes=problem.stat().st_size,
               problem_sha256_build=build.get("problem_sha256"), solver_parameters=params, protect_parameters=protect, probe_ordering_only=bool(a.probe_ordering_only),
               probe_iterations=a.probe_iterations, measurement_parameters=measure,
               started_epoch=time.time(), optimize_calls=0, host=platform.node(), python=platform.python_version(), label=receipt.get("label"), scenario=receipt.get("scenario"))
    sampler = Sampler(sp / "RESOURCE_SOLVE.jsonl"); sampler.start()
    t0 = time.time()
    try:
        import gurobipy as gp
        res["gurobipy_version"] = ".".join(map(str, gp.gurobi.version()))
        vl = np.load(lp / "vlabels.npy"); cl = np.load(lp / "clabels.npy")
        with gp.Env() as env:
            t1 = time.time(); m = gp.read(str(problem), env=env); res["read_seconds"] = time.time() - t1
            res.update(fingerprint=f"0x{int(m.Fingerprint) & 0xffffffff:08x}", fingerprint_int=int(m.Fingerprint), num_vars=int(m.NumVars), num_constrs=int(m.NumConstrs), num_nzs=int(m.NumNZs))
            if a.remove_lp:   # disk: the file is not needed after the read (process 3 rebuilds the model); the SHA256 of process 1 stays in SPLIT_BUILD.json
                problem.unlink(); res["problem_removed_after_read"] = True
            for key, value in params.items():   # as linopy Gurobi._solve: solver options in order, then the log file
                m.setParam(key, value)
            for key, value in protect.items():
                m.setParam(key, value)
            for key, value in measure.items():   # measurement-only overrides of the profile (e.g. GURO_PAR_BARDENSETHRESH on a truncated model); never in a formal run
                m.setParam(key, value)
            if a.probe_ordering_only:
                m.setParam("BarIterLimit", 0)
            elif a.probe_iterations is not None:   # measurement: a few barrier iterations (per-iteration seconds, memory with the factor allocated), then ITERATION_LIMIT
                m.setParam("BarIterLimit", int(a.probe_iterations))
            m.setParam("logfile", str(rd / "gurobi.linopy.log"))
            res["optimize_calls"] = 1; save(sp / "SPLIT_SOLVE.json", res)
            t2 = time.time(); m.optimize(); res["optimize_seconds"] = time.time() - t2
            code = int(m.Status); cond = CONDITION_MAP.get(code, "unknown"); status = linopy_status(cond)
            res.update(gurobi_status_code=code, gurobi_status_name=GUROBI_STATUS_NAME.get(code, str(code)), termination_condition=cond, linopy_status=status,
                       runtime_s=float(m.Runtime), work_units=float(m.Work), bar_iter_count=int(m.BarIterCount), sol_count=int(m.SolCount),
                       max_mem_used_gb=float(m.MaxMemUsed), mem_used_gb=float(m.MemUsed))
            have = int(m.SolCount) > 0
            if status in ("ok", "unknown") and have:   # linopy safe_get_solution: ok -> read; unknown -> try, then ok
                res["objective"] = float(m.ObjVal)
                top = int(max(int(vl.max(initial=-1)), int(cl.max(initial=-1)), 0))
                top = max(top, int(m.NumVars) + int(m.NumConstrs))
                vars_ = m.getVars(); cons = m.getConstrs()
                X, ax = values_by_label(vars_, m, "X", "x", vl, top); np.save(sp / "X_raw.npy", X.astype("<f8"))
                RC, ar = values_by_label(vars_, m, "RC", "x", vl, top); np.save(sp / "RC_raw.npy", RC.astype("<f8"))
                del vars_
                Pi, ap = values_by_label(cons, m, "Pi", "c", cl, top); np.save(sp / "Pi_raw.npy", Pi.astype("<f8"))
                del cons
                res["arrays"] = {k: dict(file=f"{k}_raw.npy", count=int(len(v)), absent_labels=int(n_abs), sha256=sha(sp / f"{k}_raw.npy")) for k, v, n_abs in (("X", X, ax), ("Pi", Pi, ap), ("RC", RC, ar))}
                if status == "unknown":
                    res["linopy_status"] = "ok"; res["status_note"] = "solution status unknown, solution parsed (linopy safe_get_solution)"
                res["solution_available"] = True
            else:
                res["solution_available"] = False; res["objective"] = None
                if status == "ok":   # the single-process path would raise on ObjVal here (receipt without termination status); the split path records it
                    res["linopy_status"] = "warning"; res["status_note"] = f"Gurobi status {GUROBI_STATUS_NAME.get(code, code)} without a solution (SolCount 0)"
            m.dispose()
    except Exception as e:
        res["failure"] = dict(error=type(e).__name__, detail=str(e)[:2000], traceback=traceback.format_exc()[-4000:])
    finally:
        sampler.stop.set()
    res.update(solve_seconds=time.time() - t0, finished_epoch=time.time(), peak_rss_bytes=sampler.peak)
    save(sp / "SPLIT_SOLVE.json", res)
    print(json.dumps({k: res.get(k) for k in ("gurobi_status_name", "termination_condition", "linopy_status", "objective", "bar_iter_count", "runtime_s", "work_units", "max_mem_used_gb", "fingerprint", "solve_seconds")}
                     | dict(peak_rss_gib=round(sampler.peak / 2**30, 2), failure=res.get("failure", {}).get("error"))))
    return 0 if "failure" not in res else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--run-dir", type=Path, required=True); p.add_argument("--remove-lp", action="store_true")
    p.add_argument("--probe-ordering-only", action="store_true"); p.add_argument("--probe-iterations", type=int, default=None, help="measurement only (SMOKE_TEST_ONLY): BarIterLimit = K iterations")
    p.add_argument("--protect", action="append", default=[], help="KEY=VALUE run-protection parameter outside the profile (recorded)")
    p.add_argument("--measure", action="append", default=[], help="KEY=VALUE measurement-only override of a profile parameter (SMOKE_TEST_ONLY; recorded as measurement_parameters)")
    sys.exit(main(p.parse_args()))
