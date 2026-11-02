#!/bin/bash
W=/home/jin/wt_v3_20261102; M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; cd $W
echo "== AC loss proxy"; head -c 1100 $M/research_inputs/corridors/AC_LOSS_PROXY_S4K1.json; echo
grep -n "ac_loss\|AC_LOSS\|loss_proxy\|lossy\|s4k" configs/research/baseline.yaml | head -12 | cut -c1-230
grep -ln "AC_LOSS_PROXY\|ac_loss_proxy" scripts_project/*.py | head
echo "== v3 switches"; grep -n "v3\|V3\|ev_structure\|liquids\|stock_mode\|facility\|subsector\|industry_v3\|node_share" configs/research/baseline.yaml | head -30 | cut -c1-230
echo "== yaml variants"; ls configs/research | tr '\n' ' '; echo; cat configs/research/no_new_xb.yaml | cut -c1-200 | head -20
echo "== disconnected build"; grep -n "border_class\|cross_border" scripts_project/scenario_network.py scripts_project/m08a_layers.py scripts_project/m08a_variants.py | head -24 | cut -c1-200
