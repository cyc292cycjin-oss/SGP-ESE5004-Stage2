#!/bin/bash
# W19a-0: extract DATA_REGISTRY.csv at the W14 package COMMIT and at the W10 baseline head; check against the package code tarball.
set -u
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109
C=26c2e47d025fdd4e46cb278718d93aeddabbe984
cd /home/jin/wt_v4_w19a || exit 1
git show $C:research_inputs/registry_v5/DATA_REGISTRY.csv > $D/cache/DATA_REGISTRY_26c2e47d.csv
git show aad8e476:research_inputs/registry_v5/DATA_REGISTRY.csv > $D/cache/DATA_REGISTRY_aad8e476.csv
mkdir -p $D/cache/tar && tar -xzf $D/../p1_v4_w14_20261109/hpc_package_v4/code_26c2e47d.tar.gz -C $D/cache/tar research_inputs/registry_v5/DATA_REGISTRY.csv
sha256sum $D/cache/DATA_REGISTRY_26c2e47d.csv $D/cache/tar/research_inputs/registry_v5/DATA_REGISTRY.csv $D/cache/DATA_REGISTRY_aad8e476.csv /home/jin/wt_v4_w14/research_inputs/registry_v5/DATA_REGISTRY.csv
wc -l $D/cache/DATA_REGISTRY_26c2e47d.csv $D/cache/DATA_REGISTRY_aad8e476.csv
git diff --stat $C HEAD -- research_inputs scripts_project config* | tail -3
