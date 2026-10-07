# Gate5 exact export engineering repair

The sole cloud solve `cloud_gate5_20261007T151625Z` at deployment
`711e18b3aad65dc9aa8083d16c06c1e6aa841e04` returned native Optimal, with
one native solution retrieval. All 9,494 original-unit dynamic/physical checks
passed before export. The original run remained FAILED_ENGINEERING because
the strict export/readback signature rejected Generator.p. Preserve that run,
its manifests, original NetCDF, mapping and native arrays unchanged.

Reconstruction from the saved qualified float64 arrays, with Highs.run,
Highs.presolve and Highs.getSolution trapped, reproduced the fault. Frozen
PyPSA 0.30.3 elided 518 all-zero Generator.p columns. Readback reordered columns
and replaced some negative zeros with positive zeros. Label-aligned values
had zero numerical difference; both frames were float64.

The exporter now explicitly writes every nonempty dynamic frame in the standard
NetCDF schema after PyPSA prepares static data, snapshots and metadata. Default
columns and signed zeros are retained. The original exact dtype/order/value
signature and physical readback checks are unchanged. A one-ULP corruption
still fails. Unicode, all-zero, signed-zero and all-NaN roundtrips pass, and the
original network is released before readback. Eight no-solver test suites pass;
their receipts and exact code hashes are bound in the qualification receipt.

The collector derives dynamic status from the qualified check evidence, so a
later export failure cannot misreport completed checks as NOT_RUN. Gate5 PASS
still requires successful export, qualification, all checks and the exact file
hash. Failed export and failed physical-check negative cases remain failures.

Recovery may only use the already saved qualified native arrays in a new output
directory. No second solve, presolve or getSolution is authorized. Scientific
freeze 8b6a50c75d688cd69ce360580d32dd80e8003ed7, frozen input, float64 values,
formulation, resource thresholds, solver settings and tolerances are unchanged.
The actual solve SHA and later export-recovery SHA must be reported separately.
