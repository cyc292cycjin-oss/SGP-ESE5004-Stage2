# V3 screening (ON the instance, read-only): per run the receipt fields for the progress line (termination, objective with and without the constant, times)
O=/root/autodl-tmp/v3_screen/runs/dfx; E=/root/autodl-tmp/envs/pypsa-earth/bin/python
for r in V1 V2 V4 V5 V3; do
  f=$O/$r/SOLVE_RECEIPT.json; [ -f "$f" ] || continue
  $E - "$f" "$r" "$(cat $O/$r/.label 2>/dev/null)" <<'X'
import json, sys
r = json.load(open(sys.argv[1]))
keys = {k: r[k] for k in r if any(s in k.lower() for s in ("objective", "termination", "status", "seconds", "runtime", "iter", "constant"))}
print(sys.argv[2], "label=" + (sys.argv[3] or "-"), json.dumps({k: v for k, v in keys.items() if not isinstance(v, (dict, list))})[:600])
X
done
