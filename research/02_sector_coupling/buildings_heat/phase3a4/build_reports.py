"""Render factual reports from completed evidence; no source or input mutation."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent
read=lambda name:json.loads((R/'evidence'/name).read_text(encoding='utf8'))
rec=read('INTEGRATION_RECEIPT.json');identity=read('FINAL_INTEGRATION_IDENTITY.json')
combined=read('COMBINED_TESTS.json')
passport='Material Passport: academic-research-suite; inline engineering/accounting audit; Phase 3A-4 v1; 2026-10-01. VERIFIED applies only to stated code/test/hash observations; accounting methods are ANALYZED/proposed and scientific inputs remain PENDING.\n\n'
def write(name,body): (R/name).write_text(body,encoding='utf8')
table='| Fix | Kind | Original commit | Integrated commit |\n|---|---|---|---|\n'
for s in rec['steps']:table+=f"| {s['fix']} | {s['kind']} | `{s['original']}` | `{s['integrated']}` |\n"
write('BUILDINGS_FIX_INTEGRATION_REPORT.md','# Buildings E1/E2/E4 integration report\n\n'+passport+f'''## Outcome and identities

**PASS — engineering integration only. E3 remains blocked.**

- Independent branch: `{identity['branch']}`.
- Worktree: `{rec['worktree']}` (WSL Ubuntu).
- Base: `{identity['base']}`.
- Combined tested source commit: `{identity['tested_source_commit']}`.
- Final combined validation-record commit: **`{identity['combined_commit']}`**; clean worktree, identical model source to tested commit.
- P=`5bacad702ccfed17ad19ab510fa710651e966f2c`; U/R=`a3616a68ee44592af6527ca9024a90f1956646ae`; T=`ce327bfae2abe5526d4c1976173f0f8d08366ba5`. All four protected trees unchanged and clean. No merge into R.

## Commit provenance

{table}
Each application used `cherry-pick -x`. Stable patch IDs match original commits; no merge conflicts or conflict resolutions occurred. The three extra `environment_doc_correction` commits only correct the original validation README’s PyPSA version from an erroneous label to actual 0.30.3; their paths are restricted and recorded. No additional model patch was introduced.

The final audit commit records receipts and the combined results in `research/02_sector_coupling/buildings_engineering_tests/phase3a4_combined/`. The [machine receipt](evidence/INTEGRATION_RECEIPT.json) includes all source/validation/doc SHA mappings and each test command; [final identity](evidence/FINAL_INTEGRATION_IDENTITY.json) supplies the commit containing all fixes and validation records.

## Step-by-step regression

| Stage | Original validation cases rerun | Strict active-fix checks | Result |
|---|---|---:|---|
| after E1 | E1:5 | 777 | PASS |
| after E2 | E1:5 + E2:7 | 777+197=974 | PASS |
| after E4 | E1:5 + E2:7 + E4:1 | 777+197+88=1,062 | PASS |
| final combined harness | All three fixes in one process | 1,062 | PASS |

The combined harness calls the real source functions on labelled synthetic PyPSA networks (11 country labels, 2 nodes/country), including non-flat profiles, nonuniform weights, fixed-fuel preservation, zero-demand boundaries, district-allocation extremes, R/S separation, zero-HDD and invalid inputs, and both electricity-filter switch states. The E2 producer→consumer test explicitly blocks positive annual heat with zero shape instead of constructing zero heat.

The [combined matrix](BUILDINGS_FIX_COMBINED_TEST_MATRIX.csv) gives before/expected/after/error per country/account/test. “Before” reuses archived frozen-U failures; “after” is this integration run. Synthetic fixtures are not observed national annual demands. Successful E2 early errors necessarily produce fewer output rows than the failing baseline. `RAISE`/boolean rows have no numerical relative error.

Absolute energy tolerance is `1e-6 MWh + 1e-12*abs(expected)`; max final MWh error is `{max(r['absolute_error'] or 0 for r in combined['rows'] if r['unit']=='MWh')}`. E1's mixed-fuel cases preserve remaining competitive heat and unchanged fixed fuel separately; these two bases are not claimed to be a scientifically calibrated uniform useful-heat total. The all-service synthetic case tests F=0. DH service and upstream additive loss `(1+loss)` are checked separately, not scientifically accepted.

## Source identity, demand and scope protection

Only three model files differ from U: `prepare_sector_network.py` (E1/E2), `prepare_heat_data.py` (E2), `final_asean_adjustment.py` (E4 one spelling). Other differences are research tests/documentation. The source bytes exactly match the already-tested Phase3A3 combined overlay. See [source diff](evidence/INTEGRATED_SOURCE.diff).

No data/config/cost/carbon/spatial-scope file was changed; all **19** retained model input hashes match before/after. Annual input/service targets are not edited. Output construction is intentionally corrected by E1/E4 and blocked on invalid shape by E2; “no demand mutation” does not mean retaining erroneous old output or accepting its scientific assumptions.

Carrier grep over all `scripts/` and `configs/` finds canonical `services electricity` in the base table producer, Load builder and E4 keep-list; no singular exact literal remains. However, `elec_carrier` and the optional non-industrial redistribution list still omit S. Thus **E4 naming is consistent, E3 accounting consumers are not complete**. No blanket “all electricity handling is fixed” claim is made.

## Mechanical preflight and limitations

First E1 preflight stopped because Git treated CRLF ends as whitespace. Read-only inspection proved its 4,041 lines and source blob exactly match the approved E1 commit; no model edit was needed. Subsequent checks explicitly used `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check`, preserving all other whitespace checks. The original stop is retained in [initial receipt](evidence/INITIAL_CRLF_PREFLIGHT_STOP.json). All commit diffs and the final cumulative diff pass this declared check; trees are clean.

Runtime: Python3.11.13, PyPSA0.30.3, NumPy1.26.4, pandas2.3.1. Existing PROJ database warning persists on import; these function tests do not exercise GIS transformations. No environment upgrade, full Snakemake build, NetCDF roundtrip acceptance, solver run, or Full-SC scientific acceptance is implied.
''')

write('BUILDINGS_ELECTRICITY_CLOSURE_TEST.md','# Buildings electricity closure checks\n\n'+passport+'''## Observed results

| Evidence | Result | Meaning |
|---|---|---|
| E1/E2/E4 combined | 1,062/1,062 PASS | Bounded source-function regressions on synthetic fixtures |
| Accounting contract | 18/18 PASS | Valid identity accepted; deliberate duplication/loss/missing inputs rejected |
| Integrated current E3 | KNOWN_E3_BLOCKER_REPRODUCED | Current total-growth function still omits Services |
| Actual ASEAN country/year/snapshot closure | NOT ESTABLISHED | No accepted base↔historical-electric-heat↔useful-service data bridge |

The [E3 specification](BUILDINGS_E3_ACCOUNTING_SPEC.md) was written before accounting tests; no E3 patch was created. [Contract results](evidence/ACCOUNTING_CONTRACT_TESTS.json) and `check_accounting_contract.py` are a research-side mathematical contract, not an alternative hidden model implementation.

The independent reference totals in the synthetic fixture detect: second subtraction of historical electric heat; second addition of Services; cooling deletion; electric cooking deletion; preloaded endogenous HP input; missing historical heat; negative residual; nonfinite input; annual equality hiding snapshot imbalance; lost cooking fuel; unknown fuel share treated as zero; missing efficiency/end-use share; HHV/LHV mismatch. A separate energy conversion example allows historical electric COP>1. All numerical fixtures are labelled synthetic; no field is exported to scientific input tables.

## Current E3 counterexample

[Integrated diagnostic](evidence/INTEGRATED_E3_DIAGNOSTIC.json) uses two synthetic electric Loads: original AC=20 TWh, S=3 TWh, and a test national target=1 TWh. The actual `include_electricity_growth` function makes AC=1 and leaves S=3, totaling4. This reproduces the selector/accounting flaw; it is **not** an estimate of ASEAN overstatement and the artificial quantities are not a valid scientific scenario. The function is unchanged by E1/E2/E4.

Adding Services to the calibration set could make a gross target match while corrupting independently accepted direct components and retaining historical electric heating. Uncommenting `electric_heat_supply` would use future fuel-shift/default quantities, not identified historical heating. Neither action is an acceptable E3 fix.

## Required future real-data acceptance tests (not run here)

1. Freeze the source-year/meter bridge A→A*, country/region mappings and physical snapshot weights. Test complete source lineage; reject missing values before upstream annual fillna.
2. For each country and R/S, verify identified historical D/E exactly covers the represented H/I service. Allocate and subtract once; preserve direct cooling and electric cooking, and preserve non-electric cooking by fuel.
3. Check pointwise and weighted annual `O+B+C+D+E=A*`, finite/nonnegative residuals, unique account ownership and no duplicate parent/subaccount Loads. Retain unclassified fuel rather than silently mapping it to heat.
4. Check H/I useful-service integrals after spatial/temporal aggregation, including water without HDD, true space-heating geography, timezone/weekend/year handling and zero/invalid profile failure. Do not call annual conservation “validated hourly demand”.
5. Check after **every subsequent workflow transformation**, especially distribution-loss adjustments, total-growth scaling and industry redistribution. Ensure no accepted account is rescaled implicitly; require the intended contract in the test oracle.
6. Once separately authorized, solved dispatch tests must check electricity, heat, CHP co-products and storage bus balances with actual Link directions; J/K/conversion input never belongs in fixed exogenous direct Load. No solve occurred in this phase.

The synthetic tests do not prove actual cooling totals or cooking totals are complete. They prove the proposed contract would reject stated losses/duplicates when valid partition data are supplied. Current full-sector code still has E3 and legacy fuel-shift issues.
''')

write('BUILDINGS_DATA_DECISION_UPDATE.md','# Buildings data decision update\n\n'+passport+'''## Decisions already supplied by the user

R/S stay separate in the model; Buildings is a reporting aggregate. The target is fixed useful space/water service with endogenous supply competition. Cooling stays direct electricity. Cooking stays NON-EXPLICIT + ACCOUNTING REQUIRED. No uniform ASEAN district-heating defaults or fabricated ASEAN heating stock. UNSD2019 is eligible for final-energy calibration but is not useful heat. BDEW remains reference only.

These instructions define scope; this report does not mark a numerical data row HUMAN_ACCEPTED.

| Item | Status / disposition after Phase3A4 |
|---|---|
| E1/E2/E4 engineering integration | ACCEPT_STRUCTURE for the user-authorized validation step; bounded tests passed, scientific inputs not accepted |
| Code provenance and known source files | SOURCE_RECOVERED; source version and local hashes retained |
| E3 accounting contract | ACCEPT_STRUCTURE as a documented design for review; numerical bridge remains ASEAN_VALIDATION_PENDING |
| E3 source changes | ENGINEERING_FIX_REQUIRED **after** data/boundary gate; not implemented |
| Country/sector end-use shares and historical electric heat | ASEAN_VALIDATION_PENDING; aggregate electricity does not identify heating |
| Historical device mix/efficiency/COP | ASEAN_VALIDATION_PENDING; tag DEA/national/literature/default/assumption separately |
| Source year, sector definitions, loss/meter and service boundary | SCIENTIFIC_DECISION_REQUIRED with documented data support |
| Default60/40, uniform DH and missing ASEAN stock interpreted as zero | REJECT_DEFAULT for automatic research adoption |
| Malaysia2016 and bounded country/region studies | DATA_UPDATE_CANDIDATE, not accepted replacements for UNSD2019 |

## What is closed, and what is not

Closed by direct evidence: the approved source patches compose without conflict; original and strict validations still pass; patched source hashes agree with prior combined source; model input/config identity remains unchanged; singular service-electricity naming is removed. The independent validation branch and its history now exist.

Not closed: actual historical electric heating; complete cooking/fuel partition; final→useful device conversion; physical time/location alignment with base electricity; future demand-growth accounting. These gaps cannot be solved by approving E1/E2/E4 or by relabelling aggregate final energy as useful heat.

No new literature search was performed. Reuse [50-row source registry](../../buildings_phase3a3/BUILDINGS_DATA_REGISTRY_UPDATED.csv) and [eight bounded source candidates](../../buildings_phase3a3/ASEAN_BUILDINGS_DATA_CANDIDATES.csv). Stronger candidate evidence remains MalaysiaNEB2016 Tables42/47, but year/region/calibration conditions still apply. The ERIA commercial figure/table unit conflict is not resolved by selecting whichever unit fits. Indonesia UNSD/ESDM scope conflict remains open. No sample result was extrapolated to national zero heating or to all Services.

## Targeted next decisions, not another broad source hunt

1. Select the base-year final-meter electricity boundary and approve a reconciled A*↔R/S bridge, including loss and future-target definitions.
2. Review existing country/region end-use evidence and identify only missing historical space/water electric components and cooking partitions; prioritize applicable official tables rather than searching for one perfect11-country dataset.
3. Approve the historical device/input-energy mix and performance evidence needed to form H/I. State source version, HHV/LHV and useful-service boundary.
4. Agree on R/S spatial/temporal construction and pointwise residual checks. Water is usage-based where evidence allows; space heating requires regional demand evidence; no final curves yet.
5. For eventual Full-SC assembly, settle DH and stock coverage without automatic default adoption. None of these decisions changes carbon policy.

The [34-row requirements register](../../../../data_registry/buildings_phase3a4/BUILDINGS_E3_DATA_REQUIREMENTS.csv) separates data gaps, boundary decisions and engineering work; includes22 country×R/S historical-electric-heating records. Human confirmation remains PENDING throughout.
''')

write('BUILDINGS_PHASE3A4_READINESS.md','# Phase 3A-4 readiness\n\n'+passport+f'''**Engineering integration: PASS. E3 implementation: BLOCKED BY EVIDENCE. READY FOR FULL-SC ASSEMBLY: NO.**

| User question | Evidence-bounded answer |
|---|---|
| A. E1/E2/E4 integrated? | Yes, independent `{identity['branch']}`, final `{identity['combined_commit']}`; P/U/R/T unchanged. |
| B. Combined tests? | All1,062 strict checks pass; staged original validations pass; 18 separate synthetic accounting-contract checks pass. |
| C. Scientific demand changed? | No source demand/config/cost/carbon/spatial input edits; 19 retained inputs hash-identical. Corrected output construction and invalid-profile rejection do change erroneous runtime behavior. |
| D. Full E3 identity clear? | The proposed country/year/snapshot identities, component ownership and execution order are explicit. Numerical ASEAN closure is not established. |
| E. Historical electric heating identifiable? | Not yet for accepted11-country R/S scope; local older/sample candidates exist but do not supply a complete matched-year bridge. |
| F. Cooling retained and not duplicated? | Required by design; synthetic contract rejects deletion/double accounting. No cooling module added. Actual national cooling preservation/partition cannot yet be certified under unresolved E3. |
| G. Cooking nonexplicit without loss? | Nonexplicit by frozen scope; ledger method retains electric/fuel amounts and excludes them from H/I. Actual complete fuel/end-use partition still unverified; do not claim existing defaults already ensure this. |
| H. E3 patch data ready? | No. No E3 patch or FIX_E3_REPORT was generated. |
| I. Useful-heat method executable? | Algorithm, field dictionary and synthetic contract are ready for review. Actual final-energy→service generation remains blocked by missing/unaligned inputs; no final research inputs produced. |
| J. Fields missing Human Acceptance? | Source version/year/geography, meter/loss/sector mapping, fuel conversion/basis, end-use shares, historical D/E, device mix/performance, service boundary, year bridge, spatial/temporal weights and future direct/service growth; DH/stock for assembly. See requirements/schema. |
| K. READY FOR FULL-SC ASSEMBLY? | No. Engineering acceptance is not scientific data acceptance. |

## Minimum remaining five evidence/decision groups

1. **Matched electricity bridge:** A*↔R/S, source year, sector coverage and meter/loss definition; identified historical space/water electrical input with exactly-once lineage.
2. **Complete end-use/fuel mapping:** heating/cooking/cooling/other partitions, unclassified handling and relevant unit/HHV-LHV conflicts; no cooking disappearance or fuel-to-heat default split.
3. **Historical performance to useful service:** input-energy device mix, efficiency/COP and delivered-service boundary; future supply performance kept distinct.
4. **Country/region and snapshot construction:** accepted R/S allocation, water-use and real space-heat shapes, historical electric-input timing and nonnegative residual proof.
5. **Assembly boundary and application order:** future direct/service growth and calibration ownership; evidence-based DH/stock scope. After1–4 and the relevant boundary decisions, implement/test E3, then review assembly readiness again.

These groups combine missing data and research decisions; they do not require an impossible single unified11-country dataset. Existing sources should be reviewed before seeking narrowly missing files. Scientific input rows accepted in this phase: **0**. Formal model/solver runs: **0**. No next-sector work begins.

## Navigation

- [Integration report](BUILDINGS_FIX_INTEGRATION_REPORT.md) / [combined matrix](BUILDINGS_FIX_COMBINED_TEST_MATRIX.csv)
- [E3 specification](BUILDINGS_E3_ACCOUNTING_SPEC.md) / [data requirements](../../../../data_registry/buildings_phase3a4/BUILDINGS_E3_DATA_REQUIREMENTS.csv)
- [Useful-heat method](BUILDINGS_USEFUL_HEAT_METHOD.md) / [field dictionary](../../../../data_registry/buildings_phase3a4/BUILDINGS_USEFUL_HEAT_INPUT_SCHEMA.csv)
- [Electricity closure checks](BUILDINGS_ELECTRICITY_CLOSURE_TEST.md) / [data decision update](BUILDINGS_DATA_DECISION_UPDATE.md)
''')
write('README.md','# Phase 3A-4 handoff\n\n'+passport+'''Start with [readiness](BUILDINGS_PHASE3A4_READINESS.md). This folder contains the six requested Markdown reports and the combined CSV matrix; the two requested data/schema CSVs are in `data_registry/buildings_phase3a4/`. The empty template there is optional convenience, with zero scientific rows.

`integrate_fixes.py` is the retained one-time execution record: it refuses an existing destination and is not a routine rerun command. Its narrowly scoped CRLF resume option documents the actual preflight event and exact inspected commit. Do not reset or rerun integration blindly. `record_combined_validation.py` is also a one-time commit operation. All user-approved fixes and original tests already reside in the independent validation worktree.

For subsequent verification, run the existing `test_buildings_fixes.py --repo <validation worktree> --fix combined --output <new receipt>` in the recorded PyPSA environment. `check_accounting_contract.py` only exercises labelled synthetic mathematical identities. `check_integrated_e3.py` confirms the remaining known E3 flaw without patching it. `build_tables.py` + `export_tables.mjs` regenerate review tables from receipts; they never create scientific model inputs. `build_reports.py` regenerates the report summaries from completed receipts.

Review evidence distinctions: VERIFIED=code/test/hash observation; analytical derivation=accounting identity under stated common-boundary assumptions; inference=why current input gaps prevent valid E3 execution; proposed test=real-data workflow/dispatch checks not yet run. A pass in the first category does not imply the latter categories passed.

The delivery ZIP includes `provenance/phase3a4_buildings_validation.bundle`, a verified Git history delta with prerequisite U `a3616a68ee44592af6527ca9024a90f1956646ae`. Its hash and final branch identity are in `evidence/INTEGRATION_BUNDLE.json`. Restore only into an audit clone containing that exact U commit: `git bundle verify <bundle>` then `git fetch <bundle> refs/heads/codex/buildings-accounting-validation:refs/heads/codex/buildings-accounting-validation`. Do not force an existing branch. The ZIP also retains prior Phase3A3/3A2/3A1 evidence dependencies; downloaded/reference materials remain evidence, not newly accepted model inputs.

Fallacy scan for this deterministic engineering task: Simpson/ecological aggregation and selection/survivorship concerns prevent nationalizing small household samples or aggregating R/S before checks. No statistical causal effect or association is estimated; Berkson, collider, base-rate neglect, regression-to-mean, look-elsewhere, forking-paths significance, correlation/causation and reverse-causality claims are not applicable to the function regressions. No independent peer review is claimed.

The existing PROJ warning limits environment/GIS readiness; no GIS transforms or optimizer were tested. Full-SC remains unaccepted. Prior audit histories are preserved. Root workspace may retain pre-existing untracked `outputs/` and `work/`; this does not describe the clean model and project-audit worktrees.
''')
print(json.dumps(dict(reports_written=5,combined_commit=identity['combined_commit'])))
