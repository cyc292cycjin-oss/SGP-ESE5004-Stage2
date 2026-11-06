cd /home/jin/wt_v4_fable || exit 1
echo "== code/input changes after the build commit 17a15c22 =="; git diff --stat 17a15c22 7aa356e4 -- scripts_project configs research_inputs tests | tail -5
echo "== per-commit stat (code/inputs only) =="; for c in c2ffe7a0 37e8a7a6 6590d3e4 c9cedcef 54b47a28 676d1383 aba72721 17a15c22 a0507578 bd890bf9 7aa356e4; do echo "-- $c"; git show --stat --format="%h %s" $c -- scripts_project configs research_inputs tests | tail -n +2 | tail -3; done
echo "== v3.1 package network receipt commit =="; python3 -c "
import json; r=json.load(open('/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/integrated_BUILD_RECEIPT.json')); print({k:(str(v)[:120]) for k,v in r.items() if k in ('commit','git_commit','code_commit','repo_commit','network','built_utc','generated_utc')}); print([k for k in r.keys()][:40])"
ls -la /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/ | head
echo "== s3_layers 95-125 =="; sed -n 95,125p scripts_project/s3_layers.py
echo "== HEAT_BAND_ACCOUNT =="; grep -n "HEAT_BAND_ACCOUNT\s*=" -A 3 scripts_project/s2_layers.py | head -8
grep -n "HEAT_BAND_BUS\s*=" -A 4 scripts_project/s2_layers.py | head -8
echo "== meter_load / plain_load accounts for industry fuels =="; grep -n "meter_load(node, c, \"industry\|plain_load(node, c, \"Industry\"" scripts_project/s2_layers.py | cut -c1-200
