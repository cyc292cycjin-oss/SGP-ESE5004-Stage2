# S4M 报告：第二批主算设置、本机冒烟、部署包重建、本机资源核对与分摊输出完整性（2026-10-19）

指令 `work/p1_step4m_20261019/S4M_CLAUDE_CODE_INSTRUCTION.md`（v1，SHA256 `e791015e…c567c`，核对一致）与补充指令 `S4M_SUPPLEMENT_01.md`（SHA256 `8743abd0…7d1e`，核对一致）。分支 `codex/s4m-mainline-pilot-20261019`（自 PR #37 头 4b4eb92c 开出），提交 921e050b → b15ea69c → 8aa2fea0 → f50c8850 →（本次：报告与证据）。证据 `S4M_EVIDENCE.json`、`evidence/s4m_{1,2,3,s2}/`，进度 `S4M_PROGRESS.md`。本报告只记录做了什么与查到什么；未经验证的推断标注 INFERENCE，查不到的写 DATA_PENDING。

## 摘要

1. **S4M-0：** 第 114–116 项登记（注册表片段 `s4m_0`，5 行；921e050b）。
2. **S4M-1：** 主算设置 `research.numerics.dust_cleanup: on`（修正规则，S4L-6 起缺省）+ `research.s2.industry.biomass_overflow_cap_share: 0.98`（1.0 → 0.98）；四个网络（2920×3h + 365×24h）静态校验通过；S4I 审查与 S4K-2 逐项对照：413 行差异全部是清理与 0.98 上限的预期结果。**发现：** 0.98 上限带来的 2 % 余量解除了 BN、SG 小池的固定需求锁定，清理删除了它们（BN 3 个、SG 2 个 < 1 GWh 的池），清理后需求 / 剩余潜力为 BN 0.9877、SG 0.9949（VN 0.9800）——指令期望的 0.980 只在 VN 成立（§3.4，决定事项 §9 第 1 项）。
3. **S4M-2：** 本机 56×3h 冒烟 ×3（档案 A）全部最优、求解器容差口径门槛全部通过；与 S4K-3 参照相比 LP 行数 −7.2 % / −7.5 %，目标值 +1.8e-4 / +4.3e-4 / +2.1e-4（0.98 上限的预期效果，与 S4L-5 诊断逐项一致）；分国差额变化 PH +0.021 bn、燃料舱 −0.037 bn 超出事先固定的标准（实质变化，非数值问题），其余国家在容差内。
4. **补充 01（分摊输出完整性）：** 清单四项在 S4M-2 冒烟上为 1a / 2 / 4 已保存、1b / 1c / 1d 缺失、3 部分；只改导出后（`assign_all_duals`、逐约束对偶文件、成本拆分、`EXPORTS.json`），授权的一体化冒烟重跑最优、目标值与 S4M-2 **相对差 0.0**、门槛通过，清单四项全部"已保存"；新增导出 365×24h 每运行 3.2 GB（< 20 GB）。
5. **S4M-3：** S4L 版脚本 + S4M 参数（TimeLimit / 墙钟缺省 14,400 / 15,300 s 为运行参数）、`speed_probe.sh`、敏感性 16 项（+2）；四个网络在最终代码提交 f50c8850 重建，与 S4M-1 构建 SHA256 逐一相同；部署包 22 个文件、260,720,379 B，SHA256SUMS、预检分节、干跑、许可扫描全部通过；本机脚本测试 30/30、探针测试 9/9；S4K 包 56d28358 作废。
6. **S4M-4：** 本机 WSL `MemTotal` 10.7 GiB（物理内存共 15.7 GiB），不满足 ≥ 24 GiB 条件 → **本机试点未执行**；`.wslconfig` 未改、WSL 未重启。
7. **资源：** 本机求解 4 次（冒烟 3 + 重跑 1，56×3h，串行，各 < 6 min，峰值 4.1 GiB，无重试）；未上云、未下载、未做 365×24h 求解。
8. **待用户决定（§9）：** BN / SG 清理后比值的处理；云端探针与试点的授权（实例、TimeLimit）；对偶与成本拆分导出口径的确认；是否保留 `assign_all_duals=True`（每运行 +1.5 GB 网络文件）。
9. 完成后停止，等待审阅；云端连接与任何云端运行均未执行。

## 1. 执行概况

| 项 | 内容 |
|---|---|
| 时间 | 2026-10-19 12:25–13:30 SGT（构建 04:28 UTC 起、冒烟 04:34–04:48 UTC、重跑 05:0x UTC、打包 05:24–05:28 UTC） |
| 本机求解 | 4 次 56×3h（档案 A，30 分钟止损，串行；`results_project/s4m/s4m2/`、`s4ms2/`）：无非最优、无重试、无 warm start |
| 构建 | 4 个部署网络 ×2（S4M-1 在 921e050b；S4M-3 在 f50c8850 重建核对），每个约 1 min、0.71–0.74 GB |
| 云端 / 下载 | 无 |
| 许可 | 只经 `GRB_LICENSE_FILE` 只读引用；日志与证据按许可特征串过滤（`GUROBI_LOG_SCRUBBED.txt`、`solve_log_scrubbed.txt`）；部署包扫描无命中 |
| 档案 A | 未改（`formal_barrier`：Method 2、Crossover 0、BarConvTol 1e-8、BarHomogeneous 1、Threads 8、Seed 123） |
| 测试 | `tests/research/test_s4m_duals.py`、`test_s4m_cost_breakdown.py` 新增并通过；脚本测试 30/30、探针 9/9；全量 `tests/research`：1 failed, 535 passed, 927 warnings in 83.15s (0:01:23)（§11） |

## 2. S4M-0 登记（第 114–116 项；921e050b）

注册表片段 `s4m_0`（`scripts_project/s4m_0_data.py` → `DATA_REGISTRY.csv`）：第 114 项（清理采用，`dust_cleanup: on`）、第 115 项（`biomass_overflow_cap_share` 0.98 为主算）、第 116 项（第二批方案：档案 A、S4L 版脚本、TimeLimit / 墙钟 14,400 / 15,300 s 为运行参数、先探针后试点、S4K 包作废），以及问题来源与范围规则两行。

## 3. S4M-1 主算设置与四个网络（921e050b；`results_project/s4m/s4m1/`，证据 `evidence/s4m_1/`）

### 3.1 设置

`configs/research/baseline.yaml`：`research.s2.industry.biomass_overflow_cap_share` 1.0 → 0.98（第 115 项）；`research.numerics.dust_cleanup` 自 S4L-6（1655e623）为 `on`（修正规则：保护服务固定需求的生物质池）。其他键未动。

### 3.2 构建（VERIFIED，`evidence/s4m_1/STATUS.txt`、`builds/*/…_BUILD_RECEIPT.json`）

| 网络 | 状态 | 2920×3h SHA256（前 16 位） | 365×24h | 组件（Bus / Generator / Link / Load / Store / StorageUnit） | 清理 |
|---|---|---|---|---|---|
| 一体化 STEPS | 静态校验通过 | 513f56a65c7e7ad3 | 4206ec5c5d88c3ae | 2,786 / 1,717 / 7,494 / 2,026 / 523 / 133 | 删除 602 个组件、合并 86 条重复链路 |
| 不互联 STEPS | 通过 | 78fa40b7f27616c4 | b411223e85c7b0ee | 2,786 / 1,717 / 7,202 / 2,026 / 523 / 133 | 同上 |
| 一体化 NZE | 通过 | 6ee7b9ca60bee50f | 71503e0bfbe6a800 | 同一体化 | 同上 |
| 不互联诊断 | 通过 | 2e677a6d99781269 | c4a5d8ffb6ff9856 | 同不互联 | 同上 |

与 S4L-6 的清理后网络（上限 1.0）相比，组件只差 Store：528 → 523（见 3.4）；与 S4K-3 网络相比：Bus −128、Generator −278、Link −90、Load −38、Store −7、StorageUnit −147（S4L-1 清理的全部效果）。

### 3.3 S4I 复核与 S4K-2 对照（VERIFIED，`evidence/s4m_1/audit/`、`review/S4K2_REVIEW.json`、`S4K2_AUDIT_DIFF.csv`）

S4I 静态审查（static + followups）重跑退出 0；`s4k_2_review.py` 对 S4K-2 网络逐项比较得 **413 行差异**：A10 情景差异 57 行，每个网络 A1 时间 3 / A3 效率与可用率 6 / A4 拓扑 60 / A5 需求 10 / A9 碳 4 / 组件数 6（4 × 89 = 356）。逐类核对：组件数、单侧母线、重复链路、全零负荷、BN / SG / VN 生物质需求与气需求（6 个负荷）全部是清理与 0.98 上限的预期结果；交流线损代理不变（λ 全线、公式一致、求解 `transmission_losses` 0）；NZE 与一体化只差燃料价格；不互联网络跨境组件 0。**没有发现新错误**（指令停止条件 1 未触发）。

### 3.4 比值与余量核对（VERIFIED，`evidence/s4m_1/BIOMASS98_CHECK_S4M1.json`、`DUST_IMPACT_vs_s4l6.json`）——发现

0.98 上限只改 6 个负荷（BN 工业生物质 −2,318.7 MWh → 气、SG 农业 −630.2 MWh → 气、VN 工业 −2,515,451.3 MWh → 气），与 S4L-5 诊断相同。指令要求核对"三国比值 0.980、池余量 ≥ 0"：

| 国 | 潜力 MWh | 固定需求（98 %）MWh | 清理删除的池 | 清理后剩余潜力 MWh | 需求 / 剩余潜力 | 余量 MWh |
|---|---|---|---|---|---|---|
| BN | 115,935.8 | 113,617.1 | 3 个（906.9 MWh，< 1 GWh） | 115,028.9 | **0.9877** | 1,411.8 |
| SG | 31,510.2 | 30,880.0 | 2 个（473.4 MWh） | 31,036.8 | **0.9949** | 156.8 |
| VN | 125,745,566 | 104,201,887（工业）… | 0 | 不变 | **0.9800** | 2,515,451.3 |

原因：S4L 修正规则只保证"池总量 ≥ 固定需求"（余量 ≥ 0）才允许删除小池；上限 1.0 时 BN、SG 的池与需求相等、小池被锁定（S4L-6 只删 MY、TL 各 1 个）；上限 0.98 给出 2 % 余量，守护条件满足，BN 3 个、SG 2 个 < 1 GWh 的池被删除，余量相应减少。余量仍 > 0（条件满足），但比值不是指令写的 0.980。两种处理（§9 第 1 项）：接受现状（比值 0.988 / 0.995，余量 1,412 / 157 MWh）；或把清理守护改为"删除后余量 ≥ 上限余量"（即 BN / SG 不删池，比值回到 0.980）——后者要改清理规则并重建、重跑冒烟，本步未做。

## 4. S4M-2 本机冒烟 ×3（档案 A，56×3h，代表权重 8760/56；921e050b；`results_project/s4m/s4m2/`，证据 `evidence/s4m_2/`；VERIFIED）

### 4.1 结果

| 运行 | 终止 | barrier 迭代 / 秒 | work units | 求解 s | 墙钟 s | 峰值 RSS | LP 行 / 列 / 非零 | 目标值 EUR | 求解器容差口径门槛 | B16 相对误差 |
|---|---|---|---|---|---|---|---|---|---|---|
| 一体化 STEPS | optimal | 141 / 218.87 | 407.73 | 235.4 | 285 | 4.10 GiB | 1,393,079 / 629,144 / 3,209,723 | 648,381,181,410.45 | 全部通过 | 3.3e-11 |
| 不互联 STEPS | optimal | 151 / 182.83 | 362.44 | 197.5 | 240 | 3.69 GiB | 1,339,505 / 605,494 / 3,043,697 | 698,979,557,971.29 | 全部通过 | 3.5e-13 |
| 一体化 NZE | optimal | 174 / 261.59 | 512.98 | 277.5 | 330 | 4.10 GiB | 1,393,079 / 629,144 / 3,209,723 | 547,960,255,151.21 | 全部通过 | 1.4e-11 |

`all_passed_solver_tolerances` 三项均 True（含 B12 配置哈希：网络与求解在同一配置下）；BarConvTol 口径的 A1_A2 / A3 / B1 / B3 与 S4K-3 以来相同（已知状态，不是新发现）。Gurobi 警告 0，无 crossover。指令停止条件 2（非最优或门槛不通过）未触发。

### 4.2 与 S4K-3 参照的对比（标准同 S4L-2：目标 1e-5、B16 1e-6、分国 1 % 或 0.01 bn；`S4M2_SMOKE_SUMMARY.json`）

| 量 | S4K-3 参照（未清理、上限 1.0） | S4M-2 | 变化 |
|---|---|---|---|
| 一体化目标 EUR | 648,262,253,996.03 | 648,381,181,410.45 | +1.83e-4（+0.119 bn） |
| 不互联目标 EUR | 698,679,222,969.73 | 698,979,557,971.29 | +4.30e-4（+0.300 bn） |
| NZE 目标 EUR | 547,843,868,849.55 | 547,960,255,151.21 | +2.12e-4；NZE − 一体化 −100.42 bn（参照 −100.42） |
| B6（不互联 − 一体化）bn | 50.417（7.78 %） | 50.598（7.80 %） | +0.18 bn |
| LP 行（一体化 / 不互联） | 1,501,471 / 1,447,897 | 1,393,079 / 1,339,505 | −7.2 % / −7.5 % |
| barrier 迭代（一体化 / 不互联 / NZE） | 124 / 117 / 182 | 141 / 151 / 174 | +14 % / +29 % / −4 % |
| 秒 / work unit | 0.58–0.61 | 0.50–0.54 | 本机 |

分国差额（不互联 − 一体化，bn EUR）变化：VN +0.156（容差 0.248 内）、TH +0.044（内）、**PH +0.021（容差 0.018，超出）**、**燃料舱 −0.037（容差 0.019，超出）**，其余 |变化| ≤ 0.008。与 S4L-5 的 98 % 诊断（未清理网络）相比，S4M-2 的分国差额、节点电价与生物质影子价格逐项相同（差别只在清理：目标 +128,226 EUR），即超出标准的两项是 **0.98 上限的实质效果**（S4L 报告 §10 已记录），不是数值问题。节点电价相对参照：交流母线平均绝对差 0.043 EUR/MWh（最大 0.16）、H2 0.057（0.20）、气 0.074（0.14）；固体生物质影子价格（一体化，EUR/MWh）：BN 221.2 → 56.9、SG 308.8 → 80.9、VN 159.1 → 62.4（不互联 250.9 / 257.9 / 279.6 → 70.9 / 75.9 / 68.1），其他国家不变（ID 41.86 → 41.89）。

### 4.3 工作原则第 8 条检查

设置变化（清理 + 0.98 上限）对各国差额的影响集中在三个零余量国家的生物质影子价格回落（不再由甲烷边际价格决定），VN 差额 +0.156 bn（占 VN 差额 24.96 bn 的 0.6 %）、PH +0.021、燃料舱 −0.037；没有系统性把成本推给或减轻某国的迹象。该规则本身（第 36 项 / R1.6）对三国的处理在 S4L 报告 §10 已说明。

## 5. 补充 01：分摊输出完整性（S4M-S1 / S4M-S2；只改导出；提交 b15ea69c、8aa2fea0、f50c8850；`results_project/s4m/s4ms2/`，证据 `evidence/s4m_s2/`）

### 5.1 清单核对（`scripts_project/s4m_s1_check.py` → `S4M_S1_CHECKLIST_{before,after}.json`）

| 项 | 之前（S4M-2 一体化冒烟） | 之后（重跑） | 保存位置 |
|---|---|---|---|
| 1a 母线平衡对偶 | 已保存 | 已保存 | 网络 `buses_t.marginal_price`（PyPSA 约定：对偶 ÷ 时段目标权重） |
| 1b 全局约束对偶 | 缺失 | 已保存 | 本模型没有 `GlobalConstraint`：各国 CO₂ / 净零上限是钩子约束 `research_country_co2_limit-<c>`，对偶在 `DUALS_BY_CONSTRAINT.nc` |
| 1c 容量上下限对偶 | 缺失 | 已保存 | 静态 `p_nom` / `s_nom` / `e_nom` 上下限（含 `lines.max_extension` 经 `s_nom_max`）在 `DUALS_BY_CONSTRAINT.nc`；运行上下限 `mu_upper` / `mu_lower` 等在网络 `*_t`（`assign_all_duals=True`） |
| 1d 研究约束对偶 | 缺失（只有原始 `solution/Pi.npy`） | 已保存 | `DUALS_BY_CONSTRAINT.nc`（715 个研究钩子约束，按名） |
| 2 逐时段流量（含国别归属） | 已保存 | 已保存 | 网络 `*_t`（lines p0/p1、links p0/p1…、storage_units p / state_of_charge；国别在 `country` / `border_class` 列） |
| 3 成本拆分（投资、FOM、寿命、折现率、年金；相对误差 ≤ 1e-6） | 部分（8,130 / 9,392 可扩展组件 = 86.6 %） | **已保存（9,392 / 9,392）** | `COMPONENT_COST_BREAKDOWN.csv` + `_SUMMARY.json` + `costs_active_research.csv` |
| 4 完整网络重载 + B16 重算 | 已保存 | 已保存 | `integrated_SMOKE_TEST_ONLY_solved.nc`（重载 ok，B16 重算通过、目标一致） |

### 5.2 修改了哪些文件（只改导出；约束、目标函数、网络未动——四个网络在最终提交重建后 SHA256 与 S4M-1 相同，§6.1）

| 文件 | 改动 |
|---|---|
| `scripts_project/s2_solve.py` | `n.optimize.assign_duals(assign_all_duals=True)`；求解后调用 `s4m_duals.write_duals(m, out)`；`--costs-table`（构建时的 `costs_active_research.csv`）→ 复制 + `s4m_cost_breakdown.breakdown(n, costs, repo)`；`EXPORTS.json`（字节、SHA256）写入回执 `exports` |
| `scripts_project/s4m_duals.py`（新） | `write_duals`：每个 linopy 约束一个变量、维度名加约束前缀（`m.dual` 在本模型上抛 `MergeError: conflicting values for variable Generator`）；`duals_from_solution`：从 `solution/Pi.npy` + `lp/clabels.npy` 离线重建（要求 PYTHONHASHSEED=0，交叉核对不精确或 LP 行数不等即拒绝写文件） |
| `scripts_project/s4m_cost_breakdown.py`（新） | 逐可扩展组件：成本行、投资、FOM、寿命、折现率、年金系数、`fixed_reconstructed`、与 `capital_cost` 的比值与匹配规则；复合成本按各层公式从成本行与组件属性复原（§5.5） |
| `scripts_project/s4m_s1_check.py`（新） | 清单四项的核对与证据 |
| `tests/research/test_s4m_duals.py`、`test_s4m_cost_breakdown.py`（新） | 玩具模型：维度冲突的对偶导出；全部复合类别、无仓库路径与被篡改距离表的情形 |
| `cloud_package/run_365x24h.sh`、`make_package.sh` | `--costs-table networks/<tag>_costs_active_research.csv`；导出清单加 6 个新文件；每情景成本表入包 |

### 5.3 重跑冒烟的对比（`results_project/s4m/s4ms2/solves/s4m_A_integrated_rerun`；授权一次，30 分钟止损，不重试）

| 量 | S4M-2 一体化 | 重跑（含新增导出） |
|---|---|---|
| 终止 / 门槛 | optimal / 全部通过 | optimal / 全部通过（A4、A5、A6、B1_BUNKERS、B2、B8、B11、B12、B13、B14、B15、B16_LEDGER、*_S4B 均 True） |
| 目标值 EUR | 648,381,181,410.4515 | 648,381,181,410.4515（**相对差 0.0** ≤ 1e-9） |
| barrier 迭代 / 秒 / work units | 141 / 218.87 / 407.73 | 141 / 213.65 / 407.73 |
| 求解 s / 墙钟 s | 235.4 / 285 | 304.2 / 350（导出 +65 s） |
| 峰值 RSS | 4.10 GiB | 4.10 GiB |

指令停止条件"目标值与 S4M-2 不一致或非最优"未触发。重跑时的运行内对偶导出走了修前的 `m.dual` 路径而失败（回执 `export_error`），`DUALS_BY_CONSTRAINT.nc` 由 `s4m_duals.py` 从该次重跑的 `solution/Pi.npy` 离线重建（无求解；同一结果）；修后的运行内路径（`write_duals`）由单元测试覆盖，并将在云端运行中生效。

### 5.4 对偶文件与交叉核对（VERIFIED）

`DUALS_BY_CONSTRAINT.nc`（15.26 MB）：756 个约束（189 个按时段索引），1,401,085 个值（8,006 个 NaN 为掩码行，按构造）；LP 行 1,393,079 = 重建模型行数。交叉核对：`Bus-nodal_balance`（2,516 条母线）与 `Bus-meshed-nodal_balance`（270 条强网状母线）的对偶 ÷ `snapshot_weightings.objective`（156.4286）与网络 `buses_t.marginal_price` 的最大相对差 **0.0**。口径：文件存 **原始 LP 行对偶**（每加权时段的 EUR），PyPSA 的 `marginal_price` = 对偶 ÷ 时段权重；静态约束不加权。

**发现（已处理）：** 离线重建第一次时 199 / 270 条强网状母线的对偶被置换（同一时段数值集合相同）。原因：PyPSA `get_strongly_meshed_buses` 用 `pandas.value_counts` 排序，同计数母线的先后随 Python 字符串哈希种子变化，约束标签随之置换；求解脚本一直导出 `PYTHONHASHSEED=0`，重建改用种子 0 后精确。`s4m_duals.py` 现在无种子 0 即拒绝运行，交叉核对不精确或行数不等就不写文件。既有结果不受影响（求解端与运行内导出不依赖重建）。

### 5.5 成本拆分（VERIFIED，`COMPONENT_COST_BREAKDOWN_SUMMARY.json`）

9,392 个可扩展组件全部复原（|比值 − 1| ≤ 1e-6；`residual_eur` 最大 0）：plain 2,141、× 效率 1,658、× 长度 564、÷ 效率 11、参数定价 53（第 89 / 95 项 CO₂ 封存价、S3 终端）、零成本无行 3,703；复合 1,262：海上风电接入（offwind + 站 + 1.25 ×（距离 × 海底电缆 + 登陆 × 地下电缆），距离表 `research_inputs/renewable_v5/OFFWIND_CONNECTION_DISTANCE_S4C1.csv` 经网络 meta 的 SHA256 校验）399、长度 × 海底份额混合（交流线、H2 / CO₂ / 气管道）355、直流线（+ 换流站对）13、零成本反向孪生 13、碳捕集变体（基础行 × 效率 + 捕集行 × efficiency3）291、工业生物质捕集 94、电制生物燃料（BtL × 效率 + C stored × FT × 效率）97。成本表 `fixed` 列与年金公式 r/(1−(1+r)^−n) + FOM 的复算全部一致（`table_fixed_inconsistent` 0）。每个复合项的各项贡献写在 `composite_terms`，可从成本行重做拆分。既有资产的 FOM 常数（`existing_annual_fixed_om_eur`）另列：Generator 78 个 0.58 bn、Link 166 个 8.60 bn、StorageUnit 86 个 1.62 bn。

### 5.6 磁盘估算（`CLOUD_RESOURCE_ESTIMATE.md` §22.5；`evidence/s4m_s2/EXPORT_DISK_ESTIMATE.json`）

每运行新增：56×3h 实测 27.5 MB → 2920×3h 1.07 GB → **365×24h 3.21 GB**（对偶文件 1.73 GB + 网络中 `mu_*` 序列 1.48 GB + 静态文件 2.8 MB；线性外推，INFERENCE）。低于补充指令的 20 GB 停止线；四个运行约 12.9 GB。

## 6. S4M-3 部署包重建（第 116 项；`research/06_scope_redesign/p1_step4m_20261019/cloud_package/`，包 `work/p1_step4m_20261019/cloud_package_dist/`，证据 `evidence/s4m_3/`）

### 6.1 网络一致性（指令停止条件 3）

四个网络在最终代码提交 f50c8850 的干净树上重建（`PACKAGE_STATUS.txt`）：2920×3h 与 365×24h 共 8 个文件与 S4M-1 构建（921e050b，冒烟所用）SHA256 **逐一相同**（`NET_IDENTICAL` ×8）。`make_package.sh` 的构建提交核对（构建后无构建输入改动）通过；探针网络（一体化 2920×3h 前 56 时段）组件数与冒烟网络相同。**部署包网络 = 冒烟网络**。

### 6.2 脚本与参数（第 116 项；S4L 版 `run_365x24h.sh` / `preflight.sh` 的 S4M 修改）

- `run_365x24h.sh`：`GUROBI_TIME_LIMIT_S`（缺省 14,400）、`WALL_CAP_S`（15,300）、`GRACE_S`、`MONITOR_S` 为环境变量参数，缺省值与覆盖值写入 `STATUS`；`--costs-table`；导出清单加对偶、成本拆分等 6 个文件；S4L 的进程组终止、cgroup 配额、回执前后核对保留。
- `speed_probe.sh`（新，§22.3）：探针网络 + `PROBE_REFERENCE.json`（本机参照 0.537 s / work unit）→ `SPEED_PROBE.json`（速度比、建议 TimeLimit = 14,400 × max(1, 0.25 / r)、墙钟 + 900 s）。
- `make_package.sh`：每情景 `costs_active_research.csv`、探针网络与参照、`PACKAGE_MANIFEST.json`（主算设置、试点说明"先一次一体化，再整批"、运行参数说明、16 项敏感性：+ 清理关（第 114 项对照）、+ 上限 1.0（第 115 项对照）、作废说明）、`DATA_CONFIG_MANIFEST.json`（521 个配置 / 输入文件）、`SHA256SUMS`、`COMMIT`。
- `CLOUD_DEPLOY_STEPS.md`（提交 f50c8850、上传 260,720,379 B、22 个文件、探针参照、授权模板）与 `CLOUD_RESOURCE_ESTIMATE.md` §22。

### 6.3 本机检查（VERIFIED）

| 检查 | 结果 |
|---|---|
| `sha256sum -c SHA256SUMS` | 全部 OK |
| `preflight.sh serial formal_barrier`（分节 sha / networks / profile / versions / tools；许可与资源分节在实例上做） | OK：代码解包到 commit f50c8850；4 个网络在；档案 A 参数一致；python 3.11.13、pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4；GNU time、setsid 在 |
| `run_365x24h.sh --solver-profile formal_barrier --mode serial --dry-run` | OK：串行三项 + 条件诊断，`wall_cap_s:15300 time_limit_s:14400`，无求解无导出 |
| 许可特征串扫描 | 无命中 |
| 脚本测试 `evidence/s4m_3/test_s4m3_scripts.sh`（假求解器、假 cgroup，S4M 缺省值；+2 项：新增导出复制、`--costs-table` 指向包内成本表） | **30/30** |
| 探针测试 `test_s4m3_probe.sh` | **9/9** |

### 6.4 作废

S4K 部署包（56d28358，L23 首批）作废；S4J / S4H / S4G / S4F 此前已作废；S4L 只构建未打包。上云只用 f50c8850 的 S4M 包。

## 7. S4M-4 本机资源核对与条件性试点（只读核对，VERIFIED）

WSL `MemTotal` 10.7 GiB、`MemAvailable` 9.9 GiB、swap 4 GiB、16 线程；`.wslconfig` `memory=11GB`；Windows 物理内存 15.7 GiB；磁盘 `/` 900 GB、`D:` 340 GB。条件（`MemTotal` ≥ 24 GiB 且 `MemAvailable` ≥ 20 GiB 且磁盘 ≥ 20 GB）**不满足**（物理内存总共 15.7 GiB，改 `.wslconfig` 也达不到）→ 本机试点不执行（指令停止条件 4 的"正常写报告"路径）。`.wslconfig` 未改、WSL 未重启。试点改在云端：先探针，再一次一体化 365×24h（档案 A，TimeLimit 按探针），都需另行授权。

## 8. 发现但未处理（只记录）

1. **BN / SG 清理后比值 0.9877 / 0.9949（§3.4）：** 两种处理都可行，需用户决定；本步未改规则。
2. **分国差额变化超标（§4.2）：** PH +0.021 bn、燃料舱 −0.037 bn 超出 S4L-2 标准，是 0.98 上限的实质效果（与 S4L-5 诊断相同），记录供解读结果时参考。
3. **linopy `m.dual` 在本模型上失败：** 固定 / 可扩展子集共用维度名 `Generator` 而坐标不同，`m.dual` 合并时抛 `MergeError`；PyPSA 自己的 `assign_duals` 逐约束读取，不受影响；本步的导出改为逐约束（§5.2）。
4. **离线对偶重建依赖 PYTHONHASHSEED=0（§5.4）：** 已加拒绝与交叉核对；运行脚本一直设种子 0。
5. **`assign_all_duals=True` 的代价：** 网络文件每 365×24h 运行 +1.5 GB（`mu_*` 21,130 列），重跑墙钟 +65 s；同样的信息在 `DUALS_BY_CONSTRAINT.nc` 里（§9 第 4 项）。
6. **BarConvTol 口径的 A1_A2 / A3 / B1 / B3 仍不通过**（S4K-3 以来的已知状态，求解器容差口径通过；S4K 报告已记录）。
7. **本机包检查脚本的路径错误（内部）：** 第一次打包时预检与干跑输出写到了临时目录（相对路径跟随 `cd`），第二次打包改为绝对路径后补齐；不影响包内容。

## 9. 需要用户决定的事项

1. **BN / SG 清理后比值：** (a) 接受现状（0.9877 / 0.9949，余量 1,412 / 157 MWh，第二批照此运行）；或 (b) 改清理守护为"删除后余量 ≥ 上限余量"（BN / SG 不删小池，比值 0.980），需改 `s4l_layers.py`、重建四个网络、重跑冒烟 ×3 并重新打包（约 1 小时本机）。
2. **云端探针与试点：** 授权实例（按 §21.3 选机：CPU 代际与主频、≥ 24 GiB、数据盘 ≥ 150 GB）、上传与预检、速度探针（一个 WLS 令牌，30 分钟止损）、再一次一体化 365×24h 试点（档案 A，TimeLimit / 墙钟按探针建议；缺省 14,400 / 15,300 s）；授权模板见 `CLOUD_DEPLOY_STEPS.md`。整批运行在试点最优后另行授权。
3. **分摊输出口径确认：** 对偶文件存原始 LP 行对偶（每加权时段），`marginal_price` 按 PyPSA 约定除以权重；成本拆分按各层公式复原（含复合项的逐项贡献）。若分摊分析需要别的口径（例如全部除以权重），只改导出即可。
4. **是否保留 `assign_all_duals=True`：** 保留（网络自含 `mu_*`，+1.5 GB / 运行）或改回缺省（只靠对偶文件，网络文件 3.7 GB）。
5. **PR：** 本分支 draft PR 叠在 #37（S4L）上；合并顺序 #37 → 本 PR，由用户决定。

## 10. 上云前清单（待第 2 项授权后执行；全部未做）

1. 上传 `cloud_package_dist/`（260,720,379 B，22 个文件）到实例数据盘；`sha256sum -c SHA256SUMS` 全部 OK；`COMMIT` = f50c8850。
2. `PY=… bash preflight.sh serial formal_barrier`（全部分节：含许可只读引用检查与 cgroup 配额、磁盘 ≥ 35 GiB）→ `PREFLIGHT OK`。
3. `GRB_LICENSE_FILE` 指向实例上的许可文件（只读引用；不复制、不打印）；同时不超过 2 个 Gurobi 会话；探针结束后等 ≥ 5 分钟再启动试点。
4. 速度探针 `bash speed_probe.sh formal_barrier` → `SPEED_PROBE.json`；按建议设 `GUROBI_TIME_LIMIT_S` / `WALL_CAP_S`（r ≥ 0.25 时用缺省）。
5. 试点 `bash run_365x24h.sh --solver-profile formal_barrier --mode serial --runs integrated`；监督 `STATUS` / `MONITOR_*.csv`（cgroup 值）；非最优不重试、不改参数。
6. 回收 `results_<run>.tar.gz` + `.sha256`（本机核对 SHA256、许可特征串扫描）；`EXPORTS.json` 中新增导出的字节与 SHA 与清单一致。
7. 试点结果报告后，整批（不互联、NZE，条件诊断）另行授权。

## 11. 证据与文件

- 报告 / 进度 / 证据：`research/06_scope_redesign/p1_step4m_20261019/{S4M_REPORT.md, S4M_PROGRESS.md, S4M_EVIDENCE.json, CLOUD_RESOURCE_ESTIMATE.md (§22), CLOUD_DEPLOY_STEPS.md, cloud_package/, evidence/s4m_1/, evidence/s4m_2/, evidence/s4m_3/, evidence/s4m_s2/}`；镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4m_20261019\`（含 `cloud_package_dist/`，不进 git）。
- 结果（不进 git）：`results_project/s4m/{s4m1, s4m2, s4ms2, s4m3}/`。
- 代码：`scripts_project/{s4m_0_data.py, s4m_2_summary.py, s4m_duals.py, s4m_cost_breakdown.py, s4m_s1_check.py, s4m_5_collect_evidence.py, s2_solve.py}`；测试 `tests/research/test_s4m_duals.py`、`test_s4m_cost_breakdown.py`；全量 `tests/research` 结果写在 `S4M_EVIDENCE.json` → `tests`。
- 注册表：片段 `s4m_0`；台账 `research/STAGE2_PROJECT_LEDGER.md` S4M 条目。
