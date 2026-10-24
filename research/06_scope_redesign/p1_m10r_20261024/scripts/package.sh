#!/bin/bash
# M10R B4.2: package v6 from the committed HEAD (make_package.sh: no cloud, no solve); v5 kept as cloud_package_dist_v5_e0a89f8e; the registered inputs compared with v5.
set -u
WT=/home/jin/wt_m10p_20261022; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10r_20261024/evidence
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
export DRILL_JSON=${DRILL_JSON:-$MAIN/m10r/drill/DRILL_POSTPROC.json}
mkdir -p $E/package_v6
cd $WT || exit 1
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed"; exit 1; }
HEAD=$(git rev-parse HEAD); echo "HEAD $HEAD"
if [ -d $W/cloud_package_dist ] && [ ! -d $W/cloud_package_dist_v5_e0a89f8e ]; then
  [ "$(cat $W/cloud_package_dist/COMMIT)" = e0a89f8e7abe7e91132135b241766464890283cb ] || { echo "cloud_package_dist is not v5"; exit 1; }
  mv $W/cloud_package_dist $W/cloud_package_dist_v5_e0a89f8e && echo "v5 kept as cloud_package_dist_v5_e0a89f8e"
fi
[ -d $W/cloud_package_dist_v5_e0a89f8e ] || { echo "v5 copy missing"; exit 1; }
[ -e $MAIN/m10p/package_variants_v6 ] && { echo "work dir exists"; exit 1; }
t0=$(date +%s)
bash research/06_scope_redesign/p1_m10p_20261022/cloud_package/make_package.sh $MAIN/m08b/builds_s01 $W/cloud_package_dist $MAIN/m10p/package_variants_v6 > $E/package_v6/MAKE_PACKAGE.log 2>&1
echo "MAKE_PACKAGE_EXIT $? $(( $(date +%s) - t0 ))s" | tee -a $E/package_v6/MAKE_PACKAGE.log
cat $E/package_v6/MAKE_PACKAGE.log
D=$W/cloud_package_dist; V5=$W/cloud_package_dist_v5_e0a89f8e
[ -f $D/PACKAGE_MANIFEST.json ] || { echo "no package"; exit 1; }
cp $D/PACKAGE_MANIFEST.json $D/SHA256SUMS $D/VARIANT_REPRODUCIBILITY.json $D/EXPECTED_VARIANTS.json $D/BUILD_INPUT_CHANGES.json $D/COMMIT $E/package_v6/
$PY - $D $V5 $E/package_v6/PACKAGE_V6_VS_V5.json <<'P'
import hashlib, json, os, sys
from pathlib import Path
d, v5, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
must = ["networks/integrated_365_24h_unsolved.nc", "networks/disconnected_365_24h_unsolved.nc", "networks/integrated_BUILD_RECEIPT.json", "networks/disconnected_BUILD_RECEIPT.json",
        "networks/integrated_costs_active_research.csv", "networks/disconnected_costs_active_research.csv", "EXPECTED_VARIANTS.json"]
same = {f: dict(v6=sha(d / f), v5=sha(v5 / f), equal=sha(d / f) == sha(v5 / f)) for f in must}
files = sorted(p for p in d.rglob("*") if p.is_file())
m6 = json.loads((d / "PACKAGE_MANIFEST.json").read_text()); m5 = json.loads((v5 / "PACKAGE_MANIFEST.json").read_text())
s6 = {r["path"]: r["sha256"] for r in m6["files"]}; s5 = {r["path"]: r["sha256"] for r in m5["files"]}
changed = sorted(p for p in set(s6) | set(s5) if s6.get(p) != s5.get(p))
res = dict(v6_commit=m6["commit"], v5_commit=m5["commit"], v6_files=len(files), v6_bytes=sum(p.stat().st_size for p in files), v6_manifest_sha256=sha(d / "PACKAGE_MANIFEST.json"),
           v6_sha256sums_sha256=sha(d / "SHA256SUMS"), fixed_files_identical_to_v5=all(v["equal"] for v in same.values()), fixed_files=same, files_changed_vs_v5=changed,
           v5_files=len(m5["files"]) + 1, v5_bytes=m5["upload_total_bytes_excluding_this_manifest"] + os.path.getsize(v5 / "PACKAGE_MANIFEST.json"), drill=m6.get("drill"))
out.write_text(json.dumps(res, indent=1))
print(json.dumps({k: res[k] for k in ("v6_commit", "v6_files", "v6_bytes", "v6_manifest_sha256", "v6_sha256sums_sha256", "fixed_files_identical_to_v5", "files_changed_vs_v5")}, indent=1))
P
echo PACKAGE_DONE
