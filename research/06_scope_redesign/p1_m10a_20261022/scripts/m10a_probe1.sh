#!/bin/bash
# M10A probe 1 (read-only except a throw-away fake s2_solve.py under /home/jin/m10a_tmp): linopy defaults, busy() double count, S4O busy, logs
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
WT=/home/jin/wt_m10p_20261022
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
echo "===== 1. linopy version and solve defaults ====="
$PY - <<'P'
import linopy, inspect, re
from pathlib import Path
print("linopy", linopy.__version__)
src = Path(linopy.model.__file__).read_text()
i = src.index("def solve(")
print(src[i:i+1400])
for pat in ("solver_dir", "gettempdir", "get_problem_file", "NamedTemporaryFile", "keep_files"):
    for m in re.finditer(pat, src):
        ln = src[:m.start()].count("\n") + 1
        print(f"{pat} @ model.py:{ln}: {src.splitlines()[ln-1].strip()[:160]}")
        break
s2 = Path(linopy.solvers.__file__).read_text()
for pat in ("class Gurobi", "io_api", "gurobipy.read", "to_gurobipy", "problem_fn", "maybe_adjust", "os.remove", "unlink"):
    hits = [src_ln for src_ln, line in enumerate(s2.splitlines(), 1) if pat in line]
    print(f"solvers.py {pat}: lines {hits[:12]}")
j = s2.index("class Gurobi")
k = s2.index("def solve_problem", j)
print(s2[k:k+1800])
P
echo
echo "===== 2. busy() double count: launch a fake s2_solve.py the way run_batch3.sh does ====="
T=/home/jin/m10a_tmp; mkdir -p $T/scripts_project
cat > $T/scripts_project/s2_solve.py <<'P'
import time, sys
time.sleep(25)
P
( cd $T && exec setsid /usr/bin/time -v env GRB_LICENSE_FILE=/nonexistent/x $PY $T/scripts_project/s2_solve.py --repo $T --network n.nc --scenario integrated > $T/solve.log 2> $T/solve.err ) &
PID=$!; sleep 3
PG=$(ps -o pgid= -p "$PID" | tr -d ' ')
echo "pid=$PID pgid=$PG"
echo "--- ps -eo cmd lines matching [s]2_solve.py ---"
ps -eo pid,pgid,comm,cmd | grep -E '[s]2_solve\.py'
echo "--- busy() as in run_batch3.sh: $(ps -eo cmd | grep -cE '[s]2_solve.py')"
echo "--- candidate fix (exclude time/setsid/env wrappers): $(ps -eo args= | grep -E '[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env ')"
echo "--- candidate fix 2 (comm starts with python): $(ps -eo comm=,args= | grep -E '^python[^ ]* .*[s]2_solve\.py' | grep -c .)"
echo "--- pgrep -g members: $(pgrep -g $PG | tr '\n' ' ')"
kill -TERM -- -$PG 2>/dev/null; sleep 2; echo "--- after TERM, alive in group: $(pgrep -g $PG | wc -l)"
wait $PID 2>/dev/null; echo "exit=$?"
echo "--- solve.err head ---"; head -5 $T/solve.err
rm -rf $T
echo
echo "===== 3. S4O cloud script busy() ====="
grep -rnE "busy|s2_solve" $WT/research/06_scope_redesign/p1_step4o_20261019/cloud_package/*.sh 2>/dev/null | head -20
ls $WT/research/06_scope_redesign/p1_step4o_20261019/ 2>/dev/null | head
echo
echo "===== 4. post_smoke dry-run dirs (56x3h post-processing timings) ====="
for D in /home/jin/m10p_dry_s01/post_smoke /home/jin/m10p_dry/post_smoke; do
  [ -d $D ] || { echo "missing $D"; continue; }
  echo "--- $D ---"; ls $D; ls $D/R1
  for r in R1 R2 R5 R6 R7; do
    for f in c1_violations.err c1_precision.err m12_owen.err; do
      [ -f $D/$r/$f ] && echo "$r/$f: $(grep -hE 'Elapsed \(wall|Maximum resident' $D/$r/$f | tr '\n' ' ')"
    done
    [ -f $D/$r/ALLOCATION.json ] && echo "$r ALLOCATION seconds: $($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('seconds'))" $D/$r/ALLOCATION.json)"
    [ -f $D/$r/m12_owen/RHS_AUDIT.json ] && echo "$r RHS_AUDIT seconds/peak: $($PY -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('seconds'), d.get('peak_rss_gib'))" $D/$r/m12_owen/RHS_AUDIT.json)"
    [ -f $D/$r/PRECISION.json ] && echo "$r PRECISION seconds: $($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('seconds'))" $D/$r/PRECISION.json)"
    [ -f $D/$r/VIOLATIONS.json ] && echo "$r VIOLATIONS seconds: $($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('seconds'))" $D/$r/VIOLATIONS.json)"
  done
  grep -E "^(VIOLATIONS|C1|M12|M12_OWEN|RHS_CHECK|V6|REGRADE|BATCH_REFERENCE|M12_LOO|M12_BENEFIT|SUMMARY|PACK|PROFILE|DONE|START)" $D/STATUS.txt | head -40
done
echo
echo "===== 5. Gurobi scrubbed logs: coefficient statistics, model size, iterations (new and old networks, 56x3h) ====="
for f in $MAIN/m08b/smoke_s01/integrated/GUROBI_LOG_SCRUBBED.txt $MAIN/m08b/smoke_s01/disconnected/GUROBI_LOG_SCRUBBED.txt $MAIN/m12b/integrated_minusVN/GUROBI_LOG_SCRUBBED.txt \
         $(ls $MAIN/s4m/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4m/*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4n/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4n/*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4o*/*/GUROBI_LOG_SCRUBBED.txt $MAIN/s4o*/*/*/GUROBI_LOG_SCRUBBED.txt 2>/dev/null | head -12); do
  [ -f "$f" ] || continue
  echo "--- $f"
  grep -E "Optimize a model with|Coefficient statistics|Matrix range|Objective range|Bounds range|RHS range|Barrier solved model|Barrier performed|Presolved:|Presolve time|Ordering time|Factor NZ|Factor Ops|Threads|Time limit|Sub-optimal|Optimal objective" "$f" | head -20
done
echo
echo "===== 6. results_project listing (top level) ====="
ls $MAIN
ls $MAIN/m08b $MAIN/m12b 2>/dev/null
echo
echo "===== 7. R1 measure receipt: scaling / offset fields ====="
$PY - <<'P'
import json
r = json.load(open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10p/measure_r1/R1/SOLVE_RECEIPT.json"))
print({k: r.get(k) for k in ("solver_profile", "solver_parameters", "lp", "peak_rss_bytes", "stop_before_solve")})
print("scaling:", json.dumps(r.get("scaling"))[:600])
m = json.load(open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10p/measure_r1/R1/lp/MATH_PROBLEM.json"))
print({k: m.get(k) for k in m if k != "arrays"})
P
echo "PROBE1_DONE"
