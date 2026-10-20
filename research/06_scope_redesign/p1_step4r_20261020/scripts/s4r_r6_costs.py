"""S4R R6: COST_CURRENCY_FIXES.csv (monetary inputs, current chain, proposed unification) and COUNTRY_WACC_SENSITIVITY_TABLE.csv
(11 countries, one method: nominal WACC = IEA Cost of Capital Observatory 2024 solar range where published, otherwise reference
country + Damodaran country-risk-premium difference; real = (1 + nominal) / (1 + IMF WEO inflation 2028-2030 average) - 1). Read-only."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4r_paths import COUNTRIES, OUT, dump_json, md_table  # noqa: E402

# IEA Cost of Capital Observatory (2025 dashboard update), solar PV 50-100 MW, FID 2024, nominal post-tax, local currency (low, high); None = not published
IEA_SOLAR_2024 = {"ID": (0.085, 0.110), "VN": (0.085, 0.100), "PH": (0.070, 0.085), "MY": (0.060, 0.070), "TH": (0.060, 0.080)}
# Damodaran, Country Default Spreads and Risk Premiums, updated 5 Jan 2026: country risk premium (equity, %)
CRP = {"ID": 2.46, "VN": 3.90, "PH": 2.46, "TH": 2.07, "MY": 1.55, "SG": 0.00, "KH": 7.12, "LA": 11.66, "MM": 15.54, "BN": 0.78, "TL": None}
# IMF WEO (October 2026) PCPIPCH, average consumer prices, % change (IMF DataMapper API, fetched 2026-10-20)
INFL = {"BN": {2028: 1.0, 2029: 1.0, 2030: 1.0}, "ID": {2028: 2.5, 2029: 2.5, 2030: 2.5}, "KH": {2028: 2.5, 2029: 2.8, 2030: 3.0}, "LA": {2028: 8.2, 2029: 8.3, 2030: 8.5},
        "MM": {2028: 10.0, 2029: 7.8, 2030: 7.8}, "MY": {2028: 2.0, 2029: 2.0, 2030: 2.0}, "PH": {2028: 3.2, 2029: 3.0, 2030: 3.0}, "SG": {2028: 2.0, 2029: 2.0, 2030: 2.0},
        "TH": {2028: 1.5, 2029: 1.7, 2030: 1.8}, "TL": {2028: 2.0, 2029: 2.0, 2030: 2.0}, "VN": {2028: 4.7, 2029: 4.6, 2030: 4.2}}
REF = "MY"   # reference country for the CRP method: IEA published, lowest CRP among the published five
US_INFL_2028_2030 = 2.1   # not used in the real conversion (local-currency nominal rates deflated with local inflation); kept for the USD-basis note


def wacc_table():
    ref_mid = np.mean(IEA_SOLAR_2024[REF]); ref_crp = CRP[REF]
    rows = []
    for c in COUNTRIES:
        infl = np.mean(list(INFL[c].values())) / 100
        if c in IEA_SOLAR_2024:
            lo, hi = IEA_SOLAR_2024[c]; mid = (lo + hi) / 2; method = "IEA Observatory 2024 solar PV range (midpoint)"
        elif CRP.get(c) is not None:
            mid = ref_mid + (CRP[c] - ref_crp) / 100; lo = mid - 0.005; hi = mid + 0.005; method = f"reference {REF} IEA midpoint {ref_mid:.3f} + (CRP_c - CRP_{REF}) Damodaran 2026-01"
        else:
            mid = lo = hi = np.nan; method = "DATA_PENDING (no IEA entry, no Damodaran CRP)"
        real = (1 + mid) / (1 + infl) - 1 if pd.notna(mid) else np.nan
        rows.append(dict(country=c, nominal_wacc_low=lo, nominal_wacc_high=hi, nominal_wacc_mid=mid, method=method, damodaran_crp_pct=CRP.get(c), imf_inflation_2028_2030_avg=infl,
                         real_wacc_mid=real, real_wacc_low=(1 + lo) / (1 + infl) - 1 if pd.notna(lo) else np.nan, real_wacc_high=(1 + hi) / (1 + infl) - 1 if pd.notna(hi) else np.nan,
                         model_uniform_real=0.07, delta_vs_model_pp=(real - 0.07) * 100 if pd.notna(real) else np.nan,
                         annuity_factor_30y_model=0.07 / (1 - (1.07) ** -30), annuity_factor_30y_country=(real / (1 - (1 + real) ** -30)) if pd.notna(real) and real > 0 else np.nan))
    df = pd.DataFrame(rows).set_index("country")
    df["annuity_ratio_country_over_model_30y"] = df.annuity_factor_30y_country / df.annuity_factor_30y_model
    return df


def cost_fixes():
    rows = [
        dict(item="technology-data v0.15.0 投资 / FOM / VOM（374 货币行；含线路、管道、储能、CCS、DAC）", source="PyPSA technology-data v0.15.0 costs_2050.csv", source_currency="EUR2025 (eur_year 2025; 源值多为 2020 年 DEA 数据经 Eurostat HICP 升通胀)",
             model_currency="EUR2020", conversion_now="× 0.83320 = 100 / EA20 GDP 平减 2025（ECB MNA）", issue="升通胀用 HICP (+25.7 %)、去通胀用 GDP 平减 (+20.0 %) → 残余 +4.8 %（LAYER_MANIFEST note）",
             proposed="取 technology-data 源表的 currency_year=2020 源值（技术数据 inputs/ 与 compile_cost_assumptions 的 adjust_for_inflation 之前）或用 Eurostat HICP (prc_hicp_aind) 同一指数回算；实现：s2_0_cost_layer_v015.py rebase() 的 deflator 改为 HICP（登记 deflator_hicp_ea_2025）", impact_bn="B6 −1.8（VN 差额 −2.1）", decision="用户：选 HICP 回算（推荐，与 technology-data 自身口径一致）或改用 2020 源值"),
        dict(item="大型核电（technology-data nuclear）", source="technology-data v0.15.0 ← Lazard v16.0 (2023) USD2023 / 1.09 → EUR, HICP → EUR2025", source_currency="USD2023 → EUR(2023) → EUR2025", model_currency="EUR2020 (9,003 EUR/kW)",
             conversion_now="× 0.83320", issue="美元通胀与欧元通胀混用；与 SMR（AEO8）不同源 → SMR 反而便宜", proposed="见 R6.3：统一核电成本来源", impact_bn="见 R6.3", decision="用户 / 师哥"),
        dict(item="SMR 投资 / FOM / VOM；地热投资", source="ACE AEO8 (2024) Appendix D Table D.15 (p.197)", source_currency="kUSD/MW，价格年未注明（D.3 正文无年份，GDP 表用 2017 PPP）", model_currency="EUR2020 (8,421 EUR/kW)",
             conversion_now="× 0.877229 (ECB 2020 年均) 无平减", issue="价格年 DATA_PENDING；若为 USD2022–23 应再 × 0.86–0.90", proposed="登记 DATA_PENDING，敏感性区间 × [0.86, 1.00]；或按 R6.3 改为同源核电", impact_bn="VN 不互联 −1.9（SMR −11 %）", decision="用户"),
        dict(item="化石燃料价（LNG 27.07、原油 35.32、煤 8.86 EUR/MWh）", source="IEA WEO 2025 Table 2.3 (p.109)", source_currency="USD2024 MER (GCV)", model_currency="EUR2020/MWh NCV",
             conversion_now="× 0.83908 (FRED A191RD3A086NBEA 2020/2024) × 0.877229 = 0.73606；GCV→NCV 另算", issue="一致；备选路径（2024 汇率 0.9244 后欧元平减）约 0.79 (+7 %) 未用", proposed="保持；把备选路径登记为敏感性 fuel_price_conversion_path=eur_deflate", impact_bn="±0.5", decision="无"),
        dict(item="进口氢 / 氨 / 甲醇 / FT 价", source="Neumann, Hampp, Brown 2025 (Zenodo 14872184)", source_currency="EUR2020 (WACC 7 %)", model_currency="EUR2020 × 1.2", conversion_now="无", issue="一致", proposed="保持", impact_bn="0", decision="无"),
        dict(item="生物质原料价", source="NEDO / ERIA-IEEJ 2024 价格", source_currency="USD2024, IDR2024", model_currency="EUR2020", conversion_now="× 0.73606（IDR 经 15,565 IDR/USD）", issue="一致（C 级）", proposed="保持", impact_bn="0", decision="无"),
        dict(item="CO₂ 封存 30 EUR/t", source="PyPSA-Eur v2025.07.0 config.default.yaml sector.co2_sequestration_cost", source_currency="EUR，年份未注明", model_currency="EUR2020", conversion_now="无",
             issue="价格年 DATA_PENDING；PyPSA-Eur 文档将其描述为 'rough estimate'；基准：GCCSI 2025 离岸 US$5–31/t，ERIA 2022 US$12.9/t", proposed="登记 DATA_PENDING（按 EUR2020 使用）；敏感性 ±50 %（已有）", impact_bn="< 0.5", decision="无"),
        dict(item="区域外封存 54.70；船运链 11.42 + 0.00295/km；老挝过境铁路", source="IEAGHG 2004 PH4/30 US$2004；ZEP 2011 EUR2009；Stolaroff 2021 USD2018", source_currency="US$2004 / EUR2009 / USD2018", model_currency="EUR2020",
             conversion_now="× 1.16898 / × 1.14668 / × 0.90369（美国 / EA20 GDP 平减 + ECB 2020 汇率）", issue="一致（A 级换算行）", proposed="保持", impact_bn="0", decision="无"),
        dict(item="LNG 码头扩建 7,018 EUR/MW/a；H₂ 码头 × 1.2", source="PyPSA-Eur import 分支 5a87cedd prepare_sector_network.py line 4561 代码常数", source_currency="未注明（无来源、无价格年）", model_currency="EUR2020",
             conversion_now="无", issue="DATA_PENDING（R3.2 检索：technology-data 无码头行；PyPSA-Eur 代码无注释；DEA 运输目录未找到 LNG 码头行）", proposed="登记 DATA_PENDING；主算改用有出处的 Ulvestad & Overland 2012 换算值 8,020 EUR2020/MW/a（已登记 lng_regas_capex_ref_ulvestad_overland_2012，2011 年价假定）并以 ±50 % 作敏感性；H₂ 码头 = LNG × 1.2 沿用 PyPSA-Eur 的相对关系", impact_bn="< 0.3", decision="用户"),
        dict(item="存量机组固定运维 10.81 bn/a", source="作者冻结基线 costs_2030_elec.csv (pypsa-asean, EUR; SourceCurrencyYears 2020, 褐煤 2023, 抽蓄 2010/2015)", source_currency="EUR 混合年份", model_currency="EUR (视作 2020)", conversion_now="未重新平减",
             issue="两情景相同，不影响 B6；口径不一", proposed="M08 重建时按 EXISTING_PERFORMANCE_OM_SOURCE_MAP.csv 的年份用 EA20 GDP 平减到 2020（褐煤 2023 → × 0.87；抽蓄 2010/15 → × 1.1）", impact_bn="0", decision="无"),
        dict(item="贴现率 0.07", source="technology-data / pypsa-asean fill value（决定 90）", source_currency="实际利率（INFERENCE）", model_currency="实际，用于不变 EUR2020 成本", conversion_now="无", issue="口径一致；国别化需先去通胀", proposed="F7：COUNTRY_WACC_SENSITIVITY_TABLE.csv（本表）", impact_bn="见 R10", decision="师哥：是否做分国 WACC 敏感性"),
        dict(item="报告货币（第 125 项 (4)）", source="—", source_currency="—", model_currency="EUR2020", conversion_now="—", issue="报告用美元", proposed="推荐 USD2020：1 EUR2020 = 1.1422 USD2020（ECB 2020 年均参考汇率，注册表 fx_usd_to_eur_2020 的倒数）；如报 USD2024 再 × 1.1918（FRED A191RD3A086NBEA 125.587/105.377）；全文只用这一个汇率", impact_bn="—", decision="用户：USD2020（推荐）或 USD2024"),
    ]
    return pd.DataFrame(rows)


def main():
    w = wacc_table(); w.to_csv(OUT / "COUNTRY_WACC_SENSITIVITY_TABLE.csv", float_format="%.4f")
    f = cost_fixes(); f.to_csv(OUT / "COST_CURRENCY_FIXES.csv", index=False)
    md = ["# R6 分国实际 WACC 表（只做表，不跑敏感性）", "",
          "方法（11 国同一）：名义 WACC = IEA 资本成本观测站（2025 更新）2024 年 FID 光伏 50–100 MW 区间中点（ID / VN / PH / MY / TH）；其余国家 = 参照国 MY 中点 + (Damodaran 2026-01 国家风险溢价差)；实际 = (1 + 名义) / (1 + IMF WEO 2026-10 CPI 通胀 2028–2030 均值) − 1；TL 无 Damodaran 行 → DATA_PENDING。", "",
          md_table(w.reset_index()[["country", "nominal_wacc_low", "nominal_wacc_high", "nominal_wacc_mid", "damodaran_crp_pct", "imf_inflation_2028_2030_avg", "real_wacc_mid", "delta_vs_model_pp", "annuity_ratio_country_over_model_30y", "method"]], "{:,.3f}"), ""]
    (OUT / "COUNTRY_WACC_SENSITIVITY_TABLE.md").write_text("\n".join(md), encoding="utf-8")
    (OUT / "COST_CURRENCY_FIXES.md").write_text("# R6 货币与价格年份修正清单\n\n" + md_table(f, "{}") + "\n", encoding="utf-8")
    print(w[["nominal_wacc_mid", "imf_inflation_2028_2030_avg", "real_wacc_mid", "delta_vs_model_pp", "annuity_ratio_country_over_model_30y"]].round(4).to_string())


if __name__ == "__main__":
    main()
