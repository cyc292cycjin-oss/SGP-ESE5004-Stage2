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
| S4J-1 | 非工业电力负荷（第 104 项） | 未开始 | — | |
| S4J-2 | 输送损耗（第 105 项 a） | 未开始 | — | |
| S4J-3 | TH–MY 直流与换流器（第 105 项 b） | 未开始 | — | |
| S4J-4 | 云端脚本与部署文档（第 106 项 a、b） | 未开始 | — | |
| S4J-5 | 静态复核 | 未开始 | — | |
| S4J-6 | 冒烟 | 未开始 | — | |
| S4J-7 | 部署包与上云前清单 | 未开始 | — | |

## 提交记录（分支 `codex/s4j-demand-losses-20261018`）

| 提交 | 内容 |
|---|---|
| （S4J-0 提交） | S4J-0：S4I §5 答复登记 |

## 续行点

S4J-0 完成。下一步 S4J-1：查清非工业电力负荷的现行计算（`s2_layers.py` Astar 残差）与需求表部门；逐部门判断是否已单独建模。

## 对 S4I 报告 §5 的答复（用户已确认 2026-10-18 19:44 SGT，指令原文摘要）

1. **K1 → 第 104 项：** 非工业电力负荷改为需求表中不单独建模部门之和，Astar 只给小时形状；开关 `research.demand.nonindustrial_electricity: table_sectors | astar_residual`。
2. **U1 → 第 105 项 a：** 按 PyPSA-Eur v2025.07.0 缺省值加输送损耗（交流线损 2、直流 0.98 × 0.977^(L/1000) 有损双向、H₂ / 气管道压缩耗电、CO₂ 无损、配电网 0.97 不采用）；开关 `research.network.transmission_losses: pypsa_eur | none`。
3. **U2 → 第 105 项 b：** TH–MY 直流改双向；两端固定 B2B 随直流扩建、不另计成本；其他直流链路同结构的同样处理。
4. **K2、U3 → 第 106 项 a、b：** 撤下 `lanes3`，`lanes2` 加 ≥ 5 分钟间隔，首批推荐 `serial`；预检检查 `/usr/bin/time`。
5. **R1–R11 → 第 106 项 c：** 按 S4I 建议时点登记。
6. **联盟算力估算 → 第 106 项 d：** 作为第 14 项的依据。

## 发现但未处理（执行中随时记录，交付时写入报告）

（暂无）

## 用户中途指示

（暂无）
