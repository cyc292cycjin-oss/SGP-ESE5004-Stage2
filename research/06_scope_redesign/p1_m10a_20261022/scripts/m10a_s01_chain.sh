#!/bin/bash
# M10A supplement 01 D4 chain: commit (D1-D3) -> package v5 (v4 kept) -> dry run pre -> BUILD_ONLY -> POST_ONLY -> build comparison with the M10P second dry run
set -u
WT=/home/jin/wt_m10p_20261022; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022; EA=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10a_20261022/evidence
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
mkdir -p $EA/tests $EA/s01 $EA/package_v5; cp /home/jin/m10a_evidence/TESTS_s01_*.log /home/jin/m10a_evidence/S01_REFERENCES.txt $EA/s01/ 2>/dev/null
echo "===== commit (D1-D3) ====="
bash /home/jin/m10a_commit.sh /home/jin/m10a_s01_msg1.txt research/06_scope_redesign/p1_m10p_20261022/RUN_PLAN.md research/06_scope_redesign/p1_m10p_20261022/cloud_package tests/research/fixtures/m10p_fake_pipeline.py tests/research/test_m10p_batch3.py || { echo "COMMIT_FAILED"; exit 1; }
cd $WT || exit 1; HEAD=$(git rev-parse HEAD); echo "HEAD $HEAD"
echo "===== package v5 (v4 kept as cloud_package_dist_v4_03677123) ====="
if [ -d $W/cloud_package_dist ] && [ ! -d $W/cloud_package_dist_v4_03677123 ]; then
  [ "$(cat $W/cloud_package_dist/COMMIT)" = 03677123abf41c91b95d5bcdefa3bff9b25a05d9 ] || { echo "cloud_package_dist is not v4"; exit 1; }
  mv $W/cloud_package_dist $W/cloud_package_dist_v4_03677123 && echo "v4 kept"
fi
[ -e $MAIN/m10p/package_variants_v5 ] && { echo "work dir exists"; exit 1; }
t0=$(date +%s)
bash research/06_scope_redesign/p1_m10p_20261022/cloud_package/make_package.sh $MAIN/m08b/builds_s01 $W/cloud_package_dist $MAIN/m10p/package_variants_v5 > $EA/package_v5/MAKE_PACKAGE.log 2>&1
echo "MAKE_PACKAGE_EXIT $? $(( $(date +%s) - t0 ))s" | tee -a $EA/package_v5/MAKE_PACKAGE.log; tail -4 $EA/package_v5/MAKE_PACKAGE.log
D=$W/cloud_package_dist; V3=$W/cloud_package_dist_v3_e0527cec; V4=$W/cloud_package_dist_v4_03677123
cp $D/PACKAGE_MANIFEST.json $D/SHA256SUMS $D/VARIANT_REPRODUCIBILITY.json $D/EXPECTED_VARIANTS.json $D/BUILD_INPUT_CHANGES.json $D/COMMIT $EA/package_v5/
$PY - $D $V3 $V4 $EA/package_v5/PACKAGE_V5_VS_V3_V4.json <<'P'
import hashlib, json, sys
from pathlib import Path
d, v3, v4, out = (Path(p) for p in sys.argv[1:5])
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
must = ["networks/integrated_365_24h_unsolved.nc", "networks/disconnected_365_24h_unsolved.nc", "networks/integrated_BUILD_RECEIPT.json", "networks/disconnected_BUILD_RECEIPT.json",
        "networks/integrated_costs_active_research.csv", "networks/disconnected_costs_active_research.csv", "EXPECTED_VARIANTS.json"]
same = {f: dict(v5=sha(d / f), v4=sha(v4 / f), v3=sha(v3 / f)) for f in must}
for v in same.values():
    v["equal"] = v["v5"] == v["v4"] == v["v3"]
files = sorted(p for p in d.rglob("*") if p.is_file())
m5 = json.loads((d / "PACKAGE_MANIFEST.json").read_text()); m4 = json.loads((v4 / "PACKAGE_MANIFEST.json").read_text())
s5 = {r["path"]: r["sha256"] for r in m5["files"]}; s4 = {r["path"]: r["sha256"] for r in m4["files"]}
res = dict(v5_commit=m5["commit"], v4_commit=m4["commit"], v5_files=len(files), v5_bytes=sum(p.stat().st_size for p in files), v5_manifest_sha256=sha(d / "PACKAGE_MANIFEST.json"),
           v5_sha256sums_sha256=sha(d / "SHA256SUMS"), fixed_files_identical_to_v3_and_v4=all(v["equal"] for v in same.values()), fixed_files=same,
           files_changed_vs_v4=sorted(p for p in set(s5) | set(s4) if s5.get(p) != s4.get(p)), instance=m5["run"]["instance"])
out.write_text(json.dumps(res, indent=1))
print(json.dumps({k: res[k] for k in ("v5_commit", "v5_files", "v5_bytes", "v5_manifest_sha256", "v5_sha256sums_sha256", "fixed_files_identical_to_v3_and_v4", "files_changed_vs_v4")}, indent=1))
P
echo "===== dry run v5: pre ====="
sed -e 's#D=/home/jin/m10a_dry;#D=/home/jin/m10a_dry_v5;#' -e 's#evidence/dryrun_v4#evidence/dryrun_v5#' /home/jin/m10a_dryrun.sh > /home/jin/m10a_dryrun_v5.sh
grep -nE "^D=|E=/mnt" /home/jin/m10a_dryrun_v5.sh | head -3
STEP=pre bash /home/jin/m10a_dryrun_v5.sh || { echo "DRY_PRE_FAILED"; exit 1; }
echo "===== dry run v5: build (BUILD_ONLY R1-R11, stop before solve) ====="
t0=$(date +%s); STEP=build bash /home/jin/m10a_dryrun_v5.sh || { echo "DRY_BUILD_FAILED"; exit 1; }; echo "BUILD_SECONDS $(( $(date +%s) - t0 ))"
echo "===== build comparison with the M10P second dry run ====="
$PY /home/jin/m10a_s01_buildcmp.py $EA/dryrun_v5/build_only $W/evidence/s01/dryrun/build_only $EA/dryrun_v5/BUILD_VS_S01.json; echo "BUILDCMP_EXIT $?"
echo "===== dry run v5: post ====="
t0=$(date +%s); STEP=post bash /home/jin/m10a_dryrun_v5.sh || { echo "DRY_POST_FAILED"; exit 1; }; echo "POST_SECONDS $(( $(date +%s) - t0 ))"
du -sh /home/jin/m10a_dry_v5; df -h /home | tail -1
echo S01_CHAIN_DONE
