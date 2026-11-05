#!/bin/bash
# Instruction 1.3: the four network SHA256 / bytes of the v3.1 package = pbs/HPC_PLAN.txt NETWORK lines (v3 and v3.1 plans) = the v3 package files. Read-only.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102; O=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence/NETWORK_SHA256_CHECK.txt
{ for pk in hpc_package_v3 hpc_package_v3_1; do
    grep '^NETWORK|' $W/$pk/pbs/HPC_PLAN.txt | while IFS='|' read -r _ f s b c; do
      a=$(sha256sum $W/hpc_package_v3_1/networks/$f | cut -c1-64); n=$(stat -c %s $W/hpc_package_v3_1/networks/$f)
      [ "$a" = "$s" ] && [ "$n" = "$b" ] && r=MATCH || r=DIFFER
      echo "$pk/pbs/HPC_PLAN.txt $f $s $b -> v3.1 package $a $n $r"
    done
  done
  for f in $(cd $W/hpc_package_v3/networks && ls); do cmp -s $W/hpc_package_v3/networks/$f $W/hpc_package_v3_1/networks/$f && echo "networks/$f identical to the v3 package" || echo "networks/$f DIFFERS from the v3 package"; done
} > $O
cat $O; echo "MATCH lines: $(grep -c ' MATCH$' $O) / 8; identical: $(grep -c identical $O)"
