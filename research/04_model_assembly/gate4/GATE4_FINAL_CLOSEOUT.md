# Gate4 final closeout — Assembly V1

**Gate4 static assembly is closed. The first complete unsolved Research Full-SC network was exported and reloaded successfully. No solver, optimization variables, Integrated/Disconnected comparison or Gate5 execution occurred.**

## Actual delivered network

`research_fullsc_2050_assembly_v1_unsolved.nc` has 100 geographical nodes, 2920 snapshots from 2013 at 3h, and 8760 physical hours. It contains 171 accepted demand accounts bound once to 1737 Loads, 745 source records/187400.4 MW existing capacity, including 47952 MW hydro. All frozen electric physical inputs were preserved. 153 arrays were reused under exact source/value/method hashes; 18 were generated for newly accepted blend accounts. No previously accepted quantity or capacity was silently removed.

Network SHA256:`238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d`.
Executed build code SHA:`4b5611dc2dbc3ebcc2ae69b3782b338d2a18b6ce`.
Baseline registry SHA256:`2e5963b7e8a89cbd6369258ead0ce4e7d807f90d0a38b40013b91ed91fbfc518`.

## Boundary choices and source interpretation

Ten compatible memo uncertainties use Z=min(P, B), with fossil and biofuel heating values kept separate. Eighteen target accounts preserve their other unique source fuels. The separate upper input variant uses Z=0; it was not built or solved. PH rail remains constant 2019. Neither endpoint is a source-reported memo or probabilistic estimate.

The 279 required target-demand records end in 171 physical accepted, 89 source-scope, 15 UN unreported nonposting, and 4 frozen-deferred states. Unknown records were never converted to zero. Future endogenous carrier use and country-owned external supply remain available under the frozen boundary.

Inherited stock is SOURCE_QUALIFIED_SURVIVING_EXISTING_STOCK_ONLY. 410 inventory uncertainty rows remain separate and nonadditive across overlapping GEM/GPD populations. Five hydro groups/684 MW are not inherited; no inflow was fabricated. Avion stays outside 2050 under the approved 25-year proxy. These exclusions do not claim real-world retirement or absence.

## Actual static validation

All listed A–T gates passed on the complete actual network before export and after readback: endpoint references, finite active numerical inputs, aligned series and weights, source/account/node/time conservation, exactly-once ownership, buildings and transport boundaries, qualified stock capacity, unchanged hydro resources, country-isolated external markets and non-electric carriers, known physical carbon ports, policy OFF, revocable fixed accounts, EUR2020 priced inputs, FT VOM, 13 zero-variable-cost DC/B2B links, 340 accepted renewable configuration fees, constraint-hook identities, and baseline component roles.

Native PyPSA unbounded-capacity sentinels, unset optional controls and unused Link-port fields are individually listed in the manifest. They are not missing scientific input values. The checker still rejects NaN in an active coefficient or connected port and does not invent large finite capacity bounds. Reported physical input rows and materialised demand arrays are finite.

Actual local nonzero-capable coupling includes 500 links: electrolysis, H2 fuel cells, FT with H2/CO2/electricity inputs, and steam methane reforming with/without capture. FT output reaches accepted oil transport/bunker obligations. The electricity control set is frozen against this network: 192 DOMESTIC, 24 CROSS_BORDER, 0 UNKNOWN. It excludes non-electric carriers and was not switched. Structural paths do not prove capacity adequacy, multi-input feasibility or dispatch.

## Accounting and policy remain separately qualified

The complete network has 1748 known physical carbon events and 200 null SMR/SMR-CC policy weights. Policy remains OFF: no 100 Mt cap is installed. Enabling policy with pending weights explicitly fails; future H2 power shares are not guessed.

807 strict fixed-resource ledger terms remain externally pending (including 5 PH industrial Animal waste terms authorized separately after actual structural proof). Unknown price and physical CO2 coefficients stay null. Animal waste adds no new quantity or technology; the authorization is limited to the accepted source row/account. Independent source quantity, country, use, and nondiversion checks remain revocable. The frozen 471 old terms are retained within the enlarged accepted set. New terms come from the 18 newly accepted accounts.

PricedObjective and known fixed FOM inclusion are distinct from pending fixed terms. Known FOM enters a future objective through its hook exactly once; no actual objective has been evaluated here. FullSystemCostComplete=false and FullSystemEmissionsComplete=false. No complete absolute cost/emissions or fixed-term cancellation claim is made.

Constraint hooks are registered and validated through readback, not executed on optimization variables. Solver/scientific-result permissions remain false. Ready for Gate5 means an engineering readiness recommendation; Gate5 itself is neither authorized nor run by this task.

## Required final statuses

| Field | Result |
|---|---|
| `ASSEMBLY_V1_INPUT_COVERAGE_COMPLETE` | YES |
| `UNRESOLVED_ACCOUNTS_SILENTLY_ZEROED` | NO |
| `BLEND_BASELINE_IMPLEMENTED` | YES |
| `BLEND_UPPER_SENSITIVITY_REGISTER_READY` | YES |
| `SOURCE_SCOPE_COVERAGE_BOUNDARY_IMPLEMENTED` | YES |
| `EXISTING_STOCK_BOUNDARY_IMPLEMENTED` | YES |
| `FULL_SC_UNSOLVED_BASELINE_BUILT` | YES |
| `SOLVER_RUNS_EXECUTED` | 0 |
| `ACTUAL_DEMAND_CONSERVATION` | PASS |
| `ACTUAL_EXACTLY_ONCE_ACCOUNTING` | PASS |
| `HIDDEN_CROSSBORDER_CARRIER_SHARING` | ELIMINATED |
| `ACTIVE_SECTOR_COUPLING_PATHWAYS` | PASS |
| `ELECTRICITY_INTERCONNECT_CONTROL_SET_READY` | YES |
| `POLICY_CAP_ACTUALLY_ENABLED` | NO |
| `FULLSYSTEM_COST_COMPLETE` | NO |
| `FULLSYSTEM_EMISSIONS_COMPLETE` | NO |
| `GATE4_STATIC_VALIDATION` | PASS |
| `PHASE4_GATE4_CLOSED` | YES |
| `READY_FOR_PHASE4_GATE5_REDUCED_VALIDATION_SOLVE` | YES |

## Reproducibility and history

Started from verified local/remote 7a7931d01a5d85b697efcc675bd6837f6db5b35d on research/full-sc-baseline. Data choices, production assembly, tests, engineering correction and supplemental Animal waste authorization are separate logical commits. The first failed qualification attempt is preserved as historical evidence and superseded by the explicit human authorization plus the successful final build.

A later roundtrip check exposed an ordering-only difference in 27 native-schema explanatory rows. Their content and counts, all other static results, and physical input tables were identical. Stable sorting by component type and field fixed that report-comparison error; no scientific value or acceptance threshold changed. The before/after receipts and positive/negative tests are preserved. Fixed-account validation also reuses one dense Load input matrix within each call, while every new call still rechecks the current network; no qualification test was removed.

Use the `research_fullsc_unsolved` target with `configs/research/final_assembly_paths.json`. The final DAG consumes the pinned input-only electric asset, an unbound JSON recipe and qualified arrays; it never merges a Load-bound development NetCDF. The upper variant and unresolved stock register are outside the baseline build. Source hashes, environment, commands and actual producer SHAs are included in manifests and receipts.

Final local HEAD, remote HEAD, clean-tree and push evidence appear in the package DELIVERY_RECEIPT.json and validation_logs/GIT_DELIVERY_RECEIPT.json. Only research/full-sc-baseline is pushed; main/reference/archive are unchanged. Stop here for Human Review. NO SOLVER.
