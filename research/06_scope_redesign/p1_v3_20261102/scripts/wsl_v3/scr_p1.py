"""V3 supplement 02, section 2.4: the 365x24h runner with a package definition of five runs. Without a definition, and with the two-run definition, the behaviour stays."""
W = "/home/jin/wt_v3_20261102/"; P = W + "research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/"


def sub(path, pairs):
    s = open(path, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, (a[:80], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="").write(s)


sub(W + "scripts_project/batch_def.py", [
    ('''    build = _jl(nets / f"{run['costs']}_BUILD_RECEIPT.json"); net = build.get(key) or {}; ok = build.get("code_sha") == build_commit
''', '''    stem = run["base"].rsplit("_", 2)[0] if run["scenario"] == run["costs"] else run["costs"]   # a bridge network has its own build receipt under the name of its base, with the cost table of its scenario
    build = _jl(nets / f"{stem}_BUILD_RECEIPT.json"); net = build.get(key) or {}; ok = build.get("code_sha") == build_commit
'''),
])
sub(W + "scripts_project/dfx_batch.py", [
    ('''_DEF = load_def()   # V3 supplement 01: the package definition replaces the v2 table and registered inputs; limits and schedule stay
if _DEF:
    RUNS, REGISTERED_SHA, REGISTERED_BYTES, BUILD_COMMIT = _DEF["runs"], _DEF["registered_sha"], _DEF["registered_bytes"], _DEF["build_commit"]
''', '''_DEF = load_def()   # V3 supplement 01: the package definition replaces the v2 table and registered inputs; V3 supplement 02: optionally its schedule and limits (five screening runs)
if _DEF:
    RUNS, REGISTERED_SHA, REGISTERED_BYTES, BUILD_COMMIT = _DEF["runs"], _DEF["registered_sha"], _DEF["registered_bytes"], _DEF["build_commit"]
    SCHEDULE = [tuple(x) for x in _DEF.get("schedule", SCHEDULE)]; TIME_LIMIT_S = _DEF.get("time_limit_s", TIME_LIMIT_S)
'''),
    ('''def _f(x, fmt="{:.4f}"):
''', '''def revision_bridge(runs: dict) -> dict | None:
    """V3 screening (RUN_PLAN_SCREEN_V3.md section 6, decision 174): v2 -> 160-162 -> 160-164 -> all on the integrated network, and the value of the stock = disconnected - no_new_xb. Description only."""
    ref = (_DEF or {}).get("bridge")
    if not ref:
        return None
    o = {k: bn(runs[k]["objective"]) if k in runs and runs[k]["objective"] is not None else None for k in RUNS}; steps = [("v2", bn(ref["v2_integrated_objective_eur"]))] + [(lab, o.get(k)) for k, lab in ref["steps"]]
    d = [dict(step=f"{a[0]} -> {b[0]}", cost_change_bn=(b[1] - a[1]) if a[1] is not None and b[1] is not None else None) for a, b in zip(steps, steps[1:])]
    return dict(objective_bn=dict(steps), steps=d, stock_value_bn=(o["V3"] - o["V2"]) if o.get("V3") is not None and o.get("V2") is not None else None, v2_b6_bn=bn(ref["v2_disconnected_objective_eur"] - ref["v2_integrated_objective_eur"]))


def _f(x, fmt="{:.4f}"):
'''),
    ('''               comparison=comparison(out, runs, b6, ref), stop_not_accepted=stop,''', '''               comparison=comparison(out, runs, b6, ref), bridge=revision_bridge(runs), stop_not_accepted=stop,'''),
    ('''    c = r.get("comparison")
    L += ["", "## 与第三批及一阶预测的对比''', '''    br = r.get("bridge")
    if br:
        L += ["", "## 修订桥与存量价值（只描述）", "", "| 步骤 | 总成本变化 bn |", "|---|---:|"] + [f"| {x['step']} | {_f(x['cost_change_bn'], '{:+.4f}')} |" for x in br["steps"]]
        L += ["", f"- 完全隔离 − `no_new_xb`（存量与专线的价值）：{_f(br['stock_value_bn'])} bn；v2 B6 {_f(br['v2_b6_bn'])} bn"]
    c = r.get("comparison")
    L += ["", "## 与第三批及一阶预测的对比'''),
])
sub(P + "run_dfx.sh", [
    ('''[ "${#SC[@]}" = 2 ] || { echo "REFUSED: run table not readable from $REPO (got ${#SC[@]} runs; expected V1, V2)"; exit 2; }
''', '''{ [ "${#SC[@]}" -ge 2 ] && [ -n "${SC[V1]:-}" ] && [ -n "${SC[V2]:-}" ]; } || { echo "REFUSED: run table not readable from $REPO (got ${#SC[@]} runs; expected V1, V2 and those of BATCH_DEF.json)"; exit 2; }
'''),
    ('''declare -A LANE_A LANE_B
while IFS='|' read -r ph la lb; do [ -n "$ph" ] && { LANE_A[$ph]=$la; LANE_B[$ph]=$lb; }; done < <(cd "$REPO" && $SUM_CMD schedule)
[ "${#LANE_A[@]}" = 1 ] || { echo "REFUSED: schedule not readable from $REPO (got ${#LANE_A[@]} phases; expected 1)"; exit 2; }
''', '''declare -A LANE_A LANE_B; PHASES=()
while IFS='|' read -r ph la lb; do [ -n "$ph" ] && { LANE_A[$ph]=$la; LANE_B[$ph]=$lb; PHASES+=("$ph"); }; done < <(cd "$REPO" && $SUM_CMD schedule)
[ "${#PHASES[@]}" -ge 1 ] || { echo "REFUSED: schedule not readable from $REPO (no phase)"; exit 2; }
'''),
    ('''[ "${#TL[@]}" = 2 ] || { echo "REFUSED: registered limits not readable from $REPO (dfx_batch.py limits)"; exit 2; }
''', '''[ "${#TL[@]}" = "${#SC[@]}" ] || { echo "REFUSED: registered limits not readable from $REPO (dfx_batch.py limits)"; exit 2; }
'''),
    (''':time_limit_s=V1=${TL[V1]},V2=${TL[V2]}:wall_cap_s=V1=${WALL[V1]},V2=${WALL[V2]}:licence_gap_s=$LICENCE_GAP_S:parallel_min_cores=$R_PAR_CORES:schedule=1[${LANE_A[1]}|${LANE_B[1]}]:truncate=''', ''':time_limit_s=$(for r in $(printf '%s\\n' "${!TL[@]}" | sort); do printf '%s=%s,' "$r" "${TL[$r]}"; done):wall_cap_s=$(for r in $(printf '%s\\n' "${!WALL[@]}" | sort); do printf '%s=%s,' "$r" "${WALL[$r]}"; done):licence_gap_s=$LICENCE_GAP_S:parallel_min_cores=$R_PAR_CORES:schedule=$(for p in "${PHASES[@]}"; do printf '%s[%s|%s]' "$p" "${LANE_A[$p]}" "${LANE_B[$p]}"; done):truncate='''),
    ('''  for rid in "${!SC[@]}"; do
    need+=("${BASE[$rid]}_unsolved.nc" "${COSTS[$rid]}_BUILD_RECEIPT.json" "${COSTS[$rid]}_costs_active_research.csv"); if is_variant "$rid"; then need+=("${BASE[$rid]}_VARIANT_RECEIPT.json"); fi
  done
''', '''  for rid in "${!SC[@]}"; do
    need+=("${BASE[$rid]}_unsolved.nc" "${COSTS[$rid]}_BUILD_RECEIPT.json" "${COSTS[$rid]}_costs_active_research.csv"); if is_variant "$rid"; then need+=("${BASE[$rid]}_VARIANT_RECEIPT.json"); else need+=("$(base_scen "$rid")_BUILD_RECEIPT.json"); fi
  done
'''),
    ('''  local la lb one=() i; IFS=, read -ra la <<< "${LANE_A[$1]}"; IFS=, read -ra lb <<< "${LANE_B[$1]}"
  local thr=$(( $(max_threads "${la[@]}") + $(max_threads "${lb[@]}") ))
''', '''  local la lb one=() i; IFS=, read -ra la <<< "${LANE_A[$1]}"; IFS=, read -ra lb <<< "${LANE_B[$1]}"
  local thr=$(( $(max_threads "${la[@]}") + $(max_threads ${lb[@]+"${lb[@]}"}) ))
'''),
    ('''    lane A "${la[@]}" & local a=$!; sleep 2; lane B "${lb[@]}" & local b=$!; wait $a; wait $b
''', '''    lane A "${la[@]}" & local a=$!; sleep 2; lane B ${lb[@]+"${lb[@]}"} & local b=$!; wait $a; wait $b
'''),
    ('''  mkdir -p "$EXP/batch"
  for f in STATUS.txt BASE_CHECK.json BATCH_REFERENCE.json DFX_SUMMARY.json DFX_SUMMARY.md STOP STOP_SAFE UNUSABLE POSTPROC_ERRORS; do [ -f "$OUT/$f" ] && cp "$OUT/$f" "$EXP/batch/"; done
''', '''  if [ -n "${BATCH_DEF:-}" ] && [ "$BUILD_ONLY" != 1 ] && [ "$DRY" != 1 ] && [ -f "$OUT/V1/COUNTRY_COST_LEDGER.csv" ] && [ -f "$OUT/V2/COUNTRY_COST_LEDGER.csv" ]; then   # V3 screening tables (RUN_PLAN_SCREEN_V3.md section 6)
    step batch screen_tables $SCREEN_CMD --out-dir "$OUT" > "$OUT/screen_tables.log" 2>&1; log "SCREEN_TABLES:exit=$?:$(tail -1 "$OUT/screen_tables.log" 2>/dev/null | cut -c1-200)"
  fi
  mkdir -p "$EXP/batch"
  for f in STATUS.txt BASE_CHECK.json BATCH_REFERENCE.json DFX_SUMMARY.json DFX_SUMMARY.md STOP STOP_SAFE UNUSABLE POSTPROC_ERRORS ID_LEDGER_DECOMPOSITION.csv VN_BIOMASS_BALANCE.json LA_EXPORT_UTILISATION.csv; do [ -f "$OUT/$f" ] && cp "$OUT/$f" "$EXP/batch/"; done
'''),
    ('''SUM_CMD=${SUM_CMD:-"$PY $REPO/scripts_project/dfx_batch.py"}; PACK_CMD=${PACK_CMD:-"bash $HERE/pack_results.sh"}
''', '''SUM_CMD=${SUM_CMD:-"$PY $REPO/scripts_project/dfx_batch.py"}; PACK_CMD=${PACK_CMD:-"bash $HERE/pack_results.sh"}; SCREEN_CMD=${SCREEN_CMD:-"$PY $REPO/scripts_project/v3_screen_tables.py"}
'''),
    ('''phase 1
regrade_all
batch_post
''', '''for ph in "${PHASES[@]}"; do phase "$ph"; regrade_all; done   # the batch reference exists after the phase of V1 and V2: the later runs use it from their first grading
batch_post
'''),
])
sub(P + "preflight_dfx.sh", [
    ('''assert list(dfx_batch.RUNS) == ["V1", "V2"], "run table"
assert dfx_batch.TIME_LIMIT_S == {"V1": 21600, "V2": 10800} and dfx_batch.WALL_MARGIN_S == 1200 and dfx_batch.LICENCE_GAP_S == 330 and dfx_batch.PARALLEL_MIN_CORES == 33, "registered limits"
assert dfx_batch.SCHEDULE == [("1", ["V1"], ["V2"])] and dfx_batch.STOP_ALWAYS == ("V1", "V2"), "schedule / stop rule"
''', '''import batch_def
D = batch_def.load_def() or {}   # V3 supplement 02: with a package definition the run table, limits and schedule are those of BATCH_DEF.json
assert list(dfx_batch.RUNS) == (list(D["runs"]) if D else ["V1", "V2"]), "run table"
assert dfx_batch.TIME_LIMIT_S == D.get("time_limit_s", {"V1": 21600, "V2": 10800}) and dfx_batch.WALL_MARGIN_S == 1200 and dfx_batch.LICENCE_GAP_S == 330 and dfx_batch.PARALLEL_MIN_CORES == 33, "registered limits"
assert dfx_batch.SCHEDULE == [tuple(x) for x in D.get("schedule", [("1", ["V1"], ["V2"])])] and dfx_batch.STOP_ALWAYS == ("V1", "V2"), "schedule / stop rule"
'''),
    ('''for c in $(cd repo && env -u GRB_LICENSE_FILE "$PY" scripts_project/dfx_batch.py runtable | cut -d'|' -f6 | sort -u); do''', '''for c in $(cd repo && env -u GRB_LICENSE_FILE "$PY" scripts_project/dfx_batch.py runtable | cut -d'|' -f6 | sort -u); do'''.replace("cut -d'|' -f6", "cut -d'|' -f6")),
] [:1])
print("patched")
