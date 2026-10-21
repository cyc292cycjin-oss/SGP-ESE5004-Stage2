#!/bin/bash
# M08b B1/B2 data chain (no build, no solve): anchors -> heat bands -> industry tables -> feedstock tables -> process-emission rows.
# Snapshot SHA256 of the existing research_inputs files before and list every pre-existing file whose bytes changed afterwards.
set -u
WT=/home/jin/wt_m08b_20261021
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export M08B_IDEES_XLSX=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/research_inputs/registry_v5/sources/jrc_idees_2021/EU27/JRC-IDEES-2021_Industry_EU27.xlsx
cd "$WT" || exit 1
SNAP=/home/jin/m08b_data_snapshot.txt
if [ "${SNAPSHOT:-1}" = "1" ]; then
  find research_inputs/demand_v5 research_inputs/registry_v5 -maxdepth 2 -type f -not -path '*/sources/*' | sort | xargs sha256sum > $SNAP
fi
cd scripts_project || exit 2
for s in m08b_demand.py m08b_heat_bands.py s3_0_industry.py s2b_feedstock.py s2_0_process_emissions.py; do
  $PY $s > /tmp/m08b_$s.log 2>&1; echo "$s exit=$?"; tail -${TAILN:-3} /tmp/m08b_$s.log
done
cd "$WT"
echo "--- pre-existing files whose bytes changed:"
sha256sum -c --quiet $SNAP 2>/dev/null | sed 's/: FAILED//' | head -60
echo "--- new files:"
comm -13 <(cut -c67- $SNAP | sort) <(find research_inputs/demand_v5 research_inputs/registry_v5 -maxdepth 2 -type f -not -path '*/sources/*' | sort) | head -60
