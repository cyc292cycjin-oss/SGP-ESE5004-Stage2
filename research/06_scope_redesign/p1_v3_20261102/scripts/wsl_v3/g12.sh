#!/bin/bash
cd /home/jin/wt_v3_20261102/scripts_project
grep -n "POOL_BUSES" v5/*.py *.py | cut -c1-200 | head
sed -n 296,316p v5/v5_gates.py | cut -c1-230
grep -n "gate_b13\|def gate_b1[0-9]\|def gate_b[0-9]\|def gate_a[0-9]" v5/v5_gates.py | cut -c1-120 | head -24
grep -n "MARITIME_TRADE_CARRIERS\|maritime_trade\|border_class" *.py v5/*.py | grep -v "^s4[a-z]_[0-9]\|^s[0-9]_[0-9]\|summary\|collect\|review" | cut -c1-150 | head -30
grep -n "ev_share\|bev_\|BEV\|EV battery\|land transport EV" *.py v5/*.py | grep -v "^s2_layers\|^d1_\|data.py\|summary" | cut -c1-150 | head -16
grep -n "^def \|keep_stock\|no_new" b4_batch4.py | cut -c1-110 | head -30
python3 - <<'P' 2>/dev/null || true
P
cat ../configs/research/composition.json | head -30
