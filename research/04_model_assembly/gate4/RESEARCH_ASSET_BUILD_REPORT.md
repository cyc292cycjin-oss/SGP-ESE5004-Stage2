# Gate4 actual stock activation

**FULLSC_NETWORK_NOT_COMPLETE. Gate5=NO. solver_runs=0.**

Source-screened survival and actual components are now different, measured stages:

|Technology|Source-screened survival MW|Actual integrated MW|Not integrated MW|
|---|---:|---:|---:|
|CCGT|42,706.4|42,706.4|0.0|
|Hard Coal|90,375.0|90,375.0|0.0|
|Hydro|48,636.0|0.0|48,636.0|
|Lignite|4,321.0|4,321.0|0.0|
|Oil|2,001.6|2,001.6|0.0|
|Total|188,040.0|139,404.0|48,636.0|

536 original thermal units aggregate after individual survival screening into90 fixed existing Links. Source-unit→node→component capacity was checked after NetCDF readback. New CAPEX is zero for existing stock, annual fixed O&M remains a separate positive input/objective-hook term, and VOM is converted from EUR/MWh-electric to input-side Link cost using the existing efficiency. Fuel costs enter via the independent supply interfaces. No actual objective or system-cost result is reported.

The existing input efficiencies are CCGT0.57, coal0.356, lignite0.33, oil0.35. The processed2030 cost table is the earliest cached compatible electricity O&M source. In particular its CCGT efficiency0.58 is NOT substituted for the corresponding existing-reference efficiency0.57. Source units, parameter year, original currency year and source citations are in EXISTING_PERFORMANCE_OM_SOURCE_MAP.csv. FOM=source investment×source FOM percent/100; the investment level is a conversion base, not charged CAPEX. New2050 candidate parameters remain separate.

Hydro unresolved quantities are reservoir39,349MW, run-of-river6,601MW and pumped storage2,686MW. Raw plant-owned hydro profiles contain168 hourly points (2013-03-01 through2013-03-07), not the required full year. Full-year author-network curves exist but their ownership relative to the accepted surviving unit set remains unqualified. PHS is a different problem: original Duration/StorageCapacity fields are missing; fixed reference max_hours is0 while frozen config.default.yaml:435 specifies6h. Neither0 nor6h has been silently adopted as usable existing energy capacity. The7-row source map presents the available parameters and the separate blockers.

No finite site-resource limit exists for the four conventional conversion technologies in the frozen input model. They enter as fixed stock, without adding candidate capacity. New renewable candidates are unique by node/carrier (438) and retain the same input p_nom_max; no wind/solar survivors have qualified under the accepted age rule. Unknown renewable inventory is retained and prevents full stock qualification. Total-capacity versus additional-potential envelopes and no-duplicate occupancy remain tested.

Multi-unit profile handling is explicit: normalised availability is capacity-weighted; dedicated absolute inflows sum once per unique source; shared inflows enter once per identified group. Ambiguous or duplicated absolute flow across groups is refused. New positive/negative regression tests cover these cases and NetCDF roundtrip.

The electric development NetCDF has100 geographic nodes,2013全年2920个3h时点,90 real fixed existing conversion components and no legacy demand. The carrier development NetCDF now binds152 qualified accounts as1,436 actual Loads, preserving carrier/sector/account/country and annual integrals. Its standalone generation/network boundary remains incomplete. carrier_fragment.json deliberately remains the unbound production recipe, so the final assembler binds once only after all gates pass; it does not merge the partially bound development.nc and then bind again.

Neither development asset is SOURCE_QUALIFIED as a complete baseline.5954.020MW confirmed-existing units still lack commissioning evidence; separately301 parent records /22628.143MW have missing links or capacity discrepancies. Unknown/planned status is retained in raw evidence. These categories are not summed into a fabricated stock total. The full-network export gate remains closed.
