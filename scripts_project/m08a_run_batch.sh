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
# M12 (item 133): after C1 every run gets its Owen allocation (m12_allocation.py run -> ALLOCATION.*, registered in the run's EXPORTS.json
# BEFORE the GATES_V6 acceptance) and, when the exported arrays exist and M12_DUAL=1 (default), the Owen dual form with the KVL decomposition
# (m12_rhs_audit.py audit -> m12_owen/, registered); once both scenarios of a profile have allocations (after the regrade): the batch's
# benefit and proportional-rule comparison (OUT/M12_BENEFIT<suffix>/); leave-one-out runs in OUT/<full tag>_minus<CC>/ -> OUT/M12_LOO_<tag>/.
# M12 supplement 01 D7 (item 136): level2 only - after the profile-A runs of both scenarios the leave-one-out variants of LOO_COUNTRIES
# (default "VN TH LA") are generated in the cloud from NETS/integrated_365_24h_unsolved.nc with VAR_CMD (m08a_variants.py, PYTHONHASHSEED=0,
# never --allow-stale-base) into OUT/variants/ (receipt + output SHA256 in STATUS) and solved ONCE each as integrated_A_minus<CC> with profile A
# (costs table of the integrated base; GATES_V6 G2.1 against the variant receipt's output.sha256); batch_reference _A regrades them too.
# The fourth batch (formal) has no leave-one-out runs.
# Test hooks: PY, SOLVE_CMD, VA_CMD, C1_CMD, M12_CMD, M12A_CMD, VAR_CMD (default the repo scripts); DRY=1 prints the commands only.
set -u
: "${RUN_KIND:?level2 or formal}" "${REPO:?}" "${NETS:?}" "${OUT:?}"
PY=${PY:-python}; SCENARIOS=${SCENARIOS:-"integrated disconnected"}; DRY=${DRY:-0}; AUTH=${AUTH:-"M08 batch (separate user authorisation required)"}
SOLVE_CMD=${SOLVE_CMD:-"$PY $REPO/scripts_project/s2_solve.py"}; VA_CMD=${VA_CMD:-"$PY $REPO/scripts_project/l23_violation_analysis.py"}
C1_CMD=${C1_CMD:-"$PY $REPO/scripts_project/s4o_c1_precision.py"}; G6="$PY $REPO/scripts_project/v5/gates_v6.py"
M12_CMD=${M12_CMD:-"$PY $REPO/scripts_project/m12_allocation.py"}; M12A_CMD=${M12A_CMD:-"$PY $REPO/scripts_project/m12_rhs_audit.py"}; M12_DUAL=${M12_DUAL:-1}
VAR_CMD=${VAR_CMD:-"$PY $REPO/scripts_project/m08a_variants.py"}; LOO_COUNTRIES=${LOO_COUNTRIES:-"VN TH LA"}
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

one_run() {   # $1 tag $2 scenario $3 resolution $4 profile $5 time limit [$6 network $7 costs table] -> solve ONCE, violations, C1; never repeated
  local tag=$1 sc=$2 res=$3 prof=$4 tl=$5 dir="$OUT/$1" net=${6:-"$NETS/${2}_${3}_unsolved.nc"} costs=${7:-"$NETS/${2}_costs_active_research.csv"}
  mkdir -p "$dir"
  if [ -f "$dir/SOLVE_RECEIPT.json" ]; then echo "SKIP_EXISTING_$tag (no re-solve)" >> "$ST"; return 0; fi
  local s=($SOLVE_CMD --repo "$REPO" --network "$net" --scenario "$sc" --output "$dir" --label "M08_${RUN_KIND}_${tag}" --authorization "$AUTH; run $tag"
           --solver gurobi --solver-profile "$prof" --scaling on --time-limit "$tl" --costs-table "$costs")
  if [ "$DRY" = 1 ]; then echo "DRY-RUN: ${s[*]}" >> "$ST"; return 0; fi
  ( cd "$REPO" && "${s[@]}" > "$dir/solve.log" 2> "$dir/solve.err" ); echo "SOLVE_$tag:exit=$?:profile=$prof:time_limit=$tl" >> "$ST"
  if [ -f "$dir/solution/X.npy" ]; then ( cd "$REPO" && $VA_CMD --repo "$REPO" --solve-dir "$dir" --network "$net" --scenario "$sc" --label "M08_$tag" --out "$dir/VIOLATIONS.json" > "$dir/va.log" 2>&1 ); fi
  ( cd "$REPO" && $C1_CMD run --repo "$REPO" --solve-dir "$dir" --network "$net" --scenario "$sc" --label "M08_$tag" --violations "$dir/VIOLATIONS.json" > "$dir/c1.log" 2>&1 )
  echo "C1_$tag:exit=$?" >> "$ST"
  m12_run "$tag" "$sc" "$net"
}

m12_run() {   # $1 tag $2 scenario $3 unsolved network: M12 allocation (and the Owen dual form) after C1, registered before the acceptance
  local dir="$OUT/$1"
  ( cd "$REPO" && PYTHONHASHSEED=0 $M12_CMD run --repo "$REPO" --solve-dir "$dir" --scenario "$2" --label "M08_$1" --out "$dir" --register > "$dir/m12.log" 2>&1 )
  echo "M12_$1:exit=$?" >> "$ST"
  if [ "$M12_DUAL" = 1 ] && [ -f "$dir/solution/X.npy" ] && [ -f "$dir/ALLOCATION.json" ]; then
    ( cd "$REPO" && PYTHONHASHSEED=0 $M12A_CMD audit --repo "$REPO" --network "$3" --scenario "$2" --solve-dir "$dir" --allocation "$dir/ALLOCATION.json" --tag "M08_$1" \
        --out "$dir/m12_owen" --register-dir "$dir" > "$dir/m12_owen.log" 2>&1 )
    echo "M12_OWEN_$1:exit=$?" >> "$ST"
  fi
}

m12_batch() {   # $1 suffix of the run tags: benefit / proportional rules of the batch once both scenarios have allocations (after any regrade);
  # runs AFTER m12_loo: the (A) basis of the proportional rules is tested against the batch's leave-one-out marginal contributions (supplement 01 D4)
  [ "$DRY" = 1 ] && return 0
  [ -f "$OUT/integrated$1/ALLOCATION.json" ] && [ -f "$OUT/disconnected$1/ALLOCATION.json" ] || { echo "M12_BENEFIT$1:missing allocations" >> "$ST"; return 0; }
  local lc=(); [ -f "$OUT/M12_LOO_integrated$1/LOO_CHECK.json" ] && lc=(--loo-check "$OUT/M12_LOO_integrated$1/LOO_CHECK.json")
  ( cd "$REPO" && $M12_CMD benefit --repo "$REPO" --integrated "$OUT/integrated$1" --disconnected "$OUT/disconnected$1" --out "$OUT/M12_BENEFIT$1" ${lc[@]+"${lc[@]}"} \
      > "$OUT/M12_BENEFIT$1.log" 2>&1 )
  echo "M12_BENEFIT$1:exit=$?:loo_check=${#lc[@]}" >> "$ST"
}

m12_loo() {   # $1 tag of the full integrated run: leave-one-out check once runs OUT/$1_minus<CC>/ exist (same resolution and profile)
  [ "$DRY" = 1 ] && return 0
  local args=() d c
  for d in "$OUT/$1"_minus*; do [ -f "$d/SOLVE_RECEIPT.json" ] || continue; c=${d##*_minus}; args+=(--loo "${c:0:2}=$d"); done
  [ ${#args[@]} -gt 0 ] || return 0
  local sa="$OUT/disconnected${1#integrated}"
  ( cd "$REPO" && $M12_CMD loo --full "$OUT/$1" "${args[@]}" --standalone "$sa" --out "$OUT/M12_LOO_$1" > "$OUT/M12_LOO_$1.log" 2>&1 )
  echo "M12_LOO_$1:exit=$?:runs=$(( ${#args[@]} / 2 ))" >> "$ST"
}

accept() {   # $1 tag $2 scenario [$3 registered SHA256 of the input network: leave-one-out variants] -> GATES_V6 label (V6_ACCEPTANCE.json)
  local dir="$OUT/$1"; [ "$DRY" = 1 ] && { echo "DRY-RUN: accept $1" >> "$ST"; echo DRY; return 0; }
  local reg=(--build-receipt "$NETS/${2}_BUILD_RECEIPT.json"); [ -n "${3:-}" ] && reg=(--registered-sha256 "$3")
  local lab; lab=$($G6 accept --solve-dir "$dir" "${reg[@]}" --repo "$REPO" 2>> "$dir/v6.err" | tail -1)
  echo "V6_$1:$lab" >> "$ST"; echo "$lab"
}

batch_reference() {   # $1 suffix of the run tags: the batch's own per-country reference, then regrade (decision 119 (b)(c) thresholds)
  [ "$DRY" = 1 ] && return 0
  [ -f "$OUT/integrated$1/COUNTRY_COST_LEDGER.csv" ] && [ -f "$OUT/disconnected$1/COUNTRY_COST_LEDGER.csv" ] || { echo "REFERENCE$1:missing ledgers (C1 keeps its default reference)" >> "$ST"; return 0; }
  $C1_CMD reference --integrated "$OUT/integrated$1" --disconnected "$OUT/disconnected$1" --out "$OUT/BATCH_REFERENCE$1.json" > /dev/null 2>> "$ST"
  local d n=0
  for sc in $SCENARIOS; do $C1_CMD regrade --solve-dir "$OUT/$sc$1" --reference "$OUT/BATCH_REFERENCE$1.json" > /dev/null 2>> "$ST"; done
  for d in "$OUT/integrated$1"_minus*; do   # leave-one-out runs of the batch (D7): same reference
    [ -f "$d/PRECISION.json" ] || continue; $C1_CMD regrade --solve-dir "$d" --reference "$OUT/BATCH_REFERENCE$1.json" > /dev/null 2>> "$ST"; n=$((n + 1))
  done
  echo "REFERENCE$1:done:loo_regraded=$n" >> "$ST"
}

variant_sha() {   # $1 variant receipt -> output.sha256
  "$PY" -c "import json,sys; print(json.load(open(sys.argv[1]))['output']['sha256'])" "$1" 2>/dev/null
}

loo_runs() {   # $1 suffix (profile tag), $2 profile: leave-one-out variants of LOO_COUNTRIES generated from the 365x24h integrated base, solved ONCE each
  case " $SCENARIOS " in *" integrated "*) ;; *) echo "LOO$1:skipped (no integrated scenario)" >> "$ST"; return 0;; esac
  local base="$NETS/integrated_365_24h_unsolved.nc" V="$OUT/variants" c rc net sha act
  mkdir -p "$V"
  echo "LOO$1:countries=$LOO_COUNTRIES:base_sha256=$( [ -f "$base" ] && sha256sum "$base" | cut -c1-64)" >> "$ST"
  for c in $LOO_COUNTRIES; do
    rc="$V/integrated_minus${c}_365_24h_VARIANT_RECEIPT.json"; net="$V/integrated_minus${c}_365_24h_unsolved.nc"
    if [ "$DRY" = 1 ]; then echo "DRY-RUN: PYTHONHASHSEED=0 $VAR_CMD --repo $REPO --base $base --out $V --set coalition.remove_countries=[$c]" >> "$ST"; continue; fi
    if [ ! -f "$rc" ]; then
      ( cd "$REPO" && PYTHONHASHSEED=0 $VAR_CMD --repo "$REPO" --base "$base" --out "$V" --set "coalition.remove_countries=[$c]" > "$V/variant_$c.log" 2>&1 )
      echo "VARIANT_$c:exit=$?" >> "$ST"
    fi
    sha=$(variant_sha "$rc"); act=$( [ -f "$net" ] && sha256sum "$net" | cut -c1-64)
    if [ -z "$sha" ] || [ "$sha" != "$act" ]; then echo "VARIANT_$c:FAILED (receipt sha256 ${sha:-missing} vs file ${act:-missing}); leave-one-out run skipped" >> "$ST"; continue; fi
    echo "VARIANT_$c:sha256=$sha" >> "$ST"
    one_run "integrated${1}_minus$c" integrated 365_24h "$2" "$TL_L2" "$net" "$NETS/integrated_costs_active_research.csv"
  done
}

loo_accept() {   # $1 suffix: GATES_V6 acceptance of the leave-one-out runs (G2.1 against the variant receipt's output.sha256)
  local d c
  for d in "$OUT/integrated$1"_minus*; do
    [ -d "$d" ] || continue; c=${d##*_minus}
    accept "integrated$1_minus$c" integrated "$(variant_sha "$OUT/variants/integrated_minus${c}_365_24h_VARIANT_RECEIPT.json")" > /dev/null
  done
}

case "$RUN_KIND" in
  level2)
    for sc in $SCENARIOS; do one_run "${sc}_A" "$sc" 365_24h "$REF" "$TL_L2"; done
    loo_runs _A "$REF"   # D7: leave-one-out (third batch only), profile A, paired with integrated_A
    for sc in $SCENARIOS; do one_run "${sc}_CAND" "$sc" 365_24h "$CAND" "$TL_L2"; done
    batch_reference _A; batch_reference _CAND
    m12_loo integrated_A; m12_loo integrated_CAND; m12_batch _A; m12_batch _CAND
    for sc in $SCENARIOS; do accept "${sc}_A" "$sc" > /dev/null; accept "${sc}_CAND" "$sc" > /dev/null; done
    [ "$DRY" = 1 ] || loo_accept _A
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
    [ -f "$OUT/STOP_NOT_ACCEPTED" ] || { m12_loo integrated; m12_batch ""; }
    ;;
  *) echo "unknown RUN_KIND $RUN_KIND" >&2; exit 2;;
esac
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ST"
