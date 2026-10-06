# Gate5 lossless memory optimization freeze

Freeze date: 2026-10-07. Branch: `research/full-sc-baseline`.
Accepted implementation baseline: `fec654693f6408a921b1750a5c5285095cfd00c8`.
This freeze authorizes no Gate5 solve, Gate6, Integrated, or Disconnected run.

## Verified evidence

The 11 pending files matched the accepted delivery hashes before any edits.
Four scientific/resource core sources and the frozen daily input were unchanged.
The accepted package's 46 files were rehashed. Full 365-snapshot mathematical
equivalence was rechecked by directly comparing its saved native transfer receipt
with run04: all 11 identity fields pass, including every constraint block, labels,
objective/bounds, D/R mapping and binary64 certificate. The completed full-model
experiment was not repeated.

Variables: 2,450,005 -> 2,450,005; constraints: 6,042,238 -> 6,042,238;
nonzeros: 11,403,496 -> 11,403,496. SCIENTIFIC_MODEL_CHANGED=NO;
MATH_PROGRAM_EQUIVALENT=PASS. This is not a Gate5 solution-validation pass.

Seven no-solve suites / 50 checks pass. Native HiGHS run and presolve entrypoints
are blocked. Coverage includes independent sparse canonical handoff, binary64
precision, qualification and negative candidates, one native solution retrieval,
source release, signed/unsigned int32 overflow and noninteger rejection, mmap,
small actual PyPSA mapper and NetCDF readback, resource/admission/authorization
guards. An integration test uses one mock execution. No native solver ran.
Solve-dependent legacy precision/inventory tests are deliberately not invoked.

## Frozen scientific and numerical contract

Preserve 365 snapshots, 100 geographical nodes, 171 accounts, 1737 Loads,
187400.4 MW stock, 807 external pending terms, 200 null policy weights,
policy OFF for Gate5 validation, all 1003 research hook groups, native lv_limit.
These accepted boundaries remain bound to the unchanged input SHA256
`7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd`.
Coefficients, RHS, bounds, costs, capacities, efficiencies and solution values
remain float64. No snapshots, carriers, sectors, constraints or options are removed;
no load shedding/free supply, solver tolerance changes, disabled presolve/IPM/
crossover, or 12-digit LP solve path are introduced. Fixed-block projection has
zero executable candidates and zero implemented variable/constraint savings.

## Adopted future lifecycle

BUILD -> exact transfer -> persist D/R + labels + hashes on D -> verify transfer
fidelity -> release unreachable PyPSA/Linopy/source objects -> allocator trim
where supported -> SOLVE -> qualify one native solution -> mmap compact float64
results on D -> release native solver when safe -> reload frozen network ->
reconstruct labels/model identity -> inverse-map original units -> PyPSA mapping
-> dynamic/physical validation -> export.

Only a separately authorized future attempt may cross SOLVE. `getSolution` is
called at most once and reused; failed qualification cannot reach PyPSA writeback.
The guarded runner is wired to this lifecycle and retains its prior authorization,
clean-tree, input, environment, qualification and resource gates.

## Memory evidence and admission

Accepted measured source-lifetime RSS drop after mapping persistence is
1,618,907,136 bytes / 1.508 GiB. Build/transfer-only kernel high-water mark is
4,254,740,480 bytes / 3.963 GiB. It must not be subtracted from run04's
7,274,795,008 bytes / 6.775 GiB interrupted full-solve sampled peak as a saving.
Complete postsolve peak remains unknown.

Conservative available-memory floors remain guest 9,959,149,568 bytes (9.275 GiB),
host physical 12,106,633,216 bytes (11.275 GiB), host commit 9,959,149,568 bytes.
No reduction follows from the 1.486 GiB pre-persistence theoretical adjustment.
The next step is read-only resource preparation; an 11GB memory / 4GB D-drive
swap candidate is not readiness evidence. A measured MEMORY_READY=PASS, clean
tree, equal local/remote HEAD, unchanged frozen input and passing lossless tests
must precede separate authorization for one fifth Gate5 attempt.

## Reproduction and evidence locations

Linux root remains `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`.
All new test output/temp files go under D; use the D source-path override
`D:\ResearchWorkspaces\ASEAN\workspace_tools\final_assembly_paths.D.json`.
Run only the no-solve suite with:

```bash
/home/jin/miniforge3/envs/pypsa-earth/bin/python scripts_project/run_lossless_freeze_tests.py --output /mnt/d/ResearchWorkspaces/ASEAN/work/<new-freeze-test-directory>
```

Versioned `lossless_memory_freeze_20261007/` evidence contains initial audit,
fresh test receipts, full identity recheck, accepted study summary and its manifest.
Original detailed evidence and mapping payloads remain in the D delivery
`outputs/phase4_gate5_lossless_memory_20261007`; its FINAL ZIP SHA256 is
`949e006d3e51ddb138751224cb4566036e0c5487b018e2e8dccd3213c1acc770`.
No historical evidence, failed attempts, source caches or protected branch is removed.
