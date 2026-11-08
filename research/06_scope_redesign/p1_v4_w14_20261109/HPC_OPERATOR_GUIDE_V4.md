# HPC 操作手册 v4（2026-11-09）——v4 主算一对 F1（一体化）、F2（`no_new_xb`），NUS Atlas（PBS Pro）

**这一版是什么：** 决策清单第 222 项：今晚只提交 v4 主算一对 F1、F2 加批级后处理（敏感性在 W19 登记后另批）。登记值、报警线与预测见 `RUN_PLAN_HPC_V4.md`（本包内，已在任何 HPC 提交之前入库）。**上传到新目录 `/hpctmp/$USER/hpr4/`**；v3 的 `hpr3/`、v3.1 的 `hpr31/` **保留不动，不要删除、改名或往里面复制文件**。正式运行目录 `runs/batch6/`，冒烟目录 `runs/smoke56_v4/`。
**使用前提：** 包为 `hpc_package_v4`，`BATCH_DEF.json` 的 `limits_status` 为 `REGISTERED`，并且含 `"formal": "runs/batch6"`。步骤 A1 显示不是这样，说明拿错了包，停下。
**使用方式：** 在 Windows PowerShell 中、连着 NUS VPN，按步骤 A → G 逐条复制执行。`[PowerShell]` 在你的 Windows 终端执行；`[bash@atlas8]` 在登录 `atlas8.nus.edu.sg` 后的 bash 中执行。**不要在登录节点上跑任何求解或长时间计算**（交互进程 30 分钟 CPU 限制）。
**要你替换的值：** 都用大写变量名，每处都在上一行说明从哪里取得：PowerShell 里的 `$HPC_USER`（你的 NUS HPC 账号，只在当前窗口里设，不写进任何文件）与 `$WSL_USER`（本机 WSL 的 Linux 用户名，只在需要重新放置许可时用到）；atlas8 上查看或撤销作业时的作业号 `F1_ID` 等（取自 `runs/batch6/SUBMITTED.txt`）；回收结果时的运行编号 `RID`。atlas8 的 bash 里直接用系统自带的 `$USER`。手册中没有任何真实账号、密码、主机连接串或许可内容。
**本机路径：** 包 `D:\ResearchWorkspaces\ASEAN\work\p1_v4_w14_20261109\hpc_package_v4`；结果 `D:\ResearchWorkspaces\ASEAN\work\p1_v4_w14_20261109\hpc_results_v4`。
**HPC 路径：** 包目录 `/hpctmp/$USER/hpr4`（所有 `qsub` 都在这里执行）；许可 `~/.gurobi/gurobi.lic`；环境 `~/miniforge3/envs/pypsa-earth`（v3 / v3.1 时已装好，预检 `env` 节一致即复用，不重装）。`/hpctmp` **60 天未改动的文件自动清除**——每个运行结束后先回收它的导出（步骤 F1），批级作业结束后回收结果包（步骤 F2）。
**同期禁止：** 从冒烟作业开始到最后一个正式求解结束，本机（WSL）与 AutoDL 都不得启动 Gurobi（同一 WLS 许可；`RUN_PLAN_HPC_V4.md` 第 14 节）。
**任何一步失败：** 不重试、不改参数，把"失败时回传"的文件发给审阅端（下载命令见附录 2）。

## 与 v3.1 指南（`HPC_OPERATOR_GUIDE_V3.md`）的全部差异

| 项 | v3.1 指南 | 本指南（v4） |
|---|---|---|
| 包 / HPC 目录 | `hpc_package_v3_1`，`/hpctmp/$USER/hpr31` | **`hpc_package_v4`，`/hpctmp/$USER/hpr4`**（`hpr3/`、`hpr31/` 不动） |
| 运行目录 | `runs/batch5`、`runs/smoke56_v31`、`runs/build_only_f1` | **`runs/batch6`、`runs/smoke56_v4`、`runs/build_only_f1_v4`** |
| 正式运行 | F1–F4 两对 + 批级（5 个作业） | **F1、F2 一对 + 批级（3 个作业）** |
| 作业名 | `hpr3_*` | **`hpr4_*`**（`hpr4_f1`、`hpr4_f2`、`hpr4_batch`、`hpr4_smoke56`、`hpr4_build_only_f1`、`hpr4_install`） |
| 依赖 | F2 after:F1；F3 afterany:F1；F4 afterany:F2；批级 afterany:F3:F4 | **F2 `after:F1`；批级 `afterany:F1:F2`** |
| TimeLimit / walltime | 240 h；F1、F3 260 h，F2、F4 262 h，批级 48 h | **72 h；F1、F2 96 h**，批级 48 h，冒烟 4 h |
| 进程 1 超时 / 参考迭代 | 5,400 s；350 / 250 / 350 / 250 | **7,200 s；F1 350、F2 300** |
| 维护通知的检查期 | 约 22 天 | **约 4 天**（walltime 96 h） |
| 包大小 / 上传时长 | 约 375 MB | **约 255 MB**（1 MB/s 约 4 分钟，0.1 MB/s 约 45 分钟） |
| 不提交演练的期望输出 | 5 行 `DRY-RUN: qsub` | **3 行**（步骤 B4） |
| 登录预检 | 无 v4 检查 | **多一段 v4 网络元数据检查**（开关集、表目录、配置哈希 = `BATCH_DEF.json` 的 `v4_meta`，步骤 B3） |
| 冒烟期望值 | 329,705,566,422.24 / 342,268,691,464.46 EUR | **363,190,038,821.0828 / 376,143,650,003.4369 EUR**（D2c 本机冒烟） |
| 状态命令 | 只显示 LP 值（标为 objective） | **同时显示含常数项的目标值与 LP 值 `objective_lp`、常数项与包的 `COMMIT`**（步骤 E） |
| 回收 | `hpc_results_v31`，RID F1–F4 | **`hpc_results_v4`，RID F1、F2** |
| STOP 处理 | 含 `PREDECESSOR_NOT_ENDED`（F3 / F4） | **无 F3 / F4，该行不适用**；其余相同（步骤 G） |
| 步骤编排 | A 上传、B 许可、C 预检、D 冒烟、E 正式、F 监控、G 回收、H 停批 | **A 本机核对与上传、B 核对与登录预检（含许可）、C 冒烟、D 正式提交、E 监控、F 回收、G 停批**（指令第 5 节） |
| 不变 | 环境锁文件、求解档案、split 求解、验收、止损分数、许可规则、单路上传、`sha256sum -c` | 同左 |

每个 PowerShell 窗口开头先设账号变量（下一行把 `YOUR_NUS_ID` 换成你的 NUS HPC 账号，只改引号里的内容）：
```powershell
$HPC_USER = "YOUR_NUS_ID"
```

---

## 步骤 A 本机核对与单路上传（约 255 MB；1 MB/s 约 4 分钟，0.1 MB/s 约 45 分钟）

A0 `[PowerShell]` 连 VPN **之前**确认本机没有 Gurobi 进程（两行都应输出 `0`），并确认本机的 Claude Code 会话都已停下：
```powershell
wsl -d Ubuntu -- bash -c "ps -eo args | grep -c '[s]2_solve.py'"
wsl -d Ubuntu -- bash -c "ps -eo args | grep -c '[b]4_split_solve.py'"
```
连上 AnyConnect 后 WSL 的外连会断：之后的上传与下载一律在 Windows PowerShell 里用 Windows 自带的 `ssh` / `scp`，不要用 `wsl ... scp`。

A1 `[PowerShell]` 本机确认包完整、是 v4：
```powershell
$PKG = "D:\ResearchWorkspaces\ASEAN\work\p1_v4_w14_20261109\hpc_package_v4"
(Get-ChildItem -Recurse -File $PKG | Measure-Object).Count
(Get-Content "$PKG\SHA256SUMS" | Measure-Object -Line).Lines
Get-Content "$PKG\COMMIT"
Select-String -Path "$PKG\BATCH_DEF.json" -Pattern '"limits_status"', '"formal": "runs/batch6"', '"name": "hpr4_f1"'
Test-Path "$PKG\DRILL_ONLY_NOT_FOR_UPLOAD.txt"
(Get-FileHash -Algorithm SHA256 "$PKG\SHA256SUMS").Hash
```
成功：第一个数 = 第二个数 + 2（`SHA256SUMS` 本身与 `HPC_PACKAGE_MANIFEST.json` 不在清单里）；`COMMIT` 为 40 位提交号，与 `REPORT.md` 第 0 节的包 `COMMIT` 相同；`limits_status` 为 `REGISTERED`，并且找到 `"formal": "runs/batch6"` 与 `"name": "hpr4_f1"`；`Test-Path` 为 `False`（演练包不得上传）；最后一行与 `REPORT.md` 第 0 节记录的 `SHA256SUMS` 的 SHA256 相同（大写）。

A2 `[PowerShell]` 建目标目录并上传（**一条 `scp -r`，不要并行开多个上传**；首次连接问 host key 时输入 yes）：
```powershell
ssh "${HPC_USER}@atlas8.nus.edu.sg" 'mkdir -p /hpctmp/$USER && test ! -e /hpctmp/$USER/hpr4 && echo READY || echo "hpr4 EXISTS - rename it first"'
scp -r $PKG "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr4"
```
成功：第一条打印 `READY`；第二条逐文件到 100 %。
失败：提示 `hpr4 EXISTS` → `[bash@atlas8] mv /hpctmp/$USER/hpr4 /hpctmp/$USER/hpr4_old_$(date +%Y%m%d%H%M)` 后重做 A2（不要往已有的 `hpr4/` 里复制，否则会多出一层目录）。**不要动 `hpr3/`、`hpr31/`。** 其他错误把 PowerShell 输出发回。

## 步骤 B atlas8 上核对与登录预检（不调用 Gurobi；约 2 分钟）

B1 `[PowerShell]` 登录，然后 `[bash@atlas8]` 看 bash 版本与队列：
```powershell
ssh "${HPC_USER}@atlas8.nus.edu.sg"
```
```bash
bash --version | head -1
qstat -u $USER
```
第一行期望 `GNU bash, version 4.2.x` 或更高（包内脚本已在本机编译的 bash 4.2 下实测，`DRILL_REPORT.md`）；低于 4.2 → 停下，把这一行发回。第二条**不应列出任何作业**；若列出作业 → 停下，把输出发回审阅端，不要自行 `qdel`。

B2 `[bash@atlas8]` 核对全部文件的 SHA256、设权限、查工具：
```bash
cd /hpctmp/$USER/hpr4 && sha256sum -c SHA256SUMS | grep -vc ': OK$' ; echo "files=$(wc -l < SHA256SUMS)"
chmod 755 *.sh hpc/*.sh pbs/*.pbs env/install_env.sh
/usr/bin/time -v true > /dev/null 2>&1 && command -v setsid pgrep timeout curl > /dev/null && echo TOOLS_OK
grep '^RUNDIRS|' pbs/HPC_PLAN.txt
```
成功：第一行 `0`，第二行 `files=` 等于 A1 的第二个数；第三行 `TOOLS_OK`；第四行 `RUNDIRS|runs/batch6|runs/smoke56_v4|runs/build_only_f1_v4`。
失败（第一行不是 0）：`sha256sum -c SHA256SUMS | grep -v ': OK$'` 看哪些文件不对，只重传这些文件（下一行的 `FILE` 换成那个文件在包内的相对路径），再做 B2：
```powershell
$FILE = "networks/integrated_2920_3h_unsolved.nc"
scp "$PKG\$($FILE -replace '/', '\')" "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr4/$FILE"
```

B3 许可（v3 / v3.1 时已放在 `~/.gurobi`；只核对属性，不看内容）与登录预检。`[bash@atlas8]`：
```bash
ls -l ~/.gurobi/gurobi.lic
cd /hpctmp/$USER/hpr4 && bash hpc/hpr_preflight_login.sh > login_preflight.txt 2>&1 ; grep -E "licence file|files OK|key packages|limits of the package|v4 network metadata|_unsolved.nc: switch|PREFLIGHT OK|PREFLIGHT FAILED|HPR_PREFLIGHT_LOGIN" login_preflight.txt
```
成功：`ls` 显示 `-rw------- 1 ...你的账号... gurobi.lic`（权限 600、属主是你）；预检至少包含 `licence file present, owner ..., mode 600`、`all ... files OK`、`limits of the package definition: TimeLimit 259200 s, status REGISTERED`、两行 `F1 integrated_2920_3h_unsolved.nc: switch d89ccbf47b00 ... -> OK` 与 `F2 no_new_xb_2920_3h_unsolved.nc: switch d89ccbf47b00 ... -> OK`、`v4 network metadata OK ...`、`PREFLIGHT OK`、`HPR_PREFLIGHT_LOGIN OK`，没有 `FAILED`。预检的 `sha` 节同时把 v4 的代码解包到 `./repo`；`env` 节把环境与 `env/ENV_LOCK.txt` 逐包比对（与 v3.1 包同一份锁文件，一致即复用）。
许可文件不是 600：`chmod 600 ~/.gurobi/gurobi.lic` 再看一次。文件不存在时（下一行把 `YOUR_WSL_USER` 换成本机 WSL 的 Linux 用户名，`wsl -d Ubuntu -- whoami` 可查），`[PowerShell]`：
```powershell
$WSL_USER = "YOUR_WSL_USER"
ssh "${HPC_USER}@atlas8.nus.edu.sg" 'mkdir -p ~/.gurobi && chmod 700 ~/.gurobi'
scp "\\wsl.localhost\Ubuntu\home\$WSL_USER\gurobi.lic" "${HPC_USER}@atlas8.nus.edu.sg:.gurobi/gurobi.lic"
ssh "${HPC_USER}@atlas8.nus.edu.sg" 'chmod 600 ~/.gurobi/gurobi.lic && ls -l ~/.gurobi/gurobi.lic'
```
失败：回传 `login_preflight.txt`。若 `env` 节报 `KEY PACKAGES DIFFER`，或出现 `V4 NETWORK METADATA CHECK FAILED` / `DIFFERS`：**停下**，不要自行重装或改文件，等审阅端回复。

B4 `[bash@atlas8]` **不提交演练**（只打印 qsub 命令，不写文件、不提交任何作业、不调用 qsub）：
```bash
cd /hpctmp/$USER/hpr4 && bash hpc/hpr_submit.sh --auth-file HPR_AUTH.txt --motd-checked --dry-run
```
期望输出（这时还没做步骤 C，所以前两行 `DRY-RUN NOTE` 是正常的；`bash` 后面是登录节点的实际版本）：
```
DRY-RUN NOTE: --auth-file FILE (the user authorisation text) is required (step D1 writes HPR_AUTH.txt) - a real submission would be refused
DRY-RUN NOTE: the smoke job has not passed (/hpctmp/.../hpr4/runs/smoke56_v4/SMOKE_STATUS.txt: SMOKE_RESULT:PASS missing) - step D first - a real submission would be refused
DRY-RUN: qsub pbs/hpr4_f1.pbs
DRY-RUN: qsub -W depend=after:F1_JOBID pbs/hpr4_f2.pbs
DRY-RUN: qsub -W depend=afterany:F1_JOBID:F2_JOBID pbs/hpr4_batch.pbs
DRY_RUN_OK: nothing submitted (bash 4.2.46(2)-release; 3 jobs; 2 check(s) above would refuse a real submission)
```
（脚本里的 "step D1"、"step D first" 是旧编号的固定文字，分别对应本指南的步骤 C1、步骤 C。）**停下并把输出发回的情况：** 出现 `unbound variable`、`syntax error`、`command not found` 或 `REFUSED:`；`DRY-RUN: qsub` 行不是这 3 行或顺序不同；最后一行不是 `DRY_RUN_OK`；出现上面两种以外的 `DRY-RUN NOTE`（例如 `./repo is not the package commit` 说明 B3 没做完；`licence file missing` 说明许可未放好）；冒烟路径不是 `runs/smoke56_v4`（说明拿错了包）。

## 步骤 C 冒烟作业（56 时段 F1 + F2 + 批级；2 次 Gurobi 会话；预计 1 小时 + 排队）

C1 `[bash@atlas8]` 写授权文件（把引号里的 `你的授权原文` 换成你的授权文字，一行；不写账号、主机或许可信息；不要用英文单引号）：
```bash
cd /hpctmp/$USER/hpr4 && printf '%s\n' '你的授权原文' > HPR_AUTH.txt && chmod 600 HPR_AUTH.txt && wc -c HPR_AUTH.txt
```
C2 `[bash@atlas8]` 提交（17 核 / 32 GB / 4 h；计算节点只记 `curl https://token.gurobi.com` 的 HTTP 状态码 → F1 56 时段 → ≥ 330 s → F2 → 批级后处理与结果包）：
```bash
cd /hpctmp/$USER/hpr4 && qsub pbs/hpr4_smoke56.pbs
```
C3 `[bash@atlas8]` 作业结束后（`qstat -u $USER` 不再列出 `hpr4_smoke56`）：
```bash
cat /hpctmp/$USER/hpr4/runs/smoke56_v4/SMOKE_STATUS.txt
```
**PASS 判据（全部满足）：** `WLS_TOKEN_HTTP:302`（或 200）；`F1:termination=optimal:...:label=ACCEPTED_LAYER2:expected_objective=363190038821.0828:relative_difference=...:...:OK`；`F2:termination=optimal:...:label=ACCEPTED_LAYER2:expected_objective=376143650003.4369:relative_difference=...:...:OK`；`relative_difference` 都 ≤ `1.000e-06`（本机演练为 `0.000e+00`，跨机器预计 1e-9 量级）；`POSTPROC_ERRORS:0`；`BATCH_DONE:True`；`HALTED:False`；`PACKS:2`；**`SMOKE_RESULT:PASS`**。迭代数（本机 89 / 80）跨机器可能不同，只记录。
失败：**不重试，也不提交正式批次**。发回 `runs/smoke56_v4/SMOKE_STATUS.txt`、`STATUS.txt`、`PBS_JOBS.txt`、`preflight_*.txt` 与 `hpr4_smoke56.o` 开头的作业输出（附录 2）。相对差 > 1e-6 也先发回审阅端，再做 D。

C4（可选，审阅端要求时才做；不调用 Gurobi；约 1 小时 + 排队）全尺寸 BUILD_ONLY：
```bash
cd /hpctmp/$USER/hpr4 && qsub pbs/hpr4_build_only_f1.pbs
```
结束后 `cat /hpctmp/$USER/hpr4/runs/build_only_f1_v4/BUILD_ONLY_STATUS.txt`，无论成败发回。参考：峰值约 96 GiB、LP 约 5.5 GB、构建加写出 ≤ 3,500 s（超时 7,200 s）。

## 步骤 D 正式提交（只在 C 为 PASS、登录欢迎信息无维护通知之后；1 分钟）

D1 `[bash@atlas8]` 重新登录一次，**阅读登录欢迎信息**：确认没有与未来约 4 天（walltime 96 h）重叠的维护通知。有 → 停下，把欢迎信息发回审阅端。然后再做一次不提交演练（同 B4 的命令）：
```bash
cd /hpctmp/$USER/hpr4 && bash hpc/hpr_submit.sh --auth-file HPR_AUTH.txt --motd-checked --dry-run
```
期望：**没有任何 `DRY-RUN NOTE`**，同样的 3 行 `DRY-RUN: qsub`，最后一行以 `3 jobs; 0 check(s) above would refuse a real submission)` 结尾。你确认无误后，才执行 D3。

D2 `[PowerShell]` 确认本机没有 Gurobi 在运行（应输出 `0`）；AutoDL 实例不在运行求解：
```powershell
wsl -d Ubuntu -- bash -c "ps -eo args | grep -c '[s]2_solve.py'"
```
D3 `[bash@atlas8]` 一条命令按登记顺序提交三个作业：F1；F2（F1 开始后，`after:F1`）；批级（F1、F2 结束后，`afterany:F1:F2`）：
```bash
cd /hpctmp/$USER/hpr4 && bash hpc/hpr_submit.sh --auth-file HPR_AUTH.txt --motd-checked
```
成功：
```
F1 job id: ...
F2 job id: ...   (depend=after:F1)
batch job id: ...   (depend=afterany:F1:F2)
SUBMITTED:utc=...:F1=...:F2=...:batch=...:resume=0
```
作业号也写在 `runs/batch6/SUBMITTED.txt`；把三个作业号发给审阅端。
失败（输出以 `REFUSED:` 开头，什么都没有提交）：`limits of the package are PROPOSED` → 拿错了包，联系审阅端；`smoke job has not passed` → 先完成 C；`runs/batch6 exists` → 联系审阅端（不要自行 `--resume`）；`gurobi_start_lock exists` → 联系审阅端（步骤 G3）；`unset before submitting` → 重新登录后再执行；其他 → 发回输出。`qsub ... failed - already queued: ...` → 把这行发回，审阅端决定是否 `qdel` 已排队的作业。
只有当这条命令因为非 qsub 的原因无法使用、且审阅端同意时，才逐条手工提交（每一行的作业号从上一条 `qsub` 的输出中取得）：
```bash
cd /hpctmp/$USER/hpr4
F1_ID=$(qsub pbs/hpr4_f1.pbs) && echo $F1_ID
F2_ID=$(qsub -W depend=after:$F1_ID pbs/hpr4_f2.pbs) && echo $F2_ID
B_ID=$(qsub -W depend=afterany:$F1_ID:$F2_ID pbs/hpr4_batch.pbs) && echo $B_ID
mkdir -p runs/batch6 && echo "SUBMITTED:manual:F1=$F1_ID:F2=$F2_ID:batch=$B_ID" >> runs/batch6/SUBMITTED.txt
```

## 步骤 E 监控（每天 1–2 次；一条命令）

```bash
cd /hpctmp/$USER/hpr4 && bash hpc/hpr_status.sh
```
看什么（第一行末尾应是 `runs runs/batch6`）：
- `PBS jobs`：F1、F2 由 `Q` 到 `R`；批级为 `H`（等依赖），F1、F2 都结束后变 `Q` / `R`。
- `F1`、`F2` 段：`phase`（`process1_built` → `process2_gurobi_running` → `process2_ended` → `ended:optimal:label=ACCEPTED_LAYER2`）、`gurobi elapsed`、最后一行 barrier、`monitor` 最后一行（内存对配额 300 / 250 GiB）、`projection`（第 20 次迭代后出现，`exceeded: False` 为正常）。
- **两种目标值（第 215 项第①条）：** 每个运行一行 `objective incl. constant: ... EUR [...]; objective_lp: ... EUR; constant: ... EUR; package_commit RUN.json xxxxxxxx / receipt xxxxxxxx`。含常数项的目标值是 B6 与报警线所用的口径；`objective_lp` 是 Gurobi 日志里的 LP 值；二者之差是常数项（F1 约 2,366,478,274 EUR，F2 约 2,537,155,330 EUR）。进程 3 结束前，含常数项的值由 LP 值加进程 1 回执的常数项给出（方括号里注明）。两个 `package_commit` 都应等于 `COMMIT` 的前 8 位。
- **报警线（`RUN_PLAN_HPC_V4.md` 第 8 节）：** F1 含常数项目标值应 ≥ 315,173,866,702 EUR，F2 应 ≥ 331,497,457,505 EUR。低于报警线 → 把状态文件发回审阅端（不是停批条件，由审阅端查数据链）。
- `start lock held by: ...`：某个运行正在等待启动 Gurobi 的时机，通常几分钟；F2 在 F1 的 Gurobi 刚启动（不到 330 s）时可以合法持有到 2 小时（`WAIT_START_MAX_S`）。持有超过 2 小时，或出现 `STOP_SAFE:START_LOCK` → 见步骤 G3。
- `STOP / STOP_SAFE files`：只要出现这一段，就说明批次已停，照步骤 G 处理。
- `stop / error lines`：应为 `(none)`。
**需要联系审阅端（把 `bash hpc/hpr_status.sh > status_$(date +%Y%m%d%H%M).txt 2>&1` 生成的文件发回）：** 任何 `STOP_SAFE`、`STOP_NOT_ACCEPTED`、`UNUSABLE`、`HALTED`、`KILLED`、`MEMORY_STOP`、`PROJECTION_STOP`、`START_LOCK`、`PREFLIGHT_FAILED` 行；`projection` 为 `exceeded: True`；作业状态 `E`，或作业消失但 `PBS_JOBS.txt` 没有对应的 `JOB_END`；`remaining to wall cap` 低于 12 小时而 barrier 仍在运行；目标值低于报警线；新的维护通知。

**查看排队原因：** 下面第二行的 `F1_ID` 换成 `runs/batch6/SUBMITTED.txt` 里的作业号（形如 `1234567.venus01`）：
```bash
qstat -u $USER
F1_ID=1234567.venus01
qstat -f $F1_ID | grep -E "comment|estimated|job_state|exec_host"
```
**撤销作业时，连同依赖它的作业一起撤销（先联系审阅端）：** F2 依赖 F1（after），批级依赖 F1、F2（afterany：无论怎样结束都会放行）。撤销时先撤后面的、再撤前面的（下一行换成你的 3 个作业号）：
```bash
F1_ID=1234567.venus01; F2_ID=1234568.venus01; B_ID=1234569.venus01
qdel $B_ID $F2_ID $F1_ID
```

## 步骤 F 回收结果（单路下载，本机核对 SHA256）

F1（G1）**每个运行结束后**（`hpr_status.sh` 显示该运行 `ended:...`），先回收它的导出（不含网络文件，约几十 MB）。`[bash@atlas8]`（下一行把 `F1` 换成刚结束的运行：F1 或 F2）：
```bash
RID=F1
cd /hpctmp/$USER/hpr4/runs/batch6 && tar czf interim_${RID}.tar.gz --exclude='*.nc' export/$RID && sha256sum interim_${RID}.tar.gz > interim_${RID}.tar.gz.sha256 && ls -l interim_${RID}.tar.gz*
```
`[PowerShell]`（下一行同样把 `F1` 换成那个运行）：
```powershell
$RID = "F1"
$RES = "D:\ResearchWorkspaces\ASEAN\work\p1_v4_w14_20261109\hpc_results_v4"
New-Item -ItemType Directory -Force $RES | Out-Null
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr4/runs/batch6/interim_${RID}.tar.gz" $RES
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr4/runs/batch6/interim_${RID}.tar.gz.sha256" $RES
(Get-FileHash -Algorithm SHA256 "$RES\interim_${RID}.tar.gz").Hash
(Get-Content "$RES\interim_${RID}.tar.gz.sha256").Split(' ')[0].ToUpper()
```
成功：最后两行相同。

F2（G2）**批级作业结束后**：`[bash@atlas8]` `ls -l /hpctmp/$USER/hpr4/runs/batch6/results_*` 看到 `results_light_final_*.tar.gz`、`results_full_final_*.tar.gz` 与 `.sha256`（停批时为 `*_halted_*`，同样回收并联系审阅端）。`[PowerShell]` 先下载并核对 light，再下载 full（一次一个文件，不要并行；full 约 3–5 GB）：
```powershell
$RES = "D:\ResearchWorkspaces\ASEAN\work\p1_v4_w14_20261109\hpc_results_v4"
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr4/runs/batch6/results_light_*" $RES
Get-ChildItem "$RES\results_light_*.tar.gz" | ForEach-Object { $_.Name; (Get-FileHash -Algorithm SHA256 $_.FullName).Hash; (Get-Content "$($_.FullName).sha256").Split(' ')[0].ToUpper() }
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr4/runs/batch6/results_full_*" $RES
Get-ChildItem "$RES\results_full_*.tar.gz" | ForEach-Object { $_.Name; (Get-FileHash -Algorithm SHA256 $_.FullName).Hash; (Get-Content "$($_.FullName).sha256").Split(' ')[0].ToUpper() }
foreach ($F in "STATUS.txt", "PBS_JOBS.txt", "SUBMITTED.txt", "BATCH4_SUMMARY.md", "BATCH4_SUMMARY.json") { scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr4/runs/batch6/$F" $RES }
```
成功：每个包名下的两行哈希相同。不同 → 只重新下载该文件再核对。通配符报 `No such file` 时加 `-O` 再试，或在 atlas8 上 `ls` 出确切文件名后逐个下载。（汇总文件名仍叫 `BATCH4_SUMMARY.*`，是运行器的固定文件名，内容是 v4 批次。）把核对结果与 `hpc_results_v4` 的文件列表发给审阅端。

**60 天清除：** LP / 解数组（约 2 × 7.8 GB）留在 `/hpctmp`，60 天未改动自动清除；需要时在清除前另行下载。下载完成并核对后再发给审阅端。

## 步骤 G 出现 `STOP` / `STOP_SAFE` 时

G1 **先不要动作业。** 不重提、不 `qdel`（除非审阅端要求）、不删除运行目录里的任何文件。停批是设计好的：尚未启动求解的运行会以 `NOT_STARTED_<编号>` 结束（退出码 3），批级作业仍会运行，重评、汇总并打出 `results_*_halted_*` 结果包。
G2 `[bash@atlas8]` 留存状态并发回：
```bash
cd /hpctmp/$USER/hpr4 && bash hpc/hpr_status.sh > status_$(date +%Y%m%d%H%M).txt 2>&1 ; cat runs/batch6/STOP runs/batch6/STOP_SAFE 2>/dev/null ; tail -40 runs/batch6/STATUS.txt
```
发回生成的 `status_*.txt`、`runs/batch6/STATUS.txt`、`runs/batch6/PBS_JOBS.txt`，以及 `STOP_SAFE` 里点名的那个运行的 `runs/batch6/MONITOR_` 加运行编号的 `.csv`（可只发 `tail -200`）与 `PROJECTION_` 加运行编号的 `.json`。

| 行 | 含义 | 审阅端可能的决定 |
|---|---|---|
| `STOP_SAFE:MEMORY:F1`（或 F2） | 内存超过配额 80 %（F1 240 GiB、F2 200 GiB），该求解已终止 | 以更大内存的新运行目录重开（资源原因的重新开始，须你授权） |
| `STOP_SAFE:PROJECTION:F1`（或 F2） | 前 20 次迭代外推超过 0.80 × TimeLimit（207,360 s） | 以更长的登记时限重开，或调整计划 |
| `STOP_SAFE:INTERRUPTED_F1`（或 F2） | 续跑时发现已开始未结束的求解 | 新运行目录重开 |
| `STOP_SAFE:WAIT_START:F2` | F1 在 2 小时内没有启动 Gurobi | 视 F1 状态决定 |
| `STOP_SAFE:START_LOCK:F2`（或 F1） | 启动锁 2 小时内取不到（锁残留，或已有 2 个求解在跑） | 见 G3 |
| `PREFLIGHT_FAILED:F1`（或 F2） | 正式作业的包内预检不通过；该运行什么都没启动，批次随之停止 | 看 `runs/batch6/preflight_*.txt` 后决定 |
| `STOP_NOT_ACCEPTED` / `UNUSABLE` | G2 不过 / 无返回解 / C1 (a) 不过 | 用户决定 |
| `KILLED_...`（后接运行编号） | 进程 2 到了墙钟（266,400 s） | 用户决定 |

（v3.1 指南中的 `PREDECESSOR_NOT_ENDED` 只用于 F3 / F4，本批不适用。）

G3 **启动锁残留**（只在审阅端确认后做）：锁目录 `runs/batch6/.gurobi_start_lock` 只在某个作业等待启动 Gurobi 时存在，通常几分钟，最多 2 小时。若 `hpr_status.sh` 显示它被持有超过 2 小时：`[bash@atlas8]` 先确认持有者（`cat` 出来的第一项是运行编号，第二项是取得锁的时刻）已不在运行：
```bash
cat /hpctmp/$USER/hpr4/runs/batch6/.gurobi_start_lock/owner ; qstat -u $USER
```
持有者的作业已不在 `qstat` 中、且审阅端同意时，才把锁目录改名移开（保留，不删除）：
```bash
mv /hpctmp/$USER/hpr4/runs/batch6/.gurobi_start_lock /hpctmp/$USER/hpr4/runs/batch6/stale_start_lock_$(date +%Y%m%d%H%M)
```
之后被 `STOP_SAFE:START_LOCK` 停下的运行如何继续，由审阅端登记后告知。

---

## 附录 1 退出码与拒绝

- 作业体 `hpc/hpr_job.sh`：`2` = 拒绝（测试开关残留、缺授权、PROPOSED 时限下的正式作业、运行编号不在定义文件中、运行目录有测试残留、许可文件缺失或权限非 600、批级作业在某个运行尚未落定时、BUILD_ONLY 目录已含上次运行、`pbs/HPC_PLAN.txt` 的运行目录不合规）——什么都没启动；`1` = 包内预检失败（运行目录下的 `preflight_*.txt`；正式作业同时写 `STOP_SAFE`，批次停止）；`3` = 停批 / 安全停止（批级作业在停批情形下照常打出 `*_halted_*` 结果包后以 3 退出）；`0` = 正常。
- 运行器 `run_batch4.sh`：`2` = 拒绝（钩子、未登记的时限、PROPOSED 时限、包的 `COMMIT` 与 `./repo/.package_commit` 缺失或不同）；`3` = `STOP` / `STOP_SAFE` / `HALTED`；`0` = `DONE` / `DONE_ONLY`。
- `hpc/hpr_submit.sh`：`2` = 拒绝（什么都没提交）；`1` = `qsub` 失败（输出列出已排队的作业）；`--dry-run`：`0` = 演练完成（最后一行 `DRY_RUN_OK`，什么都没写、没提交），`2` = 包本身有问题（作业脚本或 `pbs/HPC_PLAN.txt` 缺失、依赖顺序错）。

## 附录 2 回传单个文件

`[PowerShell]`（下一行把 `runs/batch6/STATUS.txt` 换成要回传的文件在包目录下的相对路径）：
```powershell
$FILE = "runs/batch6/STATUS.txt"
New-Item -ItemType Directory -Force "D:\ResearchWorkspaces\ASEAN\work\p1_v4_w14_20261109\hpc_results_v4" | Out-Null
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr4/$FILE" "D:\ResearchWorkspaces\ASEAN\work\p1_v4_w14_20261109\hpc_results_v4\"
```

## 附录 3 文件位置（HPC）

| 内容 | 位置 |
|---|---|
| 包、作业脚本、运行器、预检、定义文件 | `/hpctmp/$USER/hpr4/`、`pbs/`、`hpc/`、`BATCH_DEF.json` |
| 代码（预检解包） | `/hpctmp/$USER/hpr4/repo/` |
| conda 环境 | `~/miniforge3/envs/pypsa-earth`（复用） |
| 正式运行目录 / 结果包 / 中间导出 | `/hpctmp/$USER/hpr4/runs/batch6/`（`export/F1`、`export/F2`、`results_*`、`interim_*`） |
| 冒烟 / BUILD_ONLY 目录 | `runs/smoke56_v4/`、`runs/build_only_f1_v4/` |
| PBS 作业输出 | `/hpctmp/$USER/hpr4/` 下以作业名开头、`.o` 加作业序号结尾的文件 |
| 授权文本 | `/hpctmp/$USER/hpr4/HPR_AUTH.txt`（600） |
| 许可 | `~/.gurobi/gurobi.lic`（600；只经 `GRB_LICENSE_FILE` 引用） |
| v3 / v3.1 的记录（不动） | `/hpctmp/$USER/hpr3/`、`/hpctmp/$USER/hpr31/` |

## 附录 4 本手册之外、须由审阅端决定的事项

登记值的任何更改与重新打包；任何中断后的重开（新目录或 `--resume`）；冒烟目标值相对差 > 1e-6 时的处置；目标值低于报警线时的处置；启动锁残留的移开；B1 时 `qstat` 仍列出作业时的处置。
