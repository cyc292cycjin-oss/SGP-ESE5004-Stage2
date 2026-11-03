#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
du -sm $R/builds_op $R/path_check6 $R/smoke_s5 $R/dry_screen5 $R/pkg_check5 $R/s5_status | awk '{print $1, $2; s+=$1} END {print s, "MB"}'
/home/jin/miniforge3/envs/pypsa-earth/bin/python - <<'P'
import json
d = json.load(open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/dry_screen5/DRY_RUN_SCREEN.json")); print(d["passed"], d["code_commit"][:8], {k: (v["lp"]["num_row"], v["lp"]["num_col"], v["passed"], round(v["peak_rss_gib"], 2)) for k, v in d["build_check"].items()})
m = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_op/PACKAGE_MANIFEST.json")); print(m["upload"]["hours_at"], len(m["files"]), m["upload_total_bytes_excluding_this_manifest"], m["commit"][:8], m["sha256sums_sha256"])
for r in m["files"]:
    if r["path"].endswith(".nc") or r["path"].startswith("code_"): print(r["path"], r["bytes"], r["sha256"][:8])
P
cp $R/dry_screen5/DRY_RUN_SCREEN.json /home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/DRY_RUN_SCREEN.json
sha256sum /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_op/PACKAGE_MANIFEST.json /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_op/SHA256SUMS | cut -c1-110
grep -E "PREFLIGHT|leak scan|licence files|build inputs|dry run:|manifest:" /home/jin/v3/out_pkg5.txt | cut -c1-150
/home/jin/miniforge3/envs/pypsa-earth/bin/python - <<'P'
import json
d = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_op/BUILD_INPUT_CHANGES.json")); print("BUILD_INPUT", d["build_commit"][:8], d["head"][:8], "changed", len(d["changed"]), "refused", d["refused"])
e = json.load(open("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/SOURCE_BALANCE_OP_SMOKE.json")); print(max(v["max_abs_residual_mw"] for s in e.values() for v in s.values()), max(v["plant_above_stock_max_mw"] for s in e.values() for v in s.values()), sum(v["new_units_on_bus"] for s in e.values() for v in s.values()))
P
head -1 /home/jin/v3/out_tests5.txt; grep -E "passed|failed" /home/jin/v3/out_tests5.txt | tail -5 | cut -c1-170
