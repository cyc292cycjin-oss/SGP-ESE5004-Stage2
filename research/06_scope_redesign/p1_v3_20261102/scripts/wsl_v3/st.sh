#!/bin/bash
cd /home/jin/wt_v3_20261102
ps -eo pid,etime,cmd | grep -E '[g]it |[c]ommit_p1' | cut -c1-120 | head
git log --oneline -4 | cut -c1-100
git status --short | wc -l
git ls-remote origin refs/heads/codex/v3-20261102
ls /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/
du -sh research/06_scope_redesign/p1_v3_20261102 research/06_scope_redesign/p1_v3_20261102/*
