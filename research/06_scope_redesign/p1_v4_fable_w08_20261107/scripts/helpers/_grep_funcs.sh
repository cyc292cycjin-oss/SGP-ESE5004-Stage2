cd /home/jin/wt_v4_fable/scripts_project || exit 1
echo "##### s2_layers.biomass_overflow"; grep -n "def biomass_overflow" -A 30 s2_layers.py
echo "##### s2_layers rail loading"; grep -n "RailNonElectric\|rail" s2_layers.py | head -40
echo "##### s2_layers overflow params"; grep -n "ov_cap_share\|ov_binding_ratio\|overflow_cap_share\|binding_ratio" s2_layers.py | head -20
echo "##### add_biomass_layer"; grep -rn "def add_biomass_layer" -A 60 s2_network.py s2_layers.py s2_*.py 2>/dev/null | head -90
echo "##### m08b ras_split"; grep -n "def ras_split" -A 40 m08b_demand.py
echo "##### m08b row/col targets + seed"; grep -n "row_t\|col_t\|k_scale\|seed = \|def aeo8_country\|def c3_ats" m08b_demand.py | head -40
echo "##### reconstruct_base_accounts convert"; grep -n "def convert" -A 30 reconstruct_base_accounts.py | head -60
echo "##### FROZEN conversions keys"; python3 - <<'PY'
import json
c=json.load(open('/home/jin/wt_v4_fable/research_inputs/assembly_v1/sources/FROZEN_UPSTREAM_CONVERSIONS.json'))
print(list(c.keys()))
for k,v in c.items():
    if k!='constants': print(k, json.dumps(v)[:1500])
print('constants keys', list(c['constants'].keys()))
for k in c['constants']:
    print(k, json.dumps(c['constants'][k])[:600])
PY
echo "##### s3_0 OTHER bucket rows / solid_pot"; grep -n "OTHER_BUCKET_ROWS\|other_bucket_rows\|construction\|mining and quarrying" s3_0_industry.py | head -20
echo "##### d1_fossil_production conversion"; sed -n 1,40p d1_fossil_production.py; grep -n "0.9\|0.0036\|GCV\|NCV" d1_fossil_production.py | head -20
echo "##### s2_0_process_emissions rule"; grep -n "2.A.1\|cement\|multiplier" s2_0_process_emissions.py | head -30
