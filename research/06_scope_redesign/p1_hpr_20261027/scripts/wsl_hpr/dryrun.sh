#!/bin/bash
# HPR H5.3 local dry run on the BUILT package v9 (a copy, so that the dist folder stays as packaged): (1) the in-package preflight sections (resources and
# licence fail / are not run on this machine: expected), (2) the truncated-56 BUILD_ONLY through the generated build-only job script as bash
# (HPR_DRY_TRUNCATE=56: process 1 only, no Gurobi), (3) the refusals of the formal command and job body with test switches left over, an unregistered
# network and a TimeLimit differing from the registration - every one must exit non-zero without writing a STATUS.txt. No solve anywhere.
#   bash /home/jin/hpr/dryrun.sh <dist dir>
set -u
DIST=${1:?dist dir}; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/home/jin/hpr_dry; PKG=$D/pkg; O=$MAIN/results_project/hpr/dry_run_v9; mkdir -p "$O"; S=$O/DRYRUN_STATUS.txt
export PYTHONHASHSEED=0
log() { echo "$*" | tee -a "$S"; }
rm -rf "$D"; mkdir -p "$D"; cp -r "$DIST" "$PKG"; chmod 755 "$PKG"/*.sh "$PKG"/hpc/*.sh "$PKG"/pbs/*.pbs "$PKG"/env/install_env.sh
log "START:$(date -u +%FT%TZ):dist=$DIST:pkg=$PKG:commit=$(cat "$PKG/COMMIT")"
# 1. preflight sections one by one (the sha section unpacks the code archive to ./repo)
cd "$PKG"
for sec in guards sha networks env profile code tools resources; do
  PREFLIGHT_ONLY=$sec PY=$PY env -u GRB_LICENSE_FILE bash preflight.sh > "$O/preflight_$sec.txt" 2>&1; rc=$?
  log "PREFLIGHT_$sec:exit=$rc:$(tail -1 "$O/preflight_$sec.txt" | cut -c1-160)"
done
log "PREFLIGHT_licence:not_run (a Gurobi call; the local budget is for the H4 drill only)"
PY=$PY bash hpc/hpr_preflight_login.sh > "$O/preflight_login.txt" 2>&1; log "PREFLIGHT_LOGIN:exit=$?:$(tail -1 "$O/preflight_login.txt" | cut -c1-160) (licence file / PBS absent here: expected)"
# 2. truncated-56 BUILD_ONLY through the generated job script as bash (simulated PBS variables; HPR_DRY_TRUNCATE=56 -> TRUNCATE=56 ALLOW_UNREGISTERED=1 BUILD_ONLY=1 run_batch4.sh --only F1)
t0=$(date +%s)
( export PBS_O_WORKDIR=$PKG PBS_JOBID=local.dryrun NCPUS=48 HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$O HPR_DRY_TRUNCATE=56 PY=$PY; bash pbs/hpr_build_only_f1.pbs > "$O/build_only_job.out" 2>&1 ); rc=$?
log "BUILD_ONLY_56:exit=$rc:seconds=$(( $(date +%s) - t0 )):$(grep -h "^BUILD_CHECK_F1:" "$O/runs/build_only_f1/STATUS.txt" 2>/dev/null | cut -c1-200)"
cat "$O/runs/build_only_f1/BUILD_ONLY_STATUS.txt" 2>/dev/null | tee -a "$S"
[ -f "$O/runs/build_only_f1/F1/gurobi.linopy.log" ] && log "UNEXPECTED: a solver log exists" || log "NO_SOLVER_LOG:ok"
# 3. refusals (exit != 0, no STATUS.txt): the formal runner command and the formal job body with leftovers / unregistered values; an unregistered network
R=$O/refusals; rm -rf "$R"; mkdir -p "$R"; : > "$O/REFUSALS.txt"
refuse() {   # $1 tag; rest = command (run in $PKG with a clean env + the given assignments)
  local tag=$1; shift; local rd="$R/$tag"; mkdir -p "$rd"
  ( cd "$PKG" && env -i HOME="$HOME" PATH="$PATH" USER="$USER" PY=$PY "$@" ) > "$rd/out.txt" 2>&1; local rc=$?
  local st="absent"; [ -f "$rd/runs/batch4/STATUS.txt" ] || [ -f "$PKG/runs/batch4/STATUS.txt" ] && st="WRITTEN"
  echo "$tag|exit=$rc|status=$st|$(head -c 200 "$rd/out.txt" | tr '\n' ' ')" | tee -a "$O/REFUSALS.txt"
}
LICF=$D/fake_lic; echo "placeholder" > "$LICF"; chmod 600 "$LICF"
refuse R01_runner_build_only_with_auth env BUILD_ONLY=1 RUN_DIR=$R/R01/runs/batch4 REPO=$PKG/repo bash run_batch4.sh --only F1 --auth x
refuse R02_runner_split_cmd_hook env SPLIT_CMD="python x" GRB_LICENSE_FILE=$LICF RUN_DIR=$R/R02/runs/batch4 REPO=$PKG/repo bash run_batch4.sh --only F1 --auth x
refuse R03_runner_truncate_formal env TRUNCATE=56 GRB_LICENSE_FILE=$LICF RUN_DIR=$R/R03/runs/batch4 REPO=$PKG/repo bash run_batch4.sh --only F1 --auth x
refuse R04_runner_old_timelimit env GUROBI_TIME_LIMIT_S=259200 GRB_LICENSE_FILE=$LICF RUN_DIR=$R/R04/runs/batch4 REPO=$PKG/repo bash run_batch4.sh --only F1 --auth x
refuse R05_runner_wall_cap env WALL_CAP_S=266400 GRB_LICENSE_FILE=$LICF RUN_DIR=$R/R05/runs/batch4 REPO=$PKG/repo bash run_batch4.sh --only F1 --auth x
refuse R06_runner_single_mode env SOLVE_MODE=single GRB_LICENSE_FILE=$LICF RUN_DIR=$R/R06/runs/batch4 REPO=$PKG/repo bash run_batch4.sh --only F1 --auth x
refuse R07_runner_fake_hook env FAKE_SLEEP_F1=9 GRB_LICENSE_FILE=$LICF RUN_DIR=$R/R07/runs/batch4 REPO=$PKG/repo bash run_batch4.sh --only F1 --auth x
refuse R08_runner_post_only_with_only env POST_ONLY=1 RUN_DIR=$R/R08/runs/batch4 REPO=$PKG/repo bash run_batch4.sh --only F1
refuse R09_runner_no_auth env GRB_LICENSE_FILE=$LICF RUN_DIR=$R/R09/runs/batch4 REPO=$PKG/repo bash run_batch4.sh --only F1
refuse R10_job_formal_build_only_leftover env PBS_O_WORKDIR=$PKG PBS_JOBID=1.venus JOB_MODE=formal JOB_RID=F1 JOB_NCPUS=48 JOB_MEM_GB=300 HPR_AUTH=x GRB_LICENSE_FILE=$LICF BUILD_ONLY=1 bash hpc/hpr_job.sh
refuse R11_job_formal_truncate_leftover env PBS_O_WORKDIR=$PKG PBS_JOBID=1.venus JOB_MODE=formal JOB_RID=F1 JOB_NCPUS=48 JOB_MEM_GB=300 HPR_AUTH=x GRB_LICENSE_FILE=$LICF TRUNCATE=56 bash hpc/hpr_job.sh
refuse R12_job_formal_no_auth env PBS_O_WORKDIR=$PKG PBS_JOBID=1.venus JOB_MODE=formal JOB_RID=F1 JOB_NCPUS=48 JOB_MEM_GB=300 GRB_LICENSE_FILE=$LICF bash hpc/hpr_job.sh
refuse R13_job_formal_no_licence env PBS_O_WORKDIR=$PKG PBS_JOBID=1.venus JOB_MODE=formal JOB_RID=F1 JOB_NCPUS=48 JOB_MEM_GB=300 HPR_AUTH=x GRB_LICENSE_FILE=$D/none bash hpc/hpr_job.sh
refuse R14_job_formal_local_drill_switch env PBS_O_WORKDIR=$PKG PBS_JOBID=1.venus JOB_MODE=formal JOB_RID=F1 JOB_NCPUS=48 JOB_MEM_GB=300 HPR_AUTH=x GRB_LICENSE_FILE=$LICF HPR_LOCAL_DRILL=1 bash hpc/hpr_job.sh
refuse R15_job_batch_not_ready env PBS_O_WORKDIR=$PKG PBS_JOBID=1.venus JOB_MODE=batch JOB_RID=batch JOB_NCPUS=12 JOB_MEM_GB=120 bash hpc/hpr_job.sh
# an unregistered network (a byte appended to a COPY of the package): the in-job preflight networks section / base-check refuses; the runner's phase 0 would STOP_SAFE
cp -r "$PKG" "$D/pkg_badnet"; printf 'x' >> "$D/pkg_badnet/networks/integrated_2920_3h_unsolved.nc"
( cd "$D/pkg_badnet" && PREFLIGHT_ONLY=networks PY=$PY env -u GRB_LICENSE_FILE bash preflight.sh > "$R/R16_preflight_badnet.txt" 2>&1 ); echo "R16_preflight_unregistered_network|exit=$?|status=absent|$(tail -1 "$R/R16_preflight_badnet.txt" | cut -c1-160)" | tee -a "$O/REFUSALS.txt"
( cd "$D/pkg_badnet" && env -i HOME="$HOME" PATH="$PATH" USER="$USER" PY=$PY PBS_O_WORKDIR=$D/pkg_badnet PBS_JOBID=1.venus JOB_MODE=formal JOB_RID=F1 JOB_NCPUS=48 JOB_MEM_GB=300 HPR_AUTH=x GRB_LICENSE_FILE=$LICF bash hpc/hpr_job.sh > "$R/R17_job_badnet.txt" 2>&1 ); rc=$?
st=absent; [ -f "$D/pkg_badnet/runs/batch4/STATUS.txt" ] && st=WRITTEN; echo "R17_job_formal_unregistered_network|exit=$rc|status=$st|$(tail -2 "$D/pkg_badnet/runs/batch4/PBS_JOBS.txt" 2>/dev/null | tr '\n' ' ' | cut -c1-200)" | tee -a "$O/REFUSALS.txt"
# the submit script refusals (no qsub here; the checks before qsub)
( cd "$PKG" && env -i HOME="$HOME" PATH="$PATH" USER="$USER" bash hpc/hpr_submit.sh --auth-file HPR_AUTH_missing.txt > "$R/R18.txt" 2>&1 ); echo "R18_submit_no_motd|exit=$?|status=absent|$(head -c 160 "$R/R18.txt")" | tee -a "$O/REFUSALS.txt"
echo "auth" > "$D/auth.txt"
( cd "$PKG" && env -i HOME="$HOME" PATH="$PATH" USER="$USER" bash hpc/hpr_submit.sh --auth-file "$D/auth.txt" --motd-checked > "$R/R19.txt" 2>&1 ); echo "R19_submit_smoke_not_passed|exit=$?|status=absent|$(head -c 160 "$R/R19.txt")" | tee -a "$O/REFUSALS.txt"
( cd "$PKG" && env -i HOME="$HOME" PATH="$PATH" USER="$USER" BUILD_ONLY=1 bash hpc/hpr_submit.sh --auth-file "$D/auth.txt" --motd-checked > "$R/R20.txt" 2>&1 ); echo "R20_submit_hook_in_shell|exit=$?|status=absent|$(head -c 160 "$R/R20.txt")" | tee -a "$O/REFUSALS.txt"
rm -f "$PKG/HPR_AUTH.txt"
log "REFUSALS:$(wc -l < "$O/REFUSALS.txt") cases:nonzero=$(grep -vc 'exit=0|' "$O/REFUSALS.txt"):status_written=$(grep -c 'status=WRITTEN' "$O/REFUSALS.txt")"
log "DONE:$(date -u +%FT%TZ)"
