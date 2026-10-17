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

S4C-1 (decision 82, implementing decision 50) and S4C supplement 01 (ledger L18, decision 16):
  * apply_cost_layer_s4c1: research.cost_layer.electric_base_candidates = cost_layer (main) | electric_base (comparison, author costs of the
    frozen electric base) - the new-build components inherited from the frozen electric base get the technology-data v0.15.0 2050 rows:
    onwind (incl. resource classes) <- onwind; solar <- solar-utility; solar rooftop <- solar-rooftop; offwind-ac/dc <- offwind +
    <car>-station + 1.25 x (distance-to-shore x <car>-connection-submarine + landfall x <car>-connection-underground) (PyPSA-Eur
    v2025.07.0 add_electricity.py lines 541, 555-576; distances per node x class from OFFWIND_CONNECTION_DISTANCE_S4C1.csv); battery
    charger <- battery inverter; home battery charger <- home battery inverter; battery / home battery stores <- battery storage /
    home battery storage; electricity distribution grid <- electricity distribution grid; AC lines <- length x ((1 - s) HVAC overhead +
    s HVAC submarine); DC links <- length x ((1 - s) HVDC overhead + s HVDC submarine) + HVDC inverter pair (add_electricity.py lines
    475-502; the model length already carries the 1.25 factor, as in the author chain).
  * pipelines (H2 / CO2 / gas, incl. connectivity upgrades and the 2025 gas stock): L x ((1 - s) onshore row + s submarine row).
  * s = corridor subsea share of the node pair, research.corridors.subsea_share = landmass_nonland (main; user decision 2026-10-16:
    ASEAN-specific treatment "archipelagic subsea corridors": 0 on the same landmass, else the not-land share of the great-circle route) |
    geometric_all (upper bound: not-land share for every pair) | zero (former state); table SUBSEA_SHARE_S4C1.csv
    (scripts_project/s4c_1_subsea_shares.py). Existing capacity carries no new investment (PyPSA objective constant, decision 48).

S4C-2 (decision 83; user decision 2026-10-17 on stop report S4C_STOP_02):
  * apply_hydro_inflow_normalization: research.hydro.inflow_normalization = national_observed (main, option B) | national_observed_runoff_shares
    (option A, sensitivity) | frozen_base (former state). Stock = 'hydro existing' StorageUnits (inflow) + 'ror existing' Generators
    (p_max_pu x p_nom), author units and S4A/S4B additions alike; national annual target = Ember 2019-2025 median hydro generation x 1.1
    (HYDRO_NATIONAL_TARGET_S4C2.csv). B: unit energy = target x capacity share, unit seasonal shape kept (series scaled by target_u / energy_u;
    a unit without inflow takes the capacity-weighted shape of its country and kind); A: one factor target / energy per country (author
    runoff shares kept). Run-of-river availability is clipped at 1 (energy lost reported). New-build reservoir / run-of-river candidates:
    capacity-weighted per-MW inflow (availability) of the corrected same-country stock of the same kind (else the other kind of the country,
    else ASEAN); max_hours of the S4B-2 proxies unchanged; the research_new_hydro_inflow hook stays. PHS unaffected.
"""
from __future__ import annotations

import hashlib
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


ELECTRIC_BASE_ROWS = {("Generator", "onwind"): "onwind", ("Generator", "solar"): "solar-utility", ("Generator", "solar rooftop"): "solar-rooftop",
                      ("Link", "battery charger"): "battery inverter", ("Link", "home battery charger"): "home battery inverter",
                      ("Link", "electricity distribution grid"): "electricity distribution grid", ("Store", "battery"): "battery storage", ("Store", "home battery"): "home battery storage"}
PIPELINE_ROWS = {"H2 pipeline": ("H2 (g) pipeline", "H2 (g) submarine pipeline"), "CO2 pipeline": ("CO2 pipeline", "CO2 submarine pipeline"),
                 "gas pipeline": ("CH4 (g) pipeline", "CH4 (g) submarine pipeline")}
SUBSEA_MODES = {"zero": "share_zero", "geometric_all": "share_geometric_all", "landmass_nonland": "share_landmass_nonland"}
LOC_SUFFIXES = (" gas", " H2", " co2 stored", " oil")


def bus_location(n, bus):
    """Node location of a bus (n.buses.location, else the name without the carrier suffix); as in s4c_1_subsea_shares.loc."""
    b = n.buses
    l = str(b.at[bus, "location"]) if "location" in b and str(b.at[bus, "location"]) not in ("", "nan") else bus
    if l not in b.index or (float(b.at[l, "x"]) == 0.0 and float(b.at[l, "y"]) == 0.0):
        for s in LOC_SUFFIXES:
            if bus.endswith(s) and bus[: -len(s)] in b.index:
                return bus[: -len(s)]
    return l


def _fixed(costs, row):
    v = float(costs.at[row, "fixed"])
    if not np.isfinite(v):
        raise ValueError(f"cost-layer row {row!r} has no annualised cost")
    return v


def _class_of(name: str) -> int:
    """Resource class of an S4A class generator: '<name> c<k>' -> k, the original name -> 0 (s4a_layers.apply_renewable_profiles)."""
    head, _, tail = str(name).rpartition(" c")
    return int(tail) if head and tail.isdigit() else 0


def apply_cost_layer_s4c1(n, costs: pd.DataFrame, cfg, repo) -> dict:
    R = cfg["research"]
    mode = str(R["cost_layer"].get("electric_base_candidates", "electric_base"))
    C = R.get("corridors") or {}
    smode = str(C.get("subsea_share", "zero"))
    if mode not in ("cost_layer", "electric_base"):
        raise ValueError("Unknown research.cost_layer.electric_base_candidates " + mode)
    if smode not in SUBSEA_MODES:
        raise ValueError("Unknown research.corridors.subsea_share " + smode)
    led = dict(electric_base_candidates=mode, subsea_share=smode, changed={}, before_after=[])
    tab = {}
    if smode != "zero":
        p = Path(repo) / C["subsea_table"]; t = pd.read_csv(p)
        tab = {(r.loc0, r.loc1): float(getattr(r, SUBSEA_MODES[smode])) for r in t.itertuples()}
        led["subsea_table"] = dict(file=str(C["subsea_table"]), sha256=hashlib.sha256(p.read_bytes()).hexdigest(), column=SUBSEA_MODES[smode])

    def share(a, b):
        key = tuple(sorted((bus_location(n, a), bus_location(n, b))))
        if smode == "zero" or key[0] == key[1]:
            return 0.0
        if key not in tab:
            raise KeyError(f"node pair {key} missing in {C['subsea_table']}")
        return tab[key]

    def record(comp, name, carrier, before, after, extra=None):
        led["changed"][carrier] = led["changed"].get(carrier, 0) + 1
        row = dict(component=comp, name=str(name), carrier=carrier, before=float(before), after=float(after))
        row.update(extra or {})
        led["before_after"].append(row)

    if mode == "cost_layer":
        # 1. generators / links / stores inherited from the electric base
        for (comp, car), row in ELECTRIC_BASE_ROWS.items():
            df = n.df(comp); ext = "e_nom_extendable" if comp == "Store" else "p_nom_extendable"
            sel = df.index[(df.carrier == car) & df[ext]]
            v = _fixed(costs, row)
            for name in sel:
                record(comp, name, car, df.at[name, "capital_cost"], v, dict(cost_row=row, country=(str(df.at[name, "country"]) if "country" in df else "")))
            n.df(comp).loc[sel, "capital_cost"] = v
        # 2. offshore wind with the connection cost per node x class
        RN = R.get("renewable") or {}
        dp = Path(repo) / RN["offwind_distance_table"]
        dist = pd.read_csv(dp).set_index(["tech", "node", "cls"])
        led["offwind_distance_table"] = dict(file=str(RN["offwind_distance_table"]), sha256=hashlib.sha256(dp.read_bytes()).hexdigest())
        g = n.generators; missing = []
        for car in ("offwind-ac", "offwind-dc"):
            base = _fixed(costs, "offwind") + _fixed(costs, f"{car}-station")
            sub, und = _fixed(costs, f"{car}-connection-submarine"), _fixed(costs, f"{car}-connection-underground")
            for name in g.index[(g.carrier == car) & g.p_nom_extendable]:
                node = str(g.at[name, "bus"]); cls = _class_of(name)
                if (car, node, cls) not in dist.index:
                    missing.append(dict(generator=str(name), tech=car, node=node, cls=cls)); continue
                d = dist.loc[(car, node, cls)]
                conn = float(d.line_length_factor) * (float(d.average_distance_km) * sub + float(d.landfall_km) * und)
                before = float(g.at[name, "capital_cost"]); after = base + conn
                n.generators.at[name, "capital_cost"] = after
                record("Generator", name, car, before, after, dict(country=str(g.at[name, "country"]), node=node, cls=cls, distance_km=float(d.average_distance_km),
                                                                    landfall_km=float(d.landfall_km), connection_eur_per_mw_a=conn, connection_share=conn / after))
        led["offwind_missing_distance"] = missing
        if missing:
            raise ValueError(f"offshore wind generators without a connection distance: {missing[:6]} ({len(missing)})")
        # 3. AC lines and DC links with the corridor subsea share
        hv_o, hv_s = _fixed(costs, "HVAC overhead"), _fixed(costs, "HVAC submarine")
        dc_o, dc_s, inv = _fixed(costs, "HVDC overhead"), _fixed(costs, "HVDC submarine"), _fixed(costs, "HVDC inverter pair")
        if "underwater_fraction" not in n.lines:
            n.lines["underwater_fraction"] = 0.0
        for name, z in n.lines[n.lines.s_nom_extendable].iterrows():
            s = share(z.bus0, z.bus1); after = float(z.length) * ((1 - s) * hv_o + s * hv_s)
            record("Line", name, "AC", z.capital_cost, after, dict(length_km=float(z.length), subsea_share=s, border_class=str(z.get("border_class", ""))))
            n.lines.at[name, "capital_cost"] = after; n.lines.at[name, "underwater_fraction"] = s
        for name, z in n.links[(n.links.carrier == "DC") & n.links.p_nom_extendable].iterrows():
            s = share(z.bus0, z.bus1); after = float(z.length) * ((1 - s) * dc_o + s * dc_s) + inv
            record("Link", name, "DC", z.capital_cost, after, dict(length_km=float(z.length), subsea_share=s, border_class=str(z.get("border_class", ""))))
            n.links.at[name, "capital_cost"] = after; n.links.at[name, "underwater_fraction"] = s
    # 4. pipelines (priced from the cost layer since S2/S3; the subsea share applies in both modes)
    for car, (on_row, sub_row) in PIPELINE_ROWS.items():
        on, sub = _fixed(costs, on_row), _fixed(costs, sub_row)
        for name, z in n.links[(n.links.carrier == car) & n.links.p_nom_extendable].iterrows():
            s = share(z.bus0, z.bus1); after = float(z.length) * ((1 - s) * on + s * sub)
            record("Link", name, car, z.capital_cost, after, dict(length_km=float(z.length), subsea_share=s, kind=str(z.get("gas_pipeline_kind", "") or ""),
                                                                    border_class=str(z.get("border_class", ""))))
            n.links.at[name, "capital_cost"] = after; n.links.at[name, "underwater_fraction"] = s
    ba = pd.DataFrame(led["before_after"])
    led["summary"] = ({f"{c}:{k}": dict(n=int(len(x)), before_mean=float(x.before.mean()), after_mean=float(x.after.mean())) for (c, k), x in ba.groupby(["component", "carrier"])}
                      if len(ba) else {})
    n.meta["research_cost_layer_s4c1"] = {k: v for k, v in led.items() if k != "before_after"}
    return led


HYDRO_MODES = ("national_observed", "national_observed_runoff_shares", "frozen_base")


def apply_hydro_inflow_normalization(n, cfg, repo) -> dict:
    """S4C-2 (decision 83): renormalise the national inflow of the existing hydro stock and re-derive the new-build proxies (see module doc)."""
    H = (cfg["research"].get("hydro") or {})
    mode = str(H.get("inflow_normalization", "frozen_base"))
    if mode not in HYDRO_MODES:
        raise ValueError("Unknown research.hydro.inflow_normalization " + mode)
    led = dict(mode=mode, countries={}, units=[], new_build=[])
    if mode == "frozen_base":
        n.meta["research_hydro_inflow"] = led
        return led
    tp = Path(repo) / H["target_table"]
    tgt = pd.read_csv(tp, keep_default_na=False)
    tgt = {r.country: float(r.target_mwh) for r in tgt.itertuples() if r.status == "REGISTERED"}
    led["target_table"] = dict(file=str(H["target_table"]), sha256=hashlib.sha256(tp.read_bytes()).hexdigest())
    w = n.snapshot_weightings.generators.values
    su, g = n.storage_units, n.generators
    inf, pmax = n.storage_units_t.inflow, n.generators_t.p_max_pu
    res = su.index[(su.carrier == "hydro existing")]; ror = g.index[(g.carrier == "ror existing")]
    # per-unit hourly energy series (MW) and annual energy (MWh)
    series = {}
    for name in res:
        series[name] = (inf[name].values.astype(float) if name in inf else np.zeros(len(n.snapshots)), "reservoir", float(su.at[name, "p_nom"]), str(su.at[name, "country"]))
    for name in ror:
        s = pmax[name].values.astype(float) if name in pmax else np.full(len(n.snapshots), float(g.at[name, "p_max_pu"]))
        series[name] = (s * float(g.at[name, "p_nom"]), "ror", float(g.at[name, "p_nom"]), str(g.at[name, "country"]))
    by_c = {}
    for name, (s, kind, cap, c) in series.items():
        by_c.setdefault(c, []).append(name)
    new_series = {}
    for c, names in sorted(by_c.items()):
        caps = np.array([series[x][2] for x in names]); energy = np.array([float((series[x][0] * w).sum()) for x in names])
        if c not in tgt:
            raise ValueError(f"no national hydro target for {c} (stock {caps.sum():.0f} MW)")
        T = tgt[c]
        if mode == "national_observed":
            target_u = T * caps / caps.sum()
        else:
            target_u = energy * (T / energy.sum())
        for kind in ("reservoir", "ror"):
            idx = [i for i, x in enumerate(names) if series[x][1] == kind]
            shape_kind = None
            if idx:
                tot = sum(series[names[i]][0] for i in idx); e_tot = float((tot * w).sum())
                shape_kind = tot / e_tot if e_tot > 0 else None
            for i in idx:
                x = names[i]; s = series[x][0]; e = energy[i]
                if e > 0:
                    new = s * (target_u[i] / e); basis = "own shape"
                else:
                    if shape_kind is None or target_u[i] == 0:
                        new = np.zeros_like(s); basis = "zero (no shape in the country)"
                    else:
                        new = shape_kind * target_u[i]; basis = f"country {kind} capacity-weighted shape (unit had no inflow)"
                lost = 0.0
                if kind == "ror":
                    pu = new / series[x][2]; clipped = np.minimum(pu, 1.0); lost = float(((pu - clipped) * series[x][2] * w).sum()); new = clipped * series[x][2]
                new_series[x] = new
                led["units"].append(dict(name=x, country=c, kind=kind, node=(str(su.at[x, "bus"]) if kind == "reservoir" else str(g.at[x, "bus"])), p_nom=series[x][2],
                                         energy_before_mwh=e, energy_after_mwh=float((new * w).sum()), cf_before=e / (series[x][2] * 8760) if series[x][2] else np.nan,
                                         cf_after=float((new * w).sum()) / (series[x][2] * 8760) if series[x][2] else np.nan, shape_basis=basis, ror_clipped_mwh=lost))
        after = sum(float((new_series[x] * w).sum()) for x in names)
        led["countries"][c] = dict(target_mwh=T, stock_mw=float(caps.sum()), energy_before_mwh=float(energy.sum()), energy_after_mwh=after, cf_before=float(energy.sum() / (caps.sum() * 8760)),
                                   cf_after=float(after / (caps.sum() * 8760)), ror_clipped_mwh=float(sum(u["ror_clipped_mwh"] for u in led["units"] if u["country"] == c)))
    for x, s in new_series.items():
        if x in res:
            n.storage_units_t.inflow[x] = s
        else:
            n.generators_t.p_max_pu[x] = s / float(g.at[x, "p_nom"])
    # new-build candidates: capacity-weighted per-MW inflow of the corrected same-country stock
    def per_mw(c, kind):
        for scope, pick in [("country " + kind, lambda nm: series[nm][3] == c and series[nm][1] == kind), ("country all kinds", lambda nm: series[nm][3] == c),
                            ("ASEAN " + kind, lambda nm: series[nm][1] == kind)]:
            sel = [nm for nm in new_series if pick(nm)]
            cap = sum(series[nm][2] for nm in sel)
            if sel and cap > 0:
                return sum(new_series[nm] for nm in sel) / cap, scope
        raise ValueError(f"no stock to derive the new-build {kind} inflow for {c}")
    tie = set(n.meta.get("research_new_hydro_inflow_tie", []))
    for name in su.index[(su.carrier == "hydro") & su.p_nom_extendable & (su.p_nom_max > 0)]:
        c = str(su.at[name, "country"]); r, scope = per_mw(c, "reservoir"); cap = float(su.at[name, "p_nom_max"])
        old = float((inf[name] * w).sum()) if name in inf else 0.0
        n.storage_units_t.inflow[name] = r * cap
        led["new_build"].append(dict(name=name, kind="reservoir", country=c, p_nom_max=cap, scope=scope, cf_before=old / (cap * 8760), cf_after=float((r * w).sum()) / 8760, in_inflow_tie=name in tie))
    for name in g.index[(g.carrier == "ror") & g.p_nom_extendable & (g.p_nom_max > 0)]:
        c = str(g.at[name, "country"]); r, scope = per_mw(c, "ror"); cap = float(g.at[name, "p_nom_max"])
        old = float((pmax[name] * w).sum()) / 8760 if name in pmax else float(g.at[name, "p_max_pu"])
        n.generators_t.p_max_pu[name] = np.minimum(r, 1.0)
        led["new_build"].append(dict(name=name, kind="ror", country=c, p_nom_max=cap, scope=scope, cf_before=old, cf_after=float((np.minimum(r, 1.0) * w).sum()) / 8760))
    led["totals"] = dict(stock_mw=float(sum(v[2] for v in series.values())), energy_before_twh=sum(v["energy_before_mwh"] for v in led["countries"].values()) / 1e6,
                         energy_after_twh=sum(v["energy_after_mwh"] for v in led["countries"].values()) / 1e6, target_twh=sum(v["target_mwh"] for v in led["countries"].values()) / 1e6,
                         ror_clipped_twh=sum(v["ror_clipped_mwh"] for v in led["countries"].values()) / 1e6,
                         anomalous_units_cf_gt_1_before=[u["name"] for u in led["units"] if u["cf_before"] > 1])
    n.meta["research_hydro_inflow"] = led
    return led
