#!/bin/bash
# W14 section 3.2 (no solver, no licence; truncated networks): dry run of the package in an UNPACKED COPY (tar of the package folder -> extracted into a fresh
# folder -> sha256sum -c), with the shell BASH_BIN (default bash; Atlas bash 4.2: BASH_BIN=/home/jin/v3h/bash42/src/bash). The v3.1 dry run (dry_hpc31.sh)
# adapted to the v4 pair: preflight sections guards,sha,networks (incl. the v4 metadata check),env,profile,code,tools -> BUILD_ONLY with TRUNCATE=56 over
# F1, F2 (process 1 only) -> the job body in build_only mode for F1 (local drill switches, HPR_DRY_TRUNCATE=56) -> job bodies that must start nothing:
# formal F1 with a test hook (refused, exit 2), formal F2 without the authorisation text (refused, exit 2), the batch job before the runs ended (not_ready,
# exit 2) -> hpc/hpr_submit.sh --dry-run (DRY_RUN_OK; order F1 -> F2 after:F1 -> batch afterany:F1:F2) -> hpr_status.sh default folder (runs/batch6).
# The formal job body is never run without a refusal path (the package limits are REGISTERED: a clean formal F1 would start a real build and solve).
# usage: w14_dry.sh <package dir>; writes /home/jin/v4w14/dry_<stamp>/ (never reused) and DRY_RUN_HPC.txt there; never under work/
set -u
SRC=${1:?package dir}; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; BB=${BASH_BIN:-bash}
export PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
D=/home/jin/v4w14/dry_$(date -u +%Y%m%dT%H%M%SZ); [ ! -e "$D" ] || exit 2; mkdir -p "$D"; R=$D/DRY_RUN_HPC.txt
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest')" = 0 ] || { echo "REFUSED: a solve or pytest is running"; exit 4; }
mkdir -p "$D/shim"; ln -s "$(command -v "$BB")" "$D/shim/bash"; export PATH="$D/shim:$PATH"   # every nested "bash ..." of the package runs under BASH_BIN too
( cd "$(dirname "$SRC")" && tar cf "$D/pkg.tar" "$(basename "$SRC")" ) && mkdir "$D/x" && tar xf "$D/pkg.tar" -C "$D/x" && mv "$D/x/$(basename "$SRC")" "$D/pkg" && rm -rf "$D/x" "$D/pkg.tar"
cd "$D/pkg" || exit 2
echo "DRY:start:$(date -u +%FT%TZ):package=$SRC:commit=$(cat COMMIT):shell=$(bash --version | head -1)" > $R
echo "UNPACKED_COPY_SHA256SUMS:not_ok=$(sha256sum -c SHA256SUMS 2>/dev/null | grep -vc ': OK$'):files=$(wc -l < SHA256SUMS):count=$(find . -type f | wc -l)" >> $R
env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools bash preflight.sh > $D/preflight.txt 2>&1; echo "PREFLIGHT:exit=$?:$(tail -1 $D/preflight.txt)" >> $R
grep -E "files OK|limits of the package|all_equal|v4 network metadata|^F[12] |ENV|FAILED|DIFFER|MISSING|unbound|syntax error|NOTE" $D/preflight.txt | head -20 >> $R
lic=$D/fake_lic; echo "placeholder" > $lic; chmod 600 $lic   # a placeholder path for the existence / mode checks only (never a licence)
GRB_LICENSE_FILE=$lic PY=$PY bash hpc/hpr_preflight_login.sh > $D/login_preflight.txt 2>&1; echo "LOGIN_PREFLIGHT:exit=$?:$(tail -1 $D/login_preflight.txt)" >> $R
grep -E "licence file|files OK|key packages|limits of the package|v4 network metadata|_unsolved.nc: switch|PREFLIGHT OK|PREFLIGHT FAILED|HPR_PREFLIGHT_LOGIN" $D/login_preflight.txt | cut -c1-260 >> $R
T0=$(date +%s)
env -u GRB_LICENSE_FILE PY=$PY BUILD_ONLY=1 TRUNCATE=56 ALLOW_UNREGISTERED=1 RUN_DIR=$D/runs/build_only_all bash run_batch4.sh > $D/build_only.out 2>&1; rc=$?
echo "BUILD_ONLY_ALL:exit=$rc:$(( $(date +%s) - T0 ))s" >> $R
grep -E "BASE_CHECK|BUILD_CHECK_|BUILD_F[12]|STOP|REFUSED|DONE" $D/runs/build_only_all/STATUS.txt | cut -c1-300 >> $R
for f in $D/runs/build_only_all/F*/SOLVE_RECEIPT.json; do "$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); lp=r.get('lp',{}); print('LP:'+sys.argv[1].split('/')[-2]+':rows='+str(lp.get('num_row'))+':cols='+str(lp.get('num_col'))+':nnz='+str(lp.get('nnz'))+':package_commit='+str(r.get('package_commit')))" "$f" >> $R 2>/dev/null; done
for f in $D/runs/build_only_all/F*/RUN.json; do "$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print('RUN_JSON:'+r['rid']+':package_commit='+str(r.get('package_commit'))+':repo_commit='+str(r.get('repo_commit'))+':iterations_reference='+str(r.get('iterations_reference'))+':time_limit='+str(r.get('time_limit')))" "$f" >> $R 2>/dev/null; done
grep -E "unbound|syntax error|command not found" $D/build_only.out | head -5 >> $R
T0=$(date +%s)
env -u GRB_LICENSE_FILE PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.dry JOB_KEY=build_only_f1 JOB_MODE=build_only JOB_RID=F1 JOB_NCPUS=16 JOB_MEM_GB=10 JOB_WALLTIME=03:00:00 PY=$PY \
  HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$D/jobroot HPR_DRY_TRUNCATE=56 bash hpc/hpr_job.sh > $D/job_build_only.out 2>&1; rc=$?
echo "JOB_BODY_BUILD_ONLY_F1:exit=$rc:$(( $(date +%s) - T0 ))s:run_dir=$(ls -d $D/jobroot/runs/* 2>/dev/null | xargs -n1 basename | tr '\n' ' ')" >> $R
cat $D/jobroot/runs/build_only_f1_v4/BUILD_ONLY_STATUS.txt 2>/dev/null | cut -c1-200 >> $R
grep -E "unbound|syntax error|command not found" $D/job_build_only.out | head -5 >> $R
env -u GRB_LICENSE_FILE PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.dry JOB_KEY=F1 JOB_MODE=formal JOB_RID=F1 JOB_NCPUS=48 JOB_MEM_GB=300 JOB_WALLTIME=96:00:00 PY=$PY BUILD_ONLY=1 \
  HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$D/jobroot2 HPR_AUTH="dry run refusal check" GRB_LICENSE_FILE=$lic bash hpc/hpr_job.sh > $D/job_formal_hook.out 2>&1; rc=$?
echo "JOB_BODY_FORMAL_F1_WITH_HOOK_REFUSED:exit=$rc:$(head -1 $D/job_formal_hook.out | cut -c1-200):started=$( [ -e $D/jobroot2/runs/batch6/F1 ] && echo yes || echo no):runs_created=$(ls $D/jobroot2/runs 2>/dev/null | tr '\n' ' ')" >> $R
env -u GRB_LICENSE_FILE PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.dry JOB_KEY=F2 JOB_MODE=formal JOB_RID=F2 JOB_NCPUS=48 JOB_MEM_GB=250 JOB_WALLTIME=96:00:00 JOB_WAIT_START_OF=F1 JOB_DEPENDS=after:F1 PY=$PY \
  HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$D/jobroot3 GRB_LICENSE_FILE=$lic bash hpc/hpr_job.sh > $D/job_formal_noauth.out 2>&1; rc=$?
echo "JOB_BODY_FORMAL_F2_NO_AUTH_REFUSED:exit=$rc:$(head -1 $D/job_formal_noauth.out | cut -c1-200):started=$( [ -e $D/jobroot3/runs/batch6/F2 ] && echo yes || echo no)" >> $R
env -u GRB_LICENSE_FILE PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.dry JOB_KEY=batch JOB_MODE=batch JOB_RID=batch JOB_NCPUS=12 JOB_MEM_GB=120 JOB_WALLTIME=48:00:00 JOB_DEPENDS=afterany:F1:F2 PY=$PY \
  HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$D/jobroot4 bash hpc/hpr_job.sh > $D/job_batch_notready.out 2>&1; rc=$?
echo "JOB_BODY_BATCH_NOT_READY_REFUSED:exit=$rc:$(head -1 $D/job_batch_notready.out | cut -c1-200)" >> $R
GRB_LICENSE_FILE=$lic bash hpc/hpr_submit.sh --auth-file /nonexistent --motd-checked --dry-run > $D/submit_dry.out 2>&1; rc=$?
echo "SUBMIT_DRY_RUN:exit=$rc:qsub_lines=$(grep -c '^DRY-RUN: qsub' $D/submit_dry.out):notes=$(grep -c '^DRY-RUN NOTE' $D/submit_dry.out):last=$(tail -1 $D/submit_dry.out | cut -c1-160):runs_dir=$( [ -e $D/pkg/runs ] && echo yes || echo no)" >> $R
grep -E "^DRY-RUN" $D/submit_dry.out | cut -c1-240 >> $R
bash hpc/hpr_status.sh > $D/status.out 2>&1; echo "STATUS_DEFAULT_FOLDER:exit=$?:$(head -1 $D/status.out | grep -oE 'runs [^ ]+$')" >> $R
grep -E "unbound|syntax error|command not found" $D/job_formal_hook.out $D/job_formal_noauth.out $D/job_batch_notready.out $D/submit_dry.out $D/status.out | head -5 >> $R
echo "DRY:end:$(date -u +%FT%TZ):disk=$(du -sh $D | cut -f1)" >> $R
cat $R
