#!/bin/bash
# D2a section 7.1: the v4 table folders of the two attribution corners (switch sets; every other v4 change at its v4 value):
#   d4p31  demand D = v4, resource caps P = v3.1   : biomass_potential=v3  gas_caps=gross  bio_cap_share=1.0
#   d31p4  demand D = v3.1, resource caps P = v4   : base=v3_1 residue_boundary=false id_paper_fuelwood=purchased household_gasoline=none rail_parent=in_d1
#                                                    captive_coal=false products=false vn_same_run=false industry_curves=flat (P at V4_MAIN: v4_adjusted_t04, marketed, 0.99)
# Writes research_inputs/industry_v4/out_ras_<sha12> for each (scripts_project/v4_industry.py); prints the folder names and the switch SHA.
set -u
R=/home/jin/wt_v4_d2a; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d2a
export PYTHONHASHSEED=0
cd $R || exit 1
D4P31="--set biomass_potential=v3 --set gas_caps=gross --set bio_cap_share=1.0"
D31P4="--set base=v3_1 --set residue_boundary=false --set id_paper_fuelwood=purchased --set household_gasoline=none --set rail_parent=in_d1 --set captive_coal=false --set products=false --set vn_same_run=false --set industry_curves=flat"
for tag in d4p31 d31p4; do
  if [ $tag = d4p31 ]; then S=$D4P31; else S=$D31P4; fi
  $PY scripts_project/v4_industry.py --anchor-mode ras --work $T/work_out_$tag $S > $T/out_$tag.log 2>&1 || { echo "FAILED $tag"; tail -20 $T/out_$tag.log; exit 1; }
  grep -E '"out"|asean_T_v2_TWh' $T/out_$tag.log | head -2
done
$PY - <<'P'
import json, sys
sys.path.insert(0, "/home/jin/wt_v4_d2a/scripts_project")
from v4_common import V4_MAIN, out_name, switch_sha, switches
sets = {"d4p31": dict(biomass_potential="v3", gas_caps="gross", bio_cap_share=1.0),
        "d31p4": dict(base="v3_1", residue_boundary=False, id_paper_fuelwood="purchased", household_gasoline="none", rail_parent="in_d1", captive_coal=False, products=False, vn_same_run=False, industry_curves="flat")}
for tag, ov in sets.items():
    s = switches(None, {**V4_MAIN, "anchor_mode": "ras", **ov})
    print(tag, out_name(s), switch_sha(s)[:12], json.dumps({k: s[k] for k in sorted(ov)}))
P
echo ATTRIB_TABLES_DONE
