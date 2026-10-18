"""S4J deliverable: S4J_EVIDENCE.json - light evidence of S4J-0 .. S4J-7 collected from the tables, summaries, registry and git (no solve).

    python scripts_project/s4j_7_collect_evidence.py --out <work>/S4J_EVIDENCE.json --dist <cloud_package_dist> --tests "<test result>"
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "research_inputs/corridors"
R = ROOT / "results_project/s4j"


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
    smoke = jl(R / "s4j6/analysis/S4J6_SMOKE_SUMMARY.json"); ex = jl(R / "s4j7/EXTRAPOLATION_S4J7.json"); man = jl(a.dist / "PACKAGE_MANIFEST.json")
    ne = pd.read_csv(ROOT / "research_inputs/demand_v5/NONINDUSTRIAL_ELECTRICITY_S4J1.csv") if (ROOT / "research_inputs/demand_v5/NONINDUSTRIAL_ELECTRICITY_S4J1.csv").exists() else None
    ev = dict(
        instruction=dict(file="work/p1_step4j_20261018/S4J_CLAUDE_CODE_INSTRUCTION.md", sha256="c20957448c69128c05eaf4e271bcca7f98eecc7ccd3121cd37f3581daff3348f", verified=True),
        git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="09ffb727114be437abf078a5393d0a2cb3ea403e (PR #33 head)",
                 pr="https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/34 (draft)", log=git("log", "--oneline", "09ffb727..HEAD").splitlines()),
        stops=[], downloads=[],
        s4j0={k: v for k, v in pick([x for x in reg.index if x.startswith("s4j_answer_") or x.startswith("s4j_registered_") or x == "s4j_scope_rule"]).items()},
        s4j1=dict(registry=pick(["s4j1_nonindustrial_electricity_switch", "s4j1_base_load_sectors", "s4j1_explicit_electricity_inventory", "s4j1_transport_electricity_row"]),
                  table=(ne.round(6).to_dict(orient="records") if ne is not None else None), status=lines(R / "s4j1/STATUS.txt")),
        s4j2=dict(registry=pick(["s4j2_transmission_losses_switch", "s4j2_ac_transmission_losses", "s4j2_link_losses", "s4j2_line_loss_approximation"]),
                  losses={k: v for k, v in jl(C / "LOSSES_S4J2.json").items() if k != "sources"}, sources=jl(C / "LOSSES_S4J2.json").get("sources"), status=lines(R / "s4j2/STATUS.txt")),
        s4j3=dict(registry=pick(["s4j3_dc_bidirectional", "s4j3_b2b_follows_dc"]), converters=jl(C / "DC_CONVERTERS_S4J3.json"), status=lines(R / "s4j3/STATUS.txt")),
        s4j4=dict(script_checks=lines(ROOT / "research/06_scope_redesign/p1_step4j_20261018/evidence/s4j_4/SCRIPT_CHECKS.txt")),
        s4j5=dict(review=jl(R / "s4j5/review/S4J5_REVIEW.json"), status=lines(R / "s4j5/STATUS.txt")),
        s4j6=dict(runs=smoke.get("runs"), vs_s4h=smoke.get("vs_s4h"), tolerance=smoke.get("tolerance"), lp_vs_s4h=smoke.get("lp_vs_s4h"), b5_passed=(smoke.get("B5") or {}).get("passed"),
                  b6=dict(passed=(smoke.get("B6") or {}).get("passed"), difference=(smoke.get("B6") or {}).get("difference"), s4h_difference=(smoke.get("B6_s4h") or {}).get("difference")),
                  B16=smoke.get("B16"), focus=smoke.get("focus"), th_my=smoke.get("th_my"), at_cap=smoke.get("at_cap"), transport=smoke.get("transport"), capacity=smoke.get("capacity"),
                  disconnected_objective_vs_s4h=smoke.get("disconnected_objective_vs_s4h"), status=lines(R / "s4j6/STATUS.txt"),
                  ledgers={t: dict(relative_error=v.get("relative_error"), totals_bn_eur=v.get("totals_bn_eur")) for t, v in (smoke.get("ledgers") or {}).items() if v}),
        s4j7=dict(status=lines(R / "s4j7/STATUS.txt"),
                  extrapolation={k: {kk: vv for kk, vv in v.items() if kk in ("barrier_iterations", "barrier_seconds", "wall_seconds", "peak_rss_gib", "extrapolation")} for k, v in (ex.get("runs") or {}).items()},
                  package=dict(commit=man.get("commit"), upload_total_bytes=man.get("upload_total_bytes_excluding_this_manifest"), files=len(man.get("files", [])), run=man.get("run"),
                               second_batch_sensitivities=man.get("second_batch_sensitivities_registered_not_packaged"), supersedes=man.get("supersedes"),
                               coalition_run_rule=man.get("coalition_run_rule"))),
        resources=dict(cloud=False, formal_solves=False, downloads="none (S4J needs no download)"),
        tests=a.tests)
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("written", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
