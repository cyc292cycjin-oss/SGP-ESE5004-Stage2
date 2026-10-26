#!/bin/bash
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
echo "=== results_project top (dirs) ==="; ls -d $M/*/ | xargs -n1 basename | tr '\n' ' '; echo
echo "=== m08b ==="; ls -la $M/m08b
echo "=== builds_s01 ==="; ls -la $M/m08b/builds_s01/integrated $M/m08b/builds_s01/disconnected
echo "=== smoke_s01 ==="; ls -la $M/m08b/smoke_s01; ls -la $M/m08b/smoke_s01/integrated | head -50
echo "=== smoke_s01 STATUS ==="; cat $M/m08b/smoke_s01/STATUS.txt
echo "=== du ==="; du -sh $M/m08b $M/m10r $M/b4p $M/m12 2>/dev/null
echo "=== results_project assembly_v1 / s1 ==="; ls $M/assembly_v1 | head; ls $M/s1 | head
