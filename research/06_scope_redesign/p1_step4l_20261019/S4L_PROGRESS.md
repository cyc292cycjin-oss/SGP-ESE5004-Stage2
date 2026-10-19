# S4L 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4L_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-19 10:10 SGT），开始前核对 SHA256 = `03508400f675304cd0bdfd40ccbd0c61005644e7b2a122dffbe2048e6a5d529b`，与 `S4L_INSTRUCTION_SHA256.txt` 一致（2026-10-19 10:05 SGT，VERIFIED）。所有过程说明一律用中文。

- **分支：** `codex/s4l-numerics-20261019`，自 L23 分支 `codex/l23-run1-20261019` 最新提交 efb37fc2 开出（已核实 = 远端头 `efb37fc20ef1a0b185215c553ba9a61bc871830d`；PR #35 之后有 L23 的 PR #36，按指令以 L23 最新提交为准）；draft PR 叠在 #36 上。
- **仓库：** `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4l_20261019/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4l_20261019\`。
- **范围：** 第 112 项（a 登记、b 接受 NZE 回收输出、c 部署脚本）与第 113 项（(1) 近零量清理、(2) crossover 复测）；其他发现写入报告"发现但未处理"，不修改。
- **资源规则：** 不上云、不下载、不做 365×24h；档案 A 参数不改，新档案只新增；8 个本机 56×3h 诊断运行已授权（每个 30 分钟止损、不重试）；本机单项超过 8 GiB 或 1 小时先报告。
- **许可：** 只经 `GRB_LICENSE_FILE=/home/jin/gurobi.lic` 只读引用；学术 WLS 最多 2 个会话，本步运行全部串行。
- **S4L-2 事先固定的比较标准（在看到任何结果前写入，不得修改）：** 参照 = "S4K 网络 + 档案 A"（S4K-3 已收敛）；任一组合相对参照：目标相对差 ≤ 1e-5；B16 ≤ 1e-6；每国"不互联 − 一体化"差额的变化 ≤ max(该国差额的 1 %, 0.01 bn EUR)。超出时说明来源（清理带来的实质变化，或退化方向上的顶点选择差异）。
- **停止条件：** 清理会删除有经济意义的组件或口径不清；档案 A 在任一 56×3h 运行上不再收敛且原因不明；B16 不成立且原因不明；本机单项超过 8 GiB 或 1 小时。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4L-0 | 登记（第 112 项 a、b） | 完成 | d6203004 | 注册表片段 `s4l_0`（5 行：四个运行 `SCREENING_UNVERIFIED`、NZE 回收包 78a6ea15…c33b 接受、台账补记、范围规则、问题来源）；总台账补 L23 条目（L23 交付未写台账）并标 `SCREENING_UNVERIFIED` |
| S4L-1 | 近零量清单、阈值与清理（第 113 项 (1)） | 代码与清单完成（57008244）；清理后网络已构建一次（dirty 1：同时改了档案配置），提交档案后在干净树上重建 | 57008244 | 新模块 `s4l_layers.py`：开关 `research.numerics.dust_cleanup: off（缺省，S4K 状态）\| on（主算候选）`，阈值 `dust_energy_mwh` 1000、`dust_capacity_mw` 1（PyPSA-Eur `renewable.hydro.clip_min_inflow` 1.0 MW，配置第 300 行；`existing_capacities.threshold_capacity` 10 MW 第 469 行不采用；`clip_p_max_pu` 1e-2 已由 S4A 施加）；在构建末尾（所有加组件的层之后、静态校验之前）施加。清单（S4K-3 一体化与不互联网络相同，各 818 行）：删除 602（生物质池 7 个共 2,837 MWh：SG 木薯 0.47、BN 甘蔗 71、BN 玉米 82、SG 椰子 473、TL 木材加工 664、BN 木薯 753、MY 玉米 792 MWh；零上限候选 295：地热 74、ror_new 71、offwind-dc 3、水电 61、PHS 86；小容量 offwind-dc 3（0.003–0.35 MW，601 MWh）；全零出力 offwind-dc 3；全零负荷 38；单侧燃料母线 128（褐煤 92、煤 32、油 4）及其 124 台供给机组与 4 条 `oil pool` 链路）、合并 86（`biomass-to-methanol` 97 → 11）；保留只记录：FT 链路 100、东盟外 CO₂ 储存 11、小于 1 MW 的固定塑料废弃物源 11。L23 使用情况：7 个池在一体化中都被"透支"约 0.9 MWh（年末 −0.9 MWh）；东盟外储存年末水平只有 4–95 t（一体化）/ 18–192 t（不互联），即未被使用、只剩数值噪声（但作为无上限出口选项保留）；FT 链路 100 条 `p_nom_opt` 全在 1e-3 MW 以下；死端供给机组出力恒为 0。清理后组件：母线 −128、机组 −278、链路 −90、负荷 −38、储能 −7、StorageUnit −147；存留组件逐列相同（`DUST_IMPACT_S4L1.json`）；`REQUIRED_PER_NODE` 检查跳过记录在 `removed_required_structure` 的 292 个三元组。`tests/research` 532 通过 1 跳过 |
| S4L-2 | crossover 复测（第 113 项 (2)，8 个本机 56×3h 运行） | 完成（8 个运行已用完；清理后网络的判定未完成，见下） | aa9559fe、6a2ddff9 | 新档案 `formal_barrier_crossover` = 档案 A + Gurobi `Crossover` 缺省值 −1（自动；档案 A 为 0；旧 `crossover_diagnostic` 为 1）；档案 A 未改。比较标准在运行前写入注册表 `s4l2_comparison_standard` 与本文件首部，看到结果后未改。矩阵 02:35–03:05 UTC 串行（`/home/jin/s4l2_run.sh`，`results_project/s4l/s4l2/`）：**S4K + A** 两个情景最优且与 S4K-3 逐位相同（目标值 648,262,253,996.03 / 698,679,222,969.73；124 / 117 次迭代；B16 1.1e-12 / 6.6e-13；`all_passed_solver_tolerances` 仅因 B12 为 False）；**S4K + crossover** 两个情景 `infeasible_or_unbounded`：barrier 与 A 逐位相同，crossover 推进完成（Markowitz 容差收紧，推进后 Dinf 1.6e5 / 2.8e7）后单纯形清理约 150 次迭代内报 `Infeasible or unbounded`，crossover 用时 115 / 62 s = 0.54 / 0.38 × barrier，无解返回，未调参；**第一版清理网络 + A / crossover** 四个运行 `Infeasible model`（barrier 78 / 88 次判定）。原因（只读诊断，VERIFIED）：BN、SG（及 VN）的固体生物质池总量恰好等于固定生物质终端需求（零余量），第一版规则删掉 BN 3 个、SG 2 个小池后短缺 907 / 473 MWh。**停止条件触发**（清理删除了有经济意义的组件）：规则加固定需求守护（381e39b8、2983d951），干净树重建（18207839，池余量 ≥ 0），**未再求解**（授权 8 个已用完）；需要用户决定是否授权 4 个运行 |
| S4L-3 | 部署脚本修正（第 112 项 c） | 完成 | 547bb8ac | 新目录 `p1_step4l_20261019/cloud_package/`（S4K 脚本复制后修改；S4K 目录与 56d28358 部署包未动，不重建部署包）。`run_365x24h.sh`：每个求解用 `setsid` 开独立会话 / 进程组，墙钟上限按进程组发 TERM、宽限 `GRACE_S`（30 s）后 KILL，等整个组退出再导出打包；导出前核对回执是否含 `termination_condition` / `finished_epoch`（`RECEIPT_<run>:post_solve|pre_solve`），被终止的运行记 `killed_pre_solve`；监控按进程组求 RSS，并读容器 cgroup 内存限额 / 用量（v2 `memory.max` / `memory.current`，v1 `memory.limit_in_bytes` / `memory.usage_in_bytes`），宿主机 MemAvailable 另列；`--solver-profile` 接受 `formal_barrier_crossover`；测试用环境变量 `WALL_CAP_S`、`GRACE_S`、`GUROBI_TIME_LIMIT_S`、`MONITOR_S`、`CGROUP_ROOT`（缺省为生产值）。`preflight.sh`：CPU 与内存按容器 cgroup 配额（v2 `cpu.max`、`memory.max`；v1 `cpu.cfs_quota_us`/`cpu.cfs_period_us`、`memory.limit_in_bytes`），无限额时回退宿主机值并写明；增加 `setsid` 检查；`PREFLIGHT_ONLY` 可选节。本机测试 `evidence/s4l_3/test_s4l3_scripts.sh`（假求解器 `fake_s2_solve.py`，假 cgroup 树，不用 Gurobi、不用真许可）28/28 通过：20 s 上限下整个进程组（time → python → sleep 孙进程）被终止、回执判为 pre_solve、导出与 DONE 正常；正常完成判为 post_solve；lanes3 / 未知档案 / 缺档案被拒；dry-run；cgroup v2 / v1 / 无限额四种树解析正确。`CLOUD_RESOURCE_ESTIMATE.md` 复制到 S4L 目录并追加 §21（L23 实测校正：实例速度 0.23–0.30、每次迭代 15–43 s、峰值 RSS 为中值的 0.61；同类实例校正估计；选机建议 6 条）。`make_package.sh` 复制为 S4L 版（ALLOW 正则含 s4l_*），**未运行**。另：`v5_gates.gate_b12_hash` 的覆盖值解析补 `on`（与 `s2_network.py` 一致，否则清理后网络的 B12 必不通过） |
| S4L-2 续 | 修正规则网络的 4 个运行（用户追加授权） | 完成 | 见提交记录 | `results_project/s4l/s4l2b/`（03:25–03:44 UTC，S4K 参照以符号链接接入）：**s4l_A 一体化 / 不互联最优**（136 / 138 次迭代，217 / 198 s），目标值 648,262,301,211.76 / 698,679,270,580.06（相对参照 7.3e-8 / 6.8e-8），B16 8e-12 / 2e-12，分国差额变化全为 0.0000 bn，交流电价逐母线相同——**标准全部满足**；不互联运行的 B12 不通过是配置版本假象（运行期间提交了 S4L-5 的配置键；用 2983d951 配置重算通过，`B12_RECHECK_s4l_builds_2983d951.json`）。s4l_X 两个情景 `infeasible_or_unbounded`（同 S4K 网络的失败形态，crossover 用时 0.53 / 0.28 × barrier）。零余量三国的生物质影子价格在两次解之间不同（对偶不唯一） |
| S4L-5 | 生物质零余量诊断（用户追加授权，只作诊断） | 完成 | 666e5116 + 见提交记录 | 表：BN、SG、VN 比值 1.000（规则前 5.05 / 599 / 2.85 倍），其余 0–0.89；来源 = 第 36 项 / R1.6 溢出改甲烷规则（在第 55 项 R1 内）。开关 `research.s2.industry.biomass_overflow_cap_share` 1.0 | 0.98；诊断网络只改 6 个负荷（BN −2,319、SG −630、VN −2,515,451 MWh 生物质 → 气）。两个运行最优、门槛全通过：目标 +1.83e-4 / +4.30e-4（+119 / +300 M EUR），B6 50.60（参照 50.42）；分国差额变化 PH +0.021、燃料舱 −0.037 超出容差（实质变化），VN +0.156 在容差 0.248 内；三国生物质影子价格 159–309 → 57–81（不互联 155–280 → 68–76），其余国家不变。写入报告 §10，决定事项 §9 第 4 项；未并入主算 |
| S4L-4 | 报告与证据 | 完成（含 S4L-2 续与 S4L-5） | | `S4L_REPORT.md`（摘要 6 行；§3 清单 / 阈值 / 影响；§4 矩阵结果与判定；§5 脚本改动与测试；§7 发现但未处理 10 条；§9 需要用户决定 3 项）、`S4L_EVIDENCE.json`、台账 S4L 条目、镜像、draft PR |

## 提交记录（分支 `codex/s4l-numerics-20261019`）

| 提交 | 内容 |
|---|---|
| d6203004 | S4L-0：注册表片段 `s4l_0`、台账 L23 条目、进度文件 |
| 57008244 | S4L-1：清理层 `s4l_layers.py`、开关与阈值、S4K-3 网络清单与 L23 使用情况、片段 `s4l_1`、测试 |
| aa9559fe | S4L-2 准备：档案 `formal_barrier_crossover`、片段 `s4l_2`（事先固定的比较标准）、汇总与运行脚本 |
| 6e45bc1f | S4L-1 第一版规则的构建证据（后证明该规则使 BN、SG 不可行；证据移到 `evidence/s4l_1/first_rule_infeasible/`） |
| 547bb8ac | S4L-3：S4L 版部署脚本、本机测试 28/28、资源估算 §21、`make_package.sh` S4L 版；`gate_b12_hash` 接受 `on` |
| 381e39b8 | S4L-1 修正：固定需求守护、清理后池平衡断言、片段 `s4l1_pool_fixed_demand_guard` |
| 6a2ddff9 | S4L-2 结果证据（8 个运行的回执 / 门槛 / 账本 / 日志尾、矩阵汇总）；汇总标出仅 B12 不通过 |
| 2983d951 | S4L-1 守护口径修正（只计 `biomass` 载体母线上的固定需求），清单与注册表重生成 |
| 18207839 | S4L-1 修正规则的构建证据（干净树 2983d951）、不可行原因诊断 |
| 6f56551e | S4L-4：报告、证据 JSON、台账 S4L 条目、镜像 |
| 666e5116 | S4L-5：开关 `biomass_overflow_cap_share`、各国生物质平衡表、片段 `s4l_5`、汇总扩展（额外网络臂、生物质影子价格） |
| （下一提交） | S4L-2 续与 S4L-5 结果证据、报告 §4 更新与 §10 新节、台账补记、镜像 |

## 续行点

**S4L 全部完成（S4L-0 … S4L-5，含用户追加授权的 4 + 2 个运行），停止等待审阅。** 待用户决定（报告 §9）：是否采用清理（标准已满足）；crossover 档案的用途（四个运行都失败）；第二批方案；零余量三国的生物质余量（S4L-5 诊断，未并入主算）。

## 发现但未处理（执行中随时记录，交付时写入报告）

1. **B12（配置哈希一致性）对 S4K-3 网络在 S4L 配置下必然不通过：** 矩阵中 "S4K 网络 + 档案 A" 的一体化复跑与 S4K-3 逐位相同（目标值 648,262,253,996.03、124 次迭代、同一轨迹），但 `all_passed_solver_tolerances` = False，唯一不通过的是 B12——网络元数据记录的 `research_config_sha256` 是 S4K 配置的哈希，S4L 在 `baseline.yaml` 新增 `numerics` 块与 `formal_barrier_crossover` 档案后当前配置哈希变化。这是配置版本标识，不是求解器容差；汇总脚本另给 `failed_gates_excluding_B12` 与 `all_passed_solver_tolerances_excl_B12`。清理后网络（在 S4L 配置下构建）的 B12 通过（已核实）。
2. **`gate_b12_hash` 与 `s2_network.py` 的布尔覆盖值解析原本都不接受 `on`**（YAML 1.1 把 `on`/`off` 读成布尔）：`--override numerics.dust_cleanup=on` 在 `s2_network.py` 中若按旧规则会得到 False。两处都已补 `on`（S4L-1、S4L-3 提交）；此前的覆盖键都是字符串或数值，不受影响。
3. 11 台 `plastic waste source` 固定机组的 p_nom 为 0.06–0.99 MW（外生数据，合计 5.03 MW、44 GWh/a）：低于 1 MW 但不是候选，未删除，只记录。
4. 4 个只有 `oil pool <node>` 链路一端相连的节点油母线（MY_Peninsular22 0、PH_Luzon9 0、PH_Visayas10 0、TH21 0：换流站辅助节点，没有负荷）：S4I R1 把它们计入 128 个单侧燃料母线；清理把母线和这 4 条流量恒为零的链路一起删除。

## 用户中途指示

1. 2026-10-19（S4L 报告交付后）："授权按修正后的清理规则（保护服务固定需求的生物质池）重跑清理后网络的 4 个运行（档案 A 与 crossover 档案 × 一体化 / 不互联，56×3h，各 30 分钟止损，不重试）。另外授权增加一组诊断（同属 S4L，只作诊断）：1. 列出各国固体生物质：本国潜力、固定终端需求、两者之比；标出比值 ≥ 0.999 的国家（需求恰好等于潜力），并说明这是否来自第 55 项'超出潜力部分改由甲烷供给'的规则。2. 构建一个诊断网络：在 S4K 网络上，对比值 ≥ 0.999 的国家，把固定生物质需求设为潜力的 98 %，差额 2 % 按第 55 项同一规则改由甲烷母线供给（只改这一处，不清理其他近零量）。3. 用档案 A 跑该诊断网络的一体化与不互联（56×3h，各 30 分钟止损，不重试），报告状态、门槛、目标值、生物质影子价格，以及与 S4K 参照的分国差额对比（同一事先固定标准）。4. 结果写入 S4L 报告单独一节，并列为需要用户决定的事项；不要把它并入主算。"
   - 执行：S4L-2 续（`/home/jin/s4l2b_run.sh`，`results_project/s4l/s4l2b/`，S4K 参照运行以符号链接接入、不重跑）；S4L-5（`scripts_project/s4l_5_data.py`、开关 `research.s2.industry.biomass_overflow_cap_share` 1.0 | 0.98、`/home/jin/s4l5_build.sh`、`/home/jin/s4l5_run.sh`，`results_project/s4l/s4l5/`）。规则来源：第 36 项 / R1.6（在第 55 项 R1 工业载体结构内），`biomass_overflow_to_methane: true`。
