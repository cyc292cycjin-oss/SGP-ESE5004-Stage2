# BENEFIT（M12 C1 第 4、5 项：受益检查与比例规则对照；只读）

- 一体化：`/root/autodl-tmp/v3_screen_dmax/runs/dfx/V1`；不互联：`/root/autodl-tmp/v3_screen_dmax/runs/dfx/V2`。
- 主值口径（补充 01 D1）：**owen_dual_form**；来源 /root/autodl-tmp/v3_screen_dmax/runs/dfx/V1/m12_owen/OWEN.json；/root/autodl-tmp/v3_screen_dmax/runs/dfx/V2/m12_owen/OWEN.json。
- B6 = 不互联目标值 − 一体化目标值 = 14.574 bn EUR2020。
- Owen 受益为负的参与者（α 0.5）：**BUNKER**；α 区间内可能为负：BUNKER。
- 燃料舱参与者：一体化 True，不互联 True。

| 参与者 | Owen 受益 bn | 区间下限 | 区间上限 |
|---|---|---|---|
| BN | 0.066 | 0.066 | 0.066 |
| ID | 0.587 | 0.552 | 0.621 |
| KH | 0.193 | 0.156 | 0.231 |
| LA | 0.775 | 0.583 | 0.967 |
| MM | 0.245 | 0.202 | 0.287 |
| MY | 3.176 | 2.879 | 3.473 |
| PH | 0.062 | 0.062 | 0.062 |
| SG | 3.920 | 3.900 | 3.939 |
| TH | 1.013 | 0.558 | 1.469 |
| TL | 0.152 | 0.152 | 0.152 |
| VN | 4.502 | 4.465 | 4.539 |
| BUNKER | -0.117 | -0.117 | -0.117 |

- 权重（补充 01 D5）：主用 population_aeo8_d1, gdp_aeo8_d2, electricity_fixed, electricity_base；对照 population_ssp2, gdp_ppp_ssp2（表中排在后面）。

## 比例规则 (A)：按比例分摊 B6（主讨论；检验 = 去一国边际贡献，补充 01 D4）

- benefit_i = s_i x B6, payment_i = disconnected allocation_i - benefit_i; test: payment_i >= c'(i) (c'(i) = c(N) - c(N - i), D8 adjusted), i.e. benefit_i <= disconnected allocation_i - c'(i): otherwise the other players pay more than c(N - i). With B6 > 0 the benefit is never negative, so 'negative benefit' is not a test of (A). Only countries with a leave-one-out run.
- 去一国来源：无（(A) 的检验不可计算）；容差：PRECISION.json of /root/autodl-tmp/v3_screen_dmax/runs/dfx/V1 (this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen_dmax/runs/dfx/V2 minus /root/autodl-)。
- Owen（主值）去一国检查：无去一国运行

| 国 | Owen 受益 | 受益上限 φ不互联 − c′ | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.066 | — | 0.009 | 0.019 | 0.026 | 0.051 | 0.010 | 0.027 |
| ID | 0.587 | — | 5.857 | 5.667 | 3.827 | 4.686 | 5.823 | 5.664 |
| KH | 0.193 | — | 0.375 | 0.108 | 0.255 | 0.193 | 0.382 | 0.218 |
| LA | 0.775 | — | 0.181 | 0.085 | 0.119 | 0.136 | 0.175 | 0.114 |
| MM | 0.245 | — | 1.106 | 0.290 | 0.195 | 0.274 | 1.071 | 0.334 |
| MY | 3.176 | — | 0.757 | 1.533 | 1.775 | 1.766 | 0.770 | 1.338 |
| PH | 0.062 | — | 2.916 | 2.025 | 1.195 | 1.569 | 2.893 | 2.315 |
| SG | 3.920 | — | 0.109 | 0.688 | 0.424 | 0.518 | 0.124 | 0.559 |
| TH | 1.013 | — | 1.254 | 1.786 | 3.141 | 2.565 | 1.274 | 1.507 |
| TL | 0.152 | — | 0.035 | 0.012 | 0.023 | 0.035 | 0.034 | 0.008 |
| VN | 4.502 | — | 1.976 | 2.361 | 3.593 | 2.781 | 2.017 | 2.490 |

（✗ = 规则给该国的好处超过其边际贡献，其余参与者合计支付超过 c(N − i)。）

(A) 去一国检查未通过：population_aeo8_d1：无；gdp_aeo8_d2：无；electricity_fixed：无；electricity_base：无；population_ssp2：无；gdp_ppp_ssp2：无

## 比例规则 (B)：按比例分摊一体化总成本（对照；检验 = 个体理性）

- payment_i = s_i x (c(N) - phi_BUNKER - SHARED) of the integrated run; test (individual rationality): payment_i <= disconnected allocation_i (+ the C1 (b) tolerance)
- 11 国分摊总额 = 199.675 bn。Owen（主值）个体理性：全部通过

| 国 | 不互联分摊 | Owen 支付 | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.464 | 0.398 | 0.126 | 0.267 | 0.354 | 0.701 ✗ | 0.137 | 0.371 |
| ID | 72.922 | 72.335 | 80.246 ✗ | 77.638 ✗ | 52.432 | 64.203 | 79.775 ✗ | 77.607 ✗ |
| KH | 3.502 | 3.309 | 5.136 ✗ | 1.480 | 3.496 | 2.642 | 5.239 ✗ | 2.993 |
| LA | 0.882 | 0.106 | 2.479 ✗ | 1.168 ✗ | 1.632 ✗ | 1.863 ✗ | 2.396 ✗ | 1.561 ✗ |
| MM | 1.847 | 1.602 | 15.154 ✗ | 3.976 ✗ | 2.670 ✗ | 3.756 ✗ | 14.678 ✗ | 4.578 ✗ |
| MY | 24.015 | 20.839 | 10.372 | 21.001 | 24.323 ✗ | 24.201 ✗ | 10.544 | 18.327 |
| PH | 14.563 | 14.501 | 39.946 ✗ | 27.738 ✗ | 16.377 ✗ | 21.491 ✗ | 39.643 ✗ | 31.722 ✗ |
| SG | 12.766 | 8.846 | 1.493 | 9.424 | 5.813 | 7.099 | 1.702 | 7.655 |
| TH | 33.699 | 32.686 | 17.177 | 24.474 | 43.033 ✗ | 35.141 ✗ | 17.459 | 20.641 |
| TL | 0.130 | -0.022 | 0.478 ✗ | 0.163 ✗ | 0.316 ✗ | 0.479 ✗ | 0.471 ✗ | 0.111 |
| VN | 49.577 | 45.076 | 27.069 | 32.348 | 49.229 | 38.100 | 27.630 | 34.110 |

（✗ = 支付超过不互联分摊，违反个体理性。）

(B) 个体理性未通过：population_aeo8_d1：ID, KH, LA, MM, PH, TL；gdp_aeo8_d2：ID, LA, MM, PH, TL；electricity_fixed：LA, MM, MY, PH, TH, TL；electricity_base：BN, LA, MM, MY, PH, TH, TL；population_ssp2：ID, KH, LA, MM, PH, TL；gdp_ppp_ssp2：ID, LA, MM, PH

## 燃料舱参与者（补充 01 D10）

- 受益 = 不互联 66.481 − 一体化 66.598 = **-0.117 bn**（为负，照实报告）。
- 严格单独成本（只用区域外非化石进口）：106.446 bn；一体化份额 ≤ 单独成本：**True**；不互联份额 ≤ 单独成本：True。
- 解释：一体化改变液体燃料池价格，燃料舱作为没有资源、不能退出的纯价格接受者承担这一金钱外部性；不视为违反个体理性，个体理性的检验是 Owen 份额 ≤ 严格单独成本。

- (A) splits B6 among the 11 countries by positive weights: with B6 > 0 no country gets a negative benefit; the bunker account (no population / GDP / electricity) keeps its disconnected allocation (benefit 0) in (A) and its integrated allocation in (B)
- rule_budget_residual_eur = sum of the (A) payments of the first weight + bunker - (integrated objective - integrated pool residual) = change of the pool residual
- 预算残差 -1,607 EUR（池盈余变化）。
- 权重来源：{'population_aeo8': 'sources/AEO8_2050_BY_COUNTRY.csv table D.1 2050 (all scenarios); TL UN WPP 2024 median 1,889,249.5 (as m08b_demand.py)', 'gdp_aeo8': 'research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv table D.2 real GDP PPP 2017 (million USD) 2050; TL = mean(KH, LA, MM) GDP per capita x TL population (M08b TL rule)', 'population_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv IIASA-WiC POP 2025 SSP2 2050 (comparison)', 'gdp_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv OECD ENV-Growth 2025 SSP2 GDP|PPP 2050 (billion USD2017; comparison)'}

## 并列：市场结算形式（现行账本）下的受益

- 受益为负：**BUNKER**

| 参与者 | 主值受益 bn | 市场形式受益 bn | 市场 − 主值 bn |
|---|---|---|---|
| BN | 0.066 | 0.066 | -0.000 |
| ID | 0.587 | 0.595 | 0.008 |
| KH | 0.193 | 0.177 | -0.016 |
| LA | 0.775 | 0.797 | 0.021 |
| MM | 0.245 | 0.172 | -0.073 |
| MY | 3.176 | 3.168 | -0.008 |
| PH | 0.062 | 0.062 | -0.000 |
| SG | 3.920 | 3.920 | 0.000 |
| TH | 1.013 | 1.081 | 0.068 |
| TL | 0.152 | 0.152 | -0.000 |
| VN | 4.502 | 4.501 | -0.001 |
| BUNKER | -0.117 | -0.117 | -0.000 |
