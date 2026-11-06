set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107
WT=/home/jin/wt_v4_fable
B=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds
cd $WT || exit 1
echo "################ CHAIN"; $PY $S/scripts/chain_check.py $WT $S/evidence/CHAIN_CHECK.json 2>&1 | tail -40
echo "################ CONSERVATION"; $PY $S/scripts/conservation_check.py $WT $S/evidence/CONSERVATION_CHECK.json 2>&1 | tail -70
echo "################ ANCHOR / PROFILES"; $PY $S/scripts/anchor_profile_check.py $WT $S/evidence/ANCHOR_PROFILE_CHECK.json 2>&1 | tail -90
echo "################ NET main"; $PY $S/scripts/net_check.py $B/main/integrated/integrated_2920_3h_unsolved.nc $WT out_ras $S/evidence/NET_CHECK_main.json 2>&1 | grep -v "^INFO" | tail -80
