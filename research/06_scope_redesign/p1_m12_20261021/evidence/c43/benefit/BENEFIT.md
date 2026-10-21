# BENEFIT（M12 C1 第 4、5 项：受益检查与比例规则对照；只读）

- 一体化：`/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12_20261021/evidence/c43/s4n_integrated`；不互联：`/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12_20261021/evidence/c43/s4o_disconnected`。
- B6 = 不互联目标值 − 一体化目标值 = 69.243 bn EUR2020。
- Owen 受益为负的参与者（α 0.5）：**BUNKER**；α 区间内可能为负：BUNKER。
- 燃料舱参与者：一体化 True，不互联 True。

| 参与者 | Owen 受益 bn | 区间下限 | 区间上限 | 人口 SSP2 | GDP SSP2 | 人口 AEO8 | 基础电力 | 固定电力 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.114 | 0.114 | 0.114 | 0.048 | 0.129 | 0.044 | 0.213 | 0.088 |
| ID | 0.669 | 0.635 | 0.703 | 27.664 | 26.912 | 27.827 | 20.195 | 26.826 |
| KH | 2.426 | 2.362 | 2.491 | 1.817 | 1.038 | 1.781 | 1.166 | 0.686 |
| LA | 2.738 | 2.418 | 3.059 | 0.831 | 0.541 | 0.860 | 0.330 | 0.217 |
| MM | 1.131 | 1.076 | 1.186 | 5.090 | 1.588 | 5.255 | 0.973 | 1.364 |
| MY | 3.206 | 3.025 | 3.386 | 3.657 | 6.355 | 3.597 | 9.369 | 8.762 |
| PH | 0.010 | 0.010 | 0.010 | 13.747 | 11.000 | 13.852 | 6.957 | 3.529 |
| SG | 0.932 | 0.930 | 0.935 | 0.590 | 2.655 | 0.518 | 2.766 | 1.800 |
| TH | 7.513 | 7.183 | 7.843 | 6.054 | 7.158 | 5.957 | 13.989 | 11.169 |
| TL | 0.123 | 0.123 | 0.123 | 0.163 | 0.038 | 0.166 | 0.061 | 0.022 |
| VN | 51.595 | 51.367 | 51.823 | 9.581 | 11.828 | 9.387 | 13.224 | 14.782 |
| BUNKER | -1.215 | -1.215 | -1.215 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

比例规则下受益为负的国家：population_ssp2：无；gdp_ppp_ssp2：无；population_aeo8_d1：无；electricity_base：无；electricity_fixed：无

比例规则与 Owen 受益符号不同的国家：population_ssp2：无；gdp_ppp_ssp2：无；population_aeo8_d1：无；electricity_base：无；electricity_fixed：无

- proportional rules split B6 among the 11 countries by positive weights: with B6 > 0 no country can get a negative benefit under any of them; the bunker account (no population / GDP / electricity) keeps its disconnected allocation (benefit 0), so the countries absorb its Owen benefit
- rule_budget_residual_eur = sum of the rule payments + bunker - (integrated objective - integrated pool surplus) = change of the pool surplus
- 预算残差 374,034 EUR（池盈余变化）。
- 权重来源：{'population_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv IIASA-WiC POP 2025 SSP2 2050', 'gdp': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv OECD ENV-Growth 2025 SSP2 GDP|PPP 2050 (billion USD2017)', 'population_aeo8': 'sources/AEO8_2050_BY_COUNTRY.csv table D.1 2050; TL UN WPP 2024 (registry download_un_wpp2024_tl_population_2050)'}
