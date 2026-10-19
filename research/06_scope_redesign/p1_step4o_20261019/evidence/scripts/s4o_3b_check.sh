#!/bin/bash
# S4O supplement 01 S4O-3' acceptance (READ ONLY): optimal; objective vs S4M-2 648,381,181,410.4515 EUR relative <= 1e-9; C1 executed in the run and
# registered in EXPORTS.json (solve and export folders); (a)(b)(c) grade equal to the S4O-2 equivalence result (S4N-1 solve, new module). Evidence copy.
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
P=/home/jin/s4o_local/pkg_e2e; R=$(ls -d $P/runs/*/ | head -1); E=$RM/research/06_scope_redesign/p1_step4o_20261019/evidence/s4o_3b; mkdir -p $E/integrated
$PY - $R $RM/research/06_scope_redesign/p1_step4o_20261019/evidence/s4o_2/PRECISION_S4N1_new_module.json $E/S4O3B_CHECK.json <<'P'
import hashlib, json, sys
from pathlib import Path
run, ref_p, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sd, ex = run / "integrated", run / "export" / "integrated"
rec = json.loads((sd / "SOLVE_RECEIPT.json").read_text()); pr = json.loads((sd / "PRECISION.json").read_text()); ref = json.loads(ref_p.read_text())
S4M2 = 648381181410.4515
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
exp_s, exp_e = json.loads((sd / "EXPORTS.json").read_text()), json.loads((ex / "EXPORTS.json").read_text())
c1_in_exports = all(f in e and e[f]["sha256"] == sha(d / f) for e, d in ((exp_s, sd), (exp_e, ex)) for f in ("PRECISION.json", "PRECISION.md", "VIOLATIONS.json"))
def country_max(a, b, sec, key):
    return max(abs(a[sec]["country_check"][c][key] - b[sec]["country_check"][c][key]) for c in a[sec]["country_check"])
res = dict(run=str(run), termination=rec.get("termination_condition"), solver_profile=rec.get("solver_profile"), solver_parameters=rec.get("solver_parameters"),
           input_network=rec.get("input_network"), objective=rec.get("objective"), s4m2_objective=S4M2, objective_rel_diff=(rec["objective"] - S4M2) / S4M2,
           c1_in_exports_solve_and_export=c1_in_exports, grade=pr["grade"], acceptance=pr["acceptance"], reference_grade_s4o2_equivalence=ref["grade"],
           grade_equal=(pr["grade"] == ref["grade"]),
           info_vs_s4o2_equivalence=dict(a_diff_bn=(pr["a_total_cost"]["returned_difference_bn"], ref["a_total_cost"]["returned_difference_bn"]),
                                         b_country_max_abs_diff_bn=country_max(pr, ref, "b_primal_violations", "first_order_cost_bn"),
                                         c_country_max_abs_diff_bn=country_max(pr, ref, "c_prices", "S_plus_R_bn")),
           gates_information=pr.get("gates_information"), interior_solution=json.loads((sd / "INTERIOR_CHECKS.json").read_text()).get("interior_solution"),
           peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30, solve_seconds=rec.get("solve_seconds"))
res["accepted"] = dict(optimal=res["termination"] == "optimal", objective_le_1e9=abs(res["objective_rel_diff"]) <= 1e-9, c1_in_exports=c1_in_exports, grade_equal=res["grade_equal"])
res["accepted"]["all"] = all(res["accepted"].values())
out.write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(dict(accepted=res["accepted"], objective_rel_diff=res["objective_rel_diff"], profile=res["solver_profile"], grade=res["grade"]["grade"], info=res["info_vs_s4o2_equivalence"]), default=str))
P
cp $R/STATUS.txt $E/STATUS.txt; cp $R/MONITOR_integrated.csv $E/ 2>/dev/null
for f in SOLVE_RECEIPT.json V5_GATES.json GUROBI_LOG_SCRUBBED.txt COUNTRY_COST_LEDGER.csv LEDGER_IDENTITY.json EXPORTS.json INTERIOR_CHECKS.json PRECISION.json PRECISION.md VIOLATIONS.json solve_log_scrubbed.txt solve_time.txt; do cp $R/export/integrated/$f $E/integrated/ 2>/dev/null; done
grep -hE "Elapsed|Maximum resident" $R/integrated/c1_violations.err $R/integrated/c1_precision.err > $E/integrated/c1_time.txt 2>/dev/null
cp /home/jin/s4o_3b_e2e.sh /home/jin/s4o_3b_check.sh $RM/research/06_scope_redesign/p1_step4o_20261019/evidence/scripts/
ls $R/*.tar.gz* 2>/dev/null; du -sh $R/export
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $E $R/export)
[ -z "$H" ] && echo "LICENCE_SCAN: no hit" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
