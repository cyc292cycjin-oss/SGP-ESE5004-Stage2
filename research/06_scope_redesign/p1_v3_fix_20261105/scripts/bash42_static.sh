#!/bin/bash
# bash 4.2 compatibility of the shipped shell scripts (V3_HPC_UNATTENDED.md section 2): (1) "bash -n" with the locally compiled bash 4.2 on every script and
# job script of the package; (2) a static search for constructs that need bash >= 4.3 / 4.4 / 5 (namerefs, wait -n / -p / -f, mapfile -d, negative array subscripts,
# ${var@op}, EPOCHSECONDS / EPOCHREALTIME / BASH_ARGV0, inherit_errexit / localvar_*, [[ -v a[i] ]], test -R); (3) the list of "${a[@]}" / ${a[*]} expansions
# without a :- / + guard, for the review of arrays that could be empty under set -u (bash < 4.4 errors on them).
# usage: bash42_static.sh <package dir>
set -u
P=${1:?package dir}; B42=/home/jin/v3h/bash42/src/bash
echo "bash: $($B42 --version | head -1)"
mapfile -t F < <(cd "$P" && { ls *.sh hpc/*.sh pbs/*.pbs env/*.sh 2>/dev/null; } | sort -u)
echo "files: ${#F[@]}"
bad=0
for f in "${F[@]}"; do out=$($B42 -n "$P/$f" 2>&1) || { echo "SYNTAX_FAIL:$f:$out"; bad=$((bad + 1)); }; done
echo "syntax (bash 4.2 -n): $(( ${#F[@]} - bad )) / ${#F[@]} OK"
PAT='declare -n|local -n|typeset -n|wait -n|wait -p|wait -f|mapfile -d|readarray -d|\$\{[A-Za-z_][A-Za-z_0-9]*\[-[0-9]+\]\}|\$\{[A-Za-z_][A-Za-z_0-9]*(\[[^]]*\])?@[QEPAaKkUuL]\}|EPOCHSECONDS|EPOCHREALTIME|BASH_ARGV0|inherit_errexit|localvar_inherit|localvar_unset|\[\[ -v [A-Za-z_]+\[|test -R |\[ -R '
hits=$(cd "$P" && grep -nE "$PAT" "${F[@]}" 2>/dev/null)
if [ -n "$hits" ]; then echo "NEWER_SYNTAX_HITS:"; echo "$hits" | cut -c1-220; else echo "newer-syntax hits: 0"; fi
echo "unguarded array expansions (review each: never empty, or guarded):"
(cd "$P" && grep -noE '"\$\{[A-Za-z_][A-Za-z_0-9]*\[[@*]\](:[0-9]+)?\}"|\$\{[A-Za-z_][A-Za-z_0-9]*\[\*\]\}' "${F[@]}" 2>/dev/null) | sort | uniq -c | sed 's/^ */  /'
[ $bad = 0 ] && [ -z "$hits" ] && echo "STATIC_OK" || echo "STATIC_FAIL"
