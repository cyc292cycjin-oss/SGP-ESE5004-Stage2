#!/bin/bash
# S4J-7: rebuild the four package networks (2920x3h + 365x24h) at the S4J final code commit, component comparison against the S4J-6 smoke
# networks, then the cloud package (prepares files only; no solve, no cloud action).
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=results_project/s4j/s4j7; mkdir -p $OUT/builds
ST=$OUT/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
build() { local tag=$1 sc=$2; shift 2; mkdir -p $OUT/builds/$tag
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$tag "$@" > $OUT/builds/${tag}_build.log 2> $OUT/builds/${tag}_build.err
  echo "BUILD_$tag:$?:$(tail -1 $OUT/builds/${tag}_build.log | cut -c1-60):$(grep -h 'Maximum resident' $OUT/builds/${tag}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/builds/${tag}_build.err | tr -s ' '):daily=$(ls $OUT/builds/$tag/*_365_24h_unsolved.nc 2>/dev/null | wc -l)" >> $ST; }
build integrated integrated
build disconnected disconnected
build integrated_nze integrated --override fuels.price_scenario=nze
build disconnected_gap disconnected --gap-diagnostic
cat > /tmp/s4j7_cmp.py <<'P'
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
for new, old, sc in [("s4j/s4j7/builds/integrated", "s4j/s4j6b/builds/integrated", "integrated"), ("s4j/s4j7/builds/disconnected", "s4j/s4j6b/builds/disconnected", "disconnected"),
                     ("s4j/s4j7/builds/integrated_nze", "s4j/s4j6b/builds/integrated_nze", "integrated")]:
    print(f"COMPARE_{new.split('/')[-1]}_vs_smoke:" + json.dumps(same(pypsa.Network(R + f"{new}/{sc}_2920_3h_unsolved.nc"), pypsa.Network(R + f"{old}/{sc}_2920_3h_unsolved.nc"))))
P
$PY /tmp/s4j7_cmp.py 2>&1 | grep COMPARE >> $ST
DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4j_20261018/cloud_package_dist
if [ -e $DIST ]; then echo "DIST exists - not overwritten" >> $ST; else
  bash research/06_scope_redesign/p1_step4j_20261018/cloud_package/make_package.sh $OUT/builds $DIST > $OUT/make_package.log 2>&1; echo "PACKAGE:$?" >> $ST; fi
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cat $ST; tail -5 $OUT/make_package.log
