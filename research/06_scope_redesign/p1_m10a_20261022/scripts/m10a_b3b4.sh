#!/bin/bash
# M10A B3 / B4 measurements (no solver, no model network solved): real 365x24h data of the S4N pilot export (old network, solved, duals) for the
# light post-processing steps; coefficient ranges of the exported (unscaled) LP arrays old vs new (56x3h) and new 365x24h.
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
WT=/home/jin/wt_m10p_20261022
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
S4N=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/cloud_results/20261019T072454Z_5125/full/export/integrated
M=/home/jin/m10a_b3; mkdir -p $M; LOG=$M/B3B4.log; : > $LOG
log() { echo "$(date -u +%FT%TZ) $*" | tee -a $LOG; }
log "START free=$(free -g | awk '/Mem/ {print $7}')GiB"
echo "===== B4: coefficient ranges of exported LP arrays (ORIGINAL_UNSCALED basis) =====" | tee -a $LOG
$PY - $MAIN/m10p/measure_r1/R1/lp /home/jin/m10p_dry_s01/post_smoke/R1/lp $MAIN/s4n/s4n1/solve/lp $MAIN/m10p/measure_r1/R1/lp <<'P' 2>&1 | tee -a $LOG
import json, sys, time
import numpy as np
from pathlib import Path
def rng(a, nonzero=True):
    a = np.abs(np.asarray(a, dtype=float)); a = a[np.isfinite(a)]
    if nonzero: a = a[a > 0]
    return (float(a.min()), float(a.max())) if a.size else (None, None)
out = {}
for tag, p in (("new_365x24h_R1", sys.argv[1]), ("new_56x3h_smoke_R1", sys.argv[2]), ("old_56x3h_s4n1", sys.argv[3])):
    lp = Path(p); t0 = time.time()
    if not lp.exists(): out[tag] = dict(missing=str(lp)); continue
    meta = json.loads((lp / "MATH_PROBLEM.json").read_text())
    v = np.load(lp / "value.npy"); c = np.load(lp / "cost.npy"); cl = np.load(lp / "col_lower.npy"); cu = np.load(lp / "col_upper.npy"); rl = np.load(lp / "row_lower.npy"); ru = np.load(lp / "row_upper.npy")
    bounds = np.concatenate([cl, cu]); rhs = np.concatenate([rl, ru])
    r = dict(units=meta.get("units"), num_row=meta.get("num_row"), num_col=meta.get("num_col"), nnz=meta.get("nnz"), offset=meta.get("offset"),
             matrix=rng(v), objective=rng(c), bounds=rng(bounds), rhs=rng(rhs), seconds=round(time.time() - t0, 1))
    for k in ("matrix", "objective", "bounds", "rhs"):
        lo, hi = r[k]; r[k + "_ratio"] = (hi / lo) if lo else None
    out[tag] = r
    print(tag, json.dumps(r))
Path("/home/jin/m10a_b3/B4_ARRAY_RANGES.json").write_text(json.dumps(out, indent=1))
P
log "B4 done free=$(free -g | awk '/Mem/ {print $7}')GiB"
echo "===== B3: real 365x24h light steps on the S4N pilot export =====" | tee -a $LOG
ls -la $S4N | head -40 | tee -a $LOG
D=$M/R1; rm -rf $D; mkdir -p $D
# a run-dir-like copy: receipt, gates, exports, ledgers, solved network, duals (no lp/ or solution/ arrays - they stayed on the instance)
cp $S4N/*.json $S4N/*.csv $S4N/*.txt $D/ 2>/dev/null; cp $S4N/*_solved.nc $S4N/DUALS_BY_CONSTRAINT.nc $D/
ls $D | head -40
echo "--- B3.1 m12_allocation run (loads the 365x24h solved network) ---" | tee -a $LOG
( cd $WT && env -u GRB_LICENSE_FILE PYTHONHASHSEED=0 /usr/bin/time -v $PY scripts_project/m12_allocation.py run --repo $WT --solve-dir $D --scenario integrated --label M10A_B3 --out $M/alloc > $M/alloc.log 2> $M/alloc.err ); echo "exit=$?" | tee -a $LOG
grep -hE "Elapsed \(wall|Maximum resident|Exit status" $M/alloc.err | tee -a $LOG; tail -c 600 $M/alloc.log | tee -a $LOG; echo
echo "--- B3.2 gates_v6 accept (hashes every registered export incl. the 166 MB network and 77 MB duals) ---" | tee -a $LOG
( cd $WT && env -u GRB_LICENSE_FILE /usr/bin/time -v $PY scripts_project/v5/gates_v6.py accept --solve-dir $D --registered-sha256 "$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['input_network']['sha256'])" $D/SOLVE_RECEIPT.json)" --repo $WT --out $M/V6_ACCEPTANCE.json > $M/v6.log 2> $M/v6.err ); echo "exit=$?" | tee -a $LOG
grep -hE "Elapsed \(wall|Maximum resident" $M/v6.err | tee -a $LOG; cat $M/v6.log | tee -a $LOG
$PY -c "import json; a=json.load(open('/home/jin/m10a_b3/V6_ACCEPTANCE.json')); print('label', a['label'], 'G2', {k: v['passed'] for k, v in a['G2'].items()}, 'G2_3 checks', a['G2']['G2_3']['checks'])" | tee -a $LOG
echo "--- B3.3 pack_results.sh on one 365x24h export (light + full tar.gz; arrays manifest with no arrays) ---" | tee -a $LOG
PK=$M/packrun; rm -rf $PK; mkdir -p $PK/export/R1; cp -r $D/. $PK/export/R1/
( cd $WT && PY=$PY /usr/bin/time -v bash research/06_scope_redesign/p1_m10p_20261022/cloud_package/pack_results.sh $PK m10a > $M/pack.log 2> $M/pack.err ); echo "exit=$?" | tee -a $LOG
grep -hE "Elapsed \(wall|Maximum resident" $M/pack.err | tee -a $LOG; cat $M/pack.log | tee -a $LOG; du -sb $PK/export | tee -a $LOG
echo "--- B3.4 m12_rhs_audit audit in --duals mode on the S4N pilot (old 365x24h network; builds the model: M12 measured 8.08 GiB locally) ---" | tee -a $LOG
OLDNET=""
for cand in /home/jin/m12_local/s4m3_nets/integrated_365_24h_unsolved.nc $MAIN/s4m/s4m3/builds/integrated/integrated_365_24h_unsolved.nc $(ls /home/jin/m12_local/*/integrated_365_24h_unsolved.nc 2>/dev/null | head -3); do
  [ -f "$cand" ] && { s=$(sha256sum "$cand" | cut -c1-8); echo "candidate $cand sha=$s" | tee -a $LOG; [ "$s" = 4206ec5c ] && OLDNET=$cand && break; }
done
if [ -n "$OLDNET" ]; then
  log "owen audit start free=$(free -g | awk '/Mem/ {print $7}')GiB"
  ( cd $WT && env -u GRB_LICENSE_FILE PYTHONHASHSEED=0 /usr/bin/time -v $PY scripts_project/m12_rhs_audit.py audit --repo $WT --network $OLDNET --scenario integrated --duals $D/DUALS_BY_CONSTRAINT.nc --solved $D/integrated_FORMAL_TRIAL_365X24H_solved.nc --allocation $M/alloc/ALLOCATION.json --tag M10A_B3 --out $M/owen > $M/owen.log 2> $M/owen.err ); echo "exit=$?" | tee -a $LOG
  grep -hE "Elapsed \(wall|Maximum resident" $M/owen.err | tee -a $LOG; tail -c 400 $M/owen.log | tee -a $LOG; echo
  $PY -c "import json; d=json.load(open('/home/jin/m10a_b3/owen/RHS_AUDIT.json')); print('seconds', d.get('seconds'), 'peak_rss_gib', d.get('peak_rss_gib'), 'build_seconds', d.get('build_seconds'))" 2>&1 | tee -a $LOG
else
  log "owen audit skipped: old 365x24h unsolved network (4206ec5c) not found locally"
fi
log "END free=$(free -g | awk '/Mem/ {print $7}')GiB"
echo B3B4_DONE >> $LOG
