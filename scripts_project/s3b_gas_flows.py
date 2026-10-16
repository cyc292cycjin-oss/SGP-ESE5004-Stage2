"""S3B R3 / smoke: gas supply structure of a solved network - LNG imports, domestic production and cross-border pipeline flows per country,
the Singapore gas balance and the SG -> MY re-export check (decision 68).

    python scripts_project/s3b_gas_flows.py --network <solved.nc> --output <json>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import pypsa


def country(n, bus):
    return str(n.buses.at[bus, "country"]) if bus in n.buses.index else ""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", required=True); ap.add_argument("--output", required=True); a = ap.parse_args()
    n = pypsa.Network(a.network)
    w = n.snapshot_weightings.generators
    g = n.generators
    e_gen = n.generators_t.p.mul(w, axis=0).sum()
    out = dict(network=a.network, objective=float(n.objective) if hasattr(n, "objective") else None)
    rows = {}
    for car in ["LNG import", "gas production", "H2 import"]:
        sel = g[g.carrier == car]
        if len(sel):
            e = e_gen.reindex(sel.index).fillna(0.0)
            rows[car] = {c: float(e[sel.country == c].sum()) / 1e6 for c in sorted(sel.country.unique())}
    out["supply_twh"] = rows
    lng = g[g.carrier == "LNG import"]
    if len(lng):
        cap = lng.p_nom_opt if "p_nom_opt" in lng else lng.p_nom
        e = e_gen.reindex(lng.index).fillna(0.0)
        out["lng_terminals"] = {i: dict(country=str(lng.at[i, "country"]), existing_mw=float(lng.at[i, "p_nom"]), p_nom_max_mw=float(lng.at[i, "p_nom_max"]), p_nom_opt_mw=float(cap[i]),
                                        energy_twh=float(e[i]) / 1e6, utilisation=(float(e[i]) / (float(cap[i]) * float(w.sum())) if float(cap[i]) > 0 else None),
                                        at_max=bool(float(cap[i]) >= float(lng.at[i, "p_nom_max"]) * (1 - 1e-6))) for i in lng.index}
    L = n.links[n.links.carrier == "gas pipeline"]
    p0 = n.links_t.p0[L.index].mul(w, axis=0) if len(L) else pd.DataFrame()
    xb = {}
    for i in L.index:
        c0, c1 = country(n, L.at[i, "bus0"]), country(n, L.at[i, "bus1"])
        if c0 == c1:
            continue
        f = p0[i]
        fwd, bwd = float(f.clip(lower=0).sum()) / 1e6, float((-f).clip(lower=0).sum()) / 1e6
        cap = float(L.at[i, "p_nom_opt"]) if "p_nom_opt" in L else float(L.at[i, "p_nom"])
        if fwd > 1e-6:
            xb.setdefault(f"{c0}->{c1}", []).append(dict(link=i, twh=fwd, p_nom_opt_mw=cap))
        if bwd > 1e-6:
            xb.setdefault(f"{c1}->{c0}", []).append(dict(link=i, twh=bwd, p_nom_opt_mw=cap))
    out["cross_border_pipeline_twh"] = {k: dict(total=sum(r["twh"] for r in v), links=v) for k, v in sorted(xb.items())}
    tot = {k: v["total"] for k, v in out["cross_border_pipeline_twh"].items()}
    sg_in = {k: v for k, v in tot.items() if k.endswith("->SG")}; sg_out = {k: v for k, v in tot.items() if k.startswith("SG->")}
    out["sg_gas_balance_twh"] = dict(lng=rows.get("LNG import", {}).get("SG", 0.0), pipeline_in=sg_in, pipeline_out=sg_out, net_pipeline_in=sum(sg_in.values()) - sum(sg_out.values()))
    out["sg_reexport_to_my_twh"] = tot.get("SG->MY", 0.0)
    # gas uses in SG by link carrier (bus0 = an SG gas bus)
    gas_buses = [b for b in n.buses.index if n.buses.at[b, "carrier"] == "gas"]
    uses = {}
    for i in n.links.index[n.links.bus0.isin(gas_buses)]:
        if n.links.at[i, "carrier"] == "gas pipeline":
            continue
        c = country(n, n.links.at[i, "bus0"])
        uses.setdefault(c, {}).setdefault(n.links.at[i, "carrier"], 0.0)
        uses[c][n.links.at[i, "carrier"]] += float(n.links_t.p0[i].mul(w).sum()) / 1e6 if i in n.links_t.p0 else 0.0
    loads = n.loads[n.loads.bus.isin(gas_buses)]
    for i in loads.index:
        c = country(n, loads.at[i, "bus"]); e = float(n.loads_t.p[i].mul(w).sum()) / 1e6 if i in n.loads_t.p else 0.0
        uses.setdefault(c, {}).setdefault("load: " + str(loads.at[i, "carrier"]), 0.0); uses[c]["load: " + str(loads.at[i, "carrier"])] += e
    out["gas_uses_twh"] = {c: {k: v for k, v in sorted(d.items()) if abs(v) > 1e-6} for c, d in sorted(uses.items())}
    Path(a.output).write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps(dict(lng=rows.get("LNG import"), production=rows.get("gas production"), cross_border=tot, sg=out["sg_gas_balance_twh"]), indent=0)[:3000])


if __name__ == "__main__":
    main()
