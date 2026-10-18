"""S4K deliverable: S4K_EVIDENCE.json - light evidence of S4K-0 .. S4K-5 collected from the tables, summaries, registry and git (no solve).

    python scripts_project/s4k_5_collect_evidence.py --out <work>/S4K_EVIDENCE.json --dist <cloud_package_dist> --tests "<test result>"
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "research_inputs/corridors"
R = ROOT / "results_project/s4k"


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
    proxy = jl(C / "AC_LOSS_PROXY_S4K1.json"); review = jl(R / "s4k2/review/S4K2_REVIEW.json"); smoke = jl(R / "s4k3/analysis/S4K3_SMOKE_SUMMARY.json")
    ex = jl(R / "s4k4/EXTRAPOLATION_S4K4.json"); man = jl(a.dist / "PACKAGE_MANIFEST.json")
    ev = dict(
        instruction=dict(file="work/p1_step4k_20261018/S4K_CLAUDE_CODE_INSTRUCTION.md", sha256="a803f1653736640f1358659b156e6d9dbf7c72be61b9455863f793dea75825d5", verified=True),
        git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="36b8195bc8508c1f3ea1b4a6475fd860d075d16f (PR #34 head)",
                 pr="https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/35 (draft)", log=git("log", "--oneline", "36b8195b..HEAD").splitlines()),
        stops=[x for x in lines(R / "s4k3/STATUS.txt") if x.startswith(("STOP_", "NOT_PASSED_", "KILLED_"))], downloads=[],
        s4k0=pick([x for x in reg.index if x.startswith("s4k_answer_") or x in ("s4k_ledger_s4i_entry", "s4k_scope_rule", "s4k_question_source_s4j")]),
        s4k1=dict(registry=pick(["s4k1_ac_losses_switch", "s4k1_reference_loading", "s4k1_lambda", "s4k1_deviation_from_pypsa_eur", "s4k1_loss_structure", "s4k1_ledger"]),
                  sources=proxy.get("sources"), meta=proxy.get("meta"), reference_check=proxy.get("reference_check"), lambda_alpha_0_5=proxy.get("lambda_alpha_0_5"),
                  lambda_alpha_1_0=proxy.get("lambda_alpha_1_0"), length_ratio=proxy.get("length_ratio"), tangent_vs_proxy=proxy.get("tangent_vs_proxy"),
                  model_check=proxy.get("model_check"), status=lines(R / "s4k1/STATUS.txt")),
        s4k2=dict(review={k: v for k, v in review.items() if k != "model_check"},
                  model_check={k: {kk: vv for kk, vv in v.items() if kk != "loss_rows"} for k, v in (review.get("model_check") or {}).items()}, status=lines(R / "s4k2/STATUS.txt")),
        s4k3=dict(runs=smoke.get("runs"), vs_s4j=smoke.get("vs_s4j"), tolerance=smoke.get("tolerance"), lp_vs_s4j=smoke.get("lp_vs_s4j"), b5_passed=(smoke.get("B5") or {}).get("passed"),
                  b6=dict(passed=(smoke.get("B6") or {}).get("passed"), difference=(smoke.get("B6") or {}).get("difference"),
                          s4j_difference=(smoke.get("B6_s4j") or {}).get("difference"), s4h_difference=(smoke.get("B6_s4h") or {}).get("difference")),
                  B16=smoke.get("B16"), focus=smoke.get("focus"), transport_totals=smoke.get("transport_totals"), capacity=smoke.get("capacity"), at_cap=smoke.get("at_cap"),
                  clustering=smoke.get("clustering"), th_my=smoke.get("th_my"), disconnected_objective_vs_s4j=smoke.get("disconnected_objective_vs_s4j"),
                  status=lines(R / "s4k3/STATUS.txt"),
                  ledgers={t: dict(relative_error=v.get("relative_error"), totals_bn_eur=v.get("totals_bn_eur")) for t, v in (smoke.get("ledgers") or {}).items() if v}),
        s4k4=dict(status=lines(R / "s4k4/STATUS.txt"),
                  extrapolation={k: {kk: vv for kk, vv in v.items() if kk in ("barrier_iterations", "barrier_seconds", "wall_seconds", "peak_rss_gib", "extrapolation")} for k, v in (ex.get("runs") or {}).items()},
                  package=dict(commit=man.get("commit"), upload_total_bytes=man.get("upload_total_bytes_excluding_this_manifest"), files=len(man.get("files", [])), run=man.get("run"),
                               second_batch_sensitivities=man.get("second_batch_sensitivities_registered_not_packaged"), supersedes=man.get("supersedes"),
                               coalition_run_rule=man.get("coalition_run_rule"))),
        resources=dict(cloud=False, formal_solves=False, downloads="none (S4K needs no download)"),
        tests=a.tests)
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("written", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
