# V3 模型独立审查报告（决策清单第 183 项）

- **指令：** `work/p1_v3_review_20261103/V3_INDEPENDENT_REVIEW_INSTRUCTION.md`，SHA256 `65f36a12f2f4844471846ce33e3d25b00ab0c4a5d39990cf9ff65454fe9adb86`，与同目录 `V3_INDEPENDENT_REVIEW_SHA256.txt` 一致后开始。
- **冻结点：** 分支 `codex/v3-20261102` 提交 `6b1a1225`；审查 worktree `/home/jin/wt_v3_review`，新分支 `codex/v3-review-20261103`（自 `6b1a1225` 开出）。`/home/jin/wt_v3_20261102`、`/home/jin/v3s/` 未进入、未改动。
- **审查者：** 新开 Claude Code 会话（Fable），未参与 v3 开发。只读审查：模型代码、配置、输入、网络一律未改；网络未重建；无合并、无 force-push。
- **计算记账：** Gurobi 0 次；HiGHS 0 次（审查全部用只读数组查询完成，未求解）；不连 AutoDL、不连 HPC。本机 Python 只读探针 6 个，合计约 1.2 小时；磁盘新增约 1.0 GB（网络与解后网络副本放在 `/home/jin/v3rev/`，不进仓库）。
- **证据等级：** VERIFIED = 读了代码或网络数组、回执、闸门文件；EXACT = 逐项有理数核验；INFERENCE = 机制解释与量级估计；PROPOSED = 未执行的建议。
- **读过的材料：** `V3_RULES.md`、`V3_DESIGN.md`、`V3_DATA_INTAKE.md`、`V3_CODE_LOCATIONS.md`、`RUN_PLAN_V3.md`、`RUN_PLAN_SCREEN_V3.md`、`V3_LIMITATIONS_ITEM176.md`、`V3_REPORT_SCREEN.md`（其中解释一律当待核实说法）、仓库代码（`scripts_project/` 的 v3 新增模块与 `0a20aefd..6b1a1225` 的全部生产模块差异）、注册表 v3 片段、`results_project/v3/builds_op`（2920×3h）与 `screen_package_v3_dmax/networks`（第 182 项后的 365×24h 三网络）、第一批筛查回收结果（`cloud_results/final_20261103T063207Z/`，轻包全部与 V1/V2 解后网络）、`work/p1_hpr_20261027/`（HPC 运行器与部署包）。**未读** `V3_REVIEW_DECISIONS_*.md`、`V3_SCREEN_*INSTRUCTION*`、`V3_CLAUDE_CODE_INSTRUCTION.md`。
- **证据目录：** `evidence/`（探针脚本 `evidence/scripts/probe1-5.py`、探针输出 `evidence/probe*.json`、`EVIDENCE_INDEX.md` 含 SHA256）。所有数值都可以用脚本在同一网络文件上复现。

## 1. 摘要

| 级别 | 数量 |
|---|---:|
| **S1** | **0** |
| S2 | 5 |
| S3 | 4 |
| 待查问题 | 2 |

**没有 S1。** 在十个维度上，v3 代码做到了规则所写：时间权重与时区正确；需求与注册表逐国逐载体对上（最大偏差 1.3e-9 TWh，唯一差异是规则写明的 VN 生物质溢出 71.86 TWh → 有用热 64.67 TWh）；两情景在 2920×3h 与 365×24h 上的差异只在跨境候选（46 条 AC 线、283 条链路）与 16 条存量线路、9 条存量链路的可扩建标志和上界，时序、全局约束、钩子逐位相同；B6 的目标值口径在两情景间对称（FOM 常数都含，沉没资本都不含，账本分解与目标值之差 1e-10 bn）；Owen 对偶形式的前提（无主右端项 0 行）、恒等式（差 −18,095 EUR）、残差（≤ 9e3 EUR）在第一批筛查的 V1、V2 上都成立；成本表年化逐行复算一致。

S2 的五条都不改变正式结果的方向，但影响对结果的解读、后续敏感性安排与正式路径的准备：

1. **S2-1（设计质疑，局限被低估）：** 365×24h 筛查看不到任何日内平衡，不只是 EV。第一批 V1 解中固定电池与氢罐容量为 0、新建可调机组 0、光伏 2,819 GW + 屋顶 201 GW、陆风 6.6 GW、弃电 2.4 %。筛查的装机结构、节点电价、LA 净出口 132 TWh 与 LA–VN 新建 48.7 GW 都不能作为正式 2920×3h 结果的合理性依据；第 176 项第 7 条只提 EV，低估了这一点。
2. **S2-2（设计质疑）：** 液体船运单价 S-B 的公式只含船的资本与 FOM，按每年 8,000 小时满载往返计，不含燃料、港口与装卸时间；1,000 km 甲醇运费 0.12 EUR/MWh（0.67 EUR/t），比现实海运运费低一个量级。对 B6 的影响可忽略（两情景液体运费 139.6 对 137.4 M EUR，差 2 M EUR），但注册表把它登记为 B 级不当，S-A 更接近现实。
3. **S2-3（实施状态，正式路径）：** 2920×3h 正式路径尚未为 v3 准备：HPC 部署包仍是 v2 代码 `8ed41d97` 与 v2 网络，`run_batch4.sh` 包内版本没有 `BATCH_DEF` 支持；`RUN_PLAN_HPC.md` 全部登记值是 v2 的；早期测速止损的迭代参考（F1 450、F2 250）来自 v2，v3 365×24h 实测 V1 146 次、V2 95 次（DFX v2 V1 335 次），与 E2 下 `no_new_xb` 在 56 时段两次 suboptimal 的历史一起，说明止损阈值需要按 v3 重新登记。
4. **S2-4（设计质疑，影响可能被低估）：** EV 车队代理给出 3.49 TW 充电桩与 7.93 TWh 可调度电池（相当于 3.17 亿辆 50 kWh 乘用车），56 时段冒烟里 E2 对 B6 的效应 +0.44 bn（高于 S1 门槛 0.15 bn）、对总成本 −10.3 bn。flat 与 ×0.5 敏感性安排在正式运行之后，意味着读正式结果时还不知道 B6 与各国受益对这一 C 级代理的敏感程度。
5. **S2-5（测试盲区）：** `apply_ev_structure`（车队代理、早晨下限的时区落位、充电桩可用率）、`_apply_bunker_nodal`、`add_liquid_shipping`（容量上界、过境方向）、`add_demand_layer` 的按载体节点分配分支、`bunker_standalone` 的上游路线搜索都没有单元测试；它们只被网络级静态检查覆盖（这些检查是有效的，见第 4 节，但不是回归测试）。

S3：`BATCH_DEF_2920x3h.json` 的名称与注记过时；`liquid_ship_ckm_td_*` 的等级标签；专线没有长度份额表、账本按长度拆分时静默取 0.5；`DIRECT` 主题清单在两个模块各维护一份。

待查问题：B1 国家净零闸门每次都"不通过"但只是 1e-9 量级的数值差（判据是否该带容差）；按 GEM 状态拆开的 `LA2 1` 水库两部分不再共用库容（已在局限中，只记影响方向）。

## 2. 发现表

| 编号 | 级别 | 类型 | 维度 | 发现 | 对正式结果的影响估计 | 把握 |
|---|---|---|---|---|---|---|
| S2-1 | S2 | 设计质疑（局限低估） | 1、8 | 日聚合消除全部日内平衡：筛查解无固定储能、无新建可调机组，光伏 2,819 GW | 筛查 B6 与装机结构对正式值的指示作用弱于局限条文所述；正式值本身不受影响 | 数组 VERIFIED；影响 INFERENCE |
| S2-2 | S2 | 设计质疑 | 2、5、7 | 船运单价 S-B 公式低估约 5–10 倍；B 级标签不当 | B6 ≤ 0.02 bn（两情景运费差 2 M EUR × 10）；Owen 绝对份额出口国/进口国各移动 ≤ 0.5 bn 但两情景对称，受益变化 ≤ 0.02 bn | 公式 VERIFIED；量级 INFERENCE |
| S2-3 | S2 | 实施状态 | 9 | HPC 正式路径未为 v3 打包；登记值与止损迭代参考仍是 v2 | 不影响数值；不处理则正式运行无法按登记值启动，或止损误触发 | VERIFIED |
| S2-4 | S2 | 设计质疑（影响可能低估） | 7、8 | EV 车队代理（C 级）的灵活性量级决定正式 B6 的 3 % 以上，敏感性排在正式运行之后 | 56 时段 E2 对 B6 +0.44 bn；2920×3h 幅度未知，可能超过 S1 门槛，方向不定 | 56 时段数值 VERIFIED（取自 `RUN_PLAN_V3.md` 第 14 节）；外推 INFERENCE |
| S2-5 | S2 | 测试盲区 | 10 | 五处影响结果的 v3 逻辑没有单元测试 | 当前网络已被静态检查证明正确；回归风险在后续改动 | VERIFIED |
| S3-1 | S3 | 表述 | 9 | `batch_def/BATCH_DEF_2920x3h.json` 名称写"before X1b"、注记写"登记值必须重做"，而登记的哈希已是第 180 项后的网络 | 运行器只用哈希，不受影响；操作者会被误导 | VERIFIED |
| S3-2 | S3 | 表述 | 7 | `liquid_ship_ckm_td_{methanol,oil,ammonia}` 登记为 B 级，但由 C 级假设（航速、运营小时、公式）推导 | 无 | VERIFIED |
| S3-3 | S3 | 表述 | 6 | 专线不在任何 `XB_LENGTH_SHARES_*.csv` 中，账本的按长度拆分静默取 0.5（`length_shares_missing` 列出 6 条） | 主值 α 0.5 不受影响；按长度敏感性对 LA–TH 失真 | VERIFIED |
| S3-4 | S3 | 注释/维护 | 6 | `DIRECT` 主题清单在 `s4d_ledger.py:213` 与 `m12_allocation.py:194` 各维护一份，v3 两处都加了运费主题 | 现在一致；将来漏改一处会使 `direct_costs_minus_objective` 对不上 | VERIFIED |
| Q-1 | 待查 | — | 3、9 | B1 国家净零闸门在五次筛查全部不通过，最终大气存量 0.005–1.3 tCO₂（相对 1e-9） | 只是数值信息；但验收文档要反复解释 | VERIFIED |
| Q-2 | 待查 | — | 3 | 拆开的 `LA2 1` 水库两部分各自带 7.1 小时库容，不再共用 | 方向：略高估调节能力（两个 7.1 h 库 vs 一个 7.1 h 库，容量比例分配后合计库容不变，但调度解耦）；量级估计 < 0.01 bn | INFERENCE |

## 3. 发现详情

### S2-1 日分辨率筛查看不到任何日内平衡，第 176 项第 7 条低估了这一点

- **类型：** 设计质疑（局限被低估）。
- **证据（VERIFIED，`evidence/probe5.json`、`evidence/probe3b.json`，第一批筛查 V1 `integrated_DFX_365X24H_solved.nc`，SHA256 见 `V3_REPORT_SCREEN.md` 第 1 节）：**

| 量 | V1（一体化） | V2（`no_new_xb`） |
|---|---:|---:|
| 光伏 `solar` / `solar rooftop` 装机 | 2,818.9 / 201.4 GW | 2,542.3 / 274.3 GW |
| 陆风 / 海风装机 | 6.6 / 0 GW | 18.5 / 5.3 GW |
| 固定电池 `battery` + `home battery` 容量 | 0 GWh | 0 GWh |
| `H2 Store Tank` 容量 | 0 GWh | 0 GWh |
| 新建 OCGT / CCGT / H2 透平 / 燃料电池 | 0 / 0 / 0 / 0 GW | 0 / 17.8（CC）/ 0 / 0 GW |
| 存量 CCGT 129 GW 的年发电 | 7.4 TWh | 112.6 TWh |
| 电力总发电 | 4,271 TWh | 4,034 TWh |
| 光伏占发电 | 91 % | 86 % |
| 风光弃电 | 104.6 TWh（2.4 %） | 120.4 TWh（3.0 %） |
| 节点电价年均（SG / ID / TH） | 52.6 / 33.6 / 29.4 EUR/MWh | 95.3 / 32.5 / 25.5 EUR/MWh |

- **机制（INFERENCE）：** `to_daily` 把每天 8 个 3 小时值取平均（`daily_resolution.py:22-26`），光伏出力、负荷、EV 形状全部被抹平成日均值。日均值下光伏像基荷一样可靠，电池、氢罐、调峰机组的全部价值来自日内平衡，所以最优解一律不建。这同样作用于 v2 筛查，也同样作用于 V3、V4、V5。
- **对正式结果的影响估计：** 正式 2920×3h 网络必须用储能、可调机组或互联来度过夜间与雨季多云日，装机结构与跨境流会与筛查解有质的差别。筛查给出的 B6 = 14.35 bn、LA 净出口 132 TWh、LA–VN 线路 48.7 GW（`probe3b.json` `xb_elec_capacity_gw`）都是"日均光伏可直接外送"的结果。方向无法由筛查推断：互联既是日内平衡的替代品（互联价值在 3 小时分辨率下可能更高，因为能跨时区调配光伏），也与储能竞争（可能更低）。`V3_RULES.md` 第 10 节第 7 条只写"看不到 EV 日内效应，筛查 B6 与正式值差距可能大于 v2"，没有写明筛查的装机结构、节点电价与跨境流在结构上不可用于合理性判断。补充 06 的 EV 诊断已经触及其中一角（EV 电池在日分辨率下被当作多日储能），但没有推广到储能与可调机组全部为 0 这个事实。
- **最小修正建议（PROPOSED）：** 在第 176 项第 7 条补一句：日分辨率解不含任何日内平衡，固定储能与新建可调机组容量为 0，筛查的装机、电价、跨境流不作合理性对照；筛查只用于 B6 符号、账本与分摊程序的检验。论文方法说明同此。不需要改任何代码。
- **把握：** 数组 VERIFIED；影响方向 INFERENCE。

### S2-2 液体船运单价 S-B 的推导低估约 5–10 倍

- **类型：** 设计质疑（数据适配）。
- **证据（VERIFIED）：** `scripts_project/v3_data.py:41-43`：`ckm = (annuity(7 %, 寿命) + FOM) × investment / (capacity × 热值 × speed × hours / 2)`，`speed` 27.78 km/h（15 节），`hours` 8,000 h/a，皆为 C 级假设（`fragments/v3.csv` 第 26、31 行）。technology-data v0.15.0 `MeOH transport ship`：investment 3.5e7 EUR、FOM 5 %、寿命 15 a、容量 75,000 t（本身是"Assume comparable tanker as for LOHC"，Runge et al. 2020 的借用值）。复算：年成本 5.593e6 EUR ÷ (75,000 t × 5.528 MWh/t × 111,120 km) = 1.214e-4 EUR/(MWh·km)，与注册表 `liquid_ship_ckm_td_methanol` 一致。1,000 km 单程运费 0.121 EUR/MWh = 0.67 EUR/t 甲醇。
- **机制（INFERENCE）：** 公式隐含每年 8,000 小时全部在航、满载去空载回、没有港口与装卸时间、没有燃料、保险、人员与港口费用。按 1,000 km 航程，往返各 1.5 天加港口约 2 天，年航次约 73 而不是 111；加上与资本同量级的运营与燃料成本，单位运费约为 S-B 的 4–6 倍；按市场价判断（东南亚区内液体化学品海运每吨 8–15 美元量级）则为 5–10 倍，即 1–2 EUR/MWh。S-A（IEAGHG 口径，1,000 km 约 1.46 EUR/MWh）更接近这一范围。
- **对正式结果的影响估计：** 第一批筛查账本（`COUNTRY_COST_LEDGER.csv`）的 `liquid_ship_freight` 合计：V1 139.6 M EUR、V2 137.4 M EUR、V3 135.5 M EUR，两情景差 2.1 M EUR；单价放大 10 倍，B6 变化上限约 0.02 bn，远低于 S1 门槛。各国 Owen 绝对份额会移动（出口国 ID 的运费从 44 M 变为约 0.4 bn，被进口国更高的母线价格抵补），但两情景同向，受益（差）变化在 0.02 bn 量级。船运量本身对单价不敏感（SG 的 466 TWh 船用甲醇别无来源：本地生产 0，东盟外进口价 145 EUR/MWh 对 ID 母线价 98 + 运费）。
- **最小修正建议（PROPOSED）：** 把 S-A 作为主值或把 S-B 的航速、运营小时改为含港口时间与运营成本的口径（另给来源），±50 % 敏感性改为覆盖 S-A 到 S-B 的区间；注册表等级见 S3-2。不改变 B6 的结论。
- **把握：** 公式与数值 VERIFIED；现实运费量级 INFERENCE（审查者按行业常识估计，未检索文献）。

### S2-3 2920×3h 正式路径尚未为 v3 准备

- **类型：** 实施状态（不是代码缺陷）。
- **证据（VERIFIED）：**
  - `work/p1_hpr_20261027/hpc_package/`：`code_8ed41d97.tar.gz`（v2 代码）；`networks/integrated_2920_3h_unsolved.nc` 63,873,447 B（v2 网络 `08879f0b…`），不是 v3 的 `1bddacb7…`（72,050,070 B）；`run_batch4.sh` 内 `BATCH_DEF` 出现 0 次（v3 的 `research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh:51` 才有）。
  - `RUN_PLAN_HPC.md` 第 1、10 节登记的网络、字节、构建提交全部为 v2。
  - `scripts_project/b4_batch4.py`（v3 版）用 `batch_def.load_def()` 读包内 `BATCH_DEF.json` 替换运行表与登记哈希，并通过 `batch_def.input_receipt` 核对 `no_new_xb` 的变体回执链（`batch_def.py:26-33`）；`batch_def/BATCH_DEF_2920x3h.json` 登记 F1 `1bddacb7…`、F2 `b262f6aa…`、构建提交 `3cb20131`，与我在 `results_project/v3/builds_op` 上复算的 SHA256 一致（`evidence/probe1.json` 之前的 `sha256sum` 记录在 `EVIDENCE_INDEX.md`）。
  - 早期测速止损：`RUN_PLAN_HPC.md` 第 5 节第 2 条，F1 450 次、F2 250 次为 v2 参考（`BATCH_DEF_2920x3h.json` 的 `iterations_reference` 同值）。v3 365×24h 实测：V1 146 次、V2 95 次（`V3_REPORT_SCREEN.md` 第 1 节），DFX v2 V1 335 次。56 时段 E2 下 `no_new_xb` 在档案 A 与 `formal_barrier_1e6_t16` 各一次 suboptimal（`RUN_PLAN_V3.md` 第 9、14 节）。
- **机制与影响：** 不打包就没有 v3 正式运行；参考迭代数偏高只会让止损更宽松（不误触发），但 `no_new_xb` E2 的末段发散历史与 LP 规模 +4 % 都没有进入时限与止损的登记依据。`TimeLimit` 864,000 s 与墙钟沿用 B4P 外推（v2 F1 最高约 190 h）。
- **最小修正建议（PROPOSED）：** 以 ≥ `6b1a1225`（含第 182 项）的代码重打 HPC 包，包内放 `BATCH_DEF.json`、v3 两个 2920×3h 网络与变体回执；按 v3 的 365×24h 实测重写 `RUN_PLAN_HPC.md` 的迭代参考与机时预计；`BATCH_DEF_2920x3h.json` 的注记同步（S3-1）。
- **把握：** VERIFIED。

### S2-4 EV 车队代理的灵活性量级决定正式 B6 的可观部分，敏感性排在正式运行之后

- **类型：** 设计质疑（影响可能被低估；第 176 项第 4 条已列为局限）。
- **证据（VERIFIED）：** 网络元数据 `research_ev`（`evidence/probe1.json`）：`fleet_equivalent_vehicles` 3.17e8，`battery_mwh_total` 7.93e6（= N × 0.05 × 0.5），`charger_mw_total` 3.49e6（= N × 0.011），`mwh_per_vehicle_year` 2.256（12,000 km ÷ 5,319 km/MWh，`fragments/v3.csv` 第 5–6 行，C 级，`sensitivity_low/high` 0.5 / 2 倍）。56 时段冒烟（`RUN_PLAN_V3.md` 第 14 节）：EV 效应 flat − E2 对总成本 +10.28 / +10.72 bn，对 B6 +0.44 bn。
- **机制（INFERENCE）：** PyPSA-Eur 的每车参数（50 kWh 电池、11 kW 充电桩）是欧洲乘用车；东盟 2050 电动出行中两三轮车能量占比高，其电池/年电耗比约为乘用车的三分之一、充电桩/年电耗比约一半。按能量等比折算会把车队的总电池与总充电功率高估约 1.5–2 倍（若两三轮车占一半能量）。在 3 小时分辨率下，716 TWh 的可整日平移负荷是系统里最大的单一灵活性来源（冒烟里光伏 +260 GW），它与跨境互联既互补又替代，对 B6 的净效应在 56 时段为 +0.44 bn（3.5 %），超过 S1 的 0.15 bn 门槛。
- **对正式结果的影响估计：** 方向不定、幅度可能超过 1 %；按现有安排（`RUN_PLAN_V3.md` 第 15.6 节）flat 与 ×0.5 要等正式运行之后再做，读正式结果时无法知道 B6 与各国 Owen 受益对这一 C 级代理的敏感程度。
- **最小修正建议（PROPOSED）：** 把 ×0.5 车队（或 flat）的一体化与 `no_new_xb` 两次运行并入正式批次的登记（即使排在 F1/F2 之后），并把 Owen 符号的稳健性判断推迟到敏感性结果到位；不改主算规则。
- **把握：** 数值 VERIFIED；折算倍数 INFERENCE。

### S2-5 测试盲区

- **类型：** 测试覆盖。
- **证据（VERIFIED，`grep -rn` 于 `tests/`）：** `apply_ev_structure`、`_apply_bunker_nodal`、`add_liquid_shipping` 在 `tests/` 中只出现在注释或根本不出现；`bunker_standalone` 在 `test_m12_allocation.py` 中只作为字典被替身；`add_demand_layer` 的 `car_shares` / `proc_shares` 分支（`s2_layers.py:689-153`、`:874-244`、`:1017-279`）没有单元测试。`tests/research/test_v3.py` 覆盖的是：配置身份、`ev_series` 的时钟与能量、周型表、镍能耗、工业总量守恒、节点份额和为 1、`ship_unit` 单价、枢纽表、冒烟评估、X1/X1b/第 179、180 项的结构检查、B13、`no_new_xb` 存量模式。`test_s1_adapter_daily_v5.py::DailyStoreBounds` 覆盖第 182 项。本次在审查 worktree 运行 `test_v3.py`、`test_s1_adapter_daily_v5.py`、`test_v3_runners.py`：62 项通过（无求解器，66 s）。
- **现有覆盖方式：** 这些逻辑的正确性目前由网络级静态检查保证：需求对表（`v3_static.demand_check`，本次独立复算最大偏差 1.3e-9 TWh）、`source_bus_problems`、`scenario_diff`、`stock_check`。它们对**当前**网络有效，但不是回归测试：例如 `INDUSTRY_CARRIER_NODE_SHARES_V3.csv` 若缺某国某载体的键，`S(k)` 返回 0 会静默丢掉该载体需求（`s2_layers.py:184`），只能靠静态检查在构建后发现（本次核对：11 国所有非零载体都有份额键，`evidence/probe2.json`）。
- **最小修正建议（PROPOSED）：** 四个玩具网络单元测试：(i) `apply_ev_structure` 对 +6.5/+7/+8/+9 四个时区各一个节点，断言 `e_min_pu` 落在含当地 7 时的那个 3 小时时段、年能量守恒、充电桩 `p_nom = N × 0.011`；(ii) `_apply_bunker_nodal` 的终端母线国家标签、CO₂ 端口改接与链路所有者；(iii) `add_liquid_shipping` 的 270 + 7 条、容量上界 = 年需求 / 8,760 × 10、化石油只入 LA；(iv) `add_demand_layer` 在缺份额键时报错而不是静默为 0。
- **把握：** VERIFIED。

### S3-1 `BATCH_DEF_2920x3h.json` 的名称与注记过时

`batch_def/BATCH_DEF_2920x3h.json`：`name` 写 "X1 APG stock, before X1b"，`note` 写 "X1b changes the networks: the registered values below must be redone"，而 `registered_sha` 已是第 180 项后的 `1bddacb7…` / `b262f6aa…`、`build_commit` `3cb20131`。运行器只读哈希，不受影响。建议改写两段文字。VERIFIED。

### S3-2 `liquid_ship_ckm_td_*` 的 B 级标签

`fragments/v3.csv` 第 20–22 行 tier B，但推导用到的航速、运营小时是 C 级假设（第 26、31 行），公式本身也是推导。按注册表约定应为 C（且 ±50 % 的区间应覆盖 S-A）。VERIFIED。

### S3-3 专线无长度份额，按长度拆分静默取 0.5

`V1/LEDGER_IDENTITY.json` 的 `diagnostics.length_shares_missing` 列出 6 条 `dedicated plant line`；`s4d_ledger.py:198-200` 缺份额时取 0.5。主值 α 0.5 不受影响；"按长度"敏感性对 LA–TH 实为 0.5。建议在 `V3_RULES.md` 第 2.3 节写明专线不入长度份额表、按长度拆分对专线等于 0.5。VERIFIED。

### S3-4 `DIRECT` 主题清单两处维护

`s4d_ledger.py:213` 与 `m12_allocation.py:194` 各有一份 `DIRECT`，v3 两处都加入 `liquid_ship_freight`、`liquid_transit_freight`，现在一致；建议其一引用另一（`V3_CODE_LOCATIONS.md` 第 5 节已提示这个风险）。VERIFIED。

### Q-1 B1 国家净零闸门每次都不通过

五次筛查 `V5_GATES.json` 的 B1 全部 `passed: false`，而 `EMISSIONS_BY_COUNTRY.json` 的国家最终大气存量在 0.005–1.3 tCO₂（V1）、−0.02–0.011 t（V2），相对年度流量 1e-9 量级；`B1_S4B`（带预算）通过。B1 看来是严格 ≤ 0 的判据，内点解永远差一个 FeasibilityTol。它被列为"数值信息"没有错，但每份报告都要解释一次。需要确认 B1 的判据定义（`v5_gates.py` 的 `gate_b1_country_net_zero` 本次未读）后再决定是否该带 S4B 的预算。

### Q-2 拆开的 `LA2 1` 水库两部分不再共用库容

`V3_RULES.md` 第 10 节第 8 条已写入。本次核对（`evidence/probe4.json`）：拆分前后 `p_nom`（564 → 440 + 124）、年固定运维费、年入流（1.5414 TWh）逐项守恒，`max_hours` 7.145 h 两部分照抄。影响方向：两部分各带与容量成比例的库容，合计库容不变，但调度解耦使总调节能力略高于单库；量级（124 MW × 7.1 h ≈ 0.9 GWh 库容）对 B6 的影响估计 < 0.01 bn。INFERENCE。只记录，不要求处理。

## 4. 已查、没问题（逐维度）

所有数值出自 `evidence/probe*.json`，脚本在 `evidence/scripts/`，输入是 `screen_package_v3_dmax/networks/*.nc`（第 182 项后的 V1、V2、V3）、`results_project/v3/builds_op/*/*_2920_3h_unsolved.nc`、第一批筛查的 V1/V2 解后网络与轻包。

### 维度 1 时间处理

- **快照权重（VERIFIED）：** 五个网络 `snapshot_weightings` 的 objective / generators / stores 三列全等于 3 h（2920）或 24 h（365），合计 8,760 h；快照 2013-01-01 00:00 起，UTC。
- **聚合方式（VERIFIED，读 `daily_resolution.py`）：** 2920×3h → 365×24h 全部时变输入取 8 个值的精确有理数平均；唯一例外是 Store 的 `e_min_pu` 取日最大、`e_max_pu` 取日最小（第 182 项）。dmax 三网络中 96 个 EV 电池的 `e_min_pu` 全年 365 天都是 0.8，没有任何 `e_max_pu`。2920 网络中每个电池每天恰有一个 3 小时时段为 0.8。
- **时区（VERIFIED）：** 2920 网络里 EV 早晨下限落在：UTC+7 的 41 个节点 → UTC 00:00 时段（当地 07–10 时）；+8 的 31 个 → UTC 21:00（当地 05–08）；+9 的 7 个 → UTC 21:00（当地 06–09）；+6.5 的 17 个 → UTC 00:00（当地 06:30–09:30）。每个窗口都含当地 7 时。EV 负荷日峰起始落在当地 14–16 时（3 小时窗 14–19 时），与设计的 16–19 时一致。周型按**当地**星期分组：周一至周五 1.02–1.03、周六 0.99、周日 0.88，与 `EV_WEEKLY_LOCAL_SHAPE_V3.csv` 的星期均值一致（我最初按 UTC 星期分组看到"周五最低"，是分组口径的假象，不是缺陷）。充电桩可用率 0.748–0.798，均值 0.776，与 RAMP 一致。
- **储能首尾（VERIFIED）：** `e_cyclic=True`：EV 电池 96、电池 98、家用电池 98、氢罐 97、液体储罐 33、`co2 stored` 97；非循环：11 个国家大气（`e_min_pu −1`，`e_initial 0`）、燃料舱账户、7 个封存库、11 个东盟外封存、85 个固体生物质与 15 个沼气资源池（`e_initial` 为年潜力）。解后 V1 中 EV 电池 `e ≥ e_min_pu × e_nom` 的最小余量 3.6e-5 MWh（无违反）。
- **56 时段截短（VERIFIED，读 `s2_solve.py:20-35`）：** 权重放大为 8,760/N，年度上限不缩放（PyPSA-Eur 代表期约定）；只用于冒烟，不进正式路径。第 8.2 节的 B8 截短假象解释与周型机制相符。

### 维度 2 单位与换算

- 成本表 `fixed = (annuity(lifetime, r) + FOM/100) × investment` 对 36 个抽样行逐行复算，相对偏差 ≤ 4e-12（VERIFIED）；折现率 0.07（293 行）/ 0.04（8 行，屋顶与分散供热）。网络 `capital_cost`：onwind、电池、电解、OCGT/CCGT（按效率折算到燃料侧）与成本表一致；`solar` 发电机取 `solar-utility` 行（29,345.8 EUR/MW/a），不是 `solar` 行，由 `s4c_layers.py:72` 的映射规定，不是错误。
- 燃料价 WEO 2025 STEPS 2050：气 27.07、油 35.32、煤 8.86 EUR2020/MWh，与网络 `marginal_cost` 一致；换算链（USD MER 2024 → EUR2020）量级复核合理。热值 5.528 / 5.166 / 11.9 MWh/t；汇率 0.8772 EUR/USD（ECB 2020）。
- 专线 FOM：0.015 × 493.1 EUR/(MW·km) × Σ(MW × km) = 15.87 M EUR/a，与规则一致（EXACT）；电力存量 FOM 8.99 M，合计 `existing_cross_border_fom_eur` 24.86 M，两情景相同。
- EV：`a = 12,000 / (53.19 × 100) = 2.256 MWh/车·年`，`share_transport_electric_efficiency` 的注册表描述 "1 MWh_el = 53.19 × 100 km" 与代码一致。

### 维度 3 守恒

- **需求对表（VERIFIED，`probe4.json`）：** 四个网络按（国家 × 载体）与 `DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv` 比较：非溢出载体最大偏差 1.28e-9 TWh；表 7,628.637 TWh、网络 7,621.451 TWh，差 7.186 TWh = VN 生物质溢出 71.860 TWh × (1 − 0.9)，有用热侧回收 64.674 TWh（第 133 项规则）。燃料舱 130 条 ASEAN 标签负荷 725.136 TWh（航空 239.550 + 船用 485.585），落在本国节点。EV 715.964 TWh，96 条时序。
- **工业（VERIFIED）：** 网络工业负荷 3,065.6（Industry）+ 747.3（燃料表计）TWh；`INDUSTRY_CARRIER_NODE_SHARES_V3.csv` 的 `main` 案对 11 国所有非零载体都有份额键（无静默丢失）；`PROCESS_NEU_NODE_SHARES_V3.csv` 三个键齐全。`test_country_totals_conserved` 通过。
- **净零约束写法（VERIFIED，读 `country_carbon.py`、`s4c_layers.py`、`s2_layers.py`）：** 每国大气 Store 末时段 ≤ 0（`research_country_co2_limit-<c>`）；排放只经 Link 的大气端口记在所有者国（物理端口的唯一国家），发电机载体强度全部清零（U4）；过程排放经 `{node} process emissions` 母线进入；塑料焚烧进本国大气；燃料舱排放进 `co2 bunkers ASEAN`，单独 ≤ 0，且账户没有任何移除路线，所以国际航空化石航煤实际为 0（V1 化石表计 −1e-6 TWh，非化石 239.55 TWh）；封存上限 `co2 sequestered <c>` 末时段 ≤ 年潜力（ERIA/GCCSI p50 ÷ 50 年）。解后：11 国大气末值 ≤ 1.3 t；KH、PH、VN 封存上限绑定；DAC 29–36 Mt，BECCS（工业生物质直燃 CC）359 Mt。
- **生物质与可再生潜力（VERIFIED）：** 固体生物质潜力 Store 1,990.8 TWh 合计；VN 绑定（B15、B3 诊断）；B15 的国家表与潜力表一致。

### 维度 4 两情景差异

- **逐组件含时序比较（VERIFIED，`probe1.json` `diff_*`）：** 2920×3h 与 365×24h 两对，一体化 → `no_new_xb`：删除 46 条 AC 线（全部 `cross_border`）、283 条链路（H2 管 110、气管 110、CO₂ 管 55、DC 8，全部 `cross_border`）；改变列只有 16 条存量 AC 线的 `s_nom_extendable`、`s_nom_max` 与 9 条存量链路（气管 7、DC 2）的 `p_nom_extendable`、`p_nom_max`；**所有时序无差异**；全局约束无差异；钩子清单相同；元数据只差 `scenario`、`research_config*`、`research_cross_border` 与新增 `research_variant`。存量线路 `s_nom = s_nom_min`（16/16），存量链路 `p_nom = p_nom_min`（9/9），所以一体化中沉没资本经 PyPSA 常数扣除的量等于 `no_new_xb` 中不计入的量。
- **一体化 → 完全隔离（V3）：** 另有源母线 5 条、源链路 5 条、专线 6 条与拆分组件的差异（第 179、180 项的直接结果），B2B 换流器 `p_nom` 两处（第 105 项规则）。符合规则。
- `gate_b5_no_new_xb` 对两对网络通过；`stock_check` 8 对 2,870 MW + 专线 5,999 MW。

### 维度 5 成本

- 年化、寿命、FOM 见维度 2。存量设备：`existing_annual_fixed_om_eur` 合计 10.050 bn/a（Generator 0.814、Link 8.004、StorageUnit 1.233 bn），作为固定为 1 的列进目标，两情景相同。
- **目标函数常数项（EXACT，`probe3b.json` `objective_decomposition_bn`）：** V1：新建资本 174.404 + 变动 79.117 + 常数 10.075 = 263.597 bn，与 `n.objective` 差 1.0e-10 bn；V2：176.387 + 91.483 + 10.075 = 277.945 bn，差 1.1e-10 bn。`s2_solve.py:296-307,416` 在 `--scaling on` 下把常数列移出 LP 再加回（V1：+10.075 − 7.705 = +2.370 bn，即报告中的"目标值含常数项 263.5966，Gurobi 261.2262"），所以 Gurobi 目标值与项目目标值的差不是口径问题。沉没资本（PyPSA `objective_constant`，V1 7.705 bn、V2 7.534 bn）两情景都不进目标，差额 0.171 bn 正是存量跨境资产的沉没资本，在 `no_new_xb` 中因不可扩建而本来就不计——B6 对此对称。
- 各国成本表：`integrated_costs_active_research.csv` 与 `disconnected_costs_active_research.csv` SHA256 相同（`SHA256SUMS`）。

### 维度 6 记账与分摊

- **账本恒等式（VERIFIED）：** V1、V2 的 B16 相对误差 3.9e-13 / 3.8e-13；`asean_pool_surplus` 0（东盟池无行）。
- **Owen 对偶形式（VERIFIED，`m12_owen/OWEN.json`）：** 前提通过（无主与未归属的非零右端项行均为 0；V1 国家行 1,214,191、国家对行 2,287、燃料舱行 47,450；V2 国家对行 22,995，因存量链路改为固定容量后每时段的流量上界行归国家对，一体化中同一权利表现为 `*_nom-lower` 的单行，两种归属都正确）；恒等式差 −18,095 EUR（V1）、−3,478 EUR（V2），远小于 0.01 bn；市场形式 − 对偶形式 = KVL 环路转移 + 残差，残差 ≤ 9e3 EUR，KVL 转移最大 TH −89.2 M（V1）；非齐次耦合族为空。
- **右端项归属（读 `m12_rhs_audit.py`）：** 节点平衡按负荷所有者拆分（燃料舱负荷 → BUNKER）；固定容量行、资源潜力、封存上限、国家净零、燃料舱净零各归其国或燃料舱；跨境固定行归国家对，α 0.5，区间 [0, 1] 报告；船运链路归出口国（容量不绑定，对偶 0）。与 Owen（1975）线性生产博弈的要求相符。
- **对偶的符号、尺度与权重：** 账本用 `buses_t.marginal_price × snapshot_weightings.objective`（PyPSA 已把节点对偶除以权重），对偶形式直接用约束对偶 × 右端项；`v3_smoke_eval.py` 对存储的 `mu_upper` 除以权重（第 9 节注记）。V1 节点电价 0–1,223 EUR/MWh，液体母线价甲醇 96.5–99.5、氨 76.5–80.0、FT 油 76.8–78.7、化石油 35.32（LA 36.85 = 过境加价）。
- **燃料舱参与者：** 严格单独成本 106.4 bn，V1 份额 66.59、V2 66.38 bn，受益 −0.210 bn，区间内恒负；个体理性按 D10 口径通过。
- **市场结算形式的实现（读 `s4d_ledger.py`）：** 船运 `maritime_trade` 归出口国、在进口国母线结算（`liquid_trade_<carrier>`）；源链路零成本、两端都在 LA，账本无行；专线为 `XB:LA|TH` 走廊实体，租金与 FOM 按 α 拆分。`test_179_ledger_books_the_source_link_to_laos` 覆盖。

### 维度 7 数据来源与适配

- 注册表 v3 片段 41 行：B 级 11 行（APG、EPPO、GEM、Wei 2020、technology-data 船行、USGS 表）、C 级其余；`xb_stock_la_th_dedicated_lines` 保持 DATA_PENDING（X1b 已以专线表实施，这一行是历史登记）。
- 欧洲参数搬用：RAMP 26 国 EV 周型（C，已列局限）；PyPSA-Eur 每车电池/充电桩（见 S2-4）；JRC-IDEES 与 PyPSA-Eur 2050 载体比例（v2 既有）；technology-data 船行（见 S2-2）。镍用 Wei et al. 2020 的 RKEF（中国工艺），对印尼镍铁适配合理。
- 专线表：11 个项目、合同 5,427 + 572 MW，`network_fleet_mw ≥ contract_mw` 逐项成立（Hongsa 1,878 ≥ 1,473；Nam Theun 2 1,070 ≥ 948；Theun-Hinboun 440 ≥ 220 + 220）。

### 维度 8 结果合理性（第一批筛查 V1、V2、V4、V5）

- 可以作为依据的只有年度能量账：SG 船用甲醇 466 TWh 全部船运（ID 81–83 %、TH 14 %、MM 3–4 %），东盟外进口 0；甲醇价格各国 96–100 EUR/MWh，低于进口价 145；船运上界利用率最高 7.7 %，277 条容量对偶全部 0；LA 专线 V2 14.08 TWh（26.8 %），逐月 8–9 月 87–90 %、1–4 月 ≤ 3 %，与来水季节一致；Hongsa 褐煤 2e-8 TWh（净零约束下不运行）。这些与规则预期一致。
- 不能作为依据的：装机结构、节点电价、跨境流量（见 S2-1）。按指令只指出"明显不合理并能说明机制"的地方，S2-1 是唯一一条；其机制是日聚合而不是模型错误。
- 本次未用网络搜索对照公开展望：筛查解的结构是日分辨率假象，与 AEO8 / IRENA 的小时级或容量数据不可比，对照要等 2920×3h 结果。

### 维度 9 正式运行路径与数值

- 求解档案 `formal_barrier_1e6_t16`（Method 2、Crossover 0、BarConvTol 1e-6、Threads 16）：第一批筛查 Gurobi 日志末次迭代原始 − 对偶目标 V1 约 8e3 EUR、V2 约 4e3 EUR（相对 3e-8），互补 2e-3，远好于 BarConvTol 允许的 1e-6（约 0.26 bn）；C1 (a) 的 0.01 bn 标准因此有充足余量，C1 (b)(c) 全过，对偶形式可用。
- 验收闸门测的是：G2（网络 SHA、配置子集哈希、回读）→ 输入身份；C1 (a) 返回解的原始/对偶目标差 → 总成本精度；(b) 违反量 × 对偶按国 → 账本精度；(c) KKT 残差对结算的影响 → 节点价精度；B16 → 账本恒等；B6 → 符号。它们测的是"解的精度与结构身份"，不是模型是否正确——这是它们的定位，没有问题。B1 见 Q-1。
- 运行器：`b4_batch4.py` / `dfx_batch.py` 读 `BATCH_DEF` 后用变体回执链核对 `no_new_xb`（`batch_def.input_receipt`），分进程求解、时限、内存止损、续跑语义沿用 B4P/HPR（v2 已独立审查）；`test_v3_runners.py` 7 项通过。v3 包未建，见 S2-3。

### 维度 10 测试盲区

见 S2-5。另记：`tests/research` 全集在 v3 分支的历史记录为 752 通过 / 58 跳过 / 3 失败（3 项与 v3 无关，`RUN_PLAN_V3.md` 第 6 节），本次只跑了与 v3 直接相关的三个文件（62 通过）。

## 5. 本次没能覆盖的部分及原因

1. **2920×3h 的解后数值：** 没有任何 2920×3h 的 Gurobi 结果（正式运行未做，本机 56 时段冒烟结果不在允许读取的清单内），对偶质量、Owen 残差、B6 精度在正式分辨率上的表现只能由 365×24h 推断。
2. **第 182 项后的重跑：** `screen_package_v3_dmax` 的三次运行尚未（或正在）进行，本报告的解后核查用的是第一批（EV 下限 0.1）的 V1、V2；网络侧核查用的是第 182 项后的三网络。
3. **原始数据层：** 没有重新从 GEM、USGS、DOSE、APEC 图片、EPPO/ACE PDF 推导 v3 的表（节点份额、子部门能量、专线容量），只核对了表与网络、表与规则之间的一致性。
4. **v2 继承层：** 成本层、需求锚表、Astar 曲线、碳记账框架按指令为不变项，只做了与 v3 接口处的一致性核查。
5. **公开展望对照：** 未做网络搜索（理由见维度 8）。
6. **HiGHS 截短路径检查：** 未重复（`RUN_PLAN_V3.md` 第 6 节已记录两轮；本次所有核查不需要求解）。
7. **B1 闸门判据代码：** 未读 `gate_b1_country_net_zero`（见 Q-1）。

---

写完即停止，等待用户与审阅端分级处理。
