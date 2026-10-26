#!/bin/bash
# DFX phase 4: recover the results packs of runs/dfx (light first, then full) with ONE rsync stream each, verify the SHA256 locally, unpack the light
# pack and scan it for licence-like strings (counts / names only). Usage: wsl env DFX_HOST=.. DFX_PORT=.. bash /home/jin/dfx4/get.sh <light|full|both>
set -u
source /home/jin/dfx4/ssh.sh
WHAT=${1:-both}; R=/root/autodl-tmp/dfx_v8/runs/dfx; L=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_results; mkdir -p $L
err=$(mktemp)
list=$(dfx_ssh "cd $R && ls -t results_light_*.tar.gz results_full_*.tar.gz 2>/dev/null" 2>"$err") || { dfx_scrub "listing failed $(cat "$err")"; rm -f "$err"; exit 2; }
LIGHT=$(printf '%s\n' "$list" | grep '^results_light_' | head -1); FULL=$(printf '%s\n' "$list" | grep '^results_full_' | head -1)
[ -n "$LIGHT" ] || { echo "no light pack on the instance yet"; exit 2; }
TAG=$(echo "$LIGHT" | sed -E 's/^results_light_(.*)\.tar\.gz$/\1/'); D=$L/$TAG; mkdir -p $D
echo "packs: light=$LIGHT full=${FULL:-none} -> $D"
fetch() { local f=$1 t0 rc; t0=$(date +%s)
  rsync -a --partial --info=stats1 -e "ssh ${DFX_OPTS[*]} -p $DFX_PORT" "root@$DFX_HOST:$R/$f" "root@$DFX_HOST:$R/$f.sha256" "$D/" > /dev/null 2>"$err"; rc=$?
  [ -s "$err" ] && dfx_scrub "STDERR: $(cat "$err")"; : > "$err"
  echo "FETCH $f rsync_exit=$rc seconds=$(( $(date +%s) - t0 )) bytes=$(stat -c %s "$D/$f" 2>/dev/null)"
  ( cd $D && sha256sum -c "$f.sha256" ) && echo "SHA256_OK $f" || { echo "SHA256_MISMATCH $f"; return 1; } }
case "$WHAT" in light|both) fetch "$LIGHT" || exit 1
  mkdir -p $D/light_unpacked && tar xzf $D/$LIGHT -C $D/light_unpacked && echo "light unpacked: $(find $D/light_unpacked -type f | wc -l) files"
  n=$(grep -rIilE 'license[i]d|registered[[:space:]]+to|wls(secret|accessid)' $D/light_unpacked 2>/dev/null | wc -l); echo "licence-like files in the light pack: $n";; esac
case "$WHAT" in full|both) [ -n "$FULL" ] && { fetch "$FULL" || exit 1; } || echo "no full pack";; esac
rm -f "$err"; ls -la $D
