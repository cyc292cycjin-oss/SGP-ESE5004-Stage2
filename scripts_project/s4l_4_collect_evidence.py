"""S4L deliverable: S4L_EVIDENCE.json - light evidence of S4L-0 .. S4L-4 collected from the registry, the inventory / impact tables, the S4L-2 matrix
summary, the S4L-3 script test results and git (no solve).

    python scripts_project/s4l_4_collect_evidence.py --out <work>/S4L_EVIDENCE.json --tests "<test result>"
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
N = ROOT / "research_inputs/numerics"
R = ROOT / "results_project/s4l"
D = ROOT / "research/06_scope_redesign/p1_step4l_20261019"


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


def lines(p):
    p = Path(p)
    return [x for x in p.read_text().splitlines() if "PROJ" not in x] if p.exists() else []


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--tests", default="")
    a = ap.parse_args()
    import pandas as pd
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    pick = lambda ks: {k: dict(value=reg.at[k, "value"], unit=reg.at[k, "unit"], tier=reg.at[k, "tier"], status=reg.at[k, "status"]) for k in ks if k in reg.index}
    dust = jl(N / "DUST_S4L1.json"); impact = jl(N / "DUST_IMPACT_S4L1.json")
    mx = jl(R / "s4l2b/analysis/S4L2_MATRIX_SUMMARY.json") or jl(R / "s4l2/analysis/S4L2_MATRIX_SUMMARY.json")   # s4l2b = corrected-rule continuation + bio98 arm (S4L-5), s4k runs linked from s4l2
    mx_first = jl(R / "s4l2/analysis/S4L2_MATRIX_SUMMARY.json")   # the first matrix (first-rule cleaned network: infeasible)
    runs = {k: {kk: v.get(kk) for kk in ("termination", "objective", "solve_seconds", "barrier_iterations", "barrier_seconds", "crossover_present", "crossover_plus_simplex_seconds",
                                         "crossover_over_barrier", "solved_with", "extra_simplex_iterations", "all_passed_solver_tolerances", "A1_A2_gate", "A1_A2", "A1_A2_S4B", "A3_S4B",
                                         "B2", "B14", "B15", "B16", "B16_relative_error", "num_col", "num_row", "nnz", "peak_rss_gib", "result_line", "gurobi_warnings")}
            for k, v in (mx.get("runs") or {}).items()}
    ev = dict(
        instruction=dict(file="work/p1_step4l_20261019/S4L_CLAUDE_CODE_INSTRUCTION.md", sha256="03508400f675304cd0bdfd40ccbd0c61005644e7b2a122dffbe2048e6a5d529b", verified=True),
        git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="efb37fc20ef1a0b185215c553ba9a61bc871830d (L23 head, PR #36)",
                 log=git("log", "--oneline", "efb37fc2..HEAD").splitlines()),
        stops=[x for x in lines(R / "s4l2/STATUS.txt") if x.startswith(("STOP_", "NOT_OPTIMAL_", "KILLED_"))], downloads=[],
        s4l0=pick([x for x in reg.index if x.startswith("s4l_")]),
        s4l1=dict(registry=pick([x for x in reg.index if x.startswith("s4l1_")]), thresholds=dust.get("thresholds"), pypsa_eur=dust.get("pypsa_eur"),
                  inventory={sc: dict(network_sha256=v.get("sha256"), components=v.get("components"), clip_p_max_pu_applied=v.get("clip_p_max_pu_applied"), summary=v.get("summary"),
                                      pools_below_threshold=v.get("pools_below_threshold"), renewable_below_capacity=v.get("renewable_below_capacity"),
                                      single_attachment_kept=v.get("single_attachment_kept"), merged_groups=len(v.get("merged_groups") or [])) for sc, v in (dust.get("scenarios") or {}).items()},
                  l23_usage={sc: v.get("usage") for sc, v in (dust.get("l23") or {}).items()},
                  impact={sc: {k: v.get(k) for k in ("mode", "thresholds", "removed", "merged_links_removed", "removed_required_structure", "components_s4k", "components_s4l", "differences", "meta_keys_differ")}
                          for sc, v in impact.items()},
                  builds=lines(R / "s4l1/STATUS.txt"),
                  build_receipts={sc: {k: jl(R / f"s4l1/builds/{sc}/{sc}_BUILD_RECEIPT.json").get(k) for k in ("code_sha", "research_config_sha256")} | dict(network=(jl(R / f"s4l1/builds/{sc}/{sc}_BUILD_RECEIPT.json").get("network") or {}).get("sha256"))
                                  for sc in ("integrated", "disconnected")}),
        s4l2=dict(registry=pick([x for x in reg.index if x.startswith("s4l2_")]), standard=mx.get("standard"), profiles=mx.get("profiles"),
                  status_first_matrix=lines(R / "s4l2/STATUS.txt"), status_continuation=lines(R / "s4l2b/STATUS.txt"),
                  runs=runs, combinations=mx.get("combinations"), lp_size=mx.get("lp_size"), repeat_vs_s4k3=mx.get("repeat_vs_s4k3"), price_differences=mx.get("price_differences"),
                  prices_by_country=mx.get("prices_by_country"),
                  first_rule_runs={k: {kk: v.get(kk) for kk in ("termination", "barrier_iterations", "barrier_seconds", "solve_seconds", "result_line")} for k, v in (mx_first.get("runs") or {}).items() if k.startswith("s4l_")},
                  b12_recheck=jl(D / "evidence/s4l_2/B12_RECHECK_s4l_builds_2983d951.json")),
        s4l5=dict(registry=pick([x for x in reg.index if x.startswith("s4l5_")]), biomass_balance=jl(N / "BIOMASS_BALANCE_S4L5.json"),
                  impact={sc: {k: v.get(k) for k in ("components", "loads_changed", "load_changes", "pool_balance", "research_config_sha256", "overrides")} for sc, v in (jl(N / "BIOMASS98_IMPACT_S4L5.json") or {}).items()},
                  builds=lines(R / "s4l5/BUILD_STATUS.txt"), status=lines(R / "s4l5/STATUS.txt"),
                  runs={k: v for k, v in runs.items() if k.startswith("bio98_")}, combination=(mx.get("combinations") or {}).get("bio98_A"),
                  solid_biomass_shadow_prices={t: {k.split("|")[1]: v for k, v in (mx.get("prices_by_country") or {}).get(t, {}).items() if k.startswith("solid biomass|")}
                                               for t in ("s4k_A_integrated", "s4l_A_integrated", "bio98_A_integrated", "s4k_A_disconnected", "s4l_A_disconnected", "bio98_A_disconnected")}),
        s4l3=dict(scripts={f: dict(sha256=__import__("hashlib").sha256((D / "cloud_package" / f).read_bytes()).hexdigest()) for f in ("run_365x24h.sh", "preflight.sh", "make_package.sh") if (D / "cloud_package" / f).exists()},
                  s4k_scripts={f: dict(sha256=__import__("hashlib").sha256((ROOT / "research/06_scope_redesign/p1_step4k_20261018/cloud_package" / f).read_bytes()).hexdigest()) for f in ("run_365x24h.sh", "preflight.sh") if (ROOT / "research/06_scope_redesign/p1_step4k_20261018/cloud_package" / f).exists()},
                  test_results=lines(D / "evidence/s4l_3/results/TEST_RESULTS.txt"), package_rebuilt=False, cloud=False),
        resources=dict(cloud=False, formal_solves=False, downloads="none (S4L needs no download)",
                       local_solves="8 x 56x3h (S4L-2, authorised) + 4 x 56x3h (S4L-2 continuation, corrected cleanup rule, authorised 2026-10-19) + 2 x 56x3h (S4L-5 diagnostic, authorised 2026-10-19); stop-loss 30 min each, serial"),
        tests=a.tests)
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("written", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
