"""S4B-0 item 6: annual structural gaps of the disconnected scenario (CO2 and gas), solver-free, with methanation and LNG expansion.

    python scripts_project/s4b_structural_gap.py --network <disconnected 2920x3h nc> [--network <integrated nc>] --output <json> [--csv <csv>]

CO2 (per country, t/a):
  * s3b_method = scripts_project/s2_structural_gap.country_table unchanged (every fossil final-energy meter counted as unavoidable).
  * with_substitution = the same with the routes that exist in the network: oil meters are avoidable when a non-fossil oil route exists
    (Fischer-Tropsch / BtL / electrobiofuels / FT-fuel import on the non-fossil pool, origin_neutral); gas meters are avoidable when a
    synthetic or biogenic methane route exists in the country (Sabatier with in-country captured CO2, biogas upgrading); coal / lignite meters,
    process emissions, plastics burned and feedstock release stay unavoidable. A country without own storage and without a cross-border CO2
    pipeline needs zero unavoidable CO2; with own storage only, unavoidable CO2 <= the annual cap.
Gas (per country, TWh/a): fixed gas demand (gas final energy + gas feedstock loads) vs domestic production cap + LNG cap (p_nom_max x 8760 h,
  now with the decision-72 expansion) + biogas potential x upgrading efficiency; the residual must come from methanation; its electricity need
  (electrolysis for the Sabatier H2 + DAC electricity for its CO2; DAC heat reported separately) is compared with the country's variable
  renewable potential (sum of p_max_pu x p_nom_max over the loaded year).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from s2_structural_gap import country_table


def gas_table(n):
    H = 8760.0; w = n.snapshot_weightings.generators; scale = H / float(w.sum())
    pset = n.get_switchable_as_dense("Load", "p_set"); annual = pset.mul(w, axis=0).sum() * scale
    L = n.loads; g = n.generators; caps = n.meta.get("external_annual_caps", {})
    links = n.links
    sab = links[links.carrier == "Sabatier"]; el = links[links.carrier == "H2 Electrolysis"]; dac = links[links.carrier == "DAC"]
    eff_sab = float(sab.efficiency.iloc[0]) if len(sab) else None; t_per_mwh_h2 = float(-sab.efficiency2.iloc[0]) if len(sab) else None
    eff_el = float(el.efficiency.iloc[0]) if len(el) else None
    dac_t_per_mwh_el = float(dac.efficiency.iloc[0]) if len(dac) else None   # t CO2 per MWh electricity input
    dac_heat_per_t = float(-dac.efficiency3.iloc[0] / dac.efficiency.iloc[0]) if (len(dac) and "efficiency3" in dac and str(dac.bus3.iloc[0]).endswith("industry heat")) else 0.0
    pmax = n.get_switchable_as_dense("Generator", "p_max_pu")
    up = links[links.carrier == "biogas upgrading"]; up_eff = float(up.efficiency.mean()) if len(up) else 1.0
    rows = []
    for c in sorted(set(n.buses.country.dropna()) - {"", "ASEAN"}):
        dem = float(annual[L.index[(L.country == c) & L.carrier.isin(["gas final energy", "gas feedstock"])]].sum())
        prod = g[(g.carrier == "gas production") & (g.country == c)]; pc = float(sum(caps.get(i, 0.0) for i in prod.index))
        lng = g[(g.carrier == "LNG import") & (g.country == c)]; lc = float((lng.p_nom_max * H).sum()); le = float((lng.p_nom * H).sum())
        bg = n.stores[(n.stores.carrier == "biogas") & (n.stores.country == c)] if "country" in n.stores else n.stores.iloc[0:0]
        bgc = float(bg.e_initial.sum()) * up_eff
        supply = pc + lc + bgc; residual = max(0.0, dem - supply)
        n_sab = int((sab.country == c).sum())
        h2 = residual / eff_sab if (eff_sab and residual > 0) else 0.0
        co2 = h2 * t_per_mwh_h2 if t_per_mwh_h2 else 0.0
        e_need = (h2 / eff_el if eff_el else 0.0) + (co2 / dac_t_per_mwh_el if dac_t_per_mwh_el else 0.0)
        ren = g[g.carrier.isin(["solar", "solar rooftop", "onwind", "offwind-ac", "offwind-dc"]) & g.p_nom_extendable & (g.bus.map(n.buses.country) == c)]   # electric-base generators carry no country column
        pot = float(sum((pmax[k] * w).sum() * scale * min(float(z.p_nom_max), 1e9) for k, z in ren.iterrows()))
        rows.append(dict(country=c, fixed_gas_demand_twh=dem / 1e6, production_cap_twh=pc / 1e6, lng_cap_twh=lc / 1e6, lng_existing_twh=le / 1e6, biogas_twh=bgc / 1e6,
                         supply_max_without_methanation_twh=supply / 1e6, gas_gap_without_methanation_twh=residual / 1e6, sabatier_links=n_sab,
                         methanation_h2_twh=h2 / 1e6, methanation_co2_mt=co2 / 1e6, methanation_electricity_twh=e_need / 1e6, methanation_dac_heat_twh=co2 * dac_heat_per_t / 1e6,
                         variable_renewable_potential_twh=pot / 1e6, gas_gap_after_methanation_twh=(0.0 if (n_sab > 0 and e_need <= pot) else residual / 1e6)))
    return dict(rows=rows, parameters=dict(sabatier_efficiency=eff_sab, sabatier_t_co2_per_mwh_h2=t_per_mwh_h2, electrolysis_efficiency=eff_el, dac_t_per_mwh_electricity=dac_t_per_mwh_el,
                                          dac_heat_mwh_per_t=dac_heat_per_t, biogas_upgrading_efficiency=up_eff, lng_rule=n.meta.get("research_gas_network", {}).get("lng", {}).get("expansion")))


def co2_with_substitution(n, base):
    links = n.links
    has_nf_oil = bool(links.carrier.isin(["Fischer-Tropsch", "BtL", "electrobiofuels"]).any() or (n.generators.carrier == "FT fuel import").any())
    nf_twins = bool(links.index.str.endswith(" non-fossil").any())
    out = []
    for r in base["rows"]:
        c = r["country"]; fb = r["fossil_by_fuel_t"]
        sab = bool(((links.carrier == "Sabatier") & (links.country == c)).any()); bio = bool(((links.carrier == "biogas upgrading") & (links.country == c)).any())
        avoid_oil = fb.get("oil", 0.0) if (has_nf_oil and nf_twins) else 0.0
        avoid_gas = fb.get("gas", 0.0) if (sab or bio) else 0.0
        unav = r["unavoidable_co2_t"] - avoid_oil - avoid_gas
        cap = r["storage_cap_t_per_year"]; pipes = r["cross_border_co2_pipelines"]
        if pipes:
            gap = 0.0; reading = "export via cross-border CO2 pipeline"
        elif cap > 0:
            gap = max(0.0, unav - cap); reading = "own storage" if gap == 0 else "own storage cap too small"
        else:
            gap = unav; reading = "no storage potential and no cross-border CO2 pipeline"
        out.append(dict(country=c, unavoidable_s3b_method_t=r["unavoidable_co2_t"], avoidable_oil_t=avoid_oil, avoidable_gas_t=avoid_gas, unavoidable_with_substitution_t=unav,
                        coal_lignite_t=fb.get("coal", 0.0) + fb.get("lignite", 0.0), process_emissions_t=r["process_emissions_t"], plastics_burned_t=r["plastics_burned_t"],
                        feedstock_release_t=r["feedstock_release_t"], storage_cap_t_per_year=cap, cross_border_co2_pipelines=pipes,
                        structural_co2_gap_s3b_method_t=r["structural_co2_gap_t"], structural_co2_gap_with_substitution_t=gap, reading=reading,
                        sabatier_in_country=sab, biogas_upgrading_in_country=bio))
    return out


def main():
    import pypsa
    p = argparse.ArgumentParser(); p.add_argument("--network", type=Path, action="append", required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--csv", type=Path)
    a = p.parse_args(); out = {}; flat = []
    for path in a.network:
        n = pypsa.Network(str(path)); base = country_table(n); sc = base["scenario"]
        co2 = co2_with_substitution(n, base); gas = gas_table(n)
        out[sc] = dict(network=str(path), co2=co2, gas=gas, biomass=[dict(country=r["country"], biomass_final_demand_mwh=r["biomass_final_demand_mwh"], solid_biomass_potential_mwh=r["solid_biomass_potential_mwh"],
                                                                        structural_biomass_gap_mwh=r["structural_biomass_gap_mwh"]) for r in base["rows"]],
                       reading="solver-free annual bounds; a positive with_substitution CO2 gap or a positive gas gap after methanation means the per-country balance cannot close in this scenario")
        for r, gr in zip(co2, gas["rows"]):
            assert r["country"] == gr["country"]
            flat.append(dict(scenario=sc, **{k: v for k, v in r.items() if not isinstance(v, (list, dict))}, **{k: v for k, v in gr.items() if k != "country"}))
        print(sc, [(r["country"], round(r["structural_co2_gap_s3b_method_t"] / 1e6, 2), round(r["structural_co2_gap_with_substitution_t"] / 1e6, 2)) for r in co2])
        print(sc, [(g["country"], round(g["gas_gap_without_methanation_twh"], 1), round(g["gas_gap_after_methanation_twh"], 1)) for g in gas["rows"]])
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(out, indent=1, default=float))
    if a.csv:
        pd.DataFrame(flat).to_csv(a.csv, index=False)


if __name__ == "__main__":
    main()
