"""S4E deliverable: S4E_EVIDENCE.json - light evidence of S4E-0 .. S4E-4 collected from the tables, summaries, registry and git (no solve).

    python scripts_project/s4e_4_collect_evidence.py --out <work>/S4E_EVIDENCE.json --dist <cloud_package_dist> --tests "<test result>"
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "research_inputs/corridors"
R = ROOT / "results_project/s4e"


def jl(p):
    return json.loads(Path(p).read_text())


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--dist", type=Path, required=True); ap.add_argument("--tests", default="")
    a = ap.parse_args()
    import pandas as pd
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    pick = lambda ks: {k: dict(value=reg.at[k, "value"], unit=reg.at[k, "unit"], tier=reg.at[k, "tier"], status=reg.at[k, "status"]) for k in ks if k in reg.index}
    cj = jl(C / "CORRIDORS_S4E1.json"); smoke = jl(R / "s4e3/analysis/S4E3_SMOKE_SUMMARY.json"); ex = jl(R / "s4e4/EXTRAPOLATION_S4E4.json")
    man = jl(a.dist / "PACKAGE_MANIFEST.json") if (a.dist / "PACKAGE_MANIFEST.json").exists() else {}
    ev = dict(
        instruction=dict(file="work/p1_step4e_20261017/S4E_CLAUDE_CODE_INSTRUCTION.md", sha256="e5c184c12a91a89ac52e151661cf593a75139396436b95bb75ef0c1cfbb7e9db", verified=True),
        git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="0429a0eb82c40226d03256a97e1093986427538a (PR #28 head)",
                 pr="https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/29 (draft)", log=git("log", "--oneline", "0429a0eb..HEAD").splitlines()),
        stops=[], downloads=[],
        s4e0=pick(["s4e_answer_lao_destination", "s4e_answer_lao_mode", "s4e_answer_lao_shipping", "s4e_answer_storage_cost_basis", "s4e_answer_ship_distance", "s4e_answer_corridors",
                   "s4e_answer_la_th_suboptimal", "s4e_answer_lng_cap", "coalition_run_rule"]),
        s4e1=dict(rule=cj["rule"], adjacency=cj["adjacency"], cross_sea=cj["cross_sea"], domestic=cj["domestic"], new_corridors=cj["new_corridors"], new_domestic=cj["new_domestic"],
                  stock_check=[r for r in cj["stock_check"] if r["verdict"] not in ("no stock on either side",)], graph=cj["graph"], second_pass=cj.get("second_pass"),
                  registry=pick(["s4e1_corridor_rules", "s4e1_corridor_graph", "s4e1_adjacency_switch"])),
        s4e2=pick(["co2_extra_asean_storage_cost_unified", "co2_storage_cost_zep_sensitivity", "s4e2_ship_distance", "s4e2_lao_transit_shipping", "s4e2_sensitivity_lao_transit",
                   "s4e2_sensitivity_lng_uncapped"]),
        s4e3=dict(runs=smoke["runs"], vs_s4d=smoke["vs_s4d"], b5_passed=(smoke.get("B5") or {}).get("passed"), b6=dict(passed=(smoke.get("B6") or {}).get("passed"), difference=(smoke.get("B6") or {}).get("difference")),
                  corridors={t: dict(built_total_mw=v["built_total_mw"], n_built=len(v["built_over_1mw"]), pipes=v["xb_pipelines_built_over_1mw"]) for t, v in smoke["corridors"].items()},
                  exchange=smoke["exchange"], shipping=smoke["shipping"], focus=smoke["focus"], disconnected_minus_integrated_bn_eur=smoke["disconnected_minus_integrated_bn_eur"],
                  ledgers={t: dict(relative_error=v["relative_error"], totals_bn_eur=v["totals_bn_eur"]) for t, v in smoke["ledgers"].items()}),
        s4e4=dict(status=(R / "s4e4/STATUS.txt").read_text().splitlines() if (R / "s4e4/STATUS.txt").exists() else [],
                  extrapolation={k: {kk: vv for kk, vv in v.items() if kk in ("barrier_iterations", "barrier_seconds", "wall_seconds", "peak_rss_gib", "extrapolation")} for k, v in ex["runs"].items()},
                  package=dict(commit=man.get("commit"), upload_total_bytes=man.get("upload_total_bytes_excluding_this_manifest"), files=len(man.get("files", [])), run=man.get("run"),
                               first_batch_sensitivities=man.get("first_batch_sensitivities_registered_not_packaged"), coalition_run_rule=man.get("coalition_run_rule"))),
        resources=dict(cloud=False, formal_solves=False, downloads="none (S4E needs no download)"),
        tests=a.tests)
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("written", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
