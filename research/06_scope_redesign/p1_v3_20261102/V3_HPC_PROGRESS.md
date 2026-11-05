# V3 HPC 正式运行包——进度（台账 V14）

- 指令：`V3_HPC_PACKAGE_INSTRUCTION.md`，SHA256 `29dc0b0fafd0731e57cf85d054eaebc8a44ebaa10f4446dcfbbe0a8ba3b3ade1`，与 `V3_HPC_PACKAGE_SHA256.txt` 一致（2026-11-04 00:25 SGT 核对）。
- 开始条件（用户 2026-11-04 授权的补充）：V27 主体已结束（`V3_REPORT_SUPPLEMENT07.md` 第 8 节已推送，头提交 `5e372e5d`），第 8.4 节由另一个会话补写，视为满足。
- 工作位置：新 worktree `/home/jin/wt_v3_hpc`，分支 `codex/v3-hpc-20261104`（自 `5e372e5d`）；不进入 `/home/jin/wt_v3_20261102`、`/home/jin/v3s/`，不碰 `work/p1_v3_20261102/cloud_results/`。会话脚本 `/home/jin/v3h/`（镜像 `scripts/wsl_v3h/`），结果 `results_project/v3hpc/`（主检出）。
- 复制到 `work/p1_v3_20261102/`：本会话新建的文件随时复制；`RUN_PLAN_V3.md`、`V3_RULES.md` 等共用文件等 `V3_PROGRESS.md` 末尾出现 V27 会话的关机记录后再复制。
- 用户 2026-11-04 的决定：(1) S-A 按登记定义 η = 1（"S-A 单价为全成本，已含船用燃料与运营费用，货损不再另计，避免重复计算"），核对时允许船运链路的 `marginal_cost` 与 `efficiency` 两个字段不同；(2) 构建路径字符串在构建前登记为来源差异。冒烟直接开始（WLS 空闲、AnyConnect 已断开）。

| 步骤 | 状态 | 提交 |
|---|---|---|
| 0 准备 | worktree、忽略输入（`results_project` 链接主检出，6 个忽略文件复制）；`5e372e5d` 试构建：与 `1bddacb7…` 全部变量逐位相同，元数据只差构建路径 | — |
| 1 规则与小修 | `V3_RULES.md` 第 2.3 节末、第 3.3 节、第 8.3 节、第 10 节第 4、7 条、第 12 节；S-A 主值（`baseline.yaml`）；注册表等级；载体份额缺键报错；`DIRECT` 单一来源；四个玩具网络测试；`BATCH_DEF_2920x3h.json` 注记 | `a1ef782b` |
| 2 构建 F1–F4 与核对 | 构建 `a1ef782b`（约 4 分钟）；核对全部通过（`evidence/hpc/F_REBUILD_CHECK.json`）；静态检查两根全过；F1 `8b5fd663…`、F2 `e2837e4a…`、F3 `c4eb7c44…`、F4 `0bbe235e…`；登记 `RUN_PLAN_V3.md` 第 24 节（含冒烟计划、闸门预告、S-A 事先估计）；第 12.3 节计数笔误（810 → 270）核对后更正 | `a4607714`（已推送） |
| 3 本机冒烟（2 次） | 2026-11-04 01:24–01:42 SGT，额度 2 / 2：一体化 329.7056、`no_new_xb` 342.2687 bn，都 optimal、C1 111、`ACCEPTED_LAYER2`；B6 12.5631（S-B 12.5665，−0.0034）；失败闸门都在预告内；记录 `RUN_PLAN_V3.md` 第 25 节 | 本次提交 |
| 4 预测 | `RUN_PLAN_V3.md` 第 26 节（两参照并列与结构差异） | 本次提交 |
| 5 `RUN_PLAN_HPC_V3.md` | 写成；PROPOSED：TimeLimit 1,296,000 s、walltime 376 / 378 h、进程 1 超时 7,200 s、批级 48 h；参考迭代 350 / 250；运行器四运行扩展、启动锁、PROPOSED 拒绝；定义文件 `batch_def/BATCH_DEF_2920x3h_v3hpc.json` | 本次提交 |
| 3–5 提交 | 冒烟记录、预测、`RUN_PLAN_HPC_V3.md`、四运行运行器、定义文件、操作指南、16 项新测试 + 54 项回归通过 | `917c8b63` |
| 6 部署包 | `work/p1_v3_20261102/hpc_package_v3/`，COMMIT `1e7b503c`（作业体 BUILD_ONLY 文字修正后重打），46 文件，373,689,593 B，`SHA256SUMS` `2ce8e5cd…`，一致性 53 行全部一致；旧包改名 `hpc_package_v3_superseded_917c8b63/` 保留 | `1e7b503c` |
| 6 干跑（旧包 `917c8b63`） | 全过：预检（除 licence / resources）OK、284/284、四运行 BUILD_ONLY 截短 56 时段 `BUILD_CHECK passed`、作业体 build_only F3 exit 0、PROPOSED 下 formal 作业体被拒（exit 2）；`/home/jin/v3h/dry_20261103T175805Z/DRY_RUN_HPC.txt` | — |
| 6 泄露扫描 | 许可值 0、键名 / ssh / 主机 0；IP 形 30 处全部归类为非泄露（1.1.1.1、版本号、内核版本）；`evidence/hpc/leak/`（未提交） | — |
| 7 报告 | `V3_REPORT_HPC_PACKAGE.md` 第 0–11 节已写，留有占位：`DRY2_PLACEHOLDER`（新包干跑）、`COMPUTE_PLACEHOLDER`、`DISK_PLACEHOLDER`、`FULL_PLACEHOLDER`（全量测试）、`COMMIT_PLACEHOLDER`（提交、推送、复制） | 未提交 |

**交接（2026-11-04 02:10 SGT，上下文将满）：**

- **后台任务 1：全量测试** `tests/research`（提交 `1e7b503c`，18:03:52 UTC 开始，预计约 1.5 h，超时 7,800 s）。结果写入 `/home/jin/v3h/full_tests.out`（末尾有 passed / failed 汇总与 `end` 行）。全量测试运行期间不要跑干跑、stand-in 测试或任何 `s2_solve.py`。
- **后台任务 2：只读独立审查**（子代理，审查 `5e372e5d..HEAD` 的运行器、启动锁、作业体、提交脚本、`b4_batch4.py`、`batch_def.py`）。结果只以通知返回，没有落盘；如果丢失，就新开一个只读审查，不跑测试。
- **只读审查已返回（2026-11-04 约 02:25 SGT，6 条，没有发现"> 2 个会话"或"PROPOSED 下能启动正式求解"的路径）：**
  1. **【阻断，前提：Atlas 的 bash < 4.4】** `set -u` 下空数组展开报错：`run_batch4.sh` 的 `case " ${PAIRS[*]} "`、`hpr_submit.sh` 的 `qsub "${W[@]}"`。**已改**为 `${PAIRS[*]:-}`、`${W[@]+"${W[@]}"}`（未提交，未测）。
  2. 【非阻断】`.solve_start` 早于真正的 WLS 会话（`b4_split_solve.py:148` 的 `gp.Env()`，在 import 与读 0.9 GB 标签之后）；`.solve_end` 晚于进程退出最多约 5 s。实际间隔 = 330 + δ_后 − δ_前，可能小于 330 s。建议：`b4_split_solve.py` 在 `Env()` 之后写 `split/ENV_START`、`with` 块结束后写 `ENV_END`；运行器持锁直到 ENV_START 出现（或进程已死），间隔按这两个文件计算。**待决定是否实现。**
  3. 【非阻断】前序运行失败但没写 STOP 时（F1 预检失败 exit 1、被 qdel、求解中被杀），F3（afterany:F1）照常开跑。建议：作业体对 afterany 前序要求 `<X>/.ended` 存在或已停批，否则写 `STOP_SAFE:PREDECESSOR_NOT_ENDED`；正式作业 PREFLIGHT_FAILED 时也写 STOP_SAFE。
  4. 【非阻断，v2 旧问题】POST_ONLY 停批时跳过 post_run（`run_batch4.sh` 末尾的 `if ! halted` 与 `halted ||`）。建议 POST_ONLY 下对所有已结束运行都做 post_run。
  5. 【非阻断】无 BATCH_DEF 时也有启动锁（STATUS 多出 START_LOCK 行，残留锁目录会导致新的 STOP_SAFE），export/batch 多了 `BASE_CHECK_F*.json`：注释"Without a definition: v2"要改写或登记这些变化。
  6. 【非阻断】`hpr_status.sh` 与指南 H3 写"几分钟"，但 act ≥ 2 时会合法持锁最多 2 h；`hpr_submit --resume` 不检查残留锁（建议发现锁目录就拒绝）；F2 最坏情况可能等两个 WMAX，而 walltime 只算一个（余量 870 s）。
  - **审阅端意见（2026-11-04，用户转达）：** ① 第 1 条用对所有 bash 版本都安全的写法（`${arr[@]+"${arr[@]}"}`）修复，并尽量在 bash 4.2 下实测（本机编译 bash 4.2 或容器）；无法实测时，在 `HPC_OPERATOR_GUIDE_V3.md` 第一步加两项：登录节点 `bash --version`；运行 `hpr_submit.sh` 的不提交演练模式（只打印 qsub 命令），用户确认输出无误后才正式提交——没有演练模式就加一个（如 `--dry-run`）。② 第 2 条同意列为 PROPOSED，本次不改求解路径；报告写明理由：同时只有 F1、F2 两个会话，不超过上限；F3、F4 开会话前还有约 40 分钟无许可的构建，间隔自然远大于 330 s。③ 第 3、4、6 条按计划修；第 3 条另在操作指南写明撤销正式作业时要同时撤销依赖它的作业；F2 walltime 余量并入 PROPOSED 取值一起重算（`RUN_PLAN_HPC_V3.md` 第 2.2、12 节）。④ 第 5 条改注释即可。其余按交接要点的顺序继续。注意：`case " ${PAIRS[*]:-} "` 这一处是字符串展开，`:-` 在 4.2 下安全；其他数组展开统一用 `${x[@]+"${x[@]}"}`。
  - **bash 4.2 实测准备（2026-11-04 约 02:30 SGT）：** 后台任务 `bash /home/jin/v3h/bash42.sh`：从 ftp.gnu.org 下载 bash-4.2 源码到 `/home/jin/v3h/bash42/`，本地编译（不安装），成品 `/home/jin/v3h/bash42/src/bash`；编译失败就按审阅端意见走"指南加 `bash --version` + `hpr_submit.sh --dry-run`"的路线。实测方法：用 `/home/jin/v3h/bash42/src/bash` 运行 `run_batch4.sh`（stand-in，`--only` 与 `POST_ONLY`）和 `hpr_submit.sh --dry-run`，并 grep 所有改过的脚本里 `"${...[@]}"` 未加 `+` 保护的展开。全量测试运行期间不改共用脚本（测试会在运行时读取它们）。
  - **下一步：** 修第 1 条（已改）以及建议能小改的第 3、4、6 条；第 2 条改动了求解路径附近的 `b4_split_solve.py`，在报告里列为 PROPOSED 由审阅端决定，或者实现后补测试；全部修改后跑 `test_v3_hpc_runner.py` 与运行器回归（全量测试结束之后），重新打包到新目录（当前包改名 `hpc_package_v3_superseded_1e7b503c`），重做干跑；报告第 6、10 节写明审查发现与处理。
- **未提交的改动：** `V3_REPORT_HPC_PACKAGE.md`（第 7–11 节与占位）、`tests/research/test_v3_hpc_runner.py` 新增的 `test_job_body_smoke56_with_the_definition`（尚未运行）、`evidence/hpc/leak/`、本文件。
- **剩下的步骤：** (1) 读全量测试结果（已知基线：3 项与 v3 无关的失败）；(2) 复核审查意见，阻断项先修代码与测试，再重打包到新目录（旧包改名保留）；(3) 全量测试结束后跑新测试 `bash /home/jin/v3h/ut_runners.sh tests/research/test_v3_hpc_runner.py`，再在新包上重做干跑 `bash /home/jin/v3h/dry_hpc.sh /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3`；(4) 补全报告占位（计算约 2.7 h / 4 h 截至此刻，磁盘约 4–5 GB / 40 GB；报告写明包内代码 `1e7b503c` 之后只改 `research/` 文档与 `tests/`，附 `git diff --stat 1e7b503c HEAD -- . ':(exclude)research' ':(exclude)tests'` 为空的证明）；(5) 提交（消息文件先写、再 `bash /home/jin/v3h/commit.sh <msg>`）→ `bash /home/jin/v3h/push.sh` → 推送后再跑 `bash /home/jin/v3h/scan_h.sh post`；(6) 复制到 `work/p1_v3_20261102/`：只复制本会话新建的文件（`V3_HPC_PROGRESS.md`、`RUN_PLAN_HPC_V3.md`、`HPC_OPERATOR_GUIDE_V3.md`、`V3_REPORT_HPC_PACKAGE.md`、`batch_def/BATCH_DEF_2920x3h_v3hpc.json`、`hpc_v3/`、`evidence/hpc/`、`scripts/wsl_v3h/`）；`RUN_PLAN_V3.md`、`V3_RULES.md`、`batch_def/BATCH_DEF_2920x3h.json` 要等 `work/p1_v3_20261102/V3_PROGRESS.md` 末尾出现 V27 会话**新的**关机记录（第 8.4 节那次开机之后）再复制——截至 18:05 UTC 仍只有 00:16:33 SGT 的旧记录；**用户 2026-11-04 补充：V27 会话已于约 02:10 SGT 收尾（实例已关机并核实），到第 6 步时重新读 `V3_PROGRESS.md` 末尾确认这条关机记录，确认后即可复制这三个文件**；(7) 停下，等审阅端与用户决定 PROPOSED 取值。不连 HPC、不连云、不上传。

恢复点：见上面的"交接"（冒烟已完成，额度 2 / 2 用尽，不得再调用 Gurobi）。计数：本机 Gurobi 0 / 2；本机计算约 0.6 小时 / 4 小时（构建 4 分钟、静态检查、两次核对约 25 分钟含一次卡死后重跑）；磁盘新增约 0.5 GB / 40 GB。

## 无人值守补充授权（`V3_HPC_UNATTENDED.md`，SHA256 `bd985bc9a7a30d247f03e1fa61048941d79d8870fb9b348a696449bcfe05f8df`，与登记文件一致；2026-11-04 02:45 SGT 开始执行）

- bash 4.2 已编译成功：`/home/jin/v3h/bash42/src/bash`（4.2.0，源码 SHA256 `a27a1179…`，需 `CC="gcc -std=gnu89"`）；实测 `set -u` 下 `"${a[@]}"` 报 unbound，`${a[@]+"${a[@]}"}`、`${a[*]:-}` 安全。
- 第 1 节取值（审阅端代用户决定）：U = F1 外推上界 261 h（350 次 × 1,679 s × CPU 1.6；`RUN_PLAN_HPC_V3.md` 第 2.1 节）→ T = max(72, min(240, 2U)) = **240 h = 864,000 s**；止损 0.80 × T = 691,200 s，参考迭代 F1/F3 350、F2/F4 250；进程 1 超时 **5,400 s**；walltime 按 v2 公式：基础 330 + 5,400 + 871,200 + 32,400 + 7,800 + 1,800 = 918,930 s；F2 再加两个等待上限（等 F1 启动 + 启动锁，审查第 6 条），F3、F4 加一个（启动锁）；每个作业余量 ≥ 2 h，按"F3 同 F1、F4 同 F2"取同对中较保守的一个 → **F1 = F3 = 260 h，F2 = F4 = 262 h**；资源不变；批级 walltime 48 h（第 1 节未列，取原提议的保守值）；`limits_status` 改为 REGISTERED。
- 剩余步骤：(1) 全量测试结果；(2) 修审查第 1（全部数组展开）、3、4、5、6 条 + `hpr_submit.sh --dry-run`；(3) 写入取值（定义文件、`RUN_PLAN_HPC_V3.md` 新节与第 2.2、3、10、12 节）；(4) 更新测试并跑新测试、运行器回归、bash 4.2 下的替身测试；(5) 重新打包（旧包改名 `hpc_package_v3_superseded_1e7b503c`）、干跑；(6) 指南开头"用户上 HPC 操作清单"(a)–(i)；(7) 报告补全、泄露扫描、提交推送、复制（共用文件先确认 V27 关机记录）、推送后扫描、最终状态行。

### 无人值守执行记录（2026-11-04 02:35 SGT 起）

- **全量测试（提交 1e7b503c，18:03–18:36 UTC，1,946 s）：** 831 通过、4 失败、0 跳过。`test_s1_built_networks::test_static_validation_passes_on_reload` 是已知基线；`test_s3_gates.py` 三项（`test_static_b_gates`、`test_b12_with_override`、`test_b12_s3b_rebuilt`）与它同一根因：基点 5e372e5d 的配置已有 `cross_border.stock_mode`，旧的 S3-5 网络没有，B12 的 `switch_metadata_matches` 为 False（`evidence/hpc/tests/S3_GATES_B12_DIAGNOSIS.txt`）。`scripts_project/v5`、`phase4_static.py`、`test_s3_gates.py` 自基点未改；本 worktree 的 `results_project/s3_5` 链接存在，所以这三项不再跳过（以前的 worktree 跳过）。`test_s4c_0.py` 两项本次通过（WACC 表可达）。按第 2 节"其他情况：最保守、可逆"：判为与基线同类，不改闸门代码，记录证据。
- **代码修改（未提交）：** 审查第 1 条 `pair_runs` 的 `${out[*]:-}`；第 3 条 `hpr_job.sh` 前序检查 `PREDECESSOR_NOT_ENDED` 与正式作业预检失败写 `STOP_SAFE:PREFLIGHT_FAILED`；第 4 条 `run_batch4.sh` 的 POST_ONLY 对每个已结束运行做后处理（停批时也做）；第 5 条注释；第 6 条 `hpr_status.sh` 锁说明与 STOP 文件显示、`hpr_submit.sh --resume` 遇锁目录拒绝、`b4_batch4.py walltime_components` 有定义时 F2 计两个等待、`hpr_consistency.py` 加余量行；`hpr_submit.sh --dry-run`。
- **取值已写入：** 定义文件 REGISTERED（864,000 / 5,400 / 260-262-260-262 h）；`RUN_PLAN_HPC_V3.md` 第 14 节与第 2.2、3、4、5、10、12 节。须知：T = 240 h 小于 U = 263.7 h，止损约在每次迭代 1,840–1,860 s 时触发（第 14.2 节），写入报告。
- **测试：** `test_v3_hpc_runner.py` 11 / 11 通过（含 3 项新测试）。运行器回归在后台（`/home/jin/v3h/ut_reg.out`）。
- **下一步：** 回归结果 → `bash /home/jin/v3h/ut_bash42.sh`（bash 4.2 下的替身测试）→ 提交 → 旧包改名 `hpc_package_v3_superseded_1e7b503c` → `pkg.sh` 重新打包 → `bash42_static.sh <包>` → `dry_hpc2.sh <包>`（bash 5）与 `BASH_BIN=/home/jin/v3h/bash42/src/bash dry_hpc2.sh <包>`（bash 4.2）→ 全量测试再跑一次 → 报告 → 泄露扫描 → 提交推送 → 复制 → 最终行。注意：旧的 `dry_hpc.sh` 最后一步在 REGISTERED 包上会真正启动正式作业体，**不得再用**，改用 `dry_hpc2.sh`。
- **2026-11-04 03:10–03:40 SGT：** 提交 `7d22dda1`（登记的时限、审查第 1、3–6 条、`--dry-run`、测试）。运行器回归 54 / 54；`test_b4p_split` + `test_v3_runners` 19 / 19；bash 4.2 下替身测试 38 / 38。旧包改名 `hpc_package_v3_superseded_1e7b503c/`；新包 `hpc_package_v3/`：COMMIT `7d22dda1`，46 个文件，`SHA256SUMS` 的 SHA256 `63d682bbe743ce220bec747aede81d6423d3afd1cac53b7ffdbc2345e970345c`，一致性 57 / 57。bash 4.2 静态检查 18 / 18、新语法命中 0；干跑 bash 5 与 bash 4.2 都通过（`evidence/hpc/dry/`）。旧 `dry_hpc.sh` 加了拒绝运行。提交前泄露扫描 pre2：许可值 0，实际命中 0。共用文件：V27 第二次关机 02:12:51 SGT 已确认，`work/` 中三个文件与基点相同，可以覆盖。没有在最终提交上再跑全量测试（不在授权第 2 节的要求内，且会超过 4 小时计算上限）。
- **剩下：** 报告提交 → 推送 → 推送后扫描 → 最终行 → 复制到 `work/`。
- **推送与推送后扫描（03:30 SGT）：** `f141b935` 已推送到 `origin/codex/v3-hpc-20261104`（`git ls-remote` 核对相同）；推送后泄露扫描 post（6 个提交、分支目录、包、会话脚本）：许可值 0，键名 / ssh / 主机 0，IP 形命中都属于已归类的非泄露类别，实际命中 0（`evidence/hpc/leak/LEAK_SCAN_post.json`、`LEAK_CLASSIFY_post.txt`）。复制到 `work/`：本行所在提交推送后执行（`copy_work.sh`，逐文件比对）。

**最终状态（2026-11-04 03:32 SGT）：可以上 HPC。** 包 `work/p1_v3_20261102/hpc_package_v3/` 的 `SHA256SUMS` SHA256 `63d682bbe743ce220bec747aede81d6423d3afd1cac53b7ffdbc2345e970345c`；包 COMMIT `7d22dda112a3c18ed57e8c061d95e51915980417`，交付提交 `f141b935`（已推送），本行另以一个只改本文件与扫描证据的提交推送；T = 864,000 s（240 h）；walltime F1 260 h、F2 262 h、F3 260 h、F4 262 h，批级 48 h（冒烟 4 h）。剩下的只有用户的步骤：按 `HPC_OPERATOR_GUIDE_V3.md` 开头的清单连 VPN、上传、提交作业。

**V3.1 最终状态（2026-11-05 20:40 SGT，决策清单第 195 项，`work/p1_v3_fix_20261105/V3_FIX_INSTRUCTION.md`）：可以上 HPC。** 新包 `work/p1_v3_20261102/hpc_package_v3_1/`（v3 包 `hpc_package_v3/` 原样保留）：`SHA256SUMS` 的 SHA256 `b82163615e13797139cb9353851791a9cff5ad3109335bda30c81a2ba44be1ee`，包 COMMIT `d3b9a3bca18755b50397f31d4b61abe39fb50c3f`（分支 `codex/v3-fix-20261105`），交付提交 `7faefbe5` 已推送，本行另以一个只改本文件、进度与扫描证据的提交推送。修正：燃料舱净零改为逐计量流量为零的等价写法（四网络前提实测满足）；静态零松弛检查 F1–F4 PASS（打包闸门）；失败窗口 F1_M01、F2_M02 预处理通过；56×3h 回归（冒烟作业体本机演练）`SMOKE_RESULT:PASS`，目标相对差 ≤ 2.5e-9，12 个参与者 Owen 符号不变；全量测试 856 通过 / 4 项基线失败；干跑 bash 5 与 4.2 通过；泄露扫描实际命中 0。TimeLimit 864,000 s、walltime F1 / F2 / F3 / F4 = 260 / 262 / 260 / 262 h、批级 48 h、冒烟 4 h、资源、验收与预测都不变；本机 Gurobi 4 / 6。上传到新目录 `/hpctmp/$USER/hpr31/`，正式 `runs/batch5`，冒烟 `runs/smoke56_v31`（HPC 上 `hpr3/runs/batch4` 的停批记录不动）。报告 `V3_REPORT_FIX.md`。剩下的只有用户的步骤：按 `HPC_OPERATOR_GUIDE_V3.md`（v3.1）开头的清单连 VPN、单路上传、`sha256sum -c`、登录预检、冒烟（必须 PASS）、两次不提交演练，再提交 F1–F4 与批级作业。
