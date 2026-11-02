#!/bin/bash
cd /home/jin/wt_v3_20261102/scripts_project
echo "=== s4j lossy sync / ext assumptions"
grep -n "reversed\|p_nom_extendable\|s_nom_extendable" s4j_layers.py | cut -c1-210 | head -24
echo "=== s4k"
grep -n "s_nom_extendable\|extendable\|s_nom_opt\|Line-s_nom\|def " s4k_layers.py | cut -c1-200 | head -24
echo "=== s4f max_extension"
grep -n "extendable\|s_nom_max\|p_nom_max" s4f_layers.py | cut -c1-200 | head -14
echo "=== s2_solve hooks and gates by scenario"
grep -n "scenario\b\|args.scenario\|a.scenario\|research_lossy\|B5\|gate_b5\|research_bunker\|install_" s2_solve.py | cut -c1-200 | head -40
echo "=== gates_v6 structural G2 list"
grep -n "B5\|B6\|B12\|B16\|G2\b\|STRUCTURAL\|structural" v5/gates_v6.py | cut -c1-200 | head -24
echo "=== rhs audit pool / bunker owners"
grep -n "ASEAN\|POOL\|pool\|bunker\|SHARED" m12_rhs_audit.py | cut -c1-210 | head -34
echo "=== s4o_c1 ASEAN"
grep -n "ASEAN\|BUNKER" s4o_c1_precision.py | cut -c1-200 | head -14
echo "=== other consumers of regional names"
grep -ln "ASEAN oil\|ASEAN methanol\|ASEAN ammonia\|ASEAN_POOL\|oil pool" *.py v5/*.py | tr '\n' ' '; echo
echo "=== s4i static audit name"; grep -n "^def \|B5\|xb" s4i_static_audit.py | cut -c1-140 | head -30
echo "=== ACCOUNT_FOR_SHARES"; sed -n 120,125p s2_layers.py | cut -c1-260
echo "=== transport account for EV shares; assembly ports"; ls ../results_project 2>/dev/null | head -2
