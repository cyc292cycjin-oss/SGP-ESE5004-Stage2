#!/bin/bash
# M10R B2.3 structural check (no solve): generate the 7 third-batch variants from the package v5 base networks (365x24h) with the worktree code,
# compare their SHA256 with the package EXPECTED_VARIANTS.json, then list for every base / variant the ledger meta rows whose component is absent.
set -u
WT=/home/jin/wt_m10p_20261022; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
PKG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/cloud_package_dist; NETS=$PKG/networks
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10r; V=$M/variants365; mkdir -p $V; ST=$V/STATUS.txt
cd $WT || exit 1
echo "START $(date -u +%FT%TZ) head=$(git rev-parse --short HEAD)" > $ST
args=("integrated_365=$NETS/integrated_365_24h_unsolved.nc" "disconnected_365=$NETS/disconnected_365_24h_unsolved.nc")
while IFS='|' read -r rid sc base set prof costs; do
  [ -n "$set" ] || continue
  extra=(); [ "${set%%=*}" = finance.wacc_mode ] && extra=(--costs "$NETS/${costs}_costs_active_research.csv")
  if [ ! -f "$(ls $V/$rid/*_VARIANT_RECEIPT.json 2>/dev/null | head -1)" ]; then
    mkdir -p $V/$rid
    env -u GRB_LICENSE_FILE "$PY" scripts_project/m08a_variants.py --repo . --base "$NETS/${base}_unsolved.nc" --out "$V/$rid" --set "$set" "${extra[@]}" > $V/$rid.log 2>&1; echo "VARIANT_$rid exit=$?" >> $ST
  fi
  vc=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/m10_batch3_summary.py variants-check --variants $V --expected $PKG/EXPECTED_VARIANTS.json --rid $rid 2>&1 | tail -1); echo "CHECK_$rid $vc" >> $ST
  args+=("$rid=$(ls $V/$rid/*_unsolved.nc | head -1)")
done < <("$PY" scripts_project/m10_batch3_summary.py runtable)
env -u GRB_LICENSE_FILE "$PY" /home/jin/m10r/xb_check_all.py $V/XB_LEDGER_CHECK_365.json "${args[@]}" > $V/xb_check.log 2> $V/xb_check.err; echo "XB_CHECK exit=$? $(tail -1 $V/xb_check.log)" >> $ST
echo "DONE $(date -u +%FT%TZ)" >> $ST; cat $ST
