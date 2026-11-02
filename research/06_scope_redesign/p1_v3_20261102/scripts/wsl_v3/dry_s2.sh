#!/bin/bash
# V3 supplement 02 item 2.4.2: dry run of the 365x24h runner with the five-run definition on the real networks in a package-like folder (symlinks), no solver, no licence, registered SHA256 enforced; refusals checked. Writes DRY_RUN_SCREEN.json.
set -u
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=$MAIN/results_project/v3/builds_x1b; O=$MAIN/results_project/v3/dry_screen; D=$W/research/06_scope_redesign; A=$O/pkg
[ ! -e $O ] || { echo "REFUSED: $O exists"; exit 2; }
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[p]ytest')" = 0 ] || { echo "REFUSED: another solve or pytest is running"; exit 2; }
[ "$(git -C $W status --porcelain --untracked-files=no | wc -l)" = 0 ] || { echo "REFUSED: tracked changes"; exit 2; }
mkdir -p $A/networks; N=$A/networks
ln -s $B/integrated/integrated_365_24h_unsolved.nc $B/integrated/integrated_BUILD_RECEIPT.json $B/no_new_xb/no_new_xb_365_24h_unsolved.nc $B/no_new_xb/no_new_xb_365_24h_VARIANT_RECEIPT.json $B/disconnected/disconnected_365_24h_unsolved.nc $B/disconnected/disconnected_BUILD_RECEIPT.json $N/
for b in bridge_160_162 bridge_160_164; do ln -s $B/$b/integrated_365_24h_unsolved.nc $N/${b}_365_24h_unsolved.nc; ln -s $B/$b/integrated_BUILD_RECEIPT.json $N/${b}_BUILD_RECEIPT.json; done
ln -s $B/integrated/costs_active_research.csv $N/integrated_costs_active_research.csv; ln -s $B/disconnected/costs_active_research.csv $N/disconnected_costs_active_research.csv
cp $D/p1_v3_20261102/batch_def/BATCH_DEF_365x24h.json $A/BATCH_DEF.json; cp $D/p1_m10p_20261022/cloud_package/pack_results.sh $D/p1_dfx_20261026/cloud_package_dfx/run_dfx.sh $D/p1_dfx_20261026/cloud_package_dfx/preflight_dfx.sh $A/; ln -s $W $A/repo
env -u GRB_LICENSE_FILE PY=$PY BUILD_ONLY=1 RUN_DIR=$A/out bash $A/run_dfx.sh > $A/run.log 2>&1
RC=$?
echo "BUILD_ONLY exit=$RC"; grep -E "BASE_CHECK|BUILD_CHECK|STOP|SAFE|DONE|PHASE" $A/out/STATUS.txt | cut -c1-210 | tail -14
R1=$(env -u GRB_LICENSE_FILE PY=$PY BUILD_ONLY=1 RUN_DIR=$A/refuse1 bash $A/run_dfx.sh --auth x 2>&1 | tail -1 | cut -c1-90); R2=$(env -u GRB_LICENSE_FILE PY=$PY TRUNCATE=56 RUN_DIR=$A/refuse2 bash $A/run_dfx.sh --auth x 2>&1 | tail -1 | cut -c1-90)
echo "refusal1: $R1"; echo "refusal2: $R2"
$PY - "$A/out" "$(git -C $W rev-parse HEAD)" "$O/DRY_RUN_SCREEN.json" "$RC" "$R1" "$R2" <<'P'
import json, sys, time
from pathlib import Path
o, c, f, rc, r1, r2 = sys.argv[1:7]; o = Path(o); b = {}
for r in ("V1", "V2", "V3", "V4", "V5"):
    p = o / r / "BUILD_CHECK.json"; b[r] = json.loads(p.read_text()) if p.exists() else None
ok = rc == "0" and all(v and v.get("passed") for v in b.values()) and "REFUSED" in r1 and "REFUSED" in r2
json.dump(dict(code_commit=c, passed=bool(ok), written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), build_check={k: dict(passed=v.get("passed"), lp=v.get("lp"), peak_rss_gib=v.get("peak_rss_gib")) if v else None for k, v in b.items()}, refusals=[r1, r2]), open(f, "w"), indent=1, default=str)
print("passed", ok, {k: (v or {}).get("lp") for k, v in b.items()})
P
echo FINISHED
