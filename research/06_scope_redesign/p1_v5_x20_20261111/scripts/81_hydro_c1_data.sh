#!/bin/bash
# X20 C-1（决策 252）：生成 HYDRO_CANDIDATE_UNIT_INFLOW_V5.csv（Ember 年度文件 = 决策 74 的同一文件，SHA256 在脚本内核对；IHA 2024 取自 X03 HYDRO_STOCK_CHECK.csv）
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; W=/mnt/d/ResearchWorkspaces/ASEAN/work
cd /home/jin/wt_v5_x20 || exit 1
$PY scripts_project/v5_hydro_unit_inflow_data.py --ember $W/p1_step4b_20261016/sources_s4b/ember/release_generation_yearly_global.csv --iha $W/p1_v5_x03_renew_20261111/HYDRO_STOCK_CHECK.csv
sha256sum research_inputs/hydro_v5/HYDRO_CANDIDATE_UNIT_INFLOW_V5.csv
