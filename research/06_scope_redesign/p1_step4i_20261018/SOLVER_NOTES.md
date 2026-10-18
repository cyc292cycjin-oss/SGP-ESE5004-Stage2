# 求解注意事项（S4I 第 C 节，供云端首批、2920×3h 与联盟运行使用）

等级：VERIFIED = 回执或本步实测数组；INFERENCE = 外推或推理。所有数字的出处见 `S4I_EVIDENCE.json` 与 `evidence/`。

## 1. 求解器选择
- **一律用 Gurobi barrier（档案 A `formal_barrier`）。** HiGHS 只用于小规模冒烟或诊断。
- **HiGHS 的教训（VERIFIED）：** 同一 S3-7 LP（56×3h，559,050 列、2.83 M 非零元）上，HiGHS IPM 用 633 s 报"infeasible"（`p1_step3_20261015/evidence/s3_7/highs/smoke/integrated/SOLVE_RECEIPT.json`）。Gurobi barrier 123 次迭代、256 s 收敛，但随后 crossover 报 `INF_OR_UNBD`（`.../s3_7/gurobi/smoke/integrated/`）。同一 LP 后来改用档案 A（crossover 关）得到最优（`CLOUD_RESOURCE_ESTIMATE.md` §9：92 次迭代、90 s）。HiGHS IPM 在 56×3h 上就要 5–10 分钟，外推到 365×24h 超过 1 小时（同文件 §6），而且可能误判"不可行"。

## 2. 档案 A 的参数与理由
- `Method 2, Crossover 0, BarConvTol 1e-8, BarHomogeneous 1, Threads 8, Seed 123, AggFill 0, PreDual 0, GURO_PAR_BARDENSETHRESH 200`（`configs/research/baseline.yaml` 第 121 行）。云端脚本还固定 `--scaling on`（去掉目标常数、大型 Store 能量改用 GWh / kt、基尔霍夫行归一化）和 `TimeLimit 10,500 s`，到 3 h 强制停止（`run_365x24h.sh` 第 97–110 行）。
- **与 PyPSA-Eur `gurobi-default`（config 1056–1064 行）的差别：** 线程数 32 → 8，`BarConvTol` 1e-5 → 1e-8，另加 `BarHomogeneous 1`。
- **关闭 crossover 的理由：** crossover 曾把已收敛的 barrier 解报成 `INF_OR_UNBD`，用时约为 barrier 的 1.3 倍（§1）。
- **内点解的处理方法（代替顶点解）：** 验收门槛按求解器容差设定：`acceptance_basis: solver_tolerances`，原始 / 对偶预算 = 10 × FeasibilityTol / OptimalityTol（1e-6），对偶间隙与互补松弛 ≤ 10 × BarConvTol（`scripts_project/s4b_acceptance.py`）。报告用的清理阈值 τ = 10 × BarConvTol × max|x_g|（`interior.cleanup_factor`）。检查同时充放电（`INTERIOR_CHECKS.json`）。基尔霍夫行的对偶在求解后还原（`unscale_kvl_duals`）。

## 3. 数值：系数跨度的静态预警
- **方法一（不建模，几秒）：** 由线路参数计算基尔霍夫回路行系数 C·x_pu_eff 的跨度（`s4i_static_audit.py` 中的 `kvl_span`）。一体化：全局跨度 2,034，单行最大跨度 676，行归一化后最小系数 1.48e-3；不互联：112 / 28。
- **方法二（只建模、不求解，约 20 s、1.6 GiB）：** 取前 56 个日快照，权重保持 24 h，按 `s2_solve.py` 的顺序建模并缩放，读取 Gurobi 式范围（`s4i_lp_ranges.py`）。一体化缩放后：矩阵 [2.4e-4, 32]（跨度 1.3e5，最小值为气田逸散因子），目标 [0.24, 1.1e6]（最大值为 DAC 年化成本），界 [0.49, 7.4e4]，右端项 [2.0e-4, 6.1e8]（跨度 3e12；最大值推测来自以 MWh 计的年度国产气上限，INFERENCE）。缩放前目标中有一个 1.08e10 的常数列，矩阵跨度为 1.4e7。
- **建议阈值（每次换网络都先跑方法一与方法二）：**

  | 指标 | 警告 | 停下请用户决定 |
  |---|---|---|
  | 缩放后矩阵跨度 | > 1e6 | > 1e8 |
  | 单行基尔霍夫跨度 | > 1e3 | > 1e4 |
  | 目标跨度 | > 1e7 | > 1e9 |
  | 右端项最大值 | > 1e8 | > 1e10 |

  当前一体化网络只有"右端项最大值 6.1e8"超过警告线，登记即可。
- **求解后：** 读取 `SOLVE_RECEIPT.json → gurobi_log_stats.coefficient_statistics`（Gurobi 日志中的 Matrix / Objective / Bounds / RHS range），与上面的预警值对照。

## 4. 许可（Gurobi 学术 WLS）
- 同时最多 2 个会话。环境关闭后，令牌至少保留 5 分钟。每个 `s2_solve.py` 运行会通过 linopy 打开 1 个环境；`preflight.sh` 的许可检查（`gp.Model()`）也会占用 1 个。
- **因此：** `--mode lanes3` 同时有 3 个会话，必有一个运行因许可被拒。`--mode lanes2` 下，一个通道在 5 分钟内衔接下一个运行时，另一通道仍在运行，需要 3 个令牌，也有被拒风险。预检后 5 分钟内启动 `lanes2` 同样如此。`serial` 最多 2 个令牌，安全。
- 运行期间不要在本机或其他实例上使用同一许可（包括本机 WSL 中的 Gurobi 冒烟）。许可文件只通过 `GRB_LICENSE_FILE` 只读引用，导出前要检查许可字符串（脚本已做）。

## 5. 可比性
- 所有情景与联盟运行使用同一档案、同一线程数（8）、同一 `Seed`、同一软件版本（Python 3.11.13、pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4，由 `preflight.sh` 核对），并设 `PYTHONHASHSEED=0`。还要用同一种实例 CPU：barrier 在不同 CPU 上的末位数字可能不同。Gurobi 版本行从日志写入回执。

## 6. 内存与用时（引用 `CLOUD_RESOURCE_ESTIMATE.md` §17，INFERENCE）
- 365×24h：每个运行 37–52 min（悲观 76 min），峰值 23.3 / 32.6 GiB。串行共 1.9–2.6 h（悲观 3.8 h），两通道 1.2–1.7 h。
- 2920×3h：每个运行 8.7–18.5 h，峰值 164–259 GiB，超过每运行 3 h 的上限，需要另定 TimeLimit 和实例。
- 本步建模实测（VERIFIED）：56 个日快照的 LP 为 1,439,886 行 × 649,105 列、325 万非零元，与 S4H-3 冒烟 LP 的规模一致。

## 7. 止损规则
- 非最优（NUMERIC、SUBOPTIMAL、TIME_LIMIT、INF_OR_UNBD）一律不重试、不改参数、不 warm start，把日志末尾（已去除许可行）与回执带回分析。不互联主算非最优时，自动运行打包好的诊断网络（脚本已做）。
- 联盟运行要预期会出现 SUBOPTIMAL：S4D-4 中联盟 {LA, TH} 在档案 A 下为 SUBOPTIMAL（`p1_step4d_20261017/evidence/s4d_4/coal_LA_TH/SOLVE_RECEIPT.json`）。
- **云端环境依赖：** `run_365x24h.sh` 第 100 行调用 `/usr/bin/time -v`（GNU time），但 `preflight.sh` 不检查它。AutoDL 的 Miniconda / Ubuntu 22.04 镜像若没有这个程序，每个运行都会立即失败。运行前先执行 `test -x /usr/bin/time`。
