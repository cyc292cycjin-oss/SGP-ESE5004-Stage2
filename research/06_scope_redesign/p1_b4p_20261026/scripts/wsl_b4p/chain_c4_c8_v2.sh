#!/bin/bash
# B4P: Gurobi calls 4-8, re-planned after C3 (single-process 112 exceeded the 90 % memory rule; the N < 200 truncations sit in the regime where the
# coupling columns are below GURO_PAR_BARDENSETHRESH = 200 and are NOT handled as dense columns - unlike the full 2920x3h problem):
#   C4 int 224 split probe (25 barrier iterations: ordering statistics, per-iteration seconds at T16, memory with the factor; process 3 too)
#   C5 disc 224 split probe (25 iterations)
#   C6 int 273 probe (25 iterations; process 1 ~9 GiB expected - the watchdog aborts before any Gurobi call if the build exceeds 90 %)
#   C7 disc 273 probe (25 iterations)
#   C8 int 56 split, profile A, SoftMemLimit tiny (trigger test: MEM_LIMIT status, receipt, classification)
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p; ST=$R/SOLVES_STATUS.txt
SOFT_TINY=${SOFT_TINY:-1.5}
echo "CHAIN_V2_START:$(date -u +%FT%TZ):soft_tiny=$SOFT_TINY" >> "$ST"
MODE=probe PROBE_ITERS=25 PROBE_P3=1 SC=integrated N=224 PROFILE=formal_barrier_1e6_t16 TAG=c4_int224_probe25_T16 TL=3300 bash /home/jin/b4p/solve3.sh
MODE=probe PROBE_ITERS=25 PROBE_P3=1 SC=disconnected N=224 PROFILE=formal_barrier_1e6_t16 TAG=c5_disc224_probe25_T16 TL=3300 bash /home/jin/b4p/solve3.sh
MODE=probe PROBE_ITERS=25 PROBE_P3=0 SC=integrated N=273 PROFILE=formal_barrier_1e6_t16 TAG=c6_int273_probe25_T16 TL=3300 bash /home/jin/b4p/solve3.sh
MODE=probe PROBE_ITERS=25 PROBE_P3=0 SC=disconnected N=273 PROFILE=formal_barrier_1e6_t16 TAG=c7_disc273_probe25_T16 TL=3300 bash /home/jin/b4p/solve3.sh
MODE=split SC=integrated N=56 PROFILE=formal_barrier TAG=c8_int56_split_A_softmem_trigger TL=1750 PROTECT="SoftMemLimit=$SOFT_TINY" bash /home/jin/b4p/solve3.sh
echo "CHAIN_V2_DONE:$(date -u +%FT%TZ)" >> "$ST"
