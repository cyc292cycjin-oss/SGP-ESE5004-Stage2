#!/bin/bash
# D2c: run selected pytest files in the D2c worktree (no solver: the selected files are grepped for optimize( / .solve( / linprog first).
# usage: ut.sh <log name> <test files / node ids ...>
set -u
R=/home/jin/wt_v4_d2c; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; LOG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2c_20261109/logs
mkdir -p $LOG; name=$1; shift
bash /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2c_20261109/scripts/sync.sh > /dev/null
cd $R || exit 1
files=$(for t in "$@"; do echo "${t%%::*}"; done | sort -u)
if grep -nE 'optimize\(|\.solve\(|linprog' $files; then echo "REFUSED: a selected test file solves"; exit 4; fi
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
$PY -m pytest -q -p no:cacheprovider "$@" > $LOG/ut_$name.txt 2>&1; rc=$?
tail -25 $LOG/ut_$name.txt; echo "EXIT:$rc"
