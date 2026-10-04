# Phase4 Gate4 Assembly V1 input freeze — resumed, PARTIAL

This continues the same Gate4. It does not reopen Phase1–3 or overwrite upstream/tutorial inputs. The prior topology repair d13d5976 is retained. No network has been exported and no solver has run.

## Newly closed human decisions

1. BAS approximate RoadParent=`350.5315 Mtoe`, `ASSEMBLY_V1_AEO8_ROAD_PARENT_APPROX`. Exact source/page/context is in the source map. Road EV stays in Astar, with no separate fixed EV Load and no assumed zero. The explicit pathway is `DEFERRED_TO_EV_SENSITIVITY`. This supersedes resume section7 only for Assembly V1; the historical Gate2 contract remains intact.
2. International shipping and aviation: `ASSEMBLY_V1_BUNKER_CONSTANT_2019`, Source2050=`HUMAN_BASELINE_ASSUMPTION`. Verified2019 energy obligations are kept equal in2050. It is `MATERIAL_EXOGENOUS_ASSUMPTION`, `PHASE5_SENSITIVITY_REQUIRED=YES`; not an AEO8/IMO/ICAO forecast or a claim of zero real growth. No future bunker-data hunt remains open.
3. Frozen coal/gas/oil processed model prices are used without reinflation or second HHV/LHV conversion. Each country has the same independent non-binding external quantity interface by human model boundary. No common physical ASEAN fossil bus is licensed.
4. Local biomass supply is capped by accepted fixed country obligations; no360TWh regional pool or surplus expansion resource. No geological storage asset is added without an already accepted source.
5. G4-CARBON-01 is `POST_BUILD_STATIC_VALIDATION_BLOCKER`; it does not prevent numerical preflight but remains mandatory before Gate4 PASS/Gate5.

## Concrete numeric closure

Six original bunker raw files were hash-verified. Selected records were matched by country, transaction, year, unit and quantity; cached2019 totals were checked within0.000051TWh rounding tolerance. Of44 domestic/international observations,22 have a positive matching base with no listed omitted transaction. **17 of these are international obligations** and become numeric accepted2050 targets under the human boundary. Domestic records are not silently covered by the international decision. Existing raw originals and old cached CSVs are unchanged.

| Country | International account | Constant2050 MWh/year |
|---|---|---:|
| BN | InternationalAviationBunker | 1324700.0000 |
| ID | InternationalAviationBunker | 11222100.0000 |
| ID | InternationalShippingBunker | 2607000.000 |
| KH | InternationalAviationBunker | 1907300.0000 |
| LA | InternationalAviationBunker | 443500.0000 |
| MM | InternationalAviationBunker | 882000.000 |
| MM | InternationalShippingBunker | 11900.0000 |
| MY | InternationalAviationBunker | 29654300.0000 |
| MY | InternationalShippingBunker | 4636100.0000 |
| PH | InternationalAviationBunker | 20087600.0000 |
| PH | InternationalShippingBunker | 640800.0000 |
| SG | InternationalShippingBunker | 535341800.0000 |
| TH | InternationalAviationBunker | 55100500.0000 |
| TH | InternationalShippingBunker | 13132200.0000 |
| TL | InternationalAviationBunker | 35800.0000 |
| VN | InternationalAviationBunker | 15643200.0000 |
| VN | InternationalShippingBunker | 2053300.0000 |

Singapore international marine remains exactly535.3418TWh =535341800MWh; its previous float-format tail is removed by exact decimal conversion, not by rescaling demand. FT/synthetic supply may satisfy this accepted liquid-fuel energy obligation under the existing architecture; FT production electricity remains endogenous, outside the exogenous Astar parent.

International base exceptions retained as PENDING: BN/InternationalShippingBunkerFuel: MISSING_BASE_SOURCE; KH/InternationalShippingBunkerFuel: ZERO_WITHOUT_EXACT_SELECTED_RAW; LA/InternationalShippingBunkerFuel: MISSING_BASE_SOURCE; SG/InternationalAviationBunkerFuel: EXACT_SELECTED_CACHE_MATCH_WITH_OMITTED_TRANSACTION_OR_COMMODITY; TL/InternationalShippingBunkerFuel: MISSING_BASE_SOURCE. These are distinct from the **closed2050 growth decision**. Missing data are not zero; Singapore is not redistributed to another country. SG aviation has an omitted aviation-gasoline record in the existing review, so the incomplete cached aggregate is not silently declared a complete verified total.

## Representation and gate accounting

The original275 target rows contained11 Road EV rows; they did **not** contain separate Residential/Services/Industry/Agriculture direct-electricity child Loads. Exactly those11 EV rows become nonnumeric embedded boundaries. There remain264 required physical target rows. Twelve new informational RoadParent rows (ASEAN10 +11 country entries, TL pending) have `Kind=ACCOUNTING`, `Required=false`, and cannot materialise as duplicate Loads. Registry total:588 records.

Numeric accepted target demands: 17. Materialisable target demands: 0; node/time ownership is not yet established on an actual100-node/full-year network. Candidate values are never consumed as accepted values. Empty country/carrier entries remain null.

## Remaining input work

- Outstanding unit convention: `PENDING_HUMAN_CONVENTION`.225.0Mtoe and350.5315Mtoe are retained directly, without inferring final electricity from generation.
- C.3 gives2022→2050 ratios, whereas the fixed project fuel core is2019. The explicit rebasing question remains pending; candidates and year labels are saved. Domestic constant-latest-history rebasing and Agriculture-and-Others scope must stay disclosed.
- Existing2019 fuel source reconciliation is not erased by a future growth method: missing/empty-set zeros, omitted domestic navigation `in` vs `by` transactions, and calorific/industry boundary issues remain visible. No275 independent data searches are proposed.
- Road carrier composition, rail non-electric ownership and TL road evolution remain source/boundary work, not a renewed search for a BAS Road EV split.

The input gate returns `BLOCKED_INPUT_FREEZE` (expected exit2). It rejects a zero/explicit EV row, a dropped required obligation, or an additional RoadParent Load. No fake preflight or actual-network PASS is issued.
