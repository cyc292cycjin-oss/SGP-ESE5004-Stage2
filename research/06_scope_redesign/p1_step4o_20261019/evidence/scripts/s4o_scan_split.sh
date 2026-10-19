#!/bin/bash
# S4O-6 final scan, split: host name hits (must be none) and port hits with their context (number-embedded matches are coincidences in data).
# Host / port from the calling environment only; the output never prints them (the matched token is masked).
set -u
: "${S4O_HOST:?}" "${S4O_PORT:?}"
[ ${#S4O_HOST} -gt 5 ] && [ ${#S4O_PORT} -gt 3 ] || { echo "empty pattern - refused"; exit 2; }
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; D=$RM/research/06_scope_redesign/p1_step4o_20261019
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019
SP=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/1388eed3-1835-43dd-95c3-52dc53c6afe3/scratchpad
HOSTSHORT=${S4O_HOST%%.*}
echo "== host name (full or first label) hits:"
grep -rlF -e "$S4O_HOST" -e "$HOSTSHORT.west" $D $W $SP /home/jin/s4o*.sh /home/jin/s4n*.sh 2>/dev/null | grep -v "s4o_known_hosts$" || echo "none"
echo "== port as a stand-alone token (not inside a longer number / decimal):"
grep -rnoE "(^|[^0-9.eE+-])$S4O_PORT([^0-9]|$)" $D $W $SP /home/jin/s4o*.sh /home/jin/s4n*.sh 2>/dev/null | grep -v "s4o_known_hosts:" | sed "s/$S4O_PORT/<PORT>/g" | cut -c1-200 | head -20 || true
echo "== port hits inside longer numbers (count of files):"
grep -rlF -e "$S4O_PORT" $D $W $SP 2>/dev/null | wc -l
echo "== commits since b3b3e5d2: host hits, stand-alone port hits"
cd $RM && git log -p b3b3e5d2..HEAD | grep -cF -e "$S4O_HOST"; git log -p b3b3e5d2..HEAD | grep -E "(^|[^0-9.eE+-])$S4O_PORT([^0-9]|$)" | sed "s/$S4O_PORT/<PORT>/g" | cut -c1-160 | head -5
git log -p b3b3e5d2..HEAD | grep -F "$S4O_PORT" | sed "s/$S4O_PORT/<PORT>/g" | cut -c1-160 | head -3
