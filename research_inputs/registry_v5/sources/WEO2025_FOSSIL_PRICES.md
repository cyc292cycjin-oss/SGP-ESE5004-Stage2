# WEO 2025 化石燃料价格 / CO2 价格提取

- 输入文件：`/mnt/user-data/outputs/p2_data_intake/raw2/WorldEnergyOutlook2025.pdf`（IEA, World Energy Outlook 2025，519 页）
- SHA256：`ebee58b6b93d6aed43db5247d54b03a7248510c2986bd24cfb4cca59d339b8f4`
- 提取方法：`pdftotext -layout -f N -l N`；本 PDF 的 PDF 页码 = 印刷页码（已在 p108/109/111/459 核对页脚）。
- 机读版：`WEO2025_FOSSIL_PRICES.csv`（同目录，长表，含 Table 2.3 与 Table B.6 全部单元格）
- 原则：仅抄录印刷值；未出现者写 "not reported"。

## 1. Table 2.3 Wholesale fossil fuel prices by scenario（PDF p109 / 印刷 p109）

价格基准（原文）：**USD (MER, 2024)**，即 2024 年实际美元、市场汇率。

| 项目 | 单位 | 2024 | CPS 2035 | CPS 2050 | STEPS 2035 | STEPS 2050 | NZE 2035 | NZE 2050 |
|---|---|---|---|---|---|---|---|---|
| IEA crude oil | USD/barrel | 79 | 89 | 106 | 80 | 76 | 33 | **25** |
| Natural gas – United States | USD/MBtu | 2.2 | 4.5 | 5.0 | 3.9 | 4.6 | 2.1 | 2.2 |
| Natural gas – European Union | USD/MBtu | 10.3 | 9.1 | 10.6 | 6.5 | 8.4 | 4.2 | 4.0 |
| Natural gas – China | USD/MBtu | 10.3 | 9.9 | 11.2 | 7.5 | 9.1 | 4.9 | 4.8 |
| Natural gas – Japan | USD/MBtu | 13.5 | 11.2 | 12.9 | 8.4 | 9.7 | 4.9 | **4.9** |
| Steam coal – United States | USD/tonne | 56 | 56 | 53 | 41 | 41 | 25 | 23 |
| Steam coal – European Union | USD/tonne | 112 | 92 | 82 | 78 | 66 | 47 | 39 |
| Steam coal – Japan | USD/tonne | 151 | 112 | 105 | 100 | 84 | 57 | **49** |
| Steam coal – Coastal China | USD/tonne | 131 | 115 | 105 | 99 | 84 | 59 | **49** |

表注要点（原文转述，p109）：
- IEA crude oil = IEA 成员国进口价加权平均。
- 天然气价格为加权平均，**gross calorific value（GCV/高位热值）**基准；US = 国内批发价；EU、China = 管道气 + LNG 进口的加权；**Japan = 纯 LNG 进口价**；LNG 价格为"customs border prior to regasification"（再气化前的关境价）。
- 动力煤：调整至 **6 000 kcal/kg**；US = 坑口价 + 运输装卸；Coastal China = 进口与国内销售加权；EU、Japan = 纯进口价。
- **Wholesale prices exclude any emissions pricing applied at the point of use**（批发价不含使用端碳价）。
- 表中仅有 2024、2035、2050 三个年份（无 2030/2040）。

## 2. 是否有东南亚 / 亚洲 LNG 进口专属价格

- Table 2.3 中 **无 Southeast Asia 条目**：Southeast Asia 气价 / 煤价 = **not reported**。
- 最接近"亚洲 LNG 进口国"的条目是 **Japan（纯 LNG 进口，再气化前关境价）**；China 为管道+LNG 混合。
- 文本中唯一的亚洲新兴经济体气价：PDF p72（Ch.1）— "In the STEPS, weighted average gas import prices in emerging market and developing countries in Asia are around USD 7.5 per million British thermal units (MBtu) in the 2030-2035 period, around 40% lower than today." 仅 STEPS、仅 2030-2035，**无 2050、无 NZE 值**（not reported）。

## 3. NZE（及其他情景）价格形成机制（原文要点）

| 燃料 | 机制说明 | 页码 |
|---|---|---|
| 石油 | 油价作为全球供需的平衡机制；NZE 需强政策抵消低价引致的需求反弹；"In the NZE Scenario, oil prices fall to USD 33/barrel by 2035 and USD 25/barrel by 2050 as oil demand declines." CPS 2050 为 USD 106/barrel。 | p108–109 |
| 天然气 | 基准价为供需均衡价，确保新项目可回收 **long-run marginal cost of supply**；供应充裕期可能反映 **short-run marginal cost**。NZE："global demand and prices are both much lower throughout the Outlook period"。示例：EU 2035 STEPS LNG ≈ USD 6.2/MBtu（Henry Hub + 15% uplift + 液化资本回收 + 运费 + 再气化费），油价挂钩 ≈ USD 8/MBtu 以上，加权约 USD 6.5/MBtu。 | p110 |
| 天然气（补充） | CPS 价格接近 LNG 交付的长期边际成本；STEPS 2030s 接近短期边际成本。 | p69, p236 |
| 煤炭 | "In the NZE Scenario, falling demand brings prices down to very low levels: higher cost mines are forced to close, and no new mines are needed." | p110 |

## 4. CO2 价格

### 4a. Table B.6 CO2 prices for electricity in selected regions by scenario（PDF p459 / 印刷 p459）
单位/基准（原文）：**USD (2024, MER) per tonne of CO2**；"Values are rounded."

| 情景 | 地区 | 2035 | 2040 | 2050 |
|---|---|---|---|---|
| CPS | Canada | 70 | 70 | 70 |
| CPS | China | 14 | 14 | 14 |
| CPS | European Union | 87 | 87 | 87 |
| CPS | Japan | 2 | 2 | 2 |
| CPS | Korea | 13 | 13 | 13 |
| STEPS | Canada | 126 | 126 | 126 |
| STEPS | China | 22 | 26 | 34 |
| STEPS | European Union | 89 | 92 | 174 |
| STEPS | Japan | 39 | 61 | 105 |
| STEPS | Korea | 52 | 62 | 75 |
| NZE | Advanced economies with net zero emissions pledges | 180 | 205 | 250 |
| NZE | Selected EMDE*（*Brazil, China, India, **Indonesia**, South Africa） | 125 | 160 | 200 |
| NZE | Other emerging market and developing economies | 25-50 | 35-85 | 55-180 |

- 东南亚：**Indonesia 被明确归入 "Selected EMDE"（NZE 2050 = 200 USD/t）**；其他 AMS 未点名，推定属 "Other EMDE"（此归属为推断，文档未逐国列出）。
- CPS/STEPS 无任何东南亚国家 CO2 价格：**not reported**。
- 表头明确为"for electricity"（电力部门）。

### 4b. 正文中的 NZE 2050 碳价（PDF p111–112）
"Prices reach USD 250 per tonne of carbon dioxide (t CO2) in 2050 for advanced economies, USD 200/t CO2 for selected emerging markets, and USD 55/t CO2 for other emerging market and developing economies"。
- **注意不一致**：正文给 Other EMDE 2050 = USD 55/t（单值），Table B.6 给 55-180（区间）。p112 另注明 CO2 价格"do not represent the marginal cost of abatement"。

## 5. 氢 / 氨进口成本

- 按情景、按地区的氢或氨进口成本/价格表：**not reported**（全文检索 "ammonia"/"hydrogen" + import/price/USD，无此类表）。
- 仅有的相关数值：Table B.5（PDF p457）电解槽投资成本（USD/kW, USD 2024）— NZE 2050 下限 310（China）、上限 1 180（rest of world）；p343 提及开发商宣称地质氢开采成本约 USD 1/kg（非情景假设，属个别公司声明）。均非进口成本。

## 6. 对 PyPSA-ASEAN 使用的提示（非数据，仅标注）
- 无东南亚专属价格；若以 Japan LNG 作亚洲进口气代理，需在模型文档中显式声明为代理选择。
- 单位换算（GCV 基准 MBtu → MWh 等）及 2024 USD → 模型基准年的通胀调整需另行记录，本文件未做任何换算。
