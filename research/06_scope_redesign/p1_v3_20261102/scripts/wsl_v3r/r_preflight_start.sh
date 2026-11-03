# V3 screening rerun (supplement 07) (ON the instance; instruction section 2 step 5): tmux session v3s; in ITS shell the guard-variable check (names only) and preflight_dfx.sh (all sections)
P=/root/autodl-tmp/v3_screen_dmax; cd "$P" || exit 2
E=${1:-/root/autodl-tmp/envs/pypsa-earth/bin/python}
tmux has-session -t v3s 2>/dev/null && { echo "REFUSED: tmux session v3s exists"; exit 2; }
[ -x "$E" ] || { echo "REFUSED: environment python $E missing"; exit 2; }
[ -e /root/.gurobi/gurobi.lic ] || { echo "REFUSED: licence not placed"; exit 2; }
TS=$(date -u +%Y%m%dT%H%M%SZ)
tmux new-session -d -s v3s -x 230 -y 60 && echo "tmux v3s created $TS"
sleep 1
tmux send-keys -t v3s "cd $P" Enter
tmux send-keys -t v3s 'echo "GUARD_CHECK $(date -u +%FT%TZ)"; env | grep -E "ALLOW_UNREGISTERED|BUILD_ONLY|POST_ONLY|DRY=|TRUNCATE|_CMD=|FAKE_|WALL_CAP_S|GUROBI_TIME_LIMIT_S|LICENCE_GAP_S" | cut -d= -f1 > /root/autodl-tmp/v3_screen_dmax_guard_names.txt; echo "GUARD_NAMES_COUNT:$(wc -l < /root/autodl-tmp/v3_screen_dmax_guard_names.txt)"' Enter
# rerun floor (user authorisation 2026-11-03, RUN_PLAN_SCREEN_V3.md section 10, commit 6b1a1225): 16 cores / 48 GiB / 40 GB, only for this command (not exported into the shell of run_dfx.sh)
tmux send-keys -t v3s "NEED_CORES=16 NEED_MEM_GIB=48 NEED_DISK_GB=40 PY=$E GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash preflight_dfx.sh 2>&1 | tee $P/PREFLIGHT_CONSOLE_$TS.log; pfrc=\${PIPESTATUS[0]}; echo PREFLIGHT_EXIT:\$pfrc | tee -a $P/PREFLIGHT_CONSOLE_$TS.log" Enter
echo "PREFLIGHT_LOG:$P/PREFLIGHT_CONSOLE_$TS.log"
