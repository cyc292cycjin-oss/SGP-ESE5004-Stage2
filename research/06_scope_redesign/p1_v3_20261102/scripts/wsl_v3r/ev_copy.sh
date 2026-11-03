#!/bin/bash
# V3 supplement 07 rerun: copy the evidence of the recovered results into the deliverable folder evidence/dmax_screen (the packs stay in
# work/p1_v3_20261102/cloud_results/<tag>/): key files of the light pack per run, batch files, the analysis outputs, the pack SHA256 files, upload / download /
# mark / licence / shutdown records and the filtered instance records. Mirror /home/jin/v3r into scripts/wsl_v3r (no auth text, no records). No host / port.
# usage: bash ev_copy.sh <cloud_results/<tag> folder>
set -u
C=${1:?results folder}
W=/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102; D=$W/evidence/dmax_screen; X=$C/light_unpacked/export; R=/home/jin/v3r/records
mkdir -p $D/batch/M12_BENEFIT $D/instance $D/analysis
cp $X/batch/*.json $X/batch/*.md $X/batch/*.csv $X/batch/STATUS.txt $D/batch/ 2>/dev/null
cp $X/batch/M12_BENEFIT/* $D/batch/M12_BENEFIT/ 2>/dev/null
for r in V1 V2 V3; do
  mkdir -p $D/$r/m12_owen
  for f in RUN.json SOLVE_RECEIPT.json V5_GATES.json V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json PRECISION.json PRECISION.md VIOLATIONS.json \
           LEDGER_IDENTITY.json INTERIOR_CHECKS.json kkt_summary.json COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_USD2020.csv EMISSIONS_BY_COUNTRY.json \
           BUNKER_ACCOUNT.json ALLOCATION.json ALLOCATION.md GUROBI_LOG_SCRUBBED.txt solve_time.txt MONITOR_$r.csv MATH_PROBLEM.json; do
    [ -f $X/$r/$f ] && cp $X/$r/$f $D/$r/
  done
  for f in OWEN.json OWEN.md OWEN.csv OWEN_REGRADE_BATCH_REFERENCE.json RHS_AUDIT.json; do [ -f $X/$r/m12_owen/$f ] && cp $X/$r/m12_owen/$f $D/$r/m12_owen/; done
done
cp $C/analysis/* $D/analysis/ 2>/dev/null
cp $C/*.sha256 $D/
cp /home/jin/v3r/upload.log $D/instance/UPLOAD.log
for f in download.log mark_and_licence.txt r_record.txt shutdown.txt boot.txt; do [ -f $R/$f ] && cp $R/$f $D/instance/$f; done
for f in $R/LEAK_SCAN_*.json $R/LEAK_CLASSIFY_*.txt; do [ -f "$f" ] && cp "$f" $D/instance/; done
[ -f $R/r_small.txt ] && awk -v d=$D/instance '/^@@FILE /{f=d "/" $2; next} /^@@END/{f=""} f!="" {print > f}' $R/r_small.txt
mv $D/instance/STATUS.txt $D/instance/STATUS_FINAL.txt 2>/dev/null
PFX="autodl""-container-"   # built from two parts: this file holds no instance-name prefix
grep -l -E "$PFX" -r $D && { echo "INSTANCE NAME FOUND"; exit 3; }
mkdir -p $W/scripts/wsl_v3r
cp /home/jin/v3r/*.sh /home/jin/v3r/*.py $W/scripts/wsl_v3r/
find $D -type f | wc -l | sed 's/^/evidence files: /'; du -sh $D
ls $W/scripts/wsl_v3r | wc -l
