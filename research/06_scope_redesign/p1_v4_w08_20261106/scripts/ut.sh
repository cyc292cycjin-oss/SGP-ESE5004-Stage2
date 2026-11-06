#!/bin/bash
# W08: run selected pytest files in the W08 worktree (no solver: the selected files are grepped for optimize( / .solve( / linprog first).
# usage: ut.sh <log name> <test files / node ids ...>
set -u
R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; LOG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106/logs
mkdir -p $LOG; name=$1; shift
cd $R || exit 1
files=$(for t in "$@"; do echo "${t%%::*}"; done | sort -u)
if grep -nE 'optimize\(|\.solve\(|linprog' $files; then echo "REFUSED: a selected test file solves"; exit 4; fi
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
$PY -m pytest -q -p no:cacheprovider "$@" > $LOG/ut_$name.txt 2>&1; rc=$?
tail -15 $LOG/ut_$name.txt; echo "EXIT:$rc"
