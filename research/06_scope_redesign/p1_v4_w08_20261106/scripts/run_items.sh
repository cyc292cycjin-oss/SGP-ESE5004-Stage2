#!/bin/bash
# W08 sections 5-7: intake of the product input tables, item build in the worktree, item comparison with the reference dump, checkpoints S4-S6c.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106; R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
( cd $W && W08_REF_SCRATCH=/home/jin/v4w08/ref_main $PY scripts/w08_intake_items.py ) || exit 1
cd $R && $PY scripts_project/v4_products.py > /home/jin/v4w08/products.log 2>&1 || { tail -20 /home/jin/v4w08/products.log; exit 1; }
$PY - <<'EOF'
import json, sys
sys.path.insert(0, "/home/jin/wt_v4_w08/scripts_project")
import v4_products as P
ref = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106/tables/W08_REF_INPUTS.json"))
it = P.load_items()
def eq(a, b):
    return json.dumps(a, sort_keys=True, default=float) == json.dumps(b, sort_keys=True, default=float)
cap = [tuple(x) for c in ("ID", "MM", "PH") for x in ref["captive"][c]]
print("captive", [tuple(x) for x in it["captive"]] == cap)
keys = ("name", "row", "fuel19", "el19", "v2050")
print("pp", all(eq({k: it["pp"][c][k] for k in keys}, {k: ref["pp"][c][k] for k in keys}) for c in ref["pp"]), sorted(it["pp"]) == sorted(ref["pp"]))
print("pp_new", all(eq(it["pp_new"][c]["v2050"], ref["pp_new"][c]["v2050"]) for c in ref["pp_new"]), sorted(it["pp_new"]))
for c, h in ref["hvc"].items():
    hh = it["hvc_plants"][c]
    print("hvc", c, all(hh[k] == h[k] for k in ("hvc19_t", "hvc50_base_t", "hvc50_new_t", "el19_per_t", "fuel19_per_t")), hh["row"] == h["row"], hh["fuel_split"] == h["fuel_split"])
for c in ("MY", "ID", "BN"):
    a = it["methanol"][c]; b = {k: v for k, v in ref["meoh"][c].items() if k != "src"}
    print("meoh", c, eq(a, b))
print("meoh MY_new", eq(it["new_plants"]["MY"]["methanol_new_plants"], ref["meoh"]["MY_new"]["v2050"]))
for g in ("glass", "alumina", "copper", "lime"):
    print(g, all(eq(it[g][c], ref["oth"][g][c]) for c in ref["oth"][g]), sorted(it[g]) == sorted(ref["oth"][g]))
print("my_amm", [tuple(x) for x in it["my_ammonia_dup"]] == [tuple(x) for x in ref["oth"]["my_ammonia_dup"]], "vn_el", it["vn_el_rows"] == ref["vn_el_rows"])
print("bn_neu", it["bn_neu_methanol"])
EOF
