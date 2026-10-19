"""S4M deliverable: S4M_EVIDENCE.json - light evidence of S4M-0 .. S4M-5 collected from the registry, build receipts, S4I audit / review, smoke summary,
package manifest, script tests, resource check and git (no solve).

    python scripts_project/s4m_5_collect_evidence.py --out <work>/S4M_EVIDENCE.json --dist <cloud_package_dist> --tests "<test result>"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results_project/s4m"
D = ROOT / "research/06_scope_redesign/p1_step4m_20261019"
N = ROOT / "research_inputs/numerics"


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


def lines(p):
    p = Path(p)
    return [x for x in p.read_text().splitlines() if "PROJ" not in x] if p.exists() else []


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--dist", type=Path, default=None); ap.add_argument("--tests", default="")
    a = ap.parse_args()
    import pandas as pd
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    pick = lambda ks: {k: dict(value=reg.at[k, "value"], unit=reg.at[k, "unit"], tier=reg.at[k, "tier"], status=reg.at[k, "status"]) for k in ks if k in reg.index}
    review = jl(R / "s4m1/review/S4K2_REVIEW.json"); smoke = jl(R / "s4m2/analysis/S4M2_SMOKE_SUMMARY.json"); impact = jl(R / "s4m1/BIOMASS98_IMPACT_S4L5.json"); cmp6 = jl(R / "s4m1/DUST_IMPACT_S4L1.json")
    man = jl((a.dist / "PACKAGE_MANIFEST.json") if a.dist else D / "evidence/s4m_3/PACKAGE_MANIFEST.json"); dcm = jl((a.dist / "DATA_CONFIG_MANIFEST.json") if a.dist else D / "evidence/s4m_3/DATA_CONFIG_MANIFEST.json")
    receipts = {}
    for sc, nm in (("integrated", "integrated"), ("disconnected", "disconnected"), ("integrated_nze", "integrated"), ("disconnected_gap", "disconnected_gap_diagnostic")):
        r = jl(R / f"s4m1/builds/{sc}/{nm}_BUILD_RECEIPT.json"); d = r.get("dust_cleanup") or {}
        receipts[sc] = dict(status=r.get("status"), code_sha=r.get("code_sha"), research_config_sha256=r.get("research_config_sha256"), network=(r.get("network") or {}).get("sha256"),
                            daily=(r.get("daily_network") or {}).get("sha256"), components={k: v for k, v in (r.get("network") or {}).get("components", {}).items()},
                            dust=dict(mode=d.get("mode"), removed=(d.get("removed") or {}).get("count"), merged=d.get("merged_links_removed"), pool_balance_after=d.get("pool_balance_after")),
                            overrides=((r.get("inputs") or {}).get("config_overrides")))
    ev = dict(
        instruction=dict(file="work/p1_step4m_20261019/S4M_CLAUDE_CODE_INSTRUCTION.md", sha256="e791015e2135845746e0ef47a50e15fae1d45d0cc586c723cc5c8197cc4c567c", verified=True),
        git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="4b4eb92cfe99dfd7717a7ef1f3c1c7e2b4712ad6 (S4L head, PR #37)", log=git("log", "--oneline", "4b4eb92c..HEAD").splitlines()),
        stops=[x for x in lines(R / "s4m2/STATUS.txt") if x.startswith(("STOP_", "KILLED_"))], downloads=[], cloud=False,
        s4m0=pick([x for x in reg.index if x.startswith("s4m_")]),
        s4m1=dict(builds=lines(R / "s4m1/STATUS.txt"), receipts=receipts,
                  audit_diff_vs_s4k2=dict(rows=review.get("audit_diff_rows"), by_section=review.get("audit_diff_by_section")), components_vs_s4k2=review.get("components_vs_s4k2") or review.get("components_vs_s4j"),
                  proxy=review.get("proxy"), model_check=review.get("model_check"), cross_border_components=review.get("cross_border_components"), integrated_vs_nze_static=review.get("integrated_vs_nze_static"),
                  biomass_check={sc: dict(loads_changed=v.get("loads_changed"), pool_balance=v.get("pool_balance")) for sc, v in impact.items()},
                  compare_vs_s4l6={sc: {k: v.get(k) for k in ("components_s4k", "components_s4l", "differences")} for sc, v in cmp6.items()}),
        s4m2=dict(status=lines(R / "s4m2/STATUS.txt"), standard=smoke.get("standard"), runs=smoke.get("runs"), nze=smoke.get("nze"), combinations=smoke.get("combinations"), lp_size=smoke.get("lp_size"),
                  solid_biomass_shadow_prices=smoke.get("solid_biomass_shadow_prices"), price_differences=smoke.get("price_differences")),
        s4m3=dict(scripts={f: sha(D / "cloud_package" / f) for f in ("run_365x24h.sh", "preflight.sh", "speed_probe.sh", "make_package.sh")},
                  s4l_scripts={f: sha(ROOT / "research/06_scope_redesign/p1_step4l_20261019/cloud_package" / f) for f in ("run_365x24h.sh", "preflight.sh")},
                  package=dict(commit=man.get("commit"), upload_total_bytes=man.get("upload_total_bytes_excluding_this_manifest"), files=len(man.get("files", [])), main_settings=man.get("main_settings"),
                               run=man.get("run"), second_batch_sensitivities=man.get("second_batch_sensitivities_registered_not_packaged"), supersedes=man.get("supersedes"),
                               speed_probe=dcm.get("speed_probe"), network_builds={k: dict(network_2920_3h=v.get("network_2920_3h"), daily=(v.get("daily_network") or {}).get("sha256"), code_sha=v.get("code_sha")) for k, v in (dcm.get("network_builds") or {}).items()}),
                  package_status=lines(D / "evidence/s4m_3/PACKAGE_STATUS.txt"), script_tests=lines(D / "evidence/s4m_3/results/TEST_RESULTS.txt")[-1:], probe_tests=lines(D / "evidence/s4m_3/results/TEST_RESULTS_probe.txt")[-1:],
                  uploaded=False),
        s4m4=dict(resource_check=dict(wsl_memtotal_kb=11214484, wsl_memavailable_kb=10419128, wsl_swap_kb=4194304, nproc=16, wslconfig="memory=11GB swap=4GB", windows_physical_bytes=16890519552, disk_free_gb=dict(root=900, d=340)),
                  condition="MemTotal >= 24 GiB and MemAvailable >= 20 GiB and disk >= 20 GB", met=False, local_pilot_run=False, note="pilot deferred to the cloud under a separate authorisation; .wslconfig untouched"),
        resources=dict(cloud=False, formal_solves=False, downloads="none", local_solves="3 x 56x3h smoke (S4M-2, authorised) + 1 x 56x3h integrated re-run (supplement 01 S4M-S2, authorised), stop-loss 30 min each, serial; no pilot"),
        tests=a.tests)
    # supplement 01 (allocation-output completeness): checklist before / after, the authorised re-run, dual reconstruction cross-check, cost breakdown, disk estimate
    rr = R / "s4ms2/solves/s4m_A_integrated_rerun"; rec = jl(rr / "SOLVE_RECEIPT.json"); s2 = jl(R / "s4m2/solves/s4m_A_integrated/SOLVE_RECEIPT.json"); bd = jl(rr / "COMPONENT_COST_BREAKDOWN_SUMMARY.json")
    before = jl(R / "s4ms2/checklist/S4M_S1_CHECKLIST_before.json"); after = jl(R / "s4ms2/checklist/S4M_S1_CHECKLIST_after.json")
    ev["supplement_01"] = dict(
        instruction=dict(file="work/p1_step4m_20261019/S4M_SUPPLEMENT_01.md", sha256="8743abd0de60aa171b7cd1bf5672e682879b218a9218ee6876098134adba7d1e", verified=True),
        checklist_before={k: v.get("status") for k, v in (before.get("items") or {}).items()}, checklist_after={k: v.get("status") for k, v in (after.get("items") or {}).items()},
        checklist_after_detail={k: {kk: vv for kk, vv in v.items() if kk in ("status", "where", "note")} for k, v in (after.get("items") or {}).items()},
        rerun=dict(folder=str(rr.relative_to(ROOT)), termination=rec.get("termination_condition"), objective=rec.get("objective"), objective_s4m2=s2.get("objective"),
                   objective_rel_diff=(abs(float(rec["objective"]) - float(s2["objective"])) / abs(float(s2["objective"])) if (rec.get("objective") and s2.get("objective")) else None),
                   solve_seconds=rec.get("solve_seconds"), solve_seconds_s4m2=s2.get("solve_seconds"), gates={k: v for k, v in (rec.get("gates") or {}).items() if isinstance(v, bool)},
                   all_passed_solver_tolerances=jl(rr / "V5_GATES.json").get("all_passed_solver_tolerances"), all_passed_solver_tolerances_s4m2=jl(R / "s4m2/solves/s4m_A_integrated/V5_GATES.json").get("all_passed_solver_tolerances"),
                   status=lines(R / "s4ms2/STATUS.txt"), exports=rec.get("exports"), duals=rec.get("duals")),
        cost_breakdown={k: bd.get(k) for k in ("extendable", "matched", "matched_share", "by_rule", "composite_rules", "unmatched_by_carrier", "table_fixed_inconsistent", "offwind_distance_table", "tolerance")},
        disk_estimate=jl(D / "evidence/s4m_s2/EXPORT_DISK_ESTIMATE.json"),
        modified_files=dict(export_only=True, files=["scripts_project/s2_solve.py (assign_all_duals=True, s4m_duals.write_duals, --costs-table, EXPORTS.json)", "scripts_project/s4m_duals.py (new)", "scripts_project/s4m_cost_breakdown.py (new)",
                                                    "scripts_project/s4m_s1_check.py (new)", "tests/research/test_s4m_duals.py (new)", "tests/research/test_s4m_cost_breakdown.py (new)",
                                                    "cloud_package/run_365x24h.sh (--costs-table, export list)", "cloud_package/make_package.sh (costs tables per tag)"],
                            constraints_objective_network_changed=False, commits=["b15ea69c", "8aa2fea0", "f50c8850"]),
        pythonhashseed_finding="offline dual reconstruction needs PYTHONHASHSEED=0: the strongly-meshed bus order (pypsa get_strongly_meshed_buses -> value_counts) depends on the str hash seed; s4m_duals.py refuses other seeds and refuses to write when the cross-check is not exact")
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("supplement block added")
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("written", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
