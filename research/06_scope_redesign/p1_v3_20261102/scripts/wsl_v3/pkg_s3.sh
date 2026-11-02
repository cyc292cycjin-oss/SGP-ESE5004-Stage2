#!/bin/bash
# V3 supplement 03 item 2.5: build the screening package (not uploaded), preflight on a WSL copy without the licence and resource sections, leak scan by the commit patterns. No solver, no cloud.
set -u
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=$MAIN/results_project/v3/builds_oneway; O=$MAIN/results_project/v3/dry_screen3; DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_oneway; C=$MAIN/results_project/v3/pkg_check3
cd $W || exit 1
DRY_RUN_JSON=$O/DRY_RUN_SCREEN.json PY=$PY bash research/06_scope_redesign/p1_v3_20261102/screen_package/make_package_v3.sh $B $DIST 2>&1 | tail -8 | cut -c1-200
[ -f $DIST/PACKAGE_MANIFEST.json ] || { echo "PACKAGE NOT BUILT"; exit 1; }
rm -rf $C; mkdir -p $C; cp -r $DIST/. $C/; cd $C
env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools bash preflight_dfx.sh 2>&1 | tail -24 | cut -c1-200
P="WLS""ACCESSID|WLS""SECRET|LICENSE""ID|BEGIN (RSA|OPENSSH) PRIVATE"" KEY"
echo "leak scan hits: $(grep -rIlE "$P" $DIST --include='*.md' --include='*.json' --include='*.sh' --include='*.txt' 2>/dev/null | wc -l)"; tar xzf $DIST/code_*.tar.gz -C /tmp --wildcards '*.lic' 2>/dev/null; echo "licence files in the archive: $(tar tzf $DIST/code_*.tar.gz | grep -cE '\.lic$')"
du -sh $DIST | cut -f1; ls -la $DIST | awk '{print $5, $9}' | tail -14; sha256sum $DIST/SHA256SUMS $DIST/PACKAGE_MANIFEST.json | cut -c1-120
$PY -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['commit'], d['upload_total_bytes_excluding_this_manifest'], d['upload']['hours_at'], len(d['files']))" $DIST/PACKAGE_MANIFEST.json
rm -rf $C/repo; du -sh $C | cut -f1
