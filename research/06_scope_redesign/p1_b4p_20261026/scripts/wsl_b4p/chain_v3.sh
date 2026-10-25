#!/bin/bash
# B4P: Gurobi calls 5-7 (re-planned after C4: a T16 Gurobi process at 224 snapshots exceeds the 10.95 GiB WSL during the ordering, so the dense
# column regime of the full problem is emulated on smaller truncations with a MEASUREMENT-ONLY override GURO_PAR_BARDENSETHRESH=100 (the
# coupling columns of a 140 / 182-snapshot model then count as dense, as every such column does at 2920 > 200). Recorded as measurement_parameters;
# the registered profile is untouched.
#   C5 int 140 probe 25 it, thr 100 | C6 disc 140 probe 25 it, thr 100 | C7 int 182 probe 25 it, thr 100 (watchdog-protected)
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p; ST=$R/SOLVES_STATUS.txt
rm -rf "$R/solves/c5_disc224_probe25_T16"   # process 1 interrupted when the chain was paused; no Gurobi call was made
echo "CHAIN_V3_START:$(date -u +%FT%TZ):measure=GURO_PAR_BARDENSETHRESH=100 on 140 / 182 (dense-column regime emulation)" >> "$ST"
MODE=probe PROBE_ITERS=25 PROBE_P3=1 MEASURE="GURO_PAR_BARDENSETHRESH=100" SC=integrated N=140 PROFILE=formal_barrier_1e6_t16 TAG=c5_int140_probe25_T16_thr100 TL=3300 bash /home/jin/b4p/solve3.sh
MODE=probe PROBE_ITERS=25 PROBE_P3=1 MEASURE="GURO_PAR_BARDENSETHRESH=100" SC=disconnected N=140 PROFILE=formal_barrier_1e6_t16 TAG=c6_disc140_probe25_T16_thr100 TL=3300 bash /home/jin/b4p/solve3.sh
MODE=probe PROBE_ITERS=25 PROBE_P3=0 MEASURE="GURO_PAR_BARDENSETHRESH=100" SC=integrated N=182 PROFILE=formal_barrier_1e6_t16 TAG=c7_int182_probe25_T16_thr100 TL=3300 bash /home/jin/b4p/solve3.sh
echo "CHAIN_V3_DONE:$(date -u +%FT%TZ)" >> "$ST"
