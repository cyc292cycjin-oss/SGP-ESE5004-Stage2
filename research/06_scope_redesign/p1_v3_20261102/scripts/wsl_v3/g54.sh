#!/bin/bash
cd /home/jin/wt_v3_20261102/tests/research
grep -n "^def \|^[A-Z_]* = " test_dfx_runner.py | head -40 | cut -c1-150
sed -n "$(grep -n '^def _package' test_dfx_runner.py | cut -d: -f1),+34p" test_dfx_runner.py | cut -c1-230
sed -n "$(grep -n '^def _run' test_dfx_runner.py | cut -d: -f1),+14p" test_dfx_runner.py | cut -c1-230
