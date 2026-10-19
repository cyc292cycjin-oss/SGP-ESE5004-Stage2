# S4M 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4M_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-19 12:20 SGT），开始前核对 SHA256 = `e791015e2135845746e0ef47a50e15fae1d45d0cc586c723cc5c8197cc4c567c`，与 `S4M_INSTRUCTION_SHA256.txt` 一致（2026-10-19 12:25 SGT，VERIFIED）。所有过程说明一律用中文。

- **分支：** `codex/s4m-mainline-pilot-20261019`，自 PR #37（S4L）最新提交 4b4eb92c 开出（已核实 = 远端 `codex/s4l-numerics-20261019` 头 `4b4eb92cfe99dfd7717a7ef1f3c1c7e2b4712ad6`）；draft PR 叠在 #37 上。
- **仓库：** `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4m_20261019/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4m_20261019\`。
- **授权（用户 2026-10-19 12:12 SGT）：** 第 114、115、116 项；本机 56×3h 冒烟 ×3（档案 A，各 30 分钟止损，不重试）；满足 S4M-4 资源条件时的本机 365×24h 一体化试点（单次、档案 A、TimeLimit 14,400 s、墙钟 15,300 s）。**云端连接与任何云端运行均未授权。**
- **规则：** 档案 A 不改；非最优不重试、不改参数、不 warm start；不改历史结果与 SHA 定点；不合并 main、不 force-push；许可只经 `GRB_LICENSE_FILE` 只读引用；WLS 最多 2 个会话，运行期间不另开 Gurobi。
- **停止条件：** 静态复核发现新错误；冒烟非最优或门槛不通过；部署包网络与冒烟网络不一致；本机资源不满足 S4M-4 条件（不执行试点，正常写报告）；试点中 MemAvailable < 3 GiB（终止并报告）。

## S4M-4 第 1 点：本机资源核对（只读，2026-10-19 12:27 SGT，VERIFIED）

| 项目 | 值 | 来源 |
|---|---|---|
| WSL `MemTotal` | 11,214,484 kB = **10.7 GiB** | `/proc/meminfo` |
| WSL `MemAvailable` | 10,419,128 kB = 9.9 GiB | 同上 |
| WSL `SwapTotal` | 4 GiB | 同上 |
| WSL `nproc` | 16 | |
| 磁盘 | `/`（ext4，仓库所在）900 GB 可用；`D:` 340 GB 可用 | `df` |
| `.wslconfig`（`C:\Users\20122\.wslconfig`） | `[wsl2] memory=11GB, swap=4GB, swapFile=D:\WSLDistros\wsl-swap\swap.vhdx` | 文件内容 |
| Windows 物理内存 | 16,890,519,552 B = **15.7 GiB**（当时空闲 7.2 GB） | `Get-CimInstance Win32_ComputerSystem` / `Win32_OperatingSystem` |

**判定：** 条件要求 WSL `MemTotal` ≥ 24 GiB 且 `MemAvailable` ≥ 20 GiB、磁盘 ≥ 20 GB。实际 `MemTotal` 10.7 GiB（`.wslconfig` 上限 11 GB，而本机物理内存总共只有 15.7 GiB，即使改 `.wslconfig` 也达不到 24 GiB）。**不满足 → 本机试点不执行**，试点改在云端（另行授权）。未修改 `.wslconfig`，未重启 WSL。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4M-0 | 登记第 114–116 项 | 进行中 | | 注册表片段 `s4m_0` |
| S4M-1 | 主算设置（`dust_cleanup: on`、`biomass_overflow_cap_share: 0.98`）与四个网络构建、S4I 复核、比值与余量核对 | 待开始 | | |
| S4M-2 | 本机冒烟 ×3（56×3h，档案 A） | 待开始 | | |
| S4M-3 | 部署包重建（S4L 版脚本）、TimeLimit / 墙钟参数化（14,400 / 15,300）、`speed_probe.sh`、敏感性清单 +2、资源估算与部署步骤更新 | 待开始 | | |
| S4M-4 | 本机资源核对与条件性试点 | 核对完成；**试点不执行（条件不满足）** | | 见上表 |
| S4M-5 | 报告与证据 | 待开始 | | |

## 提交记录（分支 `codex/s4m-mainline-pilot-20261019`）

| 提交 | 内容 |
|---|---|

## 续行点

S4M-0 进行中：写注册表片段 `s4m_0`、改配置 0.98、提交；然后链式执行构建 → S4I 复核 → 冒烟 ×3 → 汇总（`/home/jin/s4m_chain.sh`，`results_project/s4m/`）。

## 发现但未处理（执行中随时记录，交付时写入报告）

（暂无）

## 用户中途指示

（暂无）
