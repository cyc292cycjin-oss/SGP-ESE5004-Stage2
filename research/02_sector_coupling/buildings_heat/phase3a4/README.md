# Phase 3A-4 handoff

Material Passport: academic-research-suite; inline engineering/accounting audit; Phase 3A-4 v1; 2026-10-01. VERIFIED applies only to stated code/test/hash observations; accounting methods are ANALYZED/proposed and scientific inputs remain PENDING.

Start with [readiness](BUILDINGS_PHASE3A4_READINESS.md). This folder contains the six requested Markdown reports and the combined CSV matrix; the two requested data/schema CSVs are in `data_registry/buildings_phase3a4/`. The empty template there is optional convenience, with zero scientific rows.

`integrate_fixes.py` is the retained one-time execution record: it refuses an existing destination and is not a routine rerun command. Its narrowly scoped CRLF resume option documents the actual preflight event and exact inspected commit. Do not reset or rerun integration blindly. `record_combined_validation.py` is also a one-time commit operation. All user-approved fixes and original tests already reside in the independent validation worktree.

For subsequent verification, run the existing `test_buildings_fixes.py --repo <validation worktree> --fix combined --output <new receipt>` in the recorded PyPSA environment. `check_accounting_contract.py` only exercises labelled synthetic mathematical identities. `check_integrated_e3.py` confirms the remaining known E3 flaw without patching it. `build_tables.py` + `export_tables.mjs` regenerate review tables from receipts; they never create scientific model inputs. `build_reports.py` regenerates the report summaries from completed receipts.

Review evidence distinctions: VERIFIED=code/test/hash observation; analytical derivation=accounting identity under stated common-boundary assumptions; inference=why current input gaps prevent valid E3 execution; proposed test=real-data workflow/dispatch checks not yet run. A pass in the first category does not imply the latter categories passed.

The delivery ZIP includes `provenance/phase3a4_buildings_validation.bundle`, a verified Git history delta with prerequisite U `a3616a68ee44592af6527ca9024a90f1956646ae`. Its hash and final branch identity are in `evidence/INTEGRATION_BUNDLE.json`. Restore only into an audit clone containing that exact U commit: `git bundle verify <bundle>` then `git fetch <bundle> refs/heads/codex/buildings-accounting-validation:refs/heads/codex/buildings-accounting-validation`. Do not force an existing branch. The ZIP also retains prior Phase3A3/3A2/3A1 evidence dependencies; downloaded/reference materials remain evidence, not newly accepted model inputs.

Fallacy scan for this deterministic engineering task: Simpson/ecological aggregation and selection/survivorship concerns prevent nationalizing small household samples or aggregating R/S before checks. No statistical causal effect or association is estimated; Berkson, collider, base-rate neglect, regression-to-mean, look-elsewhere, forking-paths significance, correlation/causation and reverse-causality claims are not applicable to the function regressions. No independent peer review is claimed.

The existing PROJ warning limits environment/GIS readiness; no GIS transforms or optimizer were tested. Full-SC remains unaccepted. Prior audit histories are preserved. Root workspace may retain pre-existing untracked `outputs/` and `work/`; this does not describe the clean model and project-audit worktrees.
