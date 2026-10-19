#!/bin/bash
# connectivity diagnosis (no login): DNS, TCP port reachability, general internet. Host and port from the calling command line environment only;
# the output does not repeat them.
: "${S4N_HOST:?}" "${S4N_PORT:?}"
echo "DNS: $(getent hosts "$S4N_HOST" | awk '{print $1}' | head -2 | tr '\n' ' ' | sed -E 's/[0-9]+\.[0-9]+$/x.x/')"
timeout 15 bash -c "</dev/tcp/$S4N_HOST/$S4N_PORT" 2>/dev/null && echo "TCP_PORT: open" || echo "TCP_PORT: no connection within 15 s"
timeout 15 bash -c "</dev/tcp/$S4N_HOST/22" 2>/dev/null && echo "TCP_22: open" || echo "TCP_22: closed / timeout"
curl -s -o /dev/null -w "HTTPS_GITHUB: %{http_code} in %{time_total}s\n" --max-time 15 https://github.com || echo "HTTPS_GITHUB: failed"
curl -s -o /dev/null -w "HTTPS_AUTODL: %{http_code} in %{time_total}s\n" --max-time 15 https://www.autodl.com || echo "HTTPS_AUTODL: failed"
TZ=Asia/Singapore date '+%F %T SGT'
