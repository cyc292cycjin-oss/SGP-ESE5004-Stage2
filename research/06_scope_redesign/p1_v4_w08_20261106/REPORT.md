# v4 W08：把定稿写进仓库（台账 W08；决策清单第 203–211 项）

- **指令：** `work/p1_v4_w08_20261106/V4_W08_INSTRUCTION.md` v1，SHA256 `17fdf2f16eeb68587cd61b034280f939ed02741825bd55b55abef50d1ec077c0`，与 `V4_W08_SHA256.txt` 一致（开工前核对）。先读材料已读：W08 实施清单全文、I2 报告第 0 节、验证计划、W07 指令 A 部分。
- **分支与目录：** `codex/v4-w08-20261106`（起点 `aad8e476` = `codex/v4-i2-20261106` 头），worktree `/home/jin/wt_v4_w08`。交付目录 `work/p1_v4_w08_20261106/` = 仓库 `research/06_scope_redesign/p1_v4_w08_20261106/`（zip 不入库）。提交见 `PROGRESS.md`。
- **性质：** 实施。改了仓库代码、输入、配置与注册表（全部挂在开关后，开关全关时逐字节回到 v3.1）；重建了 3 个 v4 网络（本机，2920×3h + 365×24h）；求解器只用于第 5 节授权的 4 次 56 时段求解。没有跳过 git hooks（仓库未启用 hooks）、没有合并 main、没有 force-push、没有连 HPC、没有下载新数据。
- **标记：** VERIFIED（读到的表、代码、回执）、EXACT（逐项可复现的计算）、INFERENCE（推断、解释）、PROPOSED（建议，未实施）。数字都在 `EVIDENCE.json` 与各表中。

## 0. 结论摘要

- **实施（VERIFIED / EXACT）：** 清单第 1–10 节全部写进仓库，全部挂在 `research.demand.anchor_mode` 与 `research.demand.v4.*` 开关后。仓库链与参照引擎逐步、逐国 0 差（A0 / A1：主算 16 个、IId 15 个、I2 原主算 2 个检查点）；开关全关时 m08b / s3_0 的 8 个输出与 v3.1 逐字节相同（A2）；新输入 69 行登记，DATA_REGISTRY 原有 2,321 行不变（A3）。W10 接口 `v4_industry.run_case(case)` 已实现。
- **参照值（第 211 项，EXACT）：** 东盟 2050 `T_v2` 主算（IIa + 造纸木材 (a)）**3,490.34 TWh**（"其他" 45.0 %），IId 3,166.52 TWh；相对 I2 主算 +162.00 = 造纸木材 −161.81（只 ID）+ 锚 IIa +323.82（所有国家工业倍数上升，RAS 把交通压回 C.3）。
- **网络（VERIFIED）：** 本机重建主算一体化 `cbe051d8…`、主算 `no_new_xb` `aa2bab39…`、IId 一体化 `09480713…`；静态检查全部通过（含零松弛门 3 / 3、无新的零余量行）。
- **冒烟（VERIFIED）：** 4 次 56 时段求解全部 optimal；R0（v3.1 网络在 W08 代码上复跑）与 v3.1 本机冒烟目标值逐位相同。v4 相对 v3.1：主算一体化 **+8.138 bn**、主算不互联 **+8.459 bn**、IId 一体化 **+2.592 bn**；B6（只作回归）12.884 bn（v3.1 12.563）。
- **判据：** 1（optimal）与 3（R0 对照）满足；2（门 A1 / A2 / S4B）**字面不满足**，与 v3.1 冒烟相同（失败门都在 v3.1 并集内，C1 全过，v4 三次 `ACCEPTED_LAYER2`）；4（成本差在一阶估计 ± 50 % 内）**不满足**（比值 2.86 / 2.60 / 符号相反）。
- **数据链核查（不改参数、不重试）：** 没有发现链上错误。三对实际成本差都落在两端对偶给出的 LP 凸性上下界内（+8.14 ∈ [−0.57, +12.33]；+8.46 ∈ [−30.60, +12.38]；+2.59 ∈ [−9.06, +11.66]）。一阶估计偏低的原因（INFERENCE，价格 VERIFIED）：v4 的工业热需求降了数百 TWh，ID 中温 B / 高温热价从 47.7 降到 25.2 EUR/MWh（IId 9.5），MY、TH 同向；在 v3.1 价下需求减少值 −12.5 bn，在 v4 价下只值 −0.4 bn——这是大变化的二阶项，±50 % 区间（约 ±1.5 bn，套在两个约 15 bn 的相反项的净额上）本来就窄（求解前已写明）。**按指令停下汇报。**
- **提交：** 分支 `codex/v4-w08-20261106`，按节提交并推送（第 6 节）；没有开 PR（指令只要求推送）；停下等审阅。

### 0.1 待决问题（需要审阅端 / 用户决定）

1. **第 211 项第 2 条的读法。** 实施的读法：从 2010–2017 年均燃料木材中按造纸行份额（76.4 %）移出，(b) 项只留非造纸份额（23.6 %，17.7 TWh）。字面另一读法：按 SDMX 2019 造纸行 41.59 TWh（16,389 千 m³）移出，(b) 项 = 年均 − 41.59 = 33.29 TWh——ID `T_v2` +36.89 TWh（主算、IId 相同；`tables/W08_ALT_PAPER_FUELWOOD.csv`）。潜力侧两种读法都为 0（树皮不在潜力中，ID 木材加工残余只 0.887 TWh）。
2. **残渣锚扣减与 C.3。** 第 210 项第 4 条要求所有锚模式都扣减；RAS 只在扣减前守 C.3 部门合计，扣减后东盟工业行低于 C.3 × k（S7 −15.65 %，含显式产品 −7.77 %）。是否接受这一设计结果。
3. **VN 溢出口径。** 网络用构建口径（工业汇总表全部生物质 + 农业，主算 41.10、IId 32.07 TWh），清单引用 s3_0 列 20.93 TWh（不含产品向量的生物质）。报告时以哪一个为准。
4. **门判据字面。** A1_A2、A1_A2_S4B 在 v3.1 冒烟中就不通过；是否沿用 v3.1 的验收（C1 (a)(b)(c) + GATES_V6 `ACCEPTED_LAYER2` + 失败门在并集内）。另：在本分支上 v3.1 网络的 B12 与 GATES_V6 G2.2 必然失败（配置多了新键），R0 因此 `NOT_ACCEPTED`。
5. **成本判据。** 判据 4 不满足而凸性上下界成立。是否以上下界（或其他）作为今后冒烟与 HPC 的判据；HPC 草案以此为前提。
6. **过程排放与原料碳按 v4 倍数重算**（清单未列，为一致而做，第 2 节第 4 条）。
7. **与清单写法不同之处**（第 2 节第 1–3 条：冻结转换表、`reconstruct_base_accounts.py`、`d1_demand_2050.py`、`d1_biomass.py` 都没有改，效果相同）。
8. **HPC 打包前的两项改动**（HPC 草案第 4 节：表目录按开关集命名、HVC 口径开关），会改变配置哈希。
9. 小项：EV 系数 0.30215 是四舍五入值（静态检查差 9.9e-6）；SDMX 中 ID 农业用煤为 0，构建清理去掉 5 个节点煤母线与外部煤发电机（`STATIC_CHECKS.md`）。

## 1. 参照值（指令第 1 节；`REFERENCE_V4_MAIN.csv`、`REFERENCE_V4_IID.csv`、`tables/W08_REF_VS_I2.csv`）

**做法（EXACT）：** I2 引擎（`i2_engine.py`、`i2_items.py`、`i2_chain.py`）原样复制，只做三处带断言的文本修改（`scripts/w08_ref_setup.py`）：
1. 第 211 项第 1 条：锚边界对齐在所有锚模式下适用——`ras`（IIa）在"残渣仍在工业种子中"的种子上重解 RAS（同一组行、列目标），再把工业锚减 残渣 × 工业倍数（其余部门锚与全部倍数不变）；`frozen`（IIb）同样扣减；
2. S1 的锚模式改为 IIa（主算）；
3. 第 211 项第 2 条：S2 中 ID 造纸行（SDMX 1214G）燃料木材按自产残渣 (a) 从种子与缓存移出，平衡表外燃料木材 (b) 项只留非造纸份额（= I2 敏感性 `id_paper_fw_selfuse` 的写法）。

**复核（EXACT）：** 去掉两处修改时副本与 I2 逐国 0 差（S1、S7）；IId 组 S0–S1 与 I2 0 差。

| | 东盟 S7 `T_v2`（TWh） | "其他" | 占比 |
|---|---:|---:|---:|
| I2 主算（IId，造纸木材 (b)） | 3,328.34 | 1,334.35 | 40.1 % |
| **W08 主算（IIa，造纸木材 (a)）** | **3,490.34** | **1,569.87** | **45.0 %** |
| W08 IId（造纸木材 (a)） | 3,166.52 | 1,334.79 | 42.2 % |

**主算相对 I2 的逐国差异与原因（EXACT 分解，`tables/W08_REF_VS_I2.csv`）：** 差 = 造纸木材（只 ID −161.81）+ 锚构造 IIa（东盟 +323.82）。

| 国 | I2 | W08 主算 | 差 | 造纸木材 | 锚 IIa | 工业倍数 I2 → W08 |
|---|---:|---:|---:|---:|---:|---|
| ID | 1,488.68 | 1,483.78 | −4.90 | −161.81 | +156.91 | 2.77 → 3.20 |
| VN | 742.46 | 792.70 | +50.24 | 0 | +50.24 | 2.63 → 2.89 |
| TH | 400.49 | 447.53 | +47.04 | 0 | +47.04 | 1.93 → 2.29 |
| MY | 359.10 | 400.61 | +41.51 | 0 | +41.51 | 1.37 → 1.67 |
| PH | 141.31 | 156.45 | +15.14 | 0 | +15.14 | 1.97 → 2.38 |
| SG | 92.16 | 96.91 | +4.74 | 0 | +4.74 | 1.12 → 1.25 |
| MM | 56.53 | 60.66 | +4.12 | 0 | +4.12 | 0.96 → 1.05 |
| KH | 23.00 | 25.76 | +2.75 | 0 | +2.75 | 3.68 → 4.58 |
| LA | 18.79 | 19.73 | +0.93 | 0 | +0.93 | 2.59 → 3.07 |
| BN | 5.81 | 6.22 | +0.41 | 0 | +0.41 | 0.84 → 1.05 |
| **东盟** | **3,328.34** | **3,490.34** | **+162.00** | **−161.81** | **+323.82** | |

**原因（INFERENCE，机制可复现）：** IId 用 v3 的部门系数乘各国自己的（修正后）种子，ID 家庭汽油移到道路、VN 柴油补回后，交通份额上升，东盟交通比 C.3 × k 高 26.3 %、工业比 C.3 低（S7：工业行 −26.5 %）。IIa 的 RAS 必须守 C.3 的东盟部门合计，于是把交通压回 C.3（S7 主算交通偏离 0.00 %），被挤出的能量回到工业等部门——所有国家的工业倍数都上升（上表），`T_v2` 上升 4–20 %。ID 的锚效应（+156.9）与造纸木材（−161.8）几乎抵消。主算东盟部门合计相对 C.3 × k（S7，`tables/W08_REF_C3_DEVIATION.csv`）：工业行 −15.65 %（残渣锚扣减、自备移出、平衡表外项的结果；含显式产品 −7.77 %）、交通 0.00 %、居民 +2.44 %、商业 +6.08 %、农业 +0.01 %。

**逐步（东盟 `T_v2`，TWh）：**

| 步 | 主算 | Δ | IId | Δ |
|---|---:|---:|---:|---:|
| S0 v3.1 | 3,820.05 | — | 3,820.05 | — |
| S1 基年（SDMX） | 3,880.57 | +60.52 | 3,728.65 | −91.40 |
| S2 锚边界（含造纸木材 (a)） | 3,589.34 | −291.23 | 3,357.54 | −371.12 |
| S3 (ii) 类 | 3,568.74 | −20.60 | 3,185.69 | −171.85 |
| S4 自备 (b) | 3,455.71 | −113.02 | 3,088.07 | −97.63 |
| S5b 水泥 | 3,470.30 | +14.58 | 3,100.80 | +12.74 |
| S5c 镍（"其他" −112.7） | 3,470.30 | 0 | 3,100.80 | 0 |
| S5d 纸浆造纸 | 3,452.54 | −17.76 | 3,097.75 | −3.05 |
| S5e HVC | 3,473.15 | +20.61 | 3,136.95 | +39.20 |
| S5f 甲醇 | 3,477.37 | +4.22 | 3,144.80 | +7.85 |
| S5g 新装置 | 3,534.36 | +56.99 | 3,201.79 | +56.99 |
| S6a MY 氨 | 3,524.73 | −9.63 | 3,193.85 | −7.93 |
| S6b 玻璃等 | 3,522.38 | −2.35 | 3,195.68 | +1.83 |
| S6c VN 拆分 | 3,490.34 | −32.04 | 3,166.52 | −29.16 |
| S7 网络层 | 3,490.34 | 0 | 3,166.52 | 0 |

主算的 S3 只有 −20.6（IId −171.9）：RAS 守 C.3 交通合计，ID 家庭汽油移到道路只在国家之间重新分配交通锚，不再从 ID 工业挤出能量。

## 2. 实施（指令第 2 节；清单第 1–10 节）

**总判据（VERIFIED，`CHECKPOINTS.csv`）：** 仓库链（`scripts_project/v4_industry.py`）与参照引擎逐步、逐国比较——主算 S0–S7 共 16 个检查点、IId S1–S7 共 15 个、I2 原主算（IId + 造纸木材 (b)）S1 与 S7：**`T_v2`、"其他"、12 个载体、溢出、上限的差全部为 0**（A0 / A1，容差 1e-6 TWh）。开关全关时 m08b / s3_0 的 8 个输出与 v3.1 逐字节相同（A2，`test_v4_a2_fallback.py`，在临时副本中运行）。新输入 SHA256 = 注册表（A3，`test_v4_registry.py`）；全量 `tests/research` 见第 6 节。

| 清单节 | 仓库改动（文件） | 输入（`research_inputs/`） | 测试 | 检查点 | 提交 |
|---|---|---|---|---|---|
| 1 SDMX 基年 | 新 `v4_base_sdmx.py`（I1 `Recon`、`blend`、`rail_children`、`d1_rows` 原样移入） | `assembly_v1/sources/unsd_sdmx_2019/`（11 个响应 + W12 登记行）、`SDMX_2019_CAPSULE.json`（2,752 条）、`SDMX_2019_BLEND_MEMO.csv`、`SDMX_DICTIONARY_EXTENSION.json`、`demand_v5/NCV_EXCEPTIONS.csv`、`industry_v4/D1_BASE2019_SDMX.csv`、`D1_BASE2019_V31_REBUILD.csv`、`HOUSEHOLD_GASOLINE_2019.csv` | `test_v4_base_sdmx.py`（5） | 胶囊、种子、备忘与 I2 逐字节相同；G1–G3 通过 | `37e8a7a6` |
| 2 分行业缓存 | 新 `v4_industry_cache.py` | `industry_v4/SDMX_INDUSTRY_CELLS_2019.csv`、`RESIDUE_RECORDS_2019.csv`、`RESIDUE_CLASSES.csv`、`NATIONAL_BALANCE_BIOMASS_COVERAGE.csv`、`FUELWOOD_OUTSIDE_BALANCE.csv`、`industry_cache_v4.json` | `test_v4_industry_cache.py`（4） | 三种开关集的缓存 = 参照 | `6590d3e4` |
| 3 锚构造与锚边界 | `m08b_demand.py`（选项 `--anchor-mode ras/iid/iib/external`、`--residue-anchor-adj`、`--table`、`--out-dir`、`--dump-anchors`）、`s3_0_industry.py`（`--only-mode` 等）、新 `v4_industry.py` | `demand_v5/DEMAND_ANCHOR_V3_SECTOR_FACTORS.csv`、`DEMAND_ANCHOR_V3_FROZEN.csv`、`industry_v4/ANCHORS_V31_RAS_DUMP.json` | `test_v4_anchor_iid.py`（4）、`test_v4_a2_fallback.py`（2） | S1、S2 = 参照 | `c9cedcef` |
| 4 (ii) 类 | `v4_industry.build_steps` S3；`s2_layers.land_transport_accounts` | — | `test_v4_transport_accounts.py`（4） | S3 = 参照 | `54b47a28` |
| 5、6 自备、燃料木材 | 新 `v4_products.py`（与第 7 节共用） | `industry_v4/CAPTIVE_COAL_2019.csv` | `test_v4_captive.py`（3） | S4 = 参照 | `676d1383` |
| 7 子部门 | `v4_products.py`（I2 `pp_item`、HVC、甲醇、VN 混合拆分移入） | `PULP_PAPER_FAOSTAT_V4`、`HVC_PLANTS_V4`、`METHANOL_PLANTS_V4`、`PRODUCT_DERIVED_INPUTS_V4`、`MY_AMMONIA_FUEL_DUPLICATE`、`VN_HYBRID_ELECTRICITY_ROWS`、`CEMENT_USGS_2019`（取数脚本 `scripts/w08_intake_items.py`，来源列逐行写明） | `test_v4_products.py`（6） | S5a–S6c = 参照 | `676d1383` |
| 8 网络层 | 新 `v4_biomass_potential.py`、`v4_gas_caps.py`；`s2_layers.py`（溢出上限 0.99）、`s3_layers.py`（气上限表） | `biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv`（与 I2 逐字节相同）、`BIOMASS_POTENTIAL_ADJ_V4.csv`、W12 蔗渣表；`gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv`、`FUGITIVE_FACTORS_V4.csv`、W12 气表 | `test_v4_biomass_potential.py`（3） | S7 = 参照（A0） | `aba72721` |
| 9 小时曲线 | 新 `v4_profiles.py`；`s2_layers.py`（工业电与四个热负荷按节点时区加 G5 MAIN 合成曲线） | `industry_v4/INDUSTRY_PROFILES_8760.parquet`、`INDUSTRY_PROFILE_INDEX.csv`、`INDUSTRY_PROFILE_MAPPING.csv`；权重写在各表目录 | `test_v4_profiles.py`（3） | 权重与 I2 表差 ≤ 0.48 MWh（I2 表取整） | `aba72721` |
| 10 注册表 | 新 `v4_outputs.py`、`v4_registry.py`；`d1_registry.py`（加片段）；`s2_network.py`、`s2_layers.py`、`s3_layers.py`（v4 表与开关集 SHA256 核对）；配置 `research.demand.anchor_mode`、`research.demand.v4.*` | `industry_v4/out_ras/`（主算）、`out_iid/`（IId）；`registry_v5/fragments/v4_w08.csv`（69 行），DATA_REGISTRY 2,321 → 2,390 行（原有行 0 改动） | `test_v4_registry.py`（3） | — | `aba72721` |

**W10 接口（清单第 11 节）：** `v4_industry.run_case(case) -> snapshot`，case 键与 I2 相同（`d1`、`anchor_mode`（含 I2 别名 `fixedcol` / `frozen`）、`anchor_adj`、`ats_add`、`moves`、`products`、`extra`、`nf`、`cem`、`edgar_zero`、`bn_iii`、`meoh_drop`、`vn_same_run`、`bio_cap_share`、`biopot`）；`v4_industry.Inputs()` + `build_steps(I, switches)` 给出各步的 case，W10 改一个输入项即可得到逐国 `T_v2`、"其他"、潜力与溢出的变化。

**与清单写法不同之处（都已在提交说明中写明）：**
1. `FROZEN_UPSTREAM_CONVERSIONS.json` 没有改：六个新商品名放在 `SDMX_DICTIONARY_EXTENSION.json`，建 SDMX 基年时并入（冻结的 v3.1 输入保持不变，效果相同）。
2. `reconstruct_base_accounts.py` 与 `d1_demand_2050.py` 没有改：I1 的 `Recon`（因子模式）作为子类放在 `v4_base_sdmx.py`；直接改前者会使 `test_dfx_demand.py` 的 F0.3 规则失败（该文件不在 DFX 的执行清单中）。v4 种子以"在 v3.1 D1 表上替换基数列"的方式进入 m08b（I2 `write_d1`），与清单"D1 读 SDMX 胶囊"的结果相同（检查点 0 差）。
3. `d1_biomass.py` 没有改：F3 / F4 写成 v4 后处理 `v4_biomass_potential.py`（I2 规则原样），v3.1 潜力表不变。
4. 过程排放（EDGAR 2.A / 2.C）与原料碳（2.B + 2.D）随 ATS 工业倍数增长；v4 倍数变了，所以 `v4_outputs.py` 用同一公式按 v4 倍数重算并由构建读取（清单未列，为保持一致而做）。
5. v4 表目录目前只按锚模式命名（`out_ras` / `out_iid`）；其他开关集的敏感性需要先扩展命名（见 HPC 草案第 4 节）。

## 3. 数据缺口（指令第 3 节；`DATA_TO_REPLACE.csv`）

没有等数据：按 I2 默认值实现，所有待替换的量都是输入表或开关。"W08 之前"的 6 项（T01 AEDS、T02 平衡表生物质覆盖、T03 PKS 去向、T04 IRENA 含水率、T08 UNSD 方法说明、T13 甲醇装置）与第 211 项第 2 条相关的 T16（造纸燃料构成），以及 5 项"W08 之后"的输入，逐项列出：仓库文件与列、现用值与等级、开关、数据到位后要重跑的脚本与测试、已知影响量级。

## 4. 注册表与网络（指令第 4 节；`STATIC_CHECKS.md`）

- 注册表片段 `v4_w08.csv`：11 个 SDMX 响应（字节、SHA256、取得 UTC、`Prepared`、URL）、胶囊、热值例外、覆盖表、各产品输入表、V4 潜力、曲线（FfE CC BY 4.0 "© FfE, eXtremOS Project"；NREL DOE/NREL/ALLIANCE，DOI 10.7799/1570008）、商品气上限与对应的 `fugitive_factor_oilgas_v4_*`。`d1_registry.py` 重组后 2,390 行，原有 2,321 行逐字不变。
- 配置：`research.demand.anchor_mode: ras`、`research.demand.v4.enabled: false`（其余键为 v4 主集取值，只在 enabled 时生效）。B12 的配置哈希包含新键：v4 网络以 `--override demand.v4.enabled=true`（IId 再加 `demand.anchor_mode=iid`）构建，覆盖项记在网络元数据中；**v3.1 网络在本分支上 B12 失败是预期结果**（配置多了新键）。
- 网络（2920×3h + 365×24h）：主算一体化 `cbe051d8…`、主算 `no_new_xb` `aa2bab39…`、IId 一体化 `09480713…`，构建各约 1.5 分钟、峰值 1.07 GB（本机）；2920×3h 全尺寸 LP 没有在本机构建（第 4 节限制）。
- 静态检查全部通过：工业负荷对表 ≤ 1.1e-6 MWh；457 条曲线负荷年均不变；两种分辨率一致；EV / 铁路对表、无父行；生物质池最高 0.99（VN）、无 ≥ 0.999 的池；零松弛门 3 / 3 通过；19 台国产气机组、上限合计 −298.41 TWh；ID 三个时区。**须知（INFERENCE）：** 构建中的 VN 溢出主算 41.10、IId 32.07 TWh——构建按工业汇总表的生物质（含纸浆造纸等产品向量的生物质）计，比清单引用的 s3_0 列（20.93）口径宽；网络用的是前者。

## 5. 本机 56 时段冒烟与回归（指令第 5 节；`SMOKE56_V4.md`）

- **求解前登记（`SMOKE56_V4.md` 第 1 节，提交 `a0507578`，在任何 W08 求解之前）：** 4 次运行、同 v3.1 冒烟的档案与设置（`formal_barrier_1e6_t16`、`--truncate 56`、`--scaling on`、TimeLimit 3,000 s）、判据读法、一阶估计（主算 F1 +2.844、F2 +3.254、IId −3.814 bn）。
- **结果（VERIFIED）：**

| 运行 | 状态 | 目标值（EUR） | 相对 v3.1 | 一阶估计 ± 50 % | 失败门（均在 v3.1 并集内） | C1 | GATES_V6 |
|---|---|---:|---:|---|---|---|---|
| R0 v3.1 F1 | optimal | 329,705,565,613.54 | 0（逐位） | — | A1_A2、A1_A2_S4B、A3、B1、B3、B8、B12（预期） | 通过 | `NOT_ACCEPTED`（只 G2.2：配置子集哈希，预期） |
| R1 v4 主算 F1 | optimal | 337,843,503,237.49 | +8.138 bn | +1.422…+4.266 不满足 | A1_A2、A1_A2_S4B、A3、B3、B8 | 通过 | `ACCEPTED_LAYER2` |
| R2 v4 主算 F2 | optimal | 350,727,375,547.14 | +8.459 bn | +1.627…+4.881 不满足 | A1_A2、A1_A2_S4B、A3、B1、B3、B8 | 通过 | `ACCEPTED_LAYER2` |
| R3 v4 IId F1 | optimal | 332,297,882,383.00 | +2.592 bn | −5.721…−1.907 不满足 | A1_A2、A1_A2_S4B、A3、B1、B8 | 通过 | `ACCEPTED_LAYER2` |

- **用时（VERIFIED）：** 障碍迭代 96 / 93 / 111 / 93，求解 267 / 216 / 203 / 207 s，峰值内存 5.7–7.3 GiB。B6（只作回归）v4 12,883,872,310 EUR，v3.1 12,563,125,651 EUR。
- **数据链核查（`SMOKE56_V4.md` 第 2.3 节）：** 链本身（检查点、静态检查、回执中的网络 SHA256）无误；LP 凸性上下界三对都成立（补全 v4 删去的 `oil_palm_fibre` 池、v4 中不存在的母线上的负荷、固定容量后，0 MWh 未计价）；一阶估计偏低来自工业热价随需求大降（ID 47.7 → 25.2 EUR/MWh；MY 16.5 → 7.8；TH 17.6 → 6.7），即二阶项。梯形估计（事后参考，非判据）7.59 / 7.82 / 3.92 bn 对实际 8.14 / 8.46 / 2.59 bn。
- **处理：** 按指令停下汇报；没有改参数、没有重试、没有用事后估计追认判据（待决 0.1 第 4、5 条）。

## 6. 产出、提交、额度与停止条件

- **产出（`work/p1_v4_w08_20261106/`）：** `REPORT.md`、`REFERENCE_V4_MAIN.csv`、`REFERENCE_V4_IID.csv`、`CHECKPOINTS.csv`、`STATIC_CHECKS.md` / `.json`、`SMOKE56_V4.md`、`SMOKE56_FIRST_ORDER.csv`、`DATA_TO_REPLACE.csv`、`HPC_V4_PLAN_DRAFT.md`（草案，未打包、未提交）、`EVIDENCE.json`、`PROGRESS.md`、`LEDGER_ENTRY_DRAFT.md`（台账条目草稿：指令没有指定台账分支）、`tables/`、`evidence/`、方法脚本 `scripts/`；审阅包 `REVIEW_<提交>.zip`（逐成员 SHA256 + CRC32 清单，zip 不入库，清单入 `evidence/`）。
- **提交（分支 `codex/v4-w08-20261106`，起点 `aad8e476`）：** `c2ffe7a0` W08-1 参照值；`37e8a7a6` 清单第 1 节；`6590d3e4` 第 2 节；`c9cedcef` 第 3 节；`54b47a28` 第 4 节；`676d1383` 第 5–7 节；`aba72721` 第 8–10 节；`17a15c22` 去掉误加的 `__pycache__`；`a0507578` 网络、静态检查与求解前登记；之后的冒烟结果、报告与收尾提交见 `PROGRESS.md`。
- **全量测试（A3）：** `scripts/full_tests.sh`，在 W08 头运行 `tests/research`，排除 11 个玩具求解测试（5 个已知 + `test_m12_allocation.py` 6 个；`test_m10p_batch3.py` 只是源码字符串匹配，照常运行）：**825 通过、1 失败、58 跳过**，用时 32 分钟（`logs/full_tests.txt`）。唯一的失败 `test_s1_built_networks.py::test_static_validation_passes_on_reload` 与 W08 无关（VERIFIED，`scripts/s1_xb_check.sh`）：它读取 2026-10-15 建的 S1 网络（元数据跨境开关 `co2: True`），而配置 `research.cross_border.co2` 在起点 `aad8e476` 与 W08 头都是 `False`（W08 的配置改动只在 `research.demand` 下）。这项测试在没有 S1 网络时跳过；这次运行，是因为 W08 为构建在 worktree 中建了指向主检出的 `results_project/s1`、`results_project/assembly_v1` 符号链接（2026-11-06 08:57，未入库）。
- **额度：** 求解器只用于第 5 节授权的 4 次（Gurobi 合计约 892 s，本机同一时刻至多 1 个进程；HPC 2 个，合计 ≤ 8）；其余计算（参照链、构建、检查、测试）约 1 小时量级，在 6 h 内（INFERENCE，按日志）。磁盘新增约 2.5 GB（`results_project/v4w08` 1.5 GB、`/home/jin/v4w08` 0.3 GB、worktree 检出），在 15 GB 内。没有下载：UNSD SDMX 用的是 I1 已取的响应（原样复制并登记），本次没有新的网络请求。
- **停止条件逐项：** SHA 一致；检查点差 0；开关全关逐字节回到 v3.1；静态检查无新的零余量行、无不可行；没有改求解档案或 Gurobi 参数；4 次状态都是 optimal；没有读取、打印或复制许可证与登录信息（求解日志按规则清洗后才读）。**判据 4 不满足 → 按第 5 节"先查数据链，不改参数重试，停下汇报"处理。**
- **没有做的事：** 没有跳过 git hooks（仓库未启用 hooks，未用 `-c core.hooksPath`）、没有合并 main、没有 force-push、没有连 HPC、没有碰 W10 的分支与目录、没有构建 2920×3h 全尺寸 LP、没有打包 HPC。
