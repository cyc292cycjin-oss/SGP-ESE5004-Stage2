#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
cd $W; $PY /home/jin/v3/eval_patch.py || exit 1
$PY - <<'P'
import json
O = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/dry_runners"
for k, f in (("hpc_registered", "hpc/BASE_CHECK_REGISTERED.json"),):
    d = json.load(open(f"{O}/{f}")); print(k, d["all_equal"], d["registered_checked"], {n: (v["receipt_equal"], v["registered_equal"]) for n, v in d["networks"].items()})
for lane, rids in (("autodl", ("V1", "V2")), ("hpc", ("F1", "F2"))):
    for r in rids:
        for n in ("BUILD_CHECK.json",):
            try:
                c = json.load(open(f"{O}/{lane}/out/{r}/{n}")); print(lane, r, "passed", c.get("passed"), "failed", [k for k, v in c.get("checks", {}).items() if not v], c.get("lp"))
            except Exception as e:
                print(lane, r, n, "absent", str(e)[:60])
P
env -u GRB_LICENSE_FILE timeout -k 30 540 $PY -m pytest tests/research/test_v3.py tests/research/test_v3_runners.py tests/research/test_m08a_a8.py tests/research/test_dfx_demand.py -q --no-header -p no:cacheprovider --tb=short -W ignore 2>&1 | tail -6 | cut -c1-190
git status --short scripts_project configs tests | cut -c1-80
