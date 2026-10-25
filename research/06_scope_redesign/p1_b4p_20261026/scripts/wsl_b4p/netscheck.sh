#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project; N=$R/b4p/nets_check
rm -rf "$N"; mkdir -p "$N"; cd "$N" || exit 1
for sc in integrated disconnected; do ln -s "$R/m08b/builds_s01/$sc/${sc}_2920_3h_unsolved.nc" .; ln -s "$R/m08b/builds_s01/$sc/${sc}_BUILD_RECEIPT.json" .; done
ls -la "$N"
cd /home/jin/wt_b4p_20261026 && env -u GRB_LICENSE_FILE /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts_project/b4_batch4.py base-check --nets "$N" --out "$N/BASE_CHECK.json"; echo "exit $?"
echo "=== differences C1 vs smoke"
/home/jin/miniforge3/envs/pypsa-earth/bin/python - <<'EOF'
import json
r = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/evidence/compare/C1_newcode_vs_M08b_smoke.json"))
for k in ("gurobi_log", "V5_GATES.json", "LEDGER_IDENTITY.json", "EXPORTS.json"):
    v = r["items"][k]; print("##", k, v.get("status"), "bytes_equal", v.get("bytes_equal"))
    for d in (v.get("differences") if isinstance(v.get("differences"), list) else v.get("examples") or [])[:12]:
        print("   ", str(d)[:230])
EOF
