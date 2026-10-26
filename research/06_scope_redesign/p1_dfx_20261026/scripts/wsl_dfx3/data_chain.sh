#!/bin/bash
# DFX v3 demand data chain (no build, no solve), the M08b order plus dfx_data.py: m08b_demand -> m08b_heat_bands -> s3_0_industry -> s2b_feedstock
# -> s2_0_process_emissions -> m08b_data -> dfx_data -> d1_registry -> dfx_data changelog. Runs with the F0 module recorder so that the data-chain
# modules enter the actual-execution list (CODE_MAP). SHA256 snapshot of research_inputs before / after; lists changed and new files.
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export M08B_IDEES_XLSX=$MAIN/research_inputs/registry_v5/sources/jrc_idees_2021/EU27/JRC-IDEES-2021_Industry_EU27.xlsx
export PYTHONPATH=/home/jin/dfx3/trace; export DFX_TRACE_OUT=$MAIN/results_project/dfx_v3/f0_trace/modules.jsonl
LOG=$MAIN/results_project/dfx_v3/data_chain; mkdir -p $LOG
cd "$WT" || exit 1
SNAP=$LOG/snapshot_before.txt
find research_inputs/demand_v5 research_inputs/registry_v5 -maxdepth 2 -type f -not -path '*/sources/*' | sort | xargs sha256sum > $SNAP
cd scripts_project || exit 2
rc_all=0
for s in m08b_demand.py m08b_heat_bands.py s3_0_industry.py s2b_feedstock.py s2_0_process_emissions.py m08b_data.py dfx_data.py d1_registry.py; do
  [ -f "$s" ] || { echo "$s MISSING"; continue; }
  DFX_TRACE_TAG=data_chain_${s%.py} /usr/bin/time -v $PY $s > $LOG/$s.log 2> $LOG/$s.err; rc=$?
  echo "$s exit=$rc $(grep -h 'Elapsed' $LOG/$s.err | tr -s ' ' | cut -c1-60) $(grep -h 'Maximum resident' $LOG/$s.err | tr -s ' ')"
  [ $rc = 0 ] || { rc_all=$rc; grep -v -E "UserWarning|parser.parse|Elapsed|Maximum resident|^\s" $LOG/$s.err | tail -8; }
  tail -${TAILN:-2} $LOG/$s.log
done
if [ -f dfx_data.py ]; then DFX_TRACE_TAG=data_chain_dfx_changelog $PY dfx_data.py changelog > $LOG/dfx_changelog.log 2> $LOG/dfx_changelog.err; echo "dfx_data.py changelog exit=$?"; tail -3 $LOG/dfx_changelog.log; fi
cd "$WT"
echo "--- pre-existing files whose bytes changed:"
sha256sum -c --quiet $SNAP 2>/dev/null | sed 's/: FAILED//' | head -80
echo "--- new files:"
comm -13 <(cut -c67- $SNAP | sort) <(find research_inputs/demand_v5 research_inputs/registry_v5 -maxdepth 2 -type f -not -path '*/sources/*' | sort) | head -40
echo "--- registry:"; sha256sum research_inputs/registry_v5/DATA_REGISTRY.csv; grep -c '' research_inputs/registry_v5/DATA_REGISTRY.csv
echo "DATA_CHAIN_EXIT=$rc_all"
