#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mode="${1:---dry-run}"
if [[ "$mode" != --dry-run && "$mode" != --run ]]; then
  echo "Usage: bash reproducibility/resume_2050_simplex.sh [--dry-run|--run]" >&2
  exit 2
fi
target=results/baseline-aims-3H-tutorial/postnetworks/elec_s_50_ec_lv2.0__3h_2050_0.071.nc
args=(solve_sector_networks --cores 1 --rerun-incomplete --rerun-triggers mtime
  --set-resources build_shapes:mem_mb=1024
  --configfile configs/config.asean.yaml configs/tutorials/config.asean.yaml
  configs/tutorials/config.sgp-lowmem.yaml configs/tutorials/config.sgp-simplex.yaml)
if [[ "$mode" == --dry-run ]]; then
  snakemake "${args[@]}" --dry-run
  exit $?
fi
if [[ -e "$target" ]]; then
  echo "2050 result already exists. Review it before another run; refusing to overwrite." >&2
  exit 2
fi
stamp=$(date +%Y%m%d-%H%M%S)
audit="logs/reproduction/resume-2050-simplex-$stamp"
mkdir -p "$audit"
cp configs/tutorials/config.sgp-simplex.yaml "$audit/"
cp reproducibility/resume_2050_simplex.sh "$audit/"
for file in logs/baseline-aims-3H-tutorial/solve_network/*2050_0.071*; do
  [[ -f "$file" ]] && cp "$file" "$audit/"
done
git rev-parse HEAD > "$audit/git-head.txt"
git diff > "$audit/code-changes.patch"
sha256sum results/baseline-aims-3H-tutorial/postnetworks/*2030_0.071.nc results/baseline-aims-3H-tutorial/postnetworks/*2040_0.071.nc > "$audit/input-checksums.txt"
printf '%q ' snakemake "${args[@]}" > "$audit/command.txt"
printf '\n' >> "$audit/command.txt"
conda list --explicit > "$audit/environment-explicit.txt"
set +e
snakemake "${args[@]}" 2>&1 | tee "$audit/workflow.log"
statuses=("${PIPESTATUS[@]}")
set -e
printf 'Snakemake exit code: %s\n' "${statuses[0]}" | tee "$audit/exit-code.txt"
sha256sum --check "$audit/input-checksums.txt" | tee "$audit/input-check.txt"
echo "Run records: $audit"
exit "${statuses[0]}"
