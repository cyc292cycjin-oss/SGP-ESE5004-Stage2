# DFX phase 4 (ON the instance): tmux session dfx4; in ITS shell the guard-variable check (names only) and preflight_dfx.sh (all sections)
P=/root/autodl-tmp/dfx_v8; cd "$P" || exit 2
E=${1:-/root/autodl-tmp/envs/pypsa-earth/bin/python}
tmux has-session -t dfx4 2>/dev/null && { echo "REFUSED: tmux session dfx4 exists"; exit 2; }
[ -x "$E" ] || { echo "REFUSED: environment python $E missing"; exit 2; }
[ -e /root/.gurobi/gurobi.lic ] || { echo "REFUSED: licence not placed"; exit 2; }
TS=$(date -u +%Y%m%dT%H%M%SZ)
tmux new-session -d -s dfx4 -x 230 -y 60 && echo "tmux dfx4 created $TS"
sleep 1
tmux send-keys -t dfx4 "cd $P" Enter
tmux send-keys -t dfx4 'echo "GUARD_CHECK $(date -u +%FT%TZ)"; env | grep -E "ALLOW_UNREGISTERED|BUILD_ONLY|POST_ONLY|DRY=|TRUNCATE|_CMD=|FAKE_|WALL_CAP_S|GUROBI_TIME_LIMIT_S|LICENCE_GAP_S" | cut -d= -f1 > /root/autodl-tmp/dfx_v8_guard_names.txt; echo "GUARD_NAMES_COUNT:$(wc -l < /root/autodl-tmp/dfx_v8_guard_names.txt)"' Enter
tmux send-keys -t dfx4 "PY=$E GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash preflight_dfx.sh 2>&1 | tee $P/PREFLIGHT_CONSOLE_$TS.log; pfrc=\${PIPESTATUS[0]}; echo PREFLIGHT_EXIT:\$pfrc | tee -a $P/PREFLIGHT_CONSOLE_$TS.log" Enter
echo "PREFLIGHT_LOG:$P/PREFLIGHT_CONSOLE_$TS.log"
