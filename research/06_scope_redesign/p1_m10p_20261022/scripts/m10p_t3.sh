#!/bin/bash
# M10P-3 tests of the new runner (no solver; synthetic stand-ins)
cd /home/jin/wt_m10p_20261022 || exit 1
chmod 755 research/06_scope_redesign/p1_m10p_20261022/cloud_package/*.sh
env -u GRB_LICENSE_FILE timeout 1800 /home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest tests/research/test_m10p_batch3.py -q -p no:cacheprovider -x ${K:+-k "$K"} 2>&1 | tail -60
