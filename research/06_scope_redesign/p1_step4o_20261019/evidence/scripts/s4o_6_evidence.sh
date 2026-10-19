#!/bin/bash
# S4O-6 evidence into the repo step folder (light files only; the full packages stay in the work folder, not in git) + scripts archive;
# then the final scan: the REAL host / port (from the calling environment only; refuses empty patterns) in the repo step folder, the work folder,
# this session's scratchpad, the WSL helper scripts and the S4O branch commits; licence strings in the step and work folders.
set -u
: "${S4O_HOST:?}" "${S4O_PORT:?}"
[ ${#S4O_HOST} -gt 5 ] && [ ${#S4O_PORT} -gt 3 ] || { echo "empty pattern - refused"; exit 2; }
TS=20261019T162951Z_6896
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; D=$RM/research/06_scope_redesign/p1_step4o_20261019; E=$D/evidence/s4o_6
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019; C=$W/cloud_results/$TS
SP=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/1388eed3-1835-43dd-95c3-52dc53c6afe3/scratchpad
mkdir -p $E
cp -p $C/s4o_batch_light_$TS.tar.gz $C/s4o_batch_light_$TS.tar.gz.sha256 $C/results_$TS.tar.gz.sha256 $C/BUNDLE_LISTING.txt $C/S4O6_BATCH_SUMMARY.json $C/S4O6_BATCH_SUMMARY.md $E/
cp -p $C/full/*.sha256 $E/
rsync -a $C/top/ $E/top/
rsync -a --max-size=500k $C/unpacked/ $E/light_unpacked/
cp -p $SP/s4o_watch.log $E/WATCH_LOG.txt 2>/dev/null
cp /home/jin/s4o_ssh.sh /home/jin/s4o_r_check.sh /home/jin/s4o_c1.sh /home/jin/s4o_c2.sh /home/jin/s4o_c4.sh /home/jin/s4o_c5.sh /home/jin/s4o_probe.sh /home/jin/s4o_launch_batch.sh \
   /home/jin/s4o_watch.sh /home/jin/s4o_r_watch.sh /home/jin/s4o_r_restart.sh /home/jin/s4o_r_post.sh /home/jin/s4o_r_runpack.sh /home/jin/s4o_get.sh /home/jin/s4o_get_runs.sh \
   /home/jin/s4o_del_lic.sh /home/jin/s4o_6_summary.sh /home/jin/s4o_6_unpack.sh /home/jin/s4o_6_evidence.sh $D/evidence/scripts/
chmod 755 $D/evidence/scripts/*.sh
echo "evidence files: $(find $E -type f | wc -l), size $(du -sh $E | cut -f1)"
echo "== host / port in the step folder, work folder, scratchpad and WSL helper scripts (known_hosts excluded, it is hashed):"
grep -rlF -e "$S4O_HOST" -e "$S4O_PORT" $D $W $SP /home/jin/s4o*.sh /home/jin/s4n*.sh 2>/dev/null | grep -v "s4o_known_hosts$" || echo "none"
echo "== host / port in the S4O and S4N branch commits since b3b3e5d2 (count):"
cd $RM && git log -p b3b3e5d2..HEAD | grep -cF -e "$S4O_HOST" -e "$S4O_PORT"
echo "== licence strings (step folder, work folder):"
grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $D $W 2>/dev/null || echo "none"
echo "== done"
