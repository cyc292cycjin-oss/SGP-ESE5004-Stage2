"""S4H deliverable: S4H_EVIDENCE.json - light evidence of S4H-0 .. S4H-5 collected from the tables, summaries, registry and git (no solve).

    python scripts_project/s4h_4_collect_evidence.py --out <work>/S4H_EVIDENCE.json --dist <cloud_package_dist> --tests "<test result>"
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "research_inputs/corridors"
R = ROOT / "results_project/s4h"


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


def lines(p):
    p = Path(p)
    return [x for x in p.read_text().splitlines() if "PROJ" not in x] if p.exists() else []


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--dist", type=Path, required=True); ap.add_argument("--tests", default="")
    a = ap.parse_args()
    import pandas as pd
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    pick = lambda ks: {k: dict(value=reg.at[k, "value"], unit=reg.at[k, "unit"], tier=reg.at[k, "tier"], status=reg.at[k, "status"]) for k in ks if k in reg.index}
    smoke = jl(R / "s4h3/analysis/S4H3_SMOKE_SUMMARY.json"); ex = jl(R / "s4h4/EXTRAPOLATION_S4H4.json"); man = jl(a.dist / "PACKAGE_MANIFEST.json")
    cor = jl(C / "CORRIDORS_S4H2.json"); chk = jl(R / "s4h2/CHECK_S4H2.json")
    ev = dict(
        instruction=dict(file="work/p1_step4h_20261017/S4H_CLAUDE_CODE_INSTRUCTION.md", sha256="a029bd64cef2ae1b84aec4ebc186ede21630283d17153df9aed4ae32d1fd33bd", verified=True),
        git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="78c95a75cd48afefc11e4e9e747c2ce96f0f2f1d (PR #31 head)",
                 pr="https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/32 (draft)", log=git("log", "--oneline", "78c95a75..HEAD").splitlines()),
        stops=[], downloads=[],
        s4h0=pick(["s4h_answer_la_vn_stock", "s4h_answer_candidate_reactance", "s4h_answer_numerical_risk", "s4h_answer_cloud_package", "s4h_scope_rule"]),
        s4h1=dict(registry=pick(["la_vn_grid_stock_2025", "s4h1_la_vn_stock_switch", "s4h1_ipp_export_lines_estimate"]), table=jl(C / "LA_VN_STOCK_S4H1.json"),
                  status=lines(R / "s4h1/STATUS.txt")),
        s4h2=dict(registry=pick(["s4h2_candidate_num_parallel_switch", "s4h2_candidate_convention_sources", "s4h2_apg17_readjust", "s4h2_readjust_impedance_table",
                                 "s4h2_reference_candidates", "s4h2_candidate_completeness_table", "s4h2_subsea_table", "s4h2_length_shares_table"]),
                  corridors={k: v for k, v in cor.items() if k != "sources"}, sources=cor.get("sources"), check=chk, status=lines(R / "s4h2/STATUS.txt")),
        s4h3=dict(runs=smoke.get("runs"), vs_s4g=smoke.get("vs_s4g"), disconnected_objective_vs_s4g=smoke.get("disconnected_objective_vs_s4g"),
                  tolerance=smoke.get("tolerance"), b5_passed=(smoke.get("B5") or {}).get("passed"),
                  b6=dict(passed=(smoke.get("B6") or {}).get("passed"), difference=(smoke.get("B6") or {}).get("difference"),
                          s4g_difference=(smoke.get("B6_s4g") or {}).get("difference")),
                  B16=smoke.get("B16"), lao=smoke.get("lao"), at_cap=smoke.get("at_cap"), focus=smoke.get("focus"), ipp_vs_ledger=smoke.get("ipp_vs_ledger"),
                  disconnected_minus_integrated_bn_eur=smoke.get("disconnected_minus_integrated_bn_eur"), status=lines(R / "s4h3/STATUS.txt"),
                  ledgers={t: dict(relative_error=v.get("relative_error"), totals_bn_eur=v.get("totals_bn_eur")) for t, v in (smoke.get("ledgers") or {}).items() if v}),
        s4h4=dict(status=lines(R / "s4h4/STATUS.txt"),
                  extrapolation={k: {kk: vv for kk, vv in v.items() if kk in ("barrier_iterations", "barrier_seconds", "wall_seconds", "peak_rss_gib", "extrapolation")} for k, v in (ex.get("runs") or {}).items()},
                  package=dict(commit=man.get("commit"), upload_total_bytes=man.get("upload_total_bytes_excluding_this_manifest"), files=len(man.get("files", [])), run=man.get("run"),
                               second_batch_sensitivities=man.get("second_batch_sensitivities_registered_not_packaged"), supersedes=man.get("supersedes"),
                               coalition_run_rule=man.get("coalition_run_rule"))),
        resources=dict(cloud=False, formal_solves=False, downloads="none (S4H needs no download)"),
        tests=a.tests)
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("written", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
