"""S4C model layers (S4C instruction v1, 2026-10-16; decisions 82-90).

S4C-0 (decisions 85, 90):
  * check_fuel_prices: build-time assertion that gas (LNG import, domestic production at the import price, decision 43), oil (ASEAN oil
    import) and coal (per-node external supply) carry the registry prices of ONE WEO 2025 scenario, research.fuels.price_scenario
    (steps main, nze low-price sensitivity, cps optional); lignite keeps the cost-layer value (no WEO lignite price).
  * apply_wacc_mode: research.finance.wacc_mode = uniform (main: one discount rate for all countries, social-planner view) |
    country_specific (implemented only, not run): the annualised capital cost of every new-build (extendable) component whose carrier
    maps to a cost-layer row is rescaled by [annuity(lifetime, r_country) + FOM] / [annuity(lifetime, r_row) + FOM] with the row
    lifetime, FOM and discount rate (CARRIER_COST_ROWS); r_country from research.finance.country_wacc_table (public sources only;
    countries without a sourced value are DATA_PENDING and the switch refuses to build).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from s2_costs import annuity, fuel_price_ids, fuel_price_scenario, registry_value

# carrier of a new-build component -> cost-layer row whose lifetime / FOM / discount rate annualise its capital cost
# (S4C-1 audit map; combined rows such as offwind turbine + connection use the main row for the WACC ratio)
CARRIER_COST_ROWS = {
    "onwind": "onwind", "offwind-ac": "offwind", "offwind-dc": "offwind", "solar": "solar-utility", "solar rooftop": "solar-rooftop",
    "nuclear": "nuclear", "nuclear SMR": "nuclear SMR", "geothermal": "geothermal", "ror": "ror", "hydro": "hydro", "PHS": "PHS",
    "CCGT": "CCGT", "OCGT": "OCGT", "CCGT CC": "CCGT", "H2 Electrolysis": "electrolysis", "H2 Fuel Cell": "fuel cell", "H2 turbine": "OCGT",
    "OCGT methanol": "OCGT", "SMR": "SMR", "SMR CC": "SMR CC", "Fischer-Tropsch": "Fischer-Tropsch", "Sabatier": "methanation",
    "methanolisation": "methanolisation", "Haber-Bosch": "Haber-Bosch", "ammonia cracker": "Ammonia cracker", "DAC": "direct air capture",
    "BtL": "BtL", "electrobiofuels": "electrobiofuels", "biomass EOP": "biomass EOP", "biomass EOP CC": "biomass EOP", "biogas upgrading": "biogas upgrading",
    "biomass-to-methanol": "biomass-to-methanol", "battery charger": "battery inverter", "home battery charger": "home battery inverter",
    "battery": "battery storage", "home battery": "home battery storage", "H2 Store Tank": "hydrogen storage tank type 1 including compressor",
    "industry biomass boiler": "biomass boiler", "industry biomass boiler CC": "biomass boiler", "industry gas boiler": "gas boiler steam",
    "industry electric boiler": "electric boiler steam", "industry heat pump": "industrial heat pump high temperature",
    "industry biomass CC": "cement capture", "process emissions CC": "cement capture", "electricity distribution grid": "electricity distribution grid",
    "H2 pipeline": "H2 (g) pipeline", "CO2 pipeline": "CO2 pipeline", "gas pipeline": "CH4 (g) pipeline", "DC": "HVDC overhead", "AC": "HVAC overhead",
    "co2 stored": "CO2 storage tank", "LNG import": None, "H2 import": None, "co2 sequestered": None, "ammonia store": None, "methanol store": None,
}


def check_fuel_prices(n, cfg, registry: pd.DataFrame, cost_ledger: dict) -> dict:
    """Assert one WEO scenario for gas, oil and coal and that the network prices equal the registry values of that scenario."""
    scen = fuel_price_scenario(cfg); ids = fuel_price_ids(cfg)
    price = {c: registry_value(registry, pid) for c, pid in ids.items()}
    led = dict(scenario=scen, registry_ids=ids, prices_eur2020_per_mwh=price, checks={})
    over = {o["technology"]: o for o in cost_ledger.get("overrides", []) if o.get("parameter") == "fuel"}
    if {k: over[k]["source"] for k in ids if k in over} != ids:
        raise AssertionError(f"cost-layer fuel overrides do not use the {scen} registry rows: {over}")
    if cost_ledger.get("fuel_price_scenario") != scen:
        raise AssertionError("cost ledger fuel_price_scenario differs from research.fuels.price_scenario")
    adder = float(cfg["research"]["s3"]["gas"].get("lng_regasification_adder_eur_per_mwh", 0.0))
    g = n.generators
    groups = {"gas LNG import": (g.carrier == "LNG import", price["gas"] + adder), "gas domestic production (decision 43)": (g.carrier == "gas production", price["gas"]),
              "oil ASEAN import": (g.carrier == "oil import", price["oil"]),
              "coal per-node supply": ((g.carrier == "coal") & (g.research_role == "EXTERNAL_SUPPLY"), price["coal"])}
    for label, (mask, want) in groups.items():
        mc = g.loc[mask, "marginal_cost"].astype(float)
        if len(mc) == 0:
            led["checks"][label] = dict(generators=0, note="none in this network")
            continue
        bad = mc[~np.isclose(mc, want, rtol=1e-12, atol=1e-9)]
        if len(bad):
            raise AssertionError(f"{label}: {len(bad)} generators not at the {scen} price {want}: {bad.head().to_dict()}")
        led["checks"][label] = dict(generators=int(len(mc)), marginal_cost=float(want))
    lig = g.loc[(g.carrier == "lignite") & (g.research_role == "EXTERNAL_SUPPLY"), "marginal_cost"].astype(float)
    led["lignite"] = dict(generators=int(len(lig)), marginal_cost=(float(lig.iloc[0]) if len(lig) else None),
                          note="cost-layer lignite fuel row (technology-data v0.15.0); WEO 2025 Table 2.3 has no lignite price; not switched")
    led["status"] = "PASS"
    n.meta["research_fuel_prices"] = led
    return led


def apply_wacc_mode(n, costs: pd.DataFrame, cfg, repo) -> dict:
    """research.finance.wacc_mode: uniform (main) records the discount rates in use; country_specific rescales new-build capital costs."""
    F = (cfg["research"].get("finance") or {})
    mode = str(F.get("wacc_mode", "uniform"))
    led = dict(mode=mode, uniform_discount_rate=float(F.get("uniform_discount_rate", 0.07)))
    rates = {}
    for comp, attr in [("Generator", "p_nom_extendable"), ("Link", "p_nom_extendable"), ("StorageUnit", "p_nom_extendable"), ("Store", "e_nom_extendable")]:
        df = n.df(comp)
        for car in sorted(df.loc[df[attr] & (df.capital_cost > 0), "carrier"].unique()):
            row = CARRIER_COST_ROWS.get(car)
            r = float(costs.at[row, "discount rate"]) if (row and row in costs.index and np.isfinite(float(costs.at[row, "discount rate"]))) else None
            rates[f"{comp}:{car}"] = dict(cost_row=row, discount_rate=r)
    led["rates_by_carrier"] = rates
    if mode == "uniform":
        n.meta["research_finance"] = led
        return led
    if mode != "country_specific":
        raise ValueError("Unknown research.finance.wacc_mode " + mode)
    t = pd.read_csv(Path(repo) / F["country_wacc_table"], keep_default_na=False)
    t = t[t.status != "REFERENCE_ONLY"]
    pending = sorted(t.loc[t.status == "DATA_PENDING", "country"].unique())
    countries = sorted(set(n.buses.country.dropna()) - {"", "ASEAN"}) if "country" in n.buses else []
    missing = sorted(set(countries) - set(t.loc[t.status != "DATA_PENDING", "country"]))
    if missing:
        raise ValueError(f"wacc_mode country_specific: no sourced WACC for {missing} (DATA_PENDING: {pending}); no estimate is made - keep wacc_mode uniform")
    r_c = {r.country: float(r.wacc_real) for r in t.itertuples() if r.status != "DATA_PENDING"}
    changed = []
    for comp, attr in [("Generator", "p_nom_extendable"), ("Link", "p_nom_extendable"), ("StorageUnit", "p_nom_extendable"), ("Store", "e_nom_extendable")]:
        df = n.df(comp)
        for name in df.index[df[attr] & (df.capital_cost > 0)]:
            row = CARRIER_COST_ROWS.get(df.at[name, "carrier"]); c = str(df.at[name, "country"]) if "country" in df else ""
            if not row or row not in costs.index or c not in r_c:
                continue
            life, fom, r0 = float(costs.at[row, "lifetime"]), float(costs.at[row, "FOM"]) / 100.0, float(costs.at[row, "discount rate"])
            f = (annuity(life, r_c[c]) + fom) / (annuity(life, r0) + fom)
            before = float(df.at[name, "capital_cost"]); n.df(comp).at[name, "capital_cost"] = before * f
            changed.append(dict(component=comp, name=name, country=c, cost_row=row, factor=f))
    led.update(country_wacc=r_c, changed=len(changed), by_country={c: int(sum(1 for x in changed if x["country"] == c)) for c in r_c})
    n.meta["research_finance"] = led
    return led
