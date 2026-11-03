#!/bin/bash
# facts of the built package for the report (read only)
P=${1:-/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3}; cd "$P" || exit 2
echo "files $(find . -type f | wc -l) bytes $(find . -type f -printf '%s\n' | awk '{s += $1} END {print s}')"
/home/jin/miniforge3/envs/pypsa-earth/bin/python -I -c "import json; r = json.load(open('HPC_CONSISTENCY.json')); print('consistency rows', len(r['rows']), 'all', r['all_consistent'])"
ls pbs | tr '\n' ' '; echo
sha256sum code_*.tar.gz SHA256SUMS HPC_PACKAGE_MANIFEST.json BATCH_DEF.json | cut -c1-80
