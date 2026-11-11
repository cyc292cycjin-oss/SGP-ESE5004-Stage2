#!/bin/bash
# X20 A 段：剖面 nc 是否入 git 及大小、industry_v4 表目录大小、s4a_profiles 输出参数、W14 冒烟的内存与耗时（只读）
set -u
WT=/home/jin/wt_v4_w14
C=26c2e47d025fdd4e46cb278718d93aeddabbe984
cd "$WT" || exit 2
echo "== tracked nc / large files under research_inputs at 26c2e47d (top 15 by size)"
git ls-tree -r -l $C research_inputs | sort -k4 -n -r | head -15 | awk '{printf "%s %s\n", $4, $5}'
echo "== renewable_v5 nc files (tracked?)"
git ls-tree -r -l $C research_inputs/renewable_v5 | grep -E "\.nc$" | awk '{printf "%s %s\n", $4, $5}'
echo "== industry_v4 dirs tracked bytes"
for d in out_ras out_iid; do git ls-tree -r -l $C research_inputs/industry_v4/$d | awk -v d=$d '{s+=$4} END {printf "%s %.1f MB %d files\n", d, s/1e6, NR}'; done
echo "== .git objects size (common dir)"; du -sh "$(git rev-parse --git-common-dir)/objects" 2>/dev/null
echo "== s4a_profiles args"; grep -n "add_argument" scripts_project/s4a_profiles.py | cut -c1-200
echo "== s4b_3 args"; grep -n "add_argument" scripts_project/s4b_3_wind_calibration.py scripts_project/s4b_3_export.py | cut -c1-200
echo "== s4a_2 / s4b_1 / s4b_2 args"; grep -n "add_argument" scripts_project/s4a_2_fleet_data.py scripts_project/s4b_1_fleet_data.py scripts_project/s4b_2_candidates_data.py | cut -c1-200
echo "== v4_industry args"; grep -n "add_argument" scripts_project/v4_industry.py | cut -c1-200
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109
echo "== W14 smoke drill memory/time lines"; grep -n -i -E "maximum resident|elapsed|peak|rss|wall|seconds|GiB" $W/logs/smoke_drill.txt | head -40
echo "== D2c smoke memory/time"; grep -rn -i -E "maximum resident|elapsed \(wall" /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2c_20261109/logs/ 2>/dev/null | head -20
