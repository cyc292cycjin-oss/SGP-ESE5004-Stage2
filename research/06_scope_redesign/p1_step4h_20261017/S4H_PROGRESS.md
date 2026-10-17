# S4H 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4H_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-17 21:40 SGT），开始前核对 SHA256 = `a029bd64cef2ae1b84aec4ebc186ede21630283d17153df9aed4ae32d1fd33bd`，与 `S4H_INSTRUCTION_SHA256.txt` 一致（2026-10-17，VERIFIED）。模型 Opus 5.5。所有过程说明一律用中文。

- **分支：** `codex/s4h-lavn-candidates-20261017`，自 S4G 最终交付提交 78c95a75 开出（已核实 = PR #31 的 headRefOid `78c95a75cd48afefc11e4e9e747c2ce96f0f2f1d`）；draft PR 叠在 #31 上（基分支 `codex/s4g-readjust-impedance-20261017`）。
- **仓库：** `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4h_20261017/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4h_20261017\`。
- **范围：** 只实现第 100、101 项；其他发现写入报告"发现但未处理"一节，不修改，除非触发停止条件。
- **求解：** Gurobi `formal_barrier`（档案 A）；止损：56×3h 单次 30 分钟；非最优或求解器容差门槛不通过即停，不改参数、不重试。
- **资源（第 7 条）：** 本步不需要任何下载。适用工作原则第 3、6、7、8 条。
- **停止条件：**
  - 补候选线时，某国家对按第 94 项规则无法确定端点或类型；
  - 构建后 PyPSA 实际使用的电抗没有按新回路数重算；
  - 冒烟出现非最优，或求解器容差门槛不通过；
  - 不互联目标值与 S4G 不同且原因不明。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4H-0 | 准备：§7 答复登记 | 完成 | 见提交记录 | 注册表片段 `s4h_0`（5 行：4 项答复与本步范围规则）；整个 `tests/` 523 通过 |
| S4H-1 | LA–VN 存量（第 100 项） | 完成 | 见提交记录 | `s4h_layers.apply_la_vn_stock`（构建时；`research.network.la_vn_stock: aims_zero \| author`）；线路 59/60/63/64 `s_nom = s_nom_min = 0`、可扩建、上限 20,000 MW、跨境类、长度与单位成本不变（46.497 EUR/MW/km/a）；注册表 `la_vn_grid_stock_2025` = 0（B 级）；IPP 估算 572 MW × 230.9–515.1 km × 46.497 = 6.14–13.70 M EUR/a（C 级）；author 构建与 S4G 逐组件相同，不互联构建与 S4G 相同；主算只有 4 条线改变，x 由 558,762 Ω 降为 44–99 Ω（回路数暂按模板 1.286，S4H-2 改为 1），基尔霍夫系数跨度 2.3e5 → 943；整个 `tests/` 526 通过 |
| S4H-2 | 候选线与 APG17 的电抗（第 101 项） | 完成 | 见提交记录 | (a) `apply_candidate_num_parallel`，`corridors.candidate_num_parallel: one_circuit`：46 条零容量交流候选线（32 条 S4E-1/APG11 + 4 条 LA–VN + 10 条新补）`num_parallel` = 1，存储 x = 线型公式 = PyPSA 重算（相对差 0）；(b) `READJUST_IMPEDANCE_S4H2.csv` = S4G1 19 行 + APG17：np 1.286 → 0.017667，x 67.84 → 4,938.81 Ω；(c) 缺参考候选的国家对 KH–LA、LA–MM、LA–TH（7 个节点对）、MY–SG（陆块不同 → 直流）、MY–TH，补 10 条交流 + 1 条直流（`CORRIDORS_S4H2.csv`），海底份额重算一致，管道数不变，`apg_plans` 分组无重叠；(d) x 最大 4,938.8 Ω（APG17）/ 最小 2.43 Ω，基尔霍夫系数跨度 2,034（S4G 2.3e5，S4H-1 943），环路 61 → 71，行内比 > 1e4 的行 0；复现 S4G 的构建与 S4G 逐组件相同，不互联与 S4G 相同；整个 `tests/` 531 通过 |
| S4H-3 | 冒烟 | 完成 | 见提交记录 | 代码 1887d975（工作树干净），档案 A，三项全部最优、`all_passed_solver_tolerances` 全部通过：一体化 6.39881e11（较 S4G −1.98 亿，−0.031 %），不互联 6.93191e11（与 S4G 完全相同），NZE 5.39724e11（−1.88 亿，−0.035 %）；各 225 s，峰值 3.9 / 3.5 / 3.9 GiB；B5、B6（533.1 亿 EUR，7.7 %）、B16 通过；LA 互联价值 3.26 → 2.50 bn EUR；汇总脚本 B16 读取位置修正后重跑；注册表片段 `s4h_3`（IPP 估算与账本对比） |
| S4H-4 | 云端部署包 | 完成 | 见提交记录 | 在最终代码提交 6eead675（工作树干净）上重建四个网络（2920×3h + 365×24h），一体化 / 不互联 / NZE 与 S4H-3 冒烟网络逐组件一致；包 `work/p1_step4h_20261017/cloud_package_dist/`，15 个文件，上传 232,939,289 B，清单写明 S4G 部署包（ed6af79c）作废；第二批敏感性 10 项（加 `la_vn_stock=author`、`candidate_num_parallel=template43`）只登记；资源估算 §17（单运行 37–52 min，悲观 76；峰值上限 32.9 GiB；预检下限 36 / 72 / 104 GiB 不变）；部署步骤更新；`tests/research` 514、整个 `tests/` 531 通过；许可扫描无新增命中 |
| S4H-5 | 上云前清单与交付 | 未开始 | — | |

## 提交记录（分支 `codex/s4h-lavn-candidates-20261017`）

| 提交 | 内容 |
|---|---|
| 533a6d8d | S4H-0：§7 答复登记 |
| 92986eae | S4H-1：LA–VN 存量为 0，4 条聚类线改为零容量候选线 |
| 1887d975 | S4H-2：候选线参考回路数 1、APG17 线型修正、补 11 条参考候选 |
| 6eead675 | S4H-3：冒烟三项最优，证据与注册表片段 `s4h_3`（S4H 最终代码提交，部署包据此构建） |
| （S4H-4 提交） | S4H-4：部署包重建、资源估算 §17、部署步骤 |

## 续行点

S4H-2 完成。下一步 S4H-3 冒烟：`/home/jin/s4h3_run.sh`（三个运行，档案 A，30 分钟止损，不重试），汇总 `scripts_project/s4h_3_summary.py --ref results_project/s4g/s4g3`。部署包脚本已复制到 `research/06_scope_redesign/p1_step4h_20261017/cloud_package/` 并改为 S4H 版（ALLOW = s4h_3_summary / s4h_4_*）。

## 发现但未处理（执行中随时记录，交付时写入报告）

1. 指令括注"PyPSA-Earth 的 augmented connection 用 DC 链路"与已入库源码不完全一致：`config.default.yaml` 第 177 行缺省 `new_line_type: ["HVAC"]`（脚本第 93 行兜底才是 `["HVDC"]`），HVAC 增补线不设 `num_parallel`（PyPSA 缺省 1），`s_nom_min` = 1 MW；该规则缺省不启用（第 174 行）。注册表按源码写明；与 one_circuit 约定一致，不影响实现。
2. MY–SG：按 S4E-1 陆块规则，新加坡与半岛不同陆块（柔佛海峡，海底份额 2.09%），补的参考候选为直流链路，MY–SG 因此没有交流参考电抗候选线；存量线 92 为交流。列入用户决定事项。
3. LA–TH 存量 9 条交流线，只有 7 个相邻节点对；线路 52、62 连接的节点对不相邻（聚类伪影），未补线。
4. 已有候选线的国家对中，存量线所在节点对没有同节点对的参考候选：ID_Kalimantan4 8–MY_Sarawak4 1（线 23）、KH2 4–TH2 3（线 47）、KH2 0–VN2 0（线 39）。按"每个国家对至少一条"未补。
5. LA–VN 线路 59（LA2 3–VN2 2）的节点对在 ADJACENCY_S4E1 中不相邻（聚类伪影），按第 100 项仍改为零容量候选线保留。

## 对 S4G 报告 §7 的答复（用户已确认，指令原文摘要）

1. LA–VN 存量：按 AIMS 电网间口径记为 0，4 条聚类线改为零容量候选线；独立电站专用出口线不单独建模、不下载核实，登记为 C 级局限并给出量级估算（第 100 项）。
2. 候选线与 APG17 的电抗：零容量交流候选线的参考回路数改为 1；APG17 按第 98 项同一线型关系修正；每个有存量交流线的相邻国家对至少有一条参考电抗的候选线，缺的补上（第 101 项）。
3. 数值风险：由第 100 项消除 LA–VN 极端电抗；S4H 冒烟中复核。
4. 上云：S4G 部署包作废，以 S4H 重建的部署包为准。

## 用户中途指示

（暂无）
