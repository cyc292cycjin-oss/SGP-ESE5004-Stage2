#!/bin/bash
# M10R B3.3 (RUN_PLAN.md 11.4): the post-processing drill of EVERY network type of the third batch on 56x3h - the 2 base networks and the 7
# variants: integrated, disconnected, minus VN / TH / LA, keep-stock, b1 (no intra-ASEAN CO2 shipping), country WACC integrated / disconnected.
# For every type the whole chain runs with the current code into <out>/<type>: ledger redo (s4d_ledger_redo.py) -> violation analysis -> C1
# (smoke_s01 batch reference) -> M12 allocation -> Owen dual-form audit -> GATES_V6 -> graded stop class. Types with a REAL local 56x3h solve use
# it (read only; the solved network / duals / LP and solution arrays are linked); the others get a SYNTHETIC solution (m10r_synthetic_solution.py:
# real LP build, capacities nominal, flows 0, duals 0 - only "runs through, no error, identity computable" is verified, never a result).
# No solver call anywhere (GRB_LICENSE_FILE removed). Output <out>/DRILL_POSTPROC.json (per type: source kind, step exit codes, B16, C1, M12,
# Owen, label, class; all_types_ran; code_commit) - make_package.sh requires it for the package commit (DRILL_JSON).
#   bash drill_postproc.sh <out dir>     env: WT (repo root; default: this file's repo), PY, RES (results_project of the main checkout)
set -u
OUT=${1:?out dir}
WT=${WT:-$(cd "$(dirname "$0")/../../../.." && pwd)}; PY=${PY:-/home/jin/miniforge3/envs/pypsa-earth/bin/python}
RES=${RES:-/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project}
M=$RES/m10r; B=$RES/m08b/builds_s01; S=$RES/m08b/smoke_s01; V=$RES/m12b/variants; REF=$S/BATCH_REFERENCE.json; N=56
export PYTHONHASHSEED=0
cd "$WT" || exit 1
[ -f "$REF" ] || { echo "no batch reference $REF (M08b smoke_s01 results needed)"; exit 2; }
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s "$RES/$d" results_project/$d; done
mkdir -p "$OUT"; ST=$OUT/DRILL_STATUS.txt; HEAD=$(git rev-parse HEAD)
echo "START:$(date -u +%FT%TZ):head=$HEAD:dirty=$(git status --porcelain --untracked-files=no scripts_project | wc -l)" > "$ST"
log() { echo "$1:$(date -u +%FT%TZ)${2:+:$2}" >> "$ST"; }
jget() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'): d=d.get(k) if isinstance(d, dict) else None
print('' if d is None else d)" "$1" "$2" 2>/dev/null; }
run() { local name=$1 D=$2; shift 2; ( env -u GRB_LICENSE_FILE "$@" > "$D/$name.log" 2> "$D/$name.err" ); local rc=$?; echo "$name $rc" >> "$D/STEPS.txt"; return $rc; }
chain() {   # $1 type $2 source run dir $3 unsolved network $4 scenario $5 registered sha256 $6 kind (real | synthetic)
  local T=$1 SRC=$2 NET=$3 SC=$4 REG=$5 KIND=$6 D=$OUT/$1 f
  [ -e "$D" ] && { log "SKIP_$T" "exists"; return 0; }
  mkdir -p "$D/v5"; : > "$D/STEPS.txt"; echo "$KIND" > "$D/SOURCE_KIND.txt"; echo "$SRC" > "$D/SOURCE_DIR.txt"
  for f in SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json EXPORTS.json GUROBI_LOG_SCRUBBED.txt costs_active_research.csv COMPONENT_COST_BREAKDOWN.csv \
           COMPONENT_COST_BREAKDOWN_SUMMARY.json DUALS_INDEX.csv SYNTHETIC.json; do [ -f "$SRC/$f" ] && cp "$SRC/$f" "$D/"; done
  [ -f "$SRC/v5/kkt_summary.json" ] && cp "$SRC/v5/kkt_summary.json" "$D/v5/"
  for f in "$SRC"/*_solved.nc "$SRC"/DUALS_BY_CONSTRAINT.nc; do [ -f "$f" ] && ln -s "$f" "$D/$(basename "$f")"; done
  for f in lp solution; do [ -d "$SRC/$f" ] && ln -s "$SRC/$f" "$D/$f"; done
  log "CHAIN_$T" "kind=$KIND:src=$SRC"
  run ledger "$D" "$PY" scripts_project/s4d_ledger_redo.py --solve-dir "$SRC" --into "$D" --repo .; log "LEDGER_$T" "exit=$?:$(tail -1 "$D/ledger.log" | cut -c1-200)"
  [ -f "$D/V5_GATES.json" ] || cp "$SRC/V5_GATES.json" "$D/V5_GATES.json" 2>/dev/null
  run violations "$D" "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir "$D" --network "$NET" --scenario "$SC" --label DRILL --out "$D/VIOLATIONS.json" --truncate $N; log "VA_$T" "exit=$?"
  run c1 "$D" "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir "$D" --network "$NET" --scenario "$SC" --label DRILL --violations "$D/VIOLATIONS.json" --reference "$REF" --truncate $N
  log "C1_$T" "exit=$?:a=$(jget "$D/PRECISION.json" grade.a):b=$(jget "$D/PRECISION.json" grade.b):c=$(jget "$D/PRECISION.json" grade.c)"
  run m12 "$D" "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir "$D" --scenario "$SC" --label DRILL_$T --out "$D" --register; log "M12_$T" "exit=$?"
  if [ -f "$D/ALLOCATION.json" ] && [ -e "$D/solution/X.npy" ]; then
    run owen "$D" "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$NET" --scenario "$SC" --truncate $N --solve-dir "$D" --allocation "$D/ALLOCATION.json" --tag DRILL_$T --out "$D/m12_owen" --register-dir "$D"
    log "OWEN_$T" "exit=$?"
  else echo "owen 99" >> "$D/STEPS.txt"; log "OWEN_$T" "skipped"; fi
  local lab; lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir "$D" --registered-sha256 "$REG" --repo . --out "$D/V6_ACCEPTANCE.json" 2> "$D/v6.err" | tail -1); echo "v6 $?" >> "$D/STEPS.txt"
  local cls; cls=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/m10_batch3_summary.py stop-class --dir "$D" 2> "$D/stop_class.err" | tail -1); echo "stop_class $?" >> "$D/STEPS.txt"
  log "V6_$T" "$lab:$cls"
}
synth() {   # $1 type $2 base network $3 scenario $4 --set $5 costs table (variant --costs and solve --costs-table; empty = none) -> source dir
  local T=$1 BASE=$2 SC=$3 SET=$4 COSTS=$5 VD=$OUT/_variants/$T SD=$OUT/_synthetic/$T extra=()
  [ -n "$COSTS" ] && extra=(--costs "$COSTS")
  if [ ! -f "$(ls "$VD"/*_VARIANT_RECEIPT.json 2>/dev/null | head -1)" ]; then
    mkdir -p "$VD"; ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m08a_variants.py --repo . --base "$BASE" --out "$VD" --set "$SET" "${extra[@]}" > "$VD/variant.log" 2>&1 ); log "VARIANT_$T" "exit=$?"
  fi
  local net; net=$(ls "$VD"/*_unsolved.nc | head -1); local ex=(); [ -n "$COSTS" ] && ex=(--costs-table "$COSTS")
  if [ ! -f "$SD/SYNTHETIC.json" ]; then
    mkdir -p "$SD"; ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m10r_synthetic_solution.py --repo . --network "$net" --scenario "$SC" --out "$SD" --truncate $N "${ex[@]}" > "$SD/synthetic.log" 2> "$SD/synthetic.err" ); log "SYNTHETIC_$T" "exit=$?:$(tail -1 "$SD/synthetic.log" | cut -c1-160)"
  fi
  chain "$T" "$SD" "$net" "$SC" "$(jget "$(ls "$VD"/*_VARIANT_RECEIPT.json | head -1)" output.sha256)" synthetic
}
real_or_synth() {   # $1 type $2 real run dir $3 real network $4 scenario $5 real registered sha $6.. synth args
  local T=$1 RD=$2 RN=$3 SC=$4 RS=$5; shift 5
  if [ -f "$RD/SOLVE_RECEIPT.json" ] && [ -n "$RN" ] && [ -f "$RN" ] && [ -n "$RS" ]; then chain "$T" "$RD" "$RN" "$SC" "$RS" real; else synth "$T" "$@"; fi
}
# ---- the nine types
chain integrated "$S/integrated" "$B/integrated/integrated_2920_3h_unsolved.nc" integrated "$(jget "$B/integrated/integrated_BUILD_RECEIPT.json" network.sha256)" real
chain disconnected "$S/disconnected" "$B/disconnected/disconnected_2920_3h_unsolved.nc" disconnected "$(jget "$B/disconnected/disconnected_BUILD_RECEIPT.json" network.sha256)" real
for c in VN TH LA; do chain minus$c "$RES/m12b/integrated_minus$c" "$V/integrated_minus${c}_2920_3h_unsolved.nc" integrated "$(jget "$V/integrated_minus${c}_2920_3h_VARIANT_RECEIPT.json" output.sha256)" real; done
real_or_synth keepstock "$M/keepstock_v5" "$M/variants/disconnected_keepstock_2920_3h_unsolved.nc" disconnected "$(jget "$M/variants/disconnected_keepstock_2920_3h_VARIANT_RECEIPT.json" output.sha256)" \
  "$B/integrated/integrated_2920_3h_unsolved.nc" disconnected "cross_border.stock_mode=keep_stock_no_new" ""
real_or_synth wacc_disconnected "$M/wacc_disconnected" "$(ls "$M"/variants/gen_wacc_disconnected/*_unsolved.nc 2>/dev/null | head -1)" disconnected "$(jget "$(ls "$M"/variants/gen_wacc_disconnected/*_VARIANT_RECEIPT.json 2>/dev/null | head -1)" output.sha256)" \
  "$B/disconnected/disconnected_2920_3h_unsolved.nc" disconnected "finance.wacc_mode=country_specific" "$B/disconnected/costs_active_research.csv"
real_or_synth b1_disconnected "$M/b1_disconnected" "$(ls "$M"/variants/gen_b1_disconnected/*_unsolved.nc 2>/dev/null | head -1)" disconnected "$(jget "$(ls "$M"/variants/gen_b1_disconnected/*_VARIANT_RECEIPT.json 2>/dev/null | head -1)" output.sha256)" \
  "$B/disconnected/disconnected_2920_3h_unsolved.nc" disconnected "disconnected.co2_shipping_intra_asean=forbid" ""
real_or_synth wacc_integrated "$M/wacc_integrated" "" integrated "" \
  "$B/integrated/integrated_2920_3h_unsolved.nc" integrated "finance.wacc_mode=country_specific" "$B/integrated/costs_active_research.csv"
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
    steps = dict(l.split() for l in (d / "STEPS.txt").read_text().splitlines() if l.strip()) if (d / "STEPS.txt").exists() else {}
    led = jl(d / "LEDGER_IDENTITY.json") or {}; ident = led.get("identity") or {}; prec = jl(d / "PRECISION.json") or {}; g = prec.get("grade") or {}
    alloc = jl(d / "ALLOCATION.json") or {}; owen = jl(d / "m12_owen" / "OWEN.json") or {}; acc = jl(d / "V6_ACCEPTANCE.json") or {}; sc = jl(d / "STOP_CLASS.json") or {}
    rec = jl(d / "SOLVE_RECEIPT.json") or {}
    kind = (d / "SOURCE_KIND.txt").read_text().strip() if (d / "SOURCE_KIND.txt").exists() else None
    need = ("ledger", "violations", "c1", "m12", "owen", "v6", "stop_class")
    types[d.name] = dict(source=kind, source_dir=(d / "SOURCE_DIR.txt").read_text().strip() if (d / "SOURCE_DIR.txt").exists() else None,
                         steps={k: int(v) for k, v in steps.items()}, all_steps_ran=all(steps.get(k) == "0" for k in need),
                         termination=rec.get("termination_condition"), objective=rec.get("objective"),
                         b16=dict(computable=ident.get("relative_error") is not None, relative_error=ident.get("relative_error"), difference_eur=ident.get("difference"),
                                  fom_meta=(led.get("diagnostics") or {}).get("existing_cross_border_fom_ledger")),
                         c1=dict(a=g.get("a"), b=g.get("b"), c=g.get("c"), grade=g.get("grade")), m12_identity_passed=(alloc.get("identity") or {}).get("passed"),
                         owen_usable=owen.get("usable_for_allocation"), label=acc.get("label"), stop_class=sc.get("cls"))
expected = ["integrated", "disconnected", "minusVN", "minusTH", "minusLA", "keepstock", "wacc_disconnected", "b1_disconnected", "wacc_integrated"]
ok = all(t in types and types[t]["all_steps_ran"] and types[t]["b16"]["computable"] for t in expected)
res = dict(script="research/06_scope_redesign/p1_m10r_20261024/scripts/drill_postproc.sh", code_commit=head, written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           expected_types=expected, types=types, real_types=[t for t, v in types.items() if v["source"] == "real"], synthetic_types=[t for t, v in types.items() if v["source"] == "synthetic"],
           all_types_ran=bool(ok), solver_runs=0)
(out / "DRILL_POSTPROC.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps(dict(all_types_ran=ok, real=res["real_types"], synthetic=res["synthetic_types"], labels={t: v["label"] for t, v in types.items()})))
P
echo "DONE:$(date -u +%FT%TZ)" >> "$ST"; cat "$ST"
