"""S3-1 data layer: existing cross-border gas pipelines (GEM GGIT 2025-11, batch 9), domestic production caps and LNG references.

Outputs (research_inputs/gas_v5/):
  * GAS_PIPELINES_EXISTING_CROSS_BORDER_2025.csv - the 2025 cross-border pipeline stock mapped to node pairs (decision 15 starting capacity);
    capacity MW_NCV = bcm/y x 1,199 MW per bcm/y (PyPSA-Eur build_gas_input_locations.py line 127: 1.199 MW per MCM/y, GCV-type gas
    accounting) x 0.90 GCV->NCV (registry fuel_price_basis). Rows without a GEM capacity stay DATA_PENDING (no capacity invented).
  * GAS_PIPELINES_NOTED_2025.csv - GEM rows considered but not modelled as cross-border links (JDA-Arthit, Sino-Myanmar, Trans-ASEAN), with reasons.
  * GAS_PRODUCTION_CAPS_2050.csv - UNSD 2019 gas production per country (D1 FOSSIL_PRODUCTION_CAPS_2050.csv, decision 43) with the node
    allocation basis (load shares, grade C) and the fugitive factor id used at build time.
Registry fragment gas_network.csv.

    python scripts_project/s3_1_gas_data.py
"""
from __future__ import annotations

import pandas as pd

from d1_common import ASEAN, REG_DIR, ROOT, SRC_DIR, Registry, sha256, src_sha, write_csv, write_json
from s2_costs import FUEL_PRICE_IDS

MAIN_FUEL_SCENARIO = "steps"   # S4C-0 (decision 85): configs/research/baseline.yaml research.fuels.price_scenario (main)

SCRIPT = "scripts_project/s3_1_gas_data.py"
GEM = "GEM_GGIT_GAS_PIPELINES_ASEAN.csv"
GEM_XLSX_SHA = "f56d8b14400e558f06e53a4205034d3d506fc38c5ae6bf58000252f87b1845e6"   # raw9/GEM-GGIT-Gas-Pipelines-2025-11.xlsx (SHA256SUMS_raw9.txt)
XY = "s1_network_nodes_xy.csv"
OUT = ROOT / "research_inputs/gas_v5"
PE_GAS_INPUT = SRC_DIR / "pypsa_eur_data" / "pypsa_eur_v2025.07.0_build_gas_input_locations.py"
MW_PER_BCM_Y_GCV = 1199.0      # PyPSA-Eur build_gas_input_locations.py line 127 (mcm_per_year_to_mw = 1.199)
GCV_TO_NCV = 0.90              # registry fuel_price_basis (natural gas TJ GCV x 0.90)
EXISTING = [
    dict(pipeline="Gresik-Batam-Singapore Gas Pipeline", from_node="ID_Sumatra2 0", to_node="SG2 0", direction="one_way",
         node_basis="GEM: Indonesia -> Singapore (468 km, Grissik, South Sumatra via Batam); the last Indonesian landfall is Batam (Riau Islands) -> node ID_Sumatra2 0 (104.03E 1.08N); Singapore -> SG2 0"),
    dict(pipeline="West Natuna Transportation System Gas Pipeline", from_node="ID_Sumatra2 0", to_node="SG2 0", direction="one_way",
         node_basis="GEM: Indonesia -> Singapore (640 km, offshore West Natuna, Riau Islands province) -> nearest Indonesian node ID_Sumatra2 0; lands in Singapore (SG2 0)"),
    dict(pipeline="Malaysia Singapore Gas Pipeline", from_node="MY_Peninsular2 1", to_node="SG2 0", direction="one_way",
         node_basis="GEM: Malaysia -> Singapore (70 km, Johor) -> southern Peninsular node MY_Peninsular2 1 (102.74E 2.69N); capacity not given by GEM -> DATA_PENDING (candidate on the MY_Peninsular2 1 - SG2 0 corridor only)"),
    dict(pipeline="Trans Thailand–Malaysia Gas Pipeline (TTM)", from_node="MY_Peninsular22 0", to_node="TH21 0", direction="bidirectional",
         node_basis="GEM: Malaysia -> Chana, Songkhla (267 km); Songkhla <-> Kedah/Perlis = the HVDC corridor node pair TH21 0 (100.43E 6.68N) / MY_Peninsular22 0 (100.51E 5.73N); the TTM system delivers JDA gas to both countries -> bidirectional"),
    dict(pipeline="Yetagun Gas Pipeline", from_node="MM2 4", to_node="TH2 2", direction="one_way",
         node_basis="GEM: Myanmar -> Thailand (472 km); Andaman offshore -> Kanbauk/Daminseik (Tanintharyi, ~14.5N 98.3E): nearest Myanmar node MM2 4 (97.98E 16.70N, no node further south); Thai end via the Ban I-Tong-Ratchaburi onshore line (GEM, operating) to Ratchaburi (~13.5N 99.8E): nearest TH2 2 (100.40E 14.41N); distinct from the unified electricity corridor MM2 4 - TH2 4 used for new candidates"),
    dict(pipeline="Yadana Gas Pipeline 1", from_node="MM2 4", to_node="TH2 2", direction="one_way",
         node_basis="GEM registers Yadana 1 as Myanmar-only (Yadana -> Daminseik, 409 km); Daminseik is the border landfall of the Thai export line to Ratchaburi -> modelled MM2 4 -> TH2 2 (same route basis as Yetagun); Yadana 2 (to Yangon) is domestic"),
    dict(pipeline="Zawtika Gas Pipeline", from_node="MM2 4", to_node="TH2 2", direction="one_way",
         node_basis="GEM registers Zawtika (operating row) as Myanmar-only (Zawtika -> Kanbauk, 300 km); Kanbauk feeds the Yadana export system to Thailand -> modelled MM2 4 -> TH2 2; the shelved duplicate row is ignored"),
]
NOTED = [
    dict(pipeline="JDA-Arthit Gas Pipeline", reason="offshore Malaysia-Thailand Joint Development Area -> Arthit field (Thailand), 95 km, capacity not given; JDA output is part of the UNSD production statistics of MY and TH (shared), so it enters the model as domestic production, not as a cross-border link; capacity DATA_PENDING (download list)"),
    dict(pipeline="Sino-Myanmar Gas Pipeline", reason="Kyaukpyu (MM) -> China: export outside ASEAN; imports only (no export option in the model)"),
    dict(pipeline="Trans-ASEAN Gas Pipeline", reason="shelved (GEM status), no route; candidates along the unified corridors cover the ASEAN-internal routes"),
]


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gem = pd.read_csv(SRC_DIR / GEM, dtype=str, keep_default_na=False); gem_sha = src_sha(GEM)
    xy = pd.read_csv(SRC_DIR / XY).set_index("Bus"); xy_sha = src_sha(XY)
    pe_sha = sha256(PE_GAS_INPUT)
    rows = []
    for e in EXISTING:
        g = gem[(gem.PipelineName == e["pipeline"]) & (gem.Status == "operating")]
        if len(g) != 1:
            raise ValueError(f"GEM row not unique for {e['pipeline']}: {len(g)}")
        g = g.iloc[0]
        bcm = num(g["CapacityBcm/y"]); boed = num(g["CapacityBOEd"]); L = num(g["LengthMergedKm"])
        mw = bcm * MW_PER_BCM_Y_GCV * GCV_TO_NCV if bcm is not None else None
        rows.append(dict(pipeline=e["pipeline"], gem_project_id=g["ProjectID"], gem_status=g["Status"], start_year=g["StartYear1"], countries=g["CountriesOrAreas"], capacity_bcm_per_year=bcm if bcm is not None else "",
                         capacity_boed=boed if boed is not None else "", capacity_mw_ncv=round(mw, 3) if mw is not None else "", length_km=L if L is not None else "",
                         from_node=e["from_node"], to_node=e["to_node"], country_from=xy.at[e["from_node"], "country"], country_to=xy.at[e["to_node"], "country"], direction=e["direction"],
                         node_basis=e["node_basis"], status="REGISTERED" if mw is not None else "DATA_PENDING",
                         source_locator=f"{GEM} PipelineName={e['pipeline']} (raw9 xlsx sheet Pipelines, SHA {GEM_XLSX_SHA[:16]})"))
    write_csv(rows, OUT / "GAS_PIPELINES_EXISTING_CROSS_BORDER_2025.csv", list(rows[0].keys()))
    noted = []
    for e in NOTED:
        g = gem[gem.PipelineName == e["pipeline"]]
        noted.append(dict(pipeline=e["pipeline"], gem_rows=len(g), gem_status=";".join(sorted(set(g.Status))), capacity_bcm_per_year=";".join(sorted(set(g["CapacityBcm/y"]))), reason=e["reason"]))
    write_csv(noted, OUT / "GAS_PIPELINES_NOTED_2025.csv", list(noted[0].keys()))
    caps = pd.read_csv(REG_DIR / "FOSSIL_PRODUCTION_CAPS_2050.csv", keep_default_na=False); caps_sha = sha256(REG_DIR / "FOSSIL_PRODUCTION_CAPS_2050.csv")
    gas = caps[caps.carrier == "gas"].copy()
    notes = {"TL": "UNSD EB 2019: production 164,980 TJ fully exported (Bayu-Undan to Darwin); the cap is an upper bound on domestic availability, not a forecast",
             "MY": "includes the Malaysian share of JDA production", "TH": "includes the Thai share of JDA production"}
    prod = [dict(country=r.country, cap_mwh_per_year=float(r.cap_mwh_per_year), basis=r.basis, node_allocation="load_shares (electricity load per AC node within the country; grade C, no field-level basis registered)",
                 fugitive_factor_id=f"fugitive_factor_oilgas_{r.country}", note=notes.get(r.country, "")) for r in gas.itertuples()]
    write_csv(prod, OUT / "GAS_PRODUCTION_CAPS_2050.csv", list(prod[0].keys()))
    # ---- registry ----
    reg = Registry(SCRIPT)
    src = "GEM Global Gas Infrastructure Tracker, Gas Pipelines 2025-11 (raw9) -> extraction " + GEM
    reg.add("gas_pipeline_capacity_mw_per_bcm_year", "Pipeline capacity conversion: 1 bcm/y = 1,199 MW (PyPSA-Eur build_gas_input_locations.py line 127, GCV-type) x 0.90 GCV->NCV (registry fuel_price_basis) = MW_NCV", MW_PER_BCM_Y_GCV * GCV_TO_NCV, "MW_NCV per bcm/y", "B",
            "PyPSA-Eur v2025.07.0 scripts/build_gas_input_locations.py (read-only fetch 2026-10-15T11:03:15Z)", "line 127 mcm_per_year_to_mw = 1.199; fuel_price_basis", pe_sha, decision_ref="15")
    for r in rows:
        pid = "gas_pipeline_existing_" + r["pipeline"].split(" Gas Pipeline")[0].replace(" ", "_").replace("-", "_").replace("–", "_").replace("(", "").replace(")", "").lower()
        reg.add(pid, f"{r['pipeline']} {r['from_node']} -> {r['to_node']} ({r['direction']}), GEM {r['gem_status']} {r['start_year']}, {r['capacity_bcm_per_year'] or 'capacity not given'} bcm/y, {r['length_km']} km; node basis: {r['node_basis']}",
                r["capacity_mw_ncv"] if r["capacity_mw_ncv"] != "" else None, "MW_NCV", "B", src, r["source_locator"], f"csv:{gem_sha}|xlsx:{GEM_XLSX_SHA}", country=f"{r['country_from']}-{r['country_to']}", decision_ref="15",
                status="REGISTERED" if r["capacity_mw_ncv"] != "" else "DATA_PENDING")
    for e in noted:
        reg.add("gas_pipeline_noted_" + e["pipeline"].split(" Gas Pipeline")[0].replace(" ", "_").replace("-", "_").lower(), f"{e['pipeline']}: {e['reason']}", e["gem_status"], "note", "B", src, e["pipeline"], gem_sha, decision_ref="15", status="REFERENCE_ONLY")
    reg.add("gas_pipeline_cost_onshore", "New gas pipeline capacity, onshore: technology-data v0.15.0 CH4 (g) pipeline (investment 91.37 EUR/MW/km, FOM 1.5 %, lifetime 50 a; annuity in costs_active_research.csv)", 91.3721488886, "EUR2020/MW/km", "B",
            "technology-data v0.15.0 costs_2050 (EUR2020 layer, S2-0)", "CH4 (g) pipeline rows 88-91 of costs_2050_EUR2020.csv", sha256(ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv"), decision_ref="35")
    reg.add("gas_pipeline_cost_submarine", "New gas pipeline capacity, submarine: technology-data v0.15.0 CH4 (g) submarine pipeline (investment 125.49 EUR/MW/km, FOM 3 %, lifetime 30 a)", 125.492009886, "EUR2020/MW/km", "B",
            "technology-data v0.15.0 costs_2050 (EUR2020 layer, S2-0)", "CH4 (g) submarine pipeline rows 92-95", sha256(ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv"), decision_ref="35")
    main_gas = FUEL_PRICE_IDS[MAIN_FUEL_SCENARIO].format(c="gas"); reg_df = pd.read_csv(REG_DIR / "fragments" / "fuel_prices.csv", dtype=str, keep_default_na=False).set_index("param_id")
    main_gas_price = float(reg_df.loc[main_gas, "value"])
    reg.add("gas_production_price_rule", f"Domestic gas production is priced at the import price (decision 43): WEO 2025 2050 Japan LNG of research.fuels.price_scenario; S4C-0 (decision 85) main = STEPS ({main_gas}); "
            "NZE (fuel_price_gas_NZE_2050_main, 13.67, S3-S4B main) is the low-price sensitivity", main_gas_price, "EUR2020/MWh_NCV", "B", "S3 instruction S3-1.3; D1 registry; S4C instruction S4C-0 item 1", main_gas, caps_sha, decision_ref="43, 85")
    reg.add("gas_production_node_allocation", "Domestic gas production caps are allocated to the AC nodes of each country by electricity load share at build time (no field-level siting basis registered; GEM start locations lack coordinates in the batch-9 table)", "load_shares", "method", "C",
            "S3 instruction S3-1.3", "s3_layers.add_gas_network", caps_sha, decision_ref="43", sensitivity_low=None, sensitivity_high=None, status="REFERENCE_ONLY")
    for r in prod:
        reg.add(f"gas_production_cap_2050_{r['country']}", f"{r['country']} annual gas production cap = UNSD 2019 gross production ({r['basis']}); {r['note'] or 'no note'}; fugitive factor {r['fugitive_factor_id']}", r["cap_mwh_per_year"], "MWh_NCV/a", "B",
                "D1 FOSSIL_PRODUCTION_CAPS_2050.csv (UNSD 2019)", "carrier gas", caps_sha, country=r["country"], decision_ref="43", status="REGISTERED" if r["cap_mwh_per_year"] > 0 else "SOURCE_ZERO")
    reg.add("lng_import_price_rule", f"LNG imports priced at the WEO 2025 2050 Japan LNG customs-border price of research.fuels.price_scenario; S4C-0 (decision 85) main = STEPS ({main_gas}), NZE = low-price sensitivity; "
            "regasification adder fuel_price_lng_regasification_adder stays DATA_PENDING (adder = 0 in the build; LNG cost understated -> favours LNG over domestic production, pipelines and non-gas options)",
            main_gas_price, "EUR2020/MWh_NCV", "B", "S3 instruction S3-1.4; D1 registry; S4C instruction S4C-0 item 1", main_gas, caps_sha, decision_ref="17,19,85")
    reg.add("lng_terminal_expansion_cap_factor", "LNG regasification capacity per terminal node may expand to 2.5 x the existing (operating + under construction) capacity; proposed sites are candidates with p_nom_max = proposed capacity, zero existing. "
            "S3B R3 (decision 68): sensitivity only (research.s3.gas.lng_expansion = cap_factor); main = existing_only (lng_terminal_expansion_mode); the factor still sets the liquid-H2 terminal cap (S3-2)", 2.5, "ratio", "B",
            "D1 instruction / S3 instruction S3-1.4", "LNG_IMPORT_CAPS_BY_COUNTRY.csv cap_factor", sha256(ROOT / "research_inputs/lng_terminals_v5/LNG_IMPORT_CAPS_BY_COUNTRY.csv"), decision_ref="17,19,68", status="SENSITIVITY")
    reg.add("lng_terminal_expansion_capex", "No capital cost is charged for LNG regasification expansion within the 2.5 x cap (PyPSA-Eur keeps gas entry capacities fixed; no sourced terminal capex) - stated simplification, cost direction: LNG expansion too cheap. "
            "S3B R3: applies only to the cap_factor sensitivity; candidate unit costs registered as lng_regas_capex_ref_* (REFERENCE_ONLY)", 0.0, "EUR/MW", "C",
            "stated assumption (S3-1)", "s3_layers.add_gas_network", caps_sha, decision_ref="17,68", sensitivity_low=0.0, sensitivity_high=None, status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "gas_network.csv")
    write_json(dict(script=SCRIPT, sources=dict(gem_csv=gem_sha, gem_xlsx=GEM_XLSX_SHA, nodes_xy=xy_sha, pypsa_eur_build_gas_input_locations=pe_sha, production_caps=caps_sha),
                    conversion=dict(mw_per_bcm_year_gcv=MW_PER_BCM_Y_GCV, gcv_to_ncv=GCV_TO_NCV), existing=rows, noted=noted, production=prod), OUT / "GAS_NETWORK_EVIDENCE.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 50)
    print(pd.DataFrame(rows)[["pipeline", "capacity_bcm_per_year", "capacity_mw_ncv", "from_node", "to_node", "direction", "status"]].to_string())
    print(pd.DataFrame(prod)[["country", "cap_mwh_per_year", "note"]].to_string())


if __name__ == "__main__":
    main()
