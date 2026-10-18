#!/bin/bash
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=results_project/s4k/s4k4; ST=$OUT/STATUS.txt
mkdir -p $OUT/builds/integrated_alpha1
$PY scripts_project/s2_network.py --scenario integrated --output $OUT/builds/integrated_alpha1 --no-daily --override network.ac_loss_reference_loading=1.0 > $OUT/builds/integrated_alpha1_build.log 2> $OUT/builds/integrated_alpha1_build.err
echo "BUILD_integrated_alpha1:$?:$(tail -1 $OUT/builds/integrated_alpha1_build.log | cut -c1-60)" >> $ST
cat > /tmp/s4k4_a1.py <<'P'
import pypsa, logging, json, numpy as np
logging.disable(logging.WARNING)
R = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4k/s4k4/builds/"
a = pypsa.Network(R + "integrated_alpha1/integrated_2920_3h_unsolved.nc"); b = pypsa.Network(R + "integrated/integrated_2920_3h_unsolved.nc")
bad = {}
for c in ["Bus", "Link", "Store", "Generator", "Load", "StorageUnit", "Line", "Carrier"]:
    x, y = a.df(c).sort_index(), b.df(c).sort_index()
    cols = sorted(set(x.columns) | set(y.columns)); x = x.reindex(columns=cols); y = y.reindex(columns=cols)
    d = [k for k in cols if not x[k].equals(y[k])]
    if d: bad[c] = d
r = a.lines.ac_loss_lambda / b.lines.ac_loss_lambda
print("COMPARE_alpha1_vs_main:" + json.dumps(bad) + f" | ratio min {r.min():.12f} max {r.max():.12f} | alpha {a.meta['research_ac_losses']['alpha']} | lambda {a.lines.ac_loss_lambda.min():.4f}-{a.lines.ac_loss_lambda.max():.4f}")
P
$PY /tmp/s4k4_a1.py 2>&1 | grep COMPARE >> $ST
tail -2 $ST
