# S4G 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4G_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-17 18:55 SGT），开始前核对 SHA256 = `2fd959e9134804a51aecc68b252b2ebe966813e65ed7dabd945ad3953a0d915c`，与 `S4G_INSTRUCTION_SHA256.txt` 一致（2026-10-17，VERIFIED）。模型 Opus 5.5。所有过程说明一律用中文。

- **分支：** `codex/s4g-readjust-impedance-20261017`，自 S4F 最终交付提交 04681769 开出（已核实 = PR #30 的 headRefOid `04681769cc4af29abbc034962ab1e212dc5b4361`）；draft PR 叠在 #30 上（基分支 `codex/s4f-extension-caps-20261017`）。
- **仓库：** `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4g_20261017/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4g_20261017\`。
- **求解：** Gurobi `formal_barrier`（档案 A）；止损：56×3h 单次 30 分钟；非最优或求解器容差门槛不通过即停，不改参数、不重试。
- **资源（第 7 条）：** 本步不需要任何下载。适用工作原则第 3、6、7、8 条。
- **停止条件：**
  - 已入库源码中找不到 s_nom 与线型、回路数的关系，或关系与指令不同；
  - 修正后 PyPSA 实际使用的电抗没有随回路数重算；
  - 冒烟出现非最优或求解器容差门槛不通过。
- **只记录、不修改：** LA–VN 存量和其他交流线的一致性，列入用户决定事项。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4G-0 | 准备：§7 答复登记 | 完成 | 见提交记录 | 注册表片段 `s4g_0`（4 行）；整个 `tests/` 516 通过 |
| S4G-1 | 跨境交流线的电气参数（第 98 项） | 未开始 | — | |
| S4G-2 | `existing_port` 敏感性补泰国封存（第 99 项 b） | 未开始 | — | |
| S4G-3 | 冒烟 | 未开始 | — | |
| S4G-4 | 云端部署包 | 未开始 | — | |
| S4G-5 | 上云前清单与交付 | 未开始 | — | |

## 提交记录（分支 `codex/s4g-readjust-impedance-20261017`）

| 提交 | 内容 |
|---|---|
| （S4G-0 提交） | S4G-0：§7 答复登记 |

## 续行点

S4G-0 完成。下一步 S4G-1：
- 在已入库源码中找线型与 `s_nom` 的关系（PyPSA-Earth `base_network.py`）和 PyPSA 重算 `x`、`r`、`b` 的位置；
- 对 19 条线按线型反推 `num_parallel`；
- 开关 `research.network.readjust_impedance`。

## 对 S4F 报告 §7 的答复（用户已确认，指令原文摘要）

1. 作者 readjust 改过的 19 条跨境交流线：19 条全部按线型关系使电气参数与容量一致（第 98 项）。不只改环路中的 16 条；不重新聚类，聚类成员问题登记为局限（C 级）。
2. `apg_plans` 取值规则：同意现行规则（第 99 项 a）。
3. 老挝过境 `existing_port` 敏感性：终点在泰国港口的老挝节点补"进入泰国国内封存"链路，只在该敏感性中（第 99 项 b）。
4. 上云：S4F 部署包作废，以 S4G 重建的部署包为准（第 99 项 c）。

## 用户中途指示

（暂无）
