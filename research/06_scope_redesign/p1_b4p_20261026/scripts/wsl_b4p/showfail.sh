#!/bin/bash
# show the assertion lines of the failed tests in a test log: bash showfail.sh <TAG> <test name substring> ...
f=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/evidence/tests/TESTS_${1:?tag}.log; shift
for t in "$@"; do
  echo "===== $t"
  awk -v t="$t" 'index($0, "_ " t) {p=1} p && /^_{5,} test_/ && !index($0, t) {p=0} p' "$f" | grep -E "^(E |>|tests/research)" | cut -c1-600 | head -14
done
