"""S3B R4 (decision 69): registry fragment for the solver profiles, the scaling rules and the interior-point thresholds.

    python scripts_project/s3b_r4_solver_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256

SCRIPT = "scripts_project/s3b_r4_solver_data.py"
PE_CONFIG = SRC_DIR / "pypsa_eur_v2025.07.0_config.default.yaml"
PE = dict(threads=32, method=2, crossover=0, BarConvTol=1e-5, Seed=123, AggFill=0, PreDual=0, GURO_PAR_BARDENSETHRESH=200)   # lines 1056-1064
MAIN = dict(Method=2, Crossover=0, BarConvTol=1e-8, BarHomogeneous=1, Threads=8, Seed=123, AggFill=0, PreDual=0, GURO_PAR_BARDENSETHRESH=200)
REASONS = {
    "Threads": ("8 (PyPSA-Eur 32)", "local machine has 8 physical cores (16 logical); the cloud script sets 8 per scenario for parallel runs"),
    "BarConvTol": ("1e-8 (PyPSA-Eur 1e-5)", "crossover is off, so the barrier solution itself must carry the accuracy; 1e-8 is Gurobi's default BarConvTol and three orders below PyPSA-Eur"),
    "BarHomogeneous": ("1 (not set in gurobi-default; set in PyPSA-Eur gurobi-numeric-focus / gurobi-fallback, lines 1065-1083)", "homogeneous self-dual barrier separates true infeasibility from numerical trouble (S3-7: crossover INF_OR_UNBD although barrier optimal)"),
    "TimeLimit": ("1750 s (56x3h smoke) / 10800 s (365x24h cloud)", "stop-loss rule (working principle 6), not a numerical setting"),
}


def main():
    cfg_sha = sha256(PE_CONFIG)
    reg = Registry(SCRIPT)
    reg.add("solver_profile_basis", "Gurobi profile basis = PyPSA-Eur v2025.07.0 solving.solver_options.gurobi-default: " + ", ".join(f"{k} {v}" for k, v in PE.items()), "gurobi-default", "flag", "B",
            "PyPSA-Eur v2025.07.0 config.default.yaml", "lines 1056-1064 (solver options), 1034-1035 (solver name/options)", cfg_sha, decision_ref="69", status="REFERENCE_ONLY")
    reg.add("solver_profile_formal_barrier", "Main profile formal_barrier: " + ", ".join(f"{k} {v}" for k, v in MAIN.items()), "formal_barrier", "flag", "B", "configs/research/baseline.yaml research.solver.profiles", "S3B R4.1", cfg_sha, decision_ref="69")
    reg.add("solver_profile_crossover_diagnostic", "Diagnostic profile crossover_diagnostic: identical to formal_barrier except Crossover 1", "crossover_diagnostic", "flag", "B", "configs/research/baseline.yaml research.solver.profiles", "S3B R4.1", cfg_sha, decision_ref="69", status="SENSITIVITY")
    for k, (val, why) in REASONS.items():
        reg.add(f"solver_difference_{k}", f"{k}: {val}; reason: {why}", val.split(" ")[0], "as set", "B", "S3B instruction R4.1", "difference from PyPSA-Eur gurobi-default", cfg_sha, decision_ref="69", status="REFERENCE_ONLY")
    reg.add("scaling_objective_constants_out", "LP scaling (a): constant-only objective columns (PyPSA objective_constant, Research_existing_FOM_constant, Research_existing_cross_border_FOM_constant) removed from the LP with linopy remove_variables and added back to n.objective after the solve (total-cost definition unchanged)",
            "on", "flag", "B", "scripts_project/s3b_scaling.py remove_objective_constants", "S3B R4.2(a)", sha256(ROOT / "scripts_project/s3b_scaling.py"), decision_ref="69")
    reg.add("scaling_store_energy_units", "LP scaling (b): Store-e / Store-e_nom of biomass pools (MWh -> GWh), CO2 sequestration and capture buffers (t -> kt) column-scaled by 1000 and their rows (energy balance, e / e_nom bounds, CO2 storage caps) scaled by 1/1000; solution x1000, duals /1000, reduced costs /1000 after the solve, so all outputs stay in MWh / t",
            1000.0, "factor", "B", "scripts_project/s3b_scaling.py scale_store_energy / unscale_solution", "S3B R4.2(b)", sha256(ROOT / "scripts_project/s3b_scaling.py"), decision_ref="69")
    reg.add("scaling_kirchhoff_not_applied", "Kirchhoff-voltage-law row normalisation not implemented (decision 69: only (a) and (b))", "not_applied", "flag", "B", "S3B instruction R4.2", "R4.2", cfg_sha, decision_ref="69", status="REFERENCE_ONLY")
    reg.add("interior_a1a2_gap_threshold", "A1/A2 interior criterion: relative primal-dual gap and complementarity_l1 / objective scale <= 10 x BarConvTol = 1e-7 (factor 10 covers presolve/postsolve and unscaling)", 1e-7, "relative", "B",
            "S3B instruction R4.4; Gurobi barrier termination (BarConvTol)", "v5_gates.gate_a1_a2_interior", sha256(ROOT / "scripts_project/v5/v5_gates.py"), decision_ref="69")
    reg.add("interior_a1a2_primal_threshold", "A1/A2 interior criterion: each row/column residual <= 1e-3 + 1e-7 x reference (the V4 physical budget; 1e-7 = 10 x BarConvTol)", 1e-7, "relative", "B", "V5 contract (V4 budgets)", "kkt_algebra.budget_arrays", sha256(ROOT / "scripts_project/v5/kkt_algebra.py"), decision_ref="69")
    reg.add("interior_a1a2_dual_threshold", "A1/A2 interior criterion: normalized stationarity and dual-sign error <= 100 x BarConvTol = 1e-6 (= V4 KKT budget and Gurobi default OptimalityTol)", 1e-6, "relative", "B", "V5 contract; Gurobi OptimalityTol default", "v5_gates.gate_a1_a2_interior", sha256(ROOT / "scripts_project/v5/v5_gates.py"), decision_ref="69")
    reg.add("interior_cleanup_threshold_rule", "Reporting cleanup: values with |x| < tau_g are reported as 0, tau_g = 10 x BarConvTol x max|x_g| per variable group (component x attribute), floor 1e-6 native units; derivation: barrier termination bounds the relative complementarity by BarConvTol, so bound-noise scales with the group magnitude; factor 10 for postsolve/unscaling",
            "10 x BarConvTol x max|x_g|", "rule", "B", "scripts_project/s3b_interior.py", "S3B R4.4", sha256(ROOT / "scripts_project/s3b_interior.py"), decision_ref="69")
    reg.add("interior_solution_degeneracy_note", "Interior (barrier, no crossover) solutions may split degenerate equal-cost alternatives across several options; read capacities/flows with this in mind", "note", "note", "B", "S3B instruction R4.4", "S3B_REPORT.md", cfg_sha, decision_ref="69", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "solver_r4.csv")
    print("fragment written")


if __name__ == "__main__":
    main()
