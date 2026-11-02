"""Supplement 05: session scripts derived from those of supplement 04 (outputs in new folders; the results of supplement 04 stay)."""
V = "/home/jin/v3/"


def conv(src, dst, pairs):
    s = open(V + src, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, a[:70]
        s = s.replace(a, b)
    open(V + dst, "w", encoding="utf-8").write(s)


conv("build_s4.sh", "build_s5.sh", [
    ("# V3 supplement 04 (review section 2.4 item 1, decision 179, plant lines carry stock output only): builds at a clean commit", "# V3 supplement 05 (review section 2 item 3, decision 180, only operating units on the source buses): builds at a clean commit"),
    ("results_project/v3/builds_bound/BUILD_STATUS.txt", "results_project/v3/builds_op/BUILD_STATUS.txt"),
    ("OUT=$MAIN/results_project/v3/builds_bound;", "OUT=$MAIN/results_project/v3/builds_op;"),
    ('--authorization "V3 supplement 04 build check, no solver call"', '--authorization "V3 supplement 05 build check, no solver call"'),
    ("$PY /home/jin/v3/chk_disc.py $MAIN/results_project/v3/builds_oneway/disconnected/disconnected_365_24h_unsolved.nc", "$PY /home/jin/v3/chk_disc.py $MAIN/results_project/v3/builds_bound/disconnected/disconnected_365_24h_unsolved.nc"),
])
conv("pathcheck5.sh", "pathcheck6.sh", [
    ("# V3 supplement 04: post-solve chain on the source-bus networks with HiGHS", "# V3 supplement 05: post-solve chain on the operating-only networks with HiGHS"),
    ("NETS=$MAIN/results_project/v3/builds_bound; RUN=$MAIN/results_project/v3/path_check5;", "NETS=$MAIN/results_project/v3/builds_op; RUN=$MAIN/results_project/v3/path_check6;"),
    ("V3 supplement 04 code path check", "V3 supplement 05 code path check"),
])
conv("smoke_s4.sh", "smoke_s5.sh", [
    ("# V3 supplement 04 section 2.4 item 3 (review section 3;", "# V3 supplement 05 section 2 item 5 (review section 3;"),
    ("first 56 snapshots of the source-bus 2920x3h networks", "first 56 snapshots of the operating-only 2920x3h networks"),
    ("(acceptance smoke after decision 179)", "(acceptance smoke after decision 180)"),
    ("E2=$MAIN/results_project/v3/builds_bound; RUN=$MAIN/results_project/v3/smoke_s4;", "E2=$MAIN/results_project/v3/builds_op; RUN=$MAIN/results_project/v3/smoke_s5;"),
    ("evidence/smoke_s4", "evidence/smoke_s5"),
    ('AUTH="V3 supplement 04 (user confirmation', 'AUTH="V3 supplement 05 (user confirmation'),
    ("local 56-snapshot smoke with the plant lines bound to stock output,", "local 56-snapshot smoke with only operating units on the source buses,"),
])
conv("dry_s4.sh", "dry_s5.sh", [
    ("# V3 supplement 04 section 2.4 item 4:", "# V3 supplement 05 section 2 item 6:"),
    ("B=$MAIN/results_project/v3/builds_bound; O=$MAIN/results_project/v3/dry_screen4;", "B=$MAIN/results_project/v3/builds_op; O=$MAIN/results_project/v3/dry_screen5;"),
])
conv("pkg_s4.sh", "pkg_s5.sh", [
    ("# V3 supplement 04 section 2.4 item 4:", "# V3 supplement 05 section 2 item 6:"),
    ("B=$MAIN/results_project/v3/builds_bound; O=$MAIN/results_project/v3/dry_screen4; DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_bound; C=$MAIN/results_project/v3/pkg_check4", "B=$MAIN/results_project/v3/builds_op; O=$MAIN/results_project/v3/dry_screen5; DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_op; C=$MAIN/results_project/v3/pkg_check5"),
])
conv("mk_def4.py", "mk_def5.py", [
    ('results_project/v3/builds_bound")', 'results_project/v3/builds_op")'),
])
print("written")
