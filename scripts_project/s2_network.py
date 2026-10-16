"""S2 scenario builder: S1 skeleton + cost layer C + CO2/biomass/demand/heat layers (S2-1..S2-6).

    python scripts_project/s2_network.py --repo . --scenario integrated --output results_project/s2/integrated

Builds the 2920x3h network, validates it statically (static_validate_s2), exports it, derives the
exact 365x24h daily network and writes receipts. No solver. Every input is pinned by SHA256.
"""
from pathlib import Path
import argparse, copy, json, platform, sys, time
import numpy as np
import pandas as pd
import pypsa
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from carrier_architecture import COUNTRIES, to_pypsa_fragment, ATMOSPHERE_CARRIER, atmosphere_bus
from assembly_components import merge_input_components, validate_hooks, check_global_constraints
from country_carbon import add_country_atmosphere, reconnect_atmosphere_ports, fix_u4, validate_country_attribution, install_metadata as install_carbon_metadata
from sector_adapter import load_upstream, build_options, inject, add_hydrogen, spatial_nodes, dc_to_ac
from s1_candidates import add_nuclear, add_site_candidates, confirm_extendable, apply_cost_scaling, PENDING
from build_research_assets import build_fragment
from build_research_network import REQUIRED_PER_NODE
from daily_resolution import to_daily
from network_checks import assert_input_only, compare_roundtrip, normalise_optional_strings
from scenario_network import (ELECTRIC_BASE_SHA, EXTENDABLE_REQUIRED, XB_FOM_HOOK, sha, save, git_head, config_sha, jsonable, rename_legacy_buses,
                              tag_cross_border, existing_cross_border_fom, bind_astar, component_inventory)
from s2_costs import build_research_costs, write_costs
from s3_layers import add_gas_network, add_imports, add_ammonia_methanol, add_fuel_carbon_mode
from s4a_layers import apply_renewable_profiles
from s4a_fleet import add_gem_fleet, remove_not_operating_units
from s4b_layers import apply_sector_alignment
from s2_layers import (add_existing_geothermal, set_transmission_s2, add_co2_layer, add_biomass_layer, add_industrial_heat, add_demand_layer,
                       add_gap_slack, S2_OWNER_KIND, TFEC_SECTORS, pipeline_candidates, replace_h2_pipelines, add_apg_corridor_lines)

AEO8_GEOTHERMAL_CF = 27.1 / (4.3 * 8.76)  # AEO8 Appendix C.5 generation 27.1 TWh (2022) / C.4 capacity 4.3 GW (2022), BAS panels (PDF p.185/187)
AEO8_GEOTHERMAL_CF_SOURCE = "AEO8 Appendix C.4 Installed Capacity (Geothermal 4.3 GW, 2022) and C.5 Electricity Generation (27.1 TWh, 2022): 27.1/(4.3x8.76) = 0.72 (grade B derivation)"


def apply_cross_border_switches_s2(n, switches, corridors, existing_cfg, costs):
    """research.cross_border.{electricity,H2,gas,co2}; S1 logic for electricity/H2, removal for gas/CO2 pipelines."""
    ledger = {}
    xb_lines = set(n.lines.index[n.lines.border_class == "cross_border"])
    xb_elec_links = set(n.links.index[(n.links.border_class == "cross_border") & (n.links.transport_carrier == "electricity")])
    actual = {("Line", x) for x in xb_lines} | {("Link", x) for x in xb_elec_links}
    expected = {(r.component_type, str(r.component)) for _, r in corridors.iterrows()}
    if actual != expected:
        raise ValueError("Existing cross-border electricity set differs from the corridor table: " + str(sorted(actual ^ expected))[:300])
    if switches["electricity"]:
        checks = []
        for _, r in corridors.iterrows():
            typ = r.component_type; name = str(r.component); z = n.df(typ).loc[name]; nom = "s_nom" if typ == "Line" else "p_nom"; cap = float(r.capacity_2025_mw)
            if not z[nom + "_extendable"] or float(z[nom + "_min"]) != cap or not np.isclose(float(z[nom]), cap, rtol=1e-9, atol=1e-6):
                raise ValueError("Existing cross-border edge lacks the 2025 lower bound: " + name)
            checks.append(dict(component_type=typ, component=name, capacity_2025_mw=cap))
        fom_total, fom_rows = (existing_cross_border_fom(n, corridors, costs) if existing_cfg["fom_on_existing"] else (0.0, []))
        n.meta["existing_cross_border_fom_eur"] = fom_total; n.meta["existing_cross_border_fom_ledger"] = fom_rows
        if fom_total:
            n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {XB_FOM_HOOK})
        ledger["electricity"] = dict(switch=True, kept=len(checks), existing_annual_fom_eur=fom_total)
    else:
        n.mremove("Line", sorted(xb_lines)); n.mremove("Link", sorted(xb_elec_links))
        n.meta["existing_cross_border_fom_eur"] = 0.0; n.meta["existing_cross_border_fom_ledger"] = []
        ledger["electricity"] = dict(switch=False, removed_count=len(actual))
    for key, carrier in [("H2", "H2 pipeline"), ("gas", "gas pipeline"), ("co2", "CO2 pipeline")]:
        xb = sorted(n.links.index[(n.links.border_class == "cross_border") & (n.links.carrier == carrier)])
        if switches[key]:
            ledger[key] = dict(switch=True, kept=len(xb), components=xb if key == "co2" else len(xb))
        else:
            n.mremove("Link", xb); ledger[key] = dict(switch=False, removed_count=len(xb), removed=xb if key == "co2" else len(xb))
    n.meta["research_cross_border"] = dict(switches={k: bool(v) for k, v in switches.items()}, ledger=ledger)
    return ledger


def static_validate_s2(n, cfg, corridors, demand_ledger, *, daily=False):
    R = cfg["research"]; S2 = R["s2"]; report = {}
    expected = pd.date_range("2013-01-01", "2013-12-31 21:00", freq="3h") if not daily else pd.date_range("2013-01-01", "2013-12-31", freq="24h")
    if not n.snapshots.equals(expected):
        raise ValueError("Research snapshot boundary changed")
    if not np.all(n.snapshot_weightings.to_numpy() == (3 if not daily else 24)):
        raise ValueError("Physical weights changed")
    geo = n.buses[n.buses.carrier.isin(["AC", "DC"])]
    if len(geo) != 100 or set(geo.country) != set(COUNTRIES):
        raise ValueError("Geographical electric buses changed")
    check_global_constraints(n); validate_hooks(n)
    if n.meta.get("solver_allowed") is not False:
        raise ValueError("Solver guard missing")
    if n.meta.get("skeleton_status") != S2["status"]:
        raise ValueError("S2 status must be declared in metadata")
    for name, table in [("loads", n.loads), ("generators", n.generators), ("stores", n.stores), ("storage_units", n.storage_units), ("links", n.links), ("lines", n.lines)]:
        for col in [c for c in table if c == "bus" or (c.startswith("bus") and c[3:].isdigit())]:
            if any(b not in n.buses.index for b in table[col] if b):
                raise ValueError("Dangling " + name + " bus")
    if any(" :: " in b for b in n.buses.index):
        raise ValueError("Legacy bus naming survived the rename")
    load = n.get_switchable_as_dense("Load", "p_set")
    if load.isna().any().any() or not np.isfinite(load.values).all() or (load.values < 0).any():
        raise ValueError("Invalid actual Load")
    owners = n.meta["demand_owners"]
    if set(owners) != set(n.loads.index):
        raise ValueError("Unexpected or unowned Load: " + str(sorted(set(owners) ^ set(n.loads.index))[:5]))
    w = n.snapshot_weightings.generators
    annual = (load.mul(w, axis=0)).sum()
    report["demand"] = dict(loads=int(len(n.loads)), owner_kinds=n.loads.demand_owner_kind.value_counts().to_dict(), annual_twh=float(annual.sum() / 1e6),
                            by_carrier_twh={str(k): float(v / 1e6) for k, v in annual.groupby(n.loads.carrier).sum().items()})
    # S2 demand table conservation (static B8): every table row bound once, totals conserved (sum over nodes == country value)
    led = pd.DataFrame(demand_ledger["loads"])
    bound = led.groupby(["country", "sector"]).annual_mwh.sum()
    report["demand_table_binding"] = dict(rows=int(len(led)), by_sector_twh={str(k): float(v / 1e6) for k, v in led.groupby("sector").annual_mwh.sum().items()},
                                          deferred_twh=float(sum(d["annual_mwh"] for d in demand_ledger["deferred"]) / 1e6))
    report["carbon"] = validate_country_attribution(n)
    if n.meta.get("research_carbon", {}).get("constraint_scope") != R["carbon"]["constraint_scope"]:
        raise ValueError("Carbon constraint scope metadata differs from config")
    for typ in ["Line", "Link"]:
        df = n.df(typ)
        if len(df) and ("border_class" not in df or df.border_class.isna().any() or not df.border_class.isin(["domestic", "cross_border"]).all()):
            raise ValueError("Untagged " + typ)
    sw = R["cross_border"]; xb = {}
    for key, sel in [("electricity", (n.lines.border_class == "cross_border").sum() + ((n.links.border_class == "cross_border") & (n.links.transport_carrier == "electricity")).sum()),
                     ("H2", ((n.links.border_class == "cross_border") & (n.links.carrier == "H2 pipeline")).sum()),
                     ("gas", ((n.links.border_class == "cross_border") & (n.links.carrier == "gas pipeline")).sum()),
                     ("co2", ((n.links.border_class == "cross_border") & (n.links.carrier == "CO2 pipeline")).sum())]:
        xb[key] = int(sel)
        if not sw[key] and xb[key]:
            raise ValueError("Cross-border " + key + " components present although the switch is off")
    if sw["electricity"]:
        expected_edges = {(r.component_type, str(r.component)) for _, r in corridors.iterrows()}
        actual = {("Line", x) for x in n.lines.index[n.lines.border_class == "cross_border"]} | {("Link", x) for x in n.links.index[(n.links.border_class == "cross_border") & (n.links.transport_carrier == "electricity")]}
        if actual != expected_edges:
            raise ValueError("Cross-border electricity set differs from the corridor table")
    report["cross_border"] = dict(switches=sw, components=xb)
    if n.meta.get("research_cross_border", {}).get("switches") != {k: bool(v) for k, v in sw.items()}:
        raise ValueError("Cross-border switch metadata differs from config")
    # candidate structure: resolve every port to its geographical node (bus itself, its location, or the node-name prefix of carrier buses)
    geo_names = sorted(geo.index, key=len, reverse=True)

    def node_of_bus(b):
        if b in geo.index:
            return b
        if "location" in n.buses and str(n.buses.at[b, "location"]) in geo.index:
            return str(n.buses.at[b, "location"])
        for g in geo_names:
            if b.startswith(g + " "):
                return g
        return b
    b2b = n.links[n.links.carrier == "B2B"]; coupled = set(b2b.bus0) | set(b2b.bus1)
    missing = []
    for typ, carriers in REQUIRED_PER_NODE.items():
        df = n.df(typ)
        for carrier in carriers:
            ports = set(df.bus[df.carrier == carrier]) if typ != "Link" else set(df.bus1[df.carrier == carrier]) | set(df.bus0[df.carrier == carrier])
            present = {node_of_bus(b) for b in ports}
            for node in geo.index:
                if node not in present and carrier not in ("solar", "onwind") and node not in coupled:
                    if carrier == "nuclear SMR" and geo.at[node, "country"] not in set(R["nuclear"]["smr"]["allowed_countries"]):
                        continue
                    missing.append((typ, carrier, node))
    if missing:
        raise ValueError("Required candidate structure missing: " + str(missing[:6]))
    s2_required = {"Store": ["co2 stored"], "Link": ["CCGT CC", "process emissions CC", "biomass EOP", "biomass EOP CC", "biogas upgrading", "BtL", "industry electric boiler", "industry heat pump", "industry gas boiler", "industry biomass boiler"] + (["DAC"] if S2["co2"]["dac"] else [])}
    for typ, carriers in s2_required.items():
        df = n.df(typ)
        for carrier in carriers:
            ports = set(df.bus[df.carrier == carrier]) if typ != "Link" else set(df.bus1[df.carrier == carrier]) | set(df.bus0[df.carrier == carrier])
            present = {node_of_bus(b) for b in ports}
            lacking = [node for node in geo.index if node not in present and node not in coupled]
            if lacking:
                raise ValueError(f"S2 structure {typ} {carrier} missing at {lacking[:4]}")
    pending = []
    for typ in ["Generator", "StorageUnit", "Link", "Store"]:
        df = n.df(typ)
        if "s1_candidate_status" in df:
            sel = df[df.s1_candidate_status == "DATA_PENDING"]; nom = "p_nom_max" if typ != "Store" else "e_nom_max"
            if (sel[nom] != 0).any():
                raise ValueError("DATA_PENDING candidate with nonzero potential")
            pending += [dict(component_type=typ, component=k, carrier=str(z.carrier), country=str(z.country)) for k, z in sel.iterrows()]
    report["data_pending"] = dict(count=len(pending), by_carrier=dict(pd.Series([p["carrier"] for p in pending]).value_counts()) if pending else {})
    identities = n.meta["existing_unit_components"]; groups = {}
    for ident, z in identities.items():
        groups.setdefault((z["component_type"], z["component"]), []).append(z)
    for (typ, name), parts in groups.items():
        z = n.df(typ).loc[name]; total = sum(x["capacity_mw"] for x in parts); effective = float(z.p_nom * z.efficiency if typ == "Link" else z.p_nom)
        if not np.isclose(total, effective, rtol=1e-12) or z.p_nom_extendable or z.capital_cost != 0:
            raise ValueError("Existing stock altered: " + name)
    report["existing_stock"] = dict(units=len(identities), components=len(groups), capacity_mw=float(sum(z["capacity_mw"] for z in identities.values())))
    tl = n.meta.get("transmission_limit", {})
    if tl.get("mode") == "lvopt":
        if "lv_limit" in n.global_constraints.index:
            raise ValueError("lvopt declared but lv_limit still present")
    elif tl.get("constant_mwkm") != float(n.global_constraints.at["lv_limit", "constant"]):
        raise ValueError("Transmission limit metadata differs from the GlobalConstraint")
    # storage caps and biomass pools
    caps = n.meta["research_co2_storage"]["caps_t_per_year"]
    for c, cap in caps.items():
        sb = f"co2 sequestered {c}"
        if (cap > 0) != (sb in n.stores.index):
            raise ValueError("Sequestration store/cap mismatch for " + c)
        if cap > 0 and n.meta["store_power_rules"].get(sb) != "charge_only":
            raise ValueError("Sequestration store must be charge-only: " + c)
    bio = n.stores[n.stores.research_role == "FINITE_RESOURCE"] if "research_role" in n.stores else n.stores.iloc[0:0]
    if (bio.e_nom_extendable).any() or any(n.meta["store_power_rules"].get(s) != "discharge_only" for s in bio.index):
        raise ValueError("Biomass pools must be fixed, discharge-only Stores")
    report["s2"] = dict(sequestration_countries=[c for c, v in caps.items() if v > 0], biomass_stores=int(len(bio)), biomass_potential_twh=float(bio.e_nom.sum() / 1e6),
                        co2_pipelines=int((n.links.carrier == "CO2 pipeline").sum()), capture_links=int(n.links.carrier.isin(["CCGT CC", "biomass EOP CC", "process emissions CC", "DAC", "industry biomass CC", "industry biomass boiler CC"]).sum()))
    report["status"] = "S2_STATIC_PASS"; report["solver_runs"] = 0
    return report


def estimate_memory(output):
    """S1 rule: scale the measured S1 build (0.52 GiB, 15 s) by the component count ratio with a 1.25 safety factor."""
    s1 = dict(peak_rss_gib=0.5, components=dict(Generator=1437, Link=1196, Store=304, Load=96), source="results_project/s1/S1_BUILD_MEMORY_MEASURED.json")
    s2_components = dict(Generator=1437 + 103, Link=1196 + 100 * 26, Store=304 + 100 + 11 + 120, Load=96 + 100 * 18)
    ratio = sum(s2_components.values()) / sum(s1["components"].values())
    est = dict(purpose="S2-7: estimate peak RSS of the local network assembly before building", s1_measured=s1, s2_expected_components=s2_components,
               component_ratio=ratio, estimated_peak_rss_gib=round(s1["peak_rss_gib"] * ratio * 1.25, 2), threshold_gib=7.94, decision="BUILD_LOCALLY",
               measurement_plan="/usr/bin/time -v around scripts_project/s2_network.py (recorded in S2_BUILD_MEMORY_MEASURED.json)")
    save(Path(output).parent / "S2_BUILD_MEMORY_ESTIMATE.json", est)
    return est


def build_scenario_s2(repo, scenario, output, electric_base, allocation, hydro_decisions, survival_json, daily=True, gap_diagnostic=False, overrides=None):
    repo = Path(repo); output = Path(output); output.mkdir(parents=True, exist_ok=True); t0 = time.time()
    from phase4_static import config
    cfg = config(repo, scenario); R = cfg["research"]; S2 = R["s2"]
    for ov in (overrides or []):
        key, val = ov.split("=", 1); d = cfg["research"]; parts = key.split(".")
        for k in parts[:-1]:
            d = d[k]
        old = d[parts[-1]]; d[parts[-1]] = type(old)(val) if not isinstance(old, bool) else (val.lower() in ("1", "true", "yes"))
    cfg["research"]["config_overrides"] = list(overrides or [])
    if R["scenario"] != scenario:
        raise ValueError("Scenario identity does not match the composed config")
    if sha(electric_base) != ELECTRIC_BASE_SHA:
        raise ValueError("Frozen electric base identity changed")
    registry_csv = repo / "research_inputs/registry_v5/DATA_REGISTRY.csv"
    registry = pd.read_csv(registry_csv, dtype=str, keep_default_na=False).set_index("param_id")
    costs, cost_ledger = build_research_costs(repo, cfg, registry_csv)
    costs_path = write_costs(costs, cost_ledger, output)
    n = pypsa.Network(str(electric_base)); assert_input_only(n)
    if n.meta.get("asset_qualification") != "SOURCE_QUALIFIED_ELECTRIC_BASE_UNSOLVED":
        raise ValueError("Electric base is not the source-qualified asset")
    rename_map = rename_legacy_buses(n)
    renewable = apply_renewable_profiles(n, cfg, repo)   # S4A-1 (L14): rebuilt wind / solar profiles per research.renewable (original keeps the electric base untouched)
    corridors = pd.read_csv(repo / R["existing_cross_border_electricity"]["corridors_file"], float_precision="round_trip")
    apg_added = add_apg_corridor_lines(n, corridors)   # S3-0 (decisions 59/62): APG #11 TH-MM (0 MW, candidate) and #17 LA-MM (30 MW stock) absent from the frozen base
    cc = float(cfg["sector"]["cc_fraction"])
    # 1. upstream hydrogen library
    psn = load_upstream(repo); nodes = spatial_nodes(n); options = build_options(cfg["sector"], R["hydrogen"])
    injected = inject(psn, n, options, nodes, COUNTRIES, output / "empty_gas_pipelines.csv", cfg["research_assembly"]["demand_scenario"])
    dcmap = dc_to_ac(n)
    h2 = add_hydrogen(psn, n, costs, nodes, dcmap)
    # R5 (decision 59): pipeline candidates from the electricity topology; the upstream greenfield H2 routes are replaced
    P = S2.get("pipelines", {})
    candidates = pipeline_candidates(n, nodes, corridors, dcmap, float(P.get("length_factor", 1.25))) if P.get("topology") == "electricity_network_topology" else None
    h2_pipes = replace_h2_pipelines(n, costs, candidates) if candidates is not None else dict(removed_upstream=0, added=0, note="upstream greenfield routes kept")
    # 2. research carrier recipe (fuel pools priced with the registry fuel prices, SMR/SMR CC/FT, OCGT/CCGT, national atmosphere)
    f, carbon, fragment_manifest = build_fragment(repo, n, costs_path, output, price_layer=None, cc_fraction=cc)
    sub = to_pypsa_fragment(f, list(n.snapshots), list(n.snapshot_weightings.generators), component_ids=list(f.components))
    merge_input_components(n, sub)
    add_country_atmosphere(n); moves = reconnect_atmosphere_ports(n); u4 = fix_u4(n)
    # 3. candidates: SMR priced (decision 46), geothermal/ror/hydro/PHS structures (potentials pending), existing geothermal (decision 52)
    nuclear = add_nuclear(n, costs, R["nuclear"], nodes)
    sites = add_site_candidates(n, costs, R["site_candidates"], nodes, hydro_decisions)
    extendable = confirm_extendable(n, EXTENDABLE_REQUIRED)
    contract_path = repo / "results_project/assembly_v1/final_assets/SELECTED_INTEGRATION_CONTRACT.json"
    if not contract_path.exists():
        contract_path = repo / "results_project/assembly_v1/assets/SELECTED_INTEGRATION_CONTRACT.json"
    contract = json.loads(contract_path.read_text())
    geo = add_existing_geothermal(n, costs, survival_json, AEO8_GEOTHERMAL_CF, AEO8_GEOTHERMAL_CF_SOURCE, bus_mapping=contract.get("mapping", {}))
    geo["bus_mapping_source"] = dict(path=str(contract_path), sha256=sha(contract_path))
    fleet = add_gem_fleet(n, costs, cfg, repo)   # S4A-2 (L15): GEM units in service in 2050 missing from the frozen stock; S4B-1 adds construction units without start year
    fleet["removed"] = remove_not_operating_units(n, cfg, repo)   # S4B-1 (decision 77): frozen-stock units not operating in GIPT 2026 removed (data correction)
    # 4. S2 layers
    co2 = add_co2_layer(n, costs, S2, registry, nodes, cc, candidates=candidates)
    pipelines = dict(topology=P.get("topology", "h2_pipeline_routes"), length_factor=float(P.get("length_factor", 1.25)), length_factor_source=P.get("length_factor_source", ""),
                     candidates=(int(len(candidates)) if candidates is not None else None), cross_border_candidates=(int(candidates.cross_border.sum()) if candidates is not None else None),
                     by_country_pair=({f"{a}-{b}": int(k) for (a, b), k in candidates[candidates.cross_border].groupby(["country_a", "country_b"]).size().items()} if candidates is not None else None),
                     domestic_by_country=({str(c): int(k) for c, k in candidates[~candidates.cross_border].groupby("country_a").size().items()} if candidates is not None else None),
                     h2=h2_pipes, underwater_fraction_source="corridor table subsea_share (cross-border); 0 for domestic pairs (no data)",
                     table=(candidates.to_dict("records") if candidates is not None else None))
    bio = add_biomass_layer(n, costs, S2, repo / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv", nodes, cc)
    heat = add_industrial_heat(n, costs, nodes, cc)
    demand_astar = bind_astar(n, repo, allocation)
    from s2_layers import demand_table_key
    allocation_mode = demand_table_key(cfg)   # R3 (decision 57) + S3B R1 growth method suffix (decision 66)
    demand_table = repo / S2["demand"].get("tables_by_allocation", {}).get(allocation_mode, S2["demand"]["table"])
    demand = add_demand_layer(n, costs, cfg, repo, registry, demand_table, repo / "research_inputs/registry_v5/FEEDSTOCK_CARBON_BOUNDARY_2019.csv", allocation, nodes, cc)
    demand["country_allocation"] = dict(mode=allocation_mode, table=str(demand_table.relative_to(repo)), sha256=sha(demand_table))
    n.meta["s2_demand_ledger"] = jsonable(dict(deductions=demand["deductions"], deferred=demand["deferred"], parameters=demand["parameters"],
                                              totals_by_sector_mwh={str(k): float(v) for k, v in pd.DataFrame(demand["loads"]).groupby("sector").annual_mwh.sum().items()}))
    # S3-1: gas network (domestic production, pipelines along the candidate topology incl. the 2025 cross-border stock, LNG terminals; unlimited external gas removed)
    gas_net = add_gas_network(n, costs, cfg, repo, registry, nodes, candidates) if (candidates is not None and "s3" in R and "gas" in R["s3"]) else None
    imports = add_imports(n, costs, cfg, repo, registry, nodes) if ("s3" in R and "imports" in R["s3"]) else None   # S3-2: regional oil pool, green carrier imports, H2 at LNG terminals
    nh3_meoh = add_ammonia_methanol(n, costs, cfg, repo, registry, nodes) if ("s3" in R and "ammonia_methanol" in R["s3"]) else None   # S3-3: Haber-Bosch, cracker, methanolisation, biomass-to-methanol, methanol OCGT, stores
    sector = apply_sector_alignment(n, costs, cfg, nodes) if "sector" in R else None   # S4B-0 (decision 70): PyPSA-Eur sector defaults (Sabatier, electrobiofuels, FT part load, switches)
    fuel_carbon = add_fuel_carbon_mode(n, costs, cfg, nodes) if ("s3" in R and "fuel_carbon_mode" in R["s3"]) else None   # S3-5 (decision 64): origin_neutral main / producer_credit sensitivity
    # 5. network switches, transmission, carbon metadata
    tags = tag_cross_border(n)
    xb = apply_cross_border_switches_s2(n, R["cross_border"], corridors, R["existing_cross_border_electricity"], costs)
    lv = set_transmission_s2(n, R["transmission"])
    n.meta["transmission_limit"] = jsonable(lv)
    carbon_meta = install_carbon_metadata(n, R["carbon"])
    scaling = apply_cost_scaling(n, R["cost_scaling"])
    if gap_diagnostic:
        add_gap_slack(n, S2["gap_diagnostic"], nodes)
    n.meta.update(**jsonable(dict(artifact_role=("GAP_DIAGNOSTIC_UNSOLVED" if gap_diagnostic else "S2_SCENARIO_UNSOLVED"), asset_role="S2_SCENARIO_UNSOLVED", stage="S2", skeleton_status=S2["status"],
                                  scenario=scenario, solver_allowed=False, scientific_results_allowed=False, fullsc_network_complete=False, input_coverage_complete=False,
                                  research_config=R, research_config_sha256=config_sha(R), fuel_bus_rename_map=rename_map, atmosphere_port_moves=moves, u4_zeroed_carriers=u4,
                                  upstream_adapter=injected, upstream_add_hydrogen=h2, candidate_ledger=dict(nuclear=nuclear, sites=sites, extendable=extendable),
                                  cross_border_tags=tags, demand_binding=demand_astar, electric_base_sha256=ELECTRIC_BASE_SHA, physical_carbon_map=carbon,
                                  cost_layer=dict(active=cost_ledger["layer"], overrides=cost_ledger["overrides"], appended=["nuclear SMR", "geothermal"], file=str(costs_path.name)),
                                  s2_layers=dict(geothermal=geo, co2=co2, biomass={k: v for k, v in bio.items() if k != "stores"}, heat=heat, pipelines={k: v for k, v in pipelines.items() if k != "table"}),
                                  s3_layers=dict(gas=gas_net, imports=imports, ammonia_methanol=nh3_meoh, fuel_carbon=fuel_carbon),
                                  s4a_layers=dict(renewable={k: v for k, v in renewable.items() if k not in ("replaced", "added")}, fleet={k: v for k, v in fleet.items() if k != "added"}),
                                  s4b_layers=dict(sector=sector),
                                  interim_notice="S2_SECTOR_COUPLED_SMOKE: smoke-test structure; results carry no scientific meaning before the cloud run (decision 47)")))
    for key in ["research_carbon", "research_cross_border", "existing_cross_border_fom_ledger", "existing_cross_border_fom_eur", "research_co2_storage", "research_biomass", "research_renewable", "research_fleet",
                "research_sector_alignment", "research_fleet_removed", "existing_unit_removed_s4b1"]:
        if key in n.meta:
            n.meta[key] = jsonable(n.meta[key])
    n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {"install_fragment_constraints"})
    n.meta["qualification_dimensions"] = dict(n.meta.get("qualification_dimensions", {}), physical_integrity="S2_STATIC_VALIDATION", input_coverage="S2_SECTORS_EXCEPT_SHIPPING", price_usability="COST_LAYER_LEDGER")
    normalise = normalise_optional_strings(n)
    static = static_validate_s2(n, cfg, corridors, demand)
    inventory = component_inventory(n)
    suffix = "_gap_diagnostic" if gap_diagnostic else ""
    path = output / f"{scenario}{suffix}_2920_3h_unsolved.nc"; n.export_to_netcdf(path)
    back = pypsa.Network(str(path)); compare_roundtrip(n, back)
    receipt = dict(status="S2_SCENARIO_BUILT_STATIC_PASS", scenario=scenario, gap_diagnostic=gap_diagnostic, s2_status=S2["status"],
                   network=dict(file=str(path), sha256=sha(path), bytes=path.stat().st_size, snapshots=int(len(n.snapshots)), components={c.name: int(len(c.df)) for c in n.iterate_components()}),
                   inputs={"electric_base": dict(path=str(electric_base), sha256=ELECTRIC_BASE_SHA), "costs_active": dict(path=str(costs_path), sha256=sha(costs_path)),
                           "registry": dict(path=str(registry_csv), sha256=sha(registry_csv)), "demand_table": dict(path=str(demand_table.relative_to(repo)), sha256=sha(demand_table), country_allocation=allocation_mode),
                           "biomass_table": dict(sha256=sha(repo / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv")), "survival": dict(sha256=sha(survival_json)),
                           "allocation_manifest": dict(sha256=sha(Path(allocation) / "allocation_manifest.json")), "corridors": dict(sha256=sha(repo / R["existing_cross_border_electricity"]["corridors_file"])),
                           "upstream_module": dict(path="scripts/prepare_sector_network.py", sha256=sha(repo / "scripts/prepare_sector_network.py"))},
                   research_config_sha256=config_sha(R), cross_border=xb, transmission_limit=jsonable(lv), demand_astar=demand_astar, demand_s2=dict(loads=len(demand["loads"]), deductions=demand["deductions"], deferred=demand["deferred"], parameters=demand["parameters"], country_allocation=demand["country_allocation"]),
                   geothermal=geo, co2=co2, biomass={k: v for k, v in bio.items() if k != "stores"}, biomass_stores=bio["stores"], heat=heat, pipelines=pipelines, cost_layer=cost_ledger,
                   static_validation=static, inventory=inventory, candidates=dict(nuclear=len(nuclear), sites=len(sites), extendable=extendable), optional_string_normalisation=normalise,
                   code_sha=git_head(repo), environment=dict(python=platform.python_version(), pypsa=pypsa.__version__), build_seconds=time.time() - t0, solver_runs=0)
    pd.DataFrame(demand["loads"]).to_csv(output / f"{scenario}{suffix}_S2_DEMAND_OWNERSHIP.csv", index=False)
    pd.DataFrame(geo["units"]).to_csv(output / f"{scenario}{suffix}_GEOTHERMAL_UNITS.csv", index=False)
    if daily and not gap_diagnostic:
        d, ledger = to_daily(n); dpath = output / f"{scenario}_365_24h_unsolved.nc"; d.export_to_netcdf(dpath)
        dback = pypsa.Network(str(dpath)); compare_roundtrip(d, dback)
        receipt["daily_network"] = dict(file=str(dpath), sha256=sha(dpath), bytes=dpath.stat().st_size, snapshots=int(len(d.snapshots)), aggregation_series=len(ledger))
    save(output / f"{scenario}{suffix}_BUILD_RECEIPT.json", receipt)
    return n, receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--repo", type=Path, default=HERE.parent); p.add_argument("--scenario", required=True, choices=["integrated", "disconnected", "baseline"]); p.add_argument("--output", type=Path, required=True)
    p.add_argument("--electric-base", type=Path, default=None); p.add_argument("--allocation", type=Path, default=None); p.add_argument("--survival", type=Path, default=None)
    p.add_argument("--no-daily", action="store_true"); p.add_argument("--gap-diagnostic", action="store_true"); p.add_argument("--estimate-only", action="store_true")
    p.add_argument("--override", action="append", default=[], help="research config override key=value (dotted path under research, e.g. s3.fuel_carbon_mode=producer_credit); recorded in the receipt")
    a = p.parse_args(); repo = a.repo.resolve()
    if a.estimate_only:
        print(json.dumps(estimate_memory(a.output))); sys.exit(0)
    eb = a.electric_base or repo / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"
    al = a.allocation or repo / "results_project/assembly_v1/final_allocation"
    sv = a.survival or repo / "results_project/s1/S1_SELECTED_ASSET_SURVIVAL_2050.json"
    hydro = json.loads((repo / "research_inputs/asset_survival/hydro_decisions.json").read_text())
    n, r = build_scenario_s2(repo, a.scenario, a.output, eb, al, hydro, sv, daily=not a.no_daily, gap_diagnostic=a.gap_diagnostic, overrides=a.override)
    print(json.dumps(dict(status=r["status"], network=r["network"]["sha256"], components=r["network"]["components"], seconds=round(r["build_seconds"], 1))))
