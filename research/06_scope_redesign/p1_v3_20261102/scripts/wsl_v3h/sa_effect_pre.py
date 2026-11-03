"""V3 HPC package step 3, BEFORE the S-A smoke (read-only, no solver): first-order effect of S-A on the supplement 05 smoke solutions (S-B, 56 snapshots,
weights 8,760 / 56). For every ship link: annual input flow F (p0 x weight) of the S-B solution; freight S-B = F x c_B, S-A = F x c_A (same flows); cargo
no longer lost under S-A = F x (1 - eta_B) valued at the destination bus price. INFERENCE only: the flows would re-optimise under S-A.
usage: python sa_effect_pre.py <smoke_s5 dir> <registry csv> <out json>"""
import json, sys
from pathlib import Path
import pandas as pd
import pypsa

run, regf, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
reg = pd.read_csv(regf, dtype=str, keep_default_na=False).set_index("param_id"); rv = lambda p: float(reg.loc[p, "value"])
KEY = {"oil non-fossil ship": "oil", "methanol ship": "methanol", "ammonia ship": "ammonia"}
res = {}
for rid in ("integrated", "no_new_xb"):
    f = sorted((run / rid).glob("*_solved.nc"))[0]; n = pypsa.Network(str(f)); w = n.snapshot_weightings.objective
    L = n.links[n.links.carrier.isin(list(KEY))]; p0 = n.links_t.p0[L.index].mul(w, axis=0).sum()
    km = L.route_km.astype(float); key = L.carrier.map(KEY)
    cB = pd.Series([rv(f"liquid_ship_ckm_td_{k}") * d for k, d in zip(key, km)], index=L.index)
    cA = pd.Series([rv(f"liquid_ship_fixed_ieaghg_{k}") + rv(f"liquid_ship_ckm_ieaghg_{k}") * d for k, d in zip(key, km)], index=L.index)
    price = n.buses_t.marginal_price.reindex(columns=L.bus1).set_axis(L.index, axis=1)
    lost = (n.links_t.p0[L.index] * (1.0 - L.efficiency)).mul(w, axis=0)
    loss_value = float((lost * price).sum().sum())
    by = lambda s: {k: float(v) / 1e9 for k, v in s.groupby(L.carrier).sum().items()}
    res[rid] = dict(network=f.name, shipped_twh=by(p0 / 1e3), freight_sb_bn=by(p0 * cB), freight_sa_bn=by(p0 * cA), freight_sb_total_bn=float((p0 * cB).sum() / 1e9),
                    freight_sa_total_bn=float((p0 * cA).sum() / 1e9), cargo_loss_value_bn=loss_value / 1e9,
                    first_order_cost_change_bn=float((p0 * cA).sum() - (p0 * cB).sum() - loss_value) / 1e9, objective_bn=float(n.objective) / 1e9 if n.objective else None)
res["b6_first_order_change_bn"] = res["no_new_xb"]["first_order_cost_change_bn"] - res["integrated"]["first_order_cost_change_bn"]
out.write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps({k: (v if not isinstance(v, dict) else {x: v[x] for x in ("freight_sb_total_bn", "freight_sa_total_bn", "cargo_loss_value_bn", "first_order_cost_change_bn")}) for k, v in res.items()}))
