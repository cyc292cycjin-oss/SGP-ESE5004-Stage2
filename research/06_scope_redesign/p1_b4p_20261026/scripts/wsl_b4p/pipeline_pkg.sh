#!/bin/bash
# B4P A5.3 / A5.4: package v7 at the current HEAD (DRILL_JSON of that commit required), then the local dry run (pre, build, real, synth, guards)
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/evidence; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026; R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
ST=$E/PIPELINE_PKG.txt; mkdir -p "$E/package" "$E/dryrun"
log() { echo "$1:$(date -u +%FT%TZ)${2:+:$2}" >> "$ST"; }
log START
cd /home/jin/wt_b4p_20261026 || exit 1
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py')" = 0 ] || { log ABORT "solve / stand-in process running"; exit 3; }
t0=$(date +%s)
DIST=$W/cloud_package_dist_b4
[ -e "$DIST" ] && { log ABORT "dist exists: $DIST"; exit 2; }
DRILL_JSON=$R/b4p/drill/DRILL_B4.json PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python bash research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/make_package.sh "$R/m08b/builds_s01" "$DIST" > "$E/package/make_package.log" 2>&1; rc=$?
log PACKAGE "exit=$rc:$(( $(date +%s) - t0 ))s:$(tail -3 "$E/package/make_package.log" | tr '\n' ' ' | cut -c1-300)"
[ $rc = 0 ] || exit 1
/home/jin/miniforge3/envs/pypsa-earth/bin/python - "$DIST" "$E/package/PACKAGE_SUMMARY.json" <<'P'
import hashlib, json, os, sys
d, out = sys.argv[1], sys.argv[2]
m = json.load(open(os.path.join(d, "PACKAGE_MANIFEST.json")))
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
res = dict(dist=d, commit=m["commit"], files=len(m["files"]), bytes=m["upload_total_bytes_excluding_this_manifest"], manifest_sha256=h(os.path.join(d, "PACKAGE_MANIFEST.json")), sha256sums_sha256=m["sha256sums_sha256"],
           networks=m["networks"]["files"], registered=m["networks"]["registered"], networks_equal_registered=(m["networks"]["files"] == {f"networks/{k}": v for k, v in m["networks"]["registered"].items()}),
           no_365x24h=not any("365_24h" in r["path"] for r in m["files"]), drill=m.get("drill"), code_archive=m["code_archive"]["file"], upload_hours=m["upload"]["hours_at"])
json.dump(res, open(out, "w"), indent=1); print(json.dumps({k: res[k] for k in ("commit", "files", "bytes", "networks_equal_registered", "no_365x24h")}))
P
echo "$(( $(date +%s) - t0 )) package" > "$E/package/TIME.txt"
for step in pre build real synth guards; do
  t1=$(date +%s); STEP=$step DIST=$DIST bash /home/jin/b4p/dryrun_b4.sh > "$E/dryrun/$step.out" 2>&1; log "DRY_$step" "exit=$?:$(( $(date +%s) - t1 ))s:$(tail -1 "$E/dryrun/$step.out" | cut -c1-300)"
done
/home/jin/miniforge3/envs/pypsa-earth/bin/python - "$E/dryrun" <<'P'
import json, re, sys
from pathlib import Path
e = Path(sys.argv[1]); res = {}
for f in ("PREFLIGHT_GUARDS.txt", "PREFLIGHT_GUARDS_NEG.txt", "PREFLIGHT.txt", "PREFLIGHT_RESOURCES_LOCAL.txt", "GUARDS_REFUSAL.txt"):
    p = e / f; t = p.read_text(errors="ignore") if p.exists() else ""
    res[f] = dict(exit_lines=[l for l in t.splitlines() if "EXIT" in l], ok="PREFLIGHT OK" in t, failed="PREFLIGHT FAILED" in t, refused=t.count("REFUSED"))
for d in ("build_only", "dry_real", "dry_synth"):
    st = e / d / "STATUS.txt"; t = st.read_text() if st.exists() else ""
    res[d] = dict(status_lines=len(t.splitlines()), done="DONE:" in t, halted="HALTED:" in t, stop_safe=[l for l in t.splitlines() if l.startswith("STOP_SAFE")], runs={r: [l[:160] for l in t.splitlines() if l.startswith(("RUN_" + r, "BUILD_" + r, "GUROBI_" + r, "ASSIGN_" + r, "V6_" + r, "UNUSABLE:" + r, "BUILD_CHECK_" + r))] for r in ("F1", "F2")},
                  p1=[l[:200] for l in t.splitlines() if l.startswith("P1_PROBE")], projection=[l[:160] for l in t.splitlines() if l.startswith("PROJECTION")], summary=[l[:200] for l in t.splitlines() if l.startswith("SUMMARY")], packs=[l[:200] for l in t.splitlines() if l.startswith("PACK_")])
    for r in ("F1", "F2"):
        bc = e / d / r / "BUILD_CHECK.json"
        if bc.exists():
            b = json.loads(bc.read_text()); res[d].setdefault("build_check", {})[r] = dict(passed=b.get("passed"), state=b.get("receipt_state"), lp=b.get("lp"), peak_gib=round(b.get("peak_rss_gib") or 0, 2))
    for r in ("F1", "F2"):
        acc = e / d / r / "V6_ACCEPTANCE.json"
        if acc.exists():
            res[d].setdefault("labels", {})[r] = json.loads(acc.read_text()).get("label")
json.dump(res, open(e / "DRYRUN_SUMMARY.json", "w"), indent=1); print(json.dumps({k: (v.get("done"), v.get("halted")) for k, v in res.items() if isinstance(v, dict) and "done" in v}))
P
log DONE
