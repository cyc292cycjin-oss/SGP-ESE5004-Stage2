#!/bin/bash
# X20：停掉第 2 次基线全量测试（pytest 及其子进程；按 PID，不用模式匹配，避免误杀）
P=$(pgrep -f '^/home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest -q -p no:cacheprovider --basetemp=/tmp/x20_pytest_base')
echo "pytest pid: $P"; [ -n "$P" ] || exit 0
C=$(pgrep -P $P | tr '\n' ' '); echo "children: $C"
kill $P $C 2>/dev/null; sleep 3
pgrep -f 'x20_pytest_base' >/dev/null && { echo "still alive, SIGKILL"; pkill -9 -P $P; kill -9 $P; }
sleep 1; echo "remaining: $(pgrep -fc 'x20_pytest_base')"
du -sb /tmp/x20_pytest_base 2>/dev/null; rm -rf /tmp/x20_pytest_base; echo "basetemp removed"
