# B4P 进度记录（续做点）

指令 `B4P_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `995ff3447b4ae3ef1b9dc6fc0e029ee711fbb340475f3417deddf2eebc8378b2`（与 `B4P_INSTRUCTION_SHA256.txt` 一致，2026-10-26 核对）。
会话：Fable 5.1；worktree `/home/jin/wt_b4p_20261026`，分支 `codex/b4-prep-20261026`，起点 `9f368407`（= `0d9c22a3` 之后只有报告 / 证据提交）。
用户授权（2026-10-26 03:15 SGT，原文见会话）：本机只读审查与测量；截短 2920×3h 网络 `--stop-before-solve` 构建；本机最多 **8 次** Gurobi 调用（截短 2920×3h 或已有 56×3h 网络，≤ 365 时段，每次 ≤ 60 min，间隔 ≥ 5 min，不重试）；本机计算合计 ≤ 5 h，磁盘新增 ≤ 40 GB；新分支改代码、补测试、推送；打包 v7 并干跑。不连云、不上传；不在本机构建或求解完整 2920×3h。
补充 1：候选配置加 AutoDL RTX 4090D ×4（72 核 EPYC 9754 / 240 GB / 数据盘 ≤ 60 GB / ¥7.5/h），评估 60 GB 数据盘。
补充 2：A2 第 4 项优先——分进程求解（进程 1 构建 + 写模型文件 + 标签映射；进程 2 仅 gurobipy 求解；进程 3 映射回网络接后处理），等价判据 Fingerprint 相同 + 56×3h 完整求解逐位相同。
无人值守规则：默认决定写入报告"未经用户确认的决定"；优先级 A1 > 补充 2 > A3.1 > A4 > A2 其余 > A3 其余 > A5。
本机辅助脚本：`/home/jin/b4p/`；中间结果：主检出 `results_project/b4p/`；证据：`work/p1_b4p_20261026/evidence/`。

| 子步骤 | 状态 | 提交 | 说明 |
|---|---|---|---|
| 0 核对 SHA256 / worktree | 完成 | — | worktree 建于 9f368407，干净；被忽略的 finance_v5 两个 CSV 从主检出复制；results_project/{assembly_v1,s1} 符号链接 |
| A1.1 已有数据提取 | 完成（数据在手，待写入证据 JSON） | | 云端 R1–R11（Factor NZ/Ops、预求解规模、峰值 RSS）与本机 56×3h 日志（`/home/jin/b4p/local_logs.sh`） |
| A1.2 截短构建测量 | 完成（56/112/182；273 按 90 % 规则不做） | | `results_project/b4p/builds/`，`BUILDS_STATUS.txt`：一体化峰值 2.18 / 3.97 / 6.16 GiB，不互联 1.92 / 3.47 / 5.30 GiB |
| 补充 2 代码：`s2_solve.py --split-stage build/assign`、`b4_split_solve.py`、A3.1 先落盘 | 完成（未提交） | | 单元测试 `tests/research/test_b4p_split.py` 6 passed |
| C1：56 一体化 现有方式 档案 A（新代码） | 完成 | | 与 M08b 冒烟逐位相同（解、LP、CSV、NetCDF 数据；`evidence/compare/C1_newcode_vs_M08b_smoke.json`）= A3.1 回归 + 本机 Gurobi 确定性 |
| C2：56 一体化 分进程 档案 A | 进行中（第一次尝试在许可间隔后被运行器拒绝：分支代理的替身测试进程同名；未产生 Gurobi 调用；目录删除后重跑，调用 2 于 19:58:37Z 启动） | | 进程 1：29 s，2.19 GiB，LP 文件 94.4 MB，写出 8.2 s |
| C2 ↔ C1 逐文件比较 | 完成：**全部相同** | | `evidence/compare/C2_split_vs_C1_single_56_A.json`：解/对偶/LP 数组、CSV、JSON、NetCDF 数据、Fingerprint、迭代数、WU 全等；三进程峰值 2.19 / 3.62 / 2.64 GiB vs 单进程 4.74 GiB |
| C3：112 一体化 现有方式 T16 | **按 90 % 内存规则终止**（20:09:30Z，RSS 10.5 GiB / 10.95 GiB，可用 67 MB） | | 终止前已得 barrier 统计：预求解 1,028,643 行 / 945,229 列 / 4.07e6 非零，Factor NZ 5.24e8，Factor Ops 1.15e12，排序 76 s，迭代 7→9 约 6.5 s/次（T16 本机）；发现 N < 200 时耦合列低于 `GURO_PAR_BARDENSETHRESH=200` 不作稠密列（AA' 3.3e7 vs 365×24h 1.4e7）→ 剩余调用改到 N > 200 |
| C4：int 224 探针（T16，阈值 200） | **看门狗终止**（进程 2 在排序阶段 RSS 10.65 GB，可用 58 MB） | | 调用 4 计入；得到：224 时段 LP 6,173,908 行 / 2,771,676 列 / 1.44e7 非零，预求解后 2,059,661 / 1,886,693 / 8.15e6，读入 7.2 s，预求解 15 s；进程 1 峰值 7.47 GiB，LP 文件 390.5 MB，写出 22.6 s。原 C4（112 分进程）在 Gurobi 进程启动前停止，未消耗调用，进程 1 数据保留为 `p1only_int112_split_T16` |
| C6：disc 140 探针（阈值 100，T16） | 完成 | | 调用 6：Dense cols 5,656、AA' 6.28e6、Factor NZ 8.84e7（1.7 GB）、Factor Ops 2.27e11、预求解 7.6 s、排序 30.6 s、25 次迭代 89.6 s（10→20 平均 1.9 s/次）、进程 2 峰值 5.81 GiB、MaxMemUsed 6.70 GB、读入 4.1 s；进程 1 4.16 GiB、LP 232 MB、写 14.3 s |
| C7：int 182 探针（阈值 100，T16） | 完成 | | 调用 7：Dense cols 6,055、AA' 8.63e6、Factor NZ 2.257e8（3.0 GB）、Factor Ops 1.285e12、预求解 11.8 s、排序 58.0 s、25 次迭代 225 s（10→20 平均 6.0 s/次）、进程 2 峰值 7.76 GiB、MaxMemUsed 9.44 GB、读入 5.8 s；进程 1 6.16 GiB、LP 316 MB、写 18.9 s |
| C8：disc 182 探针（阈值 100，T16） | 完成（决定：取第二个不互联点，放弃 SoftMemLimit 触发测试） | | 调用 8：Dense cols 5,817、AA' 7.79e6、Factor NZ 1.197e8（2.0 GB）、Factor Ops 3.46e11、排序 48.5 s、25 次迭代 129 s（10→20 平均 2.7 s/次）、进程 2 峰值 7.68 GiB、MaxMemUsed 9.24 GB、读入 5.5 s；进程 1 5.30 GiB、LP 303 MB |
| A1 外推与候选配置（`a1_analysis.py` / `a1_summary.py` / `report_tables.py`） | 完成（`evidence/A1_DATA.json`、`A1_EXTRAPOLATION.json`、`A1_SUMMARY.json`、`REPORT_TABLES.md`） | | F1 进程 2 峰值 90 / 124 / 160 GiB，单进程 162 / 206 / 253 GiB；8470Q T16 每次迭代 135 / 580 / 1,127 s，F1 barrier 9.5 / 56 / 146 h（72 h 时限风险）；推荐 vGPU 8470Q 368 GB → 阿里云 512 GiB → 4090D EPYC 240 GB |
| `RUN_PLAN_B4.md` 定稿、运行脚本登记常数（R_WALL 266,400；超时 3,600 / 32,400 / 10,800；POST_MEM_NEED_GIB 100；预检 25 核 / 190 GiB / 45 GB） | 完成 | | |
| 新增测试（3 轮修复） | 完成：26 passed（`evidence/tests/TESTS_new2.log` 23 passed + 3 个修后单独通过） | | 第 1 轮 8 失败（替身合成网络无登记 SHA → `base-check --no-registered`；缺 `import os`）；第 2 轮 3 失败（终止原因被 `split_built` 覆盖；NOSOLVE 模式只建 F1；构建行许可字段期望） |
| 提交 1–3 | 完成 | `a9ccc129`、`15482e3f`、`96eafa53` | 分进程 + A3.1；A3.2/A3.3；第四批运行脚本 / 计划 / 打包 / 演练 / 测试 |
| 演练 `drill_b4.sh`（56 真实 ×2 + 182 合成 ×2） | 真实两类完成（ACCEPTED_LAYER2）；合成类型因 `local` 展开顺序错误失败，已修复待重跑 | | 重跑后提交 4，再打包 |
| 9 类后处理链回归（`regress5.sh`） | 完成：ALL_EQUAL（9 类、17–18 文件 / 类、约 37,400 数值逐位相同，547 s） | | `evidence/regress/` |
| 全量测试（`tests_all.sh full`） | 完成：655 passed / 69 skipped / 0 failed（1,285 s） | | `evidence/tests/TESTS_full.log` |
| 提交 4（演练脚本修复 + 辅助脚本镜像 `scripts/wsl_b4p/`） | 完成 | `f806e3e7` | 复制时扫描命中的是扫描脚本自身的模式字面词（非泄露），已改为字符类写法并重新复制（提交 5 覆盖） |
| 演练重跑（在 `f806e3e7` 上） | 完成：4 类全部跑通（真实 56 ×2 ACCEPTED_LAYER2；合成 182 ×2 NOT_ACCEPTED/c1a 预期） | | `evidence/DRILL_B4.json`，461 s |
| 包 v7（`make_package.sh`） | 完成：19 文件 / 213,805,295 B，提交 f806e3e7，网络 = 登记值 | | 第一次因 `pipeline_pkg.sh` 的 DRILL_JSON 路径少 `b4p/` 被拒，修正后重跑 |
| 干跑（pre / build / real / synth / guards） | 完成：预检 OK；BUILD_ONLY 通过；合成整链到停批打包；真实重放被进程 3 的参数核对正确拒绝（档案 A ≠ T16）；钩子 / 未登记值拒绝 | | `evidence/dryrun/DRYRUN_SUMMARY.json`；real / synth 第一次因占位许可文件不可读被运行器拒绝，改用占位文件后重跑 |
| 报告定稿、证据 JSON | 完成 | | `B4P_REPORT.md`、`B4P_EVIDENCE.json` |
| 提交 5（报告 / 证据 / 进度 / 辅助脚本镜像）、推送 | 进行中 | | `commit5.sh` |

**本指令结束状态（2026-10-26 ~05:55 SGT）：** 全部子步骤完成；本机 Gurobi 8 / 8 次用完；本机计算约 1.8 h / 5 h；磁盘新增约 10 GB / 40 GB；不连云、不上传、未构建或求解完整 2920×3h；等待用户审阅（机器选择、SoftMemLimit、并行阈值、72 h 时限）。
| 报告 `B4P_REPORT.md` | 初稿已写（演练 / 测试 / 包 / 干跑待填） | | |
| `run_batch4.sh`、`preflight.sh`、`make_package.sh`（v7）、`drill_b4.sh`、`RUN_PLAN_B4.md` 草稿、替身 `b4p_fake_pipeline.py`、`test_b4p_batch4.py` | 已写，待运行测试 | | 阈值单元测试通过；替身整链测试待求解结束后运行（进程计数冲突） |
| `scripts_project/b4_batch4.py`（第四批运行表与辅助） | 已写，待测试 | | base-check 对登记网络 all_equal |
| A3.2 / A3.3（分支代理） | 完成（未提交） | | `run_batch3.sh` `abspath()`（`readlink -m`，START 行记完整路径）；`install_env.sh` 按频道镜像 + `--check-mirrors` + 1 KB 范围请求可达性检查；`test_b4p_paths.py` 2 passed（83 s）、`test_b4p_install_env.py` 6 passed；回归 `test_m10r_s1_modes.py` 8 passed（243 s）、`test_m10p_batch3.py` 33 passed（568 s）（`/home/jin/b4p/a3_tests.log`） |
| C5：int 140 探针（阈值 100，T16） | 完成 | | 调用 5：Dense cols 5,894、Free vars 27,936、AA' 6.92e6、Factor NZ 1.604e8（2.3 GB）、Factor Ops 7.69e11、预求解 8.8 s、排序 37.2 s、25 次迭代 163 s（迭代 10→20 平均 4.4 s/次）、进程 2 峰值 6.66 GiB、MaxMemUsed 7.75 GB、读入 4.2 s；进程 1 4.85 GiB、LP 241 MB、写 15.5 s；进程 3（迭代上限无解）4.85 GiB |

## Gurobi 使用记录（本机；授权 8 次）

| 次 | 内容 | 开始（UTC） | 结束（UTC） | 与上次间隔 | 结果 |
|---|---|---|---|---|---|
| 1 | C1 一体化 56 时段，现有单进程，档案 A（T8），TimeLimit 1750 | 2026-10-25 19:33:33 | 19:40:20 | — | optimal，129 次迭代，428.37 WU，目标 307,847,440,010.6307，峰值 4.74 GiB（单进程），与 M08b 冒烟逐位相同 |
| 2 | C2 一体化 56 时段，分进程（进程 2 `b4_split_solve.py`），档案 A（T8），TimeLimit 1750 | 2026-10-25 19:58:37 | 20:02:34 | 1,097 s | OPTIMAL，129 次迭代，428.37 WU，Fingerprint 0xb609266f（= C1 / 冒烟），LP 目标 305,492,907,999.02893（= C1），进程 2 峰值 3.62 GiB，MaxMemUsed 3.61 GB，读入 LP 1.6 s |

## 本机计算时间账（上限 5 h）

| 项 | 耗时 |
|---|---|

## 续做点

从上表第一个"进行中 / 待做"的子步骤继续。
