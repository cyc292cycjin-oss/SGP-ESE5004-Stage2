# E3 Buildings demand-accounting specification

Material Passport: academic-research-suite; inline engineering/accounting review; Phase 3A-4 v1; 2026-10-01. Verification: ANALYZED (identities below are a proposed accounting contract, not measured ASEAN closure). Written before any E3 implementation. **E3 patch gate: STOP — necessary measured/reconciled inputs are absent.**

## Evidence and current implementation

Frozen U: `a3616a68ee44592af6527ca9024a90f1956646ae`. E1/E2/E4 integration changes neither `prepare_energy_totals.py` nor the electricity recalibration functions discussed here. Sources are the retained [U source snapshot](../source_snapshot/upstream/scripts/), [baseline map](../../buildings_heat_alignment/BUILDINGS_HEAT_BASELINE_MAP.md), [2019 accounting](../../buildings_heat_alignment/BUILDINGS_DEMAND_ACCOUNTING.csv), and [source candidates](../../buildings_phase3a3/ASEAN_BUILDINGS_DATA_CANDIDATES.csv).

Direct code observations:

- `prepare_energy_totals.py:119–174`: `electricity residential space/water` combines base heat commodities with fuel-to-electric-heat shares and efficiencies. It is not observed historical electricity by heating end use. Lines 219–255 combine remaining fixed heat fuel with service-like quantities and add non-heat fuel shifting to direct electricity.
- `prepare_heat_data.py:198–212` (U line numbers): computes `electric_heat_supply`, but its subtraction from electricity is commented out. Uncommenting it would use the wrong evidentiary quantity, and the commented selector `carrier == electricity` differs from the base AC load identity.
- `prepare_sector_network.py:3402–3410` (U): `add_residential` replaces base AC load profiles with the R electricity target; `add_services:3060–3073` adds S electricity. These operations do not preserve an explicitly identified non-Buildings residual.
- The main network builder calls heat, R, S, then optional distribution-grid logic. Distribution logic may multiply AC demand by a loss factor; a meter-to-bus boundary must be established before reusing this adjustment.
- `final_asean_adjustment.py:83,175–229,233–293,423–426`: `elec_carrier` excludes `services electricity`; total electricity growth runs even when heat is retained, then optional industry redistribution can rescale selected accounts again. Simply adding S to this list would force a total while rescaling accepted components. Neither that edit nor changing the spelling alone closes E3.

## Account dictionary (no implicit addition of parent and child accounts)

All identities below use a common country, year, meter boundary and time grid. Electricity is MWh_el; useful heat is MWh_th at the chosen service-delivery boundary. R and S remain separate.

| ID | Account | Role / required evidence |
|---|---|---|
| A | Original base electricity | Immutable source profile plus year, country coverage, final-meter vs supplied energy and losses. DemandCast/GEGIS network demand is not automatically UNSD final electricity. |
| B | R direct electricity excluding explicit space/water heating | R metered electricity minus identified represented historical space/water electric inputs; includes cooling, electric cooking and other direct uses. |
| C | S direct electricity excluding explicit space/water heating | Same rule as B, independent S evidence. |
| D | Historical electric space heating | Metered electricity for the exact space service represented; historical device mix and coverage recorded. |
| E | Historical electric water heating | Metered electricity for the exact water service represented; not an exogenous future HP input. |
| F | Cooling electricity | Subaccount of B/C or the retained residual; never an extra additive load on top of its parent. Unknown split stays unpartitioned, not zero. |
| G | Other direct Buildings electricity | Subaccount excluding F, electric cooking and D/E; lighting/appliances etc. |
| H | Explicit useful space-heat service | Final energy by end use/device converted using evidenced historical performance. Independent of optimized future technology choice. |
| I | Explicit useful water-heat service | As H; water timing independent of HDD. |
| J | Endogenous HP electricity | Link input from dispatch/COP, not an exogenous electricity Load. |
| K | Endogenous resistive-heating electricity | Link input from dispatch/efficiency, not an exogenous electricity Load. |
| L | CHP and other conversion flows | Account for fuel input, heat output and electricity output separately; signed bus flow, never count CHP electricity generation as demand. TES charge/discharge is internal conversion/storage flow. |
| M | Cooking final energy by fuel | NON-EXPLICIT + ACCOUNTING REQUIRED. Electric part stays inside B/C or residual; gas/LPG/biomass/oil remain direct final-fuel accounts. Excluded from H/I. No cooking module. |

“Non-thermal direct electricity” here means excluding **explicit space/water heating**, not removing cooling or electric cooking because they physically involve heat. F/G/M are a partition only if evidence supports that partition; otherwise retain a labelled unpartitioned direct account. No repeated addition of F/G/M to B/C.

## Base-year identities and exactly-once subtraction

Let `A*` be A reconciled to an accepted common final-electricity boundary, using a separately documented reconciliation delta, not an invented residual correction. Let `T_R,T_S` be R/S metered totals already contained in A*. Let `O` be the retained other-sector/residual electricity. Let `h_s = D_s + E_s` include only historical electric heating whose service is explicitly represented. Full Buildings heat coverage is the target; partial coverage must be explicit rather than silently treating unknown heat as zero.

At each reconciled node/snapshot (and therefore after summing over a country/year):

```text
A* = O + T_R + T_S
B = T_R - h_R
C = T_S - h_S
D_accepted = O + B + C
           = A* - h_R - h_S
D_accepted + h_R + h_S = A*
T_s = cooling_s + cooking_electric_s + other_direct_s + h_s
```

The last partition is asserted only with complete end-use evidence. If cooling/cooking subcomponents are unknown, `T_s - h_s` preserves their combined electricity without guessing individual values. The total `h_s` cannot be inferred from unspecified `T_s` alone.

Implementation contract: retain A* as an immutable audit source; construct accepted direct load from **one** decomposition of A*. If explicit B/C Loads are created, their energy is transferred from the residual ledger exactly once (`O = A* - B - C - h_R - h_S`). This is an account transfer retaining B/C, not deleting all R/S demand. An equivalent aggregate check `D_accepted=A*-h_R-h_S` is calculated independently and must not trigger a second subtraction. Never subtract whole R/S totals and fail to reattach their direct components. Never subtract D/E from B/C again after they have already been excluded.

For country c/year y with physical duration weights w_t:

```text
sum[n in c,t] w_t * (O_nt + B_nt + C_nt + h_Rnt + h_Snt - A*_nt) = 0
sum[n in c,t] w_t * H_snt = accepted annual useful space heat_csy
sum[n in c,t] w_t * I_snt = accepted annual useful water heat_csy
```

Also require snapshot identities pointwise, with all direct/residual profiles finite and nonnegative. Annual closure alone does not validate an hourly subtraction. Do not clip negative residuals or redistribute them silently; reconcile incompatible profiles and rerun checks. Snapshot generator/objective weights may differ: record physical MWh weights explicitly, and reconcile their relationship to the network’s accounting conventions. Static and dynamic Load representations are alternatives at a snapshot, not summed twice.

## Transformation and execution order

1. Freeze input files/hashes, geography, sector definitions, year, units and meter/loss boundary; reconcile A with final-energy sources. No scaling to a target of unexplained meaning.
2. Create a source-row/end-use/device mapping with an exclusive destination for every amount. Unknown shares remain missing; no 0.6 or other fallback. Preserve cooking by fuel and cooling electricity.
3. Identify historical D/E in the same coverage as explicit H/I. Derive H/I from all represented heating fuels/devices using accepted historical efficiencies/COP; do not substitute future optimized COP here.
4. Construct B/C and O once; store account IDs and source-row lineage so later functions cannot subtract or add them a second time. Apply independently accepted direct-demand growth and useful-service evolution only after this base-year bridge. A future gross-electricity forecast cannot constrain total electricity including J/K while also fixing useful service and allowing endogenous supply substitution.
5. Allocate accepted annual services and direct accounts spatially and temporally with explicit normalization and nonnegative residual checks. Do not subtract a BDEW-derived historical profile merely because it has the right annual integral.
6. Build fixed direct-electric/fuel Loads and H/I service Loads. Future boilers/HP/resistive/CHP/TES compete on the heat buses. Historical heating fuel replaced by H/I is removed from **fixed heating-fuel demand** exactly once; cooking and other direct fuel remain. Otherwise fixed fossil fuel and endogenous heat would duplicate the same service.
7. Apply a separately accepted loss/bus mapping once. DH service/supply/loss quantities remain distinct; no default DH adoption. Validate every later workflow stage as an observer of the accepted accounts; any generic electricity rescaling must be replaced or bounded by the chosen accounting contract in a future E3 change.
8. Before any solver: test identities, uniqueness and finite/nonnegative values. After a future solve: add optimized conversion inputs to direct electricity; do not hard-code them beforehand. Generation/import/export/storage/loss balance is a separate physical network equation.

## Endogenous conversions and fuels

At the service boundary, schematic future dispatch identities are `heat_HP,t=COP_t*electricity_HP,t` and `heat_resistive,t=eta_t*electricity_resistive,t`; actual component efficiencies and bus directions must match their source. Thus `system electricity consumption = D_accepted + J + K + other endogenous electricity inputs + defined losses` (with storage charging and discharging separately signed in the bus balance). Electrolyser input is mentioned only to prevent duplicated accounting; no hydrogen boundary change in this phase. CHP consumes fuel once and co-produces useful heat and electricity; do not deduct its fuel twice or assign all fuel energy simultaneously to both final services.

For each observed fuel/end use: `F_total = F_heating_represented + F_cooking + F_other + F_unclassified`. Shares refer to a stated denominator and must exhaust it, or retain an explicitly unknown/unclassified term. Missing is not measured zero. Physical fuel-to-useful-heat conversion changes energy amount because of efficiency/COP; final MWh and useful MWh must not be equated or added as “total demand”.

## Evidence gate and current decision

Verified source recovery provides UNSD2019 R/S aggregate final energy and bounded end-use candidates (Malaysia2016, household samples in other countries). It does **not** provide an accepted eleven-country R/S heating-electricity decomposition aligned with the network base profile, historical device mix/performance, or matched hourly subtraction profiles. Prior 11-country UNSD national−R−S arithmetic closure does not supply these missing quantities.

Therefore the algebra and order above are explicit, but numerical country/snapshot closure is **not established**. No E3 model patch, uncommenting, carrier-list change, useful-heat input generation, or formal solve is authorized by the available evidence. Follow the [data requirements](../../../../data_registry/buildings_phase3a4/BUILDINGS_E3_DATA_REQUIREMENTS.csv) and [useful-heat method](BUILDINGS_USEFUL_HEAT_METHOD.md). Human review is still required for source/version/scope and every candidate numeric input.
