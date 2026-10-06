# Assembly V1 final coverage decisions

DecisionReference: `GATE4-20261006-FINAL-CLOSURE`; authoritative human request is preserved in `research_inputs/assembly_v1/sources/GATE4_FINAL_HUMAN_REQUEST.txt`. This round implements the three specified choices; it does not retroactively change old acceptance dates or label assumptions observed facts.

## A — compatible blend uncertainty

The ten previously qualified memo relations use `Z=min(P,B)` under `ASSEMBLY_V1_BLEND_MAXIMUM_OVERLAP_BASELINE`. Fossil quantity is `P-Z`, bio quantity is `B`; each uses its own frozen heating value. Other fuels within the same aggregate account remain present. Memo Z never becomes a third demand.

Eighteen affected 2050 accounts are recomputed. PH road gasoline and diesel remain separate parameters within the same affected accounts. PH rail uses its accepted constant-2019 method; the old growth description and stale candidate quantity were mechanically corrected. No new growth or heating values were introduced.

The separate `ASSEMBLY_V1_BLEND_NO_OVERLAP_UPPER` registry sets Z=0. It is a future sensitivity input, not the baseline and not a probability distribution. Its manifest disables posting to the Gate4 network and solver execution.

Baseline registry SHA256: `2e5963b7e8a89cbd6369258ead0ce4e7d807f90d0a38b40013b91ed91fbfc518`.
Upper registry SHA256: `e7a7aa99fdeab07e1d5bd613bfd138f45c7d65dcf08047fb062a0aadbc066060`.

## B — bounded UN reporting coverage

Fifteen exact '..' matches fall outside fixed demand: KH/LA natural-gas final-use accounts; TL coal final-use accounts; BN/KH/LA/TL international marine bunker. Their fields remain null, Posting=false and RequiredPhysical=false. The original table, symbol, legend and source hash remain pinned. This does not prohibit endogenous use or external supply of those carriers, and does not mean source-reported zero.

The 279 required target-demand ownership records now comprise:

| Coverage state | Count |
|---|---:|
| PHYSICAL_ACCEPTED_AND_POSTED | 171 |
| SOURCE_SCOPE_NO_ADDITIONAL_FINAL_LOAD | 89 |
| UNREPORTED_OUTSIDE_ASSEMBLY_V1_FIXED_DEMAND | 15 |
| DEFERRED_BY_FROZEN_RESEARCH_BOUNDARY | 4 |

The physical posting classification records accepted input intent and actual in-memory binding; the completed NetCDF is separately attested in the final network manifest. Embedded electricity remains within accepted A* and is not materialised again. Current input coverage is complete under the chosen V1 boundary; full assembly qualification is now separately validated.

## C — inherited stock boundary

`SOURCE_QUALIFIED_SURVIVING_EXISTING_STOCK_ONLY` preserves745 source records and 187400.4 MW. The frozen electric network's physical inputs were unchanged by the boundary update. 410unqualified inventory records remain in the uncertainty register; GEM and GPD populations are not added together. Five hydro groups/684 MW receive no inherited resource or fabricated inflow. Avion stays NOT_ACTIVE_2050 under its previously approved 25-year proxy. No new capacity is introduced this round.

## Supplemental fixed-account authorization

The newly materialised PH IndustryFinalEnergy:biomass includes Animal waste:2019quantity569.1464 TJ, 158096.222222222 MWh; 2050quantity477866.275143678 MWh under the already accepted561/185.6 growth method. Its five actual node resources passed exclusive fixed-obligation structure tests.

The user then explicitly authorized: “验证通过后纳入外置待核账”. New reference:`GATE4-20261006-ANIMAL-WASTE-FIXED-ACCOUNT`. The pinned decision applies only to this PHindustry source row/account; other countries, source rows or changed quantities fail. It adds no demand or production technology. Price and physical CO2factor remain null; their zero implementation fields carry an external-pending qualification. Any diversion, alternative supply, carbon credit or invalid direction/quantity revokes that qualification.

The full actual network was requalified before and after NetCDFreadback. The prior pending structural proof is retained only as history; `FIXED_ACCOUNT_ADDITIONAL_SCOPE_PROOF.json` and the final network manifest are authoritative.
