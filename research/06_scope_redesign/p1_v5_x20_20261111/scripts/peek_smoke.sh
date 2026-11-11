#!/bin/bash
RP=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
for r in F1 F2; do python3 -c "import json,sys;r=json.load(open(sys.argv[1]));p=r['peak_rss_bytes'];print(sys.argv[2],p,round(p/2**20,1),'x1.05 MiB',round(p*1.05/2**20))" $RP/v4d2c/smoke56/v4d2c_$r/SOLVE_RECEIPT.json $r; done
awk '/MemAvailable|MemTotal/' /proc/meminfo
