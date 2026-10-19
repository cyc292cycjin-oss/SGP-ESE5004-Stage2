# S4N-4 restart inspection (runs ON the instance via "ssh bash -s"; read-only). Prints the barrier iteration lines from 140 on, every non-iteration
# line of the log after the barrier header (with line numbers; licence-related lines removed), and the file time of the log.
L=/root/autodl-tmp/s4m_cloud/runs/20261019T072454Z_5125/integrated/gurobi.linopy.log
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'
date '+NOW %F %T'
echo "== iteration lines >= 140"
grep -nE '^ *[0-9]+ +[-0-9.e+]+ +[-0-9.e+]+ ' $L | awk -F: '{split($2,a," "); if (a[1]+0 >= 140) print}'
echo "== non-iteration lines after the barrier header (line numbers)"
h=$(grep -n 'Iter       Primal' $L | head -1 | cut -d: -f1)
awk -v h=$h 'NR > h && $0 !~ /^ *[0-9]+ +[-0-9.e+]+ +[-0-9.e+]+ / {print NR": "$0}' $L | grep -viE "$SCRUB"
echo "== lines between the iteration-155 line and the iteration-156 line (verbatim)"
a=$(grep -nE '^ *155 +[-0-9.e+]+ +[-0-9.e+]+ ' $L | head -1 | cut -d: -f1); b=$(grep -nE '^ *156 +[-0-9.e+]+ +[-0-9.e+]+ ' $L | head -1 | cut -d: -f1)
echo "line of 155: $a ; line of 156: $b"
[ -n "$a" ] && [ -n "$b" ] && sed -n "${a},${b}p" $L | grep -viE "$SCRUB" | cat -A | cut -c1-200
echo "== log size / mtime"; stat -c '%s bytes %y' $L
