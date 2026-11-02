#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
du -sm $R/builds_oneway $R/path_check4 $R/smoke_s3 $R/dry_screen3 $R/pkg_check3 | awk '{s+=$1} END {print s, "MB"}'
/home/jin/miniforge3/envs/pypsa-earth/bin/python - <<'P'
import json
d = json.load(open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/dry_screen3/DRY_RUN_SCREEN.json")); print(d["passed"], d["code_commit"][:8], {k: (v["lp"]["num_row"], v["passed"], round(v["peak_rss_gib"], 2)) for k, v in d["build_check"].items()})
m = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_oneway/PACKAGE_MANIFEST.json")); print(m["upload"]["hours_at"], len(m["files"]))
for r in m["files"]:
    if r["path"].endswith(".nc") or r["path"].startswith("code_"): print(r["path"], r["bytes"], r["sha256"][:8])
P
cp $R/dry_screen3/DRY_RUN_SCREEN.json /home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/DRY_RUN_SCREEN.json
