#!/bin/bash
O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b
pkill -f build_s2.sh; sleep 1; pkill -f s2_network.py; sleep 1
ps -eo pid,args | grep -E '[b]uild_s2|[s]2_network' | wc -l
grep -n -E "Error|Traceback|error:" $O/integrated_build.err | head -8 | cut -c1-220
grep -n -B12 "Command being timed" $O/integrated_build.err | head -24 | cut -c1-240
