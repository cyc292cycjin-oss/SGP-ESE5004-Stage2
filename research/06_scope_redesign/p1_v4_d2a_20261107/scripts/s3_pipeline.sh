#!/bin/bash
# D2a section 3 pipeline: apply the section-3 patch, regenerate the potential tables (W08 basis unchanged + T04), rewrite the v4 table folders (the switch set
# changed: biomass_potential = v4_adjusted_t04), registry fragments, run the v4 tests, and compare the checkpoints with the corrected reference run on the T04
# potential (reference scratch copies with BIOMASS_POTENTIAL_2050_I2.csv replaced by the T04 file). No solver, no network build.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107; R=/home/jin/wt_v4_d2a; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d2a
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
cd $R || exit 1
echo "== patch"; $PY /mnt/c/Users/20122/AppData/Local/Temp/claude/04b3c55e6902fb59/7b5b747c-ee5e-4beb-86d7-280e4d03d491/scratchpad/patch_s3b.py $R || exit 1
echo "== potential"; $PY scripts_project/v4_biomass_potential.py > $T/biopot.log 2>&1 || { tail -20 $T/biopot.log; exit 1; }; cat $T/biopot.log
[ "$(git show HEAD:research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv | sha256sum | cut -c1-64)" = "$(sha256sum research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv | cut -c1-64)" ] && echo "W08 potential file unchanged" || echo "WARNING: W08 potential file changed"
echo "== tables"; rm -rf research_inputs/industry_v4/out_ras_bf751c248682
bash $W/scripts/regen_tables.sh 2>&1 | grep -v "^SAME" | grep -v '"' | head -40
echo "== registry"; bash $W/scripts/run_registry.sh 2>&1 | tail -30
echo "== reference scratch (T04 potential)"
for n in main iid; do
  [ -d $T/ref_${n}_t04 ] || { rsync -a --exclude results $T/ref_$n/ $T/ref_${n}_t04/; cp research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4_T04.csv $T/ref_${n}_t04/BIOMASS_POTENTIAL_2050_I2.csv; echo "scratch ref_${n}_t04"; }
done
cd $W || exit 1
run() { n=$1; shift; ( export W08_REF_SCRATCH=$T/ref_$n PYTHONHASHSEED=0 "$@"; $PY scripts/d2a_ref_run.py ${STEPS:-} > $T/ref_log_$n.txt 2>&1; echo "EXIT:$?" >> $T/ref_log_$n.txt ) & }
run main_t04 W08_ANCHOR_MODE=ras W08_ID_PAPER_FW=residue
run iid_t04 W08_ANCHOR_MODE=fixedcol W08_ID_PAPER_FW=residue
wait
for n in main_t04 iid_t04; do echo "--- ref_$n"; tail -3 $T/ref_log_$n.txt; done
echo "== checkpoints"
cd $R || exit 1
cp() { label=$1; ref=$2; steps=$3; shift 3
  $PY scripts_project/v4_industry.py --checkpoints $T/cp_$label --steps $steps --work $T/work_cp_$label "$@" > $T/cp_$label.log 2>&1 || { echo "CHAIN_FAILED $label"; tail -20 $T/cp_$label.log; return 1; }
  $PY $W/scripts/d2a_checkpoints.py $T/cp_$label $T/ref_$ref/results $label --steps $steps | tail -4; echo "CP_$label:exit=$?"; }
cp main_t04 main_t04 S0,S1,S2,S3,S4,S5a,S5b,S5c,S5d,S5e,S5f,S5g,S6a,S6b,S6c,S7 --anchor-mode ras
cp iid_t04 iid_t04 S1,S2,S3,S4,S5a,S5b,S5c,S5d,S5e,S5f,S5g,S6a,S6b,S6c,S7 --anchor-mode iid
cp i2chk_s3 i2chk S1,S7 --anchor-mode iid --set id_paper_fuelwood=purchased --set biomass_potential=v4_adjusted
echo "== tests"
bash $W/scripts/ut.sh s3 tests/research/test_v4_d2a_efb.py tests/research/test_v4_d2a_supply.py tests/research/test_v4_d2a_fixes.py tests/research/test_v4_a2_fallback.py tests/research/test_v4_registry.py tests/research/test_v4_d1_prep.py tests/research/test_v4_industry_cache.py tests/research/test_v4_profiles.py tests/research/test_v4_biomass_potential.py tests/research/test_v4_transport_accounts.py tests/research/test_v4_products.py tests/research/test_v4_captive.py tests/research/test_v4_anchor_iid.py tests/research/test_v4_base_sdmx.py tests/research/test_v4_d1_missing_cost.py tests/research/test_v4_d1_palm.py tests/research/test_v4_d1_physics.py 2>&1 | tail -6
echo S3_PIPELINE_DONE
