"""V3 model layers (decisions 161, 165; V3_RULES.md sections 3, 7).

  * national liquid buses: research.liquids.structure = national_ship (main: '<ISO2> oil', '<ISO2> oil non-fossil', '<ISO2> methanol', '<ISO2> ammonia', located at the hub
    node of research.liquids.hubs_table) | asean_pool (v2: one regional bus per carrier, decision 44);
  * add_liquid_shipping: ship links between the coastal national buses (non-fossil oil, methanol, ammonia; fossil oil has the same import price everywhere), unit cost
    c(d) by research.liquids.ship_cost_basis = td_tanker (main) | ieaghg (upper-bound sensitivity) x ship_cost_scale, cargo loss eta(d), fixed non-binding capacity; Lao rail
    transit to the Vietnamese bus (decision 93 analogy). Carrier class maritime_trade: kept in every scenario;
  * apply_ev_structure: research.s2.demand.ev_structure = smart (main, E2) | smart_v2g (E3) | uncontrolled (E4) | flat (v2).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LANDLOCKED = ("LA",)   # = s4d_layers.LANDLOCKED
TRANSIT_CARRIER = "liquid transit rail"
SHIP_CARRIERS = {"oil non-fossil": "oil non-fossil ship", "methanol": "methanol ship", "ammonia": "ammonia ship"}
LOAD_CARRIERS = {"oil": ("oil final energy", "oil feedstock"), "oil non-fossil": ("oil final energy", "oil feedstock"), "methanol": ("shipping methanol", "industry methanol"), "ammonia": ("industry ammonia",)}
UNIT_KEY = {"oil": "oil", "oil non-fossil": "oil", "methanol": "methanol", "ammonia": "ammonia"}
EV_MODES = ("flat", "smart", "smart_v2g", "uncontrolled")


def liquids_cfg(cfg) -> dict:
    return cfg["research"].get("liquids") or {}


def liquids_national(cfg) -> bool:
    v = str(liquids_cfg(cfg).get("structure", "asean_pool"))
    if v not in ("national_ship", "asean_pool"):
        raise ValueError("Unknown research.liquids.structure " + v)
    return v == "national_ship"


def liquid_hubs(cfg) -> dict:
    t = pd.read_csv(ROOT / liquids_cfg(cfg)["hubs_table"])
    return dict(zip(t.country, t.hub_node))


def liquid_bus(cfg, country: str, carrier: str) -> str:
    return f"{country} {carrier}" if liquids_national(cfg) else f"ASEAN {carrier}"


def ensure_liquid_bus(n, cfg, country: str, carrier: str) -> str:
    from s2_layers import add_bus
    if not liquids_national(cfg):
        return add_bus(n, f"ASEAN {carrier}", carrier, "ASEAN", "")
    return add_bus(n, f"{country} {carrier}", carrier, country, liquid_hubs(cfg)[country])


def national_liquid_buses(cfg) -> set:
    from carrier_architecture import COUNTRIES
    return {f"{c} {k}" for c in COUNTRIES for k in LOAD_CARRIERS} if liquids_national(cfg) else set()


def _annual(n, carriers) -> float:
    w = n.snapshot_weightings.generators
    idx = n.loads.index[n.loads.carrier.isin(list(carriers))]
    return float(n.get_switchable_as_dense("Load", "p_set")[idx].mul(w, axis=0).sum().sum())


def ship_unit(cfg, registry: pd.DataFrame, key: str, km: float) -> tuple[float, float]:
    """(EUR2020/MWh delivered at the link input, efficiency) of a sea route: S-B c_km x d, eta = 1 - loss x d | S-A fixed + c_km x d, eta = 1."""
    L = liquids_cfg(cfg); basis = str(L.get("ship_cost_basis", "td_tanker")); scale = float(L.get("ship_cost_scale", 1.0)); rv = lambda p: float(registry.loc[p, "value"])
    if basis == "td_tanker":
        return rv(f"liquid_ship_ckm_td_{key}") * km * scale, 1.0 - rv("liquid_ship_cargo_loss_per_km") * km
    if basis == "ieaghg":
        return (rv(f"liquid_ship_fixed_ieaghg_{key}") + rv(f"liquid_ship_ckm_ieaghg_{key}") * km) * scale, 1.0
    raise ValueError("Unknown research.liquids.ship_cost_basis " + basis)


def add_liquid_shipping(n, cfg, registry: pd.DataFrame) -> dict:
    """Decision 161: see the module docstring. After the bunker layer (the capacity bound uses the bunker loads)."""
    from s2_layers import add_link
    led = dict(structure=str(liquids_cfg(cfg).get("structure", "asean_pool")), links=0)
    if not liquids_national(cfg):
        n.meta["research_liquids"] = led
        return led
    L = liquids_cfg(cfg); routes = pd.read_csv(ROOT / L["routes_table"]); factor = float(L["ship_capacity_factor"]); rows = []

    def bound(link, cap):
        n.links.loc[link, ["p_nom", "p_nom_extendable", "asset_role"]] = [cap, False, "trade_capacity_bound"]

    caps = {k: _annual(n, v) / 8760.0 * factor for k, v in LOAD_CARRIERS.items()}
    for carrier, link_carrier in SHIP_CARRIERS.items():
        key = UNIT_KEY[carrier]
        for _, r in routes.sort_values(["origin", "destination"]).iterrows():
            c, eta = ship_unit(cfg, registry, key, float(r.sea_km))
            name = f"{r.origin} {carrier} ship to {r.destination}"
            add_link(n, name, r.origin, link_carrier, [f"{r.origin} {carrier}", f"{r.destination} {carrier}"], [eta], marginal_cost=c, role="LIQUID_SHIPPING",
                     extra={"route_km": float(r.sea_km), "trade_class": "maritime_trade (decision 161)"})
            bound(name, caps[carrier]); rows.append(dict(link=name, km=float(r.sea_km), c=c, eta=eta))
    rv = lambda p: float(registry.loc[p, "value"])
    t = pd.read_csv(ROOT / "research_inputs/co2_v5/LAO_TRANSIT_S4D1.csv").set_index("node"); hub = liquid_hubs(cfg)["LA"]; km = float(t.at[hub, "route_km"])
    per_t = rv("co2_land_transport_rail_unit_cost") * km + rv("co2_land_transport_rail_loading_cost")
    transit = 0
    for carrier in LOAD_CARRIERS:
        c = per_t / rv(f"liquid_ship_mwh_per_t_{UNIT_KEY[carrier]}")
        for a, b in (("VN", "LA"), ("LA", "VN")):
            if carrier == "oil" and a == "LA":   # fossil oil only enters LA (no production or import there)
                continue
            name = f"{a} {carrier} transit to {b}"
            add_link(n, name, a, TRANSIT_CARRIER, [f"{a} {carrier}", f"{b} {carrier}"], [1.0], marginal_cost=c, role="LIQUID_SHIPPING", extra={"route_km": km, "trade_class": "transit_trade (decision 93 analogy)"})
            bound(name, caps[carrier]); transit += 1
    led.update(links=len(rows), transit_links=transit, ship_cost_basis=str(L.get("ship_cost_basis")), ship_cost_scale=float(L.get("ship_cost_scale", 1.0)), capacity_mw={k: float(v) for k, v in caps.items()},
               cost_range_eur_per_mwh=[float(min(x["c"] for x in rows)), float(max(x["c"] for x in rows))], efficiency_range=[float(min(x["eta"] for x in rows)), float(max(x["eta"] for x in rows))], la_transit_km=km)
    n.meta["research_liquids"] = led
    return led


def apply_ev_structure(n, cfg, repo, registry: pd.DataFrame) -> dict:
    """Decision 165, D165-1 to D165-4: EV load shape on the battery bus, charger, battery store, V2G. flat keeps the v2 structure."""
    from s2_layers import add_link, ensure_carrier
    from v3_ev import NODE_TZ, SHAPE, ev_series
    D = cfg["research"]["s2"]["demand"]; mode = str(D.get("ev_structure", "flat"))
    if mode not in EV_MODES:
        raise ValueError("Unknown research.s2.demand.ev_structure " + mode)
    led = dict(mode=mode)
    if mode == "flat":
        n.meta["research_ev"] = led
        return led
    w = pd.read_csv(Path(repo) / SHAPE.relative_to(ROOT)).sort_values(["weekday", "hour"]); week = w.consumption_norm.to_numpy(); plug = w.plugin.to_numpy()
    tz = pd.read_csv(Path(repo) / NODE_TZ.relative_to(ROOT)).set_index("node").utc_offset_h
    rv = lambda p: float(registry.loc[p, "value"]); sn = n.snapshots
    a = float(D.get("ev_annual_km_per_vehicle", rv("ev_annual_km_per_vehicle"))) / (rv("share_transport_electric_efficiency") * 100.0)
    scale = float(D.get("ev_fleet_scale", 1.0)); delay = float(D.get("ev_uncontrolled_delay_h", 3.0))
    e_car, rate, avail, eff = rv("share_bev_energy"), rv("share_bev_charge_rate"), rv("share_bev_dsm_availability"), rv("share_bev_charge_efficiency")
    res_v, res_h = rv("share_bev_dsm_restriction_value"), rv("share_bev_dsm_restriction_time")
    load_ts, charger_ts, emin_ts, v2g_ts = {}, {}, {}, {}
    fleet = 0.0
    ensure_carrier(n, "EV battery")
    for name, z in n.loads[n.loads.carrier == "land transport EV"].sort_index().iterrows():
        node = str(z.bus)[: -len(" EV battery")]; off = float(tz[node]); c = str(n.buses.at[node, "country"])
        s = ev_series(sn, off - (delay if mode == "uncontrolled" else 0.0), week); s = s / s.mean()
        load_ts[name] = float(z.p_set) * s
        if mode == "uncontrolled":
            continue
        N = float(z.p_set) * 8760.0 / a * scale; fleet += N
        ch = f"{node} BEV charger"
        n.links.loc[ch, ["p_nom", "p_nom_extendable", "p_max_pu"]] = [N * rate, False, 1.0]
        charger_ts[ch] = ev_series(sn, off, plug)
        st = f"{node} EV battery store"
        n.add("Store", st, bus=str(z.bus), carrier="EV battery", e_nom=N * e_car * avail, e_nom_extendable=False, e_cyclic=True, capital_cost=0.0, marginal_cost=0.0)
        n.stores.loc[st, ["country", "research_role"]] = [c, "EV_BATTERY"]
        lh = ((sn.hour.to_numpy() + off) % 24.0); hit = (lh <= res_h) & (res_h < lh + 3.0)
        hit |= ((lh - 24.0) <= res_h) & (res_h < lh - 21.0)
        emin_ts[st] = np.where(hit, res_v, 0.0)
        if mode == "smart_v2g":
            v2g = f"{node} V2G"
            add_link(n, v2g, c, "V2G", [str(z.bus), node], [eff], role="EV_CHARGER")
            n.links.loc[v2g, ["p_nom", "p_nom_extendable", "p_max_pu"]] = [N * rate, False, 1.0]
            v2g_ts[v2g] = charger_ts[ch]
    n.loads_t.p_set = pd.concat([n.loads_t.p_set, pd.DataFrame(load_ts, index=sn)], axis=1)
    if charger_ts or v2g_ts:
        n.links_t.p_max_pu = pd.concat([n.links_t.p_max_pu, pd.DataFrame({**charger_ts, **v2g_ts}, index=sn)], axis=1)
    if emin_ts:
        n.stores_t.e_min_pu = pd.concat([n.stores_t.e_min_pu, pd.DataFrame(emin_ts, index=sn)], axis=1)
    led.update(loads=len(load_ts), stores=len(emin_ts), v2g_links=len(v2g_ts), fleet_equivalent_vehicles=fleet, mwh_per_vehicle_year=a, fleet_scale=scale, battery_mwh_total=float(fleet * e_car * avail), charger_mw_total=float(fleet * rate))
    n.meta["research_ev"] = led
    return led
