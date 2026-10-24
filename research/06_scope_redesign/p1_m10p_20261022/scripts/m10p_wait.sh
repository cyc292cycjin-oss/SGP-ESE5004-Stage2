#!/bin/bash
# M10P: block until a file contains a marker or MAXS seconds pass (keeps the session waiting without polling from the tool side)
F=${F:?file}; M=${M:?marker}; MAXS=${MAXS:-540}; t0=$(date +%s)
until grep -q "$M" "$F" 2>/dev/null; do
  [ $(( $(date +%s) - t0 )) -ge "$MAXS" ] && { echo "WAITED ${MAXS}s - not yet"; exit 0; }
  sleep 10
done
echo "FOUND $M after $(( $(date +%s) - t0 ))s"
