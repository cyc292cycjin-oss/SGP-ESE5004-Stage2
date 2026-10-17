"""S4F model layers (S4F instruction v1, 2026-10-17; decisions 96-97).

S4F-1 (decision 96): research.network.max_extension = pypsa_eur (main) | none (former state, comparison; default when absent) | apg_plans
(conservative sensitivity, built and checked, not run).
  * pypsa_eur: PyPSA-Eur v2025.07.0 prepare_sector_network.py limit_individual_line_extension (lines 5573-5577), called at lines 6415-6417 with
    config lines.max_extension = 20000 MW (config.default.yaml line 324): s_nom_max = s_nom + 20000 for every line and p_nom_max = p_nom + 20000
    for every link of carrier DC (B2B links and pipelines excluded) - an increment over the existing capacity, one value for AC and DC.
    links.max_extension (30000 MW, line 340) is not read by the sector workflow and is not used (user decision 2026-10-17). Same rule in both
    scenarios, cross-border and domestic, stock and new candidates. PyPSA-Eur sets no individual cap on new H2 / CO2 / gas pipelines
    (add_co2_network, H2_network, gas_network_connectivity_upgrade), so none is set here.
  * apg_plans: the pypsa_eur caps, plus one constraint per APG / AIMS project with a planned or projected capacity
    (research.network.apg_plan_caps_table, scripts_project/s4f_1_data.py): sum of s_nom / p_nom of the lines / DC links joining the two areas of
    the project <= max(2025 stock of those components, plan cap), installed by the research_apg_corridor_cap hook. Projects without data (TBC)
    keep the pypsa_eur caps.
S4F-2 (decision 97):
  * a: research.network.th_my_stock = apg_aims (main) | frozen_base (comparison). apg_aims applies research.network.th_my_stock_table
    (TH_MY_STOCK_S4F2.csv): the four OSM 250878579 HVDC records (duplicates of Khlong Ngae - Gurun) are removed, line 91 is set to 80 MW
    (s_nom and s_nom_min; num_parallel and impedance unchanged; grade C, cluster artefact - see S4F_STOP_01_LINE91.md), Khlong Ngae - Gurun keeps
    300 MW (AIMS); TH-MY 2025 total 380 MW = APG. The corridor table is corrected the same way in memory. The frozen base file is not modified.
  * c: research.co2.lao_transit_vn_store = on (main) | off (default when absent): after the rail transit to a Vietnamese coastal node, Lao CO2
    can enter the Vietnamese national store 'co2 sequestered VN' (inside its annual cap, VN store unit cost on the store); link
    '<node> co2 transit to VN store', carrier 'CO2 transit rail', marginal cost = the land leg; trade (border_class maritime_trade, the trade
    class of decision 92: not network, outside B5 and the cross-border switches), both scenarios.
  * d: research.corridors.optional_sg_vn_kh = off (main) | on (second-batch sensitivity): the two 'other initiative' DC candidates SG-VN and
    SG-KH (research.corridors.optional_table_s4f2) are appended to the corridor table.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
APG_CAP_HOOK = "research_apg_corridor_cap"
TRANSIT_RAIL_CARRIER = "CO2 transit rail"
MAX_EXTENSION_PARAM = "pypsa_eur_lines_max_extension"


def _net(cfg) -> dict:
    return cfg["research"].get("network", {}) or {}


def _flag(v, allowed, key):
    v = {True: "on", False: "off"}.get(v, v) if isinstance(v, bool) else str(v).lower()
    if v not in allowed:
        raise ValueError(f"Unknown {key} {v}")
    return v


def max_extension_mode(cfg) -> str:
    return _flag(_net(cfg).get("max_extension", "none"), ("pypsa_eur", "none", "apg_plans"), "research.network.max_extension")


def _area_of(bus: str, areas) -> str | None:
    hits = [a for a in areas if bus.startswith(a)]
    return max(hits, key=len) if hits else None


def apg_plan_groups(n, table: pd.DataFrame) -> dict:
    """APG project -> lines / DC links joining its two areas (node-name prefixes) and the cap max(stock, plan)."""
    areas = sorted(set(table.area_a) | set(table.area_b))
    comps = [("Line", k, z.bus0, z.bus1, float(z.s_nom_min)) for k, z in n.lines.iterrows()]
    comps += [("Link", k, z.bus0, z.bus1, float(z.p_nom_min)) for k, z in n.links[n.links.carrier == "DC"].iterrows()]
    out, seen = {}, {}
    for _, r in table.iterrows():
        pair = {str(r.area_a), str(r.area_b)}
        g = [(t, k, s) for t, k, b0, b1, s in comps if {_area_of(str(b0), areas), _area_of(str(b1), areas)} == pair]
        if not g:
            continue
        for t, k, _ in g:
            if (t, k) in seen:
                raise ValueError(f"{t} {k} in APG groups {seen[(t, k)]} and {r.apg_no}")
            seen[(t, k)] = str(r.apg_no)
        stock = sum(s for _, _, s in g); plan = float(r.plan_cap_mw)
        out[str(r.apg_no)] = dict(project=str(r.project), areas=sorted(pair), plan_cap_mw=plan, stock_2025_mw=stock, cap_mw=max(stock, plan),
                                  plan_basis=str(r.plan_basis), lines=[k for t, k, _ in g if t == "Line"], links=[k for t, k, _ in g if t == "Link"])
    return out


def apply_max_extension(n, cfg, registry: pd.DataFrame, repo: Path = ROOT) -> dict:
    """S4F-1 (decision 96): see the module docstring. Call after the cross-border switches (the remaining lines / DC links)."""
    mode = max_extension_mode(cfg); led = dict(mode=mode)
    if mode == "none":
        n.meta["research_max_extension"] = led
        return led
    maxext = float(registry.loc[MAX_EXTENSION_PARAM, "value"])
    dc = n.links.index[n.links.carrier == "DC"]
    n.lines["s_nom_max"] = n.lines["s_nom"] + maxext
    n.links.loc[dc, "p_nom_max"] = n.links.loc[dc, "p_nom"] + maxext
    if (n.lines.s_nom_min > n.lines.s_nom_max).any() or (n.links.loc[dc, "p_nom_min"] > n.links.loc[dc, "p_nom_max"]).any():
        raise ValueError("individual extension cap below the 2025 lower bound")
    led.update(max_extension_mw=maxext, source="PyPSA-Eur v2025.07.0 config lines.max_extension (line 324); prepare_sector_network.py 5573-5577, 6415-6417",
               lines=int(len(n.lines)), lines_extendable=int(n.lines.s_nom_extendable.sum()), dc_links=int(len(dc)), dc_links_extendable=int(n.links.loc[dc, "p_nom_extendable"].sum()),
               not_capped="B2B links; H2 / CO2 / gas pipelines (no individual cap in PyPSA-Eur)")
    if mode == "apg_plans":
        table = pd.read_csv(repo / str(_net(cfg)["apg_plan_caps_table"]), dtype={"apg_no": str})
        groups = apg_plan_groups(n, table)
        n.meta["research_apg_corridor_caps"] = groups
        n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {APG_CAP_HOOK})
        led.update(apg_groups=len(groups), apg_table=str(_net(cfg)["apg_plan_caps_table"]),
                   apg_caps={g: dict(cap_mw=v["cap_mw"], stock_2025_mw=v["stock_2025_mw"], components=len(v["lines"]) + len(v["links"])) for g, v in groups.items()})
    n.meta["research_max_extension"] = led
    return led


def install_apg_corridor_cap(n):
    """research_apg_corridor_cap hook: sum(s_nom of the group's lines) + sum(p_nom of its DC links) <= cap per APG project group."""
    if getattr(n, "_research_apg_cap_model", None) is n.model:
        raise ValueError("APG corridor cap hook already installed")
    m = n.model; added = 0
    for g, v in n.meta.get("research_apg_corridor_caps", {}).items():
        terms = []
        if v["lines"] and "Line-s_nom" in m.variables:
            ln = [x for x in v["lines"] if x in m["Line-s_nom"].coords["Line-ext"].values]
            if ln:
                terms.append(m["Line-s_nom"].sel({"Line-ext": ln}).sum())
        if v["links"] and "Link-p_nom" in m.variables:
            lk = [x for x in v["links"] if x in m["Link-p_nom"].coords["Link-ext"].values]
            if lk:
                terms.append(m["Link-p_nom"].sel({"Link-ext": lk}).sum())
        if terms:
            lhs = terms[0] if len(terms) == 1 else terms[0] + terms[1]
            m.add_constraints(lhs <= float(v["cap_mw"]), name=f"{APG_CAP_HOOK}-{g}"); added += 1
    n._research_apg_cap_model = m
    return added


def th_my_stock_mode(cfg) -> str:
    return _flag(_net(cfg).get("th_my_stock", "frozen_base"), ("apg_aims", "frozen_base"), "research.network.th_my_stock")


def apply_th_my_stock(n, corridors: pd.DataFrame, cfg, repo: Path = ROOT):
    """S4F-2 a (decision 97 a): returns (corridor table, ledger). Checks the frozen-base values before changing them."""
    mode = th_my_stock_mode(cfg); led = dict(mode=mode)
    if mode == "frozen_base":
        n.meta["research_th_my_stock"] = led
        return corridors, led
    path = str(_net(cfg)["th_my_stock_table"])
    t = pd.read_csv(repo / path, dtype={"component": str})
    corridors = corridors.copy(); rows = []
    for _, r in t.iterrows():
        typ, name = str(r.component_type), str(r.component)
        df = n.df(typ)
        if name not in df.index:
            raise ValueError(f"TH-MY correction: {typ} {name} not in the frozen base")
        nom = "s_nom" if typ == "Line" else "p_nom"
        before = float(df.at[name, nom + "_min"])
        if abs(before - float(r.frozen_base_mw)) > 1e-6:
            raise ValueError(f"TH-MY correction: {typ} {name} has {before} MW, table says {r.frozen_base_mw}")
        sel = (corridors.component_type == typ) & (corridors.component.astype(str) == name)
        if r.action == "remove":
            n.mremove(typ, [name]); corridors = corridors[~sel]
        elif r.action == "set_capacity":
            v = float(r.corrected_mw)
            df.loc[name, [nom, nom + "_min"]] = v
            corridors.loc[sel, "capacity_2025_mw"] = v; corridors.loc[sel, "nominal_mw_in_base"] = v
        elif r.action != "keep":
            raise ValueError("unknown TH-MY action " + str(r.action))
        rows.append(dict(component_type=typ, component=name, action=str(r.action), frozen_base_mw=before, corrected_mw=float(r.corrected_mw), grade=str(r.grade)))
    led.update(table=path, rows=rows, th_my_total_before_mw=float(sum(x["frozen_base_mw"] for x in rows)), th_my_total_after_mw=float(sum(x["corrected_mw"] for x in rows)))
    n.meta["research_th_my_stock"] = led
    return corridors.reset_index(drop=True), led


def optional_corridor_mode(cfg) -> str:
    return _flag((cfg["research"].get("corridors") or {}).get("optional_sg_vn_kh", "off"), ("on", "off"), "research.corridors.optional_sg_vn_kh")


def extend_optional_corridors(corridors: pd.DataFrame, cfg, repo: Path = ROOT):
    """S4F-2 d (decision 97 d): SG-VN / SG-KH DC candidates appended with optional_sg_vn_kh = on (second-batch sensitivity)."""
    mode = optional_corridor_mode(cfg); led = dict(mode=mode, added=[])
    if mode == "on":
        path = str(cfg["research"]["corridors"]["optional_table_s4f2"])
        opt = pd.read_csv(repo / path, float_precision="round_trip")
        if set(opt.component.astype(str)) & set(corridors.component.astype(str)):
            raise ValueError("optional corridor already in the corridor table")
        corridors = pd.concat([corridors, opt], ignore_index=True)
        led.update(table=path, added=list(opt.component.astype(str)))
    return corridors, led


def lao_vn_store_mode(cfg) -> str:
    return _flag((cfg["research"].get("co2") or {}).get("lao_transit_vn_store", "off"), ("on", "off"), "research.co2.lao_transit_vn_store")


def apply_lao_vn_store(n, cfg, registry: pd.DataFrame) -> dict:
    """S4F-2 c (decision 97 c): see the module docstring. Only LA nodes whose transit ends at a Vietnamese coastal node get the link."""
    from s2_layers import add_link
    from s4e_layers import lao_transit_legs
    mode = lao_vn_store_mode(cfg); led = dict(mode=mode, links=0)
    if mode == "off":
        n.meta["research_lao_vn_store"] = led
        return led
    if "co2 sequestered VN" not in n.buses.index or not ((n.stores.carrier == "co2 sequestered") & (n.stores.country == "VN")).any():
        raise ValueError("research.co2.lao_transit_vn_store = on needs the Vietnamese national store")
    legs = lao_transit_legs(cfg, registry); years = float(cfg["research"]["s2"]["co2"]["storage_years"]); rows, skipped = [], []
    for node, g in sorted(legs.items()):
        if f"{node} co2 stored" not in n.buses.index:
            continue
        cn = g["coastal_node"]
        if str(n.buses.at[cn, "country"]) != "VN":
            skipped.append(dict(node=node, coastal_node=cn, reason="transit ends outside Viet Nam")); continue
        add_link(n, f"{node} co2 transit to VN store", "LA", TRANSIT_RAIL_CARRIER, [f"{node} co2 stored", "co2 sequestered VN"], [1.0], capital_cost=0.0,
                 marginal_cost=g["land_cost"], lifetime=years, role="CO2_TRANSIT",
                 extra={"via_coastal_node": cn, "land_leg_eur_per_t": g["land_cost"], "trade_class": "land transit trade (decision 97 c)",
                        "carbon_rule": "transited captured CO2 counts as abatement of LA (decision 20); stored in the Vietnamese national store, inside its annual cap (decision 28)"})
        rows.append(dict(node=node, via=cn, land=g["land_cost"]))
    led.update(links=len(rows), skipped=skipped, destination=next(iter(legs.values()))["destination"] if legs else None,
               transport_mode=next(iter(legs.values()))["mode"] if legs else None,
               land_leg_range=([round(min(x["land"] for x in rows), 3), round(max(x["land"] for x in rows), 3)] if rows else None), table=rows)
    n.meta["research_lao_vn_store"] = led
    return led


def lao_vn_store_report(n) -> dict:
    """Post-solve (S4F-2 c): tonnes and land freight per LA node into the Vietnamese national store; flows below 1 t / year not listed."""
    sl = n.links[n.links.carrier == TRANSIT_RAIL_CARRIER]
    w = n.snapshot_weightings.objective; out = {}
    for k, z in sl.iterrows():
        t = float((n.links_t.p0[k] * w).sum()) if k in n.links_t.p0 else 0.0
        if t > 1.0:
            out[str(z.bus0).split(" co2")[0]] = dict(t=t, freight_eur=t * float(z.marginal_cost), link=k)
    return out
