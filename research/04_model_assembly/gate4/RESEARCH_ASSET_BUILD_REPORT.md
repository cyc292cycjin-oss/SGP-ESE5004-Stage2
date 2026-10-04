# Gate4 — production asset build

**FULLSC_NETWORK_NOT_COMPLETE.** No solver was called and Gate5 remains closed. Real2050 development assets have been exported and read back; neither is the complete Research network.

## Actual outputs

| Asset | Actual contents | Qualification |
|---|---|---|
| electric_base_2050_unsolved.nc |100 geographical nodes;2920 snapshots;8760h;438 new renewable candidates;105 AC lines;503 electric Links;196 battery Stores | DEVELOPMENT_ONLY_PENDING_SURVIVOR_QUALIFICATION |
| carrier_fragment_2050_unsolved.nc |100 local node architectures;400 independent fossil sources;2020 Links;474 Stores;11 countries | Instantiated; commodity costs/carbon and mixed policy allocation remain pending |
| Demand allocation |133 actual node/time arrays, including the original131 unchanged arrays | Numeric/allocation evidence only; no production Load materialised |

The four local coupling pathways are electrolysis, SMR, FT and fuel-cell generation. Fixed bio obligations retain source commodity identity, including Biodiesel/Biogasoline; they are not routed into a shared solid-biomass pool. Demand destination interfaces are generated, not supplied manually. Missing demands create no fake Loads. No geological inventory or unapproved production technology is added.

## Electric input construction

The builder creates a fresh PyPSA Network and copies only allowlisted input attributes from the hash-pinned first-horizon author2025 file. It excludes optimised capacities, dispatch, duals and objective; resets new candidate capacities to zero; assigns2050 costs/lifetimes and preserves2013 exogenous profiles. Existing source capacities are kept in the inventory and are not assumed to survive by reading grouped `build_year` or `infinite lifetime`. This development asset is therefore not a greenfield scientific scenario and cannot be used as one.

2050 prepared costs are pinned to SHA `bbcc639010a6775255730278eaa6e21ba56867d0610d3a011adc3eb60d0065f5`. One-year annuity/FOM scaling was checked. The reference wind electricity costs are2030 input costs even in the author2050 file. We therefore recomputed target costs: onshore/solar use2050 entries; offshore uses2050 plant+station cost and the recovered input connection composite. Both submarine and underground connection unit-cost ratios are exactly1 for these pinned tables, so the composite can be retained without guessing sea/land distance. Values and formulae are in the electric manifest. This does not adopt the author's optimised2050 system.

Line impedance is recomputed from source type, length and parallel circuits. Source transmission capacity/topology and the legitimate `lv_limit` volume constraint remain separate from generator retirement. The765/766 engineering repair is preserved and topology regressions pass. Battery efficiency/costs are updated from2050 inputs and196 charger/discharger capacity-pair hooks persist in metadata. No interconnection scenario switch was run.

## Surviving assets

The explicit human method is **ASSEMBLY_V1_2050_SINGLE_YEAR_SURVIVING_ASSETS** with `commissioning_year <=2050< retirement_year`. This closes only the time-boundary decision. We matched2758 raw GEM unit IDs for2243 frozen PPM records:1880 observed-existing identities,45 non-existing project classes,318 unresolved identities. Of the1880,1440 have usable matched commissioning evidence but no accepted retirement/lifetime;440 lack a unique verified commissioning year. Imputed/averaged PPM dates are recorded beside real source evidence and are not substituted.

No surviving stock capacity is yet qualified for activation. This means qualification is incomplete, not that physical stock is zero. Frozen source lifetimes are visible as **unaccepted candidates** in ASSET_SURVIVAL_2050.csv. Full acceptance also needs the source raw-bus→100-node map, retained existing performance and fixed/variable O&M separation, and total-versus-additional resource occupancy. Unknown capacity is retained and summarised by country×technology; it has not been silently deleted or given infinite life. Existing annualised CAPEX is not charged as a new2050 investment.

## Remaining numerical architecture evidence

The fragment has200 actual SMR/CC atmosphere events with mixed-use policy allocation unresolved. Physical port factors are present; the disabled policy is not assigned a guessed power share. Biomass fixed-resource quantities are allocated from qualified obligations, but commodity-specific costs and physical carbon/origin evidence remain pending. PyPSA default zero cost fields in this explicitly blocked development fragment are **not accepted zero scientific costs**. The full assembler rejects both unresolved fragment qualifications and an electric development asset even if someone merely changes the bundle status string.

## Reproduction

`workflow/research_assembly.smk` now has source-asset tracing, actual allocation, actual electric/carrier asset generation and guarded final assembly dependencies. Its source-path config is recorded in evidence/PRODUCTION_SOURCE_PATHS.json. The actual `research_build_production_assets` target was executed with the greedy scheduler; no upstream solve workflow was included. Manifests record input/output SHA256, builder hash, Python/PyPSA versions and Git execution base. The final delivery adds the tested-implementation commit attestation; execution on a dirty research checkout is not misrepresented as code already present in the old HEAD.

The confirmed arrays use fixed-fuel flat-time and input-electricity node proxies; port/airport size weights remain proxies, not measured transport demand. Source→country/account→node→snapshot conservation is checked. Raw input files and earlier delivery history are retained.
