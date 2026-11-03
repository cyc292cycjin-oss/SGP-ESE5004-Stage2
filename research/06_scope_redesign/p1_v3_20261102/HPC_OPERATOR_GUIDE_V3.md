# HPC 操作手册 v3（2026-11-04）——V3 正式批次 F1–F4，NUS Atlas（PBS Pro）

**使用前提：** 时限已由审阅端按用户授权决定（2026-11-04，`RUN_PLAN_HPC_V3.md` 第 14 节），包已按登记值重新打出（`BATCH_DEF.json` 的 `limits_status` 为 `REGISTERED`）。如果 A1 显示 `PROPOSED`，说明拿错了包（旧包 `hpc_package_v3_superseded_*`），停下。
**使用方式：** 在 Windows PowerShell 中、连着 NUS VPN，按步骤 A → H 逐条复制执行。`[PowerShell]` 在你的 Windows 终端执行；`[bash@atlas8]` 在登录 `atlas8.nus.edu.sg` 后的 bash 中执行。**不要在登录节点上跑任何求解或长时间计算**（交互进程 30 分钟 CPU 限制）。
**要你替换的值：** 都用大写变量名，每处都在上一行说明从哪里取得：PowerShell 里的 `$HPC_USER`（你的 NUS HPC 账号）和 `$WSL_USER`（本机 WSL 的 Linux 用户名，只在需要重新放置许可时用到）；atlas8 上查看或撤销作业时的作业号 `F1_ID` 等（取自 `runs/batch4/SUBMITTED.txt`）；回收结果时的运行编号 `RID`。atlas8 的 bash 里直接用系统自带的 `$USER`。手册中没有任何真实账号、密码、主机连接串或许可内容。
**本机路径：** 包 `D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_package_v3`；结果 `D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_results`。
**HPC 路径：** 包目录 `/hpctmp/$USER/hpr3`（与 v2 的 `/hpctmp/$USER/hpr` 分开，所有 `qsub` 都在这里执行）；许可 `~/.gurobi/gurobi.lic`。`/hpctmp` **60 天未改动的文件自动清除**——每个运行结束后先回收它的导出（步骤 G1），批级作业结束后回收结果包（步骤 G2）。
**同期禁止：** 从冒烟作业开始到最后一个正式求解结束，本机（WSL）与 AutoDL 都不得启动 Gurobi（同一 WLS 许可；`RUN_PLAN_HPC_V3.md` 第 13 节）。
**任何一步失败：** 不重试、不改参数，把"失败时回传"的文件发给审阅端（下载命令见附录 2）。

每个 PowerShell 窗口开头先设账号变量（下一行把 `YOUR_NUS_ID` 换成你的 NUS HPC 账号，只改引号里的内容）：
```powershell
$HPC_USER = "YOUR_NUS_ID"
```

## 用户上 HPC 操作清单（按顺序；细节见后面的步骤 A–H）

时限已由审阅端按你的授权登记（`RUN_PLAN_HPC_V3.md` 第 14 节）：TimeLimit 240 h；walltime F1、F3 260 h，F2、F4 262 h，批级 48 h；`BATCH_DEF.json` 的 `limits_status` 为 `REGISTERED`。

**(a) 连 VPN 之前。** `[PowerShell]` 确认本机没有 Gurobi 进程（两行都应输出 `0`），并确认本机的两个 Claude Code 会话都已停下（窗口里没有正在运行的任务）：
```powershell
wsl -d Ubuntu -- bash -c "ps -eo args | grep -c '[s]2_solve.py'"
wsl -d Ubuntu -- bash -c "ps -eo args | grep -c '[b]4_split_solve.py'"
```

**(b) 连上 AnyConnect 后，WSL 的外连会断。** 之后的上传和下载一律在 Windows PowerShell 里用 Windows 自带的 `ssh` / `scp`，不要用 `wsl ... scp`。本机包路径：`D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_package_v3`。上传命令（步骤 A2）：
```powershell
scp -r D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_package_v3 "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr3"
```

**(c) 登录节点上的两项检查。**
- c1 登录后先看 bash 版本：`[bash@atlas8]` `bash --version | head -1`。期望 `GNU bash, version 4.2.x` 或更高（例如 `version 4.2.46(2)-release`）。脚本已在本机编译的 bash 4.2 下实测过（报告第 8 节），4.2 及以上都可以用；低于 4.2 → 停下，把这一行发回。
- c2 上传并核对完成后（步骤 A3 之后），做一次**不提交演练**。它只打印 qsub 命令，不写文件、不提交任何作业、不调用 qsub：
```bash
cd /hpctmp/$USER/hpr3 && bash hpc/hpr_submit.sh --auth-file HPR_AUTH.txt --motd-checked --dry-run
```
期望输出：
```
DRY-RUN NOTE: --auth-file FILE (the user authorisation text) is required (step D1 writes HPR_AUTH.txt) - a real submission would be refused
DRY-RUN NOTE: the smoke job has not passed (/hpctmp/.../runs/smoke56/SMOKE_STATUS.txt: SMOKE_RESULT:PASS missing) - step D first - a real submission would be refused
DRY-RUN NOTE: ./repo is not the package commit ... (step C install job / preflight sha) - a real submission would be refused
DRY-RUN: qsub pbs/hpr3_f1.pbs
DRY-RUN: qsub -W depend=after:F1_JOBID pbs/hpr3_f2.pbs
DRY-RUN: qsub -W depend=afterany:F1_JOBID pbs/hpr3_f3.pbs
DRY-RUN: qsub -W depend=afterany:F2_JOBID pbs/hpr3_f4.pbs
DRY-RUN: qsub -W depend=afterany:F3_JOBID:F4_JOBID pbs/hpr3_batch.pbs
DRY_RUN_OK: nothing submitted (bash 4.2.46(2)-release; 5 jobs; 3 check(s) above would refuse a real submission)
```
这时还没做步骤 C、D，所以前三行 `DRY-RUN NOTE` 是正常的（`bash` 后面是登录节点的实际版本）。`~/.gurobi/gurobi.lic` 还没放好时会多一行 `licence file missing or not mode 600` 的 NOTE，做完步骤 B 就会消失。**停下并把输出发回的情况：** 出现 `unbound variable`、`syntax error`、`command not found` 或 `REFUSED:`；`DRY-RUN: qsub` 行不是这 5 行或顺序不同；最后一行不是 `DRY_RUN_OK`；出现上面三种以外的 `DRY-RUN NOTE`。
- c3 步骤 D 通过后、正式提交（步骤 E3）之前，**再演练一次**（同一条命令）。期望：没有任何 `DRY-RUN NOTE`，同样的 5 行 `DRY-RUN: qsub`，最后一行以 `0 check(s) above would refuse a real submission)` 结尾。你确认无误后，才执行 E3。

**(d) 单路上传与核对：** 步骤 A（一条 `scp -r` 上传，然后在 atlas8 上运行 `sha256sum -c SHA256SUMS`，输出必须是 `0` 个不 OK 的文件）。

**(e) 预检：** 步骤 C 是登录节点预检，不调用 Gurobi，期望 `HPR_PREFLIGHT_LOGIN OK`。步骤 D 是冒烟作业：它在计算节点上做作业内预检和两次 56 时段求解，期望 `SMOKE_RESULT:PASS`。两项都通过后才能进入 (f)。

**(f) 提交作业：** 先做步骤 E1、E2，然后用一条命令按顺序提交 F1、F2、F3、F4 与批级作业：
```bash
cd /hpctmp/$USER/hpr3 && bash hpc/hpr_submit.sh --auth-file HPR_AUTH.txt --motd-checked
```
只有当这条命令因为非 qsub 的原因无法使用、且审阅端同意时，才逐条手工提交。每一行的作业号从上一条 `qsub` 的输出中取得：
```bash
cd /hpctmp/$USER/hpr3
F1_ID=$(qsub pbs/hpr3_f1.pbs) && echo $F1_ID
F2_ID=$(qsub -W depend=after:$F1_ID pbs/hpr3_f2.pbs) && echo $F2_ID
F3_ID=$(qsub -W depend=afterany:$F1_ID pbs/hpr3_f3.pbs) && echo $F3_ID
F4_ID=$(qsub -W depend=afterany:$F2_ID pbs/hpr3_f4.pbs) && echo $F4_ID
B_ID=$(qsub -W depend=afterany:$F3_ID:$F4_ID pbs/hpr3_batch.pbs) && echo $B_ID
mkdir -p runs/batch4 && echo "SUBMITTED:manual:F1=$F1_ID:F2=$F2_ID:F3=$F3_ID:F4=$F4_ID:batch=$B_ID" >> runs/batch4/SUBMITTED.txt
```

**(g) 查看队列与排队原因：** 下面第二行的 `F1_ID` 换成 `runs/batch4/SUBMITTED.txt` 里的作业号（形如 `1234567.venus01`）：
```bash
qstat -u $USER
F1_ID=1234567.venus01
qstat -f $F1_ID | grep -E "comment|estimated|job_state|exec_host"
```
`comment` 会说明排队原因，例如资源不足、依赖未满足。`estimated.start_time` 是调度器估计的开始时间。在步骤 F 里每天运行一次 `bash hpc/hpr_status.sh`。

**(h) 撤销作业时，连同依赖它的作业一起撤销：** 依赖关系是 F2 依赖 F1（after），F3 依赖 F1（afterany），F4 依赖 F2（afterany），批级依赖 F3 和 F4（afterany）。`afterany` 表示前一个作业**无论怎样结束**都会放行后一个。所以只 `qdel` F1 会让 F3 马上开始。撤销 F1 时，要同时撤销 F2、F3、F4 和批级；只撤销 F2 时，要同时撤销 F4 和批级。作业号从 `runs/batch4/SUBMITTED.txt` 取得（下一行换成你的 5 个作业号）：
```bash
F1_ID=1234567.venus01; F2_ID=1234568.venus01; F3_ID=1234569.venus01; F4_ID=1234570.venus01; B_ID=1234571.venus01
qdel $B_ID $F4_ID $F3_ID $F2_ID $F1_ID
```
先撤后面的，再撤前面的。撤销之前先联系审阅端（步骤 H）。即使漏撤，F3（F4）开始时也会发现 F1（F2）没有正常结束，于是写 `STOP_SAFE:PREDECESSOR_NOT_ENDED` 并停批，不会启动求解；但它仍会排队、占用节点，所以还是要一起撤。

**(i) 结果下载与 `/hpctmp` 的清理：** 每个运行结束后，用步骤 G1 回收该运行的导出；批级作业结束后，用步骤 G2 单路下载结果包，并在本机用 `Get-FileHash` 核对。`/hpctmp` 中 **60 天未改动的文件会被自动清除**，所以下载完成并核对后再发给审阅端。

---

## 步骤 A 上传包（单路；约 375 MB，1 MB/s 约 6 分钟，0.1 MB/s 约 1 小时）

A1 `[PowerShell]` 本机确认包完整：
```powershell
$PKG = "D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_package_v3"
(Get-ChildItem -Recurse -File $PKG | Measure-Object).Count
(Get-Content "$PKG\SHA256SUMS" | Measure-Object -Line).Lines
Get-Content "$PKG\COMMIT"
Select-String -Path "$PKG\BATCH_DEF.json" -Pattern '"limits_status"'
```
成功：第一个数 = 第二个数 + 2（`SHA256SUMS` 本身与 `HPC_PACKAGE_MANIFEST.json` 不在清单里）；`COMMIT` 为 40 位提交号；`limits_status` 为 `REGISTERED`（正式运行的前提；是 `PROPOSED` 时只能做步骤 D / D2）。

A2 `[PowerShell]` 建目标目录并上传（**一条 `scp -r`，不要并行开多个上传**；首次连接问 host key 时输入 yes）：
```powershell
ssh "${HPC_USER}@atlas8.nus.edu.sg" 'mkdir -p /hpctmp/$USER && test ! -e /hpctmp/$USER/hpr3 && echo READY || echo "hpr3 EXISTS - rename it first"'
scp -r $PKG "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr3"
```
成功：第一条打印 `READY`；第二条逐文件到 100 %。
失败：提示 `hpr3 EXISTS` → `[bash@atlas8] mv /hpctmp/$USER/hpr3 /hpctmp/$USER/hpr3_old_$(date +%Y%m%d%H%M)` 后重做 A2（不要往已有的 `hpr3/` 里复制，否则会多出一层目录）。其他错误把 PowerShell 输出发回。

A3 `[PowerShell]` 登录，然后 `[bash@atlas8]` 核对全部文件的 SHA256、设权限、查工具：
```powershell
ssh "${HPC_USER}@atlas8.nus.edu.sg"
```
```bash
cd /hpctmp/$USER/hpr3 && sha256sum -c SHA256SUMS | grep -vc ': OK$' ; echo "files=$(wc -l < SHA256SUMS)"
chmod 755 *.sh hpc/*.sh pbs/*.pbs env/install_env.sh
/usr/bin/time -v true > /dev/null 2>&1 && command -v setsid pgrep timeout curl > /dev/null && echo TOOLS_OK
```
成功：第一行 `0`，第二行 `files=` 等于 A1 的第二个数；第三行 `TOOLS_OK`。
失败（第一行不是 0）：`sha256sum -c SHA256SUMS | grep -v ': OK$'` 看哪些文件不对，只重传这些文件（下一行的 `FILE` 换成那个文件在包内的相对路径，例如 `networks/integrated_2920_3h_unsolved.nc`），再做 A3：
```powershell
$FILE = "networks/integrated_2920_3h_unsolved.nc"
scp "$PKG\$($FILE -replace '/', '\')" "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr3/$FILE"
```

## 步骤 B 许可（HPR 时已放在 `~/.gurobi`；只核对属性，不看内容）

B1 `[bash@atlas8]`：
```bash
ls -l ~/.gurobi/gurobi.lic
```
成功：`-rw------- 1 ...你的账号... gurobi.lic`（权限 600、属主是你，约 300 字节）。不是 600：`chmod 600 ~/.gurobi/gurobi.lic` 再看一次。
文件不存在时（下一行把 `YOUR_WSL_USER` 换成本机 WSL 的 Linux 用户名，`wsl -d Ubuntu -- whoami` 可查），`[PowerShell]`：
```powershell
$WSL_USER = "YOUR_WSL_USER"
ssh "${HPC_USER}@atlas8.nus.edu.sg" 'mkdir -p ~/.gurobi && chmod 700 ~/.gurobi'
scp "\\wsl.localhost\Ubuntu\home\$WSL_USER\gurobi.lic" "${HPC_USER}@atlas8.nus.edu.sg:.gurobi/gurobi.lic"
ssh "${HPC_USER}@atlas8.nus.edu.sg" 'chmod 600 ~/.gurobi/gurobi.lic && ls -l ~/.gurobi/gurobi.lic'
```

## 步骤 C 环境与登录预检（不安装；HPR 时已装好环境；不调用 Gurobi，约 1 分钟）

C1 `[bash@atlas8]`：
```bash
cd /hpctmp/$USER/hpr3 && bash hpc/hpr_preflight_login.sh > login_preflight.txt 2>&1 ; grep -E "licence file|files OK|key packages|limits of the package|PREFLIGHT OK|PREFLIGHT FAILED|HPR_PREFLIGHT_LOGIN" login_preflight.txt
```
成功：至少包含 `licence file present, owner ..., mode 600`、`all ... files OK`、`limits of the package definition: TimeLimit ... status REGISTERED`、`PREFLIGHT OK`、`HPR_PREFLIGHT_LOGIN OK`，没有 `FAILED`。预检的 `sha` 节同时把代码解包到 `./repo`；`env` 节把环境与 `env/ENV_LOCK.txt` 逐包比对（一致即复用，HPR 时为 284 / 284）。
失败：回传 `login_preflight.txt`。若 `env` 节报 `KEY PACKAGES DIFFER`：**停下**，不要自行重装，等审阅端回复（必要时按 v2 手册的步骤 C 提交 `pbs/hpr3_install.pbs`）。

## 步骤 D 冒烟作业（56 时段 F1 + F2 + 批级；2 次 Gurobi 会话；预计 1 小时 + 排队）

D1 `[bash@atlas8]` 写授权文件（把引号里的 `你的授权原文` 换成你的授权文字，一行；不写账号、主机或许可信息；不要用英文单引号）：
```bash
cd /hpctmp/$USER/hpr3 && printf '%s\n' '你的授权原文' > HPR_AUTH.txt && chmod 600 HPR_AUTH.txt && wc -c HPR_AUTH.txt
```
D2 `[bash@atlas8]` 提交（17 核 / 32 GB / 4 h；计算节点只记 `curl https://token.gurobi.com` 的 HTTP 状态码 → F1 56 时段 → ≥ 330 s → F2 → 批级后处理与结果包）：
```bash
cd /hpctmp/$USER/hpr3 && qsub pbs/hpr3_smoke56.pbs
```
D3 `[bash@atlas8]` 作业结束后：
```bash
cat /hpctmp/$USER/hpr3/runs/smoke56/SMOKE_STATUS.txt
```
成功：`WLS_TOKEN_HTTP:302`（或 200）、`F1:termination=optimal:...:label=ACCEPTED_LAYER2:...:OK`、`F2:...:OK`、`POSTPROC_ERRORS:0`、`BATCH_DONE:True`、`HALTED:False`、**`SMOKE_RESULT:PASS`**。期望目标值是本机冒烟值（F1 329,705,566,422.23596、F2 342,268,691,464.4567 EUR），`relative_difference` 应 ≤ 1e-6。
失败：**不重试**。发回 `runs/smoke56/SMOKE_STATUS.txt`、`STATUS.txt`、`PBS_JOBS.txt`、`preflight_*.txt` 与 `hpr3_smoke56.o` 开头的作业输出。相对差 > 1e-6 也先发回审阅端，再做 E。

## 步骤 D2（可选）全尺寸 BUILD_ONLY（审阅端要求时才做；不调用 Gurobi；约 1 小时 + 排队）

```bash
cd /hpctmp/$USER/hpr3 && qsub pbs/hpr3_build_only_f1.pbs
```
结束后 `cat /hpctmp/$USER/hpr3/runs/build_only_f1/BUILD_ONLY_STATUS.txt`，无论成败发回。参考：峰值约 96 GiB、LP 约 5.5 GB、构建加写出约 2,500 s。

## 步骤 E 正式提交（D 通过、无新维护通知；1 分钟）

E1 `[bash@atlas8]` 重新登录一次，**阅读登录欢迎信息**：确认没有与未来约 22 天（F1 + F3 的 walltime 最长 260 + 260 h）重叠的维护通知。有 → 停下，把欢迎信息发回审阅端。然后做清单 c3 的第二次不提交演练，确认输出无误。
E2 `[PowerShell]` 确认本机没有 Gurobi 在运行（应输出 `0`）；AutoDL 实例不在运行求解：
```powershell
wsl -d Ubuntu -- bash -c "ps -eo args | grep -c '[s]2_solve.py'"
```
E3 `[bash@atlas8]` 一条命令按登记顺序提交五个作业：F1；F2（F1 开始后）；F3（F1 结束后）；F4（F2 结束后）；批级（F3、F4 结束后）：
```bash
cd /hpctmp/$USER/hpr3 && bash hpc/hpr_submit.sh --auth-file HPR_AUTH.txt --motd-checked
```
成功：
```
F1 job id: ...
F2 job id: ...   (depend=after:F1)
F3 job id: ...   (depend=afterany:F1)
F4 job id: ...   (depend=afterany:F2)
batch job id: ...   (depend=afterany:F3:F4)
SUBMITTED:utc=...:F1=...:F2=...:F3=...:F4=...:batch=...:resume=0
```
作业号也写在 `runs/batch4/SUBMITTED.txt`；把五个作业号发给审阅端。
失败（输出以 `REFUSED:` 开头，什么都没有提交）：`limits of the package are PROPOSED` → 拿错了包，联系审阅端；`smoke job has not passed` → 先完成 D；`runs/batch4 exists` → 联系审阅端（不要自行 `--resume`）；`gurobi_start_lock exists` → 联系审阅端（步骤 H3）；`unset before submitting` → 重新登录后再执行；其他 → 发回输出。`qsub ... failed - already queued: ...` → 把这行发回，审阅端决定是否 `qdel` 已排队的作业。

## 步骤 F 监控（每天 1–2 次；一条命令）

```bash
cd /hpctmp/$USER/hpr3 && bash hpc/hpr_status.sh
```
看什么：
- `PBS jobs`：F1、F2 由 `Q` 到 `R`；F3、F4、批级为 `H`（等依赖）；F1 结束后 F3 变 `Q` / `R`，F2 结束后 F4 同样。
- `F1`–`F4` 段：`phase`（`process1_built` → `process2_gurobi_running` → `process2_ended` → `ended:optimal:label=ACCEPTED_LAYER2`）、`gurobi elapsed`、最后一行 barrier、`monitor` 最后一行（内存对配额 300 / 250 GiB）、`projection`（第 20 次迭代后出现，`exceeded: False` 为正常）。
- `start lock held by: ...`：某个运行正在等待启动 Gurobi 的时机。通常只有几分钟；如果另一个运行的 Gurobi 刚启动或刚结束（不到 330 s），或者已有 2 个求解在跑，可以合法持有到 2 小时（`WAIT_START_MAX_S`）。持有超过 2 小时，或出现 `STOP_SAFE:START_LOCK` → 见步骤 H3。
- `STOP / STOP_SAFE files`：只要出现这一段，就说明批次已停，照步骤 H 处理。
- `stop / error lines`：应为 `(none)`。
**需要联系审阅端（把 `bash hpc/hpr_status.sh > status_$(date +%Y%m%d%H%M).txt 2>&1` 生成的文件发回）：** 任何 `STOP_SAFE`、`STOP_NOT_ACCEPTED`、`UNUSABLE`、`HALTED`、`KILLED`、`MEMORY_STOP`、`PROJECTION_STOP`、`START_LOCK`、`PREFLIGHT_FAILED` 行；`projection` 为 `exceeded: True`；作业状态 `E`，或作业消失但 `PBS_JOBS.txt` 没有对应的 `JOB_END`；`remaining to wall cap` 低于 24 小时而 barrier 仍在运行；新的维护通知。

## 步骤 G 回收结果（单路下载，本机核对 SHA256）

G1 **每个运行结束后**（`hpr_status.sh` 显示该运行 `ended:...`），先回收它的导出（不含网络文件，约几十 MB）。`[bash@atlas8]`（下一行把 `F1` 换成刚结束的运行：F1、F2、F3 或 F4）：
```bash
RID=F1
cd /hpctmp/$USER/hpr3/runs/batch4 && tar czf interim_${RID}.tar.gz --exclude='*.nc' export/$RID && sha256sum interim_${RID}.tar.gz > interim_${RID}.tar.gz.sha256 && ls -l interim_${RID}.tar.gz*
```
`[PowerShell]`（下一行同样把 `F1` 换成那个运行）：
```powershell
$RID = "F1"
$RES = "D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_results"
New-Item -ItemType Directory -Force $RES | Out-Null
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr3/runs/batch4/interim_${RID}.tar.gz" $RES
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr3/runs/batch4/interim_${RID}.tar.gz.sha256" $RES
(Get-FileHash -Algorithm SHA256 "$RES\interim_${RID}.tar.gz").Hash
(Get-Content "$RES\interim_${RID}.tar.gz.sha256").Split(' ')[0].ToUpper()
```
成功：最后两行相同。

G2 **批级作业结束后**：`[bash@atlas8]` `ls -l /hpctmp/$USER/hpr3/runs/batch4/results_*` 看到 `results_light_final_*.tar.gz`、`results_full_final_*.tar.gz` 与 `.sha256`（停批时为 `*_halted_*`，同样回收并联系审阅端）。`[PowerShell]` 先下载并核对 light，再下载 full（一次一个文件，不要并行；full 约 5–10 GB）：
```powershell
$RES = "D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_results"
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr3/runs/batch4/results_light_*" $RES
Get-ChildItem "$RES\results_light_*.tar.gz" | ForEach-Object { $_.Name; (Get-FileHash -Algorithm SHA256 $_.FullName).Hash; (Get-Content "$($_.FullName).sha256").Split(' ')[0].ToUpper() }
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr3/runs/batch4/results_full_*" $RES
Get-ChildItem "$RES\results_full_*.tar.gz" | ForEach-Object { $_.Name; (Get-FileHash -Algorithm SHA256 $_.FullName).Hash; (Get-Content "$($_.FullName).sha256").Split(' ')[0].ToUpper() }
foreach ($F in "STATUS.txt", "PBS_JOBS.txt", "SUBMITTED.txt", "BATCH4_SUMMARY.md", "BATCH4_SUMMARY.json") { scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr3/runs/batch4/$F" $RES }
```
成功：每个包名下的两行哈希相同。不同 → 只重新下载该文件再核对。通配符报 `No such file` 时加 `-O` 再试，或在 atlas8 上 `ls` 出确切文件名后逐个下载。
G3 把核对结果与 `hpc_results` 的文件列表发给审阅端。LP / 解数组（约 30 GB）留在 `/hpctmp`，60 天未改动自动清除，需要时另行下载。

## 步骤 H 出现 `STOP` / `STOP_SAFE` 时

H1 **先不要动作业。** 不重提、不 `qdel`（除非审阅端要求）、不删除运行目录里的任何文件。停批是设计好的：尚未启动求解的运行会以 `NOT_STARTED_<编号>` 结束（退出码 3），批级作业仍会运行，重评、汇总并打出 `results_*_halted_*` 结果包。
H2 `[bash@atlas8]` 留存状态并发回：
```bash
cd /hpctmp/$USER/hpr3 && bash hpc/hpr_status.sh > status_$(date +%Y%m%d%H%M).txt 2>&1 ; cat runs/batch4/STOP runs/batch4/STOP_SAFE 2>/dev/null ; tail -40 runs/batch4/STATUS.txt
```
发回生成的 `status_*.txt`、`runs/batch4/STATUS.txt`、`runs/batch4/PBS_JOBS.txt`，以及 `STOP_SAFE` 里点名的那个运行的 `runs/batch4/MONITOR_<编号>.csv`（可只发 `tail -200`）与 `PROJECTION_<编号>.json`。

| 行 | 含义 | 审阅端可能的决定 |
|---|---|---|
| `STOP_SAFE:MEMORY:<编号>` | 内存超过配额 80 %，该求解已终止 | 以更大内存的新运行目录重开（资源原因的重新开始，须你授权） |
| `STOP_SAFE:PROJECTION:<编号>` | 前 20 次迭代外推超过 0.80 × TimeLimit | 以更长的登记时限重开，或调整计划 |
| `STOP_SAFE:INTERRUPTED_<编号>` | 续跑时发现已开始未结束的求解 | 新运行目录重开 |
| `STOP_SAFE:WAIT_START:F2` | F1 在 2 小时内没有启动 Gurobi | 视 F1 状态决定 |
| `STOP_SAFE:START_LOCK:<编号>` | 启动锁 2 小时内取不到（锁残留，或已有 2 个求解在跑） | 见 H3 |
| `PREDECESSOR_NOT_ENDED:F3:F1`（或 `F4:F2`） | F3（F4）开始时，F1（F2）的作业已经结束，但运行没有正常结束、也没有停批（例如被 `qdel`、到了 walltime、作业体拒绝）；F3（F4）什么都没启动 | 视 F1（F2）的情况决定 |
| `PREFLIGHT_FAILED:<编号>` | 正式作业的包内预检不通过；该运行什么都没启动，批次随之停止 | 看 `runs/batch4/preflight_*.txt` 后决定 |
| `STOP_NOT_ACCEPTED` / `UNUSABLE` | G2 不过 / 无返回解 / C1 (a) 不过 | 用户决定 |
| `KILLED_..._<编号>` | 进程 2 到了墙钟 | 用户决定 |

H3 **启动锁残留**（只在审阅端确认后做）：锁目录 `runs/batch4/.gurobi_start_lock` 只在某个作业等待启动 Gurobi 时存在，通常几分钟，最多 2 小时。若 `hpr_status.sh` 显示它被持有超过 2 小时：`[bash@atlas8]` 先确认持有者（`cat` 出来的第一项是运行编号，第二项是取得锁的时刻）已不在运行：
```bash
cat /hpctmp/$USER/hpr3/runs/batch4/.gurobi_start_lock/owner ; qstat -u $USER
```
持有者的作业已不在 `qstat` 中、且审阅端同意时，才把锁目录改名移开（保留，不删除）：
```bash
mv /hpctmp/$USER/hpr3/runs/batch4/.gurobi_start_lock /hpctmp/$USER/hpr3/runs/batch4/stale_start_lock_$(date +%Y%m%d%H%M)
```
之后被 `STOP_SAFE:START_LOCK` 停下的运行如何继续，由审阅端登记后告知。

---

## 附录 1 退出码与拒绝

- 作业体 `hpc/hpr_job.sh`：`2` = 拒绝（测试开关残留、缺授权、PROPOSED 时限下的正式作业、运行编号不在定义文件中、运行目录有测试残留、许可文件缺失或权限非 600、批级作业在某个运行尚未落定时、BUILD_ONLY 目录已含上次运行）——什么都没启动；`1` = 包内预检失败（`runs/<目录>/preflight_*.txt`；正式作业同时写 `STOP_SAFE`，批次停止）；`3` = 停批 / 安全停止（含 F3、F4 的前序检查 `PREDECESSOR_NOT_ENDED`；批级作业在停批情形下照常打出 `*_halted_*` 结果包后以 3 退出）；`0` = 正常。
- 运行器 `run_batch4.sh`：`2` = 拒绝（钩子、未登记的时限、PROPOSED 时限、四个运行时的单机批次模式）；`3` = `STOP` / `STOP_SAFE` / `HALTED`；`0` = `DONE` / `DONE_ONLY`。
- `hpc/hpr_submit.sh`：`2` = 拒绝（什么都没提交）；`1` = `qsub` 失败（输出列出已排队的作业）；`--dry-run`：`0` = 演练完成（最后一行 `DRY_RUN_OK`，什么都没写、没提交），`2` = 包本身有问题（作业脚本或 `pbs/HPC_PLAN.txt` 缺失、依赖顺序错）。

## 附录 2 回传单个文件

`[PowerShell]`（下一行把 `runs/batch4/STATUS.txt` 换成要回传的文件在包目录下的相对路径）：
```powershell
$FILE = "runs/batch4/STATUS.txt"
scp "${HPC_USER}@atlas8.nus.edu.sg:/hpctmp/${HPC_USER}/hpr3/$FILE" "D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_results\"
```

## 附录 3 文件位置（HPC）

| 内容 | 位置 |
|---|---|
| 包、作业脚本、运行器、预检、定义文件 | `/hpctmp/$USER/hpr3/`、`pbs/`、`hpc/`、`BATCH_DEF.json` |
| 代码（预检解包） | `/hpctmp/$USER/hpr3/repo/` |
| conda 环境 | `~/miniforge3/envs/pypsa-earth` |
| 正式运行目录 / 结果包 / 中间导出 | `/hpctmp/$USER/hpr3/runs/batch4/`（`export/F1`–`export/F4`、`results_*`、`interim_*`） |
| 冒烟 / BUILD_ONLY 目录 | `runs/smoke56/`、`runs/build_only_f1/` |
| PBS 作业输出 | `/hpctmp/$USER/hpr3/` 下以作业名开头、`.o` 加作业序号结尾的文件 |
| 授权文本 | `/hpctmp/$USER/hpr3/HPR_AUTH.txt`（600） |
| 许可 | `~/.gurobi/gurobi.lic`（600；只经 `GRB_LICENSE_FILE` 引用） |

## 附录 4 本手册之外、须由审阅端决定的事项

登记值的任何更改与重新打包；任何中断后的重开（新目录或 `--resume`）；冒烟目标值相对差 > 1e-6 时的处置；启动锁残留的删除；任何登记值的更改。
