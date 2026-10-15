"""S2-7 structural (solver-free) net-zero feasibility table per country, annual basis (decisions 49/53).

For each country: unavoidable CO2 = fixed fossil final-energy demand x meter EF (meters whose CO2 port is the
national atmosphere) + exogenous process emissions (2.A + 2.C) + feedstock carbon release; sink access = own
sequestration cap (potential / 50 a) plus any cross-border CO2 pipeline present in the network. Fixed biomass
final-energy demand is compared with the domestic solid-biomass potential (no cross-border biomass, decision 36).

    python scripts_project/s2_structural_gap.py --network results_project/s2/integrated/integrated_2920_3h_unsolved.nc \
        --network results_project/s2/disconnected/disconnected_2920_3h_unsolved.nc --output results_project/s2/S2_STRUCTURAL_GAP_ANNUAL.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def country_table(n):
    w = n.snapshot_weightings.generators
    hours = float(w.sum())
    pset = n.get_switchable_as_dense("Load", "p_set")
    annual = pset.mul(w, axis=0).sum() * (8760.0 / hours)
    caps = n.meta["research_co2_storage"]["caps_t_per_year"]
    links = n.links
    xb = links[(links.carrier == "CO2 pipeline") & (links.border_class == "cross_border")] if "border_class" in links else links.iloc[0:0]
    rows = []
    for c in sorted(set(n.buses.country.dropna()) - {""}):
        loads = n.loads[n.loads.country == c]
        atm = f"co2 atmosphere {c}"
        meters = links[(links.country == c) & links.carrier.str.endswith("final-energy accounting") & (links.bus2 == atm)]
        fossil = {}
        for name, z in meters.iterrows():
            dem = float(annual[[l for l in loads.index if n.loads.at[l, "bus"] == z.bus1]].sum())
            fossil[str(z.carrier).split(" ")[0]] = fossil.get(str(z.carrier).split(" ")[0], 0.0) + dem * float(z.efficiency2)
        proc = float(n.generators[(n.generators.carrier == "process emissions") & (n.generators.country == c)].p_nom.sum()) * 8760.0
        feed = links[(links.country == c) & links.carrier.str.endswith(" feedstock")]
        feed_t = 0.0
        for name, z in feed.iterrows():
            dem = float(annual[[l for l in loads.index if n.loads.at[l, "bus"] == z.bus1]].sum())
            feed_t += dem * (float(z.efficiency2) + float(z.efficiency3))
        unavoidable = sum(fossil.values()) + proc + feed_t
        cap = float(caps.get(c, 0.0))
        pipes = [x for x in xb.index if c in (str(n.buses.at[xb.at[x, "bus0"], "country"]), str(n.buses.at[xb.at[x, "bus1"], "country"]))]
        partners = sorted({str(n.buses.at[xb.at[x, p], "country"]) for x in pipes for p in ("bus0", "bus1")} - {c})
        bio_dem = float(annual[loads.index[loads.carrier == "biomass final energy"]].sum())
        bio_pot = float(n.stores[(n.stores.bus == f"solid biomass {c}") & (n.stores.research_role == "FINITE_RESOURCE")].e_nom.sum())
        if cap > 0 or pipes:
            co2_gap = max(0.0, unavoidable - cap) if not pipes else 0.0
            co2_reading = "own storage" if cap >= unavoidable else ("export via cross-border CO2 pipeline" if pipes else "own storage cap too small")
        else:
            co2_gap = unavoidable
            co2_reading = "no storage potential and no cross-border CO2 pipeline"
        rows.append(dict(country=c, fossil_final_co2_t=sum(fossil.values()), fossil_by_fuel_t=fossil, process_emissions_t=proc, feedstock_release_t=feed_t,
                         unavoidable_co2_t=unavoidable, storage_cap_t_per_year=cap, cross_border_co2_pipelines=len(pipes), pipeline_partners=partners,
                         structural_co2_gap_t=co2_gap, co2_reading=co2_reading, biomass_final_demand_mwh=bio_dem, solid_biomass_potential_mwh=bio_pot,
                         structural_biomass_gap_mwh=max(0.0, bio_dem - bio_pot),
                         net_zero_structurally_feasible=bool(co2_gap <= 1e-6 and bio_dem <= bio_pot * (1 + 1e-9))))
    total = dict(unavoidable_co2_t=sum(r["unavoidable_co2_t"] for r in rows), storage_cap_t_per_year=sum(r["storage_cap_t_per_year"] for r in rows))
    return dict(scenario=n.meta.get("scenario"), horizon_hours_loaded=hours, basis="annual (loaded snapshots scaled to 8760 h)", rows=rows, asean_total=total,
                reading="A country is structurally infeasible for per-country net zero when its unavoidable CO2 has no sink (no storage and no cross-border pipeline) or exceeds its own cap without a pipeline, or when its fixed biomass final demand exceeds the domestic solid-biomass potential; no constraint is relaxed here.")


if __name__ == "__main__":
    import pypsa
    p = argparse.ArgumentParser(); p.add_argument("--network", type=Path, action="append", required=True); p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    out = {}
    for path in a.network:
        n = pypsa.Network(str(path)); t = country_table(n); out[t["scenario"]] = t
        print(t["scenario"], [(r["country"], round(r["structural_co2_gap_t"] / 1e6, 2), round(r["structural_biomass_gap_mwh"] / 1e6, 3), r["net_zero_structurally_feasible"]) for r in t["rows"]])
    a.output.write_text(json.dumps(out, indent=2))
