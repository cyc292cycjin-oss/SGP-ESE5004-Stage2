#!/bin/bash
# syntax checks of the S4O-4 preparation files (no run)
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/research/06_scope_redesign/p1_step4o_20261019
for f in cloud_package/preflight.sh cloud_package/make_package.sh cloud_package/run_365x24h.sh evidence/s4o_4/test_s4o4_scripts.sh; do bash -n $f && echo "bash -n OK: $f"; done
/home/jin/miniforge3/envs/pypsa-earth/bin/python -m py_compile cloud_package/package_checks.py && echo "py_compile OK: cloud_package/package_checks.py"
rm -rf cloud_package/__pycache__
