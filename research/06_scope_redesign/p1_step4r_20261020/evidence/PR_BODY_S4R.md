## S4R: unification plan and gates redesign (decisions 126 / 128) — read-only, draft, stacked on #42

Branch `codex/s4r-unification-plan-20261020` from the S4P head 69b67a97. No solve, no cloud, no Gurobi call, no change to production code, registry, networks or results. All fixes are written as proposals for M08 / M10 after review.

### Commits
- 4fbddf28 S4R-0 and comparison tables (R1 demand anchor, R2 potentials, R3 LNG, R5 CO2 storage, R6 costs / WACC).
- d45955ea `GATES_V6.md` + SHA256 only (defined before any retro-evaluation).
- d0c299a9 `S4R_PLAN.md`, gates retro-evaluation, unification checklist, implementation plan, registry rows, download list, sources, evidence, progress.

### Deliverables (`research/06_scope_redesign/p1_step4r_20261020/`)
- `S4R_PLAN.md`: summary within 20 lines; R1–R8 recommended options with evidence and PyPSA-Eur conformance / deviation; R10 impact estimate; two lists (user decisions: 12; questions for the senior: 7).
- `GATES_V6.md` (SHA256 `5c0aa8b8…7f9`), `GATES_RETRO_COMPARISON.csv/.md` (20 historical runs, V5 vs V6, from exported metrics only; definition unchanged after the retro).
- `UNIFICATION_CHECKLIST.csv/.md` (19 input classes x 11 countries, 54 flagged cells).
- `DEMAND_ANCHOR_COMPARISON`, `POTENTIAL_COMPARISON`, `LNG_CAPACITY_COMPARISON`, `CO2_STORAGE_UNIFIED`, `COST_CURRENCY_FIXES`, `COUNTRY_WACC_SENSITIVITY_TABLE` (csv + md).
- `IMPLEMENTATION_PLAN.md`, `REGISTRY_ROWS_PROPOSED.csv` (31 rows), `USER_DOWNLOAD_LIST.md` (9 items), `EXTERNAL_SOURCES_S4R.md` (29 sources, DATA_PENDING list), `S4R_EVIDENCE.json`, `S4R_PROGRESS.md`, `scripts/` (8 read-only scripts), `evidence/`.

### Headline findings (INFERENCE unless marked)
- R1: the S4P demand gap is mostly the fixed PyPSA-Eur 2050 industrial routing (fixed electricity = 1.7–4.2x AEO8 ATS electricity) plus BAS anchoring (model TFEC 1,220 Mtoe vs ATS 746). Recommended anchor: AEO8 ATS per-capita x population; VN cement 581 -> 107 Mt, steel 80 -> 70 Mt.
- R2: model solar caps are 0.18–0.57 of ESMAP Level 1 x 5.1 MW/km2 in all 11 countries (systematic; density 4.6 vs 5.1 and forest classes).
- R3: LNG table consistent with GEM 2025-09; 7,018 EUR/MW/a has no source (DATA_PENDING) -> 8,020 EUR2020/MW/a; recommend removing the 2.5x cap.
- R5: VN 11.8 -> 5.30 Gt, PH 22.3 -> 0.067 Gt (ERIA-GCCSI 2024 P50).
- R6: HICP deflator (removes +4.8 %), SMR = technology-data nuclear x 1.067, report currency USD2020 at 1 EUR2020 = 1.1422 USD2020; country real WACC 2.9–11.0 %.
- R8: all 10 runs with a PRECISION file are ACCEPTED_LAYER2 under V6 (G2.2 pending); D2 dual budget question (k = 10 vs 100) left for the user, definition not changed.
- R10: B6 expected to fall from 69 bn to roughly 25–45 bn with VN share 55–70 % (still largest); to be verified in M10.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
