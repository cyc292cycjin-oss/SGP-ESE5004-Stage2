#!/bin/bash
# M10A probe 2 (read-only): linopy solve dispatch (file vs direct), 56x3h logs of the new network (M08b smoke, M12b), old network (s4m / s4n / s4o)
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
WT=/home/jin/wt_m10p_20261022
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
echo "===== 1. linopy Model.solve dispatch (io_api None -> ?) ====="
$PY - <<'P'
import linopy, re
from pathlib import Path
src = Path(linopy.model.__file__).read_text(); L = src.splitlines()
i = src.index("def solve("); body = src[i:]
j = body.index('if io_api == "direct"') if 'if io_api == "direct"' in body else body.index("io_api")
start = src[:i].count("\n") + 1
for k, line in enumerate(body.splitlines()):
    if re.search(r'io_api|problem_fn|solve_problem|get_problem_file|keep_files|maybe_remove|unlink|remove\(', line):
        print(start + k, line.rstrip()[:170])
    if k > 260: break
g = src.index("def get_problem_file")
print("--- get_problem_file ---"); print(src[g:g+900])
s = src.index("_solver_dir"); print("--- solver_dir init ---"); print(src[s-200:s+400])
P
echo
echo "===== 2. new network 56x3h: M08b smoke_s01 + M12b (profile, iterations, seconds, peak, coefficient statistics) ====="
for d in $MAIN/m08b/smoke_s01/integrated $MAIN/m08b/smoke_s01/disconnected $MAIN/m12b/integrated_minusVN $MAIN/m12b/integrated_minusTH $MAIN/m12b/integrated_minusLA; do
  [ -d $d ] || { echo "missing $d"; continue; }
  echo "--- $d"
  $PY - "$d" <<'P'
import json, sys
from pathlib import Path
d = Path(sys.argv[1]); r = json.loads((d / "SOLVE_RECEIPT.json").read_text())
print(dict(profile=r.get("solver_profile"), params=r.get("solver_parameters"), term=r.get("termination_condition"), objective=r.get("objective"), solve_seconds=r.get("solve_seconds"),
           lp={k: r.get("lp", {}).get(k) for k in ("num_row", "num_col", "nnz", "build_seconds")}, peak_gib=round((r.get("peak_rss_bytes") or 0) / 2**30, 2),
           snapshots=(r.get("input_network") or {}).get("snapshots"), truncated=(r.get("input_network") or {}).get("truncated_to"), stats=r.get("gurobi_log_stats")))
P
  grep -E "Optimize a model with|Matrix range|Objective range|Bounds range|RHS range|Barrier solved model|Barrier performed|Presolved:|Presolve time|Ordering time|Factor NZ|Factor Ops|Sub-optimal|Optimal objective|work units" $d/GUROBI_LOG_SCRUBBED.txt | head -14
done
echo
echo "===== 3. old network 56x3h and 365x24h logs under results_project (s4m / s4n / s4o / l23) ====="
for f in $(ls -d $MAIN/s4m*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4m*/*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4n*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4n*/*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4o*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4o*/*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4q*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4q*/*/*/GUROBI_LOG_SCRUBBED.txt 2>/dev/null | head -14); do
  echo "--- $f"
  r=$(dirname $f)/SOLVE_RECEIPT.json
  [ -f $r ] && $PY -c "import json,sys; r=json.load(open(sys.argv[1])); print(dict(profile=r.get('solver_profile'), term=r.get('termination_condition'), solve_seconds=r.get('solve_seconds'), rows=(r.get('lp') or {}).get('num_row'), nnz=(r.get('lp') or {}).get('nnz'), snapshots=(r.get('input_network') or {}).get('snapshots'), label=r.get('label'), peak_gib=round((r.get('peak_rss_bytes') or 0)/2**30,2)))" $r
  grep -E "Optimize a model with|Matrix range|Objective range|Bounds range|RHS range|Barrier solved model|Barrier performed|Sub-optimal|Optimal objective|Threads" $f | head -9
done
echo
echo "===== 4. results_project top level ====="
ls $MAIN
echo
echo "===== 5. R1 measure receipt: scaling / offset fields (are the exported LP arrays before or after the research scaling?) ====="
$PY - <<'P'
import json
R = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10p/measure_r1/R1/"
r = json.load(open(R + "SOLVE_RECEIPT.json"))
print({k: r.get(k) for k in ("solver_profile", "solver_parameters", "lp", "peak_rss_bytes", "stop_before_solve")})
print("scaling:", json.dumps(r.get("scaling"), ensure_ascii=False)[:900])
m = json.load(open(R + "lp/MATH_PROBLEM.json"))
print({k: m.get(k) for k in m if k != "arrays"})
print("arrays:", {k: (v.get("count"), v.get("dtype")) for k, v in m.get("arrays", {}).items()})
P
echo
echo "===== 6. 56x3h smoke LP size (post_smoke R1) ====="
$PY -c "import json; m=json.load(open('/home/jin/m10p_dry_s01/post_smoke/R1/lp/MATH_PROBLEM.json')); print({k: m.get(k) for k in ('num_row','num_col','nnz')})"
echo
echo "===== 7. git log of run_batch3.sh busy line ====="
cd $WT && git log --oneline -5 -- research/06_scope_redesign/p1_m10p_20261022/cloud_package/run_batch3.sh && git log -S"busy()" --oneline -- research/06_scope_redesign/p1_m10p_20261022/cloud_package/run_batch3.sh | head -3
echo "PROBE2_DONE"
