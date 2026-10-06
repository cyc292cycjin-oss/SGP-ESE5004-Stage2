# Phase4 final validation — FAILED_TIME_LIMIT

One new real run, `gate5_20261006_03`, ended as **FAILED_TIME_LIMIT**. Solver termination: `time_limit`. Dynamic checks: **NOT_RUN**. Gate6: **NOT_RUN_PREDECESSOR_FAILED**. Formal Phase5 runs: **0**. The first two failed attempts remain unchanged.

## What changed and what did not

Only the numerical representation of independently qualified fixed-inventory blocks changed. The original model is mapped with exact power-of-two diagonal variable/row scales. No stock, demand, efficiency, cost, resource, policy, source table or input NetCDF was modified; no physical chain or timing freedom was eliminated. Original-unit acceptance is separate from the solver's scaled tolerance.

The frozen daily input SHA256 remains `7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd`. Its 100 geographical nodes, 171 demand accounts, 1,737 Loads, 187,400.4 MW stock, 365 snapshots / 8,760 hours, 2,237 input series, 807 externally pending fixed accounts and 200 null policy weights are preserved. Policy remains OFF for validation only. Known fixed FOM is installed once. All 1,003 research hook groups and native lv_limit remain on the same model.

## Verified numerical evidence

- The saved exact certificates remain valid: block 120 has a 4.6020431909710169e-9 MWh exact binary64 contradiction; block 320 has a rational feasible witness. Reversible scaling does not erase the former mathematical fact.
- Source reconstruction covers all 385 groups / 807 stocks: 180 positive and 205 negative annual differences, maximum relative difference 5.727233442941027e-16.
- Before solving, an operation-chain bound fixed the original-unit acceptance thresholds. Maximum energy threshold is 0.00014709214189362183 MWh. No threshold was fitted or expanded after observing results.
- Local A/B/C comparison and mapping regression pass for the selected representation. Real 1 MWh and outside-roundoff shortages were rejected in original units despite optimal scaled solver status. Negative stock, wrong efficiency, extra supply and external-coupling changes were rejected.
- Full streamed float64 transfer checks every transformed row, bound, objective coefficient and label. Original-to-transformed inverse equality is independently verified. The transformed model retains 2,450,005 variables, 6,042,238 rows and 11,403,496 nonzeros. Counts are evidence, not the acceptance criterion.
- Standard crossover is enabled following a recorded largest-block IPM/KKT failure and passing crossover probe. Presolve and feasibility tolerances were not relaxed. No solver/environment upgrade or site-packages patch was made.

## This real run

Code SHA: `002f2a6dcbd4d57335653867e8f12a2b024c93ec`. Solver adapter: PROJECT_STREAMED_FLOAT64. Frozen Python 3.11.13, PyPSA 0.30.3, Linopy 0.5.5, HiGHS 1.11.0. Two threads, 3,600-second solver budget, 7,200-second wall guard, 512 MiB available-memory guard.

Process peak RSS: 5226.12 MiB. Stage-level memory is in STABLE_INVENTORY_RESOURCE_SUMMARY.json. This attempt progressed past presolve into the interior-point solver, completed 73 iterations, and reached its time limit at 3600.47 seconds. Requested crossover was not run before the limit. This is not a new physical infeasibility certificate.

Dynamic receipt rows: 0; failed rows: 0. No accepted feasible primal is available: objective=null, result_network=null, dynamic_checks=NOT_RUN. Zero executed checks is not a pass. Log objectives, including the final 0.0, are not usable system costs.

The immutable raw manifest records FAILED_ENGINEERING because subsequent PyPSA assignment rejected `Research-existing-FOM-constant`. The current view separately records the solver time limit and this mapping error. Native validity flags and the rejected scalar value were not captured in run 03; they are not inferred. The transfer receipt proves matrix fidelity and reversible arithmetic on returned arrays, not feasibility of those arrays. A bounded post-run fix now checks native HiGHS feasibility before permitting PyPSA assignment, preserves qualified limited candidates for dynamic validation, and retains the strict scalar check. Its mocked-interface tests use no solver and were not retroactively applied to run 03. See GATE5_TIME_LIMIT_AND_RESULT_QUALIFICATION.md.

The gate remains closed. See the latest run log/manifest and any bounded diagnostic evidence; no automatic second retry is permitted.

## Execution and current-state semantics

This round: 1 real Gate5 solve, 12 local optimization calls, 4 synthetic optimization calls, 0 presolve-only calls. Real Gate5 cumulative: 3. Synthetic HiGHS cumulative: 14. The historical 385 local presolve probes and one Gurobi license-rejected probe remain separate. Gate6=0; Integrated/Disconnected=0.

Current status is generated from GATE5_RUN_HISTORY.json, immutable manifests and GATE5_TERMINATION_CLASSIFICATION.json. Old FINAL_STATUS and summary views are retained under stable_inventory_evidence/previous_current_reports. The report-root gate5_solver.log is still the historical first LP log and is labelled by its sidecar; it is not presented as this run's log.

Stop for human review. Formal policy configuration and the 200 pending attribution weights remain independent scientific gates. Gate5 policy OFF is not authorization to call a future policy-OFF run a decarbonisation experiment. No Gate4 source search was reopened and no formal result is reported.
