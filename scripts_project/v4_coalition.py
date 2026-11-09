"""V4 W20 (decision 228): coalition subnetworks of the v4 main integrated network - c(S) of the PHYSICAL coalition game.

    PYTHONHASHSEED=0 python scripts_project/v4_coalition.py list
    PYTHONHASHSEED=0 python scripts_project/v4_coalition.py build --base <integrated_2920_3h_unsolved.nc> --coalition GMS --out <dir> [--truncate 56]
    PYTHONHASHSEED=0 python scripts_project/v4_coalition.py build --base <nc> --members KH,LA,MM,TH,VN [--include-bunker] --name X --out <dir>

coalition_subnetwork(network, members, include_bunker=False) returns (S-only network, ledger). The definition is decision 133 (2)a as restated in
decision 228 (V4_W20_INSTRUCTION.md section 0): a non-member country leaves ENTIRELY (demand, resources, facilities, potentials, stock and
candidates, liquid buses and shipping access, CO2 shipping, pipelines and lines); every line / pipeline / dedicated line / shipping link that
crosses the coalition boundary is removed; stock cross-border facilities and new cross-border candidates BETWEEN members stay; every member keeps
its own net-zero row. The international bunker is the 12th player and belongs to no country coalition: with include_bunker=False its loads, its
final-energy buses and its account (Store 'co2 bunkers ASEAN', hook research_bunker_net_zero) leave the network. This is NOT the decision-91 (b)
corridor switch (cross_border.coalition, which keeps every country and only cuts corridors) and NOT m08a_layers.apply_remove_countries (v2 structure;
it keeps the bunker player). Rules, applied in this order (each removed item is booked under exactly one rule):

  R1  by bus country      buses whose country is a non-member; every one-port component on them (Load, Generator, Store, StorageUnit,
                          ShuntImpedance); branches whose every port is on such buses (non-member internal facilities)
  R2  by port             every branch (Line, Transformer, Link incl. bus2..bus4) with at least one port on a removed bus and at least one on a
                          kept bus: the coalition-boundary lines, pipelines, dedicated plant lines, DC links (both directions), liquid ships,
                          liquid transit rail, CO2 ships / transit links into non-member stores, liquid-pool access of non-members
  R3  by participant      the bunker player: buses of country 'ASEAN' (bunker final-energy buses, the account bus), their loads and Store, the
                          metering / bunker shipping links feeding them; the hook research_bunker_net_zero and n.meta['research_bunkers']
                          (include_bunker=True on a subset keeps the bunker buses located at member nodes and the account)
  R4  global / hook rows  GlobalConstraint rows referencing a removed carrier or bus (the v4 network has none); the per-country hook rows follow
                          the network: research_country_co2_limit-<c> for c in n.meta['research_countries'] = members, research_co2_storage_cap-<c>
                          for members with a store, ResearchImportAnnual-<generator> / ResearchStoreDirection-<store> / battery pairs / new-hydro
                          inflow ties for the remaining components, the existing-asset FOM constant and the existing cross-border FOM constant
                          recomputed from the remaining components (decision-214 / S1 hooks), lossy bidirectional sync and AC loss proxy from the
                          remaining links / lines
  R5  clean-up            buses left without ANY attached component (that had one in the base) are removed and counted; carriers that became
                          unreferenced are removed and counted; a branch with a port on a missing bus cannot remain (R2 removes it; checked).
                          Member components that became dead ends (bus with one branch and no one-port, not a dead end in the base, e.g. the
                          member-side B2B converter of a removed DC link) are KEPT - member stock stays a member asset - and listed with their
                          fixed-cost constants.
  R6  metadata            every metadata entry that names a component removed HERE is dropped (entries already dangling in the base are left
                          as they are); country-keyed caps follow the members; n.meta['research_coalition'] records the members and the ledger.

Transit: a link whose ports are all in the coalition keeps its route even when it passes a non-member (the Lao CO2 transit through Vietnamese coastal
nodes, column via_coastal_node): the port rule, consistent with the landlocked-transit precedent of decision 132 b1 (test_m08a_a7); such links are
listed in the ledger (transit_via_non_member). Removing more options can only raise c(S), so the core check under the port rule is the stricter one.

Nothing is solved. The main build path (s2_network.py, m08a_variants.py) does not import this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

SCRIPT = "scripts_project/v4_coalition.py"
RULES_VERSION = "W20-v1"
BUNKER = "ASEAN"
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
ONE_PORT = ("Load", "Generator", "Store", "StorageUnit", "ShuntImpedance")
BRANCH = ("Line", "Transformer", "Link")
BUNKER_HOOK = "research_bunker_net_zero"
BUNKER_STORE = "co2 bunkers ASEAN"
# physical cross-border infrastructure (stock = existing capacity > 0); ships / transit links carry a trade capacity bound, not stock
PHYSICAL_XB = ("DC", "dedicated plant line", "gas pipeline", "H2 pipeline", "CO2 pipeline")

# decision 228 (a): three sub-regional groupings and their complements; (b) the 11 leave-one-out coalitions. Order = solve order (section 4).
BLOCS = {"GMS": ("KH", "LA", "MM", "TH", "VN"), "LTMS": ("LA", "MY", "SG", "TH"), "BIMP": ("BN", "ID", "MY", "PH")}


def coalitions() -> dict:
    out = {k: tuple(sorted(v)) for k, v in BLOCS.items()}
    for k, v in BLOCS.items():
        out["non" + k] = tuple(sorted(set(COUNTRIES) - set(v)))
    for c in COUNTRIES:
        out["minus" + c] = tuple(sorted(set(COUNTRIES) - {c}))
    return out


COALITION_ORDER = ["GMS", "LTMS", "BIMP", "nonGMS", "nonLTMS", "nonBIMP"] + ["minus" + c for c in COUNTRIES]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def port_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns if c == "bus" or (c.startswith("bus") and c[3:].isdigit())]


def _used(v) -> bool:
    s = str(v)
    return s not in ("", "nan", "None")


def attachments(n):
    """bus -> number of one-port components, bus -> number of branch ports."""
    one, br = Counter(), Counter()
    for typ in ONE_PORT:
        df = n.df(typ)
        if len(df):
            one.update(df.bus.astype(str))
    for typ in BRANCH:
        df = n.df(typ)
        if len(df):
            for p in port_columns(df):
                br.update(str(v) for v in df[p] if _used(v))
    return one, br


def unreferenced_carriers(n) -> set:
    used = set()
    for c in n.iterate_components():
        if c.name == "Carrier" or not len(c.df) or "carrier" not in c.df:
            continue
        used |= set(c.df.carrier.astype(str))
    return set(n.carriers.index) - used


def missing_carriers(n) -> set:
    out = set()
    for c in n.iterate_components():
        if c.name == "Carrier" or not len(c.df) or "carrier" not in c.df:
            continue
        out |= {(c.name, str(x)) for x in set(c.df.carrier.astype(str)) - set(n.carriers.index) if x not in ("", "nan")}
    return out


def branch_countries(n, typ: str, name: str) -> tuple:
    df = n.df(typ)
    return tuple(sorted({str(n.buses.at[str(df.at[name, p]), "country"]) for p in port_columns(df) if _used(df.at[name, p]) and str(df.at[name, p]) in n.buses.index}))


def fixed_cost_constant(n, typ: str, name: str) -> float:
    """objective constant carried by a component on its own: capital cost x fixed capacity (PyPSA non-extendable) + existing annual FOM."""
    df = n.df(typ)
    nom = {"Line": "s_nom", "Transformer": "s_nom", "Store": "e_nom"}.get(typ, "p_nom")
    out = 0.0
    if nom + "_extendable" in df and not bool(df.at[name, nom + "_extendable"]) and "capital_cost" in df:
        out += float(df.at[name, "capital_cost"]) * float(df.at[name, nom])
    if "existing_annual_fixed_om_eur" in df:
        v = pd.to_numeric(pd.Series([df.at[name, "existing_annual_fixed_om_eur"]]), errors="coerce").fillna(0.0).iloc[0]
        out += float(v)
    return out


def _weighted_load_mwh(n, names) -> float:
    if not len(names):
        return 0.0
    load = n.get_switchable_as_dense("Load", "p_set")[list(names)]
    return float(load.mul(n.snapshot_weightings.generators, axis=0).sum().sum())


def coalition_subnetwork(network, members, include_bunker: bool = False, *, inplace: bool = False):
    """S-only network of the physical coalition game (module docstring, rules R1-R6) and the ledger of what was removed / kept. Never solves."""
    from scenario_network import jsonable
    S = sorted(set(members or []))
    if not S:
        raise ValueError("a coalition needs at least one member")
    if set(S) - set(COUNTRIES):
        raise ValueError(f"unknown countries {sorted(set(S) - set(COUNTRIES))}")
    import copy as _copy
    if inplace:
        n = network
    else:
        n = network.copy(); n.meta = _copy.deepcopy(network.meta)
    m = n.meta
    if m.get("research_coalition"):
        raise ValueError("the base network is already a coalition subnetwork")
    if m.get("research_countries") and sorted(m["research_countries"]) != list(COUNTRIES):
        raise ValueError("the base network is a coalition.remove_countries variant; derive coalitions from the integrated network")
    if m.get("scenario") != "integrated":
        raise ValueError(f"coalition subnetworks derive from the integrated network (scenario {m.get('scenario')!r})")
    bc = n.buses.country.astype(str)
    unknown = sorted(set(bc) - set(COUNTRIES) - {BUNKER})
    if unknown:
        raise ValueError(f"buses with an unknown country tag {unknown}")
    out_members = sorted(set(COUNTRIES) - set(S)); full = not out_members
    bus_country0 = bc.to_dict(); stores0 = set(n.stores.index)
    components_before = {c.name: int(len(c.df)) for c in n.iterate_components()}
    # --- base state (pre-existing dangling / dead-end / unreferenced items are left as they are) --------------------------------------
    one0, br0 = attachments(n)
    unattached0 = {b for b in n.buses.index if one0[b] == 0 and br0[b] == 0}
    deadend0 = {b for b in n.buses.index if one0[b] == 0 and br0[b] == 1}
    unref0, miss0 = unreferenced_carriers(n), missing_carriers(n)
    # --- R1 / R3 bus sets ---------------------------------------------------------------------------------------------------------
    r1_bus = set(n.buses.index[bc.isin(out_members)])
    asean = set(n.buses.index[bc == BUNKER])
    if not include_bunker:
        r3_bus = set(asean)
    elif full:
        r3_bus = set()
    else:   # bunker buses located at non-member nodes leave with the node; the account stays while a metering link remains (checked below)
        loc = n.buses.location.astype(str) if "location" in n.buses else pd.Series("", index=n.buses.index)
        r3_bus = {b for b in asean if b != BUNKER_STORE and str(bc.get(loc[b], "")) in out_members}
    gone_bus = r1_bus | r3_bus
    removed = defaultdict(lambda: defaultdict(list))   # rule -> component type -> names
    boundary = Counter(); boundary_rows = []
    demand = dict(R1_mwh=0.0, R3_mwh=0.0)
    for typ in ONE_PORT:
        df = n.df(typ)
        if not len(df):
            continue
        hit = df.index[df.bus.astype(str).isin(gone_bus)]
        for x in hit:
            rule = "R3_bunker" if str(df.at[x, "bus"]) in r3_bus else "R1_bus_country"
            removed[rule][typ].append(str(x))
        if typ == "Load" and len(hit):
            demand["R1_mwh"] = _weighted_load_mwh(n, [x for x in hit if str(df.at[x, "bus"]) in r1_bus])
            demand["R3_mwh"] = _weighted_load_mwh(n, [x for x in hit if str(df.at[x, "bus"]) in r3_bus])
    for typ in BRANCH:
        df = n.df(typ)
        if not len(df):
            continue
        P = port_columns(df)
        hit = df.index[df[P].astype(str).isin(gone_bus).any(axis=1)]
        for x in hit:
            pb = [str(df.at[x, p]) for p in P if _used(df.at[x, p])]
            if any(b in r3_bus for b in pb):
                rule = "R3_bunker"
            elif all(b in gone_bus for b in pb):
                rule = "R1_bus_country"
            else:
                rule = "R2_boundary"
                cty = tuple(sorted({str(bc[b]) for b in pb}))
                car = str(df.at[x, "carrier"]) if "carrier" in df else ""
                boundary[(typ, car)] += 1
                boundary_rows.append(dict(component_type=typ, component=str(x), carrier=car, countries=list(cty),
                                          asset_role=str(df.at[x, "asset_role"]) if "asset_role" in df else "",
                                          border_class=str(df.at[x, "border_class"]) if "border_class" in df else "",
                                          fixed_cost_constant_eur=fixed_cost_constant(n, typ, x)))
            removed[rule][typ].append(str(x))
    for rule in list(removed):
        for typ, names in removed[rule].items():
            if names:
                n.mremove(typ, names)
    for rule in ("R1_bus_country", "R3_bunker"):
        names = sorted(r1_bus if rule == "R1_bus_country" else r3_bus)
        if names:
            n.mremove("Bus", names); removed[rule]["Bus"] = names
    # --- R3 (subset with the bunker kept): the account needs a metering link; otherwise it leaves with its hook -----------------------
    acc_removed = not include_bunker
    if include_bunker and not full and BUNKER_STORE in n.stores.index:
        P = port_columns(n.links)
        if not n.links[P].astype(str).isin([BUNKER_STORE, str(n.stores.at[BUNKER_STORE, "bus"])]).any(axis=1).any():
            b = str(n.stores.at[BUNKER_STORE, "bus"]); n.mremove("Store", [BUNKER_STORE]); removed["R3_bunker"]["Store"].append(BUNKER_STORE)
            n.mremove("Bus", [b]); removed["R3_bunker"]["Bus"].append(b); acc_removed = True
    # --- R5 clean-up ------------------------------------------------------------------------------------------------------------
    dangling = []
    while True:
        one, br = attachments(n)
        d = sorted(b for b in n.buses.index if one[b] == 0 and br[b] == 0 and b not in unattached0)
        if not d:
            break
        n.mremove("Bus", d); dangling += d
    removed["R5_cleanup"]["Bus"] = dangling
    unref_new = sorted(unreferenced_carriers(n) - unref0)
    if unref_new:
        n.mremove("Carrier", unref_new)
    removed["R5_cleanup"]["Carrier"] = unref_new
    one, br = attachments(n)
    dead_new = []
    for b in sorted(x for x in n.buses.index if one[x] == 0 and br[x] == 1 and x not in deadend0):
        for typ in BRANCH:
            df = n.df(typ)
            if not len(df):
                continue
            P = port_columns(df)
            for x in df.index[df[P].astype(str).eq(b).any(axis=1)]:
                dead_new.append(dict(bus=b, bus_country=str(n.buses.at[b, "country"]), component_type=typ, component=str(x),
                                     carrier=str(df.at[x, "carrier"]) if "carrier" in df else "", fixed_cost_constant_eur=fixed_cost_constant(n, typ, x)))
    gone = {(typ, x) for rule in removed for typ, v in removed[rule].items() for x in v}
    # --- R6 metadata --------------------------------------------------------------------------------------------------------------
    mled = {}
    def drop_keys(key, typ):
        if isinstance(m.get(key), dict):
            before = len(m[key]); m[key] = {k: v for k, v in m[key].items() if (typ, k) not in gone}
            mled[key] = dict(before=before, after=len(m[key]))
    eu = m.get("existing_unit_components")
    if isinstance(eu, dict):
        keep = {u: z for u, z in eu.items() if (z["component_type"], z["component"]) not in gone}
        mled["existing_unit_components"] = dict(before=len(eu), after=len(keep))
        if len(keep) != len(eu):
            tot, seen = 0.0, set()
            for z in keep.values():
                k = (z["component_type"], z["component"])
                if k not in seen:
                    tot += float(n.df(k[0]).at[k[1], "existing_annual_fixed_om_eur"]); seen.add(k)
            mled["existing_annual_fixed_om_eur"] = dict(before=float(m.get("existing_annual_fixed_om_eur", 0.0)), after=tot)
            m["existing_unit_components"] = keep; m["existing_annual_fixed_om_eur"] = tot
    xb_removed = []
    if isinstance(m.get("existing_cross_border_fom_ledger"), list):
        led0 = m["existing_cross_border_fom_ledger"]
        keep = [r for r in led0 if (r["component_type"], r["component"]) not in gone]
        xb_removed = [dict(r) for r in led0 if (r["component_type"], r["component"]) in gone]
        for r in xb_removed:
            r["countries"] = next((list(z["countries"]) for z in boundary_rows if z["component"] == r["component"] and z["component_type"] == r["component_type"]), None)
        mled["existing_cross_border_fom_ledger"] = dict(before=len(led0), after=len(keep))
        if len(keep) != len(led0):
            mled["existing_cross_border_fom_eur"] = dict(before=float(m.get("existing_cross_border_fom_eur", 0.0)), after=float(sum(r["annual_fom_eur"] for r in keep)))
            m["existing_cross_border_fom_ledger"] = keep; m["existing_cross_border_fom_eur"] = float(sum(r["annual_fom_eur"] for r in keep))
    if isinstance(m.get("existing_resource_groups"), dict) and m["existing_resource_groups"]:
        groups = {}
        for g, e in m["existing_resource_groups"].items():
            c = [x for x in e.get("candidates", []) if (x["ComponentType"], x["Name"]) not in gone]
            if c:
                groups[g] = dict(e, candidates=c)
        mled["existing_resource_groups"] = dict(before=len(m["existing_resource_groups"]), after=len(groups)); m["existing_resource_groups"] = groups
    if isinstance(m.get("battery_inverter_pairs"), list):
        before = len(m["battery_inverter_pairs"])
        m["battery_inverter_pairs"] = [p for p in m["battery_inverter_pairs"] if ("Link", p.get("charger")) not in gone and ("Link", p.get("discharger")) not in gone]
        mled["battery_inverter_pairs"] = dict(before=before, after=len(m["battery_inverter_pairs"]))
    drop_keys("store_power_rules", "Store"); drop_keys("external_annual_caps", "Generator")
    drop_keys("demand_owners", "Load"); drop_keys("demand_identity", "Load")
    if isinstance(m.get("research_new_hydro_inflow_tie"), list):
        before = len(m["research_new_hydro_inflow_tie"])
        m["research_new_hydro_inflow_tie"] = [x for x in m["research_new_hydro_inflow_tie"] if ("StorageUnit", x) not in gone]
        mled["research_new_hydro_inflow_tie"] = dict(before=before, after=len(m["research_new_hydro_inflow_tie"]))
    for key in ("physical_carbon_map", "existing_carbon_components"):
        if isinstance(m.get(key), list):
            before = len(m[key]); m[key] = [r for r in m[key] if (str(r.get("component_type", "Link")), str(r.get("component"))) not in gone]
            mled[key] = dict(before=before, after=len(m[key]))
    if isinstance(m.get("research_dedicated_lines"), dict) and isinstance(m["research_dedicated_lines"].get("lines"), list):
        dl = m["research_dedicated_lines"]; before = len(dl["lines"])
        dl["lines"] = [r for r in dl["lines"] if ("Link", r.get("link")) not in gone]; dl["links"] = len(dl["lines"])
        mled["research_dedicated_lines"] = dict(before=before, after=len(dl["lines"]))
    if not full:
        if isinstance(m.get("research_co2_storage"), dict):
            cs = m["research_co2_storage"]
            for k in ("caps_t_per_year", "potentials_gt"):
                if isinstance(cs.get(k), dict):
                    cs[k] = {c: v for c, v in cs[k].items() if c in S}
            mled["research_co2_storage"] = dict(countries=sorted(cs.get("caps_t_per_year", {})))
        if isinstance(m.get("research_carbon"), dict) and isinstance(m["research_carbon"].get("country_cap_tco2"), dict):
            m["research_carbon"]["country_cap_tco2"] = {c: v for c, v in m["research_carbon"]["country_cap_tco2"].items() if c in S}
            mled["research_carbon"] = dict(countries=sorted(m["research_carbon"]["country_cap_tco2"]))
        if isinstance(m.get("research_extra_asean_storage"), dict) and isinstance(m["research_extra_asean_storage"].get("countries"), dict):
            m["research_extra_asean_storage"]["countries"] = {c: v for c, v in m["research_extra_asean_storage"]["countries"].items() if c in S}
            mled["research_extra_asean_storage"] = dict(countries=sorted(m["research_extra_asean_storage"]["countries"]))
        if isinstance(m.get("research_nuclear_caps"), dict):
            m["research_nuclear_caps"] = {c: v for c, v in m["research_nuclear_caps"].items() if c in S}
        m["research_countries"] = list(S)
    bunker_meta = None
    if acc_removed and (m.get("research_bunkers") is not None or BUNKER_HOOK in m.get("required_constraint_hooks", [])):
        rb = m.pop("research_bunkers", None) or {}
        bunker_meta = dict(removed=True, mode=rb.get("mode"), account_ports=len((rb.get("account") or {}).get("ports", [])), asean_loads=len(rb.get("asean_loads", {})))
        m["required_constraint_hooks"] = [h for h in m.get("required_constraint_hooks", []) if h != BUNKER_HOOK]
    elif include_bunker and not full and isinstance(m.get("research_bunkers"), dict):
        rb = m["research_bunkers"]
        if isinstance(rb.get("account"), dict):
            rb["account"]["ports"] = [p for p in rb["account"].get("ports", []) if ("Link", p.get("link")) not in gone]
        if isinstance(rb.get("asean_loads"), dict):
            rb["asean_loads"] = {k: v for k, v in rb["asean_loads"].items() if ("Load", k) not in gone}
        bunker_meta = dict(removed=False, account_ports=len(rb["account"]["ports"]), asean_loads=len(rb["asean_loads"]))
    mled["required_constraint_hooks"] = sorted(m.get("required_constraint_hooks", []))
    # --- retained cross-border facilities and transit links ---------------------------------------------------------------------
    retained = []
    for typ in ("Line", "Transformer", "Link"):
        df = n.df(typ)
        if not len(df):
            continue
        for x in df.index:
            cty = [c for c in branch_countries(n, typ, x) if c != BUNKER]
            if len(cty) >= 2:
                nom = "s_nom" if typ in ("Line", "Transformer") else "p_nom"
                retained.append(dict(component_type=typ, component=str(x), carrier=str(df.at[x, "carrier"]), countries=cty, existing_mw=float(df.at[x, nom]),
                                     extendable=bool(df.at[x, nom + "_extendable"]), asset_role=str(df.at[x, "asset_role"]) if "asset_role" in df else "",
                                     border_class=str(df.at[x, "border_class"]) if "border_class" in df else ""))
    transit = []
    via_table = {str(r.get("node")): str(r.get("via")) for r in ((m.get("research_lao_vn_store") or {}).get("table") or []) if isinstance(r, dict)}
    for x in n.links.index:
        v = str(n.links.at[x, "via_coastal_node"]) if "via_coastal_node" in n.links else ""
        src = "via_coastal_node"
        if not _used(v) and str(n.links.at[x, "carrier"]) == "CO2 transit export extra-ASEAN":   # Lao export to its own extra-ASEAN store: rail to the coast of
            v = via_table.get(str(n.buses.at[str(n.links.at[x, "bus0"]), "location"]) if "location" in n.buses else "", "")   # research_lao_vn_store.table
            src = "research_lao_vn_store.table (same land leg)"
        if _used(v) and str(bus_country0.get(v, "")) in out_members:
            transit.append(dict(component=str(x), carrier=str(n.links.at[x, "carrier"]), via_coastal_node=v, via_country=str(bus_country0[v]), via_source=src,
                                countries=list(branch_countries(n, "Link", x))))
    # --- invariants ---------------------------------------------------------------------------------------------------------------
    allowed = set(S) | ({BUNKER} if include_bunker else set())
    if not include_bunker and (n.buses.country.astype(str) == BUNKER).any():
        raise AssertionError("bunker buses remain although include_bunker=False")
    bad_bus = sorted(set(n.buses.country.astype(str)) - allowed)
    if bad_bus:
        raise AssertionError(f"buses of countries outside the coalition remain: {bad_bus}")
    for c in n.iterate_components(list(ONE_PORT) + list(BRANCH)):
        if not len(c.df):
            continue
        for p in port_columns(c.df):
            v = c.df[p].astype(str); bad = v[v.map(_used) & ~v.isin(n.buses.index)]
            if len(bad):
                raise AssertionError(f"{c.name} {list(bad.index[:3])} references a missing bus ({p})")
    for typ in BRANCH:
        df = n.df(typ)
        for x in (list(df.index) if len(df) else []):
            if not set(branch_countries(n, typ, x)) <= allowed:
                raise AssertionError(f"{typ} {x} crosses the coalition boundary")
    if "country" in n.loads:
        lc = set(n.loads.country.astype(str)) - allowed - {"", "nan"}
        if lc:
            raise AssertionError(f"loads tagged with non-member countries {sorted(lc)}")
    from carrier_architecture import atmosphere_bus, network_countries
    if sorted(network_countries(n)) != S:
        raise AssertionError("network_countries differs from the members")
    miss_atm = [c for c in S if atmosphere_bus(c) in stores0 and atmosphere_bus(c) not in n.stores.index]
    if miss_atm:
        raise AssertionError(f"national atmosphere Store missing for {miss_atm}")
    if "reversed" in n.links:
        rev = n.links.index[n.links.reversed.astype(bool)]
        orphan = [x for x in rev if x.endswith("-reversed") and x[: -len("-reversed")] not in n.links.index]
        if orphan:
            raise AssertionError(f"reversed links without their forward twin {orphan[:3]}")
    for key, typ in (("store_power_rules", "Store"), ("external_annual_caps", "Generator"), ("demand_owners", "Load")):
        if isinstance(m.get(key), dict) and [k for k in m[key] if k not in n.df(typ).index and (typ, k) in gone]:
            raise AssertionError(f"meta {key} still names a removed component")
    if missing_carriers(n) - miss0:
        raise AssertionError(f"components reference carriers that are not in n.carriers: {sorted(missing_carriers(n) - miss0)[:5]}")
    if len(n.global_constraints):   # R4: the v4 network has none; a row naming a removed carrier / bus would be refused here
        raise AssertionError("GlobalConstraint rows present: rule R4 has no handling for them (the v4 main network has none)")
    by_rule = {r: {t: len(v) for t, v in d.items() if v} for r, d in removed.items()}
    ledger = dict(script=SCRIPT, rules_version=RULES_VERSION, decision="228 (definition decision 133 (2)a)", members=S, non_members=out_members,
                  include_bunker=bool(include_bunker), bunker_account_removed=bool(acc_removed), full_coalition=bool(full),
                  removed_by_rule=by_rule, removed_total={t: int(sum(by_rule[r].get(t, 0) for r in by_rule)) for t in sorted({t for d in by_rule.values() for t in d})},
                  boundary_by_carrier={f"{t}|{c}": k for (t, c), k in sorted(boundary.items())}, boundary_components=boundary_rows,
                  existing_cross_border_fom_removed=xb_removed, existing_cross_border_fom_removed_eur=float(sum(r["annual_fom_eur"] for r in xb_removed)),
                  existing_cross_border_fom_boundary_eur=float(sum(r["annual_fom_eur"] for r in xb_removed if r.get("countries"))),
                  d8_addback_eur=0.5 * float(sum(r["annual_fom_eur"] for r in xb_removed if r.get("countries"))),   # M12 supplement 01 D8: the members' alpha-0.5 share of the removed boundary stock FOM
                  dangling_buses_removed=dangling, carriers_removed=unref_new, dead_end_member_components_kept=dead_new,
                  dead_end_fixed_cost_constant_eur=float(sum(r["fixed_cost_constant_eur"] for r in dead_new)),
                  base_preexisting=dict(unattached_buses=len(unattached0), dead_end_buses=len(deadend0), unreferenced_carriers=len(unref0)),
                  retained_cross_border=retained, retained_cross_border_by_carrier=dict(Counter(f"{r['component_type']}|{r['carrier']}" for r in retained)),
                  retained_cross_border_stock=[r for r in retained if r["existing_mw"] > 0 and (r["component_type"] != "Link" or r["carrier"] in PHYSICAL_XB)],
                  retained_cross_border_trade_links=dict(Counter(r["carrier"] for r in retained if r["component_type"] == "Link" and r["carrier"] not in PHYSICAL_XB)),
                  transit_via_non_member=transit, demand_removed_mwh=demand, bunker=bunker_meta, meta=mled,
                  components_before=components_before, components_after={c.name: int(len(c.df)) for c in n.iterate_components()})
    m["research_coalition"] = jsonable(dict(members=S, non_members=out_members, include_bunker=bool(include_bunker), rules_version=RULES_VERSION, script=SCRIPT,
                                            decision="228", removed_by_rule=by_rule, retained_cross_border=len(retained),
                                            retained_cross_border_stock=len(ledger["retained_cross_border_stock"]), solver_runs=0))
    return n, ledger


# ------------------------------------------------------------------------------------------------------------------------- comparison
def _same(a: pd.Series, b: pd.Series) -> bool:
    if a.dtype.kind in "fc" or b.dtype.kind in "fc":
        x, y = pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce")
        return bool(((x == y) | (x.isna() & y.isna())).all())
    return bool((a.astype(str) == b.astype(str)).all())


def network_diff(n1, n2, ignore_meta=("research_coalition",)) -> dict:
    """component sets, every static column, every time series (exact), snapshots + weightings and metadata (keys in ignore_meta left out)."""
    out = dict(sets={}, static={}, series={})
    names = sorted({c.name for c in n1.iterate_components()} | {c.name for c in n2.iterate_components()})
    for c in names:
        a, b = n1.df(c), n2.df(c)
        if c == "SubNetwork":
            continue
        if set(a.index) != set(b.index):
            out["sets"][c] = dict(only_1=sorted(map(str, set(a.index) - set(b.index)))[:20], only_2=sorted(map(str, set(b.index) - set(a.index)))[:20],
                                  n_only_1=len(set(a.index) - set(b.index)), n_only_2=len(set(b.index) - set(a.index)))
        idx = a.index.intersection(b.index)
        for col in sorted(set(a.columns) | set(b.columns)):
            if col not in a.columns or col not in b.columns:
                out["static"].setdefault(c, {})[col] = "column only in one network"; continue
            if not _same(a.loc[idx, col], b.loc[idx, col]):
                out["static"].setdefault(c, {})[col] = "values differ"
        pa, pb = n1.pnl(c), n2.pnl(c)
        for k in sorted(set(pa) | set(pb)):
            ta, tb = pa.get(k, pd.DataFrame()), pb.get(k, pd.DataFrame())
            cols = sorted(set(ta.columns) | set(tb.columns))
            if not cols:
                continue
            if set(ta.columns) != set(tb.columns) or not np.array_equal(ta[cols].to_numpy(), tb[cols].to_numpy(), equal_nan=True):
                out["series"].setdefault(c, {})[k] = "differ"
    out["snapshots_and_weightings_equal"] = bool(n1.snapshots.equals(n2.snapshots) and n1.snapshot_weightings.equals(n2.snapshot_weightings))
    keys = sorted((set(n1.meta) | set(n2.meta)) - set(ignore_meta))
    out["meta_keys_differing"] = [k for k in keys if json.dumps(n1.meta.get(k), sort_keys=True, default=str) != json.dumps(n2.meta.get(k), sort_keys=True, default=str)]
    out["identical"] = (not out["sets"]) and (not out["static"]) and (not out["series"]) and out["snapshots_and_weightings_equal"] and not out["meta_keys_differing"]
    return out


def cut(n, snapshots: int) -> dict:
    """the s2_solve.py --truncate rule (first N snapshots + set_representative_weights), as W14 / D2c cut56."""
    from s2_solve import set_representative_weights
    n.set_snapshots(n.snapshots[:snapshots])
    return set_representative_weights(n)


# ------------------------------------------------------------------------------------------------------------------------------- CLI
def build(base: Path, out: Path, name: str, members, include_bunker: bool, truncate: int, expect_sha: str | None = None) -> dict:
    import pypsa
    import logging
    from network_checks import compare_roundtrip
    from scenario_network import jsonable
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise SystemExit("run with PYTHONHASHSEED=0 (deterministic NetCDF export)")
    base = Path(base).resolve(); out = Path(out); out.mkdir(parents=True, exist_ok=True)
    bsha = sha(base)
    if expect_sha and not bsha.startswith(expect_sha):
        raise SystemExit(f"base SHA256 {bsha} differs from the expected {expect_sha}")
    n = pypsa.Network(str(base))
    n, led = coalition_subnetwork(n, members, include_bunker, inplace=True)
    res = f"{truncate}" if truncate else {2920: "2920_3h", 365: "365_24h"}.get(int(len(n.snapshots)), str(len(n.snapshots)))
    scaling = cut(n, truncate) if truncate else None
    n.meta["research_coalition"] = jsonable(dict(n.meta["research_coalition"], name=name, base=dict(file=base.name, sha256=bsha),
                                                 truncate=int(truncate or 0), truncation_rule=("s2_solve.py --truncate rule: first N snapshots + set_representative_weights" if truncate else None)))
    path = out / f"{name}_{res}_unsolved.nc"
    n.export_to_netcdf(path)
    back = pypsa.Network(str(path)); compare_roundtrip(n, back)
    receipt = dict(status="W20_COALITION_NETWORK_BUILT", script=SCRIPT, script_sha256=sha(HERE / "v4_coalition.py"), name=name,
                   base=dict(path=str(base), sha256=bsha), output=dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size, snapshots=int(len(n.snapshots))),
                   truncate=int(truncate or 0), truncation=scaling, ledger=led, solver_runs=0)
    (out / f"{name}_{res}_COALITION_RECEIPT.json").write_text(json.dumps(jsonable(receipt), indent=1, sort_keys=True, default=str) + "\n")
    return receipt


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    b = sub.add_parser("build")
    b.add_argument("--base", type=Path, required=True); b.add_argument("--out", type=Path, required=True)
    b.add_argument("--coalition", choices=COALITION_ORDER, default=None); b.add_argument("--members", default=None, help="comma-separated ISO2 codes")
    b.add_argument("--name", default=None); b.add_argument("--include-bunker", action="store_true")
    b.add_argument("--truncate", type=int, default=0, help="cut to the first N snapshots with the s2_solve.py --truncate rule after the subnetwork")
    b.add_argument("--expect-base-sha256", default=None)
    a = p.parse_args(argv)
    if a.cmd == "list":
        for k in COALITION_ORDER:
            print(k, ",".join(coalitions()[k]))
        return 0
    if bool(a.coalition) == bool(a.members):
        p.error("give exactly one of --coalition / --members")
    members = coalitions()[a.coalition] if a.coalition else [x.strip() for x in a.members.split(",") if x.strip()]
    name = a.name or a.coalition
    if not name:
        p.error("--name is required with --members")
    r = build(a.base, a.out, name, members, a.include_bunker, a.truncate, a.expect_base_sha256)
    L = r["ledger"]
    print(json.dumps(dict(output=r["output"]["path"], sha256=r["output"]["sha256"], members=L["members"], removed_total=L["removed_total"],
                          boundary=sum(L["boundary_by_carrier"].values()), retained_cross_border=len(L["retained_cross_border"]),
                          retained_stock=len(L["retained_cross_border_stock"]), dangling=len(L["dangling_buses_removed"]), carriers_removed=len(L["carriers_removed"]),
                          dead_end_kept=len(L["dead_end_member_components_kept"]), transit_via_non_member=len(L["transit_via_non_member"])), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
