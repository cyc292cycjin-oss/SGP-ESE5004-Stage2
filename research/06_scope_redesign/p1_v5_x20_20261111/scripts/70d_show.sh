#!/bin/bash
# 只读：某个提交中的文件名列表（不截断）
cd /home/jin/wt_v5_x20 && git show --name-status --format='%H' "${1:-HEAD}" -- research_inputs scripts_project configs tests | head -40
