#!/bin/bash
# M10A B5.8: package v4 from the committed HEAD (make_package.sh: no cloud, no solve); v3 kept as cloud_package_dist_v3_e0527cec; fixed files compared with v3
set -u
WT=/home/jin/wt_m10p_20261022; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10a_20261022/evidence
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
mkdir -p $E/package_v4
cd $WT || exit 1
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed"; exit 1; }
HEAD=$(git rev-parse HEAD); echo "HEAD $HEAD"
if [ -d $W/cloud_package_dist ] && [ ! -d $W/cloud_package_dist_v3_e0527cec ]; then
  [ "$(cat $W/cloud_package_dist/COMMIT)" = e0527cecd8ccc798b3b3e8f54363d76ced417592 ] || { echo "cloud_package_dist is not v3"; exit 1; }
  mv $W/cloud_package_dist $W/cloud_package_dist_v3_e0527cec && echo "v3 kept as cloud_package_dist_v3_e0527cec"
fi
[ -d $W/cloud_package_dist_v3_e0527cec ] || { echo "v3 copy missing"; exit 1; }
[ -e $MAIN/m10p/package_variants_v4 ] && { echo "work dir exists"; exit 1; }
t0=$(date +%s)
bash research/06_scope_redesign/p1_m10p_20261022/cloud_package/make_package.sh $MAIN/m08b/builds_s01 $W/cloud_package_dist $MAIN/m10p/package_variants_v4 > $E/package_v4/MAKE_PACKAGE.log 2>&1
echo "MAKE_PACKAGE_EXIT $? $(( $(date +%s) - t0 ))s" | tee -a $E/package_v4/MAKE_PACKAGE.log
cat $E/package_v4/MAKE_PACKAGE.log
D=$W/cloud_package_dist; V3=$W/cloud_package_dist_v3_e0527cec
cp $D/PACKAGE_MANIFEST.json $D/SHA256SUMS $D/VARIANT_REPRODUCIBILITY.json $D/EXPECTED_VARIANTS.json $D/BUILD_INPUT_CHANGES.json $D/COMMIT $E/package_v4/
$PY - $D $V3 $E/package_v4/PACKAGE_V4_VS_V3.json <<'P'
import hashlib, json, os, sys
from pathlib import Path
d, v3, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
must = ["networks/integrated_365_24h_unsolved.nc", "networks/disconnected_365_24h_unsolved.nc", "networks/integrated_BUILD_RECEIPT.json", "networks/disconnected_BUILD_RECEIPT.json",
        "networks/integrated_costs_active_research.csv", "networks/disconnected_costs_active_research.csv", "EXPECTED_VARIANTS.json"]
same = {f: dict(v4=sha(d / f), v3=sha(v3 / f), equal=sha(d / f) == sha(v3 / f)) for f in must}
files = sorted(p for p in d.rglob("*") if p.is_file())
m4 = json.loads((d / "PACKAGE_MANIFEST.json").read_text()); m3 = json.loads((v3 / "PACKAGE_MANIFEST.json").read_text())
s4 = {r["path"]: r["sha256"] for r in m4["files"]}; s3 = {r["path"]: r["sha256"] for r in m3["files"]}
changed = sorted(p for p in set(s4) | set(s3) if s4.get(p) != s3.get(p))
res = dict(v4_commit=m4["commit"], v3_commit=m3["commit"], v4_files=len(files), v4_bytes=sum(p.stat().st_size for p in files), v4_manifest_sha256=sha(d / "PACKAGE_MANIFEST.json"),
           v4_sha256sums_sha256=sha(d / "SHA256SUMS"), fixed_files_identical_to_v3=all(v["equal"] for v in same.values()), fixed_files=same, files_changed_vs_v3=changed,
           v3_files=len(m3["files"]) + 1, v3_bytes=m3["upload_total_bytes_excluding_this_manifest"] + os.path.getsize(v3 / "PACKAGE_MANIFEST.json"))
out.write_text(json.dumps(res, indent=1))
print(json.dumps({k: res[k] for k in ("v4_commit", "v4_files", "v4_bytes", "v4_manifest_sha256", "fixed_files_identical_to_v3", "files_changed_vs_v3")}, indent=1))
P
echo PACKAGE_DONE
