#!/bin/bash
# S4O-4 (S4O instruction + supplement 01): rebuild the cloud package on the final commit ($1) - networks from the f50c8850 rebuild (results_project/s4m/s4m3/builds),
# speed-probe reference from the S4M-2 smoke, reference package = the S4M f50c8850 dist; then the package checks: SHA256SUMS, preflight sections that need no
# licence (sha, networks, profile, c1, versions, tools), dry run, licence-string scan of the dist folder. No solve, no cloud action.
set -u
WANT=${1:?commit (8 chars)}
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; cd $RM
export PATH=/home/jin/miniforge3/envs/pypsa-earth/bin:$PATH PYTHONHASHSEED=0
[ "$(git rev-parse --short=8 HEAD)" = "$WANT" ] || { echo "REFUSED: HEAD is not $WANT"; exit 2; }
DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019/cloud_package_dist; REF=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4m_20261019/cloud_package_dist
E=$RM/research/06_scope_redesign/p1_step4o_20261019/evidence/s4o_4p; mkdir -p $E
echo "== make_package"
/usr/bin/time -v bash research/06_scope_redesign/p1_step4o_20261019/cloud_package/make_package.sh results_project/s4m/s4m3/builds $DIST results_project/s4m/s4m2/solves $REF > $E/make_package_log.txt 2> $E/make_package_err.txt
rc=$?; echo "MAKE_PACKAGE_EXIT:$rc"; grep -E "all_same|changed|manifest written|data/config|Elapsed|Maximum resident" $E/make_package_log.txt $E/make_package_err.txt | cut -c1-300
[ $rc = 0 ] || exit 1
echo "== package checks"
( cd $DIST && sha256sum -c --quiet SHA256SUMS && echo "SHA256SUMS: all $(wc -l < SHA256SUMS) OK" )
T=/home/jin/s4o_tmp/pkg_check; rm -rf $T; mkdir -p $T; cp -a $DIST/. $T/
( cd $T && PREFLIGHT_ONLY=sha,networks,profile,c1,versions,tools PY=python bash preflight.sh serial ) > $E/preflight_local_sections.txt 2>&1; echo "PREFLIGHT_EXIT:$?"; grep -vE "PROJ" $E/preflight_local_sections.txt | tail -25
echo "DUMMY LICENCE PATH FOR THE DRY RUN - NOT A LICENCE" > $T/dummy.lic
( cd $T && GRB_LICENSE_FILE=$T/dummy.lic PY=python PILOT_INTEGRATED=/pilot/integrated PILOT_PRECISION=/pilot/PILOT_PRECISION.json bash run_365x24h.sh --mode serial --dry-run --auth "S4O-4 dry run (no solve)" ) > $E/run_dry_run.txt 2>&1; echo "DRY_RUN_EXIT:$?"
grep -c "DRY-RUN: .*s2_solve.py" $E/run_dry_run.txt
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $DIST $E 2>/dev/null)
[ -z "$H" ] && echo "LICENCE_SCAN_DIST: no hit ($(find $DIST -type f | wc -l) files)" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
for f in COMMIT SHA256SUMS PACKAGE_MANIFEST.json PACKAGE_DELTA.json NETWORKS_VS_REFERENCE.json DATA_CONFIG_MANIFEST.json PROBE_REFERENCE.json BUILD_INPUT_CHANGES_integrated.json; do cp $DIST/$f $E/ 2>/dev/null; done
du -sb $DIST
rm -rf $T
