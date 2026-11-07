#!/bin/bash
# V31 W15 stage B, section 5.1: result-pack SHA256 against the downloaded .sha256, member check, light-vs-full member identity, and the
# licence-like string scan with the regex of pack_results.sh (file names and hit counts only; contents never printed).
#   bash w15b_integrity.sh <hpc_results_v31> <out file>
set -u
RES=${1:?hpc_results_v31}; OUTF=${2:?out file}
RX='license[i]d|registered[[:space:]]+to|wls(secret|accessid)'   # = pack_results.sh line 30
PY=${PY:-/home/jin/miniforge3/envs/pypsa-earth/bin/python}
{
  echo "# W15 stage B result-pack integrity ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  for f in "$RES"/results_*_final_*.tar.gz; do
    b=$(basename "$f"); a=$(sha256sum "$f" | cut -c1-64); e=$(cut -c1-64 "$f.sha256")
    n=$(tar tzf "$f" | wc -l); bad=$(tar tzf "$f" | grep -cE '^/|(^|/)\.\.(/|$)')
    echo "$b bytes=$(stat -c %s "$f") sha256=$a expected=$e $( [ "$a" = "$e" ] && echo MATCH || echo MISMATCH ) members=$n absolute_or_dotdot=$bad halted=$(echo "$b" | grep -c halted)"
  done
  echo "unpacked files (full pack): $(find "$RES/unpacked/export" -type f | wc -l)"
  "$PY" -I - "$RES" <<'P'
import hashlib, sys, tarfile
from pathlib import Path
res = Path(sys.argv[1]); light = sorted(res.glob("results_light_final_*.tar.gz"))[0]
same = diff = missing = 0; bad = []
with tarfile.open(light, "r:gz") as tf:
    for m in tf:
        if not m.isfile():
            continue
        h = hashlib.sha256(tf.extractfile(m).read()).hexdigest()
        p = res / "unpacked" / m.name
        if not p.exists():
            missing += 1; bad.append(m.name); continue
        hp = hashlib.sha256(p.read_bytes()).hexdigest()
        if h == hp: same += 1
        else: diff += 1; bad.append(m.name)
print(f"light members vs full-pack files: identical={same} differ={diff} missing_in_full={missing} {bad[:10]}")
P
  if grep -rIilE "$RX" "$RES/unpacked" > /dev/null 2>&1; then
    echo "LICENCE_SCAN: HITS"; grep -rIilE "$RX" "$RES/unpacked" | while read -r h; do echo "  ${h#$RES/} $(grep -IicE "$RX" "$h")"; done
  else
    echo "LICENCE_SCAN: no hits (grep -rIilE, regex of pack_results.sh line 30; text files)"
  fi
  echo "LICENCE_SCAN_NON_NC_BINARY_INCLUDED: $(grep -railE "$RX" "$RES/unpacked" --exclude='*.nc' | wc -l) files"
  echo "LICENCE_SCAN_NC_BINARY (NetCDF attributes are stored as plain text): $(grep -ralE "$RX" "$RES/unpacked" --include='*.nc' | wc -l) of $(find "$RES/unpacked" -name '*.nc' | wc -l) files"
} > "$OUTF"
cat "$OUTF"
