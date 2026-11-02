#!/bin/bash
W=/home/jin/wt_v3_20261102; cd $W
echo "== build_v3"; cat /home/jin/v3/build_v3.sh | cut -c1-220
echo "== build_flat"; cat /home/jin/v3/build_flat.sh | cut -c1-220
echo "== run_reg"; cat /home/jin/v3/run_reg.sh | cut -c1-200
echo "== override"; grep -n "override" scripts_project/s2_network.py | head -14 | cut -c1-210
grep -rn "def apply_overrides\|def set_override\|def parse_override" scripts_project/*.py | head | cut -c1-160
echo "== TRANSPORT_CARRIERS"; grep -n "TRANSPORT_CARRIERS\s*=" -A3 scripts_project/scenario_network.py | cut -c1-220
echo "== registry"; grep -rln "fragments.*v3\|\"v3.csv\"" scripts_project/*.py | head; grep -n "^def \|^REF\|^SCRIPT\|fragments" scripts_project/v3_registry.py 2>/dev/null | head -30 | cut -c1-160
echo "== tests"; grep -n "^def test\|^@pytest\|^[A-Z_]* = " tests/research/test_v3.py | cut -c1-120 | head -40
