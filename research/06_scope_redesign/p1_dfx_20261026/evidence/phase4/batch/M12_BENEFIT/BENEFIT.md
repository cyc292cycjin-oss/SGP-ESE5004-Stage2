# BENEFIT（M12 C1 第 4、5 项：受益检查与比例规则对照；只读）

- 一体化：`/root/autodl-tmp/dfx_v8/runs/dfx/V1`；不互联：`/root/autodl-tmp/dfx_v8/runs/dfx/V2`。
- 主值口径（补充 01 D1）：**owen_dual_form**；来源 /root/autodl-tmp/dfx_v8/runs/dfx/V1/m12_owen/OWEN.json；/root/autodl-tmp/dfx_v8/runs/dfx/V2/m12_owen/OWEN.json。
- B6 = 不互联目标值 − 一体化目标值 = 14.615 bn EUR2020。
- Owen 受益为负的参与者（α 0.5）：**BUNKER**；α 区间内可能为负：BUNKER。
- 燃料舱参与者：一体化 True，不互联 True。

| 参与者 | Owen 受益 bn | 区间下限 | 区间上限 |
|---|---|---|---|
| BN | 0.076 | 0.076 | 0.076 |
| ID | 0.602 | 0.602 | 0.602 |
| KH | 0.259 | 0.256 | 0.262 |
| LA | 1.229 | 1.221 | 1.238 |
| MM | 0.305 | 0.291 | 0.320 |
| MY | 2.913 | 2.747 | 3.079 |
| PH | 0.147 | 0.147 | 0.147 |
| SG | 3.843 | 3.840 | 3.846 |
| TH | 1.769 | 1.581 | 1.956 |
| TL | 0.135 | 0.135 | 0.135 |
| VN | 3.573 | 3.572 | 3.574 |
| BUNKER | -0.237 | -0.237 | -0.237 |

- 权重（补充 01 D5）：主用 population_aeo8_d1, gdp_aeo8_d2, electricity_fixed, electricity_base；对照 population_ssp2, gdp_ppp_ssp2（表中排在后面）。

## 比例规则 (A)：按比例分摊 B6（主讨论；检验 = 去一国边际贡献，补充 01 D4）

- benefit_i = s_i x B6, payment_i = disconnected allocation_i - benefit_i; test: payment_i >= c'(i) (c'(i) = c(N) - c(N - i), D8 adjusted), i.e. benefit_i <= disconnected allocation_i - c'(i): otherwise the other players pay more than c(N - i). With B6 > 0 the benefit is never negative, so 'negative benefit' is not a test of (A). Only countries with a leave-one-out run.
- 去一国来源：无（(A) 的检验不可计算）；容差：PRECISION.json of /root/autodl-tmp/dfx_v8/runs/dfx/V1 (this batch: disconnected - integrated ledger difference (/root/autodl-tmp/dfx_v8/runs/dfx/V2 minus /root/autodl-tmp/dfx_)。
- Owen（主值）去一国检查：无去一国运行

| 国 | Owen 受益 | 受益上限 φ不互联 − c′ | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.076 | — | 0.009 | 0.020 | 0.027 | 0.051 | 0.010 | 0.027 |
| ID | 0.602 | — | 5.874 | 5.683 | 3.859 | 4.699 | 5.839 | 5.680 |
| KH | 0.259 | — | 0.376 | 0.108 | 0.265 | 0.193 | 0.383 | 0.219 |
| LA | 1.229 | — | 0.181 | 0.085 | 0.124 | 0.136 | 0.175 | 0.114 |
| MM | 0.305 | — | 1.109 | 0.291 | 0.203 | 0.275 | 1.074 | 0.335 |
| MY | 2.913 | — | 0.759 | 1.537 | 1.785 | 1.771 | 0.772 | 1.341 |
| PH | 0.147 | — | 2.924 | 2.030 | 1.242 | 1.573 | 2.902 | 2.322 |
| SG | 3.843 | — | 0.109 | 0.690 | 0.441 | 0.520 | 0.125 | 0.560 |
| TH | 1.769 | — | 1.257 | 1.791 | 3.264 | 2.572 | 1.278 | 1.511 |
| TL | 0.135 | — | 0.035 | 0.012 | 0.024 | 0.035 | 0.034 | 0.008 |
| VN | 3.573 | — | 1.981 | 2.368 | 3.382 | 2.789 | 2.022 | 2.497 |

（✗ = 规则给该国的好处超过其边际贡献，其余参与者合计支付超过 c(N − i)。）

(A) 去一国检查未通过：population_aeo8_d1：无；gdp_aeo8_d2：无；electricity_fixed：无；electricity_base：无；population_ssp2：无；gdp_ppp_ssp2：无

## 比例规则 (B)：按比例分摊一体化总成本（对照；检验 = 个体理性）

- payment_i = s_i x (c(N) - phi_BUNKER - SHARED) of the integrated run; test (individual rationality): payment_i <= disconnected allocation_i (+ the C1 (b) tolerance)
- 11 国分摊总额 = 204.429 bn。Owen（主值）个体理性：全部通过

| 国 | 不互联分摊 | Owen 支付 | population_aeo8_d1 | gdp_aeo8_d2 | electricity_fixed | electricity_base | population_ssp2 | gdp_ppp_ssp2 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.472 | 0.396 | 0.130 | 0.274 | 0.375 | 0.718 ✗ | 0.140 | 0.380 |
| ID | 73.106 | 72.504 | 82.156 ✗ | 79.487 ✗ | 53.983 | 65.731 | 81.675 ✗ | 79.455 ✗ |
| KH | 3.713 | 3.454 | 5.258 ✗ | 1.515 | 3.709 | 2.705 | 5.364 ✗ | 3.065 |
| LA | 1.368 | 0.138 | 2.538 ✗ | 1.196 | 1.731 ✗ | 1.907 ✗ | 2.453 ✗ | 1.598 ✗ |
| MM | 1.860 | 1.555 | 15.514 ✗ | 4.071 ✗ | 2.833 ✗ | 3.845 ✗ | 15.027 ✗ | 4.687 ✗ |
| MY | 23.995 | 21.082 | 10.619 | 21.501 | 24.962 ✗ | 24.777 ✗ | 10.795 | 18.763 |
| PH | 14.951 | 14.804 | 40.897 ✗ | 28.398 ✗ | 17.374 ✗ | 22.002 ✗ | 40.587 ✗ | 32.477 ✗ |
| SG | 12.805 | 8.962 | 1.528 | 9.648 | 6.167 | 7.268 | 1.743 | 7.837 |
| TH | 35.026 | 33.257 | 17.586 | 25.056 | 45.651 ✗ | 35.978 ✗ | 17.875 | 21.132 |
| TL | 0.148 | 0.013 | 0.489 ✗ | 0.167 ✗ | 0.335 ✗ | 0.490 ✗ | 0.483 ✗ | 0.113 |
| VN | 51.835 | 48.262 | 27.713 | 33.118 | 47.309 | 39.008 | 28.288 | 34.922 |

（✗ = 支付超过不互联分摊，违反个体理性。）

(B) 个体理性未通过：population_aeo8_d1：ID, KH, LA, MM, PH, TL；gdp_aeo8_d2：ID, MM, PH, TL；electricity_fixed：LA, MM, MY, PH, TH, TL；electricity_base：BN, LA, MM, MY, PH, TH, TL；population_ssp2：ID, KH, LA, MM, PH, TL；gdp_ppp_ssp2：ID, LA, MM, PH

## 燃料舱参与者（补充 01 D10）

- 受益 = 不互联 66.119 − 一体化 66.356 = **-0.237 bn**（为负，照实报告）。
- 严格单独成本（只用区域外非化石进口）：106.446 bn；一体化份额 ≤ 单独成本：**True**；不互联份额 ≤ 单独成本：True。
- 解释：一体化改变液体燃料池价格，燃料舱作为没有资源、不能退出的纯价格接受者承担这一金钱外部性；不视为违反个体理性，个体理性的检验是 Owen 份额 ≤ 严格单独成本。

- (A) splits B6 among the 11 countries by positive weights: with B6 > 0 no country gets a negative benefit; the bunker account (no population / GDP / electricity) keeps its disconnected allocation (benefit 0) in (A) and its integrated allocation in (B)
- rule_budget_residual_eur = sum of the (A) payments of the first weight + bunker - (integrated objective - integrated pool residual) = change of the pool residual
- 预算残差 -965,869 EUR（池盈余变化）。
- 权重来源：{'population_aeo8': 'sources/AEO8_2050_BY_COUNTRY.csv table D.1 2050 (all scenarios); TL UN WPP 2024 median 1,889,249.5 (as m08b_demand.py)', 'gdp_aeo8': 'research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv table D.2 real GDP PPP 2017 (million USD) 2050; TL = mean(KH, LA, MM) GDP per capita x TL population (M08b TL rule)', 'population_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv IIASA-WiC POP 2025 SSP2 2050 (comparison)', 'gdp_ssp2': 'sources/SSP2_2025_POP_GDP_ASEAN11.csv OECD ENV-Growth 2025 SSP2 GDP|PPP 2050 (billion USD2017; comparison)'}

## 并列：市场结算形式（现行账本）下的受益

- 受益为负：**BUNKER**

| 参与者 | 主值受益 bn | 市场形式受益 bn | 市场 − 主值 bn |
|---|---|---|---|
| BN | 0.076 | 0.076 | 0.000 |
| ID | 0.602 | 0.608 | 0.006 |
| KH | 0.259 | 0.247 | -0.012 |
| LA | 1.229 | 1.253 | 0.023 |
| MM | 0.305 | 0.235 | -0.070 |
| MY | 2.913 | 2.907 | -0.006 |
| PH | 0.147 | 0.147 | 0.000 |
| SG | 3.843 | 3.843 | 0.000 |
| TH | 1.769 | 1.834 | 0.065 |
| TL | 0.135 | 0.135 | 0.000 |
| VN | 3.573 | 3.567 | -0.007 |
| BUNKER | -0.237 | -0.237 | 0.000 |
