# L23 首批云端正式运行：进度记录（防中断用；每步提交后更新；时间为 SGT；不含任何凭据、主机或端口）

指令 `L23_RUN1_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-19 00:50 SGT），开始前核对 SHA256 = `2c6d9dcad11a2e6e5ff9f25d0ec6a1ff1cd45213dfabce636987df5b54790d22`，与 `L23_RUN1_INSTRUCTION_SHA256.txt` 一致（2026-10-19，VERIFIED）。模型 Opus 5.5。所有过程说明一律用中文。

## 用户授权原文（用户启动本指令时给出，原样记录）

> 我授权 Claude Code 经 SSH 连接 AutoDL 实例（西北 B 区 144 机，509c44b497-0de3e721，RTX 3080 Ti × 1，12 核 Xeon Silver 4214R，90 GB 内存，数据盘 50 GB），执行以下操作：上传 S4K 部署包 cloud_package_dist（代码提交 56d283580799c510b617c70b6e3292ba224e4ae0）并校验；安装 conda 环境；用 scp 把本机 Gurobi 许可文件直接传到实例 /root/.gurobi/gurobi.lic（权限 600，不读取、不打印、不复制到其他位置，结果回收后删除）；运行预检；预检通过并等待 5 分钟后，在 tmux 中启动首批 365×24h 正式运行（一体化 STEPS、不互联 STEPS、一体化 NZE，以及仅在不互联主算非最优时自动运行的不互联诊断），求解档案 A（formal_barrier），串行，每运行 TimeLimit 10,500 s、墙钟上限 3 h，不重试、不改参数、不 warm start；监督运行、下载结果并核对、写首轮分析报告。第二批敏感性、联盟研究、2920×3h 与任何重跑不在本次授权范围内。实例关机由我本人在 AutoDL 控制台操作。授权人：程宇晨；时间：2026-10-19 ＿＿:＿＿（SGT）。

（授权原文中的时间栏为空，按原样记录；本会话收到该授权的时间约为 2026-10-19 00:47 SGT，按本机时钟。）

## 要点

- **实例：** AutoDL 西北 B 区 144 机，实例 509c44b497-0de3e721，RTX 3080 Ti × 1（GPU 不用），12 核 Xeon Silver 4214R，90 GB 内存，数据盘 50 GB，按量计费（¥1.08/时）。报告与本文件只写"西北 B 区 144 机"，不写主机、端口、密码。
- **部署包：** `D:\ResearchWorkspaces\ASEAN\work\p1_step4k_20261018\cloud_package_dist\`（代码提交 56d283580799c510b617c70b6e3292ba224e4ae0）；不得使用 `cloud_package_dist_2d4aaac3_superseded` 及 S4J 以前的部署包。
- **运行：** 一体化 STEPS、不互联 STEPS、一体化 NZE，以及仅在不互联主算非最优时自动运行的不互联诊断；档案 A（`--solver-profile formal_barrier`），`--mode serial`；每运行 TimeLimit 10,500 s、墙钟上限 3 h（脚本固定）。不在范围内：第二批敏感性、联盟运行、2920×3h、任何重跑、参数修改、warm start。
- **许可：** 本机许可文件经 `scp` 直接传到实例 `/root/.gurobi/gurobi.lic`，`chmod 600`；全程不 `cat`、不打印、不复制到其他位置、不纳入打包；运行时只经 `GRB_LICENSE_FILE` 引用；结果回收后 `rm -f /root/.gurobi/gurobi.lic`。运行期间本机不启动任何 Gurobi 求解（包括测试）；预检结束后至少等 5 分钟再启动正式运行。
- **SSH：** 密钥登录；主机与端口只出现在命令行参数中，不写入任何文件；known_hosts 用会话临时目录中的独立文件并散列记录（`HashKnownHosts=yes`）。
- **分支：** `codex/l23-run1-20261019`，自 PR #35 最新提交 ca5eb801 开出（已核实 = 远端 `codex/s4k-ac-loss-proxy-20261018` 头 `ca5eb801ad6acb9609a8062aaea2aceab4f72473`）；draft PR 叠在 #35 上；结果压缩包不进 git。
- **仓库镜像：** `research/06_scope_redesign/p1_l23_run1_20261019/`。

## 步骤状态

| 步 | 内容 | 状态 | 时间（SGT） | 说明 |
|---|---|---|---|---|
| C0 | 核对与记录 | 完成 | 2026-10-19 00:48 | 指令 SHA256 一致；本机部署包 `sha256sum -c SHA256SUMS` 15 个 OK，`COMMIT` = 56d28358…；授权原文已记录 |
| C1 | 连接与实例核对 | 完成 | 2026-10-19 01:02 | 第一次尝试两把密钥都被拒（约 01:00，已停下报告）；用户把 WSL `~/.ssh/id_ed25519` 的公钥加入实例后，用该密钥免密登录成功。实例：Intel Xeon Silver 4214R @ 2.40GHz；容器 cgroup 限额 **12 核**（cfs 1,200,000 / 100,000 µs）、**90.0 GiB 内存**（96,636,764,160 B）；`/root/autodl-tmp` 50 GB 可用；系统盘 30 GB；Ubuntu 22.04.5 LTS，内核 5.4.0-162；时区 Asia/Shanghai（= SGT）。容器内 `nproc` = 48、`/proc/meminfo` 440 GB 为宿主机值（见发现第 1 条）。工具：`/root/miniconda3`（conda 24.4.0，不在 PATH）、`rsync` 有；`tmux`、`/usr/bin/time`、系统 `python3` 缺（部署脚本不用系统 `python3`）。均高于下限（内存 ≥ 40 GB、核数 ≥ 8、数据盘 ≥ 35 GB） |
| C2 | 上传 | 完成 | 2026-10-19 01:04 | `rsync` 到 `/root/autodl-tmp/s4k_cloud/`：17 个文件、237,200,055 B，56 s（约 4.3 MB/s），第一次即成功；实例上 `sha256sum -c SHA256SUMS` **15 个 OK**，`COMMIT` = 56d283580799c510b617c70b6e3292ba224e4ae0 |
| C3 | 环境 | 完成 | 2026-10-19 01:04–01:53 | `apt-get install tmux time` 完成（tmux 3.2a、GNU time 1.9）；`source /etc/network_turbo` 后 `conda env create -n pypsa-earth -f environment_pypsa-earth.yml`（实例后台 nohup，日志 `/root/autodl-tmp/l23_c3_conda.log`），01:04:30–01:52:43，退出码 0，环境 3.3 GB；下载期间 conda.anaconda.org 有读超时、`pillow` 一个包约 17 KB/s，conda 自动重试后完成。`$PY` = `/root/miniconda3/envs/pypsa-earth/bin/python`；版本与部署包清单**全部一致**：python 3.11.13、pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4、pandas 2.3.1、xarray 2025.1.2、scipy 1.15.2、netCDF4 1.7.2 |
| C4 | 许可 | 完成 | 2026-10-19 01:54 | 本机许可文件经 `scp` 直接传到实例 `/root/.gurobi/gurobi.lic`（目录 700、文件 600、属主 root、308 字节）；两端哈希一致（未显示哈希值）；全程未读取、打印或复制到其他位置 |
| C5 | 预检 | 完成 | 2026-10-19 01:54:31–01:54:38 | `PY=… GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash preflight.sh serial formal_barrier`：SHA256 全部 OK；代码解包到 `./repo`（56d28358）；四个网络在；档案 `formal_barrier`（Method 2、Crossover 0、BarConvTol 1e-8、BarHomogeneous 1、Threads 8、Seed 123、AggFill 0、PreDual 0、BARDENSETHRESH 200）；版本一致；GNU time 有；许可被 Gurobi 接受（输出已屏蔽）；资源 48 / 440 GiB / 49 GiB（容器内为宿主机值，见发现第 1 条）；最后一行 **`PREFLIGHT OK`**。预检占用的 WLS 令牌至少保留 5 分钟：最早 01:59:38 启动 |
| C6 | 启动 | 完成 | **2026-10-19 02:00:30** | 预检结束（01:54:38）后 5 分 52 秒；启动前确认本机无任何求解或 Gurobi 进程。tmux 会话 `s4k`：`bash /root/autodl-tmp/l23_launch.sh`（`cd /root/autodl-tmp/s4k_cloud`；`PY=/root/miniconda3/envs/pypsa-earth/bin/python GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash run_365x24h.sh --solver-profile formal_barrier --mode serial --auth "<授权原文>"`）。授权原文按 `S4K_REPORT.md` §10.4 模板填写：规格 RTX 3080 Ti × 1，12 核 Xeon Silver 4214R，90 GB 内存，数据盘 50 GB；区域 西北 B 区 144 机；运行方式 serial；许可 `/root/.gurobi/gurobi.lic`；授权人 程宇晨；时间 2026-10-19 02:00（SGT）。运行目录 `runs/20261018T180030Z_5623/`；`STATUS.txt` 首行 `START:2026-10-18T18:00:30Z mode:serial runs:integrated,disconnected,integrated_nze solver_profile:formal_barrier commit:56d28358…` |
| C7 | 监督 | 完成 | 02:00:30–09:08:23 | 整批 `DONE` 于 2026-10-19 09:00:38 SGT（运行 7 h 00 min）：一体化 SUBOPTIMAL（6,722 s）、不互联 SUBOPTIMAL（5,297 s）、不互联诊断 SUBOPTIMAL（2,311 s）、NZE 到 Gurobi TimeLimit 后被墙钟上限标记终止（10,814 s，`STATUS` 记为 `none`）。不重试、不干预。原记录：每 12 分钟一次（`/home/jin/l23_watch.sh`，只读）：`STATUS.txt`、`MONITOR_*.csv` 末行、容器 cgroup 内存（`MONITOR` 的 `mem_available_gib` 是宿主机值，见发现第 2 条）与磁盘。预计（§20）：一体化 47–65 min（悲观 95）、不互联 38–52（74）、NZE 66–94（138）、诊断 74–104（153） |
| C8 | 回收 | 完成 | 2026-10-19 09:26–09:34:34 | 下载到 `p1_step4k_20261018/cloud_results/20261018T180030Z_5623/`：`results_20261018T180030Z_5623.tar.gz`（216,618,533 B，SHA256 `39b9c9dd…ae7f`）与 `.sha256`、`STATUS.txt`、4 个 `MONITOR_*.csv`；**本机 `sha256sum -c` OK**；解包 76 个文件、373 MB（`unpacked/export/`）。NZE 未入包的输出（发现第 3 条）：实例上按脚本导出清单与许可行过滤整理为 `nze_late_outputs_20261018T180030Z_5623.tar.gz`（21 个文件、74,285,069 B，SHA256 `78a6ea15…c33b`），下载到 `nze_late/`，**本机 SHA256 OK**，解包 21 个文件、127 MB；其中 `FILE_TIMES_SGT.txt` 为实例上 `integrated_nze/` 的文件时间。**许可特征串扫描（解包结果、`nze_late`、STATUS、MONITOR、`evidence/c9`）：无。** C9 违反分析的 5 个 JSON 与 `C9_STATUS.txt` 下载到 `evidence/c9/`。**09:34:34 删除实例许可文件 `/root/.gurobi/gurobi.lic`，确认已不存在**；删除前确认实例上没有求解或分析进程。实例上其余数据未删除。**开机到 `DONE`：** 容器 PID 1 启动 00:40:26 → `DONE` 09:00:38 = **8 h 20 min（8.34 h），估算 ¥9.00**（¥1.08/时）；到删除许可时 8.90 h、约 ¥9.61；关机前继续计费。**请用户到 AutoDL 控制台关机。** |
| C9 | 首轮分析 | 进行中 | 09:14 起 | 违反分析：实例上对四个运行统一补跑（09:14:40–09:24:55，`nice -n 19`、3 个 CPU、`GRB_LICENSE_FILE` 取消；一体化 3 分 17 秒、不互联 1 分 44 秒、诊断 1 分 56 秒、NZE 3 分 12 秒，峰值 8.6–10.0 GB）；本机汇总脚本 `scripts_project/l23_c9_summary.py`（只读，不求解） |

## 监督记录（C7）

时间为 SGT；内存为容器 cgroup 值（扣除非活动文件缓存）；barrier 列为 Gurobi 日志末行（迭代、原始目标、对偶目标、原始不可行、对偶不可行、互补、用时）。

| 时间 | 运行 / 已用 | 进程树 RSS | 容器内存（已用 / 90 GiB） | 磁盘空闲 | barrier 末行 | 备注 |
|---|---|---|---|---|---|---|
| 02:01:56 | 一体化 / 60 s | 4.2 GiB | 7.3 GiB | 50 GB | — | 建模中 |
| 02:14:01 | 一体化 / 13 min | 14.7 GiB | 18.3 GiB | 49 GB | 12：4.19e12 / −8.0e10 … 520 s | barrier 已开始 |
| 02:26:05 | 一体化 / 25 min | 14.8 GiB | 18.3 GiB | 49 GB | 34：5.2694e11 / 5.1311e11，原始不可行 4.2e5 … 1,229 s | |
| 02:38:09 | 一体化 / 37 min | 14.8 GiB | 18.3 GiB | 49 GB | 54：5.1366e11 / 5.1333e11，9.9e3 … 1,942 s | |
| 02:50:14 | 一体化 / 49 min | 14.8 GiB | 18.3 GiB | 49 GB | 71：5.13270e11 / 5.13263e11，234 … 2,670 s | |
| 03:02:18 | 一体化 / 61 min | 14.8 GiB | 18.3 GiB | 49 GB | 86：5.132612e11 / 5.132600e11，原始不可行 38、对偶不可行 1.7e-4、互补 0.90 … 3,395 s | 已超 §20 中值 47–65 min 的上沿附近，仍在悲观 95 min 以内；约 40 s / 次迭代；内存远低于估计上限 34.9 GiB |
| 03:50:37 | 一体化 / 110 min | 13.2 GiB | 17.7 GiB | 49 GB | **144：5.13259523e11 / 5.13259356e11，原始不可行 5.29、对偶不可行 4.4e-4、互补 0.14 … 6,248 s → Gurobi "Sub-optimal termination"，目标 5.13259583e11** | **一体化非最优（SUBOPTIMAL）**：barrier 第 100 次后原始不可行停在约 5 左右，未达 BarConvTol 1e-8；原始 / 对偶目标相对差约 3e-7。LP 4,349,757 列 / 9,719,326 行。已超悲观 95 min（标注）。s2_solve 正在收尾；脚本按既定逻辑继续不互联、NZE（只观察、不干预，不重跑） |
| 04:00:00 | `STATUS.txt`：`RUN_integrated:suboptimal:6722s`（112 min，含建模、门槛与导出）；`export/integrated/` 已有回执、门槛、账本、CO₂ 流向、求解后网络等 | — | — | — | — | 不互联 STEPS 约 03:52 开始 |
| 04:03:13 | 不互联 / 10 min | 11.9 GiB | 16.4 GiB | 48 GB | 21：1.0483e12 / 9.6636e11，原始不可行 5.0e4 … 370 s | |
| 04:15:39 | 不互联 / 22 min | 11.9 GiB | 16.4 GiB | 48 GB | 76：5.82780e11 / 5.83338e11，59.5 / 2.6e-2 / 236 … 1,092 s | |
| 04:27:45 | 不互联 / 35 min | 11.9 GiB | 16.4 GiB | 48 GB | 120：5.820599e11 / 5.820617e11，原始不可行 0.127、对偶 1.8e-4、互补 0.46 … 1,872 s | 接近收敛 |
| 04:39:48 | 不互联 / 47 min | 11.9 GiB | 16.4 GiB | 48 GB | **178：5.91606e11 / 5.99966e11，原始不可行 1.87e4、对偶 0.37、互补 3.4e3** … 2,596 s | **迭代跳开**（残差回升四个数量级） |
| 04:51:54 | 不互联 / 59 min | 11.9 GiB | 16.4 GiB | 48 GB | 227：5.82072e11 / 5.82095e11，20.9 / 2.6e-3 / 4.8 … 3,315 s | 回落 |
| 05:03:59 | 不互联 / 71 min | 11.9 GiB | 16.4 GiB | 48 GB | 271：5.820596e11 / 5.820613e11，2.02 / 5.1e-2 / 0.38 … 4,034 s | 接近悲观 74 min（标注）；TimeLimit 175 min 内 |
| 05:16:39 | 不互联 / 83 min | 11.9 GiB | 16.4 GiB | 48 GB | 319：5.820592e11 / 5.820604e11，1.66 / 4.2e-3 / 0.27 … 4,763 s | 已超悲观 74 min（标注） |
| 05:28:44 | `STATUS.txt`：**`RUN_disconnected:suboptimal:5297s`**、`DISCONNECTED_MAIN_NON_OPTIMAL:suboptimal -> running disconnected_gap diagnostic` | — | 17.0 GiB | 46 GB | 不互联最后：326：5.820592e11 / 5.820603e11，原始不可行 1.65、对偶 4.3e-3、互补 0.26 … 4,869 s → **"Sub-optimal termination"，目标 5.82059837e11** | **不互联非最优**；脚本按设计自动运行不互联诊断（约 05:21 开始，6 min 时在排序）；之后为 NZE。只观察、不干预 |
| 05:41:31 | 诊断 / 19 min | 11.6 GiB | — | 46 GB | 61：5.82613e11 / 5.82277e11，190 / 8.0e-3 / 172 … 907 s | |
| 05:53:35 | 诊断 / 31 min | 11.6 GiB | — | 46 GB | 101：5.820602e11 / 5.820591e11，0.60 / 8.5e-4 / 0.53 … 1,617 s | |
| 06:05:40 | `STATUS.txt`：**`RUN_disconnected_gap:suboptimal:2311s`**；NZE 约 06:00 开始（5 min 时预求解删去 6,712,157 行、1,288,680 列） | 8.6 GiB | 13.2 GiB | 45 GB | 诊断最后：117：5.820599e11 / 5.820590e11，原始不可行 6.27、对偶 6.2e-3、互补 0.43 … 1,864 s → **"Sub-optimal termination"，目标 5.82060194e11** | **诊断也非最优**；用时 38.5 min，在估计内 |
| 06:18:18 | NZE / 17 min | 14.2 GiB | — | 44 GB | 18：8.6265e11 / 4.3253e11，1.2e7 … 747 s | |
| 06:30:22 | NZE / 30 min | 14.2 GiB | — | 44 GB | 41：4.28383e11 / 4.23848e11，1.2e5 / 6.5e-2 … 1,523 s | |
| 06:42:26 | NZE / 42 min | 14.2 GiB | — | 44 GB | 60：4.229303e11 / 4.228353e11，2.7e3 / 1.7e-3 … 2,253 s | |
| 06:54:30 | NZE / 54 min | 14.2 GiB | — | 44 GB | 74：4.228064e11 / 4.228003e11，194 / 1.9e-4 / 3.2 … 2,938 s | |
| 07:06:35 | NZE / 66 min | 14.2 GiB | 20.7 GiB | 45 GB | 88：4.2279869e11 / 4.2279794e11，原始不可行 20.8、对偶 4.2e-5、互补 0.30 … 3,654 s | 在悲观 138 min 内 |
| 07:19:10 | NZE / 78 min | 14.2 GiB | 20.7 GiB | 45 GB | 103：4.2279836e11 / 4.2279788e11，12.0 / 1.2e-4 / 0.19 … 4,381 s | |
| 07:31:15 | NZE / 90 min | 14.2 GiB | 20.7 GiB | 45 GB | 118：4.2279822e11 / 4.2279785e11，10.5 / 5.7e-5 / 0.14 … 5,107 s | |
| 07:43:19 | NZE / 102 min | 14.2 GiB | 20.7 GiB | 45 GB | 133：4.2279802e11 / 4.2279781e11，6.93 / 1.6e-4 / 0.08 … 5,832 s | 接近收敛 |
| 07:55:24 | NZE / 114 min | 14.2 GiB | 20.7 GiB | 45 GB | **152：1.15576e12 / 7.98533e11，原始不可行 5.9e6、对偶 11.7、互补 3.0e5** … 6,572 s | **迭代跳开**（与不互联第 178 次同类） |
| 08:07:27 | NZE / 127 min | 14.2 GiB | 20.7 GiB | 45 GB | 176：4.45262e11 / 4.36123e11，1.45e5 / 0.31 / 6.7e3 … 7,348 s | 回落中；距 TimeLimit 10,500 s 约 52 min，可能触及（标注） |
| 08:20:04 | NZE / 139 min | 14.2 GiB | 20.7 GiB | 44 GB | 196：4.240836e11 / 4.237529e11，7.8e3 / 2.1e-2 / 375 … 8,057 s | 已超悲观 138 min（标注） |
| 08:32:09 | NZE / 151 min | 14.2 GiB | 26.4 GiB | 44 GB | 212：4.228391e11 / 4.228192e11，250 / 4.5e-4 / 10.8 … 8,761 s | 容器内存多出约 5.6 GiB 为同时进行的早期违反分析（nice 19，3 个 CPU） |
| 08:44:14 | NZE / 163 min | 14.2 GiB | 20.7 GiB | 44 GB | 227：4.2280578e11 / 4.2280118e11，63.0 / 7.2e-5 / 2.0 … 9,486 s | |
| 08:56:19 | NZE / 175 min | 14.2 GiB | 20.7 GiB | 44 GB | 242：4.22798888e11 / 4.22798188e11，18.1 / 1.1e-4 / 0.28 … 10,239 s | 即将到 TimeLimit |
| 09:08:23 | `STATUS.txt`：**`KILLED_3H_integrated_nze:2026-10-19T01:00:23Z`**、`RUN_integrated_nze:none:10814s`、**`DONE:2026-10-19T01:00:38Z`**（结果包 `results_20261018T180030Z_5623.tar.gz`，216,618,533 B） | — | 7.0 GiB | 44 GB | NZE 最后：**247：4.22798768e11 / 4.22798152e11，原始不可行 16.2、对偶 2.45e-5、互补 0.25 … 10,488 s → Gurobi "Time limit reached"（10,500.91 s）** | **NZE 到 Gurobi TimeLimit，随后被 3 h 墙钟上限标记终止**；监督结束（`WATCH_EXIT:DONE`）。墙钟上限的终止没有终止实际求解进程，见发现第 3 条 |

## 续行点

**2026-10-19 09:35 SGT：C8 完成，实例许可文件已删除，实例不再需要（等待用户在 AutoDL 控制台关机）。** 下一步：本机运行 `l23_c9_summary.py` → 写完 `L23_RUN1_REPORT.md` 与 `L23_RUN1_EVIDENCE.json` → 提交、同步 PR #36 → 停止，等待审阅。不再连接实例。

原记录：**正式运行已于 2026-10-19 02:00:30 SGT 在实例 tmux 会话 `s4k` 中启动**，运行目录 `/root/autodl-tmp/s4k_cloud/runs/20261018T180030Z_5623/`。若本会话中断：先读本文件，再查该目录的 `STATUS.txt`（出现 `DONE` 即进入 C8）；只观察、不干预。连接方式：WSL `ssh` + `~/.ssh/id_ed25519`（`/home/jin/l23_ssh.sh`，主机与端口只经调用命令行的环境变量 `L23_HOST`、`L23_PORT` 传入，不写入任何文件）。若正式运行已启动而本会话中断：先读本文件，再查实例上 `runs/<时间戳>/STATUS.txt`。

## 用户中途指示

1. 2026-10-19 约 03:55 SGT（一体化 SUBOPTIMAL 之后），原文："补充首轮分析（C9）的要求，只读结果、不重跑、不改参数：1. 对一体化 STEPS（及其他非最优运行）的解，按约束族与国家列出原始违反最大的行：绝对量、相对该行右端项或相关容量的比例、所在时段；Gurobi 日志最后 20 次迭代的原始 / 对偶残差与互补间隙。2. 判断违反集中在哪些约束族（例如国家 CO₂ 上限、储能能量、节点平衡、线路容量与线性损耗代理、基尔霍夫、气 / 生物质年度上限），并与 S4J 冒烟 SUBOPTIMAL（STOP_01）中的违反模式对比，是否同类。3. 用已导出的解，计算若把这些违反视为数值误差，对目标值、B6 与各国账本的影响量级（只作估计，标注 INFERENCE）。4. 结论写入 L23_RUN1_REPORT.md 单独一节；不提出也不执行任何重跑或参数修改。"
   - 准备：新脚本 `scripts_project/l23_violation_analysis.py`（只读，不调用求解器）：按 `s2_solve.py` 重建同一个线性规划模型（不求解），核对行 / 列编号与导出的 LP 完全一致；用第 71 项的预算（1e-3 + 1e-5 × 参考量，与 `s4b_acceptance` 相同）计算每行原始违反，映射到约束族、国家与时段；按族与国家汇总，并给出一阶影响 Σ|违反| × |对偶|（INFERENCE）；读 Gurobi 日志最后 20 次迭代。
   - 已在本机用 S4J STOP_01 冒烟（56 时段，代码 ad81a01e 的临时 worktree）验证：编号一致（1,518,053 行）；超预算 44 行、最大违反 10.94、最大比 7.02、按族分布与该次 `V5_GATES.json` 完全相同。结果存 `evidence/c9/VIOLATIONS_S4J_STOP01_SMOKE_integrated.json`（作为对比）。
   - 正式运行的分析放在实例上、整批 `DONE` 之后执行（重建 365 时段模型约需 15 GB 内存，本机 WSL 只有 10 GB；不在运行期间占用实例资源），在删除许可与提醒关机之前完成。
2. 2026-10-19 约 08:20 SGT，原文："NZE 不干预，按脚本既定处理（收敛、或在 TimeLimit / 墙钟上限结束）。等待期间，授权现在就对已结束的一体化 STEPS 与不互联 STEPS 先做只读违反分析：- 用 nice -n 19 后台运行，最多占 2–3 个核，不调用求解器、不占 Gurobi 许可，不触碰 NZE 的进程与文件；- 内容按我上一条补充的 C9 要求（按约束族与国家列出最大违反、相对量级、所在时段，最后 20 次迭代的残差，与 S4J STOP_01 的模式对比，对目标值、B6 与各国账本的影响量级估计）；- 同时说明不互联运行的终止状态，以及它是否也出现了"跳开"。NZE 结束、整批 DONE 后，再按原计划补做 NZE 的分析、回收结果、删除许可并提醒我关机。"
   - 执行：`/root/autodl-tmp/l23_tools/l23_c9_early.sh`，08:27:29 SGT 起，nohup 后台；每个分析进程 `nice -n 19`、`taskset -c 45-47`（3 个 CPU）、数值库线程 2；`GRB_LICENSE_FILE` 取消（已核对 linopy 只在求解函数中创建 Gurobi 环境，分析不求解）；只读 `integrated/`、`disconnected/` 与网络文件，只写 `l23_tools/`。启动后核对：进程 NI = 19、亲和性 45–47；NZE 正常推进（08:29 第 210 次迭代）。
   - 结果：08:27:29–08:32:26 SGT 完成（一体化 3 分 10 秒、峰值 10.0 GB；不互联 1 分 46 秒、8.6 GB）；行编号与导出 LP 完全一致（9,719,326、9,373,129）。一体化超预算 11,730 行（最大为预算 902 倍，SG 生物质池年末水平 −0.91 MWh），不互联 360 行（23.6 倍）；集中在储能水平上下限、近零容量 `FT` 链路上下限与 H₂ 母线节点平衡，与 S4J STOP_01 同类；国家 CO₂ 上限、交流线与线性损耗代理无超预算。一阶影响 1.9e5 / 1.4e4 EUR（相对目标 ≤ 4e-7），对 B6（68.97 bn EUR）与各国账本可忽略（INFERENCE）；对偶侧残差对按电价结算的账本分解未量化。不互联终止状态 SUBOPTIMAL，**有跳开**（第 125 次迭代，原始残差由 0.121 跳到 1.62e11，之后回落到 1.65）；一体化为停滞、无跳开。写入 `L23_RUN1_REPORT.md` §6（初稿），证据 `evidence/c9/`（`VIOLATIONS_integrated.json`、`VIOLATIONS_disconnected.json`、`BARRIER_TRAJECTORIES.json`、`BARRIER_ITERATIONS_*.txt`、`early/` 三个运行的回执、门槛、账本）。分析脚本加了按违反量与一阶影响排序的最大行，整批 `DONE` 后对四个运行统一重跑。

## 发现但未处理

1. `preflight.sh` 用 `nproc` 与 `/proc/meminfo` 判断 CPU 与内存；AutoDL 容器内这两个值是宿主机的（48 线程、440 GB），不是容器配额（12 核、90 GiB）。本实例配额本身高于下限，所以不影响本次；若将来实例配额低于下限，预检仍会通过。建议时点：下一次修改部署脚本时改为读 cgroup 限额（未修改）。
2. `run_365x24h.sh` 的 `MONITOR_<运行>.csv` 中 `mem_available_gib` 取自 `/proc/meminfo`，在容器内是宿主机值（约 420 GB），不反映 90 GiB 配额。监督时另读 cgroup `memory.usage_in_bytes` / `memory.limit_in_bytes` 判断可用内存。建议时点同第 1 条（未修改）。
3. **3 h 墙钟上限没有终止实际求解进程，NZE 的完整输出不在结果包内。** VERIFIED（实例文件时间，SGT）：NZE 约 06:00:13 开始；Gurobi 在 10,500.91 s 到 TimeLimit（"Time limit reached"，第 247 次迭代）；脚本在 09:00:23 写 `KILLED_3H_integrated_nze`，随即读回执（此时回执还是求解前版本，无 `termination_condition`，故 `STATUS` 记 `none`），09:00:23 导出 `export/integrated_nze/`（只有求解前回执 51,405 B、日志尾、MONITOR 等 8 个文件，`solve_time.txt` 为空），09:00:37 打包、09:00:38 写 `DONE`。但 `s2_solve.py` 进程未被终止，继续写出：`solve.err` 09:00:52（linopy "Termination condition: time_limit"）、`solution/X.npy`、`Pi.npy`、`RC.npy` 09:01:54、求解后网络 09:02:22、`V5_GATES.json` 与最终 `SOLVE_RECEIPT.json`（102,713 B，`termination_condition` = `time_limit`，目标 425,684,740,304.79）09:03:01、`solve.log` 末行 09:03:02。`/usr/bin/time` 的资源摘要没有写出（`solve.err` 停在 09:00:52），说明被终止的是 `time` 一层。INFERENCE：`solve()` 中 `pkill -P $pid` 只作用于 `$pid` 的直接子进程（子 shell → `/usr/bin/time`），作为孙进程的 Python 被重新挂到 init 下继续运行。影响：①墙钟上限实际超出约 2 分 40 秒（后处理，未再调用 Gurobi 优化）；②结果包中 NZE 只有求解前回执，没有门槛、账本、求解后网络。NZE 的这些文件仍在实例运行目录 `integrated_nze/` 中，按脚本导出清单另行打包下载（C8，标注"未进入结果包"）。未修改脚本；建议时点：下一次修改部署脚本时改为按进程组终止（PROPOSED）。
