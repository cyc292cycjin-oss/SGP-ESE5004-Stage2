# Gate5 cloud portability

Engineering parent: `a55c35a7b6b082e214f79afd46fc06215a9386e4`.
Scientific/lossless freeze: `8b6a50c75d688cd69ce360580d32dd80e8003ed7`.
Frozen daily input SHA256: `7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd`.

The guarded runner now accepts an explicit Linux cloud resource mode. It reads
the process cgroup and every visible ancestor, limits memory and CPU by the
strictest applicable quota, and keeps host `/proc/meminfo` values diagnostic.
Cloud admission retains the original required physical headroom plus the
2 GiB host guard. Windows commit is inapplicable and is never fabricated.
The 512 MiB guest guard, 2 GiB available-memory guard, declared process-RSS
budget, 14,400 s wall guard, and original Windows path remain in place.
A separate 20 GiB free-data-disk planning reserve covers runtime artifacts.

An explicit result destination keeps cloud mapping, float64 mmap vectors,
logs and exports under `/root/autodl-tmp/SGP/runs/cloud_gate5_*`.
The original transfer, scaling, primal qualification, single native solution
retrieval, original-unit checks and sequential export/readback are unchanged.
No input, model coefficient, constraint, tolerance, presolve, IPM, crossover,
two-thread setting or 10,800 s solver limit changes.

The cloud preflight checks exact Git/file identities, Python distribution
versions and conda builds, native HiGHS/HDF5/NetCDF identities, no-solver tests,
and actual frozen-network/hook model construction without solving.
It is not itself run authorization. A separately supplied human receipt must
match its SHA, Git SHA, input SHA, one unique run ID and accepted budget.
Immediately before native execution, an exclusive, fsynced claim consumes
the stable human-authorization ID. A second claim is rejected even with a
different run ID. A durable worker retains child exit state and failure logs;
unqualified results always retain null objective/result and NOT_RUN dynamics.
PASS also requires the exported network hash and completed dynamic/objective
reconciliation evidence. No Gate6 or formal experiment dispatch exists.

Local verification: eight no-solve suites passed; the two changed integration
and cloud suites were rerun after the final preflight/collector additions.
Coverage includes cgroup ancestor limits, missing/invalid limits, exact guard
boundaries, path validation, durable claim replay, portable exact transfer,
environment mismatch, hash/missing-file/path-traversal rejection, and retained
unqualified/time-limit/crash evidence. Small canonical transfer, int32 overflow,
mmap, lifecycle, mapping and qualification tests remain bound in
`GATE5_LOSSLESS_RESULT_QUALIFICATION_TESTS.json`.

Local frozen-input metadata and source-operation identity checks passed with
365 snapshots, 100 geographical nodes, 171 accounts, 1737 Loads, 187400.4 MW
stock, 807 pending fixed terms, 200 null policy weights and native lv_limit.
Full cloud hook/preflight validation and the single authorized real solve are
subsequent deployment gates; this engineering commit itself performs no solve.
