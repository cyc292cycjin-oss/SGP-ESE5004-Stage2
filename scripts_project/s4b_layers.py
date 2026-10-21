"""S4B-0 (decision 70): sector technology switches aligned with the PyPSA-Eur v2025.07.0 `sector` defaults.

Reference: research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml (sector block lines 478-820) and
pypsa_eur_v2025.07.0_prepare_sector_network.py. The switch table with the original values, the new values and the reason for every
remaining deviation is research_inputs/sector_v5/SECTOR_SWITCHES_VS_PYPSA_EUR.csv (scripts_project/s4b_0_data.py).

Built here (after the S3 gas network and the S3-3 ammonia/methanol layer, before the S3-5 fuel-carbon mode):
  * methanation (config line 676, true): one Sabatier Link per node, PyPSA-Eur add_storage_and_grids lines 2094-2111: bus0 node H2,
    bus1 node gas, bus2 node co2 stored (captured CO2); efficiency = technology-data methanation efficiency, efficiency2 =
    -efficiency x gas CO2 intensity; capital cost x efficiency (cost given per kW_gas); p_min_pu = min_part_load_methanation (line 737).
    Carbon (decision 64): gas stays a network carrier with the producer-credit treatment - no synthesis port; the carbon was booked
    (or credited) where the CO2 was captured and the methane books the fossil EF where it is burned.
  * electrobiofuels (line 779, true): one Link per node, add_biomass lines 4263-4304: bus0 national solid-biomass pool, bus1 node oil,
    bus2 node H2 (input), bus3 national atmosphere (efficiency3 = -EF_solid_biomass + BtL CO2 stored x (1 - FT capture rate), i.e. the
    fuel carbon credited at production as PyPSA-Eur does); costs = BtL x efficiency + BtL C stored x Fischer-Tropsch x efficiency.
    In origin_neutral mode s3_layers.add_fuel_carbon_mode moves the output to the node non-fossil oil bus and drops the credit port,
    exactly as for BtL (biogenic carbon: neither credit nor emission).
  * min_part_load_fischer_tropsch (line 735, 0.5): p_min_pu of the Fischer-Tropsch links (S1 recipe built them with 0).
  * hydrogen_fuel_cell / SMR / SMR_cc / biomass_to_liquid (lines 686, 688, 689, 777, all true): already built (S1 recipe, upstream
    add_hydrogen, S2 biomass layer); a false switch removes the links (sensitivity only).
Switches that live elsewhere and are only recorded here: hydrogen_turbine (research.hydrogen.h2_turbine), co2_vent
(research.s2.co2.vent), dac (research.s2.co2.dac), methanol_to_power.ocgt / biomass_to_methanol (research.s3.ammonia_methanol).
"""
from __future__ import annotations

from carrier_architecture import atmosphere_bus
from s2_costs import cost
from s2_layers import add_link, country_of

PYPSA_EUR_LINES = dict(methanation=676, electrobiofuels=779, min_part_load_fischer_tropsch=735, min_part_load_methanation=737, hydrogen_fuel_cell=686,
                       hydrogen_turbine=687, SMR=688, SMR_cc=689, biomass_to_liquid=777, co2_vent=679, dac=678)
REMOVABLE = {"hydrogen_fuel_cell": "H2 Fuel Cell", "SMR": "SMR", "SMR_cc": "SMR CC", "biomass_to_liquid": "BtL"}


def apply_sector_alignment(n, costs, cfg, nodes):
    S = cfg["research"].get("sector") or {}
    led = dict(source="PyPSA-Eur v2025.07.0 config.default.yaml sector block (lines 478-820)", pypsa_eur_lines=PYPSA_EUR_LINES, switches={}, added={}, removed={}, parameters={})
    ef_gas = cost(costs, "gas", "CO2 intensity"); ef_bio = cost(costs, "solid biomass", "CO2 intensity")
    # 1. methanation (Sabatier)
    if bool(S.get("methanation", False)):
        eff = cost(costs, "methanation", "efficiency"); fixed = cost(costs, "methanation", "fixed"); vom = cost(costs, "methanation", "VOM"); life = cost(costs, "methanation", "lifetime")
        pl = float(S.get("min_part_load_methanation", 0.3))
        k = 0
        for node in nodes:
            h2, gas, co2s = f"{node} H2", f"{node} gas", f"{node} co2 stored"
            if not all(b in n.buses.index for b in (h2, gas, co2s)):
                continue
            add_link(n, f"{node} Sabatier", country_of(n, node), "Sabatier", [h2, gas, co2s], [eff, -eff * ef_gas], capital_cost=fixed * eff, marginal_cost=vom * eff, lifetime=life, p_min_pu=pl,
                     extra={"carbon_rule": "decision 64: gas producer credit - CO2 from the node captured-CO2 buffer, no synthesis port; the methane books the fossil EF where it is burned"})
            k += 1
        led["added"]["Sabatier"] = k
        led["parameters"]["methanation"] = dict(efficiency=eff, co2_t_per_mwh_h2=eff * ef_gas, capital_cost_eur_per_mw_h2_a=fixed * eff, fixed_per_mw_gas=fixed, lifetime=life, p_min_pu=pl,
                                                cost_row="technology-data v0.15.0 methanation (cost layer of decision 50)", code_ref="PyPSA-Eur prepare_sector_network.py lines 2094-2111")
    # 2. electrobiofuels
    if bool(S.get("electrobiofuels", False)):
        eb = cost(costs, "electrobiofuels", "efficiency-biomass"); eh = cost(costs, "electrobiofuels", "efficiency-hydrogen"); life = cost(costs, "electrobiofuels", "lifetime")
        scale = cost(costs, "BtL", "C stored")
        cap = cost(costs, "BtL", "fixed") * cost(costs, "BtL", "efficiency") + scale * cost(costs, "Fischer-Tropsch", "fixed") * cost(costs, "Fischer-Tropsch", "efficiency")
        vom = cost(costs, "BtL", "VOM") * cost(costs, "BtL", "efficiency") + scale * cost(costs, "Fischer-Tropsch", "VOM") * cost(costs, "Fischer-Tropsch", "efficiency")
        credit = -ef_bio + cost(costs, "BtL", "CO2 stored") * (1.0 - cost(costs, "Fischer-Tropsch", "capture rate"))
        k = 0
        for node in nodes:
            c = country_of(n, node); bio, oil, h2 = f"solid biomass {c}", f"{node} oil", f"{node} H2"
            if not all(b in n.buses.index for b in (bio, oil, h2)):
                continue
            add_link(n, f"{node} electrobiofuels", c, "electrobiofuels", [bio, oil, h2, atmosphere_bus(c)], [eb, -eb / eh, credit], capital_cost=cap, marginal_cost=vom, lifetime=life,
                     extra={"carbon_rule": "PyPSA-Eur: fuel carbon credited at production (efficiency3); origin_neutral: output to the non-fossil oil pool, credit dropped (s3_layers.add_fuel_carbon_mode)"})
            k += 1
        led["added"]["electrobiofuels"] = k
        led["parameters"]["electrobiofuels"] = dict(oil_per_mwh_biomass=eb, h2_per_mwh_biomass=eb / eh, atmosphere_t_per_mwh_biomass=credit, capital_cost_eur_per_mw_biomass_a=cap,
                                                    marginal_cost_eur_per_mwh_biomass=vom, efuel_scale_factor_btl_c_stored=scale, lifetime=life,
                                                    code_ref="PyPSA-Eur prepare_sector_network.py lines 4263-4304 (technology-data v0.15.0 electrobiofuels, BtL, Fischer-Tropsch rows)")
    # 3. Fischer-Tropsch minimum part load
    if S.get("min_part_load_fischer_tropsch") is not None:
        ft = n.links.index[n.links.carrier == "Fischer-Tropsch"]
        n.links.loc[ft, "p_min_pu"] = float(S["min_part_load_fischer_tropsch"])
        led["parameters"]["fischer_tropsch_p_min_pu"] = dict(value=float(S["min_part_load_fischer_tropsch"]), links=int(len(ft)), before=0.0, code_ref="PyPSA-Eur config line 735; prepare_sector_network.py add FT p_min_pu")
    # 4. switches for technologies built by earlier layers (default true; false removes them)
    for key, carrier in REMOVABLE.items():
        on = bool(S.get(key, True)); led["switches"][key] = on
        if not on:
            drop = list(n.links.index[n.links.carrier == carrier]); n.mremove("Link", drop); led["removed"][carrier] = len(drop)
    R = cfg["research"]
    led["switches"].update(methanation=bool(S.get("methanation", False)), electrobiofuels=bool(S.get("electrobiofuels", False)),
                           hydrogen_turbine=bool(R["hydrogen"]["h2_turbine"]), co2_vent=bool(R["s2"]["co2"].get("vent", True)), dac=bool(R["s2"]["co2"].get("dac", True)),
                           methanol_to_power_ocgt=bool(R["s3"]["ammonia_methanol"].get("methanol_to_power_ocgt", True)), biomass_to_methanol=bool(R["s3"]["ammonia_methanol"].get("biomass_to_methanol", True)))
    n.meta["research_sector_alignment"] = led
    return led


def apply_typhoon_premium(n, cfg, repo):
    """S4B-4 (decision 76): research.renewable.typhoon_premium = off (main) | on. With on, the onshore and offshore wind candidates (incl. the
    resource-class generators) at nodes whose wind potential lies for >= 50 % in cells passed by a >= 50 m/s tropical cyclone at least
    typhoon_threshold_per_decade times per 10 years (IBTrACS 1980-2024, TYPHOON_EXPOSURE_BY_NODE.csv, scripts_project/s4b_4_typhoon.py) get their
    capital cost multiplied by 1 + typhoon_premium_pct / 100 (Tarp-Johansen & Clausen 2006, +25 %, grade C, +-10 pp). The annualised capital cost
    carries the FOM as a share of investment, so the premium scales both. Implemented only; not run in S4B."""
    import pandas as pd
    from pathlib import Path
    RN = cfg["research"].get("renewable") or {}
    mode = str(RN.get("typhoon_premium", "off")); led = dict(mode=mode, applied=[])
    if mode == "off":
        n.meta["research_typhoon_premium"] = led
        return led
    if mode != "on":
        raise ValueError("Unknown research.renewable.typhoon_premium " + mode)
    th = float(RN.get("typhoon_threshold_per_decade", 1.0)); pct = float(RN.get("typhoon_premium_pct", 25.0))
    t = pd.read_csv(Path(repo) / str(RN.get("typhoon_node_table", "research_inputs/renewable_v5/TYPHOON_EXPOSURE_BY_NODE.csv")))
    col = f"potential_share_ge_{th:g}"
    if col not in t:
        raise ValueError(f"typhoon_threshold_per_decade {th} not in the exposure table (0.5, 1, 2)")
    flagged = {(str(r["node"]), str(r["tech"])) for _, r in t.iterrows() if float(r[col]) >= 0.5}
    g = n.generators; ext = g.p_nom_extendable & g.carrier.isin(["onwind", "offwind-ac", "offwind-dc", "offwind-float"])   # offwind-float: M08a A6.2, exposure of the offwind-dc row of its node
    for name in g.index[ext]:
        key = (str(g.at[name, "bus"]), "offwind-dc" if g.at[name, "carrier"] == "offwind-float" else str(g.at[name, "carrier"]))
        if key in flagged:
            before = float(g.at[name, "capital_cost"]); n.generators.at[name, "capital_cost"] = before * (1.0 + pct / 100.0)
            led["applied"].append(dict(generator=name, node=key[0], tech=key[1], capital_cost_before=before, capital_cost_after=before * (1.0 + pct / 100.0)))
    led.update(threshold_per_decade=th, premium_pct=pct, flagged=sorted(map(list, flagged)), generators=len(led["applied"]))
    n.meta["research_typhoon_premium"] = led
    return led
