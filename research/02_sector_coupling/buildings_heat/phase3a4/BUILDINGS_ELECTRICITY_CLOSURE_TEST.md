# Buildings electricity closure checks

Material Passport: academic-research-suite; inline engineering/accounting audit; Phase 3A-4 v1; 2026-10-01. VERIFIED applies only to stated code/test/hash observations; accounting methods are ANALYZED/proposed and scientific inputs remain PENDING.

## Observed results

| Evidence | Result | Meaning |
|---|---|---|
| E1/E2/E4 combined | 1,062/1,062 PASS | Bounded source-function regressions on synthetic fixtures |
| Accounting contract | 18/18 PASS | Valid identity accepted; deliberate duplication/loss/missing inputs rejected |
| Integrated current E3 | KNOWN_E3_BLOCKER_REPRODUCED | Current total-growth function still omits Services |
| Actual ASEAN country/year/snapshot closure | NOT ESTABLISHED | No accepted base↔historical-electric-heat↔useful-service data bridge |

The [E3 specification](BUILDINGS_E3_ACCOUNTING_SPEC.md) was written before accounting tests; no E3 patch was created. [Contract results](evidence/ACCOUNTING_CONTRACT_TESTS.json) and `check_accounting_contract.py` are a research-side mathematical contract, not an alternative hidden model implementation.

The independent reference totals in the synthetic fixture detect: second subtraction of historical electric heat; second addition of Services; cooling deletion; electric cooking deletion; preloaded endogenous HP input; missing historical heat; negative residual; nonfinite input; annual equality hiding snapshot imbalance; lost cooking fuel; unknown fuel share treated as zero; missing efficiency/end-use share; HHV/LHV mismatch. A separate energy conversion example allows historical electric COP>1. All numerical fixtures are labelled synthetic; no field is exported to scientific input tables.

## Current E3 counterexample

[Integrated diagnostic](evidence/INTEGRATED_E3_DIAGNOSTIC.json) uses two synthetic electric Loads: original AC=20 TWh, S=3 TWh, and a test national target=1 TWh. The actual `include_electricity_growth` function makes AC=1 and leaves S=3, totaling4. This reproduces the selector/accounting flaw; it is **not** an estimate of ASEAN overstatement and the artificial quantities are not a valid scientific scenario. The function is unchanged by E1/E2/E4.

Adding Services to the calibration set could make a gross target match while corrupting independently accepted direct components and retaining historical electric heating. Uncommenting `electric_heat_supply` would use future fuel-shift/default quantities, not identified historical heating. Neither action is an acceptable E3 fix.

## Required future real-data acceptance tests (not run here)

1. Freeze the source-year/meter bridge A→A*, country/region mappings and physical snapshot weights. Test complete source lineage; reject missing values before upstream annual fillna.
2. For each country and R/S, verify identified historical D/E exactly covers the represented H/I service. Allocate and subtract once; preserve direct cooling and electric cooking, and preserve non-electric cooking by fuel.
3. Check pointwise and weighted annual `O+B+C+D+E=A*`, finite/nonnegative residuals, unique account ownership and no duplicate parent/subaccount Loads. Retain unclassified fuel rather than silently mapping it to heat.
4. Check H/I useful-service integrals after spatial/temporal aggregation, including water without HDD, true space-heating geography, timezone/weekend/year handling and zero/invalid profile failure. Do not call annual conservation “validated hourly demand”.
5. Check after **every subsequent workflow transformation**, especially distribution-loss adjustments, total-growth scaling and industry redistribution. Ensure no accepted account is rescaled implicitly; require the intended contract in the test oracle.
6. Once separately authorized, solved dispatch tests must check electricity, heat, CHP co-products and storage bus balances with actual Link directions; J/K/conversion input never belongs in fixed exogenous direct Load. No solve occurred in this phase.

The synthetic tests do not prove actual cooling totals or cooking totals are complete. They prove the proposed contract would reject stated losses/duplicates when valid partition data are supplied. Current full-sector code still has E3 and legacy fuel-shift issues.
