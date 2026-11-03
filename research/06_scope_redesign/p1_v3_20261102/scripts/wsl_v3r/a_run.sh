# V3 screening rerun (supplement 07) (local, read-only on the recovered packs): run the result analysis on the light pack, unpack the full pack and list the solved networks.
set -u
C=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
DFX=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_results/final_20261026T223024Z/analysis/DFX_PHASE4_RESULTS.json
mkdir -p $C/analysis
PYTHONHASHSEED=0 $PY -I /home/jin/v3r/v3s_analysis.py $C/light_unpacked $DFX $C/analysis; echo "ANALYSIS_EXIT:$?"
if [ ! -d $C/full_unpacked ]; then
  mkdir -p $C/full_unpacked && tar -xzf $C/results_full_final_20261103T063207Z.tar.gz -C $C/full_unpacked; echo "UNTAR_EXIT:$?"
fi
find $C/full_unpacked -name '*_solved.nc' -printf '%s %p\n' | sed "s|$C/||"
find $C/full_unpacked -maxdepth 2 | sed "s|$C/||" | head -20
