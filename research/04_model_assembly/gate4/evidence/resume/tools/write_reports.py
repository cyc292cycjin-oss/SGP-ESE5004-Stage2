"""Write evidence-bounded resume reports; never label unrun network checks PASS."""
from pathlib import Path
import json,hashlib,shutil,csv
from decimal import Decimal as D
W=Path(__file__).resolve().parent; S=W/'stage'; G=S/'research/04_model_assembly/gate4'; GE=G/'evidence/resume'; E=W/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def text(p,x):p.write_text(x.strip()+'\n',encoding='utf-8')
r=read(S/'research_inputs/assembly_v1/registry.json'); construction=read(E/'TARGET_CONSTRUCTION.json'); decision=read(W/'resume_decisions.json'); pre=read(E/'ASSEMBLY_PREFLIGHT.json')
proof=read(E/'BUNKER_BASE_VERIFICATION.json'); receipt=read(E/'TEST_RECEIPTS.json')
for p in E.iterdir():
 if p.is_file() and (p.name.endswith('.log') or p.name in ['TEST_RECEIPTS.json','ASSEMBLY_PREFLIGHT.json','GATE3_CONFIG_REGRESSION.json','PRESERVATION_GUARD.json','CSV_EXPORT_RECEIPT.json']):shutil.copyfile(p,GE/p.name)
if (E/'gate3_regression').exists():shutil.copytree(E/'gate3_regression',GE/'gate3_regression',dirs_exist_ok=True)
source=read(S/'research_inputs/assembly_v1/sources/AEO8_BAS_SOURCE_VALUES.json')
unit=decision['Mtoe_to_TWh']
atable='\n'.join('| '+x['Country']+' | '+x['Base2019MWh']+' | '+format(D(x['Candidate2050Mtoe']),'.9f')+' | '+(x['Value2050MWh'] or 'PENDING_UNIT')+' |' for x in construction['Astar'])
rtable='\n'.join('| '+x['Country']+' | '+(x['RoadParent2050Mtoe'] and format(D(x['RoadParent2050Mtoe']),'.9f') or 'PENDING_TL_METHOD')+' |' for x in construction['RoadParent'])
btable='\n'.join('| '+x['Country']+' | '+x['Account']+' | '+x['Value2050MWh']+' |' for x in construction['BunkerAccepted'])
pending_b=[x for x in proof['records'] if x['account'].startswith('International') and not x['eligible_verified_2019_obligation']]
pending_b_text='; '.join(x['country']+'/'+x['account']+': '+x['source_status'] for x in pending_b)
text(G/'AEO8_BAS_2050_DEMAND_SOURCE_MAP.md',f'''
# AEO8 BAS 2050 demand source map — Gate4 resume

Authoritative resume: research/full-sc-baseline @ 4d944d67809d699e94e50f2b41d16b3679c65a82. Source recovery uses the existing official PDF and November2024 corrigendum, not a newly substituted report. [Official landing](https://www.aseanenergy.org/publications/the-8th-asean-energy-outlook/). Cached PDF SHA256 `{source['pdf_sha256']}`. The page images for PDF48/65/66/183/184 were rendered and reviewed; numeric table cells are read from source text and checked against the page, not inferred from chart pixels.

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

The report supplies Mtoe; its own conversion metadata was not recovered. [INSEE's standard toe definition](https://www.insee.fr/en/metadonnees/definition/c1355) gives41.868GJ/toe, equivalent to11.63TWh/Mtoe. Current explicit project convention status: `{unit['status']}`; accepted value: `{unit['value']}`. Candidate national absolute quantities remain visible in Mtoe until the outstanding convention decision is received. Do not confuse this with the traditional42.6216TJ/1000TOE in the [UNSD2014 conversion appendix](https://unstats.un.org/unsd/energy/balance/2014/05.pdf). Its liquid fuel factors are NCV; natural-gas TJ is described on GCV with a0.90 factor. The legacy generic TJ/3600 treatment requires account-specific thermal-basis review; no automatic data correction or second conversion of frozen model prices was applied.

The inspected corrigendum does not list C.2/C.3 as replaced tables. This is a bounded observation, not a claim that all report versions coincide. Full source observations and report hashes are pinned in `research_inputs/assembly_v1/sources/AEO8_BAS_SOURCE_VALUES.json`.

## Derived national allocations

2019 ASEAN10 Astar denominator: `{construction['Astar2019ASEAN10MWh']}` MWh. Exact Decimal arithmetic is preserved in `evidence/resume/TARGET_CONSTRUCTION.json`; the displayed Mtoe column below is rounded to9 decimals. ASEAN10 sums to225.0Mtoe within Decimal rounding. TL uses the separately authorized aggregate growth fallback and is not added into that regional total.

| Country | Verified2019 Astar MWh | Candidate2050 Mtoe | Accepted2050 MWh |
|---|---:|---:|---:|
{atable}

Road denominator: `{construction['Road2019ASEAN10TWh']}` TWh, the existing2019 ownership observations for ASEAN10. Country allocations are of the approximate road parent, not extra Loads. There is no independent TL road projection decision; it remains pending, without changing ASEAN10.

| Country | Approximate RoadParent2050 Mtoe |
|---|---:|
{rtable}

Road EV remains `EMBEDDED_IN_ASTAR / NOT_SEPARATELY_MATERIALISED`, with `Value=null`, not zero. Therefore no exact independent `R=EV+fuel` numerical closure is claimed yet. Missing carrier shares are not manufactured or renormalised away; compatible2019 carrier calculations are explicitly candidates, and unresolved residual remains unclassified. Shipping, aviation and rail are outside RoadParent.
''')
text(G/'PHASE4_ASSEMBLY_INPUT_FREEZE.md',f'''
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
{btable}

Singapore international marine remains exactly535.3418TWh =535341800MWh; its previous float-format tail is removed by exact decimal conversion, not by rescaling demand. FT/synthetic supply may satisfy this accepted liquid-fuel energy obligation under the existing architecture; FT production electricity remains endogenous, outside the exogenous Astar parent.

International base exceptions retained as PENDING: {pending_b_text}. These are distinct from the **closed2050 growth decision**. Missing data are not zero; Singapore is not redistributed to another country. SG aviation has an omitted aviation-gasoline record in the existing review, so the incomplete cached aggregate is not silently declared a complete verified total.

## Representation and gate accounting

The original275 target rows contained11 Road EV rows; they did **not** contain separate Residential/Services/Industry/Agriculture direct-electricity child Loads. Exactly those11 EV rows become nonnumeric embedded boundaries. There remain264 required physical target rows. Twelve new informational RoadParent rows (ASEAN10 +11 country entries, TL pending) have `Kind=ACCOUNTING`, `Required=false`, and cannot materialise as duplicate Loads. Registry total:588 records.

Numeric accepted target demands: {pre['numeric_accepted_target_demands']}. Materialisable target demands: {pre['accepted_target_demands']}; node/time ownership is not yet established on an actual100-node/full-year network. Candidate values are never consumed as accepted values. Empty country/carrier entries remain null.

## Remaining input work

- Outstanding unit convention: `{unit['status']}`.225.0Mtoe and350.5315Mtoe are retained directly, without inferring final electricity from generation.
- C.3 gives2022→2050 ratios, whereas the fixed project fuel core is2019. The explicit rebasing question remains pending; candidates and year labels are saved. Domestic constant-latest-history rebasing and Agriculture-and-Others scope must stay disclosed.
- Existing2019 fuel source reconciliation is not erased by a future growth method: missing/empty-set zeros, omitted domestic navigation `in` vs `by` transactions, and calorific/industry boundary issues remain visible. No275 independent data searches are proposed.
- Road carrier composition, rail non-electric ownership and TL road evolution remain source/boundary work, not a renewed search for a BAS Road EV split.

The input gate returns `BLOCKED_INPUT_FREEZE` (expected exit2). It rejects a zero/explicit EV row, a dropped required obligation, or an additional RoadParent Load. No fake preflight or actual-network PASS is issued.
''')
text(G/'PHASE4_GATE4_TEST_REPORT.md','''
# Gate4 resume test report

Tests run in the existing WSL pypsa-earth environment (Python3.11.13/PyPSA0.30.3), no optimizer. Exact commands, exit codes and log hashes: `evidence/resume/TEST_RECEIPTS.json`.

| Suite | Result | Scope |
|---|---|---|
| Assembly input tests |17 PASS| Includes rejecting explicit/zero EV, dropped missing obligations, duplicate RoadParent Load; SG constant bunker and post-build carbon ordering |
| Assembly preflight | BLOCKED_INPUT_FREEZE, expected exit2 | Correct refusal before network construction; not a readiness PASS |
| Gate1 static |20 PASS| Research contract/config guards |
| Gate2 demand/accounting |70 PASS| Preserved historical accounting contract |
| Gate3 carrier/carbon |60 PASS| Synthetic/static architecture, not actual assembled network |
| Gate3 config |PASS| Existing carrier configuration invariants |
| Topology regression |9 PASS| Existing single-row repair retained; no topology reinvestigation |
| Buildings / Shipping full regression |NOT_RERUN_UNCHANGED| Production builders and historical source capsules unchanged |
| Actual-network tests |NOT_RUN_NO_NETWORK| No component inventory, finite Load/conservation, interconnector set or carbon-attribution claim |

Gate3 logs retain a PROJ database startup warning from the existing environment. Its60 bounded tests passed, but this is not a geographical runtime certification. The first native Windows test attempt also encountered sandbox temporary-directory permissions in the hash-tamper fixture; the full authoritative17-test suite subsequently passed in WSL without altering its assertions.

The CSV export roundtrip and error scan passed. `PRESERVATION_GUARD.json` verifies unchanged Gate2 input capsules, upstream prepare_sector_network.py and other untouched contracts. A source-qualified number is distinct from a validated100-cluster, full-year3h allocation.
''')
statuses={'ASSEMBLY_V1_2050_INPUTS':'PARTIAL','TOPOLOGY_REFERENTIAL_INTEGRITY':'PASS','FIRST_FULLSC_UNSOLVED_NETWORK_BUILT':'NO','SOLVER_RUNS_EXECUTED':0,'ACTUAL_NETWORK_FINITE_VALUES':'NOT_RUN_NO_NETWORK','ACTUAL_DEMAND_CONSERVATION':'NOT_RUN_NO_NETWORK','ACTUAL_EXACTLY_ONCE_ACCOUNTING':'NOT_RUN_NO_NETWORK','HIDDEN_CROSSBORDER_CARRIER_SHARING':'NOT_EVALUATED_ON_ACTUAL_NETWORK','ACTUAL_POWER_CO2_SCOPE':'NOT_RUN_NO_NETWORK','ACTIVE_SECTOR_COUPLING_PATHWAYS':'NOT_RUN_NO_NETWORK','ELECTRICITY_INTERCONNECTION_CONTROL_SET_READY':'NO','FULL_SC_RESEARCH_NETWORK_STATICALLY_VALIDATED':'NO','READY_FOR_PHASE4_GATE5_VALIDATION_SOLVE':'NO'}
dump(GE/'STATUS.json',statuses)
status_table='\n'.join('| '+k+' | '+str(v)+' |' for k,v in statuses.items())
text(G/'PHASE4_GATE4_READINESS.md',f'''
# Phase4 Gate4 resume readiness — PARTIAL, no solver

Road EV source absence and international bunker2050 growth absence are **closed for Assembly V1** by explicit human decisions. They are not the reasons to keep searching. The remaining input freeze concerns existing base-account qualification, outstanding unit/rebase decisions and actual allocation. This is not Gate4 completion.

| Required status | Observed status |
|---|---|
{status_table}

`NOT_RUN_NO_NETWORK` is used instead of fabricating PASS or describing a test that was never executed as a scientific failure.

## Required resume answers A–Y

| Item | Evidence-bounded answer |
|---|---|
| A — compact anchors | C.2 final electricity225.0Mtoe; C.3 sector targets/base values; transport374.9Mtoe × human-approved0.935; BAS domestic constant-latest-history method; separate human international constant2019 boundary. |
| B — country-specific2050 forecasts | None newly accepted; national values are allocations or conditional growth candidates. |
| C — regional total ×2019share | Astar225.0Mtoe allocated overASEAN10; TL separate fallback. Road350.5315Mtoe allocated overASEAN10; TL road unresolved. |
| D — sector growth | Residential68.2/63.0, Services75.9/29.5, Industry561.0/185.6, Agriculture-and-Others27.8/8.8 are candidate ratios; source2022/project2019 rebase awaits the explicit decision. |
| E — minor constant fallback | None invoked. International constant2019 is an explicit MATERIAL human boundary, not Tier4. |
| F — exact national Astar | Exact Decimal Mtoe candidates and2019 denominators saved in TARGET_CONSTRUCTION; displayed in the source map. Final MWh awaits the unit convention. |
| G — generation excluded | YES from this Research direct-demand derivation and config. No actual network is claimed. |
| H — Road / EV | Parent350.5315Mtoe approximation; EV unknown and embedded once in Astar, no separate fixed EV Load; sensitivity deferred. |
| I — DEFAULT growth | No upstream DEFAULT/MA/NA/US future values, DEC EV share, vehicle or km proxy used in target candidates. Candidate and accepted sources explicitly identified. |
| J — fossil prices | Frozen processed coal9.5542, gas24.568, oil52.9111 EUR2020/MWh_th; no second inflation/calorific conversion. Original heat-basis metadata limitations remain disclosed. |
| K — independent fossil imports | Accepted design and synthetic Gate3 tests preserve independent country interfaces; actual-network physical separation NOT_RUN. |
| L — biomass | Local supply cap equals accepted fixed country obligation; no surplus pool or free imports. Numerical obligations still need closure. |
| M — geological storage | No asset licensed in Assembly V1 absent an accepted country source; no network has yet been built. |
| N — input preflight | BLOCKED_INPUT_FREEZE.264 physical rows,17 numeric accepted,0 actual allocation-ready. |
| O — first unsolved network | NO. |
| P — hash / inventory | null / NOT_RUN; not copied from an author or tutorial network. |
| Q/R/S — finite / conservation / once-only | Actual-network checks NOT_RUN.17 input guard tests and preserved Gate2 tests PASS are not substitutes. |
| T — prohibited hidden paths | Actual-network NOT_RUN; Gate3 synthetic results retained. |
| U — actual powerCO2 | NOT_RUN; G4-CARBON-01 moved to POST_BUILD_STATIC_VALIDATION_BLOCKER and not waived. Existing budget trajectory and baseline enable=false unchanged. |
| V — interconnector control set | Not ready; no actual2050 component set. |
| W — active sector pathways | Not asserted without a network. Explicit EV pathway deferred by human decision; existing electrolysis/H2/FT architecture remains to be materialised and audited. |
| X — solver count | ZERO. |
| Y — remaining gates | Source-qualified base-account closure + outstanding unit/rebase decisions; target node/time allocation/build assets; after-build physical/carbon/static validation. |

## Next action boundary

Do not restart broad EV or bunker-data searches. Apply the outstanding unit/rebase decisions when received, then resolve the existing2019 source-account reconciliation using preserved raw files and explicit missing-data rules. Keep candidates separate from accepted input. Only after material target obligations and allocation pass may the2050 unsolved export be enabled.100clusters/2013/full-year3h is the requested configuration, not a verified asset already assembled. No solve or Integrated/Disconnected switch is authorized.
''')
text(G/'PHASE4_RESEARCH_BUILD_CONFIG.md','''# Research build configuration — Gate4 resume

`configs/research/baseline.yaml` records AEO8 BAS as the regional final-demand anchor; the Road EV embedded override; constant2019 international bunker boundary; independent quantity-unconstrained fossil markets; local biomass obligation cap; no geological storage; post-build carbon validation.

`network_export_enabled=false`, `runnable_workflow=false`, `solver_allowed=false`, `scenario_switching=false` remain. This is a truthful blocked configuration, not a runnable Full-SC workflow. `legacy_final_adjustment=forbidden`, legacy demand builders forbidden, `only_elec_network=false`. The topology metadata now cites the already completed d13d5976 repair. Baseline carbon enable=false and its existing budgets are preserved.

The input preflight runs first. G4-CARBON-01 requires actual components after a permitted build; it does not block this numerical input check. No synthetic network is substituted for the requested complete2050 Research network.
''')
text(G/'README.md','''# Phase4 Gate4 — Assembly V1 resume

Start with PHASE4_GATE4_READINESS.md, PHASE4_ASSEMBLY_INPUT_FREEZE.md and AEO8_BAS_2050_DEMAND_SOURCE_MAP.md. The canonical input capsule is research_inputs/assembly_v1; the CSV is its review view. ASSEMBLY_V1_2050_METHOD_REGISTER.csv distinguishes source values, human assumptions and pending candidate rebases.

Road EV and international bunker future-growth questions are closed for Assembly V1. Current input freeze remains PARTIAL; no unsolved network or solver result exists. Historical Gate4 evidence is retained; current results and source traces live in evidence/resume. Actual-network CSVs remain explicitly NOT_RUN.
''')
manifest=read(G/'PHASE4_FIRST_FULLSC_NETWORK_MANIFEST.json')
manifest.update(git_commit=None,git_commit_role='Pending tested resume implementation commit; no network build commit',input_registry_sha256=sha(S/'research_inputs/assembly_v1/registry.json'),demand_ledger_version='Gate2 preserved + assembly-v1-freeze-2',preflight_evidence='evidence/resume/ASSEMBLY_PREFLIGHT.json',resume_decisions_sha256=sha(W/'resume_decisions.json'),carbon_validation_stage='POST_BUILD_STATIC_VALIDATION_BLOCKER',effective_config_after_sha256=None)
dump(G/'PHASE4_FIRST_FULLSC_NETWORK_MANIFEST.json',manifest)
print('Updated source map, freeze, readiness, test report, build config and manifest; actual network remains NOT_RUN.')
