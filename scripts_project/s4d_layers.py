"""S4D model layers (S4D instruction v1, 2026-10-17; decisions 91-93).

S4D-1 (decision 93; coastal rule: user decision 2026-10-17 on stop report S4D_STOP_01, option A with the physical coastline):
  * export_nodes_mode: research.co2.extra_asean_export_nodes = coastal (main: the extra-ASEAN export links of S4C-4 only at the coastal nodes
    of research.co2.coastal_nodes_table, research_inputs/co2_v5/COASTAL_NODES_S4D1_FINAL.csv; inland captured CO2 reaches the coast through
    the domestic CO2 pipeline candidates, decision 35, endogenous in both scenarios) | all (S4C-4 behaviour; default when the key is absent).
  * transit_mode: research.co2.landlocked_transit = on (main: for the landlocked country LA one transit export link per buffered node,
    '<node> co2 transit export extra-ASEAN', from '<node> co2 stored' to 'co2 sequestered extra-ASEAN LA'; marginal cost = land leg by rail to
    the nearest neighbouring coast, registry co2_lao_transit_land_cost_<node> (Stolaroff et al. 2021 Table 2, grade C +-50 %); the store keeps
    the extra-ASEAN unit cost, so the total per tonne = land leg + co2_extra_asean_storage_cost; treated like the liquid-fuel transit of
    decision 44 - trade, not cross-border network; both scenarios) | off (default when the key is absent). Only with export nodes = coastal.
  The links are added inside s4c_layers.apply_extra_asean_storage (before tag_cross_border: both ends are buses of the exporting country).

S4D-2 (decision 92, revised: both scenarios):
  * apply_intra_asean_shipping: research.co2.intra_asean_shipping = on (main) | off (default when absent). For every coastal buffered node of
    country i and every other country j with a national store 'co2 sequestered <j>' (injection cap > 0), one link '<node> co2 ship to <j>'
    (carrier 'CO2 ship') from '<node> co2 stored' into 'co2 sequestered <j>': the tonnes occupy j's annual cap (decision 28) and pay j's store
    unit cost (not repeated on the link); they count as abatement of i (decision 20: they leave i's captured-CO2 buffer and enter no
    atmosphere). Marginal cost = co2_ship_chain_fixed_cost + co2_ship_chain_per_km_cost x great-circle km (origin -> landing node of the route
    table research.co2.ship_routes_table) x co2_ship_route_factor x research.co2.ship_route_factor_scale (IEAGHG 2004 Table 5-3, grade C;
    route factor +-25 % first-batch sensitivity). scenario_network.tag_cross_border classifies the carrier as maritime_trade: not network, kept
    by the cross-border switches (decisions 18, 44), not counted by B5.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

TRANSIT_LINK = "CO2 transit export extra-ASEAN"
LANDLOCKED = ("LA",)
ROOT = Path(__file__).resolve().parents[1]


def _co2(cfg) -> dict:
    return cfg["research"].get("co2", {}) or {}


def export_nodes_mode(cfg) -> str:
    v = str(_co2(cfg).get("extra_asean_export_nodes", "all")).lower()
    if v not in ("coastal", "all"):
        raise ValueError("Unknown research.co2.extra_asean_export_nodes " + v)
    return v


def transit_mode(cfg) -> str:
    v = _co2(cfg).get("landlocked_transit", "off")
    v = {True: "on", False: "off"}.get(v, v) if isinstance(v, bool) else str(v).lower()
    if v not in ("on", "off"):
        raise ValueError("Unknown research.co2.landlocked_transit " + str(v))
    if v == "on" and export_nodes_mode(cfg) != "coastal":
        raise ValueError("research.co2.landlocked_transit = on requires research.co2.extra_asean_export_nodes = coastal")
    return v


def extra_asean_cost_scale(cfg) -> float:
    """S4D-6 first-batch sensitivity: research.co2.extra_asean_cost_scale multiplies the registry extra-ASEAN unit cost (key absent = 1.0, so
    the main configuration and its hash stay unchanged; added only by --override co2.extra_asean_cost_scale=0.5 | 1.5)."""
    v = float(_co2(cfg).get("extra_asean_cost_scale", 1.0))
    if not v > 0:
        raise ValueError("research.co2.extra_asean_cost_scale must be > 0")
    return v


def coastal_table(cfg) -> tuple[pd.Series, Path]:
    """node -> coastal (bool) from research.co2.coastal_nodes_table."""
    p = ROOT / str(_co2(cfg).get("coastal_nodes_table", "research_inputs/co2_v5/COASTAL_NODES_S4D1_FINAL.csv"))
    t = pd.read_csv(p)
    return t.set_index("node").coastal.astype(bool), p


def transit_cost_id(node: str) -> str:
    return "co2_lao_transit_land_cost_" + node.replace(" ", "_")


def coalition_members(switches: dict) -> set | None:
    """S4D-4 (decision 91b): research.cross_border.coalition -> set of ISO2 codes, or None when the key is null / absent. A coalition is
    defined on top of the integrated switches (all network carriers on); [] keeps no cross-border corridor."""
    from carrier_architecture import COUNTRIES
    v = switches.get("coalition")
    if v is None:
        return None
    if not isinstance(v, (list, tuple)):
        raise ValueError("research.cross_border.coalition must be a list of ISO2 codes or null")
    m = {str(x).upper() for x in v}
    if m - set(COUNTRIES):
        raise ValueError(f"unknown coalition members {sorted(m - set(COUNTRIES))}")
    if not all(bool(switches[k]) for k in ("electricity", "H2", "gas", "co2")):
        raise ValueError("research.cross_border.coalition requires the integrated switches (electricity, H2, gas, co2 all true)")
    return m


def connected_coalitions(edges: set, countries) -> dict:
    """Coalitions S (subsets of the countries) whose corridor graph restricted to S is connected - the coalitions a Myerson value needs runs
    for (singletons are connected; a disconnected S is the sum of its components)."""
    cs = sorted(countries); adj = {c: set() for c in cs}
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    by_size = {}
    for mask in range(1, 1 << len(cs)):
        S = [cs[i] for i in range(len(cs)) if mask >> i & 1]
        seen = {S[0]}; stack = [S[0]]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v in S and v not in seen:
                    seen.add(v); stack.append(v)
        if len(seen) == len(S):
            by_size[len(S)] = by_size.get(len(S), 0) + 1
    return dict(by_size=by_size, total=sum(by_size.values()), with_two_or_more=sum(v for k, v in by_size.items() if k >= 2))


SHIP_CARRIER = "CO2 ship"
SHIP_IDS = ("co2_ship_chain_fixed_cost", "co2_ship_chain_per_km_cost", "co2_ship_route_factor")


def shipping_mode(cfg) -> str:
    v = _co2(cfg).get("intra_asean_shipping", "off")
    v = {True: "on", False: "off"}.get(v, v) if isinstance(v, bool) else str(v).lower()
    if v not in ("on", "off"):
        raise ValueError("Unknown research.co2.intra_asean_shipping " + str(v))
    if v == "on" and export_nodes_mode(cfg) != "coastal":
        raise ValueError("research.co2.intra_asean_shipping = on requires research.co2.extra_asean_export_nodes = coastal (ships load at coastal nodes)")
    return v


def apply_intra_asean_shipping(n, cfg, registry: pd.DataFrame) -> dict:
    """S4D-2 (decision 92): see the module docstring."""
    from d1_common import sha256
    from s2_layers import add_link
    mode = shipping_mode(cfg)
    led = dict(mode=mode, links=0)
    if mode == "off":
        n.meta["research_intra_asean_shipping"] = led
        return led
    rows = {}
    for k in SHIP_IDS:
        r = registry.loc[k]
        if r["status"] != "REGISTERED":
            raise ValueError(f"{k} is {r['status']}: no citable shipping cost")
        rows[k] = float(r["value"])
    scale = float(_co2(cfg).get("ship_route_factor_scale", 1.0))
    factor = rows["co2_ship_route_factor"] * scale
    p = ROOT / str(_co2(cfg).get("ship_routes_table", "research_inputs/co2_v5/CO2_SHIP_ROUTES_S4D2.csv"))
    routes = pd.read_csv(p)
    coast, _ = coastal_table(cfg)
    years = float(cfg["research"]["s2"]["co2"]["storage_years"])
    buffered = sorted(b[: -len(" co2 stored")] for b in n.stores.bus[n.stores.research_role == "CO2_BUFFER"])
    origins = {x for x in buffered if bool(coast.get(x, False))}
    receivers = {str(c) for c in n.stores.country[n.stores.carrier == "co2 sequestered"]}
    have = set(zip(routes.origin, routes.receiver))
    need = {(o, j) for o in origins for j in receivers if str(n.buses.at[o, "country"]) != j}
    if have != need:
        raise ValueError(f"ship route table does not match the network: missing {sorted(need - have)[:5]}, extra {sorted(have - need)[:5]}")
    by_pair = {}
    for _, r in routes.sort_values(["origin", "receiver"]).iterrows():
        i = str(n.buses.at[r.origin, "country"]); route_km = float(r.gc_km) * factor
        cost = rows["co2_ship_chain_fixed_cost"] + rows["co2_ship_chain_per_km_cost"] * route_km
        add_link(n, f"{r.origin} co2 ship to {r.receiver}", i, SHIP_CARRIER, [f"{r.origin} co2 stored", f"co2 sequestered {r.receiver}"], [1.0], capital_cost=0.0,
                 marginal_cost=cost, lifetime=years, role="CO2_SHIPPING",
                 extra={"landing_node": r.landing, "great_circle_km": float(r.gc_km), "route_km": route_km, "trade_class": "maritime_trade (decision 92)",
                        "carbon_rule": "shipped captured CO2 counts as abatement of the exporting country (decision 20); stored in the receiver's national store (decision 28)"})
        by_pair.setdefault(f"{i}->{r.receiver}", []).append(cost)
    led.update(links=int(len(routes)), route_factor=rows["co2_ship_route_factor"], route_factor_scale=scale, fixed_eur2020_per_t=rows["co2_ship_chain_fixed_cost"],
               per_km_eur2020_per_t=rows["co2_ship_chain_per_km_cost"], routes_table=str(p.relative_to(ROOT)), routes_table_sha256=sha256(p),
               origins=len(origins), receivers=sorted(receivers),
               cost_range_by_pair={k: [round(min(v), 3), round(max(v), 3)] for k, v in sorted(by_pair.items())})
    n.meta["research_intra_asean_shipping"] = led
    return led


def shipping_report(n) -> dict:
    """Post-solve: shipped tonnes and freight (exporter) per country pair; storage enters the receiver's national store."""
    sl = n.links[n.links.carrier == SHIP_CARRIER]
    if not len(sl):
        return {}
    w = n.snapshot_weightings.objective
    out = {}
    for k, z in sl.iterrows():
        t = float((n.links_t.p0[k] * w).sum()) if k in n.links_t.p0 else 0.0
        if t <= 0:
            continue
        key = f"{n.buses.at[z.bus0, 'country']}->{str(z.bus1).split()[-1]}"
        d = out.setdefault(key, dict(t=0.0, freight_eur=0.0, links=[]))
        d["t"] += t; d["freight_eur"] += t * float(z.marginal_cost); d["links"].append(k)
    return out
