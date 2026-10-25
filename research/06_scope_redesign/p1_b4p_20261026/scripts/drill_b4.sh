#!/bin/bash
# B4P A5.1 (RUN_PLAN_B4 section 6): the post-processing drill of the fourth batch on the TRUNCATED 2920x3h networks - every step of the chain
# (ledger redo -> violation analysis -> C1 -> M12 allocation -> Owen dual form -> GATES_V6 -> graded class) with GNU time (seconds, peak RSS)
# per step, for the memory / time extrapolation of the post-processing (RUN_PLAN_B4 3.6):
#   integrated / disconnected at 56 snapshots with a REAL local solve (results_project/b4p/solves/<tag>: the split-process runs of B4P), and at the
#   largest truncation with a SYNTHETIC solution (m10r_synthetic_solution.py: the real LP build, capacities nominal, flows 0 - only "runs through,
#   no error, identity computable" is verified, never a result). No solver call anywhere (GRB_LICENSE_FILE removed).
# Output <out>/DRILL_B4.json (per type: source kind, step exit codes, seconds, peak RSS, B16, C1, M12, Owen, label, class; all_types_ran; code_commit)
# - make_package.sh (v7) requires it for the package commit (DRILL_JSON).
#   bash drill_b4.sh <out dir>   env: WT (repo root; default: this file's repo), PY, RES (results_project of the main checkout), REAL_INT / REAL_DISC
#   (solve folders of the real 56-snapshot runs), NSYN (snapshots of the synthetic drill; default 182), REF (C1 batch reference; default smoke_s01)
set -u
OUT=${1:?out dir}
WT=${WT:-$(cd "$(dirname "$0")/../../../.." && pwd)}; PY=${PY:-/home/jin/miniforge3/envs/pypsa-earth/bin/python}
RES=${RES:-/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project}
B=$RES/m08b/builds_s01; REF=${REF:-$RES/m08b/smoke_s01/BATCH_REFERENCE.json}; NSYN=${NSYN:-182}
REAL_INT=${REAL_INT:-$RES/b4p/solves/c2_int56_split_A}; REAL_DISC=${REAL_DISC:-$RES/m08b/smoke_s01/disconnected}
export PYTHONHASHSEED=0
cd "$WT" || exit 1
[ -f "$REF" ] || { echo "no batch reference $REF"; exit 2; }
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s "$RES/$d" results_project/$d; done
mkdir -p "$OUT"; ST=$OUT/DRILL_STATUS.txt; HEAD=$(git rev-parse HEAD)
echo "START:$(date -u +%FT%TZ):head=$HEAD:dirty=$(git status --porcelain --untracked-files=no scripts_project | wc -l)" > "$ST"
log() { echo "$1:$(date -u +%FT%TZ)${2:+:$2}" >> "$ST"; }
jget() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'): d=d.get(k) if isinstance(d, dict) else None
print('' if d is None else d)" "$1" "$2" 2>/dev/null; }
run() {   # $1 step $2 dir, then the command: GNU time -v -> STEPS.txt "step exit seconds peak_kb"
  local name=$1 D=$2; shift 2; local t0=$(date +%s)
  ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$@" > "$D/$name.log" 2> "$D/$name.err" ); local rc=$?
  local pk; pk=$(grep -h "Maximum resident" "$D/$name.err" | awk '{print $NF}')
  echo "$name $rc $(( $(date +%s) - t0 )) ${pk:-0}" >> "$D/STEPS.txt"; return $rc
}
chain() {   # $1 type $2 source run dir $3 unsolved network $4 scenario $5 registered sha256 $6 kind $7 N
  local T=$1 SRC=$2 NET=$3 SC=$4 REG=$5 KIND=$6 N=$7 f
  local D=$OUT/$1
  [ -e "$D" ] && { log "SKIP_$T" "exists"; return 0; }
  mkdir -p "$D/v5"; : > "$D/STEPS.txt"; echo "$KIND" > "$D/SOURCE_KIND.txt"; echo "$SRC" > "$D/SOURCE_DIR.txt"; echo "$HEAD" > "$D/CODE_COMMIT.txt"; echo "$N" > "$D/SNAPSHOTS.txt"
  for f in SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json EXPORTS.json GUROBI_LOG_SCRUBBED.txt costs_active_research.csv COMPONENT_COST_BREAKDOWN.csv \
           COMPONENT_COST_BREAKDOWN_SUMMARY.json DUALS_INDEX.csv SYNTHETIC.json; do [ -f "$SRC/$f" ] && cp "$SRC/$f" "$D/"; done
  [ -f "$SRC/v5/kkt_summary.json" ] && cp "$SRC/v5/kkt_summary.json" "$D/v5/"
  for f in "$SRC"/*_solved.nc "$SRC"/DUALS_BY_CONSTRAINT.nc; do [ -f "$f" ] && ln -s "$f" "$D/$(basename "$f")"; done
  for f in lp solution; do [ -d "$SRC/$f" ] && ln -s "$SRC/$f" "$D/$f"; done
  log "CHAIN_$T" "kind=$KIND:N=$N:src=$SRC"
  run ledger "$D" "$PY" scripts_project/s4d_ledger_redo.py --solve-dir "$SRC" --into "$D" --repo .; log "LEDGER_$T" "exit=$?"
  [ -f "$D/V5_GATES.json" ] || cp "$SRC/V5_GATES.json" "$D/V5_GATES.json" 2>/dev/null
  run violations "$D" "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir "$D" --network "$NET" --scenario "$SC" --label DRILL --out "$D/VIOLATIONS.json" --truncate "$N"; log "VA_$T" "exit=$?"
  run c1 "$D" "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir "$D" --network "$NET" --scenario "$SC" --label DRILL --violations "$D/VIOLATIONS.json" --reference "$REF" --truncate "$N"
  log "C1_$T" "exit=$?:a=$(jget "$D/PRECISION.json" grade.a):b=$(jget "$D/PRECISION.json" grade.b):c=$(jget "$D/PRECISION.json" grade.c)"
  run m12 "$D" "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir "$D" --scenario "$SC" --label DRILL_$T --out "$D" --register; log "M12_$T" "exit=$?"
  if [ -f "$D/ALLOCATION.json" ] && [ -e "$D/solution/X.npy" ]; then
    run owen "$D" "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$NET" --scenario "$SC" --truncate "$N" --solve-dir "$D" --allocation "$D/ALLOCATION.json" --tag DRILL_$T --out "$D/m12_owen" --register-dir "$D"; log "OWEN_$T" "exit=$?"
  else echo "owen 99 0 0" >> "$D/STEPS.txt"; log "OWEN_$T" "skipped"; fi
  local lab; lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir "$D" --registered-sha256 "$REG" --repo . --out "$D/V6_ACCEPTANCE.json" 2> "$D/v6.err" | tail -1); echo "v6 $? 0 0" >> "$D/STEPS.txt"
  local cls; cls=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/b4_batch4.py stop-class --dir "$D" 2> "$D/stop_class.err" | tail -1); echo "stop_class $? 0 0" >> "$D/STEPS.txt"
  log "V6_$T" "$lab:$cls"
}
synth() {   # $1 type $2 base network $3 scenario $4 N -> synthetic solve dir, then the chain
  local T=$1 NET=$2 SC=$3 N=$4
  local SD=$OUT/_synthetic/$T   # separate statement: bash expands every word of one `local` before any assignment (set -u)
  if [ ! -f "$SD/SYNTHETIC.json" ]; then
    mkdir -p "$SD"; local t0; t0=$(date +%s)
    ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/m10r_synthetic_solution.py --repo . --network "$NET" --scenario "$SC" --out "$SD" --truncate "$N" --costs-table "$B/$SC/costs_active_research.csv" > "$SD/synthetic.log" 2> "$SD/synthetic.err" )
    log "SYNTHETIC_$T" "exit=$?:$(( $(date +%s) - t0 ))s:peak_kb=$(grep -h 'Maximum resident' "$SD/synthetic.err" | awk '{print $NF}')"
  fi
  chain "$T" "$SD" "$NET" "$SC" "$(jget "$B/$SC/${SC}_BUILD_RECEIPT.json" network.sha256)" synthetic "$N"
}
# ---- the types: both base networks at 56 (real) and at NSYN (synthetic)
[ -f "$REAL_INT/SOLVE_RECEIPT.json" ] && chain integrated "$REAL_INT" "$B/integrated/integrated_2920_3h_unsolved.nc" integrated "$(jget "$B/integrated/integrated_BUILD_RECEIPT.json" network.sha256)" real 56 || log "NO_REAL_integrated" "$REAL_INT"
[ -f "$REAL_DISC/SOLVE_RECEIPT.json" ] && chain disconnected "$REAL_DISC" "$B/disconnected/disconnected_2920_3h_unsolved.nc" disconnected "$(jget "$B/disconnected/disconnected_BUILD_RECEIPT.json" network.sha256)" real 56 || log "NO_REAL_disconnected" "$REAL_DISC"
synth integrated_$NSYN "$B/integrated/integrated_2920_3h_unsolved.nc" integrated "$NSYN"
synth disconnected_$NSYN "$B/disconnected/disconnected_2920_3h_unsolved.nc" disconnected "$NSYN"
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
# ---- the drill record
env -u GRB_LICENSE_FILE "$PY" - "$OUT" "$HEAD" <<'P'
import json, sys, time
from pathlib import Path
out, head = Path(sys.argv[1]), sys.argv[2]
def jl(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None
types = {}
for d in sorted(p for p in out.iterdir() if p.is_dir() and not p.name.startswith("_")):
    steps = {}
    for l in (d / "STEPS.txt").read_text().splitlines() if (d / "STEPS.txt").exists() else []:
        parts = l.split()
        if len(parts) >= 4:
            steps[parts[0]] = dict(exit=int(parts[1]), seconds=int(parts[2]), peak_gib=round(int(parts[3]) / 2**20, 3))
    led = jl(d / "LEDGER_IDENTITY.json") or {}; ident = led.get("identity") or {}; prec = jl(d / "PRECISION.json") or {}; g = prec.get("grade") or {}
    alloc = jl(d / "ALLOCATION.json") or {}; owen = jl(d / "m12_owen" / "OWEN.json") or {}; acc = jl(d / "V6_ACCEPTANCE.json") or {}; sc = jl(d / "STOP_CLASS.json") or {}
    rec = jl(d / "SOLVE_RECEIPT.json") or {}
    kind = (d / "SOURCE_KIND.txt").read_text().strip() if (d / "SOURCE_KIND.txt").exists() else None
    need = ("ledger", "violations", "c1", "m12", "owen", "v6", "stop_class")
    types[d.name] = dict(source=kind, snapshots=int((d / "SNAPSHOTS.txt").read_text()) if (d / "SNAPSHOTS.txt").exists() else None,
                         source_dir=(d / "SOURCE_DIR.txt").read_text().strip() if (d / "SOURCE_DIR.txt").exists() else None,
                         code_commit=(d / "CODE_COMMIT.txt").read_text().strip() if (d / "CODE_COMMIT.txt").exists() else None,
                         steps=steps, all_steps_ran=all((steps.get(k) or {}).get("exit") == 0 for k in need),
                         termination=rec.get("termination_condition"), objective=rec.get("objective"),
                         b16=dict(computable=ident.get("relative_error") is not None, relative_error=ident.get("relative_error"), difference_eur=ident.get("difference")),
                         c1=dict(a=g.get("a"), b=g.get("b"), c=g.get("c"), grade=g.get("grade")), m12_identity_passed=(alloc.get("identity") or {}).get("passed"),
                         owen_usable=owen.get("usable_for_allocation"), label=acc.get("label"), stop_class=sc.get("cls"))
expected = ["integrated", "disconnected"]
ok = all(t in types and types[t]["all_steps_ran"] and types[t]["b16"]["computable"] for t in expected) and all(v["all_steps_ran"] for v in types.values())
res = dict(script="research/06_scope_redesign/p1_b4p_20261026/scripts/drill_b4.sh", code_commit=head, written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           expected_types=expected, types=types, real_types=[t for t, v in types.items() if v["source"] == "real"], synthetic_types=[t for t, v in types.items() if v["source"] == "synthetic"],
           all_types_ran=bool(ok), solver_runs=0)
(out / "DRILL_B4.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps(dict(all_types_ran=ok, real=res["real_types"], synthetic=res["synthetic_types"], labels={t: v["label"] for t, v in types.items()}, steps={t: {k: (s["seconds"], s["peak_gib"]) for k, s in v["steps"].items()} for t, v in types.items()})))
P
echo "DONE:$(date -u +%FT%TZ)" >> "$ST"; cat "$ST"
