# R12A：风电装机为 0 的原因诊断（只读）

**范围：** 只读，不修改任何文件。数据来自 D 阶段候选网络 `gate6_2920_candidate_UNQUALIFIED.nc`（`/mnt/d/ResearchWorkspaces/ASEAN/outputs/d_2920_diagnostic/d5_main2920_20261012T212658Z_0162bbf4/cloud_run/postprocess/`，314 MB）、作者参考网络 `elec_s_100_ec_lv2.0__3h_2025_0.071_DEC_0export.nc`、价格层 `model_cost_layer.json` 及其源 CSV（`costs_2050_sec.csv`、作者原始 `costs_2050.csv`、technology-data 证据 `outputs/costs_2050.csv`）。机器可读结果：`R12A_WIND_ZERO_DIAGNOSIS.json`（脚本 `scripts_project/r12a_wind_diagnosis.py`）。所有 SHA256 见 JSON。

## 结论（一句话）

**经济上合理，但前提需要修正：** D 阶段研究模型风电为 0 是因为（a）无碳约束下无限量化石燃料和光伏更便宜，（b）绝大多数节点的风电年均容量因子极低（陆上风电全国均值 0.02–0.14，仅菲律宾/越南少数节点 >0.2）。**作者参考模型的风电并不为 0**（9,116 MW：陆上 8,013 MW、越南海上 1,104 MW）——指令中"两个模型装机都是 0"的前提只对 D 阶段研究模型成立。未发现数据或代码错误；成本行是作者有意采用 AEO8 东盟成本，不是单位或年份错误。

## 逐项核查（VERIFIED，数值来自上述文件）

### 1. `p_nom_max` 是否为 0 或很小
- D 阶段与参考网络相同：242 个可扩展风电候选，`p_nom_max` 合计 13,644 GW（陆上 ~8,918 GW，海上 AC 1,673 GW，海上 DC 3,053 GW）。
- `p_nom_max = 0` 的只有 4 个（新加坡 `offwind-dc`、新加坡 `onwind` 等），<10 MW 的 5 个。**不是原因。**

### 2. `p_max_pu` 年均容量因子（2920 时段加权）按国家
| 载体 | BN | ID | KH | LA | MM | MY | PH | SG | TH | TL | VN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| onwind 均值 | 0.020 | 0.052 | 0.052 | 0.048 | 0.048 | 0.031 | 0.135 | 0.046 | 0.060 | 0.048 | 0.090 |
| onwind 节点最大 | 0.020 | 0.199 | 0.065 | 0.123 | 0.086 | 0.087 | 0.254 | 0.046 | 0.110 | 0.048 | 0.129 |
| offwind-ac 均值 | 0.058 | 0.088 | 0.093 | — | 0.135 | 0.059 | 0.180 | 0.060 | 0.103 | 0.068 | 0.251 |
| offwind-dc 均值 | 0.084 | 0.125 | 0.131 | — | 0.171 | 0.096 | 0.209 | 0.000 | 0.141 | 0.163 | **0.389**（最大 0.541） |

对比：光伏（utility）年均容量因子全国 0.127–0.155，节点间差异很小。

### 3. 资本成本与 technology-data 的一致性
| 技术 | 模型 `capital_cost`（EUR/MW/a，D 阶段） | 处理表 investment | 作者原始 costs_2050.csv 来源 | technology-data v0.13.2 同名行 |
|---|---|---|---|---|
| onwind | 114,912 | 991,619 EUR/MW；FOM 3.53 %/a；VOM 2.59 | **8th ASEAN Energy Outlook (D.15/D.17/D.18)**，EUR2020 | 1,019.1 EUR/kW；FOM 1.18 %；VOM 1.29 |
| offwind | 241,585（+站/连接） | 2,141,140 EUR/MW；FOM 3.22 % | 8th AEO | 1,523.9 EUR/kW；FOM 2.17 % |
| solar-utility | 71,546 | 850,912 EUR/MW；FOM 0.91 % | 8th AEO | 292.6 EUR/kW；FOM 2.53 % |
| solar-rooftop | 57,483 | 1,052,674 EUR/MW；FOM 0.41 % | 8th AEO | 524.9 EUR/kW |

- 年金公式核验（`fixed = (r/(1-(1+r)^-n) + FOM/100) × investment`）全部一致（`annuity_check: consistent=True`）。
- 处理值与 technology-data 的差异**不是单位或年份错误**：作者原始 `costs_2050.csv` 中这些行的来源列明写 "8th ASEAN Energy Outlook"，`currency_year=2020`，价格层状态 `ALREADY_EUR2020_UNCHANGED`（`AEO8_APPEND_USD2020_TO_EUR2020_WITH_FROZEN_TECHNOLOGY_DECLINE`）。即作者有意用 AEO8 东盟成本替换了 technology-data 的欧洲成本：**风电投资比 technology-data 低约 3%，光伏投资比 technology-data 高约 2.9 倍。** 这是作者的科学选择，是否沿用属用户决定（见"遗留"）。
- 参考网络用的是 2030 电力成本（onwind 123,791 EUR/MW/a），D 阶段用 2050 成本（114,912），两者差 7%，方向对风电有利，不能解释 0 装机。

### 4. 平准化成本（用模型实际参数：`(capital_cost + marginal_cost×CF×8760)/(CF×8760)`）
| | 全国均值 CF 下的 LCOE（EUR/MWh） | 最优节点 LCOE |
|---|---|---|
| onwind | ID 775、MY 656、TH 353、VN 471、PH 181 | **PH 51.7**、ID 66.1、VN 101.8、LA 106.3、TH 119.6 |
| offwind-dc | VN 94、PH 多数节点 inf（CF=0 节点） | **VN 63.8**、PH 88.0、ID 103.3 |
| solar-utility | 全国 53–65 | 50.9–61.0 |
| solar rooftop | 42–52 | 40.9–49.0 |

除菲律宾最佳陆上节点（51.7）和越南最佳海上节点（63.8）外，风电 LCOE 高于光伏。LCOE 不是 LP 的决策依据，但量级说明：在无碳约束、燃气 CCGT 边际成本约 43 EUR/MWh（燃料 24.57/0.57）且光伏 ~55 EUR/MWh 的系统里，风电只在极少数节点有机会，而这些节点的光伏+存量火电足以满足需求。

### 5. 是否有约束或配置把风电挡掉
- 242 个风电候选 `p_nom_extendable=True`（D 阶段 242/242；参考 242/269，其余 27 个是不可扩展的现有机组）。
- `GlobalConstraint` 只有 `lv_limit`（输电量），没有针对风电的 `max_growth`（`inf`）、无 land-use 二次约束、无资源组限制（`existing_resource_groups` 为空）。
- carriers 的 `co2_emissions=0`，`max_relative_growth=0`（未激活）。
- 可再生边际成本来自冻结配置：onwind/offwind 0.015、solar 0.01 EUR/MWh（`ASSEMBLY_V1_EXPLICIT_CONFIG_VARIABLE_COST`），对结果无影响。
- **D 阶段模型与参考模型的关键差别**：D 阶段 `policy_enabled=false`（无碳预算、无碳价），化石燃料无限量、价格冻结；参考模型是作者的 `DEC` 情景（有碳约束）。参考模型在有碳约束时建了 9.1 GW 风电（越南 4.7 GW 陆上 + 1.1 GW 海上、泰国 2.2 GW、菲律宾 0.8 GW），这与第 2 项的容量因子分布一致。

### 6. 外部参考（容量因子）
- **未核实。** 本轮联网检索（2026-10-15）未取得 IRENA 或 Global Wind Atlas 对越南/泰国/菲律宾/印尼/马来西亚的国家级陆上风电容量因子数值：IRENA《Renewable Power Generation Costs in 2023》有"Table 2.2 Country-specific average capacity factors for new onshore wind, 2010, 2022, 2023"，但表内数值未出现在检索结果中；Global Wind Atlas 3.3 提供 IEC1–3 级别、100 m 轮毂高度的容量因子图层，需在站点按国家导出。全球加权平均（IRENA 2023 执行摘要）：新建陆上风电 2010 年 27% → 2023 年 36%，仅作量级参照，不是东盟数值。按指令不做估算。
- 来源：
  - [IRENA, Renewable Power Generation Costs in 2023 — Executive Summary](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2024/Sep/IRENA_Renewable_power_generation_costs_in_2023_executive_summary.pdf)
  - [IRENA, Renewable Power Generation Costs in 2023（完整报告，Table 2.2）](https://policycommons.net/artifacts/16633582/renewable-power-generation-costs-in-2023-wwwirenaorg/17518435/)
  - [IRENA, Renewable Power Generation Costs in 2024](https://www.irena.org/Publications/2025/Jun/Renewable-Power-Generation-Costs-in-2024)
  - [Global Wind Atlas — Key Features](https://globalwindatlas.info/about/KeyFeatures)
  - [DTU: Global Wind Atlas 3.3 released（IEC 级容量因子图层）](https://wind.dtu.dk/newsarchive/2023/06/global-wind-atlas-3-3-released)
  - [GEM Asia Gas Tracker 2024 methodology（区域性假设 CF 0.26，非国家数值）](https://www.gem.wiki/Asia_Gas_Tracker_2024_Report_Methodology)

## 判定

**经济上合理**（针对 D 阶段研究模型）：风资源在绝大多数节点很差（模型内 CF），加上无碳约束与无限量冻结价格化石燃料，不建风电是模型的正常选择。参考模型在有碳约束下建了 9.1 GW，说明候选结构和出力曲线本身能够被选中。

**需要用户注意的两点（非错误，待决定）：**
1. 作者用 AEO8 成本覆盖了 technology-data 的风电/光伏成本（光伏投资约为 technology-data 的 2.9 倍、风电略低），这是作者选择；新口径下是否沿用 AEO8 成本，或改回 technology-data，需要决定（影响风光相对竞争力）。
2. 出力曲线（`p_max_pu`）的质量未核实：陆上风电全国均值 0.02–0.06 远低于常见的新建机组水平（IRENA 全球加权均值 36%，非东盟值）。这是 atlite/ERA5 在东盟低风速区的典型结果，还是选址/轮毂高度/功率曲线设置问题，需要 R12 第二部分用外部数据核对；本轮未取得国家级外部值，不下结论。
