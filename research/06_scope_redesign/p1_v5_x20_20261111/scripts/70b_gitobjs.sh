#!/bin/bash
# 本步提交新增 git 对象的磁盘占用（26c2e47d..HEAD 引入的对象；松散或打包后的实际大小）
cd /home/jin/wt_v5_x20 || exit 1
git rev-list --objects 26c2e47d..HEAD | git cat-file --batch-check='%(objecttype) %(objectsize) %(objectsize:disk)' | awk '{n++; s+=$2; d+=$3} END {print "objects", n, "size_bytes", s, "disk_bytes", d}'
git count-objects -v 2>/dev/null | tr "
" " "; echo
