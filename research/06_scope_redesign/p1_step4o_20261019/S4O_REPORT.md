# S4O 报告：生产档案定稿与本机标定复核——S4O-3 触发停止条件（2026-10-19）

## 摘要

1. **S4O-1 完成：** 标定分支推送、draft PR [#39](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/39)（叠在 #38 上）；S4N 交付物入库（f28772e6，扫描无许可串、无登录信息）；注册表补登第 118、119、120 项、台账 S4N 条目（46135c52）；S4O 分支 `codex/s4o-production-20261019` 自 46135c52 开出。
2. **S4O-2 完成：** `pypsa_eur_default` 定稿（键名大写、`Threads 8`，其余原样）并设为缺省档案，档案 A 不改；`s2_solve.py` 拒绝只差大小写的键名；C1 并入运行流水线（`s4o_c1_precision.py`，与 S4N 工具在 S4N-1 上分国数值差 0.0）；测试 543 通过；部署运行脚本并入 C1，脚本测试 50/50、探针 9/9（d5b4eb96、18f55488）。
3. **S4O-3 停止：** 第 1 次运行（一体化 STEPS，定稿档案）Gurobi **optimal**，但目标与 S4M-2（档案 A）相对差 **2.13e-5 > 1e-5**（第 107 项标准不通过）；其 C1 (a) 也不通过（原始 / 对偶差 0.018 bn、相对 2.79e-5）。按 S4O-3 第 4 点停下：在 5 分钟间隔内结束运行脚本，**不互联与 NZE 两次求解未启动**；不重试、未改参数。
4. **对照（只读，信息）：** S4N C2（同一 BarConvTol 1e-5，`threads 32`、小写键）三次运行目标差 3.4–6.2e-6，补算 C1 全部通过；同一容差下，线程数改变迭代路径，返回解落在 1e-5 标准的两侧（INFERENCE）。
5. **未执行：** S4O-4（部署包重建；脚本已写、未运行）、S4O-5（资源估算）、S4O-6（云端，未授权）。需要用户决定生产档案的处理（§7）。

## 1. 指令、授权与执行概况

- 指令 `S4O_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `b5f4d099…af6aa`，与 `S4O_INSTRUCTION_SHA256.txt` 及启动消息一致（VERIFIED）。背景已读：`S4N_REPORT.md` 全文、`S4N_PROGRESS.md`、补充 01 / 02。
- 授权（启动消息原文见 `S4O_PROGRESS.md`）：S4O-1 至 S4O-5 本机部分，含 S4O-3 的 3 次本机 56×3h 运行；S4O-6 未授权。
- 求解：本机 56×3h **1 次**（S4O-3 一体化，20:53:37–20:57:18 SGT），无重试、无 warm start、未改参数；云端无任何动作。其余 Gurobi 调用：无（C1、违反分析、比较均只用 Python，`GRB_LICENSE_FILE` 已取消）。
- 分支与提交：`codex/s4n-calibration-20261019`：7c4f97fe → f28772e6 → 46135c52（已推送，PR #39）；`codex/s4o-production-20261019`：7279ea87 → d5b4eb96 → 18f55488 → 报告提交（见 §8）。未合并 main，未 force-push。

## 2. S4O-1 整理与入库（VERIFIED）

| 项 | 结果 |
|---|---|
| 标定分支 | `codex/s4n-calibration-20261019`（7c4f97fe）推送；draft PR [#39](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/39)，base = #38 的分支 `codex/s4m-mainline-pilot-20261019` |
| S4N 入库 | `research/06_scope_redesign/p1_step4n_20261019/`：报告、进度、证据 JSON、指令与补充 01 / 02（含 SHA 文件）、`ENV_LOCK_LOCAL.txt`、`evidence/`、`scripts/`、试点轻量包（tar.gz 全量 + 解包成员 ≤ 500 kB；4 个较大成员只在 tar.gz 内；`sha256sum -c` OK）；170 个文件、5.4 MB；提交 f28772e6 |
| 入库前扫描 | 许可特征串：只命中 `s4n1_evidence.sh` 中的扫描模式本身；IPv4 形：只命中包版本号；AutoDL / SeetaCloud 主机名：只命中 `s4n_netdiag.sh` 的公开网站 `www.autodl.com`；ssh / scp / rsync 端口、user@host、密码：无（`evidence/scripts/s4o_scan.sh`；真实主机与端口从未写入文件，本扫描按模式查找） |
| 注册表 | 片段 `s4o_0`（`scripts_project/s4o_0_data.py`）：`s4n_decision_118_s4m_open_items`、`s4n_decision_119_precision_over_label`、`s4o_decision_120_production_profile`、`s4o_question_source_s4n`；注册表 1,958 行；`test_d1_registry.py` 13 passed |
| 台账 | `STAGE2_PROJECT_LEDGER.md` 新增"S4N 第 118–119 项"条目（46135c52，已推送） |
| S4O 分支 | 自 46135c52 开 `codex/s4o-production-20261019`；S4O 指令与 SHA 文件放入 `research/06_scope_redesign/p1_step4o_20261019/`（7279ea87） |

## 3. S4O-2 生产档案定稿（第 120 项 (2)；VERIFIED）

1. **档案：** `configs/research/baseline.yaml` → `pypsa_eur_default: {Threads: 8, Method: 2, Crossover: 0, BarConvTol: 1.e-5, Seed: 123, AggFill: 0, PreDual: 0, GURO_PAR_BARDENSETHRESH: 200}`。两处适配及理由写在配置注释与注册表：键名大写（Gurobi 不区分大小写，求解不变；只修正门槛路径识别）；`Threads 8`（硬件设置，与档案 A 相同）。其余键与库内 PyPSA-Eur v2025.07.0 第 1056–1064 行原文相同（单元测试逐键核对）。缺省 `research.solver.profile` 改为 `pypsa_eur_default`；档案 A 不改。
2. **键名识别：** `s2_solve.py` 新增 `profile_parameters()`——键名与已知 Gurobi 参数只差大小写即报错，防止 S4N 发现第 10 条复现；`interior_solution()` 取代原第 317 行的内联判断（行为不变）。S4O-3 运行回执 `INTERIOR_CHECKS.interior_solution` = **True**（S4N C2 为 False）。
3. **C1 并入流水线：** `scripts_project/s4o_c1_precision.py`（`run` / `reference` / `regrade`）：求解后自动执行（先 `l23_violation_analysis.py`），只用 Python、取消许可变量；`PRECISION.json/.md`、`VIOLATIONS.json` 写入求解目录与导出目录并登记到 `EXPORTS.json`；运行验收 = optimal + (a)(b)(c)；项目门槛照算并作数值信息报告。(b)(c) 的分国容差：两种 STEPS 都有结果前用 L23 365×24h 差额（注明来源），之后用本批"不互联 − 一体化"差额并对已完成运行重评（保留 `grade_history`）。
   - 等价核对（只读，影子目录）：在 S4N-1 56×3h 结果上与 S4N 工具比较，(a) 差值、超预算行数、驻点 / 互补合计、每国一阶影响与 S+R **完全相同**（最大差 0.0），分级相同；用时 22 s、1.7 GiB；S4N-1 原结果未改（`EXPORTS.json` SHA256 不变）。
4. **单元测试：** `tests/research/test_s4o_2.py` 7 项（档案定稿与原文逐键、键名识别与拒绝、内点路径、C1 玩具 LP（scipy HiGHS）的 KKT 项与扰动、分级 / 验收 / 参照、重评与 `EXPORTS.json`、无解时"不可计算"）；`tests/research` **543 passed**（原 536 + 7；`test_s4c_5.py`、`test_s3_gates.py` 中"缺省档案为 formal_barrier"的断言按第 120 项改为 `pypsa_eur_default`）。
5. **部署运行脚本（S4O 版，`research/06_scope_redesign/p1_step4o_20261019/cloud_package/`）：** `run_365x24h.sh`——缺省档案 `pypsa_eur_default`（S4M 版为必填、无缺省）、每次求解后 C1、本批参照与重评、serial 相邻求解间隔 `RUN_GAP_S` 330 s（项目规则 ≥ 5 分钟；S4M 版 serial 无间隔）、一体化非最优且 C1 不通过则停止；`preflight.sh`——档案节检查缺省档案与键名、新增 c1 节。本机脚本测试 50/50（含假求解器与真 C1 模块的停止 / 重评用例）、探针测试 9/9（`evidence/s4o_4/`）。

## 4. S4O-3 本机标定复核：一体化运行与停止（VERIFIED；`evidence/s4o_3/`）

运行：本机 i7-13620H / WSL，S4M-1 网络（2920×3h 构建，SHA256 `513f56a6…`）`--truncate 56`，代码 18f55488，**不传 `--solver-profile`**（取配置缺省，回执确认 `pypsa_eur_default`，参数 Threads 8 / Method 2 / Crossover 0 / BarConvTol 1e-5 / Seed 123 / AggFill 0 / PreDual 0 / BARDENSETHRESH 200），30 分钟止损（TimeLimit 1,750 s），一次。开始前：本机无求解进程；本机上一次 Gurobi 结束于 S4N C2（19:18:09 SGT）；云端实例已关机。

| 运行 | 档案 / 线程 | 终止 | barrier 迭代 / 秒 / WU | 求解 s | 峰值 RSS | 目标 EUR | 与档案 A 相对差 | B16 | 返回解原始 / 对偶相对差 | C1 分级 |
|---|---|---|---|---|---|---|---|---|---|---|
| S4M-2 档案 A（参照） | A / 8 | optimal | 141 / 218.87 / 407.73 | 235.4 | 4.10 GiB | 648,381,181,410.45 | — | 3.3e-11 | 1.9e-11 | — |
| **S4O-3 一体化** | `pypsa_eur_default` / 8 | **optimal** | **58 / 78.44 / 120.84** | 172.9 | 4.09 GiB | **648,395,012,280.16** | **+2.13e-5（+0.0138 bn）** | 2.4e-8 | **2.79e-5** | **not_layer1**（(a) 不通过，(b)(c) 通过） |
| S4N C2 一体化（信息） | 原样 / 32 | optimal | 65 / 93.41 / 97.47 | 186.0 | 6.21 GiB | 648,385,210,748.37 | +6.2e-6 | 2.5e-9 | 7.8e-6 | layer1 + 电价结算（补算，§5） |

- **第 107 项标准（事先固定）：** 目标相对差 ≤ 1e-5 → **不通过**（2.13e-5）；B16 ≤ 1e-6 → 通过（2.4e-8）；分国"不互联 − 一体化"差额变化 → 需要不互联运行，**未评**（停止）。
- **C1（第 119 项，L23 参照）：** (a) 返回数组 KKT 摘要原始 648,395,012,279.93、对偶 648,376,941,199.45，差 −0.0181 bn、相对 2.79e-5 → **不通过**（标准 ≤ 0.01 bn 且 ≤ 1e-5）；日志返回迭代（第 58 次）差 −2.04e7 EUR、相对 3.15e-5。(b) 超预算行 0、一阶影响合计 679 EUR → 通过。(c) B16 2.4e-8；每国 S+R 最大 ID 0.0070 bn（阈值 0.0100，70 %）→ 通过。验收（optimal + (a)(b)(c)）= **False**。
- **项目门槛（数值信息）：** `all_passed_solver_tolerances` False（A1_A2_S4B、旧口径 A1_A2、B12；B12 按构造不通过）。
- **分国账本（只作信息）：** 各实体总额相对档案 A 的变化最大 ID +0.0061 bn、VN +0.0036、燃料舱 +0.0035；S4N C2 最大燃料舱 +0.0043、ID +0.0031。
- **停止：** 20:57:18 SGT 一体化结束、20:58 C1 完成；不互联求解按脚本应在 21:02:18 SGT（间隔 5 分钟）启动。按 S4O-3 第 4 点（"任何一次非最优或标准不通过：停下报告，不进入 S4O-4"），20:58:51 SGT 结束运行脚本（`pkill`，脚本正处于间隔等待中），核实无求解 / C1 进程，`STATUS.txt` 记 `STOPPED_BY_OPERATOR` 与 `LAST_GUROBI_END 12:57:18Z`。**不互联、NZE 两次已授权的运行未执行**（是否补做由用户决定，§7）。

## 5. 原因分析（INFERENCE，供决定用）

1. **BarConvTol 1e-5 的实际落点在 1e-5 标准附近：** Gurobi 判收敛时，返回解的相对原始 / 对偶差可以超过 BarConvTol——本次日志 3.15e-5、返回数组 2.79e-5（容差 1e-5，约 3 倍）；S4N 试点档案 A 日志 3.7e-8（容差 1e-8）；但也可以远低于容差（S4N C2 5.5–7.8e-6；S4M-2 档案 A 56×3h 1.9e-11）。Gurobi 的判据在预求解、缩放后的模型上计算（项目门槛与 C1 在原始 LP 上计算），两者不完全一致（同 S4N 发现第 6 条）。因此以 1e-5 为容差的档案，其目标值与真实最优的距离可达约 3e-5，与"目标相对差 ≤ 1e-5"、C1 (a)"相对 ≤ 1e-5"同一量级。
2. **线程数改变迭代路径：** 同一档案（除线程与键名大小写外完全相同），`threads 32`（S4N C2，本机 16 逻辑核超订）65 次迭代停在相对间隙 7.8e-6；`Threads 8` 58 次停在 2.79e-5。C2 三次全部通过可视为落点较好，而非该容差的稳定性质。键名大小写不影响 Gurobi（不区分大小写）。
3. **对 365×24h 的含义：** 试点目标约 5.16e11 EUR，若相对间隙同为 ~3e-5，原始 / 对偶差约 0.015 bn，超过 C1 (a) 的绝对标准 0.01 bn；按第 120 项的运行验收，生产档案在整批中可能出现"optimal 但 (a) 不通过"。分国 (b)(c) 本次余量充足（(c) ID 70 % 除外）。
4. **补充对照（只读）：** 对 S4N C2 三次运行补算 C1（影子目录，S4N 结果未改）：(a) 相对差 7.8e-6 / 6.0e-6 / 5.5e-6、绝对 0.005 / 0.004 / 0.003 bn，三次 (a)(b)(c) 全过（L23 参照与本批参照均过）。`evidence/s4o_3/s4n_c2_c1/`。

## 6. 未执行的步骤

- **S4O-4 部署包更新：** 按停止条件未进入。S4O-3 运行期间已写好、**未运行、未测试**的准备：`cloud_package/make_package.sh`（S4O 版：第 4 参数为参照包；构建输入变更分类、打包后网络必须与 f50c8850 包逐一相同、`PACKAGE_DELTA.json`）、`cloud_package/package_checks.py`、`preflight.sh` 的就地更新处理（按 `COMMIT` 解包 `code_<COMMIT8>.tar.gz`，旧 `./repo` 改名保留不删）、脚本测试新增用例 I；只做了语法检查（`bash -n`、`py_compile`）。只读核对：f50c8850 包的网络来自 `results_project/s4m/s4m3/builds`（在 f50c8850 重建，构建提交 f50c8850），对 HEAD 18f55488 的变更分类全部可接受（`s4m_5_collect_evidence.py`、`s4o_*` 按路径；`s2_solve.py` 不被构建模块导入；`baseline.yaml` 只在 `research.solver` 下不同；注册表只增行）；用 S4M-1 构建（921e050b）则 `s4m_duals.py` 等 3 个文件被拒（S4M 的打包当时用的是 s4m3 重建）。
- **S4O-5 资源估算修订：** 未做（只读工作，但停止条件要求停下报告；生产档案若变化，2920×3h 的迭代数假设也要随之变化）。
- **S4O-6 云端：** 未授权，未做。

## 7. 需要用户决定的事项

1. **生产档案（第 120 项）如何处理**——以下为可选方向，科学决定由用户作出：
   - (a) 保留 `pypsa_eur_default`（BarConvTol 1e-5），同时调整第 107 项 / 第 119 项 (a) 的标准使之与该容差相符（例如目标相对差 ≤ 5e-5、(a) 只用相对标准）；
   - (b) 在登记理由后增加第三处适配：收紧 `BarConvTol`（例如 1e-6），重新做 3 次本机标定；
   - (c) 生产档案回到档案 A（`formal_barrier`，BarConvTol 1e-8）：S4N 试点已证明其在 365×24h 上 optimal（8470Q 上 3.3 h，含一次重启），C1 全过；代价是迭代数约为 2.2 倍；
   - (d) 其他（例如 `Threads` 取值另定）。
2. **S4O-3 已授权、因停止未做的 2 次本机运行**（不互联、NZE，定稿档案）：是否为提供信息而补做（不改变本次"不通过"的判定）。
3. **S4O-4 / S4O-5：** 生产档案定下后，是否按现有准备继续（S4O-4 的打包准备与网络一致性核对已写好；S4O-5 只读）。
4. **缺省档案的提交状态：** 当前分支上缺省档案已是 `pypsa_eur_default`（d5b4eb96）；若选 (c)，需要改回并说明。

## 8. 发现但未处理

| # | 现象 | 影响 | 建议时点 |
|---|---|---|---|
| 1 | Gurobi 判 optimal 时返回解的相对原始 / 对偶差可达 BarConvTol 的约 3 倍（本次 3.15e-5 vs 1e-5；试点 3.7e-8 vs 1e-8），也可远低于容差（S4N C2、S4M-2） | 以容差设定精度时需留余量 | 生产档案决定时 |
| 2 | 同一档案仅线程数不同（8 vs 32），目标值相对差 1.5e-5，C1 (a) 一过一不过 | 标定结论依赖线程路径 | 同上 |
| 3 | S4M 的 `make_package.sh` 允许列表不含 `s4m_duals.py` 等（S4M 当时在 f50c8850 重建网络到 `s4m3/builds` 后打包）；S4O 打包须用 `s4m3/builds` | 打包输入目录 | S4O-4 |
| 4 | S4M 版 `run_365x24h.sh` serial 模式相邻求解之间无间隔（许可上不超 2 个会话，但项目规则要求 ≥ 5 分钟）；S4O 版已加 `RUN_GAP_S` | 规则一致性 | 已在 S4O 版处理（未打包） |
| 5 | 第 95 项 f 的联盟运行回退规则写的是"档案 A 非最优 → 档案 C 重跑一次"；第 120 项把联盟运行的生产档案改为 `pypsa_eur_default` 后，回退规则如何适用未定 | 联盟运行规则 | 联盟运行前 |
| 6 | 第 120 项注册表行按 S4O-1 的顺序登记在 S4N 分支（46135c52）上 | 无 | — |
| 7 | (c) 中 ID 的 S+R 为阈值的 70 %（0.0070 / 0.0100 bn，56×3h，L23 参照） | 价格结算余量 | 整批时关注 |

## 9. 证据与文件

| 位置 | 内容 |
|---|---|
| `work/p1_step4o_20261019/S4O_PROGRESS.md`（仓库同名镜像） | 授权原文、步骤状态、提交、续行点 |
| `S4O_EVIDENCE.json` | 本报告的轻量证据（`evidence/scripts/s4o_collect_evidence.py` 生成） |
| `evidence/s4o_2/` | C1 等价核对（S4N 工具与新模块在 S4N-1 上的输出） |
| `evidence/s4o_3/` | `STATUS.txt`、一体化运行的回执 / 门槛 / 日志 / 账本 / `PRECISION` / `VIOLATIONS` / `kkt_summary`、`S4O3_INTEGRATED_INFO.json`（与档案 A、S4N C2 的对照）、`s4n_c2_c1/`（S4N C2 补算 C1） |
| `evidence/s4o_4/` | 部署脚本测试（假求解器、假 C1）与结果（50/50、9/9；用例 I 尚未运行） |
| `evidence/scripts/` | 本次全部辅助脚本（不含主机、端口、密码） |
| `cloud_package/` | S4O 版部署脚本（`run_365x24h.sh`、`preflight.sh` 已测；`make_package.sh`、`package_checks.py` 未运行） |
| 本机结果（不进 git） | `results_project/s4o/s4o3/` |
