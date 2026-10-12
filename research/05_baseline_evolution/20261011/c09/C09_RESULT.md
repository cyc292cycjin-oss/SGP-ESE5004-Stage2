# C09 精确分解后主 LP 单次求解结果

**判定：R1 — C09_DAILY_BASELINE_ACCEPTED（仅限 365 日日诊断，不等于 Gate6/2920 通过）。** 主 LP 原生返回 Status 2、SolCount 1；与块的精确解合并后，原 V4 的 10 项门槛全部通过。本地用冻结 CSC 独立复核，结果与云端逐项一致。本轮优化调用恰好 1 次，没有重试；V4、Scheme A、C01R、D/R、成本及科学约束均未改动。G6-05 仍为 PAUSED_BY_USER。

证据等级：VERIFIED（实际回执或数组计算）、EXACT（有理数逐项核验）、INFERENCE（机制解释）、PROPOSED（未执行）。

## 1. 执行记录

| 步骤 | 时间（UTC，2026-10-12） | 结果 |
|---|---|---|
| 本地发布包 SHA256 | deploy 之前 | `79d27d4f…409e6`，6,363,067 字节，与 RELEASE_DELIVERY 一致 |
| `deploy` | 18:49:32 | `C09_RELEASE_SHA_VERIFIED`；清单 SHA `779b8e25…77466`，35 个文件；求解调用 0 |
| 用户确认 | — | 用户在对话中回复"开始" |
| `start`（唯一一次） | 18:51:16 | run_id `c09_daily122_20261012T185116Z_b867e3d3`，supervisor 后台运行，`max_optimize_calls=1` |
| 进入 NATIVE | 18:51:29 | 原生加载与逐值回读 2.455 秒，EXACT_READBACK_PASS |
| GRBoptimize 返回 | 18:57:48 | 返回码 0，调用计数 1，墙钟 378.51 秒 |
| 合并、V4 后处理完成 | 18:59:24 | PHASE=DONE，worker、supervisor、guard 均退出，残留进程为空 |
| 云端封存、归档 | 18:59:31 | seal guard 状态 SEALED，退出码 0 |
| `observe` | 18:51:42 至 18:59:44 | 共 4 次只读快照，均保存在 `monitor_snapshots/` |
| `fetch` 与本地核验 | 19:00:44 | 归档 SHA 与云端一致；解压后逐文件 SHA 通过 |

说明：本机 `python` 是 Windows 应用商店的占位程序，第一次执行 `deploy` 直接以退出码 49 结束，没有连接远端，也没有生成回执。之后所有命令改用 `C:\Users\20122\miniconda3\python.exe`（3.14.7）执行，脚本和参数均未改动。

## 2. 求解终态（VERIFIED）

| 指标 | C09 |
|---|---|
| Status / SolCount | 2 / 1 |
| Barrier 迭代 | 145（Barrier 本身以 "Sub-optimal termination" 结束，目标 4.28014103e11） |
| Simplex 迭代（IterCount） | 481,420 |
| Runtime | 378.51 秒（日志 378.47 秒，175.06 work units） |
| 最终目标 ObjVal | 428,014,041,779.74445 EUR |
| ConstrVio / BoundVio / DualVio / ComplVio | 1.544e−10 / 0 / 1.208e−7 / 0 |
| 预处理后规模 | 1,019,352 行 / 788,160 列 / 2,926,608 非零（C07A/B：1,060,244 / 925,765 / 3,201,818） |
| 参数 | 154 项；相对 C06 只有 Crossover 0→−1（C09_PARAMETER_DIFF：unauthorized 为空） |

Crossover 过程：DPush 从 769,230 降到 0（DInf 始终为 0），PPush 从 71,966 降到 0；push 阶段结束时 Pinf 为 0、Dinf 为 2,316.57。随后 simplex cleanup 从第 478,218 次迭代做到第 481,420 次，Dinf 降到 0，最终 "Optimal objective 4.280140418e+11"。

Barrier 的 sub-optimal 结束本身不算终态。最终 Status 2 来自 Crossover 和 cleanup 之后的基解，V4 验收的对象就是这组返回向量。

主 LP 身份：1,565,533 列、3,839,021 行、7,868,836 非零，是冻结 C03 日 CSC 的纯行列限制，数值逐位不变。身份 SHA 为 `c378716f…afdd3b`，源清单 SHA 为 `f70b2dc2…302a70`。本地重新推导的 10 项数组 SHA 与云端回执全部一致。

## 3. 原 V4 全部门槛

| 原 V4 门槛 | C09 云端 | 本地独立复核 |
|---|---|---|
| native_optimal | PASS | Status 2 |
| complete_primal_dual | PASS | X/Pi/RC 完整，SHA 一致 |
| full_matrix_and_column_bounds | PASS | 行失败 0、列失败 0 |
| independent_KKT | PASS | 原 V4 代数重算，数值逐项相同 |
| physical_dynamics | PASS | 1,849 项物理检查全部 PASS |
| 807_inventory | PASS | 807 个账户失败 0 |
| 385_obligations | PASS | 385 个义务组失败 0 |
| FOM_once | PASS | — |
| NetCDF_exact_readback | PASS | EXACT_SEMANTIC_ROUNDTRIP，18 张动态表 |
| daily_binding | PASS | — |

块门槛（C09_BLOCK_VERIFICATION，运行时与本地各算一次）：块解耦、跨块元素 0、块成本为 0；块原始解残差最大 1.106e−16（LP 单位），块行集合与块列触及的行完全一致。合并检查：主向量逐位拷贝，块 X 等于预构造原始解，块 Pi 与块 RC 全为 0。**判定 R1 的全部条件成立，R4、R5 不触发。**

V4 KKT 数值（原单位，经冻结 D/R 映射）：

| 指标 | 值 |
|---|---|
| 行最大违约 | 2.384e−7 |
| 列最大违约 | 0 |
| stationarity 最大归一化值 | 5.227e−14（门槛 1e−6） |
| 对偶符号最大归一化误差 | 1.208e−7（门槛 1e−6），失败 0 |
| 互补 L1 / 最大互补项 | 3.170e−5 / 1.213e−6 EUR |
| 加权 stationarity L1 | 1.541e−4 EUR |
| 原对偶目标 | 428,014,041,780.10205 / 428,014,041,780.1019 EUR |
| 绝对差 / 相对差 | 1.22e−4 EUR / 2.85e−16 |
| formal_exact_lower_bound | false：这是浮点认证，不是严格最优区间 |

本地复核（`C09_LOCAL_V4_RECHECK.json`，WSL pypsa-earth 环境，numpy 1.26.4 / scipy 1.15.2，与云端版本一致，耗时 11 秒，不调用求解器）还单独用 numpy 直接计算了主 LP 在原生坐标下的残差：行违约最大 2.384e−7，列违约 0，stationarity 绝对最大 3.463e−9，cᵀx+offset = 428,014,041,780.10205。

## 4. 与 C06、C07A、C07B 对照

### 4.1 求解

| 指标 | C06 | C07A | C07B | C09 |
|---|---|---|---|---|
| 模型 | 完整日 LP | 完整日 LP（C07 D/R） | 完整日 LP（C07 D/R） | 只求主 LP；块用精确解 |
| 算法（相对 C06） | 基准 | 相同 | Crossover 0→−1 | Crossover 0→−1 |
| Status / SolCount | 2 / 1 | 2 / 1 | 3 / 0 | **2 / 1** |
| Barrier 迭代 | 143 | 153 | 153 | 145 |
| Simplex 迭代 | 0 | 0 | 511,564 | 481,420 |
| Runtime 秒 | 282.18 | 281.13 | 343.26 | 378.51 |
| Push 结束时 Dinf | — | — | 11.263 | 2,316.57 |
| 最终日志 | Optimal | Optimal | Infeasible model | Optimal |

C08 已经核实，C07 改变的 D/R 全部位于块内、块外为 0。因此 C09 交给求解器的主 LP，与 C07B 中的主 LP 系数相同；两者的区别只是去掉了零成本解耦块。

### 4.2 原 V4 指标

| 原单位 / 原 V4 指标 | C06 | C07A | C07B | C09 |
|---|---|---|---|---|
| 矩阵失败行 | 243 | 1 | 无解 | **0** |
| 矩阵最大行违约（C06/C07A 为库存行） | 54.83 MWh | 0.008420 MWh | 无解 | 2.38e−7 |
| 列界失败 | 0 | 0 | 无解 | 0 |
| 资源失败账户 /807 | 85 | 0 | 无解 | 0 |
| 义务失败组 /385 | 0 | 0 | 无解 | 0 |
| 年度正向账户超用 MWh | 307.64 | 0.008435 | 无解 | 8.17e−10 |
| 年度少用绝对量 MWh | 304.62 | 0.007736 | 无解 | 2.87e−7 |
| 最大账户误差 / 自身预算 | 见 C06 原表 | 0.0190 | 无解 | 1.34e−7 |
| stationarity 失败列 | 3,336 | 3,353 | 无解 | **0** |
| stationarity 最大归一化值 | 2.757e−5 | 2.280e−5 | 无解 | 5.23e−14 |
| 对偶符号失败（含自由 RC） | 0 | 12,045 | 无解 | **0** |
| 互补 L1 EUR | 29.53 | 30.35 | 无解 | 3.17e−5 |
| 最大互补项 EUR | 1.058 | 13.20 | 无解 | 1.21e−6 |
| 加权 stationarity L1 EUR | 120,113 | 118,540 | 无解 | 1.54e−4 |
| 原对偶绝对差 EUR | 117,699 | 116,267 | 无解 | 1.22e−4 |
| 相对目标差 | 2.75e−7 | 2.72e−7 | 无解 | 2.85e−16 |
| 独立 KKT | FAIL | FAIL | 无解 | **PASS** |

按组内账户数（1/2/3/4 个账户的组分别为 118/156/67/44 组）统计，C09 的失败组和失败账户均为 0。

### 4.3 成本（未合格候选值，不是正式系统成本）

| 指标 | C07A | C09 |
|---|---|---|
| 已知范围原科学成本 EUR | 427,765,321,341.48 | 427,765,321,345.58 |
| V3 复算目标 EUR | 428,014,092,431.82 | 428,014,041,780.10 |
| 扰动贡献 EUR | 248,771,090.34 | 248,720,434.52 |

两者的 `original_objective_optimality` 均为 NOT_PROVEN，`FullSystemCostComplete` 均为 false。C09 的 V3 目标比 C07A 低 50,651.72 EUR（相对 1.18e−7）。

## 5. 解释

- **VERIFIED：** 同一组 154 项参数（含 Crossover=−1）下，去掉零成本解耦块后，主 LP 返回 Status 2，原 V4 全部通过；而 C07B 带着这个块，返回 Status 3、SolCount 0。
- **VERIFIED：** C06、C07A 遗留的 stationarity 失败（C06 为 3,336 列；C07A 为 3,353 列，其中 Line-s 3,024、Link-p 329）在 C09 中为 0。C08 已核实这些失败全部位于块外。所以这次清除它们的，是 Crossover 返回的基解，而不是分解本身。T10 的试运行也表明，单靠分解只能消除块内失败，stationarity 仍有 3,353 列。
- **VERIFIED：** 807/385 的结果来自预先构造的块原始解（C08 的精确有理数可行性证书，运行时又复核了一次），与求解器无关。所以这两项门槛通过，是分解实现正确的直接后果，并不说明求解器的数值质量。
- **INFERENCE：** 结果与"块导致 C07B 返回 Status 3"的推断一致，但不构成证明。这只是一次运行；预处理后规模不同（788,160 列对 925,765 列），Barrier 路径也不同（C09 为 sub-optimal 结束，C07B 为 optimal 结束）；C07B 的 Status 3 也没有严格的 Farkas 证书。
- **INFERENCE：** C07A 的数值对偶目标（428,014,208,698.93 EUR）高于 C09 的原始目标（428,014,041,780.10 EUR），差 166,918.8 EUR。如果 C07A 的对偶可行，它的对偶目标应是下界；这与 C07A 存在 12,045 项对偶符号失败和巨大块对偶相符。C09 本身是浮点认证，不是严格最优区间，因此这一点只作为旁证。

## 6. 资源与备份

| 指标 | C07A | C07B | C09 |
|---|---|---|---|
| 进程树 RSS 采样峰值 GiB | 4.045 | 4.385 | 3.530 |
| cgroup 最小余量 GiB | 82.79 | 81.82 | 82.64 |
| 磁盘最小余量 GiB | 26.22 | 26.03 | 25.48 |
| 资源采样数 | — | — | 1,906 |
| 保护触发 | 无 | 无 | 无 |
| 启动到归档完成秒 | — | — | 494.36 |

cgroup 历史峰值（7.36 GiB）包含同一容器内的其他进程和缓存，不能当作 Gurobi 独占的峰值。原生求解上限 3600 秒、整个 Run 上限 7200 秒都没有用满；没有发生保护停止、续期或第二次调用。

| 项目 | 值 |
|---|---|
| 云端归档 | `/root/autodl-tmp/SGP/incoming/c09_exact_decomposition_122_20261013_779b8e25/c09_daily122_20261012T185116Z_b867e3d3_NEW_RESULTS.tar.gz` |
| 归档字节 / SHA256 | 59,076,784 / `6209efc54bb59d70c9e6cb6042abc043ff38d369f0b2c4374a55d6bc1b9d1104` |
| BACKUP_INDEX SHA256 | `e60becbd17808a8a7f2b1ea5953f43fb815fd3fd53e84e7f482a19ce285f3304`（60 个文件，545,958,882 字节） |
| 本地原件 | `D:\ResearchWorkspaces\ASEAN\outputs\c09_daily_diagnostic\c09_daily122_20261012T185116Z_b867e3d3\cloud_run` |
| 本地状态 | **LOCAL_BACKUP_SHA_VERIFIED**：整包 SHA、gzip CRC、tar 路径安全检查，60 个文件逐个 SHA；17,369 项不可变引用与 C04 已核验索引、C09 发布包 SOURCE_BINDING 及清单一致 |
| 云端原件 | 保留，没有删除或改写；封存目录中的历史字段 `LOCAL_SYNC_PENDING` 不改写，当前状态以本地回执为准 |
| 122 实例 | 仍在运行（开机计费），本轮没有关机或释放 |

## 7. 下一步（按预先写定的 R1）

R1 对应的下一步是：用同一分解准备 D 阶段，需要另行授权。**本轮不执行。** 2920 时段、Gate6、Integrated/Disconnected 情景都未授权，G6-05 仍暂停。本轮已经停止，等待用户审阅。

## 8. 文件

- 回执：`DEPLOYMENT_RECEIPT.json`、`START_ATTEMPT.json`、`START_STDOUT.txt`、`LAUNCH_RECEIPT.json`、`FETCH_WINDOW.json`、`FETCH_RECEIPT.json`、`C09_LOCAL_BACKUP_RECEIPT.json`、`monitor_snapshots/`
- 核验：`C09_LOCAL_V4_RECHECK.json`（本地独立复核）、`C09_COMPARISON.json`（账户、组与资源统计）
- 方法：`methods/c09_local_receive.py`、`methods/c09_local_v4_recheck.py`、`methods/c09_compare.py`，以及发布包源码副本 `methods/release_c09_*.py`
- 云端轻量证据（日志已脱敏）：Git 中的 `evidence/run/`
