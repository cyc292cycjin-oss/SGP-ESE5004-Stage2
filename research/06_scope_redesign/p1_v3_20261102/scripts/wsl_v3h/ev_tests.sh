#!/bin/bash
# evidence of the full suite at 1e7b503c and of the B12 diagnosis of the three test_s3_gates failures (no solve)
E=/home/jin/wt_v3_hpc/research/06_scope_redesign/p1_v3_20261102/evidence/hpc/tests
mkdir -p "$E" || exit 2
cp /home/jin/v3h/full_tests.out "$E/FULL_SUITE_1e7b503c.txt"
cd /home/jin/v3h || exit 2
PYTHONHASHSEED=0 timeout 600 /home/jin/miniforge3/envs/pypsa-earth/bin/python -I diag_b12.py /home/jin/wt_v3_hpc 2>&1 | grep -vE 'Warning|warn\(|PROJ|INFO:' > "$E/S3_GATES_B12_DIAGNOSIS.txt"
cp diag_b12.py t_s3g.sh "$E/"
ls -la "$E"; cat "$E/S3_GATES_B12_DIAGNOSIS.txt" | cut -c1-200
