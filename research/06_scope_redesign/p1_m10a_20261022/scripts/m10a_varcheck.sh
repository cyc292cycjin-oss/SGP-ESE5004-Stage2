#!/bin/bash
# M10A: the 7 variants generated with the thread budget environment of run_batch3.sh aux() (OMP / MKL / OPENBLAS / NUMEXPR = 17, TMPDIR set, timeout)
# must be byte-identical to EXPECTED_VARIANTS.json of package v4 (phase 0 compares them on the instance; a difference would be STOP_SAFE).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022; DIST=$W/cloud_package_dist; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10a_20261022/evidence
WT=/home/jin/wt_m10p_20261022; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
V=/home/jin/m10a_varcheck; rm -rf $V; mkdir -p $V/tmp $E
cd $WT || exit 1
t0=$(date +%s)
while IFS='|' read -r rid sc base set prof costs; do
  [ -n "$set" ] || continue
  extra=(); [ "${set%%=*}" = finance.wacc_mode ] && extra=(--costs "$DIST/networks/${costs}_costs_active_research.csv")
  env -u GRB_LICENSE_FILE PYTHONHASHSEED=0 TMPDIR=$V/tmp OMP_NUM_THREADS=17 MKL_NUM_THREADS=17 OPENBLAS_NUM_THREADS=17 NUMEXPR_MAX_THREADS=17 timeout -k 30 1800 \
    $PY scripts_project/m08a_variants.py --repo . --base "$DIST/networks/${base}_unsolved.nc" --out "$V/$rid" --set "$set" "${extra[@]}" > "$V/$rid.log" 2>&1 || { echo "variant $rid failed"; exit 1; }
  r=$($PY scripts_project/m10_batch3_summary.py variants-check --variants $V --expected $DIST/EXPECTED_VARIANTS.json --rid $rid); echo "$rid $r"
done < <($PY scripts_project/m10_batch3_summary.py runtable) | tee $E/VARIANTS_UNDER_THREAD_BUDGET.txt
echo "seconds $(( $(date +%s) - t0 )); tmp files: $(ls $V/tmp | wc -l)" | tee -a $E/VARIANTS_UNDER_THREAD_BUDGET.txt
grep -c ' equal:' $E/VARIANTS_UNDER_THREAD_BUDGET.txt
