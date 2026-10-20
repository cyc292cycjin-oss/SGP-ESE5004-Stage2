"""S4R R1: demand re-anchoring table (read-only), revised per S4R supplement 01 (decision 129).
(a) base electricity load anchored to AEO8 ATS buildings + agriculture/other electricity (country total from Table C.8 per-capita x
    Table D.1 population; sector split = regional ATS sector proportions x each country's 2019 sector structure, normalised);
(b) physical output 2050 = min(growth rule, per-capita saturation x population, national plan cap if any) with the latest
    uniform base year (crude steel: worldsteel 2024; cement: USGS MCS 2025 2024e where listed, interim values elsewhere);
(c) transport: service-level anchor (ATS transport TFEC by country), electrification per the current method;
(d) industry electricity endogenous (not anchored).
Output: DEMAND_ANCHOR_COMPARISON.csv / .md and evidence/R1_SUMMARY.json."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4r_paths import COUNTRIES, EV, MWH_PER_MTOE, OUT, REPO, S4P, dump_json, load_json, md_table  # noqa: E402

# ---- AEO8 (ACE, 8th ASEAN Energy Outlook 2023-2050, 2024): Table D.1 population 2050 (million), Table C.8 per-capita ATS 2050
POP2050 = {"BN": 0.5, "KH": 20.3, "ID": 317.2, "LA": 9.8, "MY": 41.0, "MM": 59.9, "PH": 157.9, "SG": 5.9, "TH": 67.9, "VN": 107.0}          # Table D.1 p.188
POP2022 = {"BN": 0.4, "KH": 16.8, "ID": 275.8, "LA": 7.5, "MY": 33.9, "MM": 54.2, "PH": 115.6, "SG": 5.6, "TH": 71.7, "VN": 98.2}
TFEC_PC_ATS_2050 = {"BN": 1463.53, "KH": 772.37, "ID": 901.77, "LA": 569.71, "MY": 1659.92, "MM": 223.94, "PH": 346.72, "SG": 2149.37, "TH": 1996.20, "VN": 1435.44}   # ktoe/1000 persons, Table C.8 p.187
TFEC_PC_2022 = {"BN": 2202.13, "KH": 407.40, "ID": 586.45, "LA": 537.17, "MY": 1404.75, "MM": 241.24, "PH": 299.16, "SG": 2242.04, "TH": 1144.02, "VN": 698.56}
ELEC_PC_ATS_2050 = {"BN": 8915, "KH": 1087, "ID": 1757, "LA": 2133, "MY": 6742, "MM": 463, "PH": 1101, "SG": 11324, "TH": 5191, "VN": 4734}   # kWh/person, Table C.8
ELEC_PC_2022 = {"BN": 10921, "KH": 742, "ID": 1055, "LA": 1289, "MY": 4835, "MM": 250, "PH": 790, "SG": 9861, "TH": 2880, "VN": 2446}
GDP_IND_2022 = {"BN": 15597, "KH": 25028, "ID": 1401363, "LA": 22039, "MY": 371617, "MM": 89421, "PH": 298648, "SG": 155971, "TH": 439555, "VN": 436152}   # Table D.3 million USD2017 PPP (industry GDP; negative CAGR printed for MY/PH/SG/TH -> not used as driver)
GDP_IND_2050 = {"BN": 29878, "KH": 171134, "ID": 2050821, "LA": 132225, "MY": 338834, "MM": 1180119, "PH": 265461, "SG": 129987, "TH": 289341, "VN": 2164662}
GDP_PC_2022 = {"BN": 58670, "KH": 4530, "ID": 12397, "LA": 8380, "MY": 28315, "MM": 4683, "PH": 8582, "SG": 110490, "TH": 17507, "VN": 11396}   # Table D.6 USD2017 PPP per person
GDP_PC_2050 = {"BN": 69726, "KH": 9500, "ID": 31836, "LA": 15539, "MY": 66575, "MM": 8630, "PH": 22852, "SG": 206569, "TH": 46899, "VN": 39320}
GDP_TOT_GROWTH = {c: (GDP_PC_2050[c] * POP2050[c]) / (GDP_PC_2022[c] * POP2022[c]) for c in GDP_PC_2022}   # total real GDP growth 2022 -> 2050 (D.6 x D.1); TL: mean of KH/LA/MM
GDP_TOT_GROWTH["TL"] = float(np.mean([GDP_TOT_GROWTH[c] for c in ("KH", "LA", "MM")]))
AEO8_REGION = {"TFEC_BAS_2050_Mtoe": 1107.9, "TFEC_ATS_2050_Mtoe": 746.2, "TFEC_2022_Mtoe": 432.2, "GEN_BAS_2050_TWh": 3036, "GEN_ATS_2050_TWh": 2769,
               "ELEC_SHARE_ATS_2050": 0.232, "ELEC_SHARE_BAS_2050": 0.203, "IND_BAS_2050_Mtoe": 561.0, "IND_ATS_2050_Mtoe": 387.0, "IND_2022_Mtoe": 185.6,
               "ELEC_ATS_2050_Mtoe": 172.7, "ELEC_2022_Mtoe": 93.7, "RES_ELEC_ATS_2050_Mtoe": 33.2, "RES_ELEC_2022_Mtoe": 29.0}   # Table C.2 ATS (p.184); section 3.1.3 p.61 residential electricity
# AEO8 Table C.3 ATS sector TFEC (Mtoe) 2022 -> 2050, p.182: the only sectoral regional table -> sector growth proxies (supplement 01 section 2 (a))
C3_ATS = {"Industry": (185.6, 387.0), "Transport": (145.2, 228.2), "Residential": (63.0, 52.8), "Commercial": (29.5, 50.4), "AgricultureOthers": (8.8, 27.8)}
# sector electricity growth proxies 2022 -> 2050 (ATS): residential = explicit residential electricity (29.0 -> 33.2 Mtoe, section 3.1.3);
# others = sector TFEC growth from Table C.3 (commercial / agriculture are electricity-dominated; industry / transport only enter the normalisation)
G_ELEC = {"Residential": 33.2 / 29.0, "Commercial": 50.4 / 29.5, "AgricultureOthers": 27.8 / 8.8, "Industry": 387.0 / 185.6, "Transport": 228.2 / 145.2}
G_TFEC = {s: v[1] / v[0] for s, v in C3_ATS.items()}
BASE_SECTORS = ["Residential", "Commercial", "AgricultureOthers", "Transport"]   # 'base electricity load' = non-industry fixed electricity (transport electricity here = 2019 rail/other, EV is a separate load)
# TL (outside AEO8): rule = simple average of the KH / LA / MM ATS per-capita values x UN WPP 2024 medium population 2050 (1.889 M; secondary quote, DATA_PENDING for the primary file)
TL_POP2050 = 1.889
TL_RULE = "per-capita = mean(KH, LA, MM) ATS 2050; population UN WPP 2024 medium 1.889 M (worldometer / populationpyramid secondary quote of the UN 2024 revision -> primary file DATA_PENDING)"
TFEC_PC_ATS_2050["TL"] = float(np.mean([TFEC_PC_ATS_2050[c] for c in ("KH", "LA", "MM")])); ELEC_PC_ATS_2050["TL"] = float(np.mean([ELEC_PC_ATS_2050[c] for c in ("KH", "LA", "MM")]))
POP2050["TL"] = TL_POP2050
# ---- ERIA RPR FY2024 No.12 (LCET-CN 2050) country values collected by the S4P sub-agent (EXT_DEMAND_BENCHMARKS)
ERIA = {  # TFEC Mtoe (LCET-CN), final electricity / generation TWh, industry growth multiplier 2019-2050 (derived in the S4P file)
    "VN": dict(tfec_mtoe=120.0, gen_twh=1019.0, elec_twh=None, ind_mult=2.0, note="Ch.16 p.214/216: TFEC 61.3 Mtoe x 2.2 %/a; generation 4.3 x 2019"),
    "ID": dict(tfec_mtoe=362.0, gen_twh=1090.0, elec_twh=884.0, ind_mult=3.0, note="Ch.6 p.78/80: final electricity 75 Mtoe; BAU generation 1,253; ERIA 2023 industry +3.6 %/a"),
    "TH": dict(tfec_mtoe=145.8, gen_twh=544.2, elec_twh=None, ind_mult=1.5, note="Ch.15 p.201-202"),
    "MY": dict(tfec_mtoe=124.0, gen_twh=324.3, elec_twh=None, ind_mult=1.6, note="Ch.10 p.139-140 (BAU generation 412.8)"),
    "PH": dict(tfec_mtoe=64.14, gen_twh=286.7, elec_twh=None, ind_mult=3.8, note="Ch.13 p.179-180 (BAU 451.7); industry growth from PEP +4.9 %/a"),
    "SG": dict(tfec_mtoe=36.86, gen_twh=83.43, elec_twh=124.0, ind_mult=2.4, note="Ch.14 p.189-190: imports 33 % -> implied demand 124 TWh"),
    "KH": dict(tfec_mtoe=16.3, gen_twh=134.0, elec_twh=None, ind_mult=3.5, note="Ch.3 p.28-29 (APS5 65.8, BAU ~78 TWh)"),
    "LA": dict(tfec_mtoe=6.86, gen_twh=160.0, elec_twh=None, ind_mult=4.0, note="Ch.9 p.127-130 (generation export-dominated)"),
    "MM": dict(tfec_mtoe=32.72, gen_twh=196.4, elec_twh=None, ind_mult=1.7, note="Ch.11 p.152-153 (BAU 81.0)"),
    "BN": dict(tfec_mtoe=3.0, gen_twh=22.6, elec_twh=4.9, ind_mult=None, note="Ch.2 p.16-18 (22.6 incl. Hengyi captive; public utility 4.9)"),
    "TL": dict(tfec_mtoe=None, gen_twh=None, elec_twh=None, ind_mult=None, note="not covered (DATA_PENDING)"),
}
# ---- national plans (electricity), from the S4P file
PLAN_ELEC = {"VN": (1237.7, 1375.1, "Decision 768/QD-TTg 2025 commercial electricity 2050"), "PH": (403.5, 408.1, "PEP 2023-2050 electricity sales 2050 CES/REF"),
             "KH": (54.6, 66.2, "PDP 2022-2040 demand 2040 (with/without EE)"), "MY": (300.0, 350.0, "IRENA/NRECC METO 2023 PES/1.5-S 2050"), "ID": (None, 1813.0, "RUKN 2025 demand 2060 (2050 DATA_PENDING)")}

# ---- R1.3 physical output: latest uniform base year (supplement 01 section 1)
BASE_YEAR = 2024
# crude steel 2024 (Mt): worldsteel, World Steel in Figures 2025, "Top steel-producing countries" p.5 (e = estimate); SG / MM not in the top-50 tables
# since the Steel Statistical Yearbook 2020 (2019 values, Table 1 p.5) -> 2019 value held flat to 2024 (DATA_PENDING: worldsteel Steel Data Viewer 2024)
STEEL_BASE = {"VN": (22.0, "worldsteel WSIF 2025 p.5 (2024)", "B"), "ID": (18.0, "worldsteel WSIF 2025 p.5 (2024 e)", "B"), "MY": (8.8, "worldsteel WSIF 2025 p.5 (2024 e)", "B"),
              "TH": (4.9, "worldsteel WSIF 2025 p.5 (2024)", "B"), "PH": (1.9, "worldsteel WSIF 2025 p.5 (2024 e)", "B"),
              "SG": (0.766, "worldsteel SSY 2020 Table 1 (2019) held flat; 2024 DATA_PENDING", "C"), "MM": (0.350, "worldsteel SSY 2020 Table 1 (2019 e) held flat; 2024 DATA_PENDING", "C"),
              "BN": (0.0, "no crude steel production (worldsteel: not listed)", "B"), "KH": (0.0, "no crude steel production", "B"), "LA": (0.0, "no crude steel production", "B"), "TL": (0.0, "no crude steel production", "B")}
# cement 2024 (Mt): USGS MCS 2025 "World Production and Capacity" (2024 e) lists only Indonesia and Viet Nam among the 11; the USGS Minerals Yearbook
# world table (all countries) could not be retrieved (pubs.usgs.gov MYB cement chapters 2019-2022 returned 404 on 2026-10-20) -> DATA_PENDING; interim
# values: national statistics collected in S4P (TH OIE 2023 via CemNet, MY DOSM 2023 via Statista; secondary) or the current model base (EDGAR 2.A.1
# clinker 2019 / 0.52 / 0.656; PH, KH, LA, MM, BN) held flat to 2024. Every interim row is flagged; the rule itself is uniform.
CEMENT_BASE = {"VN": (110.0, "USGS MCS 2025 p.55 (2024 e)", "B"), "ID": (65.0, "USGS MCS 2025 p.55 (2024 e)", "B"),
               "TH": (42.74, "OIE 2023 production excl. clinker via CemNet (secondary) held to 2024; USGS MYB DATA_PENDING", "C"),
               "MY": (23.0, "DOSM 2023 via Statista (secondary; 2022 = 19.86) held to 2024; USGS MYB DATA_PENDING", "C"),
               "PH": (32.94, "model EDGAR-derived 2019 held flat; USGS MYB DATA_PENDING (CeMAP capacity 50 Mt 2024)", "C"),
               "KH": (8.86, "model EDGAR-derived 2019 held flat; USGS MYB DATA_PENDING", "C"), "LA": (6.24, "model EDGAR-derived 2019 held flat; USGS MYB DATA_PENDING", "C"),
               "MM": (6.11, "model EDGAR-derived 2019 held flat; USGS MYB DATA_PENDING", "C"), "BN": (0.35, "model EDGAR-derived 2019 held flat; USGS MYB DATA_PENDING", "C"),
               "SG": (0.0, "no clinker production (grinding / imports only)", "B"), "TL": (0.0, "no cement production", "B")}
ELASTICITY = 0.5            # output-to-GDP elasticity (assumption, grade C; sensitivity 0.3-0.8; literature gives saturation, not a point elasticity - see plan R1.3)
ELASTICITY_RANGE = (0.3, 0.8)
CEM_CAP_T_PER_CAP = 1.0     # cement per-capita saturation t/cap/a (assumption, grade C; sensitivity 0.6-1.2)
STEEL_CAP_T_PER_CAP = 0.6   # crude steel per-capita saturation t/cap/a (assumption, grade C; sensitivity 0.4-0.8)
# national plan caps (only as caps, never as floors - supplement 01 section 1); the VN steel plan value 65-70 Mt is a sensitivity, not an input
PLAN_CAP = {("VN", "cement"): (150.0, "Decision 1266/QD-TTg (2020) Annex I: total designed capacity <= 150 Mt/a (2030), held flat"),
            ("VN", "steel"): (70.0, "Decision 261/QD-TTg (2026): 65-70 Mt crude steel 2050 (upper value as cap)")}


def growth_factor(c: str, years: float, elasticity: float) -> float:
    """GDP growth 2022-2050 (AEO8 D.6 x D.1) pro-rated to `years` at the same CAGR, to the power of the elasticity."""
    g = max(GDP_TOT_GROWTH.get(c, 1.0), 1.0)
    return g ** (years / 28.0 * elasticity)


def main():
    # model side: demand table (TFEC excl. bunkers), loads table from the S4P network extraction, industry summary
    dem = pd.read_csv(REPO / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv")
    dem = dem[dem.sector != "InternationalBunkers"]
    tfec = dem.groupby("country").value_2050_mwh.sum() / MWH_PER_MTOE
    tfec19 = dem.groupby("country").base_2019_mwh.sum() / MWH_PER_MTOE
    elec_tab = dem[dem.carrier == "electricity"].groupby("country").value_2050_mwh.sum() / 1e6
    sector = dem.groupby(["country", "sector"]).value_2050_mwh.sum().unstack(1).fillna(0) / 1e6
    sector19 = dem.groupby(["country", "sector"]).base_2019_mwh.sum().unstack(1).fillna(0) / 1e6
    el19 = dem[dem.carrier == "electricity"].groupby(["country", "sector"]).base_2019_mwh.sum().unstack(1).fillna(0) / 1e6
    el50 = dem[dem.carrier == "electricity"].groupby(["country", "sector"]).value_2050_mwh.sum().unstack(1).fillna(0) / 1e6
    ind = pd.read_csv(REPO / "research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv").set_index("country")
    loads = pd.read_csv(S4P / "evidence/net/NET_integrated_unsolved_loads.csv", index_col=0)
    c = loads["country"] if "country" in loads else loads.country_bus
    c = c.where(c.isin(COUNTRIES), loads.country_bus); loads = loads.assign(c=c)
    L = loads.pivot_table(index="carrier", columns="c", values="energy_mwh", aggfunc="sum").fillna(0) / 1e6
    rows = []
    for k in COUNTRIES:
        g = lambda car: float(L.at[car, k]) if (car in L.index and k in L.columns) else 0.0
        base_el = g("electricity"); ind_el = g("industry electricity"); ev = g("land transport EV"); agri = g("agriculture machinery electric")
        fixed_el = base_el + ind_el + ev + agri
        h2 = g("industry hydrogen"); gas = g("gas final energy") + g("gas feedstock"); oil = g("oil final energy") + g("oil feedstock"); bio = g("biomass final energy"); heat = g("industry heat")
        pop = POP2050.get(k); anchor_tfec = TFEC_PC_ATS_2050[k] / 1000 * pop if pop else np.nan          # Mtoe
        anchor_el = ELEC_PC_ATS_2050[k] / 1000 * pop if pop else np.nan                                     # TWh (final electricity consumption, all sectors)
        tfec_m = float(tfec.get(k, np.nan)); el_tab = float(elec_tab.get(k, np.nan))
        er = ERIA[k]
        cem19 = float(ind.at[k, "cement_2019_t"]) / 1e6 if k in ind.index else np.nan; cem50 = float(ind.at[k, "cement_2050_t"]) / 1e6 if k in ind.index else np.nan
        st19 = float(ind.at[k, "crude_steel_2019_t"]) / 1e6 if k in ind.index else np.nan; st50 = float(ind.at[k, "crude_steel_2050_t"]) / 1e6 if k in ind.index else np.nan
        mult = float(ind.at[k, "industry_multiplier"]) if k in ind.index else np.nan
        gind = (GDP_IND_2050[k] / GDP_IND_2022[k]) if k in GDP_IND_2050 else np.nan
        gtot = GDP_TOT_GROWTH.get(k, np.nan)
        # ---- (a) base electricity load: ATS country electricity x normalised sector weights (2019 sector electricity x ATS sector growth proxy)
        e19 = {s: float(el19.at[k, s]) if (k in el19.index and s in el19.columns) else 0.0 for s in G_ELEC}
        w = {s: e19[s] * G_ELEC[s] for s in G_ELEC}; wsum = sum(w.values())
        share = {s: (w[s] / wsum if wsum > 0 else np.nan) for s in G_ELEC}
        base_share = sum(share[s] for s in BASE_SECTORS) if wsum > 0 else np.nan
        new_base = anchor_el * base_share if (pd.notna(anchor_el) and wsum > 0) else np.nan
        res_new = anchor_el * share["Residential"] if wsum > 0 else np.nan
        com_new = anchor_el * share["Commercial"] if wsum > 0 else np.nan
        agri_new = anchor_el * share["AgricultureOthers"] if wsum > 0 else np.nan
        ind_el_ats_implied = anchor_el * share["Industry"] if wsum > 0 else np.nan   # information only: not an anchor (industry electricity endogenous)
        base19 = sum(e19[s] for s in BASE_SECTORS)
        # cross-check variant A: TFEC-proportion weights for all sectors (supplement wording), same normalisation
        wA = {s: e19[s] * G_TFEC[s] for s in G_TFEC}; wAs = sum(wA.values())
        new_base_A = anchor_el * sum(wA[s] for s in BASE_SECTORS) / wAs if wAs > 0 else np.nan
        # ---- (c) transport service anchor: ATS country TFEC x normalised sector weights (2019 sector TFEC x ATS sector TFEC growth); non-energy use counted with industry
        t19 = {s: float(sector19.at[k, s]) if (k in sector19.index and s in sector19.columns) else 0.0 for s in ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers", "NonEnergyUse"]}
        t19["Industry"] += t19.pop("NonEnergyUse")
        wt = {s: t19[s] * G_TFEC[s] for s in G_TFEC}; wts = sum(wt.values())
        transport_anchor_twh = anchor_tfec * MWH_PER_MTOE / 1e6 * wt["Transport"] / wts if (pd.notna(anchor_tfec) and wts > 0) else np.nan
        transport_model_twh = float(sector.at[k, "Transport"]) if (k in sector.index and "Transport" in sector.columns) else np.nan
        # ---- (b) physical output: latest base year, uniform rule
        st_base, st_src, st_grade = STEEL_BASE[k]; cem_base, cem_src, cem_grade = CEMENT_BASE[k]
        yrs = 2050 - BASE_YEAR
        gf = growth_factor(k, yrs, ELASTICITY); gf_lo = growth_factor(k, yrs, ELASTICITY_RANGE[0]); gf_hi = growth_factor(k, yrs, ELASTICITY_RANGE[1])
        cem_growth = cem_base * gf; cem_pc = pop * CEM_CAP_T_PER_CAP; cem_plan = PLAN_CAP.get((k, "cement"), (np.inf, ""))[0]
        cem_prop = min(cem_growth, cem_pc, cem_plan)
        cem_bind = "growth" if cem_prop == cem_growth else ("per-capita" if cem_prop == cem_pc else "plan")
        st_growth = st_base * gf; st_pc = pop * STEEL_CAP_T_PER_CAP; st_plan = PLAN_CAP.get((k, "steel"), (np.inf, ""))[0]
        st_prop = min(st_growth, st_pc, st_plan)
        st_bind = "growth" if st_prop == st_growth else ("per-capita" if st_prop == st_pc else "plan")
        rows.append(dict(country=k,
                         model_tfec_2019_mtoe=float(tfec19.get(k, np.nan)), model_tfec_2050_mtoe=tfec_m, model_industry_2050_mtoe=float(sector.at[k, "Industry"]) / MWH_PER_MTOE * 1e6 if k in sector.index else np.nan,
                         model_elec_table_2050_twh=el_tab, model_base_elec_load_twh=base_el, model_industry_elec_load_twh=ind_el, model_ev_load_twh=ev, model_agri_elec_twh=agri, model_fixed_elec_total_twh=fixed_el,
                         model_h2_twh=h2, model_gas_final_feedstock_twh=gas, model_oil_final_feedstock_twh=oil, model_fixed_biomass_twh=bio, model_industry_heat_twh=heat,
                         model_industry_multiplier=mult, model_cement_2019_mt=cem19, model_cement_2050_mt=cem50, model_steel_2019_mt=st19, model_steel_2050_mt=st50,
                         aeo8_pop_2050_m=pop, aeo8_ats_tfec_pc_2050_toe=TFEC_PC_ATS_2050[k] / 1000, aeo8_ats_tfec_2050_mtoe=anchor_tfec, aeo8_ats_elec_pc_2050_kwh=ELEC_PC_ATS_2050[k], aeo8_ats_elec_2050_twh=anchor_el,
                         aeo8_gdp_industry_growth_2022_2050=gind, aeo8_gdp_total_growth_2022_2050=gtot,
                         eria_lcet_tfec_2050_mtoe=er["tfec_mtoe"], eria_lcet_generation_2050_twh=er["gen_twh"], eria_final_elec_2050_twh=er["elec_twh"], eria_industry_multiplier=er["ind_mult"], eria_note=er["note"],
                         plan_elec_low_twh=PLAN_ELEC.get(k, (None, None, ""))[0], plan_elec_high_twh=PLAN_ELEC.get(k, (None, None, ""))[1], plan_elec_source=PLAN_ELEC.get(k, (None, None, ""))[2],
                         # (a) base load
                         base_elec_2019_twh=base19, base_elec_old_2050_twh=base_el, base_share_of_ats_elec=base_share, base_elec_new_2050_twh=new_base, base_elec_new_variantA_twh=new_base_A,
                         residential_elec_new_2050_twh=res_new, commercial_elec_new_2050_twh=com_new, agri_other_elec_new_2050_twh=agri_new, industry_elec_ats_implied_twh=ind_el_ats_implied,
                         ratio_base_new_over_old=new_base / base_el if base_el else np.nan, base_elec_new_nonnegative=bool(pd.notna(new_base) and new_base >= 0),
                         # (c) transport
                         transport_tfec_2019_twh=t19["Transport"], transport_model_2050_twh=transport_model_twh, transport_anchor_ats_2050_twh=transport_anchor_twh,
                         ratio_transport_model_over_anchor=transport_model_twh / transport_anchor_twh if transport_anchor_twh else np.nan,
                         # (b) physical output
                         base_year=BASE_YEAR, cement_base_mt=cem_base, cement_base_source=cem_src, cement_base_grade=cem_grade, steel_base_mt=st_base, steel_base_source=st_src, steel_base_grade=st_grade,
                         growth_factor_base_to_2050=gf, growth_factor_elasticity_low=gf_lo, growth_factor_elasticity_high=gf_hi,
                         cement_2050_growth_rule_mt=cem_growth, cement_2050_cap_pc_mt=cem_pc, cement_2050_plan_cap_mt=(cem_plan if np.isfinite(cem_plan) else np.nan), cement_2050_proposed_mt=cem_prop, cement_binding=cem_bind,
                         cement_2050_elasticity_low_mt=min(cem_base * gf_lo, cem_pc, cem_plan), cement_2050_elasticity_high_mt=min(cem_base * gf_hi, cem_pc, cem_plan),
                         steel_2050_growth_rule_mt=st_growth, steel_2050_cap_pc_mt=st_pc, steel_2050_plan_cap_mt=(st_plan if np.isfinite(st_plan) else np.nan), steel_2050_proposed_mt=st_prop, steel_binding=st_bind,
                         steel_2050_elasticity_low_mt=min(st_base * gf_lo, st_pc, st_plan), steel_2050_elasticity_high_mt=min(st_base * gf_hi, st_pc, st_plan)))
    df = pd.DataFrame(rows).set_index("country")
    df["ratio_tfec_model_over_aeo8_ats"] = df.model_tfec_2050_mtoe / df.aeo8_ats_tfec_2050_mtoe
    df["ratio_tfec_model_over_eria"] = df.model_tfec_2050_mtoe / df.eria_lcet_tfec_2050_mtoe
    df["ratio_elec_table_over_aeo8_ats"] = df.model_elec_table_2050_twh / df.aeo8_ats_elec_2050_twh
    df["ratio_fixed_elec_over_aeo8_ats"] = df.model_fixed_elec_total_twh / df.aeo8_ats_elec_2050_twh
    df["ratio_fixed_elec_over_eria_gen"] = df.model_fixed_elec_total_twh / df.eria_lcet_generation_2050_twh
    df["ratio_industry_mult_model_over_eria"] = df.model_industry_multiplier / df.eria_industry_multiplier
    df.to_csv(OUT / "DEMAND_ANCHOR_COMPARISON.csv", float_format="%.4f")
    # region totals and the residential-electricity validation (AEO8 ATS 2050 residential electricity 33.2 Mtoe = 386 TWh, 10 countries)
    ten = df.drop("TL")
    tot = dict(model_tfec_11_mtoe=float(df.model_tfec_2050_mtoe.sum()), model_tfec_10_mtoe=float(ten.model_tfec_2050_mtoe.sum()), model_fixed_elec_11_twh=float(df.model_fixed_elec_total_twh.sum()),
               model_elec_table_11_twh=float(df.model_elec_table_2050_twh.sum()), aeo8_ats_tfec_10_from_pc_mtoe=float(ten.aeo8_ats_tfec_2050_mtoe.sum()), aeo8_ats_elec_10_from_pc_twh=float(ten.aeo8_ats_elec_2050_twh.sum()),
               base_elec_old_11_twh=float(df.base_elec_old_2050_twh.sum()), base_elec_new_11_twh=float(df.base_elec_new_2050_twh.sum()), base_elec_new_variantA_11_twh=float(df.base_elec_new_variantA_twh.sum()),
               residential_elec_new_10_twh=float(ten.residential_elec_new_2050_twh.sum()), aeo8_ats_residential_elec_2050_twh=33.2 * MWH_PER_MTOE / 1e6,
               transport_anchor_11_twh=float(df.transport_anchor_ats_2050_twh.sum()), transport_model_11_twh=float(df.transport_model_2050_twh.sum()),
               cement_2050_proposed_11_mt=float(df.cement_2050_proposed_mt.sum()), steel_2050_proposed_11_mt=float(df.steel_2050_proposed_mt.sum()),
               cement_2050_current_11_mt=float(df.model_cement_2050_mt.sum()), steel_2050_current_11_mt=float(df.model_steel_2050_mt.sum()),
               all_base_loads_nonnegative=bool(df.base_elec_new_nonnegative.all()), **AEO8_REGION)
    md = ["# R1 需求锚定对照（已按补充 01 修订；模型 vs AEO8 ATS 人均 × 人口、ERIA LCET-CN、国家规划；单位 Mtoe / TWh / Mt）", "",
          f"- 区域合计：模型 TFEC（不含燃料舱）11 国 {tot['model_tfec_11_mtoe']:.0f} Mtoe（10 国 {tot['model_tfec_10_mtoe']:.0f}）vs AEO8 2050 BAS 1,107.9 / ATS 746.2（C.8 人均 × D.1 人口加总 {tot['aeo8_ats_tfec_10_from_pc_mtoe']:.0f}）；模型固定电力负荷 {tot['model_fixed_elec_11_twh']:.0f} TWh（需求表电力 {tot['model_elec_table_11_twh']:.0f}）vs AEO8 ATS 电力 {tot['aeo8_ats_elec_10_from_pc_twh']:.0f} TWh（C.2 ATS 172.7 Mtoe = 2,008 TWh；发电 2,769）。",
          f"- TL 规则：{TL_RULE}。",
          f"- 锚定范围（补充 01 §2）：只锚活动量。基础电力负荷锚定 ATS 建筑（居民 + 商业 / 公共）+ 农业及其他的电力；工业电力由物理产量与分温度带有用热内生，不锚定；交通锚定服务量（ATS 交通终端能耗按现行载体效率折算），电气化按现行做法；模型输出的 TFEC / 电力因电气化与内生选择偏离 ATS 属预期，不再作偏差目标。", ""]
    show = df[["model_tfec_2050_mtoe", "aeo8_ats_tfec_2050_mtoe", "eria_lcet_tfec_2050_mtoe", "ratio_tfec_model_over_aeo8_ats", "ratio_tfec_model_over_eria",
               "model_elec_table_2050_twh", "model_fixed_elec_total_twh", "aeo8_ats_elec_2050_twh", "eria_lcet_generation_2050_twh", "ratio_elec_table_over_aeo8_ats", "ratio_fixed_elec_over_aeo8_ats",
               "model_industry_multiplier", "eria_industry_multiplier", "aeo8_gdp_total_growth_2022_2050"]].copy()
    show.columns = ["模型 TFEC", "AEO8 ATS TFEC", "ERIA TFEC", "模型/ATS", "模型/ERIA", "表电力", "固定电负荷", "ATS 电力", "ERIA 发电", "表电/ATS", "固定/ATS", "工业乘数", "ERIA 工业乘数", "AEO8 总GDP 增长"]
    md.append("## 1. 总量对照（现行模型 vs 锚；诊断用，S4R 原表）"); md.append(md_table(show.reset_index())); md.append("")
    show = df[["base_elec_2019_twh", "base_elec_old_2050_twh", "aeo8_ats_elec_2050_twh", "base_share_of_ats_elec", "base_elec_new_2050_twh", "residential_elec_new_2050_twh", "commercial_elec_new_2050_twh", "agri_other_elec_new_2050_twh",
               "base_elec_new_variantA_twh", "ratio_base_new_over_old", "industry_elec_ats_implied_twh", "model_industry_elec_load_twh", "base_elec_new_nonnegative"]].copy()
    show.columns = ["基础电 2019", "基础电 旧 2050", "ATS 电力总量", "基础份额", "基础电 新 2050", "其中居民", "其中商业/公共", "其中农业及其他", "变体 A（TFEC 比例）", "新/旧", "ATS 隐含工业电（仅参考）", "模型工业电（路线）", "非负"]
    md.append(f"## 2. (a) 基础电力负荷锚定（TWh）：新基础负荷 = ATS 国家电力总量（C.8 人均 × D.1 人口）× 归一化部门权重；权重 = 各国 2019 部门电力（UNSD）× ATS 区域部门增长代理（居民电力 33.2/29.0 Mtoe，§3.1.3；商业 50.4/29.5、农业及其他 27.8/8.8、工业 387/185.6、交通 228.2/145.2，表 C.3）。基础 = 居民 + 商业 + 农业及其他 + 交通（2019 铁路等，EV 另算）。11 国同一方法，TL 按规则。校验：10 国居民电力合计 {tot['residential_elec_new_10_twh']:.0f} TWh vs AEO8 ATS 2050 居民电力 33.2 Mtoe = {tot['aeo8_ats_residential_elec_2050_twh']:.0f} TWh；11 国基础负荷旧 {tot['base_elec_old_11_twh']:.0f} → 新 {tot['base_elec_new_11_twh']:.0f} TWh（变体 A {tot['base_elec_new_variantA_11_twh']:.0f}）；全部非负：{tot['all_base_loads_nonnegative']}。")
    md.append(md_table(show.reset_index())); md.append("")
    show = df[["transport_tfec_2019_twh", "transport_model_2050_twh", "transport_anchor_ats_2050_twh", "ratio_transport_model_over_anchor", "model_ev_load_twh"]].copy()
    show.columns = ["交通终端 2019", "交通终端 模型 2050", "交通终端 ATS 锚 2050", "模型/锚", "模型 EV 电力"]
    md.append(f"## 3. (c) 交通服务量锚（TWh 终端能耗口径）：ATS 国家 TFEC × 归一化部门权重（2019 部门 TFEC × 表 C.3 ATS 部门增长；非能源用途并入工业）；服务量 = 锚 ÷ ATS 载体效率，电气化（EV 份额、效率）按现行做法。11 国合计模型 {tot['transport_model_11_twh']:.0f} vs 锚 {tot['transport_anchor_11_twh']:.0f} TWh。")
    md.append(md_table(show.reset_index())); md.append("")
    show2 = df[["cement_base_mt", "cement_base_grade", "cement_2050_growth_rule_mt", "cement_2050_cap_pc_mt", "cement_2050_plan_cap_mt", "cement_2050_proposed_mt", "cement_binding", "model_cement_2050_mt", "cement_2050_elasticity_low_mt", "cement_2050_elasticity_high_mt"]].copy()
    show2.columns = ["水泥 基年 2024", "等级", "增长规则", "人均上限", "规划上限", "建议 2050", "绑定", "现值 2050", "弹性 0.3", "弹性 0.8"]
    md.append(f"## 4. (b) 工业物理产量（Mt）：2050 = min(基年 × 增长^(ε)，人均饱和 × 人口，国家规划上限（仅作上限）)；基年 {BASE_YEAR}（水泥 USGS MCS 2025 2024e：ID、VN；其余 USGS 年鉴 DATA_PENDING，过渡值见来源列；粗钢 worldsteel WSIF 2025 2024，SG / MM 2019 值持平）；增长 = AEO8 总 GDP 增长 2022–2050 按同一 CAGR 折算到 {BASE_YEAR}–2050；ε = {ELASTICITY}（假设，C 级，敏感性 {ELASTICITY_RANGE[0]}–{ELASTICITY_RANGE[1]}）；饱和水泥 {CEM_CAP_T_PER_CAP} / 粗钢 {STEEL_CAP_T_PER_CAP} t/人/年（假设，C 级，敏感性 0.6–1.2 / 0.4–0.8）。11 国合计水泥 {tot['cement_2050_current_11_mt']:.0f} → {tot['cement_2050_proposed_11_mt']:.0f} Mt，粗钢 {tot['steel_2050_current_11_mt']:.0f} → {tot['steel_2050_proposed_11_mt']:.0f} Mt。")
    md.append(md_table(show2.reset_index())); md.append("")
    show3 = df[["steel_base_mt", "steel_base_grade", "steel_2050_growth_rule_mt", "steel_2050_cap_pc_mt", "steel_2050_plan_cap_mt", "steel_2050_proposed_mt", "steel_binding", "model_steel_2050_mt", "steel_2050_elasticity_low_mt", "steel_2050_elasticity_high_mt"]].copy()
    show3.columns = ["粗钢 基年 2024", "等级", "增长规则", "人均上限", "规划上限", "建议 2050", "绑定", "现值 2050", "弹性 0.3", "弹性 0.8"]
    md.append(md_table(show3.reset_index())); md.append("")
    src = df[["cement_base_source", "steel_base_source"]].copy(); src.columns = ["水泥基年来源", "粗钢基年来源"]
    md.append("### 基年来源"); md.append(md_table(src.reset_index())); md.append("")
    show4 = df[["model_base_elec_load_twh", "model_industry_elec_load_twh", "model_ev_load_twh", "model_agri_elec_twh", "model_h2_twh", "model_gas_final_feedstock_twh", "model_oil_final_feedstock_twh", "model_fixed_biomass_twh", "model_industry_heat_twh"]].copy()
    show4.columns = ["基础电", "工业电", "EV", "农业电", "氢", "气(终端+原料)", "油(终端+原料)", "固定生物质", "工业热"]
    md.append("## 5. 现行模型终端载体（构建网络负荷，TWh；诊断用）"); md.append(md_table(show4.reset_index())); md.append("")
    (OUT / "DEMAND_ANCHOR_COMPARISON.md").write_text("\n".join(md), encoding="utf-8")
    dump_json(dict(totals=tot, tl_rule=TL_RULE, base_year=BASE_YEAR, elasticity=ELASTICITY, elasticity_range=ELASTICITY_RANGE, cement_cap_t_per_cap=CEM_CAP_T_PER_CAP, steel_cap_t_per_cap=STEEL_CAP_T_PER_CAP,
                   sector_growth_proxies_elec=G_ELEC, sector_growth_tfec=G_TFEC, table=df.reset_index().to_dict(orient="records")), OUT / "evidence/R1_SUMMARY.json")
    pd.set_option("display.width", 250)
    print(df[["base_elec_old_2050_twh", "aeo8_ats_elec_2050_twh", "base_share_of_ats_elec", "base_elec_new_2050_twh", "base_elec_new_variantA_twh", "residential_elec_new_2050_twh"]].round(2).to_string())
    print(df[["cement_base_mt", "cement_2050_growth_rule_mt", "cement_2050_cap_pc_mt", "cement_2050_proposed_mt", "cement_binding", "steel_base_mt", "steel_2050_growth_rule_mt", "steel_2050_cap_pc_mt", "steel_2050_proposed_mt", "steel_binding"]].round(1).to_string())
    print(df[["transport_model_2050_twh", "transport_anchor_ats_2050_twh", "ratio_transport_model_over_anchor"]].round(1).to_string())
    print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in tot.items()})


if __name__ == "__main__":
    main()
