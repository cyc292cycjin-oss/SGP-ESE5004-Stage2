#!/bin/bash
# D1: commit section 5 (repository code / inputs / registry + delivery without the section-6 files), then section 6 (PHS files). Hooks not skipped.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107; R=/home/jin/wt_v4_d1; D=research/06_scope_redesign/p1_v4_d1_20261107
bash $W/scripts/sync.sh
cd $R || exit 1
git add -f $D scripts_project/v4_biomass_potential.py scripts_project/v4_registry.py scripts_project/v4_d1_registry.py tests/research/test_v4_d1_palm.py \
  research_inputs/biomass_v5/PALM_MILL_SELF_USE.csv research_inputs/biomass_v5/BIOMASS_POTENTIAL_ADJ_V4.csv research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv \
  research_inputs/registry_v5/fragments/v4_d1.csv research_inputs/registry_v5/fragments/v4_w08.csv research_inputs/registry_v5/DATA_REGISTRY.csv research_inputs/registry_v5/D1_EVIDENCE.json
git reset -q $D/PHS_PROPOSAL.md $D/evidence/PHS_LITERATURE.json $D/evidence/PHS_MODEL.json $D/scripts/d1_phs_model.py $D/scripts/msg_d1_6.txt 2>/dev/null
git status --short | grep -E '__pycache__|\.pyc$' && { echo "REFUSED: pyc staged"; exit 3; }
git commit -q -F $W/scripts/msg_d1_5.txt && git log -1 --format='%H %s'
git add -f $D/PHS_PROPOSAL.md $D/evidence/PHS_LITERATURE.json $D/evidence/PHS_MODEL.json $D/scripts/d1_phs_model.py
git commit -q -F $W/scripts/msg_d1_6.txt && git log -1 --format='%H %s'
git status --short | head
