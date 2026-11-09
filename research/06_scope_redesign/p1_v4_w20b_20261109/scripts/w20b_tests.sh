#!/bin/bash
# W20b section 2.2: tests of the coalition tool (W20 file unchanged + the W20b ports file). No solver.
set -u
WT=/home/jin/wt_v4_w20b; OUT=${1:?log}
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
cd $WT || exit 1
{
  echo "START $(date -u +%FT%TZ) commit=$(git rev-parse HEAD) module_sha256=$(sha256sum scripts_project/v4_coalition.py | cut -c1-64) ports_test_sha256=$(sha256sum tests/research/test_v4_coalition_ports.py | cut -c1-64) w20_test_sha256=$(sha256sum tests/research/test_v4_coalition.py | cut -c1-64)"
  echo "solver calls in the test files (optimize( / .solve( / linprog):"; grep -nE 'optimize\(|\.solve\(|linprog' tests/research/test_v4_coalition.py tests/research/test_v4_coalition_ports.py || echo "  none"
  /usr/bin/time -v /home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest -p no:cacheprovider -v tests/research/test_v4_coalition.py tests/research/test_v4_coalition_ports.py 2>&1 | grep -vE 'Warning|warn\('
  echo "DONE $(date -u +%FT%TZ)"
} > $OUT 2>&1
