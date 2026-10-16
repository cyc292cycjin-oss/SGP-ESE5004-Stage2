"""S4A-2 (L15): add the GEM units that are in service in 2050 but absent from the frozen electric base (research.fleet).

Input table research_inputs/fleet_v5/FLEET_ADDITIONS_2050.csv (scripts_project/s4a_2_fleet_data.py): GEM GIPT 2026-09 units,
operating (+ construction when research.fleet.include_construction) with start year + S1 lifetime > 2050, not matched to an
existing-unit identity, mapped to the nearest AC node of their country. Units are aggregated per node and model class into one
component `existing_survivor::<node>::<class>::S4A`; every GEM unit is recorded in n.meta["existing_unit_components"] so that the
static validation (capacity identity, no CAPEX, not extendable) and the FOM-once rule apply unchanged.

Representation (same conventions as the frozen stock):
  coal / lignite / oil / CCGT / OCGT existing  Link <node> <fuel> -> <node> (+ national atmosphere), p_nom = MW_el / efficiency,
       efficiency, FOM (%/a x investment, EUR/MW_el/a, objective constant) and VOM (marginal_cost = VOM x efficiency per MWh fuel)
       from technology-data v0.15.0 (grade B); CO2 port = fuel CO2 intensity (technology-data)
  geothermal existing  Generator, availability 0.7194 and FOM/VOM from AEO8 (decision 52, grade C)
  solar / onwind / offwind existing  Generator, availability = the node candidate profile of the same carrier (research.renewable
       variant), FOM technology-data (grade B)
  hydro existing  StorageUnit, inflow per MW and max_hours copied from the node (else country) existing reservoir units (grade C
       proxy), efficiency_dispatch 0.9, FOM technology-data hydro
  ror existing  Generator, p_max_pu from the node (else country) existing run-of-river units (grade C proxy), FOM technology-data ror
  PHS existing  StorageUnit, 6 h (decision proxy of the existing PHS), round-trip 0.75 (technology-data PHS), FOM technology-data
  waste existing  not added (no waste-to-energy fuel pathway in the model; listed as DATA_PENDING in the ledger)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from s2_layers import cost, country_of, ensure_carrier

FUEL_OF = {"coal existing": ("coal", "coal"), "lignite existing": ("lignite", "lignite"), "oil existing": ("oil", "oil"), "CCGT existing": ("gas", "CCGT"), "OCGT existing": ("gas", "OCGT")}
AEO8_GEOTHERMAL_CF = 0.719443559520017   # S2-1 (decision 52): AEO8 C.4/C.5 27.1 TWh / (4.3 GW x 8.76)


def _atmo(n, c):
    from carrier_architecture import atmosphere_bus
    return atmosphere_bus(c)


def add_gem_fleet(n, costs, cfg, repo: Path):
    F = dict(cfg["research"].get("fleet") or {})
    led = dict(enabled=bool(F.get("gem_additions", False)), added=[], skipped=[], fom_eur=0.0, by_class_mw={})
    if not led["enabled"]:
        n.meta["research_fleet"] = led
        return led
    table = Path(repo) / str(F.get("table", "research_inputs/fleet_v5/FLEET_ADDITIONS_2050.csv"))
    df = pd.read_csv(table, keep_default_na=False)
    df["capacity_mw"] = df.capacity_mw.astype(float); df["start_year"] = df.start_year.astype(float)
    if not bool(F.get("include_construction", True)):
        df = df[df.Status == "operating"]
    import hashlib
    led["table"] = dict(path=str(table.relative_to(repo)), sha256=hashlib.sha256(table.read_bytes()).hexdigest(), units=int(len(df)), mw=float(df.capacity_mw.sum()))
    n.meta.setdefault("existing_unit_components", {})
    ident = n.meta["existing_unit_components"]
    w = n.snapshot_weightings.generators
    su = n.storage_units; g = n.generators
    for (node, cls), d in df.groupby(["node", "model_class"]):
        if node not in n.buses.index:
            led["skipped"].append(dict(node=node, cls=cls, mw=float(d.capacity_mw.sum()), reason="node not in network")); continue
        c = country_of(n, node); mw = float(d.capacity_mw.sum()); name = f"existing_survivor::{node}::{cls}::S4A"
        start = int(d.start_year.min()); life = float(d.lifetime.iloc[0])
        units = {f"GEM:{u.gem_unit_id}": dict(component=name, node=node, capacity_mw=float(u.capacity_mw), commissioning_year=int(u.start_year), retirement_year=float(u.retire_year), source="Global Integrated Power September 2026.xlsx (GEM GIPT 2026-09)",
                                             source_version="1c99186c44ef7c1753b36ffee3c011041ba4723da43941286fd571d38b2db18e", age_basis="SOURCE_UNIT_YEAR", cohort_method=None, gem_status=str(u.Status), s4a_added=True) for u in d.itertuples()}
        ensure_carrier(n, cls)
        if cls in FUEL_OF:
            fuel, tech = FUEL_OF[cls]
            eff = cost(costs, tech, "efficiency"); fom = cost(costs, tech, "FOM") / 100.0 * cost(costs, tech, "investment"); vom = cost(costs, tech, "VOM")
            co2 = float(costs.at[fuel, "co2_emissions"])
            fb = f"{node} {fuel}"
            if fb not in n.buses.index:
                led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="fuel bus missing " + fb)); continue
            n.add("Link", name, bus0=fb, bus1=node, bus2=_atmo(n, c), carrier=cls, p_nom=mw / eff, p_nom_extendable=False, p_nom_min=0.0, efficiency=eff, efficiency2=co2,
                  capital_cost=0.0, marginal_cost=vom * eff, lifetime=life, build_year=start)
            n.links.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "variable_cost_method", "cost_qualification", "border_class"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, "technology-data v0.15.0 VOM x efficiency (grade B)", "TECHNOLOGY_DATA_V015_GRADE_B", "domestic"]
            comp = ("Link", name)
        elif cls == "geothermal existing":
            fom = cost(costs, "geothermal", "FOM") / 100.0 * cost(costs, "geothermal", "investment"); vom = cost(costs, "geothermal", "VOM")
            n.add("Generator", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, p_max_pu=AEO8_GEOTHERMAL_CF, capital_cost=0.0, marginal_cost=vom, efficiency=1.0, lifetime=life, build_year=start)
            n.generators.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "variable_cost_method", "cost_qualification"]] = \
                ["existing_survivor", c, "EXISTING_GEOTHERMAL", fom, fom * mw, "AEO8 D.15 Geothermal average VOM (grade C)", "AEO8_GRADE_C_FOM_CONSTANT_VOM"]
            comp = ("Generator", name)
        elif cls in ("solar existing", "onwind existing", "offwind existing"):
            tech = {"solar existing": "solar", "onwind existing": "onwind", "offwind existing": "offwind"}[cls]
            cand = {"solar existing": f"{node} solar-2025", "onwind existing": f"{node} onwind-2025", "offwind existing": f"{node} offwind-ac-2025"}[cls]
            if cand not in n.generators_t.p_max_pu.columns:
                led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="no candidate profile " + cand)); continue
            fom = cost(costs, tech, "FOM") / 100.0 * cost(costs, tech, "investment"); vom = cost(costs, tech, "VOM")
            n.add("Generator", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, capital_cost=0.0, marginal_cost=vom, efficiency=1.0, lifetime=life, build_year=start)
            n.generators_t.p_max_pu[name] = n.generators_t.p_max_pu[cand].values
            n.generators.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "variable_cost_method", "cost_qualification"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, "technology-data v0.15.0 VOM (grade B); availability = node candidate profile", "TECHNOLOGY_DATA_V015_GRADE_B"]
            comp = ("Generator", name)
        elif cls == "ror existing":
            ex = g[(g.carrier == "ror existing") & (g.bus == node)]; scope = "node"
            if not len(ex):
                ex = g[(g.carrier == "ror existing") & (g.bus.map(n.buses.country) == c)]; scope = "country"
            ex = ex[ex.index.isin(n.generators_t.p_max_pu.columns)]
            if not len(ex):
                led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="no existing ROR availability proxy in " + c)); continue
            prof = (n.generators_t.p_max_pu[ex.index] * ex.p_nom).sum(axis=1) / ex.p_nom.sum()
            fom = cost(costs, "ror", "FOM") / 100.0 * cost(costs, "ror", "investment")
            n.add("Generator", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, capital_cost=0.0, marginal_cost=0.0, efficiency=0.9, lifetime=life, build_year=start)
            n.generators_t.p_max_pu[name] = prof.values
            n.generators.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "variable_cost_method", "cost_qualification", "hydro_subtype"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, f"availability proxy = capacity-weighted existing ROR of the {scope} (grade C)", "TECHNOLOGY_DATA_V015_FOM_PROXY_AVAILABILITY", "Run-Of-River"]
            comp = ("Generator", name)
        elif cls == "hydro existing":
            ex = su[(su.carrier == "hydro existing") & (su.bus == node)]; scope = "node"
            if not len(ex) or not ex.index.isin(n.storage_units_t.inflow.columns).any():
                ex = su[(su.carrier == "hydro existing") & (su.bus.map(n.buses.country) == c)]; scope = "country"
            ex = ex[ex.index.isin(n.storage_units_t.inflow.columns)]
            if not len(ex):
                led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="no existing reservoir inflow proxy in " + c)); continue
            inflow_per_mw = n.storage_units_t.inflow[ex.index].sum(axis=1) / ex.p_nom.sum(); hours = float((ex.max_hours * ex.p_nom).sum() / ex.p_nom.sum())
            fom = cost(costs, "hydro", "FOM") / 100.0 * cost(costs, "hydro", "investment")
            n.add("StorageUnit", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, max_hours=hours, efficiency_store=0.0, efficiency_dispatch=0.9, p_min_pu=0.0, cyclic_state_of_charge=True, capital_cost=0.0, marginal_cost=0.0, lifetime=life, build_year=start)
            n.storage_units_t.inflow[name] = (inflow_per_mw * mw).values
            n.storage_units.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "hydro_subtype", "variable_cost_method"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, "Reservoir", f"inflow per MW and max_hours = capacity-weighted existing reservoirs of the {scope} (grade C)"]
            comp = ("StorageUnit", name)
        elif cls == "PHS existing":
            eff = float(np.sqrt(cost(costs, "PHS", "efficiency"))); fom = cost(costs, "PHS", "FOM") / 100.0 * cost(costs, "PHS", "investment")
            n.add("StorageUnit", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, max_hours=6.0, efficiency_store=eff, efficiency_dispatch=eff, p_min_pu=-1.0, cyclic_state_of_charge=True, capital_cost=0.0, marginal_cost=0.0, lifetime=life, build_year=start)
            n.storage_units.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "hydro_subtype", "variable_cost_method"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, "Pumped Storage", "6 h decision proxy of the existing PHS; round trip technology-data PHS 0.75 (grade C)"]
            comp = ("StorageUnit", name)
        else:
            led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="no representation (waste-to-energy pathway absent) -> DATA_PENDING")); continue
        for k, v in units.items():
            ident[k] = dict(v, component_type=comp[0], component=comp[1])
        fom_total = float(n.df(comp[0]).at[name, "existing_annual_fixed_om_eur"])
        led["fom_eur"] += fom_total; led["by_class_mw"][cls] = led["by_class_mw"].get(cls, 0.0) + mw
        led["added"].append(dict(component=name, component_type=comp[0], node=node, country=c, cls=cls, mw=mw, units=len(units), annual_fom_eur=fom_total))
    n.meta["existing_annual_fixed_om_eur"] = float(n.meta.get("existing_annual_fixed_om_eur", 0.0)) + led["fom_eur"]
    led["summary"] = dict(components=len(led["added"]), mw=float(sum(a["mw"] for a in led["added"])), skipped_mw=float(sum(s["mw"] for s in led["skipped"])), fom_eur=led["fom_eur"])
    n.meta["research_fleet"] = led
    return led
