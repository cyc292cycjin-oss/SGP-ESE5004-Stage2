#!/bin/bash
# X20 全量 tests/research（不求解）：同 D2c full_tests.sh 的排除项（test_m12_allocation.py 与 5 个玩具 LP 测试会调求解器）。
# 用法：21_full_tests.sh <标签: base | v5>  ；网络测试读 V4_D2A_BUILD（base = W14 365x24h；v5 = 本步 v5main 365x24h）
set -u
TAG=${1:?tag}
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; LOG=$D/logs/ut_full_$TAG${X20_TAG:-}.txt
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd $R || exit 1
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[g]urobi_cl|[s]2_network\.py')" = 0 ] || { echo "REFUSED: a solve or build is running" | tee $LOG; exit 2; }
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo)
PEAK=3221225472   # 预计峰值 3 GiB（测试内构建玩具与小网络；W14 静态检查 0.83 GB）
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK" | tee $LOG; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK" > $LOG
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
# 不设 PYTHONPYCACHEPREFIX：指向 D 盘（9p）时每个子进程导入 pypsa 要 23-26 s（不设 1.7-2.2 s，scripts/31_import_timing.sh），第 2 次基线测试因此 2 h 28 min 只到约 40 %；
# 环境包用自带 __pycache__，worktree 的 __pycache__ 被 .gitignore 忽略（体积在结尾记录）。
# pytest 的捕获临时文件不能放在 9p（/mnt/d）上：TMPDIR 与 basetemp 用 WSL /tmp，跑完记录体积后删除
BT=/tmp/x20_pytest_$TAG; rm -rf "$BT"
if [ "$TAG" = base ]; then export V4_D2A_BUILD=$MAIN/results_project/v4w14/builds/main/integrated/integrated_365_24h_unsolved.nc
else export V4_D2A_BUILD=$D/builds/${X20_MAIN:-v5main}/integrated/integrated_365_24h_unsolved.nc; fi
echo "HEAD $(git rev-parse HEAD) V4_D2A_BUILD=$V4_D2A_BUILD" >> $LOG
start=$(date +%s)
$PY -m pytest -q -p no:cacheprovider --basetemp=$BT tests/research --ignore=tests/research/test_m12_allocation.py \
  --deselect tests/research/test_s3b_r4.py::test_scaling_round_trip_small_model \
  --deselect tests/research/test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers \
  --deselect tests/research/test_s4c_5.py::test_kvl_normalisation_exact \
  --deselect tests/research/test_s4m_duals.py::test_dual_dataset_with_conflicting_dim_coords \
  --deselect tests/research/test_s4o_2.py::test_c1_kkt_terms_toy_model \
  -rfEs >> $LOG 2>&1; rc=$?
echo "EXIT:$rc seconds:$(( $(date +%s) - start ))" >> $LOG
echo "== basetemp size (WSL /tmp, removed now)" >> $LOG; du -sb "$BT" >> $LOG 2>&1; rm -rf "$BT"
echo "== worktree __pycache__ size (git-ignored, WSL home)" >> $LOG; find . -name __pycache__ -type d -prune -exec du -sb {} + | awk '{s+=$1} END {print s " B"}' >> $LOG
echo "== leftover processes from tests" >> $LOG; ps -eo pid,args | grep -E 'x20_pytest_'"$TAG" | grep -v grep >> $LOG
echo "== git status after tests" >> $LOG; git status --short | head -20 >> $LOG
tail -5 $LOG
