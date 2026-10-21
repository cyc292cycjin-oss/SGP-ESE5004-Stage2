#!/bin/bash
# M08b: mirror work/ deliverables into research/06_scope_redesign/p1_m08b_20261021, stage everything (force-add ignored inputs), commit with /home/jin/m08b_msg.txt
set -eu
WT=/home/jin/wt_m08b_20261021
WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021
DEST=$WT/research/06_scope_redesign/p1_m08b_20261021
cd "$WT"
mkdir -p "$DEST"
for f in "$WORK"/M08B_*.md "$WORK"/M08B_*.txt; do
  [ -f "$f" ] && cp "$f" "$DEST/$(basename "$f")"
done
for d in evidence scripts; do
  [ -d "$WORK/$d" ] && mkdir -p "$DEST/$d" && cp -r "$WORK/$d/." "$DEST/$d/"
done
chmod 644 "$DEST"/*.md "$DEST"/*.txt 2>/dev/null || true
git add -A scripts_project tests configs research research_inputs/registry_v5 research_inputs/demand_v5
# ignored inputs (csv / xlsx / json / nc under research_inputs) listed in /home/jin/m08b_force.txt, one path or git glob pathspec per line
if [ -f /home/jin/m08b_force.txt ]; then
  while IFS= read -r p; do [ -n "$p" ] && { git add -f -- "$p" 2>/dev/null || true; }; done < /home/jin/m08b_force.txt
fi
# never commit the copied, ignored finance tables
git reset -q -- research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv research_inputs/finance_v5/DISCOUNT_RATE_IN_USE.csv 2>/dev/null || true
git status -s | head -60
git commit -q -F /home/jin/m08b_msg.txt
git log --oneline -1
