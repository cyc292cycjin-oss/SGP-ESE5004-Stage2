#!/bin/bash
# V31 W15 stage A, section 1.1-1.2: archive SHA256 against the downloaded .sha256, member check, and the licence-like string scan with the
# regex of the package's pack_results.sh (file names and hit counts only; contents are never printed).
#   bash w15a_integrity.sh <hpc_results_v31> <out file>
set -u
RES=${1:?hpc_results_v31}; OUTF=${2:?out file}
RX='license[i]d|registered[[:space:]]+to|wls(secret|accessid)'   # = pack_results.sh line 30
{
  echo "# W15 stage A archive integrity ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  for f in "$RES"/interim_F*.tar.gz; do
    b=$(basename "$f"); a=$(sha256sum "$f" | cut -c1-64); e=$(cut -c1-64 "$f.sha256")
    n=$(tar tzf "$f" | wc -l); bad=$(tar tzf "$f" | grep -cE '^/|(^|/)\.\.(/|$)'); top=$(tar tzf "$f" | cut -d/ -f1-2 | sort -u | tr '\n' ' ')
    types=$(tar tzvf "$f" | cut -c1 | sort | uniq -c | tr -s ' ' | tr '\n' ';')
    echo "$b bytes=$(stat -c %s "$f") sha256=$a expected=$e $( [ "$a" = "$e" ] && echo MATCH || echo MISMATCH ) members=$n absolute_or_dotdot=$bad top=[$top] types=[$types]"
  done
  echo "missing: $(for r in F1 F2 F3 F4; do [ -f "$RES/interim_$r.tar.gz" ] || printf '%s ' "interim_$r.tar.gz"; done)"
  echo "unpacked files: $(find "$RES/interim_unpacked" -type f | wc -l)"
  if grep -rIilE "$RX" "$RES/interim_unpacked" > /dev/null 2>&1; then
    echo "LICENCE_SCAN: HITS"; grep -rIilE "$RX" "$RES/interim_unpacked" | while read -r h; do echo "  ${h#$RES/} $(grep -IicE "$RX" "$h")"; done
  else
    echo "LICENCE_SCAN: no hits (grep -rIilE, regex of pack_results.sh line 30)"
  fi
  echo "LICENCE_SCAN_BINARY_INCLUDED: $(grep -railE "$RX" "$RES/interim_unpacked" | wc -l) files"
} > "$OUTF"
cat "$OUTF"
