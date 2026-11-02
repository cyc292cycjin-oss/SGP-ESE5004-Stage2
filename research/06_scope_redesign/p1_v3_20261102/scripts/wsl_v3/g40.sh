#!/bin/bash
# search the decision list 172-176 in the repository, on all branches and in the local folders (read-only)
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd $M
echo "== decision numbers in the last ledger rows"
for b in $(git for-each-ref --sort=-committerdate --format='%(refname:short)' refs/heads refs/remotes | head -14); do
  n=$(git grep -lE '第 ?17[2-6] ?项|decision 17[2-6]|^\| ?17[2-6] ?\|' "$b" -- 'research/*.md' 2>/dev/null | head -3 | tr '\n' ' ')
  echo "$b: $n" | cut -c1-200
done
echo "== latest decision numbers in markdown of the v3 branch"
git grep -hoE '第 ?1[67][0-9] ?项' codex/v3-20261102 -- research | sort | uniq -c | sort -k2 | tail -14
echo "== local"
ls /mnt/d/ResearchWorkspaces | head -20
grep -rlE '已核实非问题|决策清单' /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102 2>/dev/null | head
