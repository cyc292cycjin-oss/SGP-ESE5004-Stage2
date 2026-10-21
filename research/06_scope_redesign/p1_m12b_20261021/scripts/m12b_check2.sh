#!/bin/bash
# M12b 前置核对 2（只读）：M08b 补充 01 冒烟输出与网络
set -u
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b
echo "=== builds_s01"
find $R/builds_s01 -maxdepth 2 -type f -printf '%p %s %TY-%Tm-%Td %TH:%TM\n' | sort
echo "=== smoke_s01"
find $R/smoke_s01 -maxdepth 3 -printf '%p %s %TY-%Tm-%Td %TH:%TM\n' | sort
echo "=== smoke script"
cat /home/jin/m08b_s01_smoke.sh 2>/dev/null || ls /home/jin/m08b_s01_* /home/jin/m08b_smoke*
echo "=== m12_local/m08b_s01_nets"
ls -la /home/jin/m12_local/m08b_s01_nets /home/jin/m12_local/m08b_variants
echo "=== m08a_run_batch one_run"
cd /home/jin/wt_m12_20261021
grep -n 'one_run\|s2_solve\|DUAL\|export\|c1_precision\|gates_v6' scripts_project/m08a_run_batch.sh | head -80
