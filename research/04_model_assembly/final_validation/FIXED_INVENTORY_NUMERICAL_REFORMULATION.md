# Fixed-inventory numerical reformulation

This is a Gate5 engineering validation, not a scientific scenario. No source quantity, price, capacity, physical boundary, policy choice or frozen NetCDF is changed.

## Evidence and source identity

The independent saved verifier reproduces both distinct findings: block 120 is exactly infeasible when the original binary64 values are interpreted as exact rationals; block 320 has a feasible rational witness satisfying all saved rows and variable bounds. Scaling does not turn block 120 into an exactly feasible mathematical model.

All 385 fixed groups / 807 stocks were recomputed from the frozen allocation arrays and original commodity rows. Native 2920-point annual integration, commodity composition allocation, and 365 daily means reproduce each stored value exactly. Their different floating-point evaluation paths yield 180 positive and 205 negative exact annual differences; maximum relative difference is 5.727233442941027e-16. These are source-identity roundoff discrepancies, not new fuel shortages.

## Selected representation

For each qualified isolated group choose S as the smallest power of two not below its annual energy magnitude. For its Store-e, Store-p, meter Link-p and Link-p_nom variables set x = S z. For every row belonging wholly to that group multiply both sides by 1/S. Other variables and rows are unchanged. D and R denote these positive diagonal maps:

`A' = R A D; b' = R b; l' = D^-1 l; u' = D^-1 u; c' = D c`.

The streamed adapter verifies the inverse transformation exactly in binary64 and separately reads back every transformed coefficient/bound/objective from HiGHS. Original integer labels are retained. Primal mapping is x=D z; original row dual is R times solver dual; original reduced cost is solver reduced cost divided by D. A nonzero-objective synthetic test verifies x=3, objective=6 and original dual=2. No economic interpretation of validation duals is provided.

Isolation is requalified from actual network connections and every matrix row. Any cross-group or external constraint, time-varying economic control, alternative supply, diversion, carbon-credit port or nonzero economic coefficient revokes this representation. No equations, physical obligations, stores or timing degrees of freedom are eliminated. Different commodities retain their original dispatch freedom. This does not apply to batteries, hydrogen storage or hydro resources.

## Finite-precision acceptance

Exact infeasibility remains exact infeasibility after reversible scaling. Numerical acceptance is instead explicitly bounded finite-precision treatment of scientific quantities derived along equivalent source paths. It is not a claim that the original contradictory binary64 equations have an exact solution.

Before any local solve, the audit sets u=2^-53, gamma(n)=n*u/(1-n*u), n=(2*2920-1)+(4*K-2)+8+(2*365-1). Terms conservatively cover native weighting/summation, K commodity shares, daily averaging, and daily weighting/summation. B_E=gamma(n)*max(node annual quantity, sum of initial stocks, daily integrated requirement), and B_P=B_E/24. The same conservative bound covers the shorter state arithmetic chain. Maximum B_E is 0.00014709214189362183 MWh. Budgets are not fitted to solver outputs and cannot be expanded after a failed check.

After solving and inverse mapping, every fixed-group state equation, stock bound, release direction, meter flow/efficiency/capacity, final obligation, annual release and terminal inventory is independently checked in original MW/MWh. The frozen solver feasibility tolerances and presolve setting remain unchanged. Synthetic 1 MWh and outside-budget shortages both return optimal under scaling but are rejected by this independent acceptance. Wrong efficiency, negative stock and extra supply are also rejected.

## Bounded alternatives and solver setting

Local A/B/C comparisons cover smallest/largest groups and both problem blocks. Cumulative state equations preserve the local algebra but increase nonzeros and do not resolve block 120's numerical rejection. Frozen HiGHS user_bound_scale is supported, but scales its visible LP bounds and is global; it is not selected. The project representation is scoped to the qualified fixed blocks.

An IPM-only probe of the largest group failed HiGHS postsolve/KKT acceptance. Standard crossover on the same scaled block passed, without changing feasibility tolerance or presolve. Production therefore uses IPM with standard crossover on, two threads and the existing 3600-second solver budget. No random perturbation or parameter lottery is used.

## Preconditions and stopping rule

Local comparison receipt: `results_project/validation/inventory_local_20261006_02/LOCAL_NUMERICAL_REGRESSION_RESULTS.json`.
Mapping/roundtrip receipt: `results_project/validation/inventory_mapping_20261006_01/MAPPING_REGRESSION_RESULTS.json`.
Earlier incomplete/failed probes remain in `inventory_local_20261006_01` with their original logs.

Only one real retry is authorized after these prerequisites. The full original research hooks, native lv_limit and fixed FOM must remain attached to the same model. A result requires original dynamic checks, strict fixed-block checks and export/readback, not just optimal status. No Gate6 or formal Phase5 run follows automatically.
