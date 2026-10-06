# Phase4 final validation — stopped at Gate5

Gate4 remains CLOSED. Gate5 was executed once and HiGHS returned **infeasible** during presolve. Gate6 and formal Integrated/Disconnected experiments were not executed. No resource, demand, cost, policy, tolerance or physical constraint was changed to force feasibility.

## Verified starting identity

- Branch: `research/full-sc-baseline`. Starting local/remote HEAD: `51e028f7631c45092d3b3c5d0c466f00beb109bc`, clean.
- Gate5 execution code: `f75d8293c9b9896232cc0000736de8b1a20e730d`, clean at launch. Independent CI housekeeping was committed later.
- Gate4 input SHA256: `238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d` (unchanged).
- Derived24h input SHA256: `7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd`.
- Frozen Python3.11.13, PyPSA0.30.3, Linopy0.5.5. HiGHS1.11.0. Gurobi12.0.3 restricted license fails the size probe; no upgrade/install was made.
- WSL RAM7.62GiB; free disk approximately940GiB. Solver threads2, solver limit3600s, wall limit7200s. Actual wall time90.04s; peak sampled process memory5.635GiB. Neither limit caused the failure.

## Preserved inputs and installed constraints

100 geographical nodes,171 accounts,1737 Loads,745 source records and187400.4MW existing stock remain. Full2013 becomes365 daily snapshots with24h weights,8760h total. All2237time-varying input series retain annual integrals within documented floating-point tolerance. Static component tables were compared before aggregation and after NetCDF reload. No sector/carrier or cost was removed.

The actual model contains2,450,005variables and6,042,238constraint rows. All1003research constraint groups plus native `GlobalConstraint-lv_limit` were attached and checked on the same model passed to `solve_model`. Known existing FOM coefficient is8224491125.573893EUR2020/year and was attached once. This is attachment evidence, not a reconciled optimal objective.

## Verified sufficient conflict

`PH:2050:Buildings:ResidentialFuel:biomass@PH_Luzon5 0 :: final obligation` is supplied by its Charcoal and Fuelwood fixed inventories. Linopy0.5.5's LP writer formats coefficients/RHS with12significant decimal digits. In the actual saved LP:

- Annual required energy: **43981693.30891560MWh**.
- Initial inventory sum: **43981693.3088MWh**.
- Difference: **0.00011560MWh**.

Summing1825exact LP equations cancels intermediate flows and states, leaving `-E_Charcoal,end - E_Fuelwood,end = 0.00011560`. Both end stocks have verified nonnegative bounds in that same LP. This is an independent exact-decimal infeasibility certificate. In the unrounded network the same aggregate difference is approximately−7.45e−9MWh, ordinary floating-point arithmetic. It is not a scientific fuel shortfall or a new residual Load.

This certificate is sufficient but does not prove that every other block is feasible. A future narrowly scoped engineering correction should preserve binary coefficients via a compatible direct solver interface or a sufficiently precise serialization path, then validate preservation before an explicitly resumed Gate5 attempt. Do not add fuel, relax conservation, set arbitrary bounds, or change feasibility tolerances to hide the conflict. No such correction/re-solve was performed in this package because the user instructed stopping at a failed gate.

## Diagnostic limits

The full IIS API built an internal elastic diagnostic and exited without a certificate while WSL restarted. Resource exhaustion is inferred, not proven from recovered logs. It was not used as a relaxed scientific model. Subsequent native presolve and finite interval propagation made no optimizing run; the exact algebra certificate above was recovered without an IIS or relaxation solution. PyPSA also warned about undefined carrier labels and unused multiport `efficiency3`NaNs; these warnings are retained and are not claimed as the cause.

## What was not reached

There is no primal solution, solvedResearch network, dynamic-validation PASS, objective comparison, carbon-emissions total or interconnection benefit. Gate6 policy selection/reporting freeze, final intervention freeze, scenario configs/diff guard and formal runner were not advanced beyond this stop-gate. Existing uncertainty/sensitivity registers remain unchanged and inactive. `GATE5_DYNAMIC_CHECKS.csv` and `GATE6_FULL_DYNAMIC_CHECKS.csv` explicitly say NOT_RUN, never PASS.
