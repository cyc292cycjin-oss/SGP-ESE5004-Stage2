R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd $R || exit 1
if [ -d /home/jin/wt_v4_fable ]; then echo "EXISTS /home/jin/wt_v4_fable"; else
  git worktree add -b codex/v4-fable-w08-20261107 /home/jin/wt_v4_fable 7aa356e49d284749d27c79fbdc75ade85f62866a 2>&1 | tail -3
fi
cd /home/jin/wt_v4_fable && echo "WT HEAD: $(git rev-parse HEAD) BRANCH: $(git branch --show-current)"
echo "== full name-status aad8e476..7aa356e4 =="
git diff --name-status aad8e476 7aa356e4
echo "== research/06_scope_redesign dirs with v4 =="
ls -d research/06_scope_redesign/*v4* 2>/dev/null
echo "== w08 deliverable dir in repo =="
ls research/06_scope_redesign/p1_v4_w08_20261106 2>/dev/null
echo "== w07 I2 in repo =="
ls research/06_scope_redesign/p1_v4_w07_20261106/I2 2>/dev/null | head -40
echo "== configs research =="
ls configs/research 2>/dev/null | head
