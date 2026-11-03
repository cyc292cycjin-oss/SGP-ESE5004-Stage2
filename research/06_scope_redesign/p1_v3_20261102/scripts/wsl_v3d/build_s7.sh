#!/bin/bash
# V3 supplement 07 (review EVDIAG section 2.1 item 3, decision 182): rebuild every v3 network at the clean commit with the new daily aggregation; no solver call, no licence.
# Same build steps as supplement 05 (build_s5.sh): integrated (2920x3h + 365x24h), no_new_xb variants of both, disconnected 365x24h, bridges 160-162 / 160-164 (365x24h, EV flat).
# Static check into the build folder (the supplement 05 evidence files are not overwritten). No LP build here: the dry run of the package gives the LP sizes of V1-V3.
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
OUT=$MAIN/results_project/v3/builds_dmax; ST=$OUT/BUILD_STATUS.txt
cd $W || exit 1
DIRTY=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes not committed ($DIRTY)"; exit 2; }
[ ! -e "$OUT" ] || { echo "REFUSED: $OUT exists"; exit 2; }
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[p]ytest|[s]2_network\.py')" = 0 ] || { echo "REFUSED: another solve, build or pytest is running"; exit 2; }
mkdir -p $OUT/integrated $OUT/no_new_xb $OUT/disconnected $OUT/bridge_160_162 $OUT/bridge_160_164 $OUT/static
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD)" > $ST
build() {   # folder, scenario, overrides...
  f=$1; s=$2; shift 2
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $s --output $OUT/$f "$@" > $OUT/${f}_build.log 2> $OUT/${f}_build.err
  echo "BUILD_$f:$?:$(grep -h 'Maximum resident' $OUT/${f}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/${f}_build.err | tr -s ' ' | cut -c30-):$(date -u +%H:%M:%S)" >> $ST
}
build integrated integrated
for r in 2920_3h 365_24h; do
  $PY scripts_project/m08a_variants.py --repo . --base $OUT/integrated/integrated_${r}_unsolved.nc --out $OUT/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/no_new_xb_$r.log 2>&1
  echo "VARIANT_$r:$?" >> $ST
done
build disconnected disconnected
build bridge_160_164 integrated --override s2.demand.ev_structure=flat
build bridge_160_162 integrated --override s2.demand.ev_structure=flat --override 's2.industry.v3={}'
rm -f $OUT/disconnected/disconnected_2920_3h_unsolved.nc $OUT/bridge_160_164/integrated_2920_3h_unsolved.nc $OUT/bridge_160_162/integrated_2920_3h_unsolved.nc   # 365x24h only (decision 174; bridge runs are screening runs)
( cd $OUT && sha256sum */*_unsolved.nc ) >> $ST
ls -l $OUT/*/*_unsolved.nc | awk '{print $5, $9}' >> $ST
( cd $W/scripts_project && $PY v3_static.py --dir $OUT --v2 $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc --out $OUT/static > $OUT/static.log 2>&1; echo "STATIC:$?" >> $ST )
du -sh $OUT >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cut -c1-200 $ST
