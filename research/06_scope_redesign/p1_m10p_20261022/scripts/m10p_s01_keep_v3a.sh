#!/bin/bash
# M10P supplement 01: keep the evidence of the first v3 package build (619d7b46) before the rebuild
set -u
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/evidence/s01
mkdir -p $E/package_v3a_619d7b46 && mv $E/package/* $E/MAKE_PACKAGE.log $E/PACKAGE_SUMMARY.txt $E/package_v3a_619d7b46/ && rmdir $E/package
ls $E $E/package_v3a_619d7b46
