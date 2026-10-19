#!/bin/bash
# copy the S4N helper scripts (no host / port / licence content in them) into the work folder; scan the copies and the work folder for the host /
# port given in the calling environment (refuses empty patterns) and for licence strings. Prints file names only.
: "${S4N_HOST:?}" "${S4N_PORT:?}"
[ ${#S4N_HOST} -gt 5 ] && [ ${#S4N_PORT} -gt 3 ] || { echo "empty pattern - refused"; exit 2; }
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019
mkdir -p $W/scripts
cp /home/jin/s4n*.sh /home/jin/s4n_probe_source.py $W/scripts/ 2>/dev/null
echo "archived: $(ls $W/scripts | wc -l) files"
echo "== host / port in the work folder and the session scratchpad:"
grep -rlF -e "$S4N_HOST" -e "$S4N_PORT" $W /home/jin/s4n* /mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/1fa8f672-a3bf-4ccd-aa5c-a7620da1e9a5/scratchpad 2>/dev/null | grep -v "s4n_known_hosts$"
echo "== licence strings in the work folder:"
grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $W
echo "== done"
