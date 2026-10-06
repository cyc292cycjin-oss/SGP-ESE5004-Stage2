#!/usr/bin/env bash
# One authorized validation attempt. No retry loop, no checkpoint resume.
set -euo pipefail
cd "$(dirname "$0")/.."
run_id=gate5_20261006_04
output="results_project/validation/$run_id"
test ! -e "$output" || { echo "Run already exists: $output" >&2; exit 2; }
test ! -e "${output}_driver.log" || { echo "Driver log already exists; inspect before any launch" >&2; exit 2; }
exec 9>results_project/validation/.gate5-validation.lock
flock -n 9 || { echo "Another Gate5 launch holds the lock" >&2; exit 2; }
exec /home/jin/miniforge3/envs/pypsa-earth/bin/python -u scripts_project/run_gate5_stable_inventory.py \
    --output "$output" --time-limit 10800 --wall-guard 14400 \
    >"${output}_driver.log" 2>&1
