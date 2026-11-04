# V3 HPC 正式运行包验收（独立审阅端，2026-11-04）

- **指令：** `work/p1_v3_review_20261103/V3_HPC_ACCEPTANCE_INSTRUCTION.md`，SHA256 `c6b993ea86d57c01c6bf6a34d5b637ce102344f6b335972c5fc364717ad5c2bf`，与同目录 `V3_HPC_ACCEPTANCE_SHA256.txt` 一致。
- **验收对象：** 部署包 `work/p1_v3_20261102/hpc_package_v3/`（`SHA256SUMS` 的 SHA256 `63d682bbe743ce220bec747aede81d6423d3afd1cac53b7ffdbc2345e970345c`，与 `V3_HPC_PROGRESS.md` 最后一行一致；`COMMIT` `7d22dda112a3c18ed57e8c061d95e51915980417`；`sha256sum -c SHA256SUMS` 46 个文件全部 OK）；分支 `codex/v3-hpc-20261104` 头 `865c119c`（只读 worktree `/home/jin/wt_v3_hpc_review`，detached）；`RUN_PLAN_HPC_V3.md`、`HPC_OPERATOR_GUIDE_V3.md`、`V3_REPORT_HPC_PACKAGE.md`、`V3_HPC_UNATTENDED.md`、`V3_REVIEW_DECISIONS_INDEP.md`。
- **方法与资源：** 只读；Gurobi 0 次；不连 HPC、云、VPN；本机计算约 1 小时（上限 1.5 小时）：包哈希核对、本机编译的 bash 4.2.0（`/home/jin/v3h/bash42/src/bash`，打包会话编译，本次只使用）下 18 个脚本 `bash -n` 与 4.3+ 写法扫描、`netCDF4` 读四个网络的船运与 EV 字段、泄露扫描、HPC 相关测试文件在只读 worktree 上重跑。
- **证据等级：** VERIFIED（读了文件、数组、脚本）、EXACT（逐位或整数核验）、INFERENCE（机制推断）。

## 0. 结论

**可以运行。** 没有 S1。两项 S2 都是运行中的"安全方向"风险（止损偏早、后处理超时超出 walltime 项），不阻断提交，但用户与打包端应在开跑前知悉；三项 S3 是过时文字，不改包。

正式提交前的两个条件（指令与指南已有，这里重申）：(1) 用户在 Atlas 登录节点确认 `bash --version` ≥ 4.2 并完成两次 `hpr_submit.sh --dry-run` 演练；(2) HPC 冒烟作业 `SMOKE_RESULT:PASS`。两者都不是本验收能替代的。

## 1. 发现表（格式同 `V3_INDEPENDENT_REVIEW.md`）

| 编号 | 等级 | 发现 | 证据 | 影响 | 建议 |
|---|---|---|---|---|---|
| — | S1 | **无** | — | — | — |
| H-S2-1 | S2 | **早期测速止损低于时限外推的假设（T < U）。** 登记 T = 864,000 s，止损线 0.8 T = 691,200 s，参考迭代 350（F1、F3）。第 20 次迭代判定：avg(11–20) × 350 + 已用时 > 691,200 s，等价于 Atlas 单次迭代 ≥ 约 1,840–1,860 s；U 的假设是 2,686 s/次（1,679 × CPU 因子 1.6），中值假设 1,056 s/次。即 Atlas 比 B4P 高值外推（1,679 s/次）再慢约 10 % 就会在约 10 小时后止损 | `RUN_PLAN_HPC_V3.md` 第 5、14.2 节；`V3_REPORT_HPC_PACKAGE.md` 第 5.2 节；`run_batch4.sh` 373–376 行；`BATCH_DEF.json` `iterations_reference` 350 / 250（VERIFIED） | 止损写 `STOP_SAFE:PROJECTION` → 本运行 `.ended`，F2 若已在求解则继续到底；F3、F4 的作业体与运行器见到 `STOP_SAFE` 后不启动（`run_batch4.sh` 576、410 行，VERIFIED）。损失约 10 h 求解 + 排队，结果不受污染；重开需新 RUN_DIR 与重新登记的 T（审阅端 + 用户） | 开跑前不改（登记值已定，改动需重新登记并重出包）。用户知悉：若 F1 在约 10 h 处止损，不是故障，是 240 h 上限的直接结果；这时按指南 H 报告，由审阅端与用户决定新 T |
| H-S2-2 | S2 | **walltime 的后处理项按估计值而不是超时上限计。** 组成 918,930 s 中后处理只计 2 × 3,900 s；而 `post_run` 最坏可到 violations 2 × 10,800 + C1 2 × 10,800 + m12 + m12_owen + accept 各 10,800 = 75,600 s（21 h），远超 F1 余量 17,070 s | `run_batch4.sh` 221–229、489–509 行；`b4_batch4.py walltime_components`（VERIFIED） | 只在后处理步骤反复超时时发生；此前 `.ended`、`SOLVE_RECEIPT.json`、解数组已落盘（438 行先于 `post_run`），PBS 杀作业不损失求解结果；批级作业 `POST_ONLY=1` 对每个已结束运行重做缺失的后处理（588 行；幂等，按文件存在性跳过），48 h 批级 walltime 足够 | 沿用 v2 登记的组成，不改。记录：若某运行的 PBS 作业在后处理阶段被杀，不是求解失败，批级作业会补做；用户按指南 G 回收时以批级包为准 |
| H-S3-1 | S3 | **三处运行期长度文字不一致：** `hpc/hpr_submit.sh` 25 行 MOTD 提示"next ~11 days"（v2 两作业的值）；`HPC_OPERATOR_GUIDE_V3.md` E1 写"约 22 天"（260 + 260 h，正确）；`RUN_PLAN_HPC_V3.md` 106 行写"最长约 31 天" | grep（VERIFIED） | 操作者按指南 E1（22 天）判断维护窗口即可；脚本提示偏短可能让人低估重叠 | 不改包（改一字就换 COMMIT 与 SHA）。用户以 22 天为准核对维护通知；下次出包时统一 |
| H-S3-2 | S3 | **8 个 PBS 脚本第 9 行注释仍写 v2 路径 `/hpctmp/<user>/hpr`**，v3 包目录是 `hpr3` | `pbs/*.pbs:9`（VERIFIED） | 注释，不影响执行（`cd "${PBS_O_WORKDIR:?}"` 取提交目录） | 不改包；记录 |
| H-S3-3 | S3 | **`hpc_package_v3` 内含公共登录主机名 `atlas8.nus.edu.sg`**（指南 15 处）与 `env/install_env.sh` 的通用 AutoDL 默认前缀 `/root/autodl-tmp/...` | 泄露扫描（VERIFIED） | 与 v2 包、`HPC_FACTS_20261026.md` 相同：公共 HPC 登录节点名与通用路径，不是云实例名、端口或连接地址；按项目既往口径不算泄露 | 记录；指令第 7 条的其余项（许可内容、端口、实例名）命中 0 |

## 2. 逐项结论

### 第 1 项：能在 Atlas 上跑起来 — **通过**

- **bash 4.2（VERIFIED）：** 用本机编译的 `GNU bash, version 4.2.0(2)-release` 对包内 18 个 `.sh` / `.pbs` 做 `bash -n`，全部通过。扫描 4.3 及以上写法（`declare -n`/`local -n`、`wait -n/-p/-f`、`mapfile -d`、负下标、`${var@Q}`、`EPOCHSECONDS`、`BASH_ARGV0`、`inherit_errexit`、`[[ -v a[i] ]]`、`test -R`）命中 0。`set -u` 下没有 `:-` / `+` 保护的数组展开逐条核对（`run_batch4.sh` 158、159、284、287、395、402、413、417、423、430、447、534、535、588、592 行；`hpr_submit.sh` 43、52 行）：`RIDS`、`SC` 先检查 ≥ 2 个运行（155 行），`PAIRS` 由 `RIDS` 推出 ≥ 1，`"${RIDS[@]:1}"` 对 ≥ 2 元素的数组非空，`need`、`cmd`、`pargs`、`reg` 构造时即有元素，`ORDER` 先检查 ≥ 3；`${#arr[@]}` 对空数组在 4.2 下合法。`${THREADS[${PROF[$rid]}]}` 只对 `formal_barrier_1e6_t16` 有键，四个运行的 `profile` 都是它（`BATCH_DEF.json`，VERIFIED）。
- **PBS 指令对 `HPC_FACTS_20261026.md`（VERIFIED）：** 队列 `parallel`；`select=1:ncpus=48:mem=300gb`（F1、F3）/ `250gb`（F2、F4）/ `ncpus=12:mem=120gb`（批级）≤ 540 GB、12–96 核；walltime 260 / 262 / 260 / 262 / 48 h ≤ 720 h；任一时刻最多两个正式作业 = 96 核 = 每用户上限；正式作业 5 个 ≤ 8。事实表不要求 `-P` 项目号；v2 的 D2 作业用同一格式在 Atlas 上跑过。
- **路径约定：** 包目录 `/hpctmp/$USER/hpr3`，与 v2 的 `hpr` 分开；所有 `qsub` 在包目录执行，作业体 `cd "${PBS_O_WORKDIR:?}"`；许可只核对 `~/.gurobi/gurobi.lic` 存在与 600 权限。
- **未覆盖（照实）：** Atlas 登录节点的实际 bash 版本与 PBS 版本未在本次验证（不连 HPC）；由指南清单 (c) 的 `bash --version` 与两次 `--dry-run` 兜底。

### 第 2 项：许可 — **通过**

- **任一时刻 ≤ 2 个 Gurobi 会话（VERIFIED，`run_batch4.sh` 298–340、407–413 行）：** 每次 Gurobi 启动前依次经过 `wait_gap`（距最近一次结束 ≥ 330 s）、`wait_other_start`（F2：等 F1 的 `.solve_start` + 330 s，或 F1 结束）、`start_lock_acquire`（共享 RUN_DIR 的原子 `mkdir` 锁；锁内等到距其他运行每次启动、每次结束与本运行器启动都 ≥ 330 s，且"已启动未结束"的其他运行 < 2）、`gurobi_busy < 2`。F1 / F2 并行 = 2；F3 的作业 `afterany:F1`（F1 作业已结束），进程 1 构建约 40 分钟后再进锁，此时只有 F2 可能在跑 → F2 + F3 = 2；F4 同理 → F3 + F4 = 2。PBS 每用户 96 核上限独立地保证同时最多两个 48 核作业。
- **F2 等 F1 的逻辑：** `after:F1` 让 F2 作业在 F1 作业开始执行后才可调度；F2 的 Gurobi 进程只在 F1 写出 `.solve_start` 至少 330 s 后、或 F1 结束（`.solve_end` / `.ended`）后启动；超过 7,200 s 无标记 → `STOP_SAFE:WAIT_START`。F1 构建失败（`BUILD_FAILED` → `STOP_SAFE`）时 F2 在 `wait_other_start` / `start_lock_acquire` 返回后被 410 行 `halted` 拦住，不开会话。
- **F3 / F4 对前序失败、`qdel`、walltime 杀死的行为（VERIFIED，`hpc/hpr_job.sh` 109–116、129–130 行）：** 前序没有 `.ended` 且批次未停 → `STOP_SAFE:PREDECESSOR_NOT_ENDED`，退出 3，不做预检、不启动；前序已停批 → 作业体放行，运行器在 576 行见 `STOP_SAFE` 记 `NOT_STARTED` 退出 3；正式作业预检失败 → `STOP_SAFE:PREFLIGHT_FAILED`。被杀作业留下的 `.solve_start`-无-`.solve_end` 在启动锁中永远算"在跑"，方向保守（只会多等、不会多开）。打包端列为已知局限的第 2 条（`.solve_start` 早于真实会话建立、实际间隔可能略小于 330 s）我同意不改：同时会话数上限不受影响。
- **批级作业不调用 Gurobi：** `POST_ONLY=1` → `NOSOLVE=1`，`LIC=/nonexistent/...`，每个后处理步骤 `env -u GRB_LICENSE_FILE`（224、229 行）；`solve_run` 在 POST_ONLY 下只写日志（390 行）。冒烟作业 F1、F2 串行各一次会话，中间 `wait_gap` ≥ 330 s。

### 第 3 项：登记一致性 — **通过**

| 项 | `RUN_PLAN_HPC_V3.md` | `BATCH_DEF.json` | 脚本 / PBS | 预检 |
|---|---|---|---|---|
| 网络 SHA256 | F1 `8b5fd663…` 72,050,034 B；F2 `e2837e4a…` 71,411,694；F3 `c4eb7c44…` 72,050,068；F4 `0bbe235e…` 71,411,730 | 同 | `pbs/HPC_PLAN.txt` NETWORK 行同 | `base-check` 比 SHA256 + 字节 + 回执；包内四个 `.nc` 实测 SHA256 一致（`sha256sum -c`） |
| TimeLimit / 墙钟 | 864,000 / 871,200 s | `time_limit_s` 864000，`wall_margin_s` 7200 | `JOB_TIME_LIMIT_S=864000 JOB_WALL_CAP_S=871200`；`run_batch4.sh` 经 `hpc-plan` LIMITS 行读取并拒绝不符的环境值 | `code` 节按定义断言 |
| walltime | 260 / 262 / 260 / 262 / 48 h | `hpc_jobs.walltime` 同 | `#PBS -l walltime=` 同 | 一致性检查 57 行 `ALL_CONSISTENT`（含 4 行余量 ≥ 7,200 s） |
| 构建超时 | 5,400 s | `build_timeout_s` 5400 | LIMITS 行 | 干跑记录读到 5,400 |
| 参考迭代 | F1、F3 350；F2、F4 250 | `iterations_reference` 同 | `runmeta` → `ITERS_REF`；HPC_PLAN ITERS 行 | — |
| 资源 | 48 核 300 / 250 GB；批级 12 核 120 GB | `hpc_jobs` 同 | `#PBS -l select` 同 | — |
| 依赖 | F2 `after:F1` + `WAIT_START_OF=F1`；F3 `afterany:F1`；F4 `afterany:F2`；批级 `afterany:F3:F4` | 同 | `JOB_DEPENDS` / `JOB_WAIT_START_OF` 同 | — |
| 状态 | REGISTERED | `limits_status: REGISTERED` | `STATUS|REGISTERED`；PROPOSED 时三处拒绝正式运行 | — |

**推导核验（EXACT，按 `V3_HPC_UNATTENDED.md` 第 1 节与 `RUN_PLAN_HPC_V3.md` 第 14 节）：** U = 1,679 × 350 × 1.6 = 940,240 s + 9,000 s = 263.7 h；2U = 527 h → min(240, 527) = 240 h → T = 864,000 s ✓。基础项 330 + 5,400 + 871,200 + 32,400 + 7,800 + 1,800 = 918,930 s ✓。F1：936,000 − 918,930 = 17,070 s ✓；F2：933,330（两个等待项）→ 943,200 − 933,330 = 9,870 ✓；F3：926,130 → 936,000 − 926,130 = 9,870 ✓；F4：926,130 → 943,200 − 926,130 = 17,070 ✓。四个余量都 ≥ 7,200 s ✓。`b4_batch4.py walltime_components` 的等待项计数（首个正式作业 0，其余 1，有 `wait_start_of` 再加 1）与此一致。

### 第 4 项：审查发现的落实 — **通过**（含一处对我原审查的更正）

| 项 | 决定 | 落实证据（VERIFIED） |
|---|---|---|
| S2-1 | 第 186 项 | `V3_RULES.md` 第 10 节第 7 条补写（日分辨率无任何日内平衡，筛查只用于 B6 符号、账本与分摊程序检验）；预测两参照并列（`RUN_PLAN_V3.md` 第 26 节） |
| S2-2 | 第 187 项，η = 1 | 四个网络 270 条船运链路 `efficiency` 全为 1.0，`marginal_cost` 0.48–3.93 EUR/MWh，`ship_cost_basis = ieaghg`（`netCDF4` 直读，EXACT）；`v3_layers.ship_unit` 文档改为 S-A 主值 |
| S2-3 | V14 打包 | 包内代码 `7d22dda1` ≥ `6b1a1225`，`BATCH_DEF.json` 为 v3 四运行、v3 网络、参考迭代、构建超时 |
| S2-4 | F3 / F4 车队 ×0.5 | `BATCH_DEF.json` F3、F4（pair B，F4 `parent: integrated_ev05`）；网络 `ev_fleet_scale` 0.5，EV 电池 `e_nom` 合计 3.967 TWh、充电桩 1,745.4 GW，恰为 F1 的一半（EXACT） |
| S2-5 | 四个玩具测试 | `tests/research/test_v3_units.py`：`test_ev_structure_toy_timezones_energy_charger`（参数化）、`test_bunker_nodal_toy_terminal_buses_co2_port_owner`、`test_liquid_shipping_toy_links_bounds_transit`（参数化）、`test_carrier_share_keys_missing_key_raises`，另加 `test_carrier_share_table_covers_every_carrier_with_demand`、`test_direct_subjects_single_source`；`s2_layers.check_carrier_share_keys` 在份额查找前调用（diff 266–267 行） |
| S3-1 | 改名与注记 | `batch_def/BATCH_DEF_2920x3h.json` 名称 "superseded for the formal batch"、注记指向 `_v3hpc.json`，登记值不变（diff 4 行） |
| S3-2 | 等级 C | `v3_data.py` S-B 三行 B → C、描述"下界敏感性"；S-A 标"主值" |
| S3-3 | 说明 | `V3_RULES.md` 第 2.3 节末补记专线不在长度份额表、拆分为 0.5 |
| S3-4 | 单一来源 | `s4d_ledger.DIRECT_SUBJECTS`，`m12_allocation.DIRECT` 引用它。**更正我的原审查：** 两份清单原本并不一致（`s4d_ledger` 缺 `co2_transit_rail_freight`），打包端的发现属实；统一后只改 `LEDGER_IDENTITY.json` 两个诊断量，闸门不读它们。我接受 |
| Q-1 | 写明判据 | `V3_RULES.md` 第 8.3 节：B1 通过 ⇔ 每国大气 Store 末值 ≤ cap + (1e-3 + 1e-7 × max(1, \|cap\|))，内点解下总是不过，以 `B1_S4B` 为判据，阈值不改 |

### 第 5 项：预测在任何 HPC 求解之前登记 — **通过**

`RUN_PLAN_V3.md` 第 26 节（B6 方向与区间、F4 − F3 对 F2 − F1、EV 部分、Owen 符号、迭代数、时长、终止、内存）在提交 `917c8b63`（2026-11-04 01:56:52 SGT）中，第 24 节登记在 `a4607714`（01:23:30 SGT，本机冒烟 01:24 之前）。至今没有任何 HPC 求解（用户尚未上传），所以"任何 HPC 求解之前"成立（VERIFIED，`git log --date=iso-strict`）。预测以 56 时段冒烟与 365×24h 重跑两个参照并列，并写明各自的结构失真，符合第 186 项。

### 第 6 项：操作指南可用 — **通过**

代码块内没有尖括号占位符（逐块 awk 检查，命中 0）；替换值只有 `$HPC_USER`、`$WSL_USER`、`F1_ID` 等作业号变量与 `RID`，各在上一行说明来源。VPN 连上后在 Windows PowerShell 用 `scp` 单路上传（28、105 行）、`sha256sum -c`；级联撤销 `qdel $B_ID $F4_ID $F3_ID $F2_ID $F1_ID`（82 行）；结果回收 G1 / G2 与 `/hpctmp` 60 天清理（86、239 行）；`bash --version` 与两次 `--dry-run`（32、35 行）；维护窗口按 22 天（E1）。见 H-S3-1 的文字不一致。

### 第 7 项：泄露 — **通过**

包内 46 个文本 / 脚本 / JSON 文件与 `code_7d22dda1.tar.gz` 的 1,613 个条目：许可内容、WLS 键名、ssh 密钥、`.lic` / `id_rsa` / `known_hosts` / `HPR_AUTH` 文件名命中 0；IP 形命中只有 `env/ENV_LOCK.txt` 的四段式版本号与 WSL 内核版本串；五位端口形命中 0；云实例名命中 0。分支 `5e372e5d..865c119c` 全部新增行（含证据目录）：许可值、键名、ssh、实例名、端口命中 0，只有一行描述泄露扫描本身的文字。主机名只有公共登录节点 `atlas8.nus.edu.sg`（H-S3-3）。

## 3. 测试

在只读 worktree `/home/jin/wt_v3_hpc_review`（`865c119c`）上，bash 5、`PYTHONHASHSEED=0`，重跑 `test_v3_units.py`、`test_v3_hpc_runner.py`、`test_v3_runners.py`、`test_hpr_two_jobs.py`、`test_b4p_batch4.py`：**57 项全部通过**，526 s（VERIFIED）。其中含 scipy `linprog` / HiGHS 的玩具 LP（替身测试，无模型网络、无 Gurobi）。bash 4.2 下的替身测试结果取打包端报告第 8.2 节（38 项通过），本次未重跑。

## 4. 未覆盖与说明

1. 不连 HPC：Atlas 的 bash / PBS 版本、文件系统上原子 `mkdir` 的行为、真实依赖链调度都未演练；由 HPC 冒烟作业与两次 `--dry-run` 兜底，且上述每一处失败都落到 `STOP_SAFE` 而不是多开会话。
2. 全尺寸 2920×3h LP 规模与内存峰值只有外推（打包端已照实写明）；内存止损 0.8 × 配额与 `MEM_MEASURE=auto` 的 cgroup 回退路径沿用 v2，本次只读代码核对。
3. 我没有重新运行打包端的全量测试（授权只在出现新失败时要求），只重跑了 HPC 相关测试文件（第 3 节）。
4. 本验收不替代用户在指南清单 (c)、(e) 的两步：登录节点 bash 版本确认与 HPC 冒烟作业通过。

## 5. 提交

分支 `codex/v3-review-20261103`（审查分支，自 `edea54cf` 续）；本文件复制到 `work/p1_v3_review_20261103/`。提交号见 `git log`。不改 main、不 force-push、不开 PR。
