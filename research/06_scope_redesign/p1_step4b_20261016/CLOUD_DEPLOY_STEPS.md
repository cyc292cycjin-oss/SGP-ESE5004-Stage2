# 云端部署步骤（AutoDL，365×24h 首次正式日分辨率试算，S4B 主算设置）

本文件只说明操作步骤。Claude Code 不连接云端，也不启动任何正式求解；每一步由用户在 AutoDL 上执行。**正式运行前须由用户单独明确授权**（CLAUDE.md：每次优化都需要用户单独明确授权；不自动重试、不做参数网格、不 warm start）。资源需求见 `CLOUD_RESOURCE_ESTIMATE.md` §11，部署包脚本与清单见 `cloud_package/`，打包产物在本机 `work/p1_step4b_20261016/cloud_package_dist/`（含网络与代码快照，不进 git）。

与 S3 版（`p1_step3_20261015/CLOUD_DEPLOY_STEPS.md`）的区别：代码快照与网络更新到 S4B 最终提交（第 70–79 项、`calibrated_modern` 出力曲线、3 级资源分级、台风开关关闭）；新增第三个运行——**不互联诊断**（gap_diagnostic，电力/CO₂/生物质/气松弛，第 73 项）；并行方式改为两条通道；新增数据与配置清单 `DATA_CONFIG_MANIFEST.json`。

## 0. 部署包内容（`cloud_package_dist/`）

| 文件 | 说明 |
|---|---|
| `code_<commit8>.tar.gz` | 仓库在部署提交时的完整快照（`git archive`），提交哈希见 `COMMIT`；含 `configs/` 与 `research_inputs/`（其中 `research_inputs/renewable_v5/profiles_calibrated_modern_c3_3h.nc` 等出力曲线由 raw11 cutout 生成；cutout 本身不在包内） |
| `networks/integrated_365_24h_unsolved.nc` | 一体化主算网络（S4B-5 同批构建，构建回执 `integrated_BUILD_RECEIPT.json`） |
| `networks/disconnected_365_24h_unsolved.nc` | 不互联主算网络（预期因 CO₂ 结构缺口而不可行） |
| `networks/disconnected_gap_diagnostic_365_24h_unsolved.nc` | 不互联诊断网络（gap_diagnostic，四类松弛，罚价 10,000 EUR/MWh 或 EUR/t） |
| `environment_pypsa-earth.yml`、`conda_explicit_linux64.txt` | 本机 conda 环境导出（Python 3.11.13、pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4） |
| `preflight.sh` | 云端预检：校验 SHA256、解包代码、核对版本、检查许可可用（不显示许可内容）、核对 CPU/内存/磁盘 |
| `run_365x24h.sh` | 正式试算脚本：三个运行（一体化主算、不互联主算、不互联诊断），串行或并行两条通道，每运行 8 线程、墙钟上限 3 h、每分钟记录内存与进度、结束后自动导出回执与门槛结果（日志已剔除许可行） |
| `DATA_CONFIG_MANIFEST.json` | 数据与配置清单：`configs/`、`research_inputs/` 每个文件的 SHA256 与字节数；出力曲线文件与其来源 cutout 的身份（路径、大小、SHA256、DOI）；三个网络的构建输入与回执摘要 |
| `SHA256SUMS`、`PACKAGE_MANIFEST.json`、`COMMIT` | 校验与清单（`PACKAGE_MANIFEST.json` 给出上传总字节数） |

**不包含 Gurobi 许可文件**；许可由用户在云端自行放置，并通过 `GRB_LICENSE_FILE` 引用。

## 1. 选择与创建实例

1. 登录 AutoDL 控制台 →「算力市场」。本任务只用 CPU 和内存（LP barrier 不用 GPU），但 AutoDL 按 GPU 机型出售，CPU 核数与内存随 GPU 数量配给。选择时以**内存与 CPU 核数**为准（数值见 `CLOUD_RESOURCE_ESTIMATE.md` §11）：
   - 串行（一体化 → 不互联主算 → 不互联诊断）：内存下限 32 GB、**推荐 ≥ 48 GB**，CPU ≥ 8 核；预计 2.3–3.3 h；
   - 并行（两条通道同时：一体化 ‖ 不互联主算 → 不互联诊断，各 8 线程）：内存下限 64 GB、**推荐 ≥ 96 GB**，CPU ≥ 16 核；预计 1.7–2.6 h。
   - 预检低于下限即失败，低于推荐值只给警告（单运行峰值上限估计 30 GiB，两条通道 59 GiB）。
   - 「无卡模式」只配很少的 CPU 与内存，**只用于上传、装环境和下载结果，不能用于求解**。
2. 镜像选 **Miniconda / Ubuntu 22.04**（基础镜像即可，不需要 PyTorch）。
3. 数据盘：在实例的数据盘 `/root/autodl-tmp` 下操作，可用空间 ≥ 30 GB（串行）/ ≥ 40 GB（并行）。每个运行的输出约 1.5 GB（LP 导出、V5、求解网络、日志），另加部署包与 conda 环境；系统盘不放大文件。
4. 记下实例的 SSH 登录命令与密码（控制台「登录指令」），后续用 SSH 或 JupyterLab 终端操作。

## 2. 上传部署包

1. 本机：把 `work/p1_step4b_20261016/cloud_package_dist/` 整个文件夹打成一个压缩包（或直接上传文件夹）。上传总大小见 `PACKAGE_MANIFEST.json` 的 `upload_total_bytes_excluding_this_manifest`（S4B 报告 §6 列出）。
2. 上传到实例的 `/root/autodl-tmp/s4b_cloud/`，任选一种方式：
   - JupyterLab 左侧文件栏拖拽上传（适合单个文件 < 数百 MB）；
   - `scp -P <端口> -r cloud_package_dist root@<地址>:/root/autodl-tmp/s4b_cloud`（端口、地址取自「登录指令」）；
   - AutoDL「文件存储 / 网盘」中转（大文件时更稳）。
3. 实例上核对：`cd /root/autodl-tmp/s4b_cloud && sha256sum -c SHA256SUMS`，应全部显示 OK。

## 3. 安装环境

```bash
cd /root/autodl-tmp/s4b_cloud
conda env create -n pypsa-earth -f environment_pypsa-earth.yml
```

- 若 conda 源下载慢，可先执行 AutoDL 的学术加速 `source /etc/network_turbo`（仅在当前终端有效），或改用国内镜像；`gurobi` 包来自 `gurobi` 频道，若镜像缺失该频道，可单独执行 `pip install gurobipy==12.0.3`。
- 完全复现本机构建可用显式清单：`conda create -n pypsa-earth --file conda_explicit_linux64.txt`。
- 安装后记下 Python 路径：`conda run -n pypsa-earth which python`（下文记为 `$PY`）。

## 4. 放置许可

1. 用户把自己的 Gurobi WLS 许可文件上传到实例上一个只有自己可读的位置，例如 `/root/.gurobi/gurobi.lic`，并执行 `chmod 600 /root/.gurobi/gurobi.lic`。
2. 不要把许可文件放进部署包目录或结果目录，不要 `cat` 或截图其内容。
3. WLS 许可需要实例能访问 Gurobi 令牌服务器（HTTPS 出站）。若 AutoDL 所在区域限制外网，许可检查会失败，此时换区域或联系平台开通。
4. 设置环境变量（每个新终端都要设置，或写入 `~/.bashrc`）：`export GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic`。

## 5. 预检（不求解）

```bash
cd /root/autodl-tmp/s4b_cloud
PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash preflight.sh serial
```

预检依次做：SHA256 校验 → 解包代码到 `./repo` → 核对关键包版本 → 用 `gurobipy.Model()` 检查许可（输出被屏蔽）→ 核对 CPU、内存、磁盘 → 核对三个网络文件存在。最后一行应为 `PREFLIGHT OK`；任一项失败时脚本退出，先排除再继续。并行运行时把 `serial` 换成 `parallel`。

可先空跑一次，只打印将执行的命令、不求解：`PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash run_365x24h.sh --mode serial --dry-run`。

## 6. 启动正式试算（需用户授权后）

用 `tmux`（或 `screen`）启动，避免 SSH 断开导致进程退出：

```bash
tmux new -s s4b
cd /root/autodl-tmp/s4b_cloud
PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash run_365x24h.sh --mode serial --auth "<用户授权原文与时间>"
# 按 Ctrl-b 再按 d 脱离会话；重新进入：tmux attach -t s4b
```

- `--mode serial`：一体化 → 不互联主算 → 不互联诊断；`--mode parallel`：两条通道同时运行——通道 1 一体化，通道 2 不互联主算 → 不互联诊断（需 §1 的并行配置）。
- `--runs`：只运行其中几项，例如用户决定不跑预期不可行的不互联主算时用 `--runs integrated,disconnected_gap`。默认三项全跑。
- 运行规则（脚本已固定，不要修改）：主算 `origin_neutral` + `calibrated_modern` + 3 级资源分级 + `formal_barrier`（Method 2、Crossover 0、BarConvTol 1e-8、BarHomogeneous 1、Threads 8、Seed 123）+ 缩放；每运行 Gurobi TimeLimit 10,500 s，墙钟 3 h 强制停止；**不重试、不改参数、不 warm start**。
- **不互联主算预期非最优**（INFEASIBLE、INF_OR_UNBD 或 NUMERIC，第 49、53、73 项）：脚本记录 `DISCONNECTED_MAIN_EXPECTED_NON_OPTIMAL:<状态>`，照常继续不互联诊断。
- 一体化主算或不互联诊断返回非最优（NUMERIC、SUBOPTIMAL、TIME_LIMIT 等）时，脚本只记录状态并导出日志末尾（已剔除许可行），不会自动重跑；由用户把结果带回后决定下一步。

## 7. 监控

- 总体状态：`cat runs/<时间戳>/STATUS.txt`（`RUN_<运行>:<终止状态>:<秒>`、`KILLED_3H_*`、`DISCONNECTED_MAIN_EXPECTED_NON_OPTIMAL:*`、`DONE`）。
- 每分钟记录：`tail -f runs/<时间戳>/MONITOR_integrated.csv`（另有 `MONITOR_disconnected.csv`、`MONITOR_disconnected_gap.csv`；UTC、已用秒数、进程树 RSS GiB、可用内存 GiB、剩余磁盘 GiB、Gurobi 日志最后一行，已剔除许可行）。
- 系统层面：`htop`（CPU 与内存）、`df -h /root/autodl-tmp`（磁盘）。可用内存降到 2 GiB 以下有 OOM 风险；此时只记录、不调参，结束后带回报告。

## 8. 回收结果

1. 脚本结束时生成 `runs/<时间戳>/results_<时间戳>.tar.gz` 及其 `.sha256`，内容为 `export/<运行>/`：`SOLVE_RECEIPT.json`、`V5_GATES.json`（含第 71 项求解器容差口径的 `*_S4B` 门槛与 `all_passed_solver_tolerances`、旧口径 `all_passed_barconvtol`）、`INTERIOR_CHECKS.json`、`kkt_summary.json`、`GAP_TABLE.json`（诊断）、`CO2_FLOWS.json`、`EMISSIONS_BY_COUNTRY.json`、`CAPACITY_BY_TECH_COUNTRY.json`、`cross_border_flows.csv`、`GUROBI_LOG_SCRUBBED.txt` 与 `solve_log_scrubbed.txt`（均已剔除许可行；S3 版脚本直接复制含许可横幅的 `solve.log`，会因许可串检查而拒绝打包，本版已改）、`RESOURCE.jsonl`、`MONITOR_<运行>.csv`、`solve_time.txt`、`MATH_PROBLEM.json`、求解后网络 `*_solved.nc`；非最优时另有 `LOG_TAIL_NONOPTIMAL.txt`、`STDERR_TAIL_NONOPTIMAL.txt`。打包前脚本会检查许可特征串，发现即不打包。
2. 原始 Gurobi 日志（`gurobi.linopy.log`，含许可行）和 LP 数组（`lp/`）留在实例上，不下载；若需要，由用户自行确认后单独处理。
3. 下载：JupyterLab 右键下载，或 `scp -P <端口> root@<地址>:/root/autodl-tmp/s4b_cloud/runs/<时间戳>/results_<时间戳>.tar.gz .`；本机用 `.sha256` 核对后放到 `work/p1_step4b_20261016/cloud_results/`（或下一步指定的新目录），交给 Claude Code 写入回执与报告（新结果放新目录，不覆盖旧结果）。

## 9. 关机与清理

1. 确认结果已下载并校验无误后，在 AutoDL 控制台**立即关机**（按量计费在关机后停止；数据盘内容按平台规则保留一段时间）。
2. 若不再需要实例：先删除实例上的许可文件（`rm /root/.gurobi/gurobi.lic`），再释放实例。
3. 在本机记录：实例规格、区域、开机与关机时间、实际费用，供后续 2920×3h 估算使用。
