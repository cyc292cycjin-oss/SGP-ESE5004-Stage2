# Gate5 precision handoff engineering fix

The original failed run and its LP remain immutable. The portable certificate reproduced 1,825 equalities and two nonnegative terminal-stock bounds with a positive 0.00011560 MWh serialized RHS.

Frozen Python 3.11.13, PyPSA 0.30.3, Linopy 0.5.5 and HiGHS 1.11.0 remain in use. Model.solve(io_api="direct") dispatches the existing model; PyPSA.solve_model does not rebuild it. The native direct exporter is available, but materializes a whole long-form matrix, sparse conversion and millions of string names. The project adapter streams the same Constraint.flat canonical blocks, verifies every received HiGHS row and column exactly, and passes original integer label vectors to the frozen Highs._solve result mapper. It does not use an LP/MPS input file.

All coefficients, row bounds, variable bounds and objective coefficients/offset are checked without decimal rounding. Duplicate terms use frozen Linopy coalescing semantics. Row reorder is explicitly mapped. Small synthetic matrices are independently compared to Model.matrices and native to_highspy. The actual run must produce SOLVER_TRANSFER_FIDELITY.json PASS before h.run.

Synthetic testing also exposed a pre-existing result-assignment bug: PyPSA interprets the custom scalar Research-existing-FOM-constant as a component variable. A scoped project wrapper aliases its dictionary iteration key only during post-solve annotation so the frozen mapper skips it. Its primal, integer label, objective coefficient and all constraints remain in the same model; the original name is restored in finally. No package source is modified.

The first synthetic harness had a backend subclass enumeration error before direct solve; the second reached optimal but exposed the scalar mapper failure. Both attempts are preserved. The third suite passed A-F with four synthetic solves. Actual executed synthetic solves this round: 1 + 4 + 4 = 9; the first receipt counted a pre-dispatch attempt as a solve and is superseded by this audited count. No research model had been rerun when this engineering commit was created.

The retry reads the existing SHA-pinned 365-snapshot network. It does not regenerate demand or parameters. Full matrix fidelity, all fixed-resource accounting, native lv_limit, 1,003 hook groups, known FOM once, frozen versions and memory guard are prerequisites. One real solver dispatch is allowed; no automatic retry or downstream scientific execution.
