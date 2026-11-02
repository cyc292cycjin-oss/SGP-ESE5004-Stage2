#!/bin/bash
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
git -C . log -1 --format=%h >/dev/null
grep -rln "AIRPORT_SIZE_WEIGHTS\|PORT_SIZE_WEIGHTS" scripts_project/*.py scripts_project/retired/*.py research/04_model_assembly/gate4/*.md 2>/dev/null | head -5
f=$(grep -rln "AIRPORT_SIZE_WEIGHTS" scripts_project/ 2>/dev/null | head -1); echo $f; grep -n "SIZE_WEIGHTS\|size\b.*weight\|'large'\|\"large\"\|Large\|Medium" $f 2>/dev/null | cut -c1-190 | head -14
du -sh results_project/v3 /home/jin/wt_v3_20261102
