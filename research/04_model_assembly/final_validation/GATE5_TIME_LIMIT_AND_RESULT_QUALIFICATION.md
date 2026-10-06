# Gate5 run 03: termination and result qualification

The solver stopped at its 3,600-second limit after 73 IPM iterations. HiGHS reports 3,600.47 seconds including overhead. Presolve completed; crossover was requested but not run before termination. This attempt does not establish a new infeasibility certificate or an accepted feasible solution.

## Separate evidence layers

1. **Verified solver termination:** `Time limit reached`, from the preserved run 03 solver log.
2. **Verified mapping failure:** the immutable raw manifest records `FAILED_ENGINEERING` and `Unqualified custom scalar during result mapping: Research-existing-FOM-constant`.
3. **Unavailable evidence:** native `value_valid`, `info.valid`, primal/dual solution status and the rejected scalar's numeric value were not captured in run 03. No specific values are reconstructed or asserted.
4. **Current status view:** `FAILED_TIME_LIMIT`, with the original engineering error retained separately. The raw manifest and log are unchanged and hashed in `GATE5_TERMINATION_CLASSIFICATION.json`.

The frozen Linopy 0.5.5 interface treats a time-limit termination as status `ok`. Array length alone does not certify native feasibility. The run's `solution_map_verified` and `dual_map_verified` flags certify reversible arithmetic on returned arrays; they do not certify those arrays as a primal solution or economically interpretable dual solution.

`objective=null`, `result_network=null`, and `dynamic_checks=NOT_RUN` remain mandatory for this run. The terminal log's 0.0 and the IPM iteration objectives are not system-cost results. No FOM constant was forced to one to bypass the mapping rejection.

## Bounded post-run engineering correction

The project adapter now requires native `value_valid`, valid HiGHS info, `primal_solution_status=Feasible`, a nonempty returned primal and finite values before PyPSA assignment. Otherwise it preserves the termination condition, marks warning, and removes unqualified arrays from the result object. Native qualification remains only a necessary condition: independent original-unit dynamics must still pass.

A qualified but nonoptimal limited candidate proceeds to dynamic checks; it cannot make Gate5 PASS. A native optimal/feasible result follows the original checks. The native qualification receipt is written before assignment, so any later mapping exception retains the solver-side evidence. The strict custom FOM scalar guard is unchanged.

Mocked-interface tests cover invalid placeholder arrays, an infeasible candidate, a feasible limited candidate, an optimal candidate, the runner's candidate route, and a monitoring-stage latch. They make **zero solver calls**. This correction was made after run 03 and does not claim retroactive validation or authorize another real retry.

The monitor previously classified each rolling log tail independently. Once the IPX header scrolled out it could label later iterations as presolve. The current derived resource summary maintains the one-way transition to solve; the raw timestamps and memory measurements are unchanged. The future monitor uses the same latch.

## Handoff

All source hashes, the two prior failures, exact local certificates, transfer receipt and run 03 logs are preserved. No full-model IIS was launched. There is no accepted primal for the previously unexercised production post-solve checker; its real-network validation remains unverified. Local/synthetic checks do not substitute for it.

Stop for human review. A further real solve or changed numerical budget needs a new instruction. Gate6 is `NOT_RUN_PREDECESSOR_FAILED`; formal Phase5 remains unrun and independently requires scientific policy decisions.
