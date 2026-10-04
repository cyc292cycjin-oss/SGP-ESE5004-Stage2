# Phase3B-2 account source review

Evidence class: **verified cached source/code observations**, plus explicitly identified assembly requirements. No source values changed; no new accepted number; no external search, model execution or policy change. This review closes bounded evidence extraction, not numerical acceptance.

The user's frozen representations are taken as given: aggregate road/EV explicit, residual road fuel accounted, rail embedded once, four separate shipping/aviation obligations, endogenous synthetic-fuel supply, FCEV/DSM/V2G/direct marine H2/ammonia/methanol deferred.

## 1. Four-country-account observations for all 11 countries

The following are **the actual cached 2019 annual final-energy totals** in TWh/year, not corrected totals and not accepted first-baseline inputs. `MISSING` preserves blank cells. `0 [no exact row]` means an empty selected subset, not a verified physical zero. The supporting JSON keeps the original text, exact selected rows, separately listed omitted account-related rows, and all future cached projection texts.

|Country|Domestic shipping|International shipping bunker|Domestic aviation|International aviation bunker|
|---|---|---|---|---|
|BN|MISSING|MISSING|0.0 [no exact row]|1.3247|
|ID|2.7947|2.607|33.84|11.2221|
|KH|0.0 [no exact row]|0.0 [no exact row]|0.8465|1.9073|
|LA|MISSING|MISSING|0.0649|0.4435|
|MM|0.0 [no exact row]|0.0119|1.715|0.882|
|MY|0.0 [no exact row]|4.6361|9.0649|29.6543|
|PH|4.3647|0.6408|7.7102|20.0876|
|SG|0.0 [no exact row]|535.3418|0.0 [no exact row]|103.2489|
|TH|0.0 [no exact row]|13.1322|15.8506|55.1005|
|TL|MISSING|MISSING|0.0 [no exact row]|0.0358|
|VN|0.5161|2.0533|10.3023|15.6432|

Domestic transaction labels explicitly identify national domestic consumption; international labels explicitly identify bunker accounts. This is sufficient to keep their account identities separate. It does **not** demonstrate how a future research national final-fuel parent was constructed. Confirm once which direct fuel parent contains domestic transport, and keep international bunker obligations in separate ledgers. Do not add them to ordinary domestic final consumption by default.

All future cached years use inherited DEFAULT growth/efficiency assumptions and missing-to-zero handling. They are traceable engineering projections, not accepted ASEAN transport forecasts. A source-year or target-horizon choice is still needed once in Phase4 accepted-input assembly; it does not require a vessel/aircraft model.

## 2. Exact domestic shipping omission: source says `in`, extractor selects `by`

This is a concrete extension of the Phase3B1 generic exact-match coverage warning. The four raw records were already present in the Phase3B1 JSON evidence pool, but the conversion comparison deliberately reproduced the frozen extractor, and the specific `in`/`by` omission was not identified in the existing Phase3B1 Markdown. Thus no new download uncovered this: it is a bounded reclassification of retained evidence.

Frozen U `build_base_energy_totals.py:287–291` selects `Transaction == "Consumption by domestic navigation"`. The four rows below say **Consumption in domestic navigation**. They therefore do not reach the cached DomesticShippingFuel subtotal. They do not change the InternationalShippingBunkerFuel account.

|Country|Cached domestic TWh|Raw fuel|Raw quantity (thousand metric tons)|Diagnostic TWh using frozen factor|Raw file line|
|---|---|---|---|---|---|
|KH|0.0|Gas Oil/ Diesel Oil|58.442|0.69779748|15124|
|ID|2.7947|Gas Oil/ Diesel Oil|719.982|8.59658508|43709|
|PH|4.3647|Gas Oil/ Diesel Oil|539.6|6.442824|74182|
|SG|0.0|Gas Oil/ Diesel Oil|76|0.90744|82779|

Raw file: `/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/demand/unsd/data/UNdata_Export_20250502_110559984.txt`. SHA256 `1c2952a5f87bfcdb0eef1af6b6c774e741a99e5b72c5ced91a585d6efe9be50a`. Every raw quantity and its footnote is retained in `COUNTRY_ACCOUNT_OBSERVATIONS.json`. Frozen source snapshot SHA256 `4405164ab303d3be800a5dca58978d1e403d75cbe70d8d8381178a675de9fefc`; Git identity `a3616a68ee44592af6527ca9024a90f1956646ae`.

The diagnostic conversion is raw thousand metric tons × existing diesel factor 0.01194 TWh/thousand metric tons. It demonstrates omitted positive energy; **it is not an authorized replacement or a new adopted domestic total**. KH/SG become zero because no other selected domestic row survives. ID/PH already have positive subtotals, but still omit these diesel rows. A correction must reconcile exact raw transactions/commodities before accepting country obligations; do not simply sum all keyword hits or patch cached CSV values.

This belongs to the same accepted-input/four-account assembly gate as missing quantities and carrier units. It does not create a new transport research phase. Port-allocation engineering tests alone cannot close this upstream data-selection omission.

## 3. Aviation pool is not a summable demand dataset

The Phase3B1 raw pool used keywords in `Commodity - Transaction`, so `Aviation gasoline - Imports`, exports, stock changes, production, total supply, final consumption and sector subtotals also appear. They are **source evidence**, not separate additive aviation fuel obligations. Account selection must use the transaction, not commodity-name keywords alone. Parent/subtotal rows must not be added to specific domestic/bunker rows.

Frozen extraction selects only Kerosene-type Jet Fuel, then exact domestic/by and international bunker transactions. Existing additional account-related Aviation gasoline records are shown below solely to distinguish deliberate kerosene scope from whole-aviation-fuel coverage; no imports or balance aggregates are included.

|Country|Transaction|Quantity (thousand metric tons)|Diagnostic TWh|Source file / line|
|---|---|---|---|---|
|ID|Consumption in domestic aviation|1.753|0.0215619|UNdata_Export_20250502_110251099.txt:10654|
|LA|Consumption in domestic aviation|7.4|0.09102|UNdata_Export_20250502_110251099.txt:12995|
|MM|Consumption in domestic aviation|0|0|UNdata_Export_20250502_110251099.txt:15407|
|PH|Consumption in domestic aviation|5|0.0615|UNdata_Export_20250502_110251099.txt:18347|
|SG|International aviation bunkers|0.052|0.0006396|UNdata_Export_20250502_110251099.txt:20343|
|TL|Consumption in domestic aviation|0.0145985401459854|0.0001795620438|UNdata_Export_20250502_110251099.txt:22474|

Retain an explicit commodity-coverage declaration for the accepted aviation obligation. The user allows a kerosene/fuel obligation; complete aircraft classes are unnecessary. These small separate rows are not automatically system-level blockers or grounds for expanding research. If omitted from an agreed kerosene-only scope, record that scope; do not assert the subtotal measures every aviation fuel. Row hashes and raw text remain in the supporting JSON.

## 4. Road gas and biomass cannot be silently called residual oil

All numbers below are retained cached final-energy TWh/year. The road total is not a pure liquid-petroleum account. A zero electricity column still represents no cached Electricity-road observation, not verified absence of baseline EV electricity.

|Country|Road total|Road electricity|Road gas|Road biomass|Road oil|
|---|---|---|---|---|---|
|BN|5.134|0.0|0.0|0.0|5.134|
|ID|255.6664|0.0|0.7914|47.1449|207.7302|
|KH|20.3452|0.0|0.0|0.0|20.3452|
|LA|9.5947|0.0|0.0|0.0|9.5947|
|MM|22.499|0.0|2.2556|0.0|20.2434|
|MY|263.4454|0.0|1.2726|7.5392|254.6336|
|PH|135.7023|0.0|0.0|8.2439|127.4584|
|SG|22.1433|0.0|0.0|0.0|22.1433|
|TH|348.9357|0.0|21.6892|30.234|297.0126|
|TL|0.4247|0.0|0.0|0.0|0.4247|
|VN|78.9025|0.0|0.0|0.9082|77.9943|

The frozen research road energy identity can use one common final-energy basis, but the residual account must preserve known gas/biomass/oil identities or document an explicit accepted aggregation. In particular, assigning every residual MWh to oil silently changes carbon factors and fossil/synthetic fuel supply. Road gas is positive for ID/MM/MY/TH; biomass is positive for ID/MY/PH/TH/VN. These are already-known aggregate carrier quantities; no new vehicle-class data are required.

The cached future road gas/biomass/oil/electricity columns have been zeroed because their columns are absent from CAGR inputs before `fillna(0)`. They are unusable evidence that those fuels disappeared. Reuse a separately accepted energy parent, energy-share path and residual-carrier accounting; do not infer them from the all-zero future subcolumns.

## 5. Processed port/airport weights: bounded checks

The following checks read only the already archived processed CSVs. Fractions are finite/nonnegative, and sums equal one within 1e-12 floating arithmetic tolerance where rows exist. This is numerical verification, not a materiality threshold. No duplicate location IDs were found within these ASEAN country subsets.

|Country|Port count|Port fraction sum|Airport count|Airport fraction sum|
|---|---|---|---|---|
|BN|2|1|1|1|
|ID|27|1|69|1|
|KH|1|1|5|1|
|LA|0|NO ROW|4|1|
|MM|5|1|17|1|
|MY|17|1|26|1|
|PH|14|1|39|1|
|SG|4|1|2|1|
|TH|6|1|33|1|
|TL|1|1|4|1|
|VN|7|1|20|1|

- `research/02_sector_coupling/transport/phase3b1/evidence/cached_inputs/resources/baseline-aims-3H-tutorial/ports.csv`: SHA256 `a54d323763faf5419cbc4095aaec8dca1670380d39e72ef98436b4ec89c7f28c`.
- `research/02_sector_coupling/transport/phase3b1/evidence/cached_inputs/resources/baseline-aims-3H-tutorial/airports.csv`: SHA256 `51a80a016c635fbf60665c6262abc8d334febffa79d1bf291952ff2ca400bf6e`.

These checks do not prove node-assignment coverage or national annual energy conservation after index alignment and snapshot weighting. That remains the purpose of the separate shipping-allocation candidate test and Phase4 integration checks. LA has no cached port rows and missing navigation inputs; neither can be converted to zero or invented port weights. The fallback branch must either use a consciously accepted alternative country allocation or fail clearly for a positive obligation with no valid location.

Port cache lineage remains the official NGA viewer user export of 2026-09-29 for tutorial engineering only; exact paper provenance is unverified. Airport upstream raw-version identity is still not recovered, but processed hashes freeze the candidate weights. These facts limit source acceptance; they do not require reopening location microdetail if a transparent country allocation is accepted.

## 6. Minimum remaining accepted-input gaps, without another deep-dive phase

1. **Exactly-once parent compatibility:** one accepted A* country/year/geography basis with a checkable baseline EV/rail electricity component; a direct fuel parent that demonstrably retains embedded rail fuel once. Cached road-electricity zeros cannot certify zero subtraction.
2. **Road energy and share contract:** accepted annual road final-energy parent, explicitly energy-based EV share/path, and residual gas/biomass/oil treatment on the same basis. A vehicle share or kWh/km default cannot substitute for an energy share. No passenger/freight split is needed.
3. **Four accepted obligations:** choose source/target year and approve the country domestic shipping / international bunker / domestic aviation / international bunker ledgers, retaining missing flags, correcting the exact domestic-navigation label omission through source-controlled validation, and declaring aviation commodity scope. Existing default projections and conversion factors remain unaccepted until recorded. Do not ask for 11-country fleet microdata.
4. **Assembly checks rather than new source hunts:** apply reviewed allocation validation, country annual/time-weight conservation, no duplicate EV/rail parent energy, and separate full-system reporting from the power-only policy cap. Location fraction checks above narrow this work but do not replace it.

These are minimal Phase4 input acceptance and integration gates. Model source selection, years/units and scientific approval remain separate statuses. This evidence review makes no choice of accepted numbers, no new policy, no formal solve and no Transport Phase3B-3 proposal.
