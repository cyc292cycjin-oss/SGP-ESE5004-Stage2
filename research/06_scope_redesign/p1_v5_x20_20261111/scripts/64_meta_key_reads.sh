#!/bin/bash
# X20 ④1：过期顶层 meta 键在代码中的读取点（switch-all-read-points 教训）。只读。
cd /home/jin/wt_v5_x20/scripts_project
for k in interim_notice skeleton_status stage asset_role scientific_results_allowed fullsc_network_complete input_coverage_complete source_is_solved asset_qualification resource_occupancy_status policy_constraint_qualification; do
  echo "== $k"
  grep -rn --include=*.py -E "[\"']$k[\"']" . | grep -v -E "^\./v5_layers|^\./v5_common" | grep -E "meta|get\(" | grep -v -E "[\"']$k[\"'] *\] *= |$k=" | cut -c1-200 | head -8
done
