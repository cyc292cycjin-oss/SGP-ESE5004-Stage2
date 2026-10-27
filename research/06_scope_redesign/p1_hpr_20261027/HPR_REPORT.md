# HPR 报告：HPC 正式运行前彻底审查与准备（第四批 F1 / F2，2920×3h v2；本机；不连 HPC）

**摘要**
1. **结论：`PRE_HPC_CHECKLIST.md` H-P1–H-P14 全部 PASS，独立审查两轮阻断项 0 → 可以上机**；但有 4 项保留（R1–R4，第 6 节）与第 10 节的用户决定事项，请在步骤 A 之前确认。本步骤未连 HPC、未上传、未改模型 / 网络 / 成本表 / 档案参数 / 验收阈值；本机 Gurobi 调用 2 / 2。
2. **登记在前：** `RUN_PLAN_HPC.md` 于 2026-10-27 13:19:34 SGT 提交（`1f62176f`，已推送），早于本机 H4 求解（首次 Gurobi 启动 2026-10-27T06:35:07Z，晚 75 分钟）与任何 HPC 操作（本步骤未连 HPC）。B1–B4 全部落实：TimeLimit 864,000 s（墙钟 871,200 s）；输入改为 v2 2920×3h 网络（`08879f0b…` 63,873,447 B / `d90ca992…` 63,202,193 B，构建 `72083fde`）；PBS `parallel` 两作业各 48 核、F1 300 GB / F2 250 GB；档案 `formal_barrier_1e6_t16` 与 `SOLVE_MODE=split` 不变。
3. **两作业方式复用已测试逻辑：** F1 / F2 作业各调用 `run_batch4.sh --only <rid>`（阶段 0 → 进程 1 / 2 / 3 → 逐运行后处理 → 分级，与批次模式逐步相同，替身测试逐项比对通过）；批级作业 = `POST_ONLY=1 run_batch4.sh`（参照 / 重评 / B6 / Owen / 汇总 / 打包）。F2 的 Gurobi 进程以 PBS 依赖 `after:F1` + 运行器 `WAIT_START_OF=F1` 保证在 F1 Gurobi 启动 ≥ 330 s 后开始；正式作业不做预检的许可节（不多占 WLS 会话）。
4. **内存止损计量：** 作业体从 `/proc/self/cgroup` 解析**含本作业号**的 cgroup 路径（v1 `/pbspro/<作业号>`、v2 `/pbs_jobs.service/jobid/<作业号>`）作为匿名内存计量；不可见（或路径不含作业号，如共享的 MoM 服务 cgroup）→ 进程组 RSS 之和；两种计量都对配额 80 % 判定并逐分钟记录。P1 探针在两作业方式下不再使用。
5. **H4 本机演练（提交 `be5e49fd`）：** 生成的冒烟作业脚本作为 bash 执行（模拟 PBS 变量）→ F1 / F2 56 时段均 **optimal**，目标值 340,661,983,874.5359 / 352,091,303,417.9458、迭代 113 / 139、X / Pi / RC 与全部导出与 DFX F5.5 冒烟**逐位相同**，GATES_V6 均 ACCEPTED_LAYER2，后处理链与批级作业 exit 0，B6（56 时段）11.4293 bn 相同；两次 Gurobi 调用 06:35:07Z–06:38:38Z、06:47:53Z–06:51:29Z（间隔 555 s；本机 Gurobi 2 / 2 用完）。
6. **包 v9：** 终版提交 `8ed41d97`（审查修正与自查 S-01 后重建）：36 文件、213,498,758 B，`sha256sum -c` 36 / 36 OK；两个 v2 网络 = 登记 SHA / 字节，无 365×24h、无许可；干跑：预检 7 节 OK（resources 本机失败属预期、licence 节未跑），截短 56 BUILD_ONLY 经 D2 作业脚本在新目录真实构建 exit 0，21 个拒绝用例全部 exit ≠ 0 且未写 STATUS；`hpr_consistency.py` 36 行全部一致。
7. **测试：** 替身测试新增 `test_hpr_two_jobs.py` 17 项（H3.6 的全部场景 + 审查修正 2 项）；B4P 10 项、DFX 运行器 / 第三批替身同进程通过；全量测试三次 0 failed，最后一次在最终代码提交 `8ed41d97` 上 **719 passed / 67 skipped / 0 failed**（基线 702 / 67：+17 = 新测试；67 项跳过与基线同类，逐项清单在证据中）。
8. **用户补充的步骤 D2**（全尺寸 BUILD_ONLY 测试作业）已登记为测试（RUN_PLAN_HPC §9）、有作业脚本 `hpr_build_only_f1.pbs`，本机干跑用截短 56 走同一作业脚本；正式命令在 `BUILD_ONLY` 等开关残留时被拒（干跑验证）。
9. **发现并修正的缺陷（本步骤之前不存在于任何已运行的包）：** 作业体首版在钩子检查之前给自己的 `RUN_DIR` 赋值，会使每个正式作业被拒；WSL 的 `/proc/self/cgroup` 为 `0::/init.scope` 揭示"非作业 cgroup 会被误用"的问题（已改为要求路径含作业号）；预检 `resources` 节在 mawk 下读两个文件会中止；`preflight_dfx.sh` / `preflight.sh` 的 CGROUP_ROOT 误报（DFX 阶段 4 发现 5）已修正。
10. **需要用户决定的事项：** 见第 10 节（至少：步骤 A–D、D2 是否在 10-29 18:00 维护前做；RUN_PLAN_HPC §12 的准备端取值；冒烟目标值跨机器偏差的处置口径）。

## 1. H1 现状复核（VERIFIED，只读）

### 1.1 两个 v2 2920×3h 网络

| 文件 | 实测 SHA256 | = B2 | 实测字节 | = DFX 登记 | 构建回执 `code_sha` | 回执 SHA = 文件 |
|---|---|---|---|---|---|---|
| `integrated_2920_3h_unsolved.nc` | `08879f0bede119d77160cdb3f5f3c69dba302540b256b64efa4f16adbbefb271` | 是 | 63,873,447 | 是 | `72083fde6bffd89580869af6dd00885a8d76721f` | 是 |
| `disconnected_2920_3h_unsolved.nc` | `d90ca99220d448c894c43c071b7e38f8c74e0a101b72878a4bdd941c37b164e7` | 是 | 63,202,193 | 是 | `72083fde6bffd89580869af6dd00885a8d76721f` | 是 |

`BUILD_STATUS.txt`：`START:2026-10-26T14:34:06Z commit:72083fde… dirty:0`；同一次构建写出的 365×24h 日网络 `82928a4c…` / `5c75bfa0…` 即 DFX 阶段 4 的 V1 / V2 输入——两种分辩率出自同一构建提交。

### 1.2 登记值逐项分类（沿用 / 按 B1–B4 修改 / 不再适用）

| 登记值 | B4P 值 | 分类 | HPR 取值 / 替代机制 |
|---|---|---|---|
| 网络 SHA256 / 字节 / 构建提交 | `bca20fc0…` 64,106,133 / `b401a687…` 63,439,167 / `ec80668f` | **按 B2 修改** | `08879f0b…` 63,873,447 / `d90ca992…` 63,202,193 / `72083fde` |
| TimeLimit `R_TL` | 259,200 s | **按 B1 修改** | 864,000 s（`b4_batch4.TIME_LIMIT_S` 单一来源） |
| 进程 2 墙钟 `R_WALL` | 266,400 = TL + 7,200 | **按 B1 派生** | 871,200（余量 7,200 不变） |
| 许可间隔 `R_GAP` | 330 s | 沿用 | 330 s + F2 对 F1 启动的等待（`WAIT_START_OF`，上限 7,200 s） |
| 求解方式 `R_MODE` | split | 沿用（B4） | split |
| 进程 1 / 3 超时 | 3,600 / 32,400 s | 沿用 | 同 |
| P1 探针（3,600 s / 0.40 / 33 核） | §3.2 | **两作业方式不再适用** | PBS 依赖 + 许可间隔；`--only` 不做探针 |
| 内存止损 0.80（cgroup 匿名内存） | §3.3 | 沿用；计量按 PBS 写明 | 作业 cgroup（路径含作业号）或进程组 RSS；配额 = 申请值 |
| 早期测速 0.80 / 450、250 | §3.4 | 沿用 | 止损线 691,200 s |
| 后处理并存 100 GiB、单步 10,800 s、重做一次 | §3.6 | 沿用 | 同 |
| 分级停批、资源重开、续跑判定 | §3.5 / §3.8 | 沿用 | STOP / STOP_SAFE 经共享运行目录跨作业生效 |
| 预检硬下限 25 核 / 190 GiB / 45 GB | §5 | 沿用为缺省；作业内按申请值 | `NEED_CORES=申请核数`、`NEED_MEM_GIB=申请值 × 0.9` |
| 候选云配置、云端步骤（§4–5、§8） | AutoDL / 阿里云 | **不再适用** | RUN_PLAN_HPC §3、操作手册 A–G |

### 1.3 阶段 2 草稿与 B1–B4 的不一致（全部弃用草稿脚本，改为复用 `run_batch4.sh`）

| 草稿 | 草稿取值 | 不一致 | 处理 |
|---|---|---|---|
| `make_pbs.sh` / `README_HPC.md` | 推荐单作业 96 核、210 GB（串行）/ 400 GB（并行）、260 h；两作业各 48 核、F1 210 / F2 200 GB、130 h；`TIME_LIMIT_S=432000` | B3：两作业各 48 核、**300 / 250 gb**；B1：240 h → walltime ≥ 255 h | 作业脚本由 `b4_batch4.py hpc-plan` 生成 |
| `hpc_job_both.sh` | 单作业 + P1 探针；作业内预检含 licence 节 | B3 两作业；正式作业不得多占 WLS 会话 | 弃用；`hpr_job.sh` 不跑 licence 节 |
| `hpc_run_one.sh`（未测试） | 重写三进程 + 后处理；`TL=${JOB_TIME_LIMIT_S:-259200}` 由环境覆盖；内存只记录不止损；无早期测速、无许可间隔、无 `.started` 续跑判定 | 违反"复用已测试逻辑"；B1 值未登记；缺 3.3 / 3.4 保护 | 弃用；`run_batch4.sh --only` |
| `hpc_batch_post.sh`（未测试） | 重写批级步骤 | 同上 | 弃用；`POST_ONLY=1 run_batch4.sh` |
| `hpc_smoke_56.sh` | 只跑一体化、独立后处理链 | 未覆盖 F2 与批级；非正式路径 | 冒烟 = 三个作业体顺序执行 |
| `hpc_install_env.sh` | 登录节点安装（约 14 min，接近 30 min CPU 限制） | H3.4 要求作业方式 | `hpr_install.pbs`（serial） |
| `hpc_preflight.sh` | 登记值字面量重复写在脚本里 | 可能漂移 | 调用 B4P `preflight.sh` 各节；`hpr_consistency.py` 比对 |
| `CGROUP:` 记录根 cgroup 文件 | v1 根 `memory/memory.stat` 会把全节点内存当本作业 | 内存止损误判风险 | 作业体解析含作业号的路径，否则 RSS |

## 2. `RUN_PLAN_HPC.md`

原文见附录 A（提交 `1f62176f`，2026-10-27 13:19:34 SGT）。**修订：** 独立审查（H7）之后补写说明、未改任何第 2–7 节的数值与规则（头部"修订"段逐条列出；审查员第二轮独立复核"第 2 / 3 / 10 节表格行零改动"）：§4 第 6 条去掉本机许可文件路径（F-09）；§5 第 1 项补 rss 模式下 cgroup 列为空（N-03）；§7 第 5 项补批级作业的放行条件说明（F-06）；§9 BUILD_ONLY 行补 D2 判读规则（F-16）；§11 作业日志位置更正（F-10）。

## 3. H3 改动与测试

### 3.1 代码与脚本改动（全部在分支 `codex/hpr-20261027`；模型、网络构建、成本表、档案参数、GATES_V6 / C1 阈值未改；`s2_solve.py` / `b4_split_solve.py` 未改）

| 文件 | 改动 | 作用 | 测试 |
|---|---|---|---|
| `scripts_project/b4_batch4.py` | `REGISTERED_SHA` / `REGISTERED_BYTES` / `BUILD_COMMIT` → v2（B2）；新增 `TIME_LIMIT_S` 864,000、`WALL_MARGIN_S` 7,200、`WALL_CAP_S` 871,200、`LICENCE_GAP_S` 330、`WAIT_START_MAX_S` 7,200、各超时常数、`HPC_JOBS`（六个 PBS 作业）、`SMOKE`、`SMOKE_EXPECTED_*`、`QUEUE_LIMITS`、`B4P_HIGH_PEAK_GIB`、`walltime_components()`；`memstat()` 支持 cgroup v1 作业目录布局（`total_rss` / `memory.limit_in_bytes`）；`reference_comparison()` + `summary(--reference-values)` + `hpc-plan` 子命令 | 登记值单一来源；批级对比参照 | `test_hpr_two_jobs.py::test_registered_values_are_one_single_source`、`::test_reference_comparison_and_summary_markdown`、`::test_memory_stop_by_cgroup_v1_job_directory`；B4P `test_run_table_and_thresholds_are_the_registered_plan`（断言改为 B1 / B2 值） |
| `research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh` | `--only <rid>`（阶段 0 + 同一 `solve_run` / `post_run`，无 P1 探针，无批级步骤，`BASE_CHECK_<rid>.json`，`busy()` 只数本运行目录的进程）；`WAIT_START_OF` / `WAIT_START_MAX_S` + `wait_other_start()`；`MEM_MEASURE` auto / cgroup / rss + `group_rss_b()` + `memory_exceeded <pgid>`；cgroup 三种布局；`R_TL=864000; R_WALL=871200`；START 行记录计量方式与 cgroup 来源；`REFERENCE_VALUES` 传给 summary | 两作业方式；PBS 下的内存计量 | `test_only_mode_equals_batch_mode_step_by_step`（逐步比对）、`test_f2_gurobi_waits_for_f1_start_plus_gap`、`test_f2_safe_stops_when_f1_never_starts`、`test_memory_stop_by_process_group_rss_without_cgroup_accounting`、`test_memory_stop_by_cgroup_v1_job_directory`、`test_projection_stop_and_post_solve_error_in_only_mode`、`test_batch_job_after_an_unusable_run`、拒绝用例；B4P 10 项（批次模式行为不变） |
| `…/cloud_package_b4/preflight.sh` | CGROUP_ROOT 误报修正（H3.5）；`R_TL=864000`；`code` 节断言 `b4_batch4` 登记值 = `run_batch4.sh` R_* = 预检 R_TL、构建提交 `72083fde`；`resources` 节支持 cgroup v1 作业目录；匿名内存读取逐文件 | 预检与登记一致 | `test_preflight_cgroup_root_note_fixed_and_job_dir_resources` |
| `research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/preflight_dfx.sh` | 同一 CGROUP_ROOT 误报修正 | DFX 阶段 4 发现 5 | 同上；DFX 运行器测试 14 项不变 |
| `tests/research/fixtures/b4p_fake_pipeline.py` | 新钩子 `FAKE_RSS_SPIKE_<rid>`（真实分配内存） | RSS 计量的替身 | — |
| `research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/` | `make_pbs.sh`（从 `hpc-plan` 生成六个作业脚本）、`hpr_job.sh`（作业体：formal / batch / smoke56 / build_only；build_only 对已含上次运行的目录拒绝，S-01）、`hpr_install_env.sh`（安装作业体）、`hpr_preflight_login.sh`、`hpr_submit.sh`（步骤 E 一条命令）、`hpr_status.sh`（步骤 F）、`make_hpc_package.sh`（包 v9）、`hpr_consistency.py`（H-P3）、`make_reference_values.py` | HPC 部署 | `test_make_pbs_and_consistency`、`test_job_body_smoke56_runs_f1_f2_batch_with_standins`、`test_job_body_build_only_records_metrics_and_deletes_the_lp`、`test_job_body_formal_refusals_and_batch_not_ready`、`test_job_cgroup_detection`；H4 演练（真实求解走同一作业体） |

### 3.2 H3.6 要求的替身测试覆盖

| 要求 | 测试 | 结果 |
|---|---|---|
| F1 / F2 单运行模式 = 批次模式 | `test_only_mode_equals_batch_mode_step_by_step`：同一替身在批次模式与 `--only F1` → `--only F2` → `POST_ONLY=1` 下，每个运行的调用序列（build / gurobi / assign / va / c1 / m12 / m12a / regrade）、求解参数（档案、TimeLimit、OMP、状态）、`RUN.json`（除路径）、回执关键字段、`.cond` / `.label`、导出文件清单、STATUS 行类型、B6 与结果包逐项相同；只多出 `ONLY_MODE` / `WAIT_START` / `SKIP_ENDED`（批级重访）行，少 `P1_PROBE` | 通过 |
| F2 等待许可间隔 | `test_f2_gurobi_waits_for_f1_start_plus_gap`（并发两运行器，F2 Gurobi 启动 ≥ F1 启动 + 间隔，且在 F1 结束前启动）；`test_f2_safe_stops_when_f1_never_starts`（超过 `WAIT_START_MAX_S` → `STOP_SAFE:WAIT_START`，进程 1 已做、无 Gurobi） | 通过 |
| 内存止损（cgroup 与 RSS） | `test_memory_stop_by_cgroup_v1_job_directory`（作业目录 `memory.stat total_rss` + `memory.limit_in_bytes`）；`test_memory_stop_by_process_group_rss_without_cgroup_accounting`（无 cgroup 计量 → RSS；替身真实分配 700 MB 对 0.5 GiB 配额 → `STOP_SAFE:MEMORY:F1:rss`；配额内不止损） | 通过 |
| 早期测速止损 | `test_projection_stop_and_post_solve_error_in_only_mode` | 通过 |
| 求解后异常不丢解 | 同上（`FAKE_POST_ERROR` → 终止状态与解保留、`ASSIGN exit=4`、标签 ACCEPTED、无 UNUSABLE） | 通过 |
| PBS 中断后的续跑判定 | `test_only_mode_equals_batch_mode_step_by_step` 末段：已结束 → `SKIP_ENDED`、无新 Gurobi 调用；已开始未结束 → `STOP_SAFE:INTERRUPTED`、exit 3 | 通过 |
| 批级作业在一个运行未验收时的分级 | `test_batch_job_after_an_unusable_run`（F2 MEM_LIMIT 无解 → `UNUSABLE:F2:nosol` + STOP；批级 `POST_ONLY` → `HALTED`、`results_light_halted_*`、汇总 B6 不可计算）；`test_job_body_formal_refusals_and_batch_not_ready`（两运行未结束 → `not_ready` exit 2） | 通过 |
| 测试开关残留时正式命令被拒绝 | `test_job_body_formal_refusals_and_batch_not_ready`（作业体：BUILD_ONLY / SPLIT_CMD / FAKE_* / 缺授权 / 许可缺失或非 600 / 运行目录含 build_only 或 SMOKE 残留 / 本机演练开关在真实作业号下；运行器：TRUNCATE、旧 TimeLimit 259,200、旧墙钟、POST_ONLY 与 `--only` 并存、非法 `MEM_MEASURE`、非法运行号、`WAIT_START_OF` 指向自身——全部 exit 2、无 STATUS） | 通过 |

### 3.3 测试运行记录

| 运行 | 内容 | 结果 |
|---|---|---|
| 替身首轮（同进程，提交前） | `test_hpr_two_jobs.py` + B4P 4 文件 + `test_dfx_runner.py` + 第三批 3 文件 | 85 passed / 1 skipped / 6 failed（1,469 s）——6 项全部在新文件：一致性脚本字符串比较 0.80 ≠ 0.8、SHA 行混入字段、比对测试未允许 `SKIP_ENDED`、**作业体 RUN_DIR 自赋值早于钩子检查**、cgroup 检测替身缺 `ALLOW_UNREGISTERED`、mawk 双文件中止 |
| 替身第二轮 | HPR 15 + B4P 10 | 23 passed / 2 failed（291 s）：比对测试批级阶段未传 `FAKE_C1_REGRADE_F2`；拒绝用例辅助函数先 update 再 pop 删掉了被测开关（测试编排） |
| 替身第三轮 | HPR 15 | **15 passed**（191 s） |
| 全量测试 ①（提交 `69b0b7d1`，干净树，独立审查前） | `tests/` 全部，无 Gurobi 许可变量 | **717 passed / 67 skipped / 0 failed**（1,619 s；`evidence/tests/full.log`） |
| 替身测试第四轮（审查修正后） | HPR 17 + B4P 10 | **27 passed**（首跑 26 + 1 项测试编排修正后单独重跑通过；`evidence/tests/hpr_b4p.log`） |
| 全量测试 ②（提交 `a955ab59`，审查修正后，`-rs` 含跳过原因） | `tests/` 全部 | **719 passed / 67 skipped / 0 failed**（1,600 s；`evidence/tests/full_rs_a955ab59.log`）。基线 DFX 阶段 3：702 / 67 → +17 = `test_hpr_two_jobs.py`；67 项跳过全部为"本机无该步构建 / 结果 / 外部数据"（清单 `evidence/tests/full_rs_skips_a955ab59.txt`） |
| 替身测试第五轮（自查 S-01 后） | HPR 17（build_only 用例含第二次调用）+ B4P 10 | **27 passed**（336 s；`evidence/tests/hpr_b4p.log`） |
| 全量测试 ③（**最终代码提交 `8ed41d97`**，自查 S-01 后，`-rs`；其后的最终提交只含文档与证据） | `tests/` 全部 | **719 passed / 67 skipped / 0 failed**（1,651 s；`evidence/tests/full_rs.log`、`full_rs_commit.txt`）；67 项跳过清单与 ② 逐行相同（`full_rs_skips.txt`） |

## 4. H4 本机端到端演练（VERIFIED；`evidence/h4/`）

**方式：** 演练提交 `be5e49fd`（干净树）；包副本 `/home/jin/hpr_drill/pkg`（= v9 的组成：`run_batch4.sh`、`preflight.sh`、`pack_results.sh`、`env/`、`hpc/`、`pbs/`（`make_pbs.sh` 生成）、两个 2920×3h v2 网络 + 回执 + 成本表、`code_be5e49fd.tar.gz`、`COMMIT`、`SHA256SUMS`、`REFERENCE_VALUES.json`、`HPR_AUTH.txt`）；把生成的 **`pbs/hpr_smoke56.pbs` 当作 bash 执行**，模拟 `PBS_O_WORKDIR=<包目录>`、`PBS_JOBID=local.h4drill`、`NCPUS=17`、`HPR_LOCAL_DRILL=1`（跳过 token 服务器 curl 与本机必不满足的 resources 节）、`HPR_RUN_ROOT=results_project/hpr/h4`。作业脚本依次运行三个作业体：`hpr_job.sh` smoke56 F1 → F2 → batch，即正式路径 `run_batch4.sh --only F1` → `--only F2` → `POST_ONLY=1`（`TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600` 由作业体导出；标签 `SMOKE_TEST_ONLY`）。作业内预检 guards / sha / networks / env / profile / code / tools 全部 OK（`sha` 节把代码归档解包到 `repo/`，`networks` 节按登记值核对两个网络）。作业体记录 `CGROUP:version=none`（WSL 的 `/proc/self/cgroup` 为 `0::/init.scope`，不含作业号）→ `mem_measure=rss`。

| 运行 | Gurobi 进程（UTC） | 终止 / 状态 | 回执目标值 EUR | Gurobi 目标（LP） | barrier 迭代 | Fingerprint | 进程 2 秒 / 峰值 RSS / MaxMemUsed | 进程 1 / 3 峰值 | C1 | GATES_V6（临时 → 终） | 后处理 exit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 一体化 56 | 06:35:07–06:38:38（241 s） | optimal / OPTIMAL | 340,661,983,874.5359 | 3.38307452e+11 | **113** | 0x7a66397f | 241 s / 5.85 GiB / 5.95 GB | 2.17 / 2.61 GiB | layer1_plus_nodal_price_settlement，abc 111 | ACCEPTED_LAYER2 → ACCEPTED_LAYER2 | BUILD / GUROBI / ASSIGN / VIOLATIONS / C1 / M12 / M12_OWEN 全 0 |
| F2 不互联 56 | 06:47:53–06:51:29（241 s） | optimal / OPTIMAL | 352,091,303,417.9458 | 3.49575087e+11 | **139** | 0x32f39cf2 | 241 s / 4.44 GiB / 4.56 GB | 1.88 / 2.27 GiB | 同，abc 111 | ACCEPTED_LAYER2 → ACCEPTED_LAYER2 | 全 0 |

- **两次 Gurobi 调用：** F1 结束到 F2 启动 **555 s**（≥ 330 s，≥ 5 min）；各 241 s（≤ 60 min）；运行器自身的 `GAP_PHASE_1` 330 / 331 s、`GAP` 359 / 355 s 均按登记值执行；早期测速在第 20 次迭代判定（F1 1.4 s/次 → 预计 691 s；F2 1.0 s/次 → 312 s；均 < 0.8 × 3,000）；内存止损 RSS 计量对配额 32 GiB（止损线 25.6 GiB）未触发。无重试。**本机 Gurobi 调用 2 / 2 已用完。**
- **批级作业体（POST_ONLY）：** `SKIP_ENDED_F1 / F2`（已结束不重做）→ `BATCH_REFERENCE exit 0` → `REGRADE_F1 / F2 exit 0`（ref=batch，终标签 ACCEPTED_LAYER2）→ `M12_BENEFIT exit 0`（B6 11.429319543409912 bn，负受益无）→ `SUMMARY exit 0`（含 `REFERENCE_VALUES.json` 对比节）→ `PACK_final`（light 989,079 B、full 59,598,444 B）→ `DONE`；三个作业体 `JOB_END exit 0`（771 / 750 / 7 s）；`SMOKE_STATUS.txt`：`SMOKE_RESULT:PASS`，相对差 0.000e+00。
- **与 DFX F5.5 冒烟（同网络截短 56，提交 `896828fd`，单进程路径）逐位比对（`h4_compare.py` → `evidence/h4/H4_DRILL.json`）：** 回执目标值、Gurobi 目标、终止状态、迭代数（113 / 139）、Fingerprint、求解参数、输入 SHA256、`solution/X.npy` / `Pi.npy` / `RC.npy`、`lp/` 十个数组、账本（三份）、`NODAL_PRICES.csv`、`cross_border_flows.csv`、`capacity_reduced_costs.csv`、`nodal_prices_summary.csv`、`COMPONENT_COST_BREAKDOWN*.csv/json`、`DUALS_INDEX.csv`、`DUALS_BY_CONSTRAINT.nc`、`ALLOCATION.csv`、`LEDGER_IDENTITY.json`、`EMISSIONS_BY_COUNTRY.json`、`CO2_FLOWS.json`、`CAPACITY_BY_TECH_COUNTRY.json`、`BUNKER_ACCOUNT.json`、`INTERIOR_CHECKS.json`、`lp/MATH_PROBLEM.json`、GATES_V6 标签 —— **全部逐位相同**；B6（56 时段）11.429319543409912 bn 相同。两项按构造不同、数值全同：`m12_owen/OWEN.json`（只差 5 个路径 / 标签键：`tag` `BATCH4_F1` 对 `SMOKE_integrated`、`network`、`duals`、`c1_c_dual/precision/file`、`threshold_source`；数值键 0 处不同）；求解后网络 `*_solved.nc`（241 个数据变量与坐标逐值相等（NaN 对 NaN），只有 `meta` 的 `s2_solve_authorization` 文本不同）。`ALLOCATION_LINES.csv` 在不互联情景两边都不存在（无跨境线路）。这同时是 H3 代码改动"不改变解"的回归证明：分进程路径（`run_batch4.sh --only`）与 DFX 的单进程路径在 56 时段上解、对偶、导出逐位相同。

## 5. 包 v9（VERIFIED）

- **目录：** `work/p1_hpr_20261027/hpc_package/`（`make_hpc_package.sh` 在 WSL 组装，输出到 D:）。**终版：提交 `8ed41d97`**（`COMMIT`）；**36 个文件，213,498,758 B（不含清单）**；`SHA256SUMS` SHA256 `1866529e940a4312…`（完整值在 `evidence/package/HPC_PACKAGE_MANIFEST.json` `sha256sums_sha256`），`HPC_PACKAGE_MANIFEST.json` SHA256 `31437affb59ec6ad1ef254df41d12814192742a94717a065709252d5f8ae6bb4`；`sha256sum -c` 36 / 36 OK。上传约 214 MB：1 / 4 / 10 MB/s 下约 3.6 / 0.9 / 0.4 分钟。构建历史：`86af83f3`（审查前）→ `69b0b7d1`（第一轮审查对象）→ `a955ab59`（审查修正后；清单差异统计因 git 路径规格缺陷不完整）→ `9ff86cb6`（第二轮审查对象）→ `a6e119dd`（第二轮修正后）→ **`8ed41d97`**（终版，自查 S-01 之后）；前五次均未上传、已删除。
- **内容：** `networks/`（两个 2920×3h v2 网络 `08879f0b…` 63,873,447 B / `d90ca992…` 63,202,193 B + 两份构建回执 + 两份成本表；无 365×24h 文件）；`code_8ed41d97.tar.gz`（git archive，文件名带包提交号，不含顶层 `research/`）；`run_batch4.sh`、`preflight.sh`（B4P 源 + HPR 修改）、`pack_results.sh`；`env/`（第三批锁定六文件）；`hpc/`（`hpr_job.sh`、`make_pbs.sh`、`hpr_install_env.sh`、`hpr_preflight_login.sh`、`hpr_submit.sh`、`hpr_status.sh`、`hpr_consistency.py`）；`pbs/`（`hpr_f1 / f2 / batch / smoke56 / build_only_f1 / install.pbs` + `HPC_PLAN.txt` + `MAKE_PBS.log`）；`RUN_PLAN_HPC.md`、`HPC_OPERATOR_GUIDE.md`、`HPC_FACTS_20261026.md`、`REFERENCE_VALUES.json`、`COMMIT`、`SHA256SUMS`、`HPC_PACKAGE_MANIFEST.json`。不含许可、cutout、LP / 解数组、结果、账号 / 主机信息。
- **与演练提交的关系：** 演练在 `be5e49fd`，终版包在 `8ed41d97`。打包脚本分两段比对：(1) 归档代码（`research/` 与 `tests/` 以外：`scripts_project/`、模型、配置）`git diff` **为空**；(2) 随包脚本（`cloud_package_b4/`、第三批 `cloud_package/`、`hpr_job.sh`、`make_pbs.sh`）有独立审查修正与自查 S-01 的改动（`preflight.sh` 4 行、`run_batch4.sh` 17 行、`hpr_job.sh` 20 行（含 S-01 的 7 行）、`make_pbs.sh` 1 行；另 `tests/` +43 行），以显式 `H4_PATH_DIFF_OK=1` + 说明接受并写入清单 `h4_drill.drilled_path_diff_stat` / `path_diff_note`（检查单 R3）。审查对象包 `69b0b7d1` 时被演练路径与演练提交逐字节相同。
- **干跑（H5.3；`evidence/dry_run/`）：** 包副本解到 `/home/jin/hpr_dry/pkg`：预检 7 节 OK（resources 本机失败属预期；licence 节未跑）；`hpr_preflight_login.sh` 本机失败属预期（无许可文件、无 qsub）；**截短 56 BUILD_ONLY 经生成的 `pbs/hpr_build_only_f1.pbs` 作业脚本作为 bash 执行（`HPR_DRY_TRUNCATE=56`），在新目录真实构建 31 s，exit 0**：`BUILD_CHECK_F1 passed`、`BUILD_ONLY_STATUS.txt` 记录峰值 2.17 GiB、LP 93,726,545 B、构建 18.1 s + 写出 7.9 s、写入 11.9 MB/s（LP）/ dd 1 GiB < 1 s、`LP_DELETED`、无求解器日志；**拒绝检查 21 / 21 exit ≠ 0 且无 STATUS**（含 S-01 新增的 R21：BUILD_ONLY 作业体对已含上次运行的目录 → exit 2、记录不变；清单见检查单 H-P7）。终版干跑 2026-10-27T08:39:48Z–08:40:33Z；此前四次干跑（`86af83f3` / `69b0b7d1` / `a955ab59` / `a6e119dd`）记录在 `DRYRUN_STATUS.txt` 前段，其中后三次的 BUILD_ONLY 被运行器按旧回执跳过（S-01 的来源）。

## 6. `PRE_HPC_CHECKLIST.md` 结果

见 `PRE_HPC_CHECKLIST.md`：**H-P1–H-P14 全部 PASS**；有保留项请用户确认——R1（H-P8：锁定文件版本号误报 10 处、历史提交 `be5e49fd` / `69b0b7d1` 补丁文本中的键名字面量各 1 处、代码归档 `s2_solve.py` 中沿用已久的日志清洗键名）、R2（H-P6："逐位相同"不含按构造不同的路径 / 标签 / 授权文本键）、R3（H-P6 / H-P7：H4 演练提交 `be5e49fd` ≠ 终版包提交——随包 bash 脚本经审查修正与自查 S-01，求解路径代码逐字节相同，HPC 冒烟作业为真实 Gurobi 端到端验证且为步骤 E 硬门槛）、R4（H-P8：两份构建回执含本机 WSL 用户名路径）。

## 7. 独立审查（H7）摘要与处理

- **方式：** 未参与准备的子代理（全新上下文），只给指令、`RUN_PLAN_HPC.md`、`HPC_FACTS`、包 v9（`69b0b7d1`）、手册、检查单与代码路径；只读（不运行测试 / 脚本 / 求解，不读许可与扫描模式）。原文与逐条处理见 `INDEPENDENT_REVIEW.md`。
- **第一轮结论：阻断 0，非阻断 18。** 审查员独立复算了全部登记常数（与 H-P3 的 36 行一致）、逐字节比对了包内副本与来源、顺着 `hpr_f1.pbs → hpr_job.sh → run_batch4.sh --only F1` 的真实路径读完了运行器，并做了只计数的泄露扫描（许可值 / 连接串 / 端口 0；版本号与键名字面量与检查单 R1 一致）。
- **执行端处理（全部 18 条，见 `INDEPENDENT_REVIEW.md` 第 3 节）：** 代码 / 脚本修正 8 条——F-04（冒烟 `SMOKE_STATUS` 的 WLS 状态码从 `PBS_JOBS.txt` 读取）、F-06（批级作业放行条件：停批后从未启动的运行视为落定；新测试）、F-07（`--only` 模式不再把另一作业的运行计入后处理内存条件与线程预算；rss 模式不读 cgroup 文件；新测试）、F-11（提交脚本 qsub 成功后才建目录）、F-13（状态脚本 `(none)`）、F-14（`#PBS -S /bin/bash`）、F-15（预检 JSON 按作业命名）、F-17（记录 OMP / SHELL）；手册 / 计划修正 10 条——F-01（PowerShell 行的 `$USER`）、F-02（文件计数）、F-03（C3 判据）、F-05（scp SFTP 模式：相对路径、逐文件下载、`-O` 回退）、F-08（A3 工具检查、C2 失败分支）、F-09（占位符与相对描述；回执保留 → 检查单 R4）、F-10（§11 日志位置）、F-12（半成品环境恢复）、F-16（§9 / D2-2 的 100–150 GiB 判读规则）、F-18（授权原文不含单引号）。`RUN_PLAN_HPC.md` 第 2–7 节的数值与规则未改（§7.5 补写放行条件的说明、§4 / §9 / §11 措辞，头部登记修订）。
- **H4 演练与最终包的关系：** 修正触及随包脚本 `run_batch4.sh` / `hpr_job.sh` / `preflight.sh` / `make_pbs.sh`（均为 bash；求解命令与参数不变，替身比对测试仍逐步相同），本机 Gurobi 预算已用完，H4 未重做；打包脚本以显式说明接受并写入清单（检查单 R3，请用户确认）。
- **第二轮复核（同一子代理，对象 = 修正后的包 `9ff86cb6`）：阻断 0。** 第一轮 18 条：14 条已解决、4 条部分解决且理由成立（F-08 / F-14 / F-05(b) 待 HPC 核实；F-09 → R4；F-11 残留可接受）；新发现 5 条非阻断——N-01 手册 A1 计数应为 +2（已修）、N-02 检查单 H-P5 / H-P14 须以终版落实（已落实）、N-03 RUN_PLAN §5.1 补 rss 模式说明（已补）、N-04 / N-05 手册措辞（已修）；审查员独立复核 R3 / R4"表述客观、不应升级为阻断"，并建议 R3 补写"HPC 冒烟作业是随包脚本改动后的真实 Gurobi 端到端验证且为步骤 E 硬门槛"（已补）。两轮审查原文与逐条处理见 `INDEPENDENT_REVIEW.md`。
- **审查后自查 S-01（执行端在收尾重建包的干跑记录中发现；非阻断，已修）：** 本机干跑把截短 56 的 BUILD_ONLY 作业脚本反复跑在同一干跑目录上，第二次起运行器按上次回执（`.cond=build_only`）跳过构建（2 s），作业体仍 exit 0 并把旧数字写入 `BUILD_ONLY_STATUS.txt`，而 `BUILD_CHECK_F1` 因 LP 已被上次删除而 `problem_file` 不通过——若在 HPC 上重跑步骤 D2 会得到一份看似成功的旧记录。修正：`hpr_job.sh` 的 `build_only` 分支在 `runs/build_only_f1` 已含上次运行（`F1/` 目录或 `BUILD_ONLY_STATUS.txt`）时拒绝（exit 2，不写任何文件，与其他拒绝同一口径）；替身测试 `test_job_body_build_only_records_metrics_and_deletes_the_lp` 增加第二次调用（拒绝、三个记录文件不变）；干跑脚本先移走旧目录（终版包的 BUILD_ONLY 干跑因此是真实构建）并增加拒绝用例 R21；手册 D2、`RUN_PLAN_HPC.md` §9 末条与头部修订段补说明。formal / smoke56 / batch 分支、运行器、求解路径代码未动；该项未再送独立审查（改动 5 增 2 删、逻辑 1 行，替身测试与干跑 R21 覆盖），列入检查单 H-P13 的说明。包在该修正的提交上重建（§5）。

## 8. 本机资源与 Gurobi 使用记录（VERIFIED）

| 项 | 记录 |
|---|---|
| Gurobi 调用 | **2 / 2**：F1 2026-10-27 06:35:07Z–06:38:38Z（241 s，峰值 5.85 GiB），F2 06:47:53Z–06:51:29Z（241 s，4.44 GiB）；间隔 555 s；只用截短 56 的 v2 2920×3h 网络；无重试；之后无任何调用（预检 licence 节在本机未运行；全量测试不含 Gurobi） |
| 许可 | `/home/jin/gurobi.lic` 只经 `GRB_LICENSE_FILE` 传给进程 2；未读取、未打印、未复制；演练包副本与 v9 包不含许可 |
| 本机计算用时 | 替身测试五轮 1,469 + 291 + 191 + 331 + 336 s（+ 1 项单测 8 s）；H4 演练 1,528 s（含两次 330 s 启动间隔）；打包 6 × 约 13 s、干跑 46 + 16 + 16 + 16 + 45 s、一致性 / 扫描 / 证据各约 20 s；全量测试 1,620 s + `-rs` 重跑 1,600 s + 最终 `-rs` 重跑 1,651 s（另一次 `-rs` 启动后约 12 min 被主动终止以避免与替身测试并行）；**合计约 2.9 h**（< 4 h） |
| 磁盘新增 | `results_project/hpr/` 0.89 GB（演练运行目录、干跑、测试日志）；`/home/jin/hpr_drill` 0.36 GB、`/home/jin/hpr_dry` 0.72 GB（包副本与解包代码）；worktree 0.64 GB；包 v9 0.21 GB；**合计约 2.9 GB**（< 30 GB；精确值见证据 JSON） |

## 9. 发现但未处理 / 未经用户确认的决定 / 局限

1. **PBS 环境假设未在 HPC 上验证（本步骤不连 HPC）：** 作业内 `NCPUS` 环境变量（PBS Pro 导出）缺失时作业体回退到 `JOB_NCPUS`；`PBS_O_WORKDIR` 必须是包目录（手册要求在包目录 `qsub`）；`-W depend=after:` / `afterany:` 语法按 PBS Pro 文档；cgroup 钩子的路径形式（`/pbspro/<作业号>` 或 `/pbs_jobs.service/jobid/<作业号>`）按 PBS Pro 常见配置——作业体对不符合的情形一律回退到进程组 RSS 计量（记录在 `PBS_JOBS.txt` 的 `CGROUP:` 行），冒烟作业（步骤 D）会把实际情形记录下来供审阅端核对。
2. **进程组 RSS 计量的局限：** 共享页会被重复计入（偏保守，可能略早止损），且不含进程 3 / 后处理（它们不与进程 2 并存）；cgroup 计量则是精确的作业匿名内存。两者都在 `MONITOR_<rid>.csv` 逐分钟记录。
3. **冒烟作业的 F2 未设置 `WAIT_START_OF`**（`hpr_smoke56.pbs` 顺序执行 F1 → F2 → 批级；F1 已结束时该等待立即放行），`WAIT_START_OF` 的等待逻辑由替身测试覆盖（`test_f2_gurobi_waits_for_f1_start_plus_gap`），本机演练未经真实 Gurobi 并发验证（本机只有 2 次调用且须串行）。
4. **HPC 冒烟目标值与本机值的比较只记录相对差**（跨机器浮点差异不可预知；要求 ≤ 1e-6 只是记录口径，不是验收）。
5. **H4 演练在 WSL 上的 cgroup 情形**（`0::/init.scope`，无作业号 → RSS）与 PBS 节点不同；cgroup v1 / v2 作业目录两种布局只经替身测试（`test_job_cgroup_detection`、`test_memory_stop_by_cgroup_v1_job_directory`）与一致的 `memstat` 单元测试覆盖。
6. **`SKIP_ENDED` 的续跑语义**：同一 `runs/batch4` 再次提交 F1 作业时已结束的运行被跳过且后处理只补缺——这是登记行为；但 `hpr_submit.sh` 在 `runs/batch4` 已存在时拒绝，须 `--resume` 并由审阅端判断（手册 F）。
7. **B4P 的 `run_batch4.sh` / `preflight.sh` 在仓库中被就地修改**（指令授权"新分支上修改代码与脚本"；`work/p1_b4p_20261026/` 下的已交付文件未动）；B4P 测试 `test_run_table_and_thresholds_are_the_registered_plan` 的登记值断言随 B1 / B2 更新。`RUN_PLAN_B4.md` 原文未改，其第 1 / 3.1 / 3.2 节由 `RUN_PLAN_HPC.md` 取代（RUN_PLAN_HPC 开头已写明）。
8. **历史提交中的键名字面量：** `be5e49fd` / `86af83f3` 的 `hpr_submit.sh` grep 模式含许可键名（无值），`69b0b7d1` 起改为不匹配扫描的写法；不 force-push（R1 口径）。
9. 未做：HPC 上的任何操作、上传、WLS 连通验证（留给步骤 D 冒烟作业）；2920×3h 全尺寸构建（留给步骤 D2 作业）；`SoftMemLimit` 仍不作为登记参数（B4P 3.5 第 4 项）。

## 10. 需要用户决定的事项

1. **步骤 A–D、D2 是否在 2026-10-29 18:00 维护前做**（手册与 RUN_PLAN_HPC §9 都允许两种时机）。维护前做：11-02 17:00 后可直接提交 E，且 D2 的实测（峰值内存、LP 大小、写出用时）能在维护期间由审阅端核对；风险：维护期间集群关闭不影响 `/hpctmp` 与家目录文件，但维护后应重跑 `hpr_preflight_login.sh` 再做 E。维护后做：全部在一个时段完成，但 E 要等 C / D / D2 的排队与运行。
2. RUN_PLAN_HPC §12 的准备端取值：walltime 构成（F1 255 h、F2 257 h）、批级作业 parallel 12 核 / 120 GB / 12 h、冒烟 17 核 / 32 GB / 4 h、安装 serial 1 核 / 8 GB / 2 h、正式作业不做预检 licence 节、停批信号跨作业共享、冒烟目标值只记录相对差。
3. D2 结果的处置口径：峰值 > 150 GiB 或构建 > 3,600 s（运行器超时）时先报告再决定是否调整（任何调整都是新的登记修订）。
4. 检查单第 2 节的保留项 R1–R3（扫描的版本号 / 键名字面量误报与历史提交；"逐位相同"的范围说明；演练提交与包提交的差异只在非演练路径）。
5. 许可文件在 HPC 上长期存放于 `~/.gurobi`（你已同意，手册 G4 写明保留条件）——确认或改为运行后删除。

---

## 附录 A：`RUN_PLAN_HPC.md` 原文（提交 `1f62176f` 登记；H7 后的说明性修订见其头部）

## HPC 正式运行计划（RUN_PLAN_HPC）——第四批 F1 / F2，2920×3h v2 网络，NUS Atlas（PBS Pro）两作业方式

**版本：** HPR v1，2026-10-27（SGT）。依据 `HPR_CLAUDE_CODE_INSTRUCTION.md`（SHA256 `f14cb018…412d86`）与用户 2026-10-27 12:43 SGT 确认的 B1–B4，以及用户 2026-10-27 的补充（步骤 D2：全尺寸 BUILD_ONLY 测试作业）。
**登记时间：** 本文件在任何 HPC 操作、任何本机 2920×3h v2 求解（H4 演练）之前提交（`1f62176f`，2026-10-27 13:19:34 SGT）；看到任何结果后第 2–7 节的规则与数值不再修改（修改只能作为新的、登记在前的计划修订）。
**修订（2026-10-27，独立审查 H7 之后；第 2–7 节的数值与规则未改，只补说明）：** §4 第 6 条措辞（本机许可文件不写路径）；§5 第 1 项补 rss 模式下 cgroup 列为空的说明（审查 N-03）；§7 第 5 项补"停批情形下从未启动的运行视为落定"的放行条件（审查 F-06）；§9 BUILD_ONLY 行补 D2 结果的判读规则（审查 F-16）；§11 作业日志位置更正为提交目录（审查 F-10）；§9 末条补 BUILD_ONLY 作业体对已含上次运行的目录的拒绝（审查后自查 S-01）。
**与 `RUN_PLAN_B4.md`（B4P v1，2026-10-26）的关系：** 本文件只改写 B1–B4 涉及的登记值（输入网络、TimeLimit 与派生墙钟、资源配额）和因 PBS 两作业方式不再适用的机制（P1 探针）；`RUN_PLAN_B4.md` 第 3.3–3.8 节的规则（内存止损、早期测速、验收与停批、后处理、资源止损后的重开）全部沿用，并在下文逐条写明。模型、网络构建、成本表、求解档案参数、GATES_V6 / C1 阈值一律不改。
**单一来源：** 代码中的登记常数——`scripts_project/b4_batch4.py`（`REGISTERED_SHA`、`REGISTERED_BYTES`、`BUILD_COMMIT`、`TIME_LIMIT_S`、`WALL_CAP_S`、`LICENCE_GAP_S`、`HPC_JOBS`、`MEMORY_STOP_FRACTION`、`PROJECTION_FRACTION`）与 `run_batch4.sh` 顶部的 `R_TL` / `R_WALL` / `R_GAP` / `R_MODE`；PBS 作业脚本由 `make_pbs.sh` 从 `b4_batch4.py hpc-plan` 生成；`hpr_consistency.py` 把本文件、作业脚本、运行器、预检中的值列表比对（检查单 H-P3）。

---

### 1. 运行

| 编号 | 运行 | 网络文件 | 字节 | SHA256 | 情景 | 成本表 | 档案 | 作用 |
|---|---|---|---|---|---|---|---|---|
| F1 | 一体化 2920×3h v2 | `networks/integrated_2920_3h_unsolved.nc` | 63,873,447 | `08879f0bede119d77160cdb3f5f3c69dba302540b256b64efa4f16adbbefb271` | integrated | `networks/integrated_costs_active_research.csv` | `formal_barrier_1e6_t16` | c(N)、Owen 分摊、B6 基准 |
| F2 | 不互联 2920×3h v2 | `networks/disconnected_2920_3h_unsolved.nc` | 63,202,193 | `d90ca99220d448c894c43c071b7e38f8c74e0a101b72878a4bdd941c37b164e7` | disconnected | `networks/disconnected_costs_active_research.csv` | `formal_barrier_1e6_t16` | B6 = F2 − F1 |

- **构建（B2）：** 分支 `codex/dfx-v3-20261026` 提交 `72083fde6bffd89580869af6dd00885a8d76721f`（dirty 0，`PYTHONHASHSEED=0`），DFX F5.1 构建到主检出 `results_project/dfx_v3/builds_v2/<scenario>/`；构建回执 `<scenario>_BUILD_RECEIPT.json`（`network.sha256` = 上表，`code_sha` = 构建提交）。与 DFX 365×24h v2 筛查网络（`82928a4c…` / `5c75bfa0…`）出自同一次构建。**365×24h 网络不入包**（预检发现即失败）。
- **档案（B4，不改）：** `formal_barrier_1e6_t16`：Method 2、Crossover 0、BarConvTol 1e-6、BarHomogeneous 1、Threads 16、Seed 123、AggFill 0、PreDual 0、GURO_PAR_BARDENSETHRESH 200；`--scaling on`。
- **求解方式（B4）：** `SOLVE_MODE=split`（`run_batch4.sh` 登记值 `R_MODE=split`）：进程 1 `s2_solve.py … --label BATCH4_2920X3H --split-stage build`（无许可）→ 进程 2 `b4_split_solve.py --run-dir <运行目录> --remove-lp`（唯一的 Gurobi 进程；`REMOVE_LP=1`，读入后删除约 5.4 GB 的 LP 文件）→ 进程 3 `s2_solve.py … --split-stage assign`（无许可）。B4P 等价证明（56×3h 逐位相同）不变。
- **一次求解：** 每个运行只求解一次；不重试、不改参数、不热启动；非 optimal 照实记录并按第 7 节分级。

### 2. 时限与 PBS walltime

| 量 | 值（s） | 依据 |
|---|---|---|
| **TimeLimit（B1）** `R_TL` / `TIME_LIMIT_S` | **864,000**（240 h），F1 = F2 | 用户决定 B1；B4P 外推 F1 barrier 9.5 / 56 / 146 h（v2 迭代可能多约 30 %：最高约 190 h < 240 h） |
| **进程 2（Gurobi）墙钟** `R_WALL` / `WALL_CAP_S` | **871,200** = 864,000 + 7,200 | 沿用 B4P 3.1 第 2 项的开销余量 2 × 3,600 s（LP 读入 95–154 s、解数组写出 ≤ 1,800 s）；到时终止整个进程组（TERM，30 s 后 KILL） |
| 进程 1 超时 `BUILD_TIMEOUT_S` | 3,600 | B4P：构建 + 写 LP 10–15 min，云端单核慢 1.35 倍约 20 min；3 倍 |
| 进程 3 超时 `ASSIGN_TIMEOUT_S` | 32,400 | B4P：重建 + 映射 + 导出约 2.2–3 h；3 倍 |
| 后处理单步超时 `POST_TIMEOUT_S` | 10,800 | B4P 3.6 第 3 项（3 倍余量）；违反分析与 C1 失败后重做一次 |
| 打包超时 `PACK_TIMEOUT_S` | 7,200 | B4P |
| 逐运行后处理估计 | 3,900（65 min） | B4P 6.1：违反分析 / C1 / Owen 各约 20 min（55 s × 16 × 1.35），M12 约 1 min，GATES_V6 与分级 < 1 min |
| 运行器启动后首次 Gurobi 的间隔 | 330 | B4P 3.2 第 3 项（`R_GAP`，WLS 令牌 ≥ 5 min） |
| 作业体开销（记录、预检、导出）估计 | 1,800 | HPR 估计 |
| F2 等待 F1 Gurobi 启动的上限 `WAIT_START_MAX_S` | 7,200 | 第 4 节：F1 的进程 1 ≤ 3,600 s + 330 s 间隔 + 预检与余量 |
| **PBS walltime F1** | **918,000**（`255:00:00`） | 330 + 3,600 + 871,200 + 32,400 + 2 × 3,900 + 1,800 = 917,130 → 向上取整到 255 h；≤ 720 h |
| **PBS walltime F2** | **925,200**（`257:00:00`） | 917,130 + 7,200（等待 F1 启动的上限）= 924,330 → 257 h；≤ 720 h |
| PBS walltime 批级作业 | 43,200（`12:00:00`） | 参照 / 重评 / 受益 / 汇总 / 打包为分钟级；若某运行的后处理步骤在本作业内未完成，`POST_ONLY=1` 补做最多 4 步 × 10,800 s |

早期测速（第 5 节）的止损线 = 0.80 × 864,000 = **691,200 s**。

### 3. PBS 资源（B3）

| 作业 | 队列 | 资源 | walltime | 内存配额 `MEM_QUOTA_GIB` | 核数 `CORES` | 依赖 |
|---|---|---|---|---|---|---|
| **F1** `hpr_f1` | `parallel` | `select=1:ncpus=48:mem=300gb` | 255:00:00 | **300** | 48 | 无 |
| **F2** `hpr_f2` | `parallel` | `select=1:ncpus=48:mem=250gb` | 257:00:00 | **250** | 48 | `-W depend=after:<F1 作业号>`（F1 开始执行后才可调度） |
| **批级** `hpr_batch` | `parallel` | `select=1:ncpus=12:mem=120gb` | 12:00:00 | 120 | 12 | `-W depend=afterany:<F1>:<F2>`（两者结束后，无论退出码） |

- 内存配额 = 申请值（PBS `gb` = 2^30 B；作业体把 `MEM_QUOTA_GIB=300 / 250` 显式传给运行器，不依赖 cgroup 是否可见）。F1 300 GiB ≥ B4P 高值 160 GiB × 1.25 = 200；F2 250 ≥ 149 × 1.25 = 186.25（检查单 H-P4）。止损线 80 %：F1 **240 GiB**，F2 **200 GiB**（第 5 节）。
- 48 + 48 = 96 核 = `parallel` 队列每用户合计上限（`HPC_FACTS` 队列表）；批级作业 12 核在两者结束后才运行，不与之同时占核。每用户 ≤ 8 个作业：F1、F2、批级 = 3 个。
- 300 GB / 250 GB 都 ≤ 约 360 GB，可落在 32 台 367 GB 节点（96 核 33 台、64 核 8 台都容得下 48 核）；不申请 792 GB 节点。单作业内存 ≤ 540 GB 上限；walltime ≤ 720 h。
- 不加 `-P` 项目名（本次提交未要求）；无 `-V`（登录 shell 的变量不带入作业，测试开关由预检 `guards` 节再查一次）。

### 4. 许可会话

- 学术 WLS 最多 **2 个并发会话**。F1 的进程 2 占 1 个，F2 的进程 2 占 1 个；任意时刻 ≤ 2。
- **F2 的第一次 Gurobi 会话必须在 F1 第一次会话开始 ≥ 330 s 之后。实现（两重）：** (a) `qsub -W depend=after:<F1>`：F2 只在 F1 开始执行后调度；(b) 运行器 `run_batch4.sh --only F2` 以 `WAIT_START_OF=F1` 运行：F2 的进程 1（构建，无许可）照常进行，进程 2 启动前等待共享运行目录中 `F1/.solve_start`（F1 进程 2 的启动时刻，由 F1 的运行器写出）存在且距今 ≥ `LICENCE_GAP_S` = 330 s；F1 已结束求解（`F1/.solve_end`）或 F1 未经 Gurobi 就结束（`F1/.ended`，如构建失败）也放行。等待超过 `WAIT_START_MAX_S` = 7,200 s 仍无 F1 的启动标记 → `STOP_SAFE:WAIT_START:F1`（F2 不求解，等用户）。
- **正式作业（F1 / F2 / 批级）不运行预检的 `licence` 节**（那是一次 Gurobi 会话）；作业开头只检查许可文件存在与权限位 600。许可是否可用由步骤 D 的冒烟作业验证。
- 每个运行器启动后首次 Gurobi 距运行器启动 ≥ 330 s（B4P 3.2 第 3 项，沿用）；每次启动前检查本节点上其他 `b4_split_solve.py` 进程不超过 1 个。
- **F1 / F2 运行期间，本机与任何云端都不得启动 Gurobi 会话**（本机 WSL 的许可文件与 HPC 上的 `~/.gurobi/gurobi.lic` 是同一 WLS 许可）。F2 结束后才空出 1 个会话；F1 结束后空出 2 个。
- 许可只经 `GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic` 引用；绝不进入包、代码、作业脚本、日志、结果包；导出日志经 `licen[cs]e|registered to|wls(access|secret)|academic` 过滤；打包前检索许可特征串，命中即拒绝打包。

### 5. 止损与保护（B4P 3.3–3.4 沿用，计量方式按 PBS 写明）

1. **内存止损 → `STOP_SAFE:MEMORY:<编号>`：** 每 60 s 读本作业**实际可见**的内存计量，超过配额（第 3 节 `MEM_QUOTA_GIB`）的 **80 %**（`MEMORY_STOP_FRACTION`）→ 终止正在运行的 Gurobi 进程组，不再启动任何求解，报告用户。计量取法（`MEM_MEASURE=auto`，作业体与运行器记录实际取法）：
   - **首选：PBS 作业 cgroup 的匿名内存。** 作业体从 `/proc/self/cgroup` 解析本作业的 cgroup 路径（v2：`/sys/fs/cgroup/<path>/memory.stat` 的 `anon`；v1：`/sys/fs/cgroup/memory/<path>/memory.stat` 的 `total_rss`），把该目录作为 `CGROUP_ROOT` 传给运行器。不含可回收的文件缓存（第三批 S1 的教训）。不得把节点根 cgroup（含其他用户作业）当作本作业的计量——作业体核对路径非 `/`。
   - **不可见时：进程树 RSS 之和。** 作业 cgroup 的内存控制器不存在或不可读 → 运行器每 60 s 对进程 2 的进程组（`pgrep -g <pgid>`）求 `ps -o rss` 之和（`rss_gib_group`，与监控 CSV 同一列），对同一 80 % 线判定；STATUS 记 `mem_measure=rss`。
   - 两种计量都在 `MONITOR_<编号>.csv` 中逐分钟记录（`rss_gib_group`、`cgroup_anon_gib`、`cgroup_mem_limit_gib`）；**rss 模式下**（作业体未找到含本作业号的 cgroup）运行器不读任何 cgroup 文件，CSV 的两列 cgroup 值为空、STATUS 记 `cgroup_anon_source=none(rss_mode)`（审查 F-07 / N-03 的说明，2026-10-27；计量规则本身不变）。
2. **早期测速 → `STOP_SAFE:PROJECTION:<编号>`：** 沿用 B4P 3.4：第 20 次 barrier 迭代记录后，第 11–20 次迭代平均耗时 × 参考迭代数（F1 **450**、F2 **250**）+ 已用时间（自进程 2 启动）> 0.80 × TimeLimit = **691,200 s** → 终止该进程组，报告用户；只在首次满 20 次迭代时判定一次。
3. **墙钟：** 进程 2 到 871,200 s 终止整个进程组（TERM → 30 s → KILL）；回执不含终止条件的视为求解前回执（无返回解）。
4. **求解结果先落盘（A3.1）：** 进程 2 返回后先写 `split/SPLIT_SOLVE.json`（终止状态、目标值、迭代、Work、MaxMemUsed）与原始解数组，进程 3 再映射、导出、记账、门控；进程 3 任一步异常记入回执 `post_solve_errors`，不改变终止状态与"有返回解"的判定。
5. **不重试、不改参数、不热启动**（任何状态）。`SoftMemLimit` 不作为登记参数（B4P 3.5 第 4 项不变）。
6. **P1 探针不再使用：** 两作业方式下 F1、F2 各在自己的节点与 cgroup 内运行，`--only` 单运行模式不做 P1 探针、不写 `P1_DECISION.json`；B4P 3.2 第 1–2 项由第 4 节的许可间隔与 PBS 依赖取代。

### 6. 中断与重开

- 因计划维护、节点故障、PBS 终止（walltime）、内存或时限保护而中断的运行：**从头重开同一运行（参数不变）须用户明确授权**，登记为"资源原因的重新开始"（新的 `RUN_DIR`，报告中登记），不算重试。
- 续跑判定（同一 `RUN_DIR` 再次提交同一作业）：已结束的求解一律跳过（`SKIP_ENDED`）；"已开始未结束"的求解（`.started` 存在、`.ended` 不存在）→ `STOP_SAFE:INTERRUPTED_<编号>`，等用户；后处理各步只补缺失的输出。
- **维护重叠检查：** 提交前（步骤 E）必须确认 HPC 登录欢迎信息中没有与预计运行期（提交时刻起 F1 最长 255 h ≈ 10.6 天，F2 257 h）重叠的新维护通知；有就停下报告，不提交。已知维护窗口：2026-10-29 18:00 停止调度 → 10-31 06:00 关机 → 11-02 17:00 恢复；**F1 / F2 只在 11-02 17:00 之后提交**。
- `/hpctmp` 60 天未改动自动清除：运行目录、结果包都在 `/hpctmp/<用户>/hpr/`，结果包生成后尽快下载（第 8 节）；运行中的文件持续改动，不受清除影响。

### 7. 验收、分级与后处理

1. **验收 = GATES_V6 + C1（阈值不改）：** 与第三批 / 第四批相同：先用缺省参照给出临时 C1 判定与 GATES_V6 标签（`V6_ACCEPTANCE_PROVISIONAL.json`），F1、F2 账本齐备后生成本批参照 `BATCH_REFERENCE.json` 并重评（`grade_history` 保留）。
2. **分级与停批（B4P 3.5 沿用）：** `b4_batch4.py stop-class`：G2 不通过 → `STOP`；无返回解或 C1 (a) 不通过 → `UNUSABLE` 并 `STOP`（两个运行都是本批参照，没有"其余继续"）；只有 C1 (b)/(c) 不通过 → 不停。两作业方式下"停批 = 不再启动新的求解"体现在**共享运行目录**：F1 作业写出的 `STOP` / `STOP_SAFE` 会被尚未进入进程 2 的 F2 运行器看到并放弃启动（`NOT_STARTED_F2`）；已在求解的另一运行跑完并后处理。
3. **逐运行后处理在各自作业内完成**（`run_batch4.sh --only <编号>` 的 `post_run`）：违反量分析 → C1（临时参照）→ M12 分摊（`--register`）→ Owen 对偶形式审计 → GATES_V6（`--build-receipt`）→ 分级 → 导出 `export/<编号>/`（清洗后的日志，无 LP / 解数组）。每步 `timeout 10,800 s`，违反分析与 C1 失败后重做一次（M10A D2）；异常记 `POSTPROC_ERROR`，调度不变。
4. **批级作业**（`hpr_batch`，第 3 节；`POST_ONLY=1 bash run_batch4.sh`，无许可、无 `--auth`）在两作业都结束后：补做缺失的逐运行后处理步骤（幂等）→ `BATCH_REFERENCE.json` → C1 重评、Owen 重评、GATES_V6 终标签、分级 → **B6 = F2 − F1**（`gate_b6_cost`）与分国账本差 → **Owen 对偶形式分摊**（α 0.5 主值、α 区间、市场形式并列、燃料舱参与者；`m12_allocation.py benefit`）与受益、比例规则对照 → **与 365×24h v2 V1 / V2（DFX 阶段 4）及第三批 R3 / R4（R1 / R2 并列）的对比**（只描述，不判定；参照数值来自包内 `REFERENCE_VALUES.json`，不含任何结果文件原文）→ `BATCH4_SUMMARY.json / .md` → 导出 `export/batch/` → 结果包（light / full）。任一运行未验收：批级作业照常重评与汇总，结果包标记 `halted`，退出码 3。
5. 两作业未全部"落定"时批级作业拒绝运行（`not_ready`，退出码 2）——依赖 `afterany` 保证正常情况下不会发生。"落定" = 该运行已结束（`.ended`），**或**运行目录里有 `STOP` / `STOP_SAFE` 且该运行从未开始求解（无 `.started`，即因另一运行的停批而 `NOT_STARTED`）；此时批级作业照常重评、汇总并打出 `*_halted_*` 结果包（审查 F-06 的修订，2026-10-27）。已开始未结束的运行永远不算落定。

### 8. 结果回收

- 批级作业结束后 `/hpctmp/<用户>/hpr/runs/batch4/` 下有 `results_light_final_*.tar.gz`、`results_full_final_*.tar.gz` 与各自的 `.sha256`（停批时为 `*_halted_*`）。用户尽快下载到 `D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\`，本机核对 SHA256（PowerShell `Get-FileHash`）。
- LP / 解数组（约 2 × 7.6 GB）留在 `/hpctmp`（`ARRAYS_MANIFEST.json` 登记 SHA256），60 天后自动清除；需要时另行下载。

### 9. 测试作业（登记为测试，不属于正式运行）

| 作业 | 队列 / 资源 | walltime | 内容 | 判据 |
|---|---|---|---|---|
| **环境安装** `hpr_install` | `serial`，`ncpus=1:mem=8gb` | 02:00:00 | 计算节点上：Miniforge 到 `$HOME/miniforge3`（安装包由作业下载；受限时在登录节点 `curl -o` 下载后 `MINIFORGE_SH=` 传入）→ `env/install_env.sh`（第三批锁定 538 个 conda 包 + 2 个 PyPI 包，缓存在 `/hpctmp/<用户>/hpr/conda_pkgs_cache`）→ `env_check.py` → 解包代码到包目录 `./repo`（= `COMMIT`）→ 登录节点预检各节 | `INSTALL_STATUS.txt`：`ENV_CHECK:key_all_equal=true`、`REPO:<提交>`、`PREFLIGHT:exit=0` |
| **冒烟** `hpr_smoke56`（步骤 D） | `parallel`，`ncpus=17:mem=32gb` | 04:00:00 | 作业体依次以 `JOB_MODE=smoke56` 运行 F1 体、F2 体、批级体（同一代码路径）：`TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600`，标签 `SMOKE_TEST_ONLY`，运行目录 `runs/smoke56`；两次 Gurobi 会话串行（间隔 ≥ 330 s）；计算节点 `curl https://token.gurobi.com` 只记 HTTP 状态码 | `SMOKE_STATUS.txt`：两运行 optimal、ACCEPTED_LAYER2、后处理与批级 exit 0、`DONE`；目标值与本机 H4 演练值（一体化 340,661,983,874.5359 / 不互联 352,091,303,417.9458 EUR）相对偏差 ≤ 1e-6（跨机器只记录差异，不要求逐位） |
| **全尺寸 BUILD_ONLY** `hpr_build_only_f1`（步骤 D2，用户 2026-10-27 补充） | `parallel`，`ncpus=48:mem=300gb` | 02:30:00（估计 70 min × 2：预检 5 min + 进程 1 ≤ 60 min + 写入测速与清理 5 min） | `BUILD_ONLY=1 bash run_batch4.sh --only F1`（无 `--auth`、无许可）：只跑进程 1——完整 2920×3h v2 一体化网络的构建、LP 数组导出、LP 文件写出；运行目录 `runs/build_only_f1`（与正式目录隔离）；记录峰值内存（GNU time）、LP 文件字节数、构建秒数（`lp.build_seconds`）与写出秒数（`split.write_seconds`）、`/hpctmp` 写入速度（LP 字节 / 写出秒数，另加 1 GiB `dd` 顺序写测速）、cgroup 可见性；结束后删除 LP 文件 `split/problem.lp`（数组 `lp/` 保留，约 6.4 GB，60 天后清除） | `BUILD_ONLY_STATUS.txt`：`BUILD_CHECK_F1 passed`、`LP_DELETED`；参考预期：峰值 72–92 GiB（B4P 外推）、LP 5.1–5.4 GB、≤ 3,600 s。**结果只用于核对估计，不改变第 2–3 节的登记值**；峰值 > 150 GiB 或构建 > 3,600 s（超时安全停止）→ 先报告审阅端再做步骤 E；峰值 100–150 GiB → 批级作业（120 GiB）补做后处理（重建 LP，峰值与进程 1 同量级）可能不够，由审阅端提出是否提高 `hpr_batch` 内存（登记值变更，用户决定）后再做步骤 E（审查 F-16） |

- 三个测试作业都可在 2026-10-29 18:00 维护前完成，也可在 11-02 17:00 之后做（用户决定）。
- 测试作业用到的 `TRUNCATE` / `ALLOW_UNREGISTERED` / `BUILD_ONLY` 只在对应作业体内导出；**正式作业（`JOB_MODE=formal`）在这些开关残留、`--auth` 缺失、运行目录含测试残留（`.cond` 为 `build_only` / 标签 `SMOKE_TEST_ONLY`）时拒绝**（退出码 2，不写 STATUS）；`run_batch4.sh` 自身的拒绝（测试钩子、未登记时限、`--auth` 与无求解模式并存）保持不变。**BUILD_ONLY 作业体（`JOB_MODE=build_only`）在运行目录 `runs/build_only_f1` 已含上次运行时拒绝**（退出码 2，不写任何文件）：运行器会按上次的回执跳过构建，记录会重复旧数字；重跑 D2 须先把该目录移走（审查后自查 S-01，2026-10-27）。

### 10. 登记常数一览（检查单 H-P3 的比对清单）

| 常数 | 值 | `b4_batch4.py` | `run_batch4.sh` | 作业脚本 / `make_pbs.sh` | 预检 |
|---|---|---|---|---|---|
| 网络 SHA256 F1 / F2 | `08879f0b…` / `d90ca992…` | `REGISTERED_SHA` | 阶段 0 `base-check` | 包清单 | `networks` 节 |
| 网络字节 F1 / F2 | 63,873,447 / 63,202,193 | `REGISTERED_BYTES` | 同上 | — | 同上 |
| 构建提交 | `72083fde…` | `BUILD_COMMIT` | 同上 | — | 同上 |
| TimeLimit | 864,000 | `TIME_LIMIT_S` | `R_TL` | `JOB_TIME_LIMIT_S`（只用于记录） | `profile` 节 `R_TL` |
| 进程 2 墙钟 | 871,200 | `WALL_CAP_S` | `R_WALL` | — | — |
| 许可间隔 | 330 | `LICENCE_GAP_S` | `R_GAP` | — | — |
| 求解方式 | split | — | `R_MODE` | `SOLVE_MODE=split` | `code` 节 |
| 进程 1 / 3 超时 | 3,600 / 32,400 | — | `BUILD_TIMEOUT_S` / `ASSIGN_TIMEOUT_S` 缺省 | — | — |
| 后处理单步 / 打包超时 | 10,800 / 7,200 | — | `POST_TIMEOUT_S` / `PACK_TIMEOUT_S` 缺省 | — | — |
| 内存止损分数 | 0.80 | `MEMORY_STOP_FRACTION` | 缺省读取 | — | `code` 节 |
| 早期测速分数 / 迭代参考 | 0.80 / 450、250 | `PROJECTION_FRACTION`、`RUNS[*].iterations_reference` | `ITERS_REF` | — | `code` 节 |
| F2 等待 F1 启动上限 | 7,200 | `WAIT_START_MAX_S` | `WAIT_START_MAX_S` 缺省 | F2 作业 `WAIT_START_OF=F1` | — |
| PBS F1 | parallel / 48 / 300gb / 255:00:00 | `HPC_JOBS["F1"]` | — | `hpr_f1.pbs` | `resources` 节下限 = 申请值 |
| PBS F2 | parallel / 48 / 250gb / 257:00:00 | `HPC_JOBS["F2"]` | — | `hpr_f2.pbs` | 同上 |
| PBS 批级 | parallel / 12 / 120gb / 12:00:00 | `HPC_JOBS["batch"]` | — | `hpr_batch.pbs` | — |
| PBS 冒烟 | parallel / 17 / 32gb / 04:00:00 | `HPC_JOBS["smoke56"]` | — | `hpr_smoke56.pbs` | — |
| PBS BUILD_ONLY | parallel / 48 / 300gb / 02:30:00 | `HPC_JOBS["build_only_f1"]` | — | `hpr_build_only_f1.pbs` | — |
| PBS 安装 | serial / 1 / 8gb / 02:00:00 | `HPC_JOBS["install"]` | — | `hpr_install.pbs` | — |
| 后处理并存内存条件 | 100 GiB | — | `POST_MEM_NEED_GIB` 缺省 | — | — |

### 11. 路径约定（HPC）

| 内容 | 位置 |
|---|---|
| 包目录（= `PBS_O_WORKDIR`，作业从这里提交） | `/hpctmp/<用户>/hpr/` |
| 代码（预检 `sha` 节 / 安装作业解包） | `/hpctmp/<用户>/hpr/repo/`（`.package_commit` = `COMMIT`） |
| conda 环境 | `$HOME/miniforge3/envs/pypsa-earth`（家目录 20 GB 配额，约 3.3 GiB） |
| conda 包缓存、pip 缓存 | `/hpctmp/<用户>/hpr/conda_pkgs_cache`、`/hpctmp/<用户>/hpr/tmp` |
| 运行目录 | 正式 `runs/batch4/`；冒烟 `runs/smoke56/`；BUILD_ONLY `runs/build_only_f1/`（均在包目录下） |
| 结果包 | `runs/batch4/results_{light,full}_final_*.tar.gz`（+ `.sha256`） |
| 许可 | `$HOME/.gurobi/gurobi.lic`，`chmod 600`，用户自行放置；只经 `GRB_LICENSE_FILE` 引用 |
| 作业日志 | `/hpctmp/<用户>/hpr/<作业名>.o<作业序号>`（PBS 把 `-j oe` 的输出放回提交目录；作业脚本不设 `-o`） |

### 12. 由准备端确定、请审阅确认的取值（不在 B1–B4 内）

1. walltime 的构成（第 2 节）：F1 255 h、F2 257 h；逐运行后处理估计 65 min、作业体开销 30 min、F2 等待上限 2 h。
2. 批级作业资源：parallel 12 核 / 120 GB / 12 h（为可能的后处理补做留 ≥ 100 GiB）。
3. 冒烟作业资源：parallel 17 核 / 32 GB / 4 h；两运行串行。
4. 安装作业：serial 1 核 / 8 GB / 2 h；在计算节点安装（登录节点 30 min CPU 限制）。
5. 正式作业不做预检 `licence` 节（避免多一个 WLS 会话）；许可可用性由冒烟作业证明。
6. 停批信号跨作业共享（第 7 节第 2 项）：F1 的 `STOP` / `STOP_SAFE` 会阻止尚未开始求解的 F2。
7. HPC 冒烟与本机演练的目标值比较只记录相对偏差（跨机器浮点差异），不作为验收。
