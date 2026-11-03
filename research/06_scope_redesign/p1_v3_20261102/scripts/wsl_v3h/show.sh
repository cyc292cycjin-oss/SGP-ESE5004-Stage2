#!/bin/bash
cd /home/jin/wt_v3_hpc; git show --stat --format='%H' HEAD | grep -E "test_v3_units|v3_layers|^[0-9a-f]{40}|files? changed"; echo "dirty=$(git status --porcelain | wc -l)"
