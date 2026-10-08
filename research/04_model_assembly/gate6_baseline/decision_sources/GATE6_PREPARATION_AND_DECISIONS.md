# Gate6 preparation — NOT AUTHORIZED

本轮只做文件级清点、代码读取和解析估计。GATE6_INPUT_AND_SCALE_INVENTORY.json 记录实际路径、大小、SHA 和依赖关系；没有组装优化矩阵。

## 已核实的全年输入

必须直接恢复 /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc。
大小 72,082,285 字节；SHA256=238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d。
原始 2013-01-01 00:00 至 2013-12-31 21:00，2920×3h；objective/generators/stores 三套权重均为 3，总计 8760h。100 节点、171 账户、1737 Loads、187400.4 MW 存量、807 pending、200 null 政策权重均匹配冻结状态。它是完整未求解输入。

现有云端尚无该 3h 文件（本次只读实测）。下一阶段若获部署许可，需要单独传此文件及其 FULLSC_ASSEMBLY_V1_NETWORK_MANIFEST.json，逐文件核 SHA；不能用 Gate5 的 365 日输出复制/插值，也不能默认固定 p_nom_opt 或调度为新容量/运行边界。

直接读取依赖：该完整 NetCDF；final_allocation/allocation_manifest.json 和 allocations.npz；research_inputs/assembly_v1/registry.json、sources/BASE_RECONSTRUCTION.json（固定资源原单位审计使用）；冻结代码与环境。清单还包含 22 个经 AST 追踪的 Gate5 参考项目模块，总计 32 条文件记录。该参考闭包用于 3h 适配审查，不冒充已经完成的 Gate6 执行依赖锁。

若未来需要追溯重建，workflow/research_final_assembly.smk 明确串联 final allocation → final assets → complete unsolved；路径覆盖使用 /mnt/d/ResearchWorkspaces/ASEAN/workspace_tools/final_assembly_paths.D.json。该链还依赖已冻结 registry/pins、electric base/stock/integration contract、carrier fragment/carbon map、价格层和 allocation。现有 3h 成品 SHA 已匹配，本轮不重建，也不从 C 盘旧工作区启动。

## 与 Gate5 的差别和工程缺口

| 项目 | Gate5 已验收 | Gate6 待准备 |
|---|---|---|
| 时间分辨率 | 365×24h，3h 输入按 8 点日均聚合 | 原 2920×3h，保留逐时波动 |
| 年权重 | 8760h | 8760h |
| 输入身份 | 7a07a0ec… 日聚合 | 238262c9… 原全年 |
| 容量/运行结果 | 独立验证结果 | 从未求解输入创建，不能继承 Gate5 结果边界 |
| 政策 | 工程验证 OFF | Gate6 具体用途/政策配置和正式核心实验政策均需明确，不能由 Gate5 推定 |
| 执行入口 | run_gate5_stable_inventory.py，硬编码 365、daily SHA | 目前不存在可授权的 Gate6 runner；需独立适配/测试/冻结 |

inventory_audit.py 目前硬编码 series.reshape(365,8).mean、日数据比较、日输入 SHA 及 (2×2920−1)+(4K−2)+8+(2×365−1) 源运算舍入界。Gate6 必须针对真实 3h 源读取和 2920 步状态运算重新证明预先声明的舍入界；不得改 RHS、数量或放宽 solver tolerance，也不能把日尺度 FORMULATION_MAPPING_AND_ROUNDING_AUDIT 原样宣称为全年证书。

gate5_cloud_preflight/scientific_identity、动态检查中的 Gate5 policy-OFF 断言、输入 SHA/快照数、run id/一次授权机制、资源预算、精确传输保真和新收尾入口需逐项审查并建立 Gate6 门禁。原 19 项代码哈希绑定和所有 Gate5 历史证据保持。未来新 runner 先通过无求解的 3h 小规模正反例、precision/lifecycle/qualification/export 测试，明确科学配置和预算后才可考虑授权，不在本轮写入可运行 Gate6 入口。

环境继续使用冻结 Python 3.11.13 / PyPSA 0.30.3 / Linopy 0.5.5 / HiGHS 1.11.0；沿用精确 Linux spec 和既有 538 conda/284 Python 分发校验记录，不复制环境目录、不升级依赖。候选数值路径继续 float64、PROJECT_STREAMED_FLOAT64、D/R 逆映射、一次 getSolution、IPM/标准 crossover/presolve、2 threads 与原 tolerance。任何正式变化需另行决定。

## 规模与预算：分析参考，不是实测 Gate6

现有 Gate5 标签/块证据给出：静态变量 4505，逐时活动变量 6700/点；静态约束 5138，逐时约束 16540/点。
在结构和活动 mask 相同的假设下：变量≈19,568,505，约束≈48,301,938；变量标签槽 19,577,265。非零元仅作 8×线性参考≈91,227,968，不是精确数量或保证上界。3h inflow/spill mask、时序首末项、年汇总及政策选择可改变实际数量。

当前 cgroup 上限 90.000 GiB、有效可用 83.371 GiB、CPU quota 25 cores、数据盘可用 43.900 GiB；观测时间 2026-10-08T00:14:34.343355+00:00（UTC；北京时间加 8 小时）。不把宿主机 MemTotal 当成本实例容量。

Gate5 已实测峰值 7.349 GiB；乘 8 的粗线性参考 58.794 GiB。因子分解填充、IPM 迭代、crossover 和同时驻留对象不保证线性，90 GiB 并未证明足够。原生/映射磁盘的 8×参考约 1.775 GiB，另需全年输入、结果、日志、临时数据及失败保留空间。

待人工接受的 Gate6 专用预算候选：启动有效余量至少 83 GiB；进程树 RSS 上限 75 GiB；cgroup 余量至少 8 GiB；数据盘启动余量至少 30 GiB。数值仅为有监控、可中止的方案，不是成功保证，尚未配置或批准，未改动任何 Gate5 门槛。真正获准构建时仍需分阶段记录 build/transfer/solve/postsolve/export，无法满足新门禁即停止，不靠 swap 或下调门槛硬跑。

Gate5 HiGHS 6440.59s；8×仅为约 14.31h 的参考，无法预测全年收敛。候选时间上限：solver 24h / wall 30h，须先批准实例时长和守卫；本轮未应用。所有新 run、monitor、mmap、日志、退出码和 manifest 应位于 /root/autodl-tmp/SGP/runs/<unique_gate6_id>，保持独立会话、非覆盖目录和失败留存；返回 D 盘。不存在本轮启动命令或新授权。

## 最少待决事项

| 决定 | 已批准/已验证事实 | 仍待人工确认 |
|---|---|---|
| 正式核心政策与 Gate6 用途 | Gate5 OFF 仅是工程验证；既有 2025→2050 轨迹为 1000/820/640/460/280/100 MtCO2/year | 正式核心是否启用电力预算；下一次 Gate6 是 OFF 的全年工程验收，还是明确正式配置的验收。OFF 也需明确科学选择 |
| 预算数值及统计范围 | 2050 冻结数值 100,000,000 tCO2/year，8760h 缩放；PolicyCO2_Power 与全系统物理排放分开；不改轨迹 | 冻结完整 Power 归属范围/接受的事件系数。不能用全系统 atmospheric Store 或 primary-energy 汇总替代；预算值已有来源，不默认另设新值 |
| 200 项 SMR/SMR-CC | 物理来源映射保留，policy_weight 均为 null；现有启用函数会拒绝 pending attribution | 明确有证据的共同用途归属/追踪方法并验证；不猜 H2 未来用途比例，不用零权重代替未知 |
| 正式报告与场景比较 | 已计价目标含已知 FOM 一次；807 项未知固定价/排放仍 null；成本/全系统排放完整性均 false | 接受正式 priced-subset、KnownFixedTerms、PendingFixedTerms 和物理排放披露口径；Integrated/Disconnected 比较前验证来源 ID、商品、数量、权重、独占用途、价格边界及方向 hooks 一致，否则不得假定固定项抵消 |

依据：既有 PHASE5_SCIENCE_CONFIG_FREEZE.md、FORMAL_OBJECTIVE_REPORTING_CONTRACT.md、POLICY_ACTIVATION_READINESS.md、carbon_architecture.py、Gate3 预算轨迹记录及已接受的 ASSEMBLY_V1_FINAL_DECISIONS.json。历史文件中的旧 Gate5 失败背景不代表当前 Gate5 状态，但其未决科学边界没有被工程成功自动批准。

需求增长、187400.4 MW 合格存量、最大重叠掺混等已冻结决定继续保留；本轮未发现实际矛盾，不重新开放这些问题。Gate6 缺口是：云端原全年输入同步、新 3h 工程门禁/runner/舍入界、资源与时间预算批准、上述最少科学决定、一次新的明确求解授权。Gate6、Integrated/Disconnected、正式 Phase5 均未运行。
