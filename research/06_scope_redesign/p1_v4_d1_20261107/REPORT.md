# v4 D1：第一批数据替换与 HPC 打包前的代码准备（台账 W13、W14；决策清单第 212、214、215 项）

- **指令：** `work/p1_v4_d1_20261107/V4_D1_INSTRUCTION.md` v1，SHA256 `189bcfa54d9d5f462346e9618c58a4ba96d3edccc7c48a83d5633783dbf1f8a5`，与 `V4_D1_SHA256.txt` 一致（开工前核对）。先读材料已读（W08 报告第 0 节、冒烟第 2 节、HPC 草案、待替换数据；W10 第 0 节与 C 级清单；W15 阶段 A 第 0 节、运行事实第 3 节、零成本扫描；W07 A 部分）。
- **分支与目录：** `codex/v4-d1-20261107`，起点 `7aa356e4` = `codex/v4-w08-20261106` 头（fetch 核过，本地 = 远端）；`bd890bf9` 是其祖先，二者之间只改了 W08 交付目录内 3 个文件（范围外 0 个）。worktree `/home/jin/wt_v4_d1`。交付目录 `work/p1_v4_d1_20261107/` = 仓库 `research/06_scope_redesign/p1_v4_d1_20261107/`（zip 不入库）。提交见 `PROGRESS.md`。
- **性质：** 实施。改了仓库代码、输入、配置与注册表，全部挂在开关后（开关全关 = v3.1；被替换的旧值保留为开关值或回退常数）；重建了 v4 主算两张网络；求解器只用于第 7 节授权的 2 次 56 时段求解。没有跳过 git hooks（仓库未启用 hooks；未用 `--no-verify` 或 `-c core.hooksPath`）、没有合并 main、没有 force-push、没有连 HPC、没有打包、没有下载数据文件（只读网页文献）、没有碰 Fable 审查与 W15 的目录、worktree、分支。
- **标记：** VERIFIED（读到的表、代码、网络、回执、原文）、EXACT（可逐项复现的计算）、INFERENCE（推断、解释、换算）、PROPOSED（建议，未实施）；数据等级 A–E。数字都在 `EVIDENCE.json` 与各表中。

## 0. 结论摘要

1. **打包前的代码准备（第 2 节，VERIFIED）：** 开关集新增 `research.demand.v4.hvc_basis`（b 主算 | a）与 `research.biomass.missing_cost_rule`（zero = v3.1 | proxy = v4 主集）；表目录 `out_<锚模式>` 只留给该模式的 v4 主集，其他开关集写到 `out_<锚模式>_<开关集 SHA256 前 12 位>`，每个目录带 `V4_SWITCHES.json`；构建（`s2_network.py`、`m08a_variants.py`）在导出前核对网络元数据 = 表目录 = 配置的开关集 SHA256，不一致即报错。HVC 两种口径的产品项与 I2 逐项相同，口径 (a) 整链 S7 与 I2 敏感性 `hvc_s2` 逐国差 ≤ 4.5e-7 TWh。EV 系数改为注册表未取整值 16.0712 / 53.19 × 1 = 0.302147020…（W08 静态检查 9.9e-6 的来源；现为 2.2e-16）。`out_ras` / `out_iid` 重写后 10 个网络读取的表与 W08 逐字节相同。v4 包的运行器与状态脚本是 v3.1 包文件的副本（`hpc_v4/`，原文件 SHA256 不变）：包的 `COMMIT` 写入 `RUN.json` 与求解回执（`s2_solve.py --package-commit`，不传则回执不变），状态脚本同时显示含常数项的目标值与 LP 值。定义文件草案 `batch_def/BATCH_DEF_2920x3h_v4hpc.json`（PROPOSED：TimeLimit 72 h、进程 1 超时 7,200 s、`no_new_xb` 参考迭代 300、walltime 96 h，运行目录 `runs/batch6`、`runs/smoke56_v4`），未打包、未登记。
2. **油棕树干成本（第 3 节）：** `proxy` 只作用于注册表成本为 DATA_PENDING 且成本列为空的生物质池——恰为 ID、KH、MY、PH、TH 五个油棕树干池；代理价从注册表读（新行 `biomass_missing_cost_proxy` = 32 行同源代理价 6.26706128163 EUR2020/MWh，构建时再核一次）；其余零成本组件（含 15 个有来源的零成本沼气池）不动；`zero` 走原路径。冒烟实测：系统成本 +1.449 bn EUR / 运行（两种情景几乎相同），B6 变化 −2,248 EUR（只作回归）。
3. **违反物理的登记区间（第 4 节，EXACT）：** 扫描 1,486 行在用参数中带区间的 534 行、8 类检查，违反 11 行，按同一规则截到物理界（`PHYSICS_BOUNDS_FIX.csv`）：BEV 充电效率、BEV 可用上限 → 1；甲醇 / t CO₂ 上端 → 4.02482（CO₂ + 3H₂ → CH₃OH + H₂O，甲醇 5.528 MWh/t）；甲醇 / MWh H₂ 上端 → 0.87870（氢 33.33 MWh/t）；电解制氨氢耗下端 → 5.91803（化学计量最小值）；氨、甲醇热值三行区间退化为点；油品船运热值上端 13.9 MWh/t、天然气质量热值上端 50.04 GJ/t（不高于甲烷）；船运年小时数上端 8,760。**甲醇 / t CO₂ 的主值 4.0321（PyPSA-Eur）比化学计量上限高 0.18 %**，按指令只报告、不改主值。主值、状态与网络都不变。
4. **T03：棕榈油厂纤维与 PKS 的厂内自用份额（第 5 节，第一优先）：** MPOB《Palm Oil Engineering Bulletin》第 103 期全文已读：**"15 % 纤维、22 % 壳"是马来西亚 2010 年全国纤维、壳总产量中被烧掉的比例，作者由全国厂内用电 ÷ 等熵朗肯效率倒推燃料、公式中没有锅炉效率项**（隐含燃料约 27–32 kg/t FFB，而 MPOB 对 12 家厂的实测为 116–187 kg/t FFB），它不是观测值，与能量平衡矛盾的审阅意见成立。7 个原文已读的独立来源 + 4 个转述来源给出：纤维 0.81–1.00、PKS 马来西亚 0.45–0.58、印尼 0.50–0.63、泰国 0.05–0.55。工厂能量平衡（中心值规则先定：各参数取独立来源组中位数）：需热 1.979 GJ/t FFB，纤维全部烧掉（1.00）、PKS 补足 0.485。**按第 5.3 条判定：纤维五国一致 → 保留 1.00、等级升为 MY B、其余 C；PKS 印尼、马来西亚、菲律宾、柬埔寨一致 → 保留 0.50、升 C；泰国 PKS 文献 0.30 对平衡 0.49（差 0.19）→ 矛盾，保留 0.50（D），交审阅端。** 国别参数变体下印尼改判矛盾（差 0.195），结论同为保留现值。没有替换任何值：v4 潜力表逐字节不变，检查点（主算 16、IId 15、I2 原主算 2 个）与参照逐国 0 差。低 / 高区间对东盟固体生物质潜力 +47.8 / −11.0 TWh。PKS 出口旁证：印尼出口至少约 19 %、日本自印尼 / 马来西亚进口约占当地 PKS 产量的 37–38 %（年化，INFERENCE）。
5. **抽蓄（第 6 节，研究与建议，网络不改）：** 模型"存量抽蓄 5.4 GW" = 5,406 MW 的 **2050 年存量**，含在建的 Upper Cisokan（ID 1,040）与 Bac Ai（VN 1,200）；IHA 的 2024 年在运量只有 2,260 MW（TH 1,531、PH 729）——**TH 模型多 779 MW、PH 多 127 MW 未解释**（存量处理不变，列待决）。模型已有新建候选 14,438 MW（GEM 管线上限，固定 6 h，往返 0.75，technology-data 2,297 EUR2020/kW）。东盟专门研究（Lu et al. 2021、ANU 2025）的成本折合 6 h 约 740–754 EUR2020/kW、24 h 约 1,509–1,544 EUR2020/kW，约为模型现用值的 1/3（INFERENCE）；资源量远超需求。建议（PROPOSED）见 `PHS_PROPOSAL.md`。
6. **网络与冒烟（第 7 节，VERIFIED）：** 重建主算一体化 `d40352b2…`、`no_new_xb` `c11f5b65…`；W08 全部静态检查通过、零松弛门两网络通过；与 W08 网络逐组件、逐时间序列比较，**只有 5 个树干 Store 的成本不同**。求解前登记（提交 `365c8d62`，在任何 D1 求解之前）：只有成本类变动，0 ≤ ΔV ≤ U = 代理价 × W08 解中的树干用量 = 1,449,347,007.65 / 1,449,347,007.53 EUR（容差 1e-6 × V）。2 次求解都 optimal、`ACCEPTED_LAYER2`、C1 全过、未过的门都在 v3.1 并集内；**ΔV = +1,449,347,508.86 / +1,449,345,260.81 EUR，都在登记区间内**（与上界只差 +501 / −1,747 EUR），树干仍全部用尽——W08 的解对新成本仍最优。障碍迭代 84 / 92（W08 93 / 111）。
7. **测试：** 新增 4 个测试文件 27 项全部通过；全量 `tests/research`（排除玩具求解）852 过、1 败、58 跳过，唯一失败与 W08 相同（旧 S1 网络的跨境开关元数据，与 D1 无关，第 8 节）。

### 0.1 待决问题（需要审阅端 / 用户决定）

1. **T03 泰国 PKS（矛盾）：** 文献两家泰国来源 0.05（Huailuek 2019 调查厂）与 0.55（Chavalparit 2006 单厂；同书另写 20 %），能量平衡 0.49。按规则保留 0.50（D）。是否改用泰国文献中位 0.30，或等泰国工厂燃料平衡数据。（国别参数变体下印尼也判为矛盾：平衡 0.355 对文献 0.55。）
2. **棕榈残余物热值口径（新发现，INFERENCE）：** 潜力表对纤维、PKS、空果串统一用 15 GJ/t（IRENA 惯例，含水基准未注明）；文献收到基热值为纤维约 11.4（含水约 40 %）、壳约 16.0 GJ/t，空果串含水可达 70 %。纤维与一半 PKS 已从潜力中移出，影响小；**空果串潜力（ID 216.6 TWh）可能被高估**，属 T04 一类问题，建议列入数据替换。
3. **缺数成本规则的写法：** `research.biomass.missing_cost_rule` 取值 zero | proxy，配置默认写 `null` = 随开关集（v4 关 → zero，v4 开 → proxy），显式取值覆盖。是否接受此写法（指令只写了两个取值）；代理价用于树干时的等级（注册表层级 C，描述注明树干为 D）。
4. **物理界修正：** 是否接受把纯物质热值（氨、甲醇）的区间退化为点、把油品与天然气热值上端截到甲烷热值；甲醇 / t CO₂ 主值 4.0321 是否改为化学计量值 4.0248（PyPSA-Eur 原值，差 0.18 %）；氢热值取 33.33 MWh/t（technology-data 惯例，注册表无此行）是否登记。
5. **抽蓄：** 存量对账（TH +779、PH +127 MW）是否核查；是否加入改进的新建候选、按哪种结构、成本与上限口径（`PHS_PROPOSAL.md` 第 6 节）。
6. **HPC 定义草案：** 时限与资源（PROPOSED）由审阅端在 W14 决定；网络须在包的提交上重建并登记（D1 网络与冒烟值作为候选写在 `d1_candidates`）。
7. **注册表的 W08 片段：** 重生成后 3 行只更新了文件哈希 / 说明（ADJ 表、潜力脚本；`v4_biomass_overflow_cap_share` 指向的 `baseline.yaml` 哈希自 D1-2 改配置后就已过期，本次一并更新）。

## 1. 分支（指令第 1 节）

| 项 | 值 |
|---|---|
| 起点 | `7aa356e49d284749d27c79fbdc75ade85f62866a`（`codex/v4-w08-20261106` 头，fetch 后本地 = 远端） |
| `bd890bf9` 是否祖先 | 是（`git merge-base --is-ancestor`） |
| `bd890bf9..7aa356e4` 的改动 | 3 个文件，全部在 `research/06_scope_redesign/p1_v4_w08_20261106/`（EVIDENCE.json、PROGRESS.md、审阅包清单）；范围外 0 个 |

## 2. 打包前的代码准备（指令第 2 节；第 214 项第⑧⑨条，第 215 项第①②⑦条）

| 条 | 实现（文件） | 验证 |
|---|---|---|
| 1 表目录按开关集命名 | `v4_common.is_main_set / out_name / out_dir / v4_tables / check_network_meta`；`v4_outputs`（`V4_SWITCHES.json` 加 `dir`、`main_set`）；`s2_network.py`、`m08a_variants.py` 导出前调用 `check_network_meta` | `test_v4_d1_prep.py`（命名、缺目录报 FileNotFoundError、他集记录报错、元数据 5 种篡改均报错、v3.1 网络带 v4 记录报错）；已提交的表目录逐个核对记录与文件哈希 |
| 2 HVC 口径开关 | 配置 `research.demand.v4.hvc_basis: b`；`v4_products.hvc_plants(basis)`、`load_items(hvc_basis)`；`v4_industry.Inputs.items_for(s)` 接入 `build_steps` | 两种口径的 HVC 项与 I2 `i2_items.hvc_items` 逐项相同（`tables/D1_HVC_REF_I2.csv`，相对差 ≤ 1e-12）；整链 S7（I2 原主算开关集）口径 (b) 与 I2 主算、口径 (a) 与 I2 `hvc_s2` 逐国差 ≤ 4.5e-7 TWh（`tables/D1_HVC_CHAIN_CHECK.csv`，I2 表 6 位小数） |
| 3 EV 系数 | `v4_industry.ev_factor()` = 注册表 ICE 效率 ÷ EV 效率 × EV 份额（与 `s2_layers.add_demand_layer` 同式）；`EV_FACTOR_W08 = 0.30215` 留作对照 | 推导：16.0712 / 53.19 × 1 = 0.302147020116563…，与 0.30215 相对差 9.9e-6；静态检查 C2 由 9.9e-6 降到 2.2e-16。W08 测试 `test_v4_transport_accounts.py` 的 EV 断言随之改用未取整值（参照列按 0.30215 → 未取整换算） |
| 4 运行器与状态脚本 | `hpc_v4/run_batch4.sh`（v3.1 包文件副本，`COMMIT` / `.package_commit` 写入 `RUN.json`，`--package-commit` 传给进程 1 与 3；正式运行缺少或不一致即拒绝）；`hpc_v4/hpr_status.sh`（含常数项目标值、LP 值、常数项；进程 3 之前用进程 1 回执的常数项）；`s2_solve.py --package-commit` | v3.1 包的 `run_batch4.sh`（`dc83d53a…`）与 `hpr_status.sh`（`4fd0bd5c…`）SHA256 不变；副本只在标注 "V4 D1" 的行不同；用 B4P 替身流水线跑 `--only F1`：`RUN.json` 带 `package_commit`，两次 `s2_solve` 调用都带 `--package-commit`；状态脚本输出两种目标值；`s2_solve` 不传参数时回执无该键 |
| 5 定义文件草案 | `batch_def/BATCH_DEF_2920x3h_v4hpc.json`（`limits_status: PROPOSED`；`runs/batch6`、`runs/smoke56_v4`；时限按 `HPC_RUNTIME_FACTS.md` 第 3 节） | `b4_batch4.py hpc-plan` 读草案输出 `STATUS|PROPOSED` 与新运行目录；walltime 公式 315,930 s + 等待 ≤ 96 h |

开关全关时 m08b / s3_0 的 8 个输出与 v3.1 逐字节相同（A2，`test_v4_a2_fallback.py` 通过）。

## 3. 油棕树干成本（指令第 3 节；第 212 项第⑤条、第 215 项第⑤条）

- **开关：** `research.biomass.missing_cost_rule`；`v4_common.switches` 读取（`null` = 随开关集），并纳入开关集 SHA256（`out_ras` 名称与网络核对都覆盖它）。
- **规则：** `s2_layers.biomass_missing_cost(registry, rule)` → `add_biomass_layer(..., missing_cost=)`：池的注册表成本行 `biomass_cost_<国>_<类别>` 为 DATA_PENDING 且潜力表成本列为空 → 成本 = 代理价；只有 5 个油棕树干池满足。代理价读注册表行 `biomass_missing_cost_proxy`，并核对它等于全部 32 行来源为"mean of bagasse, rice husk, maize cob prices 35.5 USD/t"的代理行（区间 3.13–9.40 同）。账本与 `n.meta.research_biomass` 记录规则、代理价与 5 个池；`zero` 时不写任何新键。
- **测试：** `test_v4_d1_missing_cost.py`（v3.1 与 v4 两张潜力表：`proxy` 下只有 5 个树干 Store 改变且 = 代理价，其余 Store 表逐列相同；`zero` 下成本 = 成本列或 0、无规则记录；注册表行等于代理行）。
- **网络（VERIFIED）：** D1 网络与 W08 网络只在这 5 个 Store 的成本上不同（第 7 节）。
- **下载候选：** `DOWNLOAD_CANDIDATES.csv` 第 3 节 6 条（树干削片、运输、砍伐成本；只列，不下载）。

## 4. 违反物理的登记区间（指令第 4 节；第 212 项 (a)）

- **推导（EXACT，`scripts_project/v4_d1_registry.physics_limits`）：** IUPAC 2021 原子量 H 1.008、C 12.011、N 14.007、O 15.999；M(CO₂) 44.009、M(CH₃OH) 32.042、M(H₂) 2.016、M(NH₃) 17.031 g/mol；甲醇热值 5.528 MWh/t（注册表 `industry_pe_param_MWh_MeOH_per_tMeOH`）；氢 33.33 MWh/t（technology-data / PyPSA-Eur 惯例，注册表无此行，INFERENCE）；甲烷 50.04 GJ/t（注册表 `biomass_methane_lhv`）。
  - MWh 甲醇 / t CO₂ ≤ 32.042 / 44.009 × 5.528 = **4.024817**（主值 4.0321 高 0.18 %，不改）；
  - MWh 甲醇 / MWh H₂ ≤ 32.042 × 5.528 / (3 × 2.016 × 33.33) = **0.878700**（主值 0.8787，差 1.5e-7，取整）；氢热值取 33.333 或 33.322 时上限变化 ≤ 1e-4（相对）；
  - MWh H₂ / t NH₃ ≥ 1.5 × 2.016 / 17.031 × 33.33 = **5.918027**（主值 5.93）；
  - 甲烷重整制氨的甲烷进料 ≥ 0.375 mol CH₄ / mol NH₃ = 4.910 MWh/t（`industry_ammonia_feedstock_gas_per_t` 下端 4.92，满足）。
- **扫描（VERIFIED，`evidence/PHYSICS_SCAN.json`，`scripts/d1_physics_scan.py`）：** 份额 / 效率 ∈ [0, 1]（48 行，违反 2）；全部 534 行端点非负（违反 0）；化学计量（4 行，违反 3）；纯物质热值无区间（3 行，违反 3）；烃类热值不高于甲烷（5 行，违反 2）；年小时数 ≤ 8,760（1 行，违反 1）；百分数 ∈ [0, 100]（2 行，0）；实际贴现率 > −1（1 行，0）。违反项恰为 11 行，与更正清单一致。另有 21 行主值不在其区间内（需求倍数、标定系数、过程排放等多方法区间），不是物理界问题，只记录不改。
- **实施：** 整行更正片段 `fragments/v4_d1_corrections.csv`（只改 `sensitivity_low/high`，描述与 `decision_ref` 追加说明），`d1_registry.py` 拆出 `assemble()` 以便对未更正的注册表生成更正（可重复运行）。构建代码不读区间列，网络不变。`test_v4_d1_physics.py`（4 项）。

## 5. T03：棕榈油厂纤维与 PKS 的厂内自用份额（指令第 5 节）

### 5.1 文献（`evidence/T03_LITERATURE.json`，58 条：URL、访问 UTC、原文短引文、页码 / 表号；网页检索由子代理完成，本会话逐条过目）

- **MPOB POEB 第 103 期（Yap & Menon 2012，pp. 9–13，全文已读）：** 第 9 页的"mills use about 15% of the total fibre and 22% of the total shell"在第 12 页由 1.6 / 10.8 Mt = 14.9 %、1.1 / 4.98 Mt = 21.5 % 得出，即马来西亚 2010 年（83 Mt FFB，421 家厂）全国纤维、壳产量中被烧掉的比例，不是占 FFB 的比例，也不限于某类工厂（作者自述"假设所有工厂锅炉运行方式相同"）。燃料需求由全国厂内用电（83 Mt × 17 kWh/t）÷ 朗肯效率 15 %（322 / 2,196 kJ/kg）倒推，**没有锅炉效率项**，隐含蒸汽约 0.22 t/t FFB、燃料约 27–32 kg/t FFB；同文另写燃料组成纤维:壳 = 60:40（是燃料构成，不是份额）；文中还有换算与给水焓的算术不一致（T03-A02、T03-D07、T03-I01）。结论：该数不是观测值，不能用。
- **观测（独立来源组，原文已读者 VERIFIED，转述者注明）：** 马来西亚——Vijaya et al. 2008（MPOB，12 家厂三个月实测）：纤维 0.865、PKS 0.452（合计口径）；Nasrin 2011（转述，6 家厂）0.805 / 0.58；Aghamohammadi 2016（转述，砂拉越）0.95 / 0.50；Dit 2007（转述）PKS 0.50。印尼——IOPRI 2012 经 GIZ 2014（约 21 家厂中 84 % 烧掉 ≥ 50 % 的壳）；Yusniati 2018（单厂工程计算）1.00 / 0.63；Setiadi 2014（转述）0.85 / 0.55。泰国——Huailuek 2019（调查厂）0.993 / 0.048；Chavalparit 2006（单厂）0.964 / 0.545（同书另写 20 %）。
- **PKS 离厂旁证（INFERENCE，年化）：** 印尼 2020 年一季度出口 702 kt（年化 2.81 Mt，约占印尼 PKS 产量的 19 %）；日本 2025 年 3 月自印尼 / 马来西亚进口 477.7 / 187.5 kt（年化约占当地产量的 38 % / 37 %）。说明相当一部分 PKS 离厂，厂内份额明显低于 1。

### 5.2 工厂能量平衡（`PALM_MILL_ENERGY_BALANCE.csv`、`evidence/T03_BALANCE.json`、`scripts/d1_t03_balance.py`）

- **公式：** 需热 Q = 蒸汽单耗 × 焓升 ÷ 锅炉效率（背压汽轮机用同一股蒸汽，厂内用电已含在锅炉蒸汽内，不另计燃料）；可用热 = FFB × 质量比 × 收到基热值；纤维先烧，PKS 补足。
- **中心值规则（先定后算）：** 每个参数取独立来源组的中位数（每组一个值）；主算各国共用每吨参数（没有任何参数有 ≥ 3 个本国来源）；变体 B 在本国有 ≥ 2 组时用本国中位数（质量比 MY / ID / TH、蒸汽 TH）。

| 参数 | 中心值 | 区间 | 来源组 |
|---|---:|---|---|
| 蒸汽单耗 t/t FFB | 0.56 | 0.45–0.75 | Vijaya 0.54、Chavalparit 0.56、Yusniati 0.60、Huailuek 0.49、Nasrin / BPPT 0.665 |
| 焓升 GJ/t 蒸汽 | 2.659 | 2.196–2.835 | Yusniati 2.60、POEB 103（21 barg，给水 32 °C）2.667、POEB 116（给水 34 °C）2.659 |
| 锅炉效率 | 0.7525 | 0.71–0.85 | Yusniati 0.73、Nasrin 0.71–0.84（0.775）；UMS 优化上限 0.85 |
| 纤维 / FFB | 0.13 | 0.106–0.15 | 7 组（POEB 103、Vijaya、GIZ、Huailuek、Yusniati、Chavalparit、HRO 汇编） |
| 壳 / FFB | 0.064 | 0.041–0.08 | 同上 7 组 |
| 纤维热值（收到基）MJ/kg | 11.39 | 9.65–13.05 | POEB 103（含水 37 %）、Yusniati（39.8 %）、Mahlia、Fauzianto |
| 壳热值（收到基）MJ/kg | 16.04 | 14.55–18.42 | 同上 4 组 |

- **结果（INFERENCE）：** Q = 1.979 GJ/t FFB，纤维可用 1.481、壳可用 1.026 GJ/t FFB → 纤维 1.00、PKS 0.485。参数区间的两个角：PKS 0（纤维 0.59）到 1.00——平衡本身的不确定性很大，所以规则用中心值。FFB 基数 = v4 潜力表所用基数（FAOSTAT 2019–2023 均值 × 增长 1.1716，核对比 1.000）；2050 年需热 ID 151.2、MY 61.5、TH 11.1 TWh。

### 5.3 判定（第 5.3 条）与表

| 国 | 文献 纤维 / PKS | 平衡（主 / 变体 B）PKS | 纤维判定 | PKS 判定 | 中值（保留） | 低–高 纤维 | 低–高 PKS | 等级 纤维 / PKS |
|---|---|---|---|---|---|---|---|---|
| ID | 0.925 / 0.55 | 0.485 / 0.355 | 一致 | 一致（变体 B 矛盾） | 1.00 / 0.50 | 0.85–1.00 | 0.355–0.63 | C / C |
| MY | 0.865 / 0.50 | 0.485 / 0.530 | 一致 | 一致 | 1.00 / 0.50 | 0.805–1.00 | 0.452–0.58 | B / C |
| TH | 0.979 / 0.30 | 0.485 / 0.442 | 一致 | **矛盾（差 0.19）** | 1.00 / 0.50 | 0.964–1.00 | 0.048–0.545 | C / D |
| PH | 0.95 / 0.50（无本国来源，合并） | 0.485 | 一致 | 一致 | 1.00 / 0.50 | 0.805–1.00 | 0.048–0.63 | C / C |
| KH | 同 PH | 0.485 | 一致 | 一致 | 1.00 / 0.50 | 0.805–1.00 | 0.048–0.63 | C / C |

- 一致且与现值相差 ≤ 0.15 → 保留现值、升级、登记区间；矛盾 → 保留现值、报告；没有"一致但偏离 > 0.15 而替换"的情形。
- **实施：** `research_inputs/biomass_v5/PALM_MILL_SELF_USE.csv`（逐国纤维、PKS 低 / 中 / 高、等级、判定、来源编号；与交付表逐字节相同）；`v4_biomass_potential.self_use()` 读表，W08 常数 1.0 / 0.5 保留为回退（`source="constant"`），`pks_share` 覆盖接口保留。`BIOMASS_POTENTIAL_2050_V4.csv` 逐字节不变（SHA256 `cd9df282…` = W08 = I2），`BIOMASS_POTENTIAL_ADJ_V4.csv` 只改规则文字与等级；注册表新增表文件行与 10 行国别份额（`v4_palm_mill_*`）。`test_v4_d1_palm.py`（5 项）。
- **检查点（`CHECKPOINTS.csv`）：** 新旧潜力逐国差 0；主算 S0–S7、IId S1–S7、I2 原主算 S1 / S7 与参照引擎逐国 0 差（S7 东盟 3,490.338011 / 3,166.521855 / 3,328.336712 TWh）。第 5 节后的新参照 = W08 参照（没有值被替换）。
- **低 / 高敏感性（EXACT）：** 东盟固体生物质潜力相对保留值 +47.8 TWh（低档，ID +31.9、MY +13.1、TH +2.6）/ −11.0 TWh（高档）。

## 6. 抽蓄（指令第 6 节）

见 `PHS_PROPOSAL.md`（VERIFIED / INFERENCE / PROPOSED 逐条标注）。要点见第 0 节第 5 条与待决第 5 条。

## 7. 网络、检查与本机冒烟（指令第 7 节；`SMOKE56_D1.md`）

- **构建（提交 `a6f81341`，`scripts/build_d1.sh`）：** 一体化 2920×3h `d40352b2…`（82,721,770 字节；365×24h `9069f398…`）、`no_new_xb` 2920×3h `c11f5b65…`（82,083,432 字节；365×24h `ba712bf2…`）；峰值 1.07 GB、1 分 32 秒。
- **静态检查（`STATIC_CHECKS.json`）、网络差异（`evidence/D1_NETWORK_DIFF.json`）、零松弛门（`evidence/ZERO_SLACK_CHECK_D1.json`）：** 全部通过（`SMOKE56_D1.md` 1.1–1.2 节）。
- **求解前登记（`SMOKE56_D1.md` 第 1 节，提交 `365c8d62`，在任何 D1 求解之前）：** 第 1.3 节的上下界与容差、第 1.4 节的判据。
- **结果（`SMOKE56_D1.md` 第 2 节）：**

| 运行 | 状态 | 目标值（EUR） | ΔV 相对 W08 | 登记区间 | 未过的门 | C1 | GATES_V6 |
|---|---|---:|---:|---|---|---|---|
| R1 `v4d1_F1` | optimal | 339,292,850,746.35 | +1,449,347,508.86 | [−0.34 M, +1,449.68 M] | A1_A2、A1_A2_S4B、A3、B1、B8 | 通过 | `ACCEPTED_LAYER2` |
| R2 `v4d1_F2` | optimal | 352,176,720,807.95 | +1,449,345,260.81 | [−0.35 M, +1,449.70 M] | A1_A2、A1_A2_S4B、A3、B1、B3、B8 | 通过 | `ACCEPTED_LAYER2` |

- **判据全部满足**；B6（只作回归）12,883,870,061.60 EUR（W08 12,883,872,309.65，−2,248 EUR）。56 时段结果只用于回归，不解读 B6。

## 8. 产出、提交、额度与停止条件

- **产出（`work/p1_v4_d1_20261107/`）：** `REPORT.md`、`PHYSICS_BOUNDS_FIX.csv`、`PALM_MILL_SELF_USE.csv`、`PALM_MILL_ENERGY_BALANCE.csv`、`PHS_PROPOSAL.md`、`SMOKE56_D1.md`、`CHECKPOINTS.csv`、`DOWNLOAD_CANDIDATES.csv`（20 条，只列不下载）、`EVIDENCE.json`、`PROGRESS.md`、`STATIC_CHECKS.json`、`LEDGER_ENTRY_DRAFT.md`（台账条目草稿：指令没有指定台账分支）、`hpc_v4/`、`batch_def/`、`tables/`、`evidence/`、方法脚本 `scripts/`；审阅包 `REVIEW_<提交>.zip`（逐成员 SHA256 + CRC32，zip 不入库，清单入 `evidence/`）。
- **提交：** 见 `PROGRESS.md`（D1-2 `f0e843ba`、D1-3 `2098149f`、D1-4 `bc2fc673`、D1-5 `9453856e`、D1-6 `a6f81341`、D1-7a `365c8d62`、之后的冒烟结果与收尾提交）。D1-5 的提交里已带上第 6 节的 8 条下载候选与 PROGRESS 的 D1-6 行（同一文件），抽蓄文件在 D1-6 提交。
- **全量测试（`scripts/full_tests.sh`，`logs/full_tests.txt`）：** 在冒烟结束后运行 `tests/research`，排除 11 个玩具求解测试（13 项）：**852 通过、1 失败、58 跳过**，用时 33 分钟（W08：825 / 1 / 58；本次新增 27 项）。唯一失败 `test_s1_built_networks.py::test_static_validation_passes_on_reload` 与 W08 相同且与 D1 无关（VERIFIED：报错"Cross-border switch metadata differs from config"——它读取 2026-10-15 建的 S1 网络，元数据跨境开关 `co2: True`，配置为 `False`；因构建时在 worktree 建了指向主检出的 `results_project/s1` 符号链接而被执行，W08 报告第 6 节已说明）。
- **额度：** 求解器只用于第 7 节授权的 2 次（Gurobi 合计约 405 s；本机同一时刻至多 1 个进程）；其余本机计算（表重写、整链核对、检查点、构建、检查、测试）约 1.5 小时量级，在 6 h 内（INFERENCE，按日志）。磁盘新增约 1.5 GB（`results_project/v4d1` 构建与冒烟 0.78 GB、worktree 检出 0.72 GB、`/home/jin/v4d1` 工作目录 0.01 GB；VERIFIED，`du`），在 10 GB 内。网页只读文献（两个检索子代理与本会话 2 次检索），没有下载数据文件，没有访问 UNSD SDMX。
- **停止条件逐项：** SHA 一致；W08 头含 `bd890bf9` 且差异只在交付目录；开关全关逐字节回到 v3.1（A2）；静态检查无新的零余量行、无不可行迹象；2 次 optimal；实际变化满足登记的界；没有改求解档案或 Gurobi 参数；没有写入 Fable 审查或 W15 的目录、worktree、分支；求解日志只读清洗后的副本，没有读取、打印或复制许可内容与登录信息。T03 有"矛盾"一项（泰国 PKS），按指令不是停止条件。
- **与指令写法不同之处（都已在提交说明中写明）：** (1) `missing_cost_rule` 的配置默认写 `null`（随开关集），见待决第 3 条；(2) W08 测试 `test_v4_transport_accounts.py` 的 EV 断言改为未取整系数（指令第 2.3 条的直接结果）；(3) 网页检索由两个只读子代理完成，证据与访问时间原样入 `evidence/`，本会话逐条过目后使用；(4) `missing_cost_rule` 与 `hvc_basis` 两个开关键在 D1-2 一起加入开关集（开关集 SHA256 覆盖二者），缺数成本的作用在 D1-3 实现。
