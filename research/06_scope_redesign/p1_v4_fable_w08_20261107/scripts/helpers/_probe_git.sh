R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd $R || exit 1
echo "== worktrees =="; git worktree list
echo "== branches w08/d1/fable =="; git branch -a | grep -E "w08|d1-2026|fable|v4" 
echo "== W08 head =="; git rev-parse codex/v4-w08-20261106
echo "== remote W08 head =="; git ls-remote origin refs/heads/codex/v4-w08-20261106 2>&1 | head -2
echo "== bd890bf9 ancestor of W08 head? =="; git merge-base --is-ancestor bd890bf9 codex/v4-w08-20261106 && echo YES || echo NO
echo "== aad8e476 ancestor? =="; git merge-base --is-ancestor aad8e476 codex/v4-w08-20261106 && echo YES || echo NO
echo "== log aad8e476..W08 =="; git log --oneline --no-decorate aad8e476..codex/v4-w08-20261106
echo "== diffstat aad8e476..W08 =="; git diff --stat aad8e476 codex/v4-w08-20261106 | tail -80
echo "== status main checkout =="; git status -sb | head -5
echo "== disk =="; df -h /home/jin | tail -1
