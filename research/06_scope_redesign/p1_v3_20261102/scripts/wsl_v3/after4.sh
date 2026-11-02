#!/bin/bash
# V3 supplement 04 section 2.4 item 4 and tests, serial: dry run of the screening runner, package with preflight, full tests/research (no solver, no licence, no cloud).
cd /home/jin/v3
bash dry_s4.sh > /home/jin/v3/out_dry4.txt 2>&1; echo "DRY_EXIT:$?"; tail -8 /home/jin/v3/out_dry4.txt | cut -c1-230
bash pkg_s4.sh > /home/jin/v3/out_pkg4.txt 2>&1; echo "PKG_EXIT:$?"; tail -34 /home/jin/v3/out_pkg4.txt | cut -c1-210
bash run_tests3.sh > /home/jin/v3/out_tests4.txt 2>&1; echo "TESTS_EXIT:$?"; tail -10 /home/jin/v3/out_tests4.txt | cut -c1-200
