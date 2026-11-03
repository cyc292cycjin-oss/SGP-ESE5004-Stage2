"""V3 registry fragment (decisions 160-165, review decisions 2026-11-02): every parameter of the V3 revision, fragments/v3.csv.

    python scripts_project/v3_data.py    (after v3_industry.py, v3_facility_shares.py, v3_ev.py, v3_liquids_data.py; then d1_registry.py)
"""
from __future__ import annotations

import json

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, fmt, sha256

SCRIPT = "scripts_project/v3_data.py"
IND = ROOT / "research_inputs/industry_v3"; TR = ROOT / "research_inputs/transport_v3"; LIQ = ROOT / "research_inputs/liquids_v3"
TD = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv"
PE_CONFIG = "research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml"
DISCOUNT = 0.07                        # s2_costs.DISCOUNT / technology-data discount rate
SPEED_KM_H = 15.0 * 1.852              # 15 knots, review D161-2 fallback
HOURS_A = 8000.0                       # review D161-2 fallback
LOSS_PER_KM = 2 * 0.01 / 5000.0        # IRENA 2022 p.44: ballast about 1 % of the cargo per 5,000 km; laden leg the same order -> 2 % per 5,000 km one-way distance
MWH_PER_T = dict(methanol=5.528, oil=11.9, ammonia=5.166)
IEAGHG_T_KM = 0.00295150322083         # registry co2_ship_chain_per_km_cost, EUR2020/(t km)
IEAGHG_FIXED_T = (13.0 + 11.4 + 2.9) / 6.205 * 1.16898366927   # registry co2_ship_chain_fixed_cost without liquefaction and buffer tanks: ships at zero distance + harbour + loading, M US$2004/a over 6.205 Mt/a x conv_usd2004_to_eur2020
ANNUAL_KM_PER_VEHICLE = 12000.0        # review D165-4 fleet proxy, grade C, x 0.5 / x 2 switch; no source inside the repository
REVIEW_SHA = "5bc090fe0bcc9808dd973b10ab47209b135b0134ffae9dd10cc355a7ea99de9b"   # V3_REVIEW_DECISIONS_PHASE1.md: rule and assumption rows cite it
TECH = dict(methanol="MeOH transport ship", oil="FT fuel transport ship", ammonia="NH3 (l) transport ship")


def annuity(r: float, n: float) -> float:
    return r / (1.0 - (1.0 + r) ** (-n))


def main():
    reg = Registry(SCRIPT); td = pd.read_csv(TD); tds = sha256(TD); dec = "161"
    val = lambda t, p: float(td[(td.technology == t) & (td.parameter == p)].value.iloc[0])
    reg.add("liquid_ship_speed_km_h", "Liquid tanker speed 15 knots; review D161-2 fallback: the original sources of the technology-data rows (Runge et al. 2020 SSRN, Cihlar et al. 2020 Publications Office) could not be reached (bot verification / WAF, 2026-11-02)", SPEED_KM_H, "km/h", "C", "assumption", "V3_REVIEW_DECISIONS_PHASE1.md D161-2", "", decision_ref=dec)
    reg.add("liquid_ship_hours_per_year", "Tanker operating hours per year; review D161-2 fallback", HOURS_A, "h/a", "C", "assumption", "V3_REVIEW_DECISIONS_PHASE1.md D161-2", "", decision_ref=dec)
    reg.add("liquid_ship_cargo_loss_per_km", "Cargo share burnt per km of one-way distance: 2 % per 5,000 km (ballast about 1 % per 5,000 km, laden leg the same order)", LOSS_PER_KM, "1/km", "C", "IRENA 2022 Global hydrogen trade Part II p.44", "ballast voyage fuel", "de6af56fe62a1223d431d770e77180ae27e66f19cb674eb96f594f8bdcac45e5", decision_ref=dec)
    for k, h in MWH_PER_T.items():
        reg.add(f"liquid_ship_mwh_per_t_{k}", f"Heating value of the {k} cargo", h, "MWh/t", "C", "PyPSA-Eur config MWh_MeOH per t 5.528, NH3 5.166; oil products 11.9", "s3_0_industry.py header / D161-2", "", decision_ref=dec)
        t = TECH[k]; a = (annuity(DISCOUNT, val(t, "lifetime")) + val(t, "FOM") / 100.0) * val(t, "investment"); cap = val(t, "capacity") * h
        ckm = a / (cap * SPEED_KM_H * HOURS_A / 2.0)
        # decision 187 (V3 HPC package, 2026-11-04): S-A is the main value of the formal 2920x3h runs, S-B the lower-bound sensitivity (the 365x24h screening kept S-B);
        # the S-B rows are grade C (independent review S3-2: derived with the grade-C speed / operating-hours assumptions and a derivation formula)
        reg.add(f"liquid_ship_ckm_td_{k}", f"S-B (lower-bound sensitivity, decision 187; main of the 365x24h screening): {t} capital + FOM per MWh of cargo and km of one-way distance = (annuity 7 % + FOM) x investment / (capacity MWh x speed x hours / 2)", ckm, "EUR2020/(MWh km)", "C", "technology-data v0.15.0 + grade-C speed and operating hours", t, tds, sensitivity_low=0.5 * ckm, sensitivity_high=1.5 * ckm, decision_ref=dec)
        reg.add(f"liquid_ship_ckm_ieaghg_{k}", f"S-A (main, decision 187; full chain cost, cargo loss not counted separately): IEAGHG 2004 per t km cost / heating value of {k}", IEAGHG_T_KM / h, "EUR2020/(MWh km)", "C", "IEAGHG 2004 via registry co2_ship_chain_per_km_cost", "PH4/30 Table 5-3", "", decision_ref=dec)
        reg.add(f"liquid_ship_fixed_ieaghg_{k}", f"S-A (main, decision 187): ships at zero distance + harbour + loading per MWh of {k}", IEAGHG_FIXED_T / h, "EUR2020/MWh", "C", "IEAGHG 2004 via registry co2_ship_chain_fixed_cost without liquefaction and buffer tanks", "PH4/30 Table 5-3", "", decision_ref=dec)
    reg.add("liquid_ship_capacity_rule", "Fixed upper bound of a ship link = ASEAN annual demand of the carrier / 8,760 x 10 (not binding by construction; capacity duals reported, review D161-10)", 10.0, "factor", "C", "review D161-10", "V3_REVIEW_DECISIONS_PHASE1.md", "", decision_ref=dec)
    reg.add("liquid_domestic_distribution_markup", "Domestic distribution mark-up on the national bus <-> node links: 0 (deliberate deviation from decision 161 'uniform mark-up proxy': with exogenous consumption a uniform mark-up only adds a constant and does not change the comparison between countries; D161-4)", 0.0, "EUR2020/MWh", "C", "review D161-4", "V3_REVIEW_DECISIONS_PHASE1.md", "", decision_ref=dec)
    reg.add("liquid_hubs_table", "National liquid hub nodes", "research_inputs/liquids_v3/LIQUID_HUB_NODES_V3.csv", "file", "C", "WPI size rule + two reviewed corrections", "scripts_project/v3_liquids_data.py", sha256(LIQ / "LIQUID_HUB_NODES_V3.csv"), decision_ref=dec, status="REFERENCE_ONLY")
    reg.add("liquid_ship_routes_table", "Port-to-port sea distances between the hub nodes (0.05 degree over-water grid of s4d_2_ship_routes.py)", "research_inputs/liquids_v3/LIQUID_SHIP_ROUTES_V3.csv", "file", "C", "model geometry", "scripts_project/v3_liquids_data.py", sha256(LIQ / "LIQUID_SHIP_ROUTES_V3.csv"), decision_ref=dec, status="REFERENCE_ONLY")
    reg.add("liquid_co2_structure_rule", "Liquid CO2 keeps the node-level structure of decisions 92, 93 (no national liquid CO2 bus): deliberate deviation from the letter of decision 161 - there never was an ASEAN CO2 pool, and the 71 coastal origins with pair-specific sea distances are finer than a national bus (D161-7)", "decision_92_structure", "flag", "C", "review D161-7", "V3_REVIEW_DECISIONS_PHASE1.md", "", decision_ref=dec)
    # ---- decision 160 ------------------------------------------------------------------------------------------------------------------------------
    reg.add("no_new_xb_definition", "Reference scenario: 2025 cross-border stock kept and dispatched (AC s_nom_min > 0, electricity links p_nom_min > 0, existing_2025 gas pipelines), all *_nom_extendable False, every other cross-border line / link removed; shipping as in the integrated scenario; B6 = objective(no_new_xb) - objective(integrated), both with the existing FOM", "no_new_xb", "flag", "B", "decision 160", "V3_DESIGN.md section 1", "", decision_ref="160")
    reg.add("xb_stock_la_th_dedicated_lines", "LA-TH dedicated IPP lines not in the 955 MW grid stock: no single source of operating capacity found (APG existing 955 MW, Zhong et al. 2025 Table S8 6.77 GW incl. under construction); V3_XB_STOCK_CHECK.md; network not changed", None, "MW", "C", "V3_XB_STOCK_CHECK.md", "D160-2", "", country="LA", decision_ref="160", status="DATA_PENDING")
    # ---- decision 162 ------------------------------------------------------------------------------------------------------------------------------
    reg.add("bunker_node_rule", "International bunkers on nodes: country totals unchanged, node shares = Assembly port size / airport size weights (allocation manifest), account 'co2 bunkers ASEAN' net zero on its own, 12th player buys at the node dual", "asean_account_nodal", "flag", "C", "decision 162, D162-1 a, D162-2 a", "research.bunkers.attribution", "", decision_ref="162")
    # ---- decision 163 ------------------------------------------------------------------------------------------------------------------------------
    ev = json.loads((IND / "INDUSTRY_V3_EVIDENCE.json").read_text()); ne = ev["nickel_unit_energy"]
    reg.add("industry_v3_summary_table", "Country x carrier industry table v3 (bound totals equal v2, residual stays in other, D163-6 a)", "research_inputs/industry_v3/INDUSTRY_2050_SUMMARY_V3.csv", "file", "C", "scripts_project/v3_industry.py", "D163-1 to D163-6", sha256(IND / "INDUSTRY_2050_SUMMARY_V3.csv"), decision_ref="163", status="REFERENCE_ONLY")
    reg.add("industry_v3_subsector_table", "Country x sub-sector x carrier table v3", "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv", "file", "C", "scripts_project/v3_industry.py", "D163-1 to D163-6", sha256(IND / "INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"), decision_ref="163", status="REFERENCE_ONLY")
    reg.add("industry_vn_apec_matrix", "VN sub-sector x carrier matrix, APEC Energy Statistics 2022 (data year 2022, base 2019: year mismatch stated), read twice, page 161 of the PDF (book page 148)", "research_inputs/industry_v3/APEC2022_VN_INDUSTRY_PJ.csv", "file", "C", "APEC Energy Statistics 2022", "PDF p.161 image", sha256(IND / "APEC2022_VN_INDUSTRY_PJ.csv"), country="VN", decision_ref="163", status="REFERENCE_ONLY")
    reg.add("nickel_electricity_mwh_per_t_ni", "RKEF final electricity per t contained Ni: Wei et al. 2020 Table 8 Case 3-FeNi (smelting 7,237 + refining 1,081 kWh/t alloy, 35 % Ni)", ne["electricity_mwh_per_t_ni"], "MWh/t_Ni", "B", "Wei et al. 2020 Energies 13(21) 5664", "Table 8", "8695d6c485b6c9e17d3cb575c636250e8925035c9aa82aa80ff9e5e106640d36", decision_ref="163")
    reg.add("nickel_fuel_mwh_per_t_ni", "RKEF final fuel per t contained Ni: drying + kiln natural gas 616 kg, anthracite reductant 569 kg per t alloy (LHV Table 3), mining excluded; in 2050 useful heat x 0.90 on the high band", ne["fuel_mwh_per_t_ni"], "MWh/t_Ni", "B", "Wei et al. 2020 Energies 13(21) 5664", "Tables 3, 8", "8695d6c485b6c9e17d3cb575c636250e8925035c9aa82aa80ff9e5e106640d36", decision_ref="163")
    reg.add("nickel_upper_bound_mwh_per_t_npi", "Upper-bound sensitivity reverse-engineered from APEC 2022 / USGS", 26.0, "MWh/t_NPI", "C", "V3_DESIGN.md 5.4 option b", "D163-2", "", decision_ref="163", status="REFERENCE_ONLY")
    reg.add("nonferrous_production_table", "ID and MY non-ferrous production (2019 main, 2023 sensitivity)", "research_inputs/industry_v3/NONFERROUS_PRODUCTION_V3.csv", "file", "B", "USGS Minerals Yearbook", "NONFERROUS_PRODUCTION_V3.csv", sha256(IND / "NONFERROUS_PRODUCTION_V3.csv"), decision_ref="163", status="REFERENCE_ONLY")
    # ---- decision 164 ------------------------------------------------------------------------------------------------------------------------------
    for f, d in (("INDUSTRY_NODE_SHARES_V3.csv", "Sub-sector node shares"), ("INDUSTRY_CARRIER_NODE_SHARES_V3.csv", "Carrier node shares"), ("PROCESS_NEU_NODE_SHARES_V3.csv", "Process emission and non-energy node shares (D164-5 a)")):
        reg.add("v3_" + f[:-4].lower(), d, "research_inputs/industry_v3/" + f, "file", "C", "GEM, USGS, DOSE V2.11, GADM 4.1", "scripts_project/v3_facility_shares.py", sha256(IND / f), decision_ref="164", status="REFERENCE_ONLY")
    # ---- decision 165 ------------------------------------------------------------------------------------------------------------------------------
    reg.add("ev_weekly_shape_table", "168-hour local-clock week of EV battery consumption and plug-in share, mean of 26 European countries (RAMP-mobility, Euro-Calliope), 2013", "research_inputs/transport_v3/EV_WEEKLY_LOCAL_SHAPE_V3.csv", "file", "C", "RAMP-mobility via Euro-Calliope", "scripts_project/v3_ev.py", sha256(TR / "EV_WEEKLY_LOCAL_SHAPE_V3.csv"), decision_ref="165", status="REFERENCE_ONLY")
    reg.add("ev_node_timezone_table", "UTC offset of every node (decision 165; ID by province)", "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv", "file", "B", "decision 165", "scripts_project/v3_ev.py", sha256(TR / "EV_NODE_TIMEZONE_V3.csv"), decision_ref="165", status="REFERENCE_ONLY")
    reg.add("ev_annual_km_per_vehicle", "Fleet proxy: annual km per vehicle (no source inside the repository; ratio battery / annual electricity of PyPSA-Eur, review D165-4)", ANNUAL_KM_PER_VEHICLE, "km/a", "C", "assumption", "V3_REVIEW_DECISIONS_PHASE1.md D165-4", "", sensitivity_low=0.5 * ANNUAL_KM_PER_VEHICLE, sensitivity_high=2.0 * ANNUAL_KM_PER_VEHICLE, decision_ref="165")
    reg.add("ev_mwh_per_vehicle_year", "Fleet proxy: annual electricity at the battery per vehicle = km / (53.19 x 100 km/MWh, PyPSA-Eur transport_electric_efficiency)", ANNUAL_KM_PER_VEHICLE / 5319.0, "MWh/a", "C", "PyPSA-Eur v2025.07.0 config + assumption", PE_CONFIG + " line 600", "", decision_ref="165")
    # ---- X1b, decisions 172, 173 ---------------------------------------------------------------------------------------------------------------------
    DL = ROOT / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv"; dl = pd.read_csv(DL); dl = dl[dl.counted.astype(bool)]; EPPO = "680ed5756fafcc82692c182cb774c0fa0c0a40a4ab38cb8ad431bfb041f2c25a"
    reg.add("dedicated_plant_lines_la_th_mw", "Lao IPP export lines to Thailand, contract capacity of the 9 EPPO projects, all operating in GEM GIPT 2026-09 and in the existing fleet of the network", float(dl[dl.other_country == "TH"].contract_mw.sum()), "MW", "B", "EPPO Power purchased from Laos PDR, page of 29 March 2016, archived 2026-06-11", "work/p2_data_intake/v3_20261102/01_industry/EPPO_power_purchased_from_Lao_PDR.pdf", EPPO, decision_ref="172,173")
    reg.add("dedicated_plant_lines_la_vn_mw", "Lao IPP export lines to Viet Nam: Xekaman 1 322 MW, Xekaman 3 250 MW (GEM, operating)", float(dl[dl.other_country == "VN"].contract_mw.sum()), "MW", "B", "GEM GIPT 2026-09, decision 100", "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", sha256(ROOT / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv"), decision_ref="172,173")
    reg.add("dedicated_plant_lines_table", "Project table: EPPO capacity, GEM status and start year, plant node, landing node (nearest node of the other country), line length", "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv", "file", "B", "decisions 172, 173", "scripts_project/v3_dedicated_lines.py", sha256(DL), decision_ref="172,173")
    AL = ROOT / "research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv"; al = pd.read_csv(AL)
    reg.add("apg_la_th_grid_lines_mw", "The APG 955 MW of Thailand - Lao PDR: seven 115 kV Energy Exchange lines; no plant-dedicated line inside (X1b overlap check)", float(al.line_capacity_mw.sum()), "MW", "B", "ACE 2024 APG Interconnections Project Profiles no. 9", "p.21-23", sha256(AL), decision_ref="173")
    for r in reg.rows:   # registry validation: numeric grade C rows carry a range; +-50 % like research.liquids.ship_cost_scale
        r["source_sha256"] = r["source_sha256"] or REVIEW_SHA
        try:
            v = float(r["value"])
        except ValueError:
            continue
        if r["tier"] == "C" and r["status"] == "REGISTERED" and r["sensitivity_low"] == "":
            if v == 0.0:
                r["status"] = "REFERENCE_ONLY"
            else:
                r["sensitivity_low"], r["sensitivity_high"] = fmt(0.5 * v), fmt(1.5 * v)
    reg.write(REG_DIR / "fragments" / "v3.csv")
    print(len(reg.rows), "rows")


if __name__ == "__main__":
    main()
