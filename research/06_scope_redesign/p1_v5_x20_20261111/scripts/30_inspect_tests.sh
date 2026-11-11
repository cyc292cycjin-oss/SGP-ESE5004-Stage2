#!/bin/bash
# X20：只读查看后台全量测试的进度（不改任何文件）
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
echo "pycache on D: files=$(find $D/pycache -name '*.pyc' | wc -l) bytes=$(du -sb $D/pycache | cut -f1)"
echo "newest pyc: $(find $D/pycache -name '*.pyc' -newermt '-10 min' | wc -l) written in last 10 min"
cd /home/jin/wt_v5_x20/tests/research
for f in $(ls test_*.py | sort); do echo "$f $(grep -c '^def test_\|^    def test_' $f)"; done > /tmp/x20_testcount.txt
awk '{s+=$2; print s, $0}' /tmp/x20_testcount.txt | awk '{print}' > /tmp/x20_cum.txt
tail -1 /tmp/x20_cum.txt
grep -n 'm10p' /tmp/x20_cum.txt | head -3; grep -n 'm10p' /tmp/x20_cum.txt | tail -2
P=$(pgrep -f 'pytest -q -p no:cacheprovider' | head -1); echo "pytest pid $P"
grep -E 'State|Threads|VmRSS' /proc/$P/status
ls -l /proc/$P/fd 2>/dev/null | awk '{print $NF}' | grep -E '^/' | grep -v '^/dev' | head
pgrep -af 'm10p_fake|fixtures' | cut -c1-200 | head -5
rm -f /tmp/x20_testcount.txt /tmp/x20_cum.txt.keep
