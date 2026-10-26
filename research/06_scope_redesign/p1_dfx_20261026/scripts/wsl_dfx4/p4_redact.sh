#!/bin/bash
# DFX phase 4: replace the instance name (given only through the environment, DFX_INST) by <INSTANCE> in the evidence copies (the authorisation text
# embedded in RUN.json / SOLVE_RECEIPT.json / solve_time.txt). The recovered packs themselves are not modified (their SHA256 stay valid).
set -u
: "${DFX_INST:?}"
E=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026/evidence/phase4
ls -la /g 2>/dev/null && echo "WARNING: /g exists" || echo "no stray /g"
for f in $(grep -rlw "$DFX_INST" "$E"); do sed -i "s/\b$DFX_INST\b/<INSTANCE>/g" "$f"; echo "redacted ${f#$E/}"; done
for f in "$E"/V1/RUN.json "$E"/V1/SOLVE_RECEIPT.json "$E"/V2/RUN.json "$E"/V2/SOLVE_RECEIPT.json; do python3 -I -c "import json,sys; json.load(open(sys.argv[1]))" "$f" || echo "INVALID JSON $f"; done
echo "remaining files with the name: $(grep -rlw "$DFX_INST" /home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026 | wc -l)"
