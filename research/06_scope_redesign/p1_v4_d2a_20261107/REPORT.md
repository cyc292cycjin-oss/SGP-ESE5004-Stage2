# v4 D2a：独立审查修复、空果串与抽蓄核实、重排修正、成本上升归因（台账 W18；决策清单第 218–220 项）

- **指令：** `work/p1_v4_d2a_20261107/V4_D2A_INSTRUCTION.md` v1，SHA256 `4920db6341793bf5df76b7651a982cdb4a653c1bc6dc866a9df3227d626e38fa`，与 `V4_D2A_SHA256.txt` 一致（开工前核对）。先读材料已读（Fable 报告全文与 `FINDINGS.csv`；D1 报告、`PHS_PROPOSAL.md`、`PALM_MILL_*.csv`；W15 基线第 0、7 节与 `RERANK_*.csv`；W08 第 0 节；W07 A 部分）。
- **执行：** Claude Fable 5.1（`claude-fable-5-1`；指令写的是 Opus 5.5 / Xhigh，本会话由用户以 Fable 启动），分支 `codex/v4-d2a-20261107`（从 `codex/v4-d1-20261107` 头 `4026c1c8` 新开，fetch 核过本地 = 远端；`6142d8ac` 是其祖先，二者之间只改了 D1 交付目录 3 个文件），worktree `/home/jin/wt_v4_d2a`；交付目录 `work/p1_v4_d2a_20261107/` = 仓库 `research/06_scope_redesign/p1_v4_d2a_20261107/`（zip 与 `cache/` 不入库）。
- **性质：** 实施。改了代码、输入、配置、注册表与表目录，全部挂在开关后（开关全关时默认运行写出的 56 个文件与 v3.1 逐字节相同，A2）；重建 56 时段网络；本机求解 §6 2 次 + §7 4 次 = 6 次（额度 6）。不连 HPC、不打包；网页只读文献（两个只读子代理，证据逐条过目，访问 UTC 与引文在 `evidence/*_LITERATURE.json`），不下载数据文件；不跳过 git hooks（仓库未启用；未用 `--no-verify` / `core.hooksPath`），不合并 main，不 force-push，不碰其他会话的目录与分支。
- **标记：** VERIFIED / EXACT / INFERENCE / PROPOSED；数据等级 A–E。数字在 `EVIDENCE.json` 与各表中。

## 0. 结论摘要

1. **Fable 修复（§2，VERIFIED / EXACT；`FABLE_FIXES.md`）：** F-01 开关值 `id_paper_fuelwood: residue_literal`（ID 2050 `T_v2` +36.889854 TWh，与 Fable 逐位相同；表目录 `out_ras_5ba297a881ba`）；F-02 溢出列在守恒层后按构建规则重算（VN 主算 29.95 → **41.10** TWh、IId 20.93 → **32.07**，= 网络台账；其他列、其他国家、网络全部不变），参照引擎同规则重跑，检查点 0 差；F-05 补 5 组测试（含"网络台账 = 表"，已在重建网络上通过）与 A2 全 56 文件；F-06 注册表层级说明、`file:` 定位、m08b 收敛记录入表目录；F-07 BN NEU 2019 基数 5.459 → 2.007 TWh（`T_v2` 影响 0）；顺手 F-11 / F-12 / F-14（F-14 的 ≤ 0.9 GWh 差额实为 S4L-1 尘埃清理，非 status）。
2. **甲醇与氢（§3.1，EXACT）：** v4 主集甲醇化 MWh/t CO₂ = 化学计量 **4.02481710559**（开关键 `meoh_per_tco2: stoichiometric`，v3.1 回退 4.0321），注册表登记氢热值 33.33 MWh/t；网络中 30 条甲醇化链路的 `efficiency3` / `efficiency4` 变 0.18 %。
3. **T04 空果串基准（§3.2，`EFB_BASIS.md`）：** 潜力表的棕榈残余物份额是 IRENA 2022 Box 4 的**湿基**工厂物料平衡，15 GJ/t 来自 IRENA 2017a 的通用假设（干基量级，基准未注明）；EFB 收到基含水 57–67 %（三个独立原文来源）、干基 LHV 15.8–19.1 → **基准不一致，按登记规则重算**：EFB 每湿吨 (1 − 0.60) × 18.0 = 7.20 GJ（× 0.48），纤维 × 0.76；PKS 一致保留；树干无法判定、保留并给区间 0.20–0.36 交审阅端。新主集 `biomass_potential: v4_adjusted_t04`（W08 值保留为 `v4_adjusted`）：东盟固体潜力 **1,618.48 → 1,448.09 TWh**（ID −112.65、MY −45.79、TH −11.36；VN 不变），检查点对 T04 参照 0 差。
4. **抽蓄存量（§3.3，`PHS_STOCK_RECON.md`，VERIFIED）：** `TH2 4` 950 MW 冻结组 = GEM 两条 Bhumibol 记录之和（779 常规 + 171 抽蓄），而 EGAT 合同容量 779.20 MW = 6 × 82.2 + 115 + 171 **已含** 8 号可逆机，GEM 重复计入 171 MW；两个独立来源（EGAT、ANDRITZ）一致，IHA 合计 1,531 = 1,000 + 360 + 171 旁证 → **修正**（`research.fleet.phs_stock_reclass`，随 v4 开关）：171 MW 抽蓄 + 608.2 MW 常规水库水电（同节点来水代理，国家来水总量不变）+ 170.8 MW 剔除；TH 抽蓄 2,310 → **1,531 MW**。PH 736 + 120 保留：736 = DOE 装机（IHA 729 为口径差），Pantabangan-Aya 是真实新建抽蓄（GEM 状态偏早，按决策 77 / 86 b 沿用）。
5. **抽蓄敏感性开关（§3.4，PROPOSED 实现）：** `research.supply.phs_case: main | asean`——`asean` 为三档时长（6 / 12 / 24 h）StorageUnit，Lu et al. 2021 成本折 EUR2020（491.25 EUR/kW + 43.86 EUR/kWh + 6.14 EUR/kW/a，50 a，往返 0.80；6 h 年化 60.8 对主算 184.5 kEUR/MW/a），每国能量上限 = ANU 短名单（新钩子 `research_phs_energy_cap`），无数据国家保持现状；`main` 下网络逐组件不变（测试 + §5 C8）。
6. **重排修正（§4，`RERANK_D2A_*.csv`、`W19_CANDIDATES.csv`）：** 封存上限对偶改读全局行 + Store `e_nom` 上界（KH −10.40、PH −16.19、VN −10.81 EUR/t 全在 Store 界上，全局行 0：退化重复确认）→ **KH 封存上限 `co2_injection_cap_unified_KH` 由第 259 升至第 3**（ΔB6 −2.16 bn，Owen KH −9.34 bn）；S-B 船运 6 行退出排序；偏向列（成本类上界 131 行、右端类下界 121、系数不定 18、离散 6）；10 对区间按物理界刷新（名次不变）。前 30 与 W15 重合 27、Spearman 0.945；前 30 占 |ΔB6| 的 96.4 %。W19 候选 23 项（§4.5）。
7. **网络与静态检查（§5，VERIFIED）：** 重建一体化 `334904c4…`、`no_new_xb` `9ec39333…`；C1–C6、C10 通过；零松弛门通过；C8 对 D1 的差异全部在预期集合内（9 个池、`TH2 4` 拆分、泰国 8 台水库来水重分配、30 条甲醇化链路）。
8. **冒烟（§6，VERIFIED；`SMOKE56_D2A.md`）：** 两次 56 时段求解均 optimal、`ACCEPTED_LAYER2`、C1 a/b/c 接受、失败门在 v3.1 并集内（新增 B3 = VN 池超用 ≤ 1.6e-3 MWh，容差层面）；对 D1 的实际变化 **ΔV F1 +9,526.7 M、F2 +8,974.0 M EUR**，高于求解前登记的报警线 +6,515.9 / +6,048.7 M（高出凸性下界 +2,963.6 / +2,879.0 M = D1 对偶线性化未计的替代路线成本）。56 时段 B6 回归值 12.3311 bn（D1 12.8839，−552.8 M；只作回归）。
9. **成本上升归因（§7，`ATTRIBUTION_56.md`；角点 VERIFIED、(D31,P31) INFERENCE）：** 4 次角点求解全部 optimal、`ACCEPTED_LAYER2`、失败门在并集内。56 时段两因素 Shapley：一体化目标值从 v3.1（近似 331.15 bn）到 v4 主集 348.82 bn 的 **+17.67 bn 中，资源上限 P 贡献 +25.13 bn、v4 需求 D 贡献 −7.46 bn**，交互项 −12.33 bn（D 在 P31 下 −1.29、在 P4 下 −13.63：v4 需求的节省在生物质上限绑定时放大）；`no_new_xb` 同向（+17.51 = P +24.84 + D −7.33）；B6 −0.16 bn（D +0.13、P −0.29）。按参与者：ID 的 Owen 受益 −0.71 → +1.08 bn（φ_P +1.29），BUNKER +3.30 → +2.41（φ_P −0.85），SG +2.77 → +2.94，MY +0.87 → +1.07；一体化台账 ID φ_P +12.7 bn、BUNKER φ_P +9.9 bn、MY φ_D +6.2 bn。只给方向，正式归因留 2920×3h 批次。
10. **测试：** 17 个 v4 测试文件 **95 过、1 跳过 → 构建后网络项也通过（96 过）**；全量 `tests/research` 未重跑（时间；D1 为 852 过 / 1 旧 S1 网络项败 / 58 跳过，本步未改那些路径——见 §8）。

### 0.1 待决问题（需要审阅端 / 用户决定）

1. **T04 口径：** 主算取"干物质 × 干基 LHV"（EFB 7.20 GJ 每湿吨）而非"湿重 × 收到基 LHV"（5.2–5.7）；是否接受（`EFB_BASIS.md` 1.1）。
2. **树干能量基准：** 表按鲜重 × 15 GJ/t（含水 70–80 %），干基 LHV 无来源 → 保留 + 区间 0.20–0.36；树干五池在每次求解中全部用尽，是 W19 第一优先数据项。
3. **抽蓄：** 接受 TH 的 171 / 608.2 / 170.8 拆分；PH 保留；`phs_case: asean` 是否进 W19 批次；ANU 站点表申请。
4. **KH 封存上限的名次：** 修正读法后升至第 3（ΔB6 −2.16 bn）；其 1.8 Mt/a 的上限（`co2_injection_cap_unified_KH`）是否列为 W19 数据项（现为 REGISTERED，区间 1.8–900 Mt/a 很宽）。
5. **F-02 旁注：** `biomass_source_band_*_share` 仍按产品前的生物质算（改之会动网络），是否在 W19 一并改。
6. **第 7 节近似：** (D31,P31) 角未求解（额度），用 v3.1 冒烟 + 已知其他改动近似（INFERENCE）；是否在正式批次前补 1–2 次求解把近似换成实测。
7. **其他农业残余物的基准**（Smeets 2004 残余因子，15 GJ/t）与 F-03 / F-04 的数据版本：W19 候选。
8. **指令写法差异：** 本会话模型为 Fable 5.1（指令写 Opus 5.5）；`phs_stock_reclass` 用 `null = 随 v4 开关`（与 D1 `missing_cost_rule` 同一写法）；重排缓存复制到本目录（不写 W15 目录）；参照引擎按 F-02 同规则改了副本（W08 引擎文件不改）。

## 1. 分支（§1）

| 项 | 值 |
|---|---|
| 起点 | `4026c1c84d8d349e9bb8c11f3e6da8f82588d621`（`codex/v4-d1-20261107` 头 = 远端） |
| `6142d8ac` 是否祖先 | 是；`6142d8ac..4026c1c8` 改 3 个文件，全部在 `research/06_scope_redesign/p1_v4_d1_20261107/` |
| 提交 | D2a-2 `f90bba46`、D2a-3 `50dfdcf7`、D2a-6a `63651f19`、D2a-7a `8e94bbe5`、之后见 `PROGRESS.md` |

## 2. Fable 修复（§2）

见 `FABLE_FIXES.md`（逐项修复、验证、F-03 / F-04 口径说明、S4 处理、表目录变化）。要点：

| 编号 | 修复 | 关键数字 |
|---|---|---|
| F-01 | 开关值 `residue_literal`；表目录 `out_ras_5ba297a881ba` | ID `T_v2` 1,483.776 → 1,520.666 TWh（+36.889854，EXACT = Fable）；东盟 3,527.228 TWh |
| F-02 | `v4_outputs` 守恒层后重算溢出列；快照同口径（旧值保留为 `*_s30`）；参照引擎同规则 | VN 29.951 → 41.097（主算）、20.928 → 32.074（IId）TWh；网络不变（§5 C8） |
| F-05 | 5 组新测试 + A2 全 56 文件 | 11 项通过（网络项在 §5 构建后通过） |
| F-06 | 层级说明；`file:` 定位；m08b 收敛记录（RAS 重拟合 8 次迭代，行误差 5.9e-11） | 注册表 2,402 → 2,404 行 |
| F-07 | BN NEU 2019 基数扣 3.452 TWh | 5.459 → 2.007 TWh；`T_v2` 0 |

## 3. 数据与物理（§3）

| 条 | 实施 | 结果 |
|---|---|---|
| 3.1 甲醇 / 氢 | 开关键 `meoh_per_tco2`（`v4_common.meoh_per_tco2_value` → `s3_layers` 甲醇化与燃料碳口）；注册表 `ammonia_methanol_MWh_MeOH_per_tCO2_stoichiometric` 4.02481710559、`physics_hydrogen_lhv_mwh_per_t` 33.33 | `efficiency3` −0.217926 → −0.218320；一阶成本 +23 M EUR（§6） |
| 3.2 T04 | `PALM_RESIDUE_BASIS_T04.csv`；`v4_biomass_potential.adjust(basis="t04")`；`biomass_potential: v4_adjusted_t04`；注册表 +9 行 | 见 `EFB_BASIS.md` 第 2 节表；东盟 −170.39 TWh |
| 3.3 抽蓄存量 | `s4a_fleet.reclassify_phs_stock`；`PHS_STOCK_RECLASS_V4.csv`；`research.fleet.phs_stock_reclass: null` | TH 1,531 MW；+608.2 MW 水库；FOM-once 与容量恒等式保持；泰国来水总量 7.2699 TWh 不变 |
| 3.4 抽蓄开关 | `s4b_candidates.phs_asean_case` + `install_phs_energy_cap`；`PHS_ASEAN_CASE_V4.csv`；注册表 12 行（SENSITIVITY） | `main` 不变；`asean` 三档、能量上限 ID 103 / LA 62 / MY 62 / MM 62 / VN 62 / PH 42 / TH 16 TWh |

检查点（`CHECKPOINTS.csv`）：`main_t04` 16 步、`iid_t04` 15 步、`i2chk_s3` 2 步，`T_v2`、"其他"、载体、溢出、上限对修正后参照逐国 0 差（参照引擎 `scripts/ref` 在 T04 潜力文件上重跑）。

## 4. 重排修正（§4；`scripts/rerank_with_results_d2a.py`、`rerank_d2a_post.py`、`rerank/`）

| 修正 | 实现 | 效果 |
|---|---|---|
| 4.1 封存上限对偶 | `scalar_rhs` 的对偶 = 全局行 + 该国 `co2 sequestered` Store 的 `e_nom` 上界对偶（从 `DUALS_BY_CONSTRAINT.nc` 补提取为 `stores_enom_upper.csv`，不读网络）；扫描 `research_co2_storage_cap-*` 7 国：全局行 0、Store 界 KH −10.40 / PH −16.19 / VN −10.81 EUR/t（退化重复，`rerank/DUPLICATE_BOUNDS.csv`） | KH 上限行 259 → **3**（ΔB6 −2.163 bn，ΔZ_F1 −9.34 bn，Owen KH） |
| 4.2 S-B 船运 | `basis_inactive_in_run` 行标"口径未生效"退出排序 | 6 行退出（`liquid_ship_hours_per_year`、`speed`、`ckm_td_*`、`cargo_loss`）；排序行 282 → 276 |
| 4.3 偏向列 | `bias_class` / `bias_dZ` / `bias_dB6`：成本类 ΔZ 上界、右端类下界、系数 / 离散不定；ΔB6 一律不定（两单侧界之差） | 成本 131、右端 121、系数 18、离散 6 |
| 4.4 区间与参照 | `--registry-ranges` 从本分支注册表刷新"登记区间"行的缺口（10 对：D1 物理界修正）；参照 `v31`（F1、F2），对照 `v31ev05`（F3、F4）；缓存复制自 W15 到 `cache/` | 10 对刷新后 ΔB6 不变（取值方向为低端）；对 `v31ev05` Spearman 0.995、前 30 重合 28 |
| 4.5 产出 | `RERANK_D2A_TOP30.csv`、`RERANK_D2A_OWEN_TOP10.csv`、`RERANK_D2A_VS_W15.csv`、`W19_CANDIDATES.csv` | 前 30 与 W15 重合 27（进入：KH 封存上限、MY 树干潜力、城市有机垃圾 CH₄ 产率；退出：3 条 S-B 船运行）；Spearman 0.945 |

**前 5（v31 参照，一阶，INFERENCE）：** WACC 模式 −3.54 bn（离散）、海上风电 alpha 标定 −2.49 bn（系数）、**KH 封存上限 −2.16 bn（右端下界）**、MY 屋顶光伏上限 −1.32 bn（右端）、电动交通效率 +1.24 bn（右端）。**Owen 前 10：** 船运甲醇份额（BUNKER −22.8 bn）、ID 树干潜力（ID −20.9 bn）、KH 封存上限（KH −9.3 bn）、陆运电动份额（TH +9.0 bn）、甲醇化 H₂ 效率（ID +8.3 bn）……

**W19 候选（`W19_CANDIDATES.csv`，23 项）：** |ΔB6| 前 15 + |Owen| 前 10（去重 18 项，含机制、偏向、是否需新数据）+ 本步识别的 5 项：燃料舱排放计入加注国净零（第 218 项）、树干能量基准（第一优先）、EFB 基准区间、`phs_case: asean`、其他农业残余物的残余因子基准。

## 5. 网络与静态检查（§5；`STATIC_CHECKS.json`、`evidence/D2A_NETWORK_DIFF.json`、`evidence/ZERO_SLACK_CHECK_D2A.json`）

- 构建（提交 `50dfdcf7`，`scripts/build_d2a.sh main`）：一体化 2920×3h `334904c4…`（82,749,429 字节；365×24h `419c56b7…`）、`no_new_xb` `9ec39333…`（82,111,961 字节；365×24h `d8c49a18…`）；峰值 1.07 GB、1 分 31 秒。
- C1–C6、C10 与零松弛门：见 `SMOKE56_D2A.md` 1.2 节表（全部通过；网络溢出台账 = 表 1.9e-4 MWh；抽蓄 ID 1,040 / PH 856 / TH 1,531 / VN 1,200 MW）。
- C8 对 D1：两种网络两种分辨率，差异全部在预期集合（9 个生物质池 `e_nom` / `e_initial`；`TH2 4` 抽蓄组 5 列；新组件 `hydro existing::D2A`；泰国 8 台水库 `inflow`；30 条甲醇化链路 `efficiency3` / `efficiency4`；元数据），**无 UNEXPECTED**。
- 检查点：§3 后的新参照逐国 0 差（`CHECKPOINTS.csv`）。

## 6. 本机冒烟回归（§6；`SMOKE56_D2A.md`）

- **求解前登记（提交 `63651f19`，1.3 节）：** 报警线 = 右端类凸性下界 − 容差 − 2·|系数一阶|：R1 **+6,515.9 M**（LB +6,563.2：ID / MY / TH 池 +6,596.5、抽蓄 +2.9、来水 +0.14、新水库 −36.4；FO +23.5；容差 0.34）、R2 **+6,048.7 M EUR**。
- **求解（`scripts/smoke_d2a.sh`，提交 63651f19 的网络，档案 `formal_barrier_1e6_t16`、`--truncate 56`、TimeLimit 3,000 s，串行、1 个 Gurobi 进程、令牌服务器 TCP 预检）：**

| 运行 | 终止 | 目标值 EUR | D1 目标值 | **ΔV** | 报警线 | ΔV − LB | 未过门（并集内） | C1 | GATES_V6 | 障碍迭代 / 求解秒 / 峰值 |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| R1 一体化 `334904c4…` | optimal | 348,819,582,511.57 | 339,292,850,746.35 | **+9,526.7 M** | +6,515.9 M | +2,963.6 M | A1_A2、A1_A2_S4B、A3、B1、B3、B8 | a/b/c 接受 | ACCEPTED_LAYER2 | 77 / 201.8 s / 7.28 GiB |
| R2 no_new_xb `9ec39333…` | optimal | 361,150,691,045.29 | 352,176,720,807.95 | **+8,974.0 M** | +6,048.7 M | +2,879.0 M | 同上 | a/b/c 接受 | ACCEPTED_LAYER2 | 89 / 171.1 s / 5.72 GiB |

- **判据 1–4 全部通过**，不是停止条件。R1 新增失败门 B3（D1 R1 通过）：VN 池用量超潜力 2.2e-4 MWh（相对 1.6e-12），R2 1.6e-3 MWh——障碍法容差层面，与 v3.1 冒烟 R2 的 B3 同类。
- **解读（INFERENCE）：** ΔV 高于下界约 2.9 bn，是因为 LB 只是 D1 对偶在 D1 解处的线性化；被移除的 170 TWh 棕榈残余物（ID 112.7、MY 45.8、TH 11.4）由更贵的路线替代，边际成本随之上升（决策 212 (b) 的凸性方向）。ΔV_LP（不含常数项）+9,530.7 / +8,977.9 M，与 ΔV 之差为 `TH2 4` 组 FOM-once 重分配等常数项。
- **B6 回归（56 时段）：** 12.3311 bn（D1 12.8839，−552.8 M）；不解读，供第 7 节使用。

## 7. v4 成本上升归因（§7；`ATTRIBUTION_56.md`、`evidence/ATTRIBUTION_56.json`、`tables/D2A_ATTRIB56_RESULTS.csv`）

- **设计：** 因素 D = v4 需求（需求与工业表、曲线、过程排放与原料碳），P = v4 资源上限（T04 生物质潜力、0.99 上限、商品气上限）；其余 v4 改动（抽蓄、甲醇、树干代理成本等）在所有角上取 v4 值。角点表集用 `v4_common` 开关组合写出（`out_ras_f8179c68f46f` = (D4,P31)，`out_ras_f5e106da1fde` = (D31,P4)），网络由 `scripts/build_d2a.sh` 构建（提交 `8e94bbe5`）；(D4,P4) 取第 6 节冒烟；**(D31,P31) 未求解（额度 6 次用尽）**，用 v3.1 网络的冒烟值（F1 W08 R0 329,705.57 M、F2 v3.1 包本机冒烟 342,268.69 M）加已知其他改动（树干代理 +1,449.3 M、抽蓄 / 来水 / 新水库下界项 −33.3 / −101.8 M、甲醇一阶 +23.5 / +23.0 M）近似，INFERENCE。
- **4 次求解（`scripts/attrib_solves.sh`，同第 6 节档案，串行，1 个 Gurobi 进程）：**

| 运行 | 终止 | 目标值 EUR | 未过门（并集内） | C1 | GATES_V6 | 障碍迭代 / 求解秒 / 峰值 |
|---|---|---:|---|---|---|---|
| d4p31_F1 `d49e5df0…` | optimal | 329,853,409,059.36 | A1_A2、A1_A2_S4B、A3、B1、B8 | a/b/c 接受 | ACCEPTED_LAYER2 | 92 / 211.2 s / 7.42 GiB |
| d4p31_F2 `dc589ba9…` | optimal | 342,431,438,654.97 | 同上 + B3 | a/b/c 接受 | ACCEPTED_LAYER2 | 91 / 167.8 s / 5.62 GiB |
| d31p4_F1 `e01503b0…` | optimal | 362,445,881,245.89 | 同上 + B3 | a/b/c 接受 | ACCEPTED_LAYER2 | 76 / 174.7 s / 7.18 GiB |
| d31p4_F2 `7bc9f2f4…` | optimal | 374,597,076,484.48 | 同上 + B3 | a/b/c 接受 | ACCEPTED_LAYER2 | 96 / 171.3 s / 5.76 GiB |

- **两因素 Shapley（bn EUR；φ_D + φ_P ≡ 总变化）：**

| 量 | (D31,P31) 近似 | (D4,P31) | (D31,P4) | (D4,P4) | 总变化 | φ_D | φ_P | 交互 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 一体化目标值 | 331.145 | 329.853 | 362.446 | 348.820 | **+17.675** | **−7.459** | **+25.134** | −12.335 |
| `no_new_xb` 目标值 | 343.639 | 342.431 | 374.597 | 361.151 | +17.512 | −7.327 | +24.839 | −12.239 |
| B6 | 12.494 | 12.578 | 12.151 | 12.331 | −0.163 | +0.132 | −0.295 | +0.096 |

- **读法（INFERENCE）：** v4 成本上升几乎全部来自资源上限（P 先：+31.3 bn；D 先：+19.0 bn），v4 需求本身**降低**成本（在 v3 潜力下 −1.3 bn，在 v4 潜力下 −13.6 bn）。交互项为负且大：v4 需求集在生物质上限绑定时省得更多，即 v4 需求把需求从受生物质约束的载体上移开（工业燃料 / 原料的重构），这一效果只有在上限收紧时才显现。B6 对两因素都不敏感（±0.3 bn，56 时段）。
- **按参与者（Owen 受益 = B6 分摊；一体化台账 = F1 成本份额）：** ID Owen −0.712（v3.1）→ −0.010（D4,P31）→ +0.782（D31,P4）→ **+1.076**（D4,P4），φ_D +0.50、φ_P +1.29：资源上限收紧使 ID 从互联"净付出"变为受益方；BUNKER 3.297 → 2.414（φ_P −0.85）；SG 2.770 → 2.937（φ_D +0.32）；MY 0.870 → 1.066（φ_P +0.22）。一体化台账：ID 91.1 → 95.6 bn（φ_D −8.15、φ_P +12.71），BUNKER 76.1 → 84.3（φ_P +9.94），MY 25.3 → 33.5（φ_D +6.17、φ_P +2.11），SG 10.0 → 11.8（φ_D +1.53）。(D31,P31) 行 = v3.1 冒烟分摊 + 其他改动按国近似。
- **边界：** 56 时段无季节与跨期储能，只作方向；(D31,P31) 近似误差来自其他改动的线性化（抽蓄 / 新水库项方向不定）；正式归因在 2920×3h 批次上重做（Fable F-22 第 3 点），建议补 (D31,P31) 两次求解把近似换成实测（§0.1 第 6 条）。

## 8. 产出、提交、额度与停止条件（§8）

- **产出（`work/p1_v4_d2a_20261107/`）：** `REPORT.md`、`FABLE_FIXES.md`、`EFB_BASIS.md`、`PHS_STOCK_RECON.md`、`RERANK_D2A_TOP30.csv`、`RERANK_D2A_OWEN_TOP10.csv`、`RERANK_D2A_VS_W15.csv`、`W19_CANDIDATES.csv`、`SMOKE56_D2A.md`、`ATTRIBUTION_56.md`、`CHECKPOINTS.csv`、`DOWNLOAD_CANDIDATES.csv`（13 条，只列不下载）、`EVIDENCE.json`、`PROGRESS.md`、`STATIC_CHECKS.json`、`LEDGER_ENTRY_DRAFT.md`、`rerank/`（重排全部输出）、`tables/`、`evidence/`（含两份文献 JSON、网络差异、零松弛、报警线、检查点参照）、方法脚本 `scripts/`（含参照引擎副本 `scripts/ref/`）；审阅包 `REVIEW_<提交>.zip`（逐成员 SHA256 + CRC32，zip 与 `cache/` 不入库）。
- **测试：** 新增 `test_v4_d2a_fixes.py`（11）、`test_v4_d2a_efb.py`（4）、`test_v4_d2a_supply.py`（7），`test_v4_a2_fallback.py` 扩展；17 个 v4 测试文件 96 过、0 败。全量 `tests/research` 未重跑（≈ 33 分钟；D1 基线 852 / 1 / 58，唯一失败是旧 S1 网络的跨境元数据项，与本步无关）——列为未做。
- **额度：** 求解器 **6 / 6 次**（§6 2 次、§7 4 次；无重试，无参数改动）；本机计算（表重写与参照重跑、检查点、构建 3 组、静态检查、重排、6 次求解与后处理）约 2 小时量级，在 6 h 内；磁盘新增约 3.6 GB（`results_project/v4d2a`：构建 0.66 + 冒烟 0.55 + 归因 1.1 GB；worktree 0.72 GB；临时构建副本 0.53 GB；重排缓存），在 15 GB 内。网页只读文献，未下载数据文件，未访问 UNSD SDMX。
- **停止条件逐项：** SHA 一致；D1 头含 `6142d8ac` 且差异只在交付目录；开关全关逐字节回到 v3.1（A2，56 文件）；修复 F-02 后主算网络无表列以外的变化（C8 对 D1 只有 §3 的预期差异）；静态检查无新的零余量行、无不可行迹象；6 次求解全部 optimal、`ACCEPTED_LAYER2`、失败门在 v3.1 并集内，§6 两次的 ΔV 高于求解前登记的报警线（未触发"查数据链、停下汇报"）；没有改求解档案或 Gurobi 参数；没有写入其他会话的目录、worktree 或分支（重排缓存复制到本目录）；求解日志只读清洗后的副本，没有读取、打印或复制许可内容与登录信息。T04 树干"无法判定"、PH 抽蓄"不修正"不是停止条件，按指令保留现值并在本报告交审阅端。
