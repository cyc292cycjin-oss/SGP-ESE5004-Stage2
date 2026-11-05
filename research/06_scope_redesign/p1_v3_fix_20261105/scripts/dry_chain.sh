#!/bin/bash
# V3.1 section 6.4: dry runs of the delivered package with bash 5 and bash 4.2, then the bash 4.2 static check of the package; results into evidence/dry/.
set -u
P=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1; S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/scripts
O=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence/dry; mkdir -p $O
bash $S/dry_hpc31.sh $P > $O/DRY_RUN_HPC_bash5.txt 2>&1; echo "dry bash5 exit $?"
BASH_BIN=/home/jin/v3h/bash42/src/bash bash $S/dry_hpc31.sh $P > $O/DRY_RUN_HPC_bash42.txt 2>&1; echo "dry bash42 exit $?"
bash $S/bash42_static.sh $P > $O/BASH42_STATIC_d3b9a3bc.txt 2>&1; echo "static exit $?"
echo DRY_CHAIN_DONE
