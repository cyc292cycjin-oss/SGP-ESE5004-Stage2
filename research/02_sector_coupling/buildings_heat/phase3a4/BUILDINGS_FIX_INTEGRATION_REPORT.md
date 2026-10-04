# Buildings E1/E2/E4 integration report

Material Passport: academic-research-suite; inline engineering/accounting audit; Phase 3A-4 v1; 2026-10-01. VERIFIED applies only to stated code/test/hash observations; accounting methods are ANALYZED/proposed and scientific inputs remain PENDING.

## Outcome and identities

**PASS — engineering integration only. E3 remains blocked.**

- Independent branch: `codex/buildings-accounting-validation`.
- Worktree: `/home/jin/research/SGP_ESE5004_Stage2/phase3a4/buildings_accounting_validation` (WSL Ubuntu).
- Base: `a3616a68ee44592af6527ca9024a90f1956646ae`.
- Combined tested source commit: `353dec3c83b859eab39bcf2dff79fe30d88a2ec0`.
- Final combined validation-record commit: **`50a73d8f531132c5459174a55cac412d5f684462`**; clean worktree, identical model source to tested commit.
- P=`5bacad702ccfed17ad19ab510fa710651e966f2c`; U/R=`a3616a68ee44592af6527ca9024a90f1956646ae`; T=`ce327bfae2abe5526d4c1976173f0f8d08366ba5`. All four protected trees unchanged and clean. No merge into R.

## Commit provenance

| Fix | Kind | Original commit | Integrated commit |
|---|---|---|---|
| E1 | source | `92e9118be20f0b3802f385adac2f56650d57299d` | `18d7df24d4eeb36800b58a11db3447b0396d55d4` |
| E1 | validation | `59dbd34880bcdb367fed54cdee39a2ace40182fd` | `faeee4cfd649d9ffa8ce8aa1ff42e0abf6c693ad` |
| E1 | environment_doc_correction | `30bafa420e5cd639e696cbdd56de0e7df36c0e47` | `b396e66e52240a50327e7285392417bea56ac824` |
| E2 | source | `31037d60d69fa762c9ed8ec9ce8289d95bd6a181` | `b542de2c19786a26ea06ebf36ff8718e082302cc` |
| E2 | validation | `1f9405720a873918614df5aad361580cff7cedde` | `9291c937af1c6f0e4cc60e9ad87f7fc85af75a99` |
| E2 | environment_doc_correction | `070db2918186829908a02a0b72a7b4426711c653` | `2f4b52bf767e062df73ad46922632320b8548b3d` |
| E4 | source | `5d761eceeeb0d0519208d760224a41ff50ec1e30` | `ab8e91edb3cd9b981928de52b9a355a505ee0aee` |
| E4 | validation | `78b23e7804ca05f2fd1f5ee5ec90f3fa6f8bbf7c` | `7878acbb57b6350f37babb1e24659a17de89eebf` |
| E4 | environment_doc_correction | `9342893fcf467eadbbc410f59c3dbe817d123aa9` | `353dec3c83b859eab39bcf2dff79fe30d88a2ec0` |

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

Absolute energy tolerance is `1e-6 MWh + 1e-12*abs(expected)`; max final MWh error is `1.862645149230957e-09`. E1's mixed-fuel cases preserve remaining competitive heat and unchanged fixed fuel separately; these two bases are not claimed to be a scientifically calibrated uniform useful-heat total. The all-service synthetic case tests F=0. DH service and upstream additive loss `(1+loss)` are checked separately, not scientifically accepted.

## Source identity, demand and scope protection

Only three model files differ from U: `prepare_sector_network.py` (E1/E2), `prepare_heat_data.py` (E2), `final_asean_adjustment.py` (E4 one spelling). Other differences are research tests/documentation. The source bytes exactly match the already-tested Phase3A3 combined overlay. See [source diff](evidence/INTEGRATED_SOURCE.diff).

No data/config/cost/carbon/spatial-scope file was changed; all **19** retained model input hashes match before/after. Annual input/service targets are not edited. Output construction is intentionally corrected by E1/E4 and blocked on invalid shape by E2; “no demand mutation” does not mean retaining erroneous old output or accepting its scientific assumptions.

Carrier grep over all `scripts/` and `configs/` finds canonical `services electricity` in the base table producer, Load builder and E4 keep-list; no singular exact literal remains. However, `elec_carrier` and the optional non-industrial redistribution list still omit S. Thus **E4 naming is consistent, E3 accounting consumers are not complete**. No blanket “all electricity handling is fixed” claim is made.

## Mechanical preflight and limitations

First E1 preflight stopped because Git treated CRLF ends as whitespace. Read-only inspection proved its 4,041 lines and source blob exactly match the approved E1 commit; no model edit was needed. Subsequent checks explicitly used `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check`, preserving all other whitespace checks. The original stop is retained in [initial receipt](evidence/INITIAL_CRLF_PREFLIGHT_STOP.json). All commit diffs and the final cumulative diff pass this declared check; trees are clean.

Runtime: Python3.11.13, PyPSA0.30.3, NumPy1.26.4, pandas2.3.1. Existing PROJ database warning persists on import; these function tests do not exercise GIS transformations. No environment upgrade, full Snakemake build, NetCDF roundtrip acceptance, solver run, or Full-SC scientific acceptance is implied.
