"""M08-0 (item 130, 2026-10-20): registry backfill and consistency corrections - registry only.

No model, configuration, build / solve script, network or result is changed; nothing is built or solved. The registry records what the
screening runs actually used ("as built"): values are read from the read-only extraction of the S4O / S4N screening networks
(research/06_scope_redesign/p1_m080_20261020/scripts/m080_extract.py -> evidence/M080_EXTRACT.json and CSVs).

Writes
  * research_inputs/registry_v5/fragments/m080.csv              new rows (registry gaps, MEET-D DATA_INVENTORY section J items 1-5, item 2 check)
  * research_inputs/registry_v5/fragments/m080_corrections.csv  full replacement rows for existing param_ids (MEET-D section I items 3, 5, 6, 7
                                                                and the related status / tier fixes); d1_registry.py applies them after
                                                                concatenating the fragments, the original fragments stay unchanged (history)
Existing rows are always taken from the original fragments (never from DATA_REGISTRY.csv), so the script is idempotent.

    python scripts_project/m080_data.py [--steps M1 M2 M3]    then    python scripts_project/d1_registry.py
"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from d1_common import ASEAN, COLUMNS, REG_DIR, ROOT, Registry, read_csv, sha256, write_csv

SCRIPT = "scripts_project/m080_data.py"
DEC = "130"
EVD = ROOT / "research/06_scope_redesign/p1_m080_20261020/evidence"
EXTRACT = EVD / "M080_EXTRACT.json"
VRE_CSV = EVD / "M080_VRE_CAPS_BY_COUNTRY.csv"
LNG_CSV = EVD / "M080_LNG_CAPS_BY_NODE.csv"
FLEET_CSV = EVD / "M080_EXISTING_FLEET_COST_BASIS.csv"
FX_2020 = 0.8772286325726557          # fx_usd_to_eur_2020 (registry, ECB 2020 mean)
AEO8_SHA = "AEO8 pdf:48c2a81913ed785cb0e14a55e332ea7bc87f912f7fabfbc8c654e09b66b11c06"   # as in smr_investment
OGCI_SHA = "CSRC_Cycle_5_Appendix_B_Asia-_August_2025.pdf:ff21cd340a252fee43321740742f5267a03a868c9ecf558b30c297b6138c6d0f"
AUTHOR_CODE = "pypsa-asean @5bacad70 (author paper commit; worktree phase2/paper_reference)"
AUTHOR_SHA = {"prepare_sector_network.py": "ade3014d041da647e78954bccce91ee07ced8c08cf7903e8eae1b38fc8f3fa8f",
              "cluster_global_buildings.py": "ca2daaf8f5dc5fde471cbd1116bff548c2e08d630da2f9c934fd4ce2bbd99f4f",
              "build_demand_profiles.py": "8d3bbab969ed201140ec323bbccbe93a9432aab25c5bd9d56dd3a10ddc3d45f6",
              "build_renewable_profiles.py": "c2a22a0de291a106c1cca0ed8f7e5695bdc82ca77772522793d5014addc17632"}
TECH_KEY = {"solar": "solar", "onwind": "onwind", "offwind-ac": "offwind_ac", "offwind-dc": "offwind_dc", "solar rooftop": "solar_rooftop"}
MARK = "[M08-0 item 130]"
STEPS: set[str] = set()   # set in main(); P1..P4 = M08-0 supplement 01 (item 131)
# supplement 01 section 2: GEGIS original publication, verified (a) in the PyPSA-Earth docs of the author chain and (b) against the Crossref record of the DOI
GEGIS_REF = ("Mattsson N., Verendel V., Hedenus F., Reichenberg L. (2021) 'An autopilot for energy models - Automatic generation of renewable supply "
             "curves, hourly capacity factors and hourly ...' (title truncated here), Energy Strategy Reviews 33, 100606, doi:10.1016/j.esr.2020.100606")
GEGIS_DOC_LOC = ("PyPSA-Earth docs cite GEGIS with doi:10.1016/j.esr.2020.100606: pypsa-asean @5bacad70 doc/data_workflow.rst 103 (author paper commit) and "
                 "@ce327bfa doc/user-guide/data-workflow.md 89, doc/tutorials/use-cases/3-demand-data.md 53")
GEGIS_DOC_SHA = ("data_workflow.rst@5bacad70:396c254f59a23783e012690fcfad31228a40fef684bd4ab426881c4f2a1ad5bd|"
                 "data-workflow.md@ce327bfa:f29d770a83f9ca56943a071b9a2154921b11eb5686d57aef3834f53e95ee9a69|"
                 "3-demand-data.md@ce327bfa:f41314540d0f443b6e28ef3b2f747bbf4b4b5283e5000823821483c008b160b2")
GEGIS_CITE_NOTE = ("Original publication (M08-0 supplement 01, item 131; verified): the PyPSA-Earth documentation of the author chain names GEGIS "
                   "(GlobalEnergyGIS, github.com/niclasmattsson/GlobalEnergyGIS; profiles extracted with the synde workflow, machine learning on temperature, "
                   "population and GDP) and links doi:10.1016/j.esr.2020.100606; the Crossref record of that DOI (read 2026-10-21) gives Mattsson, Verendel, "
                   "Hedenus, Reichenberg, Energy Strategy Reviews 33, article 100606, issued 2021-01, title beginning 'An autopilot for energy models - "
                   "Automatic generation of renewable supply curves, hourly capacity factors and hourly ...' = the reviewer's citation (the DOI carries 2020, "
                   "the volume is 2021)")
# supplement 01 section 1: rooftop PV comparison figures already in the registry (record only, values not changed)
ROOFTOP_REF = {"ID": [("AEO8 p.140 (potential_solar_rooftop_ID_aeo8)", 194000.0, 655000.0, "MWp")],
               "MY": [("AEO8 p.140 (potential_solar_rooftop_MY_aeo8)", 34000.0, 34000.0, "MWp"), ("SEDA MyRER 2021 rooftop (potential_solar_rooftop_MY_myrer)", 42000.0, 42000.0, "MW")],
               "VN": [("AEO8 p.140 (potential_solar_rooftop_VN_aeo8)", 370000.0, 370000.0, "MWp"), ("PDP8 Decision 500/QD-TTg rooftop (potential_solar_rooftop_VN_pdp8_technical)", 48200.0, 48200.0, "MW")]}


def load():
    ev = json.loads(EXTRACT.read_text(encoding="utf-8"))
    return ev, pd.read_csv(VRE_CSV), pd.read_csv(LNG_CSV), pd.read_csv(FLEET_CSV)


def net_sha(ev):
    f = ev["files"]
    return f"integrated:{f['integrated']['sha256']}|disconnected:{f['disconnected']['sha256']}"


# ------------------------------------------------------------------------------------------------------------------------------
# M1: backfill (DATA_INVENTORY section J items 1-5)
# ------------------------------------------------------------------------------------------------------------------------------
def m1_rows(reg: Registry, ev, vre, lng):
    f = ev["files"]
    nets = net_sha(ev)
    author = f"author:{f['author_net']['sha256']}"
    vcsv = f"M080_VRE_CAPS_BY_COUNTRY.csv:{sha256(VRE_CSV)}"
    rules = ev["author_renewable_rules"]
    # 1. ground PV / onshore / offshore wind and rooftop PV candidate caps per country (sum of p_nom_max over nodes and resource classes)
    vi = vre[vre.network == "integrated"].set_index(["carrier", "country"])
    for car, key in TECH_KEY.items():
        for c in ASEAN:
            r = vi.loc[(car, c)]
            v = float(r.p_nom_max_mw)
            if car == "solar rooftop":
                desc = (f"{c} rooftop PV candidate cap as built: sum of p_nom_max of the {int(r.generators)} 'solar rooftop' candidates ({int(r.nodes)} nodes) in the "
                        "S4O / S4N screening networks (integrated = disconnected); inherited unchanged from the electric base <- author paper network "
                        "(PyPSA-Earth prepare_sector_network.py add rooftop with use_building_size: p_nom_max = 0.1 kW/m2 x useful rooftop area; see "
                        "renewable_rooftop_method_built); availability profile = the node ground-PV c1 profile")
                tier, loc = "B", f"generators carrier 'solar rooftop', bus country {c}, sum p_nom_max"
                if "P1" in STEPS:   # supplement 01 section 1: not reproducible here (building inputs not local) -> grade C, +-50 %
                    tier = "C"
                    refs = ROOFTOP_REF.get(c)
                    cmp_txt = ("; comparison (record only, value not changed): " + "; ".join(
                        f"{src} {lo / 1e3:,.1f}" + (f"-{hi / 1e3:,.1f}" if hi != lo else "") + f" G{u[1:]} -> model / reference = "
                        + (f"{v / hi:.2f}-{v / lo:.2f}" if hi != lo else f"{v / lo:.2f}") for src, lo, hi, u in refs)
                           if refs else "; no official comparison figure in the registry for this country")
                    desc += ("; grade C (M08-0 supplement 01, item 131): the Microsoft building footprints are not in the local cache, so the value cannot "
                             "be reproduced here; sensitivity 0.5x-1.5x" + cmp_txt)
            else:
                rule = rules[car]
                desc = (f"{c} {car} candidate cap as built: sum of p_nom_max over {int(r.generators)} candidate generators ({int(r.nodes)} nodes, 3 resource classes, "
                        f"sum unchanged by the class split, S4B-3) in the S4O / S4N screening networks (integrated = disconnected); inherited unchanged from the "
                        f"electric base <- author paper network: PyPSA-Earth build_renewable_profiles potential 'simple' = {rule['capacity_per_sqkm']} MW/km2 x "
                        f"eligible area (Copernicus LC100 codes {rule['copernicus']['grid_codes']}, natura excluded"
                        + (f", max depth {rule.get('max_depth')} m (GEBCO), shore distance {'<=' if 'max_shore_distance' in rule else '>='} "
                           f"{(rule.get('max_shore_distance') or rule.get('min_shore_distance')) / 1000:.0f} km" if car.startswith("offwind") else "")
                        + (f", {rule['copernicus']['distance']} m buffer from code {rule['copernicus']['distance_grid_codes']}" if car == "onwind" else "")
                        + f"); see renewable_landcover_codes_built_{key}, renewable_density_built_{key}")
                tier, loc = "B", f"generators carrier '{car}', bus country {c}, sum p_nom_max (all classes)"
            status = "REGISTERED"
            if v == 0.0:
                status = "SOURCE_ZERO"
                desc += (" - zero: no candidate generator in the network for this country" if int(r.generators) == 0
                         else f" - zero: {int(r.generators)} candidate(s) with p_nom_max 0 (no eligible cells in the author layout)")
            c_grade = tier == "C"
            reg.add(f"renewable_cap_built_{key}_{c}", desc, v, "MW", tier,
                    "S4O cloud package unsolved networks (365x24h, build 126110ff) <- electric_base_2050_unsolved.nc <- author paper network "
                    "elec_s_100_ec_lv2.0__3h_2025_0.071_DEC_0export.nc (results-asean-paper-v1)", loc, f"{nets}|{author}|{vcsv}", country=c,
                    sensitivity_low=v * 0.5 if c_grade else None, sensitivity_high=v * 1.5 if c_grade else None,
                    decision_ref=f"{DEC}; 70-75" + ("; 131" if c_grade else ""), status=status)
    # land rules (author network meta renewable block = pypsa-asean config.default.yaml renewable block)
    meta_loc = "author paper network meta['renewable'][tech] (pypsa-asean config.default.yaml renewable block; PyPSA-Earth build_renewable_profiles.py 707-760)"
    for car in ("solar", "onwind", "offwind-ac", "offwind-dc"):
        rule, key = rules[car], TECH_KEY[car]
        codes = rule["copernicus"]["grid_codes"]
        extra = []
        if car == "onwind":
            extra.append(f"{rule['copernicus']['distance']} m distance to codes {rule['copernicus']['distance_grid_codes']} (urban)")
        if car.startswith("offwind"):
            extra.append(f"max_depth {rule['max_depth']} m (GEBCO 2025)")
            extra.append(f"max_shore_distance {rule['max_shore_distance']} m" if "max_shore_distance" in rule else f"min_shore_distance {rule['min_shore_distance']} m")
        reg.add(f"renewable_landcover_codes_built_{key}",
                f"{car} eligible Copernicus LC100 classes in the as-built layout (eligible = listed codes, all other classes excluded"
                + ("; forest 111-126 and water 80 / 200 are excluded" if car == "solar" else "; forest 111-126 eligible" if car == "onwind" else "") + "); "
                f"natura exclusion {'yes' if rule['natura'] else 'no'} (protected_areas_local_natura); "
                + ("; ".join(extra) + "; " if extra else "") + f"potential '{rule['potential']}'; renewable_copernicus_lc100_file",
                ",".join(str(x) for x in codes), "LC100 class codes", "B", "author paper network meta / PyPSA-Earth (pypsa-asean fork)", meta_loc,
                f"{author}|build_renewable_profiles.py:{AUTHOR_SHA['build_renewable_profiles.py']}", decision_ref=DEC)
        reg.add(f"renewable_density_built_{key}",
                f"{car} installable capacity density in the as-built potential (capacity_per_sqkm) "
                + ("(PyPSA-Eur v2025.07.0: 5.1; S4R / decision 129 propose 5.1 for M08, not applied)" if car == "solar" else ""),
                float(rule["capacity_per_sqkm"]), "MW/km2", "B", "author paper network meta / PyPSA-Earth (pypsa-asean fork)",
                meta_loc + " capacity_per_sqkm", f"{author}|build_renewable_profiles.py:{AUTHOR_SHA['build_renewable_profiles.py']}", decision_ref=DEC)
    bde = ev["author_databundles"]["bundle_data_earth"]
    for pid, k, name, src in [
            ("renewable_copernicus_lc100_file", "copernicus_lc100", "PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif",
             "Copernicus Global Land Service, Land Cover 100 m (PROBA-V LC100) v3.0.1, epoch 2019 (nrt), discrete classification map"),
            ("renewable_gebco_file", "gebco", "GEBCO_2025_sub_ice.nc",
             "GEBCO (Nippon Foundation-GEBCO Seabed 2030 Project), The GEBCO_2025 Grid, DOI 10.5285/37c52e96-24ea-67ce-e063-7086abc05f29, public domain (file attributes)"),
            ("renewable_eez_file", "eez", "eez_v11.gpkg", "Marine Regions (VLIZ), EEZ v11, CC BY 4.0 (LICENSE_EEZ_v11.txt)")]:
        reg.add(pid, f"Land / sea layer of the as-built renewable potentials: data/{name.split('_')[0].lower() if k != 'copernicus_lc100' else 'copernicus'}/{name}, delivered by the PyPSA-Earth "
                     f"data bundle bundle_data_earth ({bde['urls'].get('zenodo')}; listed in the author network meta databundles.output). The SHA256 is of the "
                     "local author-chain copy (pypsa-asean/data, same bundle); the author's own copy was not hashed in the author outputs",
                name, "file", "A", src, f"pypsa-asean/data/{'copernicus' if k == 'copernicus_lc100' else k}/{name} ({f[k]['bytes']} B)", f[k]["sha256"], decision_ref=DEC)
    for cls in ("c1", "c3"):
        fn = f"profiles_calibrated_modern_{cls}_3h.nc"
        reg.add(f"renewable_profile_file_calibrated_modern_{cls}_3h",
                f"Availability profiles read by the screening build (network meta research_renewable.files; profile_variant calibrated_modern, resource_classes 3): "
                f"{fn} - onshore wind S4B-3 calibrated (alpha x ERA5 100 m + DEA 2050 turbine), offshore wind and solar identical to the pypsa_eur rebuild "
                "(renewable_offwind_profile_check_built)" + ("; c1 = node profile used for rooftop PV" if cls == "c1" else ""),
                fn, "file", "B", "scripts_project/s4a_profiles.py --variant calibrated_modern (atlite 0.4.1, ERA5 2013 cutout)", "research_inputs/renewable_v5",
                f[fn]["sha256"], decision_ref=f"{DEC}; 74, 75")
    rc = ev["author_rooftop_cfg"]
    reg.add("renewable_rooftop_method_built",
            "Rooftop PV candidate potential of the author chain (inherited): use_building_size = true -> p_nom_max = kW_per_m2 "
            f"{rc['kW_per_m2']} x useful rooftop area per node; useful area = Microsoft Global ML Building Footprints (download_global_buildings.py) footprint "
            f"area x install ratio by building size {rc['install_ratio']} (m2 thresholds; cluster_global_buildings.py, method of H. Obane, IEEJ); "
            "the building inputs and the per-node layout CSVs are not in the local cache, so the values cannot be recomputed here (inheritance verified, "
            "upstream derivation not reproduced)" + ("; grade C (M08-0 supplement 01, item 131): grade B needs script + input hashes and "
                                                     "reproducibility, the building inputs are not available here; per-country rows carry 0.5x-1.5x"
                                                     if "P1" in STEPS else ""),
            "building_size", "flag", "C" if "P1" in STEPS else "B",
            "author paper network meta['sector']['solar_rooftop'] and author code", f"{AUTHOR_CODE}: prepare_sector_network.py 2862-2925; cluster_global_buildings.py 30-75",
            f"{author}|prepare_sector_network.py:{AUTHOR_SHA['prepare_sector_network.py']}|cluster_global_buildings.py:{AUTHOR_SHA['cluster_global_buildings.py']}",
            decision_ref=DEC + ("; 131" if "P1" in STEPS else ""))
    # 3. Astar base-load hourly shape
    lo = ev["author_load_options"]
    av = ev["astar_vs_gegis"]
    own = [c for c in ASEAN if c not in lo["substitute"]]
    min_corr = min(av[c]["corr"] for c in own)
    g = ev["gegis_attrs"]
    gsha = f"gegis:{f['gegis_asia']['sha256']}|{author}|build_demand_profiles.py:{AUTHOR_SHA['build_demand_profiles.py']}"
    reg.add("demand_astar_shape_source",
            "Hourly shape and node split of the Astar base load (national final electricity account; S4J-1 table_sectors: annual total from the demand "
            "table, Astar = shape only): the base AC loads p_set of the author paper network (scripts_project/allocate_assembly_inputs.py, PIN 06152be5), "
            "generated by PyPSA-Earth build_demand_profiles from the GEGIS country profiles in data/ssp2-2.6/2030/era5_2013/Asia.nc (variable "
            f"'Electricity demand', attributes: '{g.get('description')}', SSP {g.get('SSP scenario')}, RCP {g.get('RCP scenario')}, projection year "
            f"{g.get('projection year')}, ERA5 weather year {g.get('weather data year (ERA5)')}, {g.get('unit')}), allocated to the nodes by GDP / population; "
            f"check: national author base-load shape vs the GEGIS profile corr >= {min_corr:.6f} for the 9 countries with own profiles "
            "(demand_astar_shape_gegis_check); LA / TL substituted (demand_astar_shape_substitution). "
            + (GEGIS_CITE_NOTE if "P2" in STEPS else "The GEGIS developer / publication is not stated in the local files (not filled in)")
            + "; the bundle is on sandbox.zenodo.org (not a permanent archive)",
            "data/ssp2-2.6/2030/era5_2013/Asia.nc", "file", "B",
            f"GlobalEnergyGIS projected electricity demand via the PyPSA-Earth data bundle bundle_data_earth ({bde['urls'].get('zenodo')})"
            + ("; " + GEGIS_REF if "P2" in STEPS else ""),
            f"pypsa-asean/data/ssp2-2.6/2030/era5_2013/Asia.nc ({f['gegis_asia']['bytes']} B); author meta load_options ssp {lo['ssp']}, weather_year "
            f"{lo['weather_year']}, prediction_year {lo['prediction_year']}" + ("; " + GEGIS_DOC_LOC if "P2" in STEPS else ""),
            gsha + ("|" + GEGIS_DOC_SHA if "P2" in STEPS else ""), decision_ref=f"{DEC}; 104" + ("; 131" if "P2" in STEPS else ""))
    reg.add("demand_astar_shape_substitution",
            (("EXCEPTION (grade C, M08-0 supplement 01, item 131) to the GEGIS country-profile rule for the two countries whose GEGIS profile is zero - rule "
              "(PyPSA-Earth build_demand_profiles.py 239-253 at 5bacad70): the own GEGIS rows of LA / TL are dropped, the hourly profile of KH (for LA) / "
              "ID (for TL) is copied and normalised to mean 1 (shape only), then multiplied by load_options.scale (LA 1,456.62, TL 47.35 MW mean load); "
              "under S4J-1 table_sectors only the shape is used, the annual total comes from the demand table. ") if "P2" in STEPS else "")
            + f"Author load_options for countries with a zero GEGIS profile: substitute {lo['substitute']}, scale {lo['scale']} (LA uses the KH shape, TL the ID "
            f"shape; checked: LA vs KH corr {av['LA']['corr']:.4f}, TL vs ID corr {av['TL']['corr']:.6f}); author assumption, no source given",
            ";".join(f"{k}<-{v} x{lo['scale'][k]}" for k, v in lo["substitute"].items()), "flag", "C", "author paper network meta['load_options']",
            "load_options.substitute / scale" + ("; build_demand_profiles.py 239-253 (5bacad70)" if "P2" in STEPS else ""),
            gsha, decision_ref=f"{DEC}; 104" + ("; 131" if "P2" in STEPS else ""))
    reg.add("demand_astar_shape_gegis_check",
            "Correlation of the national author base-load shape (3 h) with the GEGIS Asia.nc country profile (3 h means), minimum over BN ID KH MM MY PH SG "
            "TH VN: " + ", ".join(f"{c} {av[c]['corr']:.7f}" for c in own) + "; scale-factor CV <= 1.2e-3 (shape identical up to a constant)",
            min_corr, "correlation", "B", "m080_extract.astar_check", "evidence/M080_EXTRACT.json astar_vs_gegis", f"extract:{sha256(EXTRACT)}|{gsha}",
            decision_ref=DEC, status="REFERENCE_ONLY")
    # 4. geothermal new-build main values (decision 52): AEO8 D.15 Geothermal average x FX
    geo = ev["geothermal_new_costs"]
    csha = f"{AEO8_SHA}|costs_active_research.csv:{f['integrated_costs_active_research.csv']['sha256']}"
    for pid, val, unit, what, srcv in [
            ("geothermal_new_investment_main", geo["investment"] / 1e3, "EUR2020/kW", "investment", "4,100 kUSD/MW x FX"),
            ("geothermal_new_FOM_main", geo["FOM"], "%/a", "FOM", "19.5 kUSD/MW/a / 4,100 kUSD/MW x 100"),
            ("geothermal_new_VOM_main", geo["VOM"], "EUR2020/MWh", "VOM", "0.3 USD/MWh x FX")]:
        reg.add(pid, f"Geothermal electricity {what} in the screening networks (decision 52, grade C, +-30 %): AEO8 Table D.15 'Geothermal average' "
                     f"{srcv} (fx_usd_to_eur_2020 {FX_2020:.10f}), no decline; network cost table row geothermal; the same FOM / VOM price the existing "
                     "geothermal units (s2_layers.py 119-140); lifetime 30 a from the active layer",
                val, unit, "C", "ACE (2024) 8th ASEAN Energy Outlook, Table D.15 row Geothermal average", "scripts_project/s2_costs.py build_research_costs "
                "(geothermal block, 126110ff); integrated_costs_active_research.csv row geothermal", csha, sensitivity_low=val * 0.7, sensitivity_high=val * 1.3,
                decision_ref=f"{DEC}; 52")
    # 5. LNG import caps as built (decision 72) - the 2.5 x existing rows stay (corrections add the note)
    lr = ev["lng_rule"]
    li = lng[lng.network == "integrated"]
    lsha = f"{nets}|LNG_IMPORT_TERMINALS_GEM_2025.csv:{f['lng_terminal_table']['sha256']}|GEM-GGIT-LNG-Teminals-2025-09.xlsx:{f['gem_lng_xlsx']['sha256']}"
    skipped = ", ".join(sorted(ev["lng_skipped_nodes"]))
    reg.add("lng_import_cap_rule_built",
            f"LNG import cap rule of the screening networks (research.s3.gas.lng_expansion = {lr['expansion']}, decision 72): per terminal node p_nom_max = "
            f"{lr['cap_factor']} x existing (GEM operating + construction) where existing > 0, else the proposed capacity; expansion above the existing "
            f"capacity priced at {lr['expansion_capital_cost_eur_per_mw_a']:.0f} EUR/MW/a; nodes without capacity data are skipped ({skipped}); "
            "annual cap = p_nom_max x 8,760 h", lr["expansion"], "flag", "C", "scripts_project/s3_layers.add_gas_network (126110ff) section 4",
            "network meta research_gas_network.lng", lsha, decision_ref=f"{DEC}; 17, 19, 68, 72")
    for c in ASEAN:
        s = li[li.country == c]
        v = float(s.p_nom_max_mw.sum()) * 8760.0
        nodes = "; ".join(f"{r.node}: {r.rule}, p_nom {r.p_nom_mw:.1f} MW, p_nom_max {r.p_nom_max_mw:.1f} MW" for r in s.itertuples())
        reg.add(f"lng_import_cap_built_{c}",
                f"{c} LNG import cap as built (decision 72 rule, lng_import_cap_rule_built): sum over the country's 'LNG import' generators of p_nom_max x "
                f"8,760 h = {v / 1e6:.2f} TWh/a (integrated = disconnected)" + (f"; nodes: {nodes}" if len(s) else "; no LNG import generator (no terminal with capacity data)")
                + f"; lng_import_cap_{c} (2.5 x existing) is only the existing-capacity part of the rule",
                v, "MWh/a", "B", "S4O cloud package unsolved networks (365x24h, build 126110ff); research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv "
                "(GEM GGIT LNG Terminals, September 2025 release)", f"generators carrier 'LNG import', country {c}; M080_LNG_CAPS_BY_NODE.csv",
                lsha, country=c, decision_ref=f"{DEC}; 72", status="REGISTERED" if v > 0 else "SOURCE_ZERO")


# ------------------------------------------------------------------------------------------------------------------------------
# M2: offshore wind turbine / wake check (verification row)
# ------------------------------------------------------------------------------------------------------------------------------
def m2_rows(reg: Registry, ev):
    p = ev["profiles"]
    f = ev["files"]
    same = all(p[f"{c}:{v}"]["pypsa_eur"]["identical"] for c in ("c1", "c3") for v in ("offwind_ac", "offwind_dc"))
    diff_fork = max(p[f"{c}:{v}"]["fork"]["max_abs_diff"] for c in ("c1", "c3") for v in ("offwind_ac", "offwind_dc"))
    reg.add("renewable_offwind_profile_check_built",
            "Offshore wind profile of the screening networks (M08-0 item 2): the offwind_ac / offwind_dc arrays of profiles_calibrated_modern_c1/c3_3h.nc are "
            f"identical to the pypsa_eur rebuild (identical = {same}; vs the fork rebuild max |diff| {diff_fork:.3f}); s4a_profiles.py at the build commit "
            "126110ff: pypsa_eur offwind = NREL_ReferenceTurbine_2020ATB_5.5MW (hub 120 m), correction_factor 0.8855 (wake proxy), add_cutout_windspeed; "
            "NREL_ReferenceTurbine_5MW_offshore without wake correction is the author / fork setting only. The offshore p_nom_max is the author layout "
            "(turbine-independent). The S4R description of the current state ('NREL 5 MW, no wake') does not apply to the screening networks",
            "NREL_ReferenceTurbine_2020ATB_5.5MW x 0.8855", "flag", "B", "m080_extract.profile_check; scripts_project/s4a_profiles.py VARIANTS (126110ff)",
            "evidence/M080_EXTRACT.json profiles, s4a_profiles_offwind_variants",
            f"calibrated_modern_c3:{f['profiles_calibrated_modern_c3_3h.nc']['sha256']}|pypsa_eur_c3:{f['profiles_pypsa_eur_c3_3h.nc']['sha256']}|"
            f"fork_c3:{f['profiles_fork_c3_3h.nc']['sha256']}", decision_ref=f"{DEC}; 70-74", status="REFERENCE_ONLY")


# ------------------------------------------------------------------------------------------------------------------------------
# M3: corrections of existing rows (DATA_INVENTORY section I items 3, 5, 6, 7; related status fixes)
# ------------------------------------------------------------------------------------------------------------------------------
def m3_rows(reg: Registry, ev, fleet):
    f = ev["files"]
    gem = ev["gem_about"]
    rel = next((s for s in gem if "release." in s and "Copyright" in s), gem[0])
    reg.add("lng_gem_ggit_release_verified",
            "GEM LNG terminal workbook release as stated in the file (sheet 'About GGIT LNG'): '" + rel.replace("©", "(c)")[:160]
            + "'; file creation date October 14, 2025; the S4R download (p1_s4r_downloads_20261020/F2_lng/gem-download (1).zip) contains the identical "
            "workbook (same SHA256). Registry label 'GEM GGIT LNG Terminals 2025-09' is correct; the S4R label '2025-08' is not",
            "September 2025 release", "release", "A", "Global Energy Monitor, Global Gas Infrastructure Tracker - LNG Terminals",
            "work/p2_data_intake/raw/GEM-GGIT-LNG-Teminals-2025-09.xlsx sheet About GGIT LNG", f"GEM-GGIT-LNG-Teminals-2025-09.xlsx:{f['gem_lng_xlsx']['sha256']}",
            decision_ref=DEC, status="REFERENCE_ONLY")
    ccgt = fleet[(fleet.technology == "CCGT") & (fleet.existing_origin.str.startswith("electric_base"))]
    eb = ev["electric_base_cost_layer"]
    reg.add("cost_v0132_usage_built",
            "Use of technology-data v0.13.2 in the screening networks (M08-0 item 3): new-build candidates are priced on the active layer v0.15.0 "
            "(+ AEO8 D.15 nuclear SMR and geothermal; receipt cost_layer rows); v0.13.2 enters numerically only through (i) smr_lifetime_proxy / "
            "smr_efficiency_proxy (read by s2_costs.py; values identical to v0.15.0 nuclear), (ii) existing-asset lifetimes of the S1 survival rule "
            "(identical to v0.15.0 for every technology checked), (iii) the electric-base existing-asset cost layer of Assembly V1 (model_cost_layer.json: "
            f"{eb['by_prior_transformation'].get('TECHNOLOGY_DATA_V0_13_2_ALREADY_REBASED_EUR2020', 0)} of {eb['rows']} rows = author technology-data v0.13.2 "
            f"costs rebased to EUR2020, author costs year 2030): existing fixed O&M constant {eb['existing_annual_fixed_om_eur_in_network'] / 1e9:.2f} bn EUR/a "
            f"and inherited existing CCGT efficiency {ccgt.existing_eff_values.iloc[0] if len(ccgt) else 'n/a'} vs 0.6 for new / GEM-added CCGT. Item (iii) is "
            "a unification issue for M08 (not changed here)", "mixed", "flag", "B", "m080_extract (screening networks, receipt, assembly_v1 model_cost_layer.json)",
            "evidence/M080_EXTRACT.json electric_base_cost_layer, existing_fleet_efficiency; M080_EXISTING_FLEET_COST_BASIS.csv",
            f"{net_sha(ev)}|model_cost_layer.json:{eb['sha256']}|M080_EXISTING_FLEET_COST_BASIS.csv:{sha256(FLEET_CSV)}", decision_ref=f"{DEC}; 46, 50, 82",
            status="REFERENCE_ONLY")


def corrections(ev):
    """Full replacement rows for existing param_ids (taken from the original fragments, so repeated runs give the same rows)."""
    frags = {}
    for p in sorted((REG_DIR / "fragments").glob("*.csv")):
        if p.stem.startswith("m080"):
            continue
        for r in read_csv(p):
            frags[r["param_id"]] = (p.stem, r)
    f = ev["files"]
    nd = ev["natura_dataverse_file"]
    out = []

    def fix(pid, step, note, **changes):
        frag, r = frags[pid]
        r = dict(r)
        for k, v in changes.items():
            r[k] = v
        r["description"] = (changes.get("description") or r["description"]) + f" | {MARK} {note}"
        r["decision_ref"] = (r["decision_ref"] + "; " if r["decision_ref"] else "") + DEC
        out.append(dict(step=step, fragment=frag, row=r, changed=sorted(k for k in changes if k != "description")))

    # M1 item 5: keep the 2.5 x existing LNG rows, state that they are only part of the decision-72 rule
    for c in ASEAN:
        fix(f"lng_import_cap_{c}", "M1",
            f"only the existing-capacity part of the decision-72 rule (nodes with existing capacity: 2.5 x existing); the screening networks use "
            f"lng_import_cap_built_{c} (proposed-only sites at their proposed capacity)")
    # M3 section I item 5: natura layer is in use
    fix("protected_areas_local_natura", "M3",
        "in use: natura exclusion layer of every as-built solar / wind potential (author meta renewable.<tech>.natura = true, build_natura_raster = false -> "
        f"bundle file); Harvard Dataverse {nd['doi']} V{nd['version']} ({nd['release'][:10]}), file {nd['filename']} ({nd['filesize']} B, MD5 {nd['md5']} = "
        f"local natura.tiff MD5 {f['natura']['md5']}), {nd['license']}; delivered by PyPSA-Earth bundle_natura_earth (natura_wpda_CC0.zip)",
        status="REGISTERED", source=f"Sosa Arango (2020) Protected areas (WDPA), Harvard Dataverse {nd['doi']} V{nd['version']}, file {nd['filename']}, {nd['license']}",
        source_sha256=f"{f['natura']['sha256']}|dataverse_md5:{nd['md5']}")
    # M3 section I item 6: v0.13.2 rows
    fix("cost_layer_A_technology_data_v0_13_2_2050", "M3",
        "历史：已被 cost_layer_C_technology_data_v0_15_0_2050_eur2020 替代 (historical: superseded as the main cost layer by decision 50; configs/research/"
        "baseline.yaml keeps it selectable as a sensitivity layer; the electric-base existing-asset costs still come from the author v0.13.2 table, see "
        "cost_v0132_usage_built)", status="REFERENCE_ONLY")
    for pid, v15 in (("smr_lifetime_proxy", "cost_C_nuclear_lifetime 40"), ("smr_efficiency_proxy", "cost_C_nuclear_efficiency 0.326")):
        fix(pid, "M3", f"read by the build (s2_costs.py:88); the value equals technology-data v0.15.0 nuclear ({v15}), so the v0.13.2 label has no numerical effect")
    fix("geothermal_existing_FOM", "M3",
        "历史：已被 geothermal_new_FOM_main 替代 (historical: the screening networks price existing geothermal FOM with the active-layer geothermal row, AEO8 "
        "D.15 0.4756 %/a = 17,106 EUR/MW/a, s2_layers.py 119-140; this v0.13.2 value is not used)", status="REFERENCE_ONLY")
    fix("geothermal_existing_lifetime", "M3",
        "used through the S1 asset-survival lifetime (lifetime source file = technology-data v0.13.2 costs_2050.csv); identical to v0.15.0 "
        "(cost_C_geothermal_lifetime 30)")
    fix("geothermal_existing_CO2_intensity", "M3",
        "not applied: carrier geothermal has co2_emissions 0 in the screening networks (non-condensable gas CO2 ignored, PyPSA-Eur practice; receipt "
        "geothermal.co2_simplification)", status="REFERENCE_ONLY")
    for pid, val, note in (("geothermal_existing_VOM", "not_in_v0_13_2", "历史：已被 geothermal_new_VOM_main 替代 (AEO8 D.15 0.263 EUR2020/MWh also prices the existing units)"),
                           ("geothermal_existing_efficiency", "not_in_v0_13_2", "not pending: the screening networks model geothermal electricity with efficiency 1.0 (cost table row geothermal)"),
                           ("geothermal_existing_investment", "not_in_v0_13_2", "not pending: existing units carry no investment (existing_cost_boundary: New CAPEX = 0)")):
        fix(pid, "M3", note, status="REFERENCE_ONLY", value=val)
    # M3 section I item 7: KH / TL storage potential not re-checkable -> grade C (values unchanged)
    why = "OGCI/CSRC Cycle 5 could not be re-checked (S4P EXTERNAL_SOURCES: bot check), grade A -> C; value kept as used in the screening runs"
    fix("co2_storage_potential_KH", "M3", why, tier="C")
    fix("co2_storage_potential_TL", "M3", why, tier="C")
    fix("co2_storage_component_KH_undiscovered_saline_text_about_85_mt", "M3", why + "; sensitivity range copied from co2_storage_potential_KH (0-0.132 Gt, D1)",
        tier="C", sensitivity_low="0", sensitivity_high="0.132")
    fix("co2_storage_component_TL_ogci_aggregated", "M3", why + "; sensitivity range copied from co2_storage_potential_TL (0-0.25 Gt, D1)",
        tier="C", sensitivity_low="0", sensitivity_high="0.25")
    # related status fixes found in M08-0 (registry vs build)
    sd = f["shipdensity_zip"]
    fix("renewable_ship_density_raster", "M3",
        f"not pending: the file is in the data intake (work/p2_data_intake/raw12/shipdensity_global.zip, {sd['bytes']} B, SHA256 verified, "
        "offshore_shipdensity_raw12_verified); not used by the screening networks (no shipping-lane exclusion, decision 76)",
        status="REFERENCE_ONLY", value="shipdensity_global.zip", source="World Bank (2021) Global Shipping Traffic Density, dataset 0037580, CC BY 4.0",
        source_locator="work/p2_data_intake/raw12/shipdensity_global.zip", source_sha256=sd["sha256"])
    fix("renewable_profile_variant", "M3",
        "历史：已被 renewable_profile_variant_s4b3 替代 (calibrated_modern since S4B-3, decision 74; its offshore wind and solar arrays are this pypsa_eur rebuild)",
        status="REFERENCE_ONLY")
    fix("renewable_resource_classes", "M3", "历史：已被 renewable_resource_classes_s4b3 替代 (3 classes since S4B-3, decision 75)", status="REFERENCE_ONLY")
    for v in ("fork_c1_3h", "fork_c3_3h", "pypsa_eur_c1_3h", "pypsa_eur_c3_3h"):
        fix(f"renewable_profile_file_{v}", "M3",
            "comparison file: not read by the screening build (network meta research_renewable.files = profiles_calibrated_modern_c1/c3_3h.nc, "
            "renewable_profile_file_calibrated_modern_*)", status="REFERENCE_ONLY")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", nargs="+", default=["M1", "M2", "M3", "P1", "P2", "P3", "P4"])
    a = ap.parse_args()
    STEPS.update(a.steps)
    ev, vre, lng, fleet = load()
    reg = Registry(SCRIPT)
    if "M1" in a.steps:
        m1_rows(reg, ev, vre, lng)
    if "M2" in a.steps:
        m2_rows(reg, ev)
    if "M3" in a.steps:
        m3_rows(reg, ev, fleet)
    reg.write(REG_DIR / "fragments" / "m080.csv")
    corr = [c for c in corrections(ev) if c["step"] in a.steps]
    write_csv(sorted((c["row"] for c in corr), key=lambda r: r["param_id"]), REG_DIR / "fragments" / "m080_corrections.csv", COLUMNS)
    log = dict(steps=a.steps, new_rows=len(reg.rows), new_by_status=pd.Series([r["status"] for r in reg.rows]).value_counts().to_dict(),
               corrections=[dict(param_id=c["row"]["param_id"], fragment=c["fragment"], step=c["step"], changed=c["changed"]) for c in corr],
               extract_sha256=sha256(EXTRACT))
    (EVD / "M080_REGISTRY_CHANGES.json").write_text(json.dumps(log, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(new_rows=log["new_rows"], new_by_status=log["new_by_status"], corrections=len(corr)), ensure_ascii=False))


if __name__ == "__main__":
    main()
