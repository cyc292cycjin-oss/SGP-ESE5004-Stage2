S4P (decision 122 point 2): full-model, 11-country audit of the 365x24h screening results - read-only (no solve, no cloud, no model / network / config / result changed). Supplement 01: currency and price-year consistency check (merged into aspect 7); NZE deprioritised (decision 124).

Stacked on #40 (S4O, base `codex/s4o-production-20261019`, branch from 0b681881).

Deliverables under `research/06_scope_redesign/p1_step4p_20261020/`:
- `S4P_REPORT.md` - summary, analysis A (per-country channel decomposition, ledger identity max diff 3e-5 EUR, B6 69.243 bn EUR2020), matrix summary per aspect, analysis B (cross-entity consistency), analysis C (ranked proposed fixes), judgement on the "Viet Nam about 3/4" share, currency / price-year section 4.7.2, user decisions.
- `COUNTRY_AUDIT_MATRIX.csv` / `.md` - 13 objects x 8 aspects (104 cells: 36 "to verify", 0 "error").
- `PROPOSED_FIXES.md` - F1-F14 ranked by magnitude (all PROPOSED, none applied).
- `S4P_EVIDENCE.json`, `EXTERNAL_SOURCES.md`, `evidence/EXT_*_BENCHMARKS.md/.json` (298 web-sourced records with institution / document / year / page / URL, 24 DATA_PENDING).
- `A_CHANNEL_*`, `ASPECTS_TABLES.md`, `ASPECT*.csv`, `POOL_SETTLEMENT_BY_ENTITY.md`, `scripts/` (6 read-only analysis scripts).

Key findings: the Viet Nam share of B6 is rule-robust (70.6-75.9 % under four settlement rules) and the direction is credible (largest importer, 757 TWh = 60 % of its fixed load), but the magnitude is set by structural caps that bind simultaneously for VN: solar candidate cap (411 GW = 0.43x the PDP8 technical potential; binding in all scenarios almost region-wide), LNG terminal cap 2.5x stock (VN / MY / KH binding in all scenarios; VN imports 220 TWh of H2 for methanation when disconnected), the 20 GW per-line expansion limit without a country-pair cap (LA-VN 112 GW built vs APG plan 0.6 GW), industrial demand (VN TFEC about 1.8x ERIA, cement 581 Mt vs a 150 Mt capacity cap) and the biomass-overflow-to-methane rule. No unit-level error invalidating the 365x24h results was found.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
