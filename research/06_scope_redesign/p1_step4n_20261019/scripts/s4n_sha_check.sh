#!/bin/bash
# S4N-2 point 2: full SHA256SUMS check of the package on the instance (every line printed), COMMIT, file list with sizes, leftover rsync temp files.
# Host and port from the calling command line environment only.
set -u
source /home/jin/s4n_ssh.sh
s4n_ssh 'cd /root/autodl-tmp/s4m_cloud && echo "CHECK_TIME: $(TZ=Asia/Singapore date "+%F %T") SGT" && sha256sum -c SHA256SUMS 2>&1; echo "SHA_EXIT:$?"; echo "SUMMARY: $(sha256sum -c SHA256SUMS 2>/dev/null | grep -c ": OK$") OK of $(grep -c . SHA256SUMS) lines"; echo "COMMIT: $(cat COMMIT)"; echo "TEMP_FILES: $(find . -name ".*" -type f | wc -l)"; find . -name ".*" -type f -printf "%s %p\n"; echo "FILES:"; find . -type f -printf "%s %TY-%Tm-%Td %p\n" | sort -k3'
