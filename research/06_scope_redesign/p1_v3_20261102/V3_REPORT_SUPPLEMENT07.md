# V3 补充 07 报告：日聚合改为上游约定（第 182 项）——本机部分

依据：`V3_REVIEW_DECISIONS_EVDIAG.md` 第 2.1 节（没有 SHA256 登记文件，本机计算 `3db56b5491ce88c5b565bf3e43b2f56ab72287c165b1d1134dae53b291a9d37f`，副本已放进本目录）。分支 `codex/v3-20261102`，起点 `2548123a`。**本机部分完成，停在第 2.2 节之前：未连 AutoDL，未上传，本机 Gurobi 0 次。** 第 2.2 节第 10 条要求的云端内容（运行状态、新旧对照、修订桥、EV 轨迹、预测对照、费用）在用户开机授权、重跑完成后补进第 8 节。

结论等级：VERIFIED = 文件字节、网络数组或回执；EXACT = 逐位相等或代数推出；INFERENCE = 机制解释或推算；PROPOSED = 未执行。

## 0. 结论（本机部分）

1. **规则先行：** `V3_RULES.md` 第 11 节在改代码、构建之前提交（`38a1ad67`）：日分辨率聚合对 Store 的 `e_min_pu` 取日最大、`e_max_pu` 取日最小，其余时变输入仍取精确平均，依据上游 `average_every_nhours`；写明这是筛查之后、依诊断作出的修正，不改阈值与已登记的预测。
2. **代码：** 只改 `scripts_project/daily_resolution.py`（`7aec953e`）；年积分断言只对这两项豁免。新增 4 项测试（`DailyStoreBounds`）：EV 型电池日下限为 0.8；两项与上游函数逐值相同；其余全部时变序列、静态表、元数据与修改前逐位相同；没有时变储能边界的网络，导出的 netCDF 逐字节相同。（VERIFIED）
3. **重建核对全部通过，没有触发停止条件**（VERIFIED，`evidence/dmax/REBUILD_CHECK.json`）：
   - 2920×3h 一体化 `1bddacb7…`、`no_new_xb` `b262f6aa…`，365×24h 修订桥 V4 `910c037f…`、V5 `20821ba9…`：与登记值**逐字节相同**。
   - V1 `a0273602…`、V2 `f9f4057b…`、V3 `f889c3ba…`：netCDF 全部变量按位比较，**只有 `stores_t_e_min_pu` 一个变量不同**，96 列都是 EV 电池，365 天全部由 0.1 变为 0.8；V1、V2 的新值逐值等于 3 小时网络同一电池的逐日最大值。
   - V2 的元数据另有一处变化：`research_variant.base.sha256`（派生时记录的母网络 SHA256）由 `330e1d31…` 变为新 V1 的 `a0273602…`。这是派生规则的必然结果，审阅决定没有写到；我在构建前把它写进了规则第 11 节，核对时要求它是唯一的元数据变化且值等于新 V1，结果符合。**请审阅端确认这一点可以接受。**
4. **预测在任何新网络求解之前提交并推送**（`fbdf2c2e`，`RUN_PLAN_V3.md` 第 23.3 节）：B6 14.25–14.80 bn（上升较可能），V5 − V1 1.14–3.61 bn（最可能 1.6–2.1），V3 − V2 1.05–1.60 bn（上升较可能），Owen 12 个参与者符号与第一次筛查相同，EV 电池高于下限的电量之和 ≤ 1.587 TWh。
5. **HiGHS 日分辨率路径检查通过**（第 4 节）：新 V1、V2、V3 截短 8 天全链路走通，三次 optimal；EV 早晨下限在解中全部成立，约一半电池·日正好压在 0.8 上；B16、Owen 恒等式 1e-13 量级，右端项未归属 0 行。一体化那次 GATES_V6 因按构建回执比对了 2920×3h 网络的 SHA256 而 `NOT_ACCEPTED`，按 365×24h 登记值重评为 `ACCEPTED_LAYER2`；B8 只有 Transport 的截短假象，数值可精确推出。
6. **部署包已打好、未上传**（第 5 节）：`screen_package_v3_dmax/`，23 个文件 185,237,457 B，`SHA256SUMS` 的 SHA256 `cce1444c…`，`PACKAGE_MANIFEST.json` `4a46fba9…`；干跑与预检（`licence`、`resources` 除外）通过。
7. **未做（按指令停下）：** 第 2.2 节云端重跑。需要用户开机、在会话中给出连接方式并写"授权 V3 重跑"，见第 7 节。

## 1. 规则与代码

| 项 | 内容 | 提交 |
|---|---|---|
| 规则 | `V3_RULES.md` 第 11 节：Store `e_min_pu` 日最大、`e_max_pu` 日最小，其余精确平均；年积分断言只对这两项豁免；适用范围（只有 96 个 EV 电池有时变储能边界）；构建前写定的预期（哪些网络逐字节相同、V1–V3 只许哪些差异、V2 元数据那一处）；网络元数据 `temporal_reduction` 文字不改及理由 | `38a1ad67`（构建前） |
| 代码 | `daily_resolution.py`：`STORE_BOUNDS = {e_min_pu: max, e_max_pu: min}`，只对 `stores`；`extreme()` 从 8 个值中取一个，不舍入；分项记录写明取最大 / 最小 | `7aec953e` |
| 测试 | `tests/research/test_s1_adapter_daily_v5.py` 类 `DailyStoreBounds` 4 项；该文件 16 项全过 | `7aec953e` |
| 测试 | `tests/research/test_v3_runners.py` 加 2 项：新定义文件与运行计划一致；运行器替身按 V1 → V2 → V3 跑完，修订桥只有 v2 → V1 一步 | `fbdf2c2e` |

上游依据（本机代码，VERIFIED）：`scripts/prepare_sector_network.py` 第 2942 行 `average_every_nhours`，第 2969–2972 行 `stores` 的 `e_max_pu` 取 `min`、`e_min_pu` 取 `max`，其余取 `mean`。

**一个有意保留的不一致：** 网络元数据 `temporal_reduction` 仍写"S1 exact daily mean of frozen 2920x3h inputs (C02 arithmetic)"。改它会让修订桥不再逐字节相同，也会给 V1–V3 多出 EV 电池以外的差异，与审阅决定的两条核对要求冲突。聚合方式以规则第 11 节为准；需要时可在以后统一改元数据（那时所有 365×24h 网络都要重新登记）。

## 2. 重建与核对

构建提交 `7aec953e`，输出 `results_project/v3/builds_dmax`（313 MB），脚本 `scripts/wsl_v3d/build_s7.sh`，构建 5 次共约 6 分钟。

| 网络 | 字节 | SHA256 | 结果 |
|---|---:|---|---|
| `integrated_2920_3h` | 72,050,070 | `1bddacb7…` | 逐字节相同（= 第 21.1 节登记值） |
| `no_new_xb_2920_3h` | 71,411,730 | `b262f6aa…` | 逐字节相同 |
| `bridge_160_162_365_24h`（V4） | 33,332,895 | `910c037f…` | 逐字节相同 |
| `bridge_160_164_365_24h`（V5） | 32,680,839 | `20821ba9…` | 逐字节相同 |
| `integrated_365_24h`（V1） | 33,541,263 | `a0273602016003fc4318cdd993b69716772c700cd2f9d079059fabcdde099c8b` | 只有 96 个 EV 电池的 `e_min_pu` |
| `no_new_xb_365_24h`（V2） | 32,902,923 | `f9f4057b9972b2d7c8ab8b574c2d90c306000ae44eb2697ad80a6c0dc3554861` | 同上，另有元数据 `research_variant.base.sha256` |
| `disconnected_365_24h`（V3） | 32,260,715 | `f889c3ba1dee0ce48dc9c5d6aa165b3dd2a436bc16a92230616a091436d89974` | 只有 96 个 EV 电池的 `e_min_pu` |

**逐组件核对方法（`chk_dmax.py`）：** 用 xarray 不解码地打开新旧 netCDF，对全部变量（数据与坐标）比较维度、数值（浮点按位）、变量属性；全局属性逐一比较；元数据解析后逐键比较。逐项结果在 `evidence/dmax/REBUILD_DIFF_V1_V2_V3.csv`。

| 核对 | V1 | V2 | V3 |
|---|---|---|---|
| 不同的变量 | `stores_t_e_min_pu` | `stores_t_e_min_pu` | `stores_t_e_min_pu` |
| 不同的全局属性 / 元数据键 | 无 / 无 | 无 / `research_variant.base.sha256` | 无 / 无 |
| 列（与旧网络相同，都是 EV 电池） | 96 | 96 | 96 |
| 旧值 → 新值 | 0.1 → 0.8 | 0.1 → 0.8 | 0.1 → 0.8 |
| 新值 = 2920×3h 同一电池逐日最大值 | 是 | 是 | —（完全隔离没有 2920×3h 网络） |
| `stores_t.e_max_pu` | 无 | 无 | 无 |

EV 电池 `e_nom` 合计 7.934 TWh；日分辨率下跨日带宽 7.140 → 1.587 TWh（EXACT）。

**静态检查：** `all_structural_passed = true`，输出文件与补充 05 的证据逐字节相同。第一次运行退出码 1：我把 `--out` 指向构建目录，而脚本要从 `--out` 读需求表 `DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv`，在检查任何网络之前报 `FileNotFoundError`；把这张表复制过去重跑（`static7.sh`）即通过。网络没有动。

**核对脚本的一处更正：** 第一版 `chk_dmax.py` 把几乎所有浮点变量都判为不同。原因是不解码读取时浮点变量的属性里有 `_FillValue = NaN`，字典比较时 NaN 不等于自身。改为按 `repr` 比较属性后重跑，结论以重跑为准。网络没有动，规则、预测也没有因此改动。

## 3. 预测（求解前登记，原文见 `RUN_PLAN_V3.md` 第 23.3 节）

依据第一次筛查、补充 06 的区间，以及第一次筛查解中的 EV 电池租值（只读计算，`evidence/dmax/EV_RENT_SCREEN_V1_V2_V3.json`：V1 1.952、V2 2.021、**V3 2.076 bn**，V3 是新算的）。预测提交 `fbdf2c2e` 并推送，早于 HiGHS 路径检查。

| 项 | 预测 |
|---|---|
| V1 目标值 | 265.1–267.6 bn（最可能 266.7–267.1）；结构下界 263.5966 |
| V5 − V1 | 1.14–3.61 bn（最可能 1.6–2.1） |
| B6 = V2 − V1 | 14.25–14.80 bn，相对 14.3481 变化 −0.10 到 +0.45，上升较可能 |
| V3 − V2 | 1.05–1.60 bn，相对 1.1448 上升较可能 |
| 修订桥 v2 → v3 合计 | −3.2 到 −5.7 bn（第一批 −7.1886） |
| Owen | 12 个参与者符号与第一次筛查相同；若翻号，最可能是 PH、BN |
| EV 跨日 | 每个日末高于下限的电量之和 ≤ 1.587 TWh；每个电池日末 ≥ 0.8；全年跨日正变化 10–60 TWh（第一批 154.7） |

第 15.5 节"|V5 − V1| < 2 bn"等已登记的预测原文不动，重跑后仍按原文判定。

## 4. HiGHS 日分辨率路径检查

脚本 `pathcheck7.sh`（读取 `chk_pc7.py`、重评 `pc7_regate.sh`），提交 `fbdf2c2e`（预测已提交并推送之后），输出 `results_project/v3/path_check7`，证据 `evidence/dmax/PATH_CHECK_DAILY.json`。新 V1、V2、V3 的 365×24h 网络截短到前 8 天（8 个 24 小时时段，截短后每时段权重 1,095 h），HiGHS 内点法，后处理全链路：违规分析、C1、M12 账本、Owen 右端审计、批参照与重评、GATES_V6、停批分类、M12 受益、筛查三表。**本机 Gurobi 0 次。** 8 天的数不作经济解读。

| 项 | V1 一体化 | V2 `no_new_xb` | V3 完全隔离 |
|---|---|---|---|
| 终止 / 求解器 | optimal / HiGHS | optimal / HiGHS | optimal / HiGHS |
| 进程墙钟、峰值 | 约 3.3 min、1.02 GiB | 约 2.9 min、0.98 GiB | 约 2.8 min、0.99 GiB |
| EV 下限：电池 × 时段 | 96 × 8，下限全为 0.8 | 同左 | 同左 |
| 日末电量 − 下限的最小值；违反（< −1e-6） | −3.2e-12；0 | −3.2e-12；0 | −3.2e-12；0 |
| 正好压在下限上（≤ 下限 + 1e-4）的电池·日 | 47.1 % | 52.2 % | 52.3 % |
| 每个日末高于下限的电量之和（TWh，上界 1.587） | 0.49–1.21 | 0.47–1.12 | 0.47–1.01 |
| C1 (a)(b)(c) | 全过 | 全过 | 全过 |
| B16 相对误差 | 3.8e-14 | 6.6e-14 | 6.8e-14 |
| Owen 恒等式相对误差 / 可用 | 6.6e-14 / 是 | 7.8e-14 / 是 | 7.8e-14 / 是 |
| 右端项：国家 / 跨境对 / 燃料舱 / 共享 / 未归属 | 28,316 / 145 / 1,040 / 0 / 0 | 28,316 / 504 / 1,040 / 0 / 0 | 28,244 / 0 / 1,040 / 0 / 0 |
| V5 闸门失败 | 只有 B8 | 只有 B8 | 只有 B8 |
| GATES_V6 | 见下 | `ACCEPTED_LAYER2` | `ACCEPTED_LAYER2` |

- **EV 早晨下限生效（VERIFIED）：** 解中每个电池每个日末电量都不低于 0.8 × `e_nom`，约一半的电池·日正好压在下限上，下限在起作用。高于下限的电量之和始终在 1.587 TWh 的带宽内。
- **记账闭合（VERIFIED）：** B16、Owen 恒等式都在 1e-13 量级；右端项没有未归属行；12 个参与者的受益之和 19.447880 bn 等于这 8 天的 B6（差 5e-12 bn）。
- **一体化的 GATES_V6：** 路径检查按补充 05 的做法给一体化传了构建回执（`--build-receipt`），G2.1 于是拿回执里 2920×3h 网络的 SHA256（`1bddacb7…`）去比 365×24h 输入（`a0273602…`），不通过，标签 `NOT_ACCEPTED`；G2.2、G2.3 通过。这与补充 02 修订桥那次的情况相同，是截短检查的调用方式造成的。同一结果改按 365×24h 登记值（`--registered-sha256 a0273602…`）重评，`ACCEPTED_LAYER2`（`V6_ACCEPTANCE_REGISTERED_365.json`，原判定文件保留）。正式运行器按回执的 `daily_network` 核对，干跑的 `BUILD_CHECK` 覆盖这一点（第 5 节）。
- **B8：** 三次都只有 Transport 超限，相对差 +1.8362e-03。这是 `V3_RULES.md` 第 8.2 节同类的截短假象：前 8 天是一整周再加一个周二，按第 8.2 节的 r = 0.0149772，(7W + 1 + r) / 8 − 1 = r × (357 / 364) / 8 = +1.8361e-03，与实测一致（EXACT 到第 4 位）。全年网络在第一次筛查中 B8 五次都通过。

## 5. 部署包

位置 `work/p1_v3_20261102/screen_package_v3_dmax/`，**未上传**。打包脚本 `screen_package/make_package_v3_dmax.sh`（由 `make_package_v3.sh` 派生，原脚本不改），本机脚本 `dry_s7.sh`、`pkg_s7.sh`、`pkg7_wrap.sh`。`screen_package_v3_op/`（第一次筛查实际上传的包）及更早的包保留不用。

| 项 | 值 |
|---|---|
| 代码提交（= 干跑提交） / 网络构建提交 | `fbdf2c2e` / `7aec953e` |
| 文件数 / 字节 | 23 / 185,237,457 |
| `SHA256SUMS` 的 SHA256 | `cce1444c056e5b36fa39b7304d6c8bca834a3dfa3cd4dd5f49a9c713f821a24b` |
| `PACKAGE_MANIFEST.json` 的 SHA256 | `4a46fba96d3b0c2e19870d536ed18bf717246dff7ec159cb253c258fad66b031` |
| 代码包 | `code_fbdf2c2e.tar.gz`，82,781,860 B |
| 网络 | `integrated_365_24h`、`no_new_xb_365_24h`、`disconnected_365_24h`（= 第 23.1 节登记值），两份构建回执、一份派生回执、两张成本表；**没有修订桥和 2920×3h 网络** |
| 定义文件 | `BATCH_DEF.json` = `batch_def/BATCH_DEF_365x24h_dmax.json`：V1 → V2 → V3，TimeLimit 21,600 / 21,600 / 10,800 s，阶段 1 V1 ∣ V2、阶段 2 V3 |
| 包内规则与计划 | `V3_RULES.md`（含第 11 节）、`RUN_PLAN_SCREEN_V3.md`（含第 10 节） |
| 构建输入检查 | `BUILD_INPUT_CHANGES.json`：`7aec953e` 到 `fbdf2c2e` 构建路径上 0 项变化 |
| 上传时间估计 | 36 KB/s 1.43 h；100 KB/s 0.51 h；318 KB/s 0.16 h；1.36 MB/s（第一次筛查实测）0.04 h |

| 运行 | 行 | 列 | 非零 | `BUILD_CHECK` | 峰值（GiB） |
|---|---:|---:|---:|---|---:|
| V1 | 10,380,525 | 4,694,244 | 24,246,787 | 通过 | 10.10 |
| V2 | 10,073,383 | 4,557,015 | 23,271,214 | 通过 | 10.07 |
| V3 | 10,021,188 | 4,536,210 | 23,146,749 | 通过 | 10.07 |

- **干跑**（真实网络、运行器 `BUILD_ONLY`、无求解器、无许可，438 s，`evidence/dmax/DRY_RUN_SCREEN.json`）：`BASE_CHECK:all_equal`（登记值严格校验），单通道 V1 → V2 → V3，三次 `BUILD_CHECK` 通过；LP 规模与第 21.1 节逐项相同（只改了变量上下界）；两项拒绝检查正常（`BUILD_ONLY` 带 `--auth`；截短运行）；批汇总正常结束。
- **预检**（包的副本，`licence`、`resources` 两节留到实例上）：`sha256sum -c` 23 个文件全部 OK；`guards,sha,networks,env,profile,code,tools` 全部通过，`PREFLIGHT OK`；环境 284 / 284 与锁定一致；运行表 V1、V2、V3，时限与登记一致；包内没有 2920×3h 网络，泄漏扫描 0 处，代码包里没有许可文件。
- 打包时工作区只有一处未提交的进度表改动，为满足"打包时 tracked 工作区干净、提交 = 干跑提交"，打包期间暂存（`git stash`），打包后恢复，没有另起提交。

## 6. 需要审阅端知道

1. **V2 元数据的母网络 SHA256**（第 0 节第 3 条）：审阅决定第 2.1 节第 3 条只允许 EV 电池的变化，这一处是派生网络的来源记录，必然随 V1 改变。我在构建前写进规则，核对时严格限定为这一个键、且值等于新 V1。若审阅端认为应按停止条件处理，请告知。
2. **网络元数据 `temporal_reduction` 文字未改**（第 1 节）。
3. **修订桥网络与 2920×3h 网络都逐字节相同：** 第一批的 V4、V5 结果有效；HPC 正式运行的两个 2920×3h 网络不受影响，但 `daily_resolution.py` 在构建路径上，HPC 打包时构建提交要取 `7aec953e` 或之后（2920×3h SHA256 不变），已记入 `V3_DEPLOY_FILES.md`。
4. **重跑包的运行器修订桥只有 v2 → V1 一步**；完整的 v2 → V4 → V5 → 新 V1 在回收后本机计算（审阅决定第 2.1 节第 6 条）。
5. 简报：无论数字如何，日分辨率下修正后的 V5 → V1 只反映 1.587 TWh 带宽内的跨日储能，看不到日内调节（第 176 项第 7 条），规则第 11 节已写明。

## 7. 云端部分：等用户开机授权

按审阅决定第 2.2 节，需要用户：

1. 在 AutoDL 控制台带卡开机，优先原 199 机；若该卡已被占用，另租同规格或更高规格（下限 17 核 / 64 GiB / 90 GB）。
2. 在会话中给出连接方式，并写"授权 V3 重跑"。连接方式只在会话中出现，不写进任何文件、日志、提交或授权文本。
3. 一并确认：没有其他会话占用 WLS 许可、HPC 上没有会调用 Gurobi 的作业；AnyConnect 已断开、重跑期间保持断开。

授权后按 `V3_SCREEN_AUTODL_INSTRUCTION.md` 第 2 节与 `V3_SCREEN_UNATTENDED.md` 全部条款执行（看门狗、预先决定表、收尾与关机），差别只在：包 `screen_package_v3_dmax/`，实例目录 `/root/autodl-tmp/v3_screen_dmax/`（上一批目录不动），3 次运行；实例上已有环境且 `env_check` 284 / 284 一致时复用，否则重装。

## 8. 云端重跑结果

（重跑完成后补写：3 次运行状态与验收；新旧对照表（V1、V2、V3 目标值，B6，V3 − V2，Owen 12 个参与者）；修订桥 v2 → V4 → V5 → 新 V1；EV 电池电量轨迹核对；预测对照；费用。）

## 9. 资源、测试与文件

- **本机 Gurobi 0 次**；求解只有第 4 节的 3 次 HiGHS（8 天截短）。测试与干跑时许可路径指向不存在的文件。未连 AutoDL、HPC，未上传。
- **本机计算约 1.0 小时 / 2 小时：** 构建 5.7 分钟，静态检查重跑约 2 分钟，核对与只读计算约 0.5 分钟，路径检查 11.7 分钟加重评约 1 分钟，干跑 7.3 分钟，打包与预检约 2 分钟，相关测试约 1.5 分钟，全量测试约 28 分钟（见下）。
- **磁盘新增约 3.2 GB / 15 GB：** `builds_dmax` 313 MB、`path_check7` 222 MB、`dry_screen7` 2.3 GB、`pkg_check7` 177 MB、部署包 177 MB、证据与脚本 < 2 MB。
- **测试：** `test_s1_adapter_daily_v5.py`、`test_v3_runners.py`、`test_v3.py` 共 62 项全过（含新增 6 项）。全量 `tests/research`（提交 `fbdf2c2e`，没有其他求解同时运行，29 分钟）：**758 通过、58 跳过、3 失败**。3 项与之前各补充相同，都与 v3 无关：`test_s1_built_networks.py::test_static_validation_passes_on_reload`、`test_s4c_0.py` 两项（worktree 缺被 git 忽略的 WACC 表）。通过数比补充 05 的 752 多 6，就是本补充新增的 6 项。

**提交：** `38a1ad67`（规则）→ `7aec953e`（代码与测试，构建提交）→ `fbdf2c2e`（核对、登记、预测、定义文件、计划、打包脚本；已推送，早于路径检查）→ 本报告提交。

**证据 `evidence/dmax/`：** `REBUILD_CHECK.json`、`REBUILD_DIFF_V1_V2_V3.csv`（重建核对）、`V3_STATIC_CHECK.json`（静态检查）、`EV_RENT_SCREEN_V1_V2_V3.json`（预测依据）、`PATH_CHECK_DAILY.json`（路径检查）、`DRY_RUN_SCREEN.json`（干跑）。**脚本** `scripts/wsl_v3d/`：`build_s7.sh`、`static7.sh`、`chk_dmax.py`、`e_rent3.py`、`mk_def7.py`、`pathcheck7.sh`、`chk_pc7.py`、`pc7_regate.sh`、`dry_s7.sh`、`pkg_s7.sh`、`pkg7_wrap.sh`、`t_daily.sh`、`t_rel.sh`、`t_full7.sh`、`commit_d.sh`、`mirror_d.sh`。
