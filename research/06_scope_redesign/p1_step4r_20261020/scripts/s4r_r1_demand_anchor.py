"""S4R R1: demand re-anchoring table (read-only). Three categories per country - (a) base electricity load, (b) activity /
physical output, (c) converted end-use carriers - against external anchors: AEO8 ATS per-capita x population (country), AEO8 BAS
regional, ERIA RPR FY2024 LCET-CN (country, from the S4P web-search file), IEA SEAEO (regional).
Output: DEMAND_ANCHOR_COMPARISON.csv / .md and R1_SUMMARY.json."""
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
               "ELEC_SHARE_ATS_2050": 0.232, "ELEC_SHARE_BAS_2050": 0.203, "IND_BAS_2050_Mtoe": 561.0, "IND_ATS_2050_Mtoe": 387.0, "IND_2022_Mtoe": 185.6}
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


def main():
    # model side: demand table (TFEC excl. bunkers), loads table from the S4P network extraction, industry summary
    dem = pd.read_csv(REPO / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv")
    dem = dem[dem.sector != "InternationalBunkers"]
    tfec = dem.groupby("country").value_2050_mwh.sum() / MWH_PER_MTOE
    tfec19 = dem.groupby("country").base_2019_mwh.sum() / MWH_PER_MTOE
    elec_tab = dem[dem.carrier == "electricity"].groupby("country").value_2050_mwh.sum() / 1e6
    sector = dem.groupby(["country", "sector"]).value_2050_mwh.sum().unstack(1).fillna(0) / 1e6
    ind = pd.read_csv(REPO / "research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv").set_index("country")
    loads = pd.read_csv(S4P / "evidence/net/NET_integrated_unsolved_loads.csv", index_col=0)
    c = loads["country"] if "country" in loads else loads.country_bus
    c = c.where(c.isin(COUNTRIES), loads.country_bus); loads = loads.assign(c=c)
    L = loads.pivot_table(index="carrier", columns="c", values="energy_mwh", aggfunc="sum").fillna(0) / 1e6
    rows = []
    for k in COUNTRIES:
        g = lambda car: float(L.at[car, k]) if (car in L.index and k in L.columns) else 0.0
        base_el = g("electricity"); ind_el = g("industry electricity"); ev = g("land transport EV"); agri = g("agriculture machinery electric"); cook_el = 0.0
        fixed_el = base_el + ind_el + ev + agri
        h2 = g("industry hydrogen"); gas = g("gas final energy") + g("gas feedstock"); oil = g("oil final energy") + g("oil feedstock"); bio = g("biomass final energy"); heat = g("industry heat")
        pop = POP2050.get(k); anchor_tfec = TFEC_PC_ATS_2050[k] / 1000 * pop if pop else np.nan          # Mtoe
        anchor_el = ELEC_PC_ATS_2050[k] / 1000 * pop if pop else np.nan                                     # TWh (final electricity consumption)
        tfec_m = float(tfec.get(k, np.nan)); el_tab = float(elec_tab.get(k, np.nan))
        er = ERIA[k]
        cem19 = float(ind.at[k, "cement_2019_t"]) / 1e6 if k in ind.index else np.nan; cem50 = float(ind.at[k, "cement_2050_t"]) / 1e6 if k in ind.index else np.nan
        st19 = float(ind.at[k, "crude_steel_2019_t"]) / 1e6 if k in ind.index else np.nan; st50 = float(ind.at[k, "crude_steel_2050_t"]) / 1e6 if k in ind.index else np.nan
        mult = float(ind.at[k, "industry_multiplier"]) if k in ind.index else np.nan
        gind = (GDP_IND_2050[k] / GDP_IND_2022[k]) if k in GDP_IND_2050 else np.nan
        gtot = GDP_TOT_GROWTH.get(k, np.nan)
        rows.append(dict(country=k,
                         model_tfec_2019_mtoe=float(tfec19.get(k, np.nan)), model_tfec_2050_mtoe=tfec_m, model_industry_2050_mtoe=float(sector.at[k, "Industry"]) / MWH_PER_MTOE * 1e6 if k in sector.index else np.nan,
                         model_elec_table_2050_twh=el_tab, model_base_elec_load_twh=base_el, model_industry_elec_load_twh=ind_el, model_ev_load_twh=ev, model_agri_elec_twh=agri, model_fixed_elec_total_twh=fixed_el,
                         model_h2_twh=h2, model_gas_final_feedstock_twh=gas, model_oil_final_feedstock_twh=oil, model_fixed_biomass_twh=bio, model_industry_heat_twh=heat,
                         model_industry_multiplier=mult, model_cement_2019_mt=cem19, model_cement_2050_mt=cem50, model_steel_2019_mt=st19, model_steel_2050_mt=st50,
                         aeo8_pop_2050_m=pop, aeo8_ats_tfec_pc_2050_toe=TFEC_PC_ATS_2050[k] / 1000, aeo8_ats_tfec_2050_mtoe=anchor_tfec, aeo8_ats_elec_pc_2050_kwh=ELEC_PC_ATS_2050[k], aeo8_ats_elec_2050_twh=anchor_el,
                         aeo8_gdp_industry_growth_2022_2050=gind, aeo8_gdp_total_growth_2022_2050=gtot,
                         eria_lcet_tfec_2050_mtoe=er["tfec_mtoe"], eria_lcet_generation_2050_twh=er["gen_twh"], eria_final_elec_2050_twh=er["elec_twh"], eria_industry_multiplier=er["ind_mult"], eria_note=er["note"],
                         plan_elec_low_twh=PLAN_ELEC.get(k, (None, None, ""))[0], plan_elec_high_twh=PLAN_ELEC.get(k, (None, None, ""))[1], plan_elec_source=PLAN_ELEC.get(k, (None, None, ""))[2]))
    df = pd.DataFrame(rows).set_index("country")
    df["ratio_tfec_model_over_aeo8_ats"] = df.model_tfec_2050_mtoe / df.aeo8_ats_tfec_2050_mtoe
    df["ratio_tfec_model_over_eria"] = df.model_tfec_2050_mtoe / df.eria_lcet_tfec_2050_mtoe
    df["ratio_elec_table_over_aeo8_ats"] = df.model_elec_table_2050_twh / df.aeo8_ats_elec_2050_twh
    df["ratio_fixed_elec_over_aeo8_ats"] = df.model_fixed_elec_total_twh / df.aeo8_ats_elec_2050_twh
    df["ratio_fixed_elec_over_eria_gen"] = df.model_fixed_elec_total_twh / df.eria_lcet_generation_2050_twh
    df["ratio_industry_mult_model_over_eria"] = df.model_industry_multiplier / df.eria_industry_multiplier
    # ---- physical output re-anchoring (INFERENCE rule): 2050 = base 2019 x min(AEO8 industry-GDP growth, country multiplier) capped by per-capita saturation
    CEM_CAP_T_PER_CAP = 1.0    # cement per-capita saturation (t/cap/a; INFERENCE, see plan R1.3)
    STEEL_CAP_T_PER_CAP = 0.6  # crude steel per-capita saturation (t/cap/a; Decision 261/QD-TTg VN 2050 finished steel 570-650 kg/cap)
    df["cement_2050_growth_rule_mt"] = df.model_cement_2019_mt * df.aeo8_gdp_total_growth_2022_2050.clip(lower=1.0) ** 0.5
    df["cement_2050_cap_pc_mt"] = df.aeo8_pop_2050_m * CEM_CAP_T_PER_CAP
    df["cement_2050_proposed_mt"] = np.minimum(df.cement_2050_growth_rule_mt, df.cement_2050_cap_pc_mt)
    df.loc["VN", "cement_2050_proposed_mt"] = min(df.at["VN", "cement_2050_proposed_mt"], 150.0)   # Decision 1266/QD-TTg capacity cap <= 150 Mt (2030), held flat
    df["steel_2050_growth_rule_mt"] = df.model_steel_2019_mt * df.aeo8_gdp_total_growth_2022_2050.clip(lower=1.0) ** 0.5
    df["steel_2050_cap_pc_mt"] = df.aeo8_pop_2050_m * STEEL_CAP_T_PER_CAP
    df["steel_2050_proposed_mt"] = np.minimum(df.steel_2050_growth_rule_mt, df.steel_2050_cap_pc_mt)
    df.loc["VN", "steel_2050_proposed_mt"] = 70.0   # Decision 261/QD-TTg (2026-02-09): 65-70 Mt crude steel 2050 (upper value)
    df.to_csv(OUT / "DEMAND_ANCHOR_COMPARISON.csv", float_format="%.4f")
    # region totals
    tot = dict(model_tfec_11_mtoe=float(df.model_tfec_2050_mtoe.sum()), model_tfec_10_mtoe=float(df.drop("TL").model_tfec_2050_mtoe.sum()), model_fixed_elec_11_twh=float(df.model_fixed_elec_total_twh.sum()),
               model_elec_table_11_twh=float(df.model_elec_table_2050_twh.sum()), aeo8_ats_tfec_10_from_pc_mtoe=float(df.drop("TL").aeo8_ats_tfec_2050_mtoe.sum()), aeo8_ats_elec_10_from_pc_twh=float(df.drop("TL").aeo8_ats_elec_2050_twh.sum()),
               **AEO8_REGION)
    md = ["# R1 需求锚定对照（模型 vs AEO8 ATS 人均 × 人口、ERIA LCET-CN、国家规划；单位 Mtoe / TWh / Mt）", "",
          f"- 区域合计：模型 TFEC（不含燃料舱）11 国 {tot['model_tfec_11_mtoe']:.0f} Mtoe（10 国 {tot['model_tfec_10_mtoe']:.0f}）vs AEO8 2050 BAS 1,107.9 / ATS 746.2（C.8 人均 × D.1 人口加总 {tot['aeo8_ats_tfec_10_from_pc_mtoe']:.0f}）；模型固定电力负荷 {tot['model_fixed_elec_11_twh']:.0f} TWh（需求表电力 {tot['model_elec_table_11_twh']:.0f}）vs AEO8 ATS 电力 {tot['aeo8_ats_elec_10_from_pc_twh']:.0f} TWh（发电 2,769）、BAS 发电 3,036。",
          f"- TL 规则：{TL_RULE}。", ""]
    show = df[["model_tfec_2050_mtoe", "aeo8_ats_tfec_2050_mtoe", "eria_lcet_tfec_2050_mtoe", "ratio_tfec_model_over_aeo8_ats", "ratio_tfec_model_over_eria",
               "model_elec_table_2050_twh", "model_fixed_elec_total_twh", "aeo8_ats_elec_2050_twh", "eria_lcet_generation_2050_twh", "ratio_elec_table_over_aeo8_ats", "ratio_fixed_elec_over_aeo8_ats",
               "model_industry_multiplier", "eria_industry_multiplier", "aeo8_gdp_total_growth_2022_2050"]].copy()
    show.columns = ["模型 TFEC", "AEO8 ATS TFEC", "ERIA TFEC", "模型/ATS", "模型/ERIA", "表电力", "固定电负荷", "ATS 电力", "ERIA 发电", "表电/ATS", "固定/ATS", "工业乘数", "ERIA 工业乘数", "AEO8 总GDP 增长"]
    md.append("## 总量（a + c 口径：TFEC 与电力）"); md.append(md_table(show.reset_index())); md.append("")
    show2 = df[["model_cement_2019_mt", "model_cement_2050_mt", "cement_2050_growth_rule_mt", "cement_2050_cap_pc_mt", "cement_2050_proposed_mt", "model_steel_2019_mt", "model_steel_2050_mt", "steel_2050_growth_rule_mt", "steel_2050_cap_pc_mt", "steel_2050_proposed_mt"]].copy()
    show2.columns = ["水泥 2019", "水泥 2050 现值", "水泥 增长规则", "水泥 人均上限", "水泥 建议", "钢 2019", "钢 2050 现值", "钢 增长规则", "钢 人均上限", "钢 建议"]
    md.append("## 工业物理产量（b 口径，Mt；建议值 = min(2019 × √总GDP增长(AEO8 D.6 × D.1), 人均饱和 × 人口)，VN 另受 Decision 1266 产能上限 150 Mt / Decision 261 钢 65–70 Mt；INFERENCE。AEO8 D.3 工业 GDP 对 MY / PH / SG / TH 印为负增长，不作驱动）"); md.append(md_table(show2.reset_index())); md.append("")
    show3 = df[["model_base_elec_load_twh", "model_industry_elec_load_twh", "model_ev_load_twh", "model_agri_elec_twh", "model_h2_twh", "model_gas_final_feedstock_twh", "model_oil_final_feedstock_twh", "model_fixed_biomass_twh", "model_industry_heat_twh"]].copy()
    show3.columns = ["基础电", "工业电", "EV", "农业电", "氢", "气(终端+原料)", "油(终端+原料)", "固定生物质", "工业热"]
    md.append("## 模型终端载体（c 口径，TWh，构建网络负荷）"); md.append(md_table(show3.reset_index())); md.append("")
    (OUT / "DEMAND_ANCHOR_COMPARISON.md").write_text("\n".join(md), encoding="utf-8")
    dump_json(dict(totals=tot, tl_rule=TL_RULE, table=df.reset_index().to_dict(orient="records")), OUT / "evidence/R1_SUMMARY.json")
    print(show.round(2).to_string()); print(show2.round(1).to_string()); print(tot)


if __name__ == "__main__":
    main()
