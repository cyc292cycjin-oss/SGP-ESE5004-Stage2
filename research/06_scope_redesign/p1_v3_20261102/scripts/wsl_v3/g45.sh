#!/bin/bash
W=/home/jin/wt_v3_20261102; cd $W
grep -n "APG\|apg" scripts_project/s3_0_corridors.py | head -24 | cut -c1-230
