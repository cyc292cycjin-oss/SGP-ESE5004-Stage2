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
