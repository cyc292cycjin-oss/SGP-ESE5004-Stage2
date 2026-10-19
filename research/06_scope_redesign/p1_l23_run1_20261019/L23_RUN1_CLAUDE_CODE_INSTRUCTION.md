# L23 首批云端正式运行：部署、监督、回收与首轮分析

**版本：** v1，2026-10-19 00:50 SGT，由 Claude（审阅端）写入。开始前核对本文件 SHA256，与同目录 `L23_RUN1_INSTRUCTION_SHA256.txt` 一致才执行；不一致就停下报告。
**模型：** Opus 5.5，xhigh。**所有过程说明、进度汇报和思考要点一律用中文输出**（代码、命令、文件名、配置键保持原样）。

## 0. 授权与范围

**用户授权（原文由用户在启动本指令时给出，写入 `L23_PROGRESS.md`）：** 用户授权 Claude Code 经 SSH 连接 AutoDL 实例，执行部署、预检、首批 365×24h 正式运行、监督、结果回收与首轮分析。

- **实例：** AutoDL 西北 B 区 144 机，实例 509c44b497-0de3e721，RTX 3080 Ti × 1（GPU 不用），12 核 Xeon Silver 4214R，90 GB 内存，数据盘 50 GB，按量计费。
- **部署包：** `D:\ResearchWorkspaces\ASEAN\work\p1_step4k_20261018\cloud_package_dist\`（代码提交 56d283580799c510b617c70b6e3292ba224e4ae0）。**不得使用** `cloud_package_dist_2d4aaac3_superseded` 及 S4J 以前的任何部署包。
- **运行：** 一体化 STEPS、不互联 STEPS、一体化 NZE，以及仅在不互联主算非最优时自动运行的不互联诊断；档案 A（`--solver-profile formal_barrier`），`--mode serial`；每运行 Gurobi TimeLimit 10,500 s、墙钟上限 3 h（脚本固定）。
- **不在范围内：** 第二批敏感性、联盟运行、2920×3h、任何重跑、任何参数修改、warm start。

## 1. 安全规则（必须遵守）

1. **SSH 凭据：** 优先用密钥登录（用户已在 AutoDL 设置免密登录时）。不得把主机、端口、密码写入仓库、进度文件、报告或提交信息（报告中只写"西北 B 区 144 机"）；不得在输出中显示密码。
2. **Gurobi 许可：** 本机许可文件经 `scp` 直接传到实例 `/root/.gurobi/gurobi.lic`，`chmod 600`；全程不得 `cat`、`head`、打印、复制到其他位置或纳入任何打包；运行时只通过 `GRB_LICENSE_FILE` 引用。若用户选择自己上传许可，则等待用户确认后再继续。结果回收后删除实例上的许可文件（`rm -f /root/.gurobi/gurobi.lic`）。
3. **许可并发：** 学术 WLS 同时最多 2 个会话。运行期间本机不得启动任何 Gurobi 求解（包括测试）；预检结束后至少等待 5 分钟再启动正式运行。
4. **不删除** 实例上除许可文件以外的任何数据；不释放实例；**关机由用户在 AutoDL 控制台操作**。
5. 不合并 main，不 force-push；不修改历史结果与 SHA 定点；不下载除本运行结果以外的任何东西（conda 环境安装所需的包除外）。

## 2. 执行步骤

每完成一步更新 `work/p1_l23_run1_20261019/L23_PROGRESS.md`（时间用 SGT；不含凭据）并提交，以便额度中断后续行。分支从 PR #35 最新提交（S4K，先核实）开出 `codex/l23-run1-20261019`，draft PR 叠在 #35 上；结果压缩包不进 git，只提交报告与摘要证据。

- **C0 核对：** 本指令 SHA256；本机部署包 `sha256sum -c SHA256SUMS`（15 个 OK）；记录用户授权原文。
- **C1 连接与实例核对：** SSH 连接；记录 `nproc`、`lscpu` 型号、`free -g`、`df -h /root/autodl-tmp`、操作系统版本。内存 < 40 GB、核数 < 8 或数据盘可用 < 35 GB 时停下报告。
- **C2 上传：** 把部署包全部内容传到 `/root/autodl-tmp/s4k_cloud/`（`rsync` 或 `scp`）；实例上 `sha256sum -c SHA256SUMS` 全部 OK，否则重传一次，仍失败则停下报告。
- **C3 环境：** `source /etc/network_turbo`（可用时）；`conda env create -n pypsa-earth -f environment_pypsa-earth.yml`；`test -x /usr/bin/time || apt-get install -y time`；记录 Python 路径与关键包版本（pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4），与部署包清单不一致时停下报告。
- **C4 许可：** 按第 1 节第 2 条。
- **C5 预检：** `PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash preflight.sh serial formal_barrier`，最后一行须为 `PREFLIGHT OK`，否则停下报告（不改脚本）。
- **C6 启动：** 预检结束后等待 ≥ 5 分钟。在 `tmux` 会话 `s4k` 中执行：
  `PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash run_365x24h.sh --solver-profile formal_barrier --mode serial --auth "<授权原文与时间>"`
  授权原文用 `S4K_REPORT.md` §10.4 模板，填入：规格"RTX 3080 Ti × 1，12 核 Xeon Silver 4214R，90 GB 内存，数据盘 50 GB"；区域"西北 B 区 144 机"；运行方式 serial；许可路径 `/root/.gurobi/gurobi.lic`；授权人"程宇晨"；时间为启动时刻（SGT）。记录启动时间。
- **C7 监督：** 每 10–15 分钟检查一次 `runs/<时间戳>/STATUS.txt`、`MONITOR_<运行>.csv` 末行、可用内存与磁盘，摘要写入进度文件。
  - **只观察、不干预：** 不中止、不重启、不改参数。脚本自身的墙钟上限与非最优处理照常生效。
  - 可用内存 < 2 GiB、或某运行已超过预计悲观用时（一体化 95、不互联 74、NZE 138、诊断 153 分钟；本机 CPU 可能较慢，实际可能更长）时，在进度文件中标注，继续观察。
  - 若本会话中断，正式运行在实例 `tmux` 中继续；续行时先读进度文件，再查 `STATUS.txt`。
- **C8 回收：** `STATUS.txt` 出现 `DONE` 后：
  1. 下载 `runs/<时间戳>/results_<时间戳>.tar.gz` 与同名 `.sha256`，以及 `STATUS.txt`、全部 `MONITOR_*.csv`，放到本机 `D:\ResearchWorkspaces\ASEAN\work\p1_step4k_20261018\cloud_results\<时间戳>\`；本机核对 SHA256。
  2. 对解包后的结果扫描许可特征串（同 S4K 收尾检查），发现即停下报告。
  3. 删除实例上的许可文件；在进度文件与对用户的消息中提醒用户**到 AutoDL 控制台关机**，并记录开机到 `DONE` 的时长与估算费用（¥1.08/时）。

## 3. 首轮分析（C9，只读结果，不做新决定）

写 `work/p1_l23_run1_20261019/L23_RUN1_REPORT.md`（开头 10 行以内摘要）与 `L23_RUN1_EVIDENCE.json`：

1. **运行概况：** 各运行终止状态、barrier 迭代、求解与墙钟时间、峰值内存，与 `CLOUD_RESOURCE_ESTIMATE.md` §20 的估算对比（给出实例 CPU 相对本机的速度比）；是否触发不互联诊断或 3 h 上限。
2. **门槛：** V5 各门槛（含 B5、B6、B16、`all_passed_solver_tolerances` 与旧口径）逐项结果；未通过的列出具体行与量级。
3. **系统结果：** 两情景总成本、B6（互联总价值，绝对值与比例）、NZE 对比；东盟及分国的装机与发电结构（按技术）；跨境输电与管道建设、潮流与损耗；CO₂ 流向（东盟内船运、老挝过境、东盟外）；燃料舱账户。
4. **分国账本：** 一体化、不互联与差额（bn EUR），按科目分解的主要来源；与 S4K 冒烟（56 个时段）的方向对比，只比方向和排序，不比规模。
5. **需要关注的已登记事项：** 到单条扩建上限的线路（S4K §7 第 3 条）、长距离聚类交流线（MM–TH 等）、越南封存是否用满、PH 互联价值、单向现有气管道等，逐项给出正式结果中的表现。
6. **"发现但未处理"：** 正式结果中的异常或疑点（例如不合理的装机、价格尖峰、门槛边缘），逐条写现象、涉及国家与量级、建议时点；**不修改、不重跑**。
7. **说明：** 365×24h 为日分辨率筛选结果，分摊结论以 2920×3h 为准（工作原则 / 正式分辨率第 6 条）；分摊规则中的 50/50 只是候选规则之一（第 110 项）；折现率为统一 0.07（第 111 项）。

## 4. 停止条件

- C1 实例规格低于下限；C2 上传校验两次失败；C3 版本不一致；C5 预检未通过；
- 需要改脚本、改参数或重跑才能继续；
- 结果中发现许可特征串；
- 任何安全规则（第 1 节）可能被违反的情形。

停下时写入进度文件并报告，等待用户与审阅端决定。

## 5. 交付

`work/p1_l23_run1_20261019/`：`L23_PROGRESS.md`、`L23_RUN1_REPORT.md`、`L23_RUN1_EVIDENCE.json`；结果压缩包在 `p1_step4k_20261018/cloud_results/<时间戳>/`（不进 git）。完成后停止，等待审阅。
