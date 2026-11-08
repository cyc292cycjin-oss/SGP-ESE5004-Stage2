#!/bin/bash
# D2c section 2 / 3: rewrite the v4 table folders (main sets out_ras / out_iid; the F-01 sensitivity set id_paper_fuelwood = residue_literal -> out_ras_<sha12>)
# with scripts_project/v4_industry.py and compare every file with the committed HEAD version (git show HEAD:<path>): SAME / CHANGED / NEW per file.
set -u
R=/home/jin/wt_v4_d2c; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d2c
export PYTHONHASHSEED=0
mkdir -p $T
cd $R || exit 1
run() { tag=$1; shift; $PY scripts_project/v4_industry.py --work $T/work_out_$tag "$@" > $T/out_$tag.log 2>&1 || { echo "FAILED $tag"; tail -30 $T/out_$tag.log; return 1; }; echo "--- $tag"; tail -14 $T/out_$tag.log; }
run ras --anchor-mode ras
run iid --anchor-mode iid
run lit --anchor-mode ras --set id_paper_fuelwood=residue_literal
for d in research_inputs/industry_v4/out_*; do
  for f in $d/*; do
    if git cat-file -e HEAD:$f 2>/dev/null; then
      [ "$(git show HEAD:$f | sha256sum | cut -c1-64)" = "$(sha256sum $f | cut -c1-64)" ] && echo "SAME $f" || echo "CHANGED $f"
    else echo "NEW $f"; fi
  done
done
echo REGEN_DONE
