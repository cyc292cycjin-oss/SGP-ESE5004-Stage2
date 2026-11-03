#!/bin/bash
# V3 supplement 07 rerun: generic pattern-file hits of one commit, by pattern name and file (counts only, never the matched text). usage: bash pf_hits.sh <commit>
cd /home/jin/wt_v3_20261102 || exit 1
C=${1:-HEAD}
for f in $(git show --name-only --format= "$C"); do
  t=$(git show "$C:$f" 2>/dev/null) || continue
  while IFS= read -r line; do
    case "$line" in \#*|"") continue;; esac
    k=${line%%=*}; p=${line#*=}
    n=$(printf '%s\n' "$t" | grep -ciE "$p")
    [ "$n" != 0 ] && echo "$k $n $f"
  done < /home/jin/.dfx_leak_patterns
done
