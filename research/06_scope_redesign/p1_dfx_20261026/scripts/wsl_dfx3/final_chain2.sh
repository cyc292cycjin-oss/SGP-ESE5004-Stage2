#!/bin/bash
# DFX v3: remove the session's results_project/s1 link (baseline environment: S1 tests skip), commit the F0.3 test fix + drafts, run the full suite again.
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
echo "tests using assembly_v1: $(grep -rl assembly_v1 $WT/tests --include=*.py | wc -l)"
[ -L $WT/results_project/s1 ] && rm $WT/results_project/s1 && echo "s1 link removed (was -> $MAIN/results_project/s1; main results untouched)"
ls -la $WT/results_project/
bash /home/jin/dfx3/collect_evidence.sh dry_run_v8b > /dev/null
echo "== commit"; bash /home/jin/dfx3/commit.sh /home/jin/dfx3/msg_phase3a.txt 2>&1 | tail -3
echo "== full test suite (second run)"; bash /home/jin/dfx3/tests_full.sh
