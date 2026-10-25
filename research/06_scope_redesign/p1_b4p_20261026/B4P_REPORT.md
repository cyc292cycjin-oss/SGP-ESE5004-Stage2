# B4P 报告：第四批（2920×3h 正式运行）准备——资源实测与外推、分进程求解、保护性修改、运行计划、部署包 v7（本机；不连云）

1. **资源结论（INFERENCE，依据本机 8 次 Gurobi 探针与第三批云端实测）：** F1 一体化 2920×3h 的 Gurobi 进程峰值约 **90 / 124 / 160 GiB**（低 / 中 / 高），单进程方式（Python 模型 + Gurobi 同驻）约 162 / 206 / 253 GiB；F2 不互联 68 / 104 / 149 GiB。**时间是更大的风险：** 一体化的因子运算量按稠密列区间外推为 3.5e13 / 1.5e14 / 2.9e14，8470Q T16 每次迭代 135 / 580 / 1,127 s，F1 barrier 用时 **9.5 / 56 / 146 h**——中值已接近 72 h 时限，高值远超；F2 为 1 / 7 / 14 h。
2. **分进程求解（补充 2）：已实现并证明等价，登记为第四批执行方式。** 56×3h 完整求解：分进程（C2）与单进程（C1）的 Fingerprint `0xb609266f`、129 次迭代、428.37 工作单元、目标值、X / Pi / RC 与全部导出逐位相同；C1 又与旧代码的 M08b 冒烟逐位相同（A3.1 回归）。三进程峰值 2.19 / 3.62 / 2.64 GiB 对单进程 4.74 GiB；在 112 时段单进程（T16）首次因子分解即超过 10.5 GiB 被 90 % 规则终止，而分进程的 Gurobi 进程在 140 / 182 时段为 6.7 / 7.8 GiB。
3. **候选配置（A1 第 4 项 + 补充 1）：** 分进程方式下五种配置都能跑 F1（高值 160 GiB ≤ 240 GB 配置的 80 % 配额 178 GiB，余量小）；单进程只有 368 GB / 512 GiB 可跑；F2 并行只有 368 GB（中值）与 512 GiB 可行。推荐：**AutoDL vGPU-48GB 4 卡 8470Q / 368 GB**（最稳：内存余量最大、CPU 速率有实测、可并行；中值约 63 h、约 ¥730）→ 阿里云 r8i 512 GiB → **AutoDL RTX 4090D 4 卡 EPYC 9754 / 240 GB**（最省钱的可跑配置，中值约 82 h、约 ¥620；串行、速率为假设）。**60 GB 数据盘够用**（持久约 36 GB + 瞬时 LP 文件 5.4 GB，`REMOVE_LP=1`）。机器由用户决定。
4. **A3.1 求解结果先落盘：** `s2_solve.py` 的求解后流程改为"终止状态与目标值 → 解与对偶数组 → 逐步导出 / 门控 / 账本，异常记入 `post_solve_errors`"，终止状态与"有返回解"判定不再因后处理异常丢失；回归逐位相同；替身与真实网络注入异常测试通过。A3.2（路径规范化）与 A3.3（conda 按频道镜像）由分支代理完成并测试。
5. **`RUN_PLAN_B4.md` 已登记：** TimeLimit 259,200 s、Gurobi 进程墙钟 266,400 s（+ 2 × 3,600 s）、P1 探针（1 h 内峰值 ≤ 40 % 配额且 ≥ 33 核才并行）、内存止损（cgroup 匿名内存 > 80 %）、早期测速（第 11–20 次迭代 × 450 / 250 + 已用 > 80 % TimeLimit 即止损）、分级停批、后处理并存条件（空闲匿名内存 ≥ 100 GiB）、单步超时 3 倍、资源重开规则；`run_batch4.sh` + `b4_batch4.py` 实现并有 10 个替身整链测试。
6. **A2.2 `SoftMemLimit`：不采用为登记参数**（8 次调用全部用于 A1 与分进程，未能做"不触发时逐位相同"的验证；通道保留，用户决定）；A2.1 直接传模型不采用（与分进程目标相反，且 LP 文件 `%+.12g` 与 float64 直传的模型不逐位相同）。
7. **本机 Gurobi 使用：** 8 次（授权 8 次），全部截短 2920×3h 网络（56–224 时段），最长 407 s，最短间隔 301 s，不重试；两次按 90 % 内存规则终止（C3 单进程 112、C4 分进程 224 排序阶段），记录到该点。本机计算合计约 1.8 h（上限 5 h），磁盘新增约 10 GB（上限 40 GB）。
8. **演练、测试、包、干跑：** 演练 4 类（56 真实 ×2 ACCEPTED_LAYER2；182 合成 ×2 跑通）、9 类后处理链回归逐项相同、全量测试 **655 passed / 69 skipped / 0 failed**；包 v7 提交 `f806e3e7`、19 文件 / 213,805,295 B、清单 `c0168cfe…1a84`、`SHA256SUMS` `b0a0ddf7…9b4f`、网络 SHA256 = 登记值、无 365×24h；干跑：预检 OK（资源节本机失败属预期）、BUILD_ONLY 两运行通过、合成整链走到停批打包、钩子残留与未登记值被拒绝。
9. **发现但未处理 / 需要用户决定：** 72 h 时限可能不够（第 9 节）；`GURO_PAR_BARDENSETHRESH=200` 使 N < 200 的截短模型结构不代表正式问题（测量用阈值 100，正式档案未改）；机器选择、是否采用 `SoftMemLimit`、并行阈值、早期测速止损后的处置。
10. **分支：** `codex/b4-prep-20261026`（从 `9f368407`），提交 `a9ccc129`（分进程 + A3.1）、`15482e3f`（A3.2/A3.3）、`96eafa53`（第四批运行脚本 / 计划 / 打包 / 演练 / 测试）、`f806e3e7`（演练脚本修复 + 辅助脚本镜像；= 包 v7 的提交）、随后的报告 / 证据提交（本分支最后一次提交）；已推送 origin。未合并 main，未 force-push。

---

**指令：** `B4P_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 `995ff3447b4ae3ef1b9dc6fc0e029ee711fbb340475f3417deddf2eebc8378b2`，与 `B4P_INSTRUCTION_SHA256.txt` 一致，开始前核对）。**授权：** 用户 2026-10-26 03:15 SGT 原文（会话消息；本机最多 8 次 Gurobi 调用、≤ 365 时段、每次 ≤ 60 min、间隔 ≥ 5 min、不重试；本机计算 ≤ 5 h；磁盘 ≤ 40 GB；新分支改代码、补测试、推送；打包 v7 并干跑；补充 1 候选配置；补充 2 分进程求解；无人值守规则）。**边界：** 不连云、不上传；未构建、未求解完整 2920×3h（只核对了两个网络文件的 SHA256 与可读性）；模型、网络、成本表、档案的求解参数、验收阈值未改（测量专用覆盖见第 9 节第 2 项）。**位置：** worktree `/home/jin/wt_b4p_20261026`；本机辅助脚本 `/home/jin/b4p/`（副本在 `scripts/`）；中间结果主检出 `results_project/b4p/`；证据 `evidence/`；过程记录 `B4P_PROGRESS.md`；证据 JSON `B4P_EVIDENCE.json`。结论等级：VERIFIED（实测 / 逐位比较）、INFERENCE（外推、机制解释）、PROPOSED（未执行）。

## 1. 资源估计（A1）

### 1.1 已有数据（VERIFIED）

第三批 R1–R11（365×24h，云端 8470Q / R11 EPYC 9654）与本机 56×3h 运行的日志统计：见 `evidence/REPORT_TABLES.md` 第一表（行 / 列 / 非零、预求解后规模、Factor NZ / Factor Ops、迭代数、每次迭代秒数、峰值 RSS、构建秒数）。要点：一体化 365×24h（R1 / R3 / R10）Factor NZ 5.28e8、Factor Ops 4.24e12，T16（R3）每次迭代均 16.4 s（第 11–20 次 11.2 s）、峰值 22.78 GiB（单进程）；不互联（R2 / R4）2.5e8 / 1.04e12，T16 每次 7.4 s、峰值 19.29 GiB；EPYC 9654（R11，T8）与 8470Q（R2，T8）同一模型每次迭代 10.0 对 9.7 s。本机 365×24h 仅构建峰值 10.15 GiB（M10P）。

### 1.2 新测量（VERIFIED）

- **截短构建（`--stop-before-solve`，56 / 112 / 182，两种情景）：** 一体化峰值 2.18 / 3.97 / 6.16 GiB，构建 19 / 30 / 45 s，`lp/` 数组 123 / 246 / 399 MB；不互联 1.92 / 3.47 / 5.30 GiB。273 与 365 时段未做：182 的峰值 × 1.55 已超过 8.5 GiB（WSL 10.95 GiB 的 90 % 规则）。
- **分进程各进程（进程 1 构建 + 写 LP 文件；进程 2 gurobipy；进程 3 重建 + 映射 + 导出）：** 表见 `evidence/REPORT_TABLES.md` 第三表。进程 1：56 / 112 / 140 / 182 / 224 时段 2.19 / 3.96 / 4.85 / 6.16 / 7.47 GiB，LP 文件 94 / 192 / 241 / 316 / 391 MB，写出 8 / 13 / 15 / 19 / 23 s；进程 2（T16，稠密列区间）：140 一体化 6.66 GiB（MaxMemUsed 7.75 GB）、182 一体化 7.76（9.44）、140 不互联 5.81（6.70）、182 不互联 7.68（9.24），读入 4–6 s；进程 3：56 时段 2.64 GiB。
- **Gurobi barrier 统计（T16）：** 一体化 140：Dense cols 5,894、AA' 6.9e6、Factor NZ 1.60e8、Factor Ops 7.7e11、排序 37 s、每次迭代（11–20）4.4 s；一体化 182：6,055、8.6e6、2.26e8、1.29e12、58 s、6.0 s；不互联 140：5,656、6.3e6、8.84e7、2.27e11、31 s、1.9 s；不互联 182：5,817、7.8e6、1.20e8、3.46e11、48 s、2.7 s。
- **两次被 90 % 规则终止的测量：** C3（单进程 112 一体化 T16）RSS 10.5 GiB 时终止，此前已得预求解 1,028,643 行 / 945,229 列、Factor NZ 5.24e8、Factor Ops 1.15e12、排序 76 s、前 9 次迭代每次约 6.5 s；C4（分进程 224 一体化 T16，阈值 200）进程 2 在排序阶段 RSS 10.65 GB 时被看门狗终止，此前已得读入 7.2 s、预求解 15 s、预求解后 2,059,661 行 / 1,886,693 列。
- **`BarIterLimit` 的确认：** Gurobi 12.0.3 在 `BarIterLimit=25` 下照常打印 barrier 统计（Dense cols / Free vars / AA' NZ / Factor NZ / Factor Ops）并在第 25 次迭代后以 ITERATION_LIMIT（状态 7）返回、`SolCount 0`；未单独验证 `BarIterLimit=0`（改用 25 次迭代以同时测每次迭代耗时与因子分配后的内存）。

### 1.3 稠密列区间（INFERENCE，机制解释）

档案参数 `GURO_PAR_BARDENSETHRESH=200`：一列的非零元超过 200 才按稠密列处理。跨时段耦合的列（如容量变量，在每个时段的上界行各有一个非零元）在 2920×3h 问题中有 2,920 个非零元（稠密列），在 365×24h 云端运行中有 365 个（日志 Dense cols 6,486），而截短到 N < 200 时只有 N 个——不作稠密列，留在 AA' 中使填充随 N 超线性增长（112 时段 AA' 3.3e7，比 365 时段的 1.4e7 还大；Factor NZ 5.2e8 ≈ 365 时段的值）。因此 N < 200 的探针不代表正式问题。本机内存又容不下 N > 200 的 T16 Gurobi 进程（C4），所以 C5–C8 对 140 / 182 时段用**测量专用覆盖** `GURO_PAR_BARDENSETHRESH=100`（`b4_split_solve.py --measure`，只对 SMOKE_TEST_ONLY 运行开放，回执记为 `measurement_parameters`；正式档案未改）使耦合列像 2920 时段一样按稠密列处理：Dense cols 5,656–6,055 与云端的 6,248–6,486 同量级，AA' 回到 6–9e6。

### 1.4 外推到 2920（INFERENCE）

方法（`scripts/a1_analysis.py`、`a1_summary.py`；数据点与拟合见 `evidence/REPORT_TABLES.md` 第四表，结果 `evidence/A1_EXTRAPOLATION.json`、`A1_SUMMARY.json`）：
- LP 规模、构建内存、`lp/` 数组、LP 文件：对数-对数幂律（低）与仿射（高）两种拟合取区间；
- Factor NZ / Ops：稠密列区间两点（140、182）的仿射外推为低值，本机幂律为高值，云端 365 点（同一网络的日分辨率版本、同一稠密列结构）按本机 182→云端 365 的指数外推 365→2920 为中值；
- 进程 2 内存 = 非因子部分（本机 RSS 减去 Gurobi 打印的因子内存，随 N 线性；云端 R3 / R4 的 Gurobi 份额减因子作锚定）+ Factor NZ × 13.3–14.3 B；
- 每次迭代秒数 = 云端 T16 每 1e12 Factor Ops 的秒数（R3 一体化 3.86、R4 不互联 7.11；不互联在 2920 取两者之间）× Factor Ops × CPU 因子（8352V 1.15–1.5、EPYC 9754 1.0–1.3，假设）；迭代数区间取第三批 253–465 / 116–228。

| 量 | F1 一体化（低 / 中 / 高） | F2 不互联（低 / 中 / 高） |
|---|---|---|
| LP 行 / 列 / 非零 | 7.94–8.03e7 / 3.52–3.60e7 / 1.87–1.88e8 | 7.67–7.76e7 / 3.41–3.48e7 / 1.79–1.80e8 |
| Factor NZ | 4.48e9 / 6.68e9 / 8.37e9 | 2.16e9 / 2.30e9 / 2.95e9 |
| Factor Ops | 3.49e13 / 1.50e14 / 2.92e14 | 8.15e12 / 2.74e13 / 3.07e13 |
| 进程 1 峰值 | 72–92 GiB | 68–79 GiB |
| 进程 2（Gurobi）峰值 | 90 / 124 / 160 GiB | 68 / 104 / 149 GiB |
| 进程 3 峰值 | 79–115 GiB | 75–99 GiB |
| 单进程峰值 | 162 / 206 / 253 GiB | 136 / 178 / 228 GiB |
| 8470Q T16 每次迭代 | 135 / 580 / 1,127 s | 31 / 150 / 218 s |
| barrier 用时 8470Q | 9.5 / 56 / 146 h | 1.0 / 7.1 / 14 h |
| barrier 用时 8352V | 11 / 75 / 218 h | 1.2 / 9.4 / 21 h |
| barrier 用时 EPYC 9754 | 9.5 / 65 / 189 h | 1.0 / 8.1 / 18 h |
| 本机 i7 T16（参考） | 每次迭代 102–160 s（140 / 182 外推） | 46–111 s |
| 预求解 + 排序 | 1,600–5,700 s | 1,400–5,700 s |
| LP 文件（读后删除） | 5.1–5.4 GB | 5.0–5.2 GB |
| `lp/` 数组 / 解数组 | 6.3–6.4 / 1.2 GB | 6.1 / 1.2 GB |

每个运行在 TimeLimit 之外的开销（INFERENCE，云端单核按本机 1.35 倍计）：进程 1 约 0.25–0.5 h、读入 2–3 min、进程 3 约 1.5–3 h（56 时段 152 s 线性放大）、后处理约 0.5–1.5 h。

### 1.5 候选配置结论与推荐（A1 第 4 项、补充 1）

表见 `evidence/REPORT_TABLES.md` 末表（也在 `RUN_PLAN_B4.md` 第 5 节）。判据：分进程 F1 高值 160 GiB 是否 ≤ 80 % 配额；单进程 253 GiB 同理；并行要求两 Gurobi 进程峰值之和 ≤ 80 % 且 ≥ 33 核；总用时 = 两运行 barrier（F1 按 72 h 封顶）+ 进程 1/3 + 后处理 + 间隔。

| 配置 | 分进程 F1 | 单进程 | F2 并行 | 总用时 h 低 / 中 / 高 | 费用 ¥ | 主要风险 |
|---|---|---|---|---|---|---|
| AutoDL CPU 4 份 128 核 8352V / 240 GB（¥3.1/h） | 可（高值 160 ≤ 178） | 否 | 否 | 18 / 91 / 106 | 54 / 281 / 329 | F1 中值 75 h > 72 h；8352V 速率为假设 |
| AutoDL vGPU-48GB 4 卡 100 核 8470Q / 368 GB（¥11.5/h） | 可 | 可 | 中值可（124 + 104 ≤ 274），高值否 | 14 / 63 / 82 | 156 / 730 / 943 | F1 中值 56 h 接近 72 h |
| AutoDL RTX 4090D 4 卡 72 核 EPYC 9754 / 240 GB / 60 GB 盘（¥7.5/h） | 可（余量小） | 否 | 否 | 16 / 82 / 103 | 120 / 618 / 775 | F1 中值 65 h；EPYC 速率为假设；数据盘需 `REMOVE_LP=1` |
| 阿里云 r8i 256 GiB（约 32 vCPU） | 可 | 否 | 否（核数 < 33） | 16 / 73 / 99 | 以控制台为准 | 同上 |
| 阿里云 r8i 512 GiB（约 64 vCPU） | 可 | 可 | 可 | 14 / 63 / 82 | 以控制台为准 | 费用 |

**推荐（能跑且最稳 → 最省钱）：** ① vGPU-48GB 4 卡 8470Q / 368 GB；② 阿里云 r8i 512 GiB；③ RTX 4090D 4 卡 EPYC 9754 / 240 GB（最省钱的可跑配置）。所有配置的共同风险是 **F1 的 72 h 时限**：中值估计 56 h（8470Q）已接近，高值远超；`RUN_PLAN_B4` 3.4 的早期测速会在前 20 次迭代（中值约 3.5 h）后判定，超过 80 % 即止损报告用户。

### 1.6 磁盘与 60 GB 数据盘（补充 1）

两个运行持久用量约 36 GB（`lp/` 数组 2 × 6.4、解数组 2 × 1.2、对偶 NetCDF 2 × 0.6、求解后网络 2 × 1.3、导出副本与结果包 2 × 4.2、环境 3.3、conda 缓存 0.75、部署包 0.4）+ 瞬时 LP 文件 5.4 GB（进程 2 读入后删除）；保留两份 LP 文件时 46 GB。**60 GB 数据盘够用**；压缩手段已登记（`REMOVE_LP=1` 缺省、`TMPDIR` 在运行目录、结果包与 `lp/` 数组可移到文件存储）。预检要求装环境后可用 ≥ 45 GB。

## 2. 候选配置表

见 1.5 与 `RUN_PLAN_B4.md` 第 5 节；`evidence/A1_SUMMARY.json` 含每项判定的中 / 高两档。

## 3. A2 各手段：测量、等价证明、采用与否

### 3.1 分进程求解（补充 2）——采用（VERIFIED）

- **实现：** `scripts_project/s2_solve.py --split-stage build`（进程 1：与现有路径完全相同地构建 linopy 模型、导出 `lp/` 数组、做目标常数 / 储能单位 / KVL 行缩放，然后用 linopy 自己的写出器 `Model.to_file(io_api="lp")`——即 `Model.solve(io_api=None)` 调用求解器前写临时文件的同一段代码（`constraints.sanitize_zeros / sanitize_infinities`、整数标签 `general`、`slice_size` 2,000,000）——把 `split/problem.lp` 写到运行目录；标签映射就是 `lp/vlabels.npy` / `lp/clabels.npy`（LP 文件中变量名 `x<标签>`、约束名 `c<标签>`）；写 `split/SPLIT_BUILD.json` 后退出）；`scripts_project/b4_split_solve.py`（进程 2：只导入 gurobipy / numpy / psutil，`gurobipy.read` 读入 LP 文件，按 linopy `Gurobi._solve` 的顺序设置档案参数再设 `LogFile`，`optimize()` 一次，把 X / Pi / RC 按标签向量的顺序分块提取（每块 100 万，缺失标签 NaN，与 linopy 的 `reindex` 一致），写 `split/SPLIT_SOLVE.json`（Gurobi 状态码与名称、linopy 的终止条件与状态——同一张 `CONDITION_MAP`、目标值、`BarIterCount`、`Runtime`、`Work`、`MaxMemUsed`、`Fingerprint`、维数、`SolCount`、本进程峰值）与 `gurobi.linopy.log`；`--remove-lp` 读后删文件）；`s2_solve.py --split-stage assign`（进程 3：重建同一模型（`PYTHONHASHSEED=0`），核对重建的标签向量与进程 1 的 `lp/` 逐位相同，用 linopy `Model.solve()` 结果映射的同一段逻辑把数组映射回模型，再走与现有路径完全相同的 unscale → `assign_solution / assign_duals / post_processing` → 导出 / 门控 / 账本链）。
- **等价判据：** (a) Fingerprint：C2 进程 2 读入文件得到 `0xb609266f`，与 C1 单进程日志、M08b 冒烟日志相同；(b) 56×3h 完整求解（档案 A，TimeLimit 1,750 s，与 M08b 冒烟同参数）：C1（单进程）与 C2（分进程）终止状态 optimal、迭代数 129、barrier 工作单元 428.37、LP 目标 305,492,907,999.02893、总目标 307,847,440,010.6307 相同；`solution/X,Pi,RC.npy` 逐字节相同；`lp/` 十个数组、全部 CSV（账本三表、节点价格、容量影子价、跨境流、成本拆分、对偶索引）、全部 JSON（V5 门控、账本恒等式、排放、CO2 流、容量、内点检查、燃料舱、成本摘要、KKT 摘要、EXPORTS、MATH_PROBLEM）相同；求解后网络与 `DUALS_BY_CONSTRAINT.nc` 的每个数据变量逐值相同（文件字节因元数据中的授权文本不同）。证据 `evidence/compare/C2_split_vs_C1_single_56_A.json`（`all_equal: true`）。
- **与旧代码的回归：** C1（新代码单进程）对 M08b 冒烟（旧代码，2026-10-21，同机同档案同 TimeLimit）：以上全部相同（`evidence/compare/C1_newcode_vs_M08b_smoke.json`；唯一差异 EXPORTS.json——冒烟目录后来由后处理登记了 PRECISION / VIOLATIONS 三项，LEDGER_IDENTITY 多 M10R 修复新增的诊断键，已在比较中排除）。
- **T16 档案：** 等价在档案 A 上验证；T16 只改 BarConvTol / Threads，两种方式把同一参数字典传给 Gurobi（进程 3 核对 `SPLIT_SOLVE.json.solver_parameters` 与本运行参数相等，不等即拒绝）。未用 T16 做第二对完整求解（预算），见第 9 节第 4 项。
- **内存与开销：** 见 1.2；LP 文件往返（写 8–23 s、读 2–7 s；外推 2920：写 140–250 s、读 95–155 s）相对 72 h 可忽略。
- **采用：** `RUN_PLAN_B4.md` 3.1 登记 `SOLVE_MODE=split`；`run_batch4.sh` 的三进程调度（墙钟只作用于进程 2；进程 1 / 3 各自 `timeout`）。

### 3.2 直接经 gurobipy 传模型（A2.1）——不采用，只报告（INFERENCE）

未单独测量（8 次调用全部用于 A1 与分进程）。分析：`io_api="direct"` 在同一进程内把 linopy 模型转成 gurobipy 模型，省去 LP 文件往返，但 Python 模型与 Gurobi 模型同驻，峰值不低于单进程方式，与分进程目标相反；LP 文件往返的开销可忽略（3.1）。等价性：`direct` 传入 float64 原值，而 LP 文件用 `%+.12g` 写系数（linopy `io.py`），两种方式交给 Gurobi 的模型不逐位相同（Fingerprint 必然不同），第三批结果来自文件路径；不满足 A2.1 的判据。结论：不采用；分进程保留文件路径。

### 3.3 Gurobi `SoftMemLimit`（A2.2）——不采用为登记参数（未验证）

Gurobi 12 的 `SoftMemLimit`（GB）在超限时于安全点终止，状态 `MEM_LIMIT`（代码 17）；linopy 0.5.5 的 `CONDITION_MAP` 把 17 映射为 `internal_solver_error`（状态 `error`，无解）；`b4_split_solve.py` 用同一映射并另记 `gurobi_status_code / gurobi_status_name`；`b4_batch4.py stop-class` 对无 `solution/X.npy` 的运行分类 `nosol` → 记为不可用并停批（替身测试 `test_mem_limit_status_without_solution_is_nosol_and_stops` 覆盖）。本机未做触发实测与"不触发时逐位相同"的第二次求解（第 8 次调用改用于不互联 182 探针，第 9 节第 5 项）。按无人注守规则"证明不了等价 → 不采用"：不作为登记参数；`run_batch4.sh` 保留 `--protect` 通道，若用户决定采用（建议值 = 配额 GB × 0.85，高于 80 % 的脚本止损线，作为第二道保护）由执行指令登记。

### 3.4 其他（A2.3、A2.4）

- 串行与并行：核数不是瓶颈，两个运行串行即可在 ≥ 25 核机器上进行；并行条件按 A1 写入 `RUN_PLAN_B4` 3.2（P1 探针 40 % + 33 核）。
- 单进程内释放 Python 对象：被分进程取代；进程 3 不重算 `M.A`（`--split-stage assign` 跳过 `export_lp`）。
- 后处理步骤（违反分析、C1、Owen 审计）都重建 LP 模型，峰值与进程 1 同量级（72–92 GiB）：`RUN_PLAN_B4` 3.6 的并存条件由此而来。

## 4. A3 修改

| 项 | 改动 | 具体作用 | 回归 / 测试 |
|---|---|---|---|
| A3.1 求解结果先落盘（提交 `a9ccc129`） | `s2_solve.py` `post_solve()`：求解返回后先写终止状态、目标值、求解秒数、Gurobi 日志统计（`SOLVE_RECEIPT.json`），再 unscale、`assign_solution`、写 `solution/X,Pi,RC.npy` 并再次保存回执，然后对偶导出、各类导出、门控、账本、V5_GATES 逐步进行；每步 `guard()` 捕获异常记入 `post_solve_errors`（步骤、错误、回溯），回执字段 `post_solve_complete`，退出码 4；终止状态与"有返回解"判定不变；`failure` 字段只用于求解前 / 中失败。步骤顺序与每一步的计算与旧代码相同 | 2920×3h 上一天多的求解不再因后处理异常被记为"无返回解"（M10A F12 / M10R 发现 2）；G2.3 照常核对导出完整性，缺项 `--repost` 补做 | C1 对 M08b 冒烟全部相同（3.1）；9 类网络后处理链回归（M10R `drill_postproc.sh` 在 B4P 代码上重跑：M08b 冒烟一体化 / 不互联、M12b 去 VN / TH / LA、M10R 保留存量 / b1 / 分国 WACC 不互联、合成分国 WACC 一体化，与 M10R 演练输出用 M10R 比较器逐项比较）**9 类全部相同**（每类 17–18 个文件，共约 37,400 个数值逐位相同；`evidence/regress/REGRESS_*.json`，547 s）；`test_b4p_split.py`（静态顺序；真实 56 网络 + 合成数组 + 注入 `co2_flows` 异常：回执保留 optimal、目标、解数组，`post_solve_errors=["co2_flows"]`，退出 4，分类非 nosol）；`test_b4p_batch4.py::test_post_solve_error_keeps_status_and_solution`（整链） |
| A3.2 路径规范化（`15482e3f`，分支代理） | `run_batch3.sh`：参数解析后 `abspath()`（`readlink -m`）把 `--into`、`--arrays`、`--use R=<dir>` 转完整路径（相对调用目录），START 行记录；`run_batch4.sh` 同样（`abs()`） | M10S1 的执行偏差（相对路径落进 repo/）不再发生 | `test_b4p_paths.py` 2 passed（相对 / 完整路径逐项相同、拒绝规则不变）；批次模式回归 `test_m10p_batch3.py` 33 passed、`test_m10r_s1_modes.py` 8 passed |
| A3.3 conda 按频道镜像（`15482e3f`，分支代理） | `install_env.sh`：`CONDA_MIRROR_CONDA_FORGE / _BIOCONDA / _GUROBI` 分别替换该频道前缀，未设频道直连；旧 `CONDA_MIRROR` 兼容；URL 格式检查；每个被替换频道取前两个包 URL 做 1 KB 范围请求可达性检查（`MIRROR_OK` / `MIRROR_CHECK_FAILED`，退出 2）；`--check-mirrors` 只检查不装 | M10 发现 6：国内镜像无 gurobi 频道时 conda-forge / bioconda 走镜像、gurobi 直连 | `test_b4p_install_env.py` 6 passed（本机回环 http.server + mock curl，不访问真实镜像） |
| A3.4 第三批脚本批次模式 | 未改动 | — | 上述回归全过 |

## 5. `RUN_PLAN_B4.md` 登记原文

全文见 `RUN_PLAN_B4.md`（提交 `96eafa53`）。登记值摘要：TimeLimit 259,200 s；进程 2 墙钟 266,400 s（+ 2 × 3,600 s：读入 ≤ 154 s + 解数组写出 ≤ 1,800 s）；进程 1 / 3 超时 3,600 / 32,400 s；许可间隔 330 s；`SOLVE_MODE=split`；P1 探针 3,600 s 窗口、40 % 配额、≥ 33 核；内存止损 cgroup 匿名内存 > 80 %；早期测速第 11–20 次迭代 × 450 / 250 + 已用 > 80 % TimeLimit；分级停批（G2 / 无解 / C1 (a) → 停批，两个运行都算）；后处理并存条件空闲匿名内存 ≥ 100 GiB；单步超时 10,800 s；资源重开需用户授权；预检下限 25 核 / 190 GiB / 45 GB；并行需 ≥ 33 核、≥ 343 GiB；`REMOVE_LP=1`。

## 6. 演练、全量测试、v7 包与干跑

### 6.1 后处理演练（A5.1；`scripts/drill_b4.sh`，提交 `f806e3e7`；`evidence/DRILL_B4.json`；VERIFIED）

截短 2920×3h 网络上的完整后处理链（账本重做与 B16 → 违反分析 → C1（M08b 冒烟参照）→ M12 分摊 → Owen 对偶形式审计 → GATES_V6 → 分级分类），每步 GNU time 计时与峰值：

| 类型 | 来源 | 时段 | 账本 s / GiB | 违反分析 s / GiB | C1 s / GiB | M12 s / GiB | Owen s / GiB | B16 相对误差 | C1 abc | 标签 / 类别 |
|---|---|---|---|---|---|---|---|---|---|---|
| 一体化 | 真实（C2 分进程 56） | 56 | 3 / 0.49 | 20 / 2.33 | 18 / 2.34 | 3 / 0.50 | 19 / 2.19 | 7.9e-12 | 111 | ACCEPTED_LAYER2 / accepted |
| 不互联 | 真实（M08b 冒烟 56） | 56 | 3 / 0.49 | 18 / 2.04 | 15 / 2.05 | 3 / 0.49 | 16 / 1.91 | 2.5e-12 | 111 | ACCEPTED_LAYER2 / accepted |
| 一体化 | 合成（`m10r_synthetic_solution.py`，57 s / 6.11 GiB） | 182 | 3 / 0.60 | 55 / 6.59 | 44 / 6.66 | 3 / 0.60 | 30 / 6.14 | 2.0e-11 | 011 | NOT_ACCEPTED / c1a（合成解，预期） |
| 不互联 | 合成（41 s / 5.30 GiB） | 182 | 3 / 0.59 | 42 / 5.74 | 35 / 5.78 | 4 / 0.60 | 25 / 5.30 | 2.0e-11 | 011 | NOT_ACCEPTED / c1a（合成解，预期） |

合成解只验证"跑通、不报错、恒等式可算"（B16 可算、M12 恒等式可算、Owen 可用），不是结果。**后处理外推（INFERENCE）：** 违反分析 / C1 / Owen 的峰值随时段线性（56 → 182：2.3 → 6.6 GiB），与进程 1 的构建峰值同量级（重建 LP 模型）→ 2920 约 72–92 GiB、每步约 55 s × 16 × 1.35 ≈ 20 min（一体化）；这就是 `RUN_PLAN_B4` 3.6 的 `POST_MEM_NEED_GIB=100` 与 `POST_TIMEOUT_S=10,800` 的依据。

### 6.2 全量测试（A5.2；VERIFIED）

`tests/research` 全量：**655 passed / 69 skipped / 0 failed**（1,285 s，`evidence/tests/TESTS_full.log`；基线 631 / 67，新增 25 个用例全部通过；跳过项都是现有的数据依赖用例，worktree 只有 `assembly_v1` / `s1` 符号链接；五个玩具 LP 求解（HiGHS / linprog）按 M10P / M10R 的做法照常运行，未调用 Gurobi）。新增测试：`test_b4p_split.py` 7（分进程状态映射与 linopy 一致、按标签取值、合成数组映射、LP 写出器、A3.1 顺序、真实 56 网络注入异常）、`test_b4p_batch4.py` 10（运行表与阈值、辅助函数、串行与续跑、探针并行、内存止损、早期测速止损、MEM_LIMIT 无解 → nosol 停批、求解后异常保留解、BUILD_ONLY 与单进程模式、正式运行拒绝钩子与未登记值）、`test_b4p_paths.py` 2、`test_b4p_install_env.py` 6；第三批替身回归 `test_m10p_batch3.py` 33、`test_m10r_s1_modes.py` 8 全过。

### 6.3 部署包 v7（A5.3；VERIFIED）

`work/p1_b4p_20261026/cloud_package_dist_b4/`（新目录，不覆盖第三批的包）：提交 **`f806e3e7`**，**19 个文件 / 213,805,295 B**（代码归档 `code_f806e3e7.tar.gz` 82,536,874 B，不含顶层 `research/`；两个 2920×3h 网络 64,106,133 + 63,439,167 B 及构建回执、成本表；`run_batch4.sh`、`preflight.sh`、`pack_results.sh`、`env/`（第三批同一锁定：538 个 conda 包 742.8 MB + 2 个 PyPI 包）、`RUN_PLAN_B4.md`、`BUILD_INPUT_CHANGES.json`、`COMMIT`、`SHA256SUMS`、`PACKAGE_MANIFEST.json`）。`PACKAGE_MANIFEST.json` SHA256 `c0168cfe804a769b7ef03c22ef881e7077c34ce5de6bc69c336df75e37bd1a84`；`SHA256SUMS` SHA256 `b0a0ddf774f7240ff1ed4da1000d16f230df6ed1443febb661b73164b4da9b4f`。**网络 SHA256 = 登记值**（打包脚本按登记值与字节数核对后才复制；清单 `networks_equal_registered: true`）；不含任何 365×24h 文件；构建输入核对：自 `ec80668f` 起 11 个改动文件都在 `s2_network.py` 的导入闭包之外（`BUILD_INPUT_CHANGES.json`，无拒绝项）；演练记录 `DRILL_B4.json`（SHA256 `e48b2282…f1fe`，提交 `f806e3e7`，4 类全部跑通）写入清单。上传量约 214 MB：36 / 100 / 318 KB/s 下约 1.65 / 0.59 / 0.19 h。

### 6.4 干跑（A5.4；VERIFIED）

包解到 `/home/jin/b4p_dry/pkg`：
- **预检：** `guards` 节干净 shell 通过、残留 `SPLIT_CMD` 时失败（负例）；`sha`（19 / 19 OK，代码解包到 `./repo`）、`networks`（2920×3h 两网络 = 构建回执 = 登记值；无 365×24h）、`env`（284 / 284 包相同）、`profile`（T16、内点门控路径、TimeLimit 259,200）、`code`（八个模块导入；运行表 F1 / F2；阈值 0.8 / 0.8 / 0.4 / 33 / 3,600）、`tools` → **PREFLIGHT OK**；`resources` 节在本机失败（16 核 / 10.9 GiB / 数据盘不足，属预期，`licence` 节未在本机运行）。
- **BUILD_ONLY（截短 56，`ALLOW_UNREGISTERED=1 TRUNCATE=56`）：** F1、F2 各走进程 1（29 / 25 s，峰值 2.19 / 1.90 GiB，LP 文件 94 / 91 MB），回执状态 `split_built`，`BUILD_CHECK.json` 两运行 **passed**（参数 = 档案 + TimeLimit、网络 SHA256 = 登记、G2.2 子集哈希相等、LP 已导出、问题文件存在），无求解器日志、许可变量未传给进程 1；批级汇总与打包正常，`DONE`（56 s）。
- **合成整链（替身进程 2 写零解，进程 1 / 3 与后处理全部真实；242 s）：** `BUILD_F1`（30 s，2.18 GiB）→ 替身 `GUROBI_F1`（OPTIMAL）→ `ASSIGN_F1`（真实进程 3：映射 + 全部导出，exit 0，`post_solve_errors=[]`，2.65 GiB）→ `RUN_F1:optimal:receipt=post_solve` → 违反分析、C1、M12（零解下 M12 退出 1 记为 `POSTPROC_ERROR`，调度不变）→ `V6_F1:NOT_ACCEPTED` → 分级 `c1a` → `UNUSABLE:F1` 并停批 → 批级汇总（F2 未启动）→ `PACK_halted`（轻量 / 完整包）→ `HALTED` 退出码 3。即"构建 → 替身求解 → 后处理 → 批级汇总 → 打包"全程走通，停批路径按登记规则执行。
- **真实结果重放（F1 = C2 的分进程结果、进程 2 替身为空操作，F2 = M08b 冒烟作为已结束运行）：** 进程 3 **正确地拒绝**了 C2 的结果——C2 是档案 A（BarConvTol 1e-8、Threads 8），而登记的 F1 档案是 T16，`split assign` 的参数核对抛出 `ValueError`（exit 1）→ F1 记为无返回解 `nosol` → 停批；F2 的续跑路径（`SKIP_ENDED`）正常。这证明参数核对防护有效；真实数据上的整链已由 6.1 的演练与 C2 本身覆盖，未再用 T16 档案重做（无调用预算）。
- **钩子与未登记值的拒绝（正式命令）：** 残留 `SPLIT_CMD` → `REFUSED`（退出 2）；`SOLVE_MODE=single` → `REFUSED: SOLVE_MODE=single differs from the registered value split`；`BUILD_ONLY=1` 与 `--auth` 同时 → `REFUSED`；三种情形均未创建运行目录。
- **完整 2920×3h 网络：** 只核对了 SHA256（= 登记值）与可读性（预检 `networks` 节 `base-check` 读取回执并哈希文件），未在本机构建。
- 证据：`evidence/dryrun/DRYRUN_SUMMARY.json` 及各步 STATUS / 回执副本。

## 7. 本机 Gurobi 使用记录（VERIFIED；`B4P_EVIDENCE.json` gurobi_usage）

| 次 | 内容 | 开始（UTC） | 结束（UTC） | 间隔 s | 时长 s | 结果 | Gurobi 进程峰值 |
|---|---|---|---|---|---|---|---|
| 1 | C1 一体化 56，单进程，档案 A | 19:33:33 | 19:40:20 | — | 407 | optimal，129 次 | 4.74 GiB（单进程） |
| 2 | C2 一体化 56，分进程，档案 A | 19:58:37 | 20:02:34 | 1,097 | 237 | OPTIMAL，129 次，与 C1 逐位相同 | 3.62 GiB |
| 3 | C3 一体化 112，单进程，T16 | 20:07:36 | 20:10:40 | 302 | 184 | 90 % 规则终止（RSS 10.5 GiB）；得 barrier 统计 | ≥ 10.5 GiB |
| 4 | C4 一体化 224，分进程探针（阈值 200），T16 | 20:16:09 | 20:16:56 | 329 | 47 | 看门狗终止（排序阶段 RSS 10.65 GB）；得预求解规模 | ≥ 10.65 GB |
| 5 | C5 一体化 140，探针 25 次，阈值 100 | 20:22:00 | 20:24:52 | 304 | 172 | ITERATION_LIMIT，统计齐全 | 6.66 GiB |
| 6 | C6 不互联 140，探针 25 次，阈值 100 | 20:29:55 | 20:31:31 | 303 | 96 | ITERATION_LIMIT | 5.81 GiB |
| 7 | C7 一体化 182，探针 25 次，阈值 100 | 20:36:34 | 20:40:26 | 303 | 232 | ITERATION_LIMIT | 7.76 GiB |
| 8 | C8 不互联 182，探针 25 次，阈值 100 | 20:45:27 | 20:47:49 | 301 | 142 | ITERATION_LIMIT | 7.68 GiB |

全部 2026-10-25（UTC；SGT 为 26 日 03:33–04:48）；全部截短 2920×3h 网络（≤ 224 时段）；最长 407 s（上限 3,600 s）；最短间隔 301 s（≥ 300 s）；不重试。一次未消耗调用的拒绝（C2 第一次尝试：分支代理的替身进程被运行器计为求解进程）与一次在 Gurobi 启动前停止的排队（112 分进程）记录在 `SOLVES_STATUS.txt`。

**本机计算时间（上限 5 h）：** 约 **1.8 h**（`B4P_EVIDENCE.json` compute_time：构建测量 3 min、8 次调用的三个进程合计约 40 min、分支代理的测试 15 min、新增测试两轮 8 min、演练 6 min、9 类回归 9 min、全量测试 21 min、打包 11 s、干跑约 6 min；等待间隔不计）。**磁盘新增：** 约 **10 GB**（上限 40 GB）：主检出 `results_project/b4p/` 7.9 GB（截短构建与求解目录、LP 文件、演练、回归）、干跑目录 1.3 GB、工作目录 0.2 GB（含 v7 包 214 MB）、worktree 0.6 GB。

## 8. 云端执行指令需要的值与步骤（PROPOSED）

1. **机器：** 按 1.5 推荐，用户决定；预检硬下限 25 核 / 190 GiB / 45 GB 可用数据盘（装好环境后）；并行需 ≥ 33 核与 ≥ 343 GiB。
2. **上传：** 包 v7 `work/p1_b4p_20261026/cloud_package_dist_b4/`（提交 `f806e3e7`，19 文件，213,805,295 B，`SHA256SUMS` SHA256 `b0a0ddf7…9b4f`，清单 `c0168cfe…1a84`）；单路 rsync + `sha256sum -c SHA256SUMS`（19 / 19）；网络 SHA256 必须等于登记值（预检 `networks` 节核对）；许可只在全部核对通过后放置。
3. **环境：** `bash env/install_env.sh`（先 `--check-mirrors`；`CONDA_MIRROR_CONDA_FORGE / _BIOCONDA` 可设国内镜像，gurobi 频道直连）；`env_check.py` 关键包相同。
4. **预检：** 在将要运行的 tmux shell 中 `PY=… GRB_LICENSE_FILE=… bash preflight.sh` → `PREFLIGHT OK`（guards / sha / networks / env / profile / code / tools / licence / resources）。
5. **启动：** `PY=… GRB_LICENSE_FILE=… BATCH3_EXPORT=<第三批 export 目录，可选> bash run_batch4.sh --auth "<用户授权原文>"`；中断后同一命令续跑；只重做后处理 `POST_ONLY=1`（不带 `--auth`）。
6. **监控要点：** `runs/batch4/STATUS.txt`（`BUILD_F1`、`SOLVE_F1`、`PROJECTION_F1`、`P1_PROBE`、`GUROBI_F1`、`ASSIGN_F1`、`V6_F1` …）；`MONITOR_F1.csv` 的 `cgroup_anon_gib` 列对配额；`P1_DECISION.json`（F1 Gurobi 启动 1 h 后）；`PROJECTION_F1.json`（第 20 次迭代后，中值约 3.5 h）；停批行 `STOP_SAFE:MEMORY` / `STOP_SAFE:PROJECTION` / `STOP_NOT_ACCEPTED` / `UNUSABLE`。
7. **判定点：** P1（3.2）：峰值 ≤ 40 % 且 ≥ 33 核 → F2 并行，否则串行；早期测速（3.4）：预计总用时 > 207,360 s → 止损；内存（3.3）：匿名内存 > 80 % → 止损。止损后由用户决定更大机器 / 更长登记时限重开（3.8）。
8. **回收：** 轻量包 → 完整包（含求解后网络与对偶 NetCDF，每运行约 2 GB）；LP / 解数组留在数据盘或移到文件存储；删除许可并核实。

## 9. 发现但未处理；未经用户确认的决定；需要用户决定的事项

**未经用户确认的决定（无人值守规则第 1 条）：**
1. **C3 终止：** 112 时段单进程 T16 求解在首次因子分解时 RSS 10.5 GiB（WSL 10.95 GiB，可用 67 MB）→ 按"超过 90 % 立即终止"手动终止；记录到该点；不重试；计入 8 次。
2. **剩余调用改到稠密列区间：** 发现 `GURO_PAR_BARDENSETHRESH=200` 的结构区间问题（1.3）后，原 C4（112 分进程 T16 完整求解）在 Gurobi 启动前停止（未消耗调用），改为 224 时段探针；C4 被看门狗终止后，C5–C8 改为 140 / 182 时段 + 测量覆盖阈值 100 + 25 次迭代。理由：用与正式问题同一结构区间的数据外推（保守一侧）；覆盖只用于测量，正式档案不变。
3. **273 / 365 时段构建不做**（182 峰值 × 1.55 > 8.5 GiB；90 % 规则）；N > 200 的 T16 Gurobi 进程本机容不下（C4）。
4. **分进程的 T16 等价：** 在档案 A 上验证（3.1），T16 不另做第二对完整求解。
5. **SoftMemLimit：** 第 8 次调用用于不互联 182 探针（A1 优先级高于 A2 其余），触发测试与不触发等价都未做；不采用为登记参数。
6. **直接传模型：** 未测量，按分析不采用。
7. **分支代理的替身测试与本机求解冲突：** C2 第一次尝试被运行器拒绝（未消耗调用），删除进程 1 产物后重跑。
8. **外推取值：** Factor NZ / Ops 取仿射（低）、云端锚定幂律（中）、本机幂律（高）；候选配置判定用中 / 高两档并分别给出。
9. **测量脚本的看门狗（`solve3.sh`）：** 可用内存 < 10 % 即终止进程组，作为 90 % 规则的自动实现。
10. **干跑的"真实结果重放"未改档案：** 进程 3 拒绝档案 A 的 C2 结果是正确行为，未为干跑增加绕过参数核对的钩子；合成整链与演练覆盖其余路径。
11. **修复轮次：** 新增测试两轮修复（替身网络的登记 SHA 核对改为 `--no-registered` 仅限 `ALLOW_UNREGISTERED=1`；终止原因不被 `split_built` 覆盖；NOSOLVE 模式两运行都构建；测试期望）；演练脚本 `local` 展开顺序一处；打包脚本调用路径一处；干跑占位许可文件一处——均 ≤ 3 轮，无未解决项。

**发现但未处理：**
- 72 h 时限对 F1 可能不够（1.4）；`RUN_PLAN_B4` 3.1 登记了风险并靠 3.4 止损；延长时限需用户在执行指令中重新登记。
- 进程 3 与后处理步骤都重建 LP 模型（72–92 GiB）：第四批的后处理只能在另一个求解之外或内存余量 ≥ 100 GiB 时进行；可进一步改为从 `lp/` 数组而非重建模型做映射（未做）。
- 本机 56 时段的单进程 / 分进程求解在 T16 下未做；`c3` 的单进程 112 数据只有求解前阶段。
- `RUN_PLAN.md`（第三批）11.2 节的相对路径示例未改文字（代理报告）。

**需要用户决定：** 机器选择（1.5）；是否采用 `SoftMemLimit`（3.3）；并行阈值 40 % / 33 核是否维持（3.2）；是否在上云前把 TimeLimit 改为更长的登记值（例如 120 h）或接受"早期测速止损 → 重开"的流程；是否接受本报告的测量覆盖（阈值 100）作为外推依据。
