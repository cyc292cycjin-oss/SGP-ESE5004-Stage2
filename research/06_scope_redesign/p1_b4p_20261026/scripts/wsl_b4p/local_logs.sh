#!/bin/bash
# B4P A1.1: barrier statistics and receipts of the local 56x3h solves (read only)
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
for d in m08b/smoke_s01/integrated m08b/smoke_s01/disconnected m10r/b1_disconnected m10r/wacc_disconnected m10r/keepstock_v5 m12b/full_integrated m12b/full_disconnected m12b/integrated_minusVN; do
  echo "== $d"
  f=$R/$d/GUROBI_LOG_SCRUBBED.txt; [ -f "$f" ] || f=$R/$d/gurobi.linopy.log
  if [ -f "$f" ]; then
    grep -E "^(Gurobi Optimizer version|Thread count|Optimize a model|Model fingerprint|Presolved:|Presolve time|Ordering time|Barrier performed|Barrier solved|Threads  |Optimal objective|Sub-optimal)" "$f"
    grep -E "^ (Dense cols|Free vars|AA. NZ|Factor NZ|Factor Ops|Threads)" "$f"
  else
    echo "no gurobi log"; ls $R/$d | head -5
  fi
  grep -hE "Maximum resident|Elapsed \(wall" $R/$d/solve.err $R/$d/solve_time.txt 2>/dev/null
  "$PY" - "$R/$d/SOLVE_RECEIPT.json" <<'EOF'
import json, sys
try:
    r = json.load(open(sys.argv[1]))
    out = {k: r.get(k) for k in ("status", "termination_condition", "objective", "objective_lp", "solve_seconds", "peak_rss_bytes", "solver_profile", "label")}
    out["threads"] = (r.get("solver_parameters") or {}).get("Threads"); out["snapshots"] = (r.get("input_network") or {}).get("snapshots")
    out["lp"] = {k: (r.get("lp") or {}).get(k) for k in ("num_row", "num_col", "nnz", "build_seconds")}
    out["peak_gib"] = round((r.get("peak_rss_bytes") or 0) / 2**30, 2)
    print("   receipt:", json.dumps(out))
except Exception as e:
    print("   receipt read fail", e)
EOF
done
