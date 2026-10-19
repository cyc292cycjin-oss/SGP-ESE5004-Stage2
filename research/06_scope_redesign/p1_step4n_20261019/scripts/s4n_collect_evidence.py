"""S4N: collect the light evidence of the report into S4N_EVIDENCE.json (reads the work folder only; no host / port / licence content)."""
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parent.parent
L = W / "cloud_results" / "20261019T072454Z_5125" / "unpacked" / "s4n_pilot_light_20261019T072454Z_5125"


def jl(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


s1 = jl(W / "evidence/s4n_1/S4N1_CHECK.json") or {}
b1 = jl(W / "evidence/s4n_b1/SPEED_PROBE.json") or {}
env = jl(W / "evidence/s4n_2/ENV_COMPARE.json") or {}
src = jl(W / "evidence/s4n_2/PROBE_NETWORK_SOURCE.json") or {}
pr = jl(W / "evidence/s4n_3/SPEED_PROBE.json") or {}
pc = jl(L / "S4N4_PILOT_CHECK.json") or {}
pp = jl(L / "PILOT_PRECISION.json") or {}
va = jl(L / "VIOLATIONS_integrated.json") or {}
c2 = jl(W / "evidence/s4n_c2/C2_CALIBRATION.json") or {}
for d in (b1, pr):
    d.pop("reference", None)
ev = dict(
    step="S4N", date="2026-10-19",
    instruction=dict(file="S4N_CLAUDE_CODE_INSTRUCTION.md", sha256=sha(W / "S4N_CLAUDE_CODE_INSTRUCTION.md")),
    supplements=[dict(file=f, sha256=sha(W / f)) for f in ("S4N_SUPPLEMENT_01.md", "S4N_SUPPLEMENT_02.md")],
    package=dict(commit="f50c8850a556bdf3b0504d0367325a5f5fb551aa", files=22, bytes=260720379, instance_sha256sums="22/22 OK (after one rsync --checksum re-send)"),
    s4n1=dict(criteria=s1.get("criteria"), accepted=s1.get("accepted"), objective=s1.get("objective_compare"), duals=(s1.get("receipt") or {}).get("duals"),
              bus_cross_check={k: {kk: v.get(kk) for kk in ("buses_compared", "max_rel_scaled", "max_rel_pure")} for k, v in (s1.get("bus_dual_cross_check") or {}).items()},
              offline=dict((k, (s1.get("offline_comparison") or {}).get(k)) for k in ("same_structure", "constraints_this", "identical_constraints", "max_abs", "max_rel_pure"))),
    supplement01_b1_local_probe=b1,
    instance=dict(region="AutoDL 西北 B 区 D58 机（L23 克隆）", cpu="Intel Xeon Platinum 8470Q", cgroup_cores=25, cgroup_memory_gib=120, data_disk_gb=50,
                  container_start_sgt="2026-10-19 14:12:53", done_sgt="2026-10-19 18:44:33", licence_deleted_sgt="2026-10-19 18:56:27", hours_to_done=4.53, cost="DATA_PENDING"),
    env_compare=dict(key_all_equal=env.get("key_all_equal"), packages=[env.get("local_packages"), env.get("instance_packages")], version_differences=len(env.get("version_differences") or {})),
    probe_network_source=src, speed_probe=pr,
    pilot=dict(run="runs/20261019T072454Z_5125", termination=(pc.get("receipt") or {}).get("termination_condition"), objective=(pc.get("receipt") or {}).get("objective"),
               objective_lp=(pc.get("receipt") or {}).get("objective_lp"), gurobi=(pc.get("receipt") or {}).get("gurobi_lines"), solve_seconds=(pc.get("receipt") or {}).get("solve_seconds"),
               peak_rss_gib=((pc.get("receipt") or {}).get("peak_rss_bytes") or 0) / 2**30, lp=(pc.get("receipt") or {}).get("lp"),
               gates=dict((k, (pc.get("gates") or {}).get(k)) for k in ("all_passed", "all_passed_solver_tolerances", "all_passed_barconvtol", "failed")),
               restart=(pp.get("a_total_cost") or {}).get("restart"), best_before_first_stall=(pp.get("a_total_cost") or {}).get("best_before_first_stall"),
               returned_iteration_by_log=(pp.get("a_total_cost") or {}).get("returned_iteration_by_log"), last_iteration=(pp.get("a_total_cost") or {}).get("last_iteration"),
               full_bundle=dict(path="/root/autodl-tmp/s4m_cloud/runs/20261019T072454Z_5125/results_20261019T072454Z_5125.tar.gz", bytes=158873778,
                                sha256="cb4927da4490d412579dd3dce063884697601a9a8743a879567978965cd27480", location="instance data disk (not downloaded)"),
               light_bundle=dict(file="s4n_pilot_light_20261019T072454Z_5125.tar.gz", bytes=2083905, sha256="087d213276a2e795daa2c1934bb7fb0ff462b68157a2aa105c1b4d0e2c071a62", licence_scan="no hit")),
    pilot_in_run_duals=dict(duals=(pc.get("receipt") or {}).get("duals"), duals_file=pc.get("duals_file"), exports_all_match=pc.get("exports_all_match"),
                            bus_cross_check={k: {kk: v.get(kk) for kk in ("buses_compared", "snapshots", "max_rel_scaled", "max_rel_pure")} for k, v in (pc.get("bus_dual_cross_check") or {}).items()},
                            export_dir_bytes=pc.get("export_dir_bytes")),
    pilot_precision_c1=dict(grade=pp.get("grade"), a=dict((k, (pp.get("a_total_cost") or {}).get(k)) for k in ("returned_difference_bn", "returned_relative", "basis", "passed")),
                            b=dict((k, (pp.get("b_primal_violations") or {}).get(k)) for k in ("rows_over_budget", "row_violation_max", "row_max_ratio", "first_order_cost_eur_all_rows", "passed", "biomass_pools_BN_SG_VN")),
                            c=dict(b16=(pp.get("c_prices") or {}).get("b16"), totals_eur=(pp.get("c_prices") or {}).get("totals_eur"), passed=(pp.get("c_prices") or {}).get("passed"),
                                   country_check=(pp.get("c_prices") or {}).get("country_check"))),
    violations_l23_method=dict(totals=va.get("totals"), families={k: {kk: v.get(kk) for kk in ("rows_over_budget", "max_violation", "max_ratio_to_budget", "first_order_cost_eur", "countries_over_budget")}
                                                              for k, v in list((va.get("by_family") or {}).items())[:10]}),
    l23_integrated_reference=dict(termination="suboptimal", objective=516146310314.3289, barrier_iterations=144, barrier_seconds=6248.04, work_units=2359.68, rows_over_budget=11730,
                                  max_violation=14.8, max_ratio=902, first_order_cost_eur=187692, peak_rss_gib=15.26, wall_s=6722),
    calibration_c2=dict(branch="codex/s4n-calibration-20261019", commit="7c4f97fe986b9d4aa91b598ae774d05365fb1405", pushed=False,
                        profile=dict(threads=32, method=2, crossover=0, BarConvTol=1e-5, Seed=123, AggFill=0, PreDual=0, GURO_PAR_BARDENSETHRESH=200,
                                     source="research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml lines 1056-1064"),
                        accepted=c2.get("accepted"), all_optimal=c2.get("all_optimal"), objective_rel_diff=c2.get("objective_rel_diff"), b16_cal=c2.get("b16_cal"),
                        B6_bn_eur=c2.get("B6_bn_eur"), country_differences=c2.get("country_differences"),
                        runs={k: {kk: v.get(kk) for kk in ("termination", "objective", "barrier_iterations", "barrier_seconds", "solve_seconds", "B16_relative_error", "failed_gates_solver_tolerance_set")}
                              for k, v in (c2.get("runs") or {}).items()}),
)
(W / "S4N_EVIDENCE.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
print("written", (W / "S4N_EVIDENCE.json").stat().st_size, "bytes")
