#!/bin/bash
# V3 HPC package step 6.3: local dry run of the built package (no solver, no licence; truncated networks): a copy of the package in a fresh folder ->
# preflight sections guards,sha,networks,env,profile,code,tools (licence / resources excluded) -> BUILD_ONLY with TRUNCATE=56 over the four runs (process 1 only)
# -> the job body in build_only mode for F3 (local drill switches, HPR_DRY_TRUNCATE=56) -> the job body refusing a formal job while the limits are PROPOSED.
# usage: dry_hpc.sh <package dir> ; writes /home/jin/v3h/dry_<stamp>/ (never reused) and DRY_RUN_HPC.txt there
set -u
echo "REFUSED: superseded by dry_hpc2.sh (2026-11-04): its last step runs a clean formal job body, which on a REGISTERED package would start a real build and solve"; exit 2
SRC=${1:?package dir}; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/home/jin/v3h/dry_$(date -u +%Y%m%dT%H%M%SZ); [ ! -e "$D" ] || exit 2; mkdir -p "$D"; R=$D/DRY_RUN_HPC.txt
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest')" = 0 ] || { echo "REFUSED: a solve or pytest is running"; exit 4; }
cp -r "$SRC" "$D/pkg"; cd "$D/pkg" || exit 2
echo "DRY:start:$(date -u +%FT%TZ):package=$SRC:commit=$(cat COMMIT)" > $R
env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools bash preflight.sh > $D/preflight.txt 2>&1; echo "PREFLIGHT:exit=$?:$(tail -1 $D/preflight.txt)" >> $R
grep -E "files OK|limits of the package|all_equal|ENV|OK|FAILED|DIFFER|MISSING" $D/preflight.txt | head -20 >> $R
T0=$(date +%s)
env -u GRB_LICENSE_FILE PY=$PY BUILD_ONLY=1 TRUNCATE=56 ALLOW_UNREGISTERED=1 RUN_DIR=$D/runs/build_only_all bash run_batch4.sh > $D/build_only.out 2>&1; rc=$?
echo "BUILD_ONLY_ALL:exit=$rc:$(( $(date +%s) - T0 ))s" >> $R
grep -E "BASE_CHECK|BUILD_CHECK_|BUILD_F[1-4]|STOP|REFUSED|DONE" $D/runs/build_only_all/STATUS.txt | cut -c1-300 >> $R
T0=$(date +%s)
env -u GRB_LICENSE_FILE PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.dry JOB_KEY=build_only JOB_MODE=build_only JOB_RID=F3 JOB_NCPUS=16 JOB_MEM_GB=10 JOB_WALLTIME=02:30:00 PY=$PY \
  HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$D/jobroot HPR_DRY_TRUNCATE=56 bash hpc/hpr_job.sh > $D/job_build_only.out 2>&1; rc=$?
echo "JOB_BODY_BUILD_ONLY_F3:exit=$rc:$(( $(date +%s) - T0 ))s" >> $R
cat $D/jobroot/runs/build_only_f1/BUILD_ONLY_STATUS.txt 2>/dev/null | cut -c1-200 >> $R
lic=$D/fake_lic; echo "placeholder" > $lic; chmod 600 $lic
env -u GRB_LICENSE_FILE PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.dry JOB_KEY=formal JOB_MODE=formal JOB_RID=F1 JOB_NCPUS=48 JOB_MEM_GB=300 JOB_WALLTIME=376:00:00 PY=$PY \
  HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$D/jobroot2 HPR_AUTH="dry run refusal check" GRB_LICENSE_FILE=$lic bash hpc/hpr_job.sh > $D/job_formal.out 2>&1; rc=$?
echo "JOB_BODY_FORMAL_F1_REFUSED:exit=$rc:$(head -1 $D/job_formal.out | cut -c1-200):started=$( [ -e $D/jobroot2/runs/batch4/F1 ] && echo yes || echo no)" >> $R
rm -f $lic
find $D/runs $D/jobroot -name 'problem.lp' -size +1M -delete 2>/dev/null
echo "DRY:end:$(date -u +%FT%TZ):disk=$(du -sh $D | cut -f1)" >> $R
cat $R
