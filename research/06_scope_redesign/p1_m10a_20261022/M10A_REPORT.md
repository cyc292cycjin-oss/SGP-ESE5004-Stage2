# M10A 报告：第三批部署包上云前独立审查（不连云、不上传、不调用 Gurobi、不求解）

**摘要（GO / NO-GO）**
1. **结论：GO（有条件）**——没有未关闭的 S1；S2 全部已修并有测试；条件是 v4 包的 `BUILD_ONLY` 干跑（约 19 分钟、约 9 GB 磁盘）因本机计算时间盒已用尽而未做（见第 5.3 节，一条命令即可补做），以及第 8 节两项需要用户决定。
2. **S1（已修）F1：** `run_batch3.sh` 的 `busy()` 把每个求解的 `/usr/bin/time` 包装进程与 python 进程各计一次（一个求解计为 2），第二条通道启动前要求"< 2"→ 正式运行在 R1 启动 1 秒后即 `STOP_SAFE:SOLVER_BUSY_R2`，整批在 R1 跑完后停下等人（本机用同名替身实证；v3 替身测试命令行不含 `s2_solve.py`，从未覆盖）。
3. **S2（已修）：** 后处理各步无超时（挂住即整批永不结束）；辅助进程无线程上限（云端 `nproc` 208、配额 25 核）；`TMPDIR` 未设（linopy 把每次求解的 LP 问题文件写到系统盘 `/tmp`，conda 包缓存也在系统盘）；测试 / 干跑开关残留无防护（v3 实测：残留替身开关时正式命令照常"运行"整批）。
4. **规则不变：** 第 3.3 节表格逐格行为修复前后相同（第 5.5 节）；`stop_class` 与停批 / 不可用判定代码未改；后处理崩溃只多了记录与超时保护；M12 / Owen / 去一国检查的异常修复前后都不停批（实证）。
5. **B3：** 后处理每运行约 6–8 分钟（S4N 云端实测 + 本机真实 365×24h 轻量步骤实测 + 外推），峰值约 11 GiB；两会话同时约 34 GiB，远低于 92 GiB。
6. **B4：** 新旧网络系数范围无任何一类扩大一个量级（RHS 下限 2e-4 → 1e-4）；R1 墙钟估计 **4.0–4.9 h**，上限超过 TimeLimit 的 75 %（4.5 h）→ 需要用户决定（第 8 节）。
7. **交付：** 修复提交 `03677123`（代码 + 测试 + `RUN_PLAN.md` v3），证据提交（本报告所在提交，SHA 见 `M10A_PROGRESS.md`）；**v4 包**：提交 `03677123`、24 个文件、148,603,385 B、`PACKAGE_MANIFEST.json` SHA256 `2489f123f1b85711af9823c98b9e464ed7c7e3afb717649d5eeee5481646e15d`；全量测试 611 passed / 67 skipped / 0 failed；分支推送结果见 `M10A_PROGRESS.md`（PR #49）。
8. **本机计算合计约 66 分钟**，超过指令的 1 小时时间盒（三轮测试链 42 min + B3/B4 测量 2 min + 打包与干跑 pre/post 8 min + 探测），故 `BUILD_ONLY` 干跑（约 19 min）停下待用户决定（第 5.3 节）。磁盘新增约 3 GB；未连云、未上传、未调用 Gurobi、未求解任何模型网络（玩具 LP 单元测试按指令照常运行）。

---

## 0. 范围、方法与核对

- 指令 `M10A_CLAUDE_CODE_INSTRUCTION.md` v2，SHA256 `d7db94976ea1cd24a33f75abc66cdf6add840c1ac2a605deb20672b06b17f98a`（与 `M10A_INSTRUCTION_SHA256.txt` 一致）。
- 工作位置核对（第 1 节）通过：worktree `/home/jin/wt_m10p_20261022`，分支 `codex/m10-batch3-20261022`，头 `d71f599e`（`git diff --stat e0527cec HEAD` 只涉及 `research/06_scope_redesign/p1_m10p_20261022/` 下报告与证据及 `research/STAGE2_PROJECT_LEDGER.md`），工作树干净，无其他进程使用该 worktree。被审包 v3 `work/p1_m10p_20261022/cloud_package_dist/`：24 个文件、148,587,335 B，`PACKAGE_MANIFEST.json` SHA256 `0fc6ab4f…1bc32`；包内 `run_batch3.sh` / `preflight.sh` / `pack_results.sh` 与仓库 `cloud_package/` 逐字节相同。
- 方法：逐行阅读 `run_batch3.sh`、`preflight.sh`、`pack_results.sh`、`env/install_env.sh`、`make_package.sh` 与 `m10_batch3_summary.py`、`gates_v6.py`（G1 / G2.1–2.3）、`s2_solve.py`（主流程、求解调用、异常处理）、`s4o_c1_precision.py`、`l23_violation_analysis.py`、`m12_allocation.py`、`m12_rhs_audit.py`、`m08a_variants.py` 的相关部分，以及环境中 linopy 0.5.5 的 `Model.solve` 分发逻辑；本机只读实证（假 `s2_solve.py` 按运行脚本同样方式启动后 `ps` 计数）；故障演练沿用 `tests/research/test_m10p_batch3.py` 的替身流水线（只补缺口）；B3 用 S4N 试点云端实测与本机真实 365×24h 数据；B4 用已有日志与 R1 的 LP 数组。
- 结论等级：VERIFIED（实测 / 日志 / 测试）、INFERENCE（外推）、PROPOSED（未执行）。

## 1. 发现清单

| 编号 | 级别 | 位置 | 现象 | 具体后果 | 处置 |
|---|---|---|---|---|---|
| F1 | **S1** | `run_batch3.sh:102` `busy()`；`:254` `[ "$(busy)" -lt 2 ]` | 求解以 `setsid /usr/bin/time -v env GRB_LICENSE_FILE=… python …/s2_solve.py …` 启动，`ps -eo cmd` 中 `time` 包装行与 python 行都含 `s2_solve.py`，一个求解计为 2（VERIFIED：本机假 `s2_solve.py` 实证 `busy()=2`；v3 脚本整批替身测试 1 s 后 `STOP_SAFE:SOLVER_BUSY_R2:2 s2_solve processes`） | 正式运行第 1 阶段 R2 永不启动；R1 跑完（约 4 h）并后处理后 `HALTED` 退出码 3 等人；若无人值守，租用时间全部浪费；若有人干预，也无规则允许"重启 R2"（续跑时 R2 无 `.started`，可重启，但需人工判断） | **已修**：只计 python 进程（排除 `time` / `setsid` / `env` 行）；替身求解器改以 `scripts_project/s2_solve.py` 同名包装启动，整批测试在 v3 脚本上失败、v4 上通过 |
| F2 | S2 | `run_batch3.sh` `post_run` / `regrade_all` / `batch_post` / `pack` | 后处理各步（违反分析、C1、M12、Owen、去一国检查、重评、批级步骤、打包）无超时；某步挂住（如 dask / netCDF 死锁、I/O 阻塞）则通道永不前进，`wait $a; wait $b` 永不返回 | 整批无限挂住，需人临时介入；若在第 2 阶段通道 B 挂住，通道 A 跑完后空等 | **已修**：每步 `timeout -k 30 $POST_TIMEOUT_S`（默认 1,800 s，打包 7,200 s；B3 实测单步 ≤ 150 s），超时 / 异常记 `POSTPROC_ERROR`（第 5.5 节） |
| F3 | S2（预防） | 所有辅助 Python 进程 | 未设 `OMP_NUM_THREADS` 等；S4N 实测云端 `nproc`=208（宿主机），容器配额 25 核；OpenBLAS / OpenMP 按 208 开线程 | 与同时运行的 24 线程求解抢核；实测影响有限（S4N 试点 VA / C1 在云端 CPU 100 %，即基本单线程），M12 / Owen 未在云端测过 | **已修**：辅助进程 `OMP / MKL / OPENBLAS / NUMEXPR` = 容器核数 − 正在运行的求解线程（≥ 1）；求解命令与环境不变（测试核对求解进程看到 `OMP_NUM_THREADS` 为空） |
| F4 | S2 | `run_batch3.sh`（`TMPDIR` 未设）、`env/install_env.sh`（conda 包缓存） | linopy 0.5.5 `Model.solve(io_api=None)` → `get_problem_file()` 用 `NamedTemporaryFile(dir=gettempdir())` 把每次求解的 LP 问题文件写到 `/tmp`（AutoDL 系统盘约 30 GB，conda 根也在其上），Gurobi 再读入（S4N 回执 solve_seconds 比 barrier 多 283 s 即此开销）；365×24h 两会话并行约数 GB；`conda create` 的包缓存默认在 conda 根 `pkgs/`（约 0.75 GB 压缩 + 3.3 GB 解压），跨文件系统到数据盘前缀时还要复制 | 系统盘写满 → LP 文件写失败 → `s2_solve.py` 异常 → 无返回解 → R1 / R2 停批（整批白跑）；安装阶段系统盘吃紧 | **已修**：`TMPDIR=runs/batch3/tmp`（数据盘）；`install_env.sh` 的 `CONDA_PKGS_DIRS` / `TMPDIR` / `PIP_CACHE_DIR` 指向包目录。这是求解进程环境唯一的新增变量（第 5.5 节说明） |
| F5 | S2 | `run_batch3.sh`、`preflight.sh` | 云端 shell 残留 `ALLOW_UNREGISTERED` / `BUILD_ONLY` / `POST_ONLY` / `*_CMD` / `FAKE_*` 时无防护：VERIFIED v3 脚本在残留替身开关 + 正式 `--auth` 下照常启动"整批"（替身求解，测试 900 s 超时才停）；`POST_ONLY=1` 残留 + `--auth` 则 30 分钟内"DONE"而无任何求解 | 跑完但结果不能用，或按未登记时限运行 | **已修**：`preflight.sh` 新增 `guards` 节（默认第一节，残留即 `PREFLIGHT FAILED`）；`run_batch3.sh` 正式运行（求解模式且无 `ALLOW_UNREGISTERED`）发现钩子即 `REFUSED`，无求解模式与 `--auth` 同时出现即 `REFUSED`；`START` 行记录 `hooks` / `allow_unregistered` / `tmpdir` / `post_timeout_s` |
| F6 | S3 | `run_batch3.sh:256`、`:324`（`export_run`） | 许可文件**路径**（非内容）出现在 `ps` 可见的命令行（`env GRB_LICENSE_FILE=…`）与 `solve.err` 的 "Command being timed" 行，后者被导出为 `export/<编号>/solve_time.txt` 并打包（S4N 试点导出同样如此）；`pack_results.sh` 的特征串扫描只找许可 ID、"registered…to"、WLS 访问 ID / 密钥三类字样，不含路径 | 路径不是秘密，无时间 / 结果后果 | 只列出。若希望连路径也不出包，`export_run` 中 `sed -E 's/GRB_LICENSE_FILE=[^ ]*/GRB_LICENSE_FILE=<path>/'` 一行即可（PROPOSED，未改） |
| F7 | S3（现状确认） | `post_run` → `gates_v6.py g2_3` | M12 分摊 / Owen 对偶形式 / 去一国右端项检查异常时，输出未登记进 `EXPORTS.json`，G2.3 只核对已登记导出 → 标签不受影响，不停批（VERIFIED：v4 替身测试继续到 `DONE`；v3 上 `M12_R2:exit=1` 后批次照常进入第 2 阶段，随后因 F1 在 R5 处 `STOP_SAFE:SOLVER_BUSY_R5`）；违反分析异常 → C1 输入缺失 → `PRECISION.json` `computable=False` → G1.a 不过 → R1 / R2 停批、R3–R11 不可用（规则 3.3"含 C1 不可计算"） | 后者按规则属"C1 (a) 不通过"；一次瞬时故障（如并发内存峰值）会按规则停批 | 规则所定，未改；v4 多了记录与超时；若希望 VA / C1 瞬时故障可补做后重判，需改规则 3.3（第 8 节提案 2） |
| F8 | S3 | 登记值：TimeLimit 21,600 s、墙钟 22,500 s | 墙钟余量 900 s 须覆盖 LP 构建（云端 118 s）+ LP 文件写 / 读（283 s）+ 求解后导出（约 100 s）：S4N 实测合计 498 s；新网络 +12 % 约 560 s | 若磁盘慢或导出变慢，到 TimeLimit 仍在导出的运行会被墙钟杀掉 → 回执非 post_solve → 无返回解（R1 / R2 停批） | 只列出（登记值不改）；余量约 1.6 倍 |
| F9 | S3 | `pack final` | 每次完成后再执行一次脚本（续跑 / 补做）都会再打一对包（完整包约 1.8 GB） | 磁盘、几分钟 | 只列出 |
| F10 | S3 | `preflight.sh` `resources` | 阈值 25 核 / 92 GiB / 60 GB 硬编码，无覆盖开关；`memory.max` 若为 92 × 10^9 B（85 GiB）即 `RESOURCE CHECK FAILED` | 需人工改脚本 | 只列出 |
| F11 | S3 | `RUN_PLAN.md` 3.7 | `STOP` / `STOP_SAFE` 之后再次执行同一命令：第 0 阶段正常，三个阶段全部因 `halted` 跳过，再打一次 `halted` 包后退出 3——按规则"等用户"，但计划未写用户决定后如何继续（如删除 `runs/batch3/STOP` 文件、或把中断运行目录改名后续跑） | 停批后的人工操作无文档 | 只列出；第 6 节给出建议写法 |
| F12 | S3 | `s2_solve.py` | 求解后导出阶段异常（如写 DUALS / 账本失败）→ 回执含 `failure`、无 `termination_condition` → 按"无返回解"处理（R1 / R2 停批） | 极小概率；S4N 试点同一导出路径在 365×24h 上成功 | 只列出 |
| F13 | — | B4 | R1 墙钟估计 4.0–4.9 h（INFERENCE），上限 > 4.5 h | 到 TimeLimit 无可用解即 R1 停批 | 第 8 节需要用户决定 |

B1 其余检查项（无发现，VERIFIED）：调度——每阶段两条通道各自依次，`phase_gap` 取所有 `.solve_end` 最大值与脚本启动时刻，通道内 `wait_gap` 用上一运行的 `.solve_end`；任一时刻至多两个会话、R3 / R4 同通道从不并行（整批测试逐时刻断言）；一条通道快另一条慢时快通道先结束、第 3 阶段等两条通道都结束（计划已注明）；许可令牌在 330 s 规则下任一时刻至多 2 个（两通道结束时刻错开时的交叉情形也成立）。墙钟终止——`setsid` 使 `time` 成为组长，`kill -TERM -- -pgid` 覆盖 `time` 与 python（Gurobi 线程在 python 进程内），GRACE 后 `KILL`，`wait` 后再等组退出 ≤ 120 s；替身忽略 TERM 的演练通过。续跑——`.ended` 跳过、`.started` 无 `.ended` 安全停止、各后处理步幂等、`POST_ONLY` 无求解；完成后再执行 11 个 `SKIP_ENDED`。cgroup v1 / v2——`cpu.max` / `cfs_quota`、`memory.max` / `limit_in_bytes` 两套都读，读不到退回宿主机值且监控不中断。时间——全部 UTC，跨日无影响。许可内容——`solve.log` / `gurobi.linopy.log` 不出包，导出文件经 `SCRUB` 过滤，`pack_results.sh` 在 `export/` 全树（文本文件）扫描特征串，`-I` 跳过二进制（`.nc` / `.npy` 不含许可行）。

## 2. 故障演练（B2）

已有测试 `test_m10p_batch3.py`（v3：17 项）确为端到端驱动真实的 `run_batch3.sh`（替身只替换求解器与后处理脚本；GATES_V6、`stop-class`、`level2`、汇总、打包为真实代码），但替身求解器命令行不含 `s2_solve.py`，`busy()` 从未被真正检查（F1）。v4 测试 28 项（`tests/research/test_m10p_batch3.py`），所有场景经 `s2_solve.py` 同名包装启动。

| 场景 | 已有覆盖（v3） | 预期（RUN_PLAN 第 3 节） | 实际（v4） | 一致 |
|---|---|---|---|---|
| (a) 全部成功 | 已覆盖 `test_full_batch_pairing_order_reference_and_resume` | `DONE`、退出码 0、批级后处理与打包完整 | 11 次求解各一次、配对 / 顺序 / 间隔 / 至多两会话断言全过，`DONE`，退出 0，两对包；**v3 脚本上同一测试 1 s 后 `STOP_SAFE:SOLVER_BUSY_R2`、退出 3** | 是（v3 否） |
| (b) R1 无返回解 | 部分（墙钟杀 R1） | 停批；另一通道当前求解跑完并后处理；汇总与打包照常；退出码 3 | 新增参数化 `R1-nosol`：`STOP_NOT_ACCEPTED:R1:nosol`，R2（正在跑）跑完、`V6_ACCEPTANCE.json` 与导出存在，`BATCH3_SUMMARY.json` + `halted` 包，退出 3，无 R3 | 是 |
| (c) R2 有解但 C1 (a) 不通过 | 已覆盖（参数化 R2） | 停批 | `STOP_NOT_ACCEPTED:R2:c1a`，退出 3 | 是 |
| (d) R5 无返回解 | 已覆盖 `…unusable_runs_and_the_batch_goes_on` | 不可用、继续；去一国检查排除 R5；`STATUS.txt` 正确 | `UNUSABLE:R5:nosol`，`M12_LOO … unusable_left_out=R5`，`DONE` 退出 0 | 是 |
| (e) R3 有解但 C1 (a) 不通过 | 部分（R3 nosol） | 不可用；第二级不通过；第四批档案 = A | 新增：`UNUSABLE:R3:c1a`，`LEVEL2` 候选 a=False，`PROFILE_CHOICE` formal_barrier，退出 0 | 是 |
| (f) 变体 / 基础网络 SHA256 不符 | 变体已覆盖；基础网络未覆盖 | `STOP_SAFE`，不启动任何求解 | 变体：`STOP_SAFE:VARIANT_SHA256_R9`；新增基础网络：`STOP_SAFE:BASE_NETWORK_SHA256:DIFFERENT:integrated_365_24h`，无 `CALLS.txt`，汇总 + `halted_phase0` 包，退出 3 | 是 |
| (g) 墙钟终止且替身忽略 TERM | 未覆盖（替身默认响应 TERM） | KILL 后进程组全部退出才导出；分类正确 | 新增：`KILLED_3S_R1`、`KILL9_R1:…after_grace_2s`，无 `GROUP_SURVIVED`，`.cond=killed_pre_solve`，`.ended` 与导出存在，`STOP_NOT_ACCEPTED:R1:nosol`，组内无残留进程；R2 跑完并后处理 | 是 |
| (h) 第 2 阶段中途杀脚本再重启 | 部分（合成 `.started` 无 `.ended`） | `STOP_SAFE`，不重跑 | `STOP_SAFE:INTERRUPTED_R1`，无求解（未真正杀运行中的脚本：被 `setsid` 脱离的求解会继续，重启时 `prepare` 的 `busy()` 会先 `STOP_SAFE:SOLVER_PROCESS_RUNNING_AT_START`，与场景 (l) 同路径） | 是（部分） |
| (i) 全部完成后再执行；`POST_ONLY=1` | 已覆盖 | 跳过求解；输出不变 | 11 个 `SKIP_ENDED`、调用数不变；`POST_ONLY` 无求解、`PREPARE:skipped`；新增：崩溃后 `POST_ONLY=1` 补齐缺失输出 | 是 |
| (j) R1 的 M12、R7 的去一国检查抛异常 | 未覆盖 | 记录现状；修复后按 B5 第 2 项 | 新增（R2 的 M12 + R7 的去一国 RHS 检查抛异常）：`POSTPROC_ERROR:R2:m12:exit=1`、`POSTPROC_ERROR:R7:rhs_loo:exit=1`，标签仍 ACCEPTED_LAYER2，`M12_BENEFIT:not_computable`，`DONE` 退出 0，汇总列出；**v3 现状：M12 异常只留 `M12_R2:exit=1` 一行、不停批，批次进入第 2 阶段后因 F1 在 R5 处 `STOP_SAFE:SOLVER_BUSY_R5`**；挂住：M12 挂住 → `exit=124:timeout_3s` 后继续；违反分析挂住 → C1 不可计算 → `STOP_NOT_ACCEPTED:R2:c1a`（规则） | 是 |
| (k) 容器核数 < 24、< 16 | < 24 已覆盖；< 16 未覆盖 | 通道正确合并 | `CORES=20`：第 2 阶段一条通道；新增 `CORES=12`：三阶段都一条通道、11 次求解互不重叠、线程预算 12 | 是 |
| (l) 已有外部 `s2_solve.py` 进程 | 未覆盖 | 拒绝启动或安全停止 | 新增：`STOP_SAFE:SOLVER_PROCESS_RUNNING_AT_START:1 s2_solve`，无求解，退出 3（v3 同样通过） | 是 |
| (m) 残留 `ALLOW_UNREGISTERED` 等开关 | 未覆盖 | 修复后：预检失败或正式运行拒绝 | 新增：`PREFLIGHT_ONLY=guards` 对 5 种残留各 `PREFLIGHT FAILED`、干净 shell `OK`；正式运行残留钩子 `REFUSED … test hooks`，`BUILD_ONLY` / `POST_ONLY` + `--auth` `REFUSED`；**v3：预检无此节（失败），正式命令照常启动** | 是 |
| 线程预算 / TMPDIR | 未覆盖 | 辅助进程有预算，求解进程不变 | R1 的 VA 在 R2 运行时 `omp=17`，R2 的 VA `omp=25`；11 次求解看到 `omp=None`、`tmp=<运行目录>/tmp` | 是 |

启动 / 结束时间核对：整批测试用替身记录的起止时刻断言任一时刻 ≤ 2 个会话、线程之和 ≤ 24、通道内与阶段间 ≥ 间隔（1 s 测试值）。

## 3. 后处理资源（B3）

| 步骤 | 56×3h 本机（M10P 演练） | 365×24h 实测 | 数据来源 | 云端新网络估计（INFERENCE） |
|---|---|---|---|---|
| 违反分析 `l23_violation_analysis.py` | 19–23 s / 2.1–2.4 GB | **105 s / 9.34 GB**（旧网络，CPU 100 %） | S4N 试点云端 `va_err_tail.txt`（8470Q） | ~120 s / ~10.5 GB（行数 +11.5 %） |
| C1 `s4o_c1_precision.py run` | 16–19 s / 2.1–2.4 GB | **72 s / 9.34 GB**（旧网络） | S4N 试点云端 `c1_err_tail.txt` | ~80 s / ~10.5 GB |
| M12 分摊 `m12_allocation.py run` | 3 s | **6.5 s / 0.80 GB**（S4N 求解后网络，本机） | 本次实测 `/home/jin/m10a_b3/alloc.err` | ~10 s / ~1 GB |
| Owen 对偶形式 `m12_rhs_audit.py audit` | 17–21 s / 1.9–2.3 GB | **54 s / 8.09 GiB**（`--duals` 模式，旧网络，本机）；新网络仅构建 65 s / 9.98 GiB（M12 S8） | 本次实测 `owen.err`；M12 报告 | ~120–150 s / ~10.5 GB（云端单线程慢于本机，r≈0.74） |
| 去一国右端项检查 `loo` | < 1 s | — | CSV 比较 | 秒级 |
| GATES_V6 `accept` | < 1 s | **0.09 s / 21 MB**（S4N 导出） | 本次实测 | 秒级 |
| 导出 `export_run` | 秒级 | 复制约 256 MB | S4N 导出大小 | ~5 s |
| 重评 / 分类 | 秒级 | — | — | 秒级 |
| 打包 `pack_results.sh` | 1.1 s | **6.6 s** / 256 MB 单运行导出（完整包 159 MB） | 本次实测 | 11 运行约 2.8 GB → 打包 ~75 s + LP / 解数组 SHA256 清单（约 10 GB）~1–2 min，≤ 5 min |
| 批级（去一国、受益、第二级、汇总） | 秒级 | — | JSON 读写 | 秒级 |

判断：每次后处理约 **6–8 分钟**（含两次重建模型），低于 `RUN_PLAN.md` 第 4 节的约 0.3 h（含许可间隔）；峰值约 11 GiB。内存：后处理与另一通道的求解同时 ≈ 11 + 15–17 GiB；两会话同时 ≈ 32–34 GiB（T16 会话可能略高）；均远低于 92 GiB。本机未在 365×24h 上运行违反分析 / C1 / 新网络 Owen（需 ≥ 10.5 GB，WSL 10 GiB），用云端实测与规模比外推（INFERENCE）。无限期挂住的保护见 F2。

## 4. 数值条件与时限（B4）

**系数范围（口径：Gurobi 日志 = 研究缩放之后；导出 LP 数组 = `ORIGINAL_UNSCALED`，缩放之前；两者不能直接互比，各自口径内比较）**

| 口径 / 网络 | 矩阵 | 目标 | 边界 | 右端项 |
|---|---|---|---|---|
| 日志，旧网络 56×3h（S4N-1 / S4N 探针） | [2e-4, 2e+2] | [2e+0, 1e+6] | [8e-1, 2e+5] | [2e-4, 6e+8] |
| 日志，新网络 56×3h（M08b 冒烟一体化 / 不互联；M12b 去 VN / TH / LA） | [2e-4, 2e+2] | [2e+0, 1e+6] | [8e-1, 2e+5] | **[1e-4, 6e+8]** |
| 日志，旧网络 365×24h（S4N 试点） | [2e-4, 3e+1] | [2e-1, 1e+6] | [3e-1, 1e+5] | [2e-4, 6e+8] |
| 数组，旧网络 56×3h（S4N-1 `lp/`） | [2.4e-4, 3.4e+3] | [1.56, 1.10e+6] | [0.76, 1.52e+5] | [2.0e-4, 2.58e+9] |
| 数组，新网络 56×3h（M08b 冒烟 `lp/`） | [2.4e-4, 3.4e+3] | [1.56, 1.05e+6] | [0.76, 1.52e+5] | [1.4e-4, 2.58e+9] |
| 数组，新网络 365×24h（M10P R1 `lp/`） | [2.4e-4, 3.4e+3] | [0.24, 1.05e+6] | [0.31, 1.19e+5] | [1.4e-4, 2.58e+9] |

- 新旧网络同口径对比：矩阵、边界完全相同；目标上限略小；右端项下限 2e-4 → 1.4e-4（日志口径 2e-4 → 1e-4），**比值扩大 ×1.5，不到一个数量级**。
- 365×24h 对 56×3h 的目标 / 边界下限缩小（1.56 → 0.24、0.76 → 0.31）来自时段权重（56×3h 代表权重 156.4 对逐小时权重），旧网络日志口径同样出现（目标 2e+0 → 2e-1）；据此推断新网络 365×24h 日志口径范围与旧网络相同，只有右端项下限 1e-4（INFERENCE）。

**难度与时长（同机同档案 A、Threads 8）**

| 运行 | 行 / 非零元 | 迭代 | 求解 s | 每迭代 s | work units |
|---|---|---|---|---|---|
| 旧 56×3h 一体化（S4N-1，本机） | 1,393,079 / 3,209,723 | 141 | 216.7 | 1.54 | 407.7 |
| 新 56×3h 一体化（M08b 冒烟，本机） | 1,553,068 / 3,621,898 | 129 | 218.8 | 1.70 | 428.4 |
| 新 56×3h 不互联 | 1,499,494 / 3,455,872 | 152 | 227.6 | 1.50 | 456.7 |
| 新 56×3h 去 VN / TH / LA（M12b） | 1.40–1.44 M / 3.26–3.35 M | 181 / 161 / 148 | 275 / 239 / 217 | 1.52 / 1.48 / 1.47 | 560 / 476 / 427 |
| 旧 365×24h 一体化（S4N 试点，8470Q 云端） | 9,017,345 / 20,952,716 | 408（第 156 次无提示重启） | 11,470 | 28.1 | 7,034 |
| 旧 365×24h 不互联（S4O-6，8481C） | 8,671,148 / 19,874,213 | 287（suboptimal） | 2,202 | 7.7 | 2,178 |
| 新 365×24h 一体化（R1，仅构建） | 10,052,113 / 23,634,770（+11.5 % / +12.8 %） | — | — | — | — |

估计（INFERENCE）：新网络每迭代耗时约 +10–15 %（56×3h 实测 +10 %，规模 +12 %），迭代数相近。R1 ≈ 3.3 h × 1.10–1.15 × 1.1–1.3（两会话并行）= **4.0–4.9 h**；R5–R7（去一国，一体化）同量级；R10 同量级；R2 ≈ 0.6 h × 1.1–1.3 ≈ **0.8–1.0 h**；R8 / R9 / R11 约 0.8–1.2 h；R3 / R4（1e-6、16 线程）短于 R1 / R2。合计约 20–25 h（`RUN_PLAN.md` v3 第 4 节）。

**判据：** 系数跨度无一类扩大一个量级 → 不触发；R1 估计上限 4.9 h > 4.5 h → **写入"需要用户决定"（第 8 节第 1 项）**。未做 `--stop-before-solve` 构建（已有 R1 数组；不互联 365×24h 的行数 9,705,916 已由 M12 S8 给出）。

## 5. 修复（B5）

### 5.1 提交与测试

- 修复提交 `03677123abf41c91b95d5bcdefa3bff9b25a05d9`（`codex/m10-batch3-20261022`，基于 `d71f599e`；7 个文件，+335 / −67 行）：`cloud_package/run_batch3.sh`、`preflight.sh`、`env/install_env.sh`、`scripts_project/m10_batch3_summary.py`、`tests/research/fixtures/m10p_fake_pipeline.py`、`tests/research/test_m10p_batch3.py`、`RUN_PLAN.md` v3（第 10 节改动说明，第 3 节一字未改）。
- 证据提交（本报告所在提交）：`research/06_scope_redesign/p1_m10a_20261022/`（报告、证据 JSON、进度、`evidence/`）与 `p1_m10p_20261022/evidence/m10a_v4/`（v4 包清单与比对）。
- 测试：`test_m10p_batch3.py` 28 项全过（v3 17 项 + 11 项新增）；全量 `tests/research` **611 passed / 67 skipped / 0 failed**（593 s，`evidence/tests/TESTS_full3.log`；M10P 基线 600 passed / 67 skipped + 11 项新增；玩具 LP 测试按指令照常运行）。此前两轮全量各有 1–4 个失败，全部是新测试自身的断言或计时余量问题（`TESTS_full2.log`：R6 停批场景中通道 A 的 R4 在 R6 停批前未来得及启动——`wait_gap` 每 5 s 轮询，已把该场景 R5 的替身耗时加长；`TESTS_m10p.log`：4 处断言写法），代码未因此改动。修复前对照：v3 脚本上整批测试 `STOP_SAFE:SOLVER_BUSY_R2`、崩溃场景无记录继续、残留钩子照常启动、预检无 `guards` 节（`evidence/tests/TESTS_before.log`）。
- 未改：求解档案、TimeLimit / 墙钟 / 许可间隔登记值、网络、变体、成本表、验收阈值、停批分级规则、运行顺序、`s2_solve.py`、`gates_v6.py`、`stop_class`。

### 5.2 v4 包

`make_package.sh` 在提交 `03677123` 的干净工作树上生成（99 s；构建输入检查 OK——6 个改动文件都不在 `s2_network.py` 导入闭包内；7 个变体两遍逐字节相同）：

| 项 | v3 | v4 |
|---|---|---|
| 提交 | `e0527cecd8ccc798b3b3e8f54363d76ced417592` | `03677123abf41c91b95d5bcdefa3bff9b25a05d9` |
| 文件数 / 字节 | 24 / 148,587,335 | **24 / 148,603,385** |
| `PACKAGE_MANIFEST.json` SHA256 | `0fc6ab4f…1bc32` | `2489f123f1b85711af9823c98b9e464ed7c7e3afb717649d5eeee5481646e15d` |
| `SHA256SUMS` SHA256 | `6f74f40e…1ea1` | `b151c90d3f85a497945f7504d16ea2c3ffe5e8ef7b242e1b355bb5e38e9d6050` |
| 代码归档 | `code_e0527cec.tar.gz`（82,477,631 B） | `code_03677123.tar.gz` |
| 与 v3 逐字节相同（VERIFIED，`evidence/package_v4/PACKAGE_V4_VS_V3.json`） | — | `networks/integrated_365_24h_unsolved.nc` `75704334…`、`disconnected_365_24h_unsolved.nc` `888a009b…`、两份 `*_BUILD_RECEIPT.json`（`52136599…` / `075d0207…`）、两份成本表（`7cee9c1a…`）、`EXPECTED_VARIANTS.json`（`d7ed165f…`） |
| 相对 v3 变化的条目 | — | `run_batch3.sh`、`preflight.sh`、`env/install_env.sh`、`RUN_PLAN.md`、`COMMIT`、`BUILD_INPUT_CHANGES.json`、代码归档（文件名随提交变化）；其余条目 SHA256 相同 |

v3 保留为 `work/p1_m10p_20261022/cloud_package_dist_v3_e0527cec/`；v4 在 `cloud_package_dist/`。上传时间与 v3 相同量级（149 MB：36 KB/s 约 1.15 h）。

### 5.3 干跑（与 M10P 补充 01 相同的步骤）

在 `/home/jin/m10a_dry/pkg`（v4 包的副本，云端目录布局）上，证据在 `evidence/dryrun_v4/`：

1. **预检（pre，VERIFIED）：** `guards` 节干净 shell → `PREFLIGHT OK`；同一节在 `POST_ONLY=1` 残留时 → `SET IN THIS SHELL … POST_ONLY` / `PREFLIGHT FAILED`（反例）；`sha`（22 个文件 OK，代码解包 1,432 个文件、无 `research/`）、`networks`（`all_equal`，7 个变体期望）、`env`（284 / 284，关键包相同）、`profile`（两档案、Threads 8 / 16、内点门槛路径）、`code`（模块导入、11 运行 / 3 阶段）、`tools`（含新增的 `timeout`）全部通过；`resources` 节在本机如预期 `RESOURCE CHECK FAILED`（16 核 / 11 GiB，仅作信息）。
2. **变体在线程预算环境下复现（VERIFIED，替代 `BUILD_ONLY` 第 0 阶段的核对）：** 用 `run_batch3.sh` `aux()` 的环境（`OMP/MKL/OPENBLAS/NUMEXPR=17`、`TMPDIR` 设定、`timeout`）由 v4 包网络重新生成 7 个变体，`variants-check` 对 `EXPECTED_VARIANTS.json` **7/7 `equal`**（34 s，`evidence/VARIANTS_UNDER_THREAD_BUDGET.txt`）。
3. **`POST_ONLY=1` 后处理演练（VERIFIED）：** R1 / R2 ← M08b 冒烟 s01，R5 / R6 / R7 ← M12b 去 VN / TH / LA（56×3h），运行脚本 v4，`RUNNER_EXIT 0`，339 s（M10P S01-3：320 s）；`START` 行记录 `tmpdir=…/post_smoke/tmp:post_timeout_s=1800:allow_unregistered=1:hooks=TRUNCATE`（干跑态）；每运行 5 步 `exit=0`（违反分析 20–26 s / 2.1–2.4 GB、C1 17–20 s、Owen 18–22 s，与 M10P 演练相同量级，线程预算未改变耗时），临时判定 → 本批参照重评（`grade_history` 1 次），去一国右端项检查 3/3 通过，去一国检查 3/3 通过，B6 9.8985 bn，`PROFILE_CHOICE` formal_barrier（R3 / R4 缺），`DONE`，两对包（完整 140.7 MB）。与 M12b 证据表比较 `agree: true`，**最大差 0.0 EUR**（`post_smoke/POST_SMOKE_VS_M12B.json`）。无 `POSTPROC_ERROR`。
4. **`BUILD_ONLY` 干跑（R1–R11 构建到求解前退出）：未做**——本机计算已约 66 分钟，超过指令 1 小时时间盒，按原则 7 停下报告。补做命令：`STEP=build bash /home/jin/m10a_dryrun.sh`（约 19 分钟，峰值 10 GiB，约 9 GB 磁盘；证据自动落到 `evidence/dryrun_v4/build_only/`）。差别评估（INFERENCE）：`s2_solve.py` 与网络未改，构建路径与 v3 干跑相同；v4 改动触及的只有第 0 阶段（第 2 项已单独核对）和 `build-check` 的 `aux` 包装（替身测试 `test_build_only_dry_run_no_solver_and_licence_tripwire` 通过）。

### 5.4 M10 执行指令需要更新的值

见第 6 节。

### 5.5 规则等价证明：第 3.3 节表格逐格对照（修复前 v3 / 修复后 v4 / 规则）

分类代码 `m10_batch3_summary.stop_class()` 与运行脚本的 `stop_check()` 未改（`git diff` 只有 `postproc_errors` / 汇总 / markdown 三处）；以下每格有替身测试（v3 的 17 项在 M10P 证据日志中通过，v4 的 28 项本次通过）：

| 情况 | R1、R2（v3 → v4） | R3–R11（v3 → v4） | 规则 | 测试 |
|---|---|---|---|---|
| G2 不通过（有解） | 停批 → 停批 | 停批 → 停批 | 停批 | R7 `g2`（参数化） |
| G2 不通过（无解；只核输入 SHA256 与配置子集） | 停批 → 停批 | 停批 → 停批 | 停批 | R6 `g2`（参数化）；`test_stop_class_cases` |
| 无返回解 | 停批 → 停批 | 不可用 → 不可用 | 停批 / 不可用 | R1 墙钟杀、R1 nosol、R3 / R5 nosol |
| 有解但 C1 (a) 不通过（含 C1 不可计算） | 停批 → 停批 | 不可用 → 不可用 | 停批 / 不可用 | R2 `c1a`、R8 / R3 `c1a`；违反分析挂住 → C1 不可计算 → R2 停批 |
| 只有 C1 (b) / (c) 不通过 | 不停 → 不停 | 不停 → 不停 | 不停 | R2 临时 (b) 不过、R8 |
| 验收文件缺失 / 分类不可读 | 停批 → 停批 | 停批 → 停批 | 停批 | `test_stop_class_cases`（缺 `V6_ACCEPTANCE.json` → g2） |
| 停批时另一通道当前求解 | 跑完并后处理 → 同 | 同 | 跑完并后处理 | R1 nosol（R2 跑完）、R6（R4）、R7（R8） |
| M12 / Owen / 去一国检查异常 | 不影响标签、不停 → 同 + 记录 `POSTPROC_ERROR` | 同 | （规则未涉及；G2.3 只核已登记导出） | (j) 测试 v4；v3 日志 `M12_R2:exit=1` 后继续（直至 F1 的 `SOLVER_BUSY_R5`） |
| 后处理挂住 | 永不前进 → 超时后按上两行处理 | 同 | （规则未涉及） | (j) 挂住测试 |

求解命令与环境：`cmd=($SOLVE_CMD --repo … --costs-table …)` 与 `exec setsid /usr/bin/time -v env GRB_LICENSE_FILE="$LIC" "${cmd[@]}"` 两行未改；环境唯一新增 `TMPDIR`（F4；替身记录 `tmp=<运行目录>/tmp`、`omp=None`）。线程预算只加在 `aux()` / `step()` 包装的辅助命令上。

## 6. M10 执行指令需要更新的值

| 项 | v3（M10P 补充 01） | v4（本次） |
|---|---|---|
| 包提交 `COMMIT` | `e0527cecd8ccc798b3b3e8f54363d76ced417592` | `03677123abf41c91b95d5bcdefa3bff9b25a05d9` |
| 文件数 / 字节 | 24 / 148,587,335 | 24 / 148,603,385 |
| `PACKAGE_MANIFEST.json` SHA256 | `0fc6ab4f5a9281679738f45972affbc6410acab6b9d6c2a778fd255138e1bc32` | `2489f123f1b85711af9823c98b9e464ed7c7e3afb717649d5eeee5481646e15d` |
| `SHA256SUMS` SHA256 | `6f74f40e90a9244c7afaaad032d8f2987f59f01393a89567f5f0a47f272a1ea1` | `b151c90d3f85a497945f7504d16ea2c3ffe5e8ef7b242e1b355bb5e38e9d6050` |
| 代码归档 | `code_e0527cec.tar.gz` | `code_03677123.tar.gz` |
| 预检命令 | `PY=… GRB_LICENSE_FILE=… bash preflight.sh` | 同，但**必须在将运行批次的同一个 tmux shell 中执行**（新 `guards` 节检查该 shell 的残留开关）；工具要求增加 `timeout`（coreutils） |
| 运行命令 | `PY=… GRB_LICENSE_FILE=… bash run_batch3.sh --auth "<原文>"` | 不变 |
| 补做后处理 | `POST_ONLY=1 PY=… bash run_batch3.sh` | 不变，**不得带 `--auth`**（否则拒绝） |
| 新环境变量（可不设） | — | `POST_TIMEOUT_S`（默认 1,800 s）、`PACK_TIMEOUT_S`（7,200 s）；`TMPDIR` 由脚本设为 `runs/batch3/tmp` |
| 环境安装 | `bash env/install_env.sh` | 不变；包缓存与临时文件落在 `<包目录>/conda_pkgs_cache`、`<包目录>/tmp`（数据盘）；可按需 `CONDA_PKGS_DIRS=…` 覆盖 |
| 状态行 | — | `START:…:tmpdir=…:post_timeout_s=…:allow_unregistered=0:hooks=`；`POSTPROC_ERROR:<编号>:<步骤>:exit=…` 只记录不停批；`NOTE:ALLOW_UNREGISTERED=1 in solve mode` 出现即为测试态（正式运行不应出现） |
| 停批后的人工操作（建议写入执行指令，PROPOSED） | — | 用户决定继续时：`STOP_NOT_ACCEPTED` → 删除 `runs/batch3/STOP` 后同一命令续跑（已结束运行不重跑，被停的运行按规则不重试）；`STOP_SAFE:INTERRUPTED_<编号>` → 用户决定后把该运行目录改名保留再续跑（视为新的一次，需登记） |

## 7. 剩余风险（本机无法排除）与应对

1. **真实求解时长（F13）：** R1 / R5–R7 / R10 估计 4.0–4.9 h，到 6 h TimeLimit 无可用解即停批（R1）或不可用（其他）；应对见第 8 节。
2. **云端网速：** 上传约 149 MB（36 KB/s 约 1.15 h）、下载完整包约 1.8 GB（4 MB/s 约 8 分钟，0.3 MB/s 约 1.7 h）；与 v3 相同。
3. **许可令牌保留时间：** 330 s 间隔按"≥ 5 分钟"规则留 30 s 余量（S4O-6 实践通过）；若 WLS 侧保留更久，第 2 阶段 R4 / R6 启动可能被拒 → 无返回解 → 不可用（R3–R11）。
4. **墙钟余量（F8）：** 900 s 对实测开销约 500–560 s；磁盘异常慢时有风险。
5. **cgroup 读取：** 若实例把配额放在容器不可见的父 cgroup，预检与调度退回宿主机值（208 核 / 1 TiB）——调度仍是两条通道（不受影响），只是预检失去配额核对；可在执行指令中要求人工核对 `nproc` 与 `cpu.max`。
6. **`BUILD_ONLY` 干跑未在 v4 上重做**（第 5.3 节）：变体在线程预算环境下的复现已单独核对，`POST_ONLY` 演练已做；差别只剩 R1–R11 的 `--stop-before-solve` 构建路径（`s2_solve.py` 未改，`aux` 包装只影响 `build-check`），建议补做。

## 8. 需要用户决定的事项

1. **R1（及 R5–R7、R10）时长估计上限 4.9 h > 4.5 h（TimeLimit 的 75 %）。** 可选：(a) 按登记值照跑，接受 R1 到时限无可用解则整批停下的风险（INFERENCE 概率不高：中值估计约 4.4 h）；(b) 在上云前以补充决定把 365×24h 的 TimeLimit / 墙钟改为例如 28,800 / 29,700 s（第 3.1 节登记值变更，需登记理由；代码只改 `R_TL` / `R_WALL` 两个常数与计划）；(c) 先只跑第 1 阶段（R1 | R2）观察后再决定——现脚本无"只跑一阶段"开关，需加一个登记过的 `STOP_AFTER_PHASE=1`（PROPOSED）。本报告未改任何登记值。
2. **`BUILD_ONLY` 干跑补做**（约 19 分钟、约 9 GB）：`STEP=build bash /home/jin/m10a_dryrun.sh`（证据落到 `work/p1_m10a_20261022/evidence/dryrun_v4/`）。
3. （提案，非必需）F7：若希望违反分析 / C1 的瞬时故障（非求解问题）可在 `POST_ONLY=1` 补做后重判而不是立即按"C1 不可计算"停批，需修改规则 3.3；本次未改。
4. （提案，非必需）F6：`solve_time.txt` 中的许可**路径**脱敏；F11：停批后人工操作写入执行指令。

## 9. 本机计算、磁盘与边界

- 未连云、未上传、未调用 Gurobi、未求解任何模型网络；玩具 LP 单元测试（scipy / HiGHS）按指令照常运行于全量测试中。
- 本机计算（含测试等待）：探测与 B3/B4 约 4 min；测试链一（修复前 15.5 min + 修复后 7 min + 全量 9.6 min）；测试链二（4 项 1 min + 全量 9.4 min）；测试链三（停批场景 2 次 3.4 min + 全量 9.9 min）；打包 1.7 min、变体复现 0.6 min、干跑 pre 约 1 min、干跑 post 5.7 min。合计约 66 分钟（超过 1 小时时间盒，`BUILD_ONLY` 干跑未做，第 5.3 节）。
- 磁盘新增：`/home/jin/m10a_b3`（642 MB）、`/home/jin/m10a_varcheck`（202 MB）、`/home/jin/m10a_dry`（2.1 GB）、v4 包（149 MB）；`cloud_package_dist` v3 改名保留（`cloud_package_dist_v3_e0527cec/`）。本步临时脚本在 `/home/jin/m10a_*.sh`（副本见 `scripts/`）。
- 证据：`work/p1_m10a_20261022/M10A_EVIDENCE.json`、`evidence/`（测试日志、B3/B4 原始输出、包比对、干跑）。
