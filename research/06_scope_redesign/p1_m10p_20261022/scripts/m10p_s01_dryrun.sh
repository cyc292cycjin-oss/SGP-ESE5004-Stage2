#!/bin/bash
# M10P supplement 01 section 2: second local dry run of the slimmed deployment package (code archive without research/). No Gurobi
# (GRB_LICENSE_FILE removed; build-only / post-only modes point it to a non-existent file), no cloud, no upload. Every Python process runs with
# the access trace scripts/m10p_s01_trace/sitecustomize.py (records any open / list / stat under <package>/repo/research/ and local paths).
#   STEP=pre   unpack the package in the cloud folder layout (/home/jin/m10p_dry_s01/pkg); tracer positive control; preflight without the licence
#              section (resources as local information only)
#   STEP=build run_batch3.sh BUILD_ONLY=1: phase 0 generates the 7 variants and compares them with EXPECTED_VARIANTS.json; every run R1-R11 once
#              with s2_solve.py --stop-before-solve (LP built and exported, parameters fixed, no solver call) + BUILD_CHECK.json
#   STEP=post  post-processing (POST_ONLY=1, no solve) on the M12b smoke results mapped to R1 (M08b smoke_s01 integrated), R2 (smoke_s01
#              disconnected), R5 / R6 / R7 (M12b integrated_minusVN / TH / LA), as in M10P-5; comparison with the M12b evidence table
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022; DIST=$W/cloud_package_dist; E=$W/evidence/s01/dryrun
D=/home/jin/m10p_dry_s01; PKG=$D/pkg; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
T12B=/home/jin/wt_m10p_20261022/research/06_scope_redesign/p1_m12b_20261021/evidence/M12B_LOO_TABLE.csv
mkdir -p $E
trace_env() { echo "PYTHONPATH=$D/trace M10P_TRACE_REPO=$PKG/repo M10P_TRACE_ROOT=$D M10P_TRACE_LOG=$D/TRACE_$1.log"; }
case "${STEP:?pre|build|post}" in
  pre)
    [ -e $D ] && { echo "exists $D"; exit 2; }
    mkdir -p $D/trace && cp $W/scripts/m10p_s01_trace/sitecustomize.py $D/trace/ && cp -r $DIST $PKG || exit 1
    # positive control: the tracer must record accesses under <package>/repo/research/ (the folder does not exist yet)
    env -u GRB_LICENSE_FILE $(trace_env control) $PY -c "import os, pathlib; p = '$PKG/repo/research/x.json'; os.path.exists(p); pathlib.Path(p).is_file(); list(pathlib.Path('$PKG/repo').glob('research/*'));
try: open(p)
except OSError: pass"
    echo "TRACER_CONTROL $(grep -c '^RESEARCH' $D/TRACE_control.log 2>/dev/null || echo 0) lines" | tee $D/TRACER_CONTROL.txt; cat $D/TRACE_control.log >> $D/TRACER_CONTROL.txt
    cd $PKG
    env -u GRB_LICENSE_FILE $(trace_env pre) PY=$PY PREFLIGHT_ONLY=sha,networks,env,profile,code,tools bash preflight.sh > $D/PREFLIGHT.txt 2>&1; echo "PREFLIGHT_EXIT $?" >> $D/PREFLIGHT.txt
    env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=resources bash preflight.sh > $D/PREFLIGHT_RESOURCES_LOCAL.txt 2>&1; echo "PREFLIGHT_RESOURCES_EXIT $? (local machine, information only)" >> $D/PREFLIGHT_RESOURCES_LOCAL.txt
    echo "repo research/ present: $([ -e $PKG/repo/research ] && echo yes || echo no); repo files: $(find $PKG/repo -type f | wc -l)" | tee $D/REPO_LAYOUT.txt
    cp $D/TRACER_CONTROL.txt $D/PREFLIGHT.txt $D/PREFLIGHT_RESOURCES_LOCAL.txt $D/REPO_LAYOUT.txt $PKG/PREFLIGHT_BASE_CHECK.json $PKG/PREFLIGHT_ENV_CHECK.json $E/ 2>/dev/null
    cat $D/PREFLIGHT.txt $D/PREFLIGHT_RESOURCES_LOCAL.txt;;
  build)
    cd $PKG || exit 1
    [ "$(ps -eo cmd | grep -cE '[s]2_solve.py')" = 0 ] || { echo "solver process running"; exit 3; }
    t0=$(date +%s)
    env -u GRB_LICENSE_FILE $(trace_env build) PY=$PY BUILD_ONLY=1 bash run_batch3.sh > $D/build_only.out 2>&1; echo "RUNNER_EXIT $? $(( $(date +%s) - t0 ))s" >> $D/build_only.out
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
    tail -30 $O/STATUS.txt;;
  post)
    cd $PKG || exit 1
    P=$D/post_smoke; [ -e $P ] && { echo "exists $P"; exit 2; }
    N=$D/post_smoke_nets; mkdir -p $P $N
    for sc in integrated disconnected; do   # build receipts of the smoke networks (G2.1: truncated runs -> the 2920x3h network SHA) and the cost tables
      ln -s $MAIN/m08b/builds_s01/$sc/${sc}_BUILD_RECEIPT.json $N/${sc}_BUILD_RECEIPT.json
      ln -s $MAIN/m08b/builds_s01/$sc/costs_active_research.csv $N/${sc}_costs_active_research.csv
    done
    map() {   # $1 rid $2 source run dir $3 network $4 scenario $5 registered sha256
      local d=$P/$1; mkdir -p $d
      rsync -aL --exclude VIOLATIONS.json --exclude 'PRECISION.*' --exclude 'ALLOCATION*' --exclude m12_owen/ --exclude m12_loo_rhs/ --exclude 'V6_ACCEPTANCE*' \
            --exclude 'c1_*' --exclude 'm12*' --exclude v6.err --exclude C1_ERR_TAIL.txt --exclude EXPORTS.json --exclude STOP_CLASS.json "$2/" "$d/"
      $PY - "$d" "$1" "$3" "$4" "$5" <<'Q'
import hashlib, json, sys, time
from pathlib import Path
d, rid, net, sc, reg = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
rec = json.loads((d / "SOLVE_RECEIPT.json").read_text())
(d / "EXPORTS.json").write_text(json.dumps(rec.get("exports") or {}, indent=1))   # solve-time export list (s2_solve writes EXPORTS.json = receipt exports)
h = hashlib.sha256(Path(net).read_bytes()).hexdigest()
assert h == rec["input_network"]["sha256"], "network differs from the receipt"
json.dump(dict(rid=rid, scenario=sc, network=net, network_sha256=h, registered_sha256=reg, profile=rec.get("solver_profile"), label="SMOKE_TEST_ONLY", truncate=56,
               output=str(d), source="M12b / M08b smoke results (56x3h, SMOKE_TEST_ONLY) mapped for the post-processing dry run", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
          open(d / "RUN.json", "w"), indent=1)
(d / ".cond").write_text(rec.get("termination_condition", "none") + "\n"); (d / ".ended").write_text("mapped\n"); (d / ".started").write_text("mapped\n")
print(rid, rec.get("termination_condition"), rec.get("objective"))
Q
    }
    jget() { $PY -c "import json,sys; print(json.load(open(sys.argv[1]))['output']['sha256'])" "$1"; }
    BS=$MAIN/m08b/builds_s01; V=$MAIN/m12b/variants
    map R1 $MAIN/m08b/smoke_s01/integrated $BS/integrated/integrated_2920_3h_unsolved.nc integrated "$($PY -c "import json; print(json.load(open('$BS/integrated/integrated_BUILD_RECEIPT.json'))['network']['sha256'])")"
    map R2 $MAIN/m08b/smoke_s01/disconnected $BS/disconnected/disconnected_2920_3h_unsolved.nc disconnected "$($PY -c "import json; print(json.load(open('$BS/disconnected/disconnected_BUILD_RECEIPT.json'))['network']['sha256'])")"
    for x in "R5 VN" "R6 TH" "R7 LA"; do set -- $x
      map $1 $MAIN/m12b/integrated_minus$2 $V/integrated_minus$2_2920_3h_unsolved.nc integrated "$(jget $V/integrated_minus$2_2920_3h_VARIANT_RECEIPT.json)"
    done
    t0=$(date +%s)
    env -u GRB_LICENSE_FILE $(trace_env post) PY=$PY POST_ONLY=1 ALLOW_UNREGISTERED=1 TRUNCATE=56 RUN_DIR=$P NETS=$N bash run_batch3.sh > $D/post_smoke.out 2>&1; echo "RUNNER_EXIT $? $(( $(date +%s) - t0 ))s" >> $D/post_smoke.out
    mkdir -p $E/post_smoke
    cp $P/STATUS.txt $D/post_smoke.out $P/BATCH3_SUMMARY.json $P/BATCH3_SUMMARY.md $P/BATCH_REFERENCE.json $P/LEVEL2.json $P/PROFILE_CHOICE.json $E/post_smoke/ 2>/dev/null
    cp -r $P/M12_LOO $P/M12_BENEFIT $E/post_smoke/ 2>/dev/null
    for r in R1 R2 R5 R6 R7; do mkdir -p $E/post_smoke/$r; for f in PRECISION.json PRECISION.md V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json ALLOCATION.json RUN.json STOP_CLASS.json; do [ -f $P/$r/$f ] && cp $P/$r/$f $E/post_smoke/$r/; done
      [ -d $P/$r/m12_owen ] && cp $P/$r/m12_owen/OWEN.json $P/$r/m12_owen/OWEN.md $E/post_smoke/$r/ 2>/dev/null; [ -f $P/$r/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json ] && cp $P/$r/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json $E/post_smoke/$r/
      [ -f $P/$r/m12_loo_rhs/LOO_RHS_CHECK.json ] && cp $P/$r/m12_loo_rhs/LOO_RHS_CHECK.json $E/post_smoke/$r/; done
    ls -la $P/results_* >> $E/post_smoke/PACKS.txt 2>/dev/null
    $PY $W/scripts/m10p_post_compare.py $P $T12B $E/post_smoke/POST_SMOKE_VS_M12B.json
    tail -40 $P/STATUS.txt;;
esac
