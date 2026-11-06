"""Fable W08 review, stage 4 (questions 4.2 / 4.3): read-only decomposition of the 56-snapshot smoke solves (no solver).
For R0 (v3.1 network on the W08 code), R1 (v4 main F1) and R3 (v4 IId F1): objective constants (objective - objective_lp), cost breakdown by
component / carrier, solid-biomass pool use by consuming link carrier, industrial heat supply by technology. usage: smoke_decomp.py <smoke56 dir> <OUT.json>"""
import json
import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
import pypsa  # noqa: E402

RUN, OUT = Path(sys.argv[1]), Path(sys.argv[2])
RUNS = {"v31_F1": "integrated", "v4_F1": "integrated", "v4iid_F1": "integrated", "v4_F2": "no_new_xb"}
res = {}
for r, sc in RUNS.items():
    d = RUN / r
    rec = json.loads((d / "SOLVE_RECEIPT.json").read_text())
    x = dict(objective=rec.get("objective"), objective_lp=rec.get("objective_lp"), constant=(rec.get("objective") or 0) - (rec.get("objective_lp") or 0), termination=rec.get("termination_condition"))
    cb = json.loads((d / "COMPONENT_COST_BREAKDOWN_SUMMARY.json").read_text())
    x["cost_breakdown_keys"] = list(cb.keys())[:40]
    x["cost_breakdown"] = cb
    n = pypsa.Network(str(d / f"{sc}_SMOKE_TEST_ONLY_solved.nc"))
    w = n.snapshot_weightings.generators
    # solid biomass pool use by consuming link carrier and country
    use = {}
    bio_buses = set(n.buses.index[n.buses.carrier == "solid biomass"])
    L = n.links[n.links.bus0.isin(bio_buses)]
    p0 = n.links_t.p0[L.index].mul(w, axis=0).sum()
    for k in L.index:
        c = n.buses.at[L.at[k, "bus0"], "country"]; car = L.at[k, "carrier"]
        use.setdefault(c, {})[car] = use.setdefault(c, {}).get(car, 0.0) + float(p0[k])
    x["biomass_use_mwh_56snap_weighted"] = use
    x["biomass_use_total_twh_annualised"] = {c: sum(v.values()) / 1e6 for c, v in use.items()}
    # industrial heat supply by technology (links feeding industry heat buses)
    hb = set(n.buses.index[n.buses.carrier.str.startswith("industry heat")])
    H = n.links[n.links.bus1.isin(hb)]
    p1 = (-n.links_t.p1[H.index]).mul(w, axis=0).sum()
    sup = {}
    for k in H.index:
        c = n.buses.at[H.at[k, "bus1"], "country"]; car = H.at[k, "carrier"]
        sup.setdefault(c, {})[car] = sup.setdefault(c, {}).get(car, 0.0) + float(p1[k])
    x["industry_heat_supply_mwh_weighted"] = sup
    # marginal prices of the solid biomass buses: mean and max over the 56 snapshots (subgradient check for a removed zero-capacity pool)
    lam = n.buses_t.marginal_price[sorted(bio_buses)]
    x["solid_biomass_price_mean_max"] = {b: dict(mean=float(lam[b].mean()), max=float(lam[b].max()), min=float(lam[b].min())) for b in lam.columns}
    res[r] = x
    print(r, "objective", x["objective"], "lp", x["objective_lp"], "constant", x["constant"])
json.dump(res, open(OUT, "w"), indent=1, default=float)
# differences v4 - v31 in the cost breakdown (flatten numeric leaves)
def flat(d, pre=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flat(v, f"{pre}{k}/"))
        elif isinstance(v, (int, float)):
            out[f"{pre}{k}"] = float(v)
    return out
a = flat(res["v31_F1"]["cost_breakdown"]); b = flat(res["v4_F1"]["cost_breakdown"]); c = flat(res["v4iid_F1"]["cost_breakdown"])
rows = [dict(key=k, v31=a.get(k, 0.0), v4=b.get(k, 0.0), d_v4=b.get(k, 0.0) - a.get(k, 0.0), d_iid=c.get(k, 0.0) - a.get(k, 0.0)) for k in sorted(set(a) | set(b) | set(c))]
df = pd.DataFrame(rows); df = df[df.d_v4.abs() > 1e7].sort_values("d_v4", key=abs, ascending=False)
pd.set_option("display.width", 250); print(df.head(40).to_string())
print("biomass use TWh (annualised):", {r: {c: round(v, 2) for c, v in res[r]["biomass_use_total_twh_annualised"].items()} for r in res})
for r in ("v31_F1", "v4_F1"):
    print(r, "ID biomass use by link carrier (TWh):", {k: round(v / 1e6, 2) for k, v in res[r]["biomass_use_mwh_56snap_weighted"].get("ID", {}).items()})
    print(r, "ID industry heat supply (TWh):", {k: round(v / 1e6, 2) for k, v in res[r]["industry_heat_supply_mwh_weighted"].get("ID", {}).items()})
    print(r, "ID solid biomass price mean/max:", res[r]["solid_biomass_price_mean_max"].get("solid biomass ID"))
