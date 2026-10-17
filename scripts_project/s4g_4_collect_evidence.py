"""S4G deliverable: S4G_EVIDENCE.json - light evidence of S4G-0 .. S4G-5 collected from the tables, summaries, registry and git (no solve).

    python scripts_project/s4g_4_collect_evidence.py --out <work>/S4G_EVIDENCE.json --dist <cloud_package_dist> --tests "<test result>"
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "research_inputs/corridors"
R = ROOT / "results_project/s4g"


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


def lines(p):
    p = Path(p)
    return p.read_text().splitlines() if p.exists() else []


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--dist", type=Path, required=True); ap.add_argument("--tests", default="")
    a = ap.parse_args()
    import pandas as pd
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    pick = lambda ks: {k: dict(value=reg.at[k, "value"], unit=reg.at[k, "unit"], tier=reg.at[k, "tier"], status=reg.at[k, "status"]) for k in ks if k in reg.index}
    smoke = jl(R / "s4g3/analysis/S4G3_SMOKE_SUMMARY.json"); ex = jl(R / "s4g4/EXTRAPOLATION_S4G4.json"); man = jl(a.dist / "PACKAGE_MANIFEST.json")
    chk = jl(R / "s4g1/READJUST_CHECK_S4G1.json"); lavn = jl(C / "LA_VN_STOCK_CHECK_S4G1.json")
    ev = dict(
        instruction=dict(file="work/p1_step4g_20261017/S4G_CLAUDE_CODE_INSTRUCTION.md", sha256="2fd959e9134804a51aecc68b252b2ebe966813e65ed7dabd945ad3953a0d915c", verified=True),
        git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="04681769cc4af29abbc034962ab1e212dc5b4361 (PR #30 head)",
                 pr="https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/31 (draft)", log=git("log", "--oneline", "04681769..HEAD").splitlines()),
        stops=[], downloads=[],
        s4g0=pick(["s4g_answer_readjust_lines", "s4g_answer_apg_plans_rule", "s4g_answer_lao_th_store", "s4g_answer_cloud_package"]),
        s4g1=dict(registry=pick(["s4g1_line_type_relation", "s4g1_readjust_impedance_table", "s4g1_readjust_impedance_switch"]),
                  sources=jl(C / "READJUST_IMPEDANCE_S4G1.json"), check={k: v for k, v in chk.items() if k != "consistency"},
                  consistency={k: v for k, v in (chk.get("consistency") or {}).items() if k != "over_10pct_list"},
                  la_vn={k: v for k, v in (lavn.get("found") or {}).items() if k != "osm_prebuilt"},
                  la_vn_osm={f: x.get("la_vn") for f, x in ((lavn.get("found") or {}).get("osm_prebuilt") or {}).items()},
                  status=lines(R / "s4g1/STATUS.txt")),
        s4g2=dict(registry=pick(["s4g2_lao_th_store", "s4g2_apg_plans_rule_confirmed", "s4g2_sensitivity_readjust_author"]), status=lines(R / "s4g2/STATUS.txt")),
        s4g3=dict(runs=smoke.get("runs"), vs_s4f=smoke.get("vs_s4f"), disconnected_objective_vs_s4f=smoke.get("disconnected_objective_vs_s4f"),
                  b5_passed=(smoke.get("B5") or {}).get("passed"), b6=dict(passed=(smoke.get("B6") or {}).get("passed"), difference=(smoke.get("B6") or {}).get("difference")),
                  gates={t: dict(all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"), A1_A2_S4B=g.get("A1_A2_S4B")) for t, g in (smoke.get("gates") or {}).items()},
                  lines_19=smoke.get("lines_19"), mekong=smoke.get("mekong"), corridors=smoke.get("corridors"), at_cap=smoke.get("at_cap"), focus=smoke.get("focus"),
                  disconnected_minus_integrated_bn_eur=smoke.get("disconnected_minus_integrated_bn_eur"),
                  ledgers={t: dict(relative_error=v.get("relative_error"), totals_bn_eur=v.get("totals_bn_eur")) for t, v in (smoke.get("ledgers") or {}).items() if v}),
        s4g4=dict(status=lines(R / "s4g4/STATUS.txt"),
                  extrapolation={k: {kk: vv for kk, vv in v.items() if kk in ("barrier_iterations", "barrier_seconds", "wall_seconds", "peak_rss_gib", "extrapolation")} for k, v in (ex.get("runs") or {}).items()},
                  package=dict(commit=man.get("commit"), upload_total_bytes=man.get("upload_total_bytes_excluding_this_manifest"), files=len(man.get("files", [])), run=man.get("run"),
                               second_batch_sensitivities=man.get("second_batch_sensitivities_registered_not_packaged"), supersedes=man.get("supersedes"),
                               coalition_run_rule=man.get("coalition_run_rule"))),
        resources=dict(cloud=False, formal_solves=False, downloads="none (S4G needs no download)"),
        tests=a.tests)
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("written", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
