# Buildings data decision update

Material Passport: academic-research-suite; inline engineering/accounting audit; Phase 3A-4 v1; 2026-10-01. VERIFIED applies only to stated code/test/hash observations; accounting methods are ANALYZED/proposed and scientific inputs remain PENDING.

## Decisions already supplied by the user

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
