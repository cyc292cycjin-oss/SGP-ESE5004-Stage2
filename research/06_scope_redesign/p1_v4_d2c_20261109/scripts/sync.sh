#!/bin/bash
# D2c: mirror the delivery folder into the repository (research/06_scope_redesign/p1_v4_d2c_20261109/; zip files, __pycache__, msg_*.txt, cache/ excluded).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2c_20261109; R=/home/jin/wt_v4_d2c; D=$R/research/06_scope_redesign/p1_v4_d2c_20261109
mkdir -p $D
rsync -a --delete --exclude '*.zip' --exclude '__pycache__' --exclude 'msg_*.txt' --exclude 'cache/' --exclude 'scripts/ref/__pycache__' $W/ $D/
echo "synced $(find $D -type f | wc -l) files"
# D2c: text files written on Windows (python stdout / write_text) carry CRLF; the repository commits LF (text=auto) and the registry hashes the mirrored
# copies, so the mirror is normalised to LF here (the Windows originals are not touched).
find $D -type f \( -name '*.json' -o -name '*.txt' -o -name '*.csv' -o -name '*.md' -o -name '*.py' -o -name '*.sh' \) -exec grep -l $'\r' {} + 2>/dev/null | while read f; do sed -i 's/\r$//' "$f"; echo "LF $f"; done
