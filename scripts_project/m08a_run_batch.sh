#!/bin/bash
# M08a A8 (decision 133): runner for the unattended third / fourth batches with the rules registered BEFORE the runs
# (configs/research/baseline.yaml research.solver.run_rules; scripts_project/v5/gates_v6.py). No automatic retry, no parameter change.
#
#   RUN_KIND=level2 REPO=<repo> NETS=<dir> OUT=<dir> [SCENARIOS="integrated disconnected"] bash scripts_project/m08a_run_batch.sh
#     365x24h level 2 (decision 127): per scenario profile A (reference) and the candidate (profile_chain.candidate), C1 per run, the batch's
#     own per-country reference (s4o_c1_precision reference + regrade), GATES_V6 acceptance, then the profile choice -> OUT/PROFILE_CHOICE.json
#   RUN_KIND=formal REPO=<repo> NETS=<dir> OUT=<dir> [PROFILE_CHOICE=<json>] bash scripts_project/m08a_run_batch.sh
#     2920x3h formal runs with the profile of PROFILE_CHOICE.json (missing -> profile A), TimeLimit = run_rules.formal_time_limit_s (48 h);
#     C1, GATES_V6 acceptance and formal-check (C1 (c) required for the allocation); a NOT_ACCEPTED run stops the batch (STOP_NOT_ACCEPTED).
# NETS holds <scenario>_<365_24h|2920_3h>_unsolved.nc, <scenario>_BUILD_RECEIPT.json and <scenario>_costs_active_research.csv.
# Test hooks: PY, SOLVE_CMD, VA_CMD, C1_CMD (default the repo scripts); DRY=1 prints the commands only.
set -u
: "${RUN_KIND:?level2 or formal}" "${REPO:?}" "${NETS:?}" "${OUT:?}"
PY=${PY:-python}; SCENARIOS=${SCENARIOS:-"integrated disconnected"}; DRY=${DRY:-0}; AUTH=${AUTH:-"M08 batch (separate user authorisation required)"}
SOLVE_CMD=${SOLVE_CMD:-"$PY $REPO/scripts_project/s2_solve.py"}; VA_CMD=${VA_CMD:-"$PY $REPO/scripts_project/l23_violation_analysis.py"}
C1_CMD=${C1_CMD:-"$PY $REPO/scripts_project/s4o_c1_precision.py"}; G6="$PY $REPO/scripts_project/v5/gates_v6.py"
mkdir -p "$OUT"; ST="$OUT/STATUS.txt"; echo "START:$RUN_KIND:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ST"

rule() {   # dotted key of research.solver.run_rules (gates_v6.run_rules: config over the registered defaults)
  "$PY" - "$REPO" "$1" <<'P'
import sys
from pathlib import Path
repo, key = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0, str(repo / "scripts_project")); sys.path.insert(0, str(repo / "scripts_project" / "v5"))
from phase4_static import config
from gates_v6 import run_rules
v = run_rules(config(repo, "integrated"))
for k in key.split("."):
    v = v[k]
print(v if not isinstance(v, list) else " ".join(map(str, v)))
P
}
TL_FORMAL=$(rule formal_time_limit_s); CAND=$(rule profile_chain.candidate); REF=$(rule profile_chain.reference); FALLBACK=$(rule profile_chain.fallback)
TL_L2=${L2_TIME_LIMIT_S:-21600}   # level-2 runs keep the S4O limit (21,600 s; decision 123 plan)
echo "RULES:formal_time_limit_s=$TL_FORMAL:candidate=$CAND:reference=$REF:fallback=$FALLBACK:level2_time_limit_s=$TL_L2" >> "$ST"

one_run() {   # $1 tag $2 scenario $3 resolution $4 profile $5 time limit -> solve ONCE, violations, C1; never repeated
  local tag=$1 sc=$2 res=$3 prof=$4 tl=$5 dir="$OUT/$1" net="$NETS/${2}_${3}_unsolved.nc"
  mkdir -p "$dir"
  if [ -f "$dir/SOLVE_RECEIPT.json" ]; then echo "SKIP_EXISTING_$tag (no re-solve)" >> "$ST"; return 0; fi
  local s=($SOLVE_CMD --repo "$REPO" --network "$net" --scenario "$sc" --output "$dir" --label "M08_${RUN_KIND}_${tag}" --authorization "$AUTH; run $tag"
           --solver gurobi --solver-profile "$prof" --scaling on --time-limit "$tl" --costs-table "$NETS/${sc}_costs_active_research.csv")
  if [ "$DRY" = 1 ]; then echo "DRY-RUN: ${s[*]}" >> "$ST"; return 0; fi
  ( cd "$REPO" && "${s[@]}" > "$dir/solve.log" 2> "$dir/solve.err" ); echo "SOLVE_$tag:exit=$?:profile=$prof:time_limit=$tl" >> "$ST"
  if [ -f "$dir/solution/X.npy" ]; then ( cd "$REPO" && $VA_CMD --repo "$REPO" --solve-dir "$dir" --network "$net" --scenario "$sc" --label "M08_$tag" --out "$dir/VIOLATIONS.json" > "$dir/va.log" 2>&1 ); fi
  ( cd "$REPO" && $C1_CMD run --repo "$REPO" --solve-dir "$dir" --network "$net" --scenario "$sc" --label "M08_$tag" --violations "$dir/VIOLATIONS.json" > "$dir/c1.log" 2>&1 )
  echo "C1_$tag:exit=$?" >> "$ST"
}

accept() {   # $1 tag $2 scenario -> GATES_V6 label (V6_ACCEPTANCE.json)
  local dir="$OUT/$1"; [ "$DRY" = 1 ] && { echo "DRY-RUN: accept $1" >> "$ST"; echo DRY; return 0; }
  local lab; lab=$($G6 accept --solve-dir "$dir" --build-receipt "$NETS/${2}_BUILD_RECEIPT.json" --repo "$REPO" 2>> "$dir/v6.err" | tail -1)
  echo "V6_$1:$lab" >> "$ST"; echo "$lab"
}

batch_reference() {   # $1 suffix of the run tags: the batch's own per-country reference, then regrade (decision 119 (b)(c) thresholds)
  [ "$DRY" = 1 ] && return 0
  [ -f "$OUT/integrated$1/COUNTRY_COST_LEDGER.csv" ] && [ -f "$OUT/disconnected$1/COUNTRY_COST_LEDGER.csv" ] || { echo "REFERENCE$1:missing ledgers (C1 keeps its default reference)" >> "$ST"; return 0; }
  $C1_CMD reference --integrated "$OUT/integrated$1" --disconnected "$OUT/disconnected$1" --out "$OUT/BATCH_REFERENCE$1.json" > /dev/null 2>> "$ST"
  for sc in $SCENARIOS; do $C1_CMD regrade --solve-dir "$OUT/$sc$1" --reference "$OUT/BATCH_REFERENCE$1.json" > /dev/null 2>> "$ST"; done
  echo "REFERENCE$1:done" >> "$ST"
}

case "$RUN_KIND" in
  level2)
    for sc in $SCENARIOS; do one_run "${sc}_A" "$sc" 365_24h "$REF" "$TL_L2"; done
    for sc in $SCENARIOS; do one_run "${sc}_CAND" "$sc" 365_24h "$CAND" "$TL_L2"; done
    batch_reference _A; batch_reference _CAND
    for sc in $SCENARIOS; do accept "${sc}_A" "$sc" > /dev/null; accept "${sc}_CAND" "$sc" > /dev/null; done
    [ "$DRY" = 1 ] && { echo "DONE:dry" >> "$ST"; exit 0; }
    "$PY" - "$OUT" "$CAND" "$REF" $SCENARIOS > "$OUT/LEVEL2.json" <<'P'
import json, sys
from pathlib import Path
out, cand, ref, scen = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4:]
def jl(p):
    try: return json.loads(Path(p).read_text())
    except Exception: return {}
res = {}
for sc in scen:
    c, a = out / f"{sc}_CAND", out / f"{sc}_A"
    acc = jl(c / "V6_ACCEPTANCE.json").get("G1", {})
    res[sc] = dict(candidate=dict(profile=cand, objective=jl(c / "SOLVE_RECEIPT.json").get("objective"), precision={k: acc.get(k, False) for k in ("a", "b", "c")}),
                   reference=dict(profile=ref, objective=jl(a / "SOLVE_RECEIPT.json").get("objective")))
print(json.dumps(res, indent=1))
P
    $G6 select-profile --level2 "$OUT/LEVEL2.json" --repo "$REPO" > "$OUT/PROFILE_CHOICE.json"
    echo "PROFILE_CHOICE:$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1]))['profile'])" "$OUT/PROFILE_CHOICE.json")" >> "$ST"
    ;;
  formal)
    PC=${PROFILE_CHOICE:-$OUT/PROFILE_CHOICE.json}
    if [ -f "$PC" ]; then PROF=$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1]))['profile'])" "$PC"); else PROF=$FALLBACK; echo "PROFILE_CHOICE:missing -> $FALLBACK" >> "$ST"; fi
    case "$PROF" in "$CAND"|"$REF") ;; *) echo "REFUSED_PROFILE:$PROF (only $CAND or $REF; the 1e-5 profile is never a fallback)" >> "$ST"; exit 3;; esac
    echo "FORMAL_PROFILE:$PROF" >> "$ST"
    for sc in $SCENARIOS; do
      one_run "$sc" "$sc" 2920_3h "$PROF" "$TL_FORMAL"
      lab=$(accept "$sc" "$sc")
      [ "$DRY" = 1 ] || $G6 formal-check --acceptance "$OUT/$sc/V6_ACCEPTANCE.json" --repo "$REPO" > "$OUT/$sc/FORMAL_DECISION.json"
      if [ "$lab" = NOT_ACCEPTED ]; then echo "STOP_NOT_ACCEPTED:$sc (no retry, no parameter change; user decision)" >> "$ST"; touch "$OUT/STOP_NOT_ACCEPTED"; break; fi
    done
    ;;
  *) echo "unknown RUN_KIND $RUN_KIND" >&2; exit 2;;
esac
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ST"
