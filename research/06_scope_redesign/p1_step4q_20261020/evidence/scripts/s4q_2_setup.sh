#!/bin/bash
# S4Q-2 setup (no solver, no licence content read): local package-like folder for the S4O run pipeline - repo = git archive of the S4Q commit,
# networks = symlinks to the S4M-1 2920x3h builds used by S4M-2 (SHA256 checked against the S4M-2 receipts), build cost tables; preflight
# sections profile (both candidates), c1, versions, tools.
set -u
W=/home/jin/wt_s4q_20261020; RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=$RM/results_project/s4m/s4m1/builds; S=$RM/results_project/s4m/s4m2/solves; P=/home/jin/s4q_local/pkg
cd $W
[ "$(git status --porcelain --untracked-files=no scripts_project configs research/06_scope_redesign/p1_step4o_20261019/cloud_package | wc -l)" = 0 ] || { echo "REFUSED: dirty tree"; exit 2; }
[ ! -e $P ] || { echo "REFUSED: $P exists"; exit 2; }
mkdir -p $P/repo $P/networks
git archive HEAD | tar x -C $P/repo; git rev-parse HEAD > $P/COMMIT; cp $P/COMMIT $P/repo/.package_commit
cp research/06_scope_redesign/p1_step4o_20261019/cloud_package/run_365x24h.sh research/06_scope_redesign/p1_step4o_20261019/cloud_package/preflight.sh $P/
echo "COMMIT $(cat $P/COMMIT)"
for spec in integrated:integrated/integrated_2920_3h_unsolved.nc:s4m_A_integrated disconnected:disconnected/disconnected_2920_3h_unsolved.nc:s4m_A_disconnected integrated_nze:integrated_nze/integrated_2920_3h_unsolved.nc:s4m_A_integrated_nze; do
  IFS=: read tag rel ref <<< "$spec"
  ln -s $B/$rel $P/networks/${tag}_365_24h_unsolved.nc
  cp $B/$(dirname $rel)/costs_active_research.csv $P/networks/${tag}_costs_active_research.csv
  h=$(sha256sum $B/$rel | cut -d' ' -f1)
  r=$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['input_network']['sha256'])" $S/$ref/SOLVE_RECEIPT.json)
  echo "NETWORK $tag $h S4M-2 $r same=$([ "$h" = "$r" ] && echo True || echo False) costs_sha=$(sha256sum $P/networks/${tag}_costs_active_research.csv | cut -c1-16)"
done
cd $P
for prof in formal_barrier_1e6 formal_barrier_1e6_t16; do
  ( PREFLIGHT_ONLY=profile,c1,versions,tools PY=$PY bash preflight.sh serial $prof ) 2>&1 | grep -viE "licen[cs]e|wls|registered" | tail -14
done
echo "licence file readable (content not read): $([ -r /home/jin/gurobi.lic ] && echo yes || echo no)"
echo "solver processes: $(ps -eo cmd | grep -cE '[s]2_solve.py|[g]urobi_cl')"; uptime; free -g | head -2; nproc
