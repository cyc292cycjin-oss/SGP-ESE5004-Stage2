#!/bin/bash
# Instruction 1.2: check package networks against pbs/HPC_PLAN.txt NETWORK rows.
set -u
PKG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3
OUT=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105/evidence/network_sha256_check.txt
mkdir -p "$(dirname "$OUT")"
{
echo "time $(date -Is)"
echo "plan $PKG/pbs/HPC_PLAN.txt sha256 $(sha256sum "$PKG/pbs/HPC_PLAN.txt" | cut -d' ' -f1)"
ok=0; bad=0
grep '^NETWORK|' "$PKG/pbs/HPC_PLAN.txt" | while IFS='|' read -r tag name sha size bc; do
  f="$PKG/networks/$name"
  got=$(sha256sum "$f" | cut -d' ' -f1)
  gsz=$(stat -c %s "$f")
  if [ "$got" = "$sha" ] && [ "$gsz" = "$size" ]; then r=MATCH; else r=MISMATCH; fi
  echo "$r $name plan_sha=$sha got_sha=$got plan_size=$size got_size=$gsz"
done
} | tee "$OUT"
