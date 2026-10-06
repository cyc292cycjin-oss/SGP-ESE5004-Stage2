# Gate5 precision handoff engineering fix

The original failed run and its LP remain immutable. The portable certificate reproduced 1,825 equalities and two nonnegative terminal-stock bounds with a positive 0.00011560 MWh serialized RHS.

Frozen Python 3.11.13, PyPSA 0.30.3, Linopy 0.5.5 and HiGHS 1.11.0 remain in use. Model.solve(io_api="direct") dispatches the existing model; PyPSA.solve_model does not rebuild it. The native direct exporter is available, but materializes a whole long-form matrix, sparse conversion and millions of string names. The project adapter streams the same Constraint.flat canonical blocks, verifies every received HiGHS row and column exactly, and passes original integer label vectors to the frozen Highs._solve result mapper. It does not use an LP/MPS input file.

All coefficients, row bounds, variable bounds and objective coefficients/offset are checked without decimal rounding. Duplicate terms use frozen Linopy coalescing semantics. Row reorder is explicitly mapped. Small synthetic matrices are independently compared to Model.matrices and native to_highspy. The actual run must produce SOLVER_TRANSFER_FIDELITY.json PASS before h.run.

Synthetic testing also exposed a pre-existing result-assignment bug: PyPSA interprets the custom scalar Research-existing-FOM-constant as a component variable. A scoped project wrapper aliases its dictionary iteration key only during post-solve annotation so the frozen mapper skips it. Its primal, integer label, objective coefficient and all constraints remain in the same model; the original name is restored in finally. No package source is modified.

The first synthetic harness had a backend subclass enumeration error before direct solve; the second reached optimal but exposed the scalar mapper failure. Both attempts are preserved. The third suite passed A-F with four synthetic solves. Actual executed synthetic solves this round: 1 + 4 + 4 = 9; the first receipt counted a pre-dispatch attempt as a solve and is superseded by this audited count. No research model had been rerun when this engineering commit was created.

The retry reads the existing SHA-pinned 365-snapshot network. It does not regenerate demand or parameters. Full matrix fidelity, all fixed-resource accounting, native lv_limit, 1,003 hook groups, known FOM once, frozen versions and memory guard are prerequisites. One real solver dispatch is allowed; no automatic retry or downstream scientific execution.

## Executed retry result

Run gate5_20261006_02, code 873d93cce481e900798377335ba472213c995613, passed full transfer fidelity and then returned FAILED_INFEASIBLE during presolve. No primal, objective or result network is available. The old failed run remains unchanged. Residual numerical evidence is recorded separately; the direct handoff does not claim global feasibility.

## Reproduction entry points

No-solver independent evidence check:
`python scripts_project/verify_precision_evidence.py --evidence research/04_model_assembly/final_validation/precision_handoff_evidence`

Original no-solver LP certificate:
`python scripts_project/verify_gate5_infeasibility.py --evidence research/04_model_assembly/final_validation --lp results_project/validation/gate5_20261006_01/gate5_problem.lp`

Authorized synthetic-only regression command (choose a new output folder to preserve earlier attempts):
`python scripts_project/test_precision_handoff.py results_project/validation/precision_synthetic_review`

The real retry used `python scripts_project/run_gate5_precision_retry.py --output results_project/validation/gate5_20261006_02`. Do not execute it again without a new authorization and new run_id. It reads the accepted daily input; it never regenerates demand or starts Gate6/Phase5. The historical run_gate5_validation.py is retained for reproduction of the first failure, not the current numerical handoff.

The project adapter is intentionally scoped to the frozen continuous LP. Unqualified model types or optional warm-start/explicit-name paths are rejected. Native Model.solve can allocate temporary filenames but the direct backend does not write/read them; no LP/MPS file is handed to HiGHS.
