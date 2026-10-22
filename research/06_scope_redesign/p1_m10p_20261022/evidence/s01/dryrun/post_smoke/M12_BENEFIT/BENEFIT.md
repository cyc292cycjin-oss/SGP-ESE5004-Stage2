# BENEFIT（M12 C1 第 4、5 项：受益检查与比例规则对照；只读）

- 一体化：`/home/jin/m10p_dry_s01/post_smoke/R1`；不互联：`/home/jin/m10p_dry_s01/post_smoke/R2`。
- 主值口径（补充 01 D1）：**owen_dual_form**；来源 /home/jin/m10p_dry_s01/post_smoke/R1/m12_owen/OWEN.json；/home/jin/m10p_dry_s01/post_smoke/R2/m12_owen/OWEN.json。
- B6 = 不互联目标值 − 一体化目标值 = 9.899 bn EUR2020。
- Owen 受益为负的参与者（α 0.5）：**无**；α 区间内可能为负：无。
- 燃料舱参与者：一体化 True，不互联 True。

| 参与者 | Owen 受益 bn | 区间下限 | 区间上限 |
|---|---|---|---|
| BN | 0.150 | 0.150 | 0.150 |
| ID | 0.219 | 0.218 | 0.221 |
| KH | 0.448 | 0.444 | 0.452 |
| LA | 1.345 | 1.335 | 1.355 |
| MM | 0.441 | 0.428 | 0.453 |
| MY | 0.465 | 0.458 | 0.472 |
| PH | 0.154 | 0.154 | 0.154 |
| SG | 1.974 | 1.971 | 1.977 |
| TH | 1.880 | 1.855 | 1.905 |
| TL | 0.019 | 0.019 | 0.019 |
| VN | 0.704 | 0.703 | 0.705 |
| BUNKER | 2.099 | 2.099 | 2.099 |

- 权重（补充 01 D5）：主用 population_aeo8_d1, gdp_aeo8_d2, electricity_fixed, electricity_base；对照 population_ssp2, gdp_ppp_ssp2（表中排在后面）。

## 比例规则 (A)：按比例分摊 B6（主讨论；检验 = 去一国边际贡献，补充 01 D4）

- benefit_i = s_i x B6, payment_i = disconnected allocation_i - benefit_i; test: payment_i >= c'(i) (c'(i) = c(N) - c(N - i), D8 adjusted), i.e. benefit_i <= disconnected allocation_i - c'(i): otherwise the other players pay more than c(N - i). With B6 > 0 the benefit is never negative, so 'negative benefit' is not a test of (A). Only countries with a leave-one-out run.
- 去一国来源：/home/jin/m10p_dry_s01/post_smoke/M12_LOO/LOO_CHECK.json；容差：PRECISION.json of /home/jin/m10p_dry_s01/post_smoke/R1 (this batch: disconnected - integrated ledger difference (/home/jin/m10p_dry_s01/post_smoke/R2 minus /home/jin/m10p_dry_s)。
- Owen（主值）去一国检查：LA 余量 0.893 bn 通过；TH 余量 0.187 bn 通过；VN 余量 1.173 bn 通过

| 国 | Owen 受益 | 受益上限 φ不互联 − c′ | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.150 | — | 0.006 | 0.013 | 0.016 | 0.035 | 0.007 | 0.018 |
| ID | 0.219 | — | 3.978 | 3.849 | 2.689 | 3.268 | 3.955 | 3.847 |
| KH | 0.448 | — | 0.255 | 0.073 | 0.194 | 0.133 | 0.260 | 0.148 |
| LA | 1.345 | 2.238 | 0.123 | 0.058 | 0.088 | 0.093 | 0.119 | 0.077 |
| MM | 0.441 | — | 0.751 | 0.197 | 0.142 | 0.179 | 0.728 | 0.227 |
| MY | 0.465 | — | 0.514 | 1.041 | 1.161 | 1.234 | 0.523 | 0.909 |
| PH | 0.154 | — | 1.980 | 1.375 | 0.895 | 1.102 | 1.965 | 1.573 |
| SG | 1.974 | — | 0.074 | 0.467 | 0.254 | 0.352 | 0.084 | 0.379 |
| TH | 1.880 | 2.067 | 0.852 | 1.213 | 1.943 | 1.638 | 0.865 | 1.023 |
| TL | 0.019 | — | 0.024 | 0.008 | 0.017 | 0.024 | 0.023 | 0.005 |
| VN | 0.704 | 1.877 | 1.342 | 1.604 | 2.499 ✗ | 1.841 | 1.370 | 1.691 |

（✗ = 规则给该国的好处超过其边际贡献，其余参与者合计支付超过 c(N − i)。）

(A) 去一国检查未通过：population_aeo8_d1：无；gdp_aeo8_d2：无；electricity_fixed：VN；electricity_base：无；population_ssp2：无；gdp_ppp_ssp2：无

## 比例规则 (B)：按比例分摊一体化总成本（对照；检验 = 个体理性）

- payment_i = s_i x (c(N) - phi_BUNKER - SHARED) of the integrated run; test (individual rationality): payment_i <= disconnected allocation_i (+ the C1 (b) tolerance)
- 11 国分摊总额 = 231.873 bn。Owen（主值）个体理性：全部通过

| 国 | 不互联分摊 | Owen 支付 | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.481 | 0.331 | 0.147 | 0.310 | 0.386 | 0.815 ✗ | 0.159 | 0.431 |
| ID | 82.630 | 82.411 | 93.185 ✗ | 90.157 ✗ | 62.986 | 76.542 | 92.640 ✗ | 90.121 ✗ |
| KH | 4.782 | 4.335 | 5.964 ✗ | 1.718 | 4.544 | 3.124 | 6.084 ✗ | 3.476 |
| LA | 1.896 | 0.551 | 2.879 ✗ | 1.356 | 2.067 ✗ | 2.176 ✗ | 2.782 ✗ | 1.812 |
| MM | 3.235 | 2.794 | 17.597 ✗ | 4.617 ✗ | 3.325 ✗ | 4.192 ✗ | 17.044 ✗ | 5.316 ✗ |
| MY | 21.414 | 20.949 | 12.045 | 24.387 ✗ | 27.191 ✗ | 28.901 ✗ | 12.245 | 21.282 |
| PH | 18.123 | 17.968 | 46.387 ✗ | 32.210 ✗ | 20.961 ✗ | 25.806 ✗ | 46.036 ✗ | 36.837 ✗ |
| SG | 9.300 | 7.326 | 1.733 | 10.944 ✗ | 5.944 | 8.241 | 1.977 | 8.889 |
| TH | 35.155 | 33.275 | 19.947 | 28.420 | 45.526 ✗ | 38.374 ✗ | 20.274 | 23.969 |
| TL | 0.376 | 0.357 | 0.555 ✗ | 0.189 | 0.409 ✗ | 0.571 ✗ | 0.547 ✗ | 0.128 |
| VN | 62.282 | 61.578 | 31.434 | 37.564 | 58.534 | 43.131 | 32.085 | 39.610 |

（✗ = 支付超过不互联分摊，违反个体理性。）

(B) 个体理性未通过：population_aeo8_d1：ID, KH, LA, MM, PH, TL；gdp_aeo8_d2：ID, MM, MY, PH, SG；electricity_fixed：LA, MM, MY, PH, TH, TL；electricity_base：BN, LA, MM, MY, PH, TH, TL；population_ssp2：ID, KH, LA, MM, PH, TL；gdp_ppp_ssp2：ID, MM, PH

## 燃料舱参与者（补充 01 D10）

- 受益 = 不互联 78.073 − 一体化 75.974 = **2.099 bn**（非负）。
- 严格单独成本（只用区域外非化石进口）：106.446 bn；一体化份额 ≤ 单独成本：**True**；不互联份额 ≤ 单独成本：True。
- 解释：一体化改变液体燃料池价格，燃料舱作为没有资源、不能退出的纯价格接受者承担这一金钱外部性；不视为违反个体理性，个体理性的检验是 Owen 份额 ≤ 严格单独成本。

- (A) splits B6 among the 11 countries by positive weights: with B6 > 0 no country gets a negative benefit; the bunker account (no population / GDP / electricity) keeps its disconnected allocation (benefit 0) in (A) and its integrated allocation in (B)
- rule_budget_residual_eur = sum of the (A) payments of the first weight + bunker - (integrated objective - integrated pool residual) = change of the pool residual
- 预算残差 -5 EUR（池盈余变化）。
- 权重来源：{'population_aeo8': 'sources/AEO8_2050_BY_COUNTRY.csv table D.1 2050 (all scenarios); TL UN WPP 2024 median 1,889,249.5 (as m08b_demand.py)', 'gdp_aeo8': 'research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv table D.2 real GDP PPP 2017 (million USD) 2050; TL = mean(KH, LA, MM) GDP per capita x TL population (M08b TL rule)', 'population_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv IIASA-WiC POP 2025 SSP2 2050 (comparison)', 'gdp_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv OECD ENV-Growth 2025 SSP2 GDP|PPP 2050 (billion USD2017; comparison)'}

## 并列：市场结算形式（现行账本）下的受益

- 受益为负：**无**

| 参与者 | 主值受益 bn | 市场形式受益 bn | 市场 − 主值 bn |
|---|---|---|---|
| BN | 0.150 | 0.150 | 0.000 |
| ID | 0.219 | 0.226 | 0.007 |
| KH | 0.448 | 0.719 | 0.271 |
| LA | 1.345 | 1.416 | 0.072 |
| MM | 0.441 | 0.396 | -0.045 |
| MY | 0.465 | 0.458 | -0.007 |
| PH | 0.154 | 0.154 | 0.000 |
| SG | 1.974 | 1.974 | 0.000 |
| TH | 1.880 | 1.293 | -0.587 |
| TL | 0.019 | 0.019 | 0.000 |
| VN | 0.704 | 0.993 | 0.289 |
| BUNKER | 2.099 | 2.099 | -0.000 |
