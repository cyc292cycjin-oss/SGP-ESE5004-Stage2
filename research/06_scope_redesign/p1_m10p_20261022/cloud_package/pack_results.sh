#!/bin/bash
# M10P results pack (instruction section 4.4): two archives of <run dir>/export, written next to the run dir.
#   bash pack_results.sh <run dir> <tag>
#   light: every file of export/ except NetCDF (*.nc): receipts, C1 / M12 / GATES_V6 outputs, ledgers, prices, scrubbed logs, monitors, batch
#          outputs (summary, reference, level-2, leave-one-out, benefit), variant receipts, ARRAYS_MANIFEST.json;
#   full:  light + the solved networks and DUALS_BY_CONSTRAINT.nc of every run.
# Never packed: the LP / solution arrays and the raw solver logs (they stay on the instance; ARRAYS_MANIFEST.json lists the arrays with SHA256),
# the licence. Both archives are refused when a licence-like string is found in export/. Writes results_{light,full}_<tag>_<utc>.tar.gz + .sha256.
# M10R (supplement S1): optional 3rd argument = the export paths to pack (space separated, relative to the run dir; default "export"), 4th = the
# arrays manifest path (default export/batch/ARRAYS_MANIFEST.json), 5th = run ids whose arrays the manifest lists (comma list; "-" = none;
# default every run folder) - for the packs of --only / --repost / --summary-s1 that hold the selected runs only.
set -u
OUT=${1:?run dir}; TAG=${2:?tag}; PATHS=${3:-export}; MAN=${4:-export/batch/ARRAYS_MANIFEST.json}; RIDS=${5:-}
OUT=$(cd "$OUT" && pwd); EXP="$OUT/export"; [ -d "$EXP" ] || { echo "PACK_FAILED:no export folder"; exit 1; }
PY=${PY:-python}; STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p "$EXP/batch" "$(dirname "$OUT/$MAN")"
"$PY" - "$OUT" "$OUT/$MAN" "$RIDS" <<'P' || { echo "PACK_FAILED:arrays manifest"; exit 1; }
import hashlib, json, sys
from pathlib import Path
out, dst, rids = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
dirs = [] if rids == "-" else ([out / r for r in rids.split(",") if r] if rids else sorted(d for d in out.iterdir() if d.is_dir()))
rows = [dict(path=str(p.relative_to(out)), bytes=p.stat().st_size, sha256=sha(p)) for d in dirs for sub in ("lp", "solution") for p in sorted(d.glob(f"{sub}/*.npy"))]
dst.write_text(json.dumps(dict(note="LP / solution arrays left on the instance (not packed); fetch separately if needed", runs=(rids or "all"), files=rows, total_bytes=sum(r["bytes"] for r in rows)), indent=1) + "\n")
P
if grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" "$EXP" > "$OUT/pack_licence_hits.txt" 2>/dev/null; then
  echo "PACK_REFUSED:licence-like string in $(head -3 "$OUT/pack_licence_hits.txt" | tr '\n' ' ')"; exit 1
fi
rm -f "$OUT/pack_licence_hits.txt"
cd "$OUT" || exit 1
L="results_light_${TAG}_${STAMP}.tar.gz"; F="results_full_${TAG}_${STAMP}.tar.gz"
for p in $PATHS; do [ -e "$p" ] || { echo "PACK_FAILED:missing $p"; exit 1; }; done
tar czf "$L" --exclude='*.nc' $PATHS && sha256sum "$L" > "$L.sha256" || { echo "PACK_FAILED:light"; exit 1; }
tar czf "$F" $PATHS && sha256sum "$F" > "$F.sha256" || { echo "PACK_FAILED:full"; exit 1; }
echo "PACKED:light=$L:$(stat -c %s "$L")B:sha256=$(cut -c1-16 "$L.sha256"):full=$F:$(stat -c %s "$F")B:sha256=$(cut -c1-16 "$F.sha256")"
