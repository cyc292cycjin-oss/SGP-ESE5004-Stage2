#!/bin/bash
# M08b supplement 01 section 4.2: variant generation test with scripts_project/m08a_variants.py on the supplement-01 base networks (2920x3h); every
# variant twice (run1 / run2, separate output folders) -> reproducibility = identical output SHA256. Nothing is solved; outputs stay in the main
# checkout's results_project/m08b/variants_s01 (not committed). Same variant list as M08b section 3.2.
set -u
WT=/home/jin/wt_m08b_20261021; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
B=$MAIN/results_project/m08b/builds_s01; V=$MAIN/results_project/m08b/variants_s01; ST=$V/VARIANT_STATUS.txt
mkdir -p $V; cd $WT || exit 1
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
run() { local tag=$1 base=$2; shift 2
  for r in run1 run2; do mkdir -p $V/$r/$tag
    /usr/bin/time -v $PY scripts_project/m08a_variants.py --repo . --base $B/$base/${base}_2920_3h_unsolved.nc --out $V/$r/$tag "$@" > $V/$r/${tag}.log 2> $V/$r/${tag}.err
    echo "VARIANT_${tag}_$r:$?:$(grep -h 'Elapsed' $V/$r/${tag}.err | tr -s ' '):$(grep -h 'Maximum resident' $V/$r/${tag}.err | tr -s ' ')" >> $ST
  done; }
run keep_stock integrated --set cross_border.stock_mode=keep_stock_no_new
run b1 disconnected --set disconnected.co2_shipping_intra_asean=forbid
run remove_VN integrated --set "coalition.remove_countries=[VN]"
run remove_TH integrated --set "coalition.remove_countries=[TH]"
run remove_LA integrated --set "coalition.remove_countries=[LA]"
run country_wacc integrated --set finance.wacc_mode=country_specific
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
echo "--- output SHA256 run1 vs run2" >> $ST
for f in $(cd $V/run1 && find . -name '*.nc' -o -name '*_VARIANT_RECEIPT.json' | sort); do
  a=$(sha256sum $V/run1/$f | cut -c1-64); b=$(sha256sum $V/run2/$f | cut -c1-64)
  [ "$a" = "$b" ] && echo "SAME:$f:$a" >> $ST || echo "DIFF:$f:run1=$a run2=$b" >> $ST
done
echo "END:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
echo DONE >> $ST
