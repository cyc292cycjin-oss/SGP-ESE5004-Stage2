#!/bin/bash
# M10P supplement 01: self-test of the access trace (scratch only)
set -u
S=/home/jin/m10p_s01_scratch/tracer; rm -rf "$S"; mkdir -p "$S/repo/research" "$S/trace" "$S/root"
cp /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/scripts/m10p_s01_trace/sitecustomize.py "$S/trace/"
echo '{}' > "$S/repo/research/x.json"
cd "$S/repo"
env PYTHONPATH="$S/trace" M10P_TRACE_REPO="$S/repo" M10P_TRACE_ROOT="$S/root" M10P_TRACE_LOG="$S/trace.log" /home/jin/miniforge3/envs/pypsa-earth/bin/python - <<'P'
import os, glob, json, pathlib
os.path.exists("research/x.json"); pathlib.Path("research/x.json").is_file(); json.load(open("research/x.json"))
list(pathlib.Path(".").glob("research/*")); os.listdir("research"); glob.glob("research/*.json")
os.path.exists("configs/research/baseline.yaml")   # not the top-level research/ folder: must not be recorded as RESEARCH
import numpy, yaml   # imports must keep working
print("ok", numpy.__version__)
P
echo "--- log"; cat "$S/trace.log"
echo "RESEARCH lines: $(grep -c '^RESEARCH' "$S/trace.log")  configs/research lines: $(grep -c 'configs/research' "$S/trace.log")"
