cd /home/jin/wt_v4_fable/scripts_project || exit 1
echo "##### d1_demand_2050.electricity_by_sector"; grep -n "def electricity_by_sector" -A 25 d1_demand_2050.py
echo "##### s2_layers 815-850 (transport loads)"; sed -n 815,850p s2_layers.py
echo "##### s2_layers 700-745 (anchor checks / v4t)"; sed -n 700,745p s2_layers.py
echo "##### s2_layers anchor_checks usage"; grep -n "anchor_checks\|anchor_tab" s2_layers.py | head -20
echo "##### v3_industry CARRIERS / col / decompose signature"; grep -n "^CARRIERS\|^def col\|^def decompose\|^def nonferrous\|^def run_vn_chain\|^def future_vectors" v3_industry.py
