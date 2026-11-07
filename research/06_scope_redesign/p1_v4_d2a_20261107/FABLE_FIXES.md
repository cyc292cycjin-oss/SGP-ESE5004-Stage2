# Fable 审查修复（V4 D2a 第 2 节；决策清单第 220 项）

- **对象：** `work/p1_v4_fable_w08_20261107/FINDINGS.csv` 的 22 条发现（F-01–F-22）。本节修复 F-01、F-02、F-05、F-06、F-07，顺手修复 F-11、F-12、F-14（都只有几行），F-03 / F-04 写口径说明，其余 S4 列表说明。F-20（HPC 草案缺开关值）随 F-01 消失；F-21（凸性括号 = 报警线）与 F-22（归因需反事实求解）分别在第 6、7 节处理。
- **开关：** 全部改动挂在 `research.demand.v4.*` 后；开关全关时默认运行写出的全部文件与 v3.1 逐字节相同（A2 扩展到 56 个文件，`tests/research/test_v4_a2_fallback.py`）。
- **提交：** D2a-2 `f90bba46`（第 2 节与 3.1 注册表行）。
- **等级：** VERIFIED（表、代码、运行结果）/ EXACT（逐项复算）/ INFERENCE / PROPOSED。

## 1. 修复逐项

| 编号 | 严重度 | 修复 | 验证 |
|---|---|---|---|
| **F-01** 第 211 项第 2 条的字面读法没有开关值 | S2 / F-20 | `research.demand.v4.id_paper_fuelwood` 新增取值 `residue_literal`（`v4_common.SWITCH_VALUES`）：ID 2010–2017 年均燃料木材 74.88 TWh 减去 SDMX 2019 造纸行 41.59 TWh，(b) 项 = 33.30 TWh（主算 `residue` 仍为非造纸份额 23.6 % = 17.67 TWh）；两种读法都从缓存中删去 1214G 的燃料木材记录（`v4_industry_cache.drop_set`）；敏感性表目录 `out_ras_5ba297a881ba`（按开关集 SHA 命名）已提交 | ID 2050 `T_v2` 1,483.776362 → 1,520.666216 TWh，**+36.889854 TWh**，与 Fable `SENS_PAPER_FUELWOOD.json` 逐位相同（EXACT）；其他 10 国 0 差；东盟 3,527.227865 TWh = Fable；`test_v4_d2a_fixes.py::test_f01_*` |
| **F-02** 表、快照中的 VN 溢出是产品向量加入前算的 | S2 | `v4_outputs.write_tables` 在守恒层之后用构建规则重算溢出列（`v4_common.overflow_split`：溢出 = max(0, `T_v2` 生物质 + 农业生物质 − 0.99 × 潜力)，先工业后农业）；`Chain.run` 的快照 `overflow` / `overflow_agriculture` / `bio_before` 同口径，s3_0 旧值保留为 `overflow_s30` / `bio_before_s30`；`V4_SWITCHES.json` 记录新旧值 | VN 主算 29.951 → **41.097 TWh**，IId 20.928 → **32.074 TWh**（= W08 网络台账，差 11.146 TWh = VN 纸浆造纸外购生物质向量）；其他国家 0 差；网络读取的列（`pe_*`、带份额、`*_to_gas`）不变 → **网络不变**（第 5 节逐组件核对）；参照引擎（`scripts/ref`，W08 引擎副本）同规则重跑，检查点 main 16 / iid 15 / i2chk 2 步逐国 0 差含溢出与上限（`CHECKPOINTS.csv`） |
| **F-05** 测试缺口 | S3 | `tests/research/test_v4_d2a_fixes.py`：(a) 每个表目录"表溢出 = 构建规则"；(b) 快照 = 表；(c) 已建网络台账 = 表（有 D2a 构建时运行）；(d) `process_and_feedstock` 复现已提交表与 2.A.1 规则；(e) `v4_tables` 拒绝篡改的开关记录（SHA、目录名、缺文件）；A2 扩展为默认运行写出的全部文件（≥ 56）逐字节相同 | 第 2 节 10 项通过（网络项在第 5 节构建后通过）；A2 56 个文件 SAME |
| **F-06** 注册表 tier / grade；上限份额定位；收敛记录 | S3 | `v4_pks_in_mill_share`：注册表层级只有 A / B / C，描述写明"层级 C = 最低层级，证据等级 D"；`v4_biomass_overflow_cap_share`：`file:` 定位到 `baseline.yaml` 的键，文件哈希受测试核对；m08b 的 RAS / 重拟合收敛记录 `DEMAND_ANCHOR_M08B_EVIDENCE.json` 写入每个表目录（`ras_refit`：8 次迭代，行误差 5.9e-11，列误差 2.2e-16） | `test_f06_*`；注册表 2,402 → 2,404 行（D2a-2） |
| **F-07** BN NEU 2019 基数未扣甲醇气 | S3 | `v4_outputs.bn_neu_methanol` 同时扣 2019 基数（厂 2019 气用能 3.452 TWh：5.459 → 2.007 TWh）与 2050 值（已有）；两项扣减按装置增长（1.166），行按 NEU 倍数（1.051）增长，`multiplier_total` 不改 | BN `T_v2` 影响 **0**（NEU 在 `T_v2` 外；网络只读 2050 值）；`test_f07_*` |
| F-11 `anchor_mode` 在 v4 关时静默无效 | S4 | `v4_common.check`：v4 关且 `anchor_mode != ras` → ValueError | `test_f11_*` |
| F-12 `shape_3h` 只接受 2920 / 8760 | S4 | 任一 8760 的约数（`y.reshape(n, 8760 // n).mean(1)`） | `test_f12_*`；2920 路径逐位不变 |
| F-14 s3_0 的潜力含构建跳过的行 | S4 | v4 路径（给了 `--biomass-potential` 或 `--biomass-cap-share`）按 status 过滤 DATA_PENDING / ZERO_BY_DECISION 行；默认 v3.1 运行不变 | 过滤本身无数值效果（这些行潜力为 0）；Fable 所说的 MY 793、BN 856、SG 473、TL 664 MWh 差额实为 **S4L-1 尘埃清理**删除的近零池（`store_e_nom` 173,215,797 对表 173,216,590 MWh），不是 status，s3_0 不复制该清理（≤ 5e-6 相对），网络对表测试的上限容差 1 GWh |

### 1.1 F-02 的旁注（未改，交审阅端）

`biomass_source_band_*_share`（固定工业生物质的来源温度带份额：高温带 = 水泥窑生物质 / 全部固定生物质）仍是 s3_0 在产品向量前算的份额。加入产品向量的外购生物质（VN 11.1 TWh，为中温蒸汽 / 干燥用途）后，更一致的高温带份额会略低。改它会改变网络（VN 溢出有用热在三带间的分配），与本节"修复 F-02 后网络不变"的预期相悖，故不改，列为 S4 口径说明。

## 2. F-03 / F-04 口径说明

- **F-03 蔗渣数据版本：** 潜力侧 F3 / F4c 用 W12 的 UNdata 导出（TH 蔗渣产量 46,878 kt），需求侧用 SDMX 当前库（51,674 kt，+10.2 %）；自用份额相同（0.4807）。两套数据是同一指标的两个版本，差额来自 UNSD 的修订；本步不重做 F3 / F4c（≤ 5 TWh，INFERENCE），列入 W19 候选"按 SDMX 胶囊重生成 W12 蔗渣表"。
- **F-04 残渣两侧的增长基准：** 需求侧自产残渣（a）按工业倍数增长（TH 78.33 → 179.35 TWh），潜力侧 F4 扣减按作物增长与厂内假设（TH −49.31、ID −195.37（T04 后 −159.75）、MY −73.81（T04 后 −59.33）TWh）。两侧口径不同是设计结果：需求侧移出的是 UNSD 2019 记录 × 倍数（锚边界），潜力侧移出的是 2050 残余物产量中厂内烧掉的部分；两者不要求相等。VN 甘蔗潜力中蔗渣 5.41 TWh 低于 UNSD 2019 记录的使用量 11.67 TWh（v3 潜力既有问题）列入 W19 候选。

## 3. 其余 S4 项

| 编号 | 处理 |
|---|---|
| F-08 规格 196.94 对 197.03 | 文档项：W08 规格数字过时，实现用 SDMX 197.032 TWh 正确；W08 交付不改写 |
| F-09 表中未覆写的 s3_0 列（`bas_*`、`other_*`、`td_*`、`s2b_td_*`） | 在 `v4_outputs` 文档中写明这些列是守恒层前的 s3_0 值、构建不读；不重算（会误导读者的是溢出列，已改） |
| F-10 开关关时 `production_caps_table` 元数据键 | 接受（B12 设计） |
| F-13 实现位置（子类与扩展字典） | 接受 |
| F-15 (b) 项虚拟 2019 基数 14.45 TWh | 文档项（规格允许） |
| F-16 HVC 原料与能源用途不同增长基准 | 写入 HPC 计划边界说明（既有设计） |
| F-17–F-19 一致性核查 | 无需改动 |

## 4. 表目录变化（D2a-2 相对 D1 头 `4026c1c8`）

| 文件 | out_ras | out_iid | 说明 |
|---|---|---|---|
| `INDUSTRY_2050_SUMMARY_V4.csv` | VN `biomass_overflow_industry_mwh` 29,951,239 → 41,097,220 | VN 20,927,787 → 32,073,768 | 只此一列一国 |
| `DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv` | BN NEU 气 `base_2019_mwh` 5,458,799.25 → 2,006,854.81 | 同 | 只此一行一列（+ `growth_method` 注） |
| `SNAPSHOT.json`、`V4_SWITCHES.json` | 溢出键、开关集 SHA、新键 | 同 | |
| `DEMAND_ANCHOR_M08B_EVIDENCE.json` | 新增 | 新增 | F-06 |
| 其余 8 个表 | 逐字节相同 | 逐字节相同 | 网络读取的 `pe_*`、带份额、节点份额、曲线权重、过程排放、原料碳不变 |

D2a-3 之后（第 3 节）开关集再变（`biomass_potential = v4_adjusted_t04`、`meoh_per_tco2`）：`INDUSTRY_2050_SUMMARY_V4.csv` 的 `solid_biomass_potential_main_mwh` 列（ID、MY、TH、KH、PH 的上限）与 `SNAPSHOT.json` / `V4_SWITCHES.json` 随之变化，见 `EFB_BASIS.md`。
