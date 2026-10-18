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
| C3 | 环境 | 进行中 | 2026-10-19 01:04 起 | `apt-get install tmux time` 完成（tmux 3.2a、GNU time 1.9，`/usr/bin/time` 已有）；`source /etc/network_turbo` 后 `conda env create -n pypsa-earth -f environment_pypsa-earth.yml` 在实例后台运行（nohup，日志 `/root/autodl-tmp/l23_c3_conda.log`） |
| C4 | 许可 | 待做 | — | |
| C5 | 预检 | 待做 | — | |
| C6 | 启动 | 待做 | — | |
| C7 | 监督 | 待做 | — | |
| C8 | 回收 | 待做 | — | |
| C9 | 首轮分析 | 待做 | — | |

## 监督记录（C7）

（尚未开始）

## 续行点

C1 完成，进行 C2 上传。连接方式：WSL `ssh` + `~/.ssh/id_ed25519`（`/home/jin/l23_ssh.sh`，主机与端口只经调用命令行的环境变量 `L23_HOST`、`L23_PORT` 传入，不写入任何文件）。若正式运行已启动而本会话中断：先读本文件，再查实例上 `runs/<时间戳>/STATUS.txt`。

## 发现但未处理

1. `preflight.sh` 用 `nproc` 与 `/proc/meminfo` 判断 CPU 与内存；AutoDL 容器内这两个值是宿主机的（48 线程、440 GB），不是容器配额（12 核、90 GiB）。本实例配额本身高于下限，所以不影响本次；若将来实例配额低于下限，预检仍会通过。建议时点：下一次修改部署脚本时改为读 cgroup 限额（未修改）。
