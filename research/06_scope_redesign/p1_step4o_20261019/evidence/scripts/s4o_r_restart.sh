# S4O-6 rule 8 (runs ON the instance via "ssh bash -s"; read-only): locate barrier restarts ("jumps") in the newest run log: iterations whose primal
# residual exceeds 1e3 x the smallest residual seen before; prints the neighbouring lines and any non-iteration line between them.
RUN=$(ls -d /root/autodl-tmp/s4o_cloud/runs/*/ | tail -1)
for L in ${RUN}*/gurobi.linopy.log; do
  echo "== $(basename $(dirname $L))"
  awk '/^ *[0-9]+ +[-0-9.e+]+ +[-0-9.e+]+ +[0-9.e+-]+ +[0-9.e+-]+ +[0-9.e+-]+ +[0-9]+s/ {it=$1; pr=$4+0; if (min=="" || pr<min) {if (min!="" && 0) {}; }
       if (min!="" && pr > 1e3*min && !seen[int(it)]) {print "JUMP at iteration " it " (" $7 "): primal residual " pr " after min " min " (iteration " minit "); previous line: " prev; seen[int(it)]=1}
       if (min=="" || pr<min) {min=pr; minit=it}; prev=$0}' "$L" | head -5
  grep -nE '^ *(1[0-9][0-9]|[0-9][0-9]) ' "$L" | head -0
done
