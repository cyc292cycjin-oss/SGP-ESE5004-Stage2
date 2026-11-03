#!/bin/bash
# V3 screening rerun (supplement 07), after shutdown (the instance name can no longer be read from the instance): leak check of the staged / last-commit text with the pattern
# file, host and port from the environment, and the generic prefix of AutoDL instance names (built here from two parts, so this file holds no instance
# name). Counts only.  wsl env V3S_HOST=.. V3S_PORT=.. bash final_check.sh <rev range or "staged">
set -u
: "${V3S_HOST:?}" "${V3S_PORT:?}"
cd /home/jin/wt_v3_20261102
if [ "${1:-staged}" = staged ]; then T=$(git diff --cached); else T=$(git show "$1"); fi
PFX="autodl""-container-"
P=$(grep -v "^#" /home/jin/.dfx_leak_patterns | cut -d= -f2- | paste -sd "|" -)
echo "lines: $(printf '%s\n' "$T" | wc -l)"
echo "host: $(printf '%s\n' "$T" | grep -cF "$V3S_HOST")"
echo "port: $(printf '%s\n' "$T" | grep -cE "\b$V3S_PORT\b")"
echo "instance prefix: $(printf '%s\n' "$T" | grep -cF "$PFX")"
echo "pattern file: $(printf '%s\n' "$T" | grep -ciE "$P")"
LIC=/home/jin/gurobi.lic; n=0
if [ -r $LIC ]; then while IFS= read -r line; do v=${line#*=}; [ "$line" != "$v" ] && [ ${#v} -ge 8 ] && n=$((n + $(printf '%s\n' "$T" | grep -cF "$v"))); done < <(grep -v '^#' $LIC); fi
echo "licence values: $n"
