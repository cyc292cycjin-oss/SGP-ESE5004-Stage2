#!/bin/bash
# S4N-4 post-processing ON the instance after DONE (user 2026-10-19 ~16:25 SGT: light retrieval). Read-only on the run, no solver call,
# GRB_LICENSE_FILE unset, nice 19. Writes only to /root/autodl-tmp/s4n_tools/. Steps:
#   1. full results bundle: sha256sum -c, size, listing (the bundle stays on the data disk);
#   2. s4n_pilot_check.py: receipt, gate summary, in-run dual export + cross-check vs marginal_price, EXPORTS.json vs files, licence-marker scan;
#   3. l23_violation_analysis.py (package code; L23 report section 6 method): primal violations by family / country, last 20 iterations;
#   4. light bundle: export files except the solved network and DUALS_BY_CONSTRAINT.nc (and anything > 30 MB), STATUS, MONITOR, the checks above,
#      logs (licence lines filtered), launch record -> licence scan -> tar.gz + sha256.
RUN=/root/autodl-tmp/s4m_cloud/runs/20261019T072454Z_5125
PKG=/root/autodl-tmp/s4m_cloud; REPO=$PKG/repo; T=/root/autodl-tmp/s4n_tools
PY=/root/miniconda3/envs/pypsa-earth/bin/python
TS=$(basename $RUN); d=$RUN/integrated; e=$RUN/export/integrated
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'
export PYTHONHASHSEED=0 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
unset GRB_LICENSE_FILE
ST=$T/POST_STATUS.txt
grep -q "^DONE" $RUN/STATUS.txt || { echo "NOT DONE - refused"; exit 1; }
ps -eo cmd | grep -qE '[s]2_solve.py|[g]urobi_cl' && { echo "solver process still running - refused"; exit 1; }
echo "POST_START:$(TZ=Asia/Singapore date '+%F %T') SGT" > $ST
# 1 full bundle
B=$RUN/results_$TS.tar.gz
(cd $RUN && sha256sum -c results_$TS.tar.gz.sha256) >> $ST 2>&1
echo "BUNDLE:path=$B:bytes=$(stat -c %s $B):sha256=$(cut -d' ' -f1 $B.sha256)" >> $ST
tar tzvf $B > $T/BUNDLE_LISTING.txt 2>&1; echo "BUNDLE_MEMBERS:$(grep -vc '/$' $T/BUNDLE_LISTING.txt)" >> $ST
echo "SOLVE_DIR_BYTES:$(du -sb $d | cut -f1):RUN_DIR_BYTES:$(du -sb $RUN | cut -f1)" >> $ST
# 2 pilot check
nice -n 19 /usr/bin/time -v $PY $T/s4n_pilot_check.py --solve $d --export $e --out $T/S4N4_PILOT_CHECK.json > $T/pilot_check.log 2> $T/pilot_check.err
echo "PILOT_CHECK:exit=$?:$(grep -h 'Maximum resident' $T/pilot_check.err | tr -s ' \t' ' '):$(grep -h 'Elapsed' $T/pilot_check.err | tr -s ' \t' ' ')" >> $ST
# 3 violation analysis (also on an optimal solve: maximum primal violation for the L23 comparison)
if [ -f $d/solution/X.npy ]; then
  nice -n 19 /usr/bin/time -v $PY $REPO/scripts_project/l23_violation_analysis.py --repo $REPO --solve-dir $d --network $PKG/networks/integrated_365_24h_unsolved.nc \
     --scenario integrated --label FORMAL_TRIAL_365X24H --out $T/VIOLATIONS_integrated.json > $T/va.log 2> $T/va.err
  echo "VA:exit=$?:$(grep -h 'Maximum resident' $T/va.err | tr -s ' \t' ' '):$(grep -h 'Elapsed' $T/va.err | tr -s ' \t' ' ')" >> $ST
else echo "VA:no solution/X.npy" >> $ST; fi
# 3b supplement 02 C1 (decision 119): precision evidence of the returned solution (read-only, Python only)
if [ -f $T/VIOLATIONS_integrated.json ]; then
  nice -n 19 /usr/bin/time -v $PY $T/s4n_c1_precision.py --repo $REPO --solve-dir $d --network $PKG/networks/integrated_365_24h_unsolved.nc --scenario integrated \
     --label FORMAL_TRIAL_365X24H --violations $T/VIOLATIONS_integrated.json --out-json $T/PILOT_PRECISION.json --out-md $T/PILOT_PRECISION.md > $T/c1.log 2> $T/c1.err
  echo "C1:exit=$?:$(grep -h 'Maximum resident' $T/c1.err | tr -s ' \t' ' '):$(grep -h 'Elapsed' $T/c1.err | tr -s ' \t' ' ')" >> $ST
else echo "C1:no violation analysis output" >> $ST; fi
# 4 light bundle
L=$T/light/s4n_pilot_light_$TS; rm -rf $T/light; mkdir -p $L/export_integrated
for f in $e/*; do
  n=$(basename $f)
  case $n in *_solved.nc|DUALS_BY_CONSTRAINT.nc) echo "LIGHT_EXCLUDED:$n:$(stat -c %s $f)" >> $ST;;
    *) if [ $(stat -c %s $f) -le 31457280 ]; then cp -p $f $L/export_integrated/; else echo "LIGHT_EXCLUDED_LARGE:$n:$(stat -c %s $f)" >> $ST; fi;; esac
done
cp -p $RUN/STATUS.txt $RUN/MONITOR_integrated.csv $B.sha256 $T/BUNDLE_LISTING.txt $L/
for f in S4N4_PILOT_CHECK.json VIOLATIONS_integrated.json PILOT_PRECISION.json PILOT_PRECISION.md; do [ -f $T/$f ] && cp -p $T/$f $L/; done
for f in pilot_check.log va.log c1.log; do [ -f $T/$f ] && grep -viE "$SCRUB" $T/$f > $L/${f%.log}_log.txt; done
for f in pilot_check.err va.err c1.err; do [ -f $T/$f ] && grep -viE "$SCRUB|PROJ" $T/$f | tail -60 > $L/${f%.err}_err_tail.txt; done
cp -p /root/autodl-tmp/s4n_pilot_launch.txt $L/PILOT_LAUNCH.txt
grep -viE "$SCRUB" /root/autodl-tmp/s4n_pilot_console.log > $L/pilot_console_scrubbed.txt 2>/dev/null
TZ=Asia/Singapore ls -la --time-style=+%FT%T $d $d/solution $d/lp 2>/dev/null | grep -v "^total" > $L/FILE_TIMES_SGT.txt
cp -p $T/POST_STATUS.txt $L/POST_STATUS_partial.txt
if grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $L >/dev/null 2>&1; then
  echo "LIGHT:LICENCE STRING FOUND - not packed: $(grep -rIilE 'license[i]d|registered[[:space:]]+to|wls(secret|accessid)' $L | tr '\n' ' ')" >> $ST
else
  (cd $T/light && tar czf $T/s4n_pilot_light_$TS.tar.gz s4n_pilot_light_$TS && cd $T && sha256sum s4n_pilot_light_$TS.tar.gz > s4n_pilot_light_$TS.tar.gz.sha256)
  echo "LIGHT:packed:$(find $L -type f | wc -l) files:$(du -sb $L | cut -f1) B unpacked:$(stat -c %s $T/s4n_pilot_light_$TS.tar.gz) B packed:sha256=$(cut -d' ' -f1 $T/s4n_pilot_light_$TS.tar.gz.sha256)" >> $ST
fi
echo "POST_DONE:$(TZ=Asia/Singapore date '+%F %T') SGT" >> $ST
cat $ST
