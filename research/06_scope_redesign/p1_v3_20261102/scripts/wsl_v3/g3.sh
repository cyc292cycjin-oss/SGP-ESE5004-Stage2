#!/bin/bash
cd /home/jin/wt_v3_20261102
F=research/STAGE2_PROJECT_LEDGER.md
for k in 18 35 44 48 88 89 92 93 119 ; do
  echo "=== item $k"
  grep -nE "第 ?$k 项|第 ?[0-9, ]*$k[ ,、]" $F | cut -c1-300 | head -4
done
echo "=== S2 instruction B6"
sed -n 30,40p research/06_scope_redesign/p1_step2_20261015/S2_CLAUDE_CODE_INSTRUCTION.md | cut -c1-400
