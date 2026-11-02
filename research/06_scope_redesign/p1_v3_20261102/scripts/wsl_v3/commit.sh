#!/bin/bash
# usage: commit.sh <message file> ; stages everything under the V3 paths (force for the ignored csv / json tables), refuses a licence-like string, commits, prints the head.
set -e
W=/home/jin/wt_v3_20261102; D=research/06_scope_redesign/p1_v3_20261102
cd "$W"
mkdir -p "$D/scripts/wsl_v3"
cp /home/jin/v3/*.py /home/jin/v3/*.sh "$D/scripts/wsl_v3/" 2>/dev/null || true
[ -f /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/V3_REVIEW_DECISIONS_PHASE1.md ] && cp /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/V3_REVIEW_DECISIONS_PHASE1.md "$D/"
P="WLS""ACCESSID|WLS""SECRET|LICENSE""ID|BEGIN (RSA|OPENSSH) PRIVATE"" KEY"
if grep -rIlE --exclude=commit_p1.sh "$P" "$D" research_inputs/industry_v3 research_inputs/transport_v3 configs 2>/dev/null; then echo "LEAK SUSPECT"; exit 3; fi
git add -A scripts_project configs tests "$D" 2>/dev/null
git add -f research_inputs/industry_v3 research_inputs/transport_v3 research_inputs/liquids_v3 research_inputs/registry_v5/fragments/v3.csv 2>/dev/null || true
[ -d "$D/evidence" ] && git add -f "$D/evidence"
for f in $(git status --porcelain --ignored=matching research_inputs 2>/dev/null | awk '$1=="!!"{print $2}' | grep -E 'registry_v5/(DATA_REGISTRY|DATA_PENDING|D1_EVIDENCE)' || true); do git add -f "$f"; done
git status --short | cut -c1-90 | head -${2:-24}
git commit -q -F "$1"
git log --oneline -1 | cut -c1-120
