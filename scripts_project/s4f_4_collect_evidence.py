"""S4F deliverable: S4F_EVIDENCE.json - light evidence of S4F-0 .. S4F-5 collected from the tables, summaries, registry and git (no solve).

    python scripts_project/s4f_4_collect_evidence.py --out <work>/S4F_EVIDENCE.json --dist <cloud_package_dist> --tests "<test result>"
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "research_inputs/corridors"
R = ROOT / "results_project/s4f"


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--dist", type=Path, required=True); ap.add_argument("--tests", default="")
    a = ap.parse_args()
    import pandas as pd
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    pick = lambda ks: {k: dict(value=reg.at[k, "value"], unit=reg.at[k, "unit"], tier=reg.at[k, "tier"], status=reg.at[k, "status"]) for k in ks if k in reg.index}
    smoke = jl(R / "s4f3/analysis/S4F3_SMOKE_SUMMARY.json"); ex = jl(R / "s4f4/EXTRAPOLATION_S4F4.json"); man = jl(a.dist / "PACKAGE_MANIFEST.json")
    cj = jl(C / "CORRIDORS_S4F2.json"); rj = jl(C / "AUTHOR_READJUST_LINES_S4F2.json")
    ev = dict(
        instruction=dict(file="work/p1_step4f_20261017/S4F_CLAUDE_CODE_INSTRUCTION.md", sha256="28d7458d47e282df6aaf5fa324e3772b886a67f9b178dd728696c5eac7216f03", verified=True),
        git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="bcda8001456618a1cc9eb863ccbdb49ff41a59e1 (PR #29 head)",
                 pr="https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/30 (draft)", log=git("log", "--oneline", "bcda8001..HEAD").splitlines()),
        stops=[dict(id="S4F_STOP_01_LINE91", file="work/p1_step4f_20261017/S4F_STOP_01_LINE91.md",
                    finding="line 91 is a cluster artefact (members: MY-internal line 1599 + TH 115 kV border line 1393), not Sadao - Chuping; 380 MW from the author's readjust_existing_interconnections",
                    user_decision="option 1: line 91 = 80 MW (grade C), Khlong Ngae - Gurun 300 MW, four OSM 250878579 duplicates removed, TH-MY 380 MW")],
        downloads=[],
        s4f0=pick(["s4f_answer_corridor_caps", "s4f_answer_th_my_stock", "s4f_answer_apg4_endpoint", "s4f_answer_coalition_scope", "s4f_answer_lao_to_vn_store",
                   "s4f_answer_sg_vn_kh", "s4f_answer_ph_value"]),
        s4f1=dict(registry=pick(["pypsa_eur_lines_max_extension", "pypsa_eur_links_max_extension", "s4f1_pipeline_extension_caps", "s4f1_max_extension_switch", "s4f1_apg_plan_caps"]),
                  status=(R / "s4f1/STATUS.txt").read_text().splitlines() if (R / "s4f1/STATUS.txt").exists() else [], excess_s4e3=jl(R / "s4f1/MAX_EXTENSION_EXCESS_S4E3.json")),
        s4f2=dict(registry=pick(["th_my_line91_s_nom_2025", "th_my_hvdc_khlong_ngae_gurun_2025", "s4f2_th_my_stock", "s4f2_apg4_endpoint", "s4f2_sensitivity_sg_vn_kh",
                                 "s4f2_lao_vn_store", "s4f2_corridors_s4f2", "s4f2_subsea_share_s4f2", "s4f2_xb_length_shares_s4f2", "s4f2_author_readjust_lines_s4f2"]),
                  corridors=cj, author_readjust=rj,
                  status=(R / "s4f2/STATUS.txt").read_text().splitlines() if (R / "s4f2/STATUS.txt").exists() else []),
        s4f3=dict(runs=smoke.get("runs"), vs_s4e=smoke.get("vs_s4e"), b5_passed=(smoke.get("B5") or {}).get("passed"),
                  b6=dict(passed=(smoke.get("B6") or {}).get("passed"), difference=(smoke.get("B6") or {}).get("difference")),
                  corridors={t: {k: v for k, v in c.items() if k != "built_over_1mw"} for t, c in (smoke.get("corridors") or {}).items()},
                  at_cap={t: {k: v for k, v in c.items() if k != "components"} for t, c in (smoke.get("at_cap") or {}).items()},
                  th_my=smoke.get("th_my"), shipping=smoke.get("shipping"), lao_vn_store=smoke.get("lao_vn_store"), focus=smoke.get("focus"),
                  disconnected_minus_integrated_bn_eur=smoke.get("disconnected_minus_integrated_bn_eur"),
                  ledgers={t: dict(relative_error=v.get("relative_error"), totals_bn_eur=v.get("totals_bn_eur")) for t, v in (smoke.get("ledgers") or {}).items() if v}),
        s4f4=dict(status=(R / "s4f4/STATUS.txt").read_text().splitlines() if (R / "s4f4/STATUS.txt").exists() else [],
                  extrapolation={k: {kk: vv for kk, vv in v.items() if kk in ("barrier_iterations", "barrier_seconds", "wall_seconds", "peak_rss_gib", "extrapolation")} for k, v in (ex.get("runs") or {}).items()},
                  package=dict(commit=man.get("commit"), upload_total_bytes=man.get("upload_total_bytes_excluding_this_manifest"), files=len(man.get("files", [])), run=man.get("run"),
                               second_batch_sensitivities=man.get("second_batch_sensitivities_registered_not_packaged"), coalition_run_rule=man.get("coalition_run_rule"))),
        resources=dict(cloud=False, formal_solves=False, downloads="none (S4F needs no download)"),
        tests=a.tests)
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("written", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
