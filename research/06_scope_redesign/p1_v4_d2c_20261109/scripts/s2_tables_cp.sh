#!/bin/bash
# D2c section 2.2: rewrite the v4 table folders for the new main switch set (biomass_potential v4_adjusted_t06), drop the superseded D2b residue_literal folder
# (t05-based), run the reference engine on the T06 potential (fresh scratch copies of the D2b T05 scratch without results; BIOMASS_POTENTIAL_2050_I2.csv
# replaced by the T06 file) and compare the repository checkpoints S0-S7 (T_v2 must be unchanged). No solver, no network build.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2c_20261109; R=/home/jin/wt_v4_d2c; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d2c
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
LOG=$W/logs/s2_tables_cp.txt; : > $LOG
exec >> $LOG 2>&1
cd $R || exit 1
echo "== tables $(date -u +%H:%M:%S)"
OLD_LIT=research_inputs/industry_v4/out_ras_74ec30609dc1
[ -d $OLD_LIT ] && { git rm -r -q --cached $OLD_LIT 2>/dev/null; rm -rf $OLD_LIT; echo "removed superseded D2b residue_literal folder $OLD_LIT"; }
bash $W/scripts/regen_tables.sh 2>&1 | grep -v "^SAME" | grep -v '"' | head -60
echo "== reference scratch (T06 potential) $(date -u +%H:%M:%S)"
for n in main iid; do
  [ -d $T/ref_${n}_t06 ] || { rsync -a --exclude results /home/jin/v4d2b/ref_${n}_t05/ $T/ref_${n}_t06/; cp research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4_T06.csv $T/ref_${n}_t06/BIOMASS_POTENTIAL_2050_I2.csv; echo "scratch ref_${n}_t06"; }
done
cd $W || exit 1
run() { n=$1; shift; ( export W08_REF_SCRATCH=$T/ref_$n PYTHONHASHSEED=0 "$@"; $PY scripts/d2c_ref_run.py ${STEPS:-} > $T/ref_log_$n.txt 2>&1; echo "EXIT:$?" >> $T/ref_log_$n.txt ) & }
run main_t06 W08_ANCHOR_MODE=ras W08_ID_PAPER_FW=residue
run iid_t06 W08_ANCHOR_MODE=fixedcol W08_ID_PAPER_FW=residue
wait
for n in main_t06 iid_t06; do echo "--- ref_$n"; tail -3 $T/ref_log_$n.txt; done
echo "== checkpoints $(date -u +%H:%M:%S)"
cd $R || exit 1
cp() { label=$1; ref=$2; steps=$3; shift 3
  $PY scripts_project/v4_industry.py --checkpoints $T/cp_$label --steps $steps --work $T/work_cp_$label "$@" > $T/cp_$label.log 2>&1 || { echo "CHAIN_FAILED $label"; tail -20 $T/cp_$label.log; return 1; }
  $PY $W/scripts/d2c_checkpoints.py $T/cp_$label $T/ref_$ref/results $label --steps $steps | tail -4; echo "CP_$label:exit=$?"; }
cp main_t06 main_t06 S0,S1,S2,S3,S4,S5a,S5b,S5c,S5d,S5e,S5f,S5g,S6a,S6b,S6c,S7 --anchor-mode ras
cp iid_t06 iid_t06 S1,S2,S3,S4,S5a,S5b,S5c,S5d,S5e,S5f,S5g,S6a,S6b,S6c,S7 --anchor-mode iid
echo "S2_TABLES_CP_DONE $(date -u +%H:%M:%S)"
