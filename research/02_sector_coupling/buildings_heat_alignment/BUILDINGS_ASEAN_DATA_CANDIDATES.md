# ASEAN Buildings 候选数据（未采用）

按 ASEAN/AEO→国家统计→国际/官方end-use来源作有界搜索；没有拼接11国新表。原始PDF/HTML已保留在 `data/raw/buildings/`，URL、下载时间、字节数及SHA256在[下载manifest](data/raw/buildings/RETRIEVAL_MANIFEST.json)；Git保存manifest和获取脚本，二进制单独缓存。所有候选UNVERIFIED、human acceptance=PENDING。

## 可核实候选及旧—新对照

| 候选 | 旧来源/拟解决问题 | 版本、定义与单位兼容性 | 覆盖与预计影响 | 当前结论 |
|---|---|---|---|---|
| [ACE AEO8](https://www.aseanenergy.org/publications/the-8th-asean-energy-outlook/) | 无ASEAN依据的fuel/end-use defaults | 2024出版，独立保存November 2024 corrigendum；Mtoe/final-energy及预测appliance shares，不是useful heat观测。当前下载本与勘误分开登记，不默认宣称已是修订本 | ASEAN10，未覆盖TL；可校验用途重要性及未来情景口径 | 来源族优先候选；不能直接替代2019端用途数据 |
| [印尼ESDM HEESI 2019](https://www.esdm.go.id/assets/media/content/content-handbook-of-energy-and-economic-statistics-of-indonesia-2019.pdf) | UNSD原始居民商品与数量交叉核验 | 2019 edition，2020发布；Table5.2.1原单位，5.2.2 thousand BOE，5.2.3份额；不能把不含biomass的份额当全燃料份额 | ID；可能显著改变当前被送入space/water的油品基数 | 同年定义/数值冲突未解决；不选赢家、不覆盖 |
| [柬埔寨MME/ERIA统计](https://www.eria.org/uploads/media/Research-Project-Report/RPR-2022-08/Cambodia-Energy-Statistics-2019-2020.pdf) | 同年全国R/S燃料平衡核验 | 正式标题2000–2019，September2022，RPR2022 No.08；原单位及ktoe，Annex A-20为2019。报告说明部分年份部门油耗按既有统计估计 | KH；不能与未经审查的其他国家来源直接拼接 | 数据候选；不是全部实测，也不是useful heat表 |
| [NEA 2017家庭用能调查](https://www.nea.gov.sg/media/news/news/index/four-in-five-households-motivated-to-save-energy-if-they-can-save-money-nea-study) | 核验direct electricity中的冷/热用途边界 | 2018-05-05发布；2017典型家庭electricity份额，AC24%、water heater11%；不是2019全国全部R/S分解 | SG居民样本；可识别需要扣分的用途类别 | 验证结构、提供子集候选；不外推11国 |
| [ACE/IEA空间制冷路线图](https://aseanenergy.org/publications/roadmap-towards-sustainable-and-energy-efficient-space-cooling-in-asean/) | 检查制冷是否可忽略/属于电力 | 官方页面6June2022、作者IEA；本轮保存landing，未取得可用11国R/S年度表 | ASEAN区域背景；不改变cooling固定在direct electricity的边界 | 来源元数据/边界证据候选，不是新模型输入 |
| [IEA end-use indicators](https://www.iea.org/data-and-statistics/data-product/energy-end-uses-and-efficiency-indicators) | 潜在统一end-use补充源 | June2026产品元数据，2000–2024，按能源产品/end-use的final energy；不等于useful heat。完整数据未下载 | 国家覆盖不均；本轮未核实ASEAN11国完整性，也未购买数据 | 国际候选备选；不得假定已有统一可用表 |

文件名、具体hash、用途与转换脚本逐项见[登记CSV](BUILDINGS_DATA_REGISTRY.csv)。PDF页码以下均从1开始，另给印刷页码；[可复核页定位](evidence/PDF_LOCATION_CHECKS.json)。

## 两个足以阻止“默认接受”的具体证据

**1. 烹饪不能先假定很小。** AEO8下载本PDF第69页/印刷67页，Figure3.12列出的BAS 2050烹饪占比为54.8%；这是**2050预测**，不是2019实测。图下注明2022历史终端细分不能报告，细分从2023预测开始。因此它支持“不能忽略用途边界”的判断，但不能生成11国2019采暖/热水表。商业端用途同样见PDF第71页/印刷69页。[AEO8](https://www.aseanenergy.org/publications/the-8th-asean-energy-outlook/)

**2. 印尼当前居民oil并非一个已核实的建筑热燃料集合。** 本地UNSD原始行经原模型因子换算：motor gasoline 16011.611千吨→196.9428153 TWh；LPG6610.02千吨→86.7895626 TWh；柴油527.813千吨→6.30208722 TWh。合计290.0345 TWh（base表舍入）。这些只是模型转换值，未验HHV/LHV。[可追溯原行/转换](data/processed/buildings/UNSD_2019_BUILDINGS_CLASSIFIED.json)

ESDM同年Table5.2.1（PDF41/印刷46）为居民LPG7447千吨、电力103016 GWh；本地UNSD为LPG6610.02千吨、电力104714 GWh。ESDM定义（PDF94/印刷116）居民能耗排除私人汽车。差异可能来自修订、部门统计范围或上报口径；**本轮不能判定原因，也不能把汽油记录直接移到别的部门**。它足以说明 DEFAULT `h_oil=.6667` 不能未经核实就作用于全部居民oil并解释为space/water。[ESDM官方原表](https://www.esdm.go.id/assets/media/content/content-handbook-of-energy-and-economic-statistics-of-indonesia-2019.pdf)

## 候选接受前最小决策表

| 事项 | 必须共同确认 | 不可自动做 |
|---|---|---|
| 统一来源 vs 国家子集 | 是否采用国家异质源；若采用，定义、年份、缺失和转换如何统一 | 用ID/KH/SG悄悄补齐11国 |
| Cooking | 保持不建独立模块；如何使其电力/燃料只记一次，并不被当成space/water | 宣称其对互联收益可忽略，或新增cooking优化模块 |
| 有用热与燃料 | 各用途燃料/电热基数、η或COP、HHV/LHV与最终服务口径 | 直接把所有fuel TWh变成heat service TWh |
| 数据版本 | 固定原文件hash，记录选择理由和是否含corrigendum | 用官网较新文件覆盖P/T输入 |
| 研究范围 | 无stock时是否明确greenfield；DH是否需要地区限定 | 把缺资料视为真实0，自动开关DH |

November2024勘误已单独获取；其列出的页码中没有上述印刷67/69页终端用途说明。仅检查与本轮Buildings主张有关的版本影响，不实施勘误涉及的其他部门或政策变化。
