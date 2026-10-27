#!/bin/bash
# HPR PBS job body (RUN_PLAN_HPC.md): ONE code path for the formal runs, the batch-level job and the test jobs - every mode calls the fourth-batch
# runner run_batch4.sh (B4P, HPR amendments) and never anything else:
#   JOB_MODE=formal      JOB_RID=F1|F2   run_batch4.sh --only <rid> --auth "<text>"       (RUN_PLAN_HPC 1-7; F2 with WAIT_START_OF=F1)
#   JOB_MODE=batch                       POST_ONLY=1 run_batch4.sh                        (batch-level: reference, regrade, B6, Owen, summary, packs)
#   JOB_MODE=smoke56     JOB_RID=F1|F2|batch   the same two commands with TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600
#                                        (label SMOKE_TEST_ONLY; RUN_PLAN_HPC 9; the local H4 drill runs exactly this as bash)
#   JOB_MODE=build_only  JOB_RID=F1      BUILD_ONLY=1 run_batch4.sh --only F1 (process 1 only, no licence; RUN_PLAN_HPC 9 / user step D2), then the
#                                        build metrics, a 1 GiB write-speed test on scratch and the deletion of the LP file
# Reads: JOB_* (exported by the generated .pbs), PBS_O_WORKDIR = the package folder, PBS_JOBID / NCPUS (PBS), HPR_AUTH (environment) or
# <package>/HPR_AUTH.txt (written by hpr_submit.sh; solve modes only). Writes <runs>/PBS_JOBS.txt (node, CPU model, resources, cgroup path and
# limit, memory measure, exit codes) and the mode's status file. Refusals (exit 2, nothing started, no STATUS.txt written): a test hook / dry-run
# switch in the environment of a formal job, a missing authorisation, a run folder holding test leftovers (build_only / SMOKE_TEST_ONLY), a licence
# file missing or not mode 600, a batch job before both runs ended (not_ready). Local drill: HPR_LOCAL_DRILL=1 (skips the token-server curl;
# HPR_RUN_ROOT=<dir> puts runs/ elsewhere; HPR_DRY_TRUNCATE=56 for the truncated BUILD_ONLY dry run) - refused under a real PBS job.
set -u
JOB_MODE=${JOB_MODE:?formal|batch|smoke56|build_only}; JOB_RID=${JOB_RID:-}; JOB_KEY=${JOB_KEY:-$JOB_MODE}
PKG=${PBS_O_WORKDIR:?run under PBS (qsub) - or set PBS_O_WORKDIR for the local drill}; cd "$PKG" || exit 2
JOBID=${PBS_JOBID:-local}; PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}
RUNS_ROOT=${HPR_RUN_ROOT:-$PKG}
# local drill / stand-in switches (HPR_LOCAL_DRILL=1, HPR_RUN_ROOT, HPR_DRY_TRUNCATE, HPR_TEST_STANDIN=1): never under a real PBS job id (a real id is
# "<number>.<server>"; the drill simulates PBS_JOBID=local...); hpr_submit.sh refuses them in the submitting shell as well
if [ -n "${PBS_JOBID:-}" ] && [ "${PBS_JOBID#local}" = "${PBS_JOBID}" ]; then
  for k in HPR_LOCAL_DRILL HPR_RUN_ROOT HPR_DRY_TRUNCATE HPR_TEST_STANDIN HPR_TEST_PREFLIGHT_SECTIONS HPR_PROC_CGROUP_FILE HPR_CGROUP_FS; do [ -z "${!k:-}" ] || { echo "REFUSED: $k is a local-drill / test switch (not under a real PBS job)"; exit 2; }; done
fi
if [ -n "${HPR_TEST_STANDIN:-}" ] && [ -z "${HPR_LOCAL_DRILL:-}" ]; then echo "REFUSED: HPR_TEST_STANDIN needs HPR_LOCAL_DRILL=1"; exit 2; fi
case "$JOB_MODE" in formal|batch|smoke56|build_only) ;; *) echo "REFUSED: JOB_MODE=$JOB_MODE (formal | batch | smoke56 | build_only)"; exit 2;; esac
# the job environment must carry none of the runner's hooks / overrides (checked BEFORE this body sets its own RUN_DIR / CORES / ... below)
HOOKS="ALLOW_UNREGISTERED BUILD_ONLY POST_ONLY DRY TRUNCATE SOLVE_CMD SPLIT_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD LEDGER_CMD WALL_CAP_S GUROBI_TIME_LIMIT_S LICENCE_GAP_S GRACE_S MONITOR_S POST_TIMEOUT_S PACK_TIMEOUT_S SOLVE_MODE P1_WINDOW_S P1_THRESHOLD P1_MIN_CORES MEMORY_STOP_FRACTION PROJECTION_FRACTION BUILD_TIMEOUT_S ASSIGN_TIMEOUT_S POST_MEM_NEED_GIB WAIT_START_MAX_S MEM_MEASURE CGROUP_ROOT RUN_DIR CORES MEM_QUOTA_GIB WAIT_START_OF REPO NETS"
bad=""; for k in $HOOKS $(compgen -A variable | grep -E '^FAKE_'); do [ -z "${!k:-}" ] || bad="$bad $k"; done
if [ -n "$bad" ] && [ -z "${HPR_TEST_STANDIN:-}" ]; then echo "REFUSED: test hook / dry-run switch / runner override set in the job environment:$bad (every value comes from the job script and this body)"; exit 2; fi
case "$JOB_MODE" in
  formal|batch) RUN_DIR=$RUNS_ROOT/runs/batch4;;
  smoke56) RUN_DIR=$RUNS_ROOT/runs/smoke56;;
  build_only) RUN_DIR=$RUNS_ROOT/runs/build_only_f1;;
esac
# ---- authorisation text (solve modes): environment, else <package>/HPR_AUTH.txt
AUTH=${HPR_AUTH:-}; [ -n "$AUTH" ] || { [ -f "$PKG/HPR_AUTH.txt" ] && AUTH=$(cat "$PKG/HPR_AUTH.txt"); }
case "$JOB_MODE" in
  formal)
    case "$JOB_RID" in F1|F2) ;; *) echo "REFUSED: JOB_RID=$JOB_RID (F1 | F2)"; exit 2;; esac
    [ -n "$AUTH" ] || { echo "REFUSED: the user authorisation text is missing (HPR_AUTH or $PKG/HPR_AUTH.txt)"; exit 2; }
    for d in "$RUN_DIR"/F1 "$RUN_DIR"/F2; do
      [ -d "$d" ] || continue
      c=$(cat "$d/.cond" 2>/dev/null); case "$c" in build_only|split_built|stopped_before_solve) echo "REFUSED: $d holds a dry-run leftover (.cond=$c) - the formal RUN_DIR must be fresh (runs/batch4)"; exit 2;; esac
      [ -f "$d/RUN.json" ] && grep -q '"label": "SMOKE_TEST_ONLY"' "$d/RUN.json" && { echo "REFUSED: $d holds a smoke leftover (label SMOKE_TEST_ONLY)"; exit 2; }
      [ -f "$d/RUN.json" ] && grep -Eq '"truncate": [0-9]' "$d/RUN.json" && { echo "REFUSED: $d holds a truncated run"; exit 2; }
    done;;
  batch)
    for rid in F1 F2; do [ -f "$RUN_DIR/$rid/.ended" ] || { echo "REFUSED: not_ready - $RUN_DIR/$rid has not ended (the batch job runs after BOTH F1 and F2; depend=afterany)"; exit 2; }; done;;
  smoke56)
    case "$JOB_RID" in F1|F2|batch) ;; *) echo "REFUSED: JOB_RID=$JOB_RID (F1 | F2 | batch)"; exit 2;; esac
    [ "$JOB_RID" = batch ] || [ -n "$AUTH" ] || { echo "REFUSED: the user authorisation text is missing (HPR_AUTH or $PKG/HPR_AUTH.txt)"; exit 2; };;
  build_only)
    case "$JOB_RID" in F1|F2) ;; *) echo "REFUSED: JOB_RID=$JOB_RID (F1 | F2)"; exit 2;; esac;;
esac
# ---- licence file: existence and mode only (never read); the formal / smoke solve modes need it, build_only and batch do not use it
export GRB_LICENSE_FILE=${GRB_LICENSE_FILE:-$HOME/.gurobi/gurobi.lic}
case "$JOB_MODE:$JOB_RID" in
  formal:*|smoke56:F1|smoke56:F2)
    [ -f "$GRB_LICENSE_FILE" ] && [ "$(stat -c %a "$GRB_LICENSE_FILE")" = 600 ] || { echo "REFUSED: licence file missing or not mode 600 at $GRB_LICENSE_FILE (existence and mode checked only)"; exit 2; };;
esac
# ---- records (RUN_PLAN_HPC H3.3): node, CPU model, requested resources, the job cgroup and its memory limit / accounting
mkdir -p "$RUN_DIR" || exit 2; J="$RUN_DIR/PBS_JOBS.txt"; T0=$(date +%s)
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }; rec() { echo "$*" >> "$J"; }
job_cgroup() {   # prints "<v2|v1|none>|<memory accounting dir>" for THIS process. Only a cgroup whose path carries THIS job's id (PBS Pro cgroup hook: v1
  # /pbspro/<jobid>, v2 /pbs_jobs.service/jobid/<jobid>) is the job's own; the root cgroup, a service cgroup shared by every job of the node (e.g. the
  # MoM's when the hook is off) or an unrelated scope (local drill: /init.scope) would count other processes -> none -> the process-group RSS measure
  local f=${HPR_PROC_CGROUP_FILE:-/proc/self/cgroup} fs=${HPR_CGROUP_FS:-/sys/fs/cgroup} jid=${PBS_JOBID:-local} line path dir
  local jnum=${jid%%.*}
  is_job_path() { [ -n "$1" ] && [ "$1" != / ] && { case "$1" in *"$jid"*|*"/$jnum"|*"/$jnum."*|*"/$jnum/"*) return 0;; esac; }; return 1; }
  line=$(grep -E '^0::' "$f" 2>/dev/null | head -1)
  if [ -n "$line" ]; then path=${line#0::}; path=${path%% *}; dir="$fs${path}"; is_job_path "$path" && [ -r "$dir/memory.stat" ] && { echo "v2|$dir"; return; }; fi
  line=$(grep -E '^[0-9]+:[^:]*\bmemory\b[^:]*:' "$f" 2>/dev/null | head -1)
  if [ -n "$line" ]; then path=${line##*:}; dir="$fs/memory${path}"; is_job_path "$path" && [ -r "$dir/memory.stat" ] && { echo "v1|$dir"; return; }; fi
  echo "none|"
}
IFS='|' read -r CGV CGDIR < <(job_cgroup)
CGLIM=""; CGKEY=none
if [ "$CGV" != none ]; then
  for f in "$CGDIR/memory.max" "$CGDIR/memory.limit_in_bytes"; do [ -r "$f" ] && { CGLIM=$(cat "$f"); break; }; done
  CGKEY=$(awk '$1 == "anon" {a=1} $1 == "total_rss" {t=1} $1 == "rss" {r=1} END {if (a) print "anon"; else if (t) print "total_rss"; else if (r) print "rss"; else print "nokey"}' "$CGDIR/memory.stat")
fi
if [ "$CGV" != none ] && [ "$CGKEY" != nokey ]; then export CGROUP_ROOT="$CGDIR" MEM_MEASURE=cgroup; else export MEM_MEASURE=rss; fi   # RUN_PLAN_HPC 5: job cgroup anon memory, else the process-group RSS
export CORES=${NCPUS:-${JOB_NCPUS:?}} MEM_QUOTA_GIB=${JOB_MEM_GB:?}
CPU_MODEL=$(lscpu 2>/dev/null | awk -F: '/Model name/ {gsub(/^ +/, "", $2); print $2; exit}')
rec "JOB_START:$JOB_KEY:$JOB_MODE:$JOB_RID:jobid=$JOBID:node=$(hostname):cpu=${CPU_MODEL:-?}:nproc=$(nproc):ncpus=$CORES:mem_gb=$MEM_QUOTA_GIB:walltime=${JOB_WALLTIME:-?}:queue=${JOB_QUEUE:-?}:pbs_o_workdir=$PKG:run_dir=$RUN_DIR:utc=$(now)"
rec "CGROUP:$JOB_KEY:version=$CGV:dir=${CGDIR:-none}:limit=${CGLIM:-none}:anon_key=$CGKEY:mem_measure=$MEM_MEASURE:cgroup_root=${CGROUP_ROOT:-default}:proc_self_cgroup=$(tr '\n' ';' < ${HPR_PROC_CGROUP_FILE:-/proc/self/cgroup} | cut -c1-300)"
rec "DISK:$JOB_KEY:$(df -Pk "$RUNS_ROOT" | awk 'NR==2 {printf "free_gib=%.1f used_pct=%s", $4/1048576, $5}'):tmpdir_pbs=${TMPDIR:-unset}"
# ---- the B4P preflight inside the job (no licence section: that would be a WLS session - RUN_PLAN_HPC 4); the guards section sees the job environment
#      (CGROUP_ROOT / MEM_MEASURE / CORES / MEM_QUOTA_GIB set by this body are listed as operational notes, not as hooks); the resources section is
#      checked against this job's request (cores / 90 % of the memory / 45 GB scratch) and reads the job cgroup when it was found
case "$JOB_MODE" in batch) SECS=guards,sha,networks,env,code,tools,resources;; *) SECS=guards,sha,networks,env,profile,code,tools,resources;; esac
[ -z "${HPR_LOCAL_DRILL:-}" ] || SECS=${SECS%,resources}   # the local machine never meets the HPC floor (recorded as skipped)
[ -z "${HPR_TEST_STANDIN:-}" ] || SECS=${HPR_TEST_PREFLIGHT_SECTIONS:-tools}
NEED_MEM=$(( MEM_QUOTA_GIB * 9 / 10 )); PF="$RUN_DIR/preflight_${JOB_KEY}_${JOB_RID:-x}_${JOBID}.txt"
PREFLIGHT_ONLY=$SECS NEED_CORES=$CORES NEED_MEM_GIB=$NEED_MEM NEED_DISK_GB=45 PREFLIGHT_DISK_PATH="$RUNS_ROOT" PY="$PY" bash "$PKG/preflight.sh" > "$PF" 2>&1; rc=$?
rec "PREFLIGHT:$JOB_KEY:exit=$rc:sections=$SECS:need_cores=$CORES:need_mem_gib=$NEED_MEM:$(tail -1 "$PF")"
[ $rc = 0 ] || { rec "PREFLIGHT_FAILED:$JOB_KEY - job ends, nothing started:utc=$(now)"; exit 1; }
# ---- the runner (RUN_PLAN_HPC 7): REPO / NETS / RUN_DIR / registered split mode / REMOVE_LP; the job cgroup or RSS memory measure
export REPO="$PKG/repo" NETS="$PKG/networks" RUN_DIR PY SOLVE_MODE=split REMOVE_LP=1 PYTHONHASHSEED=0
[ -z "${JOB_WAIT_START_OF:-}" ] || export WAIT_START_OF="$JOB_WAIT_START_OF"
[ -f "$PKG/REFERENCE_VALUES.json" ] && export REFERENCE_VALUES="$PKG/REFERENCE_VALUES.json"
WLS=skipped
if [ "$JOB_MODE" = smoke56 ] && [ "$JOB_RID" = F1 ]; then   # the token server from the compute node: HTTP status only (RUN_PLAN_HPC 9; HPC_FACTS: 302 expected)
  if [ -n "${HPR_LOCAL_DRILL:-}" ]; then WLS=skipped_local_drill; else WLS=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 30 https://token.gurobi.com 2>/dev/null || echo curl_failed); fi
  rec "WLS_TOKEN_HTTP:$WLS (302 or 200 expected)"
  case "$WLS" in 200|301|302|skipped_local_drill) ;; *) rec "WLS_TOKEN_UNREACHABLE - no solve attempted:utc=$(now)"; exit 3;; esac
fi
case "$JOB_MODE" in
  formal)      bash "$PKG/run_batch4.sh" --only "$JOB_RID" --auth "$AUTH"; rc=$?;;
  batch)       POST_ONLY=1 bash "$PKG/run_batch4.sh"; rc=$?;;
  smoke56)
    if [ "$JOB_RID" = batch ]; then POST_ONLY=1 ALLOW_UNREGISTERED=1 TRUNCATE=56 bash "$PKG/run_batch4.sh"; rc=$?
    else TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600 bash "$PKG/run_batch4.sh" --only "$JOB_RID" --auth "$AUTH; HPC smoke 56 (SMOKE_TEST_ONLY)"; rc=$?; fi;;
  build_only)
    if [ -n "${HPR_DRY_TRUNCATE:-}" ]; then TRUNCATE=$HPR_DRY_TRUNCATE ALLOW_UNREGISTERED=1 BUILD_ONLY=1 bash "$PKG/run_batch4.sh" --only "$JOB_RID"; rc=$?
    else BUILD_ONLY=1 bash "$PKG/run_batch4.sh" --only "$JOB_RID"; rc=$?; fi;;
esac
rec "RUNNER:$JOB_KEY:$JOB_MODE:$JOB_RID:exit=$rc:seconds=$(( $(date +%s) - T0 )):status_tail=$(tail -1 "$RUN_DIR/STATUS.txt" 2>/dev/null | cut -c1-240):utc=$(now)"
# ---- mode-specific records
if [ "$JOB_MODE" = build_only ]; then   # RUN_PLAN_HPC 9 / user step D2: peak memory, LP bytes, build / write seconds, scratch write speed; then delete the LP file
  d="$RUN_DIR/$JOB_RID"; S="$RUN_DIR/BUILD_ONLY_STATUS.txt"
  peak=$(grep -h 'Maximum resident' "$d/p1.err" 2>/dev/null | awk '{printf "%.2f", $NF/1048576}')
  read -r pbytes wsec bsec rows cols nnz < <("$PY" - "$d" <<'P'
import json, sys
from pathlib import Path
d = Path(sys.argv[1]); b = json.load(open(d / "split" / "SPLIT_BUILD.json")) if (d / "split" / "SPLIT_BUILD.json").exists() else {}
r = json.load(open(d / "SOLVE_RECEIPT.json")) if (d / "SOLVE_RECEIPT.json").exists() else {}; lp = r.get("lp") or {}
print(b.get("problem_bytes", 0), round(float(b.get("write_seconds") or 0), 1), round(float(lp.get("build_seconds") or 0), 1), lp.get("num_row"), lp.get("num_col"), lp.get("nnz"))
P
)
  wspeed=$(awk -v b="$pbytes" -v s="$wsec" 'BEGIN {if (s > 0) printf "%.1f", b/s/1e6; else print "n/a"}')
  t1=$(date +%s); dd if=/dev/zero of="$RUN_DIR/.ddtest" bs=1M count=1024 conv=fsync > /dev/null 2>&1; dd_s=$(( $(date +%s) - t1 )); rm -f "$RUN_DIR/.ddtest"
  dd_speed=$(awk -v s="$dd_s" 'BEGIN {if (s > 0) printf "%.0f", 1024/s; else print ">1024"}')
  bc=$(grep -h "^BUILD_CHECK_$JOB_RID:" "$RUN_DIR/STATUS.txt" 2>/dev/null | tail -1 | cut -c1-200)
  arrays=$(du -sb "$d/lp" 2>/dev/null | cut -f1)
  lpf=$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1])).get('problem_file',''))" "$d/split/SPLIT_BUILD.json" 2>/dev/null)
  del=not_present; [ -n "$lpf" ] && [ -f "$lpf" ] && { rm -f "$lpf" && del=LP_DELETED; }
  {
    echo "BUILD_ONLY:$JOB_RID:jobid=$JOBID:node=$(hostname):cpu=${CPU_MODEL:-?}:ncpus=$CORES:mem_gb=$MEM_QUOTA_GIB:cgroup=$CGV:utc=$(now)"
    echo "RUNNER_EXIT:$rc"
    echo "PEAK_RSS_GIB:${peak:-?} (GNU time of process 1; B4P estimate 72-92 GiB)"
    echo "LP_FILE_BYTES:$pbytes (B4P estimate 5.1-5.4 GB)"
    echo "LP_ARRAYS_BYTES:${arrays:-?} (lp/ kept; purged by /hpctmp after 60 days)"
    echo "BUILD_SECONDS:$bsec WRITE_SECONDS:$wsec (process 1 total $(( $(date +%s) - T0 )) s incl. preflight; runner timeout 3,600 s)"
    echo "LP_ROWS_COLS_NNZ:$rows $cols $nnz"
    echo "SCRATCH_WRITE_MBPS:lp_write=$wspeed dd_1GiB_fsync=$dd_speed (MB/s, 1e6 B)"
    echo "$bc"
    echo "$del:$lpf"
    echo "DONE:utc=$(now)"
  } > "$S"
  rec "BUILD_ONLY_STATUS:$(tr '\n' ';' < "$S" | cut -c1-600)"
fi
if [ "$JOB_MODE" = smoke56 ] && [ "$JOB_RID" = batch ]; then   # RUN_PLAN_HPC 9: the smoke verdict
  S="$RUN_DIR/SMOKE_STATUS.txt"
  "$PY" - "$RUN_DIR" "$PKG/repo" "$WLS" "$JOBID" > "$S" 2>&1 <<'P'
import json, sys, time
from pathlib import Path
out, repo, wls, jobid = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
sys.path.insert(0, str(repo / "scripts_project")); import b4_batch4 as B
st = (out / "STATUS.txt").read_text() if (out / "STATUS.txt").exists() else ""
ok = True; lines = [f"SMOKE:jobid={jobid}:utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}", f"WLS_TOKEN_HTTP:{wls}"]
for rid in ("F1", "F2"):
    rec = json.loads((out / rid / "SOLVE_RECEIPT.json").read_text()) if (out / rid / "SOLVE_RECEIPT.json").exists() else {}
    sp = json.loads((out / rid / "split" / "SPLIT_SOLVE.json").read_text()) if (out / rid / "split" / "SPLIT_SOLVE.json").exists() else {}
    acc = json.loads((out / rid / "V6_ACCEPTANCE.json").read_text()) if (out / rid / "V6_ACCEPTANCE.json").exists() else {}
    term, obj, it, lab = rec.get("termination_condition"), rec.get("objective"), sp.get("bar_iter_count"), acc.get("label")
    exp = B.SMOKE_EXPECTED_OBJECTIVE.get(rid); rel = (abs(obj - exp) / abs(exp)) if (obj is not None and exp) else None
    good = term == "optimal" and lab in ("ACCEPTED_LAYER1", "ACCEPTED_LAYER2") and rel is not None and rel <= 1e-6
    ok = ok and good
    lines.append(f"{rid}:termination={term}:objective={obj!r}:iterations={it}:label={lab}:expected_objective={exp!r}:relative_difference={rel if rel is None else f'{rel:.3e}'}:gurobi_status={sp.get('gurobi_status_name')}:{'OK' if good else 'NOT_OK'}")
pe = st.count("POSTPROC_ERROR:"); done = "DONE:" in st; halted = "HALTED" in st or (out / "STOP").exists() or (out / "STOP_SAFE").exists()
ok = ok and pe == 0 and done and not halted
lines += [f"POSTPROC_ERRORS:{pe}", f"BATCH_DONE:{done}", f"HALTED:{halted}", f"PACKS:{len(list(out.glob('results_*_final_*.tar.gz')))}", f"SMOKE_RESULT:{'PASS' if ok else 'FAIL'}"]
print("\n".join(lines))
P
  rec "SMOKE_STATUS:$(tr '\n' ';' < "$S" | cut -c1-600)"
fi
rec "JOB_END:$JOB_KEY:$JOB_MODE:$JOB_RID:exit=$rc:seconds=$(( $(date +%s) - T0 )):utc=$(now)"
[ "$JOB_MODE" = batch ] || [ "$JOB_MODE" = smoke56 ] && ls -l "$RUN_DIR"/results_*.tar.gz "$RUN_DIR"/results_*.tar.gz.sha256 >> "$J" 2>/dev/null
exit $rc
