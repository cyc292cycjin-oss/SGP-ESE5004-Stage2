# 云端部署步骤（AutoDL，365×24h 日分辨率运行；S4K 最终提交，云端档案 A `formal_barrier`，首批串行）

本文件只说明操作步骤。Claude Code 不连接云端，也不启动任何正式求解；每一步由用户在 AutoDL 上执行。**正式运行前须由用户单独明确授权**（CLAUDE.md：每次优化都需要用户单独明确授权；不自动重试、不做参数网格、不 warm start）。授权原文模板见 `S4K_REPORT.md` §10.4。

- 资源需求见 `CLOUD_RESOURCE_ESTIMATE.md` §20。
- 部署包脚本在 `cloud_package/`（仓库 `research/06_scope_redesign/p1_step4k_20261018/cloud_package/`）。
- 打包产物在本机 `work/p1_step4k_20261018/cloud_package_dist/`（含网络与代码快照，不进 git）。

与 S4J 版（`p1_step4j_20261018/CLOUD_DEPLOY_STEPS.md`）的区别：

- **S4J 部署包作废（S4K，第 108 项）：** 上云只用本文件对应的 S4K 部署包（`work/p1_step4k_20261018/cloud_package_dist/`）。S4H、S4G、S4F 部署包此前已作废。若实例上已有旧包，请删除后再上传。
- **代码快照与四个网络更新到 S4K 最终代码提交。** 在 S4J 主算设置之上，交流线损改为**线性损耗代理（第 108 项）**：每条交流线、每个时段的损耗 ≥ λ × |潮流|，并且 ≤ λ × 允许负载；λ 按线型逐线计算（一回线、参考负载为允许负载的一半，0.77–13.7 %，中位 3.5 %），损耗在两端各计一半。求解时 PyPSA `transmission_losses` = 0，代理由钩子 `research_ac_loss_proxy` 加入。直流与管道损耗不变。
- **预计墙钟变长：** 串行 2.5–3.5 h（S4J 2.2–3.0 h），NZE 单运行悲观 138 min；见 §1 与 `CLOUD_RESOURCE_ESTIMATE.md` §20。
- **第二批敏感性**增加第 108 项的上下界两项，共 14 项（§10）。

S4J 起已有、仍然适用的变化（相对 S4H）：

- **S4J 主算设置（第 104–107 项）：**
  - **非工业电力负荷（第 104 项）：** 各国基础负荷改为需求表中居民、商业、农业及其他、交通的电力之和，Astar 只给小时形状；
  - **输送损耗（第 105 项 a）：** 按 PyPSA-Eur v2025.07.0 缺省值：直流 0.98 × 0.977^(L/1000)；H₂ / 气管道压缩耗电；双向链路拆为正、反两条（交流线损自 S4K 起改为线性代理，见上）；
  - **TH–MY 直流（第 105 项 b、第 107 项）：** 直流改为双向（有损拆分）；两端两台 B2B 换流器双向、不可扩建，容量固定为直流扩建上限 20,300 MW，不另计成本（开关 `research.network.th_my_hvdc: bidirectional_fixed_b2b`）。
- **许可与运行方式（第 106 项 a、b）：**
  - 学术 WLS 许可同时最多 2 个会话；Gurobi 环境关闭后，令牌至少保留 5 分钟。每个运行占 1 个会话，预检的许可检查也占 1 个。
  - **三通道（`lanes3`）已撤下**，脚本会拒绝并说明原因。**首批推荐串行（`serial`）。**
  - 两通道（`lanes2`）启动时先等 330 秒，通道内衔接下一个运行前再等 330 秒。
  - 预检新增 `/usr/bin/time`（GNU time）检查，缺失时为失败项，并提示 `apt-get install -y time`。
- **云端档案为 A：** 运行命令一律写 `--solver-profile formal_barrier`。脚本仍保持"必填、无默认值"，不写时拒绝启动。
- **导出：** 与 S4H 相同；损耗体现在求解后网络的 `p0` / `p1` 中（交流线 `p0 + p1` = 线损，直流链路 `p0 + p1` = 直流损耗，管道第三端口 `p2` = 压缩耗电）。
- **首批三个运行不变：** 一体化主算（STEPS）、不互联主算（STEPS）、一体化 NZE 敏感性。不互联诊断网络也打包，**只在不互联主算非最优时自动运行**。
- **第二批敏感性只登记、不打包、不运行**，见 §10。联盟研究的范围由交付后与第 14 项一并确定（第 97 项 f），运行规则见 §11。

## 0. 部署包内容（`cloud_package_dist/`）

| 文件 | 说明 |
|---|---|
| `code_<commit8>.tar.gz` | 仓库在 S4K 最终代码提交时的完整快照（`git archive`），提交哈希见 `COMMIT`。含 `configs/` 与 `research_inputs/`：需求表与非工业电力表、走廊表 `CORRIDORS_S4H2.csv`、TH–MY 修正表、LA–VN 存量表、20 条线的电气参数修正表、损耗与直流换流表、交流损耗 λ 表 `LAMBDA_S4K1.csv`、海底份额与长度分摊表、APG 规划上限表、船运与过境表 |
| `networks/integrated_365_24h_unsolved.nc` | 一体化主算（STEPS）网络，构建回执 `integrated_BUILD_RECEIPT.json` |
| `networks/disconnected_365_24h_unsolved.nc` | 不互联主算网络（STEPS；东盟外 CO₂ 封存、老挝过境、东盟内船运、老挝进越南封存都保留） |
| `networks/integrated_nze_365_24h_unsolved.nc` | 一体化 NZE 敏感性网络（构建覆盖 `fuels.price_scenario=nze`，回执 `integrated_nze_BUILD_RECEIPT.json`） |
| `networks/disconnected_gap_diagnostic_365_24h_unsolved.nc` | 不互联诊断网络（gap_diagnostic）；只在不互联主算非最优时运行 |
| `environment_pypsa-earth.yml`、`conda_explicit_linux64.txt` | 本机 conda 环境导出（Python 3.11.13、pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4） |
| `preflight.sh` | 云端预检：校验 SHA256、解包代码、核对版本、检查 `/usr/bin/time`、检查许可可用（不显示许可内容）、核对 CPU / 内存 / 磁盘（§20 的下限）、可选核对求解档案名；只接受 `serial` / `lanes2` |
| `run_365x24h.sh` | 运行脚本：三个运行（加条件诊断），串行（推荐）/ 两通道（带 330 秒许可间隔），三通道已撤下；每运行 8 线程、墙钟上限 3 h；每分钟记录内存与进度；结束后自动导出回执、门槛结果、分国账本与节点价格（日志已剔除许可行） |
| `DATA_CONFIG_MANIFEST.json` | 数据与配置清单：`configs/`、`research_inputs/` 每个文件的 SHA256 与字节数；出力曲线与来源 cutout 的身份；四个网络的构建输入与回执摘要 |
| `SHA256SUMS`、`PACKAGE_MANIFEST.json`、`COMMIT` | 校验与清单。`PACKAGE_MANIFEST.json` 给出上传总字节数、运行命令示例、每运行的导出清单、首批运行，以及第二批敏感性的覆盖项 |

**不包含 Gurobi 许可文件**；许可由用户在云端自行放置，并通过 `GRB_LICENSE_FILE` 引用。

## 1. 选择与创建实例

1. 登录 AutoDL 控制台，进入「算力市场」。本任务只用 CPU 和内存（LP barrier 不用 GPU）。AutoDL 按 GPU 机型出售，CPU 核数与内存随 GPU 数量配给，所以按**内存与 CPU 核数**选择（数值见 `CLOUD_RESOURCE_ESTIMATE.md` §19）：
   - **串行（首批推荐）**（一体化 → 不互联主算（→ 诊断）→ 一体化 NZE）：内存下限 36 GB、推荐 ≥ 48 GB（单运行峰值上限估计 35.1 GiB，下限余量只有约 0.9 GiB），CPU ≥ 8 核；预计墙钟 2.5–3.5 h（悲观 5.1 h），若触发不互联诊断 3.8–5.3 h（悲观 7.7 h）；
   - 两通道（[一体化 → 330 秒 → NZE] ‖ [不互联主算（→ 330 秒 → 诊断）]，启动前另等 330 秒）：内存下限 72 GB、推荐 ≥ 96 GB，CPU ≥ 16 核；预计墙钟 2.1–2.8 h（内存带宽竞争再加 10–20 %；悲观 4.1 h），含诊断大致相同（两条通道用时相近）；
   - 三通道已撤下：学术 WLS 许可同时最多 2 个会话，三通道必有一个运行因许可被拒；
   - 预检低于下限即失败，低于推荐值只给警告。「无卡模式」只配很少的 CPU 与内存，**只用于上传、装环境和下载结果，不能用于求解**。
2. 镜像选 **Miniconda / Ubuntu 22.04**（基础镜像即可）。
3. 数据盘 `/root/autodl-tmp`：可用空间串行 ≥ 35 GB、两通道 ≥ 45 GB（每个运行输出约 1.5 GB，另加部署包与 conda 环境）。
4. 确认镜像有 GNU time：`test -x /usr/bin/time || apt-get install -y time`（预检也会检查）。
5. 由用户自己记下实例的登录方式（控制台「登录指令」）；Claude Code 不需要、也不接收登录密码。

## 2. 上传部署包

1. 本机：把 `work/p1_step4k_20261018/cloud_package_dist/` 整个文件夹上传。上传总大小见 `PACKAGE_MANIFEST.json` 的 `upload_total_bytes_excluding_this_manifest`（S4K 报告 §10.1 列出）。
2. 上传到实例的 `/root/autodl-tmp/s4k_cloud/`。可用 JupyterLab 拖拽、`scp -P <端口> -r cloud_package_dist root@<地址>:/root/autodl-tmp/s4k_cloud`，或经 AutoDL 网盘中转。
3. 实例上核对：`cd /root/autodl-tmp/s4k_cloud && sha256sum -c SHA256SUMS`，应全部 OK。

## 3. 安装环境

```bash
cd /root/autodl-tmp/s4k_cloud
conda env create -n pypsa-earth -f environment_pypsa-earth.yml
```

- 下载慢时可先执行 `source /etc/network_turbo`（AutoDL 学术加速，只对当前终端有效），或改用国内镜像。
- 若镜像缺 `gurobi` 包，可单独 `pip install gurobipy==12.0.3`。要完全复现，可用 `conda create -n pypsa-earth --file conda_explicit_linux64.txt`。
- 记下 Python 路径：`conda run -n pypsa-earth which python`（下文记为 `$PY`）。

## 4. 放置许可

1. 用户把自己的 Gurobi WLS 许可文件上传到只有自己可读的位置，例如 `/root/.gurobi/gurobi.lic`，并 `chmod 600`。
2. 不要把许可文件放进部署包目录或结果目录，不要 `cat` 或截图其内容。
3. WLS 许可需要实例能访问 Gurobi 令牌服务器（HTTPS 出站）；若所在区域限制外网，许可检查会失败，换区域或联系平台。
4. `export GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic`（每个新终端都要设置，或写入 `~/.bashrc`）。

## 5. 预检（不求解）

```bash
cd /root/autodl-tmp/s4k_cloud
PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash preflight.sh serial formal_barrier
```

- **检查顺序：** SHA256 → 解包代码到 `./repo` → 四个网络文件 → 求解档案名是否存在于打包的配置 → 关键包版本 → `/usr/bin/time` → 许可可用（输出屏蔽）→ CPU、内存、磁盘。
- **结果：** 最后一行应为 `PREFLIGHT OK`。两通道时把 `serial` 换成 `lanes2`；传入 `lanes3` 会被拒绝。
- **许可令牌：** 预检的许可检查会占用 1 个 WLS 令牌至少 5 分钟。串行不受影响；两通道的运行脚本启动时会先等 330 秒。
- **空跑：** `PY=$PY GRB_LICENSE_FILE=... bash run_365x24h.sh --solver-profile formal_barrier --mode serial --dry-run`。它只打印将执行的命令；不给 `--solver-profile` 时脚本拒绝启动，这是预期行为。

## 6. 启动运行（需用户授权后）

```bash
tmux new -s s4k
cd /root/autodl-tmp/s4k_cloud
PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash run_365x24h.sh --solver-profile formal_barrier --mode serial --auth "<用户授权原文与时间>"
# Ctrl-b 再按 d 脱离；重新进入：tmux attach -t s4k
```

- `--solver-profile formal_barrier`：用户 2026-10-17 确认的云端档案 A（含基尔霍夫行归一化）。
- `--mode`：`serial`（首批推荐）| `lanes2`（见 §1；脚本自动加 330 秒许可间隔，状态文件记录 `LICENCE_GAP:*`）。`lanes3` 已撤下，传入时脚本拒绝启动。`--runs` 可以只跑其中几项，例如 `--runs integrated,disconnected`；名单中写了 `disconnected_gap` 时，诊断无条件运行。
- **运行规则（脚本已固定，不要修改）：** 每运行 Gurobi TimeLimit 10,500 s，墙钟到 3 h 强制停止；**不重试、不改参数、不 warm start**；缩放与基尔霍夫行归一化按打包配置开启。
- **不互联主算预期可行。** 若它返回非最优，脚本记录 `DISCONNECTED_MAIN_NON_OPTIMAL:<状态>`，并自动运行不互联诊断以定位缺口。
- **任一运行非最优**（NUMERIC、SUBOPTIMAL、TIME_LIMIT 等）时，只记录状态并导出日志末尾（已剔除许可行），不会自动重跑；由用户把结果带回后决定下一步。

## 7. 监控

- **总体状态：** `cat runs/<时间戳>/STATUS.txt`。其中依次记录 `START … solver_profile:<档案>`、`RUN_<运行>:<终止状态>:<秒>`、`KILLED_3H_*`、`DISCONNECTED_MAIN_NON_OPTIMAL:*`、`DONE`。
- **每分钟记录：** `tail -f runs/<时间戳>/MONITOR_<运行>.csv`。字段为 UTC、已用秒数、进程树 RSS GiB、可用内存 GiB、剩余磁盘 GiB、Gurobi 日志最后一行（已剔除许可行）。
- **系统层面：** `htop`、`df -h /root/autodl-tmp`。可用内存降到 2 GiB 以下有 OOM 风险；只记录、不调参，结束后带回报告。

## 8. 回收结果

1. 脚本结束时生成 `runs/<时间戳>/results_<时间戳>.tar.gz` 及 `.sha256`，内容为 `export/<运行>/` 下的以下文件。打包前会检查许可特征串，发现即不打包。
   - **回执与门槛：** `SOLVE_RECEIPT.json`；`V5_GATES.json`（含 `B1_BUNKERS`、`B16_LEDGER`、第 71 项求解器容差口径的 `*_S4B` 门槛与 `all_passed_solver_tolerances`、旧口径 `all_passed_barconvtol`）；`INTERIOR_CHECKS.json`、`kkt_summary.json`；
   - **分国账本：** `COUNTRY_COST_LEDGER.csv`、`COUNTRY_COST_LEDGER_DETAIL.csv`、`LEDGER_IDENTITY.json`；
   - **节点价格：** `NODAL_PRICES.csv`；
   - **能源与碳：** `BUNKER_ACCOUNT.json`；`CO2_FLOWS.json`（东盟外封存、老挝过境、东盟内船运、老挝进越南封存）；`EMISSIONS_BY_COUNTRY.json`、`CAPACITY_BY_TECH_COUNTRY.json`、`cross_border_flows.csv`；`GAP_TABLE.json`（诊断）；
   - **日志与资源：** `GUROBI_LOG_SCRUBBED.txt` 与 `solve_log_scrubbed.txt`（均已剔除许可行）、`RESOURCE.jsonl`、`MONITOR_<运行>.csv`、`solve_time.txt`、`MATH_PROBLEM.json`；
   - **网络：** 求解后网络 `*_solved.nc`；非最优时另有 `LOG_TAIL_NONOPTIMAL.txt`、`STDERR_TAIL_NONOPTIMAL.txt`。
2. 原始 Gurobi 日志与 LP 数组（`lp/`）留在实例上，不下载。
3. 下载后在本机用 `.sha256` 核对，放到 `work/p1_step4k_20261018/cloud_results/`（或下一步指定的新目录），交给 Claude Code 写入回执与报告。新结果放新目录，不覆盖旧结果。

## 9. 关机与清理

1. 确认结果已下载并校验后，在 AutoDL 控制台**立即关机**（按量计费在关机后停止）。
2. 不再需要实例时：先删除实例上的许可文件（`rm /root/.gurobi/gurobi.lic`），再释放实例。
3. 在本机记录实例规格、区域、开机与关机时间、实际费用，供 2920×3h 估算使用。

## 10. 第二批敏感性（只登记，不打包、不运行）

按 S4K 指令 S4K-4（沿用 S4J 的十二项，并加入第 108 项的上界 `network.ac_loss_reference_loading=1.0` 与下界 `network.ac_losses=none`）。在首批云端运行经用户审阅之后另行授权；需在本机按下列覆盖项重建网络，再另行打包。十四项都已在本机构建中核对过结构，但没有求解。S4K 新做的构建核对：`ac_losses=none` 在 S4K-1 单独构建一次（与 S4J-7 构建逐组件相同）；`ac_loss_reference_loading=1.0` 在 S4K-4 单独构建一次（只有 λ 列变为主算的 2 倍）。S4J 的损耗、TH–MY 直流规则与 S4K 的交流损耗代理同样作用于这些敏感性（损耗对照项除外）：

| 敏感性 | 构建覆盖项（`s2_network.py --override`） | 情景 | 说明 |
|---|---|---|---|
| 东盟外 CO₂ 封存单价 −50 % / +50 % | `co2.extra_asean_cost_scale=0.5` / `1.5` | 一体化、不互联 | 乘在统一口径的 54.70 EUR2020/t 上 |
| 统一 ZEP 封存单价 | `s2.co2.sequestration_cost_eur_per_t=16.0535` | 一体化、不互联 | ZEP 2011 海上咸水层 Medium，同时作用于全部地质封存（东盟外 = 24.70 + 16.05 = 40.75） |
| 航线单一系数 | `co2.ship_distance=route_factor` | 一体化、不互联 | 大圆距离 × 1.091 代替逐对海上距离 |
| 老挝过境口径 | `co2.lao_transit_destination=existing_port`，`co2.lao_transit_mode=truck`（可单独或合用） | 一体化、不互联 | 最近现有海港 / 罐车 |
| LNG 接收站不设上限、只按成本 | `s3.gas.lng_expansion=uncapped_cost` | 一体化、不互联 | 扩建按 7,018 EUR/MW/a 计价；B14 在该模式下不设上限 |
| APG / AIMS 规划扩建上限（保守） | `network.max_extension=apg_plans` | 一体化、不互联 | 在 PyPSA-Eur 单条上限之外，每个 APG 项目组的总容量 ≤ max(存量, 规划)；18 组，钩子 `research_apg_corridor_cap` |
| SG–VN、SG–KH 候选 | `corridors.optional_sg_vn_kh=on` | 一体化 | APG 其他倡议，两条直流候选 |
| 19 条 readjust 线与 APG17 的作者电气参数（对照） | `network.readjust_impedance=author` | 一体化 | 第 98、101 b 项的对照：恢复作者 / 模板的 `num_parallel` 与阻抗 |
| LA–VN 作者存量（对照） | `network.la_vn_stock=author` | 一体化 | 第 100 项的对照：作者 1 MW 按长度分摊到线路 59 / 60 / 63 / 64（S4G 状态） |
| 候选线原回路数约定（对照） | `corridors.candidate_num_parallel=template43` | 一体化 | 第 101 a 项的对照：零容量交流候选线沿用模板线 43 的 `num_parallel` 1.286 |
| 非工业电力按 Astar 残差（对照） | `demand.nonindustrial_electricity=astar_residual` | 一体化、不互联 | 第 104 项的对照：Astar 减去比率法工业电力与交通电力（S4H 状态） |
| 不计输送损耗（对照） | `network.transmission_losses=none` | 一体化、不互联 | 第 105 a 项的对照：无交流线损（代理也不加）、直流效率 1、管道无压缩耗电、不拆分链路（TH–MY 直流仍为双向、`p_min_pu` = −1，两台 B2B 仍固定 20,300 MW） |
| 交流损耗代理上界 | `network.ac_loss_reference_loading=1.0` | 一体化、不互联 | 第 108 项：参考负载取一回线允许负载的全部（α = 1.0），λ 为主算的 2 倍（1.55–27.3 %） |
| 交流线无损（下界） | `network.ac_losses=none` | 一体化、不互联 | 第 108 项：交流线不计损耗，直流与管道损耗保留 |

用户确定后，敏感性网络的构建命令示例：`python scripts_project/s2_network.py --scenario integrated --output <dir> --override network.max_extension=apg_plans`。B12 门槛会按记录的覆盖项复核配置哈希。

## 11. 联盟研究的运行规则（第 95 项 f；范围待定，第 97 项 f）

- **联盟运行：** 在一体化情景上加覆盖项，例如 `--override "cross_border.coalition=[MY,SG]"`。只保留两端都在名单内的跨境走廊；贸易类链路（船运、老挝过境）与东盟外选项不受影响。
- **范围：** 联盟研究做哪些联盟，交付后与第 14 项一并请师哥判断（用户 2026-10-17 决定），本部署包不含联盟运行。S4E 拓扑下成员 ≥ 2 的连通联盟共 383 个；S4F–S4K 不改变国家间走廊图（S4H 新补的候选线都在已有走廊的国家对上，S4J 的反向链路是同一走廊的复制，S4K 只改交流线损耗）。算力估算见 S4I 报告 §4（第 106 项 d，作为第 14 项的依据）；学术许可最多两通道。
- **非最优的处理（用户 2026-10-17 决定）：** 联盟运行在档案 A（`formal_barrier`）下非最优时，改用档案 C（`--solver-profile barrier_numericfocus2`）重跑一次。仍非最优则标记为 **UNVERIFIED**，不再重跑，也不改参数。每次重跑都要记录在运行状态中。
