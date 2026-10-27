# 独立审查记录（HPR H7）

审查方式：未参与准备的子代理（全新上下文），只给指令原文、`RUN_PLAN_HPC.md`、`HPC_FACTS_20261026.md`、包 v9（提交 `69b0b7d1`）、`HPC_OPERATOR_GUIDE.md`、`PRE_HPC_CHECKLIST.md` 与相关代码路径；不给准备过程的结论、进度与证据；只读（不运行测试 / 脚本 / 求解，不读许可文件与扫描模式文件）。第 2 节为第一轮审查原文（原样记录，未改动）；第 3 节为执行端对每条发现的处理；第 4 节为第二轮复核原文。

## 1. 第一轮：输入

- 包 v9：`work/p1_hpr_20261027/hpc_package/`（提交 `69b0b7d1`，36 文件）。
- 文档：`RUN_PLAN_HPC.md`（`1f62176f`）、`HPC_OPERATOR_GUIDE.md`、`PRE_HPC_CHECKLIST.md`（H-P13 / H-P14 待填）、`HPC_FACTS_20261026.md`。
- 代码：`scripts_project/b4_batch4.py`、`b4_split_solve.py`、`s2_solve.py`、`research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/{run_batch4.sh,preflight.sh}`、`research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/`、`tests/research/test_hpr_two_jobs.py`。

## 2. 第一轮审查原文

## 独立审查报告 —— HPC 部署包 v9 与操作手册（HPR，第四批 F1 / F2，NUS Atlas PBS Pro）

审查人：独立子代理（未参与准备；只读；未运行任何测试、脚本或求解；未读取任何许可文件或泄露模式文件）。审查日期：2026-10-27。

---

## 1. 审查范围与方法

**读过的材料（全文）**
- 指令：`/home/jin/wt_hpr_20261027/research/06_scope_redesign/p1_hpr_20261027/HPR_CLAUDE_CODE_INSTRUCTION.md`（含用户补充的步骤 D2 要求）
- 运行计划 `RUN_PLAN_HPC.md`、实测事实 `HPC_FACTS_20261026.md`、操作手册 `HPC_OPERATOR_GUIDE.md`、检查单 `PRE_HPC_CHECKLIST.md`（同目录）
- 包 v9 `/mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027/hpc_package/` 全部 36 个清单文件：`run_batch4.sh`（547 行，逐行）、`preflight.sh`、`pack_results.sh`、`hpc/`（7 个脚本）、`pbs/`（6 个 .pbs + `HPC_PLAN.txt` + `MAKE_PBS.log`）、`env/`（6 个）、`REFERENCE_VALUES.json`、`SHA256SUMS`、`HPC_PACKAGE_MANIFEST.json`、`COMMIT`
- 代码：`scripts_project/b4_batch4.py`（全文）、`b4_split_solve.py` / `s2_solve.py`（分进程相关部分）、`tests/research/test_hpr_two_jobs.py`（测试清单与作业体测试）、`hpc_package_src/make_hpc_package.sh`（复制与拒绝步骤）
- 本分支 `82c32c53..69b0b7d1` 四个提交的 `git log`、`git diff --stat`，以及 `run_batch4.sh` / `preflight.sh` / `preflight_dfx.sh` / `b4_batch4.py` / 测试替身的完整补丁

**做过的核对**
1. `sha256sum -c SHA256SUMS`：36 / 36 OK；清单与 `SHA256SUMS` 哈希一致；`COMMIT` = `69b0b7d1…` = worktree HEAD。
2. 包内副本与来源逐字节 `cmp`：`run_batch4.sh`、`preflight.sh` = `p1_b4p_20261026/cloud_package_b4/`；`pack_results.sh` 与 `env/*` 六文件 = `p1_m10p_20261022/cloud_package/`；`hpc/*` 七文件 = `hpc_package_src/`；`RUN_PLAN_HPC.md` / `HPC_OPERATOR_GUIDE.md` / `HPC_FACTS_20261026.md` / `REFERENCE_VALUES.json` = 交付目录版本；这些来源在 HEAD 上均无未提交改动。
3. 代码归档 `code_69b0b7d1.tar.gz`：1,564 个条目，无 `research/`；`scripts_project/b4_batch4.py`、`s2_solve.py` 的 SHA256 与 `git show HEAD:` 相同；后处理链所需模块与 `configs/research/baseline.yaml` 均在；无 `*.lic`。
4. 登记常数：从 `RUN_PLAN_HPC.md` §1–3、§9、§10、`b4_batch4.py`、`run_batch4.sh` 顶部、`preflight.sh`、六个 `.pbs`、`hpc/hpr_job.sh`、`pbs/HPC_PLAN.txt` 独立抽取并复算（见第 3 节）。
5. 执行路径：`pbs/hpr_f1.pbs` → `hpc/hpr_job.sh`（formal）→ `run_batch4.sh --only F1`（阶段 0 → 进程 1/2/3 → `post_run` → 分级 → 退出码）；F2（`WAIT_START_OF=F1`、`-W depend=after:`）；批级（`POST_ONLY=1`）；冒烟与 BUILD_ONLY 作业体；`hpr_submit.sh` / `hpr_status.sh` / `hpr_install_env.sh` / `hpr_preflight_login.sh`。
6. 泄露扫描（只计数）：包内文本文件、手册、检查单、`hpc_package_src/`、分支补丁文本、代码归档（单遍内存扫描），模式为 WLS 键名（不分大小写）、`KEY=` 行、IPv4、`ssh -p` / `scp -P`、`用户@主机` 字面量、密码词、本机用户名路径、云厂商主机词。
7. 本机环境核对（只读）：`wsl -l -q` 确认发行版名为 `Ubuntu`；`ssh -V` 为 `OpenSSH_for_Windows_9.5p2`（用于评估手册中 scp 命令）。

---

## 2. 发现清单

**阻断项：未发现。** 以下均为非阻断；其中 F-01 ~ F-06、F-10、F-13 建议在上传前修正（手册 / 作业体文字或小逻辑；手册改动需重建包与 `SHA256SUMS`），F-07 / F-08 / F-14 建议在步骤 E 之前确认或修正。

| 编号 | 分级 | 位置 | 问题 | 后果 | 建议 |
|---|---|---|---|---|---|
| **F-01** | 非阻断（建议修正） | `HPC_OPERATOR_GUIDE.md` 步骤 A2 第 24 行 | `[PowerShell] ssh … "mkdir -p /hpctmp/$USER && test ! -e /hpctmp/$USER/hpr && echo READY …"` 用双引号，`$USER` 在 **PowerShell** 中先被展开（Windows 下 PowerShell 无 `$USER`，为空），远端实际执行 `mkdir -p /hpctmp/ && test ! -e /hpctmp//hpr` | 总是打印 `READY`：即使 `hpr` 已存在也不报 `hpr EXISTS`，随后 `scp -r … :/hpctmp/<用户>/hpr` 会把包复制成 `hpr/hpc_package/`，A3 的 `sha256sum -c` 找不到文件；若 `/hpctmp/<用户>` 不存在则 `mkdir` 也未真正创建 | 远端命令改用单引号（`ssh … 'mkdir -p /hpctmp/$USER && …'`）或把 `$USER` 写成 `<你的用户名>`；手册头部"在 atlas8 的 bash 里可直接用 `$USER`"的说明不适用于 PowerShell 行 |
| **F-02** | 非阻断（建议修正） | 手册 A1 第 17–20 行 | `Get-ChildItem … \| Measure-Object` 只数顶层条目（15 个：9 个文件 + `env/ hpc/ networks/ pbs/` 等），而"成功判据"是"与 `HPC_PACKAGE_MANIFEST.json` 中的文件数一致"（清单 36 个，文件夹含清单共 37 个）；并引用用户手上没有的 `HPR_REPORT.md` | 用户第一步就得到"不一致"的假失败 | 改为 `Get-ChildItem -Recurse -File … \| Measure-Object`，并直接写出期望数（37，含清单）或改引用包内 `SHA256SUMS` 行数 36 |
| **F-03** | 非阻断（建议修正） | 手册 C3 第 88 行；`hpc/hpr_preflight_login.sh` | `bash hpc/hpr_preflight_login.sh \| tail -15`，但脚本输出约 40 行（预检段 `tail -25` + 配额 + PBS + 维护通知 + 结尾），"成功应看到"的 `licence file present…`、`all <N> files OK`、通常连 `PREFLIGHT OK` 都在前面被截掉 | 用户按判据找不到成功标志 | 去掉 `tail -15`，或改为 `> login_preflight.txt 2>&1; grep -E "licence file|files OK|PREFLIGHT OK|HPR_PREFLIGHT_LOGIN"` |
| **F-04** | 非阻断（建议修正） | 手册 D3 第 111 行；`hpc/hpr_job.sh` 第 104–109、155–177 行；`RUN_PLAN_HPC.md` §9 冒烟行 | `SMOKE_STATUS.txt` 由 **批级** 那次 `hpr_job.sh` 调用写出，而 `WLS` 变量只在 F1 那次调用中被 `curl` 赋值（三次是独立的 bash 进程），批级调用里 `WLS=skipped` → `SMOKE_STATUS.txt` 必然是 `WLS_TOKEN_HTTP:skipped`；真实状态码只在 `runs/smoke56/PBS_JOBS.txt` 的 `WLS_TOKEN_HTTP:` 记录中。替身测试只断言 `PBS_JOBS.txt`，未断言 `SMOKE_STATUS.txt` 中的该行 | 手册写"成功：含 `WLS_TOKEN_HTTP:302`（或 200）"，用户看到 `skipped` 会误判冒烟失败（`SMOKE_RESULT` 本身不受影响） | 作业体在批级调用中从 `PBS_JOBS.txt` 读取最后一条 `WLS_TOKEN_HTTP:` 写入 `SMOKE_STATUS.txt`；或手册改为"`WLS_TOKEN_HTTP` 看 `runs/smoke56/PBS_JOBS.txt`" |
| **F-05** | 非阻断（建议修正） | 手册 B2 第 51、53 行；G2 第 178 行 | 本机 Windows OpenSSH 为 **9.5p2**，`scp` 缺省走 SFTP 协议：(a) G2 第二条的大括号展开 `{STATUS.txt,PBS_JOBS.txt,…}` 是远端 shell 功能，SFTP 模式不支持，会报 `No such file`；(b) B2 远端路径 `~/.gurobi/gurobi.lic` 的 `~` 展开依赖服务器端扩展（atlas8 的 sshd 版本待确认），旧 sshd 下会失败 | 用户在 B2 或 G2 卡住（可恢复，但 B2 失败会让用户尝试别的办法放许可文件，增加误操作风险） | B2 远端路径写成相对家目录的 `.gurobi/gurobi.lic`；G2 拆成四条 `scp`（或统一加 `-O` 用旧协议） |
| **F-06** | 非阻断（建议修正或写明） | `hpc/hpr_job.sh` 第 50 行；`RUN_PLAN_HPC.md` §7.4–7.5（第 88–89 行）；手册 G1 | 批级作业要求 `runs/batch4/F1/.ended` 与 `F2/.ended` 都存在，否则 `not_ready` 退出 2。但当 F1 先触发 `STOP` / `STOP_SAFE`（如 `MEMORY`、`PROJECTION`、`BASE_NETWORK_SHA256`）而 F2 尚未进入进程 2 时，F2 运行器按设计记 `NOT_STARTED_F2` 并退出 3，**不写 `F2/.ended`**（甚至 `F2/` 可能不存在）；随后批级作业必然 `not_ready` 退出 2，不做 §7.4 承诺的"照常重评与汇总、结果包标记 halted"，手册 G1 的"停批时文件名为 `*_halted_*`"也不会出现。RUN_PLAN §7.5 说 `afterany` 保证正常情况下不会发生，但停批正是会发生的情形 | 停批情形下没有 halted 结果包与 `BATCH4_SUMMARY`，用户按手册找不到文件；不影响正式运行成功的路径 | 批级作业放行条件改为：每个运行 `.ended` 存在，**或** `RUN_DIR` 下有 `STOP`/`STOP_SAFE` 且该运行无 `.started`（NOT_STARTED）；并补一条替身测试。或至少在 RUN_PLAN §7.5 与手册 F/G 写明此例外 |
| **F-07** | 非阻断（建议修正） | `run_batch4.sh` 第 183–196 行（`aux_threads`、`other_solve_running`、`free_anon_gib`、`wait_for_memory`）、第 168–171 行（`cg_anon_b`）；`hpr_job.sh` 第 84 行 | `--only` 模式下这几处仍扫描共享 `RUN_DIR` 下**另一作业**的运行（`.started` 无 `.ended`）：(a) F1 后处理各步的线程预算变成 48 − 16（无害，稍慢）；(b) 更要紧的是 `wait_for_memory`：当作业 cgroup 不可见时作业体导出 `MEM_MEASURE=rss` 但 **不设 `CGROUP_ROOT`**，运行器缺省 `CGROUP_ROOT=/sys/fs/cgroup`；在 cgroup v1 节点上 `/sys/fs/cgroup/memory/memory.stat` 的 `total_rss` 是**整节点**（含他人作业）的匿名内存，`free_anon_gib = 300 − 节点总量`；若 F1 落在 792 GB 节点且其他用户占用大，`free < 100` 且 F2 正在另一节点求解 → F1 的后处理被 `POST_QUEUED` 直到 F2 结束（可能数天），F1 可能因 walltime 被 PBS 终止 | 该情形下 F1 作业状态 E、后处理留给批级作业补做（幂等，结果最终仍可产出）；内存止损本身不受影响（用 RSS） | `--only` 模式下让 `other_solve_running` 恒为假（另一运行在别的作业 / cgroup 中，配额按作业计），或仅统计本运行；`aux_threads` 同理。纯 bash 改动，不触及解；补替身测试 |
| **F-08** | 非阻断（**上机前待确认**） | `preflight.sh` 第 84–87 行；`run_batch4.sh` 第 109 行；`HPC_FACTS` 未提及 | 硬性依赖 `/usr/bin/time`（GNU time）、`setsid`、`pgrep`、`timeout`。RHEL 系节点常**不预装** `time` 包；HPC_FACTS 没有核实。缺失时安装作业的预检 `tools` 节失败 → `PREFLIGHT:exit=1`、`INSTALL_END:exit=1`；手册 C2 的失败分支没有这一情形的处理（脚本提示的 `apt-get install` 在 HPC 上无意义） | 若缺失，用户在步骤 C 卡住，且无法自行修复（路径硬编码） | 步骤 A3 后加一条 `[bash@atlas8] ls -l /usr/bin/time && /usr/bin/time -v true && command -v setsid pgrep timeout`（登录节点与计算节点通常同镜像）；预备回退：conda-forge 的 `time` 包装到 `$HOME`，并让运行器 / 预检接受 `TIME_BIN` 覆盖（需补替身测试），或请管理员安装 |
| **F-09** | 非阻断（**待用户确认**） | `HPC_OPERATOR_GUIDE.md`（2 处）、`HPC_PACKAGE_MANIFEST.json`（2 处）、`networks/integrated_BUILD_RECEIPT.json`（7 处）、`networks/disconnected_BUILD_RECEIPT.json`（7 处）、`RUN_PLAN_HPC.md`（1 处）；交付目录同名文件及 `hpc_package_src/make_hpc_package.sh`（1 处） | 含本机 WSL Linux 用户名的路径（`/home/<本机用户名>/…`、`\\wsl.localhost\Ubuntu\home\<本机用户名>\gurobi.lic`）。这些文件会原样上传到 HPC。指令"不变的规则"要求账号名不写进任何文件，检查单 H-P8 的 R1 保留项未列此类命中（其扫描模式在仓库外，本审查未读取） | 泄露的是本机 Linux 用户名与本机目录结构，不含 HPC 账号、密码或许可；风险低 | 手册中改为 `<WSL 用户名>` 占位符（并说明 `wsl -l` 查看发行版名）；清单的 `h4_drill.file` / `networks.source` 可写相对路径；构建回执属 DFX 产物，建议说明保留原因。请用户确认是否接受 |
| **F-10** | 非阻断（建议修正） | `RUN_PLAN_HPC.md` §11 第 142 行；`hpc/make_pbs.sh`（无 `#PBS -o`）；手册 C2 / 附录 3 第 217 行 | RUN_PLAN 登记作业日志在 `/hpctmp/<用户>/hpr/pbs_logs/<作业名>.o<作业号>`，但 `.pbs` 未设 `-o`，PBS 缺省把 `-j oe` 的输出放回提交目录 `/hpctmp/<用户>/hpr/<作业名>.o<序号>`（手册写的是后者，且 PBS 文件名用序号不含 `.venus01`） | 文档不一致；用户按 RUN_PLAN 找不到日志 | 二选一：RUN_PLAN 改为包目录；或 `make_pbs.sh` 生成 `#PBS -o pbs_logs/` 并在 `hpr_submit.sh` / 手册中 `mkdir -p pbs_logs`（PBS 要求目录已存在） |
| **F-11** | 非阻断 | `hpc/hpr_submit.sh` 第 33–34 行 | `mkdir -p runs/batch4` 在任何 `qsub` 之前；若 `qsub F1` 因瞬时错误失败（退出 1），目录已存在，重跑被第 27–28 行拒绝（`runs/batch4 exists`），手册 E3 让用户联系审阅端 | 用户在一次无害的 qsub 失败后卡住 | F1 `qsub` 成功后再 `mkdir`，或失败时 `rmdir runs/batch4`（仅空目录） |
| **F-12** | 非阻断 | `hpc/hpr_install_env.sh` 第 30–31 行；手册 C2 第 84 行 | 安装被中断（walltime / 网络）留下的**半成品环境**被视为 `ENV:present`，`env_check` 必然 `key_all_equal=false`；手册只说"停下、发回"，没有恢复步骤 | 用户卡住 | 手册 C2 补一条：`ENV_INSTALL_FAILED` / 中断后 `rm -rf ~/miniforge3/envs/pypsa-earth` 再重提 C1；或作业体把 `ENV_CHECK` 失败且本作业刚创建环境的情形区分出来 |
| **F-13** | 非阻断 | `hpc/hpr_status.sh` 第 14 行；手册 F 第 155 行 | `grep … \| tail -8 \|\| echo "(none)"`：`\|\|` 作用于 `tail`（总是 0），`(none)` 永远不打印；手册写"应为 `(none)`" | 用户看到空段落，不知是否正常 | 用 `grep … > tmp; [ -s tmp ] && tail -8 tmp \|\| echo "(none)"` 的写法 |
| **F-14** | 非阻断（**待确认**） | `hpc/make_pbs.sh`（生成的六个 `.pbs`） | 没有 `#PBS -S /bin/bash`。PBS Pro 缺省用用户的登录 shell 运行作业脚本；若用户在 Atlas 的登录 shell 不是 bash（如 tcsh），`export A=1 B=2` / `${PBS_O_WORKDIR:?…}` / `exec bash …` 在作业里会失败 | 作业立即失败（可见于 `.o` 文件），不损坏数据 | 用户在 atlas8 执行 `echo $SHELL` 确认；或在 `make_pbs.sh` 中无条件加 `#PBS -S /bin/bash`（无副作用） |
| **F-15** | 非阻断（说明即可） | `preflight.sh` 第 43、49 行 | F1、F2 两个正式作业几乎同时在同一包目录跑预检，都写 `PREFLIGHT_BASE_CHECK.json`、`PREFLIGHT_ENV_CHECK.json`（同名文件竞争）；判定只用退出码，JSON 可能被交错写坏 | 仅影响这两个信息文件 | 文件名加 `${PBS_JOBID}` 或忽略 |
| **F-16** | 非阻断（D2 后决策） | `RUN_PLAN_HPC.md` §3 / §12.2（批级 12 核 / 120 GiB） | 后处理步骤（违反分析 / C1 / Owen）会重建 LP 模型，B4P 外推进程 1 峰值 72–92 GiB（v1 网络）；若正式作业内后处理未完成而由批级作业补做，120 GiB 的 cgroup 上限对 v2 网络是否够用取决于 D2 实测 | 超限会被 OOM 杀死 → `POSTPROC_ERROR`，需再补做 | 把"D2 的 `PEAK_RSS_GIB` > 约 100 → 提高 `hpr_batch` 内存（登记值变更，用户决定）"写进 RUN_PLAN §9 / 手册 D2-2 的判读规则 |
| **F-17** | 非阻断（说明即可） | PBS 作业环境 | PBS Pro 在作业环境里设置 `OMP_NUM_THREADS=ncpus`（48）；进程 1（构建）与进程 3 以 48 个 BLAS/OpenMP 线程运行（后处理各步经 `aux_env` 另行设定）。不改变 Gurobi 的 `Threads=16`；对 LP 构建的确定性无已知影响（HPC 冒烟按相对 1e-6 比对目标值即覆盖） | 无 | 可在作业体记录 `OMP_NUM_THREADS`，便于解释跨机器差异 |
| **F-18** | 非阻断（说明即可） | 手册 D1 第 103 行 | `printf '%s\n' '<你的授权原文>'` 若授权文字含英文单引号会破坏命令 | 小概率卡住 | 提示避免单引号或用 heredoc |

**核对为"未发现问题"的要点（供检查单引用）**
- 正式路径：F1 → 阶段 0（输入 / 登记 SHA / 无残留求解进程）→ 进程 1（无许可、`timeout 3600`）→ `wait_gap` 330 s → `wait_other_start`（F2）→ 进程 2（`setsid`、监控、墙钟 871,200 s、内存止损、首 20 次迭代测速）→ `SPLIT_SOLVE.json` 先落盘 → 进程 3（无许可、`timeout 32400`）→ `post_run` → GATES_V6 → 分级 → 导出清洗。`REMOVE_LP=1` 删除的 `split/problem.lp` 在进程 3 不再需要（`--split-stage assign` 读 `lp/MATH_PROBLEM.json` 数组）。进程 1 用 linopy 自带写出器写 LP，不导入 gurobipy，BUILD_ONLY 确实不触碰许可。
- 许可：只经 `GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic` 引用；作业体 / 提交脚本 / 登录预检只 `stat` 权限位与属主；进程 1 / 3、后处理、批级作业 `env -u GRB_LICENSE_FILE`；正式作业不跑预检 `licence` 节；导出日志经 SCRUB 过滤；打包前检索许可特征串。手册步骤 B 只有 `mkdir / chmod / scp / ls -l`。
- 测试开关残留：`hpr_job.sh` 第 23–31 行在真实 PBS 作业号下拒绝全部本机演练 / 测试开关与运行器钩子（含 `BUILD_ONLY`、`TRUNCATE`、`FAKE_*`）；`run_batch4.sh` 自身再拒绝未登记时限 / 墙钟 / 求解方式与 `--auth` 并存无求解模式；`hpr_submit.sh` 在提交 shell 中再查一次。D2 要求的"正式命令仍须拒绝 BUILD_ONLY 等残留"满足；BUILD_ONLY 目录 `runs/build_only_f1` 与正式目录隔离。
- cgroup 三种情形：v2 作业目录（`memory.stat anon` / `memory.max`）、v1 作业目录（`total_rss` / `memory.limit_in_bytes`）、无钩子（路径 `/` 或非本作业路径 → `MEM_MEASURE=rss`，进程组 RSS）均有处理；根 cgroup 不会被当作本作业计量（`is_job_path`）。
- 中断 / 续跑：`SKIP_ENDED`、`STOP_SAFE:INTERRUPTED`、`--resume` 仅在无 `STOP`/`STOP_SAFE` 时允许。
- `qsub -W depend=after:<id>` / `afterany:<id1>:<id2>` 语法正确；无 `-V`；无 `-P`。
- 包内文本文件无 CRLF；`REFERENCE_VALUES.json` 只含数值。

**泄露扫描结果（只计数）**
- WLS 键名（不分大小写）：包内文本文件 0；手册 / 检查单 / `hpc_package_src/` 0；代码归档 1 处（`scripts_project/s2_solve.py`，键名字面量，无 `=值`，非注释 / 正则 —— 属 DFX R1 口径的键名字面量）；分支补丁新增行 1 处（提交 `be5e49fd` 的 `hpc_package_src/hpr_submit.sh`，与检查单 R1(b) 的说明一致，工作树已改写）。
- `KEY=值` 形式的许可行：包 0、归档 0、补丁 0。
- IPv4 字面量：包内仅 `env/ENV_LOCK.txt`（7）与 `env/conda_explicit_linux64.txt`（3）—— 四段式版本号（与检查单 R1(a) 一致）；手册 / 计划 / 源码 / 补丁 0。
- `ssh -p` / `scp -P` 端口：全部 0。`用户@主机` 字面量：包 0（手册 9 处均为 `<你的用户名>@atlas8.nus.edu.sg` 占位符）；归档 2 个上游文件（`REUSE.toml`、`configs/bundle_config.yaml`，上游维护者邮箱 / URL，非本项目账号）。
- 密码词：`hpr_submit.sh` 1（grep 模式）、`HPC_FACTS` 1（"不含…密码"声明）、手册 2（操作说明）—— 均无值。
- 本机用户名路径：见 F-09。`atlas8` 主机名：`HPC_FACTS` 4、手册 30 —— 指令 H5.2 要求写明的公开登录地址。
- 云厂商词：`env/install_env.sh` 2（缺省前缀注释 `/root/autodl-tmp`，非主机）。

---

## 3. 登记值一致性核对表（独立抽取）

| 常数 | RUN_PLAN_HPC.md | `b4_batch4.py` | `run_batch4.sh` | `preflight.sh` | `pbs/*.pbs` / `HPC_PLAN.txt` | `hpr_job.sh` | 一致 |
|---|---|---|---|---|---|---|---|
| 网络 SHA256 F1 / F2 | `08879f0b…b271` / `d90ca992…64e7`（§1） | `REGISTERED_SHA` 同值 | 阶段 0 `base-check` | `networks` 节 `base-check` | `HPC_PLAN.txt` NETWORK 行同值；`SHA256SUMS` 中 `.nc` 哈希同值 | — | ✓ |
| 网络字节 F1 / F2 | 63,873,447 / 63,202,193 | `REGISTERED_BYTES` 同值 | 同上 | 同上 | `HPC_PLAN.txt` 同值；包内文件大小同值 | — | ✓ |
| 构建提交 | `72083fde…721f` | `BUILD_COMMIT` 同值 | 经 `base-check` 回执 `code_sha` | `code` 节断言 `startswith("72083fde")` | `HPC_PLAN.txt` 同值 | — | ✓ |
| TimeLimit | 864,000（§2） | `TIME_LIMIT_S=864000` | `R_TL=864000` | `R_TL=864000`（`code` 节断言三者相等） | 六个 `.pbs` `JOB_TIME_LIMIT_S=864000` | — | ✓ |
| 进程 2 墙钟 | 871,200 = 864,000 + 7,200 | `WALL_CAP_S=871200` | `R_WALL=871200` | — | `JOB_WALL_CAP_S=871200` | — | ✓ |
| 许可间隔 | 330 | `LICENCE_GAP_S=330` | `R_GAP=330` | — | `JOB_LICENCE_GAP_S=330` | — | ✓ |
| 求解方式 | split | — | `R_MODE=split` | `code` 节 | — | `SOLVE_MODE=split` | ✓ |
| 进程 1 / 3 超时 | 3,600 / 32,400 | 同值 | 缺省 3600 / 32400 | — | `LIMITS` 行 3600/32400 | — | ✓ |
| 后处理单步 / 打包超时 | 10,800 / 7,200 | 同值 | 缺省 10800 / 7200 | — | `LIMITS` 行 | — | ✓ |
| 后处理并存内存 | 100 GiB | `POST_MEM_NEED_GIB=100` | 缺省 100 | — | `LIMITS` 行 | — | ✓ |
| 内存止损 / 测速分数 | 0.80 / 0.80 | 0.80 / 0.80 | 缺省 0.80 / 0.80 | — | `STOP|0.8|0.8` | — | ✓ |
| 迭代参考 F1 / F2 | 450 / 250 | `RUNS[*].iterations_reference` | `ITERS_REF` 450 / 250 | — | `STOP` 行 | — | ✓ |
| F2 等待上限 | 7,200 | `WAIT_START_MAX_S=7200` | 缺省 7200 | — | `LIMITS` 行 | `WAIT_START_OF` 由 `JOB_WAIT_START_OF=F1` 导出 | ✓ |
| 测速止损线 | 691,200 | `walltime_components()` 0.8×864,000 | 运行时 `projection` 计算 | — | — | — | ✓（复算 691,200） |
| 内存止损线 F1 / F2 | 240 / 200 GiB | — | `QUOTA_GIB × 0.80`（`MEM_QUOTA_GIB` 由作业体传入 300 / 250） | — | `JOB_MEM_GB=300 / 250` | `MEM_QUOTA_GIB=$JOB_MEM_GB` | ✓（复算 240 / 200） |
| PBS F1 | parallel / 48 / 300gb / 255:00:00 = 918,000 s | `HPC_JOBS["F1"]` | — | `resources` 节下限 48 核 / 270 GiB（= 300×0.9） | `hpr_f1.pbs` 同值 | — | ✓ |
| PBS F2 | parallel / 48 / 250gb / 257:00:00 = 925,200 s；`after:F1`；`WAIT_START_OF=F1` | `HPC_JOBS["F2"]` | — | 下限 48 / 225 | `hpr_f2.pbs` 同值；`hpr_submit.sh` `-W depend=after:` | — | ✓ |
| PBS 批级 | parallel / 12 / 120gb / 12:00:00；`afterany:F1:F2` | `HPC_JOBS["batch"]` | — | 下限 12 / 108 | `hpr_batch.pbs`；`hpr_submit.sh` `afterany` | — | ✓ |
| PBS 冒烟 | parallel / 17 / 32gb / 04:00:00；`TRUNCATE=56 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600` | `HPC_JOBS["smoke56"]`、`SMOKE` | — | — | `hpr_smoke56.pbs`；`SMOKE|56|3000|3600` | 第 115 行同值 | ✓ |
| PBS BUILD_ONLY | parallel / 48 / 300gb / 02:30:00 | `HPC_JOBS["build_only_f1"]` | — | — | `hpr_build_only_f1.pbs` | 第 116–118 行 | ✓ |
| PBS 安装 | serial / 1 / 8gb / 02:00:00 | `HPC_JOBS["install"]` | — | — | `hpr_install.pbs` → `hpr_install_env.sh` | — | ✓ |
| walltime 构成 | 330+3,600+871,200+32,400+2×3,900+1,800 = 917,130 ≤ 918,000；+7,200 = 924,330 ≤ 925,200 | `walltime_components()` 同式 | — | — | — | — | ✓（复算） |
| 队列限制 / 1.25 倍 | ≤540 GB、48+48=96≤96、≤720 h；300≥200、250≥186.25 | `QUEUE_LIMITS`、`B4P_HIGH_PEAK_GIB` | — | — | — | — | ✓ |

与检查单 H-P3 的"36 行全部 OK"结论一致。附带核对：H-P1 的"RUN_PLAN_HPC.md 自 `1f62176f`（2026-10-27 13:19:34 +08）起未修改"—— `git log --follow` 只有这一次提交，属实。

---

## 4. 操作手册逐步可执行性评价

| 步骤 | 命令可原样执行 | 成功 / 失败判据可操作 | 评价 |
|---|---|---|---|
| 头部 / 占位符 | — | — | `[PowerShell]` / `[bash@atlas8]` 标注齐全；账号一律占位符或 `$USER`；无查看许可内容的命令。缺少"PowerShell 行里不能用 `$USER`"的说明（F-01） |
| A1 | 是 | **否**（F-02：计数方式与判据不符；引用用户没有的 `HPR_REPORT.md`） | 需改 |
| A2 | 第一条**否**（F-01 `$USER` 被 PowerShell 吞掉）；`scp -r` 可执行 | 部分 | 首次上传通常仍能成功；重传或目录已存在时误导 |
| A3 | 是 | 是（`0` / `files=36`） | 良好；`chmod` 合理（scp 不保留执行位） |
| B1–B3 | B2 的 `~` 远端路径在 SFTP 模式下**待确认**（F-05）；备选命令可用（发行版名 `Ubuntu` 已核实） | 是（只看 `ls -l`） | 符合"不出现查看内容的命令"；含本机用户名路径（F-09） |
| C1–C2 | 是 | 是；失败分支覆盖下载失败 / 频道不可达 / 环境不一致，但缺"半成品环境如何重来"（F-12）与"`/usr/bin/time` 缺失"（F-08） | 基本可用 |
| C3 | 是 | **否**（F-03 `tail -15` 截掉判据） | 需改 |
| D1–D3 | 是 | D3 的 `WLS_TOKEN_HTTP` 判据与实际输出不符（F-04）；其余判据（`F1:termination=optimal…:OK`、`POSTPROC_ERRORS:0`、`BATCH_DONE:True`、`HALTED:False`、`SMOKE_RESULT:PASS`）与 `hpr_job.sh` 输出格式逐项相符 | 需小改 |
| D2-1 / D2-2 | 是 | 是（`RUNNER_EXIT:0`、`BUILD_CHECK_F1:{"passed": true, …}`、`LP_DELETED:`、`DONE`，与作业体第 140–152 行一致）；预期区间给出 | 良好；建议补 F-16 的判读规则 |
| E1–E3 | 是（E2 的 PowerShell 命令可执行） | 是（`SUBMITTED:` 行格式与 `hpr_submit.sh` 一致；`REFUSED:` 分支齐全） | 良好；F-11 的 qsub 失败情形依赖联系审阅端 |
| F | 是 | `(none)` 永不出现（F-13）；其余字段与 `hpr_status.sh` 一致 | 基本可用 |
| G1–G5 | G2 第二条**否**（F-05 大括号展开）；G3 的 PowerShell 哈希比对正确 | 是 | 需改 G2 |
| 附录 1–4 | — | — | 时间窗口、退出码（与 `hpr_job.sh` / `run_batch4.sh` / `hpr_submit.sh` 实际退出码一致）、文件位置（与 RUN_PLAN §11 的日志路径不一致，F-10）清楚 |

---

## 5. 结论

- **阻断项：0。** 正式执行路径（两作业方式、许可会话间隔、三种 cgroup 情形的内存止损、早期测速、墙钟、中断续跑、停批共享、后处理与批级作业、测试开关拒绝）与登记值在计划、代码、运行器、预检、作业脚本之间逐项一致；包完整、副本与来源逐字节相同、代码归档为最终提交、无许可值 / 账号 / 连接串 / 端口泄露。
- **非阻断项：18**（F-01 ~ F-18）。其中：
  - 建议上传前修正（手册 / 文档 / 作业体文字，需重建包与 `SHA256SUMS`）：F-01、F-02、F-03、F-04、F-05、F-10、F-13；
  - 建议修正的小逻辑（纯 bash，不触及解，需补替身测试）：F-06（批级作业在 NOT_STARTED 情形的放行）、F-07（`--only` 模式忽略另一作业的运行）、F-11、F-12；
  - 上机前待确认：F-08（`/usr/bin/time` 等工具在 Atlas 是否存在）、F-14（登录 shell）、F-05(b)（atlas8 sshd 对 `~` 的支持）；
  - 请用户确认：F-09（本机用户名路径是否接受留在上传文件中）、F-16（D2 结果对批级作业内存的判读规则）；
  - 说明即可：F-15、F-17、F-18。
- 本审查未读取许可文件、`~/.dfx_leak_patterns` 或准备过程的证据 / 进度文件；所有"待确认"项均无法在本机闭环，需在 HPC 登录节点上由用户核实。
- 审查过程中的一个附带说明：为识别代码归档中的键名命中，曾启动一条逐文件解压归档的后台命令，发现其占用 CPU 后已立即停止（未完成、未写任何仓库 / 包文件）；随后改用单遍内存扫描完成。未在仓库、包或交付目录写入任何文件。

## 3. 执行端处理（逐条）

第一轮结论：**阻断项 0，非阻断 18**。执行端对全部 18 条逐条处理如下（修正后重新运行替身测试、重建包 v9、重做干跑 / 一致性 / 泄露扫描、重跑全量测试；详见 `HPR_REPORT.md` 第 7 节）。改动不触及求解代码（`s2_solve.py` / `b4_split_solve.py` / 模型 / 配置 / 网络）；第 2–7 节登记值不变。

| 编号 | 处理 | 位置 |
|---|---|---|
| F-01 | **已修**：A2 远端命令改单引号（`$USER` 由 atlas8 展开），手册头部增加"PowerShell 行里没有 `$USER`"说明 | `HPC_OPERATOR_GUIDE.md` A2、头部 |
| F-02 | **已修**：A1 改为递归计数文件数并与 `SHA256SUMS` 行数 + 1 比较；删去对 `HPR_REPORT.md` 的引用 | 手册 A1 |
| F-03 | **已修**：C3 改为输出到文件后 `grep` 四个判据行 | 手册 C3 |
| F-04 | **已修**：批级作业体从 `PBS_JOBS.txt` 读取 F1 作业体记录的 `WLS_TOKEN_HTTP:` 状态码写入 `SMOKE_STATUS.txt`；手册 D3 注明来源 | `hpr_job.sh`、手册 D3 |
| F-05 | **已修**：B2 远端路径改为相对家目录 `.gurobi/gurobi.lic`，注明 `-O` 回退；G2 拆成逐文件 `scp` 并给出通配符失败的回退 | 手册 B2、G2 |
| F-06 | **已修 + 补测试**：批级作业放行条件 = 每个运行 `.ended`，或运行目录有 `STOP` / `STOP_SAFE` 且该运行无 `.started`（NOT_STARTED）；已开始未结束仍为 `not_ready`；`RUN_PLAN_HPC.md` §7.5 与手册附录 2 写明；新测试 `test_batch_job_runs_when_the_other_run_never_started_after_a_stop`（F1 MEM_LIMIT 停批 → F2 NOT_STARTED → 批级作业重评、汇总、`*_halted_*` 包、exit 3；F2 `.started` 时仍 `not_ready`） | `hpr_job.sh`、`RUN_PLAN_HPC.md` §7.5、`test_hpr_two_jobs.py` |
| F-07 | **已修 + 补测试**：`--only` 模式下 `other_solve_running` 恒为假、`aux_threads` 只计本运行；`MEM_MEASURE=rss` 时运行器完全不读 `CGROUP_ROOT` 下的 cgroup 文件（监控 CSV 的 cgroup 列为空，`cgroup_anon_source=none(rss_mode)`）；新测试 `test_only_mode_ignores_the_other_job_run_for_post_memory_and_threads`（另一作业的 `.started` 存在且"节点级"匿名内存 230 GiB：无 `POST_QUEUED`、线程预算 = 全部 25 核、cgroup 列为空） | `run_batch4.sh`、`test_hpr_two_jobs.py` |
| F-08 | **部分处理（待用户在 HPC 核实）**：手册 A3 增加工具检查命令（`/usr/bin/time -v true`、`setsid pgrep timeout curl`）与"缺失即停下回传"的说明；C2 失败分支增加 `MISSING /usr/bin/time` 情形。`TIME_BIN` 可配置化会改动运行器多处且需替身测试，本步骤不做；缺失时由审阅端另行修订 | 手册 A3、C2 |
| F-09 | **部分处理（待用户确认）**：手册 B2 的 WSL 路径改为 `<WSL 用户名>` 占位符并说明查法；`RUN_PLAN_HPC.md` §4 去掉本机许可文件路径；打包清单 `h4_drill.file` 改为文件名、`networks.source` 改为相对描述；`make_hpc_package.sh` 缺省 PY 路径改用 `$HOME`。**保留：** 两份构建回执（DFX 产物，含构建 worktree 路径；改动会破坏回执与网络的对应关系，B4P / DFX 包同样随包上传），以及 WSL 辅助脚本 `scripts/wsl_hpr/*` 中的本机路径（不入包）。本机 Linux 用户名不是 HPC 账号，列入检查单保留项 R4 请用户确认 | 手册、`RUN_PLAN_HPC.md` §4、`make_hpc_package.sh`、`PRE_HPC_CHECKLIST.md` R4 |
| F-10 | **已修**：`RUN_PLAN_HPC.md` §11 作业日志位置更正为提交目录 `<作业名>.o<作业序号>`（与手册附录 3 一致；作业脚本不设 `-o`） | `RUN_PLAN_HPC.md` §11 |
| F-11 | **已修**：`hpr_submit.sh` 在 F1 `qsub` 成功后才建 `runs/batch4`；F1 失败的提示改为"什么都没提交，修正后重跑" | `hpr_submit.sh` |
| F-12 | **已修（手册）**：C2 增加半成品环境的恢复步骤（`rm -rf ~/miniforge3/envs/pypsa-earth` 后重提） | 手册 C2 |
| F-13 | **已修**：`hpr_status.sh` 的"停止 / 错误行"段无命中时打印 `(none)` | `hpr_status.sh` |
| F-14 | **已修**：`make_pbs.sh` 生成的六个作业脚本加 `#PBS -S /bin/bash`；手册 A3 顺带显示 `$SHELL` | `make_pbs.sh`、手册 A3 |
| F-15 | **已修**：预检 JSON 文件名可加 `PREFLIGHT_TAG`（作业体传 `<作业键>_<运行>_<作业号>`） | `preflight.sh`、`hpr_job.sh` |
| F-16 | **已修（文档）**：`RUN_PLAN_HPC.md` §9 与手册 D2-2 增加判读规则：D2 峰值 100–150 GiB → 批级作业内存是否提高由审阅端提出、用户决定（登记值变更）后再做步骤 E | `RUN_PLAN_HPC.md` §9、手册 D2-2 |
| F-17 | **已修（记录）**：作业体 `JOB_START` 记录 `OMP_NUM_THREADS` 与 `SHELL` | `hpr_job.sh` |
| F-18 | **已修（手册）**：D1 注明授权原文不要含英文单引号 | 手册 D1 |

另：审查报告"泄露扫描"段提到代码归档中 `scripts_project/s2_solve.py` 含 1 处许可键名字面量（无值）——这是 S4B 以来就在仓库中的日志清洗模式（DFX R1 口径的同类项，见 DFX 阶段 3 检查单），本步骤未改该文件，列入检查单 R1。

## 4. 第二轮复核原文

ROUND2_PLACEHOLDER
