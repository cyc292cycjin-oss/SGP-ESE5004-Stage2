# Shipping / Aviation / H2 fuel / Carbon — frozen-source audit notes

Status: source-verified architecture; analytical risks stated separately; no model edits, new data, solver, or new policy. This is supporting evidence for Phase 3B-1, not a human-approved research boundary. Root audit is responsible for actual saved-network membership and numerical demand checks.

P = `5bacad702ccfed17ad19ab510fa710651e966f2c`; U = `a3616a68ee44592af6527ca9024a90f1956646ae`. Every source reference below is relative to `evidence/source/`; line numbers refer to these frozen copies. V and R are not modified. Prior carbon background reused: `research/01_baseline_construction/CARBON_EQUIVALENCE_TEST.md` (its existing scope test is not rerun).

## 1. Findings that matter to the first Full-SC boundary

1. **Shipping and aviation are explicit fuel-demand functions in U, enabled in ASEAN config; final ASEAN electricity stripping removes their demand carriers.** Framework support and sector enable flags do not prove retained final demand. `U/scripts/prepare_sector_network.py:1545–1628,1683–1850,3979–3994`; `U/configs/config.asean.yaml:198–208,260–262`; `U/scripts/final_asean_adjustment.py:18–80,124–143,419–421`.
2. **Raw national demand is final fuel/energy consumption in TWh/year, not passenger-km or tonne-km.** Domestic and international categories are separate at extraction, then added together before nodal fuel Loads. There is no endogenous shipping/aviation transport-service bus and no vehicle/ship/aircraft stock competition.
3. **The international-bunkers flag is an emissions switch, not a demand switch.** `false` does not remove international fuel supply. Moreover its false branch uses a regional total multiplied by the sum of national domestic fractions, rather than a country-demand-weighted sum. This algebraic issue is present in P and U; it must not be silently treated as an accepted domestic-emissions ledger.
4. **Shipping H2 adoption is exogenous; fuel supply can be endogenous.** ASEAN DEC shipping H2 shares are all zero for 2020–2050. H2 production, storage, and FT oil production are separate extendable supply options. Their existence does not prove positive transport H2/synthetic-fuel demand or production.
5. **Aviation uses one oil bus/kerosene-labelled fixed Load.** There is no direct aviation H2, NH3, or methanol demand in the inspected constructor. FT can feed the same oil bus; this is aggregate synthetic oil supply, not a separate aircraft kerosene-blend/technology choice.
6. **The shared atmosphere ledger includes the Shipping/Aviation combustion that is explicitly connected and upstream fuel-production emissions; this does not prove complete accounting of every transport mode.** Applying the original power-case trajectory to that enlarged ledger is a `SYSTEM_LEVEL_BLOCKER` for a claim of unchanged carbon scope. Rail oil has a separate omission path, documented in Section 9. This phase diagnoses these issues; it does not alter the cap or solve an alternative policy.

## 2. National raw demand → prepared demand

### Verified source chain

`Snakefile:1717–1748` → `data/demand/unsd/paths/Energy_Statistics_Database.xlsx` → cached/downloaded UNSD commodity transaction text files → `resources/<SECDIR>/energy_totals_base.csv` → growth/efficiency tables → `energy_totals_<year>.csv` → Shipping/Aviation constructor.

- Entry workbook and source links: `U/scripts/build_base_energy_totals.py:366–375`. If update enabled, source URLs are fetched; fallback is a Google Drive archive at `:376–405`. Do not rerun this download for the audit.
- Concatenate semicolon UNSD files and parse country/transaction: `:412–445`. Select configured year and countries: `:450–456`.
- Default base year **2019**, `U/config.default.yaml:686–690`; ASEAN country selection is the config list, not guaranteed raw-data completeness. Source retrieval date/version must come from retained raw-file evidence, not from the configurable base year.
- Conversion to TWh: thousand metric tons × fuel factor; million kWh ÷ 1000; TJ ÷ 3600; thousand cubic metres × commodity factor. `U/scripts/build_base_energy_totals.py:108–132`. Unsupported units are not explicitly rejected in this block; raw-unit completeness needs the retained-file check.
- Helper fuel factors cite the UN energy balance methodology URL, but the local numbers are a hard-coded mapping, `U/scripts/_helpers.py:1837–1907`. Examples: kerosene-type jet fuel `0.01225` and fuel oil `0.01122` TWh per thousand tonnes (`:1859,1865`). No statement here establishes that every raw fuel and technology efficiency has an aligned HHV/LHV basis. Do not infer scientific acceptance solely from the citation.

| Mode | Raw transaction / commodity filter | Prepared columns | Meaning / caution | Source lines |
|---|---|---|---|---|
| Aviation domestic | `Kerosene-type Jet Fuel` AND `Consumption by domestic aviation` | `total domestic aviation` | Fuel energy; excludes other aviation fuel names even if present | `U/scripts/build_base_energy_totals.py:262–276` |
| Aviation international | `Kerosene-type Jet Fuel` AND `International aviation bunkers` | `total international aviation` | Bunker-energy column; does not prove inclusion in national final-consumption parent | same |
| Navigation domestic | `Consumption by domestic navigation` within navigation/marine-bunkers sector filter | `total domestic navigation` | Sums all matched commodities, then constructor represents oil/H2 | `:36–44,278–292` |
| Navigation international | `International marine bunkers` | `total international navigation` | Supply in reporting country, not a route-by-route bilateral transport model | same; final interpretation of UNSD reporting coverage stays unverified |

These original statistics are best classified `GLOBAL_HARMONIZED` with country-specific observations, not ASEAN-model-specific forecasts. The model does **not** derive these demands from AEO8. International bunker columns are selected separately from domestic transactions; this code alone cannot establish how an external ASEAN/national final-energy aggregate includes or excludes them. An explicit research ledger decision is required before treating bunkers as national final demand, total regional transport obligation, or excluded scope. No numerical correction is made.

### Projection and missingness

`U/scripts/prepare_energy_totals.py:63–109` reads base, growth, efficiency, fuel shares and district heating; compounds each CAGR over target-year minus base-year. Missing country rows/cells inherit `DEFAULT` (`:39–44,77–89`).

- Aviation uses general `base × efficiency_factor × growth_factor` (`:105–109`). Navigation is overwritten by oil/H2-share-weighted efficiency factors (`:272–289`). Thus the intermediate generic `total international navigation` efficiency column is not the final factor for these overwritten navigation totals.
- Frozen `data/demand/growth_factors_cagr.csv` has `DEFAULT, MA, NA, US`, no ASEAN rows. DEFAULT aviation domestic/international CAGRs = `0.03715/0.02156`; navigation domestic/international = `0.006453/0.02504`. DEFAULT duplicates MA for these entries. These are direct file values, **not accepted ASEAN forecasts or proof of European provenance**.
- Frozen `efficiency_gains_cagr.csv` has `DEFAULT, MA, US`, no ASEAN rows. DEFAULT aviation factors are zero CAGR; navigation oil/H2 CAGRs `-0.001062/-0.008517` enter the overwritten navigation calculation. Treat as `DEFAULT` with original calibration unverified.
- `prepare_energy_totals.py:296` writes `energy_totals.fillna(0)`. Empty national observations may therefore become zeros; missing ≠ demonstrated zero. In base extraction, `round(sum(),4)` can also return zero when sector rows exist but no exact target commodity/transaction matches. This is a coverage risk, not evidence that every reported zero is wrong.
- Growth/efficiency defaults have a credible pathway to H2/oil/electricity magnitude and country costs. They are more material than fine ship/aircraft subtypes.

## 3. Shipping construction

### Spatial and temporal chain

1. `prepare_ports.py:21–31`: World Port Index monthly CSV, NGA URL embedded in source. This is a changing global port-location dataset; date not pinned by URL alone.
2. `:120–135`: small/medium/large ports retained; numerical weights 1/2/3 normalized by country. These are categorical-size proxies, **not observed bunker sales or throughput**. Tiny/unknown ports are excluded. `filter_ports(:36–63)` affects export-port output; normal `ports.csv` is written beforehand at `:137` and includes all retained sizes. Do not confuse `export_ports.csv` with shipping-demand allocation.
3. `prepare_sector_network.py:1704–1728` filters countries and maps port points to geographic nodes. `_helpers.locate_bus:1814–1832` does country-specific nearest spatial join and drops unmapped rows. This requires country/nodal conservation verification; no road/population distribution is used for shipping.
4. H2 load = `H2_share × port_fraction × (domestic+international TWh) × shipping_average_efficiency / fuel_cell_efficiency × 1e6/8760` (`:1709–1741`). The scalar MW is constant across snapshots. No sailing schedules, bunker inventory requirements, or vessel activity profiles are imposed by the Load.
5. Optional H2 liquefaction adds a Bus and extendable Link (`:1748–1772`), with costs/efficiency from prepared technology costs. This Link has H2 input/output, not an explicit AC electricity port. Default liquefaction false (`config.default.yaml:979`).
6. `H2 for shipping` Load is added unless special reference-policy/remove-H2-load flags apply (`:1774–1785`). Zero share can still produce zero-valued structural Loads; component existence is not positive H2 demand.
7. Oil share = `1 − H2_share`, creating `shipping oil` constant Load on nodal oil Bus (`:1787–1805`). Endogenous port-level fuel substitution is **not** present. No ship capex/stock/turnover exists here.
8. Oil supply if absent: extendable oil Generator with marginal fuel cost plus cyclic extendable oil Store (`:1829–1850`). This is commodity supply, not inferred domestic oil production or import geography.

### Important source-level implementation risks

- Shipping `ports` is grouped by node at `:1743–1746` and then reused at `:1790–1796` to map `ports['country']` to national demand. Summing object columns can concatenate multiple country strings (e.g., multiple same-country ports per node) or omit them under other pandas behavior; the subsequent map can fail or create missing oil p_set. This is a source-derived risk whose actual magnitude belongs to saved-network/raw-port checks, not a claim that all current shipping Loads fail.
- `shipping_average_efficiency=0.4` comment says fuel-oil-to-propulsion in **2011** (`config.default.yaml:980`), while `doc/configtables/sector_shipping_aviation.csv` describes it as hydrogen-powered-ship efficiency. The actual formula uses it as baseline oil propulsion efficiency divided by fuel-cell efficiency. This documentation/definition conflict and 2011→2019/target-year compatibility remain unaccepted assumptions.
- Navigation future demand is already share-weighted for efficiency in `prepare_energy_totals.py:272–289`, then converted to H2/oil in the constructor. These are two distinct transformations. Without original calibration definitions, do not declare them either automatically valid or automatically double-counted.
- ASEAN DEC H2 share is zero at every listed year (`config.asean.yaml:232–239`). `scenario.demand=['DEC']` is migrated to `demand_data.scenario` by `_helpers.py:241–245`. Do not accidentally use default AB share 0.05 for the ASEAN DEC case.

## 4. Aviation construction

`prepare_airports.py:19–40` retrieves global OurAirports airports/runways; optional custom file at `:97–99`. Filtering at `:48–55`: medium/large airport, non-null IATA, scheduled service yes. Airport-size proxy medium=1, large=`airport_sizing_factor` (default3), normalized within country (`:57–77`, `config.default.yaml:991`). Runways are joined (`:125–137`) but demand shares use categorical airport size, not runway length, passenger count, or fuel sales.

`prepare_sector_network.py:1569–1606` adds domestic plus international energy, assigns port-like spatial mapping, then constant `kerosene for aviation` MW Load = TWh × fraction × 1e6/8760. Carrier label is kerosene, physical supply bus is **oil**, shared with other petroleum demands. Passenger/freight aviation are not distinguished. There is no endogenous flight-service choice, hydrogen aircraft, NH3 aircraft, methanol aircraft, or aircraft stock model in this function.

The source comment `aviation runs with dummy data` at `:3988` and the missing-data note at `:2250–2256` are warning clues, **not proof** that retained country fuel-energy inputs are dummy. Actual data provenance must be based on the generating rule and retained values.

No flight schedule is imposed. Upstream synthesis/production/storage can time-shift supply; a constant fuel sink does not mean the associated electricity profile must be flat. Airport placement can affect H2/FT siting and grid investment, so the size proxy is a spatial limitation with a system-level pathway, without demanding every aircraft subtype.

## 5. Hydrogen and synthetic fuel: what is connected

| Path | Constructor / consumption | Default or ASEAN state | Interpretation |
|---|---|---|---|
| AC → H2 electrolysis | `prepare_sector_network.py:420–425,651–684` | production list includes H2 Electrolysis | Extendable production, endogenous AC withdrawal |
| Gas → H2 SMR / SMR CC | `:506–524,651–684` | both in default list `config.default.yaml:787–790` | Endogenous supply; atmosphere/store emissions and capture |
| H2 → shipping | `:1733–1785` | DEC H2_share0, default liquefactionfalse | Fixed exogenous fuel demand, not ship-tech competition |
| H2 + CO2 + AC → oil (FT) | `:344–380,3950–3951` | FT true `config.default.yaml:1005`; minload0.9 `:1006` | Endogenous aggregate oil supply for shipping/aviation/other oil sinks if retained |
| H2 + AC → NH3; NH3 → H2 | `:2146–2235` | ammonia enabletrue | Industrial NH3 Load and storage; **no direct shipping/aviation NH3 Load** |
| H2 → gas (Sabatier), AC → gas (helmeth) | `:1631–1680` | both true `config.default.yaml:1000–1001` | Common gas supply pathways; not direct marine/aviation methane engines |
| Methanol | no match in inspected sector constructor | no direct transport path found | `ABSENT` within inspected implementation, not a claim about every PyPSA fork |
| Biofuels | base navigation sums matched commodities; aviation strictly kerosene-type jet fuel | no explicit transport-specific biofuel blend/production/demand choice here | Do not infer a sustainable aviation fuel pathway from the existence of generic biomass |

Haber-Bosch draws H2 and AC and supplies industrial NH3; cracker may indirectly supply a common H2 bus. This does not make ammonia a represented shipping propulsion fuel. FT has H2 bus0, oil bus1, negative CO2-stored input at bus2 and negative AC input at bus3. It therefore has direct additional AC use as well as electrolysis demand. Costs and efficiency are read from prepared `costs` DataFrame (`:3923–3924`); these code references establish consumption and capacity basis, not human acceptance of raw DEA values.

**Accounting test, not a patch:** fixed H2/fuel demand + endogenous H2/fuel production is normal supply-demand balancing. Double counting requires a duplicated obligation: e.g., fixed A* electricity already includes future electrolysis for that exact fuel demand **and** the new production Link withdraws it again; or the same oil/H2 final demand appears in both general direct-fuel accounts and explicit transport accounts. Historical transport electricity subtraction must be exact and evidence-linked. Do not subtract electrolysis merely because a future H2 Load exists. Do not convert all marine/aviation fuel consumption to electricity before allowing endogenous conversion.

## 6. Carbon ledger and the bunker error

### Verified mechanics

- `add_co2`, `U/scripts/prepare_sector_network.py:1426–1446`: `Carrier co2` with `co2_emissions=-1`; one `co2 atmosphere` Bus and non-cyclic, extendable Store which can be negative.
- Conventional generators become Links to that atmosphere; fuel-carrier emissions set to zero to avoid counting both fuel and atmosphere (`:3809–3832`).
- Aviation (`:1622–1628`) and shipping (`:1821–1827`) combustion are negative-p_set Loads on the same atmosphere, equivalent to injecting CO2. Oil supply may be fossil or synthetic, while fixed sink emission bookkeeping represents combustion of total fuel; FT consumes stored CO2 and can receive DAC/capture carbon credits through the shared carbon system. Net emissions depend on the complete supply/capture chain, not on calling kerosene synthetic.
- H2 itself has no direct combustion CO2 in shipping Load; SMR/SMR CC upstream emissions enter that same ledger (`:506–524`). Biomass-derived H2 is supported in tech definitions but not in the default enabled production list; do not count it as active.
- `add_co2_budget:3626–3662` creates scaled global budget via `prepare_network.add_co2limit:149–156`. That consumer supplies carrier_attribute `co2_emissions`, <= and annual limit×snapshot-weighted years; it contains **no power-sector filter**.
- In a retained Full-SC network, transport demand expands the physical emissions ledger subject to this constraint. The pre-existing research assumption is the paper power-system trajectory (including its retained power-supply conversion chain), not permission to reuse that cap for all transport/heat/industry. `SYSTEM_LEVEL_BLOCKER`; merely disabling H2 pipelines or CO2 pipelines does not separate the ledger.
- Baseline `co2.budget.enable=false` avoids an active trajectory cap, but does not resolve the scope equivalence required for any later DEC comparison.

### Algebraic derivation of the false-bunkers branch

Let `q_c` be each country's summed domestic+international oil demand and `r_c = domestic_c/(domestic_c+international_c)`. The code at `:1616–1620` and `:1815–1819` computes an expression proportional to:

`sum_c(q_c) * sum_c(r_c) * oil_CO2_intensity`.

The intended country-weighted domestic-only expression would instead be:

`sum_c(q_c * r_c) * oil_CO2_intensity`.

These are not generally equal for more than one country. This is a **source algebra finding**, not a numerical estimate of actual saved-network emissions. Missing or 0/0 shares also interact with pandas summation. The true branch simply counts all the spatially allocated oil demand. Both branches retain domestic+international fuel energy. Same logic already exists in P `prepare_sector_network.py:1245–1303,1403–1520`; this is not a new U-only drift.

### Version issue retained separately

P `prepare_sector_network.py:2973–3009` consumes old `co2_budget.co2base_value`. U consumer reads `co2.budget.base_value` (`:3642`). U ASEAN file still has nested `co2.budget.co2base_value:1e9` (`config.asean.yaml:171–182`), while default base_value is `limit` and default limit77.5e6 (`config.default.yaml:603–621`). `_helpers.py:266–281` migrates old top-level co2_budget only, not the mixed nested key. Prior Phase2 report already distinguishes key/value equivalence from sector-scope equivalence. No fix is applied here; root should state which effective config pertains to each saved artifact rather than interpreting U's raw YAML as a successful run.

## 7. Candidate classification and minimum review decisions

These are proposals for human review only:

- **Shipping:** `SYSTEM_RELEVANT_PENDING`; potentially FIXED fuel-demand obligation with EXPLICIT supply links after country/bunker coverage, growth assumptions, nodal oil conservation, H2-share definition and carbon scope are reviewed. Do not close it solely because data are imperfect; it can materially affect fuel supply, H2, renewable capacity, storage and interconnection. H2 share is an externally chosen scenario assumption, not a cost-optimal ship choice.
- **Aviation:** `SYSTEM_RELEVANT_PENDING`; fixed aggregate oil/kerosene demand with possible explicit FT supply is a defensible *candidate*, subject to volume/growth and bunker/carbon boundary. No need for aircraft types. Do not state synthetic aviation fuel is guaranteed or quantify its system impact without a solved, approved model.
- **NH3/methanol transport use:** DEFERRED/ABSENT in this implementation. Existing industrial ammonia and cracker do not authorize adding marine ammonia or methanol technology.
- **Major temporal mechanics:** flat fuel obligation with storage and endogenous fuel production can still materially affect electricity/storage, especially FT min part load0.9. Ship departure/flight detail is not automatically a blocker. Liquefaction defaults and throughput-based siting may be refined later if material.
- **Research decisions, not missing raw files:** international bunker scope/allocation; admissible fixed H2 and synthetic fuel shares; which regional fuel networks remain under Disconnected; shared-fuel and capture-credit carbon allocation while preserving original power cap. These should not be described as requests for the user to find every national vessel database.
- **Minimal quantitative evidence if moving beyond this audit:** retained 2019 domestic/international country totals with zero/missing flags and units; accepted future growth/share settings; country-sum equality after port/airport mapping; parent/direct-fuel deduplication; named emissions ledgers. Existing cached files should be exhausted first. No new data requested here until root integrates all retained evidence.

## 8. Retained-network evidence supplied by root and independently read

Read-only metadata artifact: `evidence/NETWORK_TRANSPORT_EVIDENCE.json`, `TUTORIAL_PRE_STRIP.selected_components.loads`. This source preserves non-finite static `p_set` as the string `NaN`; values are not repaired or silently summed as zero here.

| Tutorial pre-strip carrier | Structural Load count | Non-finite static p_set | Positive finite | Zero finite | Meaning |
|---|---:|---:|---:|---:|---|
| H2 for shipping | 48 | 1 | 0 | 47 | DEC zero share does not make the non-finite record a verified zero |
| shipping oil | 48 | 39 | 7 | 2 | Current full shipping national demand is not quantitatively verified |
| kerosene for aviation | 48 | 0 | 45 | 3 | Numerically finite, not automatically source/boundary accepted |

- H2 non-finite node: `PH_Luzon9 0 H2 for shipping`. H2 p_set is built before the problematic post-grouping oil map; its NaN requires separate node/index-alignment tracing. Do not claim the oil map alone explains it.
- Finite oil node values sum to `140.1615547950945 MW`; this is a **partial finite-node sum**, not a complete ASEAN shipping-demand estimate.
- Aviation sums to `48115.220236008616 MW`, with retained snapshot weights summing8760 gives `421.48932926743547 TWh`. This is a retained tutorial pre-strip network quantity; no independent reproduction and no new model execution. It does not validate airport share proxies, default growth, missing countries or national-final-energy/bunker scope.
- Root extraction finds author final2025/2050 networks with EV and rail-electric Loads but no shipping/aviation terminal Load; tutorial final retains rail-electric Loads and no shipping/aviation terminal Load. This is consistent with `only_elec_network` stripping. Generic FT/SMR/H2 components retained for the electricity supply chain do not restore those missing terminal transport demands.

Therefore classification must distinguish **explicit construction capability and pre-strip components** from **final-network terminal demand**, and the saved pre-strip Full-SC shipping representation remains unverified. No missing input is inferred to be zero.

## 9. Bounded follow-up: rail oil combustion can bypass the carbon ledger

Requested source cross-check after the road/rail audit found no explicit rail-emissions component. This adds an **accounting-completeness** issue distinct from the power-versus-Full-SC **scope** issue. Do not summarize this audit as “all transport combustion is already counted.”

### Source-verified conditional omission path

1. `U/scripts/prepare_sector_network.py:3696–3740` is the entire `add_rail_transport` body. It reads annual total rail minus rail electricity, creates a `rail transport oil` Load directly on the shared oil Bus (`:3721–3730`), and creates a separate rail-electric Load (`:3733–3740`). It creates no oil-to-mobility combustion Link and no negative CO2 Load to `co2 atmosphere`.
2. `add_carrier_buses` initially attaches the fuel CO2 intensity to a new Carrier (`:297`) and creates ordinary fuel supply Generators and cyclic Stores (`:301–315`). The oil Generator has only the oil Bus; it does not physically inject CO2 at the atmosphere.
3. Default `conventional_generation` includes `oil: oil` (`U/config.default.yaml:1018–1024`). When at least one conventional oil power Generator is converted, the conversion adds an oil-to-electricity Link with atmosphere bus2 (`U/scripts/prepare_sector_network.py:3809–3820`) and sets the **shared oil Carrier's** `co2_emissions` to zero (`:3831–3832`) to avoid double counting that power combustion. The `carrier_gens.empty` branch at `:3801–3803` makes this zeroing conditional on a matching converted oil generator; it is not guaranteed for every possible configuration.
4. If the retained oil carrier factor is zero, then fossil-oil Generator → shared oil Bus → rail-oil Load bypasses both a nonzero carrier factor and an atmosphere injection. The oil powerplant Link's emissions apply only to its own dispatched fuel, not all withdrawals from the oil bus. A rail Load's name/carrier alone does not generate combustion CO2.
5. Therefore **source proves a concrete omission path under an explicitly stated condition**. It does not yet quantify omitted emissions or prove dispatch uses fossil oil. A network with nonzero oil carrier factor could count fuel-supply emissions through the primary-energy constraint, but that is a different accounting setup that would also need checks against separately emitted oil combustion.

### Retained evidence: sample condition now confirmed

`NETWORK_TRANSPORT_EVIDENCE.json` establishes for `TUTORIAL_PRE_STRIP`: 48 `rail transport oil` Loads, 48 `oil` Generators, and 33 `oil` power Links. The bounded follow-up `evidence/CARBON_LEDGER_OBSERVATION.json` now directly confirms the critical saved-network condition, using read-only xarray static variables with no solver:

- Network SHA256: `4b406321f2cc7c0170e2b48d20cdbddc16e9ffb16e2f37cabc97cb9d8788c8ae`.
- Saved carrier CO2 factors: `oil=0`, `gas=0`, `H2=0`, `co2=-1`.
- 48 oil-supply Generators; no rail-named Links.
- Complete atmosphere-Load listing contains industry oil/coal, shipping, aviation, agriculture and residential/services oil/gas; no rail component. A name search alone would not rule out a differently named aggregate, but the source formulas inspected above and the road/rail audit show no aggregate rail-combustion term.

Thus this retained pre-strip sample **has the source-identified rail oil combustion omission structure**: a rail oil sink, zero oil-carrier emissions factor, and no rail combustion return to the atmosphere. This establishes a ledger-structure defect, not an amount of actual dispatched fossil fuel or quantified omitted emissions. No new emissions estimate is claimed.

The tutorial pre-strip network has no active CO2Limit in the extracted global constraints (only `lv_limit`), so this is a ledger/compliance-readiness finding, **not a demonstrated violation of a solved DEC cap**. Final electricity stripping removes rail oil; the omission matters if Full-SC retains this terminal fuel demand.

**Analytical further risk:** FT can also supply the same rail oil sink. If synthetic fuel carbon is withdrawn upstream from stored CO2 but rail combustion is never returned to atmosphere, the carbon cycle is not closed and capture/negative-emission credits can be misstated. This is a mechanism-level concern, not evidence of a quantified loophole exploited by an existing solve. Record as a system-level accounting check; do not patch or prescribe a new carbon policy in Phase3B-1.

Stop: audit supporting notes only. No Phase3B-2, source fix, demand replacement, model assembly or sensitivity run.
