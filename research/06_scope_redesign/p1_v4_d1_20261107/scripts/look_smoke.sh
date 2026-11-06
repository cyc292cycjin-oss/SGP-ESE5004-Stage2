#!/bin/bash
S=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56
for r in v4_F1 v4_F2; do echo "== $r"; ls $S/$r | tr '\n' ' '; echo; ls $S/$r/solution 2>/dev/null | head -20 | tr '\n' ' '; echo; done
du -sh $S; df -h /home/jin | tail -1
