#!/bin/bash
# V3 DIAG step 5 (+ a second F1 window): F2 February window [248,472) with the runner TRUNCATE weighting - presolve probe, then the bunker row deleted;
# F1 January [0,248) with the bunker row deleted. Constraint-group indexes and bunker labels by rebuild (no solver). Three Gurobi calls.
set -u
. "$(dirname "$0")/common.sh"
bash "$S/build.sh" F2_M02 F2 248 224 || { log "STEP5_STOP:F2_M02 build failed"; exit 2; }
bash "$S/probe.sh" F2_M02 F2_M02 --protect MemLimit=7 --protect SoftMemLimit=6; ex=$?
[ $ex = 3 ] && { log "STEP5_STOP:no token route"; exit 2; }
L=$RUNROOT/F2_M02/gurobi.linopy.log
if grep -qi "infeasible or unbounded" "$L"; then v=INF_OR_UNBD; elif grep -q "^Presolved:" "$L"; then v=PRESOLVE_PASSED; else v=UNDECIDED; fi
log "VERDICT:F2_M02:$v:probe_exit=$ex"
bash "$S/con_groups.sh" F2_M02
bash "$S/bunker_labels.sh" F2_M02
[ "$v" = INF_OR_UNBD ] && bash "$S/del_probe.sh" F2_M02 F2_M02_del_bunker '^research_bunker_co2_limit'
bash "$S/con_groups.sh" F1_M01
bash "$S/del_probe.sh" F1_M01 F1_M01_del_bunker '^research_bunker_co2_limit'
log "STEP5_DONE:$(now)"
