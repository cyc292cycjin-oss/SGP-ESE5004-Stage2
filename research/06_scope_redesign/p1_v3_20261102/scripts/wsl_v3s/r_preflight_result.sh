# V3 screening (ON the instance): the latest preflight console log (licence lines filtered) + guard-name count
P=/root/autodl-tmp/v3_screen; PL=$(ls -t $P/PREFLIGHT_CONSOLE_*.log 2>/dev/null | head -1)
[ -n "$PL" ] || { echo "no preflight log"; exit 2; }
echo "LOG ${PL##*/}"; grep -viE 'licen[cs]e[^ ]* (id|key|file)|registered[[:space:]]+to|wls(access|secret)|academic' "$PL"
echo "guard names: $(cat /root/autodl-tmp/v3_screen_guard_names.txt 2>/dev/null | tr '\n' ' ') (count $(wc -l < /root/autodl-tmp/v3_screen_guard_names.txt 2>/dev/null))"
