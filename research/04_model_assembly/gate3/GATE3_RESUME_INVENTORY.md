# Gate3 resume inventory

Verified base `ad5e81e75882704ac9e33a6eac96c5c79717c5e1`; local/remote research match; working tree clean; main unchanged. No model write or commit during inventory.

| Artifact | Classification | Basis / action |
|---|---|---|
| START.json, EFFECTIVE_CONFIG.json, source/*.py | VALID_REUSE | Current SHA/config content matches saved evidence. |
| TUTORIAL_COMPONENTS.json, CARRIER_FACTORS.json | VALID_REUSE | Original historical NetCDF SHA matches; reference only, not Research assembly. |
| REFERENCE_GRAPH_AUDIT.json, REFERENCE_POLICY_MAP.json | VALID_REUSE | Inputs and source hashes unchanged; reuse derived reference graph/maps, no rerun. |
| RAW_ELECTRICITY_CLASSIFICATION.json | VALID_REUSE | All four pinned raw topology input hashes match. |
| Six stage implementation drafts | NEEDS_RECHECK | Preserved byte copies and exact Gate2 diffs; final tests incomplete. |
| probe.py, audit_reference.py, complete_source_audit.py | VALID_REUSE | Extraction/replay provenance; do not regenerate validated reference evidence. |
| integrate.py | NEEDS_RECHECK | Never ran before interruption; must add Buildings, Shipping, manifest regressions. |
| Gate3 final CSVs, reports, package | UNKNOWN | Not yet present; must produce. |
| Existing fix_topology worktree | VALID_REUSE | Inventory only; untouched and excluded from Gate3. |
| Other historical worktrees/branches | VALID_REUSE | Retained as references; no Gate3-specific worktree or branch found. |

OBSOLETE: none proven. No draft/evidence/history deleted. Implementation target is only research/full-sc-baseline. Native workspace is delivery staging, not the model repository.

## Worktrees at resume
```
worktree /home/jin/research/SGP_ESE5004_Stage2/phase2/model-source
HEAD ce327bfae2abe5526d4c1976173f0f8d08366ba5
branch refs/heads/sgp-stage2-asean

worktree /home/jin/research/SGP_ESE5004_Stage2/phase2/fix_carbon_config
HEAD 753ac81c23f8b9a1ca8ceed531d0630b56f6953d
branch refs/heads/codex/fix-carbon-config

worktree /home/jin/research/SGP_ESE5004_Stage2/phase2/fix_industrial_gdp
HEAD a7a8f06b43f0dcce0dbd7005b989d8f73d142b81
branch refs/heads/codex/fix-industrial-gdp

worktree /home/jin/research/SGP_ESE5004_Stage2/phase2/fix_topology
HEAD a3616a68ee44592af6527ca9024a90f1956646ae
branch refs/heads/codex/fix-topology-765-766

worktree /home/jin/research/SGP_ESE5004_Stage2/phase2/paper_reference
HEAD 5bacad702ccfed17ad19ab510fa710651e966f2c
branch refs/heads/codex/paper-reference-5bacad70

worktree /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit
HEAD 753ff15b45ddb91c406a823f8252fc7b603f29c4
branch refs/heads/codex/github-health-audit

worktree /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
HEAD ad5e81e75882704ac9e33a6eac96c5c79717c5e1
branch refs/heads/research/full-sc-baseline

worktree /home/jin/research/SGP_ESE5004_Stage2/phase2/upstream_sc_baseline
HEAD a3616a68ee44592af6527ca9024a90f1956646ae
branch refs/heads/codex/upstream-sc-baseline-a3616a68ee44

worktree /home/jin/research/SGP_ESE5004_Stage2/phase3a2/fix_e1
HEAD 30bafa420e5cd639e696cbdd56de0e7df36c0e47
branch refs/heads/codex/buildings-e1

worktree /home/jin/research/SGP_ESE5004_Stage2/phase3a2/fix_e2
HEAD 070db2918186829908a02a0b72a7b4426711c653
branch refs/heads/codex/buildings-e2

worktree /home/jin/research/SGP_ESE5004_Stage2/phase3a2/fix_e4
HEAD 9342893fcf467eadbbc410f59c3dbe817d123aa9
branch refs/heads/codex/buildings-e4

worktree /home/jin/research/SGP_ESE5004_Stage2/phase3a4/buildings_accounting_validation
HEAD 50a73d8f531132c5459174a55cac412d5f684462
branch refs/heads/codex/buildings-accounting-validation

worktree /home/jin/research/SGP_ESE5004_Stage2/phase3b2/shipping_allocation_validation
HEAD 85a32dc231458fd753445df38d422b78435b8aad
branch refs/heads/codex/transport-shipping-reviewable-patch
```

## Branches at resume
```
archive/phase1-3-research-snapshot
+ codex/buildings-accounting-validation
+ codex/buildings-e1
+ codex/buildings-e2
+ codex/buildings-e4
  codex/buildings-heat-alignment
  codex/buildings-heat-audit
  codex/buildings-phase3a3
  codex/buildings-phase3a4
  codex/buildings-phase3a5
  codex/buildings-phase3a6
  codex/buildings-phase3a7
+ codex/fix-carbon-config
+ codex/fix-industrial-gdp
+ codex/fix-topology-765-766
+ codex/github-health-audit
+ codex/paper-reference-5bacad70
  codex/phase2-baseline-review
  codex/remaining-sector-phase3c
  codex/research-sc-main
  codex/transport-phase3b1
  codex/transport-phase3b2
  codex/transport-shipping-allocation
+ codex/transport-shipping-reviewable-patch
  codex/transport-shipping-target-guard
+ codex/upstream-sc-baseline-a3616a68ee44
  fix/research-shipping-compat
* research/full-sc-baseline
+ sgp-stage2-asean
```

Identity and hash checks: evidence/RESUME_IDENTITY.json. Draft byte copies: preserved_drafts/ in the working delivery area; exact patches: evidence/resume_diffs/.
