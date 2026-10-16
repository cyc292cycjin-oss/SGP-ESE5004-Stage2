"""S4B smoke summary: capacity / generation by country (s4a_4_smoke_compare.tables) for a solved 56x3h network against a reference smoke,
plus the S4B-0 items (Sabatier methane, electrobiofuels, Fischer-Tropsch, LNG imports and terminal expansion, domestic gas, CO2 flows).
SMOKE_TEST_ONLY results, representative weights; no scientific meaning before the cloud run (decision 47).

    python scripts_project/s4b_smoke_summary.py --new <solved.nc> --new-label S4B0 --old <solved.nc> --old-label S4A --output <dir>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

from s4a_4_smoke_compare import tables, country_of


def link_out(n, carrier, port="p1"):
    w = n.snapshot_weightings.generators; L = n.links[n.links.carrier == carrier]
    if L.empty:
        return {}
    p = (-n.links_t[port].reindex(columns=L.index, fill_value=0.0)).mul(w, axis=0).sum()
    s = pd.Series({k: float(v) for k, v in p.items()}).groupby(L.country).sum() / 1e6
    return {str(k): float(v) for k, v in s.items() if abs(v) > 1e-6}


def gen_out(n, carrier):
    w = n.snapshot_weightings.generators; g = n.generators[n.generators.carrier == carrier]
    if g.empty:
        return {}
    e = n.generators_t.p.reindex(columns=g.index, fill_value=0.0).mul(w, axis=0).sum()
    s = pd.Series({k: float(v) for k, v in e.items()}).groupby(g.country).sum() / 1e6
    return {str(k): float(v) for k, v in s.items() if abs(v) > 1e-6}


def system_items(n):
    g = n.generators; lng = g[g.carrier == "LNG import"]
    lng_cap = {str(k): dict(existing_gw=float(v.p_nom) / 1e3, optimal_gw=float(v.p_nom_opt) / 1e3, max_gw=float(v.p_nom_max) / 1e3, capex_eur_per_mw_a=float(v.capital_cost)) for k, v in lng.iterrows()}
    out = dict(objective=float(n.objective) if n.objective is not None else None,
               sabatier_gas_twh=link_out(n, "Sabatier"), sabatier_capacity_gw_h2={str(c): float(v) / 1e3 for c, v in n.links[n.links.carrier == "Sabatier"].groupby("country").p_nom_opt.sum().items() if v > 1e-3},
               electrobiofuels_oil_twh=link_out(n, "electrobiofuels"), fischer_tropsch_oil_twh=link_out(n, "Fischer-Tropsch"), btl_oil_twh=link_out(n, "BtL"),
               methanolisation_twh=link_out(n, "methanolisation"), smr_h2_twh=link_out(n, "SMR"), smr_cc_h2_twh=link_out(n, "SMR CC"), electrolysis_h2_twh=link_out(n, "H2 Electrolysis"),
               lng_import_twh=gen_out(n, "LNG import"), lng_terminals=lng_cap, domestic_gas_twh=gen_out(n, "gas production"),
               dac_captured_mt=link_out(n, "DAC"), co2_vent_links=int((n.links.carrier == "co2 vent").sum()))
    out["lng_expansion_gw"] = float(sum(max(0.0, v["optimal_gw"] - v["existing_gw"]) for v in lng_cap.values()))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--new", type=Path, required=True); ap.add_argument("--old", type=Path, default=None)
    ap.add_argument("--new-label", default="new"); ap.add_argument("--old-label", default="old"); ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True); L1, L0 = a.new_label, a.old_label
    nn = pypsa.Network(str(a.new)); tn = tables(nn); tn.to_csv(a.output / f"CAP_GEN_BY_COUNTRY_{L1}.csv", index=False)
    out = dict(new=str(a.new), new_label=L1, items_new=system_items(nn), asean_new=tn.groupby("group")[["gw", "twh"]].sum().round(3).to_dict("index"))
    if a.old and a.old.exists():
        no = pypsa.Network(str(a.old)); to = tables(no); to.to_csv(a.output / f"CAP_GEN_BY_COUNTRY_{L0}.csv", index=False)
        m = tn.merge(to, on=["group", "country"], how="outer", suffixes=(f"_{L1}", f"_{L0}")).fillna(0.0)
        m["d_gw"] = m[f"gw_{L1}"] - m[f"gw_{L0}"]; m["d_twh"] = m[f"twh_{L1}"] - m[f"twh_{L0}"]
        m.to_csv(a.output / f"CAP_GEN_BY_COUNTRY_{L1}_VS_{L0}.csv", index=False)
        out.update(old=str(a.old), old_label=L0, items_old=system_items(no), asean_old=to.groupby("group")[["gw", "twh"]].sum().round(3).to_dict("index"))
    (a.output / f"SMOKE_SUMMARY_{L1}.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(dict(objective_new=out["items_new"]["objective"], objective_old=out.get("items_old", {}).get("objective")), default=float))


if __name__ == "__main__":
    main()
