#!/bin/bash
# W08: remove force-added __pycache__ files from the index (files stay on disk; a new commit, no history rewrite).
set -u
cd /home/jin/wt_v4_w08 || exit 1
git ls-files | grep -E '__pycache__|\.pyc$' > /home/jin/v4w08/pyc_list.txt
wc -l < /home/jin/v4w08/pyc_list.txt
[ -s /home/jin/v4w08/pyc_list.txt ] || exit 0
git log --format='%h %s' -1 -- $(head -1 /home/jin/v4w08/pyc_list.txt)
xargs -a /home/jin/v4w08/pyc_list.txt git rm -q --cached
git commit -q -F /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106/scripts/msg_w08_pyc.txt && git log -1 --format='%H %s'
git ls-files | grep -cE '__pycache__|\.pyc$'
