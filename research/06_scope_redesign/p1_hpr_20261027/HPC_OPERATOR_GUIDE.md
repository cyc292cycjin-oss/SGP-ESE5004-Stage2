# HPC 操作手册（HPR v1，2026-10-27）——第四批 F1 / F2 正式运行，NUS Atlas（PBS Pro），两作业方式

**使用方式：** 你在 Windows PowerShell 中、连着 NUS VPN、登录 `atlas8.nus.edu.sg` 后，按步骤 A → G 逐条复制执行。每一步写明命令、预计用时、成功时应看到什么、失败时把什么发回审阅端。
**标注：** `[PowerShell]` 在你的 Windows 终端执行；`[bash@atlas8]` 在登录节点的 bash 中执行（`ssh` 登录后）。**不要在登录节点上跑任何求解或长时间计算**（交互进程 30 分钟 CPU 限制）。
**占位符：** `<你的用户名>` = 你的 NUS HPC 账号；`<WSL 用户名>` = 你本机 WSL（Ubuntu）里的 Linux 用户名（`[PowerShell] wsl -d Ubuntu -- whoami` 可查）。手册中不含任何真实账号、密码、主机连接串或许可内容。**只在 atlas8 的 bash 行里**可直接用 `$USER`；`[PowerShell]` 行里没有 `$USER`（PowerShell 会把它展开成空），所以 PowerShell 命令一律写 `<你的用户名>`。
**本机路径：** 包 `D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_package`；结果回收到 `D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results`。
**HPC 路径：** 包目录 `/hpctmp/<你的用户名>/hpr`（= `PBS_O_WORKDIR`，所有 `qsub` 都在这里执行）；许可 `~/.gurobi/gurobi.lic`。`/hpctmp` **60 天未改动的文件自动清除**——结果包生成后尽快回收（步骤 G）。
**规则来源：** `RUN_PLAN_HPC.md`（包内副本）。正式运行 F1 / F2 **只在 2026-11-02 17:00（SGT）之后**提交；步骤 A–D、D2 可在 2026-10-29 18:00 维护开始前做，也可在 11-02 17:00 之后做，**由你决定**。F1 / F2 运行期间，本机与任何云端都不得启动 Gurobi 会话。
**任何一步失败：** 不重试、不改参数，把"失败时回传"列出的文件发给审阅端。回传文件用 `[PowerShell] scp <你的用户名>@atlas8.nus.edu.sg:/hpctmp/<你的用户名>/hpr/<文件> D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\`。

---

## 步骤 A 上传包（预计 2–10 分钟）

A1 `[PowerShell]` 确认包完整（本机）：
```powershell
(Get-ChildItem -Recurse -File D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_package | Measure-Object).Count
(Get-Content D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_package\SHA256SUMS | Measure-Object -Line).Lines
Get-Content D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_package\COMMIT
```
成功：第一个数 = 第二个数 + 2（`SHA256SUMS` 列出的 36 个文件，再加 `SHA256SUMS` 本身与清单 `HPC_PACKAGE_MANIFEST.json`，即 38 / 36）；`COMMIT` 为 40 位提交号。

A2 `[PowerShell]` 建目标目录并上传（包约 215 MB；1–10 MB/s 下 0.5–4 分钟；首次连接会问 host key 指纹，输入 yes；之后输入密码或用你已配置的密钥）。远端命令用**单引号**，`$USER` 由 atlas8 展开：
```powershell
ssh <你的用户名>@atlas8.nus.edu.sg 'mkdir -p /hpctmp/$USER && test ! -e /hpctmp/$USER/hpr && echo READY || echo "hpr EXISTS - rename it first"'
scp -r D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_package <你的用户名>@atlas8.nus.edu.sg:/hpctmp/<你的用户名>/hpr
```
成功：第一条打印 `READY`；第二条逐文件显示 100 %，无 `No such file` / `Permission denied`。
失败：把 PowerShell 的完整输出复制发回。如果提示 `hpr EXISTS`：`[bash@atlas8] mv /hpctmp/$USER/hpr /hpctmp/$USER/hpr_old_$(date +%Y%m%d%H%M)` 后重做 A2（不要把包复制进已存在的 `hpr/`，否则会多出一层 `hpr/hpc_package/`）。

A3 `[PowerShell]` 登录，然后 `[bash@atlas8]` 核对 SHA256、设执行权限、检查运行器依赖的工具（约 1 分钟）：
```powershell
ssh <你的用户名>@atlas8.nus.edu.sg
```
```bash
cd /hpctmp/$USER/hpr && sha256sum -c SHA256SUMS | grep -vc ': OK$' ; echo "files=$(wc -l < SHA256SUMS)"
chmod 755 *.sh hpc/*.sh pbs/*.pbs env/install_env.sh
ls -l /usr/bin/time && /usr/bin/time -v true > /dev/null 2>&1 && command -v setsid pgrep timeout curl && echo TOOLS_OK ; echo "shell=$SHELL"
```
成功：第一行输出 `0`（没有不 OK 的文件），第二行 `files=36`；第三组打印 `TOOLS_OK` 与 `shell=/bin/bash`（或其他 shell：作业脚本已指定 `#PBS -S /bin/bash`，不受影响）。
失败（第一行不是 0）：`sha256sum -c SHA256SUMS | grep -v ': OK$'` 看哪些文件失败，只重传这些文件（`[PowerShell] scp D:\...\hpc_package\<文件> <你的用户名>@atlas8.nus.edu.sg:/hpctmp/<你的用户名>/hpr/<文件>`），再做 A3。
失败（没有 `TOOLS_OK`，例如 `/usr/bin/time` 不存在）：**停下**，把这一组命令的输出发回审阅端——运行器与预检硬性依赖 GNU time（`/usr/bin/time`）、`setsid`、`pgrep`、`timeout`，缺失时需要管理员安装 `time` 包或由审阅端提供替代路径的修订；登录节点与计算节点通常是同一镜像，冒烟作业（步骤 D）会在计算节点再查一次。

## 步骤 B 放置许可（预计 2 分钟；手册中没有任何查看许可内容的命令）

B1 `[bash@atlas8]` 建目录：
```bash
mkdir -p ~/.gurobi && chmod 700 ~/.gurobi && ls -ld ~/.gurobi
```
成功：`drwx------ ... /home/svu/<你的用户名>/.gurobi`。

B2 `[PowerShell]`（新开一个 PowerShell 窗口）从本机 WSL 路径把许可文件复制到 HPC（文件约 300 B；不显示内容）。远端路径写成相对家目录的 `.gurobi/gurobi.lic`（不用 `~`，Windows 的新版 scp 走 SFTP，`~` 展开不保证）：
```powershell
scp \\wsl.localhost\Ubuntu\home\<WSL 用户名>\gurobi.lic <你的用户名>@atlas8.nus.edu.sg:.gurobi/gurobi.lic
```
备选（如果 Windows 的 scp 不接受 UNC 路径）：`wsl -d Ubuntu -- scp /home/<WSL 用户名>/gurobi.lic <你的用户名>@atlas8.nus.edu.sg:.gurobi/gurobi.lic`。两种都失败时加 `-O`（用旧的 scp 协议）再试一次。

B3 `[bash@atlas8]` 设权限、只看属性（不看内容）：
```bash
chmod 600 ~/.gurobi/gurobi.lic && ls -l ~/.gurobi/gurobi.lic
```
成功：`-rw------- 1 <你的用户名> ... 3xx ... gurobi.lic`（权限 600、属主是你、大小约 300 字节）。
失败：把 `ls -l` 的输出发回（它不含许可内容）。

## 步骤 C 环境安装作业（计算节点；预计 15–45 分钟，含排队）

C1 `[bash@atlas8]` 提交安装作业（serial 队列，1 核 / 8 GB / 2 h；在计算节点上下载 Miniforge 安装包并安装第三批锁定环境到 `~/miniforge3/envs/pypsa-earth`，conda 缓存放 `/hpctmp`）：
```bash
cd /hpctmp/$USER/hpr && qsub pbs/hpr_install.pbs
```
成功：打印一个作业号（形如 `1234567.venus01`）。

C2 `[bash@atlas8]` 等待并查看（serial 队列排队约 3 分钟实测；安装 15–30 分钟；每隔几分钟执行一次）：
```bash
qstat -u $USER ; tail -5 /hpctmp/$USER/hpr/INSTALL_STATUS.txt 2>/dev/null
```
成功（作业从 `qstat` 列表消失后）：`INSTALL_STATUS.txt` 末尾有
```
ENV_CHECK:key_all_equal=true:...
PREFLIGHT:exit=0:PREFLIGHT OK
REPO:<40 位提交号>:package_commit=<同一提交号>
INSTALL_END:exit=0:...
```
失败：发回 `/hpctmp/$USER/hpr/INSTALL_STATUS.txt`、`/hpctmp/$USER/hpr/hpr_install.o<作业号>`、`install_env_*.log` 的最后 50 行（`tail -50`）。
- 若 `MINIFORGE_DOWNLOAD_FAILED`（计算节点下不到 GitHub）：`[bash@atlas8]` 在登录节点只做下载（不解算、不安装，几十秒）：`curl -L -o /hpctmp/$USER/hpr/Miniforge3-Linux-x86_64.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh`，然后重做 C1。
- 若 `ENV_INSTALL_FAILED` / `CONDA_CREATE_FAILED`，或作业因 walltime / 网络中断留下了半成品环境（再次提交会显示 `ENV:present` 却 `ENV_CHECK:key_all_equal=false`）：`[bash@atlas8] rm -rf ~/miniforge3/envs/pypsa-earth` 删掉半成品后重做 C1（只删这个环境目录；Miniforge 本体保留可复用）。
- 若 `PREFLIGHT:exit=1` 且 `preflight_install_<作业号>.txt` 里有 `MISSING /usr/bin/time`（或 setsid / pgrep / timeout）：计算节点缺少运行器依赖的工具，**停下**发回该文件（见 A3 的说明）。
- 若 `CONDA_CREATE_FAILED` 且日志显示频道不可达：计算节点访问 conda 频道受限。回退办法：请管理员开通到 `conda.anaconda.org` 的访问，或由审阅端提供 NUS 内部镜像地址后以 `qsub -v CONDA_MIRROR_CONDA_FORGE=<镜像>,CONDA_MIRROR_BIOCONDA=<镜像> pbs/hpr_install.pbs` 重提（gurobi 频道没有公共镜像，须直连）。登录节点不能用于 30 分钟以上的安装。
- 若 `ENV_CHECK:key_all_equal=false`：**停下**，发回 `ENV_CHECK.json`；不得用不一致的环境运行。

C3 `[bash@atlas8]` 登录节点预检（1 分钟；不调用 Gurobi）：
```bash
cd /hpctmp/$USER/hpr && bash hpc/hpr_preflight_login.sh > login_preflight.txt 2>&1 ; grep -E "licence file|files OK|PREFLIGHT OK|PREFLIGHT FAILED|HPR_PREFLIGHT_LOGIN" login_preflight.txt
```
成功：输出**至少包含**这四行（还会有标题行与重复的 `all 36 files OK`）：`licence file present, owner <你的用户名>, mode 600`、`all 36 files OK`、`PREFLIGHT OK`、`HPR_PREFLIGHT_LOGIN OK`；且没有任何 `FAILED`。
失败（出现 `FAILED`）：回传 `login_preflight.txt`。

## 步骤 D 冒烟作业（56 时段 F1 + F2 + 批级；预计 1–2 小时 + 排队；2 次 Gurobi 会话）

D1 `[bash@atlas8]` 写授权文件（把 `<你的授权原文>` 换成你的授权文字，一行；**不要写任何账号、主机或许可信息；不要用英文单引号 `'`**，否则命令会断开——用中文引号或不加引号）：
```bash
cd /hpctmp/$USER/hpr && printf '%s\n' '<你的授权原文>' > HPR_AUTH.txt && chmod 600 HPR_AUTH.txt && wc -c HPR_AUTH.txt
```
成功：显示字节数 > 10。

D2 `[bash@atlas8]` 提交冒烟作业（parallel 队列 17 核 / 32 GB / 4 h；计算节点 `curl https://token.gurobi.com` 只记录 HTTP 状态码 → F1 56 时段分进程求解 → ≥ 330 s → F2 → 批级后处理与结果包）：
```bash
cd /hpctmp/$USER/hpr && qsub pbs/hpr_smoke56.pbs
```
成功：打印作业号。parallel 队列排队可能较久（查询时 306 个排队）。

D3 `[bash@atlas8]` 等待并查看（作业结束后）：
```bash
cat /hpctmp/$USER/hpr/runs/smoke56/SMOKE_STATUS.txt
```
成功：含 `WLS_TOKEN_HTTP:302`（或 200；该状态码由 F1 作业体记录在 `runs/smoke56/PBS_JOBS.txt`，批级作业体写入此文件）、`F1:termination=optimal:...:label=ACCEPTED_LAYER2:...:OK`、`F2:...:OK`、`POSTPROC_ERRORS:0`、`BATCH_DONE:True`、`HALTED:False`、**`SMOKE_RESULT:PASS`**。目标值与本机演练值的相对差 `relative_difference` 一般 ≤ 1e-9（跨机器允许到 1e-6）。
失败（`SMOKE_RESULT:FAIL` 或文件不存在）：**不重试**。发回 `runs/smoke56/SMOKE_STATUS.txt`、`runs/smoke56/STATUS.txt`、`runs/smoke56/PBS_JOBS.txt`、`hpr_smoke56.o<作业号>`、`runs/smoke56/preflight_*.txt`。

## 步骤 D2 全尺寸 BUILD_ONLY 测试作业（用户 2026-10-27 补充；预计 1–1.5 小时 + 排队；不调用 Gurobi）

D2-1 `[bash@atlas8]` 提交（parallel 队列 48 核 / 300 GB / 2.5 h；只运行进程 1：完整 2920×3h v2 一体化网络的构建、LP 数组导出与 LP 文件写出；记录峰值内存、LP 文件大小、构建与写出用时、`/hpctmp` 写入速度；结束后删除 LP 文件）：
```bash
cd /hpctmp/$USER/hpr && qsub pbs/hpr_build_only_f1.pbs
```
D2-2 `[bash@atlas8]` 作业结束后：
```bash
cat /hpctmp/$USER/hpr/runs/build_only_f1/BUILD_ONLY_STATUS.txt
```
成功：`RUNNER_EXIT:0`、`BUILD_CHECK_F1:{"passed": true, ...}`、`LP_DELETED:...`、`DONE`。参考预期：`PEAK_RSS_GIB` 72–92、`LP_FILE_BYTES` 约 5.1–5.4e9、`BUILD_SECONDS` + `WRITE_SECONDS` < 3,600。
**无论成败，把 `BUILD_ONLY_STATUS.txt` 发回审阅端**（用于核对估计；它不改变登记值）。若 `PEAK_RSS_GIB` > 150、`RUNNER_EXIT` ≠ 0 或 `BUILD_CHECK_F1` 不是 passed：**先等审阅端回复再做步骤 E**。若 `PEAK_RSS_GIB` 在 100–150 之间：正式运行不受影响（F1 / F2 作业各有 300 / 250 GB），但批级作业（120 GB）若需要补做某个运行的后处理步骤（它们重建 LP，峰值与进程 1 同量级）可能不够——审阅端会据此决定是否提高批级作业内存（登记值变更，需你确认），同样等回复再做 E。
注：此作业与正式运行使用不同目录（`runs/build_only_f1`），不影响步骤 E。**若需重跑 D2**（只在审阅端要求时）：先把上次的目录移走，否则作业体拒绝（`REFUSED: ... holds a previous build-only run`，exit 2，不写任何文件）——因为运行器会按上次的回执跳过构建，记录会重复旧数字：
```bash
mv /hpctmp/$USER/hpr/runs/build_only_f1 /hpctmp/$USER/hpr/runs/build_only_f1_old && cd /hpctmp/$USER/hpr && qsub pbs/hpr_build_only_f1.pbs
```

## 步骤 E 正式提交（只在 2026-11-02 17:00 SGT 之后、D 通过、且无新维护通知时；1 分钟）

E1 `[bash@atlas8]` 重新登录一次，**阅读登录欢迎信息**：确认没有与未来约 11 天（F1 最长 255 h、F2 257 h）重叠的新维护通知。有 → 停下，把欢迎信息发回审阅端。
E2 确认本机与任何云端都没有 Gurobi 在运行（本机 WSL：`wsl -d Ubuntu -- bash -c "ps -eo args | grep -c '[s]2_solve\.py\|[b]4_split_solve\.py'"` 应为 `0`）。
E3 `[bash@atlas8]` 一条命令依次提交 F1、F2（依赖 F1 开始执行）、批级作业（依赖两者结束）：
```bash
cd /hpctmp/$USER/hpr && bash hpc/hpr_submit.sh --auth-file HPR_AUTH.txt --motd-checked
```
成功：
```
SUBMITTED:utc=...:F1=<作业号>:F2=<作业号>:batch=<作业号>:resume=0
F1 job id:    ...
F2 job id:    ...   (starts after F1 started; its Gurobi process waits for F1's Gurobi start + 330 s)
batch job id: ...   (after both ended)
```
作业号也写在 `runs/batch4/SUBMITTED.txt`。把这三个作业号发给审阅端。
失败（输出以 `REFUSED:` 开头，什么都没有提交）：按提示处理——`smoke job has not passed` → 先完成步骤 D；`runs/batch4 exists` → 这是第二次提交，先联系审阅端（不要自行 `--resume`）；`unset before submitting` → 当前 shell 里残留了测试变量，重新登录后再执行；其他 → 把输出发回。

## 步骤 F 监控（每天 1–2 次；一条命令）

F1 `[bash@atlas8]`：
```bash
cd /hpctmp/$USER/hpr && bash hpc/hpr_status.sh
```
看什么：
- `PBS jobs`：F1 / F2 状态 `Q`（排队）→ `R`（运行）；批级作业 `H`（等待依赖）→ `R`；排队可能持续数小时到数天。
- `F1` / `F2` 段：`phase`（`process1_built` → `process2_gurobi_running` → `process2_ended` → `ended:optimal:label=ACCEPTED_LAYER2`）、`gurobi elapsed`、`last barrier line`、`iterations logged`、`monitor` 的最后一行（内存列 `rss_gib_group` / `cgroup_anon_gib`，对配额 300 / 250 GiB）、`projection`（第 20 次迭代后出现，`exceeded: False` 为正常）。
- `stop / error lines`：应为 `(none)`。
- `packs`：批级作业结束后出现 `results_light_final_*.tar.gz`、`results_full_final_*.tar.gz` 及 `.sha256`。
**需要联系审阅端的情况（把 `bash hpc/hpr_status.sh > status_$(date +%Y%m%d%H%M).txt 2>&1` 的文件发回）：**
1. 任何 `STOP_SAFE`、`STOP_NOT_ACCEPTED`、`UNUSABLE`、`HALTED`、`KILLED`、`MEMORY_STOP`、`PROJECTION_STOP`、`PREFLIGHT_FAILED` 行；
2. `projection` 显示 `exceeded: True`；
3. 作业状态为 `E`，或作业从 `qstat` 消失但 `PBS_JOBS.txt` 没有对应的 `JOB_END` 行（节点故障 / walltime）；
4. `remaining to wall cap` 低于 24 小时而 barrier 仍在运行；
5. 登录欢迎信息出现新的维护通知。
**中断后不要自行重提**：从头重开同一运行须审阅端登记并由你明确授权（`RUN_PLAN_HPC.md` 第 6 节）；审阅端会告知是 `hpr_submit.sh --resume`（已结束的运行跳过）还是新的运行目录。
附加文件（审阅端可能索取）：`runs/batch4/STATUS.txt`、`runs/batch4/PBS_JOBS.txt`、`runs/batch4/MONITOR_F1.csv`（可只发最后 200 行 `tail -200`）、`runs/batch4/PROJECTION_F1.json`、`hpr_f1.o<作业号>`。

## 步骤 G 回收结果（批级作业结束后尽快；/hpctmp 60 天清除）

G1 `[bash@atlas8]` 列出结果包（light 约 5 MB，full 约 5 GB，各有 `.sha256`）：
```bash
ls -l /hpctmp/$USER/hpr/runs/batch4/results_*final*
```
停批时文件名为 `*_halted_*`：同样回收，并联系审阅端。

G2 `[PowerShell]` 下载到本机（full 包 5 GB 在 1–10 MB/s 下 10–80 分钟）。一条命令一个文件 / 一个通配符（Windows 的 scp 走 SFTP，不支持远端大括号展开）：
```powershell
New-Item -ItemType Directory -Force D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results | Out-Null
scp "<你的用户名>@atlas8.nus.edu.sg:/hpctmp/<你的用户名>/hpr/runs/batch4/results_*final*" D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\
scp <你的用户名>@atlas8.nus.edu.sg:/hpctmp/<你的用户名>/hpr/runs/batch4/STATUS.txt D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\
scp <你的用户名>@atlas8.nus.edu.sg:/hpctmp/<你的用户名>/hpr/runs/batch4/PBS_JOBS.txt D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\
scp <你的用户名>@atlas8.nus.edu.sg:/hpctmp/<你的用户名>/hpr/runs/batch4/BATCH4_SUMMARY.md D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\
scp <你的用户名>@atlas8.nus.edu.sg:/hpctmp/<你的用户名>/hpr/runs/batch4/BATCH4_SUMMARY.json D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\
```
若 `results_*final*` 的通配符在你的 scp 下报 `No such file`：加 `-O` 再试，或在 `[bash@atlas8]` 用 `ls /hpctmp/$USER/hpr/runs/batch4/results_*final*` 看到确切文件名后逐个下载。
G3 `[PowerShell]` 本机核对 SHA256（每个包一次；两行输出的哈希必须相同）：
```powershell
Get-FileHash -Algorithm SHA256 D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\results_light_final_*.tar.gz | Select-Object -ExpandProperty Hash
(Get-Content D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\results_light_final_*.tar.gz.sha256).Split(' ')[0].ToUpper()
Get-FileHash -Algorithm SHA256 D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\results_full_final_*.tar.gz | Select-Object -ExpandProperty Hash
(Get-Content D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\results_full_final_*.tar.gz.sha256).Split(' ')[0].ToUpper()
```
成功：两对哈希分别相同。失败：重新下载该包（单文件 scp），再核对。
G4 许可文件的处置（你已同意：许可长期存放在个人 `~/.gurobi`，`chmod 600`）。**保留的条件：** 只在你的家目录 `~/.gurobi/gurobi.lic`、权限 600、不进入任何包 / 作业脚本 / 日志 / 结果包（本手册与作业脚本从不复制它）。如改为删除：`[bash@atlas8] rm -f ~/.gurobi/gurobi.lic && ls -la ~/.gurobi`（应只剩目录）。
G5 发给审阅端：G3 的核对结果（两对哈希）与 `hpc_results` 的文件列表；LP / 解数组（约 15 GB）留在 `/hpctmp`，60 天后自动清除，需要时另行下载。

---

## 附录 1 时间窗口与顺序

| 时间 | 可做 |
|---|---|
| 现在 → 2026-10-29 18:00 | A、B、C、D、D2（你决定是否维护前做） |
| 10-29 18:00 → 10-31 06:00 | 不调度新作业；已运行的作业会在 10-31 06:00 被终止——不要在此期间提交任何作业 |
| 10-31 06:00 → 11-02 17:00 | 集群关闭 |
| 11-02 17:00 之后 | （若尚未做）A–D2；E 正式提交；F；G |

## 附录 2 退出码与拒绝

- 作业体 `hpc/hpr_job.sh`：`2` = 拒绝（测试开关残留、缺授权、运行目录有测试残留、许可文件缺失或权限非 600、批级作业在某个运行尚未结束（且不是因停批而从未启动）之前、BUILD_ONLY 作业体在 `runs/build_only_f1` 已含上次运行时、模式错误）——什么都没启动，没有 `STATUS.txt`；`1` = 包内预检失败（`runs/<目录>/preflight_*.txt`）；`3` = 运行器停批 / 安全停止（批级作业在停批情形下照常重评、汇总并打出 `*_halted_*` 结果包后以 3 退出）；`0` = 正常。
- 运行器 `run_batch4.sh`：`2` = 拒绝（钩子、未登记的时限 / 墙钟 / 求解方式、`--auth` 与无求解模式并存）；`3` = `STOP` / `STOP_SAFE` / `HALTED`；`0` = `DONE` / `DONE_ONLY`。
- `hpc/hpr_submit.sh`：`2` = 拒绝（什么都没提交）；`1` = `qsub` 失败（输出里写了哪些已提交）。

## 附录 3 文件位置（HPC）

| 内容 | 位置 |
|---|---|
| 包、作业脚本、`run_batch4.sh`、`preflight.sh` | `/hpctmp/$USER/hpr/`、`pbs/`、`hpc/` |
| 代码（作业 C 解包） | `/hpctmp/$USER/hpr/repo/` |
| conda 环境 | `~/miniforge3/envs/pypsa-earth` |
| 正式运行目录 / 结果包 | `/hpctmp/$USER/hpr/runs/batch4/` |
| 冒烟 / BUILD_ONLY 目录 | `runs/smoke56/`、`runs/build_only_f1/` |
| PBS 作业输出 | `/hpctmp/$USER/hpr/<作业名>.o<作业序号>`（PBS 把 `-j oe` 的输出放回提交目录；序号 = 作业号中 `.` 前的数字） |
| 授权文本 | `/hpctmp/$USER/hpr/HPR_AUTH.txt`（600） |
| 许可 | `~/.gurobi/gurobi.lic`（600；只经 `GRB_LICENSE_FILE` 引用） |

## 附录 4 本手册未包含、须由审阅端决定的事项

- 任何中断后的重开（新目录 / `--resume`）；任何对登记值的更改；D2 结果超出预期时的处置；冒烟目标值相对差 > 1e-6 时的处置。
