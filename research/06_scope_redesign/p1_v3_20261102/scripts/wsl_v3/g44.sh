#!/bin/bash
W=/home/jin/wt_v3_20261102
cd $W
git grep -n -E 'S4E-1|apg_existing_mw|Table 1' -- 'scripts_project/*.py' | head -12 | cut -c1-200
git log --all --oneline --grep='APG' | head -8 | cut -c1-120
grep -rln "CORRIDOR_APG_CROSSCHECK" scripts_project research/ 2>/dev/null | head -10
