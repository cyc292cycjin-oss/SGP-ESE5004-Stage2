# DFX phase 4 (ON the instance, read-only): print small record files for the evidence copy, licence-like lines filtered (same filter as r_status.sh)
S="license[i]d|registered[[:space:]]+to|wls(access|secret)|academic|licen[cs]e (file|key|id)"
P=/root/autodl-tmp/dfx_v8
for f in "$P/ENV_CHECK_EXISTING.json" $P/PREFLIGHT_CONSOLE_*.log "$P/runs/dfx/RUN_DFX_CONSOLE.log" "$P/runs/dfx/STATUS.txt"; do
  [ -f "$f" ] || { echo "@@MISSING $f"; continue; }
  echo "@@FILE $(basename "$f") $(stat -c %s "$f") B; filtered lines: $(grep -ciE "$S" "$f")"
  grep -viE "$S" "$f"
done
echo "@@END"
