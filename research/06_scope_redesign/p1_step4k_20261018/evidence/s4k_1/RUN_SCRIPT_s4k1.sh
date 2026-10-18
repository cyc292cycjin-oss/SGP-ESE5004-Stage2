#!/bin/bash
# S4K-1 (decision 108): builds (no solve), comparisons against the S4J-7 builds, data + registry, tests.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=results_project/s4k/s4k1; mkdir -p $OUT/builds
ST=$OUT/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
build() { local tag=$1 sc=$2; shift 2; mkdir -p $OUT/builds/$tag
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$tag --no-daily "$@" > $OUT/builds/${tag}_build.log 2> $OUT/builds/${tag}_build.err
  echo "BUILD_$tag:$?:$(tail -1 $OUT/builds/${tag}_build.log | cut -c1-60):$(grep -h 'Maximum resident' $OUT/builds/${tag}_build.err | tr -s ' ')" >> $ST; }
build integrated integrated
build integrated_tangent integrated --override network.ac_losses=pypsa_tangent
build integrated_noac integrated --override network.ac_losses=none
build disconnected disconnected
cat > /tmp/s4k1_cmp.py <<'P'
import pypsa, logging, json
logging.disable(logging.WARNING)
R = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/"
def same(a, b):
    bad = {}
    for c in ["Bus", "Link", "Store", "Generator", "Load", "StorageUnit", "Line", "Carrier"]:
        x, y = a.df(c).sort_index(), b.df(c).sort_index()
        if set(x.index) != set(y.index): bad[c] = "index differs"; continue
        cols = sorted(set(x.columns) | set(y.columns)); x = x.reindex(columns=cols); y = y.reindex(columns=cols)
        d = [k for k in cols if not x[k].equals(y[k])]
        if d: bad[c] = d
        for attr, df in a.pnl(c).items():
            if not df.sort_index(axis=1).equals(b.pnl(c)[attr].sort_index(axis=1)): bad.setdefault(c + "_t", []).append(attr)
    return bad
for new, old, sc in [("integrated", "integrated", "integrated"), ("integrated_tangent", "integrated", "integrated"), ("integrated_noac", "integrated", "integrated"),
                     ("disconnected", "disconnected", "disconnected")]:
    a = pypsa.Network(R + f"s4k/s4k1/builds/{new}/{sc}_2920_3h_unsolved.nc"); b = pypsa.Network(R + f"s4j/s4j7/builds/{old}/{sc}_2920_3h_unsolved.nc")
    m = a.meta.get("research_ac_losses", {}); t = a.meta.get("research_transmission_losses", {})
    print(f"COMPARE_{new}_vs_s4j7:" + json.dumps(same(a, b)) + f" | ac_losses={m.get('mode')} solver_tangents={t.get('ac_transmission_losses')} hook={'research_ac_loss_proxy' in a.meta.get('required_constraint_hooks', [])}")
P
$PY /tmp/s4k1_cmp.py 2>&1 | grep COMPARE >> $ST
(cd scripts_project && $PY s4k_1_data.py --network ../$OUT/builds/integrated/integrated_2920_3h_unsolved.nc --tangent ../$OUT/builds/integrated_tangent/integrated_2920_3h_unsolved.nc > ../$OUT/data.log 2>&1); echo "DATA:$?" >> $ST
grep -q '"s4k_1"' scripts_project/d1_registry.py || sed -i 's/"s4k_0"]/"s4k_0", "s4k_1"]/' scripts_project/d1_registry.py
(cd scripts_project && $PY d1_registry.py 2>&1 | tail -1) >> $ST
$PY -m pytest -q -p no:cacheprovider tests/research/test_s4k_1.py 2>&1 | tail -1 | sed 's/^/S4K_TESTS:/' >> $ST
$PY -m pytest -q -p no:cacheprovider tests 2>&1 | tail -1 | sed 's/^/FULL_TESTS:/' >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
grep -v PROJ $ST
