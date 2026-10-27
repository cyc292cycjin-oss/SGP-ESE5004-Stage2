# H1 现状复核（HPR，2026-10-27；只读复核，以代码、网络与日志为准）

## H1.1 两个 v2 2920×3h 网络（主检出 `results_project/dfx_v3/builds_v2/`）

| 文件 | 实测 SHA256 | = B2 | 实测字节 | = DFX 登记（RUN_PLAN_DFX 第 1 节） | 构建回执 `code_sha` | 回执 `network.sha256` = 文件 |
|---|---|---|---|---|---|---|
| `integrated/integrated_2920_3h_unsolved.nc` | `08879f0bede119d77160cdb3f5f3c69dba302540b256b64efa4f16adbbefb271` | 是 | 63,873,447 | 是（63,873,447） | `72083fde6bffd89580869af6dd00885a8d76721f` | 是 |
| `disconnected/disconnected_2920_3h_unsolved.nc` | `d90ca99220d448c894c43c071b7e38f8c74e0a101b72878a4bdd941c37b164e7` | 是 | 63,202,193 | 是（63,202,193） | `72083fde6bffd89580869af6dd00885a8d76721f` | 是 |

- `BUILD_STATUS.txt`：`START:2026-10-26T14:34:06Z commit:72083fde… dirty:0`；两个情景 `S2_SCENARIO_BUILT_STATIC_PASS`，网络 SHA 与上表一致；同一次构建同时写出的 365×24h 日网络 `82928a4c…` / `5c75bfa0…` = DFX 阶段 4 筛查所用网络（V1 / V2 回执 `input_sha256`）。结论：两个 2920×3h v2 网络与 365×24h v2 筛查网络出自同一构建提交 `72083fde`（VERIFIED）。
- 成本表：`builds_v2/<scenario>/costs_active_research.csv`（各 42,518 B），随网络进包。

## H1.2 `run_batch4.sh` / `b4_batch4.py` / `RUN_PLAN_B4.md` 登记值逐项分类

| 登记值 | B4P 值（来源） | 分类 | HPR 取值 / 替代机制 |
|---|---|---|---|
| 基础网络 SHA256 / 字节 / 构建提交 | `bca20fc0…` 64,106,133 / `b401a687…` 63,439,167 / `ec80668f`（`b4_batch4.REGISTERED_*`、RUN_PLAN_B4 §1） | **按 B2 修改** | `08879f0b…` 63,873,447 / `d90ca992…` 63,202,193 / `72083fde` |
| TimeLimit `R_TL` | 259,200 s（`run_batch4.sh`；RUN_PLAN_B4 §3.1） | **按 B1 修改** | 864,000 s；`b4_batch4.TIME_LIMIT_S` 为单一来源 |
| 进程 2 墙钟 `R_WALL` | 266,400 = TL + 7,200（§3.1 第 2 项） | **按 B1 派生修改** | 871,200 = 864,000 + 7,200（余量不变） |
| 许可间隔 `R_GAP` | 330 s（§3.2 第 3 项） | 沿用 | 330 s；两作业方式另加 F2 对 F1 启动 + 330 s 的等待（`WAIT_START_OF`） |
| 求解方式 `R_MODE` | split（§3.1 第 3 项） | 沿用（B4） | split |
| 进程 1 / 3 超时 | 3,600 / 32,400 s（§3.1 第 2 项） | 沿用 | 同 |
| P1 探针 `P1_WINDOW_S` / `P1_THRESHOLD` / `P1_MIN_CORES` | 3,600 s / 0.40 / 33（§3.2 第 1–2 项） | **因 PBS 两作业方式不再适用** | F1、F2 各在自己的节点与 cgroup 内；并发由 PBS 依赖（F2 `depend=after:F1`）与 `WAIT_START_OF=F1` 的许可间隔决定；`--only` 模式不做探针、不写 `P1_DECISION.json`；常数保留在代码中供批次模式使用 |
| 内存止损 `MEMORY_STOP_FRACTION` | 0.80，cgroup 匿名内存对配额（§3.3） | 沿用；**计量方式按 PBS 写明** | 配额 = 申请值（300 / 250 GiB）；作业体解析本作业 cgroup（路径含作业号才算）；不可见 → 进程组 RSS 之和（`MEM_MEASURE=rss`） |
| 早期测速 `PROJECTION_FRACTION` / 迭代参考 | 0.80 / F1 450、F2 250（§3.4） | 沿用 | 止损线 691,200 s |
| 后处理并存条件 `POST_MEM_NEED_GIB` | 100 GiB（§3.6 第 2 项） | 沿用（两作业下很少触发：另一运行不在本 cgroup） | 100 |
| 后处理单步超时 / 重做 | 10,800 s；违反分析与 C1 失败重做一次（§3.6 第 3 项） | 沿用 | 同 |
| 分级停批 | G2 → STOP；无解 / C1 (a) → UNUSABLE + STOP；(b)/(c) → 不停（§3.5） | 沿用 | 同；STOP / STOP_SAFE 经共享运行目录跨作业生效 |
| 资源止损后的重开 | 新 RUN_DIR + 用户授权，不算重试（§3.8） | 沿用 | 同，写入 RUN_PLAN_HPC §6 |
| 续跑判定 | 已结束跳过；已开始未结束 → STOP_SAFE（§3.8） | 沿用 | 同（`--only` 复用 `solve_run`） |
| 预检硬下限 | 25 核 / 190 GiB / 45 GB（RUN_PLAN_B4 §5） | 沿用为缺省；作业内按申请值核对 | 作业体传 `NEED_CORES=申请核数`、`NEED_MEM_GIB=申请值 × 0.9`、磁盘 45 GB |
| 实例规格 / 候选配置（§4–5） | AutoDL / 阿里云配置表 | **不再适用**（HPC） | RUN_PLAN_HPC §3（PBS 资源） |
| 云端步骤（§8） | tmux + `run_batch4.sh --auth` 单进程批次 | **不再适用** | 操作手册步骤 A–G；F1 / F2 / 批级三个 PBS 作业 |

## H1.3 阶段 2 草稿（`hpc_package_dfx/`）与 B1–B4 的不一致

| 草稿文件 | 草稿取值 | 与 B1–B4 的不一致 | HPR 处理 |
|---|---|---|---|
| `make_pbs.sh` / `README_HPC.md` §3 | 推荐单作业 `dfx_f12_both.pbs`：96 核、210 GB（串行）或 400 GB（并行）、walltime 260 h；两作业各 48 核 / F1 210 GB、F2 200 GB、130 h | B3 规定两作业各 48 核、F1 **300gb**、F2 **250gb**；B1 规定 TimeLimit 240 h → walltime 需 ≥ 255 h | 作业脚本改由 `b4_batch4.py hpc-plan` 生成（单一来源）；单作业方案弃用 |
| `make_pbs.sh` `TIME_LIMIT_S=432000` | 120 h（"指令阶段 2 暂定"） | B1 = 864,000 s（240 h） | 全部取登记值 |
| `README_HPC.md` §5 | 时限登记问题留待用户（方案 A / B） | 已由 B1 决定 | `run_batch4.sh` R_TL / R_WALL 已改并登记于 RUN_PLAN_HPC |
| `hpc_job_both.sh` | 单作业跑 `run_batch4.sh --auth`（含 P1 探针）；作业内运行预检 **含 licence 节**（一次 WLS 会话） | B3 两作业；正式作业不得多占许可会话 | 弃用；`hpr_job.sh` 不运行 licence 节 |
| `hpc_run_one.sh`（PROPOSED，未测试） | 另起一套三进程 + 后处理驱动（约 60 行重写 `run_batch4.sh` 的逻辑）；`TL=${JOB_TIME_LIMIT_S:-259200}` 可被作业变量覆盖；内存监控只记录不止损；无早期测速；无许可间隔；无续跑的 `.started` 判定 | 违反 H3.1"复用已测试逻辑"；B1 值被环境变量覆盖而非登记；缺 B4P 3.3 / 3.4 保护 | 弃用；改为 `run_batch4.sh --only <rid>`（同一 `solve_run` / `post_run`） |
| `hpc_batch_post.sh`（PROPOSED，未测试） | 重写批级步骤（参照 / 重评 / B6 / 汇总 / 导出 / 打包） | 同上 | 弃用；改为 `POST_ONLY=1 bash run_batch4.sh`（已测试的 `regrade_all` / `batch_post` / `pack`） |
| `hpc_smoke_56.sh` | 只跑一体化一次；`curl token.gurobi.com`；单独写的后处理链 | 未覆盖 F2 与批级；非正式代码路径 | 冒烟改为作业体顺序执行 F1、F2、批级三个作业体（与正式路径相同） |
| `hpc_install_env.sh` | 在**登录节点**安装（conda create 约 14 min，接近 30 min CPU 限制） | H3.4 要求以作业方式在计算节点安装 | `hpr_install.pbs`（serial 队列） |
| `hpc_preflight.sh` | 登记值字面量（`REG` 字典、`BUILD` 提交）重复写在脚本里 | 与代码登记值可能漂移 | 改为调用 B4P `preflight.sh` 各节（`base-check` 读 `b4_batch4.py`）；一致性由 `hpr_consistency.py` 比对 |
| `make_hpc_package.sh` | 清单记 `registration_pending`（B2 未登记时） | 已由 B2 决定 | v9 打包脚本要求 `b4_batch4.py` 登记值 = 包内网络，并要求本机 H4 演练记录 |
| `HPC_GO_LIVE_CHECKLIST.md` B1–B6 | 待用户决定项（时限、v2 登记、单 / 双作业、内存、REMOVE_LP、冒烟队列） | B1–B4 已决定；REMOVE_LP=1、冒烟 parallel 17 核由 HPR 登记 | RUN_PLAN_HPC §9、§12 |
| 草稿中 `MEM_QUOTA_GIB=${JOB_MEM_GB}`、`CORES=${JOB_NCPUS}` | 正确思路 | 一致 | 沿用（作业体显式传入） |
| 草稿中 `CGROUP:` 记录只读根 cgroup 文件 | `/sys/fs/cgroup/memory.max` 在 PBS 节点上多为根 / 不存在；若 v1 根 `memory/memory.stat` 可读会把全节点内存当作本作业 | 内存止损误判风险 | 作业体从 `/proc/self/cgroup` 解析含作业号的路径；否则 RSS |
