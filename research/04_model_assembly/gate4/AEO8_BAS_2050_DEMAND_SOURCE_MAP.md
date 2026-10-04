# AEO8 BAS 2050 demand source map — Gate4 resume

Authoritative resume: research/full-sc-baseline @ 4d944d67809d699e94e50f2b41d16b3679c65a82. Source recovery uses the existing official PDF and November2024 corrigendum, not a newly substituted report. [Official landing](https://www.aseanenergy.org/publications/the-8th-asean-energy-outlook/). Cached PDF SHA256 `48c2a81913ed785cb0e14a55e332ea7bc87f912f7fabfbc8c654e09b66b11c06`. The page images for PDF48/65/66/183/184 were rendered and reviewed; numeric table cells are read from source text and checked against the page, not inferred from chart pixels.

## Direct source observations

All regional values below have ASEAN10 coverage; Timor-Leste is outside these totals.

| Account | 2022 | 2050 BAS | Unit | Exact location / definition |
|---|---:|---:|---|---|
| Final electricity | 93.7 | 225.0 | Mtoe | C.2, printed181 / PDF183, Electricity row; final energy, NOT generation |
| Residential | 63.0 | 68.2 | Mtoe | C.3, printed182 / PDF184; total sector final energy |
| Commercial / Services | 29.5 | 75.9 | Mtoe | C.3, printed182 / PDF184 |
| Industry | 185.6 | 561.0 | Mtoe | C.3, printed182 / PDF184 |
| Agriculture and Others | 8.8 | 27.8 | Mtoe | C.3, printed182 / PDF184; broader than pure agriculture |
| Transport | 145.2 | 374.9 | Mtoe | C.3, printed182 / PDF184 and §3.1.2 printed63 / PDF65 |

The report's approximate93.5% road proportion is on printed64 / PDF66, adjacent to the ATS discussion and Figure3.8. **Human decision**, rather than an independently recovered BAS road table, permits applying it to BAS: `374.9×0.935 = 350.5315 Mtoe`, method `ASSEMBLY_V1_AEO8_ROAD_PARENT_APPROX`. Retain exact multiplication in the ledger;350.5 is only a displayed approximation.

Printed63 / PDF65 reports0.2% electricity for the whole BAS Transport sector. It supplies the human materiality rationale; it is **not** multiplied by RoadParent, allocated to countries, or used as an exclusive Road EV share. ATS4.3%, vehicle shares and the later BAU/OPT exercise are not used.

§2.1.1, printed46 / PDF48, holds rail, domestic air and inland waterway consumption at latest historical levels. The report base is2022, whereas project fuel observations are2019. A constant2019 domestic candidate therefore still needs an explicitly recorded rebase; it is not automatically an exact AEO8 quantity. Likewise, using C.3 ratios on2019 observations preserves the2019 vector but does not recover missing2019 AEO8 totals. Agriculture and Others is only a candidate proxy for the narrower agriculture fuel core.

No compatible country-level2050 international bunker trajectory was recovered. That search is CLOSED by the separate human constant2019 boundary; no global IMO/ICAO growth is imported.

## Units and source limits

The report supplies Mtoe; its own conversion metadata was not recovered. [INSEE's standard toe definition](https://www.insee.fr/en/metadonnees/definition/c1355) gives41.868GJ/toe, equivalent to11.63TWh/Mtoe. Current explicit project convention status: `PENDING_HUMAN_CONVENTION`; accepted value: `None`. Candidate national absolute quantities remain visible in Mtoe until the outstanding convention decision is received. Do not confuse this with the traditional42.6216TJ/1000TOE in the [UNSD2014 conversion appendix](https://unstats.un.org/unsd/energy/balance/2014/05.pdf). Its liquid fuel factors are NCV; natural-gas TJ is described on GCV with a0.90 factor. The legacy generic TJ/3600 treatment requires account-specific thermal-basis review; no automatic data correction or second conversion of frozen model prices was applied.

The inspected corrigendum does not list C.2/C.3 as replaced tables. This is a bounded observation, not a claim that all report versions coincide. Full source observations and report hashes are pinned in `research_inputs/assembly_v1/sources/AEO8_BAS_SOURCE_VALUES.json`.

## Derived national allocations

2019 ASEAN10 Astar denominator: `995248426.888889000` MWh. Exact Decimal arithmetic is preserved in `evidence/resume/TARGET_CONSTRUCTION.json`; the displayed Mtoe column below is rounded to9 decimals. ASEAN10 sums to225.0Mtoe within Decimal rounding. TL uses the separately authorized aggregate growth fallback and is not added into that regional total.

| Country | Verified2019 Astar MWh | Candidate2050 Mtoe | Accepted2050 MWh |
|---|---:|---:|---:|
| BN | 3906135.000 | 0.883076377 | PENDING_UNIT |
| ID | 258092000 | 58.347944524 | PENDING_UNIT |
| KH | 10191090.00 | 2.303942602 | PENDING_UNIT |
| LA | 6595540.00 | 1.491081483 | PENDING_UNIT |
| MM | 18681010.00 | 4.223294543 | PENDING_UNIT |
| MY | 158709264.000 | 35.880071181 | PENDING_UNIT |
| PH | 87118300.0 | 19.695200686 | PENDING_UNIT |
| SG | 51730200.0 | 11.694864001 | PENDING_UNIT |
| TH | 193175999.000 | 43.672111003 | PENDING_UNIT |
| TL | 384247.000 | 0.086868336 | PENDING_UNIT |
| VN | 207048888.888889000 | 46.808413599 | PENDING_UNIT |

Road denominator: `1162.3685` TWh, the existing2019 ownership observations for ASEAN10. Country allocations are of the approximate road parent, not extra Loads. There is no independent TL road projection decision; it remains pending, without changing ASEAN10.

| Country | Approximate RoadParent2050 Mtoe |
|---|---:|
| ASEAN10 | 350.531500000 |
| BN | 1.548242852 |
| ID | 77.100443355 |
| KH | 6.135432502 |
| LA | 2.893440921 |
| MM | 6.784946614 |
| MY | 79.446329826 |
| PH | 40.923279298 |
| SG | 6.677679380 |
| TH | 105.227347717 |
| TL | PENDING_TL_METHOD |
| VN | 23.794357537 |

Road EV remains `EMBEDDED_IN_ASTAR / NOT_SEPARATELY_MATERIALISED`, with `Value=null`, not zero. Therefore no exact independent `R=EV+fuel` numerical closure is claimed yet. Missing carrier shares are not manufactured or renormalised away; compatible2019 carrier calculations are explicitly candidates, and unresolved residual remains unclassified. Shipping, aviation and rail are outside RoadParent.
