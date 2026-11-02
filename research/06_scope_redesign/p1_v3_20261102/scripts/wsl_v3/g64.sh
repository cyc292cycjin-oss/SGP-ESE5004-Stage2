#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
du -sm $R/builds_bound $R/path_check5 $R/smoke_s4 $R/dry_screen4 $R/pkg_check4 | awk '{print $1, $2; s+=$1} END {print s, "MB"}'
/home/jin/miniforge3/envs/pypsa-earth/bin/python - <<'P'
import json
d = json.load(open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/dry_screen4/DRY_RUN_SCREEN.json")); print(d["passed"], d["code_commit"][:8], {k: (v["lp"]["num_row"], v["lp"]["num_col"], v["passed"], round(v["peak_rss_gib"], 2)) for k, v in d["build_check"].items()})
m = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_bound/PACKAGE_MANIFEST.json")); print(m["upload"]["hours_at"], len(m["files"]), m["upload_total_bytes_excluding_this_manifest"], m["commit"][:8], m["sha256sums_sha256"])
for r in m["files"]:
    if r["path"].endswith(".nc") or r["path"].startswith("code_"): print(r["path"], r["bytes"], r["sha256"][:8])
P
cp $R/dry_screen4/DRY_RUN_SCREEN.json /home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/DRY_RUN_SCREEN.json
sha256sum /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_bound/PACKAGE_MANIFEST.json /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_bound/SHA256SUMS | cut -c1-110
grep -E "guards|sha|networks|env|profile|code|tools|PASS|FAIL|OK" /home/jin/v3/out_pkg4.txt | tail -16 | cut -c1-180
grep -E "failed|passed" /home/jin/v3/out_tests4.txt | tail -6 | cut -c1-170
