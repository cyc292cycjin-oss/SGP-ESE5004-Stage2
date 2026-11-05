# BENEFIT（M12 C1 第 4、5 项：受益检查与比例规则对照；只读）

- 一体化：`/home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31/F1`；不互联：`/home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31/F2`。
- 主值口径（补充 01 D1）：**owen_dual_form**；来源 /home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31/F1/m12_owen/OWEN.json；/home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31/F2/m12_owen/OWEN.json。
- B6 = 不互联目标值 − 一体化目标值 = 12.563 bn EUR2020。
- Owen 受益为负的参与者（α 0.5）：**ID, LA**；α 区间内可能为负：ID, LA。
- 燃料舱参与者：一体化 True，不互联 True。

| 参与者 | Owen 受益 bn | 区间下限 | 区间上限 |
|---|---|---|---|
| BN | 0.184 | 0.184 | 0.184 |
| ID | -0.712 | -0.741 | -0.684 |
| KH | 0.366 | 0.316 | 0.417 |
| LA | -0.108 | -1.589 | 1.373 |
| MM | 0.298 | 0.225 | 0.371 |
| MY | 0.870 | 0.754 | 0.985 |
| PH | 0.130 | 0.130 | 0.130 |
| SG | 2.770 | 2.712 | 2.829 |
| TH | 4.073 | 2.503 | 5.643 |
| TL | 0.026 | 0.026 | 0.026 |
| VN | 1.369 | 1.357 | 1.381 |
| BUNKER | 3.297 | 3.297 | 3.297 |

- 权重（补充 01 D5）：主用 population_aeo8_d1, gdp_aeo8_d2, electricity_fixed, electricity_base；对照 population_ssp2, gdp_ppp_ssp2（表中排在后面）。

## 比例规则 (A)：按比例分摊 B6（主讨论；检验 = 去一国边际贡献，补充 01 D4）

- benefit_i = s_i x B6, payment_i = disconnected allocation_i - benefit_i; test: payment_i >= c'(i) (c'(i) = c(N) - c(N - i), D8 adjusted), i.e. benefit_i <= disconnected allocation_i - c'(i): otherwise the other players pay more than c(N - i). With B6 > 0 the benefit is never negative, so 'negative benefit' is not a test of (A). Only countries with a leave-one-out run.
- 去一国来源：无（(A) 的检验不可计算）；容差：PRECISION.json of /home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31/F1 (this batch: disconnected - integrated ledger difference (/home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31/F2 minus /h)。
- Owen（主值）去一国检查：无去一国运行

| 国 | Owen 受益 | 受益上限 φ不互联 − c′ | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.184 | — | 0.008 | 0.017 | 0.022 | 0.044 | 0.009 | 0.023 |
| ID | -0.712 | — | 5.049 | 4.885 | 3.315 | 4.147 | 5.019 | 4.883 |
| KH | 0.366 | — | 0.323 | 0.093 | 0.222 | 0.169 | 0.330 | 0.188 |
| LA | -0.108 | — | 0.156 | 0.073 | 0.103 | 0.118 | 0.151 | 0.098 |
| MM | 0.298 | — | 0.953 | 0.250 | 0.164 | 0.227 | 0.923 | 0.288 |
| MY | 0.870 | — | 0.653 | 1.321 | 1.544 | 1.566 | 0.663 | 1.153 |
| PH | 0.130 | — | 2.513 | 1.745 | 1.037 | 1.398 | 2.494 | 1.996 |
| SG | 2.770 | — | 0.094 | 0.593 | 0.364 | 0.446 | 0.107 | 0.482 |
| TH | 4.073 | — | 1.081 | 1.540 | 2.678 | 2.079 | 1.098 | 1.299 |
| TL | 0.026 | — | 0.030 | 0.010 | 0.020 | 0.031 | 0.030 | 0.007 |
| VN | 1.369 | — | 1.703 | 2.035 | 3.095 | 2.337 | 1.738 | 2.146 |

（✗ = 规则给该国的好处超过其边际贡献，其余参与者合计支付超过 c(N − i)。）

(A) 去一国检查未通过：population_aeo8_d1：无；gdp_aeo8_d2：无；electricity_fixed：无；electricity_base：无；population_ssp2：无；gdp_ppp_ssp2：无

## 比例规则 (B)：按比例分摊一体化总成本（对照；检验 = 个体理性）

- payment_i = s_i x (c(N) - phi_BUNKER - SHARED) of the integrated run; test (individual rationality): payment_i <= disconnected allocation_i (+ the C1 (b) tolerance)
- 11 国分摊总额 = 253.631 bn。Owen（主值）个体理性：未通过 ID, LA

| 国 | 不互联分摊 | Owen 支付 | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.622 | 0.438 | 0.161 | 0.339 | 0.439 | 0.891 ✗ | 0.174 | 0.471 |
| ID | 89.379 | 90.092 | 101.929 ✗ | 98.617 ✗ | 66.922 | 83.724 | 101.332 ✗ | 98.578 ✗ |
| KH | 4.481 | 4.115 | 6.523 ✗ | 1.879 | 4.484 | 3.417 | 6.655 ✗ | 3.802 |
| LA | 0.274 | 0.382 | 3.149 ✗ | 1.483 ✗ | 2.071 ✗ | 2.381 ✗ | 3.043 ✗ | 1.983 ✗ |
| MM | 3.282 | 2.983 | 19.248 ✗ | 5.050 ✗ | 3.303 ✗ | 4.586 ✗ | 18.644 ✗ | 5.815 ✗ |
| MY | 25.735 | 24.865 | 13.175 | 26.675 ✗ | 31.167 ✗ | 31.613 ✗ | 13.394 | 23.279 |
| PH | 17.408 | 17.278 | 50.740 ✗ | 35.233 ✗ | 20.938 ✗ | 28.227 ✗ | 50.356 ✗ | 40.294 ✗ |
| SG | 12.812 | 10.041 | 1.896 | 11.970 | 7.346 | 9.014 | 2.162 | 9.723 |
| TH | 46.980 | 42.907 | 21.819 | 31.087 | 54.075 ✗ | 41.975 | 22.177 | 26.218 |
| TL | 0.378 | 0.351 | 0.607 ✗ | 0.207 | 0.402 ✗ | 0.625 ✗ | 0.599 ✗ | 0.140 |
| VN | 61.548 | 60.179 | 34.383 | 41.089 | 62.485 ✗ | 47.178 | 35.096 | 43.327 |

（✗ = 支付超过不互联分摊，违反个体理性。）

(B) 个体理性未通过：population_aeo8_d1：ID, KH, LA, MM, PH, TL；gdp_aeo8_d2：ID, LA, MM, MY, PH；electricity_fixed：LA, MM, MY, PH, TH, TL, VN；electricity_base：BN, LA, MM, MY, PH, TL；population_ssp2：ID, KH, LA, MM, PH, TL；gdp_ppp_ssp2：ID, LA, MM, PH

## 燃料舱参与者（补充 01 D10）

- 受益 = 不互联 79.372 − 一体化 76.075 = **3.297 bn**（非负）。
- 严格单独成本（只用区域外非化石进口）：106.446 bn；一体化份额 ≤ 单独成本：**True**；不互联份额 ≤ 单独成本：True。
- 解释：一体化改变液体燃料池价格，燃料舱作为没有资源、不能退出的纯价格接受者承担这一金钱外部性；不视为违反个体理性，个体理性的检验是 Owen 份额 ≤ 严格单独成本。

- (A) splits B6 among the 11 countries by positive weights: with B6 > 0 no country gets a negative benefit; the bunker account (no population / GDP / electricity) keeps its disconnected allocation (benefit 0) in (A) and its integrated allocation in (B)
- rule_budget_residual_eur = sum of the (A) payments of the first weight + bunker - (integrated objective - integrated pool residual) = change of the pool residual
- 预算残差 -5,005 EUR（池盈余变化）。
- 权重来源：{'population_aeo8': 'sources/AEO8_2050_BY_COUNTRY.csv table D.1 2050 (all scenarios); TL UN WPP 2024 median 1,889,249.5 (as m08b_demand.py)', 'gdp_aeo8': 'research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv table D.2 real GDP PPP 2017 (million USD) 2050; TL = mean(KH, LA, MM) GDP per capita x TL population (M08b TL rule)', 'population_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv IIASA-WiC POP 2025 SSP2 2050 (comparison)', 'gdp_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv OECD ENV-Growth 2025 SSP2 GDP|PPP 2050 (billion USD2017; comparison)'}

## 并列：市场结算形式（现行账本）下的受益

- 受益为负：**ID**

| 参与者 | 主值受益 bn | 市场形式受益 bn | 市场 − 主值 bn |
|---|---|---|---|
| BN | 0.184 | 0.184 | 0.000 |
| ID | -0.712 | -0.704 | 0.008 |
| KH | 0.366 | 0.654 | 0.287 |
| LA | -0.108 | 1.359 | 1.468 |
| MM | 0.298 | 0.239 | -0.059 |
| MY | 0.870 | 0.861 | -0.008 |
| PH | 0.130 | 0.130 | -0.000 |
| SG | 2.770 | 2.770 | -0.000 |
| TH | 4.073 | 1.986 | -2.087 |
| TL | 0.026 | 0.026 | 0.000 |
| VN | 1.369 | 1.759 | 0.390 |
| BUNKER | 3.297 | 3.297 | -0.000 |
