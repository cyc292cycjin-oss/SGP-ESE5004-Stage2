#!/bin/bash
# V3.1 section 6.4: local dry run of the built package (no solver, no licence; truncated networks) with the shell BASH_BIN (default bash; bash 4.2 drill:
# BASH_BIN=/home/jin/v3h/bash42/src/bash). Same steps as the V14 dry run (dry_hpc2.sh), with the v3.1 run folders: a copy of the package in a fresh folder ->
# preflight sections guards,sha,networks,env,profile,code,tools (licence / resources excluded) -> BUILD_ONLY with TRUNCATE=56 over the four runs (process 1 only)
# -> the job body in build_only mode for F3 (local drill switches, HPR_DRY_TRUNCATE=56) -> two formal job bodies that must start nothing: F1 with a test hook
# (refused, exit 2) and F3 without an ended F1 (STOP_SAFE:PREDECESSOR_NOT_ENDED, exit 3; must land in runs/batch5) -> hpr_submit.sh --dry-run (notes, DRY_RUN_OK;
# the smoke note must name runs/smoke56_v31) -> hpr_status.sh default folder. The formal job body is never run without a refusal path.
# usage: dry_hpc31.sh <package dir> ; writes /home/jin/v3fix/dry_<stamp>/ (never reused) and DRY_RUN_HPC.txt there; deletes nothing itself
set -u
SRC=${1:?package dir}; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; BB=${BASH_BIN:-bash}
D=/home/jin/v3fix/dry_$(date -u +%Y%m%dT%H%M%SZ); [ ! -e "$D" ] || exit 2; mkdir -p "$D"; R=$D/DRY_RUN_HPC.txt
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest')" = 0 ] || { echo "REFUSED: a solve or pytest is running"; exit 4; }
mkdir -p "$D/shim"; ln -s "$(command -v "$BB")" "$D/shim/bash"; export PATH="$D/shim:$PATH"   # every nested "bash ..." of the package runs under BASH_BIN too
cp -r "$SRC" "$D/pkg"; cd "$D/pkg" || exit 2
echo "DRY:start:$(date -u +%FT%TZ):package=$SRC:commit=$(cat COMMIT):shell=$(bash --version | head -1)" > $R
env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools bash preflight.sh > $D/preflight.txt 2>&1; echo "PREFLIGHT:exit=$?:$(tail -1 $D/preflight.txt)" >> $R
grep -E "files OK|limits of the package|all_equal|ENV|OK|FAILED|DIFFER|MISSING|unbound|syntax error" $D/preflight.txt | head -20 >> $R
T0=$(date +%s)
env -u GRB_LICENSE_FILE PY=$PY BUILD_ONLY=1 TRUNCATE=56 ALLOW_UNREGISTERED=1 RUN_DIR=$D/runs/build_only_all bash run_batch4.sh > $D/build_only.out 2>&1; rc=$?
echo "BUILD_ONLY_ALL:exit=$rc:$(( $(date +%s) - T0 ))s" >> $R
grep -E "BASE_CHECK|BUILD_CHECK_|BUILD_F[1-4]|STOP|REFUSED|DONE" $D/runs/build_only_all/STATUS.txt | cut -c1-300 >> $R
for f in $D/runs/build_only_all/F*/SOLVE_RECEIPT.json; do "$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); lp=r.get('lp',{}); print('LP:'+sys.argv[1].split('/')[-2]+':rows='+str(lp.get('num_row'))+':cols='+str(lp.get('num_col'))+':nnz='+str(lp.get('nnz'))+':bunker_row_in_hooks='+str('research_bunker_co2_limit' in (lp.get('research_constraints') or [])))" "$f" >> $R 2>/dev/null; done
grep -E "unbound|syntax error|command not found" $D/build_only.out | head -5 >> $R
T0=$(date +%s)
env -u GRB_LICENSE_FILE PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.dry JOB_KEY=build_only JOB_MODE=build_only JOB_RID=F3 JOB_NCPUS=16 JOB_MEM_GB=10 JOB_WALLTIME=02:30:00 PY=$PY \
  HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$D/jobroot HPR_DRY_TRUNCATE=56 bash hpc/hpr_job.sh > $D/job_build_only.out 2>&1; rc=$?
echo "JOB_BODY_BUILD_ONLY_F3:exit=$rc:$(( $(date +%s) - T0 ))s" >> $R
cat $D/jobroot/runs/build_only_f1/BUILD_ONLY_STATUS.txt 2>/dev/null | cut -c1-200 >> $R
grep -E "unbound|syntax error|command not found" $D/job_build_only.out | head -5 >> $R
lic=$D/fake_lic; echo "placeholder" > $lic; chmod 600 $lic
env -u GRB_LICENSE_FILE PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.dry JOB_KEY=formal JOB_MODE=formal JOB_RID=F1 JOB_NCPUS=48 JOB_MEM_GB=300 JOB_WALLTIME=260:00:00 PY=$PY BUILD_ONLY=1 \
  HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$D/jobroot2 HPR_AUTH="dry run refusal check" GRB_LICENSE_FILE=$lic bash hpc/hpr_job.sh > $D/job_formal_hook.out 2>&1; rc=$?
echo "JOB_BODY_FORMAL_F1_WITH_HOOK_REFUSED:exit=$rc:$(head -1 $D/job_formal_hook.out | cut -c1-200):started=$( [ -e $D/jobroot2/runs/batch5/F1 ] && echo yes || echo no):runs_created=$(ls $D/jobroot2/runs 2>/dev/null | tr '\n' ' ')" >> $R
env -u GRB_LICENSE_FILE PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.dry JOB_KEY=formal JOB_MODE=formal JOB_RID=F3 JOB_NCPUS=48 JOB_MEM_GB=300 JOB_WALLTIME=260:00:00 PY=$PY JOB_DEPENDS=afterany:F1 \
  HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$D/jobroot3 HPR_AUTH="dry run predecessor check" GRB_LICENSE_FILE=$lic bash hpc/hpr_job.sh > $D/job_formal_pred.out 2>&1; rc=$?
echo "JOB_BODY_FORMAL_F3_PREDECESSOR:exit=$rc:$(tail -1 $D/job_formal_pred.out | cut -c1-200):stop_safe=$(head -c 120 $D/jobroot3/runs/batch5/STOP_SAFE 2>/dev/null):started=$( [ -e $D/jobroot3/runs/batch5/F3 ] && echo yes || echo no):preflight_run=$(grep -c '^PREFLIGHT:' $D/jobroot3/runs/batch5/PBS_JOBS.txt 2>/dev/null):runs_created=$(ls $D/jobroot3/runs 2>/dev/null | tr '\n' ' ')" >> $R
GRB_LICENSE_FILE=$lic bash hpc/hpr_submit.sh --auth-file /nonexistent --motd-checked --dry-run > $D/submit_dry.out 2>&1; rc=$?
echo "SUBMIT_DRY_RUN:exit=$rc:qsub_lines=$(grep -c '^DRY-RUN: qsub' $D/submit_dry.out):notes=$(grep -c '^DRY-RUN NOTE' $D/submit_dry.out):last=$(tail -1 $D/submit_dry.out | cut -c1-160):runs_dir=$( [ -e $D/pkg/runs ] && echo yes || echo no)" >> $R
grep -E "^DRY-RUN" $D/submit_dry.out | cut -c1-220 >> $R
bash hpc/hpr_status.sh > $D/status.out 2>&1; echo "STATUS_DEFAULT_FOLDER:exit=$?:$(head -1 $D/status.out | grep -oE 'runs [^ ]+$')" >> $R
grep -E "unbound|syntax error|command not found" $D/job_formal_hook.out $D/job_formal_pred.out $D/submit_dry.out $D/status.out | head -5 >> $R
echo "DRY:end:$(date -u +%FT%TZ):disk=$(du -sh $D | cut -f1)" >> $R
cat $R
