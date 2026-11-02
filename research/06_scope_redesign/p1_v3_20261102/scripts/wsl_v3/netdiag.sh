#!/bin/bash
# read-only network check from WSL (prints no addresses of proxies or credentials)
echo "proxy env set: $(env | grep -ci _proxy)"
echo "git proxy set: $(git config --global --get-regexp 'http.*proxy' | wc -l)"
getent hosts github.com | head -2
curl -sS -m 12 -o /dev/null -w "github http=%{http_code} t=%{time_total}\n" https://github.com 2>&1 | tail -1
curl -sS -m 12 -o /dev/null -w "irena http=%{http_code} t=%{time_total}\n" https://www.irena.org 2>&1 | tail -1
ip route | head -3 | cut -c1-70
uptime
