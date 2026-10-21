# BENEFIT（M12 C1 第 4、5 项：受益检查与比例规则对照；只读）

- 一体化：`/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12_20261021/evidence/c43/s4n_integrated`；不互联：`/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12_20261021/evidence/c43/s4o_disconnected`。
- 主值口径（补充 01 D1）：**owen_dual_form**；来源 /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12_20261021/evidence/s01/s4n_pilot_365x24h/OWEN.json；/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12_20261021/evidence/s01/s4o6_disconnected_365x24h/OWEN.json。
- B6 = 不互联目标值 − 一体化目标值 = 69.243 bn EUR2020。
- Owen 受益为负的参与者（α 0.5）：**BUNKER**；α 区间内可能为负：BUNKER。
- 燃料舱参与者：一体化 True，不互联 True。

| 参与者 | Owen 受益 bn | 区间下限 | 区间上限 |
|---|---|---|---|
| BN | 0.114 | 0.114 | 0.114 |
| ID | 0.636 | 0.634 | 0.638 |
| KH | 2.420 | 2.416 | 2.425 |
| LA | 2.482 | 2.471 | 2.492 |
| MM | 1.173 | 1.172 | 1.174 |
| MY | 3.239 | 3.090 | 3.388 |
| PH | 0.010 | 0.010 | 0.010 |
| SG | 0.932 | 0.930 | 0.935 |
| TH | 7.477 | 7.322 | 7.633 |
| TL | 0.123 | 0.123 | 0.123 |
| VN | 51.852 | 51.851 | 51.853 |
| BUNKER | -1.215 | -1.215 | -1.215 |

- 权重（补充 01 D5）：主用 population_aeo8_d1, gdp_aeo8_d2, electricity_fixed, electricity_base；对照 population_ssp2, gdp_ppp_ssp2（表中排在后面）。

## 比例规则 (A)：按比例分摊 B6（主讨论；检验 = 去一国边际贡献，补充 01 D4）

- benefit_i = s_i x B6, payment_i = disconnected allocation_i - benefit_i; test: payment_i >= c'(i) (c'(i) = c(N) - c(N - i), D8 adjusted), i.e. benefit_i <= disconnected allocation_i - c'(i): otherwise the other players pay more than c(N - i). With B6 > 0 the benefit is never negative, so 'negative benefit' is not a test of (A). Only countries with a leave-one-out run.
- 去一国来源：无（(A) 的检验不可计算）；容差：L23 default reference (s4o_c1_precision.L23_REFERENCE)。
- Owen（主值）去一国检查：无去一国运行

| 国 | Owen 受益 | 受益上限 φ不互联 − c′ | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.114 | — | 0.044 | 0.093 | 0.088 | 0.213 | 0.048 | 0.129 |
| ID | 0.636 | — | 27.827 | 26.923 | 26.826 | 20.195 | 27.664 | 26.912 |
| KH | 2.420 | — | 1.781 | 0.513 | 0.686 | 1.166 | 1.817 | 1.038 |
| LA | 2.482 | — | 0.860 | 0.405 | 0.217 | 0.330 | 0.831 | 0.541 |
| MM | 1.173 | — | 5.255 | 1.379 | 1.364 | 0.973 | 5.090 | 1.588 |
| MY | 3.239 | — | 3.597 | 7.283 | 8.762 | 9.369 | 3.657 | 6.355 |
| PH | 0.010 | — | 13.852 | 9.619 | 3.529 | 6.957 | 13.747 | 11.000 |
| SG | 0.932 | — | 0.518 | 3.268 | 1.800 | 2.766 | 0.590 | 2.655 |
| TH | 7.477 | — | 5.957 | 8.487 | 11.169 | 13.989 | 6.054 | 7.158 |
| TL | 0.123 | — | 0.166 | 0.056 | 0.022 | 0.061 | 0.163 | 0.038 |
| VN | 51.852 | — | 9.387 | 11.218 | 14.782 | 13.224 | 9.581 | 11.828 |

（✗ = 规则给该国的好处超过其边际贡献，其余参与者合计支付超过 c(N − i)。）

(A) 去一国检查未通过：population_aeo8_d1：无；gdp_aeo8_d2：无；electricity_fixed：无；electricity_base：无；population_ssp2：无；gdp_ppp_ssp2：无

## 比例规则 (B)：按比例分摊一体化总成本（对照；检验 = 个体理性）

- payment_i = s_i x (c(N) - phi_BUNKER - SHARED) of the integrated run; test (individual rationality): payment_i <= disconnected allocation_i (+ the C1 (b) tolerance)
- 11 国分摊总额 = 438.560 bn。Owen（主值）个体理性：全部通过

| 国 | 不互联分摊 | Owen 支付 | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.879 | 0.765 | 0.278 | 0.587 | 0.556 | 1.348 ✗ | 0.301 | 0.815 |
| ID | 159.247 | 158.611 | 176.249 ✗ | 170.522 ✗ | 169.908 ✗ | 127.910 | 175.216 ✗ | 170.453 ✗ |
| KH | 5.205 | 2.785 | 11.279 ✗ | 3.250 | 4.342 | 7.382 ✗ | 11.507 ✗ | 6.575 ✗ |
| LA | 1.356 | -1.126 | 5.445 ✗ | 2.565 ✗ | 1.371 | 2.091 ✗ | 5.262 ✗ | 3.428 ✗ |
| MM | 3.833 | 2.660 | 33.283 ✗ | 8.733 ✗ | 8.636 ✗ | 6.165 ✗ | 32.237 ✗ | 10.055 ✗ |
| MY | 69.841 | 66.602 | 22.781 | 46.125 | 55.493 | 59.341 | 23.159 | 40.252 |
| PH | 22.472 | 22.463 | 87.735 ✗ | 60.922 ✗ | 22.350 | 44.066 ✗ | 87.071 ✗ | 69.673 ✗ |
| SG | 22.045 | 21.112 | 3.278 | 20.698 | 11.398 | 17.516 | 3.739 | 16.813 |
| TH | 61.905 | 54.428 | 37.728 | 53.753 | 70.741 ✗ | 88.604 ✗ | 38.346 | 45.335 |
| TL | 0.009 | -0.115 | 1.050 ✗ | 0.357 ✗ | 0.137 ✗ | 0.383 ✗ | 1.035 ✗ | 0.243 ✗ |
| VN | 162.227 | 110.375 | 59.453 | 71.048 | 93.627 | 83.755 | 60.685 | 74.917 |

（✗ = 支付超过不互联分摊，违反个体理性。）

(B) 个体理性未通过：population_aeo8_d1：ID, KH, LA, MM, PH, TL；gdp_aeo8_d2：ID, LA, MM, PH, TL；electricity_fixed：ID, MM, TH, TL；electricity_base：BN, KH, LA, MM, PH, TH, TL；population_ssp2：ID, KH, LA, MM, PH, TL；gdp_ppp_ssp2：ID, KH, LA, MM, PH, TL

## 燃料舱参与者（补充 01 D10）

- 受益 = 不互联 76.477 − 一体化 77.692 = **-1.215 bn**（为负，照实报告）。
- 严格单独成本（只用区域外非化石进口）：106.446 bn；一体化份额 ≤ 单独成本：**True**；不互联份额 ≤ 单独成本：True。
- 解释：一体化改变液体燃料池价格，燃料舱作为没有资源、不能退出的纯价格接受者承担这一金钱外部性；不视为违反个体理性，个体理性的检验是 Owen 份额 ≤ 严格单独成本。

- (A) splits B6 among the 11 countries by positive weights: with B6 > 0 no country gets a negative benefit; the bunker account (no population / GDP / electricity) keeps its disconnected allocation (benefit 0) in (A) and its integrated allocation in (B)
- rule_budget_residual_eur = sum of the (A) payments of the first weight + bunker - (integrated objective - integrated pool residual) = change of the pool residual
- 预算残差 761,581 EUR（池盈余变化）。
- 权重来源：{'population_aeo8': 'sources/AEO8_2050_BY_COUNTRY.csv table D.1 2050 (all scenarios); TL UN WPP 2024 median 1,889,249.5 (as m08b_demand.py)', 'gdp_aeo8': 'research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv table D.2 real GDP PPP 2017 (million USD) 2050; TL = mean(KH, LA, MM) GDP per capita x TL population (M08b TL rule)', 'population_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv IIASA-WiC POP 2025 SSP2 2050 (comparison)', 'gdp_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv OECD ENV-Growth 2025 SSP2 GDP|PPP 2050 (billion USD2017; comparison)'}

## 并列：市场结算形式（现行账本）下的受益

- 受益为负：**BUNKER**

| 参与者 | 主值受益 bn | 市场形式受益 bn | 市场 − 主值 bn |
|---|---|---|---|
| BN | 0.114 | 0.114 | 0.000 |
| ID | 0.636 | 0.669 | 0.033 |
| KH | 2.420 | 2.426 | 0.006 |
| LA | 2.482 | 2.738 | 0.257 |
| MM | 1.173 | 1.131 | -0.042 |
| MY | 3.239 | 3.206 | -0.034 |
| PH | 0.010 | 0.010 | 0.000 |
| SG | 0.932 | 0.932 | -0.000 |
| TH | 7.477 | 7.513 | 0.036 |
| TL | 0.123 | 0.123 | 0.000 |
| VN | 51.852 | 51.595 | -0.257 |
| BUNKER | -1.215 | -1.215 | 0.000 |
