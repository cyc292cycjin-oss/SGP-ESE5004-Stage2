# W14 第 3 节：打包与本机演练

- **标记：** VERIFIED（回执、记录文件）、EXACT、INFERENCE、PROPOSED。逐条记录在 `logs/`（`pkg_*.txt`、`final_drill.txt`、`dry_bash*.txt`、`smoke_drill.txt`、`rebuild_and_dry_12083cf5.txt`），脚本 `hpc_v4/make_hpc_package_v4.sh`、`scripts/w14_pkg.sh`、`scripts/w14_dry.sh`、`scripts/w14_smoke_drill.sh`、`scripts/w14_final_drill.sh`。
- **演练副本不在 work/ 下、不得上传：** 每次演练都把交付包整个打成 tar、解到 `/home/jin/v4w14/<dry|smoke>_<时间>/pkg`（全新目录，从不复用），先 `sha256sum -c SHA256SUMS` 再做任何事；包的副本里没有 `DRILL_ONLY` 之类的标记文件，交付包本身从未被演练写入（`runs/` 只在副本中出现）。

## 1. 交付包 `work/p1_v4_w14_20261109/hpc_package_v4/`（第 3.1 条；VERIFIED）

| 项 | 值 |
|---|---|
| 包的 `COMMIT`（= 打包前本分支最后一次提交，W14-4c） | `26c2e47d025fdd4e46cb278718d93aeddabbe984` |
| `SHA256SUMS` 的 SHA256 | `9f97e221c05b7196531776c21a1ef2f0478338d3f14b70ffe5d817c9f40b98fd` |
| 文件数 | 41（`SHA256SUMS` 登记 39 个 + `SHA256SUMS` + `HPC_PACKAGE_MANIFEST.json`） |
| 大小 | 251,432,422 字节（不含清单 251,419,699；上传 1 MB/s 约 4.2 分钟，0.1 MB/s 约 42 分钟） |
| 代码包 | `code_26c2e47d.tar.gz`（84,049,847 字节，SHA256 `8bbdcb1b…`）：`git archive` 去掉顶层 `research/`；`research/` 之外与网络构建提交 `59b128ea` 逐文件相同（打包脚本核对 `git diff` 为空才出包） |
| 网络 | `networks/integrated_2920_3h_unsolved.nc` `86f6d6a0…`（82,749,911）、`networks/no_new_xb_2920_3h_unsolved.nc` `24e835f7…`（82,112,443）= 定义文件登记值；`integrated_BUILD_RECEIPT.json`（`code_sha` = `59b128ea` = 定义文件 `build_commit`）、`no_new_xb_2920_3h_VARIANT_RECEIPT.json`、`integrated_costs_active_research.csv`；无 365×24h |
| `BATCH_DEF.json` | = `batch_def/BATCH_DEF_2920x3h_v4hpc.json`（由 D1 草案更新：只含 F1、F2、批级 `afterany:F1:F2`、`smoke56`、`install`、`build_only_f1`；`limits_status: REGISTERED`；`v4_meta`） |
| `pbs/` | `hpr4_f1`、`hpr4_f2`、`hpr4_batch`、`hpr4_smoke56`、`hpr4_build_only_f1`、`hpr4_install` 六个作业脚本 + `HPC_PLAN.txt`（`RUNDIRS|runs/batch6|runs/smoke56_v4|runs/build_only_f1_v4`）；由 `hpc/make_pbs.sh` 从定义文件生成 |
| `hpc/` | HPR 的 `hpr_job.sh`、`hpr_submit.sh`、`hpr_preflight_login.sh`、`hpr_install_env.sh`、`make_pbs.sh`、`hpr_consistency.py`（与 v3.1 包逐字节相同）+ D1 的 `hpr_status.sh`（同时显示含常数项目标值、`objective_lp`、常数项与包 `COMMIT`） |
| 运行器 / 预检 / 打包 | `run_batch4.sh` = D1 `hpc_v4/run_batch4.sh`（包 `COMMIT` 写入 `RUN.json` 与回执，正式运行缺少或不一致即拒绝）；`preflight.sh` = v3.1 预检 + D1 的开关集与网络元数据检查（`networks` 节）；`pack_results.sh` 与 v3.1 相同 |
| `env/` | 与 v3.1 包同一锁文件（`ENV_LOCK.txt` 等 6 个文件逐字节相同）；HPC 上已装环境在预检 `env` 节一致即复用 |
| 文档 | `RUN_PLAN_HPC_V4.md`、`HPC_OPERATOR_GUIDE_V4.md`、`HPC_FACTS_20261026.md`、`REFERENCE_VALUES.json`（只有数：v3.1 2920×3h F1 / F2、D2c 与 v3.1 的本机 56 时段冒烟）、`ZERO_SLACK_CHECK.json`、`HPC_CONSISTENCY.json / .txt`、`HPC_PACKAGE_MANIFEST.json` |

**出包闸门（全部通过，`logs/pkg_hpc_package_v4.txt`）：** 网络 SHA256 / 字节 = 定义文件；`base-check`（回执、构建提交）；零松弛门两网通过（705 / 589 行，无强制行）；登记值一致性 **44 / 44 `ALL_CONSISTENT`**（计划、定义文件、运行器、预检、PBS 脚本、作业体、运行目录）；**许可类字符串扫描（`pack_results.sh` 同一正则 `license[i]d|registered[[:space:]]+to|wls(secret|accessid)`，不分大小写，文本文件）对整个包 0 个文件**；用户机外的模式文件扫描 0；无 365×24h 网络；在包的副本上运行包自己的预检（guards、sha、networks 含 v4 元数据、env、profile、code、tools）`PREFLIGHT OK`；解包后的代码只有 1 行命中上述正则，为 `scripts_project/s2_solve.py` 第 181 行的日志清洗标记表（求解日志中要删去的词，不含许可内容；v3.1 包中是同一文件），按该行 SHA256 列入白名单，其余任何命中都拒绝出包。

**打包经过（如实记录）：**

| 次 | 提交 | 结果 | 去向 |
|---|---|---|---|
| 1 | `6d45a37b` | 其余闸门全过，额外的"解包代码"扫描命中上述日志清洗标记表，按设计拒绝出包 | 半成品改名 `hpc_package_v4_refused_6d45a37b`（不上传） |
| 2 | `12083cf5` | 白名单按原文比对，全部闸门通过；干跑两种 bash 通过（第 2 节） | 打包脚本自身含白名单原文，交付目录与审阅包的扫描会命中它，改为按 SHA256 比对后重打；改名 `hpc_package_v4_superseded_12083cf5`（不上传） |
| 3 | **`26c2e47d`** | 全部闸门通过 | **交付包 `hpc_package_v4`** |

三次的差异只在打包脚本（`research/` 内）；代码包内容、网络、定义文件、计划、指南逐字节相同（只有 `COMMIT`、代码包名与其 tar 头中的提交号、清单与 `SHA256SUMS` 随提交变化）。

## 2. 在包的代码提交上重建核对（第 2.1 条；VERIFIED）

在包的 `COMMIT` `26c2e47d` 上于同一 worktree 路径重建（`scripts/build_w14.sh rebuild_pkg_26c2e47d`）：一体化与 `no_new_xb` 的 2920×3h、365×24h 四个文件与构建提交 `59b128ea` 的文件**逐字节相同**；包内 `networks/integrated_2920_3h_unsolved.nc` 与构建文件逐字节相同（`logs/final_drill.txt`）。第二次打包的提交 `12083cf5` 上同样核对过一次（`logs/rebuild_and_dry_12083cf5.txt`）。详见 `STATIC_CHECKS.md` 第 4 节。

## 3. 提交脚本 dry-run 与拒绝路径（第 3.2 条；VERIFIED；不调用求解器，不读许可）

在交付包的解压副本中（`scripts/w14_dry.sh`；`logs/dry_bash.txt` 为 bash 5.3.9，`logs/dry_bash42.txt` 为本机编译的 **bash 4.2.0**，即 Atlas 登录节点的版本；两次结果逐项相同）：

| 步骤 | 结果 |
|---|---|
| 解压副本 `sha256sum -c` | 0 个不 OK，39 个登记文件，副本共 41 个文件 |
| 包的预检（guards、sha、networks 含 v4 元数据、env、profile、code、tools） | `PREFLIGHT OK`；v4 元数据两行 `-> OK`（开关集 `d89ccbf47b00`、表目录 `out_ras`、配置哈希 = 重组值）；环境 284 / 284 个关键包一致 |
| 登录预检 `hpc/hpr_preflight_login.sh`（许可路径用一个权限 600 的占位文件，只核对存在、属主与权限） | `HPR_PREFLIGHT_LOGIN OK`；指南步骤 B3 列出的期望行都在 |
| BUILD_ONLY（`TRUNCATE=56`，F1、F2 只跑进程 1） | exit 0（67 / 70 s）；`BUILD_CHECK_F1/F2 passed`；56 时段 LP F1 1,604,504 行 / 729,105 列 / 3,722,003 非零、F2 1,556,922 / 707,751 / 3,571,769（与 D2c 冒烟的 LP 相同）；`RUN.json` 与求解回执都记 `package_commit` = `repo_commit` = `26c2e47d…`；参考迭代 350 / 300；TimeLimit 259,200 |
| 作业体 BUILD_ONLY（`JOB_MODE=build_only`，F1，本机演练开关） | exit 0；运行目录 `runs/build_only_f1_v4`；作业内预检 `PREFLIGHT OK`；`BUILD_ONLY_STATUS.txt` 完整（峰值、LP 字节、构建与写出秒数、写盘速度），LP 文件已删除 |
| 正式作业体带测试开关（`BUILD_ONLY=1`） | **exit 2，`REFUSED: test hook ... BUILD_ONLY`**，什么都没创建 |
| 正式作业体 F2 无授权文本 | **exit 2，`REFUSED: the user authorisation text is missing`**，未启动 |
| 批级作业体在 F1、F2 未结束时 | **exit 2，`REFUSED: not_ready`** |
| `hpc/hpr_submit.sh --auth-file /nonexistent --motd-checked --dry-run` | exit 0，**以 `DRY_RUN_OK` 结束**；3 行，顺序 **`qsub pbs/hpr4_f1.pbs` → `qsub -W depend=after:F1_JOBID pbs/hpr4_f2.pbs` → `qsub -W depend=afterany:F1_JOBID:F2_JOBID pbs/hpr4_batch.pbs`**；3 条 NOTE：缺授权文件、冒烟未 PASS（路径 `runs/smoke56_v4`）、本机没有 `qsub`（HPC 登录节点上不会出现，指南 B4 写的是前两条）；没有创建 `runs/` |
| `hpc/hpr_status.sh` 缺省目录 | `runs runs/batch6` |
| `unbound variable` / `syntax error` / `command not found` | 无 |

## 4. 冒烟作业体演练（第 3.2 条；VERIFIED；**求解器 2 / 2 次**，即本指令授权的全部额度）

**方法（`scripts/w14_smoke_drill.sh`，`logs/smoke_drill.txt`，证据 `evidence/smoke_drill/`）：** 交付包的解压副本 `/home/jin/v4w14/smoke_20261108T204757Z/pkg`（`sha256sum -c` 0 个不 OK）中，用 bash **原样执行生成的作业脚本 `pbs/hpr4_smoke56.pbs`**（`#PBS` 行是注释；`JOB_*` 值 17 核 / 32 GB / 4 h），作业体依次 F1、F2、批级：`TRUNCATE=56`、`formal_barrier_1e6_t16`（Threads 16）、TimeLimit 3,000 s / 墙钟 3,600 s、split 三进程、运行目录 `runs/smoke56_v4`。只加本机演练开关：`HPR_LOCAL_DRILL=1`（不向令牌服务器发 HTTP、不做资源节）、`PBS_JOBID=local.smoke`、`PBS_O_WORKDIR` = 副本。开始前：令牌服务器 TCP 连接预检通过、许可文件只核对存在与权限 600（未读）、本机无其他求解或 pytest；同一时刻至多 1 个 Gurobi 进程；运行器保证两次会话间隔 ≥ 330 s；无重试、无参数改动。2026-11-08 20:48:10–21:13:54 UTC，作业 1,543 s。

| 项 | F1 一体化 | F2 `no_new_xb` |
|---|---|---|
| 网络 | `86f6d6a0…`（包内，`base-check` 等于构建回执） | `24e835f7…` |
| 会话间隔 / 启动锁 | 运行器启动后 330 s；锁内无其他 Gurobi | 330 s + 锁内距 F1 结束 ≥ 330 s（360 s） |
| 进程 1 | 36 s，峰值 2.22 GiB，LP 97,709,092 字节 | 29 s，1.99 GiB，94,356,707 字节 |
| 进程 2（Gurobi） | **optimal**，89 次迭代，254 s，峰值 6.07 GiB（`MaxMemUsed` 5.94 GB） | **optimal**，80 次迭代，161 s，4.66 GiB（4.47 GB） |
| 早期测速（第 20 次迭代后） | 未超线 | 未超线（外推 421 s / 线 2,400 s） |
| 目标值（含常数项） | **363,190,038,821.0828** | **376,143,650,003.4369** |
| `objective_lp` / 常数项 | 360,823,560,546.8396 / 2,366,478,274.24 | 373,606,494,673.1073 / 2,537,155,330.33 |
| 期望值（D2c 本机冒烟）/ **相对差** | 363,190,038,821.0828 / **0.000e+00** | 376,143,650,003.4369 / **0.000e+00** |
| C1 (a)(b)(c) / GATES_V6 | 111 / **`ACCEPTED_LAYER2`** | 111 / **`ACCEPTED_LAYER2`** |
| 未通过的闸门 | A1_A2、A1_A2_S4B、A3、B1、B3、B8（= D2c 冒烟，在 v3.1 并集内） | 同左 |
| 回执中的包提交 | `RUN.json` 与回执 `package_commit` = `26c2e47d` | 同左 |

- **`SMOKE_STATUS.txt`（逐行）：** `F1:termination=optimal:...:label=ACCEPTED_LAYER2:...:relative_difference=0.000e+00:gurobi_status=OPTIMAL:OK`；`F2:...:OK`；`POSTPROC_ERRORS:0`；`BATCH_DONE:True`；`HALTED:False`；`PACKS:2`；**`SMOKE_RESULT:PASS`**（`WLS_TOKEN_HTTP:skipped_local_drill`：本机演练不发 HTTP 请求，令牌服务器的可达性另由 TCP 预检确认）。
- **批级后处理：** exit 0（11 s）；本批参照与重评、B6 = 12.9536 bn（= D2c 冒烟）、Owen 受益（56 时段 LA、PH 为负，与 D2c 冒烟相同）、`reference_comparison`（对 D2c 冒烟目标值差 0.0、对 v3.1 本机回归 +33.48 / +33.87 bn、对 v3.1 2920×3h 只是数值并列）、两个结果包（light 1,063,404 字节、full 63,667,948 字节，`.sha256` 已写）。
- **状态命令：** `hpc/hpr_status.sh runs/smoke56_v4` 每个运行显示 `objective incl. constant: 363,190,038,821.08 EUR [SOLVE_RECEIPT.json (process 3)]; objective_lp: 360,823,560,546.84 EUR; constant: 2,366,478,274.24 EUR; package_commit RUN.json 26c2e47d / receipt 26c2e47d`（F2 同理）。
- **作业内预检：** 三个作业体各一次，`PREFLIGHT OK`，v4 元数据检查通过。
- **STATUS 中的 `NOTE:ALLOW_UNREGISTERED=1 in solve mode - tests only`：** 冒烟按设计用 `ALLOW_UNREGISTERED=1`（作业体固定写法），运行器每次都记这一行，不是问题。

### 4.1 冒烟之后的不提交演练（指南步骤 D1；"0 NOTE"）

在同一副本中（冒烟已 PASS、`./repo` = 包提交）用授权文件与一个权限 600 的占位许可路径运行 `hpc/hpr_submit.sh --auth-file ... --motd-checked --dry-run`。本机没有 `qsub`，脚本在 dry-run 中只检查 `command -v qsub`、从不调用，所以放了一个名为 `qsub` 的桩（被调用就打印 `STUB_QSUB_CALLED` 并退出 99）。结果（`logs/dry_after_smoke.txt`，bash 5.3 与 bash 4.2 相同）：**exit 0；0 条 `DRY-RUN NOTE`**；3 行 `DRY-RUN: qsub`（F1 → F2 `after:F1` → 批级 `afterany:F1:F2`）；最后一行 `DRY_RUN_OK: nothing submitted (...; 3 jobs; 0 check(s) above would refuse a real submission)`；桩未被调用；未创建 `runs/batch6`。不放桩时只多一条 `qsub not found (login node?)`（`logs/smoke_drill.txt`），HPC 登录节点上不会出现。

## 5. 判定（指令第 3.2 条）

| 判据 | 结果 |
|---|---|
| dry-run 以 `DRY_RUN_OK` 结束，依赖顺序 F1 → F2（`after:F1`）→ 批级（`afterany:F1:F2`） | **满足**（冒烟前、冒烟后，bash 5.3 与 bash 4.2） |
| SMOKE PASS | **满足**（`SMOKE_RESULT:PASS`） |
| 目标值与期望值相对差 ≤ 1e-6 | **满足**（F1、F2 均为 0.000e+00，逐位相同） |
| 批级后处理 exit 0 | **满足**（`RUNNER:...:batch:exit=0`，`POSTPROC_ERRORS:0`，`DONE`） |
| 0 NOTE | **满足**（冒烟后的 dry-run 0 条 NOTE；冒烟前的 NOTE 为"缺授权文件 / 冒烟未通过"，属预期） |
| 演练包不得上传 | 演练全部在 `/home/jin/v4w14/` 的解压副本中；交付包 `hpc_package_v4` 未被写入（`runs/` 不存在） |
