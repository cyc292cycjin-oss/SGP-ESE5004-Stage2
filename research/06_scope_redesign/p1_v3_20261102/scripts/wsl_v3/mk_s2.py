"""smoke_s2.sh from smoke_s1.sh: X1b networks, two runs, no flat pair (RUN_PLAN_V3.md section 15.2)."""
s = open("/home/jin/v3/smoke_s1.sh", encoding="utf-8").read()
pairs = [
    ("# V3 supplement 01 step 4 (review decisions 3, 1; at most 4 local Gurobi calls,", "# V3 supplement 02 item 2.3.2 (review section 3; at most 2 local Gurobi calls,"),
    ("# and AnyConnect disconnected before the call): first 56 snapshots of the 2920x3h networks, serial: integrated E2, no_new_xb E2 (acceptance smoke after X1), integrated flat, no_new_xb flat (control, report\n# only), profile", "# and AnyConnect disconnected before the call): first 56 snapshots of the X1b 2920x3h networks, serial: integrated E2, no_new_xb E2 (acceptance smoke after X1b), profile"),
    ("E2=$MAIN/results_project/v3/builds; FL=$MAIN/results_project/v3/builds_flat; RUN=$MAIN/results_project/v3/smoke_s1; ST=$RUN/STATUS.txt", "E2=$MAIN/results_project/v3/builds_x1b; RUN=$MAIN/results_project/v3/smoke_s2; ST=$RUN/STATUS.txt"),
    ("EV=$WT/research/06_scope_redesign/p1_v3_20261102/evidence/smoke_s1", "EV=$WT/research/06_scope_redesign/p1_v3_20261102/evidence/smoke_s2"),
    ('AUTH="V3 supplement 01 step 4 (user confirmation', 'AUTH="V3 supplement 02 (user confirmation'),
    ("local 56-snapshot smoke, integrated and no_new_xb, E2 and flat, profile", "local 56-snapshot smoke after X1b, integrated and no_new_xb, profile"),
    ('for spec in "integrated integrated $E2" "no_new_xb no_new_xb $E2" "integrated_flat integrated $FL" "no_new_xb_flat no_new_xb $FL"; do\n  set -- $spec; rid=$1; sc=$2; nd=$3\n  dir=', 'for spec in "integrated integrated $E2" "no_new_xb no_new_xb $E2"; do\n  set -- $spec; rid=$1; sc=$2; nd=$3\n  dir='),
    ('for pair in "integrated no_new_xb BATCH_REFERENCE.json M12_BENEFIT" "integrated_flat no_new_xb_flat BATCH_REFERENCE_FLAT.json M12_BENEFIT_FLAT"; do', 'for pair in "integrated no_new_xb BATCH_REFERENCE.json M12_BENEFIT"; do'),
    ('for spec in "integrated integrated $E2" "no_new_xb no_new_xb $E2" "integrated_flat integrated $FL" "no_new_xb_flat no_new_xb $FL"; do\n  set -- $spec; rid=$1; sc=$2; nd=$3\n  [ -f', 'for spec in "integrated integrated $E2" "no_new_xb no_new_xb $E2"; do\n  set -- $spec; rid=$1; sc=$2; nd=$3\n  [ -f'),
    ('--v2-run $MAIN/results_project/dfx_v3/smoke_v2 > $RUN/eval.log 2>&1; log EVAL "exit=$?"\n', '--v2-run $MAIN/results_project/dfx_v3/smoke_v2 > $RUN/eval.log 2>&1; log EVAL "exit=$?"\nenv -u GRB_LICENSE_FILE "$PY" scripts_project/v3_screen_tables.py --out-dir $RUN --runs integrated,no_new_xb > $RUN/screen.log 2>&1; log SCREEN_TABLES "exit=$?"\n'),
]
for a, b in pairs:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open("/home/jin/v3/smoke_s2.sh", "w", encoding="utf-8").write(s); print("written")
