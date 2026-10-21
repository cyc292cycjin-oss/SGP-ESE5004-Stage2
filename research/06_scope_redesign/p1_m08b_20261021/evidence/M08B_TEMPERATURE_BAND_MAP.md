# M08b 温度档映射表（第 133 项；代码 `s2_layers.HEAT_BAND_TECH`，表 `research_inputs/demand_v5/INDUSTRY_HEAT_BAND_TECHNOLOGY_MAP.csv`，注册表 `industry_heat_band_technology_map`）

规则：每一档只用 technology-data v0.15.0 有条目的技术；热泵只在低温档；>400 °C 档只有覆盖该温度的电加热行时才允许电加热（v0.15.0 无此行 → 不建）；氢、甲烷、生物质中，只有有条目的才建（v0.15.0 无任何氢锅炉 / 氢直燃行 → 不建氢供热）。效率与成本取当前成本层（technology-data v0.15.0，EUR2020，HICP 回算）；生物质 + CC = 同一行 + biomass boiler capture × CO₂ 强度 × 捕集率。

| 温度档 | 母线 | technology-data 行 | 链路载体 | 输入 | 效率 | 投资（EUR2020/kW） | FOM（%/a） | VOM（EUR2020/MWh） | 寿命（a） | 温度依据（DEA 工业过程热目录） |
|---|---|---|---|---|---|---|---|---|---|---|
| 低 <150 °C | `{node} industry heat` | electric boiler steam | industry electric boiler | 电 | 0.99 | 70.49 | 1.31 | 0.79 | 25 | 310.1 电蒸汽锅炉 1–16 bar，典型 8 bar / 175 °C |
| 低 | 同上 | industrial heat pump high temperature | industry heat pump | 电 | COP 3.2 | 845.88 | 0.09 | 3.14 | 20 | 302.b 高温热泵，≤150 °C（只用于低温档） |
| 低 | 同上 | gas boiler steam | industry gas boiler | 甲烷 | 0.94 | 45.77 | 3.74 | 1.01 | 25 | 311.1c 燃气蒸汽锅炉，蒸汽 125–300 °C |
| 低 | 同上 | solid biomass boiler steam（+CC） | industry biomass boiler（CC） | 生物质 | 0.90 | 540.12 | 6.28 | 2.87 | 25 | 311.1e 木质蒸汽锅炉，蒸汽 125–300 °C |
| 中 150–400 °C | `{node} industry heat medium` | electric boiler steam | industry electric boiler | 电 | 0.99 | 同上 | | | | 只覆盖约 ≤200 °C（16 bar 饱和）——档内上段无覆盖，列为待审 |
| 中 | 同上 | gas boiler steam | industry gas boiler | 甲烷 | 0.94 | 同上 | | | | 蒸汽 125–300 °C（100 bar 时 311 °C）；300–400 °C 无覆盖，待审 |
| 中 | 同上 | solid biomass boiler steam（+CC） | industry biomass boiler（CC） | 生物质 | 0.90 | 同上 | | | | 同上 |
| 高 >400 °C | `{node} industry heat high` | direct firing gas | industry direct firing gas | 甲烷 | 1.00 | 15.10 | 1.03 | 0.28 | 15 | 312.a 燃气直燃，400–800 °C 与 >800–1,600 °C |
| 高 | 同上 | direct firing solid fuels（+CC） | industry direct firing biomass（CC） | 生物质 | 1.00 | 221.54 | 1.41 | 0.34 | 15 | 312.b 固体燃料直燃（煤 / 生物质多燃料燃烧器），高温过程 |
| 高 | — | （无） | — | 电 | — | — | — | — | — | DEA 2026 版有电直燃 400–800 °C，但 technology-data v0.15.0 无对应行 → 不建 |
| 任一档 | — | （无） | — | 氢 | — | — | — | — | — | technology-data v0.15.0 无氢锅炉 / 氢直燃行 → 不建（与指令"高温只允许氢、甲烷、生物质"的张力，待审） |

注：投资、VOM 为模型所用成本层值（technology-data v0.15.0 costs_2050，经 EEA HICP 回算为 EUR2020，系数 0.79533；原表值见 `value_v0_15_0` 列）；FOM、寿命为原表值；网络中年化成本由成本层计算。温度依据文本来自 DEA《Technology Data for Industrial Process Heat》2026 版（version 0006）；technology-data v0.15.0 的数据取自 DEA 较早版本的数据表，行名中的编号沿用当时编号（302.a/b、310.1、311.1c/e、312.a/b）。
