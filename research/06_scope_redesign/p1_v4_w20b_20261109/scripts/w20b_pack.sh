#!/bin/bash
# V4 W20b: lossless compression of one run's large arrays (lp/*.npy, solution/*.npy, v5/kkt/*/*.npy) after its analyses (disk budget 5 GB, instruction
# section 5). The manifest ARRAYS_GZ_MANIFEST.txt (SHA256, bytes, path of every original file) is written first; gzip -1 -n replaces each file by
# <file>.gz; every .gz is then decompressed and checked against the manifest (ARRAYS_GZ_CHECK.txt: OK / BAD per file). Restore: gunzip <file>.gz.
# Sourced by w20b_solve.sh; prints files / ok / bad / bytes before / directory bytes after.
pack() {
  local d=$1 man=$1/ARRAYS_GZ_MANIFEST.txt
  ( cd "$d" && find lp solution v5/kkt -name '*.npy' -type f 2>/dev/null | sort | while read -r f; do echo "$(sha256sum "$f" | cut -c1-64) $(stat -c %s "$f") $f"; done ) > "$man"
  ( cd "$d" && cut -d' ' -f3 "$man" | xargs -r gzip -1 -n )
  ( cd "$d" && while read -r h s f; do g=$(gzip -dc "$f.gz" | sha256sum | cut -c1-64); if [ "$g" = "$h" ] && [ ! -f "$f" ]; then echo "OK $f"; else echo "BAD $f"; fi; done < "$man" ) > "$d/ARRAYS_GZ_CHECK.txt"
  echo "files=$(wc -l < "$man"):ok=$(grep -c '^OK ' "$d/ARRAYS_GZ_CHECK.txt"):bad=$(grep -c '^BAD ' "$d/ARRAYS_GZ_CHECK.txt"):bytes_before=$(awk '{s+=$2} END {print s+0}' "$man"):dir_bytes_after=$(du -sb "$d" | cut -f1)"
}
