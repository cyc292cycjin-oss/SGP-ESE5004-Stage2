#!/bin/bash
# X20 A 段：抽查子代理报告中的关键行号（只读，代码副本 = commit 26c2e47d）
set -u
C=/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111/cache/code
cd "$C" || exit 2
show() { echo "---- $1:$2"; sed -n "$2p" "$1" | cut -c1-220; }
show scripts_project/s4a_profiles.py 110,121
show scripts_project/s4b_3_wind_calibration.py 38,38
show scripts_project/s4b_3_wind_calibration.py 111,111
show scripts_project/s4b_3_wind_calibration.py 145,149
show scripts_project/s4a_fleet.py 92,101
show scripts_project/s4c_2_data.py 22,22
show scripts_project/s4c_2_data.py 39,39
show scripts_project/s4c_layers.py 334,334
show scripts_project/s4c_layers.py 351,351
show scripts_project/s4c_layers.py 364,369
show scripts_project/s4b_candidates.py 189,201
show scripts_project/s4b_2_candidates_data.py 46,47
show scripts_project/s4b_2_candidates_data.py 89,93
show scripts_project/s4b_2_candidates_data.py 124,124
show scripts_project/s4f_layers.py 80,90
show scripts_project/s4f_layers.py 132,162
show scripts_project/s4j_layers.py 75,80
show scripts_project/s4j_layers.py 128,145
show scripts_project/s4a_2_fleet_data.py 34,34
show scripts_project/s4a_2_fleet_data.py 91,91
show scripts_project/asset_survival.py 18,26
show scripts_project/m08b_demand.py 324,324
show scripts_project/m08b_demand.py 335,335
show scripts_project/m08b_demand.py 383,395
show scripts_project/s3_layers.py 96,116
show scripts_project/v4_common.py 60,100
show scripts_project/s2_solve.py 281,281
show scripts_project/s2_solve.py 449,449
show scripts_project/s2_network.py 310,320
show scripts_project/s2_network.py 349,360
show scripts_project/s2_network.py 400,420
show scripts_project/s2_network.py 422,424
show scripts_project/s2_network.py 449,449
show scripts_project/s2_network.py 495,510
show scripts_project/v5/gates_v6.py 34,43
show scripts_project/s2_layers.py 187,204
show configs/research/baseline.yaml 236,256
show configs/research/baseline.yaml 272,290
show configs/research/baseline.yaml 318,336
show configs/research/baseline.yaml 370,386
show configs/research/baseline.yaml 512,536
