# E1/E2/E4 combined validation

Engineering integration only, from frozen U a3616a68ee44592af6527ca9024a90f1956646ae.
All approved source and validation patches are recorded with `cherry-pick -x`.
The three following documentation corrections record actual PyPSA 0.30.3.
Original cases: E1=5, E2=7, E4=1. Final strict checks: 777+197+88=1062 PASS.
All staged active-fix regression suites passed. No solver was invoked.
The source bytes equal the previously tested Phase3A3 combined overlay.
P/U/R/T and 19 retained model input files are unchanged.

The 18 synthetic accounting-contract checks demonstrate proposed identities and
reject duplicate/lost demand. They do not close actual ASEAN E3 accounting.
The integrated E3 diagnostic still reproduces total-target + omitted Services.
E3 patch is NOT implemented; data acceptance remains pending.

Runtime: Python3.11.13 / PyPSA0.30.3 / NumPy1.26.4 / pandas2.3.1.
The existing PROJ database warning persists; these tests do not call GIS transforms.
`INTEGRATION_RECEIPT.json` records the tested parent commit; this documentation
commit does not change model source. Final HEAD is recorded by the research audit.
