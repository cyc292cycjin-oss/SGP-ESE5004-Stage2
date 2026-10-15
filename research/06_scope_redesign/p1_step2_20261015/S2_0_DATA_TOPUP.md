# S2-0 数据层补齐（S2 补充指令 01，第 50–54 项；2026-10-15）

分支 `codex/s2-co2-biomass-demand-20261015`（自 D1 分支 8f977156 开出）。本步只改数据登记与加工文件，不建网络、不求解。新数据来自 `work/p2_data_intake/raw5/`（EDGAR 2025、USGS MCS 2025）与 `raw6/`（UNSD 能源平衡 2019 四国导出、JRC98626），哈希见 `SHA256SUMS_raw5.txt`、`SHA256SUMS_raw6.txt`，来源说明见 `SOURCE_MANIFEST.md` 第五、六批。登记规则与 D1 相同。

## 0.1 technology-data 升级到 v0.15.0（第 50 项）

- 版本：标签 `v0.15.0` → 提交 `07e43575c7996a988c60964d00772376ab9bd10c`（GitHub API `refs/tags/v0.15.0`）；发布资产 `outputs/costs_2050.csv` SHA256 `244c8f9ed3a5b8b0…`（完整值见登记表 `technology_data_v0_15_0_costs_2050_sha256`）；源码包 SHA256 `c4787c1d…`。
- 货币基年：`config.yaml` 第 18 行 `eur_year: 2025`；发布说明 v0.14.0 "Changed currency year from 2020 to 2025 … using updated Eurostat inflation rates"，v0.15.0 "currency_year column now reflects the inflation adjusted currency year"。376 个货币行中 374 行为 2025 年价，另 2 行为 2020（commodity）、2019（pelletizing cost），按各自年份回算。与指令假设一致（2025），无需以文档为准另作说明。
- 换算：欧元区 EA20 GDP 平减指数，ECB Data Portal 序列 `MNA.A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N`（2020 = 100；文件 `research_inputs/prices/sources/ECB_EA20_GDP_DEFLATOR.csv`，SHA `77a6cea5…`，取值 2019 98.22096、2020 100、2025 120.01983）。EUR2025→EUR2020 = 100/120.01983 = 0.833196。非货币行不变。
- 注意：technology-data 自身用 Eurostat HICP 把 2020 年价膨胀到 2025（约 +25.7%），而本层用 GDP 平减指数回算（+20.0%），因此来源未变的数值回算后仍比 v0.13.2 高约 4.8%（如电解槽 1,000 → 1,047.6 EUR2020/kW）。这是指数选择差异，已登记（`cost_layer_index_mismatch_note`），未人为抹平。
- 产出：`research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/`：`costs_2050_EUR2020.csv`（长表，含 `value_v0_15_0`、`conversion_factor`、`source_currency_year`）、`costs_2050_EUR2020_prepared.csv`（宽表，年化：fixed = (annuity(寿命, 7%) + FOM/100) × investment；marginal = VOM + fuel/效率；与上游 `process_cost_data.prepare_costs` 同式，DAC 行核验一致）、`LAYER_MANIFEST.json`、`COMPARISON_v0.13.2_vs_v0.15.0_EUR2020.csv`。
- 配置：`research.cost_layer.active = technology_data_v0_15_0_2050_eur2020`（主算）；`technology_data_v0_13_2_2050`（D1 主算）与 `aeo8_author_rule_2050` 保留为敏感性；SMR 仍取 AEO8（第 46 项）。

**主要技术差异（2050，EUR2020）**

| 技术 | 参数 | v0.13.2 | v0.15.0 原值（EUR2025） | v0.15.0 → EUR2020 | 变化 |
|---|---|---|---|---|---|
| 光伏（utility） | 投资 EUR/kW | 292.6 | 367.9 | 306.5 | +4.8% |
| 陆上风电 | 投资 EUR/kW | 1,019.1 | 1,286.5 | 1,071.9 | +5.2% |
| 海上风电 | 投资 EUR/kW | 1,523.9 | 1,916.1 | 1,596.5 | +4.8% |
| 海底 HVDC | 投资 EUR/MW/km | 1,008.3 | 2,680.0 | 2,233.0 | +121.5%（DEA 2025 输电数据更新） |
| 海底 HVAC | 投资 EUR/MW/km | 无 | 3,750.0 | 3,124.5 | 新增 |
| 核电 | 投资 EUR/kW | 8,594.1 | 10,805.7 | 9,003.3 | +4.8% |
| 核燃料 / 铀 | EUR/MWh_th | 3.41 | 7.45 | 6.21 | +82.0% |
| 电解槽 | 投资 EUR/kW | 1,000.0 | 1,257.3 | 1,047.6 | +4.8% |
| 电池储能 | 投资 EUR/kWh | 79.8 | 100.3 | 83.6 | +4.8% |
| DAC | 投资 EUR/(tCO₂/h) | 4,000,000 | 5,029,338 | 4,190,423 | +4.8% |
| CO₂ 管道（陆上/海底） | 投资 EUR/(tCO₂/h)/km | 2,116.4 / 4,232.9 | 2,671.6 / 5,343.2 | 2,226.0 / 4,451.9 | +5.2% |
| 燃料：气 / 煤 / 油 | EUR/MWh_th | 24.57 / 9.55 / 52.91 | 22.76 / 6.72 / 40.86 | 18.96 / 5.60 / 34.05 | −22.8% / −41.4% / −35.7% |

完整对比（48 项技术 × 7 参数）在 `COMPARISON_v0.13.2_vs_v0.15.0_EUR2020.csv`；Fischer-Tropsch 在 v0.15.0 中单位重构（EUR/MW_FT → EUR/kW_FT/year，效率 0.80 → 0.75，寿命 20 → 25），S2-1 使用时需按新单位处理。v0.15.0 仍没有地热发电的投资/效率/VOM 行（只有 `geothermal` 的 FOM、寿命、CO₂ 强度），按第 52 项改用 AEO8（S2-1 登记）。

## 0.2 城市垃圾有机部分改走沼气（第 51 项）

- 删除"有机质量 × 11.6 GJ/t 直接燃烧"口径；新品类 `msw_organic_biogas`（feedstock_group = biogas）。
- technology-data v0.15.0 的沼气条目（`biogas`、`biogas CC`、`biogas upgrading`、`digestible biomass`）只有成本与效率，没有每吨垃圾的沼气产率；故按来源顺序第 2 条用 IPCC 2006 第 5 卷：CH₄ = 湿重 × DOC（表 2.4，湿基：食物 0.15 [0.08–0.20]，园林 0.20 [0.18–0.22]）× DOCf 0.5 × MCF 1（密闭厌氧消化）× F 0.5 × 16/12（第 3 章式 3.2–3.3）；甲烷低位热值 50.04 GJ/t（NIST WebBook 燃烧焓 −890.8 kJ/mol 扣除水汽化焓推导）。**产率按湿重计算**；食物垃圾 0.05 tCH₄/t 湿重 = 2.50 GJ/t，园林 0.0667 tCH₄/t。C 级，低/高取 DOC 区间。
- 结果（PJ 沼气/年，2050，主算）：ID 95.1、TH 54.5、VN 45.3、PH 39.6、MY 29.9、MM 27.1、KH 9.9、SG 0.8、TL 0.5、BN 0.4（合计约 303 PJ；高值按 DOC 上限约 398 PJ）；老挝无成分数据，仍 DATA_PENDING。进入沼气路线（沼气提纯并入天然气），不进固体生物质母线。

## 0.3 工业过程排放（EDGAR 2025）

- 来源：`extraction/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv`（93 行，kt CO₂，2019/2024；原始 `raw5/IEA_EDGAR_CO2_1970_2024.zip` SHA `da129df6…`，表 "IPCC 2006"，CC BY-NC-ND 4.0）。映射：2.A.1–2.A.4 → 非金属矿物；2.B → 化工；2.C → 金属。B 级（直接来源 + 口径映射）。D1 的 55 行 `process_emissions_*`/`industrial_output_*` DATA_PENDING 全部关闭（实物产量不再需要，USGS 仅作交叉核对：ID 水泥 0.44、VN 0.39 tCO₂/t，量级合理）。
- 2019 过程排放（Mt）：非金属矿物 ASEAN 117.7（VN 43.9、ID 30.1、TH 17.0、PH 11.3、MY 8.0、KH 3.0、LA 2.1、MM 2.1、BN 0.1、SG 0.04）；化工 48.6（ID 16.0、TH 12.0、SG 10.4、MY 8.0、VN 2.2）；金属 7.5（ID 5.7、VN 1.1、MY 0.4）。
- 增长：2050 = 2019 × D1 国家工业乘数（AEO8 BAS 工业总量、GDP 分配；ID 3.37、VN 4.97、TH 2.21、PH 4.50、MY 2.85、KH 5.62、LA 3.95、MM 2.17、SG 2.05、BN 1.92、TL 3.22）；低值 = 2019 常数，高值 = 人口法乘数。文件 `registry_v5/PROCESS_EMISSIONS_2019_2050.csv`。
- **与化工原料碳的边界（方法问题，提交用户确认）：** EDGAR 2.B（化工过程）、2.D（燃料非能源产品）、4.C 化石部分（垃圾焚烧）属于原料碳口径——PyPSA-Eur 方法把"naphtha for industry"的进料碳记为蒸汽裂解过程排放 + 非封存 HVC 最终排放（`prepare_sector_network.py` 第 4690–4800 行）。因此本步只把 2.A 与 2.C 装入过程排放母线；2.B/2.D/4.C 登记为 REFERENCE_ONLY，由 S2-4 的原料碳核算覆盖，二者不重叠。检验：新加坡 2.B = 10.36 Mt，而按 UNSD 非能源用途全部碳含量计的原料碳潜在排放 20.18 Mt（石脑油 73.0 TWh 等）；差额对应出口化工产品所含碳。各国边界表 `FEEDSTOCK_CARBON_BOUNDARY_2019.csv`（ID 22.5 vs 2.B 16.0；TH 66.5 vs 12.0；MY 33.4 vs 8.0 Mt）。取"全部原料碳最终排放"（PyPSA-Eur 默认，封存比例 0）会使净零比 EDGAR 口径严格得多——这是 S2 报告中的待确认方法问题。
- 过程排放捕集：沿用上游结构（过程排放母线 → 过程排放 CC → `co2 stored`），S2-2 实现。
- 逸散排放（1.B）：因子 = EDGAR 2019 1.B ÷ UNSD 2019 国内产量（B 级）：煤 ID 0.00095、VN 0.00142、PH 0.00213 tCO₂/MWh；油气 VN 0.00633、TH 0.00513、MY 0.00445、ID 0.00392、PH 0.00334、TL 0.00109、MM 0.00024。产量为 0 的国家（KH/LA/SG 油气、SG/TL 煤）因子不适用，排放量登记为参考。文件 `FUGITIVE_EMISSION_FACTORS_2019.csv`。
- 钢铁基年工艺结构：未建模需要；若 S2 需要，列 DATA_PENDING（worldsteel Steel Statistical Yearbook 2019），已入下载清单。
- **1.A 核对**（`EDGAR_1A_VS_UNSD_2019.csv`；模型侧 = D1 基年燃料 × technology-data CO₂ 强度；国际舱燃料两侧均不含；1.A.1 电力与炼油无 D1 对应项，仅列出）：工业 1.A.2 偏差 ID −1.6%、MY −13%、TH −25%、PH −26%、VN +10%、SG +13%、KH +55%、TL −100%（UNSD 无工业燃料行）；交通 1.A.3 偏差 ID **−65%**（52 vs 148 Mt）、VN **−48%**、其余 ±13% 内；居民/商业/农业 ID **+180%**（80 vs 28.5 Mt）、LA +583%、KH +39%、其余 ±25% 内。印尼与越南的 UNSD 2019 基年在交通与建筑之间的分配与 EDGAR 明显不一致（与 D1 发现的 AEO8-2022/UNSD-2019 交通比值 1.447 相符），按规则只报告，不调参。

## 0.4 国际燃料舱（第六批）

- BN、KH、LA、TL 2019 年国际海运舱燃料 = 0（UNSD 能源平衡显示无流量 "---"），A 级，来源 `extraction/UNSD_EB_2019_BUNKERS_BN_KH_LA_TL.csv`（原始 `raw6/UNSD_EB_2019_{BN,KH,LA,TL}.csv`）。D1 的 4 行 `demand_bunker_pending_*` 关闭，需求表中这 4 行为 SOURCE_ZERO。
- 四国国际航空舱燃料比对（能源平衡 TJ → MWh vs 研究层 UNSD 导出）：BN 1,324,722 vs 1,324,700（+0.002%）、KH 1,907,222 vs 1,907,300（−0.004%）、LA 443,333 vs 443,500（−0.04%，UNSD 估计值）、TL 35,833 vs 35,800（+0.09%，估计值）；差异为 TJ 取整，未改数。

## 0.5 林业残余（第 54 项）

- 伐木残余：主算记 0（ZERO_BY_DECISION；IRENA 2022 第 41、63、84、105 页只计人工林与加工残余；第 32 项）。11 行 `biomass_potential_*_logging_residues` 不再是 DATA_PENDING。
- 高生物质敏感性：FAOSTAT FO 工业原木 2019–2023 均值 × FAO/APFC 2001 表 7 残余系数（KH/ID/LA/MY 2.0、MM/VN 1.5、PH/TH 1.0；BN/SG/TL 用"约 55% 回收率"→ 0.818）× JRC98626 表 A3-3 可提取 67%（坡度 ≤35%）× 9.14 GJ/m³（UNSD）；FAO 2001 "10% 经济可用"作为另一参考。高值（PJ）：ID 1,074、VN 396、MY 181、TH 89、MM 40、PH 24、LA 20、KH 3.9、BN 0.4、SG/TL 0（无工业原木产量）。
- 木材加工残余（7 国）：残余 = 锯材 ÷ 出材率 − 锯材 + 胶合板 ÷ 出材率 − 胶合板；产量取 FAOSTAT FO 2019–2023 均值；出材率取 FAO 2001 表 12/13 分国值（KH 50/47%、LA 40/47%、MM 40/47%、PH 50/47%，B 级），BN/SG/TL 用表 9 的 10 国均值 50.8/46.9%（C 级）；收集率 90%。结果（PJ）：MM 22.3、PH 5.7、LA 4.6、KH 3.7、BN 0.2、SG 0.02、TL 0.004。ID/MY/TH/VN 仍用 FAOSTAT "Wood residues" 直报值（ID 3.2、MY 11.5、TH 49.4、VN 5.3 PJ），并附推导值交叉核对。
- 厂内自用与重复计算：UNSD 2019 只有泰国一行"Fuelwood – Consumption by wood and wood products"（33.1 千 m³），其余国家无木材工业生物质自用行；木材加工厂自用本来就包含在 D1 的工业生物质需求（`IndustryFinalEnergy biomass`）中，而该需求将从同一国家生物质母线取用，所以供给侧**不再扣减**（否则重复扣除）。已登记 `biomass_wood_residue_own_use_treatment`。

## 关闭的 DATA_PENDING 项（98 → 22）

| 组 | 行数 | 处理 |
|---|---|---|
| process_emissions_* / industrial_output_* | 55 | EDGAR 2025 填补（B 级）；实物产量不再需要 |
| biomass_potential_*_logging_residues | 11 | 按决定记 0（ZERO_BY_DECISION），高值敏感性 |
| biomass_potential_*_wood_processing_residues | 7 | FAO 2001 出材率推导 |
| demand_bunker_pending_* | 4 | UNSD 能源平衡 = 0（A 级） |

仍为 DATA_PENDING（22）：LNG 无容量单元 9、油棕树干成本 5、地热发电投资/效率/VOM 3（S2-1 按第 52 项用 AEO8 登记）、LA/MM 封存评估 2、LA 垃圾成分 1、LNG 再气化加价 1、钢铁工艺结构 1。下载清单更新为 `DOWNLOAD_LIST.csv`（7 项），已关闭项记录在 `DOWNLOAD_LIST_CLOSED_S2_0.csv`。

## 文件与测试

- 脚本：`scripts_project/s2_0_cost_layer_v015.py`、`s2_0_process_emissions.py`；修改 `d1_biomass.py`（0.2、0.5）、`d1_demand_2050.py`（0.4）、`d1_registry.py`、`d1_common.py`（新增状态 ZERO_BY_DECISION、EA20 平减指数读取）；配置 `configs/research/baseline.yaml`。
- 登记表 `DATA_REGISTRY.csv` 937 行（A 204 / B 471 / C 262；REGISTERED 692、REFERENCE_ONLY 80、SENSITIVITY 55、SOURCE_ZERO 53、CANDIDATE_ONLY 24、DATA_PENDING 22、ZERO_BY_DECISION 11）。
- 测试：`tests/research/test_d1_registry.py` 13 项（新增 v0.15.0 回算与过程排放两项）。
