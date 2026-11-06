#!/bin/bash
# W08 checklist section 1: the eleven W12 SDMX responses (read only) -> research_inputs/assembly_v1/sources/unsd_sdmx_2019/ (+ the W12 registry rows).
# Receipts are not copied (HTTP headers incl. a load-balancer cookie); url / UTC / bytes / SHA256 are in the registry file.
set -eu
S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/W12
D=/home/jin/wt_v4_w08/research_inputs/assembly_v1/sources/unsd_sdmx_2019
mkdir -p "$D"
cp "$S"/sdmx/*_2019_all.xml "$D"/
cp "$S"/DATA_REGISTRY_W12_SDMX.csv "$D"/SDMX_RESPONSES_REGISTRY_W12.csv
cd "$D" && sha256sum *.xml && ls | wc -l
