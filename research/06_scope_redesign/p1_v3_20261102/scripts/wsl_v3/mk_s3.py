"""Supplement 03: session scripts derived from those of supplement 02 (outputs in new folders; the X1b two-way results stay)."""
V = "/home/jin/v3/"


def conv(src, dst, pairs):
    s = open(V + src, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, a[:70]
        s = s.replace(a, b)
    open(V + dst, "w", encoding="utf-8").write(s)


conv("build_s2.sh", "build_s3.sh", [
    ("# V3 supplement 02 (review section 2.3 item 1): builds at a clean commit", "# V3 supplement 03 (review item 2.2, one-way plant lines): builds at a clean commit"),
    ("results_project/v3/builds_x1b/BUILD_STATUS.txt", "results_project/v3/builds_oneway/BUILD_STATUS.txt"),
    ("OUT=$MAIN/results_project/v3/builds_x1b;", "OUT=$MAIN/results_project/v3/builds_oneway;"),
    ('''"integrated integrated 2920_3h 56" "no_new_xb no_new_xb 2920_3h 56" "integrated integrated 365_24h 0"''', '''"integrated integrated 365_24h 0"'''),
    ('''du -sh $OUT >> $ST
''', '''for s in integrated no_new_xb; do
  L=$OUT/lp_${s}_2920_3h_t56; mkdir -p $L
  env GRB_LICENSE_FILE=/nonexistent /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/$s/${s}_2920_3h_unsolved.nc --scenario $s --output $L --solver gurobi --truncate 56 --label SMOKE_TEST_ONLY --authorization "V3 supplement 03 build check, no solver call" --stop-before-solve > $L/out.log 2> $L/err.log
  echo "LP_${s}_t56:$?:$(tail -1 $L/out.log | cut -c1-120)" >> $ST
  rm -f $L/*.lp
done
$PY /home/jin/v3/chk_disc.py $MAIN/results_project/v3/builds_x1b/disconnected/disconnected_365_24h_unsolved.nc $OUT/disconnected/disconnected_365_24h_unsolved.nc >> $ST 2>&1
du -sh $OUT >> $ST
'''),
])
conv("pathcheck3.sh", "pathcheck4.sh", [
    ("# V3 supplement 02: post-solve chain on the X1b networks with HiGHS", "# V3 supplement 03: post-solve chain on the one-way networks with HiGHS"),
    ("NETS=$MAIN/results_project/v3/builds_x1b; RUN=$MAIN/results_project/v3/path_check3;", "NETS=$MAIN/results_project/v3/builds_oneway; RUN=$MAIN/results_project/v3/path_check4;"),
    ("V3 supplement 02 code path check", "V3 supplement 03 code path check"),
    (''' "bridge_160_162 integrated $NETS/bridge_160_162/integrated_365_24h_unsolved.nc"; do''', '''; do'''),
    (''' "bridge_160_162 --build-receipt $NETS/bridge_160_162/integrated_BUILD_RECEIPT.json"; do''', '''; do'''),
])
conv("smoke_s2.sh", "smoke_s3.sh", [
    ("# V3 supplement 02 item 2.3.2 (review section 3;", "# V3 supplement 03 item 2.4 (review section 3;"),
    ("first 56 snapshots of the X1b 2920x3h networks", "first 56 snapshots of the one-way 2920x3h networks"),
    ("(acceptance smoke after X1b)", "(acceptance smoke after the one-way change)"),
    ("E2=$MAIN/results_project/v3/builds_x1b; RUN=$MAIN/results_project/v3/smoke_s2;", "E2=$MAIN/results_project/v3/builds_oneway; RUN=$MAIN/results_project/v3/smoke_s3;"),
    ("evidence/smoke_s2", "evidence/smoke_s3"),
    ('AUTH="V3 supplement 02 (user confirmation', 'AUTH="V3 supplement 03 (user confirmation'),
    ("local 56-snapshot smoke after X1b,", "local 56-snapshot smoke with one-way plant lines,"),
])
conv("dry_s2.sh", "dry_s3.sh", [
    ("# V3 supplement 02 item 2.4.2:", "# V3 supplement 03 item 2.5:"),
    ("B=$MAIN/results_project/v3/builds_x1b; O=$MAIN/results_project/v3/dry_screen;", "B=$MAIN/results_project/v3/builds_oneway; O=$MAIN/results_project/v3/dry_screen3;"),
])
conv("pkg_s2.sh", "pkg_s3.sh", [
    ("# V3 supplement 02 item 2.4.2:", "# V3 supplement 03 item 2.5:"),
    ("B=$MAIN/results_project/v3/builds_x1b; O=$MAIN/results_project/v3/dry_screen; DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3; C=$MAIN/results_project/v3/pkg_check", "B=$MAIN/results_project/v3/builds_oneway; O=$MAIN/results_project/v3/dry_screen3; DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_oneway; C=$MAIN/results_project/v3/pkg_check3"),
])
conv("mk_def.py", "mk_def3.py", [
    ('results_project/v3/builds_x1b")', 'results_project/v3/builds_oneway")'),
    ('T16 = "formal_barrier_1e6_t16"; BUILD = "4df45b569ff314e710a75ed70c4d1e381474844e"', 'T16 = "formal_barrier_1e6_t16"; BUILD = json.loads((M / "integrated/integrated_BUILD_RECEIPT.json").read_text())["code_sha"]'),
])
print("written")
