# BENEFIT（M12 C1 第 4、5 项：受益检查与比例规则对照；只读）

- 一体化：`/root/autodl-tmp/v3_screen/runs/dfx/V1`；不互联：`/root/autodl-tmp/v3_screen/runs/dfx/V2`。
- 主值口径（补充 01 D1）：**owen_dual_form**；来源 /root/autodl-tmp/v3_screen/runs/dfx/V1/m12_owen/OWEN.json；/root/autodl-tmp/v3_screen/runs/dfx/V2/m12_owen/OWEN.json。
- B6 = 不互联目标值 − 一体化目标值 = 14.348 bn EUR2020。
- Owen 受益为负的参与者（α 0.5）：**BUNKER**；α 区间内可能为负：BUNKER。
- 燃料舱参与者：一体化 True，不互联 True。

| 参与者 | Owen 受益 bn | 区间下限 | 区间上限 |
|---|---|---|---|
| BN | 0.063 | 0.063 | 0.063 |
| ID | 0.559 | 0.528 | 0.589 |
| KH | 0.197 | 0.164 | 0.230 |
| LA | 0.781 | 0.592 | 0.970 |
| MM | 0.200 | 0.159 | 0.241 |
| MY | 3.139 | 2.848 | 3.431 |
| PH | 0.058 | 0.058 | 0.058 |
| SG | 3.845 | 3.818 | 3.871 |
| TH | 1.097 | 0.657 | 1.537 |
| TL | 0.137 | 0.137 | 0.137 |
| VN | 4.482 | 4.444 | 4.519 |
| BUNKER | -0.210 | -0.210 | -0.210 |

- 权重（补充 01 D5）：主用 population_aeo8_d1, gdp_aeo8_d2, electricity_fixed, electricity_base；对照 population_ssp2, gdp_ppp_ssp2（表中排在后面）。

## 比例规则 (A)：按比例分摊 B6（主讨论；检验 = 去一国边际贡献，补充 01 D4）

- benefit_i = s_i x B6, payment_i = disconnected allocation_i - benefit_i; test: payment_i >= c'(i) (c'(i) = c(N) - c(N - i), D8 adjusted), i.e. benefit_i <= disconnected allocation_i - c'(i): otherwise the other players pay more than c(N - i). With B6 > 0 the benefit is never negative, so 'negative benefit' is not a test of (A). Only countries with a leave-one-out run.
- 去一国来源：无（(A) 的检验不可计算）；容差：PRECISION.json of /root/autodl-tmp/v3_screen/runs/dfx/V1 (this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen/runs/dfx/V2 minus /root/autodl-tmp/v)。
- Owen（主值）去一国检查：无去一国运行

| 国 | Owen 受益 | 受益上限 φ不互联 − c′ | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.063 | — | 0.009 | 0.019 | 0.025 | 0.050 | 0.010 | 0.027 |
| ID | 0.559 | — | 5.766 | 5.579 | 3.768 | 4.613 | 5.732 | 5.577 |
| KH | 0.197 | — | 0.369 | 0.106 | 0.251 | 0.190 | 0.376 | 0.215 |
| LA | 0.781 | — | 0.178 | 0.084 | 0.117 | 0.134 | 0.172 | 0.112 |
| MM | 0.200 | — | 1.089 | 0.286 | 0.192 | 0.270 | 1.055 | 0.329 |
| MY | 3.139 | — | 0.745 | 1.509 | 1.748 | 1.739 | 0.758 | 1.317 |
| PH | 0.058 | — | 2.870 | 1.993 | 1.177 | 1.544 | 2.849 | 2.279 |
| SG | 3.845 | — | 0.107 | 0.677 | 0.418 | 0.510 | 0.122 | 0.550 |
| TH | 1.097 | — | 1.234 | 1.759 | 3.092 | 2.525 | 1.255 | 1.483 |
| TL | 0.137 | — | 0.034 | 0.012 | 0.023 | 0.034 | 0.034 | 0.008 |
| VN | 4.482 | — | 1.945 | 2.324 | 3.537 | 2.738 | 1.985 | 2.451 |

（✗ = 规则给该国的好处超过其边际贡献，其余参与者合计支付超过 c(N − i)。）

(A) 去一国检查未通过：population_aeo8_d1：无；gdp_aeo8_d2：无；electricity_fixed：无；electricity_base：无；population_ssp2：无；gdp_ppp_ssp2：无

## 比例规则 (B)：按比例分摊一体化总成本（对照；检验 = 个体理性）

- payment_i = s_i x (c(N) - phi_BUNKER - SHARED) of the integrated run; test (individual rationality): payment_i <= disconnected allocation_i (+ the C1 (b) tolerance)
- 11 国分摊总额 = 197.005 bn。Owen（主值）个体理性：全部通过

| 国 | 不互联分摊 | Owen 支付 | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.457 | 0.394 | 0.125 | 0.264 | 0.349 | 0.692 ✗ | 0.135 | 0.366 |
| ID | 72.320 | 71.761 | 79.173 ✗ | 76.600 ✗ | 51.731 | 63.344 | 78.709 ✗ | 76.569 ✗ |
| KH | 3.407 | 3.210 | 5.067 ✗ | 1.460 | 3.449 ✗ | 2.607 | 5.169 ✗ | 2.953 |
| LA | 0.880 | 0.099 | 2.446 ✗ | 1.152 ✗ | 1.610 ✗ | 1.838 ✗ | 2.364 ✗ | 1.540 ✗ |
| MM | 1.834 | 1.633 | 14.951 ✗ | 3.923 ✗ | 2.634 ✗ | 3.706 ✗ | 14.481 ✗ | 4.517 ✗ |
| MY | 23.957 | 20.818 | 10.234 | 20.720 | 23.998 ✗ | 23.877 | 10.403 | 18.082 |
| PH | 14.272 | 14.214 | 39.412 ✗ | 27.367 ✗ | 16.158 ✗ | 21.203 ✗ | 39.113 ✗ | 31.298 ✗ |
| SG | 12.762 | 8.918 | 1.473 | 9.298 | 5.736 | 7.004 | 1.680 | 7.553 |
| TH | 33.006 | 31.910 | 16.948 | 24.146 | 42.458 ✗ | 34.672 ✗ | 17.225 | 20.365 |
| TL | 0.118 | -0.020 | 0.472 ✗ | 0.161 ✗ | 0.312 ✗ | 0.473 ✗ | 0.465 ✗ | 0.109 |
| VN | 48.550 | 44.068 | 26.707 | 31.915 | 48.571 | 37.591 | 27.260 | 33.654 |

（✗ = 支付超过不互联分摊，违反个体理性。）

(B) 个体理性未通过：population_aeo8_d1：ID, KH, LA, MM, PH, TL；gdp_aeo8_d2：ID, LA, MM, PH, TL；electricity_fixed：KH, LA, MM, MY, PH, TH, TL；electricity_base：BN, LA, MM, PH, TH, TL；population_ssp2：ID, KH, LA, MM, PH, TL；gdp_ppp_ssp2：ID, LA, MM, PH

## 燃料舱参与者（补充 01 D10）

- 受益 = 不互联 66.381 − 一体化 66.591 = **-0.210 bn**（为负，照实报告）。
- 严格单独成本（只用区域外非化石进口）：106.446 bn；一体化份额 ≤ 单独成本：**True**；不互联份额 ≤ 单独成本：True。
- 解释：一体化改变液体燃料池价格，燃料舱作为没有资源、不能退出的纯价格接受者承担这一金钱外部性；不视为违反个体理性，个体理性的检验是 Owen 份额 ≤ 严格单独成本。

- (A) splits B6 among the 11 countries by positive weights: with B6 > 0 no country gets a negative benefit; the bunker account (no population / GDP / electricity) keeps its disconnected allocation (benefit 0) in (A) and its integrated allocation in (B)
- rule_budget_residual_eur = sum of the (A) payments of the first weight + bunker - (integrated objective - integrated pool residual) = change of the pool residual
- 预算残差 -3,478 EUR（池盈余变化）。
- 权重来源：{'population_aeo8': 'sources/AEO8_2050_BY_COUNTRY.csv table D.1 2050 (all scenarios); TL UN WPP 2024 median 1,889,249.5 (as m08b_demand.py)', 'gdp_aeo8': 'research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv table D.2 real GDP PPP 2017 (million USD) 2050; TL = mean(KH, LA, MM) GDP per capita x TL population (M08b TL rule)', 'population_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv IIASA-WiC POP 2025 SSP2 2050 (comparison)', 'gdp_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv OECD ENV-Growth 2025 SSP2 GDP|PPP 2050 (billion USD2017; comparison)'}

## 并列：市场结算形式（现行账本）下的受益

- 受益为负：**BUNKER**

| 参与者 | 主值受益 bn | 市场形式受益 bn | 市场 − 主值 bn |
|---|---|---|---|
| BN | 0.063 | 0.063 | -0.000 |
| ID | 0.559 | 0.567 | 0.008 |
| KH | 0.197 | 0.179 | -0.018 |
| LA | 0.781 | 0.797 | 0.016 |
| MM | 0.200 | 0.120 | -0.080 |
| MY | 3.139 | 3.131 | -0.008 |
| PH | 0.058 | 0.058 | -0.000 |
| SG | 3.845 | 3.845 | -0.000 |
| TH | 1.097 | 1.187 | 0.090 |
| TL | 0.137 | 0.137 | -0.000 |
| VN | 4.482 | 4.474 | -0.008 |
| BUNKER | -0.210 | -0.210 | -0.000 |
