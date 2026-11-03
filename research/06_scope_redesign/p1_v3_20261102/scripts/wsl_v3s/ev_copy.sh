#!/bin/bash
# V3 screening: copy the evidence of the recovered results into the deliverable folder (evidence/screen), as DFX phase 4 did: key files of the light pack
# (the packs stay in work/p1_v3_20261102/cloud_results/), the analysis outputs, the pack SHA256 files, upload / download / mark / licence logs and the
# filtered instance records (r_small.sh, r_record.sh). Mirror /home/jin/v3s into scripts/wsl_v3s (no auth text, no records). No host / port anywhere.
set -u
C=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z
W=/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102; D=$W/evidence/screen; X=$C/light_unpacked/export; R=/home/jin/v3s/records
mkdir -p $D/batch/M12_BENEFIT $D/instance $D/analysis
cp $X/batch/*.json $X/batch/*.md $X/batch/*.csv $X/batch/STATUS.txt $D/batch/
cp $X/batch/M12_BENEFIT/* $D/batch/M12_BENEFIT/
for r in V1 V2 V4 V5 V3; do
  mkdir -p $D/$r/m12_owen
  for f in RUN.json SOLVE_RECEIPT.json V5_GATES.json V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json PRECISION.json PRECISION.md VIOLATIONS.json \
           LEDGER_IDENTITY.json INTERIOR_CHECKS.json kkt_summary.json COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_USD2020.csv EMISSIONS_BY_COUNTRY.json \
           BUNKER_ACCOUNT.json ALLOCATION.json ALLOCATION.md GUROBI_LOG_SCRUBBED.txt solve_time.txt MONITOR_$r.csv MATH_PROBLEM.json; do
    [ -f $X/$r/$f ] && cp $X/$r/$f $D/$r/
  done
  for f in OWEN.json OWEN.md OWEN.csv OWEN_REGRADE_BATCH_REFERENCE.json RHS_AUDIT.json; do [ -f $X/$r/m12_owen/$f ] && cp $X/$r/m12_owen/$f $D/$r/m12_owen/; done
done
cp $C/analysis/* $D/analysis/
cp $C/*.sha256 $D/
cp /home/jin/v3s/upload.log $D/instance/UPLOAD.log
cp $R/download.log $D/instance/DOWNLOAD.log; cp $R/mark_and_licence.txt $D/instance/MARK_AND_LICENCE.txt; cp $R/r_record.txt $D/instance/RECORD_BEFORE_SHUTDOWN.txt
[ -f $R/shutdown.txt ] && cp $R/shutdown.txt $D/instance/SHUTDOWN.txt
cp $R/boot.txt $D/instance/BOOT_TIME.txt
for f in $R/LEAK_SCAN_*.json $R/LEAK_CLASSIFY_*.txt; do [ -f "$f" ] && cp "$f" $D/instance/; done
awk -v d=$D/instance '/^@@FILE /{f=d "/" $2; next} /^@@END/{f=""} f!="" {print > f}' $R/r_small.txt
mv $D/instance/STATUS.txt $D/instance/STATUS_FINAL.txt 2>/dev/null
grep -l -E 'autodl-container-' -r $D && { echo "INSTANCE NAME FOUND"; exit 3; }
mkdir -p $W/scripts/wsl_v3s
cp /home/jin/v3s/*.sh /home/jin/v3s/*.py $W/scripts/wsl_v3s/
find $D -type f | sort | sed "s|$D/||" > /tmp/v3s_ev_list.txt; echo "evidence files: $(wc -l < /tmp/v3s_ev_list.txt)"; du -sh $D
ls $W/scripts/wsl_v3s | wc -l
