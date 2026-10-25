#!/bin/bash
# wait (<= 9.5 min) for a test log's EXIT line: bash wait_tests.sh <TAG>
f=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/evidence/tests/TESTS_${1:?tag}.log
w=0; while ! grep -q "^EXIT" "$f" 2>/dev/null && [ $w -lt 570 ]; do sleep 10; w=$((w + 10)); done
grep -q "^EXIT" "$f" || { echo "NOT_DONE after ${w}s"; tail -c 300 "$f"; exit 1; }
grep -E "^(FAILED|ERROR)|passed|failed|^EXIT" "$f" | tail -14
