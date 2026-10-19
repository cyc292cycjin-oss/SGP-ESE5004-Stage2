# S4O 报告：生产档案、运行流水线、部署包与 365×24h 整批（2026-10-19 至 10-20）

## 摘要（S4O-6 后，最新）

1. **整批（档案 A，8481C 实例，串行，无人值守）：** 不互联 STEPS、不互联诊断、一体化 NZE 三个运行**均 SUBOPTIMAL**（TimeLimit 未用尽；不互联两次在第 124–126 次迭代无提示重启后停滞）；不重试、未改参数。三者 C1 (a)(b)(c) **全部通过**（总成本精度 ≤ 0.004 bn），按第 119 项可作"第一层 + 电价结算"；按第 120 项的运行验收为 False（非最优）。
2. **B6 = 本批不互联 − 试点一体化 = 69.243 bn EUR**（L23 68.970）；**NZE − 一体化 = −90.491 bn EUR**（L23 −90.462）；分国差额除 VN（+0.275 bn）外与 L23 相差 ≤ 0.005 bn；试点与本批网络、档案一致。
3. **回收：** 轻量包、整批完整包（461.0 MB）与两个单运行完整包已下载并核对 SHA256、无许可串；试点完整包不在本克隆实例上（只在原 D58 数据盘）。**许可已删除（03:43:29），可以在 AutoDL 控制台关机。**
4. **自动决定 13 条（§11.8）**；需要用户决定的事项见 §11.10。详细见 §11；补充 01 见 §10；S4O-3 停止报告见 §1–§9。

## 摘要（补充 01 后）

1. **第 121 项执行：** 生产档案回到档案 A（`formal_barrier`），`pypsa_eur_default` 保留为已登记的非生产档案；键名识别、内点路径函数、C1 流水线、`RUN_GAP_S` 全部保留；注册表片段 `s4o_1`；`tests/research` 544 通过，部署脚本测试 59/59、探针 9/9（87e28e3b）。
2. **S4O-3′ 端到端验证通过：** 用 S4O 版 `run_365x24h.sh`（56×3h，缺省档案 A，自动 C1）跑一次一体化：optimal，目标与 S4M-2 **相对差 0.0**，C1 自动执行并写入 `EXPORTS.json`，分级 layer1 + 电价结算，与 S4O-2 等价核对一致（126110ff）。
3. **S4O-4 部署包：** 在 126110ff 上重建，`networks/` 13 个文件与 f50c8850 包 **逐一相同**；缺省档案 A、缺省运行"不互联 + NZE"、TimeLimit / 墙钟 21,600 / 22,500 s、试点一体化作 C1 参照；`PACKAGE_DELTA.json`：只需上传 124.3 MB（10 个变化或新增文件 + 清单）；预检、干跑、许可扫描、脚本测试全部通过。
4. **S4O-5：** 2920×3h 外推：72.1 M 行；峰值 106–165 GiB（线性至超线性 1.15）；8470Q 上单运行约 15–35 h；建议 2 卡（240 GiB）、数据盘 ≥ 100 GB；单价待查（DATA_PENDING）。S4M §22.5 的 365×24h 导出高估已更正（应按时段比 6.52 而非小时比 156.4）。
5. **停下等待云端授权（S4O-6）。** 原 S4O-3 停止报告保留在下方 §1–§9；补充 01 的详细结果见 §10。

## 摘要（S4O-3 停止时，原文保留）

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

> 注：上表为 S4O-3 停止时的状态；补充 01 之后 `evidence/s4o_4/` 的结果为 59/59、9/9（含用例 I–M），`make_package.sh`、`package_checks.py` 已在 S4O-4 运行，见 §10。

## 10. 补充 01（第 121 项）：回到档案 A、端到端验证、部署包与资源估算

### 10.1 指令与授权

- `S4O_SUPPLEMENT_01.md` v1，SHA256 `f723c544…a7a4`，与 `S4O_SUPPLEMENT_01_SHA256.txt` 及用户消息一致（VERIFIED）。
- 用户消息（原文见 `S4O_PROGRESS.md`）：第 121 项已确认，生产档案回到档案 A；本补充中 1 次本机 56×3h 运行已授权；云端（S4O-6）仍未授权，本机部分完成后停下报告。
- 第 121 项另定：不补做 S4O-3 未运行的两次；不放宽第 107 项与第 119 项 (a) 的标准。
- 求解：本机 56×3h **1 次**（S4O-3′，21:35:29–21:41 SGT），无重试；云端无动作。本机上一次 Gurobi 结束于 20:57:18（间隔 > 5 分钟）。

### 10.2 S4O-2′ 配置与测试（87e28e3b；VERIFIED）

| 项 | 内容 |
|---|---|
| 配置 | `research.solver.profile: formal_barrier`；注释写明第 121 项及理由：1e-5 容差的落点约为 3e-5，约合 0.015–0.02 bn，与 0.01 bn 判定单位同量级，余量不足；结果受线程路径影响。`pypsa_eur_default` 注明为非生产档案（参数不变） |
| 注册表 | 片段 `s4o_1`（`scripts_project/s4o_1_data.py`）：`s4o_decision_121_production_profile_A`、`s4o_decision_121_standards_kept`、`s4o_decision_121_batch_plan`、`s4o_question_source_s4o`；注册表 1,962 行 |
| 保留 | 键名识别 `profile_parameters()`、内点路径 `interior_solution()`、C1 流水线 `s4o_c1_precision.py`、`RUN_GAP_S` |
| 部署脚本 | `run_365x24h.sh`：缺省档案 A；缺省运行 `disconnected,integrated_nze`（一体化可用 `--runs` 选）；TimeLimit / 墙钟缺省 21,600 / 22,500 s；`PILOT_INTEGRATED` / `PILOT_PRECISION`：本批无一体化时，不互联完成后以"本批不互联 − 试点一体化"作 C1 分国参照（`BATCH_REFERENCE.json`），在**副本**上重评试点 C1（保留 `grade_history`，试点原文件不改），并写 `PILOT_CONSISTENCY.json`（试点输入网络 SHA256 是否等于本包 `integrated_365_24h_unsolved.nc`、档案与参数是否一致）；`TRUNCATE` 钩子（仅本机端到端验证用）。`speed_probe.sh` 建议值基数改为 21,600 s。`preflight.sh` 提示改为档案 A |
| C1 模块 | `regrade` 兼容 S4N 试点的 `PILOT_PRECISION.json`（无 `acceptance` / `reference` 字段） |
| 测试 | `test_s4o_2.py` 8 项（新增：用真实试点 `PILOT_PRECISION.json` 在副本上重评）；`test_s4c_5.py`、`test_s3_gates.py` 的缺省档案断言改回 `formal_barrier`；`tests/research` **544 passed**；部署脚本测试 **59/59**（新增用例 K：无一体化、试点参照、试点一致性、副本重评；L：试点网络不同时报告 `network_same=False`；M：`TRUNCATE` 干跑），探针测试 **9/9**（期望值 21,600 / 22,500 与 27,000 / 27,900 s） |

### 10.3 S4O-3′ 本机端到端验证（VERIFIED；`evidence/s4o_3b/`）

运行方式：本机类包目录（代码 = 87e28e3b 的 `git archive`；`networks/integrated_365_24h_unsolved.nc` 为 S4M-1 一体化 2920×3h 构建（SHA256 `513f56a6…`）的符号链接；构建成本表），**S4O 版 `run_365x24h.sh`**，`TRUNCATE=56`，不传档案（取缺省），`--runs integrated`，TimeLimit 1,750 s / 墙钟 1,800 s（30 分钟止损），一次。预检（profile、c1、versions、tools）OK。

| 验收项（补充 01） | 结果 |
|---|---|
| optimal | **是**（141 次迭代 / 217.03 s / 407.73 WU；求解 310.6 s；墙钟 362 s；峰值 4.11 GiB；回执档案 `formal_barrier`，`interior_solution` True） |
| 目标与 S4M-2（648,381,181,410.4515 EUR）相对差 ≤ 1e-9 | **0.0**（目标 648,381,181,410.4515） |
| C1 在运行中自动执行并写入 `EXPORTS.json` | **是**：`PRECISION_integrated:layer1_plus_nodal_price_settlement:accepted=True:abc=111:ref=L23`（33 s、1.7 GiB）；`PRECISION.json/.md`、`VIOLATIONS.json` 在求解目录与导出目录的 `EXPORTS.json` 中，SHA256 与文件一致 |
| (a)(b)(c) 分级与 S4O-2 等价核对一致 | **是**：同为 layer1 + 电价结算；(a) 差值 −1.2e-8 bn 相同，(b)(c) 分国数值最大差 0.0 |

- 项目门槛（数值信息）：S4B 口径（A1_A2_S4B、A3_S4B、A5_S4B、B1_S4B、B3_S4B）全通过；`all_passed_solver_tolerances` False **只因 B12**（`research_config_sha256` 与构建时不同：构建后配置新增了 `pypsa_eur_default` 档案，B12 对整个 research 配置取哈希，按构造不通过；S4N-1 用 f50c8850 包代码时配置未变，B12 通过）；BarConvTol 口径 A1_A2 / A3 / B1 / B3 不通过，与 S4M-2 的已知状态相同。
- 结果包 `results_20261019T133528Z_584.tar.gz` 生成，导出 66 MB；许可扫描无命中。

### 10.4 S4O-4 部署包（126110ff；VERIFIED；`evidence/s4o_4p/`，包在 `work/p1_step4o_20261019/cloud_package_dist/`，不进 git）

| 项 | 结果 |
|---|---|
| 提交 / 代码 | `COMMIT` 126110ff（`code_126110ff.tar.gz`，123.9 MB） |
| 网络来源 | `results_project/s4m/s4m3/builds`（f50c8850 重建）；构建输入变更分类（`BUILD_INPUT_CHANGES_<情景>.json`）：按路径 4 个（`s4m_5_collect_evidence.py`、`s4o_0_data.py`、`s4o_1_data.py`、`s4o_c1_precision.py`）、求解驱动 `s2_solve.py`（构建模块不导入）、`baseline.yaml` 只在 `research.solver` 下不同、注册表只增行；拒绝 0 |
| **网络与 f50c8850 包** | `networks/` 下 13 个文件（四个 365×24h 网络、探针网络、构建回执、成本表）**SHA256 逐一相同**（`NETWORKS_VS_REFERENCE.json`） |
| 缺省值 | 档案 `formal_barrier`；运行 `disconnected,integrated_nze`；TimeLimit / 墙钟 21,600 / 22,500 s；`serial`；C1 后处理在包内 |
| `PACKAGE_DELTA.json` | 变化 5（`COMMIT`、`DATA_CONFIG_MANIFEST.json`、`preflight.sh`、`run_365x24h.sh`、`speed_probe.sh`）；新增 5（4 个 `BUILD_INPUT_CHANGES_*.json`、`code_126110ff.tar.gz`）；去掉 1（`code_f50c8850.tar.gz`，实例上不删，不在新 `SHA256SUMS` 内）；未变 16 个 140.1 MB；**上传 124.3 MB**（按 0.16 MB/s 约 13 分钟） |
| 检查 | `SHA256SUMS` 26/26 OK；预检（sha、networks、profile、c1、versions、tools）OK（代码解包到 `./repo` 并写 `.package_commit`）；干跑列出 2 个求解（不互联、NZE）与各自 C1；许可串扫描 30 个文件无命中；包内脚本重跑脚本测试 59/59、探针 9/9 |
| 就地更新 | 实例上已有 f50c8850 包时：单路上传 `PACKAGE_DELTA.json` 的 `upload` 列表 → 完整 `sha256sum -c SHA256SUMS` → 核对 `COMMIT`；`preflight.sh` 按 `COMMIT` 解包 `code_126110ff.tar.gz`，旧 `./repo` 改名为 `repo_prev_unknown_<时间>` 保留（用例 I 已测） |

### 10.5 S4O-5 资源估算（只读；`CLOUD_RESOURCE_ESTIMATE.md` §23）

- 实测点：56×3h 1.39 M 行 / 4.1 GiB；365×24h 9.02 M 行 / 15.1 GiB，档案 A 408 次迭代、barrier 11,470 s（含一次重启）；结果包 158.9 MB。
- 2920×3h（INFERENCE）：72.1 M 行 / 32.3 M 列 / 168 M 非零；峰值内存 106 GiB（线性仿射）/ 121 GiB（等比）/ 165 GiB（超线性 1.15），规划 ≥ 160 GiB；8470Q 上每次迭代 225–419 s，单运行中间情形 15–35 h（150–600 次迭代时 9–70 h），TimeLimit 建议 ≥ 48 h；每运行磁盘约 15 GB、结果包约 1.3 GB。
- 选机：AutoDL 按卡分配，8470Q / 8481C 机单卡 25 核 / 120 GiB → 2920×3h 用 **2 卡**、数据盘 ≥ 100 GB；365×24h 整批 1 卡（约 2.5–6.5 h）。费用 = 卡数 × 卡时单价 × 时长，单价 DATA_PENDING。
- 更正 S4M §22.5：365×24h 列应按时段比 6.52 放大（原按小时比 156.4，高估约 20–40 倍）。

### 10.6 S4O-6 的准备状态（未授权，未执行）

- 按补充 01：只跑不互联 STEPS、一体化 NZE（诊断仅在不互联非最优时）；B6 = 本批不互联 − 试点一体化；报告中核对两者网络 SHA256 与档案参数（`PILOT_CONSISTENCY.json` 自动生成）。
- 启动时需要：`PILOT_INTEGRATED` 指向试点一体化结果目录（D58 或其克隆上为 `/root/autodl-tmp/s4m_cloud/runs/20261019T072454Z_5125/integrated/`；否则用本机试点轻量包的 `export_integrated/` 上传），`PILOT_PRECISION` 指向试点 `PILOT_PRECISION.json`（D58 上 S4N 后处理目录 `/root/autodl-tmp/s4n_tools/`，或轻量包内）。
- 其余按原 S4O-6：只读核对；按 `PACKAGE_DELTA.json` 单路上传；许可按授权原文处理；预检；探针仅在 CPU 与 8470Q 不同时运行；回收轻量包与完整包（D58 或克隆时含试点完整包 `cb4927da…`）；删除许可。

### 10.7 发现但未处理（补充 01 新增）

| # | 现象 | 影响 | 建议时点 |
|---|---|---|---|
| 8 | 整批每个运行的 B12 都会按构造不通过：网络在 f50c8850 构建，之后 research 配置新增了 `pypsa_eur_default`（B12 哈希整个 research 配置，含 `solver.profiles`）；若为让 B12 通过而重建网络，网络 SHA256 会变，与 S4O-4 的"与 f50c8850 逐一相同"冲突 | 门槛标签（数值信息，第 120 项） | 报告整批时注明 |
| 9 | 代码包 `code_126110ff.tar.gz` 123.9 MB，是上传量的主体（`git archive` 含 `research/` 下全部交付物与证据）；只打包运行所需目录可减到数 MB | 上传时间（0.16 MB/s 时约 13 分钟） | 下次打包时由用户决定 |
| 10 | 第 95 项 f 的联盟运行回退规则（档案 A 非最优 → 档案 C 重跑一次）在第 121 项后又与生产档案一致；原发现第 5 条随之消解 | 无 | — |

### 10.8 需要用户决定的事项

1. **S4O-6 云端整批的授权：** 实例（D58 或其克隆，或其他西北 B 区 8470Q / 8481C 机）、许可处理授权原文、以及是否按 §10.6 的方式提供试点一体化目录。
2. 代码包是否瘦身（发现第 9 条），不影响本次包的使用。

### 10.9 补充 01 的证据与文件

| 位置 | 内容 |
|---|---|
| `S4O_SUPPLEMENT_01.md`、`S4O_SUPPLEMENT_01_SHA256.txt` | 补充指令 |
| `evidence/s4o_3b/` | S4O-3′：`STATUS.txt`、`MONITOR_integrated.csv`、导出的回执 / 门槛 / 日志 / 账本 / `PRECISION` / `VIOLATIONS` / `EXPORTS.json`、`S4O3B_CHECK.json`（验收） |
| `evidence/s4o_4/` | 部署脚本测试与结果（59/59、9/9） |
| `evidence/s4o_4p/` | 部署包：`COMMIT`、`SHA256SUMS`、`PACKAGE_MANIFEST.json`、`PACKAGE_DELTA.json`、`NETWORKS_VS_REFERENCE.json`、`DATA_CONFIG_MANIFEST.json`、`PROBE_REFERENCE.json`、`BUILD_INPUT_CHANGES_integrated.json`、打包日志、预检与干跑输出 |
| `CLOUD_RESOURCE_ESTIMATE.md` §23 | S4O-5 |
| `work/p1_step4o_20261019/cloud_package_dist/` | 部署包（264.4 MB，不进 git） |
| 本机结果（不进 git） | `/home/jin/s4o_local/pkg_e2e/runs/20261019T133528Z_584/` |

## 11. S4O-6 云端整批（补充 01 调整；补充 02 无人值守）

### 11.1 摘要

1. **实例：** D58 在西北 B 区 F73 机上的克隆（AutoDL 实际分配的区域代号见登录指令，主机与端口未写入任何文件）；**Xeon Platinum 8481C**，容器 25 核 / **92 GiB**；数据盘为空（克隆只带系统盘）→ 整包上传，试点参照文件从本机轻量包上传，试点完整包无法从本实例下载（D1–D3）。
2. **探针：** r = **0.836**，目标与本机参照相对差 −2.5e-12 → TimeLimit / 墙钟 21,600 / 22,500 s 不变。
3. **整批（档案 A，串行）：** 不互联 STEPS、不互联诊断（因不互联非最优，按原计划）、一体化 NZE **三个运行均 SUBOPTIMAL**（Gurobi 在 TimeLimit 之前停于停滞状态）；不重试、未改参数。三个运行的 C1 (a)(b)(c) **全部通过**（本批参照），分级为"第一层 + 节点电价结算可用"；按第 120 项的运行验收（optimal + (a)(b)(c)）为 False。
4. **主要数值：** **B6 = 本批不互联 − 试点一体化 = 69.243 bn EUR**（相对 13.4 %；L23 筛查未验证 68.970 bn）；**NZE − 一体化 = −90.491 bn EUR**（L23 −90.462 bn）；试点与本批网络 SHA256、档案参数一致。
5. **回收与许可：** 轻量包、整批完整包（461.0 MB）与两个单运行完整包均已下载、SHA256 核对 OK、无许可串；许可 03:43:29 删除并核实。**可以在 AutoDL 控制台关机。**

### 11.2 授权与执行概况

- 用户授权原文（主机与端口删去）与两次确认见 `S4O_PROGRESS.md` "S4O-6 云端整批"；补充 02 原文与 SHA256 核对见同文件"补充 02"。
- 求解次数（全部一次、无重试、无 warm start、未改参数）：云端探针 1 次（56×3h，档案 A）、整批 3 次（365×24h，档案 A）。本机在云端期间未启动 Gurobi（00:10:03 核对）。
- 时间线（SGT，2026-10-20）：上传 22:09–00:09（前一天开始）→ 许可 00:10:26 → 预检 00:10:43 OK → 探针 00:16:57–00:24:28 → 整批 00:29:51 启动 → 不互联 00:29:52–01:13 → 诊断 01:18:33–01:57 → NZE 02:02:34–03:36 → DONE 03:40:20 → 回收 03:41–03:44 → 许可删除 03:43:29。实例从容器启动（21:57:27）到许可删除约 5 h 46 min；费用 DATA_PENDING。

### 11.3 实例、上传、预检与探针（VERIFIED；`evidence/s4o_6/`）

| 项 | 结果 |
|---|---|
| CPU / 配额 | Xeon Platinum 8481C（Sapphire Rapids，2 路 × 56 核 / 224 线程，最高 2.0 GHz，L3 210 MiB，AVX-512）；cgroup v2：25 核、98,784,247,808 B（92.0 GiB） |
| 环境 | python 3.11.13、pypsa 0.30.3、linopy 0.5.5、numpy 1.26.4、gurobipy 12.0.3（与本机一致）；tmux / rsync / setsid / GNU time 在 |
| 上传 | 整包 264,363,290 B，单路 rsync 7,192 s（约 36 KB/s；下载方向约 4 MB/s）；试点 3 个文件 14 s；实例上 `sha256sum -c` **26 OK**，`COMMIT` 126110ff，无残留临时文件 |
| 许可 | scp 直传，mode 600、目录 700、仅此一个文件，两端哈希一致（未打印） |
| 预检 | `PREFLIGHT OK`：缺省档案 A（内点门槛路径）、C1 可导入、版本、工具、许可被接受（输出屏蔽）、资源 25 核 / 92 GiB / 49 GiB |
| 速度探针 | optimal，目标 648,381,181,408.8285（本机参照相对差 −2.5e-12；与 S4N 8470Q 探针目标相同），141 次迭代 / 240.99 s / 375.14 WU → 0.642 s/WU；**r = 0.836**（每次迭代 0.908）；墙钟 451 s |

### 11.4 整批运行（VERIFIED；运行目录 `runs/20261019T162951Z_6896`；`cloud_results/…/S4O6_BATCH_SUMMARY.json/.md`）

| 运行 | 终止 | LP 行 / 列 / 非零 | barrier 迭代 / 秒 / WU | 每次迭代 | 重启 | 最后迭代（原始 / 对偶目标，原始残差） | 墙钟 | 峰值 RSS | 目标 EUR |
|---|---|---|---|---|---|---|---|---|---|
| 不互联 STEPS | **SUBOPTIMAL** | 8,671,148 / 3,896,653 / 19,874,213 | 287 / 2,201.6 / 2,177.96 | 7.7 s | 第 126 次（1,003 s）：残差 3.68 → 1.76e11；第一轮最小 0.306（第 111 次） | 5.82438789e11 / 5.82444754e11，9.0 | 2,588 s | 12.9 GiB | 585,495,017,158.94 |
| 不互联诊断 | **SUBOPTIMAL** | 8,821,003 / 3,971,694 / 20,173,729 | 245 / 1,919.6 / 1,866.56 | 7.8 s | 第 124 次（1,013 s）：3.61 → 1.77e11；第一轮最小 2.08（第 103 次） | 5.82439452e11 / 5.82438541e11，24.0 | 2,308 s | 13.2 GiB | 585,497,545,941.42 |
| 一体化 NZE | **SUBOPTIMAL** | 9,017,345 / 4,048,847 / 20,952,716 | 216 / 5,238.3 / 3,638.01 | 24.3 s | 无；第 150 次后停滞于原始残差 4–7 | 4.22874418e11 / 4.22874284e11，4.4 | 5,652 s | 15.2 GiB | 425,761,150,197.18 |

- 三个运行都在 TimeLimit（21,600 s）之前由 Gurobi 自行以 sub-optimal 结束；不互联两次运行都在第 124–126 次迭代出现无提示重启（L23 不互联为第 125 次），重启后第二轮停滞。
- 容器内存峰值约 21 GiB / 92 GiB；数据盘空闲始终 ≥ 45 GB；无内存或磁盘问题。

### 11.5 精度证据与验收（C1，第 119 / 120 项；本批参照 = 本批不互联 − 试点一体化）

| 运行 | (a) 原始 / 对偶差 | (b) 超预算行 / 一阶影响合计 / 最差国占阈值 | (c) B16 / 最差国 S+R 占阈值 | 分级 | 验收（optimal + abc） | 门槛（数值信息） |
|---|---|---|---|---|---|---|
| 不互联 | 0.00076 bn，1.3e-6 | 821 / 29,802 EUR / ID 0.06 % | 6.5e-7 / ID 12 % | 第一层 + 电价结算 | False（非最优） | 不通过：A1_A2_S4B、A3_S4B、B3_S4B、B14、B15、B12 等 |
| 诊断 | −0.0039 bn，6.7e-6 | 5 / 5,171 EUR / ID 0.02 % | 2.8e-7 / ID 22 % | 第一层 + 电价结算 | False | 同上（无 B1） |
| NZE | −0.00014 bn，3.2e-7 | 3,499 / 66,699 EUR / ID 0.15 % | 1.9e-9 / ID 0.7 % | 第一层 + 电价结算 | False | 另有 B2 不通过 |
| 试点一体化（副本重评） | 同 S4N | 同 S4N | 同 S4N | 第一层 + 电价结算 | **True** | — |

- BN / SG / VN 生物质池行在三个运行中都不占主导。
- 试点一致性（`PILOT_CONSISTENCY.json`）：试点输入网络 SHA256 `4206ec5c…` 与本包 `integrated_365_24h_unsolved.nc` 相同；档案 `formal_barrier`、参数（除 TimeLimit）相同；试点 optimal。
- S4O-6 第 5 点（全规模标定：定稿档案一体化对试点）在第 121 项后不适用：生产档案即试点所用的档案 A，一体化未重跑。

### 11.6 结果（INFERENCE 标注处除外为 VERIFIED）

- **B6（不互联 − 一体化）= 69.243 bn EUR**，相对一体化 13.4 %；L23 为 68.970 bn（+0.273 bn）；S4M-2 56×3h 为 50.60 bn。不互联为 SUBOPTIMAL，但 C1 (a) 的总成本精度 0.00076 bn，远小于 B6。
- **分国差额（bn EUR，本批 / L23）：** VN 51.595 / 51.320、TH 7.513 / 7.510、MY 3.206 / 3.210、LA 2.738 / 2.740、KH 2.426 / 2.426、MM 1.131 / 1.133、SG 0.932 / 0.932、ID 0.669 / 0.669、TL 0.123 / 0.124、BN 0.114 / 0.114、PH 0.010 / 0.010、燃料舱 −1.216 / −1.219、共享池 −0.0004 / −0.0002。与 L23 相比除 VN（+0.275）外各国变化都在 0.005 bn 以内（INFERENCE：清理与 0.98 上限只影响小池与近零对象，对分国结论影响很小）。
- **NZE − 一体化 = −90.491 bn EUR**（相对 −17.5 %；L23 −90.462）；分国（bn）：ID −28.42、MY −17.02、VN −12.94、TH −11.96、燃料舱 −11.24、SG −5.99、PH −4.04、BN −0.29、TL −0.23，KH +0.74、LA +0.62、MM +0.28。
- 与试点对比：试点一体化 516,252,148,340.37 EUR（optimal）；本批 NZE 425,761,150,197.18。

### 11.7 回收

| 文件 | 字节 | SHA256 | 核对 |
|---|---|---|---|
| 整批完整结果包 `results_20261019T162951Z_6896.tar.gz`（105 个成员） | 461,001,705 | `c37f8d938176850d3cbd316907030e07eadb6a71eef0491d6f3f82e9fd47ccef` | 实例与本机 `sha256sum -c` OK；许可串 0 命中 |
| 轻量包 `s4o_batch_light_20261019T162951Z_6896.tar.gz` | 5,782,612 | `f8cffc10d4ac503727c62625384820f56d331678397ce16f1b09743de264caca` | OK；无许可串 |
| 不互联完整包 `full_disconnected_…tar.gz` | 150,455,004 | `cf4c3909…32ec` | OK；与整批包内文件逐一相同 |
| 诊断完整包 `full_disconnected_gap_…tar.gz` | 151,427,801 | `523d4a6d…013b` | OK；同上 |
| 试点完整包 `results_20261019T072454Z_5125.tar.gz` | 158,873,778 | `cb4927da…7480` | **未下载**：只在原 D58 的数据盘（本克隆未带数据盘），释放期约到 11-03 |

本机位置：`work/p1_step4o_20261019/cloud_results/20261019T162951Z_6896/`（不进 git）；轻量证据入库 `evidence/s4o_6/`。实例上除许可外未删除任何文件。

### 11.8 自动决定汇总（补充 02）

| # | 情况 | 依据 | 处理 |
|---|---|---|---|
| D1 | 数据盘空，无旧包 | 授权第 3 点；第 12 条 | 整包单路上传，完整校验 |
| D2 | 试点目录不在实例 | 授权第 3 点 | 从本机轻量包上传 3 个文件，两端 SHA256 一致 |
| D3 | 试点完整包不在本实例 | 第 12 条（不换实例） | 不下载，报告注明 |
| D4 | CPU 8481C ≠ 8470Q | 补充 01；第 4 条 | 先跑探针 |
| D5 | 探针启动被本机脚本自检误拒（命令行自匹配），未启动任何求解 | 第 12 条 | 检查与启动分两次 SSH，重新启动 |
| D6 | r = 0.836 | 第 4 条 | TimeLimit / 墙钟 21,600 / 22,500 s |
| D7 | 监督脚本误报内存不足（查询在本机执行） | 第 12 条 | 远程查询改为文件经 `ssh bash -s` |
| D8 | 不互联第 126 次迭代重启 | 第 8 条 | 只记录 |
| D9 | 不互联 SUBOPTIMAL | 第 6 条 | 不重试；按原计划诊断运行 |
| D10 | 诊断 SUBOPTIMAL（第 124 次重启） | 第 6、8 条 | 不重试；继续 NZE |
| D11 | 以试点一体化作 C1 参照并重评 | 补充 01 | 流水线自动完成；网络与档案一致 |
| D12 | 回收时间不确定 | 第 10、12 条 | NZE 期间先打包下载已完成的两个运行 |
| D13 | NZE SUBOPTIMAL | 第 6 条 | 不重试；收尾 |

### 11.9 发现但未处理（S4O-6 新增）

| # | 现象 | 影响 | 建议时点 |
|---|---|---|---|
| 11 | 本批三个运行都是 SUBOPTIMAL（档案 A，TimeLimit 远未用尽）：不互联两次在第 124–126 次迭代无提示重启后停滞；NZE 无重启但停滞于原始残差 4–7。C1 (a)(b)(c) 全过，按第 119 项分级可作"第一层 + 电价结算"；按第 120 项的运行验收为 False | 结果用途 | 用户决定（§11.10 第 1 项） |
| 12 | 门槛 B14（码头上限）、B15（国内产量上限）、NZE 的 B2（储存上限）不通过：这几项没有容差（S4N 发现第 6 条同类） | 门槛标签 | 与第 119 项口径一起决定 |
| 13 | 上传方向约 36 KB/s、下载方向约 4 MB/s（同一实例）；整包上传用了 2 小时 | 上云时间 | 下次可先测速；代码包瘦身（§10.7 第 9 条）可省约 2 / 3 上传时间 |
| 14 | 克隆实例不带数据盘；试点完整包仍只在原 D58 数据盘 | 试点完整包需另行下载 | 约 11-03 前 |
| 15 | 预检输出的过滤词 `PROJ` 不区分大小写，会把含 `scripts_project` 的行（c1 节的 "present"）一并过滤；只影响显示 | 无 | 下次改过滤词 |

### 11.10 需要用户决定的事项

1. **本批三个 SUBOPTIMAL 运行的用途：** C1 全过（总成本精度 ≤ 0.004 bn，B6 的 0.006 %）。是否按第 119 项采纳为筛查级结果（B6、分国差额、NZE − 一体化，以及按电价结算），还是另作安排（任何改档案或参数的重跑都属新的决定，需另行授权）。
2. **试点完整结果包：** 是否在 D58 数据盘释放前（约 11-03）用无卡模式开机下载。
3. **下一步：** 2920×3h 正式运行（资源见 `CLOUD_RESOURCE_ESTIMATE.md` §23）与敏感性批次的安排。
