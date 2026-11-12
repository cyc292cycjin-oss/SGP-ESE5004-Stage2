#!/bin/bash
# X20 C 段（决策 253 第 ① 项）：最终 v5 网络（builds/c2main，提交 645c37e9）的本机 56 时段回归，F1 与 F2 各一次；设定与 69_smoke56.sh（B 段）相同，输出 smoke56_c2/。
#   profile formal_barrier_1e6_t16（Threads 16），--truncate 56，Gurobi TimeLimit 3,000 s，墙钟上限 3,600 s（杀整个进程组），标签 SMOKE_TEST_ONLY，
#   两次之间 >= 330 s，串行，同时至多一个 Gurobi，不重试，不改参数；F1 无解或非 optimal 则 F2 不启动。
# 授权：X20 指令 §3 第 6 步 + 决策 246 Q18 (b)：峰值 <= 可用 - 2 GiB，且没有其他 Claude 会话在跑（启动前由会话端核对，见 --confirmed 的说明文字）。
# 内存门：估计峰值 = D2c 同构 56 时段冒烟实测峰值 x（v5 主集 / v5off 随时段组件数之比）（scripts/69a_peak_estimate.py -> evidence/SMOKE56_PEAK_ESTIMATE.json：
#   F1 7,445.6 MiB x 1.00688 -> 7,497 MiB，F2 5,856.5 MiB x 1.00705 -> 5,898 MiB）；MemAvailable - 2 GiB 小于估计峰值即拒绝（不启动）。
# 每次求解前：对令牌服务器做一次裸 TCP 连接（不发数据，不读许可证）。许可证只经 GRB_LICENSE_FILE 传给求解进程（不读、不复制、不打印）；
# 原始 solve.log / solve.err 含许可证行，证据只用剔除后的副本。所有输出在 D 盘 $RUN；求解临时文件 TMPDIR 也在 D 盘。
set -u
WT=/home/jin/wt_v5_x20; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
B=$D/builds/c2main
RUN=$D/smoke56_c2; ST=$RUN/STATUS.txt
LIC=/home/jin/gurobi.lic; TL=3000; WALL=3600; GAP=330; GRACE=60; N=56; PROFILE=formal_barrier_1e6_t16
[ "${1:-}" = "--confirmed" ] || { echo "REFUSED: needs --confirmed <time>"; exit 5; }
AUTH="V5 X20 C segment, decision 253 item 1 (local 56-snapshot regression F1 + F2 of the final v5 networks, Gurobi <= 2, decision 246 Q18 (b) gate: peak <= available - 2 GiB, no other Claude session; ${2:?note}; script start $(date -u +%Y-%m-%dT%H:%M:%SZ)): profile $PROFILE, TimeLimit $TL s, wall cap $WALL s, no retry"
mkdir -p $RUN $D/tmp_solve_c2; export TMPDIR=$D/tmp_solve_c2; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl|[b]4_split_solve\.py|[s]2_network\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
token_route() { timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null; }
memgate() {   # $1 run id, $2 estimated peak MiB; Q18 (b): estimated peak <= MemAvailable - 2048 MiB
  local av; av=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
  if [ $(( av - 2048 )) -lt "$2" ]; then log MEM_GATE_REFUSED_$1 "available=${av}MiB:estimated_peak=${2}MiB"; return 1; fi
  log MEM_GATE_OK_$1 "available=${av}MiB:estimated_peak=${2}MiB"; return 0
}
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }
token_route || { log NO_TOKEN_ROUTE "token server not reachable from WSL (VPN?) - not started"; exit 6; }
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
[ "$(ps -eo args= | grep -c '[p]ytest')" = 0 ] || { log PYTEST_RUNNING "not started"; exit 4; }
DT=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l); [ "$DT" = 0 ] || { log DIRTY "$DT tracked changes - not started"; exit 2; }
SPECS=("F1 integrated $B/integrated/integrated_2920_3h_unsolved.nc $B/integrated/costs_active_research.csv 7497"
       "F2 no_new_xb $B/no_new_xb/no_new_xb_2920_3h_unsolved.nc $B/integrated/costs_active_research.csv 5898")
log START "commit=$(git rev-parse HEAD):profile=$PROFILE:truncate=$N:time_limit=$TL:wall_cap=$WALL:tmpdir=$TMPDIR"
for spec in "${SPECS[@]}"; do
  set -- $spec; rid=$1; sc=$2; net=$3; costs=$4; est=$5
  dir=$RUN/$rid; mkdir -p $dir
  if [ -f $dir/SOLVE_RECEIPT.json ]; then log SKIP_EXISTING_$rid "no re-solve"; continue; fi
  if [ -f $RUN/.last_solve_end ]; then
    last=$(cat $RUN/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP_$rid "$(( $(date +%s) - last ))s"
  fi
  [ "$(busy)" = 0 ] || { log SOLVER_BUSY_$rid "$(busy) processes - stop"; break; }
  memgate $rid $est || break
  token_route || { log NO_TOKEN_ROUTE_$rid "token server not reachable from WSL - stop"; break; }
  log NETWORK_$rid "$(sha256sum $net | cut -c1-64)"
  cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario $sc --output "$dir" --label SMOKE_TEST_ONLY --authorization "$AUTH; run $rid"
       --solver gurobi --solver-profile $PROFILE --scaling on --time-limit $TL --costs-table "$costs" --truncate $N)
  ( exec setsid env GRB_LICENSE_FILE=$LIC /usr/bin/time -v "${cmd[@]}" > $dir/solve.log 2> $dir/solve.err ) &
  pid=$!; t0=$(date +%s); sleep 1; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  log SOLVE_$rid "pid=$pid:pgid=$pg"
  while kill -0 $pid 2>/dev/null; do
    sleep 5
    if [ $(( $(date +%s) - t0 )) -ge $WALL ]; then
      log KILLED_${WALL}S_$rid; kill -TERM -- "-$pg" 2>/dev/null; g=0
      while alive $pg && [ $g -lt $GRACE ]; do sleep 1; g=$((g + 1)); done
      alive $pg && { kill -KILL -- "-$pg" 2>/dev/null; log KILL9_$rid; }
      break
    fi
  done
  wait $pid 2>/dev/null; rc=$?; date +%s > $RUN/.last_solve_end
  cond=$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'), r.get('status','none'), r.get('objective', ''))" $dir/SOLVE_RECEIPT.json 2>/dev/null || echo "no_receipt")
  log END_$rid "exit=$rc:$(( $(date +%s) - t0 ))s:$cond:$(grep -h 'Maximum resident' $dir/solve.err | awk '{printf "%.2fGiB", $NF/1048576}')"
  grep -viE 'licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic' $dir/solve.log > $dir/solve_log_scrubbed.txt
  grep -viE 'licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic' $dir/solve.err > $dir/solve_err_scrubbed.txt
  [ -f $dir/solution/X.npy ] || { log STOP_NO_SOLUTION_$rid "no returned solution - the remaining runs are not started"; break; }
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --out $dir/VIOLATIONS.json --truncate $N > $dir/c1_violations.log 2>&1 ); log VIOLATIONS_$rid "exit=$?"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --violations $dir/VIOLATIONS.json --truncate $N > $dir/c1_precision.log 2>&1 ); log C1_$rid "exit=$?"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $dir --scenario $sc --label SMOKE_$rid --out $dir --register > $dir/m12.log 2>&1 ); log M12_$rid "exit=$?"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario $sc --solve-dir $dir --allocation $dir/ALLOCATION.json --tag SMOKE_$rid --out $dir/m12_owen --register-dir $dir --truncate $N > $dir/m12_owen.log 2>&1 ); log OWEN_$rid "exit=$?"
  if [ "$(echo $cond | cut -d' ' -f1)" != "optimal" ]; then log STOP_NOT_OPTIMAL_$rid "$cond - the remaining runs are not started"; break; fi
done
a=F1; b=F2
if [ -f $RUN/$a/COUNTRY_COST_LEDGER.csv ] && [ -f $RUN/$b/COUNTRY_COST_LEDGER.csv ]; then
  env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py reference --integrated $RUN/$a --disconnected $RUN/$b --out $RUN/BATCH_REFERENCE.json > $RUN/c1_reference.log 2>&1; log REFERENCE "exit=$?"
  for rid in $a $b; do
    env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py regrade --solve-dir $RUN/$rid --reference $RUN/BATCH_REFERENCE.json > $RUN/$rid/c1_regrade.log 2>&1; log REGRADE_$rid "exit=$?"
    [ -f $RUN/$rid/m12_owen/OWEN.json ] && { env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py regrade --owen $RUN/$rid/m12_owen/OWEN.json --precision $RUN/$rid/PRECISION.json --out $RUN/$rid/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json > $RUN/$rid/m12_owen_regrade.log 2>&1; log OWEN_REGRADE_$rid "exit=$?"; }
  done
  env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py benefit --repo . --integrated $RUN/$a --disconnected $RUN/$b --out $RUN/M12_BENEFIT > $RUN/M12_BENEFIT.log 2>&1; log M12_BENEFIT "exit=$?"
fi
for spec in "${SPECS[@]}"; do
  set -- $spec; rid=$1; sc=$2; net=$3
  [ -f $RUN/$rid/SOLVE_RECEIPT.json ] || continue
  rec=$(dirname $net)/${sc}_BUILD_RECEIPT.json
  if [ $sc = integrated ] && [ -f $rec ]; then reg=(--build-receipt $rec); else reg=(--registered-sha256 $(sha256sum $net | cut -d' ' -f1)); fi
  lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir $RUN/$rid "${reg[@]}" --repo . --out $RUN/$rid/V6_ACCEPTANCE.json 2> $RUN/$rid/v6.err | tail -1); log V6_$rid "$lab"
  env -u GRB_LICENSE_FILE "$PY" scripts_project/m10_batch3_summary.py stop-class --dir $RUN/$rid > $RUN/$rid/stop_class.log 2>&1; log STOPCLASS_$rid "$(tail -1 $RUN/$rid/stop_class.log)"
done
rm -rf $D/tmp_solve_c2
log DONE
