"""Supplement 04: session scripts derived from those of supplement 03 (outputs in new folders; the one-way results stay)."""
V = "/home/jin/v3/"


def conv(src, dst, pairs):
    s = open(V + src, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, a[:70]
        s = s.replace(a, b)
    open(V + dst, "w", encoding="utf-8").write(s)


conv("build_s3.sh", "build_s4.sh", [
    ("# V3 supplement 03 (review item 2.2, one-way plant lines): builds at a clean commit", "# V3 supplement 04 (review section 2.4 item 1, decision 179, plant lines carry stock output only): builds at a clean commit"),
    ("results_project/v3/builds_oneway/BUILD_STATUS.txt", "results_project/v3/builds_bound/BUILD_STATUS.txt"),
    ("OUT=$MAIN/results_project/v3/builds_oneway;", "OUT=$MAIN/results_project/v3/builds_bound;"),
    ('--authorization "V3 supplement 02 build check, no solver call"', '--authorization "V3 supplement 04 build check, no solver call"'),
    ('--authorization "V3 supplement 03 build check, no solver call"', '--authorization "V3 supplement 04 build check, no solver call"'),
    ("$PY /home/jin/v3/chk_disc.py $MAIN/results_project/v3/builds_x1b/disconnected/disconnected_365_24h_unsolved.nc", "$PY /home/jin/v3/chk_disc.py $MAIN/results_project/v3/builds_oneway/disconnected/disconnected_365_24h_unsolved.nc"),
])
conv("pathcheck4.sh", "pathcheck5.sh", [
    ("# V3 supplement 03: post-solve chain on the one-way networks with HiGHS", "# V3 supplement 04: post-solve chain on the source-bus networks with HiGHS"),
    ("NETS=$MAIN/results_project/v3/builds_oneway; RUN=$MAIN/results_project/v3/path_check4;", "NETS=$MAIN/results_project/v3/builds_bound; RUN=$MAIN/results_project/v3/path_check5;"),
    ("V3 supplement 03 code path check", "V3 supplement 04 code path check"),
])
conv("smoke_s3.sh", "smoke_s4.sh", [
    ("# V3 supplement 03 item 2.4 (review section 3;", "# V3 supplement 04 section 2.4 item 3 (review section 3;"),
    ("first 56 snapshots of the one-way 2920x3h networks", "first 56 snapshots of the source-bus 2920x3h networks"),
    ("(acceptance smoke after the one-way change)", "(acceptance smoke after decision 179)"),
    ("E2=$MAIN/results_project/v3/builds_oneway; RUN=$MAIN/results_project/v3/smoke_s3;", "E2=$MAIN/results_project/v3/builds_bound; RUN=$MAIN/results_project/v3/smoke_s4;"),
    ("evidence/smoke_s3", "evidence/smoke_s4"),
    ('AUTH="V3 supplement 03 (user confirmation', 'AUTH="V3 supplement 04 (user confirmation'),
    ("local 56-snapshot smoke with one-way plant lines,", "local 56-snapshot smoke with the plant lines bound to stock output,"),
])
conv("dry_s3.sh", "dry_s4.sh", [
    ("# V3 supplement 03 item 2.5:", "# V3 supplement 04 section 2.4 item 4:"),
    ("B=$MAIN/results_project/v3/builds_oneway; O=$MAIN/results_project/v3/dry_screen3;", "B=$MAIN/results_project/v3/builds_bound; O=$MAIN/results_project/v3/dry_screen4;"),
])
conv("pkg_s3.sh", "pkg_s4.sh", [
    ("# V3 supplement 03 item 2.5:", "# V3 supplement 04 section 2.4 item 4:"),
    ("B=$MAIN/results_project/v3/builds_oneway; O=$MAIN/results_project/v3/dry_screen3; DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_oneway; C=$MAIN/results_project/v3/pkg_check3", "B=$MAIN/results_project/v3/builds_bound; O=$MAIN/results_project/v3/dry_screen4; DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_bound; C=$MAIN/results_project/v3/pkg_check4"),
])
conv("mk_def3.py", "mk_def4.py", [
    ('results_project/v3/builds_oneway")', 'results_project/v3/builds_bound")'),
])
print("written")
