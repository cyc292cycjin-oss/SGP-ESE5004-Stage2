#!/bin/bash
# DFX phase 4: mirror /home/jin/dfx4 into the deliverable folder scripts/wsl_dfx4. Excluded: auth.txt (authorisation text; names the instance),
# instance_records.txt (raw copy; the filtered records are in evidence/phase4/instance), tmp_*.sh, upload.log (copied to evidence). The instance
# name is replaced by a placeholder in the mirrored copies. Host / port never appear in these files (checked by the leak scan at run time).
set -u
S=/home/jin/dfx4; M=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026/scripts/wsl_dfx4
mkdir -p "$M"
for f in "$S"/*.sh "$S"/*.py; do
  b=$(basename "$f")
  case "$b" in tmp_*) continue;; esac
  sed "s/instance <INSTANCE>/instance <INSTANCE>/g; s/<INSTANCE>/<INSTANCE>/g" "$f" > "$M/$b"
done
ls "$M" | wc -l; grep -c "<INSTANCE>" "$M"/* | grep -v ":0" || echo "no instance name in the mirror"
