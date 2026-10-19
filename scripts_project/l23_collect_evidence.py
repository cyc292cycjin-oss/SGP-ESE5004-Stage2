"""L23 C9: lightweight evidence of the first cloud batch (L23_RUN1_EVIDENCE.json) from the downloaded results, the C9 summary and the violation
analyses. Read-only; no solve. Host, port and licence content are never read or written.

    python scripts_project/l23_collect_evidence.py --results <cloud_results/<ts>> --work <work/p1_l23_run1_20261019> --out <L23_RUN1_EVIDENCE.json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RUNS = ("integrated", "disconnected", "disconnected_gap", "integrated_nze")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ("results", "work", "out"):
        ap.add_argument("--" + k, type=Path, required=True)
    a = ap.parse_args()
    S = json.loads((a.work / "evidence/c9_summary/L23_C9_SUMMARY.json").read_text())
    tar = a.results / "results_20261018T180030Z_5623.tar.gz"; late = a.results / "nze_late/nze_late_outputs_20261018T180030Z_5623.tar.gz"
    ev = dict(
        step="L23 first cloud batch 365x24h (C0-C9)", label="FORMAL_TRIAL_365X24H", resolution="DAILY_SCREENING_365X24H (allocation conclusions rest on 2920x3h)",
        instruction_sha256="2c6d9dcad11a2e6e5ff9f25d0ec6a1ff1cd45213dfabce636987df5b54790d22", package_commit="56d283580799c510b617c70b6e3292ba224e4ae0",
        instance="AutoDL north-west B zone machine 144 (12 cores Xeon Silver 4214R, 90 GiB cgroup, data disk 50 GB)", solver_profile="formal_barrier", mode="serial",
        timeline_sgt=dict(container_start="2026-10-19 00:40:26", preflight_ok="01:54:38", launch="02:00:30", killed_3h_nze="09:00:23", done="09:00:38",
                          nze_process_last_write="09:03:02", licence_removed="09:34:34"),
        cost=dict(power_on_to_done_h=8.34, cny_per_h=1.08, cny_power_on_to_done=9.00, note="billing continues until the user powers off in the AutoDL console"),
        status_txt=(a.results / "STATUS.txt").read_text().splitlines(),
        archives={tar.name: dict(bytes=tar.stat().st_size, sha256=sha256(tar), local_check="sha256sum -c OK", in_tarball=True),
                  late.name: dict(bytes=late.stat().st_size, sha256=sha256(late), local_check="sha256sum -c OK", in_tarball=False,
                                  note="NZE outputs written by s2_solve.py after the wall-clock kill marker and after the tarball was sealed (finding 3)")},
        licence_scan="no licence string in the unpacked results, nze_late, STATUS, MONITOR, evidence/c9",
        runs={}, cpu_speed=S.get("cpu_speed"), gates={}, B5_passed=(S.get("B5") or {}).get("passed"), B6=S.get("B6"), nze_vs_integrated=S.get("nze_vs_integrated"),
        ledger_bn_eur=dict(integrated=S["ledger_difference"]["integrated_bn_eur"], disconnected=S["ledger_difference"]["disconnected_bn_eur"],
                           disconnected_minus_integrated=S["ledger_difference"]["total_bn_eur"], main_subjects=S["ledger_difference"]["main_subjects"],
                           vs_s4k_smoke=S["ledger_difference"].get("vs_s4k_smoke"), rank_correlation=S["ledger_difference"].get("rank_correlation_spearman"),
                           nze_minus_integrated=S.get("ledger_nze_minus_integrated_bn_eur")),
        asean_by_group=S.get("asean_by_group"), cross_border_capacity_gw=S.get("cross_border_capacity"), transport_totals=S.get("transport_totals"),
        lines_at_single_cap=S.get("at_cap"), long_lines=S.get("long_lines"), violations={}, barrier={})
    for t in RUNS:
        r = S["runs"].get(t)
        if r:
            ev["runs"][t] = {k: r.get(k) for k in ("termination", "objective_eur", "num_col", "num_row", "nnz", "barrier_iterations", "barrier_seconds", "work_units",
                                                   "solve_seconds", "wall_seconds", "build_seconds", "peak_rss_gib_receipt", "status_line", "killed_3h_utc")}
        g = S["gates"].get(t)
        if g:
            ev["gates"][t] = dict(passed=g["passed"], all_passed_solver_tolerances=g["all_passed_solver_tolerances"], all_passed_barconvtol=g["all_passed_barconvtol"],
                                  failing_solver_tolerances=g["failing_solver_tolerances"], failing_barconvtol=g["failing_barconvtol"],
                                  A1_A2_S4B={k: v for k, v in g["details"]["A1_A2_S4B"].items() if not isinstance(v, dict)}, B16=g["details"]["B16_LEDGER"])
        v = a.work / f"evidence/c9/VIOLATIONS_{t}.json"
        if v.exists():
            d = json.loads(v.read_text())
            ev["violations"][t] = dict(label_check=d["label_check"], totals=d["totals"],
                                       over_budget_by_family={k: x["rows_over_budget"] for k, x in d["by_family"].items() if x["rows_over_budget"]})
    bt = json.loads((a.work / "evidence/c9/BARRIER_TRAJECTORIES.json").read_text())
    for t, x in bt.items():
        ev["barrier"][t] = dict(min_primal_residual=x.get("min_primal_residual"), jumps=x.get("jumps"))
    nz = json.loads((a.work / "evidence/c9/BARRIER_TRAJECTORY_integrated_nze.json").read_text())
    ev["barrier"]["integrated_nze"] = dict(min_primal_residual=nz["min_primal_residual"], first_jump=nz["first_jump"], last20_ranges=nz["last20_ranges"])
    ev["findings_not_handled"] = 12
    ev["user_decisions"] = ["treatment of the four non-optimal runs", "archive of the NZE outputs outside the tarball", "timing of the run_365x24h.sh / preflight.sh fixes"]
    a.out.write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=str) + "\n")
    print("written", a.out, a.out.stat().st_size, "B")


if __name__ == "__main__":
    main()
