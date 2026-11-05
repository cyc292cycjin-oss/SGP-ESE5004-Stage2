# W08 实施清单（v4 工业需求与网络层修正；I2 定稿 → 仓库实现）

- **依据：** 决策清单第 203–210 项；I2 报告（`REPORT.md`）与本目录各表。全部条目为 PROPOSED，I2 没有改仓库。
- **基线：** 分支 `codex/v4-i2-20261106`（= `07e08f38` + 9 个 W07 / I1 分支的合并提交）；代码与 v3.1 `d3b9a3bc` 在 `research/` 以外无差异。
- **验收数字的来源：** `tables/I2_STEPS_LONG.csv`（逐步、逐国）、`<CC>_V4_FINAL.csv`、`BIOMASS_POTENTIAL_ADJ.csv`、`tables/I2_PEAK_IMPACT_ASEAN.csv`。I2 的临时副本代码（`scripts/i2_engine.py`、`i2_items.py`、`i2_chain.py`）是 W08 的参照实现：W08 在仓库中实现同一组规则后，**同一输入下逐国 `T_v2` 必须等于 I2 S7 值 ± 1e-6 TWh**（总判据 A0）；若 W08 有意改动某条规则，先在 I2 引擎中加同一改动、给出新参照值，再实施。
- **通用要求：** 每项改动单独提交并附单元测试；每个新输入登记 SHA256 与来源（注册表片段）；未改动路径逐字节复现 v3.1；不跳过 git hooks；求解另行授权。

## 0. 总判据

| 编号 | 判据 | 数值来源 |
|---|---|---|
| A0 | 全部改动后，11 国 2050 年 `T_v2`（`v3_industry.CARRIERS` 12 列，生物质取溢出前）= I2 S7 ± 1e-6 TWh；东盟 3,328.34 TWh | `tables/I2_STEPS_LONG.csv` S7 |
| A1 | 每一步单独实施后的中间状态 = I2 对应步（S1…S7）± 1e-6 TWh（按 W08 的实施顺序，至少 S1、S2、S3、S4、S5、S6、S7 七个检查点） | 同上 |
| A2 | 任何开关关闭时（配置回到 v3.1），`m08b_demand.py`、`s3_0_industry.py` 的 8 个输出与 v3.1 逐字节相同 | I2 复现关（`evidence/I2_base.json`、`I2_repro.json`） |
| A3 | 新增输入文件 SHA256 与注册表一致；`tests/research` 全部通过（worktree 的 2 failed / 63 skipped 基线除外，见记忆说明） | — |

## 1. 2019 基年：UNSD SDMX 当前库与字典（第 210 项第 1 条）

| 项 | 内容 |
|---|---|
| 文件 | 新增 `research_inputs/assembly_v1/sources/SDMX_2019_CAPSULE.json`（由 W12 的 11 个 SDMX 响应生成；I1 `i1_sdmx.py` 的转换规则）、`SDMX_2019_BLEND_MEMO.csv`、SDMX 电力记录；`FROZEN_UPSTREAM_CONVERSIONS.json` 的 `biomass_fuels / oil_fuels / coal_fuels` 增加"其他植物性残渣""其他液体生物燃料""其他油品 n.e.c.""白节油""其他回收气""其他煤制品"；原导出胶囊保留作对照 |
| 函数 | `scripts_project/reconstruct_base_accounts.py`：`Reconstruction.convert` 增加因子模式（SDMX `CONVERSION_FACTOR`，例外表 `ID hard coal 20.29`、`ID coke oven coke 28.20`）；掺混规则通用化（有"其中"备忘量用备忘量，否则最大重叠：I1 `i1_base.blend`）；`d1_demand_2050.py` 读 SDMX 胶囊与 SDMX 电力记录 |
| 改法 | 把 I1 `scripts/i1_base.py` 的 `Recon`、`blend`、`rail_children`、`d1_rows` 移入仓库（不改算法）；热值例外写成配置表（`research_inputs/demand_v5/NCV_EXCEPTIONS.csv`：国家、品种、GJ/t、依据：第 207 / 210 项） |
| 测试 | `test_v4_base_sdmx.py`：(1) 胶囊记录数 2,752、11 个响应 SHA256 与 W12 登记一致；(2) 旧胶囊路径下 G1–G3 三道关通过（273 个账户、375 行 D1 逐字符串）；(3) 新基年 D1 每行 = I1 `BASE2019_SDMX_D1_ROWS.csv` S5 列，唯一例外 ID `NonEnergy:Coke-oven coke` +1,758,943 MWh（791 kt × (28.20 − 20.1947) / 3.6） |
| 验收 | S1 东盟 `T_v2` 3,728.65 TWh；ID 1,761.93、VN 782.40、TH 536.62（± 1e-6） |

## 2. 分行业缓存（第 210 项第 1 条"同步重建"）

| 项 | 内容 |
|---|---|
| 文件 | 新增 `scripts_project/v4_industry_cache.py`，写 `research_inputs/assembly_v1/sources/industry_cache.json` 的 v4 版（或新文件名 + 配置开关） |
| 改法 | I2 `i2_items.sdmx_industry_cells` + `build_cache`：SDMX 121 与 1211–1214O 分行，S5p 折算，煤父项替代子项；"其他" = 1214O + 121 减已报子行的正余量；自用残渣 (a) 的记录同时从子行与 121 总量中去掉；ID 燃料木材按 2010–2017 年均缩放（29,510 千 m³） |
| 测试 | `test_v4_industry_cache.py`：各国各载体缓存和 = D1 工业行（残渣移出后）± 1 MWh；ID 生物质只含燃料木材与木炭；去掉的 (a) 记录清单 = `tables/I2_RESIDUE_A_RECORDS.csv`（由 I2 `meta.json` 导出） |

## 3. 锚构造 IId 与锚边界对齐（第 210 项第 3、4 条）

| 项 | 内容 |
|---|---|
| 文件 | `scripts_project/m08b_demand.py` 第 241–248 行（RAS 之后）；配置 `configs/research/baseline.yaml` 新键 `research.demand.anchor_mode: ras | iid`（默认 `ras` 保持 v3.1） |
| 改法 | IId：σ_s 取 v3 RAS 解（ID 行：工业 2.6186、交通 2.8536、居民 0.7260、商业 2.1101、农业 3.2825，写成冻结表 `DEMAND_ANCHOR_V3_SECTOR_FACTORS.csv`），tfa_cs = A_c × x⁰_cs σ_s / Σ_s x⁰_cs σ_s；**锚扣减**：对平衡表含自用残渣的国家，按"残渣仍在种子中"算部门拆分，再把工业锚减 R_c × m_ind（其余部门锚与全部倍数不变；I2 `i2_engine.M08B_PATCH_BLOCK`）；平衡表覆盖表 `NATIONAL_BALANCE_BIOMASS_COVERAGE.csv`（本步：ID = 不含（HEESI 工业生物质 0.9 TWh），其余 = 与 UNSD 相同，待各国平衡表核定） |
| (b) 项 | ID 平衡表外的工业燃料木材（2010–2017 年均 29,510 千 m³ × SDMX 9.135 GJ/m³ = 74.88 TWh；木炭 0.80、生物柴油 3.70 TWh 在 HEESI 内，留在种子）不进种子，在 ATS 工业生物质行按 **v3 工业倍数 2.6186** 加回（s3_0 用行倍数乘基数，所以基数写 B × m_v3 / m_row，2019 基数另行报告真值） |
| 测试 | `test_v4_anchor_iid.py`：(1) 种子不变时 IId = v3 锚，最大偏差 ≤ 1e-6 TWh（I1：2e-8）；(2) 残渣锚扣减：除工业外各部门锚与 R_c = 0 时相同、全部倍数不变、国家总量减 R_c × m；(3) 东盟部门合计相对 C.3 的偏离写入输出 `DEMAND_ANCHOR_C3_DEVIATION.csv` |
| 验收 | S2 东盟 3,519.59；TH 390.71（残渣 78.3 TWh 2019 移出，锚扣减）；ID 1,755.52 |

## 4. (ii) 类：ID 家庭汽油与铁路父行（第 210 项第 6 条、第 209 项 F2 / F6）

| 项 | 内容 |
|---|---|
| 文件 | D1 账户映射（`reconstruct_base_accounts.py` 账户表 / `d1_demand_2050.py` 第 166–200 行）；`reconstruct_base_accounts.py:225-234`（铁路父 / 子行）；`s2_layers.py:25`（`LAND_TRANSPORT_ACCOUNTS`） |
| 改法 | ID `ResidentialFuel` 车用汽油（S5p 196.94 TWh 2019）移到 `RoadResidualFuel`（MM 479 kt 只作敏感性，开关）；`TransportEmbeddedFuelParent` 不再写入 D1（方案 b），RAS / IId 种子与交通基数都只含 `RailNonElectric` 子行；陆运账户去掉父行 |
| 测试 | `test_v4_transport_accounts.py`：D1 中无父行；ID 居民油品 2019 = S5p 值 − 196.94 TWh；陆运燃料 2050 ID 1,199.87、EV 362.54 TWh（I2 S7 `land_fuel` × 0.30215）± 1e-6 |
| 验收 | S3 东盟 3,347.51；ID 1,581.62；东盟 10 国交通 2050 3,350.0 TWh（对 C.3 × k +26.3 %，单列报告） |

## 5. (i) 类：自备电厂 (b)（第 204 项第 1–2 条；第 208 项）

| 项 | 内容 |
|---|---|
| 文件 | 新增 `research_inputs/industry_v4/CAPTIVE_COAL_2019.csv`（国家、行、kt、GJ/t、E GWh、是否记工业用电、来源）；在 v4 工业模块（见第 7 节）中实现 |
| 改法 | 口径 I（倍数不变）：ID 中心值 10,589.2 kt × 20.29（59.68 TWh）出"其他"煤、19.21 TWh 入"其他"电；MM 低档 66.09 kt × 23.26 出非金属矿物煤、0.116 TWh 入"其他"电；PH 纸厂 181.54 kt（(b)，电 0.373 TWh 入造纸行）、炼厂 309.94 kt（(b′)，不加电），22.058 GJ/t；TH、VN、MY、BN、KH、LA、SG、TL 为 0 |
| 测试 | `test_v4_captive.py`：移出量 = 吨 × 热值；ATS 工业倍数不变；S4 各国 `T_v2` = I2 ± 1e-6 |
| 验收 | S4 东盟 3,249.88；ID −95.79、PH −1.58、MM −0.26 TWh |

## 6. 燃料木材（第 206 项、第 210 项第 4 条 b）

| 项 | 内容 |
|---|---|
| 改法 | 见第 2、3 节：ID 2010–2017 年均（29,510 千 m³ × SDMX 系数 9.135 GJ/m³ = 74.88 TWh；第 206 项的 74.95 是冻结系数 9.144 下的同一体积）在锚外按 v3 倍数增长；其余国家用 SDMX 当前库（VN 7,260 千 m³；G2 的导出值 14,725 作敏感性，+31.7 TWh） |
| 测试 | ID 平衡表外燃料木材 2019 真值 = 74.88 TWh，2050 = 74.88 × 2.6186；ID 种子内工业生物质只剩木炭 0.80 与生物柴油 3.70 TWh |

## 7. 子部门（新模块 `scripts_project/v4_industry.py`，替代 `v3_industry.py` 的守恒层；第 204、206、208、210 项）

统一规则（I2 `i2_engine.deduct`）：产品的 2019 年能耗先从同名 UNSD 行扣（燃料按该行燃料结构、电从该行电），不够从缓存"其他"行扣，再不够按 D163-4 记录不扣；2050 年显式向量加入 `T_v2`，"其他" = `T_v2` − 显式（D163-6 a）。输入表放 `research_inputs/industry_v4/`。

| 子部门 | 改法（数值见 I2 表） | 测试 / 验收 |
|---|---|---|
| 钢 | 只换空间：ID 2.81 Mt 缺口归 IMIP 节点（S2 / G0 份额） | 节点份额 = `ID_NODE_SHARES.csv` share_v4 |
| 水泥 | 修正 (ii)：粉磨电按 USGS 2019 水泥（ID 71.9、MY 16.102、VN 105.533、TH 40.261、PH 27.7、MM 5.1、KH 7.4、LA 5.208、BN 0.1 Mt）；`s3_0_industry.py` 的 `el19` 行读 v4 表；BN (iii)：EDGAR 2.A.1 视为 0、2050 只计水泥比的电 | S5b 东盟 +12.74 TWh |
| 镍 | 2023 基年、Wei Case 3 全部产品（`v3_industry.nonferrous(…, "nf2023")`）；节点份额按 2023 年设施（MISSING T05） | ID `T_v2` 不变，"其他" −112.68 |
| 纸浆造纸 | FAOSTAT × JRC-IDEES 今天结构（PyPSA-Eur 结构）；黑液 = 化学浆 + 溶解浆 × 22 GJ/t，以燃料部分为上限，单列在 `T_v2` 外；其余燃料（含外购生物质）计入；2019 年从造纸行扣（ID、MY、LA 无该行 → "其他"） | S5d 东盟 −3.05；闭环黑液 2050 ID 95.4、TH 10.1、VN 3.8 TWh |
| HVC | 2019 年扣除 5.191 MWh/t（电 0.272、燃料 4.918），2050 年向量 (b) 4.627 MWh/t（电 2.454、低温热 0.182、甲烷 1.819、氢 0.173）；乙烯利用率 0.85；SG 去掉 GEPDSGP0004；MY 燃料从"其他"的气扣（NEB） | S5e 东盟 +39.20（SG +20.92） |
| 甲醇 | 有化工行的国家（BN、ID、MM、PH、SG、TH、VN）删除欧盟权重甲醇负荷（仿 DFX F2，`s3_0_industry.py:294-303` 旁加一段并记录）；MY（Labuan 2,330 kt × 0.85）、ID（Kaltim 660 kt × 0.85）、BN（850 kt × 0.85）按能源用途显式（气 4.778、电 0.167 MWh/t；2019 年 BN 不从工业扣：燃料在 UNSD 非能源用途，**须同步从 BN NEU 气扣 2019 3.45 / 2050 × 增长 TWh**） | S5f 东盟 +7.85（BN +4.16） |
| 新装置 | 最新状态年在运者进主算（只 2050）：ID LINE（2025 基年）、MY PIC（2025）与 Sarawak Petchem 甲醇（2023）、VN 龙山（2023）、TH Cracker No 5（2020）、LA 2021 年纸线 | S5g 东盟 +56.99 |
| MY 合成氨燃料重复 | 中档：2019 年从"其他"移出气 5.546、电 0.782 TWh | S6a MY −7.93 |
| 玻璃、氧化铝、铜、石灰 | 玻璃 VN / TH / PH / SG（ETSAP 2020）、氧化铝 VN（USGS 2022）、铜 MM / LA（USGS 2018 → 2019）、石灰 MY（ETSAP 2018 BAT）；PH 铜只作敏感性 | S6b 东盟 +1.83 |
| VN 混合拆分 | 缓存 VN 记录 = UNSD 明示分行 + "未细分"按 APEC 2022 份额分（钢铁、化工电按 2020 年回推 9.94 / 9.49 TWh）；`T_v2` 与分解来自同一次运行（删除 `v3_industry.run_vn_chain` 的双运行规则） | S6c VN −29.16；**VN 工业生物质 2050 升到 127.1 TWh，超过调整后潜力（溢出 20.9 TWh），见第 9 节** |

单元测试 `test_v4_products.py`：每个产品的 2019 扣除日志（`tables/I2_DEDUCTION_LOG.csv`：行、实扣、找不到）与 2050 向量逐项相等；"其他"非负；守恒 Σ 部分 = `T_v2`（1e-9 相对）。

## 8. 网络层：气上限、铁路、蔗渣热值、潜力扣减、上限余量（第 209 项 F1–F4、F7）

| 编号 | 文件 / 函数 | 改法 | 测试 / 验收 |
|---|---|---|---|
| F1 | `d1_fossil_production.py:26-28, :5-6, :89-92`；`s2_0_process_emissions.py:66-108` | 国产气上限 = UNSD 商品气产量（`Natural gas (including LNG) - production`）；逸散因子 = EDGAR 1.B.2 ÷（油 + 商品气上限）；改正文档串与注册表 `fossil_production_gas_basis` | 上限合计 −298.4 TWh（ID −134.0、MY −134.9、TL −15.5、VN −7.5、BN −3.2、TH −3.1、MM −0.2）；19 台国产气机组上限 = 商品气折算 |
| F2 | 见第 4 节 | 父行退出 D1、种子、陆运负荷 | EV 重复 6.17 TWh_el 消失 |
| F3 | `d1_biomass.py:47, :286-290, :478-486` | 蔗渣部分用 R2（每吨甘蔗能量与 UNSD 2019 对齐）；单价同口径 | 潜力 −25.97 TWh（`BIOMASS_POTENTIAL_ADJ.csv` F3 列） |
| F4 | `d1_biomass.py:296-315`（新增"厂内自用"扣减步） | 棕榈纤维 100 %、PKS 50 %（中心值，待 MISSING T03）、蔗渣按 UNSD 工业消费 / 产量比、食品 / n.e.s. 5150 中棕榈未覆盖部分按稻、椰残渣比例、木材行 5150 | 潜力 −346.36 TWh；东盟固体潜力 1,990.82 → 1,618.48 TWh |
| F7 | `s3_0_industry.py:347`（溢出判断）与 `s2_layers.py` `biomass_overflow` | 上限 = 0.99 × 潜力 | VN 溢出 14.32 → 20.93 TWh（潜力下调 + 余量）；其余国家 0 |
| F6 | 见第 4 节 | — | — |

单元测试 `test_v4_biomass_potential.py`（逐国逐类 = `BIOMASS_POTENTIAL_ADJ.csv`）、`test_v4_gas_caps.py`（上限 = 商品气 × 0.9 折算）。

## 9. 小时曲线（G5 推荐方案；I2 第 3.3 节）

| 项 | 内容 |
|---|---|
| 文件 | `s2_layers.py` 工业负荷构建处（`industry electricity` 与四个工业热负荷）；新输入 `research_inputs/industry_v4/INDUSTRY_PROFILES_8760.parquet`（G5 MAIN 曲线）与权重表 `INDUSTRY_CURVE_WEIGHTS_V4.csv`（= I2 `tables/I2_CURVE_WEIGHTS.csv`：国家 × 时区 × 曲线键 × 载体类型 × MWh） |
| 改法 | 每个"节点 × 载体"负荷 = 年电量 × 按子部门能量加权的合成曲线（年均 1.0）；连续流程平线；"其他"用东盟 dispersed 混合形状；燃料、原料、氢、氨、甲醇负荷保持恒定；快照为 2013 UTC，按节点法定时区平移 |
| 测试 | `test_v4_profiles.py`：每条合成曲线年均 1.0（≤ 1e-9）、年电量不变（≤ 1e-6 MWh）、ID 节点时区 = `TIMEZONE_NODES.csv` |
| 验收 | v4 量下东盟同时刻固定交流负荷峰值增量（3 h）主算 +21.52 GW、"其他"平线 +11.22 GW、上界 +41.98 GW（`tables/I2_PEAK_IMPACT_ASEAN.csv`） |

## 10. 注册表与数据登记

- 注册表片段 `research_inputs/registry_v5/fragments/v4_w08.csv`：SDMX 11 个响应（文件、字节、SHA256、取得 UTC、`Prepared`、URL）、SDMX 胶囊、热值例外表、平衡表覆盖表、各产品输入表（来源、等级 A–E、基年）、`BIOMASS_POTENTIAL_2050.csv` v4、曲线与权重表、FfE（CC BY 4.0，"© FfE, eXtremOS Project"）与 NREL（DOE/NREL/ALLIANCE，DOI 10.7799/1570008）许可声明。
- `d1_registry.py` 重新组装后 `tests/research` 的注册表一致性测试通过；新增键在配置哈希（B12）中——**任何 v4 网络必须在注册表完成后重建**（B12 对旧网络失败，见记忆 s2-solve gate 说明）。

## 11. 给 W10（C 级数据影响排序）的接口

- **情形文件：** I2 引擎的"情形"是一个 JSON 可序列化字典（`d1` 改动、`anchor_adj`、`ats_add`、`moves`、`products`、`extra`、`nf`、`cem` 等），W08 应保留同一接口（`v4_industry.run_case(case) -> snapshot`），W10 只需改一个输入项（例如 PKS 份额、某产品利用率、某国热值）即可得到逐国 `T_v2`、"其他"、潜力与溢出的变化。
- **排序输入：** `MISSING_DATA_ALL.csv`（24 个主题，已按影响量级排序）与 `tables/I2_SENSITIVITY_ALL.csv`（全部敏感性，含会话值）；W10 对每个 C 级输入给出"±一档"对 `T_v2`、潜力、B6 的影响（B6 部分须求解授权）。

## 12. 实施顺序建议

1 → 2 → 3（检查点 S1、S2）→ 4（S3）→ 5、6（S4）→ 7（S5、S6）→ 8 → 9 → 10；每个检查点跑一次 I2 对照（A1），全部完成后 A0、A2、A3。
