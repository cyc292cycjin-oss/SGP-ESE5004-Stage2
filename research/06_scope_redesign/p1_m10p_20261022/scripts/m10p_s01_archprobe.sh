#!/bin/bash
# M10P supplement 01: size of the code archive with and without research/ (scratch only; no package written)
set -u
cd /home/jin/wt_m10p_20261022 || exit 1
git --version
S=/home/jin/m10p_s01_scratch/archprobe; rm -rf "$S"; mkdir -p "$S"
git archive --format=tar.gz -o "$S/full.tar.gz" HEAD
git archive --format=tar.gz -o "$S/slim.tar.gz" HEAD -- . ':(exclude)research'
ls -l "$S"
echo "slim research entries: $(tar tzf "$S/slim.tar.gz" | grep -c '^research/')"
echo "slim entries: $(tar tzf "$S/slim.tar.gz" | grep -vc '/$')  full entries: $(tar tzf "$S/full.tar.gz" | grep -vc '/$')"
echo "tracked outside research/: $(git ls-files | grep -vc '^research/')  tracked in research/: $(git ls-files | grep -c '^research/')"
echo "largest top-level dirs in slim:"; tar tzvf "$S/slim.tar.gz" | awk '{split($6,a,"/"); s[a[1]]+=$3} END {for (k in s) printf "%12d %s\n", s[k], k}' | sort -rn | head -8
