# V3 screening rerun (supplement 07) (ON the instance; instruction section 2 step 3): new instance, no reusable environment. In tmux session v3env: --check-mirrors, then the
# install (direct, no mirror variable: no Chinese mirror carries the gurobi channel). The console log is on the data disk; the session survives ssh loss.
P=/root/autodl-tmp/v3_screen_dmax; cd "$P/env" || exit 2
E=/root/autodl-tmp/envs/pypsa-earth
[ -e "$E" ] && { echo "REFUSED: $E exists"; exit 2; }
tmux has-session -t v3env 2>/dev/null && { echo "REFUSED: tmux session v3env exists"; exit 2; }
L=$P/ENV_INSTALL_CONSOLE.log
tmux new-session -d -s v3env -x 200 -y 50 && echo "tmux v3env created $(date -u +%FT%TZ)"
sleep 1
tmux send-keys -t v3env "cd $P/env; export CONDA=/root/miniconda3/bin/conda; { bash install_env.sh --check-mirrors; echo CHECK_MIRRORS_EXIT:\$?; bash install_env.sh; echo INSTALL_EXIT:\$?; } 2>&1 | tee $L" Enter
echo "started; log $L"
