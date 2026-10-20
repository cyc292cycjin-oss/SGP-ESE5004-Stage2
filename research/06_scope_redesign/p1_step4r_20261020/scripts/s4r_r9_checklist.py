"""S4R R9: UNIFICATION_CHECKLIST.csv / .md - input class x 11 countries with source, method, currency / price year, data grade,
same-basis flag, exceptions, value before (current) and after (proposed). Values come from the S4R comparison tables and S4P outputs."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4r_paths import COUNTRIES, OUT, S4P, load_json, md_table  # noqa: E402


def main():
    dem = pd.read_csv(OUT / "DEMAND_ANCHOR_COMPARISON.csv").set_index("country")
    pot = pd.read_csv(OUT / "POTENTIAL_COMPARISON.csv").set_index("country")
    lng = pd.read_csv(OUT / "LNG_CAPACITY_COMPARISON.csv").set_index("country")
    co2 = pd.read_csv(OUT / "CO2_STORAGE_UNIFIED.csv").set_index("country")
    wacc = pd.read_csv(OUT / "COUNTRY_WACC_SENSITIVITY_TABLE.csv").set_index("country")
    S = load_json(S4P / "ASPECTS_SUMMARY.json"); caps = S["aspect3_candidate_caps_gw"]
    bio = pd.read_csv(S4P / "ASPECT6_BIOMASS.csv").set_index("country")
    rows = []

    def add(cls, c, source, method, currency, grade, same, exception, before, after, unit):
        rows.append(dict(input_class=cls, country=c, source=source, method=method, currency_price_year=currency, data_grade=grade, same_basis_as_other_countries=same, exception_and_reason=exception, value_before=before, value_after_proposed=after, unit=unit))

    for c in COUNTRIES:
        d = dem.loc[c]
        # demand by sector (TFEC, electricity, industry)
        add("需求：终端能耗总量", c, "现：UNSD 2019 × 桥接 × AEO8 BAS 增长 × ATS 相对因子（D1 / S3B R1 / R3）；拟：AEO8 ATS 人均（C.8）× 人口（D.1）", "ratio 法 → 人均锚定", "能量（无货币）", "B", "是（TL 例外）",
            "TL：AEO8 不覆盖 → KH/LA/MM 均值 × UN WPP 人口（规则登记）" if c == "TL" else "", round(float(d.model_tfec_2050_mtoe), 1), round(float(d.aeo8_ats_tfec_2050_mtoe), 1), "Mtoe")
        add("需求：基础电力负荷", c, "现：Astar 形状 × 需求表非工业电力（第 104 项）；拟：AEO8 ATS 人均电力 × 人口（含工业电力，扣除路线电力后为基础）", "table_sectors → ATS 锚", "—", "B", "是", "TL 同上" if c == "TL" else "", round(float(d.model_base_elec_load_twh), 1), "由 ATS 电力总量 − 工业路线电力反推（M08 计算）", "TWh")
        add("需求：工业能耗与路线", c, "现：UNSD 2019 工业 × 乘数，pypsa_eur_2050 路线（JRC-IDEES 比率）；拟：物理产量按 R1.3 规则，其余能耗按 ATS 增长，载体由有用热分温度带内生选择（R1.4 / R4）", "路线固定 → 有用热内生", "—", "C", "是", "", round(float(d.model_industry_elec_load_twh), 1), "待 M08 重算（工业电力预计降至 ATS 工业电力份额水平）", "TWh（工业电力）")
        add("需求：水泥产量 2050", c, "现：EDGAR 2.A.1 熟料 / 0.52 / 0.656 × 乘数；拟：USGS 2019 × √总GDP增长，人均 1.0 t 上限，国家规划上限", "R1.3 规则", "—", "C", "是（VN 加国家上限）", "VN：Decision 1266 ≤ 150 Mt" if c == "VN" else "", round(float(d.model_cement_2050_mt), 1) if pd.notna(d.model_cement_2050_mt) else "", round(float(d.cement_2050_proposed_mt), 1) if pd.notna(d.cement_2050_proposed_mt) else "DATA_PENDING", "Mt")
        add("需求：粗钢产量 2050", c, "现：worldsteel 2019 × 乘数；拟：worldsteel 2019 × √总GDP增长，人均 0.6 t 上限，国家规划（VN 70 Mt）", "R1.3 规则", "—", "B/C", "是（VN 加国家规划）", "VN：Decision 261 65–70 Mt" if c == "VN" else "", round(float(d.model_steel_2050_mt), 1) if pd.notna(d.model_steel_2050_mt) else "", round(float(d.steel_2050_proposed_mt), 1) if pd.notna(d.steel_2050_proposed_mt) else "DATA_PENDING", "Mt")
        p = pot.loc[c]
        add("潜力：光伏（地面）", c, "现：PyPSA-Earth 布局（Copernicus 类 20/30/40/50/60/90/100，natura，4.6 MW/km²）；拟：5.1 MW/km²（PyPSA-Eur）+ 加入开阔林 121–126，ESMAP L1 × 5.1 作上限对照", "统一参数重算（M08）", "—", "C", "是", "", round(float(p.model_solar_gw), 1), f"≥ {p.adjusted_solar_density_only_gw:.0f}（仅密度）；上限对照 ESMAP L1×5.1 = {p.esmap_l1_x5_1_gw:.0f}", "GW")
        add("潜力：屋顶光伏", c, "现：作者电力底座 solar rooftop 候选（来源 S4A）；拟：不变，登记口径（PyPSA-Earth 无屋顶潜力，作者自定）", "沿用", "—", "C", "是", "", round(float(p.model_rooftop_gw), 1) if pd.notna(p.model_rooftop_gw) else "", "不变（标 C 级）", "GW")
        add("潜力：陆上风", c, "现：PyPSA-Earth 布局 3 MW/km²，Copernicus 类（含林地），alpha 校准（PH/TH/VN 实测，其余均值）；拟：参数不变（与 PyPSA-Eur 同为 3 MW/km²），对照 Zhong 高/中", "沿用", "—", "C", "是（alpha 分国实测 vs 均值）", "PH / TH / VN 用实测 alpha，其余 C 级均值（口径差，登记）", round(float(p.model_onwind_gw), 1), "不变", "GW")
        add("潜力：海上风", c, "现：PyPSA-Earth 水深 ≤ 50 m、离岸 30 km 分 AC/DC、无航道排除、无漂浮、NREL 5 MW；拟：PyPSA-Eur 规则（60 m、漂浮 60–1,000 m、ship_threshold 400、2020ATB 5.5 MW、0.8855 尾流）+ 海上 alpha 校准（F9）", "统一参数重算（M08）", "—", "C", "是", "ESMAP 无行的 MY/TH/BN/MM/TL/SG：候选保留但预期不被选（CF 低）", round(float(p.model_offwind_total_gw), 1), f"重算；对照 ESMAP {p.esmap_offwind_total_gw:.0f}" if pd.notna(p.esmap_offwind_total_gw) else "重算；ESMAP 无行（< 7 m/s）", "GW")
        add("潜力：水电 / 地热", c, "S4B-2 国家潜力 − 存量（官方潜力 / GEM 管线）", "沿用（第 78 项）", "—", "B/C", "否（来源逐国不同：EBTKE、AEO8、ADB、MyRER、DOE、PDP8）", "逐国官方来源，无统一方法；登记为例外", f"hydro {caps.get('ror',{}).get(c,'')} / geo {caps.get('geothermal',{}).get(c,'')}", "不变", "GW")
        b = bio.loc[c]
        add("潜力：生物质", c, "FAOSTAT 2019–23 × IRENA RPR 收集系数（D1）；对照 IRENA 2022", "沿用；溢出规则改 R4", "原料价 USD2024 → EUR2020 × 0.73606", "B/C", "是", "", round(float(b.e_nom_twh), 1), "不变（溢出改有用热）", "TWh")
        k = co2.loc[c]
        add("CO₂ 封存潜力", c, "现：ERIA 2024（ID/MY/BN/TH）、IEA 2021（VN/PH）、OGCI（KH/TL）、零（LA/MM/SG）；拟：ERIA 2024 P50 六国 + KH 文献低值 + TL/LA/MM 零（UNASSESSED）", "统一 ERIA P50", "—", "A/B/C", "是（拟）", k.rule if isinstance(k.rule, str) else "", round(float(k.current_potential_gt), 3), round(float(k.unified_potential_gt), 3), "Gt")
        l = lng.loc[c]
        add("LNG 接收站", c, "现：GEM 2025-08（existing ×2.5 + 拟建）；拟：GEM GGIT 2025-09，取消 2.5× 上限、按有出处成本内生扩建", "统一来源，上限规则改", "码头成本 7,018（无价格年）→ 8,020 EUR2020/MW/a（Ulvestad 2012，2011 年价假定）", "B/C", "是", "", round(float(l.model_p_nom_max_mtpa_equiv), 1), f"内生（项目口径对照 {l.gem2509_project_cap_mtpa:.1f}）", "Mtpa")
        add("区域外进口价（氢 / 氨 / 甲醇 / FT / 原油 / 煤）", c, "Neumann 2025 × 1.2（EUR2020）；WEO 2025 USD2024 × 0.73606", "沿用", "EUR2020", "B", "是", "", "105.75 / 116.78 / 145.16 / 150.11 / 35.32 / 8.86", "不变（再气化加价 +1.26 EUR/MWh）", "EUR/MWh")
        add("技术成本", c, "technology-data v0.15.0 EUR2025 × 0.8332；SMR / 地热 AEO8 × 0.8772；拟：HICP 回算，核电同源", "统一平减指数", "EUR2020（残余 +4.8 % 待消除）", "B/C", "是（11 国同表）", "", "见 COST_CURRENCY_FIXES", "见 R6", "EUR")
        w = wacc.loc[c]
        add("WACC / 贴现率", c, "现：统一 0.07 实际；拟（敏感性）：IEA 观测站 / Damodaran + IMF 通胀", "主算统一；敏感性分国", "实际利率", "B/C", "是（主算）", "TL 无 Damodaran 行 → DATA_PENDING" if c == "TL" else "", 0.07, round(float(w.real_wacc_mid), 4) if pd.notna(w.real_wacc_mid) else "DATA_PENDING", "per unit")
        add("跨境候选通道", c, "CORRIDORS_S4H2（APG + 邻接补齐 + S4H-2）；每条 +20 GW（第 96 项，F3 已定）", "沿用", "线路成本 technology-data（EUR2025 → 2020）", "B", "是", "", "见 S4P 方面 2", "不变", "—")
        add("核电 / SMR", c, "允许：大型核电 10 国（SG 除外）、SMR 11 国，无上限（F8 已定）；成本改同源（R6.3）", "沿用允许条件；成本统一", "EUR2020（同源比值）", "C", "否（SG 无大型核电）", "SG：大型核电不允许（决定 38，面积 / 政策）", "SMR 8,421 / PWR 9,003 EUR/kW", "PWR 9,003 / SMR 9,603 EUR/kW（td × AEO8 比值）", "EUR/kW")
        add("存量机组", c, "GEM GIPT 2026-09 + 冻结底座（S4A / S4B-1）；FOM 作者表（混合年份）", "沿用；FOM 平减到 2020", "EUR（2020 / 2023 / 2010-15 混合）→ EUR2020", "B", "是", "", "10.81 bn/a 合计", "按年份平减（两情景相同）", "EUR/a")
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "UNIFICATION_CHECKLIST.csv", index=False)
    flagged = df[df.same_basis_as_other_countries.str.startswith("否") | (df.exception_and_reason != "")]
    md = ["# R9 统一性核查表（每类输入 × 11 国；口径不同或有例外的格子见末表）", "", f"- 共 {len(df)} 格；标出的口径差 / 例外 {len(flagged)} 格。", ""]
    for cls in df.input_class.unique():
        sub = df[df.input_class == cls][["country", "source", "currency_price_year", "data_grade", "same_basis_as_other_countries", "exception_and_reason", "value_before", "value_after_proposed", "unit"]]
        md.append(f"## {cls}"); md.append(md_table(sub, "{}")); md.append("")
    md.append("## 口径不同 / 有例外的格子"); md.append(md_table(flagged[["input_class", "country", "same_basis_as_other_countries", "exception_and_reason"]], "{}"))
    (OUT / "UNIFICATION_CHECKLIST.md").write_text("\n".join(md), encoding="utf-8")
    print("rows", len(df), "flagged", len(flagged))


if __name__ == "__main__":
    main()
