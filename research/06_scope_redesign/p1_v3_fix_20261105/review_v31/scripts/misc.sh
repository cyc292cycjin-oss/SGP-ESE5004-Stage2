#!/bin/bash
cd /home/jin/wt_v31_review || exit 1
echo "=== commit times ==="; for c in ae849e1e 64aea2e3 13ebce95 d3b9a3bc 7faefbe5 1117a07f; do git log -1 --format="%h %cI %s" $c | cut -c1-110; done
echo "=== code tar: suspicious files ==="
PK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1
tar tzf $PK/code_d3b9a3bc.tar.gz | grep -i -E "\.lic$|gurobi\.lic|known_hosts|id_rsa|id_ed25519|\.pem$|\.key$|\.env$|secret|credential|results_project/|\.nc$" | head -20; echo "(end suspicious; total entries: $(tar tzf $PK/code_d3b9a3bc.tar.gz | wc -l))"
echo "=== tar top-level dirs ==="; tar tzf $PK/code_d3b9a3bc.tar.gz | cut -d/ -f1 | sort | uniq -c | sort -rn | head -15
echo "=== package hpc scripts: RUNDIRS and price csv ==="
grep -n -c "RUNDIRS" $PK/hpc/hpr_job.sh $PK/hpc/hpr_submit.sh $PK/hpc/hpr_status.sh
grep -n -E "NODAL_PRICES|nodal_prices" $PK/hpc/*.sh $PK/pack_results.sh $PK/run_batch4.sh | head
echo "=== zero_slack_check.py port classification ==="
grep -n -E "def |removal|two_way|inflow|p_nom|usable|capacity" scripts_project/zero_slack_check.py | head -60
