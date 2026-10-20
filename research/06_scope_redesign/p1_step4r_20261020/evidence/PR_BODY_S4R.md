## S4R: unification plan and gates redesign (decisions 126 / 128) + supplement 01 (decision 129) — read-only, draft, stacked on #42

Branch `codex/s4r-unification-plan-20261020` from the S4P head 69b67a97. No solve, no cloud, no Gurobi call, no change to production code, registry, networks or results. All fixes are written as proposals for M08 / M10 after review.

### Commits
- 4fbddf28 S4R-0 and comparison tables (R1 demand anchor, R2 potentials, R3 LNG, R5 CO2 storage, R6 costs / WACC).
- d45955ea `GATES_V6.md` + SHA256 only (defined before any retro-evaluation).
- d0c299a9 `S4R_PLAN.md`, gates retro-evaluation, unification checklist, implementation plan, registry rows, download list, sources, evidence, progress.
- 50bd2f8d close-out (progress, ledger entry, PR body).
- 48ad097d supplement 01 (decision 129): revised R1 / R2 / R8 / R7 items, `GATES_V6_NOTES.md`, updated tables and registry rows.
- SUPP01_CLOSE_SHA supplement 01 close-out (progress record, ledger entry).

### Supplement 01 (decision 129) in brief
- R1.3: one physical-output rule for 11 countries, 2050 = min(base 2024 x G^(years/28 x 0.5), per-capita saturation x population, national plan cap); plan caps never raise output (VN steel 70 -> 40.7 Mt, cement 107.0 Mt); base year 2024 (worldsteel WSIF 2025; USGS MCS 2025 for ID / VN, USGS Minerals Yearbook world table DATA_PENDING for the other nine, interim values flagged); elasticity 0.5 and saturation 1.0 / 0.6 t/cap registered as assumptions (grade C) with sensitivity ranges 0.3-0.8 and 0.6-1.2 / 0.4-0.8 (literature gives saturation evidence only: Bleischwitz 2018, van Ruijven 2016, Pauliuk 2013).
- R1 electricity: only activity levels are anchored; base load = AEO8 ATS country electricity x buildings + agriculture share (11 countries 1,032 -> 966 TWh, all non-negative; residential check 428 vs 386 TWh); industry electricity endogenous (the M08-5 formula "ATS electricity - route electricity" is withdrawn); transport anchored at service level (model final energy 1.1-3.2 x the ATS anchor).
- R2: main run changes only the solar density 4.6 -> 5.1 MW/km2 (p_nom_max x 1.109, no raster recomputation); open forest 121-126 becomes an upper-bound sensitivity with a trigger rule (cap binding and shadow price x capacity >= 1 bn); the model / ESMAP Level-1 ratio 0.18-0.57 decomposes into 6-18 % density parameter and the rest basis differences (protected areas <= 17-84 %, forest and other criteria >= 33-71 %), same type as PyPSA-Eur. Copernicus LC100, WDPA raster, GEBCO 2025 and EEZ v11 are already in the author cache; the download list is split into main-run (shipping density raster, USGS yearbook cement table, worldsteel 2024 SG / MM, UN WPP TL, Eurostat HICP) and sensitivity-only groups.
- R8: k = 10 kept, `GATES_V6.md` unchanged (SHA256 5c0aa8b8...7f9); new `GATES_V6_NOTES.md` records that barrier solutions without crossover carry ~40-240 x BarConvTol dual-sign error on 56x3h optimal runs and ~1e-2 on 365x24h solutions; D2 is a diagnostic only.
- R7: with the VN storage cap 236 -> 106 Mt/a, ~130 Mt/a re-routes to intra-ASEAN shipping (MY), +1.9-2.0 bn/a per scenario; disconnected VN shipping ~225 Mt/a (~2/3 of its stored CO2); if maritime CO2 trade counted as interconnection, +5.5 bn/a. Basis for interview item 9.
- Lists: 9 interview items; 2 user to-dos (download list, 42 proposed registry rows). Combined impact widened to B6 ~25-50 bn, VN share 55-70 %.

### Deliverables (`research/06_scope_redesign/p1_step4r_20261020/`)
- `S4R_PLAN.md` (revised per supplement 01), `GATES_V6.md` (SHA256 `5c0aa8b8…7f9`), `GATES_V6_NOTES.md`, `GATES_RETRO_COMPARISON.csv/.md`, `UNIFICATION_CHECKLIST.csv/.md` (209 cells, 64 flagged), `DEMAND_ANCHOR_COMPARISON`, `POTENTIAL_COMPARISON`, `LNG_CAPACITY_COMPARISON`, `CO2_STORAGE_UNIFIED`, `COST_CURRENCY_FIXES`, `COUNTRY_WACC_SENSITIVITY_TABLE` (csv + md), `IMPLEMENTATION_PLAN.md`, `REGISTRY_ROWS_PROPOSED.csv` (42 rows), `USER_DOWNLOAD_LIST.md`, `EXTERNAL_SOURCES_S4R.md` (41 sources), `S4R_EVIDENCE.json`, `S4R_PROGRESS.md`, `scripts/`, `evidence/`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
