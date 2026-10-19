# S4O 进度记录（防中断用；时间为 SGT；不含任何主机、端口、密码或许可内容）

指令 `S4O_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-19 20:00 SGT），开始前核对 SHA256 = `b5f4d099f2afe2e4e4d93cd2dee94ce42857b3a26f62d2622657d78b068af6aa`，与 `S4O_INSTRUCTION_SHA256.txt` 及启动消息给出的值一致（VERIFIED）。模型 Opus 5.5。所有过程说明一律用中文。

## 用户授权原文（启动消息，原样记录）

> 授权：S4O-1 至 S4O-5 的本机部分（含 S4O-3 的 3 次本机 56×3h 运行）。云端部分（S4O-6）暂未授权——本机部分完成后停下报告，等待我提供实例与授权。
> 安全约束照旧：主机、端口、密码不写入任何文件或提交；非最优不重试、不改参数、不 warm start；不合并 main、不 force-push；上传只用单路 rsync。

## 步骤状态

| 步 | 内容 | 状态 | 时间（SGT） | 提交 / 说明 |
|---|---|---|---|---|
| S4O-0 | 核对与背景 | 完成 | | 指令 SHA256 一致；已读 S4N 报告全文、S4N 进度、补充 01 / 02 |
| S4O-1 | 整理与入库 | **完成** | 20:05–20:25 | ① `codex/s4n-calibration-20261019`（7c4f97fe）推送，draft PR [#39](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/39)，base = #38 分支 `codex/s4m-mainline-pilot-20261019`；② S4N 交付物入库 `research/06_scope_redesign/p1_step4n_20261019/`（170 个文件，5.4 MB；试点轻量包 tar.gz 全量 + 解包成员 ≤ 500 kB，4 个较大成员只在 tar.gz 内；`sha256sum -c` OK），先扫描：许可特征串（只命中 `s4n1_evidence.sh` 的扫描模式本身）、IPv4 形（只命中包版本号）、AutoDL / SeetaCloud 主机名（只命中 `s4n_netdiag.sh` 的公开网站 `www.autodl.com`）、ssh / scp / rsync 端口、user@host、密码——无登录信息（`/home/jin/s4o_scan.sh`），提交 **f28772e6**；③ 注册表片段 `s4o_0`（`scripts_project/s4o_0_data.py`：第 118、119、120 项 + 问题来源，共 4 行；注册表 1,958 行；`test_d1_registry.py` 13 passed）、台账 S4N 条目，提交 **46135c52**，已推送；④ 自 46135c52 开 `codex/s4o-production-20261019`，S4O 指令与 SHA 文件放入 `research/06_scope_redesign/p1_step4o_20261019/` |
| S4O-2 | 生产档案定稿 | **完成** | 20:25–21:20 | ① `configs/research/baseline.yaml`：`pypsa_eur_default` = `{Threads: 8, Method: 2, Crossover: 0, BarConvTol: 1.e-5, Seed: 123, AggFill: 0, PreDual: 0, GURO_PAR_BARDENSETHRESH: 200}`（两处适配：键名大写、Threads 8；理由写在配置注释与注册表 `s4o_decision_120_production_profile`），缺省 `research.solver.profile` 改为 `pypsa_eur_default`，档案 A 不改；② `s2_solve.py`：`profile_parameters()`（键名与已知 Gurobi 参数只差大小写即拒绝，防止 S4N 发现第 10 条复现）、`interior_solution()`（门槛路径，行为不变）；③ C1 流水线模块 `scripts_project/s4o_c1_precision.py`（`run` / `reference` / `regrade`；输出 `PRECISION.json/.md` 写入 `EXPORTS.json`；验收 = optimal + (a)(b)(c)；门槛作数值信息；分国容差参照：本批两种 STEPS 都有结果前用 L23，之后用本批差额并重评）；在 S4N-1 结果上与 S4N 工具等价（影子目录，原结果未改；分国数值最大差 0.0，分级相同；用时 22 s / 1.7 GiB）；④ 测试 `test_s4o_2.py` 7 项（档案键名识别、内点路径、C1 玩具模型 KKT 项、分级 / 验收 / 参照、重评与 `EXPORTS.json`、无解时不可计算），`tests/research` 543 passed（原 536 + 7；两处旧测试的缺省档案断言改为 `pypsa_eur_default`）——提交 **d5b4eb96**；⑤ 部署运行脚本并入 C1（`research/06_scope_redesign/p1_step4o_20261019/cloud_package/run_365x24h.sh`：缺省档案 `pypsa_eur_default`；每次求解后 C1（`env -u GRB_LICENSE_FILE`）；批内参照与重评；serial 相邻求解间隔 `RUN_GAP_S` 330 s；一体化非最优且 C1 不通过则停止）、`preflight.sh`（档案节检查缺省档案与键名、新增 c1 节）；脚本测试 50/50、探针测试 9/9（`evidence/s4o_4/`） |
| S4O-3 | 本机标定复核（3 次 56×3h） | **停止（标准不通过）** | 20:53:36–20:59:01 | `/home/jin/s4o_3_run.sh 18f55488`（不传 `--solver-profile`，取缺省；30 分钟止损；间隔 ≥ 5 分钟；每次求解后 C1）。**一体化：optimal**，58 次迭代 / 78.44 s / 120.84 WU，求解 172.9 s，墙钟 222 s，峰值 4.09 GiB，`interior_solution` True；目标 648,395,012,280.16，与 S4M-2 档案 A 相对差 **2.13e-5 > 1e-5（第 107 项标准不通过）**；B16 2.4e-8；C1：(a) **不通过**（−0.0181 bn，相对 2.79e-5），(b)(c) 通过，分级 not_layer1，验收 False。按 S4O-3 第 4 点停下：20:58:51 在间隔等待中结束运行脚本，不互联与 NZE **未启动**；核实无求解 / C1 进程；本机最后 Gurobi 结束 20:57:18。只读补充：S4N C2 三次运行补算 C1 全过（相对差 5.5–7.8e-6）。证据 `evidence/s4o_3/` |
| S4O-4 | 部署包更新 | **未进入**（停止条件） | | 运行期间写好的 `make_package.sh`（S4O 版）、`package_checks.py`、`preflight.sh` 就地更新处理、测试用例 I：未运行，只做语法检查；只读核对：f50c8850 包网络来自 `results_project/s4m/s4m3/builds`（构建提交 f50c8850），对 18f55488 的变更分类全部可接受 |
| S4O-5 | 资源估算修订 | **未做**（停止） | | |
| S4O-6 | 云端整批 | **未授权** | | 等待用户提供实例与授权原文 |
| S4O-7 | 报告 | 停止报告完成 | 21:30 | `S4O_REPORT.md`、`S4O_EVIDENCE.json`、台账 S4O 条目；提交 **a1ff1e6a**，分支已推送，draft PR [#40](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/40)（base = #39 分支） |

## 补充 01（第 121 项）

用户原文（约 21:45 SGT）："补充指令：请阅读并执行 …S4O_SUPPLEMENT_01.md，先核对 SHA256 应为 f723c544946142ca5e896a56652f95e4fcb3eba586bed21d9cce5ce6e8c7a7a4，不一致就停下报告。第 121 项已确认：生产档案回到档案 A；本补充中的 1 次本机 56×3h 运行已授权；云端（S4O-6）仍未授权，本机部分完成后停下报告。所有说明用中文输出。"——SHA256 核对一致（与 `S4O_SUPPLEMENT_01_SHA256.txt` 相同）。

| 步 | 内容 | 状态 | 时间（SGT） | 提交 / 说明 |
|---|---|---|---|---|
| S4O-2′ | 缺省档案改回 A、脚本参数、测试 | **完成** | 约 21:10–21:34 | 配置缺省 `formal_barrier`（注释写明第 121 项与理由），`pypsa_eur_default` 注明非生产；注册表片段 `s4o_1`（第 121 项 3 行 + 问题来源，注册表 1,962 行）；`run_365x24h.sh` 缺省档案 A、缺省运行 `disconnected,integrated_nze`、TimeLimit / 墙钟 21,600 / 22,500 s、`PILOT_INTEGRATED` / `PILOT_PRECISION`（以试点一体化作参照、在副本上重评试点 C1、`PILOT_CONSISTENCY.json`）、`TRUNCATE` 钩子；`speed_probe.sh` 建议值基数 21,600 s；`s4o_c1_precision.regrade` 兼容 S4N 试点格式；测试：`test_s4o_2.py` 8 项、`tests/research` **544 passed**，部署脚本测试 **59/59**、探针 **9/9**——提交 **87e28e3b** |
| S4O-3′ | 本机 56×3h 端到端验证（1 次，已授权） | **完成，验收全部通过** | 21:35:28–21:42:04 | `/home/jin/s4o_3b_e2e.sh 87e28e3b`：本机类包目录（代码 = 87e28e3b 的 git archive；`networks/integrated_365_24h_unsolved.nc` → S4M-1 2920×3h 构建（`513f56a6…`）的符号链接；`TRUNCATE=56`）+ S4O 版 `run_365x24h.sh`（不传档案 → 缺省 `formal_barrier`，回执确认；TimeLimit 1,750 s、墙钟 1,800 s；一次）。预检（profile / c1 / versions / tools）OK。**optimal**，141 次迭代 / 217.03 s / 407.73 WU，求解 310.6 s，墙钟 362 s，峰值 4.11 GiB，`interior_solution` True；目标 648,381,181,410.4515，与 S4M-2 **相对差 0.0**（≤ 1e-9）；流水线自动 C1（33 s、1.7 GiB）：layer1 + 电价结算，验收 True，`PRECISION.json/.md`、`VIOLATIONS.json` 在求解与导出目录的 `EXPORTS.json` 中（SHA256 一致）；分级与 S4O-2 等价核对相同，(a) 差值、(b)(c) 分国数值差 0.0。门槛：S4B 口径全通过，`all_passed_solver_tolerances` 仅因 B12（配置哈希，按构造）为 False。许可扫描无命中。证据 `evidence/s4o_3b/`；提交 **126110ff**（含 S4O-5 文档） |
| S4O-4 | 部署包更新 | **完成** | 21:45–21:50 | `/home/jin/s4o_4_package.sh 126110ff`：`make_package.sh`（S4O 版）以 `results_project/s4m/s4m3/builds`（f50c8850 重建）与参照包 `work/p1_step4m_20261019/cloud_package_dist` → `work/p1_step4o_20261019/cloud_package_dist/`（26 个文件，264.4 MB，`COMMIT` 126110ff）；构建输入变更分类无拒绝；**`networks/` 13 个文件与 f50c8850 包 SHA256 逐一相同**；`PACKAGE_DELTA.json`：变化 5、新增 5、去掉 1、未变 16，上传 124.3 MB；`SHA256SUMS` 26/26、预检（sha / networks / profile / c1 / versions / tools）OK、干跑 2 个求解、许可扫描无命中；包内脚本重跑测试 59/59、9/9。证据 `evidence/s4o_4p/` |
| S4O-5 | 资源估算修订 | **完成** | 21:40 | `CLOUD_RESOURCE_ESTIMATE.md` §23（计算 `evidence/scripts/s4o5_calc.py`） |
| S4O-7′ | 报告（补充 01） | **完成** | 21:55 | `S4O_REPORT.md` §10、`S4O_EVIDENCE.json`、台账补记 |

## S4O-6 云端整批（用户授权）

用户授权原文（约 22:00 SGT；**主机与端口已删去，只在命令行使用**）："授权 S4O-6（按补充 01）：1. 实例：<D58 / D58 在西北B区的克隆，主机 CPU 为 8470Q 或 8481C>；SSH 登录指令：[已删去] 2. 许可文件按 L23 方式处理：scp 到 /root/.gurobi/gurobi.lic，chmod 600，不读不打印，全部运行回收后删除。3. 试点结果：使用实例上的原目录 /root/autodl-tmp/s4m_cloud/runs/20261019T072454Z_5125/integrated/（若为新实例，则从本机轻量包上传所需文件）。4. TimeLimit / 墙钟：21,600 / 22,500 s。串行运行不互联 STEPS 与一体化 NZE（诊断仅在不互联非最优时运行）；非最优不重试、不改参数。同时下载试点完整结果包。代码包暂不瘦身。所有说明用中文输出。"——因整段为粘贴内容且实例一栏为占位符，向用户确认；用户回复（原文，主机端口删去）："确认，这是我本人的授权。实例是 <=D58 在西北B区 F73 机上的克隆>，CPU 为 <595.91.07>；登录指令无误（区域代码以 AutoDL 实际分配为准）。按补充 01 的 S4O-6 执行。[已删去]"；随后补充："25 vCPU Intel(R) Xeon(R) Platinum 8481C"。

| 步 | 内容 | 状态 | 时间（SGT） | 说明 |
|---|---|---|---|---|
| 6.1 | 只读核对 | 完成 | 22:08 | 密钥登录成功。**Xeon Platinum 8481C**（2 路 × 56 核 / 224 线程，最高 2.0 GHz，L3 210 MiB，AVX-512）；cgroup v2：**25 核**、内存 **92.0 GiB**（98,784,247,808 B）；数据盘 50 GB **空**；系统盘 25 GB 可用；Ubuntu 22.04.5；容器启动 21:57:27；环境 python 3.11.13 / pypsa 0.30.3 / linopy 0.5.5 / numpy 1.26.4 / gurobipy 12.0.3；tmux / rsync / setsid / GNU time 在；`/root/.gurobi` 空。**克隆未带数据盘：无 f50c8850 包、无试点运行目录、无试点完整结果包** → 整包上传（增量不适用）；试点参照按授权第 3 点从本机轻量包上传 3 个小文件；试点完整包无法从本实例下载（只在原 D58 数据盘） |

| 6.2 | 上传整包 + 试点文件 | **完成，26/26 OK** | 22:09–00:09 | `s4o_c2.sh`：单路 rsync → `/root/autodl-tmp/s4o_cloud/`，264,363,290 B / 7,192 s（约 36 KB/s，S4N 时 131 KB/s）；不打断、无并行流；试点 3 个文件 14 s → `/root/autodl-tmp/s4n_pilot/`（两端 SHA256 一致）；实例上完整 `sha256sum -c SHA256SUMS` **26 OK**、`COMMIT` 126110ff、30 个文件、字节数相同、无残留临时文件 |
| 6.3 | 许可 | 完成 | 00:10:26 | 本机无 Gurobi 进程（00:10:03）；`s4o_c4.sh` scp → `/root/.gurobi/gurobi.lic`，mode 600、目录 700、仅此一个文件、308 B，两端哈希一致（未打印）；未读取、未打印 |
| 6.4 | 预检 | **PREFLIGHT OK** | 00:10:33–00:10:43 | `s4o_c5.sh`：全部分节，缺省档案 A（内点门槛路径），C1 可导入，版本一致，许可被接受（输出屏蔽），资源 25 核 / 92 GiB / 磁盘 49 GiB（serial 下限 8 / 40 / 35） |
| 6.5 | 速度探针 | **完成，r = 0.836 ≥ 0.5** | 00:16:57–00:24:28 | `s4o_probe.sh`（预检令牌 + 5 分钟后；第一次启动被脚本自检拒绝，见 D5）；tmux `s4o_probe`，目录 `probe/20261019T161657Z_5633/`：optimal，目标 648,381,181,408.8285（与本机参照相对差 **−2.5e-12** ≤ 1e-6，环境等价；与 S4N 8470Q 探针目标相同），141 次迭代 / 240.99 s / 375.14 WU → 0.642 s/WU；**r（WU）0.836**，按迭代 0.908；墙钟 451 s。按第 4 条：TimeLimit / 墙钟 21,600 / 22,500 s 不变 |
| 6.7 | 回收 | **完成** | 02:04–03:43 | 不互联、诊断的单运行完整包在 NZE 运行期间下载（D12）；DONE 后实例端 `s4o_r_post.sh`：整批结果包 `sha256sum -c` OK（461,001,705 B，105 个成员，SHA256 `c37f8d93…ccef`），轻量包 5,782,612 B（SHA256 `f8cffc10…caca`，许可扫描无命中）；本机单路下载：轻量包 9 s、整批完整包 80 s，`sha256sum -c` 均 OK，许可串扫描 0 命中；批内不互联 / 诊断文件与单运行包逐文件相同；结果在 `work/p1_step4o_20261019/cloud_results/20261019T162951Z_6896/`（不进 git）。试点完整包不在本实例（D3） |
| 6.8 | 删除许可 | **完成** | 03:43:29 | 确认无求解 / 分析进程、无 s4o tmux 会话后 `shred -u /root/.gurobi/gurobi.lic`，核实不存在；其他文件未删除。**可以在 AutoDL 控制台关机** |
| 6.6 | 整批 | **完成（三个运行均 SUBOPTIMAL）** | 00:29:51–03:40:20 | 运行目录 `runs/20261019T162951Z_6896`；STATUS：`START … runs:disconnected,integrated_nze solver_profile:formal_barrier commit:126110ff wall_cap_s:22500 time_limit_s:21600 profile_source:default_(decision_121) run_gap_s:330 c1_step:on truncate:none pilot_integrated:given`、`CGROUP_MEMORY_LIMIT_GIB:92.00`、`SOLVE_disconnected` 00:29:52；磁盘空闲 49.0 GiB。| `s4o_launch_batch.sh`：探针结束 + 5 分钟后，tmux `s4o`，`run_365x24h.sh --mode serial`（缺省：档案 A；不互联 → NZE；诊断仅在不互联非最优时），21,600 / 22,500 s，`PILOT_INTEGRATED` / `PILOT_PRECISION` → `/root/autodl-tmp/s4n_pilot/` |

### 整批监督记录（只读；时间 SGT；内存为容器 cgroup，扣除非活动文件缓存）

| 时间 | 运行 | 已用 | 进程组 RSS | 容器内存 | 磁盘空闲 | barrier 末行（迭代：原始 / 对偶目标，原始残差 / 对偶残差 / 互补，秒） | 备注 |
|---|---|---|---|---|---|---|---|
| 00:31 | 不互联 | 1 min | 6.0 GiB | 6.7 / 92 GiB | 49 GB | — | 建模中 |
| 00:45 | 不互联 | 16 min | — | — | 49 GB | 107：5.82442947e11 / 5.82457302e11，0.584 / 3.5e-4 / 2.02，825 s | 约 10 s / 次 |
| 01:01 | 不互联 | 31 min | 11.5 GiB | 12.1 / 92 GiB（可用 79.9） | 48 GB | 232：5.82455958e11 / 5.82526850e11，11.9 / 1.6e-3 / 8.12，1,735 s | **第 126 次迭代重启（D8）**；第二轮回落中，对偶目标高于原始目标 |
| 01:17 | 不互联 → 诊断 | 47 min | — | 1.7 / 92 GiB | 48 GB | 287（末行）：5.82438789e11 / 5.82444754e11，9.00 / 3.6e-2 / 0.451，2,202 s → **"Barrier performed 287 iterations in 2201.57 seconds (2177.96 work units)"，"Sub-optimal termination - objective 5.82438909e+11"** | `RUN_disconnected:suboptimal:2588s`；`PRECISION_disconnected:layer1_plus_nodal_price_settlement:accepted=False:abc=111:ref=L23`（133 s，7.7 GiB）；`DISCONNECTED_MAIN_NON_OPTIMAL:suboptimal -> running disconnected_gap diagnostic`（D9） |
| 01:32 | 诊断 | 14 min | 11.8 GiB | 13.4 / 92 GiB（可用 78.6） | 47 GB | 88：5.82442072e11 / 5.82437389e11，4.37 / 1.8e-4 / 1.11，701 s | `GAP_disconnected_gap:333s`，01:18:33 启动；约 8 s / 次 |
| 02:03 | 诊断 → NZE | — | 11.1 GiB（诊断峰段） | 10.5 / 92 GiB | 46 GB | 诊断末行 245：5.82439452e11 / 5.82438541e11，24.0 / 1.04e-2 / 0.528，1,920 s → **Sub-optimal termination - objective 5.82441437e+11** | `RUN_disconnected_gap:suboptimal:2308s`；C1 125 s / 7.9 GiB；`BATCH_REFERENCE`（试点一体化）、`PILOT_CONSISTENCY:network_same=True:profile_same=True:pilot=optimal`、三条 `REGRADE`；`SOLVE_integrated_nze` 02:02:34（D10、D11） |
| 02:34 | NZE | 31 min | 15.2 GiB | 18.0 / 92 GiB（可用 74.0） | 45 GB | 83：4.22875514e11 / 4.22873872e11，26.8 / 2.3e-5 / 0.498，1,714 s | 约 26 s / 次；无跳开 |
| 03:04 | NZE | 62 min | 15.2 GiB | 18.0 / 92 GiB | 45 GB | 152：4.22874524e11 / 4.22874252e11，6.87 / 2.8e-5 / 0.082，3,535 s | 下降放缓（第 150–152 次残差 7.3 → 6.9）；无跳开 |
| 03:35 | NZE | 结束 | — | 11.7 / 92 GiB | 45 GB | 216（末行）：4.22874418e11 / 4.22874284e11，4.40 / 1.0e-4 / 0.041，5,238 s → **"Barrier performed 216 iterations in 5238.26 seconds (3638.01 work units)"，"Sub-optimal termination - objective 4.22874423e+11"** | 第 152–216 次停滞于原始残差 4–7（D13）；C1 运行中 |

## 补充 02（无人值守运行规则）

用户原文（约 22:25 SGT）："补充指令：请阅读并执行 …S4O_SUPPLEMENT_02.md，先核对 SHA256 应为 1898d3f79798eff99ddddccda32c7f0bc57ec669c25dabcd4c4bfb1bdbcb7d97，不一致就停下报告。这是我本人的要求：从现在起无人值守运行到 S4O 报告完成，按补充 02 的决定规则处理，不再向我提问；所有自动决定记入进度文件并在报告中汇总。所有说明用中文输出。"——SHA256 核对一致（与 `S4O_SUPPLEMENT_02_SHA256.txt` 相同）。

## 自动决定

| # | 时间（SGT） | 情况 | 依据 | 处理 |
|---|---|---|---|---|
| D1 | 22:10 | 克隆实例的数据盘为空：没有 f50c8850 包，`PACKAGE_DELTA.json` 的增量上传不适用 | 授权第 3 点"若为新实例"；补充 02 第 12 条（最保守：不改包内容） | 单路 rsync 上传**整个** S4O 部署包（264.4 MB，与本机 `cloud_package_dist` 相同），之后完整 `sha256sum -c` |
| D2 | 22:10 | 试点运行目录与 `PILOT_PRECISION.json` 不在实例上 | 授权第 3 点 | 从本机试点轻量包上传 `export_integrated/COUNTRY_COST_LEDGER.csv`、`SOLVE_RECEIPT.json`、`PILOT_PRECISION.json` 到 `/root/autodl-tmp/s4n_pilot/`，核对 SHA256 |
| D3 | 22:10 | 授权要求"同时下载试点完整结果包"，但它只在原 D58 的数据盘上，本实例没有 | 补充 02 第 12 条（不新租或更换实例） | 不下载，报告中写明：试点完整包仍在原 D58 数据盘（`runs/20261019T072454Z_5125/results_20261019T072454Z_5125.tar.gz`，SHA256 `cb4927da…7480`，释放期约到 11-03），需另行安排 |
| D4 | 22:10 | CPU 为 8481C（与 8470Q 不同） | 补充 01；补充 02 第 4 条 | 预检后先跑速度探针，按 r 决定 TimeLimit 或收尾 |
| D5 | 00:16 | 第一次启动探针被本会话脚本的进程检查拒绝（"REFUSED: solve running"）：检查与启动在同一条远程命令里，命令行含 `speed_probe.sh` 字样，`ps` 匹配到了自己；核实实例上无求解进程、无 tmux 会话、无探针目录（未启动任何求解） | 补充 02 第 12 条（不改模型 / 档案 / 网络；只修正本机辅助脚本） | 把进程检查与启动拆成两次 SSH 调用（探针与整批启动脚本都改），00:16:57 重新启动探针（不是求解重试） |
| D7 | 00:30 | 本机监督脚本误报"内存不足"：脚本中 `$( … )` 内的 here-document 未被识别，查询在本机 WSL 执行（实例未受影响） | 补充 02 第 12 条（只修正本机辅助脚本） | 远程查询改为文件 `s4o_r_watch.sh` 经 `ssh bash -s` 执行，测试正确后重新监督（00:32） |
| D8 | 01:05 | 不互联运行内点法重启：第 126 次迭代（1,003 s，约 00:48 SGT），原始残差 3.68（第 125 次）→ **1.76e11**，原始 / 对偶目标 3.32e15 / −9.91e15；第一轮最小原始残差 0.306（第 111 次）；之后快速回落（第 130 次 7.3e8） | 补充 02 第 8 条 | 只记录，不干预 |
| D9 | 01:17 | 不互联 STEPS 以 **SUBOPTIMAL** 结束（287 次迭代，2,201.6 s；第二轮停在原始残差约 9、对偶残差约 3.6e-2）；C1 (a)(b)(c) 均通过（L23 参照），验收 False（非最优） | 补充 02 第 6 条 | 不重试、不改参数、不 warm start；C1 与违反分析已由流水线完成；按原计划诊断运行（`disconnected_gap`）由脚本自动启动（间隔 ≥ 330 s），之后 NZE |
| D10 | 02:03 | 不互联诊断 `disconnected_gap` 以 **SUBOPTIMAL** 结束（245 次迭代，1,919.6 s，1,866.56 WU；LP 目标 5.82441437e11；墙钟 2,308 s）；第 124 次迭代（1,013 s）重启：原始残差 3.61 → 1.77e11（第一轮最小 2.08，第 103 次）；C1 (a)(b)(c) 通过，验收 False | 补充 02 第 6、8 条 | 不重试；记录重启；继续 NZE（02:02:34 启动） |
| D11 | 02:03 | 本批无一体化运行，不互联完成后以"本批不互联 − 试点一体化"作 C1 参照（`BATCH_REFERENCE.json`，01:59:05）；`PILOT_CONSISTENCY`：网络相同、档案参数相同、试点 optimal；重评：试点副本验收 True，不互联 / 诊断 abc=111 | 补充 01 S4O-6 第 3 点（流水线自动） | 照流水线执行，无人工干预 |
| D12 | 02:05 | 不互联与诊断已完成且已重评；回收时间不确定（上传曾只有约 36 KB/s） | 补充 02 第 10 条精神（先回收已完成结果）；第 12 条（不删、不改结果） | NZE 运行期间在实例上为这两个运行各打一个完整包（`nice -n 19`，只读 `export/<运行>/`），单路下载：150,455,004 B / 41 s、151,427,801 B / 32 s（约 4 MB/s），本机 `sha256sum -c` OK，许可扫描无命中 |
| D13 | 03:35 | 一体化 NZE 以 **SUBOPTIMAL** 结束（216 次迭代，5,238 s，远低于 TimeLimit 21,600 s；第 150 次后停滞于原始残差 4–7，无跳开） | 补充 02 第 6 条 | 不重试、不改参数；C1 与违反分析由流水线完成；整批收尾（重评、打包）由脚本完成 |
| D6 | 00:24 | 探针 r = 0.836（≥ 0.5），目标相对差 −2.5e-12（≤ 1e-6） | 补充 02 第 4 条 | 照常：TimeLimit / 墙钟 21,600 / 22,500 s；探针结束 + 5 分钟后启动整批 |

## 发现但未处理

见 `S4O_REPORT.md` §8。

## 续行点

**S4O 全部完成（2026-10-20 约 03:55 SGT）。** S4O-6 整批三个运行均 SUBOPTIMAL、C1 全过；B6 69.243 bn、NZE − 一体化 −90.491 bn；回收完成，许可 03:43:29 删除，可关机。报告 `S4O_REPORT.md` §11（自动决定 D1–D13 汇总 §11.8，用户决定事项 §11.10）。终检：主机名 0 命中、端口无独立出现（只在 20 个数据文件的长数字中出现，巧合）、许可串 0 命中。

此前：**补充 01 本机部分全部完成，停下等待 S4O-6 云端授权（2026-10-19 约 21:55 SGT）。** 部署包 `work/p1_step4o_20261019/cloud_package_dist/`（`COMMIT` 126110ff）；上云按 `S4O_REPORT.md` §10.6 与 `PACKAGE_DELTA.json`：单路上传变化文件 → 完整 `sha256sum -c` → 预检（就地解包新代码）→ `PILOT_INTEGRATED` / `PILOT_PRECISION` 指向试点结果 → `run_365x24h.sh --mode serial`（缺省档案 A、不互联 + NZE、21,600 / 22,500 s）。云端运行期间本机不启动 Gurobi。

原记录：**S4O-3 触发停止条件，停下报告，等待用户决定（2026-10-19 约 21:30 SGT）。** 用户决定事项见 `S4O_REPORT.md` §7（生产档案如何处理；是否补做 2 次未执行的本机运行；S4O-4 / S4O-5 是否继续）。S4O-4 继续时：用 `results_project/s4m/s4m3/builds`（f50c8850 重建）与参照包 `work/p1_step4m_20261019/cloud_package_dist` 运行 `cloud_package/make_package.sh`，先跑 `evidence/scripts/s4o_4_script_tests.sh`（含新用例 I）。本地仓库在 `codex/s4o-production-20261019` 上。
