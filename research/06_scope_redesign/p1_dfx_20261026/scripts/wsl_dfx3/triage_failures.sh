#!/bin/bash
# DFX v3: triage of the 3 full-suite failures. (1) where results_project/s1 comes from in the worktree; (2) the S1 test in the MAIN checkout (main HEAD,
# no DFX change) - pre-existing or not; (3) the config vs S1-network cross-border switch keys (names only); (4) rerun the flaky B4P test alone and the
# whole test_dfx_demand.py after the F0.3 test fix.
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
echo "== (1) worktree results_project"; ls -la $WT/results_project 2>&1 | head -3; ls -la $WT/results_project/s1 2>&1 | head -3; git -C $WT check-ignore -v results_project/s1/integrated/integrated_BUILD_RECEIPT.json 2>&1 | head -1; git -C $WT ls-files results_project | head -2
echo "== (2) S1 test in the main checkout ($(git -C $MAIN rev-parse --short HEAD), $(git -C $MAIN branch --show-current))"
( cd $MAIN && env -u GRB_LICENSE_FILE $PY -m pytest -q -p no:cacheprovider tests/research/test_s1_built_networks.py 2>&1 | grep -E "passed|failed|ValueError" | tail -3 )
echo "== (3) switch keys: config vs S1 network meta (worktree)"
( cd $WT && $PY - <<'P' 2>/dev/null
import sys; sys.path.insert(0, "scripts_project")
from pathlib import Path
import pypsa, logging; logging.disable(logging.CRITICAL)
from phase4_static import config
R = config(Path("."), "integrated")["research"]; sw = R["cross_border"]
n = pypsa.Network("results_project/s1/integrated/integrated_2920_3h_unsolved.nc")
m = n.meta.get("research_cross_border", {}).get("switches")
print("config cross_border keys:", sorted(sw)); print("meta switches keys:", sorted(m) if isinstance(m, dict) else m)
print("differing keys:", sorted(set(sw) ^ set(m or {})), "| equal on common keys:", all(bool(sw[k]) == m[k] for k in set(sw) & set(m or {})))
P
)
echo "== (4) reruns in the worktree"
( cd $WT && env -u GRB_LICENSE_FILE $PY -m pytest -q -p no:cacheprovider "tests/research/test_b4p_batch4.py::test_parallel_when_the_probe_passes" tests/research/test_dfx_demand.py 2>&1 | grep -E "passed|failed|^FAILED" | tail -5 )
