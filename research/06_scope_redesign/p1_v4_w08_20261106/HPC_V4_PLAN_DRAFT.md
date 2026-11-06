# v4 正式批次作业草案（PROPOSED；只写草案，不打包、不提交、不连 HPC）

- **依据：** 指令第 6 节；验证计划第 4、6 节；v3.1 HPC 包 `work/p1_v3_20261102/hpc_package_v3_1/`（作业体、PBS 模板、运行器、门与后处理沿用）。全部数值为 PROPOSED，提交前须审阅端与用户确认，每个作业单独授权。
- **用时依据：** 指令给出的 v3.1 2920×3h 实测 barrier 用时 F1 约 6 h、F2 约 5.5 h（Atlas，档案 `formal_barrier_1e6_t16`）。本草案没有自行核对 HPC 回执（本会话不连 HPC），用到的地方标 INFERENCE。

## 1. 网络与规模

v4 网络与 v3.1 同一构建路径，只换需求 / 工业 / 生物质 / 气上限 / 曲线表（`research.demand.v4.enabled=true`）。结构差异（`STATIC_CHECKS.md`）：Bus −59、Link +10、Generator −5、Store −5、Load −35，另有 457 条工业负荷的时间序列（常数项，不增加变量或约束）。**LP 维数与 v3.1 同量级（INFERENCE，差 < 0.5 %）**，所以每次 barrier 迭代的用时按 v3.1 取；迭代数可能随需求结构变化（VN 生物质池从零余量变为 1 % 余量，退化减弱，可能更少）。

| 作业 | 网络 | 构建覆盖项 | 用途 |
|---|---|---|---|
| V4-M1 | 2920×3h 一体化 | `demand.v4.enabled=true`（锚 IIa） | 主结果 c(N)、Owen |
| V4-M2 | 2920×3h `no_new_xb`（由 V4-M1 派生） | 同上 + `cross_border.stock_mode=no_new_xb` | B6 = M2 − M1 |
| V4-S1 一对 | 365×24h | `demand.anchor_mode=iid` | 锚构造 IId（T_v2 −323.8 TWh 相对主算） |
| V4-S2 一对 | 365×24h | `demand.anchor_mode=iib` | 锚构造 IIb（冻结 v3 锚） |
| V4-S3 一对 | 365×24h | HVC S2 口径（2019 3.269、2050 6.103 MWh/t）**——需先加开关，见第 4 节** | I2：T_v2 +98 TWh 量级 |
| V4-S4 一对 | 365×24h | `demand.v4.id_paper_fuelwood=purchased` | 造纸木材按 (b)（第 211 项第 2 条的敏感性，ID +161.8 TWh） |
| V4-S5 一对 | 365×24h | `demand.v4.residue_boundary=false`（残渣旧读法：自用残渣留在需求与锚中） | I2：蔗渣留在 T_v2 +171 TWh、平衡表不含残渣 +41 TWh 一类 |
| V4-S6 一对 | 2920×3h | `demand.v4.industry_curves=flat` | 工业曲线全平（G5 Q10：曲线对成本的方向；需日内结构，所以用 2920×3h） |

## 2. 资源与时限（按 v3.1 实测重估，INFERENCE）

**估计方法：** 进程 2 的 Gurobi 时长 = v3.1 实测 barrier（F1 6 h、F2 5.5 h）× 迭代数因子（v4 / v3.1：0.8–1.5，中值 1.0）+ 预处理与交叉（v3.1 关交叉）+ 构建写 LP（v3.1 登记 5,400 s 上限内）。

| 项 | V4-M1（一体化） | V4-M2（`no_new_xb`） | V4-S6 一对（2920×3h，各一个） | 365×24h 敏感性（每个运行） |
|---|---|---|---|---|
| barrier 预计 | 6 h（4.8–9 h） | 5.5 h（4.4–8.3 h） | 同 M1 / M2 | 本机 8470Q 同档案的 v3 实测约 3.3 h（AutoDL 记忆）；Atlas 1.0–1.6 倍 |
| **TimeLimit（建议）** | **108,000 s（30 h）** = 高值 9 h × 约 3.3 倍余量 | **100,800 s（28 h）** | 同 M1 / M2 | **43,200 s（12 h）** |
| 早期测速止损 | 第 20 次迭代按"第 11–20 次平均 × 参考迭代数 + 已用 > 0.8 × TimeLimit"（v3.1 规则不变），参考迭代数取 v3.1 2920×3h 实测次数 × 1.5 | 同左 | 同左 | 同左（参考迭代数取 v3.1 365×24h 实测 × 1.5） |
| PBS walltime | 36 h（TimeLimit + 构建 1.5 h + 后处理 3 h + 打包 2 h，余量约 0.5 h；v3.1 规则 ≤ 720 h） | 34 h | 同 M1 / M2 | 18 h |
| 资源 | `parallel`，48 核，300 GB（v3.1 F1 同；D2 构建峰值 92 GiB） | 同左 | 同左 | 24 核，128 GB（365×24h 本机构建 LP 8 GiB；求解峰值按 v3 云端约 30–60 GB，INFERENCE） |
| Gurobi 并发 | 同一时刻至多 2 个 HPC 会话 + 0 个本机（第 192 项上限 8） | — | — | — |

- 合计（主算一对 + S6 一对 + 5 对 365×24h）：约 4 × 6 h + 10 × 4 h ≈ 64 h 求解（中值），按每次 2 个并发约 32–40 h 墙钟（INFERENCE）。
- TimeLimit 从 v3.1 登记的 864,000 s（240 h，实测前的上界）降到 30 h，是因为现在有 v3.1 实测；若审阅端想保守，可取 48 h（实测高值 9 h 的 5.3 倍）。

## 3. 冒烟、验收与比较

- **前提（求解后补记）：** 本机 W08 冒烟四次 optimal、R0 与 v3.1 逐位相同，但判据 4（成本差在一阶估计 ± 50 % 内）三对都不满足，数据链核查未发现错误、结果落在 LP 凸性上下界内（`SMOKE56_V4.md` 第 2.2–2.3 节；报告 0.1 第 5 条）。本草案的任何作业都以审阅端对该判据的决定为前提。
- **HPC 冒烟：** 正式提交前跑 `smoke56`（V4-M1 / M2 前 56 时段，`TRUNCATE=56`，标签 `SMOKE_TEST_ONLY`），期望值 = 本机 W08 冒烟 R1 / R2 的目标值（`SMOKE56_V4.md` 第 2 节），相对 1e-6 内（跨机器只记差异），与 v3.1 包的冒烟作业体相同。
- **验收：** C1 (a)(b)(c)、GATES_V6（`ACCEPTED_LAYER2` 或更好）、B16、B6 为正、无松弛；失败门须在 v3.1 并集之内。
- **与 v3.1 的比较：** 同规模、同档案；ΔB6 分解为需求项（检查点 S1–S6 的 T_v2 变化）+ 网络项（F1–F4、F7）+ 曲线项（V4-S6）；结果放新目录，不改写 v3.1 回执。

## 4. 打包前必须先做的改动（PROPOSED，本次未做）

1. **表目录按开关集命名：** 现在 `research_inputs/industry_v4/out_<anchor_mode>/` 只按锚模式区分；V4-S4 / S5 / S6 与主算同为 `ras`，会互相覆盖。建议 `out_<anchor_mode>` 只留给该模式的 v4 主集，其他开关集写到 `out_<anchor_mode>_<开关集 SHA256 前 12 位>`（`v4_common.out_dir` / `v4_tables` 两处），并在包内登记每个表目录的 `V4_SWITCHES.json`。
2. **HVC 口径开关：** `v4_products.hvc_plants(basis)` 已能取 S2 口径（`a`：3.269 / 6.103），但配置中没有开关；加 `research.demand.v4.hvc_basis: b | a` 并接入 `build_steps` / `load_items`。
3. 上两项会改变配置哈希（B12），所以必须在构建 HPC 网络之前完成并重建全部网络；本机 56 时段冒烟的网络不用于 HPC 包。
4. HPC 包脚本 `hpc_v31/make_hpc_package_v31.sh` 复制为 v4 版：网络、定义文件（`BATCH_DEF_2920x3h_v4hpc.json`，`run_dirs` 新目录 `runs/batch6`、`runs/smoke56_v4`）、v4 表目录与注册表随包；`preflight.sh` 增加 `V4_SWITCHES.json` 与网络元数据 `v4_w08.switch_sha256` 的一致性检查。
