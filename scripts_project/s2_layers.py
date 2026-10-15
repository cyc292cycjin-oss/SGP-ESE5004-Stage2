"""S2 component layers on top of the S1 skeleton (S2 instruction + supplement 01, 2026-10-15).

Every builder adds components to an existing PyPSA network, records what it added in a ledger
and never creates a Load outside the single demand-ownership table. Carbon is booked through
explicit atmosphere ports of Links in the emitter's national atmosphere (country_carbon);
captured CO2 goes to `<node> co2 stored`, permanent storage to `co2 sequestered {ISO2}`.
Nothing here solves.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from carrier_architecture import COUNTRIES, ATMOSPHERE_CARRIER, atmosphere_bus, finite
from s2_costs import cost

HOURS = 8760.0
S2_OWNER_KIND = "S2_DEMAND_TABLE"
TFEC_SECTORS = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
LAND_TRANSPORT_ACCOUNTS = {"RoadResidualFuel", "TransportNEC", "TransportEmbeddedFuelParent"}
FUEL_EF_KEYS = {"coal": "coal", "oil": "oil", "gas": "gas", "unclassified_fuel": "oil"}  # technology-data CO2 intensity rows
# IEA, Defining energy access: 2020 methodology, Table 2 "Cookstove efficiencies by type and region"
COOKSTOVE_BASIC_FUELWOOD = {"ID": 0.08, "TH": 0.16}      # other ASEAN countries: "Other Southeast Asia" 0.08
COOKSTOVE_BASIC_DEFAULT = 0.08
COOKSTOVE_MODERN = 0.53                                  # modern stoves (LPG, electricity, natural gas, ...) 53 % (ID, TH, Other Southeast Asia)
ACCOUNT_FOR_SHARES = {"Industry": "IndustryFinalEnergy", "Transport": "RoadResidualFuel", "Residential": "ResidentialFuel",
                      "Commercial": "ServicesFuel", "AgricultureOthers": "AgricultureFinalEnergy", "NonEnergyUse": "IndustryFinalEnergy",
                      "ProcessEmissions": "IndustryFinalEnergy", "AviationInternational": "InternationalAviationBunker",
                      "AviationDomestic": "RoadResidualFuel"}


def jload(p):
    return json.loads(Path(p).read_text())


def country_of(n, node):
    return str(n.buses.at[node, "country"])


def ensure_carrier(n, name):
    if name not in n.carriers.index:
        n.add("Carrier", name, co2_emissions=0.0)


def add_bus(n, name, carrier, country, location=""):
    if name in n.buses.index:
        return name
    ensure_carrier(n, carrier)
    n.add("Bus", name, carrier=carrier)
    n.buses.loc[name, "country"] = country
    if "location" in n.buses:
        n.buses.loc[name, "location"] = location
    return name


def add_link(n, name, country, carrier, ports, effs, *, capital_cost=0.0, marginal_cost=0.0, lifetime=25.0, p_min_pu=0.0,
             role="CONVERSION", length=None, extra=None):
    """ports[0] is the input; effs[i] is the coefficient of ports[i+1] (negative = additional input)."""
    if name in n.links.index:
        raise ValueError("duplicate link " + name)
    ensure_carrier(n, carrier)
    kw = {f"bus{i}": b for i, b in enumerate(ports)}
    for i, e in enumerate(effs, 1):
        kw["efficiency" if i == 1 else f"efficiency{i}"] = finite(e, nonnegative=False)
    if length is not None:
        kw["length"] = float(length)
    n.add("Link", name, carrier=carrier, p_nom_extendable=True, p_nom=0.0, p_min_pu=float(p_min_pu), capital_cost=float(capital_cost),
          marginal_cost=float(marginal_cost), lifetime=float(lifetime), build_year=2050, **kw)
    n.links.loc[name, "country"] = country
    n.links.loc[name, "research_role"] = role
    n.links.loc[name, "asset_role"] = "new_build_candidate"
    for k, v in (extra or {}).items():
        n.links.loc[name, k] = v
    return name


# ----------------------------------------------------------------------------------------------
# S2-1: SMR, existing geothermal (decision 52), transmission (decision 45)
# ----------------------------------------------------------------------------------------------
def geothermal_unit_table(survival_json: Path) -> pd.DataFrame:
    S = jload(survival_json)
    rec = [r for r in S["unit_evidence"]["records"] if r.get("Technology") == "Geothermal"]
    cols = ["AssetID", "ParentAssetID", "Country", "OriginalCapacity", "CommissioningYear", "RetirementYear", "Lifetime", "LifetimeSource",
            "SurvivalStatus", "OriginalMappedBus", "Source", "AgeBasis", "S1LifetimeRerun"]
    df = pd.DataFrame(rec)
    for c in cols:
        if c not in df:
            df[c] = ""
    df = df[cols].copy()
    df["in_service_2050"] = df.SurvivalStatus == "SURVIVES_2050"
    df["judgement"] = np.where(df.SurvivalStatus == "SURVIVES_2050", "commissioning + 30 a > 2050: in service",
                      np.where(df.SurvivalStatus == "NOT_ACTIVE_2050", "commissioning + 30 a <= 2050: retired",
                      np.where(df.SurvivalStatus == "UNRESOLVED_COMMISSIONING", "no commissioning year: DATA_PENDING, not added", df.SurvivalStatus)))
    return df


def add_existing_geothermal(n, costs, survival_json: Path, capacity_factor: float, cf_source: str, bus_mapping: dict | None = None):
    """bus_mapping: reference-network bus id (OriginalMappedBus) -> research node, from the Assembly-V1 integration contract."""
    units = geothermal_unit_table(survival_json)
    bus_mapping = bus_mapping or {}
    units["node"] = [bus_mapping.get(str(b), {}).get("Node", str(b)) if isinstance(bus_mapping.get(str(b), {}), dict) else bus_mapping.get(str(b), str(b)) for b in units.OriginalMappedBus]
    live = units[units.in_service_2050]
    fom_eur_per_mw_a = cost(costs, "geothermal", "FOM") / 100.0 * cost(costs, "geothermal", "investment")
    vom = cost(costs, "geothermal", "VOM")
    ensure_carrier(n, "geothermal existing")
    added = []
    n.meta.setdefault("existing_unit_components", {})
    for node, g in live.groupby("node"):
        if node not in n.buses.index:
            raise ValueError("geothermal survivor bus not in network: " + str(node) + " (reference bus " + str(g.OriginalMappedBus.iloc[0]) + ")")
        country = country_of(n, node)
        name = f"existing_survivor::{node}::Geothermal::S2"
        p_nom = float(g.OriginalCapacity.sum())
        n.add("Generator", name, bus=node, carrier="geothermal existing", p_nom=p_nom, p_nom_extendable=False, p_max_pu=float(capacity_factor),
              capital_cost=0.0, marginal_cost=vom, efficiency=1.0, lifetime=float(g.Lifetime.iloc[0]), build_year=int(g.CommissioningYear.min()))
        n.generators.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "variable_cost_method", "cost_qualification"]] = \
            ["existing_survivor", country, "EXISTING_GEOTHERMAL", fom_eur_per_mw_a, fom_eur_per_mw_a * p_nom, "AEO8 D.15 Geothermal average VOM (grade C)", "AEO8_GRADE_C_FOM_CONSTANT_VOM"]
        for _, u in g.iterrows():
            n.meta["existing_unit_components"][u.AssetID] = dict(component_type="Generator", component=name, capacity_mw=float(u.OriginalCapacity), node=node,
                                                                 source=str(u.Source), commissioning_year=int(u.CommissioningYear), retirement_year=float(u.RetirementYear),
                                                                 age_basis=str(u.AgeBasis), cohort_method=None, s2_added=True)
        n.meta["existing_annual_fixed_om_eur"] = float(n.meta.get("existing_annual_fixed_om_eur", 0.0)) + fom_eur_per_mw_a * p_nom
        added.append(dict(generator=name, node=node, country=country, p_nom_mw=p_nom, units=list(g.AssetID), capacity_factor=capacity_factor,
                          cf_source=cf_source, fom_eur_per_mw_a=fom_eur_per_mw_a, annual_fom_eur=fom_eur_per_mw_a * p_nom, vom_eur_per_mwh=vom,
                          co2_simplification="non-condensable gas CO2 ignored (PyPSA-Eur practice); order of magnitude 0.12 tCO2/MWh (technology-data geothermal) x output"))
    return dict(added=added, units=units.to_dict("records"), in_service_mw=float(live.OriginalCapacity.sum()),
                pending_units=units[units.SurvivalStatus == "UNRESOLVED_COMMISSIONING"].AssetID.tolist())


def set_transmission_s2(n, cfg_transmission):
    from scenario_network import set_transmission_limit
    mode = cfg_transmission["volume_limit_mode"]
    if mode != "lvopt":
        return set_transmission_limit(n, cfg_transmission)
    if "lv_limit" not in n.global_constraints.index:
        raise ValueError("Reference transmission volume limit missing")
    lv = n.global_constraints.loc["lv_limit"]; carriers = lv.carrier_attribute.split(", ")
    lines = n.lines[n.lines.carrier.isin(carriers)]; links = n.links[n.links.carrier.isin(carriers)]
    existing = float((lines.s_nom * lines.length).sum() + (links.p_nom * links.length).sum())
    removed = dict(constant_mwkm=float(lv.constant), type=str(lv["type"]))
    n.remove("GlobalConstraint", "lv_limit")
    n.meta["approved_global_constraints"] = [g for g in n.meta.get("approved_global_constraints", []) if g != "lv_limit"]
    return dict(mode="lvopt", constant_mwkm=None, existing_volume_mwkm=existing, removed_reference_constraint=removed,
                sensitivity=dict(mode="factor_of_existing", factor=float(cfg_transmission["volume_limit_factor"])), carriers=carriers)


# ----------------------------------------------------------------------------------------------
# S2-2: CO2 capture, transport, storage
# ----------------------------------------------------------------------------------------------
def add_co2_layer(n, costs, s2cfg, registry: pd.DataFrame, nodes, cc_fraction: float):
    R = s2cfg["co2"]
    ledger = dict(renamed_buses=0, buffers=0, sequestration_countries={}, vents=0, pipelines=0, capture_links={})
    # 1. captured -> stored (upstream naming), one buffer Store per node
    mapping = {b: b.replace(" co2 captured", " co2 stored") for b in n.buses.index if n.buses.at[b, "carrier"] == "co2 captured"}
    if mapping:
        n.buses.rename(index=mapping, inplace=True)
        n.buses.loc[list(mapping.values()), "carrier"] = "co2 stored"
        ensure_carrier(n, "co2 stored")
        for typ in ["Link", "Store", "Generator", "Load", "StorageUnit"]:
            df = n.df(typ)
            for col in [c for c in df if c == "bus" or (c.startswith("bus") and c[3:].isdigit())]:
                df[col] = df[col].map(lambda x: mapping.get(x, x))
    ledger["renamed_buses"] = len(mapping)
    tank_fixed = cost(costs, "CO2 storage tank", "fixed")
    for node in nodes:
        b = f"{node} co2 stored"
        if b not in n.buses.index:
            add_bus(n, b, "co2 stored", country_of(n, node), node)
        n.add("Store", b, bus=b, carrier="co2 stored", e_nom_extendable=True, e_cyclic=True, e_initial=0.0, capital_cost=tank_fixed,
              lifetime=cost(costs, "CO2 storage tank", "lifetime"))
        n.stores.loc[b, ["country", "research_role"]] = [country_of(n, node), "CO2_BUFFER"]
        ledger["buffers"] += 1
    # 2. permanent storage per country (decisions 20, 28-30)
    seq_cost = float(R["sequestration_cost_eur_per_t"]); years = float(R["storage_years"])
    caps = {}
    for c in sorted(COUNTRIES):
        row = registry.loc[f"co2_injection_cap_{c}"]
        cap = float(row["value"]) if row["status"] != "DATA_PENDING" else 0.0
        caps[c] = cap
        if cap <= 0:
            ledger["sequestration_countries"][c] = dict(cap_t_per_year=0.0, store=None, note="no storage potential (decision 30)")
            continue
        sb = f"co2 sequestered {c}"
        add_bus(n, sb, "co2 sequestered", c, "")
        n.add("Store", sb, bus=sb, carrier="co2 sequestered", e_nom_extendable=True, e_nom_max=cap, e_cyclic=False, e_initial=0.0,
              capital_cost=seq_cost, lifetime=years)
        n.stores.loc[sb, ["country", "research_role"]] = [c, "PERMANENT_STORAGE"]
        n.meta.setdefault("store_power_rules", {})[sb] = "charge_only"
        links = []
        for node in [x for x in nodes if country_of(n, x) == c]:
            links.append(add_link(n, f"{node} co2 sequestration", c, "CO2 sequestration", [f"{node} co2 stored", sb], [1.0], capital_cost=0.0,
                                  lifetime=years, role="PERMANENT_STORAGE"))
        ledger["sequestration_countries"][c] = dict(cap_t_per_year=cap, store=sb, links=len(links), capital_cost_eur_per_t=seq_cost,
                                                     potential_gt=float(registry.loc[f"co2_storage_potential_{c}", "value"]))
    n.meta["research_co2_storage"] = dict(caps_t_per_year=caps, storage_years=years, horizon_fraction=1.0, hook="research_co2_storage_cap",
                                          method="final-snapshot level of each national co2 sequestered Store <= cap x horizon_fraction; charge-only")
    n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {"research_co2_storage_cap"})
    # 3. vents (captured CO2 may return to the capturing country's atmosphere)
    if R.get("vent", True):
        for node in nodes:
            add_link(n, f"{node} co2 vent", country_of(n, node), "co2 vent", [f"{node} co2 stored", atmosphere_bus(country_of(n, node))], [1.0], role="CO2_VENT")
            ledger["vents"] += 1
    # 4. pipelines along the greenfield H2 routes (decision 35; cross-border controlled by research.cross_border.co2)
    on_fixed, sub_fixed = cost(costs, "CO2 pipeline", "fixed"), cost(costs, "CO2 submarine pipeline", "fixed")
    life = cost(costs, "CO2 pipeline", "lifetime")
    h2 = n.links[n.links.carrier == "H2 pipeline"]
    routes = {}
    for name, z in h2.iterrows():
        a, b = z.bus0[:-3], z.bus1[:-3]
        key = tuple(sorted((a, b)))
        u = float(z.underwater_fraction) if "underwater_fraction" in h2 and np.isfinite(z.get("underwater_fraction", np.nan)) else 0.0
        L = float(z.length)
        if key not in routes or L < routes[key]["length"]:
            routes[key] = dict(a=a, b=b, length=L, underwater_fraction=u, h2_routes=routes.get(key, {}).get("h2_routes", 0) + 1)
        else:
            routes[key]["h2_routes"] += 1
    ledger["h2_routes_merged"] = int(sum(r["h2_routes"] for r in routes.values()) - len(routes))
    for key in sorted(routes):
        r = routes[key]; a, b, L, u = r["a"], r["b"], r["length"], r["underwater_fraction"]
        add_link(n, f"CO2 pipeline {a} -> {b}", country_of(n, a), "CO2 pipeline", [f"{a} co2 stored", f"{b} co2 stored"], [1.0], p_min_pu=-1.0,
                 capital_cost=L * ((1 - u) * on_fixed + u * sub_fixed), lifetime=life, length=L, role="TRANSPORT",
                 extra={"underwater_fraction": u})
        ledger["pipelines"] += 1
    # 5. capture technologies at every node
    ef_gas = cost(costs, "gas", "CO2 intensity"); cc = float(cc_fraction)
    cap_fixed = cost(costs, "biomass CHP capture", "fixed"); cap_vom = cost(costs, "biomass CHP capture", "VOM")
    cap_el = cost(costs, "biomass CHP capture", "electricity-input") + cost(costs, "biomass CHP capture", "compression-electricity-input")
    ccgt_eff = cost(costs, "CCGT", "efficiency"); ccgt_fixed = cost(costs, "CCGT", "fixed"); ccgt_vom = cost(costs, "CCGT", "VOM")
    dac_el = cost(costs, "direct air capture", "electricity-input") + cost(costs, "direct air capture", "compression-electricity-input") \
        + cost(costs, "direct air capture", "heat-input") - cost(costs, "direct air capture", "compression-heat-output")  # heat supplied electrically, COP 1
    dac_fixed = cost(costs, "direct air capture", "fixed"); dac_life = cost(costs, "direct air capture", "lifetime")
    cem_fixed = cost(costs, "cement capture", "fixed"); cem_vom = cost(costs, "cement capture", "VOM"); cem_rate = cost(costs, "cement capture", "capture_rate")
    cem_el = cost(costs, "cement capture", "electricity-input") + cost(costs, "cement capture", "compression-electricity-input")
    counts = dict(ccgt_cc=0, dac=0, process=0)
    for node in nodes:
        c = country_of(n, node); atmo = atmosphere_bus(c); co2s = f"{node} co2 stored"; gas = f"{node} gas"
        eff_net = ccgt_eff - cap_el * ef_gas * cc
        add_link(n, f"{node} CCGT CC", c, "CCGT CC", [gas, node, atmo, co2s], [eff_net, ef_gas * (1 - cc), ef_gas * cc],
                 capital_cost=ccgt_fixed * ccgt_eff + cap_fixed * ef_gas * cc, marginal_cost=ccgt_vom * ccgt_eff + cap_vom * ef_gas * cc,
                 lifetime=cost(costs, "CCGT", "lifetime"), extra={"capture_fraction": cc, "capture_cost_row": "biomass CHP capture (generic post-combustion, PyPSA-Eur practice)"})
        counts["ccgt_cc"] += 1
        if R.get("dac", True):
            t_per_mwh = 1.0 / dac_el
            add_link(n, f"{node} DAC", c, "DAC", [node, co2s, atmo], [t_per_mwh, -t_per_mwh], capital_cost=dac_fixed * t_per_mwh, lifetime=dac_life,
                     extra={"electricity_mwh_per_t": dac_el, "heat_supply": R.get("dac_heat_supply", "electricity_cop_1")})
            counts["dac"] += 1
        pb = add_bus(n, f"{node} process emissions", "process emissions", c, node)
        add_link(n, f"{node} process emissions", c, "process emissions", [pb, atmo], [1.0], role="PROCESS_EMISSION_RELEASE")
        add_link(n, f"{node} process emissions CC", c, "process emissions CC", [pb, atmo, co2s, node], [1 - cem_rate, cem_rate, -cem_el * cem_rate],
                 capital_cost=cem_fixed, marginal_cost=cem_vom * cem_rate, lifetime=cost(costs, "cement capture", "lifetime"))
        counts["process"] += 1
    ledger["capture_links"] = counts
    ledger["parameters"] = dict(cc_fraction=cc, dac_electricity_mwh_per_t=dac_el, process_capture_rate=cem_rate, co2_storage_tank_fixed_eur_per_t_a=tank_fixed,
                                sequestration_cost_eur_per_t=seq_cost, pipeline_fixed_onshore=on_fixed, pipeline_fixed_submarine=sub_fixed)
    return ledger


# ----------------------------------------------------------------------------------------------
# S2-3: biomass supply and conversion (decisions 31, 32, 36)
# ----------------------------------------------------------------------------------------------
def add_biomass_layer(n, costs, s2cfg, potentials_csv: Path, nodes, cc_fraction: float):
    R = s2cfg["biomass"]
    df = pd.read_csv(potentials_csv, keep_default_na=False)
    ledger = dict(stores=[], skipped=[], conversion_links=0, by_country_mwh={})
    for c in sorted(COUNTRIES):
        add_bus(n, f"solid biomass {c}", "solid biomass", c, "")
        add_bus(n, f"biogas {c}", "biogas", c, "")
    for r in df.itertuples():
        if r.category in R.get("categories_excluded", []) or r.status in ("DATA_PENDING", "ZERO_BY_DECISION"):
            ledger["skipped"].append(dict(country=r.country, category=r.category, status=r.status))
            continue
        pot = float(r.potential_main_mwh) if r.potential_main_mwh != "" else 0.0
        if pot <= 0:
            continue
        bus = f"biogas {r.country}" if r.feedstock_group == "biogas" else f"solid biomass {r.country}"
        mc = float(r.cost_eur2020_per_mwh) if r.cost_eur2020_per_mwh != "" else 0.0
        name = f"{r.country} biomass {r.category}"
        n.add("Store", name, bus=bus, carrier=n.buses.at[bus, "carrier"], e_nom=pot, e_nom_extendable=False, e_initial=pot, e_cyclic=False, marginal_cost=mc)
        n.stores.loc[name, ["country", "research_role", "s2_category", "s2_cost_tier"]] = [r.country, "FINITE_RESOURCE", r.category, r.cost_tier]
        n.meta.setdefault("store_power_rules", {})[name] = "discharge_only"
        ledger["stores"].append(dict(store=name, country=r.country, category=r.category, group=r.feedstock_group, potential_mwh=pot,
                                     potential_low_mwh=float(r.potential_low_mwh) if r.potential_low_mwh != "" else None,
                                     potential_high_mwh=float(r.potential_high_mwh) if r.potential_high_mwh != "" else None, marginal_cost=mc, cost_tier=r.cost_tier))
        ledger["by_country_mwh"][r.country] = ledger["by_country_mwh"].get(r.country, 0.0) + pot
    n.meta["research_biomass"] = dict(stores={s["store"]: s["potential_mwh"] for s in ledger["stores"]}, cross_border=False, layer=R["potential_layer"])
    # conversion at every node from the national pools
    ef_bio = cost(costs, "solid biomass", "CO2 intensity"); ef_gas = cost(costs, "gas", "CO2 intensity"); ef_oil = cost(costs, "oil", "CO2 intensity"); cc = float(cc_fraction)
    eop_eff = cost(costs, "biomass EOP", "efficiency"); eop_fixed = cost(costs, "biomass EOP", "fixed"); eop_vom = cost(costs, "biomass EOP", "VOM"); eop_life = cost(costs, "biomass EOP", "lifetime")
    cap_fixed = cost(costs, "biomass CHP capture", "fixed"); cap_vom = cost(costs, "biomass CHP capture", "VOM")
    cap_el = cost(costs, "biomass CHP capture", "electricity-input") + cost(costs, "biomass CHP capture", "compression-electricity-input")
    up_fixed = cost(costs, "biogas upgrading", "fixed"); up_vom = cost(costs, "biogas upgrading", "VOM"); up_life = cost(costs, "biogas upgrading", "lifetime")
    btl_eff = cost(costs, "BtL", "efficiency"); btl_fixed = cost(costs, "BtL", "fixed"); btl_vom = cost(costs, "BtL", "VOM"); btl_life = cost(costs, "BtL", "lifetime")
    for node in nodes:
        c = country_of(n, node); atmo = atmosphere_bus(c); bio = f"solid biomass {c}"; bg = f"biogas {c}"; co2s = f"{node} co2 stored"
        add_link(n, f"{node} biomass EOP", c, "biomass EOP", [bio, node], [eop_eff], capital_cost=eop_fixed * eop_eff, marginal_cost=eop_vom * eop_eff, lifetime=eop_life)
        add_link(n, f"{node} biomass EOP CC", c, "biomass EOP CC", [bio, node, atmo, co2s], [eop_eff - cap_el * ef_bio * cc, -ef_bio * cc, ef_bio * cc],
                 capital_cost=eop_fixed * eop_eff + cap_fixed * ef_bio * cc, marginal_cost=eop_vom * eop_eff + cap_vom * ef_bio * cc, lifetime=eop_life,
                 extra={"capture_fraction": cc})
        add_link(n, f"{node} biogas upgrading", c, "biogas upgrading", [bg, f"{node} gas", atmo], [1.0, -ef_gas], capital_cost=up_fixed, marginal_cost=up_vom, lifetime=up_life)
        add_link(n, f"{node} BtL", c, "BtL", [bio, f"{node} oil", atmo], [btl_eff, -ef_oil * btl_eff], capital_cost=btl_fixed, marginal_cost=btl_vom * btl_eff, lifetime=btl_life)
        ledger["conversion_links"] += 4
    ledger["carbon_treatment"] = ("biomass combustion carbon-neutral (no atmosphere port); CC variants book -EF x cc in the atmosphere and +EF x cc in co2 stored; "
                                  "biogas upgrading and BtL credit -EF of the produced fossil-equivalent carrier so its later combustion nets to zero; no biomass-to-hydrogen in S2 (upstream U3 not reproduced)")
    return ledger


# ----------------------------------------------------------------------------------------------
# S2-5: industrial low-temperature heat bus per node
# ----------------------------------------------------------------------------------------------
def add_industrial_heat(n, costs, nodes, cc_fraction: float):
    ef_gas = cost(costs, "gas", "CO2 intensity"); ef_bio = cost(costs, "solid biomass", "CO2 intensity"); cc = float(cc_fraction)
    cap_row = "biomass boiler capture" if "biomass boiler capture" in costs.index and np.isfinite(costs.at["biomass boiler capture", "fixed"]) else "biomass CHP capture"
    cap_fixed = cost(costs, cap_row, "fixed"); cap_el = cost(costs, cap_row, "electricity-input") + cost(costs, cap_row, "compression-electricity-input")
    count = 0
    for node in nodes:
        c = country_of(n, node); hb = add_bus(n, f"{node} industry heat", "industry heat", c, node); atmo = atmosphere_bus(c); bio = f"solid biomass {c}"
        for tech, carrier, ports, effs in [
            ("electric boiler steam", "industry electric boiler", [node, hb], [cost(costs, "electric boiler steam", "efficiency")]),
            ("industrial heat pump high temperature", "industry heat pump", [node, hb], [cost(costs, "industrial heat pump high temperature", "efficiency")]),
            ("gas boiler steam", "industry gas boiler", [f"{node} gas", hb, atmo], [cost(costs, "gas boiler steam", "efficiency"), ef_gas]),
            ("solid biomass boiler steam", "industry biomass boiler", [bio, hb], [cost(costs, "solid biomass boiler steam", "efficiency")])]:
            eff = effs[0]
            add_link(n, f"{node} {carrier}", c, carrier, ports, effs, capital_cost=cost(costs, tech, "fixed") * eff, marginal_cost=cost(costs, tech, "VOM") * eff,
                     lifetime=cost(costs, tech, "lifetime"))
            count += 1
        eff = cost(costs, "solid biomass boiler steam", "efficiency")
        add_link(n, f"{node} industry biomass boiler CC", c, "industry biomass boiler CC", [bio, hb, atmo, f"{node} co2 stored", node],
                 [eff, -ef_bio * cc, ef_bio * cc, -cap_el * ef_bio * cc], capital_cost=cost(costs, "solid biomass boiler steam", "fixed") * eff + cap_fixed * ef_bio * cc,
                 marginal_cost=cost(costs, "solid biomass boiler steam", "VOM") * eff, lifetime=cost(costs, "solid biomass boiler steam", "lifetime"), extra={"capture_cost_row": cap_row})
        count += 1
    return dict(buses=len(nodes), supply_links=count, options=["electric boiler", "high-temperature heat pump", "gas boiler", "biomass boiler", "biomass boiler CC"])


# ----------------------------------------------------------------------------------------------
# S2-4: demand layer from the D1 table
# ----------------------------------------------------------------------------------------------
def allocation_node_shares(n, repo: Path, allocation_dir: Path):
    """(country, account) -> {node: share} from the Assembly-V1 allocation arrays; plus Astar electricity shares."""
    am = jload(allocation_dir / "allocation_manifest.json")
    z = np.load(allocation_dir / am["arrays_file"], allow_pickle=False)
    shares = {}
    for ar in am["records"]:
        parts = ar["InputID"].split(":"); country, account = parts[0], parts[3]
        arr = np.asarray(z[ar["ArrayKey"]], dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        tot = arr.sum()
        if tot <= 0:
            continue
        shares[(country, account)] = {node: float(arr[:, j].sum() / tot) for j, node in enumerate(ar["Nodes"])}
    astar = {}
    w = n.snapshot_weightings.generators
    pset = n.get_switchable_as_dense("Load", "p_set")
    for name, z0 in n.loads[n.loads.account == "Astar"].iterrows():
        e = float((pset[name] * w).sum()); astar.setdefault(z0.country, {})[z0.bus] = astar.get(z0.country, {}).get(z0.bus, 0.0) + e
    for c in astar:
        tot = sum(astar[c].values()); astar[c] = {k: v / tot for k, v in astar[c].items()}
    return shares, astar


def _shares_for(shares, astar, country, sector):
    acc = ACCOUNT_FOR_SHARES.get(sector, "IndustryFinalEnergy")
    s = shares.get((country, acc)) or shares.get((country, "IndustryFinalEnergy")) or astar[country]
    return s, (acc if (country, acc) in shares else ("IndustryFinalEnergy" if (country, "IndustryFinalEnergy") in shares else "Astar"))


def add_demand_layer(n, costs, cfg, repo: Path, registry: pd.DataFrame, demand_csv: Path, boundary_csv: Path, allocation_dir: Path, nodes, cc_fraction: float):
    S2 = cfg["research"]["s2"]; D = S2["demand"]; I = S2["industry"]
    dem = pd.read_csv(demand_csv, keep_default_na=False)
    bound = pd.read_csv(boundary_csv).set_index("country")
    shares, astar_shares = allocation_node_shares(n, repo, allocation_dir)
    reg = registry
    rv = lambda pid: float(reg.loc[pid, "value"])
    ef = {k: cost(costs, v, "CO2 intensity") for k, v in FUEL_EF_KEYS.items()}; ef["biomass"] = 0.0; ef["electricity"] = 0.0
    ev_share, fc_share, ice_share = rv("share_land_transport_electric_share_2050"), rv("share_land_transport_fuel_cell_share_2050"), rv("share_land_transport_ice_share_2050")
    oil_to_el = rv("share_transport_ice_efficiency") / rv("share_transport_electric_efficiency")      # MWh_el per MWh_oil (PyPSA-Eur efficiencies per 100 km)
    oil_to_h2 = rv("share_transport_ice_efficiency") / rv("share_transport_fuel_cell_efficiency")
    bev_eff, bev_avail = rv("share_bev_charge_efficiency"), rv("share_bev_avail_mean")
    ag_el_share, ag_oil_share = rv("share_agriculture_machinery_electric_share"), rv("share_agriculture_machinery_oil_share")
    ag_gain = rv("share_agriculture_machinery_fuel_efficiency") / rv("share_agriculture_machinery_electric_efficiency")
    hvc_primary = rv("share_HVC_primary_fraction_2050"); eol_release = float(I["feedstock_end_of_life_release_fraction"])
    s_lt, boiler_eff = float(I["low_temperature_heat_share_of_fuels"]), float(I["existing_boiler_efficiency"])
    loads, deductions, deferred = [], [], []
    n.meta.setdefault("demand_owners", {}); n.meta.setdefault("demand_identity", {})

    def register(name, country, sector, account, carrier, source_row, annual_mwh, bus):
        if name in n.meta["demand_owners"]:
            raise ValueError("Demand bound twice: " + name)
        owner = f"S2:{country}:{sector}:{account}:{carrier}"
        for col, val in [("sector", sector), ("account", account), ("source_account_id", source_row), ("country", country), ("demand_owner_kind", S2_OWNER_KIND)]:
            n.loads.loc[name, col] = val
        n.meta["demand_owners"][name] = owner
        n.meta["demand_identity"][name] = dict(carrier=carrier, sector=sector, account=account, country=country, owner_kind=S2_OWNER_KIND)
        loads.append(dict(load=name, country=country, sector=sector, account=account, carrier=carrier, source_row=source_row, annual_mwh=annual_mwh, bus=bus))

    def fuel_bus(node, country, fuel):
        return f"solid biomass {country}" if fuel == "biomass" else f"{node} {'oil' if fuel == 'unclassified_fuel' else fuel}"

    def meter_load(node, country, sector, fuel, annual_mwh, source_row, account):
        fb = add_bus(n, f"{node} {sector} {fuel} final", f"{fuel} final energy", country, node)
        link = f"{node} {sector} {fuel} meter"
        if link not in n.links.index:
            ports, effs = [fuel_bus(node, country, fuel), fb], [1.0]
            if ef.get(fuel, 0.0) > 0:
                ports.append(atmosphere_bus(country)); effs.append(ef[fuel])
            add_link(n, link, country, f"{fuel} final-energy accounting", ports, effs, role="FUEL_CARBON_METER")
        name = f"{node} {sector} {fuel} demand"
        n.add("Load", name, bus=fb, carrier=f"{fuel} final energy", p_set=annual_mwh / HOURS)
        register(name, country, sector, account, fuel, source_row, annual_mwh, fb)

    def plain_load(node, country, sector, account, carrier, bus, annual_mwh, source_row, name):
        n.add("Load", name, bus=bus, carrier=carrier, p_set=annual_mwh / HOURS)
        register(name, country, sector, account, carrier, source_row, annual_mwh, bus)

    tf = dem[dem.value_2050_mwh != ""].copy(); tf["v"] = tf.value_2050_mwh.astype(float)
    for c in sorted(COUNTRIES):
        d = tf[tf.country == c]
        cnodes = [x for x in nodes if country_of(n, x) == c]
        # ---- transport ------------------------------------------------------------------------------
        land = d[(d.sector == "Transport") & d.account.isin(LAND_TRANSPORT_ACCOUNTS) & (d.carrier != "electricity")]
        E_land = float(land.v.sum()); src_land = ";".join(sorted(set(land.account)))
        sh, acc_used = _shares_for(shares, astar_shares, c, "Transport")
        for node, s in sh.items():
            if s <= 0:
                continue
            if ev_share > 0:
                ensure_carrier(n, "Li ion"); evb = add_bus(n, f"{node} EV battery", "Li ion", c, node)
                if f"{node} BEV charger" not in n.links.index:
                    add_link(n, f"{node} BEV charger", c, "BEV charger", [node, evb], [bev_eff], role="EV_CHARGER", extra={"p_max_pu": bev_avail})
                    n.links.loc[f"{node} BEV charger", "p_max_pu"] = bev_avail
                plain_load(node, c, "Transport", "LandTransportEV", "land transport EV", evb, E_land * s * ev_share * oil_to_el, src_land, f"{node} land transport EV")
            if fc_share > 0:
                plain_load(node, c, "Transport", "LandTransportFCEV", "land transport fuel cell", f"{node} H2", E_land * s * fc_share * oil_to_h2, src_land, f"{node} land transport fuel cell")
            if ice_share > 0:
                meter_load(node, c, "transport ICE", "oil", E_land * s * ice_share, src_land, "LandTransportICE")
        for account, sector, switch in [("DomesticAviationFuel", "aviation domestic", True), ("InternationalAviationBunker", "aviation international", bool(D["international_bunkers"])),
                                        ("RailNonElectric", "rail", True)]:
            rows = d[d.account == account]
            if not len(rows):
                continue
            if not switch:
                deferred.append(dict(country=c, account=account, carrier="oil", annual_mwh=float(rows.v.sum()), reason="switch research.s2.demand.international_bunkers=false"))
                continue
            sh2, _ = _shares_for(shares, astar_shares, c, "AviationInternational" if account == "InternationalAviationBunker" else "Transport")
            for carrier, v in rows.groupby("carrier").v.sum().items():
                if v <= 0:
                    continue
                fuel = "oil" if carrier in ("oil", "unclassified_fuel") else carrier
                for node, s in sh2.items():
                    if s > 0:
                        meter_load(node, c, sector, fuel, v * s, f"{c}:{account}:{carrier}", account)
        for account in ["DomesticShippingFuel", "InternationalShippingBunker"]:
            rows = d[d.account == account]
            if len(rows):
                deferred.append(dict(country=c, account=account, carrier="oil", annual_mwh=float(rows.v.sum()), reason="shipping deferred to S3 (methanol/ammonia)"))
        # ---- industry ---------------------------------------------------------------------------------
        ind = d[(d.sector == "Industry") & (d.carrier != "electricity")]
        sh, _ = _shares_for(shares, astar_shares, c, "Industry")
        heat_total = float(ind.v.sum()) * s_lt * boiler_eff
        for node, s in sh.items():
            if s <= 0:
                continue
            if heat_total > 0:
                plain_load(node, c, "Industry", "IndustryLowTemperatureHeat", "industry heat", f"{node} industry heat", heat_total * s, "IndustryFinalEnergy x low_temperature_heat_share x boiler_eff", f"{node} industry heat demand")
            for carrier, v in ind.groupby("carrier").v.sum().items():
                if v * (1 - s_lt) * s > 0:
                    meter_load(node, c, "industry", carrier, v * (1 - s_lt) * s, f"{c}:IndustryFinalEnergy:{carrier}", "IndustryFinalEnergy")
            # industrial biomass with capture (BECCS in industry): alternative route into the same biomass final bus
            fb = f"{node} industry biomass final"
            if fb in n.buses.index and f"{node} industry biomass CC" not in n.links.index:
                ef_bio = cost(costs, "solid biomass", "CO2 intensity"); cc = float(cc_fraction)
                cap_row = "biomass boiler capture" if "biomass boiler capture" in costs.index and np.isfinite(costs.at["biomass boiler capture", "fixed"]) else "biomass CHP capture"
                cap_el = cost(costs, cap_row, "electricity-input") + cost(costs, cap_row, "compression-electricity-input")
                add_link(n, f"{node} industry biomass CC", c, "industry biomass CC", [f"solid biomass {c}", fb, atmosphere_bus(c), f"{node} co2 stored", node],
                         [1.0, -ef_bio * cc, ef_bio * cc, -cap_el * ef_bio * cc], capital_cost=cost(costs, cap_row, "fixed") * ef_bio * cc,
                         marginal_cost=cost(costs, cap_row, "VOM") * ef_bio * cc, lifetime=cost(costs, cap_row, "lifetime"), extra={"capture_fraction": cc})
        # ---- buildings (residential + commercial): cooking and hot water -----------------------------
        for sector in ["Residential", "Commercial"]:
            b = d[(d.sector == sector) & (d.carrier != "electricity")]
            sh, _ = _shares_for(shares, astar_shares, c, sector)
            eta_basic = COOKSTOVE_BASIC_FUELWOOD.get(c, COOKSTOVE_BASIC_DEFAULT)
            for node, s in sh.items():
                if s <= 0:
                    continue
                for carrier, v in b.groupby("carrier").v.sum().items():
                    if v * s <= 0:
                        continue
                    if carrier == "biomass" and D.get("clean_cooking", True):
                        useful = v * s * eta_basic
                        cb = add_bus(n, f"{node} clean cooking", "clean cooking useful", c, node)
                        if f"{node} cooking electric" not in n.links.index:
                            add_link(n, f"{node} cooking electric", c, "cooking electric", [node, cb], [COOKSTOVE_MODERN])
                            add_link(n, f"{node} cooking gas", c, "cooking gas", [f"{node} gas", cb, atmosphere_bus(c)], [COOKSTOVE_MODERN, ef["gas"]])
                            add_link(n, f"{node} cooking LPG", c, "cooking LPG", [f"{node} oil", cb, atmosphere_bus(c)], [COOKSTOVE_MODERN, ef["oil"]])
                        name = f"{node} {sector} clean cooking demand"
                        if name in n.loads.index:
                            n.loads.at[name, "p_set"] += useful / HOURS
                        else:
                            plain_load(node, c, sector, f"{sector}Fuel biomass -> clean cooking (decision 23)", "clean cooking useful", cb, useful, f"{c}:{sector}Fuel:biomass x eta_basic {eta_basic}", name)
                    else:
                        meter_load(node, c, sector.lower(), carrier, v * s, f"{c}:{sector}Fuel:{carrier}", f"{sector}Fuel")
        # ---- agriculture and others -------------------------------------------------------------------
        a = d[(d.sector == "AgricultureOthers") & (d.carrier != "electricity")]
        sh, _ = _shares_for(shares, astar_shares, c, "AgricultureOthers")
        for node, s in sh.items():
            if s <= 0:
                continue
            for carrier, v in a.groupby("carrier").v.sum().items():
                if v * s <= 0:
                    continue
                if carrier in ("oil", "unclassified_fuel"):
                    if ag_el_share > 0:
                        plain_load(node, c, "AgricultureOthers", "AgricultureMachineryElectric", "agriculture machinery electric", node, v * s * ag_el_share / ag_gain, f"{c}:AgricultureFinalEnergy:oil x electric share", f"{node} agriculture machinery electric")
                    if ag_oil_share > 0:
                        meter_load(node, c, "agriculture", "oil", v * s * ag_oil_share, f"{c}:AgricultureFinalEnergy:{carrier}", "AgricultureFinalEnergy")
                else:
                    meter_load(node, c, "agriculture", carrier, v * s, f"{c}:AgricultureFinalEnergy:{carrier}", "AgricultureFinalEnergy")
        # ---- non-energy use: feedstock carbon (PyPSA-Eur structure; method question) -----------------------
        ne = d[d.sector == "NonEnergyUse"]
        feed_pot = float(bound.at[c, "feedstock_carbon_potential_tco2"]) if c in bound.index else 0.0
        f_process = min(1.0, float(bound.at[c, "edgar_2B_chemicals_tco2"]) / feed_pot) if feed_pot > 0 else 0.0
        sh, _ = _shares_for(shares, astar_shares, c, "NonEnergyUse")
        for carrier, v in ne.groupby("carrier").v.sum().items():
            if v <= 0:
                continue
            scale = hvc_primary if (carrier == "oil" and I.get("hvc_recycling_applies_to_naphtha", True)) else 1.0
            for node, s in sh.items():
                if s <= 0:
                    continue
                fb = add_bus(n, f"{node} feedstock {carrier} final", f"{carrier} feedstock", c, node)
                link = f"{node} feedstock {carrier}"
                if link not in n.links.index:
                    add_link(n, link, c, f"{carrier} feedstock", [f"{node} {carrier}", fb, f"{node} process emissions", atmosphere_bus(c)],
                             [1.0, f_process * ef[carrier], (1 - f_process) * eol_release * ef[carrier]], role="FEEDSTOCK_CARBON",
                             extra={"process_share": f_process, "end_of_life_release": eol_release})
                plain_load(node, c, "NonEnergyUse", f"NonEnergy:{carrier}", f"{carrier} feedstock", fb, v * s * scale, f"{c}:NonEnergy:{carrier} x HVC primary {scale if carrier == 'oil' else 1.0}", f"{node} feedstock {carrier} demand")
        # ---- process emissions (EDGAR 2.A + 2.C, 2050) ------------------------------------------------------
        proc = sum(float(reg.loc[f"process_emissions_{g}_2050_{c}", "value"]) for g in S2["co2"]["process_emissions_scope"] if reg.loc[f"process_emissions_{g}_2050_{c}", "status"] in ("REGISTERED", "SOURCE_ZERO"))
        sh, _ = _shares_for(shares, astar_shares, c, "ProcessEmissions")
        ensure_carrier(n, "process emissions")
        for node, s in sh.items():
            if proc * s <= 0:
                continue
            g = f"{node} process emissions source"
            n.add("Generator", g, bus=f"{node} process emissions", carrier="process emissions", p_nom=proc * s / HOURS, p_nom_extendable=False, p_min_pu=1.0, p_max_pu=1.0, marginal_cost=0.0, capital_cost=0.0)
            n.generators.loc[g, ["country", "research_role", "asset_role"]] = [c, "PROCESS_EMISSION_SOURCE", "exogenous_process_emission"]
            loads.append(dict(load=g, country=c, sector="ProcessEmissions", account="EDGAR 2.A+2.C x industry multiplier", carrier="process emissions", source_row=f"process_emissions_*_2050_{c}", annual_mwh=proc * s, bus=f"{node} process emissions"))
        # ---- Astar deduction: transport electricity already explicit ------------------------------------------
        te = float(d[(d.sector == "Transport") & (d.carrier == "electricity")].v.sum())
        astar_c = [l for l in n.loads.index if n.loads.at[l, "account"] == "Astar" and n.loads.at[l, "country"] == c]
        pset = n.loads_t.p_set
        w = n.snapshot_weightings.generators
        astar_total = float(sum((pset[l] * w).sum() for l in astar_c if l in pset))
        if te > 0 and astar_total > 0:
            factor = 1.0 - te / astar_total
            if factor < 0:
                raise ValueError("Transport electricity exceeds Astar for " + c)
            for l in astar_c:
                if l in pset:
                    n.loads_t.p_set[l] = pset[l] * factor
            deductions.append(dict(country=c, deducted="transport electricity (rail/road, embedded in Astar)", deducted_mwh=te, astar_before_mwh=astar_total, astar_after_mwh=astar_total * factor, factor=factor,
                                   added_explicit=dict(ev_mwh=E_land * ev_share * oil_to_el, fcev_h2_mwh=E_land * fc_share * oil_to_h2)))
        else:
            deductions.append(dict(country=c, deducted="none", deducted_mwh=te, astar_before_mwh=astar_total, astar_after_mwh=astar_total, factor=1.0,
                                   added_explicit=dict(ev_mwh=E_land * ev_share * oil_to_el, fcev_h2_mwh=E_land * fc_share * oil_to_h2)))
    ledger = dict(loads=loads, deductions=deductions, deferred=deferred, parameters=dict(ev_share=ev_share, fcev_share=fc_share, ice_share=ice_share, oil_to_electricity=oil_to_el, oil_to_hydrogen=oil_to_h2,
                  bev_charge_efficiency=bev_eff, bev_availability=bev_avail, agriculture_electric_share=ag_el_share, agriculture_efficiency_gain=ag_gain, hvc_primary_fraction=hvc_primary,
                  feedstock_end_of_life_release=eol_release, industry_low_temperature_heat_share=s_lt, existing_boiler_efficiency=boiler_eff, cookstove_basic=COOKSTOVE_BASIC_FUELWOOD,
                  cookstove_basic_default=COOKSTOVE_BASIC_DEFAULT, cookstove_modern=COOKSTOVE_MODERN), node_share_source=D["node_allocation"])
    return ledger


# ----------------------------------------------------------------------------------------------
# gap diagnostic (decisions 49, 53) and hooks
# ----------------------------------------------------------------------------------------------
def add_gap_slack(n, gcfg, nodes):
    ensure_carrier(n, "gap slack electricity")
    for node in nodes:
        name = f"{node} gap slack electricity"
        n.add("Generator", name, bus=node, carrier="gap slack electricity", p_nom_extendable=True, p_nom=0.0, capital_cost=0.0, marginal_cost=float(gcfg["penalty_eur_per_mwh"]))
        n.generators.loc[name, ["country", "research_role", "asset_role"]] = [country_of(n, node), "GAP_DIAGNOSTIC_SLACK", "diagnostic_slack"]
    # Biomass slack (added after gap run 1): the fixed biomass final-energy demand of SG and VN exceeds the domestic solid-biomass
    # potential, so the diagnostic needs a penalised external biomass source per country to become solvable (decision 36 unchanged in scenarios).
    ensure_carrier(n, "gap slack biomass")
    for c in sorted(COUNTRIES):
        bus = f"solid biomass {c}"
        if bus in n.buses.index:
            name = f"{c} gap slack biomass"
            n.add("Generator", name, bus=bus, carrier="gap slack biomass", p_nom_extendable=True, p_nom=0.0, capital_cost=0.0, marginal_cost=float(gcfg["penalty_eur_per_mwh"]))
            n.generators.loc[name, ["country", "research_role", "asset_role"]] = [c, "GAP_DIAGNOSTIC_SLACK", "diagnostic_slack"]
    hooks = set(n.meta.get("required_constraint_hooks", [])) - {"research_country_net_zero"} | {"research_gap_diagnostic"}
    n.meta["required_constraint_hooks"] = sorted(hooks)
    n.meta["gap_diagnostic"] = dict(enabled=True, penalty_eur_per_mwh=float(gcfg["penalty_eur_per_mwh"]), penalty_eur_per_tco2=float(gcfg["penalty_eur_per_tco2"]),
                                    slacks=["electricity", "co2", "biomass"], label="GAP_DIAGNOSTIC_NOT_FOR_INTERCONNECTION_VALUE")
    n.meta["artifact_role"] = "GAP_DIAGNOSTIC_UNSOLVED"


def install_co2_storage_cap(n):
    if getattr(n, "_research_co2_cap_model", None) is n.model:
        raise ValueError("CO2 storage cap hook already installed")
    cfg = n.meta["research_co2_storage"]; m = n.model; e = m["Store-e"]; last = n.snapshots[-1]; frac = float(cfg.get("horizon_fraction", 1.0))
    for c, cap in cfg["caps_t_per_year"].items():
        sb = f"co2 sequestered {c}"
        if sb in n.stores.index:
            m.add_constraints(e.sel(snapshot=last, Store=sb) <= float(cap) * frac, name="research_co2_storage_cap-" + c)
    n._research_co2_cap_model = m


def install_gap_diagnostic(n):
    if getattr(n, "_research_gap_model", None) is n.model:
        raise ValueError("Gap diagnostic hook already installed")
    cfg = n.meta["research_carbon"]; g = n.meta["gap_diagnostic"]; m = n.model; e = m["Store-e"]; last = n.snapshots[-1]
    slack = m.add_variables(lower=0.0, coords=[pd.Index(sorted(COUNTRIES), name="country")], name="Research_gap_co2_slack")
    for ct in sorted(COUNTRIES):
        m.add_constraints(e.sel(snapshot=last, Store=atmosphere_bus(ct)) - slack.sel(country=ct) <= float(cfg["country_cap_tco2"][ct]), name="research_gap_co2_limit-" + ct)
    m.objective += (slack * float(g["penalty_eur_per_tco2"])).sum()
    n._research_gap_model = m
