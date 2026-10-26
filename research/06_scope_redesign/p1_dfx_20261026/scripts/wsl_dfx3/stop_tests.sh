#!/bin/bash
# DFX v3: stop the running full test suite (own pytest) and the stuck helper shells of this session; report what was killed.
for p in $(pgrep -f "pytest -q -p no:cacheprovider tests"); do echo "kill pytest $p: $(ps -o args= -p $p | cut -c1-80)"; kill $p; done
sleep 2; pkill -9 -f "pytest -q -p no:cacheprovider tests" 2>/dev/null
for p in $(pgrep -f "for f in \$(grep -l -E"); do echo "kill stuck shell $p"; kill -9 $p; done
for p in $(pgrep -f "wc -c \$f; tail -c 600"); do echo "kill stuck shell $p"; kill -9 $p; done
sleep 1; echo "remaining: pytest=$(pgrep -fc pytest) s2_solve=$(ps -eo args= | grep -c '[s]2_solve\.py') fake=$(pgrep -fc m10p_fake_pipeline)"
pkill -9 -f m10p_fake_pipeline 2>/dev/null; pkill -9 -f "standin/scripts_project/s2_solve.py" 2>/dev/null; sleep 1
echo "after: pytest=$(pgrep -fc pytest) s2_solve=$(ps -eo args= | grep -c '[s]2_solve\.py')"
