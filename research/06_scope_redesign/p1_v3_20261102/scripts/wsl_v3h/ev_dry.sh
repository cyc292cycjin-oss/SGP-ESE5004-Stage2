#!/bin/bash
# evidence of the dry runs on the package 7d22dda1 (bash 5 and bash 4.2), the bash 4.2 static check and the extra runner tests (copies; nothing deleted)
E=/home/jin/wt_v3_hpc/research/06_scope_redesign/p1_v3_20261102/evidence/hpc/dry
mkdir -p "$E" || exit 2
cp /home/jin/v3h/dry_20261103T191419Z/DRY_RUN_HPC.txt "$E/DRY_RUN_HPC_7d22dda1_bash5.txt"
cp /home/jin/v3h/dry_20261103T191743Z/DRY_RUN_HPC.txt "$E/DRY_RUN_HPC_7d22dda1_bash42.txt"
cp /home/jin/v3h/dry_20261103T191419Z/submit_dry.out "$E/SUBMIT_DRY_RUN_bash5.txt"
cp /home/jin/v3h/dry_20261103T191743Z/submit_dry.out "$E/SUBMIT_DRY_RUN_bash42.txt"
cp /home/jin/v3h/bash42_static.out "$E/BASH42_STATIC_7d22dda1.txt"
cp /home/jin/v3h/ut_split.out /home/jin/wt_v3_hpc/research/06_scope_redesign/p1_v3_20261102/evidence/hpc/tests/RUNNER_EXTRA_split_v3runners.txt
cp /home/jin/v3h/dry_20261103T175805Z/DRY_RUN_HPC.txt "$E/DRY_RUN_HPC_917c8b63_bash5.txt"
ls -la "$E"
grep -lE "unbound|syntax error|command not found" /home/jin/v3h/dry_20261103T191419Z/*.out /home/jin/v3h/dry_20261103T191743Z/*.out 2>/dev/null | head; echo "error-pattern files listed above (none = clean)"
