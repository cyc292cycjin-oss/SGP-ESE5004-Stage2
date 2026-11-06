set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107
RUN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56
ls $RUN; ls $RUN/v31_F1 | head -50
head -c 1500 $RUN/v4_F1/COMPONENT_COST_BREAKDOWN_SUMMARY.json; echo
cd /home/jin/wt_v4_fable && $PY $S/scripts/smoke_decomp.py $RUN $S/evidence/SMOKE_DECOMP.json 2>&1 | grep -v "^INFO" | tail -70
