#!/bin/bash
# X20 C-2 停止点：把 worktree 中未提交的 C-2 改动存为补丁（不提交、不推送），列出未跟踪的新文件及其 SHA256
cd /home/jin/wt_v5_x20 || exit 1
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
git diff > $D/evidence/C2_UNCOMMITTED_WORKTREE.patch
echo "HEAD $(git rev-parse HEAD)"; git diff --stat | tail -12
echo "== untracked / ignored new C-2 files"
for f in research_inputs/renewable_v5/WIND_GWA_CELL_QUANTILES_V5.nc research_inputs/renewable_v5/WIND_GWA_CELL_QUANTILES_V5.csv research_inputs/renewable_v5/WIND_GWA_QUANTILES_V5_LOG.json; do
  [ -e $f ] && echo "$(sha256sum $f | cut -c1-64) $(stat -c %s $f) $f"; done
sha256sum $D/evidence/C2_UNCOMMITTED_WORKTREE.patch | cut -c1-64
