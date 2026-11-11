"""S4A-2 (L15): add the GEM units that are in service in 2050 but absent from the frozen electric base (research.fleet).

Input table research_inputs/fleet_v5/FLEET_ADDITIONS_2050.csv (scripts_project/s4a_2_fleet_data.py): GEM GIPT 2026-09 units,
operating (+ construction when research.fleet.include_construction) with start year + S1 lifetime > 2050, not matched to an
existing-unit identity, mapped to the nearest AC node of their country. Units are aggregated per node and model class into one
component `existing_survivor::<node>::<class>::S4A`; every GEM unit is recorded in n.meta["existing_unit_components"] so that the
static validation (capacity identity, no CAPEX, not extendable) and the FOM-once rule apply unchanged.

Representation (same conventions as the frozen stock):
  coal / lignite / oil / CCGT / OCGT existing  Link <node> <fuel> -> <node> (+ national atmosphere), p_nom = MW_el / efficiency,
       efficiency, FOM (%/a x investment, EUR/MW_el/a, objective constant) and VOM (marginal_cost = VOM x efficiency per MWh fuel)
       from technology-data v0.15.0 (grade B); CO2 port = fuel CO2 intensity (technology-data)
  geothermal existing  Generator, availability 0.7194 and FOM/VOM from AEO8 (decision 52, grade C)
  solar / onwind / offwind existing  Generator, availability = the node candidate profile of the same carrier (research.renewable
       variant), FOM technology-data (grade B)
  hydro existing  StorageUnit, inflow per MW and max_hours copied from the node (else country) existing reservoir units (grade C
       proxy), efficiency_dispatch 0.9, FOM technology-data hydro
  ror existing  Generator, p_max_pu from the node (else country) existing run-of-river units (grade C proxy), FOM technology-data ror
  PHS existing  StorageUnit, 6 h (decision proxy of the existing PHS), round-trip 0.75 (technology-data PHS), FOM technology-data
  waste existing  not added (no waste-to-energy fuel pathway in the model; listed as DATA_PENDING in the ledger)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from s2_layers import cost, country_of, ensure_carrier

FUEL_OF = {"coal existing": ("coal", "coal"), "lignite existing": ("lignite", "lignite"), "oil existing": ("oil", "oil"), "CCGT existing": ("gas", "CCGT"), "OCGT existing": ("gas", "OCGT")}
AEO8_GEOTHERMAL_CF = 0.719443559520017   # S2-1 (decision 52): AEO8 C.4/C.5 27.1 TWh / (4.3 GW x 8.76)


def _atmo(n, c):
    from carrier_architecture import atmosphere_bus
    return atmosphere_bus(c)


def add_gem_fleet(n, costs, cfg, repo: Path):
    F = dict(cfg["research"].get("fleet") or {})
    led = dict(enabled=bool(F.get("gem_additions", False)), added=[], skipped=[], fom_eur=0.0, by_class_mw={})
    if not led["enabled"]:
        n.meta["research_fleet"] = led
        return led
    table = Path(repo) / str(F.get("table", "research_inputs/fleet_v5/FLEET_ADDITIONS_2050.csv"))
    import v5_common as V5
    s5 = V5.switches(cfg)
    rule = (s5["lifetime_boundary"], int(s5["geothermal_existing_lifetime"]))
    if s5["enabled"] and rule != ("strict", 30):   # V5 X20 (2-5, decisions 244, 246 Q2 (b)): GEM additions of the v5 lifetime rule (s4a_2_fleet_data.py --v5-out)
        table = table.with_name(table.stem + ("_V5" if rule == ("inclusive", 40) else f"_V5_{rule[0]}_L{rule[1]}") + table.suffix)
        if not table.exists():
            raise FileNotFoundError(f"{table} missing: run scripts_project/s4a_2_fleet_data.py --boundary {rule[0]} --geothermal-lifetime {rule[1]} --v5-out")
        led["v5_lifetime_rule"] = list(rule)
    df = pd.read_csv(table, keep_default_na=False)
    df["capacity_mw"] = df.capacity_mw.astype(float); df["start_year"] = df.start_year.astype(float)
    df["batch"] = "S4A"; df["age_basis"] = "SOURCE_UNIT_YEAR"
    if not bool(F.get("include_construction", True)):
        df = df[df.Status == "operating"]
    import hashlib
    led["table"] = dict(path=str(table.relative_to(repo)), sha256=hashlib.sha256(table.read_bytes()).hexdigest(), units=int(len(df)), mw=float(df.capacity_mw.sum()))
    # S4B-1 (decision 77): GEM units under construction without a start year (start >= 2026 from the 2026-09 status) are counted; components "::S4B1"
    t2 = F.get("construction_no_start_year_table")
    if t2 and bool(F.get("include_construction", True)) and bool(F.get("include_construction_no_start_year", False)):
        p2 = Path(repo) / str(t2); d2 = pd.read_csv(p2, keep_default_na=False)
        d2["capacity_mw"] = d2.capacity_mw.astype(float); d2["start_year"] = d2.assumed_start_year.astype(float); d2["batch"] = "S4B1"
        led["table_construction_no_start_year"] = dict(path=str(p2.relative_to(repo)), sha256=hashlib.sha256(p2.read_bytes()).hexdigest(), units=int(len(d2)), mw=float(d2.capacity_mw.sum()))
        df = pd.concat([df, d2[[c for c in d2.columns if c in df.columns]]], ignore_index=True)
    if s5["enabled"]:   # V5 X20 (2-6, decision 244): checked coordinates of approximate GEM points - only a node change moves a unit (GEM_COORD_CORRECTIONS_V5.csv)
        from v5_layers import GEM_COORD_TABLE, gem_node_override
        df, moved = gem_node_override(df, cfg, repo)
        led["v5_gem_coord"] = dict(mode=s5["gem_coord_fix"], moved=moved, table=(dict(path=GEM_COORD_TABLE, sha256=hashlib.sha256((Path(repo) / GEM_COORD_TABLE).read_bytes()).hexdigest())
                                                                                if s5["gem_coord_fix"] == "verified" else None))
    n.meta.setdefault("existing_unit_components", {})
    ident = n.meta["existing_unit_components"]
    w = n.snapshot_weightings.generators
    su = n.storage_units; g = n.generators
    for (node, cls, batch), d in df.groupby(["node", "model_class", "batch"]):
        if node not in n.buses.index:
            led["skipped"].append(dict(node=node, cls=cls, mw=float(d.capacity_mw.sum()), reason="node not in network")); continue
        c = country_of(n, node); mw = float(d.capacity_mw.sum()); name = f"existing_survivor::{node}::{cls}::{batch}"
        start = int(d.start_year.min()); life = float(d.lifetime.iloc[0])
        units = {f"GEM:{u.gem_unit_id}": dict(component=name, node=node, capacity_mw=float(u.capacity_mw), commissioning_year=int(u.start_year), retirement_year=float(u.retire_year), source="Global Integrated Power September 2026.xlsx (GEM GIPT 2026-09)",
                                             source_version="1c99186c44ef7c1753b36ffee3c011041ba4723da43941286fd571d38b2db18e", age_basis=str(u.age_basis), cohort_method=None, gem_status=str(u.Status), s4a_added=True,
                                             **({"s4b1_added": True} if batch == "S4B1" else {})) for u in d.itertuples()}
        ensure_carrier(n, cls)
        if cls in FUEL_OF:
            fuel, tech = FUEL_OF[cls]
            eff = cost(costs, tech, "efficiency"); fom = cost(costs, tech, "FOM") / 100.0 * cost(costs, tech, "investment"); vom = cost(costs, tech, "VOM")
            co2 = float(costs.at[fuel, "co2_emissions"])
            fb = f"{node} {fuel}"
            if fb not in n.buses.index:
                led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="fuel bus missing " + fb)); continue
            n.add("Link", name, bus0=fb, bus1=node, bus2=_atmo(n, c), carrier=cls, p_nom=mw / eff, p_nom_extendable=False, p_nom_min=0.0, efficiency=eff, efficiency2=co2,
                  capital_cost=0.0, marginal_cost=vom * eff, lifetime=life, build_year=start)
            n.links.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "variable_cost_method", "cost_qualification", "border_class"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, "technology-data v0.15.0 VOM x efficiency (grade B)", "TECHNOLOGY_DATA_V015_GRADE_B", "domestic"]
            comp = ("Link", name)
        elif cls == "geothermal existing":
            fom = cost(costs, "geothermal", "FOM") / 100.0 * cost(costs, "geothermal", "investment"); vom = cost(costs, "geothermal", "VOM")
            n.add("Generator", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, p_max_pu=AEO8_GEOTHERMAL_CF, capital_cost=0.0, marginal_cost=vom, efficiency=1.0, lifetime=life, build_year=start)
            n.generators.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "variable_cost_method", "cost_qualification"]] = \
                ["existing_survivor", c, "EXISTING_GEOTHERMAL", fom, fom * mw, "AEO8 D.15 Geothermal average VOM (grade C)", "AEO8_GRADE_C_FOM_CONSTANT_VOM"]
            comp = ("Generator", name)
        elif cls in ("solar existing", "onwind existing", "offwind existing"):
            tech = {"solar existing": "solar", "onwind existing": "onwind", "offwind existing": "offwind"}[cls]
            cand = {"solar existing": f"{node} solar-2025", "onwind existing": f"{node} onwind-2025", "offwind existing": f"{node} offwind-ac-2025"}[cls]
            if s5["enabled"]:   # V5 X20 (1-2, decision 241; Q12, decision 246): best class for existing wind, the Q12 rule for existing solar
                from v5_layers import existing_profile_column
                cand, basis = existing_profile_column(n, node, cls, cfg)
                led.setdefault("v5_profile_class", []).append(dict(component=name, cls=cls, mw=mw, column=cand, basis=basis))
            if cand not in n.generators_t.p_max_pu.columns:
                led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="no candidate profile " + cand)); continue
            fom = cost(costs, tech, "FOM") / 100.0 * cost(costs, tech, "investment"); vom = cost(costs, tech, "VOM")
            n.add("Generator", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, capital_cost=0.0, marginal_cost=vom, efficiency=1.0, lifetime=life, build_year=start)
            n.generators_t.p_max_pu[name] = n.generators_t.p_max_pu[cand].values
            n.generators.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "variable_cost_method", "cost_qualification"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, "technology-data v0.15.0 VOM (grade B); availability = node candidate profile", "TECHNOLOGY_DATA_V015_GRADE_B"]
            comp = ("Generator", name)
        elif cls == "ror existing":
            ex = g[(g.carrier == "ror existing") & (g.bus == node)]; scope = "node"
            if not len(ex):
                ex = g[(g.carrier == "ror existing") & (g.bus.map(n.buses.country) == c)]; scope = "country"
            ex = ex[ex.index.isin(n.generators_t.p_max_pu.columns)]
            if not len(ex):
                led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="no existing ROR availability proxy in " + c)); continue
            prof = (n.generators_t.p_max_pu[ex.index] * ex.p_nom).sum(axis=1) / ex.p_nom.sum()
            fom = cost(costs, "ror", "FOM") / 100.0 * cost(costs, "ror", "investment")
            n.add("Generator", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, capital_cost=0.0, marginal_cost=0.0, efficiency=0.9, lifetime=life, build_year=start)
            n.generators_t.p_max_pu[name] = prof.values
            n.generators.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "variable_cost_method", "cost_qualification", "hydro_subtype"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, f"availability proxy = capacity-weighted existing ROR of the {scope} (grade C)", "TECHNOLOGY_DATA_V015_FOM_PROXY_AVAILABILITY", "Run-Of-River"]
            comp = ("Generator", name)
        elif cls == "hydro existing":
            ex = su[(su.carrier == "hydro existing") & (su.bus == node)]; scope = "node"
            if not len(ex) or not ex.index.isin(n.storage_units_t.inflow.columns).any():
                ex = su[(su.carrier == "hydro existing") & (su.bus.map(n.buses.country) == c)]; scope = "country"
            ex = ex[ex.index.isin(n.storage_units_t.inflow.columns)]
            if not len(ex):
                led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="no existing reservoir inflow proxy in " + c)); continue
            inflow_per_mw = n.storage_units_t.inflow[ex.index].sum(axis=1) / ex.p_nom.sum(); hours = float((ex.max_hours * ex.p_nom).sum() / ex.p_nom.sum())
            fom = cost(costs, "hydro", "FOM") / 100.0 * cost(costs, "hydro", "investment")
            n.add("StorageUnit", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, max_hours=hours, efficiency_store=0.0, efficiency_dispatch=0.9, p_min_pu=0.0, cyclic_state_of_charge=True, capital_cost=0.0, marginal_cost=0.0, lifetime=life, build_year=start)
            n.storage_units_t.inflow[name] = (inflow_per_mw * mw).values
            n.storage_units.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "hydro_subtype", "variable_cost_method"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, "Reservoir", f"inflow per MW and max_hours = capacity-weighted existing reservoirs of the {scope} (grade C)"]
            comp = ("StorageUnit", name)
        elif cls == "PHS existing":
            eff = float(np.sqrt(cost(costs, "PHS", "efficiency"))); fom = cost(costs, "PHS", "FOM") / 100.0 * cost(costs, "PHS", "investment")
            n.add("StorageUnit", name, bus=node, carrier=cls, p_nom=mw, p_nom_extendable=False, max_hours=6.0, efficiency_store=eff, efficiency_dispatch=eff, p_min_pu=-1.0, cyclic_state_of_charge=True, capital_cost=0.0, marginal_cost=0.0, lifetime=life, build_year=start)
            n.storage_units.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "hydro_subtype", "variable_cost_method"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_S4A", fom, fom * mw, "Pumped Storage", "6 h decision proxy of the existing PHS; round trip technology-data PHS 0.75 (grade C)"]
            comp = ("StorageUnit", name)
        else:
            led["skipped"].append(dict(node=node, cls=cls, mw=mw, reason="no representation (waste-to-energy pathway absent) -> DATA_PENDING")); continue
        for k, v in units.items():
            ident[k] = dict(v, component_type=comp[0], component=comp[1])
        fom_total = float(n.df(comp[0]).at[name, "existing_annual_fixed_om_eur"])
        led["fom_eur"] += fom_total; led["by_class_mw"][cls] = led["by_class_mw"].get(cls, 0.0) + mw
        led["added"].append(dict(component=name, component_type=comp[0], node=node, country=c, cls=cls, mw=mw, units=len(units), annual_fom_eur=fom_total))
    n.meta["existing_annual_fixed_om_eur"] = float(n.meta.get("existing_annual_fixed_om_eur", 0.0)) + led["fom_eur"]
    led["summary"] = dict(components=len(led["added"]), mw=float(sum(a["mw"] for a in led["added"])), skipped_mw=float(sum(s["mw"] for s in led["skipped"])), fom_eur=led["fom_eur"],
                          mw_s4b1=float(sum(a["mw"] for a in led["added"] if a["component"].endswith("::S4B1"))))
    n.meta["research_fleet"] = led
    return led


def reclassify_phs_stock(n, costs, cfg, repo: Path):
    """V4 D2a (decision 220; V4_D2A_INSTRUCTION.md section 3.3): frozen-stock pumped-storage groups that aggregate conventional reservoir units
    (research_inputs/fleet_v5/PHS_STOCK_RECLASS_V4.csv: Bhumibol, TH2 4 - GEM lists the plant twice, 779 MW conventional + 171 MW pumped, the 779 MW already
    containing the 171 MW reversible unit; EGAT contracted capacity 779.2 MW). research.fleet.phs_stock_reclass: null = follows research.demand.v4.enabled
    (v4 main on, v3.1 off) | true | false. Each identity of the table leaves its PHS component (capacity and the proportional fixed O&M) and joins the
    'hydro existing' StorageUnit existing_survivor::<node>::hydro existing::D2A (created when absent: reservoir representation of add_gem_fleet - node, else
    country inflow / max_hours proxy, efficiency_dispatch 0.9, no pumping) with reclass_mw; drop_mw (the double count) leaves the stock. The vintage cost step
    (m08a_layers.apply_existing_vintage_costs, run afterwards) prices both parts by commissioning year and recomputes the FOM constant; the national inflow
    normalisation (s4c_layers, run afterwards) shares the country's observed inflow by capacity, so the reclassified capacity adds no energy."""
    import hashlib
    import json
    F = dict(cfg["research"].get("fleet") or {})
    flag = F.get("phs_stock_reclass", None)
    if flag is None:
        from v4_common import switches
        enabled = bool(switches(cfg)["enabled"]); rule = "null: follows research.demand.v4.enabled"
    else:
        enabled = bool(flag); rule = "explicit"
    led = dict(enabled=enabled, rule=rule, moved=[], created=[], missing=[], mw_reclassified=0.0, mw_dropped=0.0, fom_delta_eur=0.0)
    if not enabled:
        n.meta["research_phs_stock_reclass"] = led
        return led
    p = Path(repo) / str(F.get("phs_reclass_table", "research_inputs/fleet_v5/PHS_STOCK_RECLASS_V4.csv")); tab = pd.read_csv(p, keep_default_na=False)
    led["table"] = dict(path=str(p.relative_to(repo)), sha256=hashlib.sha256(p.read_bytes()).hexdigest(), rows=int(len(tab)))
    ident = n.meta["existing_unit_components"]
    fom_hydro = cost(costs, "hydro", "FOM") / 100.0 * cost(costs, "hydro", "investment")
    for r in tab.itertuples():
        if r.identity not in ident:
            led["missing"].append(r.identity); continue
        z = ident[r.identity]; comp = z["component"]; mw = float(z["capacity_mw"])
        su = n.storage_units
        if z["component_type"] != "StorageUnit" or comp not in su.index or str(su.at[comp, "carrier"]) != "PHS existing":
            raise ValueError(f"{r.identity}: not a 'PHS existing' StorageUnit ({comp})")
        if abs(mw - float(r.gem_capacity_mw)) > 1e-6 or abs(float(r.reclass_mw) + float(r.drop_mw) - mw) > 1e-6:
            raise ValueError(f"{r.identity}: table capacities {r.gem_capacity_mw} = {r.reclass_mw} + {r.drop_mw} do not match the identity {mw} MW")
        if str(r.reclass_to) != "hydro existing":
            raise ValueError(f"{r.identity}: reclass_to {r.reclass_to} not implemented (hydro existing only)")
        node = str(su.at[comp, "bus"]); c = str(su.at[comp, "country"]); fom_phs = float(su.at[comp, "existing_fixed_om_eur_per_mw_year"])
        rest = [v for k, v in ident.items() if v["component"] == comp and k != r.identity]
        # 1. the PHS component keeps the other units only
        if rest:
            keep = sum(float(v["capacity_mw"]) for v in rest)
            su.at[comp, "p_nom"] = keep; su.at[comp, "existing_annual_fixed_om_eur"] = fom_phs * keep
            for col in ("retained_electric_capacity_mw", "source_group_capacity_mw"):
                if col in su.columns:
                    su.at[comp, col] = keep
            if "source_unit_id" in su.columns:
                su.at[comp, "source_unit_id"] = json.dumps([k.split(":", 1)[1] for k, v in ident.items() if v["component"] == comp and k != r.identity])
        else:
            n.remove("StorageUnit", comp); led.setdefault("components_removed", []).append(comp)
        # 2. the reservoir component of the node (created once)
        name = f"existing_survivor::{node}::hydro existing::D2A"
        su = n.storage_units
        if name not in su.index:
            ex = su[(su.carrier == "hydro existing") & (su.bus == node) & su.index.isin(n.storage_units_t.inflow.columns)]; scope = "node"
            if not len(ex):
                ex = su[(su.carrier == "hydro existing") & (su.bus.map(n.buses.country) == c) & su.index.isin(n.storage_units_t.inflow.columns)]; scope = "country"
            if not len(ex):
                raise ValueError("no existing reservoir inflow proxy for " + name)
            inflow_per_mw = n.storage_units_t.inflow[ex.index].sum(axis=1) / float(ex.p_nom.sum()); hours = float((ex.max_hours * ex.p_nom).sum() / ex.p_nom.sum())
            n.add("StorageUnit", name, bus=node, carrier="hydro existing", p_nom=0.0, p_nom_extendable=False, max_hours=hours, efficiency_store=0.0, efficiency_dispatch=0.9,
                  p_min_pu=0.0, cyclic_state_of_charge=True, capital_cost=0.0, marginal_cost=0.0, lifetime=float(z.get("retirement_year", 2064.0)) - float(z["commissioning_year"]),
                  build_year=int(z["commissioning_year"]))
            n.storage_units_t.inflow[name] = 0.0
            n.storage_units.loc[name, ["asset_role", "country", "research_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "hydro_subtype", "variable_cost_method",
                                       "cost_qualification", "source_parent_id", "storage_energy_basis", "source_group_capacity_mw", "retained_electric_capacity_mw"]] = \
                ["existing_survivor", c, "EXISTING_FLEET_D2A_RECLASS", fom_hydro, 0.0, "Reservoir", f"inflow per MW and max_hours = capacity-weighted existing reservoirs of the {scope} (grade C); "
                 "V4 D2a reclassification of a frozen PHS group (PHS_STOCK_RECLASS_V4.csv)", "TECHNOLOGY_DATA_V015_FOM_PROXY_INFLOW", str(su.at[comp, "source_parent_id"]) if comp in su.index and "source_parent_id" in su.columns else "",
                 "ASSEMBLY_V1_RESERVOIR_PROXY_D2A", 0.0, 0.0]
            n.meta.setdefault("research_phs_stock_reclass_inflow_proxy", {})[name] = dict(scope=scope, proxies=sorted(ex.index), per_mw_annual_mwh=float((inflow_per_mw * n.snapshot_weightings.generators).sum()))
            led["created"].append(dict(component=name, node=node, country=c, proxy_scope=scope, max_hours=hours))
        else:
            pr = n.meta["research_phs_stock_reclass_inflow_proxy"][name]
            ex = n.storage_units.loc[pr["proxies"]]; inflow_per_mw = n.storage_units_t.inflow[ex.index].sum(axis=1) / float(ex.p_nom.sum())
        add = float(r.reclass_mw)
        su = n.storage_units
        su.at[name, "p_nom"] = float(su.at[name, "p_nom"]) + add
        su.at[name, "existing_annual_fixed_om_eur"] = fom_hydro * float(su.at[name, "p_nom"])
        for col in ("source_group_capacity_mw", "retained_electric_capacity_mw"):
            su.at[name, col] = float(su.at[name, "p_nom"])
        n.storage_units_t.inflow[name] = n.storage_units_t.inflow[name].values + (inflow_per_mw * add).values
        ident[r.identity] = dict(z, component=name, component_type="StorageUnit", capacity_mw=add,
                                 d2a_reclass=dict(from_component=comp, gem_capacity_mw=mw, reclass_mw=add, drop_mw=float(r.drop_mw), gem_technology=str(r.gem_technology), reason=str(r.reason), sources=str(r.sources)))
        d_fom = -fom_phs * mw + fom_hydro * add
        led["fom_delta_eur"] += d_fom; led["mw_reclassified"] += add; led["mw_dropped"] += float(r.drop_mw)
        led["moved"].append(dict(identity=r.identity, from_component=comp, to_component=name, node=node, country=c, gem_capacity_mw=mw, reclass_mw=add, drop_mw=float(r.drop_mw),
                                 phs_component_p_nom_after=(float(n.storage_units.at[comp, "p_nom"]) if comp in n.storage_units.index else 0.0), fom_delta_eur=d_fom))
    n.meta["existing_annual_fixed_om_eur"] = float(n.meta.get("existing_annual_fixed_om_eur", 0.0)) + led["fom_delta_eur"]
    n.meta["research_phs_stock_reclass"] = led
    return led


def remove_not_operating_units(n, cfg, repo: Path):
    """S4B-1 (decision 77): remove the frozen-stock units that GEM GIPT 2026-09 lists as cancelled / mothballed / retired / absent
    (research.fleet.remove_not_operating_gipt2026, data correction). Each identity leaves existing_unit_components (kept in
    n.meta["existing_unit_removed_s4b1"] with its reason); its component loses the unit capacity (MW_el) and the proportional share of the
    component's annual fixed O&M (also subtracted from the existing-FOM constant); a component left without units is removed."""
    F = dict(cfg["research"].get("fleet") or {})
    led = dict(enabled=bool(F.get("remove_not_operating_gipt2026", False)), removed=[], components_removed=[], mw=0.0, fom_eur=0.0, missing=[])
    if not led["enabled"]:
        n.meta["research_fleet_removed"] = led
        return led
    import hashlib
    p = Path(repo) / str(F["removal_table"]); tab = pd.read_csv(p, keep_default_na=False)
    led["table"] = dict(path=str(p.relative_to(repo)), sha256=hashlib.sha256(p.read_bytes()).hexdigest(), units=int(len(tab)))
    ident = n.meta["existing_unit_components"]; gone = n.meta.setdefault("existing_unit_removed_s4b1", {})
    for r in tab.itertuples():
        if r.identity not in ident:
            led["missing"].append(r.identity); continue
        z = ident.pop(r.identity); typ, comp, mw = z["component_type"], z["component"], float(z["capacity_mw"])
        if typ not in ("Link", "Generator"):
            raise ValueError("removal of a " + typ + " unit needs time-series scaling: " + r.identity)
        df = n.df(typ); eff = float(df.at[comp, "efficiency"]) if typ == "Link" else 1.0
        total = float(df.at[comp, "p_nom"]) * eff; fom = float(df.at[comp, "existing_annual_fixed_om_eur"]) if "existing_annual_fixed_om_eur" in df else 0.0
        cut = fom * mw / total if total > 0 else 0.0
        rest = [v for v in ident.values() if v["component"] == comp]
        if rest:
            df.at[comp, "p_nom"] = sum(float(v["capacity_mw"]) for v in rest) / eff
            if "existing_annual_fixed_om_eur" in df:
                df.at[comp, "existing_annual_fixed_om_eur"] = fom - cut
        else:
            n.remove(typ, comp); led["components_removed"].append(comp)
        gone[r.identity] = dict(z, removal_reason=str(r.removal_reason), gipt_status_2026=str(r.gipt_status_2026), removed_fom_eur=cut)
        led["mw"] += mw; led["fom_eur"] += cut
        led["removed"].append(dict(identity=r.identity, component=comp, component_type=typ, mw=mw, fom_eur=cut, gipt_status_2026=str(r.gipt_status_2026)))
    n.meta["existing_annual_fixed_om_eur"] = float(n.meta.get("existing_annual_fixed_om_eur", 0.0)) - led["fom_eur"]
    n.meta["research_fleet_removed"] = led
    return led
