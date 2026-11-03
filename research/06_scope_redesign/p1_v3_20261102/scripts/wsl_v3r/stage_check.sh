#!/bin/bash
# V3 supplement 07 rerun: stage the given paths (force for ignored csv / json), mirror /home/jin/v3d too, then the staged-text leak check (final_check.sh: host, port, instance
# prefix, pattern file, licence values; counts only). Commits only when every count of the leak check is 0 and a message file is given. Host / port only from the environment.
# usage: wsl env V3S_HOST=.. V3S_PORT=.. bash stage_check.sh <message file> <path> [<path> ...]
set -u
: "${V3S_HOST:?}" "${V3S_PORT:?}"
MSG=$1; shift
W=/home/jin/wt_v3_20261102; D=research/06_scope_redesign/p1_v3_20261102
cd $W || exit 1
mkdir -p $D/scripts/wsl_v3d $D/scripts/wsl_v3r; cp /home/jin/v3d/*.py /home/jin/v3d/*.sh $D/scripts/wsl_v3d/ 2>/dev/null; cp /home/jin/v3r/*.py /home/jin/v3r/*.sh $D/scripts/wsl_v3r/ 2>/dev/null
[ -e $D/scripts/wsl_v3r/auth.txt ] && { echo "AUTH TEXT IN THE MIRROR"; exit 3; }
git add -f "$@" $D/scripts/wsl_v3d $D/scripts/wsl_v3r
echo "== staged"; git diff --cached --stat | tail -12
R=$(bash /home/jin/v3r/final_check.sh staged); echo "$R"
bad=$(printf '%s\n' "$R" | grep -E '^(host|port|instance prefix|licence values): ' | awk -F': ' '$2 != 0' | wc -l)
pf=$(printf '%s\n' "$R" | awk -F': ' '/^pattern file: /{print $2}')
echo "nonzero connection / instance / licence counts: $bad; pattern-file count: $pf (generic patterns; classified separately)"
[ "$bad" = 0 ] || { echo "REFUSED: leak check not clean - nothing committed (still staged)"; exit 3; }
git commit -q -F "$MSG" && git log --oneline -1 | cut -c1-120
