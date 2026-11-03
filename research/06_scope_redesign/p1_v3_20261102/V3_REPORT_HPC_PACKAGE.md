# V3 HPC 正式运行包报告（台账 V14）

- **指令：** `work/p1_v3_20261102/V3_HPC_PACKAGE_INSTRUCTION.md`，SHA256 `29dc0b0fafd0731e57cf85d054eaebc8a44ebaa10f4446dcfbbe0a8ba3b3ade1`，与同目录 `V3_HPC_PACKAGE_SHA256.txt` 一致（2026-11-04 00:25 SGT 核对）。
- **开始条件（用户 2026-11-04 授权的补充）：** V27 主体已结束（`V3_REPORT_SUPPLEMENT07.md` 第 8 节已推送，头提交 `5e372e5d`），第 8.4 节由另一个会话补写，视为满足。为避免两个会话在同一分支提交，本次在新 worktree `/home/jin/wt_v3_hpc`、自 `5e372e5d` 开出的新分支 `codex/v3-hpc-20261104` 上工作；未进入 `/home/jin/wt_v3_20261102`、`/home/jin/v3s/`，未碰 `work/p1_v3_20261102/cloud_results/`。
- **用户在本会话的决定：** (1) S-A 按登记定义 η = 1，原话"S-A 单价为全成本，已含船用燃料与运营费用，货损不再另计，避免重复计算"，核对时允许船运链路的 `marginal_cost` 与 `efficiency` 两个字段不同；(2) 网络元数据里的构建 worktree 路径在构建前登记为来源差异，并要求确认 HPC 预检与运行器不依赖它（第 2.2 节）；(3) 冒烟直接开始（WLS 空闲、AnyConnect 已断开）。
- **无人值守补充授权：** `work/p1_v3_20261102/V3_HPC_UNATTENDED.md` v1，SHA256 `bd985bc9a7a30d247f03e1fa61048941d79d8870fb9b348a696449bcfe05f8df`，与同目录 `V3_HPC_UNATTENDED_SHA256.txt` 一致（2026-11-04 02:45 SGT 核对）。审阅端按用户授权代为决定原 PROPOSED 取值（第 5 节），并给出审查六条的处理意见（第 6.1 节）；授权不扩大到模型、网络、成本、求解档案、验收阈值、已登记的预测、Gurobi、HPC / 云 / VPN、上传、合并 main、force-push 与删除文件。
- **证据等级：** VERIFIED（读了数组、回执、闸门文件）、EXACT（逐位或有理数核验）、INFERENCE（机制解释与外推）、PROPOSED（未执行、待决定）。
- **不连 HPC、不连云、不连 VPN、未上传。** 本机 Gurobi 2 / 2（登记的两次冒烟），无人值守阶段 0 次。

## 0. 摘要

1. **规则（第 1 节）：** 第 187 项 S-A 成为 2920×3h 正式运行的船运单价主值（η = 1），S-B 保留为下界敏感性开关；筛查不重建，口径差写入规则；第 186 项补写第 176 项第 7 条并把车队 ×0.5 的 F3、F4 并入正式批次；B1 判据写明；S3-1、S3-3、S3-4 修正；`add_demand_layer` 缺份额键改为报错；四个玩具网络单元测试。**发现审查一处不准：** `DIRECT` 两份清单原本并不一致（`s4d_ledger` 缺 `co2_transit_rail_freight`），改为单一来源后只影响账本恒等式的两个诊断量。
2. **四个网络（第 2 节）：** 构建 `a1ef782b`，逐元素核对全部符合构建前写定的预期：F1、F2 对登记网络只有 270 条船运链路的单价与效率不同（S-A 公式逐条吻合、η = 1）；F3、F4 对 F1、F2 只有 96 个 EV 电池容量与 96 个充电桩功率不同，逐位为 0.5 倍；F2 − F1、F4 − F3 与登记对的差异结构完全相同。新 SHA256：F1 `8b5fd663…`、F2 `e2837e4a…`、F3 `c4eb7c44…`、F4 `0bbe235e…`。
3. **冒烟（第 3 节）：** 两次 optimal、C1 111、`ACCEPTED_LAYER2`；一体化 329.7056、`no_new_xb` 342.2687 bn，**B6 12.5631 bn**；S-A 使两情景总成本各增约 0.50 bn，B6 只变 −0.0034 bn（审查估计 ≤ 0.02 bn 成立）；12 个参与者的 Owen 受益符号不变。
4. **预测（第 4 节）：** 在任何 HPC 求解之前登记（`RUN_PLAN_V3.md` 第 26 节），两个参照（56 时段冒烟、365×24h 重跑）并列并写明各自的结构失真。
5. **登记的时限（第 5 节，审阅端按用户授权决定，2026-11-04）：** U = 263.7 h → **TimeLimit 864,000 s（240 h，被 240 h 上限截断）**、进程 2 墙钟 871,200 s、止损线 691,200 s；进程 1 超时 **5,400 s**；walltime **F1 260 h、F2 262 h、F3 260 h、F4 262 h**（每个作业余量 ≥ 2 h），批级 48 h；资源不变；`limits_status` **REGISTERED**。须知：T < U，止损约在 Atlas 每次迭代 1,840–1,860 s 时触发，低于 U 假设的 2,686 s（第 5.2 节）。
6. **审查六条（第 6.1 节）：** 第 1 条空数组展开加保护，并新增 `hpr_submit.sh --dry-run`；第 2 条列为已知局限，不改求解路径；第 3 条前序检查与预检失败停批；第 4 条停批时 `POST_ONLY` 仍做后处理；第 5 条改注释；第 6 条锁的说明、`--resume` 遇锁拒绝、F2 的 walltime 计两个等待。
7. **bash 4.2（第 8.2 节）：** 从 GNU 源码编译 bash 4.2 后实测：替身测试 38 项全过；包上的干跑（预检、四运行 BUILD_ONLY、作业体、`hpr_submit.sh --dry-run`）与 bash 5 结果相同；18 个脚本 `bash -n` 全过，4.3 及以上才有的写法命中 0。Atlas 的实际版本由用户在登录节点确认（指南清单 (c)）。
8. **部署包（第 7–8 节）：** `work/p1_v3_20261102/hpc_package_v3/`，COMMIT `7d22dda1`，46 个文件（含清单共 48 个、373,712,296 B），`SHA256SUMS` 的 SHA256 `63d682bb…`；一致性检查 57 行全部一致；旧包两份改名保留。
9. **终点：** 包、操作指南、报告定稿并提交推送；剩下的只有用户连 VPN 上传与提交作业（指南开头的清单）。全量测试只有与基线同一根因的失败（第 9 节）。

## 1. 规则与小修（指令第 1 节；提交 `a1ef782b`，构建前）

| 项 | 内容 | 位置 |
|---|---|---|
| 第 187 项 | `research.liquids.ship_cost_basis = ieaghg`：c(d) = 固定项 + c_km × d，η = 1（第 3.3 节早已登记的 S-A 定义，开关已存在，构建代码不改）；S-B 为下界敏感性；筛查（S-B）不重建，口径差：正式运行每 MWh 船运液体多付运费且不计货损，两情景都付；用当前配置重评筛查结果会在 G2.2 / B12 上不一致，筛查以其构建提交的配置为准 | `V3_RULES.md` 第 12.1 节、第 3.3 节标注；`configs/research/baseline.yaml` |
| 注册表（审查 S3-2） | `liquid_ship_ckm_td_{methanol,oil,ammonia}` B → C，描述标"下界敏感性"；S-A 六行标"主值"；数值一行不改（逐列比较：只有 9 行描述、3 行等级与来源变化）；`DATA_REGISTRY.csv` 2,321 行，SHA256 `93dbeb43…` | `scripts_project/v3_data.py` |
| 第 186 项 ① | 第 176 项第 7 条补写：日分辨率没有任何日内平衡，固定储能为 0、新建可调机组几乎为 0；装机、电价、跨境流与 B6 量级不作正式结果的合理性参照；筛查只用于 B6 符号、账本与分摊程序检验 | `V3_RULES.md` 第 10 节第 7 条 |
| 第 186 项（S2-4） | 车队 ×0.5 的一体化与 `no_new_xb` 作为 F3、F4 并入正式批次（`--override s2.demand.ev_fleet_scale=0.5`）；第 176 项第 4 条加注 | 第 12.2 节、第 10 节第 4 条 |
| 审查 Q-1 | 读 `gate_b1_country_net_zero`：通过 ⇔ 每国大气 Store 末值 ≤ cap + (1e-3 + 1e-7 × max(1, \|cap\|)) tCO₂，cap = 0 时容差约 1 kg；内点解不交叉，年度端口流量 1e7–1e9 t 的相对 1e-9 残差就是 0.01–1 t，所以总是"不通过"；阈值不改，以 `B1_S4B` 为判据 | 第 8.3 节 |
| 审查 S3-1 | `BATCH_DEF_2920x3h.json` 名称与注记改写（登记值不变） | `batch_def/` |
| 审查 S3-3 | 专线不在长度份额表中，按长度拆分对专线等于 0.5（写明，代码不改） | 第 2.3 节末 |
| 审查 S3-4 | `DIRECT` 改为单一来源 `s4d_ledger.DIRECT_SUBJECTS`（运费主题另立 `FREIGHT_SUBJECTS`），`m12_allocation.DIRECT` 引用它。**实施时发现两份原本不一致**：`s4d_ledger` 的清单缺 `co2_transit_rail_freight`，同一模块的运费映射却会产生这一主题；审查写"现在一致"不准确。统一后只改变 `LEDGER_IDENTITY.json` 的两个诊断量 `direct_costs_minus_objective`、`settlement_sum`（有老挝铁路 CO₂ 运费时相差这笔运费）；B16、账本各行、Owen 不变，闸门不读这两个量 | `s4d_ledger.py`、`m12_allocation.py` |
| 审查 S2-5 | `add_demand_layer`：有工业需求而没有 v3 载体节点份额（或份额和为 0）时报错（`check_carrier_share_keys`）；F1–F4 构建都通过了这一检查（现网没有缺键）。四个玩具网络单元测试与 `DIRECT` 单一来源测试，`tests/research/test_v3_units.py` 8 项通过 | `s2_layers.py` |

第 (iv) 项测试的说明：缺键报错用检查函数本身测试，并核对 `add_demand_layer` 在份额查找之前调用它；没有在玩具网络上运行完整的 `add_demand_layer`（它需要整条需求输入链），由真实构建覆盖。

## 2. 四个 2920×3h 网络与核对（指令第 2 节；`RUN_PLAN_V3.md` 第 24.1 节）

**构建（VERIFIED）：** 提交 `a1ef782b`，`PYTHONHASHSEED=0`，`results_project/v3hpc/builds/`（`sa/` = F1、F2，`sa_ev05/` = F3、F4），每个约 1.5 分钟、峰值 0.8 GiB；静态检查两根 `all_structural_passed = true`。

| 运行 | 包内文件名 | 字节 | SHA256 |
|---|---|---:|---|
| F1 | `integrated_2920_3h_unsolved.nc` | 72,050,034 | `8b5fd663d6c783e9af549bec8394700c9b4b5785b1ec809ab7d8e668d78657ef` |
| F2 | `no_new_xb_2920_3h_unsolved.nc` | 71,411,694 | `e2837e4ada978e0d05fc04108d7ceb99567e41c33b6837ab4447be74bdd918b7` |
| F3 | `integrated_ev05_2920_3h_unsolved.nc` | 72,050,068 | `c4eb7c44a54175ba06d7d60d4926cb095fc0ec603eced4ff28aecd8493bcb063` |
| F4 | `no_new_xb_ev05_2920_3h_unsolved.nc` | 71,411,730 | `0bbe235e08654f566afe8f94eb2299a9ed1a8bb1f791520f8206449e02c3bac7` |

**逐元素核对（VERIFIED / EXACT，`evidence/hpc/F_REBUILD_CHECK.json`）：** 全部 netCDF 变量按位比较，差异落到具体组件；元数据逐叶键比较；按 `V3_RULES.md` 第 12.3 节构建前写定的允许差异判定。

| 比较 | 结果 |
|---|---|
| F1 对 `1bddacb7…` | 只有 `links_marginal_cost`、`links_efficiency`，不同的组件恰为全部 270 条船运链路；新单价与 S-A 公式最大相对偏差 0.0（EXACT），η 全为 1；元数据只有船运单价键、两个配置哈希与构建路径 |
| F2 对 `b262f6aa…` | 同上；母网络 SHA256 = 新 F1 |
| F3 对 F1 | 只有 96 个 EV 电池 `e_nom`、96 个充电桩 `p_nom`，**逐位等于 F1 × 0.5**（电池 7.934 → 3.967 TWh，充电桩 3,490.9 → 1,745.4 GW）；元数据只有车队键、覆盖记录与配置哈希 |
| F4 对 F2 | 同上；母网络 SHA256 = F3 |
| F2 − F1、F4 − F3 | 与登记对的差异结构完全相同；删除 46 条 AC 线、283 条链路（H2 管 110、气管 110、CO₂ 管 55、DC 8），共同组件上只有存量 16 条 AC 线与 9 条链路的可扩建标志与上界，时序无差异（与审查维度 4 一致） |

**两处核对口径（照实说明）：** (1) 我在构建前写的第 12.3 节把船运链路数写成"810 条（各 270 条）"，是计数笔误，第 3.3 节登记的是 270 条（90 条有向航线 × 3 载体）；核对按"全部船运链路"这一集合判定，集合与两个字段都符合，计数已在规则中更正并注明。(2) F4 的覆盖记录同时带有派生变体自己的 `cross_border.stock_mode=no_new_xb`（F2 本来就有），允许的键不变，是核对脚本第一版没预计到这个值。两处都不是规则外差异，网络未重建。另：第一版核对脚本有一处 O(n²) 写法跑了 15 分钟未完，终止后改正重跑（约 3 分钟）。

### 2.1 LP 规模（INFERENCE，线性外推）

| 网络 | 列 | 行 | 非零 |
|---|---:|---:|---:|
| F1、F3 | 37,480,004 | 82,955,300 | ≈ 1.93 亿 |
| F2、F4 | 36,384,650 | 80,501,958 | ≈ 1.85 亿 |

同一方法对 v2 一体化给出 35,748,446 列 × 79,714,102 行，与 D2 在 Atlas 上的实测逐位相同，非零多估 0.56 %。本机 10 GiB 放不下全尺寸 LP，未实际构建。

### 2.2 构建路径与 HPC（回答用户的确认问题，VERIFIED）

- `s2_layers.geothermal.bus_mapping_source.path` 只在 `s2_network.py:350` 写入，`scripts_project` 中没有任何代码读它。
- HPC 预检 `networks` 节调用 `b4_batch4.py base-check`：只比网络文件 SHA256、字节数与构建回执、登记值；G2.1 只比输入网络 SHA256 与登记值、回读状态；G2.2 只比配置子集哈希（取自配置文件）。
- 旁证：V27 的 AutoDL 重跑（网络元数据写的是本机 worktree 路径，代码目录不同）G2 全过、`ACCEPTED_LAYER2`；D2 在 Atlas 上 `BUILD_CHECK` 通过 `g2_2_subset_equal`。所以 HPC 上目录不同不会被误判。
- 在 `5e372e5d` 上于新 worktree 试构建（配置未改）：与 `1bddacb7…` 全部变量逐位相同，元数据只差这一个键（`evidence/hpc/TRIAL_5E372E5D_VS_REGISTERED.json`）。

## 3. 本机冒烟与 S-A 的影响（指令第 3 节；`RUN_PLAN_V3.md` 第 24、25 节）

登记（第 24 节，含闸门预告与 S-A 事先估计）在 `a4607714` 提交并推送后才启动。2026-11-04 01:24–01:42 SGT，两次串行，间隔 334 s，额度 2 / 2，无重试。路径与设置同补充 05（`smoke_s5.sh`）。

| 运行 | 终止 | 目标值 bn | barrier 次 / s | 求解 s | 峰值 GiB | C1 abc | GATES_V6 |
|---|---|---:|---|---:|---:|---|---|
| 一体化（F1 前 56 时段） | optimal | 329.7056 | 80 / 190.5 | 210.4 | 7.31 | 111 | `ACCEPTED_LAYER2` |
| `no_new_xb`（F2 前 56 时段） | optimal | 342.2687 | 66 / 111.2 | 127.8 | 5.71 | 111 | `ACCEPTED_LAYER2` |

**验收全部通过（VERIFIED，`evidence/hpc/smoke/V3_SMOKE_RESULT.json`）：** B16 相对误差 1.8e-13；B6 为正；SG 船用燃料有来源；无松弛。失败闸门全在预告内（一体化 A1_A2、A1_A2_S4B、A3、B1、B3、B8；`no_new_xb` 同上去掉 B3）；B8 只有 Transport −4.1146e-05。船运容量对偶 554 行全部 0，最大利用率 8.45 %。

**与补充 05 冒烟（S-B）并列（VERIFIED，`evidence/hpc/SA_EFFECT_SMOKE.json`）：**

| 项 | S-A（本次） | S-B（补充 05） | S-A − S-B | 事先估计（第 24.3 节） |
|---|---:|---:|---:|---|
| 一体化 bn | 329.7056 | 329.1998 | **+0.5057** | +0.3 到 +0.92（一阶 +0.583） |
| `no_new_xb` bn | 342.2687 | 341.7664 | **+0.5023** | +0.3 到 +0.94（一阶 +0.580） |
| B6 bn | 12.5631 | 12.5665 | **−0.0034** | ±0.05（一阶 −0.003） |
| 船运运费 bn（一体化 / `no_new_xb`） | 0.982 / 1.012 | 0.138 / 0.154 | +0.84 / +0.86 | — |

- 口径：56 时段按 8,760 / 56 年化（一周放大为一年）。运费增加约 0.85 bn/情景，但不再计货损（S-B 下约 0.34–0.36 bn 的货物价值）且流量重新优化，所以总成本只增约 0.50 bn。两情景运量相近，B6 几乎不变：**审查估计"≤ 0.02 bn"成立**。
- Owen 受益（α 主值，bn）S-A / S-B：BN +0.184 / +0.183，ID −0.712 / −0.832，KH +0.366 / +0.367，LA −0.108 / −0.101，MM +0.298 / +0.295，MY +0.870 / +0.847，PH +0.130 / +0.173，SG +2.770 / +2.769，TH +4.073 / +4.066，TL +0.026 / +0.026，VN +1.369 / +1.366，BUNKER +3.297 / +3.408；符号全部相同；变化最大的是 ID（+0.12）与 BUNKER（−0.11），都是甲醇出口国与燃料舱买方，符合运费由买方母线价承担的机制（INFERENCE）。
- 这两次的目标值与迭代数登记为 HPC 冒烟作业的期望值。

## 4. 预测（指令第 4 节；`RUN_PLAN_V3.md` 第 26 节，任何 HPC 求解之前提交）

两个参照与 2920×3h 的结构差异：56 时段冒烟有日内平衡与 EV 日内灵活性，但只有旱季一周（老挝来水约为 9 月的 7 %）；365×24h 有全年季节，但没有任何日内平衡（固定储能 0、光伏约九成，EV 只剩 1.59 TWh 跨日带宽）且为 S-B。2920×3h 两者都没有这些失真，所以区间按两参照放宽。主要登记：

| 项 | 预测 |
|---|---|
| B6 = F2 − F1 | 为正（把握很大但不是结构必然：零容量 AC 候选线在线性化 KVL 下仍约束环路）；9–19 bn，最可能 12–16 bn（参照 12.56、14.57） |
| B6 = F4 − F3 | 为正；9.5–19.5 bn |
| (F4 − F3) − (F2 − F1) | 为正较可能：−0.3 到 +0.8 bn，最可能 +0.05 到 +0.30 bn（56 时段 flat − E2 为 +0.443 bn，车队减半介于两者之间、靠近下端） |
| EV 部分：F3 − F1、F4 − F2 | 都为正，+1 到 +7 bn，最可能 +2.5 到 +5 bn；EV 部分在 B6 中的份额 < 5 %，最可能 < 2.5 % |
| Owen 符号（F1 / F2） | BN、KH、MM、MY、PH、SG、TH、TL、VN 为正（两参照都正）；ID、LA、BUNKER 不定：LA 最可能正（全年雨季出口），ID 正负各半、最可能正且 \|·\| < 1 bn，BUNKER 最可能正（3 小时分辨率 +3.30，日分辨率 −0.12） |
| Owen 符号（F3 / F4） | 9 个稳健为正的仍为正；其余三者与 F1 / F2 同号可能性较大；稳健性由审阅端在 F3、F4 到位后判断 |
| barrier 迭代 | F1、F3 160–350（最可能 200–300）；F2、F4 110–250（最可能 130–200） |
| 求解时长（Atlas） | F1、F3 8–260 h（最可能 30–100 h）；F2、F4 1.5–40 h（最可能 5–20 h） |
| 终止与内存 | F1、F3 optimal；F2、F4 optimal 或 suboptimal；C1 全过；进程 2 峰值 F1、F3 117–208 GiB，F2、F4 88–194 GiB |

## 5. `RUN_PLAN_HPC_V3.md` 与登记的时限（指令第 5 节；无人值守授权第 1 节）

V3 HPC v1 提交时的取值是 PROPOSED（TimeLimit 1,296,000 s、walltime 376 / 378 / 378 / 378 h、进程 1 超时 7,200 s、批级 48 h；`RUN_PLAN_HPC_V3.md` 第 12 节保留作记录）。2026-11-04 审阅端按用户授权按下列规则决定，写入 `RUN_PLAN_HPC_V3.md` 新的第 14 节"审阅端按用户授权决定（2026-11-04）"并登记（定义文件 `limits_status: REGISTERED`），在任何 HPC 求解之前提交。

### 5.1 TimeLimit：T = max(72 h, min(240 h, 2 × U))，向上取整到 12 h

**U（F1 求解时长的外推上界，INFERENCE，每一项都取保守端）：** 单次迭代 = B4P 对 v2 F1 2920×3h 的高值 1,127 s（8470Q T16）× v3 / v2 单次迭代比的上端 1.49（365×24h 同档案、同机型实测 1.30–1.49）= 1,679 s；迭代数 = 一体化 56 时段 80–83、365×24h 146–186 次，按 56 → 365 的增长外推到 2920 的上端 350 次；CPU 因子取假设区间 1.0 / 1.3 / 1.6 的上端 1.6；barrier 1,679 × 350 × 1.6 = 940,240 s = 261.2 h，加预求解与排序的上端 2.5 h，**U = 263.7 h**。

2 × U = 527 h → min(240, 527) = 240 h → **T = 864,000 s（240 h）**；进程 2 墙钟 871,200 s。

### 5.2 早期测速止损

0.80 × T = **691,200 s**（192 h）；参考迭代数取 U 所用的 350 次（F1、F3），F2、F4 保持 250 次。

**须知（INFERENCE）：** 240 h 上限使 T < U。止损在第 20 次迭代判定（第 11–20 次平均 × 350 + 第 20 次的日志时间 > 691,200 s），等价于 Atlas 上每次迭代超过约 (691,200 − 预求解) / 370 ≈ **1,840–1,860 s**。这低于 U 假设的 2,686 s / 次，高于中值 1,056 s / 次。所以授权第 1 节第 2 条"只有实际单次迭代比 U 的假设慢很多时才会触发"在本取值下不完全成立：落在第 2.1 节高值区间上段（≥ 约 69 % 的 U 假设）的运行会在约 20 次迭代、约 10 小时后被止损，由用户决定以更长时限重开（新运行目录）。这是规则中 240 h 上限的直接结果，按授权不改，报告请审阅端知悉。

### 5.3 其余取值

| 项 | 登记值 | 推导 |
|---|---|---|
| 进程 1 超时 | **5,400 s** | D2 实测 2,382 s，v3 LP 约大 4 % → 约 2,500 s，余量约 2.2 倍 |
| walltime 基础项 | 918,930 s | 330 + 5,400 + 871,200 + 32,400 + 2 × 3,900 + 1,800（v2 `RUN_PLAN_HPC.md` 第 2 节的构成） |
| PBS walltime F1 | **260 h**（余量 17,070 s） | 无等待项：918,930 + 2 h → 257.3 h；"F3 同 F1" → 260 h |
| PBS walltime F2 | **262 h**（余量 9,870 s） | 两个等待项（等 F1 启动 + 启动锁，审查第 6 条）：933,330 + 2 h → 261.3 h → 262 h |
| PBS walltime F3 | **260 h**（余量 9,870 s） | 一个等待项（启动锁）：926,130 + 2 h → 259.3 h → 260 h |
| PBS walltime F4 | **262 h**（余量 17,070 s） | 一个等待项：259.3 h；"F4 同 F2" → 262 h |
| 批级 walltime | 48 h | 授权第 1 节未列，沿用原提议的保守值（四个运行的补做上限） |
| 资源 | F1、F3 300 GB，F2、F4 250 GB，48 核；批级 120 GB / 12 核 | 授权第 1 节第 5 条（与原值相同；两项可选提议未采纳） |

全部 ≤ Atlas `parallel` 上限 720 h；一致性检查逐作业核对"walltime ≥ 求和"与"余量 ≥ 7,200 s"（`HPC_CONSISTENCY.json`）。

**整批时长：** F1、F2 并行，F3 接 F1、F4 接 F2，总时长约 max(F1 + F3, F2 + F4) + 排队：中值约 6–7 天；walltime 全部用满约 22 天（`/hpctmp` 60 天清除之内；每个运行结束后先下载其导出）。

**作业链与许可（`RUN_PLAN_HPC_V3.md` 第 3–4 节）：** F1；F2 `after:F1` + `WAIT_START_OF=F1`（沿用 v2）；F3 `afterany:F1`；F4 `afterany:F2`；**一个批级作业 `afterany:F3:F4`**。任意时刻最多两个正式作业（96 核 = 每用户上限），所以 ≤ 2 个 Gurobi 会话；新增的**启动锁**（共享运行目录中的原子 `mkdir`，跨节点有效）把所有 Gurobi 启动串行化：锁内等到距其他运行的每次启动、任何结束与本运行器启动都 ≥ 330 s，且其他在跑的会话少于 2 个。批级作业只设一个的理由：F3、F4 在跑时每用户 96 核的上限会让"第 A 对"的批级作业排队到 F3 或 F4 结束，单设它几乎换不来时间。

**资源：** F1、F3 300 GB、F2、F4 250 GB、48 核；批级 120 GB / 12 核（指令第 5.5 条；D2 峰值 92 GiB 低于审查 F-16 的 100 GiB 线）。**同期禁止：** HPC 正式求解期间本机与 AutoDL 不调用 Gurobi。

## 6. 运行器与作业脚本的改动（为四个运行；无定义文件时 v2 行为与输出完全不变）

| 文件 | 改动 |
|---|---|
| `scripts_project/b4_batch4.py` | 定义文件可携带时限、作业表、冒烟期望值、内存高值（`limits_status` PROPOSED / REGISTERED）；`pairs()`；B6 与 M12 受益按对；两对比较；`runmeta` 子命令；`hpc-plan` 增加 `ITERS`、`PAIR`、`STATUS` 行；`walltime_components` 按作业；`STOP_ALWAYS` = 全部运行 |
| `scripts_project/batch_def.py` | `build_stem`：变体可指定母网络（F4 ← F3） |
| `run_batch4.sh` | 时限经 `hpc-plan` 读取（单一来源）；PROPOSED 时拒绝正式运行；参考迭代、母网络、对经 `runmeta` 读取；四个运行只能 `--only`；启动锁；受益按对；导出全部 `PROJECTION_*`、`M12_BENEFIT_*` |
| `preflight.sh` | 有定义文件时 TimeLimit 取自 `b4_batch4.py`；`code` 节的运行表与时限断言按定义文件 |
| `hpr_job.sh` | 运行编号取定义文件；批级作业等全部运行落定；PROPOSED 时拒绝正式作业；`afterany` 前序检查与正式作业预检失败时停批（审查第 3 条） |
| `hpr_submit.sh` | 按 `pbs/HPC_PLAN.txt` 的作业与依赖逐个提交（v2 生成的 qsub 命令不变）；PROPOSED 时拒绝；`--dry-run` 不提交演练；`--resume` 遇锁目录拒绝（审查第 1、6 条） |
| `hpr_status.sh`、`make_pbs.sh`、`hpr_consistency.py` | 全部运行与启动锁；读包内定义文件；比对行按运行表生成（v2 计划仍 `ALL_CONSISTENT`） |
| 新增 | `batch_def/BATCH_DEF_2920x3h_v3hpc.json`、`hpc_v3/make_hpc_package_v3.sh`、`hpc_v3/make_reference_values_v3.py`、`hpc_v3/REFERENCE_VALUES_V3.json`（只有数值） |

**测试（VERIFIED）：** `tests/research/test_v3_hpc_runner.py` 11 项（定义文件 = 登记计划与登记值；有无定义文件的输出与 walltime 构成；F1 → F2 → F3 → F4 各一个作业再接批级作业，两对 B6、受益与比较；启动锁让两个同时启动相隔 ≥ 间隔；已有两个求解或锁残留 → `STOP_SAFE:START_LOCK`；PROPOSED 拒绝、四运行的单机批次拒绝、四运行 BUILD_ONLY；PBS 生成、对本计划的一致性（含 4 行余量）、`--dry-run`、PROPOSED 拒绝、经替身 `qsub` 的依赖链、`--resume` 遇锁拒绝；冒烟作业体；作业体拒绝；前序未结束与预检失败停批；停批时 `POST_ONLY` 的后处理）全部通过；原有运行器回归（`test_b4p_batch4`、`test_hpr_two_jobs`、`test_v3_runners`、`test_b4p_paths`、`test_dfx_runner`）54 项全部通过，`test_b4p_split.py` 8 项另跑通过。bash 4.2 下的结果见第 8.2 节，全量测试见第 9 节。

### 6.1 审查六条的处理（只读审查 `5e372e5d..1e7b503c`，2026-11-04 02:25 SGT；审阅端意见 02:24 与无人值守授权第 1、2 节）

| 条 | 发现 | 处理 | 验证 |
|---|---|---|---|
| 1【阻断，若 Atlas bash < 4.4】 | `set -u` 下空数组展开报错（`run_batch4.sh` 的 `${PAIRS[*]}`、`hpr_submit.sh` 的 `"${W[@]}"`） | 改为 `${PAIRS[*]:-}`、`${W[@]+"${W[@]}"}`、`pair_runs` 的 `${out[*]:-}`；其余未加保护的展开逐一核对，都是构造上不会为空的数组（第 8.2 节清单）；新增 `hpr_submit.sh --dry-run`（只打印 qsub 命令，不写、不提交、不调用 qsub），操作指南第一步加 `bash --version` 与两次演练 | 本机编译 bash 4.2 实测（第 8.2 节） |
| 2【非阻断】 | `.solve_start` 早于 `gp.Env()` 真正建立 WLS 会话，`.solve_end` 晚于退出最多约 5 s，实际间隔可能略小于 330 s | **列为已知局限，本次不改求解路径**（审阅端意见，`RUN_PLAN_HPC_V3.md` 第 4 节）。理由：同时只有 F1、F2 两个会话，不超过上限；F3、F4 开会话前还有约 40 分钟无许可的构建（进程 1），与前一个会话的间隔自然远大于 330 s | — |
| 3【非阻断】 | 前序运行失败但没写 STOP（预检失败、`qdel`、被杀）时，F3 / F4（`afterany`）照常开跑 | 作业体：`afterany` 前序没有 `.ended` 且批次未停 → 写 `STOP_SAFE:PREDECESSOR_NOT_ENDED`，什么都不启动（退出码 3）；正式作业包内预检失败 → 写 `STOP_SAFE:PREFLIGHT_FAILED`；操作指南 (h) 写明撤销正式作业时同时撤销依赖它的作业 | 新测试；干跑第 8.1 节 |
| 4【非阻断，v2 旧问题】 | `POST_ONLY` 在停批时跳过 `post_run` | `POST_ONLY` 对每个已结束运行都做后处理（停批时也做），再重评、汇总、打 `halted` 包 | 新测试 |
| 5【非阻断】 | 无定义文件时也有启动锁与 `BASE_CHECK_F*.json`，注释"Without a definition: v2"不准 | 改注释，写明这两项在无定义文件时同样生效 | — |
| 6【非阻断】 | 状态与指南写"几分钟"，但合法持锁可到 2 h；`--resume` 不查残留锁；F2 最坏可等两个 `WAIT_START_MAX_S` 而 walltime 只算一个 | `hpr_status.sh` 与指南改为"通常几分钟、合法最多 2 h"，并显示 `STOP` / `STOP_SAFE` 文件；`hpr_submit.sh --resume` 发现锁目录即拒绝；有定义文件时 `walltime_components` 给 F2 计两个等待项，F2 walltime 按此决定（262 h，余量 9,870 s）；锁残留的处置改为改名移开，不删除 | 新测试；一致性检查 |

## 7. 部署包与操作指南（指令第 6 节）

**包：** `work/p1_v3_20261102/hpc_package_v3/`，由 `hpc_v3/make_hpc_package_v3.sh` 在干净提交 **`7d22dda112a3c18ed57e8c061d95e51915980417`** 上打出（dirty 0；`COMMIT` = 新分支的提交，指令补充第 2 条）。`SHA256SUMS` 列 46 个文件，`SHA256SUMS` 自身 SHA256 **`63d682bbe743ce220bec747aede81d6423d3afd1cac53b7ffdbc2345e970345c`**；清单 `HPC_PACKAGE_MANIFEST.json` `af9f91bc…`；共 48 个文件、373,712,296 B（含 `SHA256SUMS` 与清单）。旧包都改名保留、不再使用：`hpc_package_v3_superseded_1e7b503c/`（PROPOSED 取值，审查前）与 `hpc_package_v3_superseded_917c8b63/`（作业体文字修正前）。

| 类别 | 内容 |
|---|---|
| 代码 | `code_7d22dda1.tar.gz`（82,796,517 B，`3c8c0af9…`；`git archive` 不含顶层 `research/`） |
| 定义 | `BATCH_DEF.json`（= `batch_def/BATCH_DEF_2920x3h_v3hpc.json`，`59c68214…`；**`limits_status: REGISTERED`**，TimeLimit 864,000 s，进程 1 超时 5,400 s） |
| 网络与回执 | 四个 2920×3h 网络（第 2 节）、`integrated_BUILD_RECEIPT.json`、`integrated_ev05_BUILD_RECEIPT.json`、两个变体回执、`integrated_costs_active_research.csv`；**没有 365×24h 文件** |
| 运行与作业 | `run_batch4.sh`、`preflight.sh`、`pack_results.sh`、`hpc/`（作业体、PBS 生成、安装、登录预检、提交（含 `--dry-run`）、状态、一致性检查）、`pbs/`（8 个作业脚本：walltime F1 / F2 / F3 / F4 = `260:00:00` / `262:00:00` / `260:00:00` / `262:00:00`，批级 `48:00:00`；`HPC_PLAN.txt`、`MAKE_PBS.log`） |
| 环境 | `env/`（第三批锁定，未改；HPC 上已有环境，预检 `env` 节 284 / 284 一致即复用） |
| 文档与参照 | `RUN_PLAN_HPC_V3.md`（含第 14 节）、`HPC_OPERATOR_GUIDE_V3.md`（含开头的操作清单）、`RUN_PLAN_V3.md`、`V3_RULES.md`、`HPC_FACTS_20261026.md`、`REFERENCE_VALUES.json`（只有数值） |
| 核对 | `HPC_CONSISTENCY.json` / `.txt`：**57 行全部一致**（`ALL_CONSISTENT`；比原来多 4 行"walltime 余量 ≥ 7,200 s"），否则打包脚本拒绝出包 |
| 不进包 | 许可、cutout、LP 与解的数组、`results_project` 下的结果、`solve.log` / `solve.err`、账号与主机信息、365×24h 网络 |

**上传时间估计（单路）：** 373.7 MB；1 MB/s 约 6 分钟，0.1 MB/s 约 1 小时；按 AutoDL 上传曾实测的 0.058 MB/s 约 1.8 小时。NUS VPN 到 Atlas 的实际速度未测。

**操作指南 `HPC_OPERATOR_GUIDE_V3.md`：** 开头一页"用户上 HPC 操作清单"(a)–(i)：(a) 连 VPN 前确认本机没有 Gurobi 进程、两个 Claude Code 会话都已停下；(b) 连 AnyConnect 后 WSL 外连会断，上传、下载一律用 Windows PowerShell 的 `ssh` / `scp`，写出完整命令与本机路径；(c) 登录节点 `bash --version` 与两次不提交演练（上传后一次、冒烟通过后正式提交前一次），写出期望输出与停下条件；(d) 单路上传与 `sha256sum -c`；(e) 登录预检与冒烟作业；(f) 一条命令按顺序提交 F1、F2、F3、F4 与批级作业，另附逐条手工提交的完整命令（作业号用大写变量、从上一条 `qsub` 的输出取得）；(g) `qstat -u $USER`、`qstat -f F1_ID | grep -E "comment|estimated|job_state|exec_host"`；(h) 撤销作业时连同依赖它的作业一起撤销（依赖关系与 `qdel` 顺序）；(i) 结果下载与 `/hpctmp` 60 天自动清理。随后是详细步骤 A（上传）→ B（许可只核对属性）→ C（登录预检）→ D（冒烟）→ D2（可选 BUILD_ONLY）→ E（提交）→ F（监控）→ G（回收）→ H（停批处置，锁残留改名移开、不删除）。**命令中没有尖括号占位符**（逐个代码块检查）；要替换的值只有 `$HPC_USER`、`$WSL_USER`、作业号 `F1_ID` 等与运行编号 `RID`，都在上一行说明从哪里取得。

## 8. 干跑、bash 4.2 实测、静态检查与泄露扫描（指令第 6.3 条；无求解器、无许可）

### 8.1 干跑（VERIFIED，`evidence/hpc/dry/`）

在新包 `7d22dda1` 上用新的干跑脚本 `dry_hpc2.sh` 各做一次，分别用 bash 5.3.9 与本机编译的 bash 4.2.0（第 8.2 节；`PATH` 垫片让包内每一处嵌套的 `bash` 也用同一版本）。两次结果相同：

| 步骤 | bash 5 | bash 4.2 |
|---|---|---|
| 预检 `guards,sha,networks,env,profile,code,tools`（`licence`、`resources` 除外） | `PREFLIGHT OK`：46 个文件 SHA256 全部 OK；环境 284 / 284；四个网络 `all_equal`；档案正确；TimeLimit 864,000、状态 REGISTERED | 同左 |
| `BUILD_ONLY=1 TRUNCATE=56` 四个运行的进程 1 | 全部 `BUILD_CHECK passed`，129 s；LP 与登记值相同（F1、F3 729,156 × 1,603,380、非零 3,715,722；F2、F4 707,802 × 1,555,798、非零 3,565,488） | 同左，135 s |
| 作业体 `JOB_MODE=build_only JOB_RID=F3`（本机演练开关） | 退出码 0、`BUILD_CHECK_F3 passed`，记录里的超时读到 5,400 s | 同左 |
| 正式作业体 F1，环境里带测试开关 `BUILD_ONLY=1` | **拒绝**（退出码 2），什么都没启动 | 同左 |
| 正式作业体 F3，`JOB_DEPENDS=afterany:F1`，F1 没有结束（审查第 3 条） | 退出码 3、`STOP_SAFE:PREDECESSOR_NOT_ENDED:F3:F1`，没有运行预检、没有启动运行 | 同左 |
| `hpr_submit.sh --dry-run`（本机没有 qsub、没有授权文件、冒烟未过） | 5 行 `DRY-RUN: qsub ...` 依赖链正确，3 条 NOTE（授权、冒烟、qsub），`DRY_RUN_OK`，没有写任何文件 | 同左 |

两次的所有输出中都没有 `unbound`、`syntax error`、`command not found`。

**干跑脚本的一处隐患（发现并处理）：** 原干跑脚本 `dry_hpc.sh` 的最后一步运行一个"干净的"正式作业体，用来确认它在 PROPOSED 下被拒绝。包改为 REGISTERED 后，这一步会真正启动构建与求解。新脚本 `dry_hpc2.sh` 改用两条一定什么都不启动的路径（带测试开关的拒绝、前序检查的停批）；旧脚本开头加了拒绝运行（退出码 2），没有删除。历史：`917c8b63` 包的干跑见 `evidence/hpc/dry/DRY_RUN_HPC_917c8b63_bash5.txt`；`1e7b503c` 包在审查后被取代，没有单独干跑。

### 8.2 bash 4.2 实测（VERIFIED）

- **编译：** 从 GNU 官方源码 `bash-4.2.tar.gz`（SHA256 `a27a1179ec9c0830c65c6aa5d7dab60f7ce1a2a608618570f96bfa72e95ab3d8`）在本机编译，不安装，成品 `/home/jin/v3h/bash42/src/bash`，`GNU bash, version 4.2.0(2)-release`。第一次编译失败：当前 gcc 默认 C23，`mkbuiltins.c` 的旧式声明报错；加 `CC="gcc -std=gnu89"` 后成功。
- **行为确认：** `set -u` 下 `"${a[@]}"` 对空数组报 `unbound variable`；`${a[@]+"${a[@]}"}`、`${a[*]:-}` 安全。
- **替身测试（`PATH` 垫片，已核实测试子进程与嵌套调用都解析到 4.2，`evidence/hpc/tests/BASH42_SHIM_CHECK.txt`）：** `test_v3_hpc_runner.py`、`test_hpr_two_jobs.py`、`test_b4p_batch4.py` 共 **38 项全部通过**（`STANDIN_TESTS_bash42.txt`），覆盖 `run_batch4.sh` 的 `--only`、`POST_ONLY`（含停批）、`BUILD_ONLY` 与单机批次，作业体各模式，`make_pbs.sh`，`hpr_submit.sh` 的 `--dry-run`、经替身 `qsub` 的依赖链与 `--resume` 遇锁拒绝。
- **包上的干跑：** 第 8.1 节，与 bash 5 相同。
- **静态检查（`evidence/hpc/dry/BASH42_STATIC_7d22dda1.txt`）：** 包内 18 个脚本与作业脚本在 bash 4.2 下 `bash -n` 全部通过；4.3 / 4.4 / 5 才有的写法（`declare -n` / `local -n`、`wait -n` / `-p` / `-f`、`mapfile -d`、负数组下标、`${var@Q}` 等、`EPOCHSECONDS`、`BASH_ARGV0`、`inherit_errexit`、`[[ -v a[i] ]]`、`test -R`）命中 0。没有 `:-` 或 `+` 保护的数组展开逐条核对：`ORDER`（先检查 ≥ 3）、`RIDS`（运行表先检查 ≥ 2）、`need`、`cmd`、`pargs`、`reg`（构造时就有元素）、`PAIRS`（≥ 1）、`bad[*]`（只在个数 > 0 时展开）、`"${RIDS[@]:1}"`（四运行 BUILD_ONLY 已在 4.2 下跑过），其余都已有 `+` 保护。
- **Atlas 登录节点的 bash 版本未知**（本次不连 HPC），所以操作指南清单 (c) 让用户先看 `bash --version`，并在提交前做两次不提交演练，写明期望输出与停下条件。

### 8.3 泄露扫描（VERIFIED，`evidence/hpc/leak/`）

**方法：** 特征来自仓库外的特征文件（键名、ssh、IP、主机名，运行时读取，不写进扫描脚本），加上本机许可文件的值（只在内存中比较，从不打印）；命中只输出遮蔽片段（前 3 个字符、长度、字符类）。对象：分支 `p1_v3_20261102/` 全部文件、新包 48 个文件、`hpc_package_src/`、`cloud_package_b4/`、会话脚本目录 `/home/jin/v3h`（排除各次干跑目录与下载的 bash 4.2 源码，后者是第三方源码，不进包、不提交），以及 `5e372e5d..HEAD` 的每个提交。

- **提交前（`pre`，`1e7b503c` 包）：** 许可值 0；键名、ssh、主机名 0；IP 形 30 处，全部归类为非泄露：公共 DNS 地址（旧会话的连通性测试说明）、软件包四段式版本号（`env/` 锁文件，与 v2 包相同）、WSL 内核版本字符串（`D1_EVIDENCE.json`）。
- **提交前（`pre2`，`7d22dda1` 包与本报告）：** 许可值 0；键名、ssh、主机名 0；IP 形命中的类别与 `pre` 相同，新增的只有引用这些类别的文字（进度文件中"IP 形 30 处"一句、上一次分类记录里的遮蔽片段），都不是泄露。**实际命中 0。**
- **推送后（`post`）：** 见第 11 节。

## 9. 资源记账与测试

| 项 | 用量 / 上限 |
|---|---|
| 本机 Gurobi | **2 / 2**（两次冒烟，无重试；无人值守阶段 0 次） |
| HPC、AutoDL、VPN | 未连接、未上传 |
| 本机计算 | 约 **3.5 小时 / 4 小时**（各步墙钟累计、保守计；无人值守阶段约 0.6 小时：两次运行器测试、回归 9 分钟、bash 4.2 测试 7.5 分钟、另两个测试文件 4 分钟、打包、两次干跑 6.5 分钟、诊断） |
| 磁盘新增 | 约 **7.1 GB / 40 GB**（会话目录 `/home/jin/v3h` 4.1 GB，含 bash 4.2 源码与编译、各次干跑；`results_project/v3hpc` 1.1 GB；`work/` 下三份包 1.1 GB；worktree 0.75 GB） |

**测试（VERIFIED）：**
- **全量 `tests/research`（提交 `1e7b503c`，没有其他求解或测试同时运行，1,946 s）：831 通过、4 失败、0 跳过**（`evidence/hpc/tests/FULL_SUITE_1e7b503c.txt`）。`test_s1_built_networks.py::test_static_validation_passes_on_reload` 是已知基线。`test_s3_gates.py` 的 `test_static_b_gates`、`test_b12_with_override`、`test_b12_s3b_rebuilt` 与它同一根因：基点 `5e372e5d` 的配置已有 `cross_border.stock_mode`，旧的 S3-5 网络没有这个键，B12 的 `switch_metadata_matches` 为 False（`S3_GATES_B12_DIAGNOSIS.txt`）；`scripts_project/v5`、`phase4_static.py` 与该测试自基点未改；本 worktree 链接了 `results_project/s3_5`，所以这三项不再像以前的 worktree 那样跳过。以前的"3 项已知失败"中的 `test_s4c_0.py` 两项本次通过（WACC 表可达）。按授权第 2 节"其他情况：最保守、可逆"，判为与基线同类、不指向本次改动，不改闸门代码。其中含 scipy `linprog` / HiGHS 的玩具 LP（无模型网络、无 Gurobi），照实列出。
- **`1e7b503c` 之后的改动**（运行器、作业体、提交与状态脚本、一致性检查、`b4_batch4.py` 的 `walltime_components`、定义文件、计划、测试）：读取这些文件的测试文件全部重跑（检索 `tests/research` 得到 5 个文件 + 新测试文件）。bash 5：`test_v3_hpc_runner.py` 11 项、运行器回归（`test_b4p_batch4`、`test_hpr_two_jobs`、`test_v3_runners`、`test_b4p_paths`、`test_dfx_runner`）54 项、`test_b4p_split.py` 与 `test_v3_runners.py` 19 项，全部通过；bash 4.2：38 项全部通过。
- **没有在最终提交上再跑一次全量：** 授权第 2 节只在出现新失败时要求重跑全量，本次没有新失败；改动涉及的代码都由上述测试覆盖；再跑一次约 0.55 小时，会使本机计算超过指令的 4 小时上限（约 3.5 + 0.55 h）。所以不再跑，记录在此。

## 10. 偏差、发现与未覆盖

1. **审查 S3-4 的"现在一致"不准确：** 两份 `DIRECT` 清单相差 `co2_transit_rail_freight`；统一后只改变两个诊断量（第 1 节）。
2. **我在构建前写的计数笔误：** 第 12.3 节"810 条"应为 270 条；集合与字段的规定不变，已更正并注明（第 2 节）。
3. **核对脚本的效率问题：** 第一版 O(n²) 写法卡了 15 分钟，终止后改正重跑；不影响结果。
4. **全尺寸 2920×3h LP 未在本机构建**（10 GiB 放不下）：规模由线性外推给出，同一方法对 v2 与 D2 实测逐位相同；HPC 上可用可选的 BUILD_ONLY 作业（步骤 D2）实测。
5. **四运行链在 HPC 上的真实调度未演练：** 依赖链、启动锁、停批传播、前序检查与批级汇总都用替身测试验证；HPC 冒烟作业只覆盖 F1、F2 两次真实会话。
6. **T < U（第 5.2 节）：** 240 h 上限使高值区间上段（Atlas 每次迭代 ≥ 约 1,850 s）的 F1、F3 会被早期测速止损；按授权不改，请审阅端知悉。外推本身依赖 CPU 因子假设（1.0–1.6），没有 Atlas 上的求解测速。
7. **`test_s3_gates.py` 三项失败**（第 9 节）：与已知基线同一根因，不在本次改动范围。
8. **旧干跑脚本的隐患**（第 8.1 节）：已加拒绝运行，改用 `dry_hpc2.sh`。
9. **审查第 2 条是已知局限**（第 6.1 节），求解路径未改。
10. **干跑中由被测代码删除的文件：** BUILD_ONLY 作业体按设计删除它自己刚写出的 LP 文件（`LP_DELETED`，干跑目录中的临时文件，这是包在 HPC 上节省磁盘的登记行为）；我写的脚本没有删除任何文件（旧包、旧脚本都是改名或加拒绝）。
11. **Atlas 登录节点的 bash 版本未知：** 本机 bash 4.2 实测全过；指南让用户先看版本并做两次演练。

## 11. 提交、推送与复制

**分支：** `codex/v3-hpc-20261104`（自 `5e372e5d`；独立 worktree `/home/jin/wt_v3_hpc`；不改 main、不 force-push、不合并；指令没有要求开 PR，本次没有开）。

| 提交 | 内容 |
|---|---|
| `a1ef782b` | 规则与小修；四个网络的构建提交 |
| `a4607714` | 四个网络的登记与冒烟计划（冒烟之前推送） |
| `917c8b63` | 冒烟记录、预测、`RUN_PLAN_HPC_V3.md`、四运行的运行器 |
| `1e7b503c` | 作业体 BUILD_ONLY 文字修正 |
| **`7d22dda1`** | 登记的时限（第 5 节）、审查第 1、3–6 条、`--dry-run`、测试；**部署包的 `COMMIT`** |
| 本报告所在的提交 | 报告、指南定稿、证据、会话脚本；提交号与推送结果写在 `V3_HPC_PROGRESS.md` 最后一行（报告不能写自己的提交号） |

`7d22dda1` 之后只改 `research/` 下的文档、证据与会话脚本，包内代码不变（包内文档是 `7d22dda1` 的版本；之后对指南和计划都没有改动）。

**复制到 `work/p1_v3_20261102/`：** 本会话新建的文件：`V3_HPC_PROGRESS.md`、`RUN_PLAN_HPC_V3.md`、`HPC_OPERATOR_GUIDE_V3.md`、`V3_REPORT_HPC_PACKAGE.md`、`batch_def/BATCH_DEF_2920x3h_v3hpc.json`、`hpc_v3/`、`evidence/hpc/`、`scripts/wsl_v3h/`。共用文件 `RUN_PLAN_V3.md`、`V3_RULES.md`、`batch_def/BATCH_DEF_2920x3h.json`：复制前读了 `V3_PROGRESS.md` 末尾，确认 V27 会话的关机记录（第二次关机 02:12:51 SGT，02:14:08 重新登录被拒，已核实停止；"补充 07 全部完成"）；并核对 `work/` 中这三个文件与基点 `5e372e5d` 逐字节相同（V27 没有改它们，SHA256 前 12 位 `76872ca32999` / `08accba45c02` / `0376bc1563b4`），所以覆盖它们不会丢失 V27 的内容，旧内容在 git `5e372e5d` 中。

**推送与推送后的泄露扫描：** 见 `V3_HPC_PROGRESS.md` 最后一行。

**终点：** 部署包、操作指南、报告定稿并提交推送。剩下的只有用户的步骤：按 `HPC_OPERATOR_GUIDE_V3.md` 开头的清单，连 VPN、单路上传、`sha256sum -c`、登录预检、冒烟、两次不提交演练，再提交 F1–F4 与批级作业。不连 HPC、不连云、不连 VPN、不上传。
