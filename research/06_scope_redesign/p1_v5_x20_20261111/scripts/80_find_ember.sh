#!/bin/bash
# 只读：查找本地 Ember 年度文件与 IHA 数据副本（不下载）
find /home/jin/research /home/jin/wt_v5_x20 -maxdepth 7 -iname "*release_generation_yearly*" -o -maxdepth 7 -iname "*ember*yearly*" 2>/dev/null | grep -v "/.git/" | head
find /mnt/d/ResearchWorkspaces/ASEAN -maxdepth 6 \( -iname "*release_generation_yearly*" -o -iname "*IHA*" -o -iname "*hydropower_status*" \) 2>/dev/null | head -20
grep -rn "ember" /home/jin/wt_v5_x20/research_inputs/registry_v5/fragments/s4c_2.csv 2>/dev/null | cut -c1-300 | head -3
