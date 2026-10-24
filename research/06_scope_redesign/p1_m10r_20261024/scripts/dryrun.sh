#!/bin/bash
# M10R B4.3: local dry run of package v6 (no Gurobi: GRB_LICENSE_FILE removed, the no-solve modes point it to a non-existent file; no cloud, no upload).
#   STEP=pre     unpack v6 into /home/jin/m10r_dry/pkg; preflight guards (clean shell + a negative check), sha / networks / env / profile / code / tools; resources (information)
#   STEP=build   batch mode BUILD_ONLY=1: phase 0 (7 variants vs EXPECTED_VARIANTS.json) + every run R1-R11 with --stop-before-solve + BUILD_CHECK.json; compared run by run with the v5 dry run
#   STEP=only    BUILD_ONLY=1 --only R11 into its own RUN_DIR: variant R11, LP build to the pre-solve exit, BUILD_CHECK, no solve
#   STEP=repost  --repost R9 on the 56x3h keep-stock result (results_project/m10r/keepstock_v5 mapped as R9; smoke_s01 integrated / disconnected as R1 / R2 with the
#                batch reference) into a new folder, then --summary-s1 with the reposted R9
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022; DIST=$W/cloud_package_dist; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10r_20261024/evidence/dryrun_v6
D=/home/jin/m10r_dry; PKG=$D/pkg; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project; M=$MAIN/m10r
V5E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10a_20261022/evidence/dryrun_v5
mkdir -p $E
busy() { ps -eo args= | grep -E '[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
case "${STEP:?pre|build|only|repost}" in
  pre)
    [ -e $D ] && { echo "exists $D"; exit 2; }
    mkdir -p $D && cp -r $DIST $PKG || exit 1
    cd $PKG
    env -u GRB_LICENSE_FILE -u ALLOW_UNREGISTERED -u BUILD_ONLY -u POST_ONLY -u DRY -u TRUNCATE -u LEDGER_CMD PY=$PY PREFLIGHT_ONLY=guards bash preflight.sh > $D/PREFLIGHT_GUARDS.txt 2>&1; echo "PREFLIGHT_GUARDS_EXIT $?" >> $D/PREFLIGHT_GUARDS.txt
    env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=guards LEDGER_CMD="python x" bash preflight.sh > $D/PREFLIGHT_GUARDS_NEG.txt 2>&1; echo "PREFLIGHT_GUARDS_NEG_EXIT $? (LEDGER_CMD left in the shell: must FAIL)" >> $D/PREFLIGHT_GUARDS_NEG.txt
    env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=sha,networks,env,profile,code,tools bash preflight.sh > $D/PREFLIGHT.txt 2>&1; echo "PREFLIGHT_EXIT $?" >> $D/PREFLIGHT.txt
    env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=resources bash preflight.sh > $D/PREFLIGHT_RESOURCES_LOCAL.txt 2>&1; echo "PREFLIGHT_RESOURCES_EXIT $? (local machine, information only)" >> $D/PREFLIGHT_RESOURCES_LOCAL.txt
    echo "repo research/ present: $([ -e $PKG/repo/research ] && echo yes || echo no); repo files: $(find $PKG/repo -type f | wc -l); s4d_ledger_redo present: $([ -f $PKG/repo/scripts_project/s4d_ledger_redo.py ] && echo yes || echo no)" | tee $D/REPO_LAYOUT.txt
    cp $D/PREFLIGHT_GUARDS.txt $D/PREFLIGHT_GUARDS_NEG.txt $D/PREFLIGHT.txt $D/PREFLIGHT_RESOURCES_LOCAL.txt $D/REPO_LAYOUT.txt $PKG/PREFLIGHT_BASE_CHECK.json $PKG/PREFLIGHT_ENV_CHECK.json $E/ 2>/dev/null
    cat $D/PREFLIGHT_GUARDS.txt $D/PREFLIGHT_GUARDS_NEG.txt $D/PREFLIGHT.txt $D/PREFLIGHT_RESOURCES_LOCAL.txt;;
  build)
    cd $PKG || exit 1
    [ "$(busy)" = 0 ] || { echo "solver process running"; exit 3; }
    t0=$(date +%s)
    env -u GRB_LICENSE_FILE PY=$PY BUILD_ONLY=1 bash run_batch3.sh > $D/build_only.out 2>&1; echo "RUNNER_EXIT $? $(( $(date +%s) - t0 ))s" >> $D/build_only.out
    O=$PKG/runs/batch3
    cp $O/STATUS.txt $E/BUILD_ONLY_STATUS.txt; cp $D/build_only.out $E/
    mkdir -p $E/build_only
    for r in R1 R2 R3 R4 R5 R6 R7 R8 R9 R10 R11; do
      mkdir -p $E/build_only/$r
      for f in RUN.json BUILD_CHECK.json SOLVE_RECEIPT.json; do [ -f $O/$r/$f ] && cp $O/$r/$f $E/build_only/$r/; done
      [ -f $O/$r/lp/MATH_PROBLEM.json ] && cp $O/$r/lp/MATH_PROBLEM.json $E/build_only/$r/
      grep -hE "Maximum resident|Elapsed \(wall" $O/$r/solve.err > $E/build_only/$r/solve_time.txt 2>/dev/null
      [ -d $O/$r/lp ] && du -sb $O/$r/lp | cut -f1 > $E/build_only/$r/lp_bytes.txt
    done
    mkdir -p $E/variants; for r in R5 R6 R7 R8 R9 R10 R11; do cp $O/variants/$r/*_VARIANT_RECEIPT.json $E/variants/ 2>/dev/null; done
    cp $O/BATCH3_SUMMARY.json $O/BATCH3_SUMMARY.md $O/BASE_CHECK.json $E/ 2>/dev/null
    $PY /home/jin/m10r/buildcmp.py $E/build_only $V5E/build_only $E/BUILD_VS_V5.json
    tail -30 $O/STATUS.txt;;
  only)
    cd $PKG || exit 1
    [ "$(busy)" = 0 ] || { echo "solver process running"; exit 3; }
    O=$PKG/runs/only_r11; [ -e $O ] && { echo "exists $O"; exit 2; }
    t0=$(date +%s)
    env -u GRB_LICENSE_FILE PY=$PY BUILD_ONLY=1 RUN_DIR=$O bash run_batch3.sh --only R11 > $D/only_r11.out 2>&1; echo "RUNNER_EXIT $? $(( $(date +%s) - t0 ))s" >> $D/only_r11.out
    mkdir -p $E/only_r11; cp $O/STATUS.txt $E/only_r11/ONLY_STATUS.txt; cp $D/only_r11.out $E/only_r11/
    for f in RUN.json BUILD_CHECK.json SOLVE_RECEIPT.json; do [ -f $O/R11/$f ] && cp $O/R11/$f $E/only_r11/; done
    cp $O/variants/R11/*_VARIANT_RECEIPT.json $E/only_r11/ 2>/dev/null; ls $O > $E/only_r11/RUN_DIR_LISTING.txt; ls $O/*.tar.gz >> $E/only_r11/RUN_DIR_LISTING.txt 2>/dev/null
    $PY - $E/only_r11 $V5E/build_only/R11 <<'Q'
import json, sys
from pathlib import Path
a, b = Path(sys.argv[1]), Path(sys.argv[2])
ba, bb = json.loads((a / "BUILD_CHECK.json").read_text()), json.loads((b / "BUILD_CHECK.json").read_text())
r = dict(passed=ba["passed"], lp_equal_v5=all(ba["lp"][k] == bb["lp"][k] for k in ("num_row", "num_col", "nnz")), parameters_equal_v5=ba["parameters"] == bb["parameters"],
         network_sha256_equal_v5=ba["network_sha256"] == bb["network_sha256"], lp=ba["lp"], solver_calls=0)
(a / "ONLY_R11_VS_V5.json").write_text(json.dumps(r, indent=1)); print(json.dumps(r))
Q
    tail -15 $O/STATUS.txt;;
  repost)
    cd $PKG || exit 1
    P=$D/repost_demo; [ -e $P ] && { echo "exists $P"; exit 2; }
    N=$D/repost_nets; mkdir -p $P $N
    for sc in integrated disconnected; do
      ln -sf $MAIN/m08b/builds_s01/$sc/${sc}_BUILD_RECEIPT.json $N/${sc}_BUILD_RECEIPT.json
      ln -sf $MAIN/m08b/builds_s01/$sc/costs_active_research.csv $N/${sc}_costs_active_research.csv
    done
    cp $MAIN/m08b/smoke_s01/BATCH_REFERENCE.json $P/BATCH_REFERENCE.json
    map() {   # $1 rid $2 source run dir (hard-linked copy: read only, nothing of the source changes) $3 network $4 scenario $5 registered sha256
      local d=$P/$1; cp -al "$2" "$d"
      $PY - "$d" "$1" "$3" "$4" "$5" <<'Q'
import hashlib, json, sys, time
from pathlib import Path
d, rid, net, sc, reg = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
rec = json.loads((d / "SOLVE_RECEIPT.json").read_text())
h = hashlib.sha256(Path(net).read_bytes()).hexdigest()
assert h == rec["input_network"]["sha256"], "network differs from the receipt"
json.dump(dict(rid=rid, scenario=sc, network=net, network_sha256=h, registered_sha256=reg, profile=rec.get("solver_profile"), label="SMOKE_TEST_ONLY", truncate=56,
               output=str(d), source="56x3h local results mapped for the --repost dry run (M10R B4.3)", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())), open(d / "RUN.json", "w"), indent=1)
(d / ".cond").write_text(rec.get("termination_condition", "none") + "\n"); (d / ".ended").write_text("mapped\n"); (d / ".started").write_text("mapped\n")
print(rid, rec.get("termination_condition"), rec.get("objective"))
Q
    }
    jget() { $PY -c "import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'): d=d.get(k)
print(d)" "$1" "$2"; }
    BS=$MAIN/m08b/builds_s01
    map R1 $MAIN/m08b/smoke_s01/integrated $BS/integrated/integrated_2920_3h_unsolved.nc integrated "$(jget $BS/integrated/integrated_BUILD_RECEIPT.json network.sha256)"
    map R2 $MAIN/m08b/smoke_s01/disconnected $BS/disconnected/disconnected_2920_3h_unsolved.nc disconnected "$(jget $BS/disconnected/disconnected_BUILD_RECEIPT.json network.sha256)"
    map R9 $M/keepstock_v5 $M/variants/disconnected_keepstock_2920_3h_unsolved.nc disconnected "$(jget $M/variants/disconnected_keepstock_2920_3h_VARIANT_RECEIPT.json output.sha256)"
    for r in R1 R2 R9; do [ -f $P/$r/V6_ACCEPTANCE.json ] || echo "note: $r has no V6_ACCEPTANCE.json in the source"; done
    INTO=$P/s1; snap_before=$(find $P/R9 -type f -printf '%p %s %T@\n' | sort | sha256sum | cut -c1-16)
    t0=$(date +%s)
    env -u GRB_LICENSE_FILE PY=$PY ALLOW_UNREGISTERED=1 TRUNCATE=56 RUN_DIR=$P NETS=$N bash run_batch3.sh --repost R9 --into $INTO > $D/repost.out 2>&1; echo "RUNNER_EXIT $? $(( $(date +%s) - t0 ))s" >> $D/repost.out
    snap_after=$(find $P/R9 -type f -printf '%p %s %T@\n' | sort | sha256sum | cut -c1-16)
    env -u GRB_LICENSE_FILE PY=$PY ALLOW_UNREGISTERED=1 TRUNCATE=56 RUN_DIR=$P NETS=$N bash run_batch3.sh --summary-s1 --into $INTO --use R9=$INTO/R9 > $D/summary_s1.out 2>&1; echo "RUNNER_EXIT $?" >> $D/summary_s1.out
    mkdir -p $E/repost_r9
    cp $INTO/STATUS.txt $E/repost_r9/S1_STATUS.txt; cp $D/repost.out $D/summary_s1.out $E/repost_r9/
    for f in REPOST.json REPOST_CHECK.json LEDGER_REDO.json LEDGER_IDENTITY.json PRECISION.json PRECISION.md ALLOCATION.json V6_ACCEPTANCE.json STOP_CLASS.json EXPORTS.json; do [ -f $INTO/R9/$f ] && cp $INTO/R9/$f $E/repost_r9/; done
    [ -d $INTO/R9/m12_owen ] && { mkdir -p $E/repost_r9/m12_owen; cp $INTO/R9/m12_owen/OWEN.json $INTO/R9/m12_owen/OWEN.md $E/repost_r9/m12_owen/ 2>/dev/null; }
    cp $INTO/batch_s1/BATCH3_SUMMARY_S1.json $INTO/batch_s1/BATCH3_SUMMARY_S1.md $E/repost_r9/ 2>/dev/null
    ls $INTO/*.tar.gz > $E/repost_r9/PACKS.txt 2>/dev/null
    echo "source R9 folder unchanged by the repost: $([ "$snap_before" = "$snap_after" ] && echo yes || echo NO) ($snap_before / $snap_after)" | tee $E/repost_r9/SOURCE_UNCHANGED.txt
    tail -12 $INTO/STATUS.txt;;
esac
