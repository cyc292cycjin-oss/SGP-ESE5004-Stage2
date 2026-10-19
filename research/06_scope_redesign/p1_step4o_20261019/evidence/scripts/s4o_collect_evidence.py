"""S4O: light evidence JSON of the S4O report (read only; files of the step folder and the local S4O-3 results).

    python s4o_collect_evidence.py <repo root> <out json>
"""
import hashlib, json, sys
from pathlib import Path

R = Path(sys.argv[1]); out = Path(sys.argv[2])
D = R / "research/06_scope_redesign/p1_step4o_20261019"; E = D / "evidence"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jl(p):
    return json.loads(Path(p).read_text()) if Path(p).exists() else None


s3 = E / "s4o_3/s4o_integrated"; prec = jl(s3 / "PRECISION.json") or {}; info = jl(E / "s4o_3/S4O3_INTEGRATED_INFO.json") or {}
c2 = {t: (jl(E / f"s4o_3/s4n_c2_c1/{t}_PRECISION_regraded.json") or {}) for t in ("cal_integrated", "cal_disconnected", "cal_integrated_nze")}
res = dict(
    schema="s4o-evidence-v1", instruction=dict(file="S4O_CLAUDE_CODE_INSTRUCTION.md", sha256=sha(D / "S4O_CLAUDE_CODE_INSTRUCTION.md"), expected="b5f4d099f2afe2e4e4d93cd2dee94ce42857b3a26f62d2622657d78b068af6aa"),
    authorisation="S4O-1 .. S4O-5 local parts incl. 3 local 56x3h runs (S4O-3); S4O-6 cloud not authorised",
    s4o_1=dict(pr="https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/39", calibration_branch="codex/s4n-calibration-20261019", commits=["7c4f97fe", "f28772e6", "46135c52"],
               s4n_archive_files=170, registry_rows=["s4n_decision_118_s4m_open_items", "s4n_decision_119_precision_over_label", "s4o_decision_120_production_profile", "s4o_question_source_s4n"],
               s4o_branch="codex/s4o-production-20261019", s4o_branch_base="46135c52"),
    s4o_2=dict(commits=["d5b4eb96", "18f55488"], profile=dict(Threads=8, Method=2, Crossover=0, BarConvTol=1e-5, Seed=123, AggFill=0, PreDual=0, GURO_PAR_BARDENSETHRESH=200),
               default_profile="pypsa_eur_default", tests=dict(test_s4o_2=7, tests_research_passed=543), script_tests=dict(run_preflight="50/50", probe="9/9"),
               c1_equivalence_on_s4n1=dict(max_abs_country_diff_bn=0.0, grade_same=True, seconds=22, peak_rss_gib=1.7)),
    s4o_3=dict(runs_made=1, runs_not_started=["s4o_disconnected", "s4o_integrated_nze"], stop="S4O-3 point 4: decision-107 objective standard not passed (2.13e-5 > 1e-5); runner ended in the 5-min gap before the disconnected solve",
               integrated=dict(termination=prec.get("termination"), objective=prec.get("objective"), receipt_profile=prec.get("solver_profile"), parameters=prec.get("solver_parameters"),
                               barrier=dict(iterations=(info.get("s4o") or {}).get("iterations"), seconds=(info.get("s4o") or {}).get("barrier_seconds"), work_units=(info.get("s4o") or {}).get("work_units")),
                               solve_seconds=(info.get("s4o") or {}).get("solve_seconds"), peak_rss_gib=(info.get("s4o") or {}).get("peak_rss_gib"),
                               objective_rel_diff_vs_profile_A=(info.get("s4o") or {}).get("objective_rel_diff_vs_A"), b16=(info.get("s4o") or {}).get("b16"),
                               kkt_relative_gap=(info.get("s4o") or {}).get("kkt_relative_gap"), c1_grade=prec.get("grade"), c1_acceptance=prec.get("acceptance"),
                               c1_a=dict(diff_bn=(prec.get("a_total_cost") or {}).get("returned_difference_bn"), relative=(prec.get("a_total_cost") or {}).get("returned_relative")),
                               gates_information=prec.get("gates_information"), interior_solution=(jl(s3 / "INTERIOR_CHECKS.json") or {}).get("interior_solution")),
               standard_decision_107=dict(objective="not passed", b16="passed", country_differences="not evaluated (disconnected not run)"),
               info_s4n_c2_c1={t: dict(grade=(v.get("grade") or {}).get("grade"), a_relative=(v.get("a_total_cost") or {}).get("returned_relative"),
                                       a_diff_bn=(v.get("a_total_cost") or {}).get("returned_difference_bn")) for t, v in c2.items()},
               info_s4n_c2_integrated=dict(objective_rel_diff_vs_A=(info.get("s4n_c2") or {}).get("objective_rel_diff_vs_A"), iterations=(info.get("s4n_c2") or {}).get("iterations"),
                                           kkt_relative_gap=(info.get("s4n_c2") or {}).get("kkt_relative_gap"))),
    not_done_at_the_s4o3_stop=dict(s4o_4="not entered (stop condition); make_package.sh / package_checks.py / preflight in-place update written during the S4O-3 run, not run (syntax checked only)",
                                   s4o_5="not done (stop)", s4o_6="not authorised"),
    supplement_01=dict(
        file="S4O_SUPPLEMENT_01.md", sha256=sha(D / "S4O_SUPPLEMENT_01.md"), expected="f723c544946142ca5e896a56652f95e4fcb3eba586bed21d9cce5ce6e8c7a7a4", decision=121,
        s4o_2b=dict(commit="87e28e3b", default_profile="formal_barrier", registry_fragment="s4o_1", tests_research_passed=544, test_s4o_2=8, script_tests="59/59", probe_tests="9/9",
                    run_defaults=dict(runs="disconnected,integrated_nze", gurobi_time_limit_s=21600, wall_cap_s=22500, pilot_reference="PILOT_INTEGRATED / PILOT_PRECISION")),
        s4o_3b=jl(E / "s4o_3b/S4O3B_CHECK.json"),
        s4o_4=dict(commit="126110ff", networks_vs_f50c8850=jl(E / "s4o_4p/NETWORKS_VS_REFERENCE.json"),
                   delta={k: v for k, v in (jl(E / "s4o_4p/PACKAGE_DELTA.json") or {}).items() if k in ("changed", "added", "removed", "upload", "unchanged_bytes")},
                   build_input_changes=jl(E / "s4o_4p/BUILD_INPUT_CHANGES_integrated.json"), sha256sums_ok="26/26", preflight="OK (sha, networks, profile, c1, versions, tools)",
                   dry_run_solves=2, licence_scan="no hit (30 files)", script_tests_on_packaged_scripts="59/59, 9/9"),
        s4o_5=dict(file="CLOUD_RESOURCE_ESTIMATE.md section 23", rows_2920=72.06e6, memory_gib=dict(affine=106, proportional=121, superlinear_1_15=165), hours_per_run_8470Q="15-35 (9-70)",
                   cards=2, data_disk_gb=">=100", price="DATA_PENDING"),
        s4o_6="see s4o_6 below"),
    s4o_6=dict(
        supplement_02=dict(file="S4O_SUPPLEMENT_02.md", sha256=sha(D / "S4O_SUPPLEMENT_02.md") if (D / "S4O_SUPPLEMENT_02.md").exists() else None,
                           expected="1898d3f79798eff99ddddccda32c7f0bc57ec669c25dabcd4c4bfb1bdbcb7d97", mode="unattended, decision rules"),
        instance=dict(cpu="Intel Xeon Platinum 8481C", cgroup_cores=25, cgroup_memory_bytes=98784247808, data_disk="50 GB, empty (clone without data disk)",
                      host_port="not recorded (command line only)"),
        upload=dict(bytes=264363290, seconds=7192, sha256sums="26 OK", commit="126110ff"), licence=dict(uploaded="2026-10-20 00:10:26", deleted="2026-10-20 03:43:29", verified_absent=True),
        preflight="OK", probe=dict(r_work_units=0.8356, r_iterations=0.9082, objective_rel_diff=-2.5e-12, time_limit_s=21600, wall_cap_s=22500),
        batch=jl(E / "s4o_6/S4O6_BATCH_SUMMARY.json"),
        recovery=dict(full_batch=dict(bytes=461001705, sha256="c37f8d938176850d3cbd316907030e07eadb6a71eef0491d6f3f82e9fd47ccef"),
                      light=dict(bytes=5782612, sha256="f8cffc10d4ac503727c62625384820f56d331678397ce16f1b09743de264caca"),
                      per_run=dict(disconnected=150455004, disconnected_gap=151427801), pilot_full="not on this instance (original D58 data disk only)"),
        automatic_decisions="D1-D13 (S4O_PROGRESS.md, report section 11.8)",
        final_scan=dict(host_hits=0, port_standalone_hits=0, port_inside_longer_numbers_files=20, licence_string_hits=0)),
    files={str(p.relative_to(D)): sha(p) for p in sorted(E.rglob("*")) if p.is_file() and "__pycache__" not in p.parts},
)
out.write_text(json.dumps(res, indent=1, default=str))
print("evidence written:", out, len(res["files"]), "files")
