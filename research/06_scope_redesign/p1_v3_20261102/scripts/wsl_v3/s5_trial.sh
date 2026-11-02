#!/bin/bash
# Supplement 05: one integrated build on the working tree, no daily network, before the commit: does the layer run on the real network and pass the static validation. Output removed afterwards. No solver.
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; O=$MAIN/results_project/v3/s5_trial
rm -rf $O; mkdir -p $O; cd $W
$PY scripts_project/s2_network.py --scenario integrated --output $O --no-daily > $O/out.log 2> $O/err.log; echo "BUILD_EXIT:$?"
tail -3 $O/err.log | cut -c1-220; tail -1 $O/out.log | cut -c1-200
$PY - "$O" <<'P' 2>&1 | grep -v -E "PROJ|Warning|warn\("
import json, logging, sys
import pypsa
logging.disable(logging.WARNING)
n = pypsa.Network(sys.argv[1] + "/integrated_2920_3h_unsolved.nc")
for r in n.meta["research_dedicated_lines"]["sources"]:
    print(r["node"], "moved", r["moved_mw"], "non-thermal", r["non_thermal_mw"], "contract", r["contract_mw"], r["moved_mw_by_carrier"], "stayed", len(r["stayed_units"]), [x["component"][-40:] for x in r["split"]])
print(n.meta["research_dedicated_lines"].get("status_table"))
a = "existing_survivor::LA2 1::hydro existing::S4A"; b = a + " operating"; u = n.storage_units
print(u.loc[[a, b], ["bus", "p_nom", "existing_annual_fixed_om_eur"]].to_string()); print(round(float(n.storage_units_t.inflow[[a, b]].sum().sum()), 3), n.storage_units.dtypes.astype(str).value_counts().to_dict())
print("FOM columns", sum(float(n.df(t).existing_annual_fixed_om_eur.fillna(0).sum()) for t in ("Generator", "StorageUnit", "Link")), "meta", n.meta["existing_annual_fixed_om_eur"])
P
du -sh $O | cut -f1; rm -rf $O
