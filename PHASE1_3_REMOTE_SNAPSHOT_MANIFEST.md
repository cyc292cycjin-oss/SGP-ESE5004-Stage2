# Phase1–3 safe remote snapshot manifest

Preparation UTC: 2026-10-04T11:26:30.849677+00:00

Snapshot branch: `archive/phase1-3-research-snapshot`.

**Snapshot content commit SHA: 1cc05b3d024dd9445884e98195d2bf018ca4187c.**

Construction: one parentless documentation-content commit followed by one provenance-only identity commit. The final branch tip is verified separately in FINAL_REMOTE_REF_VERIFICATION.csv; the content SHA is recorded here without a circular self-hash. This is not the original local ancestry and is not byte-identical to branches containing excluded raw bytes.

## Original histories

Source research branch: `codex/github-health-audit` @ `753ff15b45ddb91c406a823f8252fc7b603f29c4`.

Buildings validation: `codex/buildings-accounting-validation` @ `50a73d8f531132c5459174a55cac412d5f684462`.

Tutorial: `sgp-stage2-asean` @ `ce327bfae2abe5526d4c1976173f0f8d08366ba5`.

Prior infrastructure reports: Windows `codex/pre-phase4-remote-freeze` @ `09c03c8385c117ddb94a8081fab9301d9d115622`.

Original named local phase checkpoints are retained in snapshot_provenance/ORIGINAL_LOCAL_REFS.json; no original refs/commits are rewritten or deleted.

## Scientific scope preserved

| Family | Path | Files |
| --- | --- | --- |
| model_audit | research/00_model_audit | 80 |
| source_provenance | research/00_source_provenance | 122 |
| phase2_baseline | research/01_baseline_construction | 65 |
| buildings_3a1 | research/02_sector_coupling/buildings_heat | 387 |
| buildings_3a2 | research/02_sector_coupling/buildings_heat_alignment | 47 |
| buildings_3a3 | research/02_sector_coupling/buildings_phase3a3 | 65 |
| buildings_3a4 | research/02_sector_coupling/buildings_heat/phase3a4 | 61 |
| buildings_3a5 | research/02_sector_coupling/buildings_heat/phase3a5 | 79 |
| buildings_3a6 | research/02_sector_coupling/buildings_heat/phase3a6 | 107 |
| buildings_3a7 | research/02_sector_coupling/buildings_heat/phase3a7 | 23 |
| transport_3b1 | research/02_sector_coupling/transport/phase3b1 | 138 |
| transport_3b2 | research/02_sector_coupling/transport/phase3b2 | 51 |
| phase3c | research/02_sector_coupling/phase3c | 40 |
| github_health | docs/repository_health/20261003 | 95 |
| data_registries | research/01_baseline_construction/data_registry | 4 |
| tutorial engineering/run evidence | reproducibility | 18 |
| buildings original combined engineering evidence | research/02_sector_coupling/buildings_engineering_tests | 29 |
| previous remote freeze audit | docs/repository_freeze/20261004 | 48 |

Counts include overlapping directories and must not be added as unique-file totals. All retained historical report/source/evidence blobs are reused unchanged; existing dated findings are not rewritten to match later conclusions. Historical readiness statements remain historical. Current infrastructure status is in the final operation closeout.

## Intentionally excluded source bytes

10 paths / 6 distinct blobs: 1 Simplemaps CSV, 3 DEA workbooks, 1 Eurostat workbook, and 5 copies of the small UNSD URL-index workbook. The latter five are additional binary packaging exclusions; the original endpoint mappings remain in UNSD_REGISTRY_EVIDENCE.json. Their exclusion is not a claim of unlawful use. No original file is removed from disk or history.

### Exclusion 1

| Field | Value |
| --- | --- |
| Path | research/00_model_audit/input_snapshot/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| Source | PyPSA-ASEAN UNSD download-URL registry |
| Version | Frozen source a3616a68ee44592af6527ca9024a90f1956646ae; same SHA256 across these copies |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/00_model_audit/input_snapshot/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| SHA256 | b6ada40d0db7c4e5ef6c91a13743d366dbd05b301d7facd8d89d7a0d71d8692c |
| URL | https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| RetrievalDate | UNKNOWN; not inferred from audit date |
| ReasonExcluded | Documentation snapshot omits original binary workbooks; URL registry already preserved as JSON. Not classified as prohibited proprietary data |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | Maps UNSD energy-product names to original export endpoints |
| DerivedArtifactsPreserved | research/00_source_provenance/UNSD_REGISTRY_EVIDENCE.json (all original URL mappings); INDUSTRIAL_DEMAND_TRACE.md; source scripts |

### Exclusion 2

| Field | Value |
| --- | --- |
| Path | research/00_model_audit/input_snapshot/data/industry/us_cities.csv |
| Source | Simplemaps US Cities, upstream configured Basic source |
| Version | Configured Basic v1.93; current copied bytes not independently matched to source ZIP |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/00_model_audit/input_snapshot/data/industry/us_cities.csv |
| SHA256 | 7ae1a9f4883684a098889e5cf44f6679da2d90ba1e20a26b346c9d3c6ec11098 |
| URL | https://simplemaps.com/static/data/us-cities/1.93/basic/simplemaps_uscities_basicv1.93.zip |
| RetrievalDate | UNKNOWN; not inferred from audit date |
| ReasonExcluded | Unresolved exact-copy redistribution/attribution evidence; fixed source ZIP returned 403 in previous audit |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | US ammonia plant city mapping input; provenance audit copy, not newly accepted ASEAN data |
| DerivedArtifactsPreserved | research/00_model_audit/INPUT_INVENTORY.json; MODEL_INPUT_MAP.md; DATA_LEDGER.csv; source scripts |

### Exclusion 3

| Field | Value |
| --- | --- |
| Path | research/00_source_provenance/diagnostic_inputs/Energy_Statistics_Database.xlsx |
| Source | PyPSA-ASEAN UNSD download-URL registry |
| Version | Frozen source a3616a68ee44592af6527ca9024a90f1956646ae; same SHA256 across these copies |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/00_source_provenance/diagnostic_inputs/Energy_Statistics_Database.xlsx |
| SHA256 | b6ada40d0db7c4e5ef6c91a13743d366dbd05b301d7facd8d89d7a0d71d8692c |
| URL | https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| RetrievalDate | UNKNOWN; not inferred from audit date |
| ReasonExcluded | Documentation snapshot omits original binary workbooks; URL registry already preserved as JSON. Not classified as prohibited proprietary data |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | Maps UNSD energy-product names to original export endpoints |
| DerivedArtifactsPreserved | research/00_source_provenance/UNSD_REGISTRY_EVIDENCE.json (all original URL mappings); INDUSTRIAL_DEMAND_TRACE.md; source scripts |

### Exclusion 4

| Field | Value |
| --- | --- |
| Path | research/00_source_provenance/official/technology-data/inputs/Eurostat_inflation_rates.xlsx |
| Source | Eurostat inflation rates through PyPSA technology-data |
| Version | technology-data v0.13.2 / ec22a1843632fd28ecb9a139ee5156faf23324a3; original source edition only as documented |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/00_source_provenance/official/technology-data/inputs/Eurostat_inflation_rates.xlsx |
| SHA256 | 16c771de24c9bf00f907eea47c482ec2631bf14e82d7b4f86f4020ad86aacc62 |
| URL | https://raw.githubusercontent.com/PyPSA/technology-data/ec22a1843632fd28ecb9a139ee5156faf23324a3/inputs/Eurostat_inflation_rates.xlsx |
| RetrievalDate | Wed, 30 Sep 2026 11:54:42 GMT |
| ReasonExcluded | Original binary workbook with embedded image/media; preserve citation/hash instead of distributing source bytes. Eurostat included under same binary packaging rule, not a new infringement finding |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | Frozen technology costs/efficiencies or inflation conversion evidence; no model parameter update |
| DerivedArtifactsPreserved | research/00_source_provenance/DEA_WORKBOOK_EVIDENCE.json; DEA_COST_SOURCE_TRACE.md; RECOVERY_SUMMARY.json; COST_FETCH_LOG.json; HISTORY_FETCH_LOG.json; current compiled cost CSVs |

### Exclusion 5

| Field | Value |
| --- | --- |
| Path | research/00_source_provenance/official/technology-data/inputs/data_sheets_for_renewable_fuels.xlsx |
| Source | Danish Energy Agency through PyPSA technology-data |
| Version | technology-data v0.13.2 / ec22a1843632fd28ecb9a139ee5156faf23324a3; original source edition only as documented |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/00_source_provenance/official/technology-data/inputs/data_sheets_for_renewable_fuels.xlsx |
| SHA256 | efa1ce103b813a2a3d807d20c6cd05c937f80010320a38e51149d234b60cd086 |
| URL | https://raw.githubusercontent.com/PyPSA/technology-data/ec22a1843632fd28ecb9a139ee5156faf23324a3/inputs/data_sheets_for_renewable_fuels.xlsx |
| RetrievalDate | Wed, 30 Sep 2026 11:48:30 GMT |
| ReasonExcluded | Original binary workbook with embedded image/media; preserve citation/hash instead of distributing source bytes. Eurostat included under same binary packaging rule, not a new infringement finding |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | Frozen technology costs/efficiencies or inflation conversion evidence; no model parameter update |
| DerivedArtifactsPreserved | research/00_source_provenance/DEA_WORKBOOK_EVIDENCE.json; DEA_COST_SOURCE_TRACE.md; RECOVERY_SUMMARY.json; COST_FETCH_LOG.json; HISTORY_FETCH_LOG.json; current compiled cost CSVs |

### Exclusion 6

| Field | Value |
| --- | --- |
| Path | research/00_source_provenance/official/technology-data/inputs/technology_data_catalogue_for_energy_storage.xlsx |
| Source | Danish Energy Agency through PyPSA technology-data |
| Version | technology-data v0.13.2 / ec22a1843632fd28ecb9a139ee5156faf23324a3; original source edition only as documented |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/00_source_provenance/official/technology-data/inputs/technology_data_catalogue_for_energy_storage.xlsx |
| SHA256 | 5eaff3f3f242efabafc12ba5d556cf770bc2e569fde55dc0bf1a638a95f70911 |
| URL | https://raw.githubusercontent.com/PyPSA/technology-data/ec22a1843632fd28ecb9a139ee5156faf23324a3/inputs/technology_data_catalogue_for_energy_storage.xlsx |
| RetrievalDate | Wed, 30 Sep 2026 11:48:29 GMT |
| ReasonExcluded | Original binary workbook with embedded image/media; preserve citation/hash instead of distributing source bytes. Eurostat included under same binary packaging rule, not a new infringement finding |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | Frozen technology costs/efficiencies or inflation conversion evidence; no model parameter update |
| DerivedArtifactsPreserved | research/00_source_provenance/DEA_WORKBOOK_EVIDENCE.json; DEA_COST_SOURCE_TRACE.md; RECOVERY_SUMMARY.json; COST_FETCH_LOG.json; HISTORY_FETCH_LOG.json; current compiled cost CSVs |

### Exclusion 7

| Field | Value |
| --- | --- |
| Path | research/00_source_provenance/official/technology-data/inputs/technology_data_for_el_and_dh.xlsx |
| Source | Danish Energy Agency through PyPSA technology-data |
| Version | technology-data v0.13.2 / ec22a1843632fd28ecb9a139ee5156faf23324a3; original source edition only as documented |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/00_source_provenance/official/technology-data/inputs/technology_data_for_el_and_dh.xlsx |
| SHA256 | 3ab3f61377f4b9026bf74aed95351ef5675c44d321bb9d05b5da05a45071b79f |
| URL | https://raw.githubusercontent.com/PyPSA/technology-data/ec22a1843632fd28ecb9a139ee5156faf23324a3/inputs/technology_data_for_el_and_dh.xlsx |
| RetrievalDate | Wed, 30 Sep 2026 11:48:30 GMT |
| ReasonExcluded | Original binary workbook with embedded image/media; preserve citation/hash instead of distributing source bytes. Eurostat included under same binary packaging rule, not a new infringement finding |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | Frozen technology costs/efficiencies or inflation conversion evidence; no model parameter update |
| DerivedArtifactsPreserved | research/00_source_provenance/DEA_WORKBOOK_EVIDENCE.json; DEA_COST_SOURCE_TRACE.md; RECOVERY_SUMMARY.json; COST_FETCH_LOG.json; HISTORY_FETCH_LOG.json; current compiled cost CSVs |

### Exclusion 8

| Field | Value |
| --- | --- |
| Path | research/02_sector_coupling/buildings_heat/source_snapshot/paper/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| Source | PyPSA-ASEAN UNSD download-URL registry |
| Version | Frozen source 5bacad702ccfed17ad19ab510fa710651e966f2c; same SHA256 across these copies |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/02_sector_coupling/buildings_heat/source_snapshot/paper/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| SHA256 | b6ada40d0db7c4e5ef6c91a13743d366dbd05b301d7facd8d89d7a0d71d8692c |
| URL | https://github.com/pypsa-meets-earth/pypsa-asean/blob/5bacad702ccfed17ad19ab510fa710651e966f2c/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| RetrievalDate | UNKNOWN; not inferred from audit date |
| ReasonExcluded | Documentation snapshot omits original binary workbooks; URL registry already preserved as JSON. Not classified as prohibited proprietary data |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | Maps UNSD energy-product names to original export endpoints |
| DerivedArtifactsPreserved | research/00_source_provenance/UNSD_REGISTRY_EVIDENCE.json (all original URL mappings); INDUSTRIAL_DEMAND_TRACE.md; source scripts |

### Exclusion 9

| Field | Value |
| --- | --- |
| Path | research/02_sector_coupling/buildings_heat/source_snapshot/upstream/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| Source | PyPSA-ASEAN UNSD download-URL registry |
| Version | Frozen source a3616a68ee44592af6527ca9024a90f1956646ae; same SHA256 across these copies |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/02_sector_coupling/buildings_heat/source_snapshot/upstream/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| SHA256 | b6ada40d0db7c4e5ef6c91a13743d366dbd05b301d7facd8d89d7a0d71d8692c |
| URL | https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| RetrievalDate | UNKNOWN; not inferred from audit date |
| ReasonExcluded | Documentation snapshot omits original binary workbooks; URL registry already preserved as JSON. Not classified as prohibited proprietary data |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | Maps UNSD energy-product names to original export endpoints |
| DerivedArtifactsPreserved | research/00_source_provenance/UNSD_REGISTRY_EVIDENCE.json (all original URL mappings); INDUSTRIAL_DEMAND_TRACE.md; source scripts |

### Exclusion 10

| Field | Value |
| --- | --- |
| Path | research/02_sector_coupling/transport/phase3b1/evidence/cached_inputs/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| Source | PyPSA-ASEAN UNSD download-URL registry |
| Version | Frozen source a3616a68ee44592af6527ca9024a90f1956646ae; same SHA256 across these copies |
| OriginalLocalPath | /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit/research/02_sector_coupling/transport/phase3b1/evidence/cached_inputs/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| SHA256 | b6ada40d0db7c4e5ef6c91a13743d366dbd05b301d7facd8d89d7a0d71d8692c |
| URL | https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/data/demand/unsd/paths/Energy_Statistics_Database.xlsx |
| RetrievalDate | UNKNOWN; not inferred from audit date |
| ReasonExcluded | Documentation snapshot omits original binary workbooks; URL registry already preserved as JSON. Not classified as prohibited proprietary data |
| LocalAvailability | EXISTS; SHA256 matches |
| ScientificUse | Maps UNSD energy-product names to original export endpoints |
| DerivedArtifactsPreserved | research/00_source_provenance/UNSD_REGISTRY_EVIDENCE.json (all original URL mappings); INDUSTRIAL_DEMAND_TRACE.md; source scripts |

## Preservation and limits

Existing reports may still cite excluded original paths. Those citations are intentionally unchanged; use the exclusion entries and local originals to resolve them. Hash preservation is identity evidence, not human scientific acceptance. No model parameter, demand, accounting conclusion or candidate-fix code was edited. Large original packages/NetCDF/weather/environment caches that were already outside committed research documentation remain outside this snapshot. Their existing manifests/URLs/hashes are preserved; no new broad filesystem crawl or experiment was performed.
