#!/bin/bash
set -eu
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4k_20261018
OLD=$W/cloud_package_dist_2d4aaac3_superseded
[ -e $OLD ] || { echo "superseded dir missing"; exit 1; }
[ "$(cat $OLD/COMMIT)" = "2d4aaac34ef4db779a1ac5a4d40f3029b65dbafb" ] && [ ! -e $W/cloud_package_dist ]
echo "old package kept at $OLD"
S=results_project/s4k/s4k4; ST=$S/STATUS.txt
echo "REPACK_START:$(date -u +%FT%TZ) commit:$(git rev-parse --short HEAD) (serial preflight minimum 40 GiB, user decision on S4K report 8.1); previous package kept as cloud_package_dist_2d4aaac3_superseded" >> $ST
bash research/06_scope_redesign/p1_step4k_20261018/cloud_package/make_package.sh $S/builds $W/cloud_package_dist > $S/make_package_repack.log 2>&1; echo "REPACKAGE:$?" >> $ST
tail -3 $ST
cat $W/cloud_package_dist/COMMIT
cd $W && diff <(sed 's/  .*//' cloud_package_dist_2d4aaac3_superseded/SHA256SUMS | sort) <(sed 's/  .*//' cloud_package_dist/SHA256SUMS | sort) >/dev/null || true
join -j 2 <(awk '{print $1, $2}' cloud_package_dist_2d4aaac3_superseded/SHA256SUMS | sort -k2) <(awk '{print $1, $2}' cloud_package_dist/SHA256SUMS | sort -k2) | awk '{print ($2==$3 ? "same   " : "CHANGED"), $1}'
grep -n "need_m=" cloud_package_dist/preflight.sh
