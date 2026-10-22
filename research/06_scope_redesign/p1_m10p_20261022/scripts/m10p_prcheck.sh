#!/bin/bash
# M10P-1: every commit of the PRs #45 (M08a), #47 (M08b), #46 (M12), #48 (M12b) and #41 (S4Q, FIXED_RUNS) is an ancestor of the integration branch head
set -u
WT=/home/jin/wt_m10p_20261022; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/evidence
cd $WT; H=$(git rev-parse HEAD)
/home/jin/miniforge3/envs/pypsa-earth/bin/python - "$E" "$H" <<'P'
import json, subprocess, sys
from pathlib import Path
E, H = Path(sys.argv[1]), sys.argv[2]
names = {45: "M08a", 46: "M12", 47: "M08b", 48: "M12b", 41: "S4Q (FIXED_RUNS, 1e-6 profiles)"}
res = dict(branch="codex/m10-batch3-20261022", head=H, prs={})
for n in (45, 47, 46, 48, 41):
    pr = json.loads((E / f"pr_{n}.json").read_text())
    missing = [c for c in pr["commits"] if subprocess.run(["git", "merge-base", "--is-ancestor", c, H]).returncode != 0]
    head_in = subprocess.run(["git", "merge-base", "--is-ancestor", pr["headRefOid"], H]).returncode == 0
    res["prs"][str(n)] = dict(name=names[n], head_ref=pr["headRefName"], head_oid=pr["headRefOid"], base_ref=pr["baseRefName"], commits=len(pr["commits"]), missing=missing, head_in_branch=head_in)
# S4Q FIXED_RUNS code commit and the switch in the run script
fx = subprocess.run(["git", "merge-base", "--is-ancestor", "84532e78", H]).returncode == 0
grep = subprocess.run(["git", "grep", "-c", "FIXED_RUNS", H, "--", "research/06_scope_redesign/p1_step4o_20261019/cloud_package/run_365x24h.sh"], capture_output=True, text=True).stdout.strip()
res["s4q_fixed_runs"] = dict(code_commit="84532e78", in_branch=fx, run_365x24h_sh_mentions=grep)
res["merges_needed"] = [n for n, v in res["prs"].items() if v["missing"] or not v["head_in_branch"]] + ([] if fx else ["S4Q 84532e78"])
(E / "M10P_PR_COMMIT_CHECK.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps({k: (v["commits"], len(v["missing"]), v["head_in_branch"]) for k, v in res["prs"].items()}), res["s4q_fixed_runs"], "merges_needed:", res["merges_needed"])
P
