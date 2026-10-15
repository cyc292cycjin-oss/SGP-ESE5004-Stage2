"""S3 model layers on top of the S2 scenario network.

S3-1 add_gas_network: node gas buses keep the PyPSA-Eur gas_network structure (one gas bus per node; every gas user is already on it).
  * the per-node unlimited external gas generators of the S1/S2 carrier recipe are removed;
  * domestic production: one wellhead Generator per node (annual cap = country UNSD 2019 production x node load share, enforced by the
    ResearchImportAnnual hook via n.meta['external_annual_caps']; price = import price, decision 43) delivering to the node gas bus
    through a Link whose second output port books the fugitive CO2 (S2-0 factor) in the country atmosphere;
  * pipelines: one bidirectional candidate per electricity connection (same topology as H2/CO2, R5), technology-data CH4 (g) pipeline /
    submarine costs; the 2025 cross-border stock (GEM, batch 9) is added with p_nom_min = capacity (decision 15), extendable at the
    candidate cost; cross-border pipelines are removed by research.cross_border.gas = false (apply_cross_border_switches_s2);
  * LNG: one import Generator per terminal node (D1 registry), p_nom = existing (operating + construction) capacity, p_nom_max = 2.5 x,
    proposed-only sites p_nom 0 / p_nom_max = proposed capacity; price = WEO NZE Japan LNG + regasification adder (DATA_PENDING -> 0).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from carrier_architecture import atmosphere_bus
from s2_costs import cost
from s2_layers import add_bus, add_link, country_of, ensure_carrier

HOURS = 8760.0


def _haversine(x0, y0, x1, y1):
    la1, lo1, la2, lo2 = map(np.radians, [y0, x0, y1, x1])
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return float(2 * 6371.0 * np.arcsin(np.sqrt(h)))


def electricity_load_shares(n, nodes):
    """{country: {node: share}} from the electricity loads attached to the AC nodes (static p_set + time series mean)."""
    ac = [b for b in nodes if n.buses.at[b, "carrier"] == "AC"]
    loads = n.loads[n.loads.bus.isin(ac)]
    tot = loads.p_set.astype(float).copy()
    ts = [c for c in n.loads_t.p_set.columns if c in loads.index]
    if ts:
        tot.loc[ts] = tot.loc[ts] + n.loads_t.p_set[ts].mean()
    by_bus = tot.groupby(loads.bus).sum()
    out = {}
    for node in ac:
        c = country_of(n, node)
        out.setdefault(c, {})[node] = float(by_bus.get(node, 0.0))
    for c, d in out.items():
        s = sum(d.values())
        out[c] = {k: (v / s if s > 0 else 1.0 / len(d)) for k, v in d.items()}
    return out


def add_gas_network(n, costs, cfg, repo, registry: pd.DataFrame, nodes, candidates: pd.DataFrame):
    G = cfg["research"]["s3"]["gas"]
    led = {}
    price = float(registry.loc["fuel_price_gas_NZE_2050_main", "value"])
    adder = float(G.get("lng_regasification_adder_eur_per_mwh", 0.0))
    # 1. remove the unlimited per-node external gas supply of the carrier recipe
    ext = list(n.generators.index[(n.generators.carrier == "gas") & (n.generators.research_role == "EXTERNAL_SUPPLY")])
    n.mremove("Generator", ext)
    led["external_gas_generators_removed"] = len(ext)
    # 2. domestic production (decision 43)
    caps = pd.read_csv(repo / G["production_caps"], keep_default_na=False)
    shares = electricity_load_shares(n, nodes)
    ensure_carrier(n, "gas wellhead"); ensure_carrier(n, "gas production"); ensure_carrier(n, "gas production delivery")
    n.meta.setdefault("external_annual_caps", {})
    prod_led = {}
    for r in caps.itertuples():
        cap = float(r.cap_mwh_per_year); c = r.country
        fid = r.fugitive_factor_id
        if cap <= 0 or c not in shares:
            prod_led[c] = dict(cap_mwh=cap, nodes=0, fugitive_t_per_mwh=None, note="no domestic production (cap 0) -> no wellhead generators; fugitive row not applicable")
            continue
        if fid not in registry.index or not str(registry.loc[fid, "unit"]).startswith("tCO2/MWh"):
            raise ValueError(f"fugitive factor {fid} missing or not per MWh of production")
        fug = float(registry.loc[fid, "value"])
        k = 0
        for node, s in shares[c].items():
            if s <= 0:
                continue
            wb = f"{node} gas wellhead"
            add_bus(n, wb, "gas wellhead", c, node)
            gname = f"{node} gas production"
            n.add("Generator", gname, bus=wb, carrier="gas production", p_nom_extendable=True, p_nom=0.0, capital_cost=0.0, marginal_cost=price, p_min_pu=0.0)
            n.generators.loc[gname, ["country", "research_role"]] = [c, "DOMESTIC_PRODUCTION"]
            n.meta["external_annual_caps"][gname] = cap * s
            add_link(n, f"{node} gas production delivery", c, "gas production delivery", [wb, f"{node} gas", atmosphere_bus(c)], [1.0, fug], role="SUPPLY",
                     extra=dict(fugitive_factor_id=fid))
            k += 1
        prod_led[c] = dict(cap_mwh=cap, nodes=k, fugitive_t_per_mwh=fug, allocation=str(r.node_allocation))
    led["production"] = prod_led
    # 3. pipelines
    on, sub = cost(costs, "CH4 (g) pipeline", "fixed"), cost(costs, "CH4 (g) submarine pipeline", "fixed")
    life = cost(costs, "CH4 (g) pipeline", "lifetime")
    ensure_carrier(n, "gas pipeline")
    added = 0
    for _, r in candidates.iterrows():
        a, b, L, u = r.a, r.b, float(r.length_km), float(r.underwater_fraction)
        add_link(n, f"gas pipeline {a} -> {b}", country_of(n, a), "gas pipeline", [f"{a} gas", f"{b} gas"], [1.0], p_min_pu=-1.0,
                 capital_cost=L * ((1 - u) * on + u * sub), lifetime=life, length=L, role="TRANSPORT", extra={"underwater_fraction": u, "gas_pipeline_kind": "candidate"})
        added += 1
    # connectivity upgrade (PyPSA-Eur prepare_sector_network.py lines 1968-2010, config gas_network_connectivity_upgrade: 1, line 768): every gas bus
    # whose node carries no pipeline candidate (DC converter nodes outside the AC topology) gets one bidirectional candidate to the nearest gas bus
    # of the same country (great-circle x the candidate length factor), so that the gas graph is connected like the H2/CO2 graphs.
    touched = set(candidates.a) | set(candidates.b)
    lf = float(cfg["research"]["s2"].get("pipelines", {}).get("length_factor", 1.25))
    upgrades = []
    gas_nodes = [b[:-4] for b in n.buses.index if n.buses.at[b, "carrier"] == "gas" and b.endswith(" gas") and b[:-4] in n.buses.index]   # AC nodes and DC converter nodes with a gas bus
    for node in gas_nodes:
        if node in touched:
            continue
        c = country_of(n, node)
        others = [m for m in gas_nodes if m != node and m in touched and country_of(n, m) == c]
        if not others:
            continue
        x0, y0 = float(n.buses.at[node, "x"]), float(n.buses.at[node, "y"])
        dist = {m: _haversine(x0, y0, float(n.buses.at[m, "x"]), float(n.buses.at[m, "y"])) for m in others}
        m = min(dist, key=dist.get); L = dist[m] * lf
        add_link(n, f"gas pipeline new {node} <-> {m}", c, "gas pipeline", [f"{node} gas", f"{m} gas"], [1.0], p_min_pu=-1.0, capital_cost=L * on, lifetime=life, length=L,
                 role="TRANSPORT", extra={"underwater_fraction": 0.0, "gas_pipeline_kind": "connectivity_upgrade"})
        upgrades.append(dict(node=node, to=m, great_circle_km=dist[m], length_km=L))
    ex = pd.read_csv(repo / G["existing_cross_border"], keep_default_na=False)
    stock, pending = [], []
    for r in ex.itertuples():
        if str(r.capacity_mw_ncv) == "":
            pending.append(dict(pipeline=r.pipeline, from_node=r.from_node, to_node=r.to_node, status="DATA_PENDING: capacity not given by GEM; only the corridor candidate exists"))
            continue
        cap = float(r.capacity_mw_ncv); L = float(r.length_km) if str(r.length_km) != "" else 0.0
        name = f"gas pipeline existing {r.pipeline}"
        add_link(n, name, country_of(n, r.from_node), "gas pipeline", [f"{r.from_node} gas", f"{r.to_node} gas"], [1.0], p_min_pu=(-1.0 if r.direction == "bidirectional" else 0.0),
                 capital_cost=L * on, lifetime=life, length=L, role="TRANSPORT", extra={"underwater_fraction": 0.0, "gas_pipeline_kind": "existing_2025", "gem_project_id": str(r.gem_project_id)})
        n.links.loc[name, ["p_nom", "p_nom_min"]] = [cap, cap]
        stock.append(dict(pipeline=r.pipeline, link=name, from_node=r.from_node, to_node=r.to_node, capacity_mw_ncv=cap, direction=r.direction, length_km=L))
    led["pipelines"] = dict(candidates=added, connectivity_upgrades=upgrades, cost_rows=dict(onshore="CH4 (g) pipeline", submarine="CH4 (g) submarine pipeline", fixed_onshore=on, fixed_submarine=sub, lifetime=life),
                            existing_2025=stock, existing_pending=pending, note="existing links are one-way in the registered export direction (TTM bidirectional); candidates bidirectional")
    # 4. LNG terminals (decisions 17/19)
    lng = pd.read_csv(repo / G["lng_terminals"], keep_default_na=False)
    lng["cap"] = pd.to_numeric(lng.capacity_mwh_per_year, errors="coerce").fillna(0.0)
    factor = float(G.get("lng_cap_factor", 2.5))
    ensure_carrier(n, "LNG import")
    terms = {}
    for node, g in lng.groupby("node"):
        if not node or f"{node} gas" not in n.buses.index:
            continue
        existing = float(g[g.status.isin(["operating", "construction"])].cap.sum()) / HOURS
        proposed = float(g[g.status == "proposed"].cap.sum()) / HOURS
        missing = int((g.cap <= 0).sum())
        p_max = factor * existing if existing > 0 else proposed
        if p_max <= 0:
            terms[node] = dict(existing_mw=0.0, proposed_mw=0.0, p_nom_max_mw=0.0, units_missing_capacity=missing, skipped="no capacity data")
            continue
        name = f"{node} LNG import"
        c = country_of(n, node)
        n.add("Generator", name, bus=f"{node} gas", carrier="LNG import", p_nom=existing, p_nom_min=existing, p_nom_extendable=True, p_nom_max=p_max, capital_cost=0.0, marginal_cost=price + adder)
        n.generators.loc[name, ["country", "research_role"]] = [c, "EXTERNAL_SUPPLY"]
        terms[node] = dict(country=c, existing_mw=existing, proposed_mw=proposed, p_nom_max_mw=p_max, units_missing_capacity=missing, terminals=";".join(g.terminal))
    led["lng"] = dict(price_eur_per_mwh=price, regasification_adder=adder, adder_status="DATA_PENDING (0 used)", cap_factor=factor, terminals=terms)
    n.meta["research_gas_network"] = led
    return led


def add_imports(n, costs, cfg, repo, registry: pd.DataFrame, nodes):
    """S3-2 (decisions 17/18/64): extra-ASEAN imports.
    * Oil: one regional pool bus (ASEAN oil, country tag ASEAN -> not a cross-border port, scenario_network.tag_cross_border) with the external
      import generator at the WEO NZE crude price; the 100 per-node external oil generators are removed and every node oil bus joins the pool
      through a free bidirectional distribution link (decision 18: oil is not network-constrained). Coal/lignite keep the per-node S2 pools.
    * Green carriers (Neumann et al. 2025 base x 1.20, research_inputs/imports_v5/IMPORT_PRICES_2050.csv): ammonia and methanol on new regional
      buses (ASEAN ammonia / ASEAN methanol; demands connect in S3-3/S3-4), Fischer-Tropsch fuel on the regional non-fossil oil bus (consumers
      connect in S3-5), liquid hydrogen at the LNG terminal nodes (node H2 bus, p_nom_max = LNG terminal capacity x 2.5 as PyPSA-Eur maps
      shipping-lh2 to LNG entry points, terminal capital cost 7018 x 1.2 EUR/MW/a, import branch 5a87cedd lines 4540/4560-4563/4651).
    * Imports only (generators), same prices in both scenarios, no CO2 port (decision 64); price_sensitivity switch +-20 %.
    """
    I = cfg["research"]["s3"]["imports"]
    sens = float(I.get("price_sensitivity", 0.0))
    prices = pd.read_csv(repo / I["price_table"], keep_default_na=False)
    prices = prices[prices.status == "REGISTERED"].set_index("carrier")
    led = dict(price_sensitivity=sens, markup=float(prices.markup.iloc[0]))

    def pool_bus(name, carrier):
        if name not in n.buses.index:
            add_bus(n, name, carrier, "ASEAN", "")   # country tag ASEAN: excluded from cross-border tagging (scenario_network.tag_cross_border)
        return name

    def import_gen(name, bus, carrier, price, country="ASEAN", **kw):
        ensure_carrier(n, carrier)
        n.add("Generator", name, bus=bus, carrier=carrier, p_nom_extendable=True, p_nom=0.0, marginal_cost=float(price), capital_cost=float(kw.pop("capital_cost", 0.0)), **kw)
        n.generators.loc[name, ["country", "research_role"]] = [country, "EXTERNAL_SUPPLY"]
        return name

    # 1. oil regional pool
    oil_price = float(registry.loc["fuel_price_oil_NZE_2050_main", "value"])
    pool = pool_bus("ASEAN oil", "oil")
    ext = list(n.generators.index[(n.generators.carrier == "oil") & (n.generators.research_role == "EXTERNAL_SUPPLY")])
    n.mremove("Generator", ext)
    import_gen("ASEAN oil import", pool, "oil import", oil_price)
    ensure_carrier(n, "oil pool")
    k = 0
    for b in n.buses.index[n.buses.carrier == "oil"]:
        if b == pool or not b.endswith(" oil"):
            continue
        node = b[:-4]
        add_link(n, f"oil pool {node}", country_of(n, node) if node in n.buses.index else "ASEAN", "oil pool", [b, pool], [1.0], p_min_pu=-1.0, role="TRANSPORT",
                 extra={"gas_pipeline_kind": "", "pool": "ASEAN oil"})
        k += 1
    led["oil"] = dict(pool=pool, external_removed=len(ext), distribution_links=k, price=oil_price, direction="bidirectional (node <-> pool)")
    # 2. coal / lignite unchanged (per node, S2 structure)
    led["coal"] = dict(structure="per_node_unchanged", generators=int(((n.generators.carrier.isin(["coal", "lignite"])) & (n.generators.research_role == "EXTERNAL_SUPPLY")).sum()))
    # 3. green carriers on regional buses
    f = 1.0 + sens
    green = {}
    for carrier, bus_name, bus_carrier, gcar in [("ammonia", "ASEAN ammonia", "ammonia", "ammonia import"), ("methanol", "ASEAN methanol", "methanol", "methanol import"),
                                                   ("oil non-fossil", "ASEAN oil non-fossil", "oil non-fossil", "FT fuel import")]:
        p = float(prices.at[carrier, "applied_eur2020_per_mwh"]) * f
        pool_bus(bus_name, bus_carrier)
        import_gen(f"{bus_name} import", bus_name, gcar, p)
        green[carrier] = dict(bus=bus_name, generator=f"{bus_name} import", price_applied=p, base=float(prices.at[carrier, "base_eur2020_per_mwh"]), esc=prices.at[carrier, "esc"])
    # 4. liquid hydrogen by ship at the LNG terminal nodes
    h2p = float(prices.at["hydrogen", "applied_eur2020_per_mwh"]) * f
    term_cost = float(I.get("h2_terminal_capital_cost_eur_per_mw_a", 7018.0 * 1.2))
    lng = n.generators[n.generators.carrier == "LNG import"]
    h2 = {}
    for g, z in lng.iterrows():
        node = str(z.bus)[:-4]
        cap = float(z.p_nom_max)
        if cap <= 0 or f"{node} H2" not in n.buses.index:
            continue
        name = import_gen(f"{node} H2 import", f"{node} H2", "H2 import", h2p, country=country_of(n, node), p_nom_max=cap, capital_cost=term_cost)
        h2[node] = dict(generator=name, p_nom_max=cap, lng_generator=g)
    green["hydrogen"] = dict(nodes=len(h2), price_applied=h2p, base=float(prices.at["hydrogen", "base_eur2020_per_mwh"]), terminal_capital_cost=term_cost, terminals=h2)
    led["green"] = green
    n.meta["research_imports"] = led
    return led


def add_ammonia_methanol(n, costs, cfg, repo, registry: pd.DataFrame, nodes):
    """S3-3 (decision 44): single regional ammonia and methanol buses with the PyPSA-Eur v2025.07.0 default conversions.
    * Haber-Bosch per node (add_ammonia, prepare_sector_network.py lines 1424-1440): bus0 electricity, bus1 ASEAN ammonia, bus2 node H2;
      efficiency 1/electricity-input, efficiency2 = -hydrogen-input/electricity-input, capital cost / electricity-input (technology-data Haber-Bosch).
    * Ammonia cracker per node (lines 1441-1452): ASEAN ammonia -> node H2, efficiency 1/MWh_NH3_per_MWh_H2_cracker (1.46), cost per MW_H2 / 1.46.
    * Ammonia store on the regional bus (lines 1453-1462, NH3 (l) storage tank incl. liquefaction); methanol store (add_carrier_buses, General
      liquid hydrocarbon storage (product)).
    * Methanolisation per node (lines 4628-4645): bus0 node H2, bus1 ASEAN methanol, bus2 electricity, bus3 node co2 stored (captured CO2);
      efficiency MWh_MeOH_per_MWh_H2, efficiency2 = -MWh_MeOH_per_MWh_H2 / MWh_MeOH_per_MWh_e, efficiency3 = -MWh_MeOH_per_MWh_H2 / MWh_MeOH_per_tCO2;
      p_min_pu = min_part_load_methanolisation (config line 736); capital cost x MWh_MeOH_per_MWh_H2 (per MW_H2).
    * PyPSA-Eur defaults also switch on biomass-to-methanol (config biomass_to_methanol: true, add_biomass_to_methanol lines 983-1002: country
      solid-biomass pool -> ASEAN methanol, atmosphere port -EF_methanol x efficiency, i.e. the fuel carbon is credited at production like BtL)
      and the methanol OCGT (methanol_to_power.ocgt: true, add_methanol_to_power; ASEAN methanol -> node electricity, +carbondioxide-input to the
      node country's atmosphere). Not built: methanol CCGT / CCGT CC / Allam (default false), methanol reforming (false), waste-heat use
      (no district-heat buses in this model), relocation options.
    """
    A = cfg["research"]["s3"]["ammonia_methanol"]
    meoh_per_h2, meoh_per_tco2, meoh_per_e = float(A["MWh_MeOH_per_MWh_H2"]), float(A["MWh_MeOH_per_tCO2"]), float(A["MWh_MeOH_per_MWh_e"])
    cracker_in = float(A["MWh_NH3_per_MWh_H2_cracker"]); min_pl = float(A["min_part_load_methanolisation"])
    nh3 = add_bus(n, "ASEAN ammonia", "ammonia", "ASEAN", ""); meoh = add_bus(n, "ASEAN methanol", "methanol", "ASEAN", "")
    led = dict(buses=[nh3, meoh], components={})
    # stores on the regional buses
    st_nh3 = "NH3 (l) storage tank incl. liquefaction"
    ensure_carrier(n, "ammonia store"); ensure_carrier(n, "methanol store")
    n.add("Store", "ASEAN ammonia store", bus=nh3, carrier="ammonia store", e_nom_extendable=True, e_cyclic=True, capital_cost=cost(costs, st_nh3, "fixed"), lifetime=cost(costs, st_nh3, "lifetime"))
    n.add("Store", "ASEAN methanol store", bus=meoh, carrier="methanol store", e_nom_extendable=True, e_cyclic=True, capital_cost=cost(costs, "General liquid hydrocarbon storage (product)", "fixed"),
          lifetime=cost(costs, "General liquid hydrocarbon storage (product)", "lifetime"))
    for s in ["ASEAN ammonia store", "ASEAN methanol store"]:
        n.stores.loc[s, ["country", "research_role"]] = ["ASEAN", "REGIONAL_STORE"]
    hb_el, hb_h2 = cost(costs, "Haber-Bosch", "electricity-input"), cost(costs, "Haber-Bosch", "hydrogen-input")
    hb_fixed, hb_vom, hb_life = cost(costs, "Haber-Bosch", "fixed"), cost(costs, "Haber-Bosch", "VOM"), cost(costs, "Haber-Bosch", "lifetime")
    cr_fixed, cr_life = cost(costs, "Ammonia cracker", "fixed"), cost(costs, "Ammonia cracker", "lifetime")
    me_fixed, me_vom, me_life = cost(costs, "methanolisation", "fixed"), cost(costs, "methanolisation", "VOM"), cost(costs, "methanolisation", "lifetime")
    ef_meoh = cost(costs, "methanol", "CO2 intensity")
    btm = A.get("biomass_to_methanol", True); ocgt = A.get("methanol_to_power_ocgt", True)
    btm_eff, btm_fixed, btm_vom, btm_life = (cost(costs, "biomass-to-methanol", k) for k in ["efficiency", "fixed", "VOM", "lifetime"])
    oc_eff, oc_fixed, oc_vom, oc_life = (cost(costs, "OCGT", k) for k in ["efficiency", "fixed", "VOM", "lifetime"])
    counts = dict(haber_bosch=0, ammonia_cracker=0, methanolisation=0, biomass_to_methanol=0, methanol_ocgt=0)
    for node in nodes:
        c = country_of(n, node); atmo = atmosphere_bus(c); h2 = f"{node} H2"; co2s = f"{node} co2 stored"
        if h2 not in n.buses.index:
            continue
        add_link(n, f"{node} Haber-Bosch", c, "Haber-Bosch", [node, nh3, h2], [1.0 / hb_el, -hb_h2 / hb_el], capital_cost=hb_fixed / hb_el, marginal_cost=hb_vom / hb_el, lifetime=hb_life)
        counts["haber_bosch"] += 1
        add_link(n, f"{node} ammonia cracker", c, "ammonia cracker", [nh3, h2], [1.0 / cracker_in], capital_cost=cr_fixed / cracker_in, lifetime=cr_life)
        counts["ammonia_cracker"] += 1
        if co2s in n.buses.index:
            add_link(n, f"{node} methanolisation", c, "methanolisation", [h2, meoh, node, co2s], [meoh_per_h2, -meoh_per_h2 / meoh_per_e, -meoh_per_h2 / meoh_per_tco2],
                     capital_cost=me_fixed * meoh_per_h2, marginal_cost=me_vom * meoh_per_h2, lifetime=me_life, p_min_pu=min_pl,
                     extra={"carbon_rule": "CO2 taken from the node captured-CO2 buffer; methanol carbon released at use (producer credit until S3-5)"})
            counts["methanolisation"] += 1
        bio = f"solid biomass {c}"
        if btm and bio in n.buses.index:
            add_link(n, f"{node} biomass-to-methanol", c, "biomass-to-methanol", [bio, meoh, atmo], [btm_eff, -ef_meoh * btm_eff], capital_cost=btm_fixed / btm_eff, marginal_cost=btm_vom / btm_eff, lifetime=btm_life,
                     extra={"carbon_rule": "fuel carbon credited at production (-EF_methanol x efficiency, PyPSA-Eur add_biomass_to_methanol), released at use"})
            counts["biomass_to_methanol"] += 1
        if ocgt:
            add_link(n, f"{node} OCGT methanol", c, "OCGT methanol", [meoh, node, atmo], [oc_eff, ef_meoh], capital_cost=oc_fixed * oc_eff, marginal_cost=oc_vom * oc_eff, lifetime=oc_life)
            counts["methanol_ocgt"] += 1
    led["components"] = counts
    led["parameters"] = dict(MWh_MeOH_per_MWh_H2=meoh_per_h2, MWh_MeOH_per_tCO2=meoh_per_tco2, MWh_MeOH_per_MWh_e=meoh_per_e, MWh_NH3_per_MWh_H2_cracker=cracker_in, min_part_load_methanolisation=min_pl,
                             haber_bosch_electricity_input=hb_el, haber_bosch_hydrogen_input=hb_h2, methanol_co2_intensity=ef_meoh, biomass_to_methanol=bool(btm), methanol_ocgt=bool(ocgt))
    n.meta["research_ammonia_methanol"] = led
    return led
