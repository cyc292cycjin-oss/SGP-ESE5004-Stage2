#!/bin/bash
# S4O-3 after the stop (READ ONLY, no solver, licence variable removed): (1) C1 of the three S4N C2 calibration runs (pypsa_eur_default as copied:
# threads 32, lowercase keys) in shadow folders (symlinks + copied EXPORTS.json; the S4N results are not touched); (2) the S4O-3 integrated run
# against S4M-2 profile A and S4N C2 by country (ledger totals), B16, iterations, work units, the log gap at the returned iterate.
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=$RM/results_project/s4m/s4m1/builds; C2=$RM/results_project/s4n/s4n_c2/solves; T=/home/jin/s4o_tmp/c2_c1; rm -rf $T; mkdir -p $T
E=$RM/research/06_scope_redesign/p1_step4o_20261019/evidence/s4o_3; mkdir -p $E/s4n_c2_c1
export PYTHONHASHSEED=0; unset GRB_LICENSE_FILE
cd $RM
for spec in "cal_integrated:integrated:integrated" "cal_disconnected:disconnected:disconnected" "cal_integrated_nze:integrated_nze:integrated"; do
  IFS=: read tag bt sc <<< "$spec"; d=$C2/$tag; s=$T/$tag; mkdir -p $s
  before=$(sha256sum $d/EXPORTS.json | cut -c1-16)
  for f in $d/*; do b=$(basename $f); [ "$b" = EXPORTS.json ] && cp -p $f $s/ || ln -s $f $s/$b; done
  net=$B/$bt/${sc}_2920_3h_unsolved.nc
  $PY scripts_project/l23_violation_analysis.py --repo $RM --solve-dir $s --network $net --scenario $sc --truncate 56 --label SMOKE_TEST_ONLY --out $s/VIOLATIONS.json > $s.va.log 2>&1
  $PY scripts_project/s4o_c1_precision.py run --repo $RM --solve-dir $s --network $net --scenario $sc --truncate 56 --label SMOKE_TEST_ONLY --violations $s/VIOLATIONS.json > $s.c1.log 2>&1
  echo "$tag: $(tail -1 $s.c1.log | cut -c1-200) | S4N file unchanged: $([ "$(sha256sum $d/EXPORTS.json | cut -c1-16)" = "$before" ] && echo yes || echo NO)"
  cp $s/PRECISION.json $E/s4n_c2_c1/${tag}_PRECISION.json; cp $s/PRECISION.md $E/s4n_c2_c1/${tag}_PRECISION.md
done
# reference: the S4N C2 batch's own difference (both STEPS runs exist) -> re-grade the shadow copies (information)
$PY scripts_project/s4o_c1_precision.py reference --integrated $C2/cal_integrated --disconnected $C2/cal_disconnected --out $T/REF.json > /dev/null
for tag in cal_integrated cal_disconnected cal_integrated_nze; do $PY scripts_project/s4o_c1_precision.py regrade --solve-dir $T/$tag --reference $T/REF.json | cut -c1-160; cp $T/$tag/PRECISION.json $E/s4n_c2_c1/${tag}_PRECISION_regraded.json; done
$PY - $RM <<'P' > $E/S4O3_INTEGRATED_INFO.json
import json, re, sys
from pathlib import Path
import pandas as pd
R = Path(sys.argv[1]) / "results_project"
runs = dict(s4o=R / "s4o/s4o3/solves/s4o_integrated", profile_A=R / "s4m/s4m2/solves/s4m_A_integrated", s4n_c2=R / "s4n/s4n_c2/solves/cal_integrated")
out = {}
for k, d in runs.items():
    rec = json.loads((d / "SOLVE_RECEIPT.json").read_text()); g = json.loads((d / "V5_GATES.json").read_text())
    it = sec = wu = None
    for line in (d / "GUROBI_LOG_SCRUBBED.txt").read_text(errors="ignore").splitlines():
        m = re.match(r"Barrier solved model in (\d+) iterations and ([\d.]+) seconds(?: \(([\d.]+) work units\))?", line)
        if m: it, sec, wu = int(m.group(1)), float(m.group(2)), float(m.group(3) or "nan")
    kkt = json.loads((d / "v5/kkt_summary.json").read_text()) if (d / "v5/kkt_summary.json").exists() else {}
    out[k] = dict(profile=rec.get("solver_profile"), parameters=rec.get("solver_parameters"), termination=rec.get("termination_condition"), objective=rec.get("objective"),
                  iterations=it, barrier_seconds=sec, work_units=wu, solve_seconds=rec.get("solve_seconds"), peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30,
                  b16=(g.get("B16_LEDGER") or {}).get("relative_error"), all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"),
                  kkt_relative_gap=kkt.get("relative_gap"), kkt_absolute_gap_eur=kkt.get("absolute_gap"),
                  ledger_total_bn=(pd.read_csv(d / "COUNTRY_COST_LEDGER.csv", index_col=0)["total"] / 1e9).round(6).to_dict())
A = out["profile_A"]["objective"]
for k in ("s4o", "s4n_c2"):
    out[k]["objective_rel_diff_vs_A"] = (out[k]["objective"] - A) / A; out[k]["objective_abs_diff_vs_A_eur"] = out[k]["objective"] - A
    out[k]["ledger_change_vs_A_bn"] = {c: round(v - out["profile_A"]["ledger_total_bn"].get(c, 0.0), 6) for c, v in out[k]["ledger_total_bn"].items()}
out["standard_decision_107"] = dict(objective_rel_tol=1e-5, b16_tol=1e-6, note="country-difference criterion needs the disconnected run (not run: stopped)")
out["verdict"] = dict(objective_within_1e_5=abs(out["s4o"]["objective_rel_diff_vs_A"]) <= 1e-5, b16_within_1e_6=(out["s4o"]["b16"] or 1) <= 1e-6)
print(json.dumps(out, indent=1, default=str))
P
$PY -c "import json; d=json.load(open('$E/S4O3_INTEGRATED_INFO.json')); [print(k, {x: d[k].get(x) for x in ('objective','iterations','barrier_seconds','work_units','b16','kkt_relative_gap','objective_rel_diff_vs_A')}) for k in ('s4o','profile_A','s4n_c2')]; print(d['verdict']); print('max |ledger change vs A| bn s4o', max(abs(v) for v in d['s4o']['ledger_change_vs_A_bn'].values()), 's4n_c2', max(abs(v) for v in d['s4n_c2']['ledger_change_vs_A_bn'].values()))"
