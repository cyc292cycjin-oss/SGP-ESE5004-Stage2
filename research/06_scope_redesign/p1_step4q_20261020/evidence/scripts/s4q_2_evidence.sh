#!/bin/bash
# S4Q-2 evidence (read only, no solver): light files of the six runs from the licence-scrubbed export folders (files < 600 kB, no .nc), the run
# STATUS files, the driver status, the preflight outputs, the results tarball SHA256 files; licence-string scan of the evidence folder.
set -u
W=/home/jin/wt_s4q_20261020; P=/home/jin/s4q_local/pkg; E=$W/research/06_scope_redesign/p1_step4q_20261020/evidence/s4q_2
mkdir -p $E; cp /home/jin/s4q_local/DRIVER_STATUS.txt $E/
for prof in formal_barrier_1e6 formal_barrier_1e6_t16; do
  grep -viE "licen[cs]e|wls|registered" $P/preflight_$prof.txt > $E/preflight_$prof.txt
  r=$(grep -l "solver_profile:$prof " $P/runs/*/STATUS.txt | head -1); r=$(dirname $r); t=$([ $prof = formal_barrier_1e6 ] && echo t8 || echo t16)
  mkdir -p $E/$t; echo "$(basename $r)" > $E/$t/RUN_FOLDER.txt
  cp $r/STATUS.txt $E/$t/; cp $r/results_*.tar.gz.sha256 $E/$t/ 2>/dev/null; cp $r/BATCH_REFERENCE.json $E/$t/ 2>/dev/null
  grep -viE "licen[cs]e|wls|registered" $P/run_stdout_$prof.txt > $E/$t/run_stdout.txt
  for sc in integrated disconnected integrated_nze; do
    mkdir -p $E/$t/$sc
    find $r/export/$sc -maxdepth 1 -type f -size -600k ! -name '*.nc' -exec cp {} $E/$t/$sc/ \;
    for k in c1_violations c1_precision; do grep -E "Elapsed|Maximum resident" $r/$sc/$k.err > $E/$t/$sc/${k}_time.txt 2>/dev/null; done
    ls -la $r/export/$sc | awk 'NR>1 {print $5, $9}' > $E/$t/$sc/EXPORT_LISTING.txt
  done
done
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $E)
[ -z "$H" ] && echo "LICENCE_SCAN_S4Q2_EVIDENCE: no hit ($(find $E -type f | wc -l) files, $(du -sh $E | cut -f1))" || { echo "LICENCE STRING FOUND:"; echo "$H"; exit 1; }
