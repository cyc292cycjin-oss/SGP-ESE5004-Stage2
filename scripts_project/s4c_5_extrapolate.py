"""S4C-5 (decision 84; user request 2026-10-17): cloud time and memory of the solver profiles A (formal_barrier) and C (barrier_numericfocus2),
extrapolated from the 56x3h runs to 365x24h (x 6.52 snapshots) and 2920x3h (x 52.1, reference), against the package caps (3 h wall clock per
run, Gurobi TimeLimit 10,500 s). Method as CLOUD_RESOURCE_ESTIMATE.md sections 9-11 (INFERENCE):
  * barrier time = measured barrier time x s^1.3 (low) .. s^1.5 (high), s = snapshot ratio; the measured per-iteration time and iteration count
    are reported, and a high case with 1.5 x more iterations is added (S4B section 11: barrier iterations grew with numerical difficulty);
  * model build + LP export + gates (wall clock minus solve) linear in s;
  * peak RSS = (measured - 0.40 GiB) x s + 0.40, upper x 1.4 (Cholesky fill).

    python scripts_project/s4c_5_extrapolate.py --run A=<dir> --run C=<dir> [--run A_kvl_off=<dir>] --status <STATUS.txt> --output <json>
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RATIOS = {"365x24h": 365 / 56, "2920x3h": 2920 / 56}
CAP_S = 3 * 3600; TIME_LIMIT_S = 10500


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="append", required=True); ap.add_argument("--status", type=Path, required=True); ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    wall = {}
    for line in a.status.read_text().splitlines():
        m = re.match(r"RUN_(\w+?):(\w+):(\d+)s", line)
        if m:
            wall[m.group(1)] = int(m.group(3))
    out = dict(method=__doc__.split("\n\n")[0], caps=dict(wall_clock_s=CAP_S, gurobi_time_limit_s=TIME_LIMIT_S), runs={})
    for spec in a.run:
        tag, d = spec.split("=", 1); d = Path(d)
        r = json.loads((d / "SOLVE_RECEIPT.json").read_text()); gl = r.get("gurobi_log_stats", {})
        bar = " ".join(gl.get("lines", {}).get("barrier", [])); m = re.search(r"in (\d+) iterations and ([\d.]+) seconds", bar)
        it, bt = (int(m.group(1)), float(m.group(2))) if m else (None, None)
        solve = float(r.get("solve_seconds") or 0); peak = (r.get("peak_rss_bytes") or 0) / 2**30
        w = wall.get(Path(d).name, wall.get(tag)); other = (w - solve) if w else None
        row = dict(profile=r.get("solver_profile"), kvl=(r.get("scaling") or {}).get("kirchhoff_row_normalisation", {}).get("applied"), termination=r.get("termination_condition"),
                   lp=r.get("lp"), barrier_iterations=it, barrier_seconds=bt, seconds_per_iteration=(bt / it if it else None), solve_seconds=solve, wall_seconds=w,
                   non_solve_seconds=other, peak_rss_gib=peak, extrapolation={})
        for k, s in RATIOS.items():
            lo, hi = bt * s ** 1.3, bt * s ** 1.5
            hi_it = hi * 1.5
            nonsolve = (other or 0) * s
            mem = (peak - 0.40) * s + 0.40
            e = dict(snapshot_ratio=s, barrier_s=[lo, hi], barrier_s_with_1_5x_iterations=hi_it, non_solve_s=nonsolve,
                     wall_s=[lo + nonsolve, hi + nonsolve, hi_it + nonsolve], peak_rss_gib=[mem, mem * 1.4],
                     within_time_limit=dict(low=lo + nonsolve <= TIME_LIMIT_S, high=hi + nonsolve <= TIME_LIMIT_S, high_1_5x_iterations=hi_it + nonsolve <= TIME_LIMIT_S))
            row["extrapolation"][k] = e
        out["runs"][tag] = row
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(out, indent=1, default=str))
    for tag, row in out["runs"].items():
        print(tag, row["profile"], "kvl", row["kvl"], row["termination"], "it", row["barrier_iterations"], "bar_s", row["barrier_seconds"], "s/it", round(row["seconds_per_iteration"] or 0, 3),
              "solve", round(row["solve_seconds"], 1), "wall", row["wall_seconds"], "peak", round(row["peak_rss_gib"], 2))
        for k, e in row["extrapolation"].items():
            print("   ", k, "barrier min", [round(x / 60, 1) for x in e["barrier_s"]], "+1.5x it", round(e["barrier_s_with_1_5x_iterations"] / 60, 1), "wall min", [round(x / 60, 1) for x in e["wall_s"]],
                  "RSS GiB", [round(x, 1) for x in e["peak_rss_gib"]], "within 10500 s", e["within_time_limit"])


if __name__ == "__main__":
    main()
