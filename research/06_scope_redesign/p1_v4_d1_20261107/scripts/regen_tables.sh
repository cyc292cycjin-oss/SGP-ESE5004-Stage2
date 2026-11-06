#!/bin/bash
# D1: rewrite the v4 table folders of the given anchor modes (v4 main sets; --set overrides for other sets) and compare every file with the committed
# HEAD version (git show HEAD:<path>); prints SAME / CHANGED / NEW per file.
# usage: regen_tables.sh <tag> <anchor mode> [--set k=v ...]
set -u
R=/home/jin/wt_v4_d1; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d1
tag=$1; mode=$2; shift 2
export PYTHONHASHSEED=0
cd $R || exit 1
$PY scripts_project/v4_industry.py --anchor-mode $mode --work $T/work_out_$tag "$@" > $T/out_$tag.log 2>&1 || { tail -30 $T/out_$tag.log; exit 1; }
tail -8 $T/out_$tag.log
d=$(ls -td research_inputs/industry_v4/out_${mode}* | head -1)
echo "folder: $d"
for f in $d/*; do
  if git cat-file -e HEAD:$f 2>/dev/null; then
    [ "$(git show HEAD:$f | sha256sum | cut -c1-64)" = "$(sha256sum $f | cut -c1-64)" ] && echo "SAME $f" || echo "CHANGED $f"
  else echo "NEW $f"; fi
done
