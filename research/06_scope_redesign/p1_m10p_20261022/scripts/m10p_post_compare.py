"""M10P-5 (read only): the post-processing dry run on the M12b smoke results against the M12b results computed by the M12b scripts - same
inputs, so the leave-one-out quantities (c(N - i), c'(i), Owen dual-form share, margin, tolerance) of VN / TH / LA, the C1 grades and the
GATES_V6 labels must agree.

    python m10p_post_compare.py <post_smoke run dir> <M12B_LOO_TABLE.csv> <out json>
"""
import csv
import json
import sys
from pathlib import Path

out, table, dst = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
m12b = {r["country"]: r for r in csv.DictReader(open(table))}
loo = json.loads((out / "M12_LOO" / "LOO_CHECK.json").read_text())["check"]["countries"]
rows, ok = {}, True
for rid, cc in (("R5", "VN"), ("R6", "TH"), ("R7", "LA")):
    a, b = loo[cc], m12b[cc]
    pairs = dict(c_N_minus_i_raw=(a["c_N_minus_i_raw"], float(b["c_N_minus_i_raw"])), addback_eur=(a["addback_remaining_side_fom_eur"], float(b["addback_eur"])),
                 marginal_cost=(a["marginal_cost"], float(b["c_prime"])),
                 allocation=(a["allocation"], float(b["phi_dual"])), tolerance=(a["tolerance"], float(b["tolerance"])))
    diffs = {k: abs(x - y) for k, (x, y) in pairs.items()}
    prec = json.loads((out / rid / "PRECISION.json").read_text())["grade"]; v6 = json.loads((out / rid / "V6_ACCEPTANCE.json").read_text())["label"]
    same = all(d <= 1.0 for d in diffs.values()) and prec["grade"] == b["c1_grade"] and v6 == b["v6_label"] and a["passed"] is True
    ok &= same
    rows[cc] = dict(run=rid, dry_run={k: x for k, (x, y) in pairs.items()}, m12b={k: y for k, (x, y) in pairs.items()}, abs_difference_eur=diffs,
                    margin_bn=a["margin"] / 1e9, passed=a["passed"], c1_grade=(prec["grade"], b["c1_grade"]), v6=(v6, b["v6_label"]), agree=same)
res = dict(note="post-processing dry run (run_batch3.sh POST_ONLY=1 on the mapped smoke runs) vs the M12b evidence table; tolerance 1 EUR", agree=ok, countries=rows)
dst.write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(dict(agree=ok, margins_bn={c: round(v["margin_bn"], 4) for c, v in rows.items()}, max_abs_diff_eur=max(max(v["abs_difference_eur"].values()) for v in rows.values()))))
