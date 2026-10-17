# 云端部署步骤（AutoDL，365×24h 日分辨率运行，S4C 主算设置）

本文件只说明操作步骤。Claude Code 不连接云端，也不启动任何正式求解；每一步由用户在 AutoDL 上执行。**正式运行前须由用户单独明确授权**（CLAUDE.md：每次优化都需要用户单独明确授权；不自动重试、不做参数网格、不 warm start）。资源需求见 `CLOUD_RESOURCE_ESTIMATE.md` §12，部署包脚本在 `cloud_package/`，打包产物在本机 `work/p1_step4c_20261016/cloud_package_dist/`（含网络与代码快照，不进 git）。

与 S4B 版（`p1_step4b_20261016/CLOUD_DEPLOY_STEPS.md`）的区别：

- 代码快照与网络更新到 S4C 最终提交（S4C-0 至 S4C-5：WEO 2025 STEPS 燃料价格、风光候选成本层与海上风并网成本、走廊海底份额、水电入流 `national_observed`、燃料舱 `asean_pool` 与单独净零的燃料舱账户、东盟外 CO₂ 封存、基尔霍夫行归一化）；
- 三个运行：**一体化主算（STEPS）**、**不互联主算（STEPS + 东盟外 CO₂ 封存）**、**一体化 NZE 敏感性**；不互联诊断网络也打包，**只在不互联主算非最优时自动运行**；
- **`--solver-profile` 必填、无默认值**：由用户确认 S4C-5 的推荐后填写；未填时脚本拒绝启动；
- 运行方式三种：串行、两通道、三通道并行；
- 导出新增 `BUNKER_ACCOUNT.json`（燃料舱账户与 B1_BUNKERS 门槛）与 `CO2_FLOWS.json` 中的东盟外封存用量。

## 0. 部署包内容（`cloud_package_dist/`）

| 文件 | 说明 |
|---|---|
| `code_<commit8>.tar.gz` | 仓库在部署提交时的完整快照（`git archive`），提交哈希见 `COMMIT`；含 `configs/` 与 `research_inputs/`（出力曲线由 raw11 cutout 生成；cutout 本身不在包内） |
| `networks/integrated_365_24h_unsolved.nc` | 一体化主算（STEPS）网络，构建回执 `integrated_BUILD_RECEIPT.json` |
| `networks/disconnected_365_24h_unsolved.nc` | 不互联主算网络（STEPS，东盟外 CO₂ 封存开启） |
| `networks/integrated_nze_365_24h_unsolved.nc` | 一体化 NZE 敏感性网络（构建覆盖 `fuels.price_scenario=nze`，回执 `integrated_nze_BUILD_RECEIPT.json`） |
| `networks/disconnected_gap_diagnostic_365_24h_unsolved.nc` | 不互联诊断网络（gap_diagnostic，电力/CO₂/生物质/气松弛）；只在不互联主算非最优时运行 |
| `environment_pypsa-earth.yml`、`conda_explicit_linux64.txt` | 本机 conda 环境导出（Python 3.11.13、pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4） |
| `preflight.sh` | 云端预检：校验 SHA256、解包代码、核对版本、检查许可可用（不显示许可内容）、核对 CPU/内存/磁盘、可选核对求解档案名 |
| `run_365x24h.sh` | 运行脚本：三个运行（+ 条件诊断），串行 / 两通道 / 三通道，每运行 8 线程、墙钟上限 3 h、每分钟记录内存与进度、结束后自动导出回执与门槛结果（日志已剔除许可行） |
| `DATA_CONFIG_MANIFEST.json` | 数据与配置清单：`configs/`、`research_inputs/` 每个文件的 SHA256 与字节数；出力曲线与来源 cutout 的身份；四个网络的构建输入与回执摘要 |
| `SHA256SUMS`、`PACKAGE_MANIFEST.json`、`COMMIT` | 校验与清单（`PACKAGE_MANIFEST.json` 给出上传总字节数） |

**不包含 Gurobi 许可文件**；许可由用户在云端自行放置，并通过 `GRB_LICENSE_FILE` 引用。

## 1. 选择与创建实例

1. 登录 AutoDL 控制台 →「算力市场」。本任务只用 CPU 和内存（LP barrier 不用 GPU），AutoDL 按 GPU 机型出售，CPU 核数与内存随 GPU 数量配给。按**内存与 CPU 核数**选择（数值见 `CLOUD_RESOURCE_ESTIMATE.md` §12）：
   - 串行（一体化 → 不互联主算（→ 诊断）→ 一体化 NZE）：内存下限 32 GB、推荐 ≥ 48 GB，CPU ≥ 8 核；
   - 两通道（[一体化 → NZE] ‖ [不互联主算（→ 诊断）]）：内存下限 64 GB、推荐 ≥ 96 GB，CPU ≥ 16 核；
   - 三通道（一体化 ‖ 不互联主算（→ 诊断）‖ NZE）：内存下限 96 GB、推荐 ≥ 128 GB，CPU ≥ 24 核。
   - 预检低于下限即失败，低于推荐值只给警告。「无卡模式」只配很少的 CPU 与内存，**只用于上传、装环境和下载结果，不能用于求解**。
2. 镜像选 **Miniconda / Ubuntu 22.04**（基础镜像即可）。
3. 数据盘 `/root/autodl-tmp`：可用空间串行 ≥ 35 GB、两通道 ≥ 45 GB、三通道 ≥ 50 GB（每个运行输出约 1.5 GB，另加部署包与 conda 环境）。
4. 记下实例的 SSH 登录命令与密码（控制台「登录指令」）。

## 2. 上传部署包

1. 本机：把 `work/p1_step4c_20261016/cloud_package_dist/` 整个文件夹打包或直接上传；上传总大小见 `PACKAGE_MANIFEST.json` 的 `upload_total_bytes_excluding_this_manifest`（S4C 报告 §7 列出）。
2. 上传到实例的 `/root/autodl-tmp/s4c_cloud/`：JupyterLab 拖拽、`scp -P <端口> -r cloud_package_dist root@<地址>:/root/autodl-tmp/s4c_cloud` 或 AutoDL 网盘中转。
3. 实例上核对：`cd /root/autodl-tmp/s4c_cloud && sha256sum -c SHA256SUMS`，应全部 OK。

## 3. 安装环境

```bash
cd /root/autodl-tmp/s4c_cloud
conda env create -n pypsa-earth -f environment_pypsa-earth.yml
```

- 下载慢时可先执行 `source /etc/network_turbo`（AutoDL 学术加速，仅当前终端有效）或改用国内镜像；`gurobi` 包若镜像缺失可单独 `pip install gurobipy==12.0.3`。完全复现：`conda create -n pypsa-earth --file conda_explicit_linux64.txt`。
- 记下 Python 路径：`conda run -n pypsa-earth which python`（下文记为 `$PY`）。

## 4. 放置许可

1. 用户把自己的 Gurobi WLS 许可文件上传到只有自己可读的位置，例如 `/root/.gurobi/gurobi.lic`，并 `chmod 600`。
2. 不要把许可文件放进部署包目录或结果目录，不要 `cat` 或截图其内容。
3. WLS 许可需要实例能访问 Gurobi 令牌服务器（HTTPS 出站）；若区域限制外网，许可检查会失败，换区域或联系平台。
4. `export GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic`（每个新终端都要设置，或写入 `~/.bashrc`）。

## 5. 预检（不求解）

```bash
cd /root/autodl-tmp/s4c_cloud
PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash preflight.sh serial <用户确认的求解档案>
```

依次：SHA256 校验 → 解包代码到 `./repo` → 四个网络文件 → 求解档案名是否存在于打包的配置 → 关键包版本 → 许可可用（输出屏蔽）→ CPU、内存、磁盘。最后一行应为 `PREFLIGHT OK`。两通道 / 三通道时把 `serial` 换成 `lanes2` / `lanes3`。

可先空跑：`PY=$PY GRB_LICENSE_FILE=... bash run_365x24h.sh --solver-profile <档案> --mode serial --dry-run`（只打印将执行的命令；不给 `--solver-profile` 时脚本拒绝启动，这是预期行为）。

## 6. 启动运行（需用户授权后）

```bash
tmux new -s s4c
cd /root/autodl-tmp/s4c_cloud
PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash run_365x24h.sh --solver-profile <用户确认的档案> --mode serial --auth "<用户授权原文与时间>"
# Ctrl-b 再按 d 脱离；重新进入：tmux attach -t s4c
```

- `--solver-profile`：`formal_barrier` | `crossover_diagnostic` | `barrier_numericfocus2`（S4C 报告 §6 给出推荐；由用户选定）。
- `--mode`：`serial` | `lanes2` | `lanes3`（见 §1）。`--runs` 可只跑其中几项，例如 `--runs integrated,disconnected`；名单中写 `disconnected_gap` 时诊断无条件运行。
- 运行规则（脚本已固定，不要修改）：每运行 Gurobi TimeLimit 10,500 s，墙钟 3 h 强制停止；**不重试、不改参数、不 warm start**；缩放与基尔霍夫行归一化按打包配置开启。
- **不互联主算预期可行**（东盟外 CO₂ 封存开启）。若它返回非最优，脚本记录 `DISCONNECTED_MAIN_NON_OPTIMAL:<状态>` 并自动运行不互联诊断以定位缺口。
- 任一运行非最优（NUMERIC、SUBOPTIMAL、TIME_LIMIT 等）时只记录状态并导出日志末尾（已剔除许可行），不会自动重跑；由用户把结果带回后决定下一步。

## 7. 监控

- 总体状态：`cat runs/<时间戳>/STATUS.txt`（`START … solver_profile:<档案>`、`RUN_<运行>:<终止状态>:<秒>`、`KILLED_3H_*`、`DISCONNECTED_MAIN_NON_OPTIMAL:*`、`DONE`）。
- 每分钟记录：`tail -f runs/<时间戳>/MONITOR_<运行>.csv`（UTC、已用秒数、进程树 RSS GiB、可用内存 GiB、剩余磁盘 GiB、Gurobi 日志最后一行，已剔除许可行）。
- 系统层面：`htop`、`df -h /root/autodl-tmp`。可用内存降到 2 GiB 以下有 OOM 风险；只记录、不调参，结束后带回报告。

## 8. 回收结果

1. 脚本结束时生成 `runs/<时间戳>/results_<时间戳>.tar.gz` 及 `.sha256`，内容为 `export/<运行>/`：`SOLVE_RECEIPT.json`、`V5_GATES.json`（含 `B1_BUNKERS`、第 71 项求解器容差口径的 `*_S4B` 门槛与 `all_passed_solver_tolerances`、旧口径 `all_passed_barconvtol`）、`INTERIOR_CHECKS.json`、`BUNKER_ACCOUNT.json`、`kkt_summary.json`、`GAP_TABLE.json`（诊断）、`CO2_FLOWS.json`（含 `extra_asean_by_country`）、`EMISSIONS_BY_COUNTRY.json`、`CAPACITY_BY_TECH_COUNTRY.json`、`cross_border_flows.csv`、`GUROBI_LOG_SCRUBBED.txt` 与 `solve_log_scrubbed.txt`（均已剔除许可行）、`RESOURCE.jsonl`、`MONITOR_<运行>.csv`、`solve_time.txt`、`MATH_PROBLEM.json`、求解后网络 `*_solved.nc`；非最优时另有 `LOG_TAIL_NONOPTIMAL.txt`、`STDERR_TAIL_NONOPTIMAL.txt`。打包前检查许可特征串，发现即不打包。
2. 原始 Gurobi 日志与 LP 数组（`lp/`）留在实例上，不下载。
3. 下载后在本机用 `.sha256` 核对，放到 `work/p1_step4c_20261016/cloud_results/`（或下一步指定的新目录），交给 Claude Code 写入回执与报告（新结果放新目录，不覆盖旧结果）。

## 9. 关机与清理

1. 确认结果已下载并校验后，在 AutoDL 控制台**立即关机**（按量计费在关机后停止）。
2. 不再需要实例时：先删除实例上的许可文件（`rm /root/.gurobi/gurobi.lic`），再释放实例。
3. 在本机记录：实例规格、区域、开机与关机时间、实际费用，供 2920×3h 估算使用。
