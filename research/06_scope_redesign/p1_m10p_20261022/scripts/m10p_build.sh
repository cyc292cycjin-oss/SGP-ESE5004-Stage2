#!/bin/bash
# M10P-2 (instruction section 1.4): rebuild the four networks (integrated / disconnected; each build writes the 2920x3h network and its exact daily
# mean 365x24h) on the clean integration-branch commit and compare every file SHA256 with the M08b supplement 01 builds (commit ec80668f,
# main checkout results_project/m08b/builds_s01). No solve. Same procedure as /home/jin/m08b_build.sh: inputs from the main checkout's
# results_project (assembly_v1, s1) through temporary symlinks in the worktree (removed afterwards); outputs to the main checkout's
# results_project/m10p/builds (gitignored, not committed).
set -u
WT=/home/jin/wt_m10p_20261022; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
REF=$MAIN/results_project/m08b/builds_s01; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/evidence
export PYTHONHASHSEED=0
OUT=$MAIN/results_project/m10p/builds; [ -e $OUT ] && { echo "output folder $OUT exists - not overwritten"; exit 2; }
mkdir -p $OUT; ST=$OUT/BUILD_STATUS.txt
cd $WT || exit 1
dirty=$(git status --porcelain --untracked-files=no | wc -l)
[ "$dirty" = 0 ] || { echo "START_REFUSED:dirty=$dirty" >> $ST; exit 3; }
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD) dirty:$dirty" >> $ST
build() { local sc=$1; mkdir -p $OUT/$sc
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/$sc > $OUT/${sc}_build.log 2> $OUT/${sc}_build.err
  echo "BUILD_$sc:$?:$(tail -1 $OUT/${sc}_build.log | cut -c1-120):$(grep -h 'Maximum resident' $OUT/${sc}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/${sc}_build.err | tr -s ' ')" >> $ST; }
for sc in integrated disconnected; do build $sc; done
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
rmdir results_project 2>/dev/null
echo "END:$(date -u +%Y-%m-%dT%H:%M:%SZ) dirty_after:$(git status --porcelain --untracked-files=no | wc -l)" >> $ST
# every file of the new builds against the reference builds (networks first; receipts and side tables listed with their differences)
$PY - $OUT $REF $E <<'P'
import hashlib, json, sys
from pathlib import Path
out, ref, E = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
rows = []
for sc in ("integrated", "disconnected"):
    for f in sorted((out / sc).iterdir()):
        r = ref / sc / f.name
        rows.append(dict(scenario=sc, file=f.name, bytes=f.stat().st_size, sha256=sha(f), reference_sha256=(sha(r) if r.exists() else None)))
        rows[-1]["equal"] = rows[-1]["sha256"] == rows[-1]["reference_sha256"]
nets = [r for r in rows if r["file"].endswith("_unsolved.nc")]
rec = {}
for sc in ("integrated", "disconnected"):
    a = json.loads((out / sc / f"{sc}_BUILD_RECEIPT.json").read_text()); b = json.loads((ref / sc / f"{sc}_BUILD_RECEIPT.json").read_text())
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    rec[sc] = dict(differing_top_level_keys=diff, new={k: a.get(k) for k in diff if k not in ("inputs",)}, reference={k: b.get(k) for k in diff if k not in ("inputs",)},
                   network_sha256=(a.get("network") or {}).get("sha256"), daily_sha256=(a.get("daily_network") or {}).get("sha256"), code_sha=a.get("code_sha"), reference_code_sha=b.get("code_sha"))
res = dict(step="M10P-2", reference=dict(folder=str(ref), commit="ec80668fbd14742565e189fa368fbee8b8f29242"), new_folder=str(out),
           networks_all_equal=all(r["equal"] for r in nets) and len(nets) == 4, networks=nets, other_files=[r for r in rows if r not in nets], receipts=rec)
(E / "M10P_NETWORK_REBUILD.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps(dict(networks_all_equal=res["networks_all_equal"], networks=[(r["file"], r["sha256"][:16], r["equal"]) for r in nets],
                      other_differing=[(r["scenario"], r["file"]) for r in res["other_files"] if not r["equal"]],
                      receipt_diff={k: v["differing_top_level_keys"] for k, v in rec.items()})))
P
cp $ST $E/M10P_BUILD_STATUS.txt
echo DONE >> $ST
