# Bounded Gate5 run 04

User instruction: GitHub notification triage + bounded Gate5 continuation, 2026-10-06. Exactly one new real local validation attempt is authorized after existing local tests, new mock qualification checks, immutable input hash, hook and resource checks pass.

| Setting | Accepted value |
|---|---|
| Run ID | gate5_20261006_04 |
| Input | Same frozen 365-point input; SHA256 7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd |
| HiGHS time limit | 10800 seconds |
| Process wall guard | 14400 seconds |
| Threads | 2 |
| Method | IPM + standard crossover; original presolve/tolerances |
| Adapter | PROJECT_STREAMED_FLOAT64 |
| Fixed-block representation | Previously verified power-of-two reversible scaling |
| Original-unit limits | Existing source-operation bounds, unchanged |
| Policy | OFF for validation; 200 attribution weights remain null |
| Downstream | Gate6=0; formal Integrated/Disconnected=0 |

`scripts_project/run_gate5_bounded_once.sh` is the single WSL entry. It refuses an existing output directory or driver log and acquires a local launch lock. It contains no retry loop. The Python process monitors available RAM and stages every two seconds, retains the 512 MiB reserve guard, and enforces the wall limit. Before construction it also checks available memory against the observed run03 peak plus that reserve. No WSL memory setting is changed.

This is a fresh solve from unchanged input, not resumption from IPM iteration 73. Run03 remains FAILED_TIME_LIMIT with its separate FOM mapping exception preserved. The present qualification diagnostics were added after run03 and were not active in that run.

The run's native flags, model status, nonfinite counts and original FOM values are saved before PyPSA assignment. Invalid arrays are not passed to the network; the termination reason is retained. A qualified limited candidate must undergo original-unit dynamics and is at most VALIDATION_FEASIBLE_NOT_OPTIMAL. Only an optimal result passing all dynamic checks can pass Gate5. An optimal result failing dynamics remains a failure.

Logs: `results_project/validation/gate5_20261006_04_driver.log` and the run directory's `gate5_solver.log`, `RESOURCE_MONITOR.jsonl`, transfer/qualification receipts and manifest. This authorization file alone is not evidence that the process started; the run manifest's solver_runs and actual solver log establish execution.

The 12-case mock receipt GATE5_RESULT_QUALIFICATION_TESTS.json binds to the exact tested project code hashes and makes zero solver calls. Existing full matrix, block, shortage, scaling and export regressions are reused because their scientific inputs/representation are unchanged. No cloud runner or paid service is involved.
