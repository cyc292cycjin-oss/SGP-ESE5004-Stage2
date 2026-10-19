#!/bin/bash
# S4O: pattern scan of a folder (or files) for licence strings and login details (host / port / password patterns).
# The real host and port are not known to this script (they were never written to a file); the scan uses generic patterns:
# IPv4 addresses, AutoDL / SeetaCloud host names, ssh / scp / rsync port options, user@host forms, password words.
# Usage: bash s4o_scan.sh <path> [<path> ...]   -> prints hits; exit 0 always (the caller reads the counts).
set -u
[ $# -ge 1 ] || { echo "usage: s4o_scan.sh <path> ..."; exit 2; }
echo "== licence strings (files):"
grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)|academic[[:space:]]+licen" "$@" | grep -v "/s4o_scan.sh$" || true
echo "== IPv4-like addresses (file:line:match):"
grep -rIonE "(^|[^0-9.])((25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])([^0-9.]|$)" "$@" \
  | grep -vE "/s4o_scan.sh:" | head -50 || true
echo "== cloud host names (seetacloud / autodl domains):"
grep -rIonE "[a-z0-9.-]*(seetacloud\.com|autodl\.(com|pro|net))[a-z0-9./-]*" "$@" | grep -v "/s4o_scan.sh:" | head -50 || true
echo "== ssh / scp / rsync port options with a literal number:"
grep -rIonE "(ssh|scp|rsync)[^\n]{0,80}(-p|-P|--port[= ])[[:space:]]*[0-9]{2,5}" "$@" | grep -v "/s4o_scan.sh:" | head -50 || true
grep -rIonE "(^|[[:space:]])Port[[:space:]]+[0-9]{2,5}" "$@" | grep -v "/s4o_scan.sh:" | head -50 || true
echo "== user@host forms:"
grep -rIonE "root@[a-z0-9][a-z0-9.-]{3,}" "$@" | grep -v "/s4o_scan.sh:" | head -50 || true
echo "== password words with a value:"
grep -rIonE "(password|passwd|密码)[[:space:]]*[:=][[:space:]]*[^[:space:]\"']{4,}" "$@" | grep -v "/s4o_scan.sh:" | head -50 || true
echo "== scan done"
