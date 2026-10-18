# S4K 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4K_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-18 22:45 SGT），开始前核对 SHA256 = `a803f1653736640f1358659b156e6d9dbf7c72be61b9455863f793dea75825d5`，与 `S4K_INSTRUCTION_SHA256.txt` 一致（2026-10-18，VERIFIED）。模型 Opus 5.5。所有过程说明一律用中文。

- **分支：** `codex/s4k-ac-loss-proxy-20261018`，自 PR #34 最新提交 36b8195b 开出（已核实 = 远端 `codex/s4j-demand-losses-20261018` 头 `36b8195bc8508c1f3ea1b4a6475fd860d075d16f`）；draft PR 叠在 #34 上。
- **仓库：** `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4k_20261018/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4k_20261018\`。
- **范围：** 只实现第 108 项；其他发现写入报告"发现但未处理"一节，不修改，除非触发停止条件。
- **求解：** Gurobi `formal_barrier`（档案 A，参数不改）；56×3h 单次止损 30 分钟；不重试。授权覆盖 S4K-3 三项冒烟；一体化非最优或求解器容差门槛不通过时，只做 1 个条件诊断（`network.ac_losses=none`），然后停止。
- **停止条件：**
  - PyPSA 0.30.3 的损耗结构与指令描述不同且无法说明；
  - λ 核对与预期相差超过 20 %；
  - B16 恒等式不成立且原因不明；
  - 冒烟非最优或求解器容差门槛不通过（条件诊断后停止）；
  - 静态复核发现 S4K 引入的新错误。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4K-0 | 登记第 108 项与 S4J §12 第 2、3 项；台账补 S4I 条目 | 完成 | 见提交记录 | 注册表片段 `s4k_0`（6 行：第 108 项、不互联中 B2B 维持 S4H 状态、`th_my_hvdc=s4h` 只保留开关、台账补 S4I、范围规则、问题来源 S4J 报告）；`research/STAGE2_PROJECT_LEDGER.md` 在 S4J 条目之前补 S4I 条目 |
| S4K-1 | 交流线性损耗代理 | 待做 | — | |
| S4K-2 | 静态复核 | 待做 | — | |
| S4K-3 | 冒烟（三项） | 待做 | — | |
| S4K-4 | 部署包 | 待做 | — | |
| S4K-5 | 上云前清单、报告与交付 | 待做 | — | |

## 提交记录（分支 `codex/s4k-ac-loss-proxy-20261018`）

| 提交 | 内容 |
|---|---|
| （S4K-0 提交） | S4K-0：第 108 项登记、台账补 S4I 条目 |

## 续行点

S4K-0 完成后：S4K-1，先读 PyPSA 0.30.3 的 `transmission_losses` 实现（变量、节点平衡、容量约束、基尔霍夫、求解后 `p0` / `p1`），再写代理与 λ。

## 发现但未处理（执行中随时记录，交付时写入报告）

（暂无）

## 用户中途指示

（暂无）
