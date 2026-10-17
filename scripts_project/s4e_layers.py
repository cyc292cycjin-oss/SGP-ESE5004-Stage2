"""S4E model layers (S4E instruction v1, 2026-10-17; decisions 94-95).

S4E-1 (decision 94, implementing decision 15): research.corridors.adjacency_completion = on (main) | off (default when absent: the original
corridor table). With on, the corridor table is research.corridors.corridors_table_s4e1 (cross_border_corridors.csv + the S4E-1 candidates:
land-adjacent node pairs as AC lines, APG AIMS III cross-sea projects #4 / #7 / #16 as DC links; scripts_project/s4e_1_corridors.py) and the
domestic candidates of research.corridors.domestic_table_s4e1 (APG national projects #3 / #18a / #18b, DC links) are added in both scenarios.
Every candidate starts at capacity 0 and is extendable; the 2025 stock rows are unchanged. AC rows absent from the frozen base are added by
s2_layers.add_apg_corridor_lines (base conventions); DC rows by add_corridor_dc_links with the conventions of the frozen base's AC-to-AC DC link
(HVDC XLPE 1000, bidirectional, lossless as in the base); the decision-50 cost layer (S4C-1) prices both from length and subsea share
(research.corridors.subsea_table). H2 / CO2 / gas candidates follow the electricity topology (decision 59). The disconnected scenario removes
every cross-border line / link as before (apply_cross_border_switches_s2).

S4E-2 (decision 95, modifying the unit cost of decision 89):
  * extra_asean_unit_cost: research.co2.extra_asean_cost_basis = unified (main: one storage cost basis for all geological storage - the extra-ASEAN
    price = IEAGHG 2004 shipping chain at 4,500 km (registry co2_extra_asean_shipping_chain_4500km x conv_usd2004_to_eur2020 = 24.70 EUR2020/t) +
    research.s2.co2.sequestration_cost_eur_per_t, the same value as the national stores (PyPSA-Eur default 30 -> 54.70); the ZEP 2011 offshore
    saline aquifer Medium 16.05 EUR/t is the sensitivity override s2.co2.sequestration_cost_eur_per_t=16.0535, applied to every store) | s4c4
    (former 40.75 registry total; default when the key is absent). co2.extra_asean_cost_scale (+-50 %) multiplies the result.
  * lao_transit_legs: land leg of the Lao transit, research.co2.lao_transit_destination = nearest_coast (main) | existing_port (nearest sea port of
    the author WPI subset) and research.co2.lao_transit_mode = rail (main) | truck (Stolaroff 2021 Table 2); main = the registered
    co2_lao_transit_land_cost_<node>; the destination fixes the coastal node where the CO2 reaches the sea.
  * apply_lao_transit_shipping: research.co2.lao_transit_shipping = on (main) | off (default when absent): per LA node and per receiver of the
    shipping routes of that coastal node, one link '<node> co2 transit ship to <j>' (carrier 'CO2 transit ship', maritime trade) into
    'co2 sequestered <j>', marginal cost = land leg + ship leg (the coastal node's route, active distance mode); receiver storage on its store.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DC_TEMPLATE = "1076672675-1_0+4"   # frozen-base DC link between two AC buses (PH_Mindanao6 0 - PH_Visayas7 0)


def corridor_mode(cfg) -> str:
    v = (cfg["research"].get("corridors") or {}).get("adjacency_completion", "off")
    v = {True: "on", False: "off"}.get(v, v) if isinstance(v, bool) else str(v).lower()
    if v not in ("on", "off"):
        raise ValueError("Unknown research.corridors.adjacency_completion " + str(v))
    return v


def corridor_tables(cfg) -> tuple[str, str | None]:
    """(corridor table, domestic candidate table or None), paths relative to the repository."""
    R = cfg["research"]; C = R.get("corridors") or {}
    if corridor_mode(cfg) == "on":
        return str(C["corridors_table_s4e1"]), str(C["domestic_table_s4e1"])
    return str(R["existing_cross_border_electricity"]["corridors_file"]), None


def _dc_template(n):
    dc = n.links[n.links.carrier == "DC"]
    if DC_TEMPLATE in dc.index:
        return dc.loc[DC_TEMPLATE]
    return dc.iloc[0]


def _add_dc(n, name, bus0, bus1, length, cap, subsea, tmpl):
    cpk = float(tmpl.capital_cost) / float(tmpl.length)
    n.add("Link", name, bus0=bus0, bus1=bus1, carrier="DC", type=str(tmpl.get("type", "")), length=float(length), p_nom=float(cap), p_nom_min=float(cap),
          p_nom_extendable=True, p_min_pu=-1.0, efficiency=float(tmpl.efficiency), capital_cost=cpk * float(length), lifetime=float(tmpl.lifetime), build_year=0)
    if "underwater_fraction" in n.links.columns:
        n.links.at[name, "underwater_fraction"] = float(subsea)
    return dict(component=name, bus0=bus0, bus1=bus1, length_km=float(length), capacity_2025_mw=float(cap), subsea_share=float(subsea),
                placeholder_capital_cost_eur_per_mw_a=cpk * float(length), template_link=str(tmpl.name))


def add_corridor_dc_links(n, corridors: pd.DataFrame) -> list:
    """Corridor-table rows of type Link (carrier DC) absent from the network -> DC links (S4E-1 cross-sea candidates)."""
    tmpl = _dc_template(n); added = []
    for _, r in corridors.iterrows():
        if r.component_type != "Link" or str(r.component) in n.links.index:
            continue
        if str(r.carrier) != "DC":
            raise ValueError(f"corridor row {r.component}: only DC links can be added")
        added.append(_add_dc(n, str(r.component), r["from"], r["to"], r.length_km, r.capacity_2025_mw, r.subsea_share, tmpl) | dict(status=str(r.status)))
    n.meta["s4e_corridor_dc_additions"] = added
    return added


def _co2(cfg) -> dict:
    return cfg["research"].get("co2", {}) or {}


def extra_asean_cost_basis(cfg) -> str:
    v = str(_co2(cfg).get("extra_asean_cost_basis", "s4c4")).lower()
    if v not in ("unified", "s4c4"):
        raise ValueError("Unknown research.co2.extra_asean_cost_basis " + v)
    return v


def extra_asean_unit_cost(cfg, registry: pd.DataFrame) -> dict:
    """S4E-2 (95 a): extra-ASEAN unit cost before the +-50 % scale."""
    basis = extra_asean_cost_basis(cfg)
    if basis == "s4c4":
        return dict(basis=basis, price=float(registry.loc["co2_extra_asean_storage_cost", "value"]))
    ship = float(registry.loc["co2_extra_asean_shipping_chain_4500km", "value"]) * float(registry.loc["conv_usd2004_to_eur2020", "value"])
    store = float(cfg["research"]["s2"]["co2"]["sequestration_cost_eur_per_t"])
    return dict(basis=basis, price=ship + store, shipping_eur2020_per_t=ship, storage_eur2020_per_t=store)


def lao_transit_options(cfg) -> tuple[str, str]:
    d = str(_co2(cfg).get("lao_transit_destination", "nearest_coast")).lower(); m = str(_co2(cfg).get("lao_transit_mode", "rail")).lower()
    if d not in ("nearest_coast", "existing_port") or m not in ("rail", "truck"):
        raise ValueError(f"Unknown Lao transit option {d} / {m}")
    return d, m


def lao_transit_legs(cfg, registry: pd.DataFrame) -> dict:
    """node -> dict(land_cost, coastal_node, route_km, destination, mode, source)."""
    from s4d_layers import transit_cost_id
    dest, mode = lao_transit_options(cfg)
    t = pd.read_csv(ROOT / "research_inputs/co2_v5/LAO_TRANSIT_S4D1.csv").set_index("node")
    ports = pd.read_csv(ROOT / "research_inputs/co2_v5/PORTS_ASEAN_TO_NODES_S4D1.csv")
    rail, load, truck = (float(registry.loc[k, "value"]) for k in ("co2_land_transport_rail_unit_cost", "co2_land_transport_rail_loading_cost", "co2_land_transport_truck_unit_cost"))
    out = {}
    for node, r in t.iterrows():
        if dest == "nearest_coast":
            cnode, km, where = str(r.coastal_node_at_point).split("/")[0], float(r.route_km), f"coast ({r.coast_point_x}, {r.coast_point_y})"
        else:
            port = str(r.alt_sea_port).split(" (")[0]
            hit = ports[ports.port == port]
            if hit.empty:
                raise ValueError(f"port {port} of {node} not in PORTS_ASEAN_TO_NODES_S4D1.csv")
            cnode, km, where = str(hit.node.iloc[0]), float(r.alt_port_route_km), f"port {port}"
        if dest == "nearest_coast" and mode == "rail":
            row = registry.loc[transit_cost_id(node)]
            if row["status"] != "REGISTERED":
                raise ValueError(f"{transit_cost_id(node)} is {row['status']}")
            cost, src = float(row["value"]), transit_cost_id(node)
        else:
            cost = km * rail + load if mode == "rail" else km * truck
            src = f"{mode} unit cost x {km:.1f} km ({where})"
        out[node] = dict(land_cost=cost, coastal_node=cnode, route_km=km, destination=dest, mode=mode, source=src)
    return out


def lao_shipping_mode(cfg) -> str:
    v = _co2(cfg).get("lao_transit_shipping", "off")
    v = {True: "on", False: "off"}.get(v, v) if isinstance(v, bool) else str(v).lower()
    if v not in ("on", "off"):
        raise ValueError("Unknown research.co2.lao_transit_shipping " + str(v))
    return v


def apply_lao_transit_shipping(n, cfg, registry: pd.DataFrame) -> dict:
    """S4E-2 (95 c): see the module docstring. Requires the intra-ASEAN shipping routes and the Lao transit (S4D-1)."""
    from s2_layers import add_link
    from s4d_layers import TRANSIT_SHIP_CARRIER, ship_cost_function, shipping_mode
    mode = lao_shipping_mode(cfg); led = dict(mode=mode, links=0)
    if mode == "off":
        n.meta["research_lao_transit_shipping"] = led
        return led
    if shipping_mode(cfg) != "on":
        raise ValueError("research.co2.lao_transit_shipping = on requires research.co2.intra_asean_shipping = on")
    legs = lao_transit_legs(cfg, registry); ship = ship_cost_function(cfg, registry)
    routes = pd.read_csv(ROOT / str(_co2(cfg).get("ship_routes_table", "research_inputs/co2_v5/CO2_SHIP_ROUTES_S4D2.csv")))
    receivers = {str(c) for c in n.stores.country[n.stores.carrier == "co2 sequestered"]}
    years = float(cfg["research"]["s2"]["co2"]["storage_years"]); rows = []
    for node, g in sorted(legs.items()):
        if f"{node} co2 stored" not in n.buses.index:
            continue
        rr = routes[routes.origin == g["coastal_node"]]
        if rr.empty:
            raise ValueError(f"no shipping route from {g['coastal_node']} (Lao transit of {node})")
        for _, r in rr.sort_values("receiver").iterrows():
            if r.receiver not in receivers:
                continue
            cost = g["land_cost"] + ship(r)
            add_link(n, f"{node} co2 transit ship to {r.receiver}", "LA", TRANSIT_SHIP_CARRIER, [f"{node} co2 stored", f"co2 sequestered {r.receiver}"], [1.0], capital_cost=0.0,
                     marginal_cost=cost, lifetime=years, role="CO2_SHIPPING",
                     extra={"landing_node": r.landing, "via_coastal_node": g["coastal_node"], "land_leg_eur_per_t": g["land_cost"], "ship_leg_eur_per_t": cost - g["land_cost"],
                            "trade_class": "maritime_trade (decision 95 c)",
                            "carbon_rule": "shipped captured CO2 counts as abatement of LA (decision 20); stored in the receiver's national store (decision 28)"})
            rows.append(dict(node=node, receiver=r.receiver, via=g["coastal_node"], land=g["land_cost"], total=cost))
    led.update(links=len(rows), destination=next(iter(legs.values()))["destination"] if legs else None, transport_mode=next(iter(legs.values()))["mode"] if legs else None,
               cost_range={k: [round(min(x["total"] for x in rows if x["receiver"] == k), 3), round(max(x["total"] for x in rows if x["receiver"] == k), 3)] for k in sorted({x["receiver"] for x in rows})})
    n.meta["research_lao_transit_shipping"] = led
    return led


def add_domestic_candidates(n, table: pd.DataFrame) -> list:
    """S4E-1 item 4: domestic candidates (both scenarios) - DC links for node pairs on different landmasses; AC rows use the cross-border AC
    conventions (s2_layers.add_apg_corridor_lines)."""
    from s2_layers import add_apg_corridor_lines
    if (table.country_from != table.country_to).any():
        raise ValueError("domestic candidate table holds a cross-border row")
    tmpl = _dc_template(n); added = []
    for _, r in table.iterrows():
        if str(r.component) in n.links.index or str(r.component) in n.lines.index:
            raise ValueError(f"domestic candidate {r.component} already in the network")
        if r.component_type == "Link":
            added.append(_add_dc(n, str(r.component), r["from"], r["to"], r.length_km, r.capacity_2025_mw, r.subsea_share, tmpl) | dict(status=str(r.status)))
    lines = table[table.component_type == "Line"]
    if len(lines):
        keep = n.meta.get("apg_corridor_additions")
        added += add_apg_corridor_lines(n, lines)
        n.meta["apg_corridor_additions"] = keep
    n.meta["s4e_domestic_additions"] = added
    return added
