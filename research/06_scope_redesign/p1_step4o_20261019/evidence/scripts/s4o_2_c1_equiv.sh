#!/bin/bash
# S4O-2: equivalence of the pipeline C1 module (scripts_project/s4o_c1_precision.py, S4O branch) with the S4N pilot tool (s4n_c1_precision.py) on the
# S4N-1 56x3h solve (READ ONLY, no solver call). The S4N-1 results are not touched: the new module writes into a shadow folder made of symlinks
# (lp/, solution/, v5/, files) plus a COPY of EXPORTS.json.
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PKG=/home/jin/s4n_local/pkg/repo; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=$RM/results_project/s4n/s4n1/solve; NET=$RM/results_project/s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc
T=/home/jin/s4o_tmp/c1_equiv; rm -rf $T; mkdir -p $T/shadow
export PYTHONHASHSEED=0; unset GRB_LICENSE_FILE
for f in $D/*; do b=$(basename $f); [ "$b" = EXPORTS.json ] && cp -p $f $T/shadow/ || ln -s $f $T/shadow/$b; done
sha_before=$(sha256sum $D/EXPORTS.json | cut -c1-16)
$PY $RM/scripts_project/l23_violation_analysis.py --repo $RM --solve-dir $T/shadow --network $NET --scenario integrated --truncate 56 --label SMOKE_TEST_ONLY --out $T/shadow/VIOLATIONS.json > $T/va_new.log 2> $T/va_new.err
echo "VA_NEW_EXIT:$?"
$PY $PKG/scripts_project/l23_violation_analysis.py --repo $PKG --solve-dir $D --network $NET --scenario integrated --truncate 56 --label SMOKE_TEST_ONLY --out $T/VIOLATIONS_old.json > $T/va_old.log 2> $T/va_old.err
echo "VA_OLD_EXIT:$?"
$PY /home/jin/s4n_c1_precision.py --repo $PKG --solve-dir $D --network $NET --scenario integrated --truncate 56 --label SMOKE_TEST_ONLY --violations $T/VIOLATIONS_old.json --out-json $T/PP_old.json --out-md $T/PP_old.md > $T/c1_old.log 2> $T/c1_old.err
echo "C1_OLD_EXIT:$?"
/usr/bin/time -v $PY $RM/scripts_project/s4o_c1_precision.py run --repo $RM --solve-dir $T/shadow --network $NET --scenario integrated --truncate 56 --label SMOKE_TEST_ONLY --violations $T/shadow/VIOLATIONS.json > $T/c1_new.log 2> $T/c1_new.err
echo "C1_NEW_EXIT:$? $(grep -h 'Elapsed' $T/c1_new.err | tr -s ' \t' ' ') $(grep -h 'Maximum resident' $T/c1_new.err | tr -s ' \t' ' ')"; cat $T/c1_new.log
echo "S4N-1 EXPORTS.json unchanged: $([ "$(sha256sum $D/EXPORTS.json | cut -c1-16)" = "$sha_before" ] && echo yes || echo NO)"
$PY - $T/PP_old.json $T/shadow/PRECISION.json $T/VIOLATIONS_old.json $T/shadow/VIOLATIONS.json <<'P'
import json, sys
o, n, vo, vn = (json.load(open(p)) for p in sys.argv[1:5])
d = {}
d["a_diff_bn"] = (o["a_total_cost"]["returned_difference_bn"], n["a_total_cost"]["returned_difference_bn"])
d["b_totals"] = (o["b_primal_violations"]["first_order_cost_eur_all_rows"], n["b_primal_violations"]["first_order_cost_eur_all_rows"])
d["b_over"] = (o["b_primal_violations"]["rows_over_budget"], n["b_primal_violations"]["rows_over_budget"])
d["c_totals"] = (o["c_prices"]["totals_eur"], n["c_prices"]["totals_eur"])
mx = 0.0
for sec, key in (("b_primal_violations", "first_order_cost_bn"), ("c_prices", "S_plus_R_bn"), ("c_prices", "all_terms_bn")):
    for c, v in o[sec]["country_check"].items():
        mx = max(mx, abs(v[key] - n[sec]["country_check"][c][key]))
d["max_abs_country_diff_bn"] = mx
d["grade"] = (o["grade"], n["grade"]); d["acceptance_new"] = n["acceptance"]; d["gates_info_new"] = n["gates_information"]
d["violation_totals_equal"] = vo["totals"] == vn["totals"]
print(json.dumps(d, indent=1, default=str))
P
