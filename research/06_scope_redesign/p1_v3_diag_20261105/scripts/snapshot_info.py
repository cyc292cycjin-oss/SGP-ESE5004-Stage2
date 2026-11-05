"""V3 DIAG: snapshot index, weightings and month boundaries of a package network; the required constraint hooks in n.meta (read only)."""
import json, sys
import pypsa, logging
logging.getLogger("pypsa").setLevel(logging.ERROR)
net, out = sys.argv[1], sys.argv[2]
n = pypsa.Network(net)
s = n.snapshots
w = n.snapshot_weightings
months = {}
for i, t in enumerate(s):
    k = f"{t.year:04d}-{t.month:02d}"
    months.setdefault(k, [i, i])
    months[k][1] = i
res = dict(network=net, snapshots=int(len(s)), first=str(s[0]), last=str(s[-1]),
           weight_cols={c: dict(min=float(w[c].min()), max=float(w[c].max()), sum=float(w[c].sum())) for c in w.columns},
           months={k: dict(start=v[0], end_excl=v[1] + 1, length=v[1] - v[0] + 1) for k, v in months.items()},
           required_constraint_hooks=list(n.meta.get("required_constraint_hooks", [])),
           scenario=n.meta.get("scenario"))
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
