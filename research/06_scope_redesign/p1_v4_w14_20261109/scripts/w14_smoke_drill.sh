#!/bin/bash
# W14 section 3.2: local drill of the HPC smoke job in an UNPACKED COPY of the package (tar -> extract into a fresh folder outside work/ -> sha256sum -c):
# the generated job script pbs/hpr4_smoke56.pbs is run AS IS with bash (its #PBS lines are comments): the three job bodies F1, F2, batch with TRUNCATE=56,
# formal_barrier_1e6_t16, TimeLimit 3,000 s / wall cap 3,600 s, run folder runs/smoke56_v4; only the local drill switches are added (HPR_LOCAL_DRILL=1: no token-server
# HTTP request from the job, no resources section; PBS_JOBID=local.smoke; PBS_O_WORKDIR = the copy). These are the 2 authorised solves of the instruction (W14 section 0 /
# 3.2: "本机至多 2 次 56 时段求解；用户启动本指令即授权"): serial (the runner keeps >= 330 s between the two Gurobi sessions), at most one Gurobi process on this machine,
# no retry, no parameter change. Before the job: a bare TCP connect to the token server (no data, no licence), the licence file's existence and mode only (never read).
# After the job: SMOKE_STATUS.txt and a second hpr_submit.sh --dry-run in the copy with an authorisation file and a placeholder licence path (mode 600) - expected:
# no DRY-RUN NOTE at all (the guide's step c3).
# usage: w14_smoke_drill.sh <package dir> --confirmed <utc time>; writes /home/jin/v4w14/smoke_<stamp>/
set -u
SRC=${1:?package dir}; [ "${2:-}" = "--confirmed" ] || { echo "REFUSED: needs --confirmed <time>"; exit 5; }; WHEN=${3:?time}
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; LIC=/home/jin/gurobi.lic
export PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
D=/home/jin/v4w14/smoke_$(date -u +%Y%m%dT%H%M%SZ); [ ! -e "$D" ] || exit 2; mkdir -p "$D"; R=$D/SMOKE_DRILL.txt
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl|[b]4_split_solve\.py|[s]2_network\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
[ "$(busy)" = 0 ] || { echo "REFUSED: a solve or build is running"; exit 4; }
[ "$(ps -eo args= | grep -c '[p]ytest')" = 0 ] || { echo "REFUSED: pytest running"; exit 4; }
[ -f "$LIC" ] && [ "$(stat -c %a "$LIC")" = 600 ] || { echo "REFUSED: licence file missing or not mode 600 (existence and mode only)"; exit 3; }
timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null || { echo "REFUSED: no TCP route to the token server from WSL (AnyConnect?) - nothing started"; exit 6; }
( cd "$(dirname "$SRC")" && tar cf "$D/pkg.tar" "$(basename "$SRC")" ) && mkdir "$D/x" && tar xf "$D/pkg.tar" -C "$D/x" && mv "$D/x/$(basename "$SRC")" "$D/pkg" && rm -rf "$D/x" "$D/pkg.tar"
cd "$D/pkg" || exit 2
echo "SMOKE_DRILL:start:$(date -u +%FT%TZ):package=$SRC:commit=$(cat COMMIT):unpacked_copy_not_ok=$(sha256sum -c SHA256SUMS 2>/dev/null | grep -vc ': OK$'):files=$(wc -l < SHA256SUMS)" > $R
AUTH="V4 W14 section 3.2 local drill of the HPC smoke job (V4_W14_INSTRUCTION.md SHA 6cb103db; 2 local 56-snapshot solves authorised by starting the instruction; $WHEN)"
T0=$(date +%s)
env PBS_O_WORKDIR=$D/pkg PBS_JOBID=local.smoke PY=$PY HPR_LOCAL_DRILL=1 HPR_AUTH="$AUTH" GRB_LICENSE_FILE=$LIC bash pbs/hpr4_smoke56.pbs > $D/smoke_job.out 2>&1; rc=$?
echo "SMOKE_JOB:exit=$rc:$(( $(date +%s) - T0 ))s" >> $R
cat runs/smoke56_v4/SMOKE_STATUS.txt >> $R 2>/dev/null
grep -E "^(START|BASE_CHECK|PREPARE|BUILD|SOLVE|GAP|WAIT|END|POST|C1|M12|OWEN|V6|STOP|HALTED|DONE|POSTPROC_ERROR|REFERENCE|PACK|START_LOCK)" runs/smoke56_v4/STATUS.txt | cut -c1-260 >> $R
grep -E "^(JOB_START|PREFLIGHT|RUNNER|JOB_END|WLS)" runs/smoke56_v4/PBS_JOBS.txt | cut -c1-260 >> $R
grep -h "PREFLIGHT OK\|PREFLIGHT FAILED\|v4 network metadata" runs/smoke56_v4/preflight_*.txt >> $R
grep -E "unbound|syntax error|command not found" $D/smoke_job.out | head -5 >> $R
printf '%s\n' "local drill authorisation placeholder for the dry-run check" > $D/auth.txt
fake=$D/fake_lic; echo "placeholder" > $fake; chmod 600 $fake
GRB_LICENSE_FILE=$fake bash hpc/hpr_submit.sh --auth-file $D/auth.txt --motd-checked --dry-run > $D/submit_dry_after.out 2>&1; rc=$?
echo "SUBMIT_DRY_RUN_AFTER_SMOKE:exit=$rc:qsub_lines=$(grep -c '^DRY-RUN: qsub' $D/submit_dry_after.out):notes=$(grep -c '^DRY-RUN NOTE' $D/submit_dry_after.out):last=$(tail -1 $D/submit_dry_after.out | cut -c1-160)" >> $R
grep -E "^DRY-RUN" $D/submit_dry_after.out | cut -c1-240 >> $R
bash hpc/hpr_status.sh runs/smoke56_v4 > $D/status_smoke.out 2>&1; echo "STATUS_SMOKE:exit=$?" >> $R; grep -E "objective incl|phase|ended" $D/status_smoke.out | cut -c1-260 >> $R
echo "SMOKE_DRILL:end:$(date -u +%FT%TZ):disk=$(du -sh $D | cut -f1)" >> $R
cat $R
