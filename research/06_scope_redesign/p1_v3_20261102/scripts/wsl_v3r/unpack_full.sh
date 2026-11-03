#!/bin/bash
# V3 supplement 07 rerun, second power-on: unpack the verified full pack into a new, empty full_unpacked folder (after refusing absolute or parent paths),
# then scan it for licence-like strings and names (counts / names only, values never printed). Append the resume fetch lines to records/download.log.
# usage: bash unpack_full.sh <cloud_results/<tag> folder> [fetch output file to append]
set -u
D=${1:?results folder}; F=$(ls $D/results_full_*.tar.gz | head -1); U=$D/full_unpacked
( cd $D && sha256sum -c "$(basename $F).sha256" ) || { echo "SHA256_MISMATCH"; exit 1; }
bad=$(tar tzf $F | grep -cE '^/|(^|/)\.\.(/|$)'); echo "entries: $(tar tzf $F | wc -l); absolute or parent paths: $bad"; [ "$bad" = 0 ] || exit 2
[ -e $U ] && { echo "full_unpacked already exists, not overwritten"; exit 3; }
mkdir -p $U && tar xzf $F -C $U --no-same-owner --no-same-permissions && echo "full unpacked: $(find $U -type f | wc -l) files, $(du -sb $U | cut -f1) B"
n=$(grep -rIilE 'license[i]d|registered[[:space:]]+to|wls(secret|accessid)' $U 2>/dev/null | wc -l); echo "licence-like files in the full pack: $n"
echo "licence-like file names: $(find $U -iname '*.lic' -o -iname 'gurobi.lic*' | wc -l)"
for r in V1/integrated V2/no_new_xb V3/disconnected; do ls -la $U/export/${r}_DFX_365X24H_solved.nc 2>&1 | awk '{print $5, $9}' | sed "s|$U/||"; done
if [ -n "${2:-}" ] && [ -f "$2" ]; then
  { echo "== second power-on (no-card mode), resume of the full pack, $(TZ=Asia/Singapore date '+%F %T') SGT"; grep -vE '^[[:space:]]*[0-9]+ Nov|^total|^drwx' "$2"; } >> /home/jin/v3r/records/download.log
  echo "download.log appended"
fi
