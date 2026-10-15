# 第六批：四国国际燃料舱与林业残余参考资料

原始文件在 `raw6/`，SHA256 见 `SHA256SUMS_raw6.txt`。为了路径稳定，文件已重命名，原文件名见第 3 节。

## 1. 四国 2019 年国际燃料舱（UNSD 能源平衡，单位 TJ）

**来源：** UNSD Energy Balance Visualization 的 "Energy Balances" 页导出，https://unstats.un.org/unsd/energystats/dataPortal/ 。表中 `---` 表示没有该项流量，`*` 表示 UNSD 估计值。抽取结果在 `extraction/UNSD_EB_2019_BUNKERS_BN_KH_LA_TL.csv`。

| 国家 | 国际海运燃料舱 | 国际航空燃料舱（油品） |
|---|---|---|
| BN | 无（`---`） | 4,769 TJ = 1.32 TWh |
| KH | 无（`---`） | 6,866 TJ = 1.91 TWh |
| LA | 无（`---`），内陆国 | 1,596 TJ*（估计）= 0.44 TWh |
| TL | 无（`---`） | 129 TJ*（估计）= 0.04 TWh |

**结论：**
- 四国国际海运燃料舱按 UNSD 平衡表记为 0（A 级）。D1 的 4 行 `demand_bunker_pending_*_InternationalShippingBunker` 从 DATA_PENDING 改为 0，可以关闭。
- 这与 D1 导出中"没有交易行"一致：UNSD 的平衡表本身就没有这项流量，而不是数据缺失。

**给 S2 的核对任务：** 用航空燃料舱的四个数，和研究层 UNSD 2019 导出中这四国的航空燃料舱逐一比对，确认两边口径一致。如果不一致，报告差异，不改数。

## 2. 林业残余：JRC98626 报告不提供可迁移的系数

**文件：** `raw6/JRC98626_biomass_potentials_in_europe_web_rev.pdf`，即 Ruiz et al.（2015）*The JRC-EU-TIMES model. Bioenergy potentials for EU and neighbouring countries*，ENSPRESO 生物质的方法学报告，共 176 页。

**核查结果：**
- 报告的伐木残余由 EFISCEN 欧洲林分模型逐区域模拟得出（第 36–37 页），没有给出可以独立使用的"残余/原木"比，因此不能迁移到东南亚。
- 报告只提供可持续采收约束，例如附录表 A3-3、A3-4：坡度 ≤35% 时回收率 67%；泥炭地 0%；保护区 0%。这些可作为 C 级参考，用于高情景的可收集比例。

**IRENA 2022 的立场（`raw/IRENA_Biomass_Energy_Transition_2022.pdf`）：**
- 第 41、63、84、105 页对 ID、TH、VN 等国都写明："只计人工林木质生物质。天然林采伐的木材是否可持续，需要更深入的分析。"
- D1 第 172 行已经采用这一原则，即"只计人工林与加工残余，天然林与现有薪柴不计"。
- FAOSTAT 的工业原木产量不区分天然林和人工林，所以无法按"产量 × 系数"只取出人工林的伐木残余。

**东南亚本地的系数来源（备选）：** FAO 与亚太林业委员会（2001）*Trash or treasure? Logging and mill residues in Asia and the Pacific*，链接 http://www.fao.org/docrep/003/x6966e/X6966E02.htm 。该文是 IRENA 2017 引用的文献，给出了分国家的锯材和胶合板出材率，例如 ID 锯材 46–54%、MY 52%、PH 48%、LA 30–40%、MM 30–40%，其余国家假设 50%。它可以用来推算 FAOSTAT 缺少"木材残余"产量的 7 个国家的加工残余：加工残余 = 锯材产量 ÷ 出材率 − 锯材产量。

**建议（见《决策清单》第 54 项）：**
- **主算：** 伐木残余记 0，遵循 IRENA 2022 和第 32 项。
- **加工残余：** 7 个缺数的国家用 FAO 2001 的出材率推导（B 级）。
- **高生物质敏感性：** 加入伐木残余，系数取 FAO 2001 或 IPCC 2006 第 4 卷第 4 章的热带系数（C 级），回收率取 JRC 的 67%。

## 3. 原文件名对照

| 新文件名 | 用户上传的原文件名 |
|---|---|
| raw6/UNSD_EB_2019_BN.csv | Brunei Darussalam-2019.csv |
| raw6/UNSD_EB_2019_KH.csv | Cambodia-2019.csv |
| raw6/UNSD_EB_2019_LA.csv | Lao People's Democratic Republic-2019.csv |
| raw6/UNSD_EB_2019_TL.csv | Timor-Leste-2019.csv |
| raw6/JRC98626_biomass_potentials_in_europe_web_rev.pdf | biomass potentials in europe_web rev.pdf |
