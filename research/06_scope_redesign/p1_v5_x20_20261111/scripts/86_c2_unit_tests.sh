#!/bin/bash
# X20 C-2：不依赖导出剖面的单元测试（分位档、Jensen 性质、开关集、基线配置、C-1 回归、v4 表目录身份）
cd /home/jin/wt_v5_x20 || exit 1
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
/home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest -q -p no:cacheprovider --basetemp=/tmp/x20_pytest_c2 tests/research/test_v5_x20.py \
  -k "quantile_bins or subgrid or switches_off_and_main or baseline_config or v4_table_identity or hydro_candidate or hydro_inflow_operating or onwind_reference or profile_variant_switch or calibrated_gwa_v5_profiles" 2>&1 | tail -6
rm -rf /tmp/x20_pytest_c2
