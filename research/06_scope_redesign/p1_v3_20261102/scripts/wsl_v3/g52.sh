#!/bin/bash
O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b
tail -14 $O/integrated_build.err | cut -c1-220
echo ---; ps -eo pid,etime,args | grep -E '[b]uild_s2|[s]2_network' | cut -c1-120
