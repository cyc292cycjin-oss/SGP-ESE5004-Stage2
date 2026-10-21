#!/bin/bash
# S4Q-3 (read only, no solver, licence variable removed): verdict of decision 123 point (5) with s4q_judge.py on the two run folders.
set -u
W=/home/jin/wt_s4q_20261020; RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=$W/research/06_scope_redesign/p1_step4q_20261020; E=$D/evidence/s4q_3; SH=/home/jin/s4q_local/judge_shadow
export PYTHONHASHSEED=0; unset GRB_LICENSE_FILE
rm -rf $SH; mkdir -p $E
R=/home/jin/s4q_local/pkg/runs
before=$(cat $R/*/*/PRECISION.json $R/*/*/EXPORTS.json | sha256sum | cut -c1-16)
cd $W
/usr/bin/time -v $PY $D/scripts/s4q_judge.py --repo $W --s4m2 $RM/results_project/s4m/s4m2/solves --builds $RM/results_project/s4m/s4m1/builds \
  --ref-duals-integrated $RM/results_project/s4m/s4ms2/solves/s4m_A_integrated_rerun \
  --path t8=$R/20261020T001252Z_564 --path t16=$R/20261020T004641Z_8849 --shadow $SH --out $E > $E/judge_stdout.txt 2> $E/judge_stderr.txt
echo "JUDGE_EXIT:$?"; cat $E/judge_stdout.txt | cut -c1-900
grep -E "Elapsed|Maximum resident" $E/judge_stderr.txt
grep -vE "Warning|warn|PROJ|^\s" $E/judge_stderr.txt | grep -v "Command being\|time\|Percent\|size\|faults\|switches\|swaps\|inputs\|outputs\|Socket\|Signals\|Page\|Exit status\|Average\|Minor\|Major\|Voluntary\|Involuntary\|File system" | tail -5
after=$(cat $R/*/*/PRECISION.json $R/*/*/EXPORTS.json | sha256sum | cut -c1-16)
echo "run folders' PRECISION/EXPORTS unchanged: $([ "$before" = "$after" ] && echo yes || echo NO)"
