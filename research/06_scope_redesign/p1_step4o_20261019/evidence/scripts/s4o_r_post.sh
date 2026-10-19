# S4O-6 point 6 (runs ON the instance via "ssh bash -s" after DONE; read-only on the results; Python not needed; no licence content):
# batch results tarball check (sha256sum -c), member list, a LIGHT package = the export without solved networks and dual files + STATUS / monitor /
# launch / console (licence-type lines filtered) -> /root/autodl-tmp/s4o_post/; licence-string scan of the light package before packing.
set -u
RUN=$(ls -d /root/autodl-tmp/s4o_cloud/runs/*/ | tail -1); RUN=${RUN%/}; TS=$(basename $RUN)
P=/root/autodl-tmp/s4o_post; rm -rf $P; mkdir -p $P
echo "RUN $TS"; grep -E "^(DONE|LICENCE)" $RUN/STATUS.txt
( cd $RUN && sha256sum -c results_$TS.tar.gz.sha256 && ls -l results_$TS.tar.gz | awk '{print "BUNDLE_BYTES", $5}' && tar tzf results_$TS.tar.gz > $P/BUNDLE_LISTING.txt && echo "BUNDLE_MEMBERS $(wc -l < $P/BUNDLE_LISTING.txt)" )
cp $RUN/results_$TS.tar.gz.sha256 $P/
L=$P/s4o_batch_light_$TS; mkdir -p $L
( cd $RUN/export && find . -type f ! -name '*_solved.nc' ! -name 'DUALS_BY_CONSTRAINT.nc' -print0 | xargs -0 -I{} cp --parents {} $L/ )
cp $RUN/STATUS.txt $L/STATUS_run.txt; cp $RUN/MONITOR_*.csv $L/ 2>/dev/null
for f in s4o_batch_launch.txt s4o_preflight.log; do [ -f /root/autodl-tmp/$f ] && cp /root/autodl-tmp/$f $L/; done
grep -viE "licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic" /root/autodl-tmp/s4o_batch_console.txt > $L/batch_console_scrubbed.txt 2>/dev/null
D=$(ls -d /root/autodl-tmp/s4o_cloud/probe/*/ 2>/dev/null | tail -1)
if [ -n "$D" ]; then mkdir -p $L/probe; for f in SPEED_PROBE.json STATUS.txt GUROBI_LOG_SCRUBBED.txt solve_log_scrubbed.txt; do [ -f $D/$f ] && cp $D/$f $L/probe/; done; cp $D/solve/SOLVE_RECEIPT.json $D/solve/V5_GATES.json $L/probe/ 2>/dev/null; fi
( cd $RUN/export && find . -type f -printf '%s %p\n' | sort -k2 ) > $L/EXPORT_FILE_SIZES.txt
du -sh $RUN $RUN/export | sed 's/^/SIZE /'
if grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $L; then echo "LICENCE STRING FOUND IN LIGHT PACKAGE - not packed"; exit 1; fi
( cd $P && tar czf s4o_batch_light_$TS.tar.gz s4o_batch_light_$TS && sha256sum s4o_batch_light_$TS.tar.gz > s4o_batch_light_$TS.tar.gz.sha256 && ls -l s4o_batch_light_$TS.tar.gz | awk '{print "LIGHT_BYTES", $5}' && cat s4o_batch_light_$TS.tar.gz.sha256 )
echo "POST_DONE $(date '+%F %T')"
