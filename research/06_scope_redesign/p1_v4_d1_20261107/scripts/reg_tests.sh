#!/bin/bash
# D1: every tests/research file that reads DATA_REGISTRY.csv, without the files that call a solver (optimize( / .solve( / linprog).
set -u
R=/home/jin/wt_v4_d1
cd $R || exit 1
F=$(grep -l 'DATA_REGISTRY' tests/research/*.py | while read f; do grep -qE 'optimize\(|\.solve\(|linprog' $f || echo $f; done)
echo "files: $(echo $F | wc -w); skipped (solver strings): $(grep -l 'DATA_REGISTRY' tests/research/*.py | while read f; do grep -qE 'optimize\(|\.solve\(|linprog' $f && echo $f; done | tr '\n' ' ')"
bash /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107/scripts/ut.sh reg_tests $F
