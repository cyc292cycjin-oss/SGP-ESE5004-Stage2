# Phase4 final validation — STOPPED_RESOURCE_GUARD

Latest attempt: `gate5_20261006_04`. Native solver termination: `None`. Network writeback qualified: `False`. Dynamic checks: **NOT_RUN**. Gate6: **NOT_RUN_PREDECESSOR_FAILED**. Formal Integrated/Disconnected runs: **0**.

## Cloud triage is separate

User-confirmed main runs MkDocs 37457818388, CodeQL 37457818326 and Test 37457818293, plus the two subsequent Dependabot runs, carry explicit billing/spending-limit startup-block annotations. No steps executed. The exact financial subcause was not independently read. All three authorized workflows are disabled; no active runs needed cancellation. CodeQL pause is not a security pass. Main's web commit fba7e2fd is retained. Its remaining matrix.include macOS entry explains the still-generated macOS job separately from the billing block. See GITHUB_THREE_RUNS_TRIAGE.md and the full raw API receipts.

## Local validation

Run code SHA: `b8a6ad146b6931f5543f9ecdd2e1dc535bd522fa`. This is a new solve from frozen input, not continuation from iteration 73. Time limit=10800 s; wall guard=14400 s; threads=2; IPM with standard crossover; presolve and existing tolerances unchanged. Frozen Python3.11.13/PyPSA0.30.3/Linopy0.5.5/HiGHS1.11.0 remain unchanged.

The 12-case mock qualification suite passed with zero solver calls before launch. It covers native validity, placeholder/nonfinite arrays, invalid and valid FOM scalars, durable pre-writeback diagnostics, limited candidates and monitor stage progression. Run04 was interrupted before backend return: actual native flags and scalar assignment were NOT_CAPTURED_PROCESS_INTERRUPTED / NOT_REACHED. Its transfer receipt records pre-solve fidelity only. Mock values are not substituted for unavailable actual flags. Native feasibility would still require original-unit physical validation.

Input SHA256: `7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd`. The same 100 geographic nodes, 171 accounts, 1737 Loads, 187400.4 MW existing capacity, 365 snapshots/8760 hours, 2237 input series, 807 external pending fixed accounts and 200 null policy weights remain. Policy OFF is validation scope only. Source annual amounts and the predeclared MW/MWh acceptance bounds are unchanged. All1003 research hook groups and native lv_limit remain on the same model; known FOM is installed once.

Run04 stopped after 4666.203 s, when available memory fell to 400.438 MiB, below the unchanged512 MiB guard. Peak RSS: 6937.0625 MiB. It reached108 IPM iterations (including starred106–108), imprecise crossover and HiGHS's automatic simplex cleanup; the final log line begins original-LP postsolve recovery. There is no final native model status or accepted primal. This is STOPPED_RESOURCE_GUARD, not a time-limit or proved physical-infeasibility conclusion. The transformed model is identical to run03 in the full comparison receipt. No fifth attempt was launched.

Dynamic check counts: `{'NOT_RUN': 1}`. Objective and result_network remain null. Iteration/cleanup objectives are not system costs. Unknown fixed prices/emissions remain null; complete system cost/emissions are not claimed. See GATE5_RESOURCE_STOP_DIAGNOSTIC.md for verified memory facts and limits of attribution. Future resource readiness requires a reviewed memory plan for postsolve; simply raising the time limit is insufficient evidence of readiness.

Historical run03 remains FAILED_TIME_LIMIT: 73 IPM iterations,3600.47s,crossover not run,no accepted primal,objective/result_network null,dynamic checks NOT_RUN. Its raw FOM-mapping exception and the first two infeasible runs are preserved. The exact block120 binary64 contradiction remains mathematically true; reversible scaling does not erase it. Full transfer fidelity is not primal feasibility.

This round executed 1 real Gate5 attempt and zero local/synthetic optimization or presolve-only calls. The mock suite invokes no solver. Cumulative real Gate5=4; historical local optimization=12; synthetic HiGHS=14; documented historical presolve-only=386. No automatic fifth real attempt is authorized.

Stop for human review. Formal policy configuration,200 pending attribution weights and formal experiment/report contracts remain separate scientific gates. No Gate4 source search, extra supply, load reduction, tolerance relaxation, removed constraints, or cloud model execution was used.
