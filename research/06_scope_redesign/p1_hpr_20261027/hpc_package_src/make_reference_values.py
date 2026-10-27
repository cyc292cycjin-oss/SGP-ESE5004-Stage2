"""HPR (RUN_PLAN_HPC 7.4): REFERENCE_VALUES.json for the batch-level comparison of F1 / F2 (2920x3h v2) with (a) the third batch's 365x24h v1 runs
R3 / R4 (main; same profile, optimal) and R1 / R2 (alternative), (b) the DFX v2 365x24h screening V1 / V2. NUMBERS ONLY (objective, Owen dual-form
alpha-main shares, B6, labels, termination, profile) copied from the committed DFX files BATCH3_REFERENCE_VALUES.json and
evidence/phase4/DFX_PHASE4_RESULTS.json - no result file, no path, no authorisation text, no host enters the package.

    python hpc/make_reference_values.py <BATCH3_REFERENCE_VALUES.json> <DFX_PHASE4_RESULTS.json> <out REFERENCE_VALUES.json>
"""
import hashlib
import json
import sys
import time
from pathlib import Path

b3f, dfxf, out = (Path(p) for p in sys.argv[1:4])
b3 = json.loads(b3f.read_text())["batch3"]; dfx = json.loads(dfxf.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def b3_run(rid):
    return dict(rid=rid, objective_eur=b3["objective_eur"][rid], termination=b3["termination"][rid], label=b3["labels"][rid], profile=b3["profile"][rid], owen_alpha_main_eur=b3["owen_alpha_main_eur"][rid])


def dfx_run(rid):
    r = dfx["runs"][rid]
    return dict(rid=rid, objective_eur=r["objective_eur"], termination=r["termination"], label=r["v6"], profile="formal_barrier_1e6_t16", owen_alpha_main_eur=r["owen_alpha_main_eur"], barrier_iterations=r.get("barrier_iterations"))


res = dict(source="HPR make_reference_values.py: third batch (M10P 2026-10-23; BATCH3_REFERENCE_VALUES.json of the DFX package) and DFX phase 4 (cloud 365x24h v2 screening, 2026-10-27; DFX_PHASE4_RESULTS.json) - values only",
           written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), inputs={str(b3f.name): sha(b3f), str(dfxf.name): sha(dfxf)},
           references=dict(batch3_main=dict(label="第三批 365×24h v1，R3 / R4（同档案 formal_barrier_1e6_t16，optimal；主参照）", integrated=b3_run("R3"), disconnected=b3_run("R4"), b6_bn=b3["b6_bn"], resolution="365x24h", demand="v1"),
                           batch3_alternative=dict(label="第三批 365×24h v1，R1 / R2（档案 formal_barrier，suboptimal；并列）", integrated=b3_run("R1"), disconnected=b3_run("R2"), b6_bn=b3["b6_alternative_bn"], resolution="365x24h", demand="v1"),
                           dfx_v2_365x24h=dict(label="DFX 阶段 4 365×24h v2，V1 / V2（同档案，optimal）", integrated=dfx_run("V1"), disconnected=dfx_run("V2"), b6_bn=dfx["b6"]["bn_eur"], resolution="365x24h", demand="v2")),
           note="description only (RUN_PLAN_HPC 7.4): resolution (2920x3h vs 365x24h) and demand version (v2 vs v1) effects; never an acceptance criterion")
out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
print(json.dumps({k: dict(runs=(v["integrated"]["rid"], v["disconnected"]["rid"]), b6_bn=v["b6_bn"]) for k, v in res["references"].items()}, ensure_ascii=False))
