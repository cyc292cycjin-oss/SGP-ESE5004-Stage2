# Phase3C agriculture bounded source and boundary review

Evidence classes: **verified frozen-code behavior**, **verified cached input text**, and **analytical assembly recommendations** are distinguished below. All numeric cache entries remain **UNVERIFIED for scientific input acceptance**. No internet search, new raw-data sweep, new technology, model solve, or source/config modification was performed.

## 1. Direct answer and first-baseline recommendation

Agriculture does not require a new technology or service-competition model for the first Full-SC baseline. The inspected upstream implementation is **fixed final-energy demand**, not agricultural activity, useful heat or a machinery model. Recommended first representation: **EMBEDDED electricity in A*** plus **FIXED carrier-specific fuel obligations retained once**. Preserve accepted biomass/coal as well as oil; do not drop energy merely because the narrow upstream agricultural consumer only implements oil. No crop, machinery, irrigation or agricultural H2 deep dive is justified by the current evidence.

This recommendation is based on the represented mechanisms and the user's scope rule, **not a claim that agricultural energy is universally negligible**. Oil and biomass account magnitudes below require retention. Aggregate fuel supply can indirectly couple agriculture to synthetic-fuel production and therefore electricity/H2 even though agriculture itself has no substitution decision.

## 2. Exact code lineage and units

Frozen U: `a3616a68ee44592af6527ca9024a90f1956646ae`. Paths and full SHA256s are recorded in `AGRICULTURE_OBSERVATIONS.json`.

- `config.default.yaml:690` sets demand base year 2019; `:730` and `configs/config.asean.yaml:206` enable agriculture. Enabled capability does not prove a full-SC final network.
- `Snakefile:1717–1748`: UNSD link workbook/raw directory → `build_base_energy_totals.py` → base annual national energy CSV → `prepare_energy_totals.py` with growth and efficiency CAGR → future annual CSV.
- `build_base_energy_totals.py:59–62` selects agriculture by the commodity/transaction string. `:85–89` records missing electricity/oil/biomass if the entire sector subset is empty. `:224–243` sums electricity, grouped oil, grouped biomass and grouped coal final energy. No agriculture useful-heat or activity quantity is produced there. Fuel group factors are inherited from `_helpers`; a generic mass/energy factor citation is not automatically an accepted HHV/LHV convention.
- Unit conversions are source electricity million kWh /1000 to TWh; TJ /3600 to TWh; mass-based fuels through the existing per-commodity factor. The cached national annual columns are TWh/year. No crop output, hectares, machine-hours or service-efficiency conversion is present in this chain.
- `prepare_energy_totals.py:37–44,78–94,107–111` grows the final-energy quantities using `(1 + efficiency_CAGR)^years × (1 + growth_CAGR)^years`; `:296` writes `fillna(0)`. All ASEAN country rows are absent from both inherited CAGR tables, so they receive DEFAULT. A DEFAULT parameter is not an accepted ASEAN forecast.
- `prepare_heat_data.py:149–160` uses the country label `pop_layout.ct`, sets node labels, and multiplies all energy totals by population fractions. Its `fillna(0)` is another missing-to-zero step. The fact this intermediate file lives in `demand/heat/` does **not** make agricultural final electricity/oil a thermal-service demand.
- `Snakefile:1474–1478` passes that nodal annual table when either agriculture or rail is enabled. `prepare_sector_network.py:4013–4016` calls `add_agriculture`.
- `add_agriculture`, `:3161–3199`: fixed nodal electricity Load on electricity buses, fixed nodal oil Load on oil buses, each `annual_TWh × 1e6 / 8760` MW; an aggregated negative Load on `co2 atmosphere` reports oil emissions. No efficiency-based replacement, electric tractor, thermal bus, H2 consumer, or agricultural device investment variable appears in this function.
- `:3468–3470` moves electricity-labelled Loads to low-voltage buses when distribution-grid logic is enabled. This is a network assignment, not agricultural end-use substitution.

## 3. Cached 2019 annual source text and limitations

These values are copied directly from `energy_totals_base.csv`, preserving the source text. `MISSING` is a blank, **not zero**. Cache zero has not been independently established as a measured zero; the source sums can turn empty commodity subsets into zero. The earlier transport raw evidence pool cannot establish agriculture raw coverage, so no agricultural-zero claim is made here.

|Country|Electricity TWh|Oil TWh|Biomass TWh|Coal TWh|
|---|---|---|---|---|
|BN|MISSING|MISSING|MISSING|MISSING|
|ID|0.594|4.3145|0.0|0.0|
|KH|0.0|0.0036|0.0|0.0|
|LA|0.0419|0.3821|0.0|0.0|
|MM|0.0|16.0165|0.0|0.0|
|MY|0.6639|10.2298|0.0|0.0|
|PH|2.79|2.8012|0.0461|0.0|
|SG|MISSING|MISSING|MISSING|MISSING|
|TH|0.468|34.9603|0.0|0.0|
|TL|MISSING|MISSING|MISSING|MISSING|
|VN|6.5954|10.9716|4.4005|0.2152|

|Field|Sum of available cached 2019 rows (TWh)|Countries with missing base values|
|---|---|---|
|agriculture electricity|11.1532|BN, SG, TL|
|agriculture oil|79.6796|BN, SG, TL|
|agriculture biomass|4.4466|BN, SG, TL|
|agriculture coal|0.2152|BN, SG, TL|

These are incomplete cache subtotals with BN/SG/TL missing, not an adopted ASEAN total and not proof of negligibility. Country maxima and positive fuels show why accounting retention matters: TH oil 34.9603 TWh; VN electricity 6.5954 TWh and biomass 4.4005 TWh; PH biomass 0.0461 TWh; VN coal 0.2152 TWh. No numerical materiality threshold is assigned.

All four agricultural fields for BN/SG/TL are blank in the base table. In future cached 2030/2040/2050 tables they are zeroed. Agriculture coal has no growth or efficiency column, and its positive VN base value becomes zero in the future table through column alignment and `fillna(0)`. Therefore future zero coal is not evidence of an accepted coal phaseout. The biomass column can remain positive in projected inputs, but the `add_agriculture` function consumes only electricity/oil and does not itself create a biomass or coal demand. Avoid silently discarding these streams when consolidating the research fuel ledger.

|DEFAULT field|Growth CAGR original text|Efficiency CAGR original text|
|---|---|---|
|agriculture electricity|0.02156|-0.002696|
|agriculture oil|-0.01859|-0.006705|
|agriculture biomass|0.01471|-0.01232|
|agriculture coal|NO COLUMN|NO COLUMN|

Source acceptance for an aggregate fixed account can be handled with the common Phase4 annual-demand/growth decision. It does not require a special agricultural forecasting project.

## 4. Capability, effective configuration and actual tutorial result differ

Frozen ASEAN config enables agriculture but `only_elec_network: true` (`config.asean.yaml:262`) later restricts the network. Prior retained `research/00_model_audit/SECTOR_COUPLING_MAP.md` reports 48 agriculture-electricity Loads, 37 nonzero, and oil Loads removed in the solved tutorial. The retained tutorial weighted annual electricity was 13.690059 / 16.493763 / 19.871660 TWh for 2030/2040/2050 respectively. These are **previously derived model quantities**, with 6-day sampling weighted to 8760, not annual observations or accepted Research Full-SC demand. No completed solve was rerun.

That earlier audit also records the missing comma joining agriculture and rail names in the final-adjustment carrier list. Current source `final_asean_adjustment.py:83–86` directly corroborates it. This reinforces the need for the common Phase4 parent-account conservation checks; it does not require an agriculture-specific model or justify reusing the tutorial final total as A*.

## 5. Exactly-once electricity/fuel and carbon contract

**Electricity:** A* is the accepted final-user electricity parent. If agricultural electricity is already included in A*, retain it within the direct parent and suppress the additional research agriculture-electricity child Load. An alternative separately labelled fixed child is valid only with an equal, compatible parent subtraction exactly once. `add_agriculture` itself adds the child and performs no parent subtraction. We have not verified the numerical contents of a future accepted A*; conceptual inclusion is not a measured subtraction value.

**Fuels:** Retain an agriculture carrier subledger, or demonstrable inclusion in a common fixed final-fuel ledger. Do not add the same oil quantity to an already inclusive national fuel parent. Preserve existing biomass/coal where accepted; no automatic oil conversion, coal-to-electricity shift or invented heat service is authorized. For countries with missing subaccounts, an accepted inclusive parent may retain them without a guessed child; otherwise preserve the missing flag for common input reconciliation.

**Supply coupling:** Agricultural demand is fixed. Oil supplied through common fossil or FT/synthetic options can create endogenous upstream electricity/H2 demand; it belongs to fuel-supply accounting, not a preloaded agricultural electricity estimate. Do not add an exogenous H2 requirement for the same synthetic fuel. The fixed electricity requirement is served through the common power system.

**Carbon:** Current `add_agriculture` oil emissions go to `co2 atmosphere` (`:3187–3199`). In the research architecture they belong to `ReportingCO2_FullSystem`; they must not silently enter the original `PolicyCO2_Power` cap. Biomass/coal reporting follows whichever accepted fuel-specific treatment is retained; do not invent emission factors. This is part of the shared carbon-scope assembly blocker, not a request for a new agricultural carbon policy.

## 6. Materiality and Phase4 handoff

| Issue | Evidence and scientific relevance | Phase4 treatment |
|---|---|---|
| Repeated agricultural electricity | Additional fixed child exists; no subtraction inside add_agriculture; A* is inclusive by definition | Use shared exactly-once parent conservation; EMBEDDED electricity recommended |
| Fuel energy silently omitted | Positive oil/biomass/coal in base; only electricity/oil consumed; coal projected to zero by missing columns | Retain fixed carrier obligations/parent membership, validate totals; do not relabel all fuel as oil |
| Emissions scope collision | Agricultural oil emissions Load attaches to shared atmosphere | Shared power-policy/reporting isolation; no new cap |
| Missing BN/SG/TL and unsourced future growth | Blank base cells then zeros; no ASEAN CAGR rows | Preserve uncertainty and use common input acceptance/fallback contract; not a new design phase |
| Temporal and spatial conservation | National annual energy allocated by population and flat MW = annual/8760 | Common node and snapshot-weight checks; not crop/irrigation precision |
| Agricultural device substitution details | No such endogenous technology mechanism in inspected function | DEFER; no evidence requiring EXPLICIT_REQUIRED agricultural technology |

**Conclusion:** Freeze agriculture as **EMBEDDED electricity + FIXED/retained final fuels once**, subject to existing common Phase4 input/conservation/carbon gates. No evidence establishes that a new agricultural technology model is necessary for the core electricity-interconnection comparison. Preserve shared fuel-supply coupling and known energy quantities; do not claim energy is negligible, fill missing countries, or open a new sector deep dive.
