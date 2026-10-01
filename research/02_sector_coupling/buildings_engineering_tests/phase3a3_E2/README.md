# E2: Phase 3A-3 national conservation validation

Source fix: `31037d60d69fa762c9ed8ec9ce8289d95bd6a181`; frozen baseline: `a3616a68ee44592af6527ca9024a90f1956646ae`.
The source fix already exists as a separate commit. This follow-up adds stricter,
11-country-label/22-node synthetic regressions. It changes no source or input.

Run with the existing PyPSA 0.30.3 environment:
`python research/02_sector_coupling/buildings_engineering_tests/phase3a3_E2/test_buildings_fixes.py --repo . --fix E2 --output /tmp/E2_audit.json`

The matching test on frozen U must fail; this branch must pass. Numeric energy
tolerance: abs(error) <= 1e-6 MWh + 1e-12 * abs(expected MWh).
Test countries are labels, not measured demand. No optimizer. Not merged into R.
E3 and real-data electricity accounting remain outside this patch.
