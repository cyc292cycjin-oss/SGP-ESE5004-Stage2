# Gate4 consolidated numerical review

**FULLSC_NETWORK_NOT_COMPLETE. No solver. Return for human review.** Scientific approvals for the2050 single-year boundary, growth factors, Mtoe, EV embedded, RoadReference and bunker obligations remain in force. They are not reopened here.

## 1. Existing stock: one lifetime decision table, separate qualifications

229/229 aggregate-year problems are repaired in preprocessing (148,181.9MW of source parent capacity, **not**2050 survivors). Each raw unit is screened first; compatible survivors are then aggregated by research node, technology, source-qualified performance/profile and resource envelope. No average commissioning year selects a group's survival. No duplicate raw unit ID was found.

There are2,758 matched raw units for2,243 parent rows.1,942 parents reconcile capacity;301 do not fully reconcile/link, representing22,628.143MW of parent capacity. These remain separate, with signed differences and known subunits visible. Verified observed-existing units lacking commissioning years total**5,954.020MW**. Across all statuses, missing-year unit capacity is13,436.520MW, including planned/unknown records; this broader number must not be called missing observed stock.

The compact table has12 technology rows,11 with matched observed stock. Nuclear has no matched observed-existing stock affected; its project status must not be turned into inherited stock by accepting a lifetime.

|Technology|Candidate life (years)|Observed, capacity-reconciled MW|Conditional2050 survivors MW|
|---|---:|---:|---:|
|Biogas|20|2,162.390|0.000|
|CCGT|40|93,027.000|42,706.400|
|Geothermal|15|1,149.000|0.000|
|Hard Coal|45|108,582.000|90,375.000|
|Hydro|100|48,636.000|48,636.000|
|Lignite|45|6,501.000|4,321.000|
|Nuclear|50|0.000|0.000|
|Oil|40|6,933.200|2,001.600|
|Solar|25|24,213.700|0.000|
|Solid Biomass|20|3,632.730|0.000|
|Waste|25|475.500|0.000|
|Wind|25|10,582.100|0.000|

**Decision:** accept or replace source-backed historical-equipment lifetime assumptions by technology. These frozen powerplantmatching defaults are generic fill assumptions, not actual retirement notices or automatic acceptance of new-build2050 lifetime. Candidate results stay conditional. Missing source status/year/capacity is independent of that decision; group unresolved capacity by country/technology, not individual future retirement requests.

**Stock integration dependencies:** accept a compatible raw-to100-node mapping or the documented proxy; qualify existing performance and fixed/variable O&M independently of2050 new equipment; resolve inventory differences/resource occupancy. Code interfaces now implement all these inputs. Unknown values are not zero; no numerical default is promoted to HUMAN_ACCEPTED.

## 2. Mapping choice

The frozen raw→simplified map exists. The exact simplified→100-node map has not been recovered from reviewed cached inputs or tracked author code. The tracked custom map is a two-line template (`Bus,busmap`;`1,NG0 1`). See ASSET_NODE_MAPPING_PROVENANCE.md. A candidate restricted to same country, cached region label and original AC partition yields2,516 candidate raw-bus mappings;6 remain unassigned. All mappings are PENDING. Approval of that proxy is distinct from lifetime approval and changes spatial asset attribution, not the100-node topology.

## 3. Thailand local vintage choice; no repeat retrieval

The already cached same-vintage TH2019 Road1221 bundle contains MO8672, DL14817, AL/ZG1284.804 and BD/ZD1575.2 thousand tonnes (all observation statusA). Old AL1604 and BD1790 differ. The new parent and memo are reconciled **within that same bundle**; old memo is not invented.

Using the existing project commodity-specific NCV conversion and the already approved exact road growth factor374.9/145.2, the affected MO/DL/AL/BD subtotal is274.632227776TWh in2019 and709.088307116TWh in2050. This is a conditional replacement bundle, not a full Thailand transport forecast. The old unresolved display subtotal313.814556TWh differed by39.182328224TWh; it was never an accepted de-duplicated baseline. Each formula, mass quantity, footnote, dataset version and hash is in THAILAND_LOCAL_VINTAGE_UPDATE_CANDIDATE.csv. RawAPI calorific-factor fields are also shown; no silent switch from the project's frozen rounded factors.

**Decision:** adopt or reject this local same-vintage bundle and its explicitly retained conversion convention. Until decided, no TH source row/target/allocation is overwritten. Malaysia's accepted reconciliation and all133 accepted targets/arrays remain unchanged.

## 4. Rail/NEC: three method groups

|Use group|Countries|Source accounts|2019 display TWh|
|---|---|---:|---:|
|RailNonElectric|ID;KH;MM;PH;TH|5|7.028406|
|TransportNEC|SG;TH;TL;VN|4|3.649541|
|OtherNEC|BN;ID;KH;LA;MM;MY;SG|11|18.026616|

**Decision:** one explicit2050 quantity method per use group, with country exceptions if necessary. Constant2019 is a candidate only. The road factor does not cover these uses. PH rail still has oil/biodiesel overlap; its displayed parent value is not a certified additive total. NEC identity is preserved, not reclassified as Road/Industry/Agriculture. Source row ownership remains unique; fuel overlap qualification is a separate check.

## 5. Source coverage and remaining blend originals

The remaining33 combinations are7 missing transactions in cached scope,11 absent source families and15 combinations with known NEC energy but unresolved sector split. None has been dropped or newly excluded. These are distinct evidence/coverage questions. Remaining coverage decisions must say what is outside the research boundary; mathematical Cartesian absence alone cannot justify exclusion or a positive demand.

Only**10 exact memo transactions** remain in the existing request list: ID ZD industry121/road1221/services1235; PH ZD industry121/road1221/rail1222/agriculture1232/services1235 plus ZG road1221; VN ZG road1221.2019 throughout; ZD=SDMX5222, ZG=5212. Existing parents are cached. Reuse prior official HTTP/NoRecordsFound receipts; no identical query was retried this round. Needed: transaction-specific compatible memo observations or explicit source metadata excluding blends, not a legal blending percentage.

## 6. Seven biofuel commodities and two SMR structures

Animal waste, Bagasse, Biodiesel, Biogases, Biogasoline, Charcoal and Fuelwood each retain their own source identity. Review delivered supply cost, calorific basis, physical combustion CO2 and carbon origin by commodity, using BIOFUEL_COMMODITY_PARAMETER_REVIEW.csv. Existing database fuel fields for biomass/biogas or biodiesel crop feedstock are contextual candidates, not automatic finished-fuel prices. Prepared net CO2=0 is not proof of zero physical combustion. Default development zero costs do not approve free supplies. Fixed-obligation resources cannot supply extra power/H2, and liquid biofuels cannot enter a solid biomass pool.

SMR means**steam methane reforming**. SMR: local gas→H2 plus direct atmospheric carbon. SMR-CC: direct atmospheric fraction plus captured CO2; captured transfer is not an automatic permanent-removal credit. Existing physical factors and ports are retained in the actual map. Review mixed-use reporting/policy attribution as two technology structures, not200 node-specific data tasks. `policy_enabled=false`; no guessed power share and no new policy. This round does not relax the existing full-export qualification gate.
