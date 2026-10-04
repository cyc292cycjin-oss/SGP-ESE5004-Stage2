# Cached transport demand evidence (read-only)

Evidence class: direct cache inspection and analytical conversion check; no new accepted input. Cache is the original tutorial checkout, **not** proof that these data entered a sector-coupled solved ASEAN network. Frozen U source SHA is `a3616a68ee44592af6527ca9024a90f1956646ae`.

## Scope and exact evidence

`CACHED_DEMAND_EVIDENCE.json` records every inspected file SHA256, copied small-file path, original raw row and physical line end, year, unit, quantity, footnotes, commodity, transformation factor, and country/mode coverage. `inspect_cached_demand.py` only reads the explicit UNSD input directory and named small inputs; no download, model imports, workflow or solver. All amounts below are cached **annual final-energy TWh**, not passenger-km/tonne-km/vehicle-km or accepted useful mobility service.

52 cached UNSD TXT exports named `UNdata_Export_20250502_*` were streamed; 123 ASEAN 2019 transport records were retained. File names give an export-date clue, not evidence that 2025 is the observation year: all extracted observations are 2019. The cached raw archive, raw files and original link workbook have separate hashes. Source links/download paths: frozen U `build_base_energy_totals.py:366–455` reads the path workbook, can retrieve its URLs, or falls back to Google Drive archive `1VUV0X-tTQECi2pHdE5EWXjPI2yeCdk6F`; the presence of an archive does not prove which historical download branch ran.

## Base transport accounts

The table deliberately preserves missing cells. A displayed 0 can be an empty-commodity-subset sum and is not automatically an observed national zero.

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

|Country|Rail total|Rail electricity|Domestic navigation|International navigation|Domestic aviation|International aviation|
|---|---|---|---|---|---|---|
|BN|MISSING|MISSING|MISSING|MISSING|0.0|1.3247|
|ID|2.7617|0.278|2.7947|2.607|33.84|11.2221|
|KH|2.6984|0.0|0.0|0.0|0.8465|1.9073|
|LA|MISSING|MISSING|MISSING|MISSING|0.0649|0.4435|
|MM|0.9671|0.0|0.0|0.0119|1.715|0.882|
|MY|0.4778|0.4778|0.0|4.6361|9.0649|29.6543|
|PH|0.1256|0.1062|4.3647|0.6408|7.7102|20.0876|
|SG|3.0193|3.0193|0.0|535.3418|0.0|103.2489|
|TH|1.0747|0.215|0.0|13.1322|15.8506|55.1005|
|TL|MISSING|MISSING|MISSING|MISSING|0.0|0.0358|
|VN|MISSING|MISSING|0.5161|2.0533|10.3023|15.6432|

## Source units and aggregation

- Source electricity units `Kilowatt-hours, million` become TWh by /1000; `Terajoules` by /3600. Cached transport mass records `Metric tons,  thousand` use the frozen `_helpers.get_conv_factors("industry")` dictionary. All 123 retained rows have a supported conversion. Fuel-factor provenance points to the UN energy balance methodology in code; HHV/LHV acceptance is not established merely by that citation.
- `build_base_energy_totals.py:203–222`: road is the sum of final energy across available commodities; no passenger/freight split. Road electricity is a filtered `Electricity` sum.
- `:246–259`: rail total uses only diesel, biodiesel and electricity; electricity is a subset, not an additional independent total. Do not add `total rail + electricity rail` as separate full demands.
- `:261–290`: aviation uses Kerosene-type Jet Fuel only and distinguishes domestic consumption from international aviation bunkers. Navigation uses all selected commodities and distinguishes domestic navigation from international marine bunkers. Bunkers are a separate named transaction; their assignment to a research national final-energy boundary remains a boundary decision.
- An independent numerical check using NumPy scalar summation/rounding to match pandas-derived rounding reproduces every nonblank cached base cell (107 of 121 transport cells). No model was executed. This verifies consistency with the present cache, not scientific acceptance of factors, completeness, or paper provenance.

## Missing and zero are materially different

1. All 11 `road electricity` cells are `0.0`, but **there is no Electricity-road record for any of the 11 countries in the cached 2019 raw data**. The road-sector subset contains non-electric rows, then `.sum()` over its empty electricity subset returns zero. Therefore these cells cannot establish that historical EV electricity is zero or justify an EV subtraction of zero from A*.
2. Rail electricity records exist for ID, MY, PH, SG and TH. KH and MM have rail fuel rows but no electricity rail rows: their rail-electricity 0 is another empty-subset sum. BN, LA, TL and VN have no rail rows and base rail fields are missing.
3. There are 14 blank base transport cells: both rail fields for BN/LA/TL/VN (8) and domestic/international navigation for BN/LA/TL (6). All become `0.0` in the cached 2030/2040/2050 tables. `prepare_energy_totals.py:296` explicitly performs `fillna(0)` on output. This is missing-to-zero engineering behavior, not verification of absent demand.
4. In addition, growth and efficiency input tables omit `road electricity`, `road gas`, `road biomass`, and `road oil` columns. Column-aligned multiplication (`prepare_energy_totals.py:108–112`) creates missing values for these subaccounts; all four become zero in future output even when base gas/biomass/oil are positive. Thus these future columns are not valid historical account evidence and do not show that future road fuel demand disappeared; the separate total road remains.

## Projection defaults

Every ASEAN country is absent from both growth and efficiency CAGR country indices and therefore inherits `DEFAULT`; the fuel-shares table likewise has no ASEAN rows. This is directly demonstrated in `cagr` JSON. Do not label the generic default as an ASEAN forecast, or assume a European geographic calibration that the table itself does not prove. The actual geographic calibration is unverified.

`prepare_energy_totals.py:260–289` overwrites road and navigation totals with share-weighted technology-specific efficiency projections times growth. Accordingly, the presence of generic `total international navigation = 0.2742` in the efficiency CAGR file does **not** mean the final navigation value uses that rate: the later override uses `total navigation oil` / `total navigation hydrogen`.

|Default parameter|Growth CAGR|Efficiency CAGR|
|---|---|---|
|total road|0.01390|NO COLUMN|
|total rail|0.04940|-0.004951|
|electricity rail|0.03982|-0.002146|
|total domestic aviation|0.03715|0.0|
|total international aviation|0.02156|0.0|
|total domestic navigation|0.006453|-0.01786|
|total international navigation|0.02504|0.2742|
|total road ev|NO COLUMN|-0.06140|
|total road fcev|NO COLUMN|-0.02652|
|total road ice|NO COLUMN|0.0|
|total navigation oil|NO COLUMN|-0.001062|
|total navigation hydrogen|NO COLUMN|-0.008517|

## Vehicle and location caches

- `resources/baseline-aims-3H-tutorial/transport_data.csv` does **not** exist. This bounds the evidence: it does not prove no other checkout generated such a file. The inspected original tutorial cache does not contain the prepared vehicle input.
- `data/temp_hard_coded/transport_data.csv` exists, SHA256 `360a8812c03e42c823e5a45665e9dd9a802228594b1dc79ea095e5d87612d3b7`, 183 rows including all 11 countries. `number cars` and `average fuel efficiency` have no per-row source/year metadata. Source code describes WHO registered vehicles plus Wikipedia completion, World Bank fuel data and fallback. These cached values must not be presented as verified ASEAN passenger-car stock or country-specific vintage; the current units/source semantics need their producer trace. This audit performs no external refresh.
- Tutorial ports have explicit engineering provenance: user export from the official NGA WPI viewer on 2026-09-29, then field mapping from GDB. Raw ZIP SHA256 `34461849e406f2b1fc92009dd928e2f35785ddf1549971c397b4eddfc873e224`; converted full CSV SHA256 `c86b548f5a214649f2f2b16e700986824ee8dbd9d6451a5195514fc7846d7d19`. The copied provenance says **tutorial engineering test only; not verified as author paper input**. Current upstream's monthly WPI URL must not be substituted for this actual cache lineage.
- Tutorial `ports.csv` SHA256 `a54d323763faf5419cbc4095aaec8dca1670380d39e72ef98436b4ec89c7f28c` and `airports.csv` SHA256 `51a80a016c635fbf60665c6262abc8d334febffa79d1bf291952ff2ca400bf6e` are retained as small copies. ASEAN country row counts and actual rows are in JSON. No Lao port row is observed; that should be resolved against selected bunker/domain geography, not auto-filled.
- Airport producer points to live OurAirports airports/runways files, but the exact raw source version/archive was not located in this bounded cache inspection. The processed file hash freezes what exists, not its upstream release. `data/custom/airports.csv` is also copied and hashed; its presence alone is not proof that the effective tutorial switch selected it.

## Review implications

Verified cache gaps that matter: missing-versus-zero transport electricity, loss of future road subaccounts, generic projections, and large separately reported international bunker accounts. The existing cached inputs support a bounded transport audit, not an accepted new demand scenario. National EV stock microdetail is not required merely to acknowledge these accounting issues. No values were patched and no missing demands were constructed.
