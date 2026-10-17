# S4C 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4C_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-16 21:50 SGT），开始前核对 SHA256 = `e1bad922b036bcb425cb9b77853e5cc4f9ca771c59c90da1a23321b89a1dcdd3`，与 `S4C_INSTRUCTION_SHA256.txt` 一致（2026-10-16，VERIFIED）。模型 Opus 5.5 xhigh。

分支 `codex/s4c-allocation-fixes-20261016`，自 S4B 最终提交 819ade64 开出（已核实 = PR #26 的 headRefOid `819ade64b79114c97cf49e5af16b43c42dddf356`）；draft PR 叠在 #26 上（基分支 `codex/s4b-fixes-calibration-20261016`）。
仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4c_20261016/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4c_20261016\`。
求解环境：`/home/jin/miniforge3/envs/pypsa-earth/bin/python`，`PYTHONHASHSEED=0`，Gurobi 12.0.3（`GRB_LICENSE_FILE=/home/jin/gurobi.lic` 只读引用）；止损：56×3h 单次 30 分钟、非最优即停不重试（例外：S4C-5 的 B 档 crossover 诊断，S4C-6 不互联主算非最优时停下报告后跑诊断）。
资源（第 7 条）：只允许两类下载——(1) CO₂ 船运与海外封存成本公开文献（第 89 项）；(2) 分国融资成本公开数据或报告（第 90 项）；总量 ≤ 300 MB，单个 > 50 MB 先报告；其他下载、本机单次计算 > 1 h 或 > 约 8 GiB、任何云端操作，先报告。
决策清单原文：本机（D:\ 工作区与 WSL 仓库）未找到决策清单文件；按指令逐项摘要执行（与 S4B 相同情形）。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4C-0 | 化石燃料价格改 STEPS（第 85 项）；小项（第 86 项）；折现率（第 90 项） | 完成 | 901b354e | `research.fuels.price_scenario: steps`（气 27.07、油 35.32、煤 8.86 EUR2020/MWh；NZE 13.67/11.62/5.17 低价敏感性；CPS 可选）；构建时断言三燃料同一情景且网络价格 = 登记值（`s4c_layers.check_fuel_prices`）；褐煤保持成本层 6.62（WEO 无褐煤价）；BtL 投资 × 效率 113,726（PyPSA-Eur 4230–4231 行，S4B 写的 4227–4228 更正）；4 个 gate4 测试改断言已接受状态；折现率盘点（成本层 0.07，屋顶光伏等 8 行 0.04，存量无年金）；`research.finance.wacc_mode: uniform`，`country_specific` 只实现（IEA 资本成本观察站分国值为名义税后本币，11 国模型实际值全部 DATA_PENDING）；三个构建静态 PASS（各 43 s、0.69 GiB）；`tests/research` 439 通过 / 0 失败 |
| S4C-1 | 风光候选成本改用第 50 项成本层；全组件成本审计（第 82 项） | 完成 | d7e93d20 / 24c0b552（停止前部分提交）+ S4C-1 提交（见下一提交） | 2026-10-16 23:10 因补充 01 结果不合理停下，23:15/23:20 用户决定（A 同陆块按陆上、非陆地口径、PyPSA-Eur 公式）后继续。`research.cost_layer.electric_base_candidates: cost_layer`（`s4c_layers.apply_cost_layer_s4c1`）：陆风 114,912 → 99,000；地面光伏 71,546 → 30,743（solar-utility）；屋顶 57,483 → 36,610；海上风 AC 均值 277,842 → 230,295、DC 291,038 → 265,076（并网按到岸距离：AC 中位 12.6 km、DC 60.6 km，并网段占海上风年化成本按潜力加权 AC 5.9%、DC 14.5%；10 台无 S4A 布局的发电机用同节点/同国均值代理，C 级）；电池充电器 24,093 → 10,118；电池储能 +4.8%；配电网 +5.2%；DC 链路 ×2.5（换流站 15,753 → 40,497）；AC 线路 +11%（含海底段）；管道 +3–14%。全组件审计 84 组：成本层 51、已确认例外 5（SMR、地热、LNG 接收站、H₂ 进口接收站、CO₂ 封存 30 EUR/t——technology-data 无此行）、无投资 28、无法判断 0（两情景相同）。补充 01：`research.corridors.subsea_share: landmass_nonland`（主算）/ `geometric_all` / `zero`；129 对候选（跨境 24），主算 > 0.05 的 18 对、全几何 32 对。五个构建静态 PASS（各约 42 s、0.70 GiB）；`tests/research` 444 通过 / 0 失败 |
| 补充 01 | 走廊海底份额与走廊成本（台账 L18，第 16 项），作为 S4C-1 第 5 条 | 完成（并入 S4C-1） | 同上 | 判定表：`SUBSEA_SHARE_S4C1.csv`（节点对）、`COMPONENT_SUBSEA_SHARE_S4C1.csv`（473 条组件）、`CORRIDOR_SUBSEA_SHARE_S4C1.csv`（走廊表 26 行）；登记为东盟特有处理"群岛海底通道"（工作原则第 3 条） |
| S4C-2 | 水电入流诊断与重新归一（第 83 项） | 完成 | 315b22da（诊断，停止）+ 9a5ea111 | 2026-10-17 用户决定 B（按容量分配）+ Ember 2019–2025 中位 × 1.1。`research.hydro.inflow_normalization: national_observed`（B 主算）/ `national_observed_runoff_shares`（A 敏感性）/ `frozen_base`；存量 58.2 GW 年入流 232.8 → 230.2 TWh（目标 231.6，径流式截断 1.40 TWh）；逐国 ID 31.4 → 34.1、KH 4.9 → 5.3、LA 46.1 → 38.8、MM 6.5 → 10.4、MY 35.4 → 35.1、PH 10.7 → 10.8、TH 6.6 → 7.3、VN 91.4 → 88.4 TWh；8 个原 CF > 1 单元消除；新建代理改同国口径；四个构建静态 PASS（各约 42 s、0.70 GiB）；`tests/research` 447 通过 / 0 失败。诊断（315b22da，停止）：与推断机理只部分吻合——补入照抄单位入流导致重复计算成立（ID、LA 合计 = IRENA 2023 × 1.1 的 1.16 / 1.15）；但底座只拿到全国目标的 48–95%，单位入流偏高只在 VN、PH 成立；主导偏差是作者链路按上游径流分配（单元 CF 最高 4.6）。另证实 S4B §8 第 12 项 ID 新建代理 CF 1.01–1.08 是 56 时段冒烟（1 月第一周）口径产物，全年 0.48–0.52（`S4C_STOP_02_HYDRO_DIAGNOSIS.md`） |
| S4C-3 | 国际燃料舱归属（第 88 项） | 完成 | S4C-3 提交（见下一提交） | 现状（`bunkering_country`）：国际航空煤油 239.6 TWh 按加注国挂节点、化石部分计入该国大气（0.2571 t/MWh）；国际航运甲醇 485.6 TWh（SG 465.5）在 origin_neutral 下燃烧为零（碳在合成国记账）。主算 `research.bunkers.attribution: asean_pool`：两条东盟负荷（航空、航运分列，country=ASEAN）挂在区域液体母线（`ASEAN oil` 化石计量 + `ASEAN oil non-fossil` 孪生；`ASEAN methanol`），化石燃烧进新账户 `co2 bunkers ASEAN`，单独净零（钩子 `research_bunker_net_zero`，行 `research_bunker_co2_limit`，门槛 `B1_BUNKERS`），账户只有排放口、拒绝负排放端口（不转入他国负排放）→ 化石航煤在任何可行解中为 0；`excluded` 不计入（22 行 798.0 TWh 列为 deferred）。各国差异：SG 国家需求 881.1 → 312.3 TWh，MY 1,479.9 → 1,446.3 TWh；化石当量 CO₂ 上限 61.6 Mt（SG 26.5、TH 14.2、MY 7.6）。`tag_cross_border` 最小改动：端口全在区域母线的链路记为 domestic。四个构建静态 PASS（各约 44 s、0.69 GiB）；`tests/research` 452 通过 / 0 失败。另：查实 `research.cost_layer.registry` 自 077ebd0b 起被误挪到 `corridors` 下（S4C-1 插入 corridors 块所致），无任何代码读取该键（构建器用固定路径），S4C-1 / S4C-2 主算及 frozen_base 构建与修正后配置的构建逐项一致（静态属性、时间序列、成本表全同），不需重建；已挪回 |
| S4C-4 | 东盟外 CO₂ 封存选项（第 89 项） | 未开始 | — | |
| S4C-5 | 基尔霍夫行归一化与求解设置对比（第 84 项） | 未开始 | — | |
| S4C-6 | 冒烟与云端部署包（只准备） | 未开始 | — | |
| 交付 | S4C_REPORT.md、S4C_EVIDENCE.json、DOWNLOAD_LIST.csv | 未开始 | — | |

## 续行点

S4C-0（901b354e）、S4C-1（077ebd0b，含补充 01）、S4C-2（315b22da 诊断 + 9a5ea111 修正）、S4C-3 完成并提交，draft PR #27（叠在 #26 上）。下一步：S4C-4（东盟外 CO₂ 封存，第 89 项；先只读查找单价文献，查不到可引用来源时停下）。

## 用户中途指示

1. 2026-10-16 约 22:00 SGT：追加 `S4C_SUPPLEMENT_01.md`（走廊海底份额与走廊成本，台账 L18，落实第 16 项），先核对 SHA256 与 `S4C_SUPPLEMENT_01_SHA256.txt`（e0bc1743…a8340a）一致——已核对一致（VERIFIED）；作为 S4C-1 第 5 条执行；海底份额结果不合理或形状不足以判定时停下报告。

2. 2026-10-16 约 23:15 SGT（对 `S4C_STOP_01_SUBSEA_SHARE.md` 的答复，用户原话为选项）：
   - 走廊海底份额："A 同陆块按陆上"——两端节点位于作者陆地形状同一多边形 → 海底份额 0；不同陆块 → 大圆几何份额；
   - 形状缺口："非陆地口径"——不在陆地形状内即算海底（内水与群岛水域计入海底）；
   - 海上风并网距离："PyPSA-Eur 公式"——按 PyPSA-Eur v2025.07.0 公式在 S4A 曲线同一布局上算到岸距离 + 登陆段。
3. 2026-10-16 约 23:20 SGT（用户确认三题并补充要求）：
   1) 第 1、2 题登记为东盟特有处理（工作原则第 3 条，"群岛海底通道"）：PyPSA-Eur 的海底份额来自真实线路走向、海上形状用 EEZ，在欧洲内水很小；本模型无走向数据，且印尼、菲律宾的群岛水域（UNCLOS 第四部分，群岛基线以内、不属 EEZ）面积很大，故采用"同陆块判定 + 非陆地即海底的几何份额"；同陆块判定用作者陆地形状，按连通多边形判定，小岛与主岛不相连时按跨海处理；
   2) 输出每条走廊和候选的判定表：两端陆块编号、是否同陆块、几何份额（EEZ 口径与非陆地口径两列）、最终取值；
   3) 开关三值：`zero`（原状）、`geometric_all`（全几何，海底份额上限）、`landmass_nonland`（主算）；
   4) 第 3 题：引用 PyPSA-Eur v2025.07.0 到岸距离公式与登陆段长度所在配置行与代码行；报告各节点海上风 AC/DC 到岸距离分布与并网成本占海上风总成本比例；作者网络复现核对不通过的原因（区域划分不同）如实写入报告。

4. 2026-10-17（对 `S4C_STOP_02_HYDRO_DIAGNOSIS.md` 的答复）："确认：1-B 按容量分配；2-Ember 2019–2025 中位数 × 1.1"。补充要求：
   1) 登记为对冻结电力底座的数据更正，偏离 PyPSA-Earth 的"按上游径流分配"，理由：原作者底座存量不全，径流分配产生单元 CF 2.3–4.6 等物理上不可能的值，其空间份额不可信；B 保证全国水电总量与实际发电一致，并消除补入单元的重复计算；
   2) 局限写入报告：同一国家内各电站年容量因子相同（季节形状仍逐站保留）；Ember 只有水电总量，水库与径流不分；
   3) A（保留原径流份额、只消除重复计算）保留为开关值作敏感性，主算为 B；
   4) 报告逐国列出：原作者底座入流、补入前后、修正后的年入流与折合 CF；被消除的异常单元清单（原 CF > 1 的单元及其节点）。
5. 2026-10-17（S4C-2 收尾中断后）：先核对 S4C-2 是否已提交，未提交则跑全部测试、通过后提交并推送（9a5ea111，447 通过）；再按 S4C-3 → S4C-6 → 交付顺序执行，规则不变。

6. 2026-10-17（S4C-3 构建中途中断后）：(1) 核对 S4C-3 未提交代码完整；(2) 核查 `research.cost_layer.registry` 被误挪到 `corridors` 下：从哪个提交开始、期间读取该键的代码读到什么；S4C-1/S4C-2 构建若受影响则用修正配置重建并对比风光候选成本与水电入流，无影响则写明依据；(3) 重跑 `s4c3_build.sh`、全部测试、提交推送；(4) 继续 S4C-4 → S4C-6 → 交付。核查结论：自 077ebd0b 起误挪（至 9a5ea111）；全仓无代码读取该键（命中均为 `assembly_v1/registry.json` 或固定路径 `s2_network.py:237`），配置组装器不校验键；修正配置构建与 S4C-2 主算、S4C-2 frozen_base、S4C-1 主算逐项一致（风光候选成本均值 99,000 / 30,743 / 36,610 / 230,295 / 265,076；水电存量入流 196.34 + 径流 33.86 TWh，frozen_base 209.58 + 23.20 TWh），不需重建（`evidence/s4c_3/config_key_check/`）。

## 下载登记（第 7 条，第 2 类：分国融资成本）

| 文件 | 来源 | 字节 | SHA256 | 取得时间（UTC） |
|---|---|---|---|---|
| `IEA_CoC_Observatory_dashboard_2025.html` | https://www.iea.org/reports/cost-of-capital-observatory/dashboard-2 | 305,280 | 942a5613…59d3a | 2026-10-16T13:57:17Z |
| `IEA_commentary_SEA_cost_of_capital_20251008.html` | https://www.iea.org/commentaries/high-cost-of-capital-and-limited-project-pipeline-hinder-clean-energy-investment-in-southeast-asia | 270,294 | a9ae6970…38a9f1d | 2026-10-16T13:57:17Z |
| IRENA 2023《The cost of financing for renewable power》PDF | irena.org（HTTP 403）、apren.pt 镜像（404） | — | 未取得 | 2026-10-16 |

累计下载 0.58 MB（上限 300 MB）。
