# Phase4 final validation — Gate5 still failed

The precision-preserving handoff is implemented and verified. The single new real attempt `gate5_20261006_02` is **FAILED_INFEASIBLE**. Objective and result network are null; dynamic checks are NOT_RUN. The first failed attempt is retained unchanged. Gate6 is NOT_RUN_PREDECESSOR_FAILED; formal Phase5 runs remain zero.

## Preserved inputs and changes

The original Gate4 network, 365-snapshot Gate5 input and old failed LP retain their exact supplied SHA256 values. All 100 geographical nodes, 171 demand accounts, 1,737 Loads, 187,400.4 MW accepted stock, 2,237 input time series and their annual quantities remain untouched. 807 external pending fixed accounts stay null-qualified, policy stays OFF, and 200 policy weights stay null. Native lv_limit and all 1,003 research constraint groups are present; the known FOM coefficient is installed once.

Project engineering changes stream the existing Linopy model into HiGHS without text serialization and verify all received matrix data. The frozen backend and PyPSA network mapping remain in use, with a scoped compatibility fix for the custom FOM scalar. No package/environment replacement or scientific-input modification occurred.

## Verified execution

- Full transfer: 2,450,005 variables, 6,042,238 constraints, 11,403,496 nonzeros; zero numerical transfer differences.
- Certificate rows plus stock bounds: 1,827 matched. All 385 fixed-resource groups / 807 stores screened.
- The old PH positive LP deficit is absent in the faithful matrix.
- New run wall time approximately 60.47 s; HiGHS presolve 3.94 s; process peak RSS 4.637 GiB. The 512 MiB available-memory guard was not reached. IPM iterations did not begin.
- Synthetic A-F passed. Nine actual synthetic HiGHS solves this round (ten cumulative) plus one historical Gurobi license-rejected dispatch. Real Gate5 attempts: two cumulative, one this round. Gate6/formal runs: zero.

## Remaining diagnosis and gate

Two exact-input local blocks reproduce presolve rejection. Indonesia road Biodiesel has a 4.602e-9 MWh exact binary64 stock contradiction. Vietnam industry has a fully verified rational feasible witness despite presolve rejection. These are numerical evidence, not newly inferred physical fuel shortages. See RESIDUAL_NUMERICAL_DIAGNOSIS.md for scope and proof files. No whole-model IIS or second real retry was run.

No real primal solution exists, so bus/state/annual-release/objective/carbon post-solve checks did not execute. The synthetic annotation fix is verified, but the research post-solve checker still requires real successful data. No system-cost or interconnection-benefit result is reported.

OSM documentation now matches actual 1/2-second backoff. Live Ubuntu/macOS GitHub CI was not verified and is not asserted green. Carrier-label warnings, unused efficiency3 NaNs and PROJ warning are separately inventoried; they are not assigned as the infeasibility cause without evidence.

Stop here for review. First resolve the remaining fixed-chain numerical behavior with local equivalence proofs; then seek authorization for another real validation attempt. Formal policy activation and its pending attribution remain independent scientific gates.
