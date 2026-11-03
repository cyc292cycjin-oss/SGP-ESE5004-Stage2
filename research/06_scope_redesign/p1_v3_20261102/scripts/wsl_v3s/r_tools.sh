# V3 screening (ON the instance): the tools the preflight asks for that the image lacks (M10: apt, 9 s). Only tmux and GNU time; nothing else changes.
need=(); [ -x /usr/bin/time ] || need+=(time); command -v tmux >/dev/null 2>&1 || need+=(tmux)
if [ ${#need[@]} -gt 0 ]; then echo "installing: ${need[*]}"; apt-get update -qq >/dev/null 2>&1; apt-get install -y -qq "${need[@]}" >/dev/null 2>&1; echo "apt exit=$?"; fi
/usr/bin/time -v true >/dev/null 2>&1 && echo "GNU time -v works" || echo "GNU time -v NOT working"
command -v tmux >/dev/null 2>&1 && tmux -V || echo "tmux MISSING"
