#!/bin/bash
# X20 ①5：从 W14 结果归档只提取 F1 / F2 2920x3h 已解网络到 D 盘 cache/v4solved（HK01 已删解包副本，按 CLEANUP_MANIFEST 的来源），核对 SHA256。只读归档。
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work; D=$W/p1_v5_x20_20261111; O=$D/cache/v4solved; LOG=$D/logs/45_extract_v4_solved.log
A=$W/p1_v4_w14_20261109/hpc_results_v4/results_full_final_20261109T142421Z.tar.gz
mkdir -p $O
{
echo "archive $(stat -c %s $A) B; start $(date '+%F %T')"
s=$(date +%s)
tar -xzf $A -C $O export/F1/integrated_BATCH4_2920X3H_solved.nc export/F2/no_new_xb_BATCH4_2920X3H_solved.nc; echo "tar exit $? seconds $(( $(date +%s) - s ))"
cd $O && printf '%s  %s\n' 9e342e3971712eece8b9c17b731f557f9de5b83993f8456bcd01195790a0d522 export/F1/integrated_BATCH4_2920X3H_solved.nc 6a82e6f8032fd23571f3c1cfb352f8230952657cff0cca08105df335d5a122bc export/F2/no_new_xb_BATCH4_2920X3H_solved.nc | sha256sum -c
echo "end $(date '+%F %T')"; du -sb $O
} > $LOG 2>&1
