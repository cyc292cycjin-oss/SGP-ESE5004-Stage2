#!/bin/bash
set -u
W=/home/jin/wt_s4q_20261020; D=$W/research/06_scope_redesign/p1_step4q_20261020
cd $W
cp /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4q_20261020/S4Q_PROGRESS.md $D/; chmod 644 $D/S4Q_PROGRESS.md
cp /home/jin/s4q_2_setup.sh /home/jin/s4q_2_run.sh /home/jin/s4q_2_evidence.sh /home/jin/s4q_mon.sh /home/jin/s4q_watch.sh /home/jin/s4q_wait.sh /home/jin/s4q_peek.sh /home/jin/s4q_1_commit_ev.sh /home/jin/s4q_pr.sh $D/evidence/scripts/
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $D)
[ -z "$H" ] && echo "LICENCE_SCAN: no hit" || { echo "LICENCE STRING FOUND: $H"; exit 1; }
git add -f $D
git diff --cached --stat | tail -1
git commit -q -m "S4Q-2 (decision 123): six local 56x3h runs of the BarConvTol 1e-6 candidate, S4O pipeline (TRUNCATE 56, TimeLimit 1,750 s / wall 1,800 s, FIXED_RUNS=on, automatic C1), serial with gaps >= 330 s - formal_barrier_1e6 (Threads 8, run 20261020T001252Z_564) and formal_barrier_1e6_t16 (Threads 16, run 20261020T004641Z_8849): integrated, disconnected, integrated NZE all OPTIMAL, no retry, no stop, no kill; pipeline C1 (a)(b)(c) passed for all six; networks = S4M-1 builds with the S4M-2 SHA256; light evidence (scrubbed exports < 600 kB, STATUS, driver status, preflight), driver and helper scripts, progress

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git log --oneline -1 | cut -c1-100
git push -q origin codex/s4q-tol-calibration-20261020 2>&1 | tail -1; git ls-remote --heads origin codex/s4q-tol-calibration-20261020 | cut -c1-12
