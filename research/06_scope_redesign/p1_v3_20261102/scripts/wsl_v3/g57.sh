#!/bin/bash
O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b
grep -n -E "Error|error" $O/integrated_build.err | tail -6 | cut -c1-240
L=$(grep -n "Command exited" $O/integrated_build.err | cut -d: -f1); sed -n "$((L-8)),$((L-1))p" $O/integrated_build.err | cut -c1-200
