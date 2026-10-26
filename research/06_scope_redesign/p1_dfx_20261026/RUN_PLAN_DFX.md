# DFX 365×24h 筛查运行计划（RUN_PLAN_DFX）——v2 需求网络，V1 一体化 / V2 不互联

**登记时间：** 2026-10-26（SGT），在任何 v2 网络求解之前提交（本机 56 时段冒烟也在此提交之后）。看到任何 v2 求解结果后，第 3 节规则、第 4 节预测、第 5 节阈值不再修改。指令 v3 SHA256 `b60da4c6…5a6df`；规则文件 `DFX_RULES.md`（提交 `834a0f19`，早于 v2 构建提交 `72083fde`）。

## 1. 网络与代码

| 文件 | 分辨率 | 快照 | 字节 | SHA256 |
|---|---|---|---|---|
| `integrated_365_24h_unsolved.nc` | 365×24h | 365 | 31,292,240 | `82928a4c9151a6a176ac8c81bf56bbe41867e16ba0d059ce2ad8c6e78e59f6b2` |
| `disconnected_365_24h_unsolved.nc` | 365×24h | 365 | 30,620,986 | `5c75bfa0e338fde4104deb41cdcaa72dddcf7b3782e6ad8ca1f4fb6c15cfbd5c` |
| `integrated_2920_3h_unsolved.nc`（第四批 / HPC 用，不在 v8 包内） | 2920×3h | 2,920 | 63,873,447 | `08879f0bede119d77160cdb3f5f3c69dba302540b256b64efa4f16adbbefb271` |
| `disconnected_2920_3h_unsolved.nc`（同上） | 2920×3h | 2,920 | 63,202,193 | `d90ca99220d448c894c43c071b7e38f8c74e0a101b72878a4bdd941c37b164e7` |

- 构建：分支 `codex/dfx-v3-20261026` 提交 `72083fde`（dirty 0），`PYTHONHASHSEED=0`，`scripts_project/s2_network.py --scenario {integrated,disconnected}`（与 M08b `m08b_build.sh` 相同，每次写 2920×3h 与其精确日均 365×24h），worktree `/home/jin/wt_dfx_v3_20261026`，输出主检出 `results_project/dfx_v3/builds_v2/`；构建回执 `builds_v2/<scenario>/<scenario>_BUILD_RECEIPT.json`（`daily_network.sha256` = 上表 365×24h 值）。
- v1 基线（对照用）：同一 worktree 路径在基提交 `55ab07c0`（需求代码 = `ec80668f`）重建的四个网络（`builds_v1`）——与 `ec80668f` 登记网络逐组件相同，只有 `n.meta.s2_layers` 的构建路径字段不同（`equivalence/V1_REBUILD_VS_REGISTERED.json`）。
- v1 → v2 结构等价（`tests/research/test_dfx_demand.py::test_f5_structural_equivalence`，四个网络全部通过）：除 `loads` / `loads_t.p_set` 外的差异只有——(a) 过程排放发电机 `p_nom`（EDGAR × 工业乘数，F1）与 TL 过程排放源消失（TL 工业乘数 0）；(b) 随负荷有无而增减的需求侧计量 / 终端 / 炊事 / 原料组件（Link 114 个、Bus 52 个、Load 59 − 15 个）：BN / MM / PH / SG / TH 的氨负荷消失、MY 新增（F2）；TH 居民、VN 居民燃料负荷归零（F1 负锚），SG 农业、TH 商业由零转正；VN NEU 天然气截断为 0（F2.4）；(c) `n.meta` 中的需求账本与配置哈希键（`s2_demand_ledger`、`demand_owners`、`demand_identity`、`research_config*`、`research_dust_cleanup`、`research_fuel_carbon`、`s3_layers`、`s4l_layers`、`cross_border_tags`）。其余组件（发电机除过程排放、线路、链路、储能、母线、载体、全局约束及全部时序）逐字段相等。
- 注册表 `DATA_REGISTRY.csv` 2,280 行，SHA256 `7516113e4d40142f6d48a73236976b2b4c15d31a5b64c310bfbd7a45fcc6c217`；配置 `configs/research/baseline.yaml` 只改需求键（`physical_output_base_year` 加 `ammonia: 2019`、HVC 开关注释）。

## 2. 运行清单

| 运行 | 情景 | 网络 | 档案 | 成本表 | 作用 |
|---|---|---|---|---|---|
| V1 | integrated | `integrated_365_24h_unsolved.nc` | `formal_barrier_1e6_t16`（Threads 16，与第四批正式运行相同） | `integrated_costs_active_research.csv` | 本批参照（一体化）、Owen 分摊 |
| V2 | disconnected | `disconnected_365_24h_unsolved.nc` | `formal_barrier_1e6_t16` | `disconnected_costs_active_research.csv` | 本批参照（不互联）、B6 |

无变体、无去一国运行（LOO 留给 2920×3h 正式运行）。

## 3. 事先登记的规则（看结果前不得修改）

### 3.1 时限与求解
- 每个运行只求解一次：不重试、不改参数、不热启动；非 optimal 照实记录（分级见 3.3）。
- TimeLimit = 第三批 R3 / R4 求解进程墙钟（`M10_REPORT.md` 第 2 节：R3 4,882 s、R4 1,423 s）× 3：**V1 14,646 s，V2 4,269 s**；墙钟止损 = TimeLimit + 1,200 s（**V1 15,846 s，V2 5,469 s**；第三批 30,000 / 28,800 的同一余量），到时终止整个进程组（TERM → 30 s → KILL）。依据：R3 / R4 与本批同档案、同分辨率，v2 需求总量比 v1 高 6.7 %（7,628.6 对 7,147.6 TWh）、负荷数少 59 个，LP 规模同量级；3 倍是对迭代数增加的保守余量。
- 其他求解参数 = 档案 `formal_barrier_1e6_t16` 的登记值（`baseline.yaml research.solver.profiles`），`--scaling on`，与第三批 R3 / R4 完全相同。

### 3.2 并发与顺序
- 两次启动间隔 ≥ 330 s（WLS 令牌 ≥ 5 min；同第三批）。
- 两个运行并行只在容器核数 ≥ 33（2 × Threads 16 + 后处理 1 核）时；否则串行 V1 → V2（一个通道）。25 核实例（第三批同型）即串行。任意时刻 Gurobi 会话 ≤ 2（云端 2 + 本机 0）。
- 续跑：同一命令在同一运行目录再次执行时，已结束的求解不重复；"已开始未结束"的求解 → 安全停止等用户。

### 3.3 验收与停批
- 每个运行：违反量分析 → C1（先按缺省参照，V1 与 V2 都有账本后生成本批参照 `BATCH_REFERENCE.json` 并重评，保留 `grade_history`）→ M12 分摊（对偶形式主值 α 0.5、α 区间、市场形式、燃料舱参与者）→ Owen 对偶形式审计 → GATES_V6（`gates_v6.py accept --build-receipt`：未截短的 365 快照运行取日网络 SHA256 = 第 1 节登记值）→ 分级分类（`m10_batch3_summary.py stop-class`，`M10_BATCH=dfx`）。
- **停批规则：** V1 与 V2 都是本批参照运行——任一运行 G2 不通过、无返回解或 C1 (a) 不通过 → `STOP`（不再启动新求解，正在运行的求解结束并后处理，写汇总与结果包，等用户）；只有 C1 (b) / (c) 不通过 → 不停（记录，第 138 项 D12）。
- 不在规则内的情况 → 安全停止 `STOP_SAFE`（续跑时发现已开始未结束的求解、启动时已有求解进程、基础网络 SHA256 与构建回执不符、输入缺失、启动时其他求解进程多于一个）。

### 3.4 后处理与对比（批级）
1. `BATCH_REFERENCE.json`（V1 / V2 账本）→ 重评 C1 与 Owen（`OWEN_REGRADE_BATCH_REFERENCE.json`）→ 最终 GATES_V6 标签；
2. **B6 = V2 − V1** 目标值（`v5_gates.gate_b6_cost`），并列 M12 受益（`m12_allocation.py benefit --integrated V1 --disconnected V2`）；
3. 账本与 B16（每个运行的 `COUNTRY_COST_LEDGER*.csv`、`LEDGER_IDENTITY.json`、`V5_GATES.json` B16）；
4. Owen 对偶形式分摊表：α 0.5 主值、α 区间、市场形式、燃料舱参与者（`m12_owen/OWEN.json`，`ALLOCATION.*`）；
5. **与第三批 R1 / R2 的对比**（只描述，不作验收依据）：目标值（R1 249.8354 / R2 261.1355 bn EUR）、B6（11.300 bn EUR）、分国 Owen 份额——包内 `BATCH3_REFERENCE_VALUES.json`；
6. **实际 ΔB6 与第 4 节一阶预测的对比**（只描述）；
7. 汇总 `DFX_SUMMARY.json / .md`（`m10_batch3_summary.py summary`，`M10_BATCH=dfx`）；导出到 `export/V1`、`export/V2`、`export/batch`（清洗后的日志，无 LP / 解数组，无原始求解日志）；打包 `pack_results.sh`（light / full），许可特征串检查后才打包。

### 3.5 无人值守与资源
- 运行脚本 `run_dfx.sh`（由第三批 `run_batch3.sh` 派生，规则同上）；监控每 60 s 记录进程组 RSS、cgroup 内存、磁盘；后处理每步 1,800 s 超时（`POST_TIMEOUT_S`），违反量分析与 C1 失败后重做一次（M10A 补充 01 D2）；`TMPDIR` 在运行目录（数据盘）。
- 正式运行拒绝任何测试钩子 / 干跑开关 / 未登记时限（`ALLOW_UNREGISTERED=1` 只用于本机干跑与替身测试）；无求解模式（`BUILD_ONLY` / `POST_ONLY` / `DRY`）拒绝 `--auth`。
- 资源原因（内存、磁盘）终止后，在更大实例上从头重开同一运行须用户授权并登记（指令阶段 4）。

## 4. 一阶预测（事先登记；INFERENCE，大变动外推）

方法 = DMD `dmd_d5_duals.py`（包络定理）：第三批 365×24h R1 / R2（主）与 R3 / R4（optimal 1e-6，稳健性）各负荷母线的年度负荷加权对偶价格 λ；ΔD = v2 − v1 逐（国家, 账户, 载体）年量（网络负荷，`DEMAND_BY_COUNTRY_SECTOR_CARRIER_v1/v2.csv`）；ΔC = Σ λ·ΔD；ΔB6 = ΔC_不互联 − ΔC_一体化；v1 中不存在的负荷类（MY 氨、SG 农业生物质、TH 商业油）取同载体均价。脚本 `work/p1_dfx_20261026/scripts/dfx_first_order.py`，证据 `evidence/DFX_FIRST_ORDER.json`。

| 口径 | ΔD TWh | ΔC_一体化 bn EUR | ΔC_不互联 bn EUR | **ΔB6 bn EUR** | 预测 B6（11.300 + ΔB6） |
|---|---|---|---|---|---|
| 主（R1 / R2） | +481.0 | +19.450 | +22.510 | **+3.060**（+3.488 bn USD） | **14.36 bn EUR** |
| 稳健性（R3 / R4） | +481.0 | +19.450 | +22.510 | +3.060 | 14.36 |

按变动类别（主口径）：F1 交通锚（RAS）ΔD +355.2 TWh → ΔB6 +2.169；F1 工业乘数 +238.1 → +1.173；F1 建筑锚 −132.9 → −0.026；F1 农业锚 −29.0 → −0.082；F2 氨产量法 +66.3 → −0.153；F2 NEU 天然气扣除 −143.4 → −0.021；F3 HVC 范围 + 乘数（NEU 油）+126.2 → 0.000。分国受益变化（bn EUR）：MY +1.552、SG +1.150、VN +0.376、TH +0.115、BN +0.029、PH +0.018、MM +0.010、KH +0.004、TL +0.002、LA −0.016、ID −0.181。

说明：这是对 +481 TWh（+6.7 %）大变动的线性外推，只作方向与量级参考；实际求解后的 ΔB6 与此处的差异在报告中只描述，不作验收依据。DMD 报告对"NEU 移出 + 交通按 ATS"的一阶合计 +7 bn 未计入 F1 对居民 / 农业 / NEU 天然气的减量与工业乘数的重算；本预测以实际 v2 − v1 负荷差为准。

## 5. 资源估计与实例规格（INFERENCE，基于第三批实测）

- 第三批同档案实测（8470Q，25 核 / 92 GiB）：R3 一体化 T16 4,882 s 墙钟（260 次 barrier，16.9 s/次），峰值 22.78 GiB；R4 不互联 T16 1,423 s，峰值 19.29 GiB；后处理每次约 6–8 min、峰值约 11 GiB（违反量分析 / C1 各约 9.3 GB，Owen 审计 8.1 GiB）。
- v2：LP 规模同量级（负荷 2,241 对 2,300；行列数在干跑 `BUILD_CHECK.json` 中记录），需求 +6.7 %。预计 V1 1.0–2.0 × R3 = **1.4–2.7 h**，V2 0.4–0.8 h；串行合计（含两次后处理、330 s 间隔）**2.5–4.0 h**；加环境安装（直连约 14 min，M10 实测 827 s）与上传（包约 150 MB，36–318 KB/s：0.1–1.2 h）→ 实例占用约 **3.5–6 h**。TimeLimit 是实测的 3 倍（V1 4.07 h），止损前最坏 V1 4.4 h + V2 1.5 h。
- **规格下限（预检硬下限，`preflight_dfx.sh`）：** 核数 ≥ 17（Threads 16 + 后处理 1；并行需 ≥ 33）；容器内存 ≥ 64 GiB（单会话峰值 23 GiB + 后处理 11 GiB ≈ 34 GiB，2 倍余量；并行两会话 42 + 11 ≈ 53 GiB）；装好环境后数据盘可用 ≥ 45 GB（两个运行目录各约 1.8 GB + 导出与结果包约 1 GB + 环境 3.3 GiB + 包缓存 0.75 GB + 包 0.15 GB ≈ 8 GB，预检沿用第三批下限）。**租用建议：** 第三批同型 AutoDL West-B 8470Q 25 核 / 92 GiB / 50 GB 数据盘（串行）即可；并行则需 ≥ 33 核。
- 费用：按 AutoDL 控制台现行单价 × 占用时长（3.5–6 h）；单价以控制台为准（第三批同型实例约 10 h 的账单可作参照）。

## 6. 部署包 v8（`work/p1_dfx_20261026/cloud_package_dfx/`）

两个 365×24h v2 网络 + 构建回执 + 成本表（`networks/`）；代码归档 `code_<commit8>.tar.gz`（git archive，不含顶层 `research/`）；`run_dfx.sh`、`preflight_dfx.sh`、`pack_results.sh`；`env/`（第三批同一锁定：`ENV_LOCK.txt`、`conda_explicit_linux64.txt`、`pip_only.txt`、`ENV_DOWNLOAD.json`、`install_env.sh`、`env_check.py`——关键包 python 3.11.13、pypsa 0.30.3、linopy 0.5.5、xarray 2025.1.2、pandas 2.3.1、numpy 1.26.4、scipy 1.15.2、gurobipy 12.0.3、netCDF4 1.7.2、h5netcdf 1.6.4、dask 2025.7.0、pyomo 6.9.3、highspy 1.11.0 必须相同）；`RUN_PLAN_DFX.md`；`BATCH3_REFERENCE_VALUES.json`；`COMMIT`；`SHA256SUMS`；`PACKAGE_MANIFEST.json`。绝不包含：许可、cutout、LP / 解数组、2920×3h 网络、结果。上传单路 rsync，之后全量 `sha256sum -c`。

## 7. 云端步骤（阶段 4；主机、端口、密码不写入任何文件）

1. 用户在会话中给出连接方式；SSH 用 WSL `~/.ssh/id_ed25519`；
2. 单路上传 v8 包 → `sha256sum -c SHA256SUMS` 全部 OK；
3. `bash env/install_env.sh`（先 `--check-mirrors`；gurobi 频道直连）→ `env_check.py` 关键包相同；
4. 经用户授权后 `scp` 许可到 `/root/.gurobi/gurobi.lic`，`chmod 600`，不读取、不打印；
5. 同一 tmux shell：`PY=… GRB_LICENSE_FILE=… bash preflight_dfx.sh` → `PREFLIGHT OK`；
6. `PY=… GRB_LICENSE_FILE=… bash run_dfx.sh --auth "<用户授权原文>"`；监控 `runs/dfx/STATUS.txt`、`MONITOR_V1.csv`；`STOP` / `STOP_SAFE` 即停等用户；
7. 回收：先 light 包，再 full 包（含求解后网络与对偶 NetCDF）；本机 `sha256sum` 核对；
8. 删除云端许可（`shred -u`，`ls` 核实）；其他云端文件不删。

## 8. 由准备端确定、请审阅确认的取值

TimeLimit 3 × R3 / R4 墙钟（14,646 / 4,269 s）；并行阈值 33 核；预检硬下限 17 核 / 64 GiB / 45 GB；B6 的第三批参照值取 R1 / R2（suboptimal、ACCEPTED_LAYER2）而非 R3 / R4（optimal）——两者 B6 相差 0.0001 bn；一阶预测只作对比描述。
