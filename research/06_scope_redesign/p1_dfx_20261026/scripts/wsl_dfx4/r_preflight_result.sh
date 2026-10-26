# DFX phase 4 (ON the instance): the latest preflight console log (licence lines filtered) + guard-name count
P=/root/autodl-tmp/dfx_v8; PL=$(ls -t $P/PREFLIGHT_CONSOLE_*.log 2>/dev/null | head -1)
[ -n "$PL" ] || { echo "no preflight log"; exit 2; }
echo "LOG ${PL##*/}"; grep -viE 'licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic' "$PL"
echo "guard names: $(cat /root/autodl-tmp/dfx_v8_guard_names.txt 2>/dev/null | tr '\n' ' ') (count $(wc -l < /root/autodl-tmp/dfx_v8_guard_names.txt 2>/dev/null))"
