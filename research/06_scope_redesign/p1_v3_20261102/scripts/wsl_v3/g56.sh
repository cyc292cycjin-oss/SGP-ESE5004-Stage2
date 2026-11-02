#!/bin/bash
O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b
pkill -f build_s2.sh; sleep 1; pkill -f s2_network.py; sleep 1
grep -n -A12 -E "^Traceback" $O/integrated_build.err | tail -22 | cut -c1-200
ls -la $O/integrated | cut -c25-120
