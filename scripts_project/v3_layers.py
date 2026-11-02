"""V3 model layers (decisions 161, 165; V3_RULES.md sections 3, 7).

  * national liquid buses: research.liquids.structure = national_ship (main: '<ISO2> oil', '<ISO2> oil non-fossil', '<ISO2> methanol', '<ISO2> ammonia', located at the hub
    node of research.liquids.hubs_table) | asean_pool (v2: one regional bus per carrier, decision 44);
  * add_liquid_shipping: ship links between the coastal national buses (non-fossil oil, methanol, ammonia; fossil oil has the same import price everywhere), unit cost
    c(d) by research.liquids.ship_cost_basis = td_tanker (main) | ieaghg (upper-bound sensitivity) x ship_cost_scale, cargo loss eta(d), fixed non-binding capacity; Lao rail
    transit to the Vietnamese bus (decision 93 analogy). Carrier class maritime_trade: kept in every scenario;
  * apply_ev_structure: research.s2.demand.ev_structure = smart (main, E2) | smart_v2g (E3) | uncontrolled (E4) | flat (v2);
  * add_dedicated_plant_lines (X1b, decisions 172, 173): the Lao IPP export lines of research.network.dedicated_plant_lines_table, merged by plant node and landing node, one fixed lossy forward / '-reversed'
    pair each, in every scenario with the cross-border electricity switch on; empty key = v2 state.
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
DEDICATED_CARRIER = "dedicated plant line"
DEDICATED_STOCK = "dedicated_plant_line"
DEDICATED_LENGTH_FACTOR = 1.25   # lines.length_factor of the electric base: LA2 3 - TH2 1 great circle 222.9 km, model line 278.66 km
DEDICATED_LOSS_TYPE = ("Al/St 240/40 4-bundle 380.0", 380.0, 0.7)   # type, v_nom, s_max_pu of the cross-border AC lines: the loss proxy of decision 108 per km


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


def great_circle_km(x0: float, y0: float, x1: float, y1: float) -> float:
    p0, p1 = np.radians(y0), np.radians(y1); dl = np.radians(x1 - x0); dp = p1 - p0
    return float(2.0 * 6371.0 * np.arcsin(np.sqrt(np.sin(dp / 2.0) ** 2 + np.cos(p0) * np.cos(p1) * np.sin(dl / 2.0) ** 2)))


def add_dedicated_plant_lines(n, cfg, repo, costs, existing_cfg) -> dict:
    """X1b: see the module docstring and V3_RULES.md section 2.2. After apply_ac_losses (the lossy split is done here: efficiency = 1 - proxy lambda over the length). The stock FOM rule of the corridors applies.
    Not added with the cross-border electricity switch off (fully disconnected network). p_nom_min = p_nom marks the stock for apply_stock_mode."""
    from s2_layers import add_link
    from s4d_layers import coalition_members
    from s4k_layers import ac_loss_mode, reference_loading, type_lambda_per_km
    R = cfg["research"]; table = (R.get("network") or {}).get("dedicated_plant_lines_table"); led = dict(table=table, links=0)
    if not table or not R["cross_border"]["electricity"]:
        n.meta["research_dedicated_lines"] = led
        return led
    t = pd.read_csv(Path(repo) / table); t = t[t.counted.astype(bool)]; units = n.meta["existing_unit_components"]; members = coalition_members(R["cross_border"]); gone = []
    for _, r in t.iterrows():
        for i in str(r.gem_unit_ids).split(";"):
            if units[f"GEM:{i}"]["node"] != r.plant_node:
                raise ValueError(f"X1b: {r.project} unit {i} is not at {r.plant_node}")
    ptype, v_nom, s_max = DEDICATED_LOSS_TYPE
    lam_km = type_lambda_per_km(n, ptype, reference_loading(cfg), s_max, v_nom) if ac_loss_mode(cfg) == "linear_proxy" else 0.0
    if "stock" not in n.links:
        n.links["stock"] = ""
    rows = []
    for (a, b), g in t.groupby(["plant_node", "landing_node"], sort=True):
        ca, cb = str(n.buses.at[a, "country"]), str(n.buses.at[b, "country"])
        if members is not None and not {ca, cb} <= members:
            gone.append(f"{a}-{b}")
            continue
        km = great_circle_km(float(n.buses.at[a, "x"]), float(n.buses.at[a, "y"]), float(n.buses.at[b, "x"]), float(n.buses.at[b, "y"])) * DEDICATED_LENGTH_FACTOR
        mw = float(g.contract_mw.sum()); eta = 1.0 - lam_km * km; name = f"dedicated plant line {a} - {b}"
        for x, f, to, co, rev in ((name, a, b, ca, False), (f"{name}-reversed", b, a, cb, True)):
            add_link(n, x, co, DEDICATED_CARRIER, [f, to], [eta], role="EXISTING_CROSS_BORDER_STOCK", length=0.0 if rev else km, extra={"length_original": km})
            n.links.loc[x, ["p_nom", "p_nom_min", "p_nom_max"]] = [mw, mw, mw]
            n.links.loc[x, "p_nom_extendable"] = False; n.links.loc[x, "reversed"] = rev; n.links.loc[x, "asset_role"] = "existing_cross_border_stock"
            n.links.loc[x, "border_class"] = "cross_border"; n.links.loc[x, "transport_carrier"] = "electricity"; n.links.loc[x, "stock"] = DEDICATED_STOCK
        fom = (float(costs.at["HVAC overhead", "FOM"]) / 100.0 * float(costs.at["HVAC overhead", "investment"]) * km * mw) if existing_cfg["fom_on_existing"] else 0.0
        rows.append(dict(link=name, plant_node=a, landing_node=b, pair="-".join(sorted((ca, cb))), projects=sorted(g.project), contract_mw=mw, length_km=km, efficiency=eta, annual_fom_eur=fom))
    n.links["reversed"] = n.links["reversed"].fillna(False).astype(bool); n.links["stock"] = n.links["stock"].fillna("").astype(str)   # as s4j_layers: a mixed column does not export
    if rows:
        fl = list(n.meta.get("existing_cross_border_fom_ledger", [])) + [dict(component_type="Link", component=r["link"], capacity_2025_mw=r["contract_mw"], length_km=r["length_km"], annual_fom_eur=r["annual_fom_eur"], cost_rows=["HVAC overhead"]) for r in rows if r["annual_fom_eur"]]
        n.meta["existing_cross_border_fom_ledger"] = fl; n.meta["existing_cross_border_fom_eur"] = float(sum(r["annual_fom_eur"] for r in fl))
    led.update(links=len(rows), lines=rows, total_mw=float(sum(r["contract_mw"] for r in rows)), loss_per_km=lam_km, coalition_removed=gone, annual_fom_eur=float(sum(r["annual_fom_eur"] for r in rows)))
    n.meta["research_dedicated_lines"] = led
    return led


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
