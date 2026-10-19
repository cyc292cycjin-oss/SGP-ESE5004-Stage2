# S4O-6 point 6 (runs ON the instance via "RUNS='a b' bash -s"; read-only on the results): per-run FULL package = export/<run>/ (incl. solved network
# and dual file, already re-graded) -> /root/autodl-tmp/s4o_post/full_<run>_<TS>.tar.gz + .sha256; licence-string scan of the text members first.
set -u
RUN=$(ls -d /root/autodl-tmp/s4o_cloud/runs/*/ | tail -1); RUN=${RUN%/}; TS=$(basename $RUN); P=/root/autodl-tmp/s4o_post; mkdir -p $P
for r in $RUNS; do
  [ -d $RUN/export/$r ] || { echo "NO EXPORT $r"; continue; }
  if grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $RUN/export/$r; then echo "LICENCE STRING FOUND in $r - not packed"; continue; fi
  ( cd $RUN/export && nice -n 19 tar czf $P/full_${r}_$TS.tar.gz $r && cd $P && sha256sum full_${r}_$TS.tar.gz > full_${r}_$TS.tar.gz.sha256 && ls -l full_${r}_$TS.tar.gz | awk '{print "PACKED", $NF, $5}' )
done
ls -l $P | tail -5
