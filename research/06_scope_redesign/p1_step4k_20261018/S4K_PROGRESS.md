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
| S4K-1 | 交流线性损耗代理 | 完成 | 见提交记录 | 新模块 `s4k_layers.py`：开关 `research.network.ac_losses: linear_proxy \| pypsa_tangent \| none`、`ac_loss_reference_loading: 0.5`；构建时逐线写 λ（`ac_loss_lambda`），求解时 `transmission_losses` = 0，钩子 `research_ac_loss_proxy`（研究钩子中最先执行）用 PyPSA 自己的函数建 `Line-loss`、重建节点平衡与线路容量约束（损耗两端各 −0.5、容量约束 ∓1），再加 `loss ≥ ±λ·s`、`loss ≤ λ·s_max_pu·s_nom`；求解后 PyPSA `assign_solution` 自动 `p0`/`p1` 各加一半损耗（VERIFIED 源码行号，PyPSA 结构与指令描述一致）。148 条线全是 `Al/St 240/40 4-bundle 380.0`（r 0.03 Ω/km、i_nom 2.58 kA、380 kV、`s_max_pu` 0.7），λ 只随长度变：α 0.5 时 0.77–13.66 %，中位 3.50 %（跨境 4.50 %、国内 3.02 %）；100 km 核对 1.2348 %（预期约 1.2 %，+2.9 %）/ 2.4695 %（约 2.5 %，−1.2 %）；长度 / 大圆距离：存量 1.250、候选 1.244–1.252（已含 1.25）。构建核对：代理主算与 S4J-7 构建只差 Line 列 `ac_loss_lambda`；`pypsa_tangent`、`none` 构建与 S4J-7 逐组件相同。56 时段建模核对（EXACT）：代理模型减去损耗项后，节点平衡（148,064 + 15,120 行）、线路容量（2 × 8,288 行）、基尔霍夫（3,976 行）与无损模型逐行相同；损耗项 16,576 个 −0.5、容量约束 ∓1；代理行 3 × 8,288；LP 675,750 列 / 1,501,471 行（S4J 切线模型 1,518,047 行，−16,576）。注册表片段 `s4k_1`（6 行，含对 PyPSA-Eur 的偏离登记与账本计算式）；数据表 `LAMBDA_S4K1.csv`、`TANGENT_VS_PROXY_S4K1.csv`、`AC_LOSS_PROXY_S4K1.json`；整个 `tests/` 546 通过。构建在提交前进行（dirty 4，开发阶段），S4K-2 在提交后的代码上重建 |
| S4K-2 | 静态复核 | 完成 | 见提交记录 | 在 e4d3c73a（工作树干净）上构建四个网络（2920×3h + 365×24h），重跑 `s4i_static_audit.py`、`s4i_followups.py`，`s4k_2_review.py` 与 S4J（补充 01 (a) 的 `s4j3b`）逐项比较：审查差异 5 处，全部是预期的——四个网络的钩子清单多了 `research_ac_loss_proxy`，情景间元数据差异多了 `research_ac_losses`（λ 统计因不互联只有国内线而不同）；A 节无新增问题。四个网络与 S4J 逐组件比较只差 Line 列 `ac_loss_lambda`，链路（直流、管道损耗）完全不变；λ 在全部交流线上、与公式一致、其他组件没有；元数据 `ac_losses` = linear_proxy，求解 `transmission_losses` = 0。56 时段建模核对：`Line-loss` 一体化 8,288 / 不互联 4,816 个，切线行 0，代理行各 3 组；LP 一体化 675,750 列 / 1,501,471 行，不互联 652,099 / 1,447,897。NZE 与一体化仍只差 136 台燃料供给的边际成本（另有与 S4J 相同的 `source_identity` 元数据字段）；不互联跨境组件 0，一体化 62 线 + 292 链路 |
| S4K-3 | 冒烟（三项） | 待做 | — | |
| S4K-4 | 部署包 | 待做 | — | |
| S4K-5 | 上云前清单、报告与交付 | 待做 | — | |

## 提交记录（分支 `codex/s4k-ac-loss-proxy-20261018`）

| 提交 | 内容 |
|---|---|
| a8a53cb9 | S4K-0：第 108 项登记、台账补 S4I 条目 |
| e4d3c73a | S4K-1：交流线性损耗代理 |
| （S4K-2 提交） | S4K-2：静态复核（另含 S4K-3 汇总脚本） |

## 续行点

S4K-2 完成后：S4K-3 冒烟用 `/home/jin/s4k3_run.sh`（含条件诊断：一体化非最优或容差门槛不通过时，只做 `network.ac_losses=none` 一个诊断运行后停止），输出 `results_project/s4k/s4k3/`；通过后汇总 `s4k_3_summary.py`（对比 S4J s4j6b 与 S4H s4h3）。

## 发现但未处理（执行中随时记录，交付时写入报告）

1. 存量线的固定回路数二次损耗（`r_pu_eff × 流量`，即 S4J 切线所逼近的曲线）在 500 MW 时中位已有 5.2 %、3.5 GW 时 36 %：存量线电阻按其 `num_parallel` 计（全网 0.018–31.9，S4G 修正后部分线很小），与存量容量不成比例。线性代理按一回线、参考负载计 λ，与 `num_parallel` 无关，所以不受影响；只记录（S4J 切线结果的成因之一）。
2. λ 最大的几条线来自聚类后相距很远的节点对：MM–TH 一条 1,106 km（λ 13.7 %）、LA–TH 最大 9.9 %、ID–MY 最大 7.4 %。这么长的交流线现实中多为直流或分段建设，按交流线型计损耗是聚类拓扑的结果；未修改，只记录。

## 用户中途指示

（暂无）
