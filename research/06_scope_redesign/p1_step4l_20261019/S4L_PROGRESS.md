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
| S4L-1 | 近零量清单、阈值与清理（第 113 项 (1)） | 代码与清单完成（57008244）；清理后网络已构建一次（dirty 1：同时改了档案配置），提交档案后在干净树上重建 | 57008244 | 新模块 `s4l_layers.py`：开关 `research.numerics.dust_cleanup: off（缺省，S4K 状态）\| on（主算候选）`，阈值 `dust_energy_mwh` 1000、`dust_capacity_mw` 1（PyPSA-Eur `renewable.hydro.clip_min_inflow` 1.0 MW，配置第 300 行；`existing_capacities.threshold_capacity` 10 MW 第 469 行不采用；`clip_p_max_pu` 1e-2 已由 S4A 施加）；在构建末尾（所有加组件的层之后、静态校验之前）施加。清单（S4K-3 一体化与不互联网络相同，各 818 行）：删除 602（生物质池 7 个共 2,837 MWh：SG 木薯 0.47、BN 甘蔗 71、BN 玉米 82、SG 椰子 473、TL 木材加工 664、BN 木薯 753、MY 玉米 792 MWh；零上限候选 295：地热 74、ror_new 71、offwind-dc 3、水电 61、PHS 86；小容量 offwind-dc 3（0.003–0.35 MW，601 MWh）；全零出力 offwind-dc 3；全零负荷 38；单侧燃料母线 128（褐煤 92、煤 32、油 4）及其 124 台供给机组与 4 条 `oil pool` 链路）、合并 86（`biomass-to-methanol` 97 → 11）；保留只记录：FT 链路 100、东盟外 CO₂ 储存 11、小于 1 MW 的固定塑料废弃物源 11。L23 使用情况：7 个池在一体化中都被"透支"约 0.9 MWh（年末 −0.9 MWh）；东盟外储存全部在用（4–192 Mt）；FT 链路 100 条 `p_nom_opt` 全在 1e-3 MW 以下；死端供给机组出力恒为 0。清理后组件：母线 −128、机组 −278、链路 −90、负荷 −38、储能 −7、StorageUnit −147；存留组件逐列相同（`DUST_IMPACT_S4L1.json`）；`REQUIRED_PER_NODE` 检查跳过记录在 `removed_required_structure` 的 292 个三元组。`tests/research` 532 通过 1 跳过 |
| S4L-2 | crossover 复测（第 113 项 (2)，8 个本机 56×3h 运行） | 档案与标准已登记（片段 `s4l_2`），运行待开始 | | 新档案 `formal_barrier_crossover` = 档案 A + Gurobi `Crossover` 缺省值 −1（自动；档案 A 为 0；旧 `crossover_diagnostic` 为 1）；档案 A 未改。比较标准在运行前写入注册表 `s4l2_comparison_standard` 与本文件首部 |
| S4L-3 | 部署脚本修正（第 112 项 c） | 待开始 | | |
| S4L-4 | 报告与证据 | 待开始 | | |

## 提交记录（分支 `codex/s4l-numerics-20261019`）

| 提交 | 内容 |
|---|---|
| d6203004 | S4L-0：注册表片段 `s4l_0`、台账 L23 条目、进度文件 |
| 57008244 | S4L-1：清理层 `s4l_layers.py`、开关与阈值、S4K-3 网络清单与 L23 使用情况、片段 `s4l_1`、测试 |
| （下一提交） | S4L-2 准备：档案 `formal_barrier_crossover`、片段 `s4l_2`（事先固定的比较标准）、汇总与运行脚本 |

## 续行点

S4L-2 准备已提交后：在干净树上重建 S4L-1 两个网络（`/home/jin/s4l1_build.sh`，约 2 分钟），提交构建证据；然后启动 `/home/jin/s4l2_run.sh`（8 个运行，串行，预计 45–70 分钟），结果在 `results_project/s4l/s4l2/`。

## 发现但未处理（执行中随时记录，交付时写入报告）

（暂无）

## 用户中途指示

（暂无）
