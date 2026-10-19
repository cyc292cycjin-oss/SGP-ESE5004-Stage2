#!/bin/bash
# S4N final: archive the helper scripts into the work folder; scan the work folder, the session scratchpad, the WSL helper scripts and the
# calibration commit for the host / port (from the calling environment; refuses empty patterns) and the work folder for licence strings.
: "${S4N_HOST:?}" "${S4N_PORT:?}"
[ ${#S4N_HOST} -gt 5 ] && [ ${#S4N_PORT} -gt 3 ] || { echo "empty pattern - refused"; exit 2; }
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019; SP=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/1fa8f672-a3bf-4ccd-aa5c-a7620da1e9a5/scratchpad
cp /home/jin/s4n*.sh /home/jin/s4n*.py $W/scripts/ 2>/dev/null; echo "scripts archived: $(ls $W/scripts | wc -l)"
echo "== host / port in the work folder, scratchpad and WSL helper scripts (known_hosts excluded, it is hashed):"
grep -rlF -e "$S4N_HOST" -e "$S4N_PORT" $W $SP /home/jin/s4n*.sh /home/jin/s4n*.py 2>/dev/null | grep -v "s4n_known_hosts$"
echo "== host / port in the calibration commit (count):"
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model && git show 7c4f97fe | grep -cF -e "$S4N_HOST" -e "$S4N_PORT"
echo "== licence strings in the work folder:"
grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $W
echo "== done"
