# Gate4 resume test report

Tests run in the existing WSL pypsa-earth environment (Python3.11.13/PyPSA0.30.3), no optimizer. Exact commands, exit codes and log hashes: `evidence/resume/TEST_RECEIPTS.json`.

| Suite | Result | Scope |
|---|---|---|
| Assembly input tests |17 PASS| Includes rejecting explicit/zero EV, dropped missing obligations, duplicate RoadParent Load; SG constant bunker and post-build carbon ordering |
| Assembly preflight | BLOCKED_INPUT_FREEZE, expected exit2 | Correct refusal before network construction; not a readiness PASS |
| Gate1 static |20 PASS| Research contract/config guards |
| Gate2 demand/accounting |70 PASS| Preserved historical accounting contract |
| Gate3 carrier/carbon |60 PASS| Synthetic/static architecture, not actual assembled network |
| Gate3 config |PASS| Existing carrier configuration invariants |
| Topology regression |9 PASS| Existing single-row repair retained; no topology reinvestigation |
| Buildings / Shipping full regression |NOT_RERUN_UNCHANGED| Production builders and historical source capsules unchanged |
| Actual-network tests |NOT_RUN_NO_NETWORK| No component inventory, finite Load/conservation, interconnector set or carbon-attribution claim |

Gate3 logs retain a PROJ database startup warning from the existing environment. Its60 bounded tests passed, but this is not a geographical runtime certification. The first native Windows test attempt also encountered sandbox temporary-directory permissions in the hash-tamper fixture; the full authoritative17-test suite subsequently passed in WSL without altering its assertions.

The CSV export roundtrip and error scan passed. `PRESERVATION_GUARD.json` verifies unchanged Gate2 input capsules, upstream prepare_sector_network.py and other untouched contracts. A source-qualified number is distinct from a validated100-cluster, full-year3h allocation.
