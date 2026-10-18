# S4J 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4J_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-18 19:50 SGT），开始前核对 SHA256 = `c20957448c69128c05eaf4e271bcca7f98eecc7ccd3121cd37f3581daff3348f`，与 `S4J_INSTRUCTION_SHA256.txt` 一致（2026-10-18，VERIFIED）。模型 Opus 5.5。所有过程说明一律用中文。

- **分支：** `codex/s4j-demand-losses-20261018`，自 PR #33 最新提交 09ffb727 开出（已核实 = 远端 `codex/s4i-preflight-audit-20261018` 头 `09ffb727114be437abf078a5393d0a2cb3ea403e`）；draft PR 叠在 #33 上。S4H 部署代码 6eead675 到 09ffb727 之间只增加了 4 个 S4I 审查脚本，没有模型代码改动。
- **仓库：** `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4j_20261018/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4j_20261018\`。
- **范围：** 只实现第 104–106 项；其他发现写入报告"发现但未处理"一节，不修改，除非触发停止条件。
- **求解：** Gurobi `formal_barrier`（档案 A）；止损：56×3h 单次 30 分钟；非最优或求解器容差门槛不通过即停，不改参数、不重试。
- **资源：** 本步不需要任何下载；PyPSA-Eur 文件库内没有时写明缺什么，按库内配置与 `prepare_sector_network.py` 实现并说明等价性。
- **停止条件：**
  - 需求表中某部门是否已单独建模无法确定（S4J-1 第 2 点）；
  - PyPSA 0.30.3 不支持 `transmission_losses`，或其行为与 PyPSA-Eur 不同且无法说明；
  - 有损耗后 B16 恒等式不成立且原因不明；
  - 冒烟出现非最优，或求解器容差门槛不通过；
  - 静态复核发现 S4J 引入的新错误。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4J-0 | 准备：S4I §5 答复登记 | 完成 | 见提交记录 | 注册表片段 `s4j_0`（18 行：K1/U1/U2/K2/U3 答复、联盟算力估算、范围规则，R1–R11 按 S4I 建议时点） |
| S4J-1 | 非工业电力负荷（第 104 项） | 完成 | 见提交记录 | `s2_layers.add_demand_layer` 的 Astar 段加开关 `research.demand.nonindustrial_electricity: table_sectors \| astar_residual`；基础负荷 = 需求表中居民 + 商业 + 农业及其他 + 交通的电力（交通电力行在代码中没有单独负荷，原方法扣减后未补回；工业电力在 `pypsa_eur_2050` 下按路线单独建模，`bas_fixed` 时并入），Astar 只给小时形状与节点分配；东盟 1,079.4 → 1,032.4 TWh，VN 30.0 → 197.2 TWh（= S4I 方案 (b)），与方案 (b) 的差只在交通电力（SG 4.75、MY 1.06、ID 0.77、TH 0.55、PH 0.26 TWh）；`astar_residual` 构建与 S4H 逐组件相同，主算只改 96 个 Astar 负荷；整个 `tests/` 534 通过 |
| S4J-2 | 输送损耗（第 105 项 a） | 完成 | 见提交记录 | 新模块 `s4j_layers.py`（`apply_transmission_losses`，开关 `research.network.transmission_losses: pypsa_eur \| none`），构建时在单条扩建上限之后施加；直流效率 0.98 × 0.977^(L/1000)（2.1–4.8 %），H₂ / 气管道压缩耗电 0.018 / 0.01 MWh_el/(MWh·1000 km) 接送端电力母线，CO₂ 无损；双向链路拆为正向 + `-reversed`（321 条：直流 12、H₂ 148、气 161），单向的 TH–MY 直流与 5 条现有气管道保留方向；反向容量 = 正向（钩子 `research_lossy_bidirectional_sync`，等价于 PyPSA-Eur `Link-bidirectional_sync`，`solve_network.py` 不在库内）；交流线损由 `s2_solve.py` 按网络元数据传 `transmission_losses=2`（PyPSA 0.30.3 源码逐行断言）；静态校验的跨境集合比较排除反向复制；账本对反向链路沿用正向长度份额；`none` 构建与 S4J-1 逐组件相同；56 时段建模检查：线损变量 8,288、同步 321 行，LP 675,693 列 / 1,517,932 行；整个 `tests/` 537 通过 |
| S4J-3 | TH–MY 直流与换流器（第 105 项 b） | 完成 | 见提交记录 | `s4j_layers.apply_dc_converter_rule`（单条上限之后、损耗拆分之前；两种损耗口径都施加）：Khlong Ngae–Gurun 单向 → 双向（有损时拆为正向 + `-reversed`，无损对照 `p_min_pu` = −1）；"DC 母线只连 1 条直流 + 1 台 B2B"的换流站结构（TH21 0、MY_Peninsular22 0）B2B 改为可扩建、零资本成本，B2B 容量 − 2,000 = 直流容量 − 300（钩子 `research_b2b_follows_dc`），上限 22,000 MW；增量形式保留现有 2,000 MW（两个 DC 母线上还有发电候选，只能经 B2B 接入交流网）；PH_Visayas10 0（2 条直流 + 1 台 B2B）结构不同只报告；其余直流均已双向；不互联构建与 S4J-2 相同；建模检查 B2B 2 行、同步 322 行；整个 `tests/` 539 通过 |
| S4J-4 | 云端脚本与部署文档（第 106 项 a、b） | 完成 | 见提交记录 | 部署包脚本复制为 `p1_step4j_20261018/cloud_package/`：`run_365x24h.sh` 撤下 `lanes3`（拒绝并说明原因），`lanes2` 启动前与通道内衔接前各等 330 秒（`LICENCE_GAP`），首批推荐 `serial`；`preflight.sh` 检查 `/usr/bin/time -v`，缺失为失败项并提示 `apt-get install -y time`，只接受 `serial` / `lanes2`；`make_package.sh` 改为 S4J（允许后续改动 `s4j_5/6/7_*`、`tests/`；第二批 12 项；S4H 包作废）；空跑测试通过；`CLOUD_DEPLOY_STEPS.md` 改为 S4J 版，`CLOUD_RESOURCE_ESTIMATE.md` 加 §18（三通道作废、许可 2 会话、令牌 ≥ 5 分钟） |
| S4J-5 | 静态复核 | 完成 | 见提交记录 | 在代码 66473e9a 上构建四个网络（2920×3h + 365×24h），重跑 `s4i_static_audit.py`、`s4i_followups.py`，`s4j_5_review.py` 与 S4I 逐项比较：726 处差异全部归因于 S4J-1/2/3，没有新增问题；需求总量四个网络都 −46.977 TWh（= S4J-1，只电力变）；损耗规则全部成立（直流 2.1–4.8 %、压缩端口在电力母线、反向复制 322 条、CO₂ 无损、5 条单向气管道保留）；TH–MY 直流一体化中正反两条、不互联中移除；NZE 与一体化仍只差 136 台燃料供给的边际成本；不互联跨境组件 0，一体化跨境 62 线 + 292 链路（正向 176、反向 116）；碳平衡新增 322 条全部平衡 |
| S4J-6 | 冒烟 | **停止（停止条件触发）** | 见提交记录 | 代码 ad81a01e，档案 A；一体化 STEPS **SUBOPTIMAL**（barrier 118 次，原始残差停在 1.4–3.1，目标 6.56829e11），求解器容差门槛三项未通过；按止损规则不互联与 NZE 未运行，不改参数、不重试；只读诊断：系数范围与 S4H 相同，非最优解中 131 / 322 对拆分链路正反向同时送电（气管道 100 对，11.2 TWh），推测为管道拆分带来的退化与档案 A 的 1e-8 精度共同作用（PyPSA-Eur `gurobi-default` BarConvTol 1e-5）；停止报告 `S4J_STOP_01_SMOKE_SUBOPTIMAL.md` |
| S4J-6 诊断 1 | 关闭输送损耗的隔离诊断（用户授权） | 完成，结果 **仍为 SUBOPTIMAL** | 见提交记录 | 覆盖项 `network.transmission_losses=none`，代码 aa4455e9，档案 A，56×3h，一体化 1 个运行：barrier 151 次后停滞（原始残差约 1.07），目标 6.32999e11（未收敛），门槛未过；非最优不只来自 S4J-2，S4J-1 或 S4J-3 至少其一涉及；用户追加的第二次诊断以"诊断 1 最优"为前提，前提不成立，**未运行** |
| S4J-7 | 部署包与上云前清单 | 暂停（等待用户决定） | — | |

## 提交记录（分支 `codex/s4j-demand-losses-20261018`）

| 提交 | 内容 |
|---|---|
| 4b15d7b8 | S4J-0：S4I §5 答复登记 |
| 34de92c9 | S4J-1：非工业电力负荷按需求表部门 |
| 8c4bf2ae | S4J-2：输送损耗 |
| 8cbf33d2 | S4J-3：TH–MY 直流双向、换流站 B2B 随直流扩建 |
| 66473e9a | S4J-4：云端脚本与部署文档 |
| ad81a01e | S4J-5：静态复核 |
| 7b5e7ce4、aa4455e9 | S4J-6：冒烟一体化 SUBOPTIMAL，停止报告与诊断证据 |
| （诊断 1 提交） | S4J-6 诊断 1：关闭输送损耗仍为 SUBOPTIMAL，停止报告 §5–§6 |

## 续行点

**S4J-6 触发停止条件（冒烟非最优），已停止，等待用户决定。** 见 `S4J_STOP_01_SMOKE_SUBOPTIMAL.md` §4 的可选下一步（都需要用户授权）。用户决定后：按决定处理 → 重跑 S4J-6 三个运行（`/home/jin/s4j6_run.sh`，输出目录需换新，旧结果保留）→ S4J-7（`/home/jin/s4j7_build.sh`、`s4j7_extrap.sh`、`s4j7_final.sh` 已备好，`s4j_7_collect_evidence.py` 已写）。

## 对 S4I 报告 §5 的答复（用户已确认 2026-10-18 19:44 SGT，指令原文摘要）

1. **K1 → 第 104 项：** 非工业电力负荷改为需求表中不单独建模部门之和，Astar 只给小时形状；开关 `research.demand.nonindustrial_electricity: table_sectors | astar_residual`。
2. **U1 → 第 105 项 a：** 按 PyPSA-Eur v2025.07.0 缺省值加输送损耗（交流线损 2、直流 0.98 × 0.977^(L/1000) 有损双向、H₂ / 气管道压缩耗电、CO₂ 无损、配电网 0.97 不采用）；开关 `research.network.transmission_losses: pypsa_eur | none`。
3. **U2 → 第 105 项 b：** TH–MY 直流改双向；两端固定 B2B 随直流扩建、不另计成本；其他直流链路同结构的同样处理。
4. **K2、U3 → 第 106 项 a、b：** 撤下 `lanes3`，`lanes2` 加 ≥ 5 分钟间隔，首批推荐 `serial`；预检检查 `/usr/bin/time`。
5. **R1–R11 → 第 106 项 c：** 按 S4I 建议时点登记。
6. **联盟算力估算 → 第 106 项 d：** 作为第 14 项的依据。

## 发现但未处理（执行中随时记录，交付时写入报告）

1. 原方法（`astar_residual`）把需求表的交通电力行从 Astar 中扣掉，但没有任何单独负荷补回（电动车只来自交通燃料行的折算），东盟合计少计 7.39 TWh（SG 4.75、MY 1.06、ID 0.77、TH 0.55、PH 0.26）。`table_sectors` 已把它计入基础负荷，这是与 S4I 方案 (b) 的唯一差别。
2. BN 需求表中居民 + 商业 + 农业及其他 + 交通的 2050 电力 3.17 TWh，略低于 2019 年 3.20 TWh（倍数 0.99）；MM 1.11、SG 1.36、LA 1.41 倍也偏低。属需求表本身的投影，未修改。
3. 交流线损近似（PyPSA `define_loss_constraints`，与 PyPSA-Eur 同一函数）：切点在 k/2 × `s_max_pu` × `s_nom_max`（本模型 `s_nom_max` = 存量 + 20 GW），流量低于 3.5–13 GW 时近似损耗为 0；扩建不降低电阻（回路数固定），一回候选线在第一个切点的损耗率中位数 55 %、最大 161 %，存量线（S4G 修正后回路数很小）中位 76 %。物理上一回线满载（× 0.7）约 2.5 %/100 km。冒烟中量化实际损耗；列入用户决定事项。
4. 5 条现有跨境气管道单向（S4I R11），按"只拆分双向链路"保留方向，只加压缩耗电。
5. PH_Visayas10 0 的 DC 母线连 2 条直流（至 PH_Visayas7 0、PH_Luzon5 0）与 1 台固定 2,000 MW 的 B2B（至 PH_Visayas7 0），结构不同于换流站，只报告；PH_Luzon9 0 的 DC 母线没有 B2B。两个 PH DC 母线上都有发电、储能和转换候选。
7. 静态复核中的预期差异（不是错误）：反向链路长度记为 0（PyPSA-Eur 约定，`length_original` 保留），S4I 审查脚本 B3 的"长度 / 大圆距离"中位数因此下降；一体化与不互联在两台 TH–MY B2B 上属性不同（不互联中直流链路被移除，B2B 维持固定 2,000 MW）。
6. B2B 增量联动的选择：字面"随直流链路扩建"也可读作 B2B 容量 = 直流容量；那样 TH21 0 / MY_Peninsular22 0 的现有 2,000 MW 换流器会降到 300 MW，影响 DC 母线上的发电候选，所以采用增量形式。列入用户决定事项（可改为等量）。

## 用户中途指示

1. 2026-10-18：授权停止报告 §4 第 1 项——"同一冒烟加覆盖项 network.transmission_losses=none（保留 S4J-1、S4J-3），档案 A，56×3h，只跑一体化 1 个运行，仅作诊断，不改其他参数。" 已执行，结果 SUBOPTIMAL。
2. 2026-10-18：条件授权——"若无损耗诊断为最优，授权再做一次同条件隔离诊断：保留交流线损与直流损耗，关闭 H₂ 与气管道的压缩耗电及其拆分（管道恢复为单条双向、无损耗）……两次诊断结果出来后停止，写入停止报告，等待审阅。" 条件不成立（诊断 1 非最优），未运行；结果已写入停止报告 §5–§6，停止等待审阅。
