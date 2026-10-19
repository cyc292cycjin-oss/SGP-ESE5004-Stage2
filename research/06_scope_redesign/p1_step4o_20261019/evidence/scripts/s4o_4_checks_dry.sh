#!/bin/bash
# S4O-4 preparation (read only): build commits of the four S4M-1 networks and the build-input classification against HEAD
set -u
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
export PATH=/home/jin/miniforge3/envs/pypsa-earth/bin:$PATH
for sc in integrated disconnected integrated_nze disconnected_gap; do
  rec=$(ls results_project/s4m/s4m3/builds/$sc/*_BUILD_RECEIPT.json | head -1)
  echo "$sc $(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['code_sha'])" $rec)"
done
b=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['code_sha'])" results_project/s4m/s4m3/builds/integrated/integrated_BUILD_RECEIPT.json)
python3 research/06_scope_redesign/p1_step4o_20261019/cloud_package/package_checks.py build-inputs $b $(git rev-parse HEAD); echo "exit $?"
