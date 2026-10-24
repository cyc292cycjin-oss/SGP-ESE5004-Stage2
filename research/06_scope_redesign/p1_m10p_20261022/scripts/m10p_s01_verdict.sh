#!/bin/bash
# M10P supplement 01: comparison of the two dry runs, trace summary and the research/ verdict (read only)
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022; E=$W/evidence/s01; D=/home/jin/m10p_dry_s01; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
V=$W/scripts/m10p_s01_verdict.py
$PY $V builds $W/evidence/dryrun/build_only $E/dryrun/build_only $E/S01_DRYRUN_BUILDS_VS_FIRST.json
logs=(); for s in control pre build post; do [ -f $D/TRACE_$s.log ] && logs+=($D/TRACE_$s.log); done
$PY $V trace $E/S01_TRACE_SUMMARY.json "${logs[@]}"
mkdir -p $E/dryrun/trace; for f in "${logs[@]}"; do cp $f $E/dryrun/trace/; gzip -kf $E/dryrun/trace/$(basename $f) 2>/dev/null; done
ls -la $E/dryrun/trace
if [ "${VERDICT:-0}" = 1 ]; then $PY $V verdict $E/S01_STATIC_RESEARCH_RAW.json $E/S01_TRACE_SUMMARY.json $E/S01_DRYRUN_BUILDS_VS_FIRST.json $E/S01_RESEARCH_DEPENDENCY.json; fi
