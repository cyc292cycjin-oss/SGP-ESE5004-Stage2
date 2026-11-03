# V3 screening rerun (supplement 07) (ON the instance; instruction section 2 step 6): after PREFLIGHT OK, start run_dfx.sh in the SAME tmux shell (v3s) as the preflight
P=/root/autodl-tmp/v3_screen_dmax; cd "$P" || exit 2
E=${1:-/root/autodl-tmp/envs/pypsa-earth/bin/python}
tmux has-session -t v3s 2>/dev/null || { echo "REFUSED: tmux session v3s missing"; exit 2; }
PL=$(ls -t $P/PREFLIGHT_CONSOLE_*.log 2>/dev/null | head -1)
[ -n "$PL" ] && grep -q '^PREFLIGHT OK' "$PL" && grep -q '^PREFLIGHT_EXIT:0' "$PL" || { echo "REFUSED: latest preflight log ${PL:-none} has no PREFLIGHT OK / exit 0"; exit 2; }
n=$(ps -eo args= | grep -E '[s]2_solve\.py|[r]un_dfx\.sh|[r]un_batch' | wc -l); [ "$n" = 0 ] || { echo "REFUSED: $n solve / runner processes already running"; exit 2; }
[ -e "$P/runs/dfx/.created" ] && { echo "REFUSED: runs/dfx already holds a batch (.created)"; exit 2; }
[ -s /root/autodl-tmp/v3_screen_dmax_auth.txt ] || { echo "REFUSED: authorisation text file missing"; exit 2; }
echo "LAUNCH: $(TZ=Asia/Singapore date "+%F %T") SGT / $(date -u +%FT%TZ); preflight log ${PL##*/}"
tmux send-keys -t v3s "mkdir -p runs/dfx && PY=$E GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash run_dfx.sh --auth \"\$(cat /root/autodl-tmp/v3_screen_dmax_auth.txt)\" 2>&1 | tee -a runs/dfx/RUN_DFX_CONSOLE.log" Enter
echo "send-keys exit=$?"
