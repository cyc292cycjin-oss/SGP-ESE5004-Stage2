#!/bin/bash
# V3 HPC package session: git-ignored inputs of the new worktree (results_project links to the main checkout; ignored research_inputs copied); no solver
set -e
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; W=/home/jin/wt_v3_hpc
cd $W
for d in $(ls $MAIN/results_project); do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
for p in research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv research_inputs/finance_v5/DISCOUNT_RATE_IN_USE.csv research_inputs/renewable_v5/regions_offshore.geojson research_inputs/renewable_v5/regions_onshore.geojson research_inputs/registry_v5/sources/jrc_idees_2021/EU27/JRC-IDEES-2021_Industry_EU27.xlsx research_inputs/registry_v5/sources/pypsa_eur_data/usgs_myb1-2022-nitro-ert.xlsx; do
  [ -e $p ] || { mkdir -p $(dirname $p); cp -p $MAIN/$p $p; }
done
git status --porcelain --untracked-files=no | wc -l
ls -la results_project | head -8; ls results_project | wc -l
