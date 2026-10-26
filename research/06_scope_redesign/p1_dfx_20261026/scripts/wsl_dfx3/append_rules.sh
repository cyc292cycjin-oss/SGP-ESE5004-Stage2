#!/bin/bash
# DFX v3: append DFX_RULES.md verbatim to the phase-1 report (appendix A), once.
D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026
grep -q "^# DFX 规则" $D/DFX_REPORT_PHASE1.md 2>/dev/null && { echo "already appended"; exit 0; }
head -3 $D/DFX_RULES.md | cut -c1-80
cat $D/DFX_RULES.md >> $D/DFX_REPORT_PHASE1.md
echo "report lines: $(wc -l < $D/DFX_REPORT_PHASE1.md); rules lines: $(wc -l < $D/DFX_RULES.md)"; ls -la /DFX_RULES.md /DFX_REPORT_PHASE1.md 2>&1 | head -2
