"""S4L-2 data (S4L instruction S4L-2; decision 113 (2)): registry fragment s4l_2 - the new solver profile formal_barrier_crossover (profile A with
the Gurobi parameter Crossover at its default -1), the diagnostic matrix and the comparison standard fixed BEFORE any run (S4L-2 point 4).

    python scripts_project/s4l_2_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4l_2_data.py"
INSTRUCTION_SHA = "03508400f675304cd0bdfd40ccbd0c61005644e7b2a122dffbe2048e6a5d529b"
SRC = "S4L instruction v1 2026-10-19 10:10 SGT, section S4L-2 (user decision 113 confirmed 2026-10-19 09:57 SGT; 8 local 56x3h runs authorised)"
LOC = "work/p1_step4l_20261019/S4L_CLAUDE_CODE_INSTRUCTION.md"
CFG = "configs/research/baseline.yaml"
PE = "research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml"
STANDARD = dict(reference="S4K network + profile A (formal_barrier), 56x3h, S4K-3 converged", objective_rel_tol=1e-5, b16_tol=1e-6,
                country_difference_tol="max(1 % of the country's disconnected - integrated difference in the reference, 0.01 bn EUR)")


def main():
    reg = Registry(SCRIPT)
    reg.add("s4l2_profile_formal_barrier_crossover", "S4L-2 point 1: new research.solver.profiles entry formal_barrier_crossover = profile A (Method 2, BarConvTol 1e-8, "
            "BarHomogeneous 1, Threads 8, Seed 123, AggFill 0, PreDual 0, GURO_PAR_BARDENSETHRESH 200; scaling and Kirchhoff row normalisation as in A) with the "
            "Gurobi parameter Crossover at its default value -1 (automatic: crossover to a basic solution after the barrier; profile A uses 0 = off; the older "
            "crossover_diagnostic profile uses 1 = dual push first). Added only; profile A unchanged. With Crossover != 0 s2_solve.py evaluates the basic-solution "
            "KKT gate (gate_a1_a2_kkt) instead of the interior criteria; the decision-71 solver-tolerance gates are evaluated as before",
            "Crossover=-1", "gurobi_parameter", "B", "Gurobi 12 parameter reference: Crossover (default -1, automatic); " + SRC, CFG, sha256(ROOT / CFG), decision_ref="113", status="REFERENCE_ONLY")
    reg.add("s4l2_diagnostic_matrix", "S4L-2 point 2: local 56x3h diagnostic matrix, 8 runs authorised: {S4K-3 network, S4L-1 cleaned network} x {formal_barrier, "
            "formal_barrier_crossover} x {integrated STEPS, disconnected STEPS}; serial (academic WLS: at most 2 sessions), 30 min stop-loss per run (TimeLimit 1,750 s, "
            "hard kill 1,800 s), no retry, no parameter change; label SMOKE_TEST_ONLY (56 snapshots, representative weights, decision 58)",
            "8_runs", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="113", status="REFERENCE_ONLY")
    reg.add("s4l2_comparison_standard", "S4L-2 point 4, fixed before any run (registered here before the matrix starts): reference = S4K network + profile A (S4K-3 "
            "converged); for every other combination, per scenario: |objective / reference objective - 1| <= 1e-5; B16 ledger identity relative error <= 1e-6; for "
            "every country the change of the 'disconnected - integrated' ledger difference against the reference <= max(1 % of that country's reference difference, "
            "0.01 bn EUR). Exceeding values are explained by their source (a real change from the cleanup, or a vertex choice along a degenerate direction), not "
            "re-run. Crossover failures (e.g. INF_OR_UNBD) or a crossover time above 5 x the barrier time are recorded as such, no tuning (point 5)",
            "obj_1e-5;B16_1e-6;country_max(1pct,0.01bn)", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="113", status="REFERENCE_ONLY")
    reg.add("s4l2_pypsa_eur_crossover_reference", "PyPSA-Eur v2025.07.0 gurobi-default solver options (config.default.yaml lines 1056-1064): method 2, crossover 0, "
            "BarConvTol 1e-6, Seed 123, AggFill 0, PreDual 0, GURO_PAR_BARDENSETHRESH 200 - PyPSA-Eur runs the barrier WITHOUT crossover by default; the "
            "gurobi-numeric-focus option set uses crossover 0 as well. formal_barrier_crossover is therefore a deviation for the verification purpose of S4L-2 "
            "(a basic solution with converged duals for the price-settled ledger), not a PyPSA-Eur default", "crossover_0_in_pypsa_eur", "flag", "B",
            "PyPSA-Eur v2025.07.0 config.default.yaml, solving.solver_options.gurobi-default (lines 1056-1064)", PE, sha256(ROOT / PE), decision_ref="113", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4l_2.csv")
    print("registry fragment s4l_2 written: 4 rows")


if __name__ == "__main__":
    main()
