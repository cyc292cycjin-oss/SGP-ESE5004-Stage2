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
# S4J-1 (decision 104): demand-table electricity sectors that no other demand of the model represents. Residential / commercial electricity (incl. building
# cooling, not modelled separately) and agriculture-and-others electricity have no explicit load; the transport electricity row (rail, existing electric road)
# is not modelled either (the explicit EV / FCEV loads convert the non-electric land-transport fuel rows only). Industry electricity is explicit in the route
# mode (pypsa_eur_2050) and joins the base load only in the bas_fixed comparison mode.
TABLE_BASE_SECTORS = ("Residential", "Commercial", "AgricultureOthers", "Transport")


def nonindustrial_electricity_mode(cfg) -> str:
    """research.demand.nonindustrial_electricity: table_sectors (main, decision 104) | astar_residual (former method; default when absent)."""
    v = str((cfg["research"].get("demand") or {}).get("nonindustrial_electricity", "astar_residual")).lower()
    if v not in ("table_sectors", "astar_residual"):
        raise ValueError("Unknown research.demand.nonindustrial_electricity " + v)
    return v
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

# ----------------------------------------------------------------------------------------------
# R5 (decision 59): pipeline candidate topology = electricity network connections (PyPSA-Eur create_network_topology)
# ----------------------------------------------------------------------------------------------
def _haversine_km(x0, y0, x1, y1):
    r = 6371.0088
    p0, p1 = np.radians(y0), np.radians(y1); dphi = p1 - p0; dl = np.radians(x1 - x0)
    a = np.sin(dphi / 2) ** 2 + np.cos(p0) * np.cos(p1) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def pipeline_candidates(n, nodes, corridors, dc_map, length_factor: float):
    """One candidate per connected node pair of the electricity network (AC lines + DC links, incl. the 24 cross-border
    corridors), following PyPSA-Eur v2025.07.0 prepare_sector_network.create_network_topology (lines 368-420): candidates
    from lines and DC links, mapped to locations, ordered pairs, one row per pair. Deviations: length = great-circle
    distance x length_factor (config lines 325/341) instead of the grid length; underwater fraction from the corridor
    table subsea_share for cross-border pairs (domestic pairs 0: no data)."""
    node_set = set(nodes)
    def loc(b):
        if b in node_set:
            return b
        if b in dc_map:
            return dc_map[b]
        return None
    cand = []
    for name, z in n.lines.iterrows():
        cand.append((loc(z.bus0), loc(z.bus1), "line", name))
    for name, z in n.links[n.links.carrier == "DC"].iterrows():
        cand.append((loc(z.bus0), loc(z.bus1), "DC link", name))
    xy = n.buses[["x", "y"]]
    sub = {}
    for _, r in corridors.iterrows():   # corridor endpoints may be DC converter buses -> same location mapping as the candidates
        key = tuple(sorted((loc(str(r["from"])) or str(r["from"]), loc(str(r["to"])) or str(r["to"]))))
        sub[key] = max(sub.get(key, 0.0), float(r.get("subsea_share", 0.0) or 0.0))
    rows = {}
    for a, b, kind, name in cand:
        if a is None or b is None or a == b:
            continue
        key = tuple(sorted((a, b)))
        if key not in rows:
            L = float(_haversine_km(xy.at[key[0], "x"], xy.at[key[0], "y"], xy.at[key[1], "x"], xy.at[key[1], "y"])) * float(length_factor)
            rows[key] = dict(a=key[0], b=key[1], length_km=L, underwater_fraction=sub.get(key, 0.0), country_a=country_of(n, key[0]), country_b=country_of(n, key[1]),
                             cross_border=country_of(n, key[0]) != country_of(n, key[1]), sources=[], grid_elements=0)
        rows[key]["sources"].append(kind); rows[key]["grid_elements"] += 1
    df = pd.DataFrame(sorted(rows.values(), key=lambda r: (r["a"], r["b"])))
    df["sources"] = df.sources.map(lambda s: ";".join(sorted(set(s))))
    corridor_pairs = {tuple(sorted((loc(str(r["from"])) or str(r["from"]), loc(str(r["to"])) or str(r["to"])))) for _, r in corridors.iterrows()}
    missing = sorted(k for k in corridor_pairs if k not in rows)
    if missing:
        raise ValueError("Corridor pairs absent from the electricity topology: " + str(missing[:5]))
    return df


def replace_h2_pipelines(n, costs, cand: pd.DataFrame):
    """Drop the upstream greenfield H2 pipelines and add one candidate per electricity connection (R5)."""
    old = n.links.index[n.links.carrier == "H2 pipeline"]
    removed = int(len(old))
    for name in old:
        n.remove("Link", name)
    on_fixed, sub_fixed = cost(costs, "H2 (g) pipeline", "fixed"), cost(costs, "H2 (g) submarine pipeline", "fixed")
    life = cost(costs, "H2 (g) pipeline", "lifetime")
    added = 0
    for _, r in cand.iterrows():
        a, b, L, u = r.a, r.b, float(r.length_km), float(r.underwater_fraction)
        if f"{a} H2" not in n.buses.index or f"{b} H2" not in n.buses.index:
            raise ValueError("H2 bus missing for pipeline candidate " + a + " / " + b)
        add_link(n, f"H2 pipeline {a} -> {b}", country_of(n, a), "H2 pipeline", [f"{a} H2", f"{b} H2"], [1.0], p_min_pu=-1.0,
                 capital_cost=L * ((1 - u) * on_fixed + u * sub_fixed), lifetime=life, length=L, role="TRANSPORT", extra={"underwater_fraction": u})
        added += 1
    return dict(removed_upstream=removed, added=added, cost_rows=dict(onshore="H2 (g) pipeline", submarine="H2 (g) submarine pipeline", fixed_onshore=on_fixed, fixed_submarine=sub_fixed))


def add_co2_layer(n, costs, s2cfg, registry: pd.DataFrame, nodes, cc_fraction: float, candidates: pd.DataFrame | None = None):
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
    # 4. pipelines (decision 35; cross-border controlled by research.cross_border.co2). R5: one candidate per electricity
    #    connection (pipeline_candidates); the former H2-route dedup/shortest-path method is kept only as a fallback.
    on_fixed, sub_fixed = cost(costs, "CO2 pipeline", "fixed"), cost(costs, "CO2 submarine pipeline", "fixed")
    life = cost(costs, "CO2 pipeline", "lifetime")
    if candidates is not None:
        ledger["topology"] = "electricity_network_topology (R5)"
        for _, r in candidates.iterrows():
            a, b, L, u = r.a, r.b, float(r.length_km), float(r.underwater_fraction)
            add_link(n, f"CO2 pipeline {a} -> {b}", country_of(n, a), "CO2 pipeline", [f"{a} co2 stored", f"{b} co2 stored"], [1.0], p_min_pu=-1.0,
                     capital_cost=L * ((1 - u) * on_fixed + u * sub_fixed), lifetime=life, length=L, role="TRANSPORT", extra={"underwater_fraction": u})
            ledger["pipelines"] += 1
        ledger["cross_border_candidates"] = int(candidates.cross_border.sum())
    else:
        ledger["topology"] = "h2_pipeline_routes (S2 fallback)"
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
    # R6 (decision 60): DAC inputs per technology-data v0.15.0 (sources/costs_2050_v0.15.0.csv lines 938-942: compression-electricity-input 0.15,
    # compression-heat-output 0.2, electricity-input 0.4, heat-input 1.6 MWh/tCO2) combined as in PyPSA-Eur v2025.07.0 prepare_sector_network.add_dac
    # (lines 1198-1225): electricity = electricity-input + compression-electricity-input; heat = heat-input - compression-heat-output.
    dac_el_only = cost(costs, "direct air capture", "electricity-input") + cost(costs, "direct air capture", "compression-electricity-input")
    dac_heat = cost(costs, "direct air capture", "heat-input") - cost(costs, "direct air capture", "compression-heat-output")
    dac_heat_mode = str(R.get("dac_heat_mode", "electric_cop1"))
    if dac_heat_mode not in ("industry_heat_bus", "electric_cop1"):
        raise ValueError("Unknown research.s2.co2.dac_heat_mode " + dac_heat_mode)
    dac_el = dac_el_only + (dac_heat if dac_heat_mode == "electric_cop1" else 0.0)   # electric_cop1: heat supplied electrically at COP 1 (S2 treatment, now sensitivity)
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
            t_per_mwh = 1.0 / dac_el   # t CO2 captured per MWh of electricity input
            if dac_heat_mode == "industry_heat_bus":
                hb = add_bus(n, f"{node} industry heat", "industry heat", c, node)   # served by the industrial heat options (add_industrial_heat): heat pump, electric/gas/biomass boiler
                add_link(n, f"{node} DAC", c, "DAC", [node, co2s, atmo, hb], [t_per_mwh, -t_per_mwh, -dac_heat * t_per_mwh], capital_cost=dac_fixed * t_per_mwh, lifetime=dac_life,
                         extra={"electricity_mwh_per_t": dac_el_only, "heat_mwh_per_t": dac_heat, "heat_supply": "industry heat bus (R6, decision 60)"})
            else:
                add_link(n, f"{node} DAC", c, "DAC", [node, co2s, atmo], [t_per_mwh, -t_per_mwh], capital_cost=dac_fixed * t_per_mwh, lifetime=dac_life,
                         extra={"electricity_mwh_per_t": dac_el, "heat_mwh_per_t": dac_heat, "heat_supply": "electricity COP 1 (sensitivity)"})
            counts["dac"] += 1
        pb = add_bus(n, f"{node} process emissions", "process emissions", c, node)
        add_link(n, f"{node} process emissions", c, "process emissions", [pb, atmo], [1.0], role="PROCESS_EMISSION_RELEASE")
        add_link(n, f"{node} process emissions CC", c, "process emissions CC", [pb, atmo, co2s, node], [1 - cem_rate, cem_rate, -cem_el * cem_rate],
                 capital_cost=cem_fixed, marginal_cost=cem_vom * cem_rate, lifetime=cost(costs, "cement capture", "lifetime"))
        counts["process"] += 1
    ledger["capture_links"] = counts
    ledger["parameters"] = dict(cc_fraction=cc, dac_electricity_mwh_per_t=dac_el, dac_electricity_only_mwh_per_t=dac_el_only, dac_heat_mwh_per_t=dac_heat, dac_heat_mode=dac_heat_mode,
                                process_capture_rate=cem_rate, co2_storage_tank_fixed_eur_per_t_a=tank_fixed,
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
        # S4C-0 (decision 86 a): BtL capital cost x efficiency per MW biomass input as PyPSA-Eur v2025.07.0 prepare_sector_network.py lines 4230-4231
        # (former model: BtL fixed per MW biomass, 2.2 x higher)
        add_link(n, f"{node} BtL", c, "BtL", [bio, f"{node} oil", atmo], [btl_eff, -ef_oil * btl_eff], capital_cost=btl_fixed * btl_eff, marginal_cost=btl_vom * btl_eff, lifetime=btl_life)
        ledger["conversion_links"] += 4
    ledger["btl_capital_cost"] = dict(eur_per_mw_biomass_a=btl_fixed * btl_eff, rule="BtL fixed x BtL efficiency (S4C-0, decision 86 a)",
                                      code_ref="PyPSA-Eur v2025.07.0 scripts/prepare_sector_network.py lines 4230-4231", former_eur_per_mw_biomass_a=btl_fixed)
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


def demand_table_key(cfg):
    """Country allocation (decision 57) plus the growth method suffix (S3B R1, decision 66): ratio = main tables, level = *_level tables."""
    D = cfg["research"]["demand"]; key = str(D.get("country_allocation", "aeo8_ats_relative")); gm = str(D.get("growth_method", "ratio"))
    if gm not in ("ratio", "level"):
        raise ValueError("Unknown research.demand.growth_method " + gm)
    return key + ("_level" if gm == "level" else "")


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
    # R1 (decision 55): industrial carrier structure. pypsa_eur_2050 = 2050 process routes (scripts_project/s2b_industry.py);
    # bas_fixed = AEO8 BAS 2019 carrier shares x multiplier with the former 20 % low-temperature-heat assumption (comparison switch).
    carrier_mode = str(I.get("carrier_mode", "bas_fixed")); alloc_mode = demand_table_key(cfg)
    ne_mode = nonindustrial_electricity_mode(cfg)   # S4J-1 (decision 104): Astar base-load total
    if carrier_mode not in ("pypsa_eur_2050", "bas_fixed"):
        raise ValueError("Unknown research.s2.industry.carrier_mode " + carrier_mode)
    # S3-0 (decision 61): ratio source. jrc_idees_2021 = PyPSA-Eur v2025.07.0 ratios reproduced from JRC-IDEES-2021 for all sub-sectors (s3_0_industry.py, main);
    # technology_data_v015 = S2B steel/cement substitutes (sensitivity tables *_TD_SENSITIVITY.csv).
    ratio_source = str(I.get("ratio_source", "jrc_idees_2021"))
    if ratio_source not in ("jrc_idees_2021", "technology_data_v015"):
        raise ValueError("Unknown research.s2.industry.ratio_source " + ratio_source)
    ind_path = repo / (I["pypsa_eur_tables"] if ratio_source == "jrc_idees_2021" else I["technology_data_sensitivity_tables"])[alloc_mode]
    # S3B R2 (decision 67): other bucket. pypsa_eur_2050 = 'Other industrial sectors' 2050 ratios (main); idees_today = JRC-IDEES-2021 EU27 2019 carrier structure
    # of that sector without process switch (sensitivity tables *_OTHER_IDEES_TODAY.csv written by s3_0_industry.py next to the main tables).
    # S4B-0 (S3B section 8 item 6): asean_own_2019 = the UNSD 2019 carrier composition of the ASEAN country's own other bucket, no conversion (tables
    # *_OTHER_ASEAN_OWN_2019.csv; implemented only, not run in the formal trial).
    other_bucket = str(((cfg["research"].get("s3") or {}).get("industry") or {}).get("other_bucket", "pypsa_eur_2050"))
    if other_bucket not in ("pypsa_eur_2050", "idees_today", "asean_own_2019"):
        raise ValueError("Unknown research.s3.industry.other_bucket " + other_bucket)
    if other_bucket == "idees_today":
        ind_path = ind_path.with_name(ind_path.stem + "_OTHER_IDEES_TODAY.csv")
    elif other_bucket == "asean_own_2019":
        ind_path = ind_path.with_name(ind_path.stem + "_OTHER_ASEAN_OWN_2019.csv")
    ind_summary = pd.read_csv(ind_path).set_index("country")
    # S3-0 interim handling of the ratio ammonia/methanol rows: convert_to_h2_and_gas = ammonia -> H2 + electricity (PyPSA-Eur ammonia:false route,
    # config MWh_H2_per_tNH3_electrolysis 5.93 / MWh_elec_per_tNH3_electrolysis 0.2473 per 5.166 MWh_NH3, lines 849/852/853), methanol -> methane +
    # electricity (today's SMR route, MWh_CH4_per_tMeOH 10.25 / MWh_elec_per_tMeOH 0.167 per 5.528 MWh_MeOH, lines 904-906); regional_buses = loads on the
    # regional ammonia / methanol buses (S3-3).
    am_mode = str(I.get("ammonia_methanol_mode", "convert_to_h2_and_gas"))
    if am_mode not in ("convert_to_h2_and_gas", "regional_buses"):
        raise ValueError("Unknown research.s2.industry.ammonia_methanol_mode " + am_mode)
    NH3_H2, NH3_EL = 5.93 / 5.166, 0.2473 / 5.166
    MEOH_CH4, MEOH_EL = 10.25 / 5.528, 0.167 / 5.528
    overflow_ledger, hydrogen_ledger, am_ledger = {}, {}, {}
    # R2 (decision 56): feedstock carbon. territorial = EDGAR 2.B+2.D on the process bus + domestic plastics burned (s2b_feedstock.py);
    # full_release = PyPSA-Eur default (all feedstock carbon released) as implemented in S2.
    fc_mode = str(I.get("feedstock_carbon_mode", "full_release"))
    if fc_mode not in ("territorial", "full_release"):
        raise ValueError("Unknown research.s2.industry.feedstock_carbon_mode " + fc_mode)
    fc_path = repo / I["territorial_tables"][alloc_mode]
    fc_table = pd.read_csv(fc_path, keep_default_na=False).set_index("country")
    feedstock_ledger = {}
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
        # S3-4 (decision 10, D1 section 4): shipping. Oil-equivalent demand (D1 table) x PyPSA-Eur 2050 fuel shares (methanol 1 / hydrogen 0 / oil 0,
        # registry share_shipping_*_2050) x energy conversion shipping_oil_efficiency / shipping_methanol_efficiency (config lines 635-636), served
        # from the regional methanol bus through a node link that books 1/MWh_MeOH_per_tCO2 in the consuming country (add_shipping lines 5195-5227);
        # the international bunker part shares the switch research.s2.demand.international_bunkers with aviation. S3-5 splits by fuel origin.
        SHIP = cfg["research"].get("s3", {}).get("shipping")
        for account, switch in [("DomesticShippingFuel", True), ("InternationalShippingBunker", bool(D["international_bunkers"]))]:
            rows = d[d.account == account]
            if not len(rows):
                continue
            v_oil = float(rows.v.sum())
            if SHIP is None:
                deferred.append(dict(country=c, account=account, carrier="oil", annual_mwh=v_oil, reason="shipping deferred to S3 (methanol/ammonia)"))
                continue
            if not switch:
                deferred.append(dict(country=c, account=account, carrier="oil", annual_mwh=v_oil, reason="switch research.s2.demand.international_bunkers=false"))
                continue
            sh2 = shares.get((c, account)) or _shares_for(shares, astar_shares, c, "Transport")[0]
            m_share, h_share, o_share = rv("share_shipping_methanol_share_2050"), rv("share_shipping_hydrogen_share_2050"), rv("share_shipping_oil_share_2050")
            conv_m = float(SHIP["shipping_oil_efficiency"]) / float(SHIP["shipping_methanol_efficiency"])
            ef_meoh = cost(costs, "methanol", "CO2 intensity")
            sector = "shipping domestic" if account == "DomesticShippingFuel" else "shipping international"
            for node, s in sh2.items():
                if s <= 0:
                    continue
                if m_share > 0:
                    add_bus(n, "ASEAN methanol", "methanol", "ASEAN", "")
                    fb = add_bus(n, f"{node} shipping methanol final", "methanol final energy", c, node)
                    link = f"{node} shipping methanol"
                    if link not in n.links.index:
                        add_link(n, link, c, "shipping methanol", ["ASEAN methanol", fb, atmosphere_bus(c)], [1.0, ef_meoh], role="CONVERSION",
                                 extra={"carbon_rule": "methanol carbon released at use in the consuming country (PyPSA-Eur shipping methanol link); origin-neutral split in S3-5"})
                    plain_load(node, c, "Transport", account, "shipping methanol", fb, v_oil * s * m_share * conv_m, f"{c}:{account}:oil x {m_share} x {conv_m:.4f}", f"{node} {sector} methanol")
                if h_share > 0:
                    conv_h = float(SHIP["shipping_oil_efficiency"]) / cost(costs, "fuel cell", "efficiency")
                    plain_load(node, c, "Transport", account, "shipping hydrogen", f"{node} H2", v_oil * s * h_share * conv_h, f"{c}:{account}:oil x {h_share} x {conv_h:.4f}", f"{node} {sector} hydrogen")
                if o_share > 0:
                    meter_load(node, c, sector, "oil", v_oil * s * o_share, f"{c}:{account}:oil x {o_share}", account)
        # ---- industry (R1: carrier structure by mode) --------------------------------------------------------
        ind = d[(d.sector == "Industry") & (d.carrier != "electricity")]
        sh, _ = _shares_for(shares, astar_shares, c, "Industry")
        m = ind_summary.loc[c] if c in ind_summary.index else None
        if carrier_mode == "pypsa_eur_2050" and m is not None:
            ov_summary = float(m["biomass_overflow_industry_to_gas_mwh"])
            ind_car = {"coal": float(m["pe_coal_mwh"]), "oil": float(m["pe_oil_mwh"]), "gas": float(m["pe_gas_mwh"]) - ov_summary, "biomass": float(m["pe_biomass_before_overflow_mwh"]),
                       "electricity": float(m["pe_electricity_mwh"]), "hydrogen": float(m["pe_hydrogen_mwh"]), "heat": float(m["pe_heat_mwh"]),
                       "ammonia": float(m["pe_ammonia_mwh"]) if "pe_ammonia_mwh" in m.index else 0.0, "methanol": float(m["pe_methanol_mwh"]) if "pe_methanol_mwh" in m.index else 0.0}
            if am_mode == "convert_to_h2_and_gas":
                am_ledger[c] = dict(mode=am_mode, ammonia_mwh=ind_car["ammonia"], methanol_mwh=ind_car["methanol"], to_hydrogen_mwh=ind_car["ammonia"] * NH3_H2,
                                    to_gas_mwh=ind_car["methanol"] * MEOH_CH4, to_electricity_mwh=ind_car["ammonia"] * NH3_EL + ind_car["methanol"] * MEOH_EL)
                ind_car["hydrogen"] += ind_car["ammonia"] * NH3_H2; ind_car["gas"] += ind_car["methanol"] * MEOH_CH4
                ind_car["electricity"] += ind_car["ammonia"] * NH3_EL + ind_car["methanol"] * MEOH_EL
                ind_car["ammonia"] = 0.0; ind_car["methanol"] = 0.0
            else:
                am_ledger[c] = dict(mode=am_mode, ammonia_mwh=ind_car["ammonia"], methanol_mwh=ind_car["methanol"])
            src_ind = f"{c}:Industry2050PyPSAEurRoutes"
            heat_src = ("PyPSA-Eur ratio heat row, all sub-sectors (JRC-IDEES-2021 reproduction, decision 61)" if ratio_source == "jrc_idees_2021"
                        else "PyPSA-Eur ratio heat row with technology-data steel/cement substitutes (S2B method, sensitivity)")
        else:
            ind_car = {carrier: float(v) * (1 - s_lt) for carrier, v in ind.groupby("carrier").v.sum().items()}
            ind_car["heat"] = float(ind.v.sum()) * s_lt * boiler_eff; ind_car["electricity"] = 0.0; ind_car["hydrogen"] = 0.0
            src_ind = f"{c}:IndustryFinalEnergy"; heat_src = "IndustryFinalEnergy x low_temperature_heat_share x boiler_eff"
        # decision 36 / R1.6: fixed solid-biomass demand above the national main potential moves to methane at equal heat (industry first, then agriculture)
        ag_rows = d[(d.sector == "AgricultureOthers") & (d.carrier == "biomass")]
        ag_bio = float(ag_rows.v.sum())
        pot_c = float(n.stores[(n.stores.bus == f"solid biomass {c}") & (n.stores.research_role == "FINITE_RESOURCE")].e_nom.sum()) if "research_role" in n.stores else 0.0
        overflow = max(0.0, ind_car.get("biomass", 0.0) + ag_bio - pot_c)
        ov_ind = min(overflow, ind_car.get("biomass", 0.0)); ov_ag = min(overflow - ov_ind, ag_bio)
        ind_car["biomass"] = ind_car.get("biomass", 0.0) - ov_ind
        overflow_ledger[c] = dict(solid_biomass_potential_mwh=pot_c, industry_biomass_before_mwh=ind_car.get("biomass", 0.0) + ov_ind, agriculture_biomass_before_mwh=ag_bio,
                                  overflow_industry_to_gas_mwh=ov_ind, overflow_agriculture_to_gas_mwh=ov_ag, mode=carrier_mode)
        hydrogen_ledger[c] = ind_car.get("hydrogen", 0.0)
        for node, s in sh.items():
            if s <= 0:
                continue
            if ind_car.get("heat", 0.0) * s > 0:
                plain_load(node, c, "Industry", "IndustryLowTemperatureHeat", "industry heat", f"{node} industry heat", ind_car["heat"] * s, heat_src, f"{node} industry heat demand")
            for carrier in ["coal", "oil", "gas", "biomass", "unclassified_fuel"]:
                v = ind_car.get(carrier, 0.0)
                if v * s > 0:
                    meter_load(node, c, "industry", carrier, v * s, f"{src_ind}:{carrier}", "IndustryFinalEnergy")
            if ov_ind * s > 0:
                meter_load(node, c, "industry overflow", "gas", ov_ind * s, f"{c}:IndustryBiomass -> gas (above solid-biomass potential, decision 36)", "IndustryBiomassOverflowToGas")
            if ind_car.get("electricity", 0.0) * s > 0:
                plain_load(node, c, "Industry", "IndustryElectricityRoutes", "industry electricity", node, ind_car["electricity"] * s, f"{src_ind}:electricity", f"{node} industry electricity demand")
            if ind_car.get("hydrogen", 0.0) * s > 0:
                plain_load(node, c, "Industry", "IndustryHydrogenDRI", "industry hydrogen", f"{node} H2", ind_car["hydrogen"] * s, f"{src_ind}:hydrogen", f"{node} industry hydrogen demand")
            # S3-3 (decision 44), regional_buses mode: ammonia load on the regional ammonia bus (no CO2); methanol through a node link that books the
            # methanol carbon in the consuming country's atmosphere (PyPSA-Eur industry methanol link, prepare_sector_network.py lines 4617-4626,
            # efficiency2 = 1 / MWh_MeOH_per_tCO2 = technology-data methanol CO2 intensity 0.2482 t/MWh); the regional buses are created here when the
            # import layer (S3-2) has not created them yet. S3-5 (origin-neutral) replaces the fossil EF by the fuel-origin split.
            if ind_car.get("ammonia", 0.0) * s > 0:
                add_bus(n, "ASEAN ammonia", "ammonia", "ASEAN", "")
                plain_load(node, c, "Industry", "IndustryAmmonia", "industry ammonia", "ASEAN ammonia", ind_car["ammonia"] * s, f"{src_ind}:ammonia", f"{node} industry ammonia demand")
            if ind_car.get("methanol", 0.0) * s > 0:
                add_bus(n, "ASEAN methanol", "methanol", "ASEAN", "")
                fb = add_bus(n, f"{node} industry methanol final", "methanol final energy", c, node)
                link = f"{node} industry methanol use"
                if link not in n.links.index:
                    add_link(n, link, c, "industry methanol", ["ASEAN methanol", fb, atmosphere_bus(c)], [1.0, cost(costs, "methanol", "CO2 intensity")], role="CONVERSION",
                             extra={"carbon_rule": "methanol carbon released at use (PyPSA-Eur industry methanol link); origin-neutral split in S3-5"})
                plain_load(node, c, "Industry", "IndustryMethanol", "industry methanol", fb, ind_car["methanol"] * s, f"{src_ind}:methanol", f"{node} industry methanol demand")
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
                elif carrier == "biomass":
                    if (v - ov_ag) * s > 0:
                        meter_load(node, c, "agriculture", "biomass", (v - ov_ag) * s, f"{c}:AgricultureFinalEnergy:biomass", "AgricultureFinalEnergy")
                    if ov_ag * s > 0:
                        meter_load(node, c, "agriculture overflow", "gas", ov_ag * s, f"{c}:AgricultureFinalEnergy:biomass -> gas (above solid-biomass potential, decision 36)", "AgricultureBiomassOverflowToGas")
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
                    if fc_mode == "territorial":
                        # the fuel is still drawn from the fuel bus; its carbon is booked only where it is emitted domestically (process bus + plastics below)
                        add_link(n, link, c, f"{carrier} feedstock", [f"{node} {carrier}", fb], [1.0], role="FEEDSTOCK_CARBON", extra={"feedstock_carbon_mode": "territorial"})
                    else:
                        add_link(n, link, c, f"{carrier} feedstock", [f"{node} {carrier}", fb, f"{node} process emissions", atmosphere_bus(c)],
                                 [1.0, f_process * ef[carrier], (1 - f_process) * eol_release * ef[carrier]], role="FEEDSTOCK_CARBON",
                                 extra={"process_share": f_process, "end_of_life_release": eol_release, "feedstock_carbon_mode": "full_release"})
                plain_load(node, c, "NonEnergyUse", f"NonEnergy:{carrier}", f"{carrier} feedstock", fb, v * s * scale, f"{c}:NonEnergy:{carrier} x HVC primary {scale if carrier == 'oil' else 1.0}", f"{node} feedstock {carrier} demand")
        # ---- process emissions (EDGAR 2.A + 2.C, 2050; territorial mode adds 2.B + 2.D) ------------------------
        pe_sfx = "_level" if alloc_mode.endswith("_level") else ""   # S3B R1: level growth method uses the level process-emission rows
        proc = sum(float(reg.loc[f"process_emissions_{g}_2050{pe_sfx}_{c}", "value"]) for g in S2["co2"]["process_emissions_scope"] if reg.loc[f"process_emissions_{g}_2050_{c}", "status"] in ("REGISTERED", "SOURCE_ZERO"))
        fc_row = fc_table.loc[c] if c in fc_table.index else None
        proc_feed = float(fc_row["process_2B_2D_2050_t"]) if (fc_mode == "territorial" and fc_row is not None) else 0.0
        plastics = float(fc_row["plastics_burned_co2_2050_t"]) if (fc_mode == "territorial" and fc_row is not None) else 0.0
        feedstock_ledger[c] = dict(mode=fc_mode, process_2B_2D_2050_t=proc_feed, plastics_burned_co2_2050_t=plastics, edgar_2A_2C_2050_t=proc,
                                   full_release_2050_t=(float(fc_row["full_release_2050_t"]) if fc_row is not None else None))
        sh, _ = _shares_for(shares, astar_shares, c, "ProcessEmissions")
        ensure_carrier(n, "process emissions")
        for node, s in sh.items():
            if (proc + proc_feed) * s <= 0:
                continue
            g = f"{node} process emissions source"
            n.add("Generator", g, bus=f"{node} process emissions", carrier="process emissions", p_nom=(proc + proc_feed) * s / HOURS, p_nom_extendable=False, p_min_pu=1.0, p_max_pu=1.0, marginal_cost=0.0, capital_cost=0.0)
            n.generators.loc[g, ["country", "research_role", "asset_role"]] = [c, "PROCESS_EMISSION_SOURCE", "exogenous_process_emission"]
            loads.append(dict(load=g, country=c, sector="ProcessEmissions", account="EDGAR 2.A+2.C x industry multiplier" + (" + 2.B+2.D (territorial feedstock carbon, R2)" if proc_feed > 0 else ""),
                              carrier="process emissions", source_row=f"process_emissions_*_2050_{c}" + (f";feedstock_process_2B_2D_2050_{c}" if proc_feed > 0 else ""), annual_mwh=(proc + proc_feed) * s, bus=f"{node} process emissions"))
        # ---- domestic plastics burned (R2 b): exogenous release to the national atmosphere, no capture ---------------------
        if plastics > 0:
            ensure_carrier(n, "plastic waste"); ensure_carrier(n, "waste incineration")
            for node, s in sh.items():
                if plastics * s <= 0:
                    continue
                pb = add_bus(n, f"{node} plastic waste", "plastic waste", c, node)
                g = f"{node} plastic waste source"
                n.add("Generator", g, bus=pb, carrier="plastic waste", p_nom=plastics * s / HOURS, p_nom_extendable=False, p_min_pu=1.0, p_max_pu=1.0, marginal_cost=0.0, capital_cost=0.0)
                n.generators.loc[g, ["country", "research_role", "asset_role"]] = [c, "PLASTIC_WASTE_SOURCE", "exogenous_waste_emission"]
                add_link(n, f"{node} plastic waste burning", c, "waste incineration", [pb, atmosphere_bus(c)], [1.0], role="WASTE_BURNING_RELEASE",
                         extra={"energy_recovery": "not modelled (R2: emissions only)"})
                loads.append(dict(load=g, country=c, sector="ProcessEmissions", account="domestic end-of-life plastics burned (What a Waste 3.0 x IPCC Table 2.4)", carrier="plastic waste",
                                  source_row=f"feedstock_plastics_burned_co2_2050_{c}", annual_mwh=plastics * s, bus=pb))
        # ---- Astar base load. S4J-1 (decision 104) table_sectors: annual total = demand-table electricity of the sectors not modelled separately
        #      (TABLE_BASE_SECTORS; + Industry in bas_fixed), Astar only gives the hourly shape and the node split (every Astar load of the country is
        #      scaled by the same factor). astar_residual (former method): Astar minus the explicit industry / transport electricity --------------------
        te = float(d[(d.sector == "Transport") & (d.carrier == "electricity")].v.sum())
        ie = float(d[(d.sector == "Industry") & (d.carrier == "electricity")].v.sum()) if carrier_mode == "pypsa_eur_2050" else 0.0   # R1: industry electricity is explicit in the route mode
        astar_c = [l for l in n.loads.index if n.loads.at[l, "account"] == "Astar" and n.loads.at[l, "country"] == c]
        pset = n.loads_t.p_set
        w = n.snapshot_weightings.generators
        astar_total = float(sum((pset[l] * w).sum() for l in astar_c if l in pset))
        ded_total = te + ie
        parts = [p for p, v in [("transport electricity (rail/road, embedded in Astar)", te), ("industry electricity (AEO8 BAS share embedded in Astar; replaced by the 2050 route electricity)", ie)] if v > 0]
        explicit = dict(ev_mwh=E_land * ev_share * oil_to_el, fcev_h2_mwh=E_land * fc_share * oil_to_h2, industry_electricity_mwh=ind_car.get("electricity", 0.0), industry_hydrogen_mwh=ind_car.get("hydrogen", 0.0))
        if ne_mode == "table_sectors":
            el = d[d.carrier == "electricity"]
            base_sectors = list(TABLE_BASE_SECTORS) + ([] if carrier_mode == "pypsa_eur_2050" else ["Industry"])
            by_sector = {s: float(el[el.sector == s].v.sum()) for s in base_sectors}
            target = float(sum(by_sector.values()))
            if astar_total <= 0 and target > 0:
                raise ValueError("No Astar shape for the table-sector electricity of " + c)
            factor = target / astar_total if astar_total > 0 else 1.0
            for l in astar_c:
                if l in pset:
                    n.loads_t.p_set[l] = pset[l] * factor
            deductions.append(dict(country=c, mode="table_sectors", deducted="replaced: annual total = demand-table electricity of " + " + ".join(base_sectors) + " (Astar = hourly shape)",
                                   deducted_mwh=astar_total - target, deducted_transport_mwh=0.0, deducted_industry_mwh=ie, astar_before_mwh=astar_total, astar_after_mwh=target,
                                   factor=factor, base_sectors_mwh=by_sector, added_explicit=explicit))
        elif ded_total > 0 and astar_total > 0:
            factor = 1.0 - ded_total / astar_total
            if factor < 0:
                raise ValueError("Deducted electricity exceeds Astar for " + c)
            for l in astar_c:
                if l in pset:
                    n.loads_t.p_set[l] = pset[l] * factor
            deductions.append(dict(country=c, mode="astar_residual", deducted=" + ".join(parts), deducted_mwh=ded_total, deducted_transport_mwh=te, deducted_industry_mwh=ie, astar_before_mwh=astar_total, astar_after_mwh=astar_total * factor, factor=factor,
                                   added_explicit=explicit))
        else:
            deductions.append(dict(country=c, mode="astar_residual", deducted="none", deducted_mwh=ded_total, deducted_transport_mwh=te, deducted_industry_mwh=ie, astar_before_mwh=astar_total, astar_after_mwh=astar_total, factor=1.0, added_explicit=explicit))
    ledger = dict(loads=loads, deductions=deductions, deferred=deferred, parameters=dict(ev_share=ev_share, fcev_share=fc_share, ice_share=ice_share, oil_to_electricity=oil_to_el, oil_to_hydrogen=oil_to_h2,
                  bev_charge_efficiency=bev_eff, bev_availability=bev_avail, agriculture_electric_share=ag_el_share, agriculture_efficiency_gain=ag_gain, hvc_primary_fraction=hvc_primary,
                  feedstock_end_of_life_release=eol_release, industry_low_temperature_heat_share=(s_lt if carrier_mode == "bas_fixed" else "ratio heat row (R1)"), existing_boiler_efficiency=boiler_eff, cookstove_basic=COOKSTOVE_BASIC_FUELWOOD,
                  cookstove_basic_default=COOKSTOVE_BASIC_DEFAULT, cookstove_modern=COOKSTOVE_MODERN, industry_carrier_mode=carrier_mode, nonindustrial_electricity=ne_mode, industry_table=str(ind_path.relative_to(repo))), node_share_source=D["node_allocation"],
                  industry=dict(carrier_mode=carrier_mode, ratio_source=ratio_source, ammonia_methanol_mode=am_mode, table=str(ind_path.relative_to(repo)), biomass_overflow=overflow_ledger,
                                hydrogen_mwh=hydrogen_ledger, ammonia_methanol=am_ledger),
                  feedstock=dict(mode=fc_mode, table=str(fc_path.relative_to(repo)), by_country=feedstock_ledger))
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
    # S4B-0 (decision 73): gas slack per country balance - one penalised source on every node gas bus (the gas balance is nodal; nodes of a country
    # are joined by the domestic pipeline candidates), reported per country in the gap table; same penalty as the other slacks. Main runs unchanged.
    slacks = ["electricity", "co2", "biomass"]
    gas_pen = float(gcfg.get("penalty_eur_per_mwh_gas", gcfg["penalty_eur_per_mwh"]))
    if "gas" in list(gcfg.get("slacks", ["electricity", "co2", "biomass", "gas"])):
        ensure_carrier(n, "gap slack gas")
        for node in nodes:
            bus = f"{node} gas"
            if bus in n.buses.index:
                name = f"{node} gap slack gas"
                n.add("Generator", name, bus=bus, carrier="gap slack gas", p_nom_extendable=True, p_nom=0.0, capital_cost=0.0, marginal_cost=gas_pen)
                n.generators.loc[name, ["country", "research_role", "asset_role"]] = [country_of(n, node), "GAP_DIAGNOSTIC_SLACK", "diagnostic_slack"]
        slacks.append("gas")
    hooks = set(n.meta.get("required_constraint_hooks", [])) - {"research_country_net_zero"} | {"research_gap_diagnostic"}
    n.meta["required_constraint_hooks"] = sorted(hooks)
    n.meta["gap_diagnostic"] = dict(enabled=True, penalty_eur_per_mwh=float(gcfg["penalty_eur_per_mwh"]), penalty_eur_per_tco2=float(gcfg["penalty_eur_per_tco2"]),
                                    penalty_eur_per_mwh_gas=gas_pen, slacks=slacks, label="GAP_DIAGNOSTIC_NOT_FOR_INTERCONNECTION_VALUE")
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


def add_apg_corridor_lines(n, corridors):
    """S3-0 (decisions 59/62): corridor-table rows whose Line component is absent from the frozen electric base (APG AIMS III 2024 #11 TH-MM and
    #17 LA-MM, scripts_project/s3_0_corridors.py) are added as AC lines with the base conventions: capital cost per km = median of the existing
    cross-border AC lines (uniform 42.01 EUR/MW/km/a), line type / s_max_pu / electrical parameters per km from the existing cross-border line
    closest to the median num_parallel, s_nom = s_nom_min = capacity_2025_mw (0 for #11, 30 MW for #17), extendable, border_class cross_border."""
    added = []
    cty = n.buses.country
    xb = n.lines[cty.reindex(n.lines.bus0).to_numpy() != cty.reindex(n.lines.bus1).to_numpy()]   # border_class is tagged later (tag_cross_border)
    cpk = float((xb.capital_cost / xb.length).median())
    tmpl = xb.iloc[int((xb.num_parallel - xb.num_parallel.median()).abs().argsort().iloc[0])]   # typical border line: closest to the median num_parallel of the existing cross-border AC lines
    for _, r in corridors.iterrows():
        if r.component_type != "Line" or str(r.component) in n.lines.index:
            continue
        name = str(r.component); length = float(r.length_km); cap = float(r.capacity_2025_mw); npar = float(tmpl.num_parallel)
        n.add("Line", name, bus0=r["from"], bus1=r["to"], carrier="AC", type=tmpl.type, s_max_pu=float(tmpl.s_max_pu), length=length, num_parallel=npar,
              s_nom=cap, s_nom_min=cap, s_nom_extendable=True, capital_cost=cpk * length, build_year=0,
              x=float(tmpl.x) / float(tmpl.length) * length, r=float(tmpl.r) / float(tmpl.length) * length, b=float(tmpl.b) / float(tmpl.length) * length)
        if "price_qualification" in n.lines.columns:
            n.lines.at[name, "price_qualification"] = tmpl.price_qualification
        added.append(dict(component=name, bus0=r["from"], bus1=r["to"], length_km=length, capacity_2025_mw=cap, capital_cost_eur_per_mw_a=cpk * length,
                          capital_cost_eur_per_mw_km_a=cpk, template_line=str(tmpl.name), num_parallel=npar, line_type=str(tmpl.type), status=str(r.status)))
    n.meta["apg_corridor_additions"] = added
    return added
