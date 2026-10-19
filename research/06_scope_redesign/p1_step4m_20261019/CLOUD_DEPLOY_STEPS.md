# 云端部署步骤（AutoDL 或同类按量实例，365×24h 日分辨率运行；S4M 部署包，云端档案 A `formal_barrier`；先探针、再试点、后整批）

本文件只说明操作步骤。Claude Code 不连接云端，也不启动任何正式求解；每一步由用户在实例上执行（或在用户授权下经 SSH 执行，方式同 L23）。**速度探针、试点与整批都须由用户单独明确授权**（CLAUDE.md：每次优化都需要用户单独明确授权；不自动重试、不做参数网格、不 warm start）。授权原文模板见 §7。

- 资源需求与选机建议见 `CLOUD_RESOURCE_ESTIMATE.md` §20–§22。
- 部署包脚本在 `cloud_package/`（仓库 `research/06_scope_redesign/p1_step4m_20261019/cloud_package/`）。
- 打包产物在本机 `work/p1_step4m_20261019/cloud_package_dist/`（含网络、代码快照与探针参照，不进 git）：代码提交 f50c8850，上传 260720379 B，22 个文件。

## 1. 与 S4K 部署包（56d28358，L23 首批）的区别

- **S4K 部署包作废**（第 114–116 项）：上云只用本文件对应的 S4M 部署包（代码 f50c8850）。S4L 构建了网络但没有打包；S4J、S4H、S4G、S4F 部署包此前已作废。
- **模型（主算设置，用户 2026-10-19 12:12 SGT 决定）：**
  - 第 114 项：`research.numerics.dust_cleanup: on`（修正规则）——构建末尾删除近零对象（零上限候选 295、单侧燃料母线 128 及其死端组件 128、全零负荷 38、全零出力 3、小容量 offwind 3、MY / TL 两个 < 1 GWh 的生物质池）、合并 86 条相同的 `biomass-to-methanol` 链路；被固定需求依赖的池、FT 链路、东盟外 CO₂ 储存保留。`off` 为对照（S4K / L23 状态）。crossover 档案不作正式或核验档案。
  - 第 115 项：`research.s2.industry.biomass_overflow_cap_share: 0.98`——BN、SG、VN 的固定生物质需求设为潜力的 98 %，差额 2 % 按第 36 项规则改由甲烷供给；`1.0` 列入第二批敏感性。
  - 档案 A `formal_barrier` 不变。
- **脚本（S4L-3 + S4M-3）：**
  - `run_365x24h.sh`：每个求解在独立进程组中运行（`setsid`），墙钟上限对整个组发 TERM、宽限 30 s 后 KILL，等组退出后再导出打包；导出前核对回执版本（`RECEIPT_<run>:post_solve|pre_solve`），被终止的运行记 `killed_pre_solve`；监控文件含进程组 RSS 与 cgroup 内存用量 / 限额。**TimeLimit 与墙钟上限是运行参数**：`GUROBI_TIME_LIMIT_S`（缺省 **14,400 s**）、`WALL_CAP_S`（缺省 **15,300 s**），按 L23 实测放大（§21）；探针后可按速度比再放大（§5）。
  - `preflight.sh`：CPU 与内存按容器 cgroup 配额（v1 / v2）判断；检查 GNU time 与 `setsid`。
  - `speed_probe.sh`（新）：在实例上用包内的 56×3h 一体化探针网络跑一次档案 A（30 分钟止损），输出 Gurobi 每 work unit 秒数、每次迭代秒数，与本机 S4M-2 同一运行（`PROBE_REFERENCE.json`）相比给出速度比和建议的 TimeLimit / 墙钟。
- **部署包内容：** `code_<commit8>.tar.gz`（整个仓库快照）、`networks/`（4 个 365×24h 网络 + 构建回执 + `integrated_56_3h_probe_unsolved.nc`）、`PROBE_REFERENCE.json`、`run_365x24h.sh`、`preflight.sh`、`speed_probe.sh`、`environment_pypsa-earth.yml`、`conda_explicit_linux64.txt`、`COMMIT`、`DATA_CONFIG_MANIFEST.json`、`PACKAGE_MANIFEST.json`、`SHA256SUMS`。不含许可、cutout、LP 数组。

## 2. 选机（§21.3、§22）

1. 求解只用 CPU，GPU 型号无关；按量计费时选 CPU 与内存满足要求的最便宜机型。
2. 比较 CPU 型号与代际、全核频率、内存带宽：L23 的 Xeon Silver 4214R（Cascade Lake，2.4 GHz）每 work unit 比本机 i7-13620H 慢 3.4–4.4 倍；优先较新代际、≥ 3 GHz、负载低的宿主机。
3. 串行最低 8 核 / 40 GiB / 数据盘 35 GB（`preflight.sh` 下限；L23 实测单运行峰值 15.3 GiB）；两通道 16 核 / 72 GiB。
4. 用探针（§5）核实实际速度后再决定 TimeLimit / 墙钟与是否换机。

## 3. 上传与环境

1. 上传 `cloud_package_dist/` 到实例数据盘（如 `/root/autodl-tmp/s4m_cloud/`），上传后 `sha256sum -c SHA256SUMS`（须全部 OK）并核对 `COMMIT` = f50c8850。
2. `apt-get install -y tmux time util-linux`（GNU time 与 setsid；L23 实例缺 tmux 与 time）。
3. `conda env create -n pypsa-earth -f environment_pypsa-earth.yml`（L23 实测 48 min），`PY=<env>/bin/python`；版本须与 `PACKAGE_MANIFEST.json` 一致。
4. 许可：用户自行把 Gurobi 许可文件放到实例（如 `/root/.gurobi/gurobi.lic`，权限 600）；脚本只经 `GRB_LICENSE_FILE` 引用，不复制、不打印、不打包；结果回收后删除。

## 4. 预检

```bash
GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic PY=$PY bash preflight.sh serial formal_barrier
```

须以 `PREFLIGHT OK` 结束；资源一节打印容器 cgroup 的核数与内存（宿主机值另列）。预检的许可检查占一个 WLS 令牌 ≥ 5 分钟：**之后至少等 5 分钟再启动探针或运行**。

## 5. 速度探针（第 116 项；单独授权）

```bash
GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic PY=$PY bash speed_probe.sh --auth "<授权原文>"
```

一次 56×3h 一体化求解（本机 S4M-2 同一 LP：目标值 648,381,181,410.45 EUR、141 次 barrier 迭代、218.87 s、407.73 work units、0.537 s 每 work unit），30 分钟止损。输出 `probe/<时间戳>/SPEED_PROBE.json`：`seconds_per_work_unit`、`seconds_per_iteration`、速度比（实例 / 本机，< 1 = 实例慢；L23 实例 0.23–0.30）、`objective_rel_diff_vs_local`、建议的 `suggested_gurobi_time_limit_s` / `suggested_wall_cap_s`（速度比 ≥ 0.25 时维持 14,400 / 15,300；更慢时按 0.25 / 速度比放大，取整到 300 s）。探针后等 ≥ 5 分钟再启动试点。

## 6. 试点与整批（在 tmux 中；各自单独授权）

试点（第 116 项：先一体化 STEPS 单运行）：

```bash
PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic GUROBI_TIME_LIMIT_S=14400 WALL_CAP_S=15300 bash run_365x24h.sh --solver-profile formal_barrier --mode serial --runs integrated --auth "<授权原文>"
```

整批（试点审阅后）：

```bash
PY=$PY GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic GUROBI_TIME_LIMIT_S=<按探针> WALL_CAP_S=<按探针> bash run_365x24h.sh --solver-profile formal_barrier --mode serial --auth "<授权原文>"
```

串行顺序：一体化 → 不互联（非最优时自动跑不互联诊断）→ NZE；`--runs` 可指定子集；`lanes2` 需 72 GiB 并自动留 330 s 许可间隔；`lanes3` 被拒绝。非最优不重试。

## 7. 授权原文模板

> 我授权在 ＿＿ 实例（规格 ＿＿；区域 ＿＿）上运行 S4M 部署包（代码 f50c8850）的 [速度探针 | 365×24h 一体化试点 | 365×24h 整批：一体化 STEPS、不互联 STEPS、一体化 NZE 及仅在不互联主算非最优时自动运行的不互联诊断]，求解档案 A（formal_barrier），运行方式 serial，每运行 TimeLimit ＿＿ s、墙钟上限 ＿＿ s（缺省 14,400 / 15,300），不重试、不改参数、不 warm start；许可文件 ＿＿，只经 GRB_LICENSE_FILE 引用，结果回收后删除。授权人：＿＿；时间：＿＿（SGT）。

## 8. 监督与回收

- `STATUS.txt`：`START`（含 `wall_cap_s` / `time_limit_s`）、`CGROUP_MEMORY_LIMIT_GIB`、每个运行的 `SOLVE_<run>:pid=…:pgid=…`、`RECEIPT_<run>:post_solve|pre_solve`、`RUN_<run>:<终止>:<秒>`，被终止时 `KILLED_<cap>S_<run>` / `KILL9_<run>`，最后 `DONE`。
- `MONITOR_<run>.csv`：每 60 s 一行（进程组 RSS、cgroup 内存用量 / 限额、宿主机 MemAvailable、磁盘、Gurobi 末行）。
- 结束后 `runs/<时间戳>/results_<时间戳>.tar.gz` 与 `.sha256`；下载后本机 `sha256sum -c`，解包并做许可特征串扫描；随后删除实例上的许可文件，再关机。
- 非最优的运行不重试；按 L23 的口径做只读违反分析后交首轮分析。
