#!/bin/bash
# start the read-only post-processing on the instance in tmux session s4n_post (after DONE), then wait (max MAX_S) for POST_DONE. Host / port from env.
set -u
source /home/jin/s4n_ssh.sh
MAX_S=${1:-3000}
s4n_ssh 'RUN=/root/autodl-tmp/s4m_cloud/runs/20261019T072454Z_5125; grep -q "^DONE" $RUN/STATUS.txt || { echo "PILOT NOT DONE"; exit 2; }
  tmux has-session -t s4n_post 2>/dev/null && { echo "s4n_post exists"; exit 2; }
  tmux new -d -s s4n_post "bash /root/autodl-tmp/s4n_tools/s4n_r_post.sh > /root/autodl-tmp/s4n_tools/post_console.log 2>&1"; sleep 5; tmux ls; head -3 /root/autodl-tmp/s4n_tools/POST_STATUS.txt' || exit $?
t0=$(date +%s)
while :; do
  out=$(s4n_ssh 'cat /root/autodl-tmp/s4n_tools/POST_STATUS.txt 2>/dev/null' 2>&1)
  echo "$out" | grep -q "^POST_DONE" && { echo "$out"; exit 0; }
  [ $(( $(date +%s) - t0 )) -ge $MAX_S ] && { echo "WAIT_TIMEOUT"; echo "$out"; exit 1; }
  sleep 30
done
