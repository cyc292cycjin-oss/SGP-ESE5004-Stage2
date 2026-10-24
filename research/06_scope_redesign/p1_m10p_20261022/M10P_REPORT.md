# M10P 报告：第三批上云准备（本机；不连云）——整合分支、运行清单、事先登记规则、部署包、本机干跑

**摘要（2026-10-22；只做本机准备：未连云、未上传、未调用 Gurobi）**
1. **整合：** 分支 `codex/m10-batch3-20261022` 自 M12b 头 `1f46517d`；#45、#47、#46、#48 与 S4Q #41（`FIXED_RUNS`）的全部提交已在其中，**无需 merge**。
2. **测试：** 整合分支 582 passed / 67 skipped / 0 failed；最终代码 `eac6c3e0` **595 passed / 67 skipped / 0 failed**。
3. **网络：** 干净提交上重建的四个网络 SHA256 都不同 → 按第 1.4 节停下；原因是元数据中构建 worktree 的绝对路径（`s2_network.py:344`），数据逐项相同。**用户决定 A：入包用 `ec80668f` 原构建**（`75704334…` / `888a009b…` / `bca20fc0…`）。
4. **运行清单与事先登记规则：** `RUN_PLAN.md`（R1–R11 + P1、两会话与线程预算、许可间隔、临时→本批参照重评、D12 停批、第四批档案选择、批级后处理、安全停止、断点续跑）；运行脚本 `run_batch3.sh`。
5. **部署包：** `cloud_package_dist/`（提交 `eac6c3e0`，23 个文件 283.7 MB，清单 `PACKAGE_MANIFEST.json` 逐文件 SHA256）；非克隆部署环境下载约 743 MB、预计 5–15 分钟；单路上传约 0.5–2.2 h。
6. **干跑：** 第一版包发现分国 WACC 变体的 SHA256 随目录变化（`m08a_variants.py` 写入了成本表绝对路径）→ 修正后重建；第二版：预检 OK，7 个变体三遍逐字节相同，R1–R11 全部"构建完成、求解前退出"且核对通过，P1 参数核对通过，后处理演练与 M12b 证据差 0.0 EUR。
7. **需你决定（第 8 节）：** 25 核上 R3 / R4 先后跑是否接受；无解运行是否停批（含敏感性）；P1 内存风险；实例规格；代码归档是否瘦身；两处路径依赖的处理。
8. **补充 01（第 142 项，第 10 节）：** 第 8 节六项已由用户决定并落实；部署包 v3（`e0527cec`，148.6 MB，不含 `research/` 与 2920×3h 网络）通过第二次干跑。

等级：整合核对、测试、SHA256、干跑结果为 VERIFIED（回执与文件比较）；时长、磁盘、内存（P1）与安装时间为 INFERENCE。

---

## 1. 整合结果

- 分支 `codex/m10-batch3-20261022`，worktree `/home/jin/wt_m10p_20261022`，自 M12b 头 `1f46517d`（已含 M08a、M08b 补充 01、M12、M12 补充 01）。
- 逐 PR 核对（`evidence/M10P_PR_COMMIT_CHECK.json`，PR 提交列表 `evidence/pr_*.json`）：

| PR | 内容 | 提交数 | 缺失 | 头在分支中 |
|---|---|---|---|---|
| #45 | M08a | 23 | 0 | 是 |
| #47 | M08b（含补充 01） | 14 | 0 | 是 |
| #46 | M12（含补充 01） | 20 | 0 | 是 |
| #48 | M12b | 20 | 0 | 是 |
| #41 | S4Q（`FIXED_RUNS` 提交 `84532e78`、两个 1e-6 档案） | 5 | 0 | 是 |

- 无需补 merge；未 rebase、未 force-push。
- 被 git 忽略、测试会读取的 2 个输入文件（`research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv`、`DISCOUNT_RATE_IN_USE.csv`）自 M12 worktree 复制，与 M12b 测试所用相同。分国 WACC 变体所用的 `COUNTRY_WACC_REAL_M08A.csv` 已入库，`git archive` 会带上。

## 2. 测试

| 时点 | 提交 | 结果 | 日志 |
|---|---|---|---|
| 整合分支（第 1.3 节） | `1f46517d` | **582 passed、67 skipped、0 failed**（155.9 s） | `evidence/M10P_FULL_TESTS_m10p1.log` |
| 加入运行脚本测试后 | `be1ce466` 之前（工作树含 M10P-3 改动） | 593 passed、67 skipped、0 failed | `evidence/M10P_FULL_TESTS_m10p3.log` |
| 最终代码 | `eac6c3e0` | **595 passed、67 skipped、0 failed**（285 s） | `evidence/M10P_FULL_TESTS_m10p_final.log` |

- 指令允许玩具 LP，故不再排除 5 个玩具求解用例：3 个运行并通过（HiGHS / scipy），2 个因缺本机数据跳过（`test_s3b_r4`、`test_s4c_3`）。与 M12b 的 579 passed / 65 skipped / 5 deselected 对得上（582 = 579 + 3，67 = 65 + 2）。未调用 Gurobi。
- 新增测试（13 项）：`tests/research/test_m10p_batch3.py` 12 项——运行表与登记计划一致；`--stop-before-solve` 在求解调用之前退出；完整批次的顺序、R1 | R2 并行、25 核上 R3 / R4 先后、32 核上并行、通道内与阶段间间隔、每个运行只求解一次、临时判定→本批参照重评与 `grade_history`、只因 C1 (b) 的 NOT_ACCEPTED 不停批、C1 (a) 不通过停批且另一通道跑完、墙钟终止整个进程组、续跑不重解与"已开始未结束"的安全停止、变体 SHA256 不符的安全停止、干跑模式（许可绊线）、`POST_ONLY`、未登记时限被拒、打包许可扫描、P1 解析、缺第二级运行时回落档案 A（全部用替身流水线，无求解器）；`test_m08a_a7.py::test_wacc_variant_bytes_independent_of_the_folder`（修正前失败、修正后通过）。

## 3. 网络与 SHA256（第 1.4 节）

**重建（停止条件触发）：** 在干净提交 `b46fc23d` 上（dirty 0；`/home/jin/m10p_build.sh`，同 M08b 做法），`PYTHONHASHSEED=0`，`s2_network.py` 两次构建写出四个网络（各 87 s / 76 s，峰值 0.75 GiB，`S2_SCENARIO_BUILT_STATIC_PASS`）。四个 SHA256 全部与 `ec80668f` 构建不同，按指令停下报告。

| 网络 | 大小（B） | 重建（`b46fc23d`） | `ec80668f` 构建（入包） |
|---|---|---|---|
| `integrated_2920_3h_unsolved.nc` | 64,106,133 | `5a47e15b…24384f4` | **`bca20fc08a149772074b620e1f587e86b0306c29e81d138fa67f4a9b9ae53cab`** |
| `integrated_365_24h_unsolved.nc` | 31,524,926 | `4406fc65…dd63c0e` | **`75704334dc11deeb06fc80f84ef197d65c3ac5bd658ab450e4ee1a93a3ccb19e`** |
| `disconnected_2920_3h_unsolved.nc` | 63,439,167 | `117d8168…8969dd44` | `b401a68729524c885a8245962bc2a46706a1760c42ef40bdd9943e60a859bcc7`（不入包） |
| `disconnected_365_24h_unsolved.nc` | 30,857,960 | `1695487e…3c1c3853a` | **`888a009b5f19eb34f7f1c24e36f7c8370617a9c405b1097a9caed0599cecbee4`** |

**原因（VERIFIED，`evidence/M10P_NETWORK_CONTENT_DIFF.json`）：** 四个网络的全部组件静态表、全部时间序列、快照与权重逐项相同；元数据逐键比较只有一处不同——`s2_layers.geothermal.bus_mapping_source.path`，即构建所在 worktree 下集成契约文件的绝对路径（`/home/jin/wt_m08b_20261021/…` → `/home/jin/wt_m10p_20261022/…`），由 `scripts_project/s2_network.py:344` 写入；同一行记录的文件 SHA256 相同。构建回执的差异也只有路径与 `code_sha`。

**用户决定（2026-10-22，会话中）：A**——部署包用 `ec80668f` 原构建（主检出 `results_project/m08b/builds_s01/`，即 M08b 冒烟与 M12b 去一国所用、G2.1 已登记的文件）；本次重建作为"内容相同"的复核证据（包内 `NETWORK_REBUILD_CHECK.json`）。

**构建输入检查（`make_package.sh`，包内 `BUILD_INPUT_CHANGES.json`）：** `ec80668f` 之后改动的 6 个脚本（`m08a_run_batch.sh`、`m08a_variants.py`、`m10_batch3_summary.py`、`m12_allocation.py`、`m12_rhs_audit.py`、`s2_solve.py`）都不在构建入口 `s2_network.py` 的导入闭包内；`configs/`、`research_inputs/` 未变。

## 4. 运行清单、规则与部署包

- **运行清单与事先登记的规则：** 见 `RUN_PLAN.md`（第 2、3 节；入包）。要点：
  - R1–R11 为 365×24h，P1 为 2920×3h 探针；档案 A，R3、R4 为 1e-6 T16；TimeLimit 21,600 s / 墙钟 22,500 s，P1 墙钟 3,600 s；不重试、不改参数、不 warm start。
  - 两会话只在两档案 Threads 之和不超过容器核数时同时跑：25 核上 R1 | R2、第 3 阶段两条通道并行，**R3、R4（16 + 16）先后跑**。
  - 顺序：[R1 | R2] → 本批参照与重评 → [R3, R4] → 第二级比较 → 通道 A：R5 → R7 → R9 → R11 / 通道 B：R6 → R8 → R10 → 批级后处理与打包 → P1 单独跑 → 最终打包。
  - 许可：同一通道内、每个阶段开始前（含脚本启动后）≥ 330 s。
  - 验收、阈值参照（临时判定 → 本批参照重评，`grade_history`）、停批（只 C1 (a) / G2，D12）、对偶形式（第 138 项）、第四批档案选择、后处理与批级后处理、安全停止、断点续跑：按指令第 3 节写入，详见 `RUN_PLAN.md` 第 3 节。
- **运行脚本 `run_batch3.sh`**（在 `m08a_run_batch.sh` 之上扩展，并吸收 S4O 云端脚本的进程组、墙钟、监控、清洗导出）：
  - 第 0 阶段（不用许可）：输入齐全、基础网络 SHA256 = 构建回执、生成 7 个变体并与本机期望 SHA256 比较；
  - 每个运行求解一次；`.started` / `.ended` 标记——续跑时已结束的跳过，已开始未结束的安全停止，不重跑；
  - 后处理每步只补缺失输出，可重复；`POST_ONLY=1` 只做后处理（不启动任何求解，可在云端单独重跑后处理）；`BUILD_ONLY=1` 为本机干跑；
  - 启动时拒绝与登记值不同的时限 / 间隔。
- **辅助模块 `scripts_project/m10_batch3_summary.py`：** 运行表唯一来源、基础网络与变体核对、干跑构建核对、P1 参数核对、`LEVEL2.json`、B6、敏感性差额（R8 / R9 / R11 对 R2，R10 对 R1；另列 R11 − R10 作信息项）、批级汇总 `BATCH3_SUMMARY.{json,md}`、P1 计时与内存解析。
- **`s2_solve.py --stop-before-solve`：** LP 构建并导出、求解参数确定并写入回执后，在调用求解器之前退出（`optimize_calls` 为 0）。
- **部署包 `cloud_package_dist/`（不入库；`make_package.sh` 在提交 `eac6c3e0` 上生成）：** 23 个文件，283,737,685 B，每个文件的 SHA256 见 `PACKAGE_MANIFEST.json` 与 `SHA256SUMS`（副本在 `evidence/package/`）：
  - `code_eac6c3e0.tar.gz`：该提交的 `git archive`；
  - `networks/`：`ec80668f` 原构建的三个网络（365×24h 一体化 / 不互联、2920×3h 一体化）、两份构建回执、两份成本表（两表内容相同，SHA256 `7cee9c1a…`）；
  - `EXPECTED_VARIANTS.json`：7 个变体的期望 SHA256（打包时两遍生成，逐字节相同，`VARIANT_REPRODUCIBILITY.json`）；变体不上传；
  - `run_batch3.sh`、`preflight.sh`、`pack_results.sh`、`RUN_PLAN.md`、`env/`、`BUILD_INPUT_CHANGES.json`、`NETWORK_REBUILD_CHECK.json`、`COMMIT`。
  - 不含：许可、cutout、LP / 解数组、变体网络、任何结果。
- **环境（非克隆部署，S4N 补充 01 做法）：** `env/ENV_LOCK.txt`（python 3.11.13、284 个 pip 包、conda 清单）、`env/conda_explicit_linux64.txt`（538 个包的精确构建与 md5）、`env/pip_only.txt`（2 个 PyPI 包）、`env/install_env.sh`、`env/env_check.py`（关键包必须完全相同）。下载约 743 MB（`env/ENV_DOWNLOAD.json`，本机 `conda-meta` 记录，未联网），安装后约 3.3 GiB，**预计 5–15 分钟**（2–20 MB/s，INFERENCE）。不需要较大的环境文件（未打包 conda 环境）。
- **预检 `preflight.sh`：** SHA256SUMS 与解包、网络与回执、环境与锁定清单、两档案参数、代码导入、工具、许可是否可用（输出全部屏蔽）、资源（核 ≥ 16、内存 ≥ 72 GiB、磁盘 ≥ 50 GiB）。
- **结果打包 `pack_results.sh`：** 轻量包（除 NetCDF 外的全部导出）与完整包（加求解后网络与 `DUALS_BY_CONSTRAINT.nc`）分开；LP / 解数组与原始求解日志不打包（`ARRAYS_MANIFEST.json` 记 SHA256）；发现许可特征串即拒绝打包。P1 之前先打包一次（`pre_p1`）。

## 5. 本机干跑（第 5 节；不调用 Gurobi）

全部在 WSL 中、移除 `GRB_LICENSE_FILE` 后运行；运行脚本的干跑模式把许可变量指向不存在的文件（任何 Gurobi 环境都会失败），求解调用 0 次。脚本 `scripts/m10p_dryrun.sh`，证据 `evidence/dryrun/`。

### 5.1 按云端目录结构解包与预检

- 部署包复制到 `/home/jin/m10p_dry/pkg`；`preflight.sh`（不含许可一节）：**PREFLIGHT OK**——23 个文件 SHA256 全对；代码解包到 `./repo`（`eac6c3e0`）；三个基础网络 = 构建回执；`EXPECTED_VARIANTS.json` 7 条；环境与 `env/ENV_LOCK.txt` 284 / 284 个包版本逐一相同；两档案参数名、内点门槛路径、Threads 8 / 16 正确；运行与后处理模块无许可可导入、运行表 12 个；GNU time、setsid、pgrep、tmux 齐全。
- 资源一节在本机不满足（16 核、11 GiB 内存 < 72 GiB）——本机信息，不影响结论（`evidence/dryrun/PREFLIGHT_RESOURCES_LOCAL.txt`）。

### 5.2 变体生成与 SHA256 复现

- **第一版包（`be1ce466`）：** R5–R9 与期望相同，**R10 不同 → 安全停止**；原因与修正见第 7 节第 3 项（`evidence/dryrun_v1_be1ce466/FINDING_R10_VARIANT_SHA256.md`）。
- **第二版包（`eac6c3e0`）：** 打包时两遍 + 解包目录中运行脚本第 0 阶段第三遍，**7 个变体三遍逐字节相同**，`stale_config` 均为 false：

| 运行 | 变体文件 | 大小（B） | SHA256 |
|---|---|---|---|
| R5 | `integrated_minusVN_365_24h_unsolved.nc` | 28,606,319 | `8a9c71364d07951b80c6a5616a42afab345e9071eab4ac7d124a14476548e6f8` |
| R6 | `integrated_minusTH_365_24h_unsolved.nc` | 29,443,454 | `90b3d7fd74c1f44a1c4f3ab9648e448493edb6f217d7778337e3e7252e03fbc0` |
| R7 | `integrated_minusLA_365_24h_unsolved.nc` | 29,749,399 | `29858e7d93e86faa6662c2ac11e04911c063737f40291100e961158b40b96bee` |
| R8 | `disconnected_noco2ship_365_24h_unsolved.nc` | 29,806,852 | `02292afe82694ebc4d0833a9e767798b460ac57ca4b62d53b79781da3b3cb19e` |
| R9 | `disconnected_keepstock_365_24h_unsolved.nc` | 30,901,303 | `5a54850e4c860984c5498956577d60ad0130fb6622621c30252c317728f3a5ce` |
| R10 | `integrated_wacccountry_365_24h_unsolved.nc` | 31,527,498 | `c3d86255d9f0fb551ebfba443c4fc467cdc51fff8eff859279cdf9351963f0e8` |
| R11 | `disconnected_wacccountry_365_24h_unsolved.nc` | 30,860,144 | `85ade73c3096ebde1338c1afa05b73121223b0b468aa5cdbaf3d435f2852fe63` |

### 5.3 每个运行"LP 构建完成、求解前退出"（`run_batch3.sh BUILD_ONLY=1`）

全程 1,129 s；三个阶段均为单通道（干跑模式）；每个运行 `BUILD_CHECK.json` 全部通过：求解前退出且无求解器日志、求解参数 = 登记档案 + TimeLimit 21,600、档案正确、输入网络 SHA256 = 登记值（基础网络 = 构建回执日网络，变体 = 变体回执）、快照 365、**GATES_V6 G2.2 配置子集在求解前已一致**、LP 已导出、输出目录 = `runs/batch3/<编号>/`、成本表存在。

| 运行 | 行 | 列 | 非零元 | 构建 s | 墙钟 s | 峰值 GiB | LP 数组 B |
|---|---|---|---|---|---|---|---|
| R1 | 10,052,113 | 4,509,642 | 23,634,770 | 144 | 151 | 10.14 | 799,796,145 |
| R2 | 9,705,916 | 4,357,448 | 22,556,267 | 72 | 81 | 10.04 | 768,143,605 |
| R3 | 10,052,113 | 4,509,642 | 23,634,770 | 125 | 141 | 10.13 | 799,796,145 |
| R4 | 9,705,916 | 4,357,448 | 22,556,267 | 68 | 76 | 10.05 | 768,143,605 |
| R5 | 9,048,930 | 4,054,907 | 21,248,615 | 72 | 81 | 10.09 | 719,351,869 |
| R6 | 9,253,938 | 4,150,749 | 21,641,255 | 83 | 91 | 10.08 | 734,387,981 |
| R7 | 9,351,193 | 4,193,946 | 21,891,064 | 84 | 96 | 10.12 | 742,446,925 |
| R8 | 9,357,960 | 4,183,232 | 21,687,091 | 58 | 66 | 7.79 | 738,917,205 |
| R9 | 9,745,023 | 4,372,438 | 22,680,056 | 74 | 82 | 9.92 | 771,662,397 |
| R10 | 10,052,113 | 4,509,642 | 23,634,770 | 123 | 136 | 10.16 | 799,796,145 |
| R11 | 9,705,916 | 4,357,448 | 22,556,267 | 71 | 82 | 10.07 | 768,143,605 |

- R3 / R10 与 R1 同维（同一网络 / 只改成本），R4 / R11 与 R2 同维；去一国变体逐国变小。LP 数组合计 8.4 GB（每运行 0.72–0.80 GB，与第 6 节磁盘估计一致）。
- **P1 只核对参数**（`PARAM_CHECK.json` 通过）：档案 A、内点门槛路径、Threads 8；网络 = 2920×3h 一体化且 SHA256 = 回执；TimeLimit 3,600 s、墙钟 3,600 s；标签 `BATCH3_P1_PROBE_2920X3H`；输出目录正确。本机不构建 2920×3h LP（内存不足）。
- 批级汇总在干跑模式下照常生成（各运行状态为 `built_stopped_before_solve`），`pre_p1` 与 `final` 打包脚本照常运行。

### 5.4 后处理演练（M12b 冒烟结果；`run_batch3.sh POST_ONLY=1`，不启动任何求解）

- **映射：** R1 ← M08b 补充 01 冒烟一体化，R2 ← 冒烟不互联，R5 / R6 / R7 ← M12b 去 VN / TH / LA（56×3h，`SMOKE_TEST_ONLY`）。只复制求解输出（派生文件不复制，`EXPORTS.json` 恢复为回执中求解时的清单），`TRUNCATE=56`；网络 SHA256 逐一与回执核对。
- **逐运行（全部 exit 0）：** 违反量 → C1 → M12 分摊 → Owen 对偶形式 → （R5–R7）去一国右端项检查 → GATES_V6。
  - R1、R2 先以缺省参照作临时判定（C1 111，ACCEPTED_LAYER2）；生成 `BATCH_REFERENCE.json` 后重评（`grade_history` 1 条，临时标签另存），最终 ACCEPTED_LAYER2。
  - R5–R7 直接用本批参照：C1 111、ACCEPTED_LAYER2、右端项检查通过（剩余所有者权利变化 0）。
  - 未求解的 R3、R4、R8–R11、P1 记 `POST_ONLY_*` 跳过。
- **批级：** 去一国检查 3 / 3 通过（不可分成本为正）；B6 = **9.8985 bn**（门槛通过；与 M08b 冒烟 +9.90 bn 一致），受益与比例规则对照无负受益；第二级比较因 R3 / R4 缺失 → **档案 A**（"缺运行即不通过"的设计生效）；敏感性差额标为不可计算；`BATCH3_SUMMARY.{json,md}` 生成；轻量包 2.3 MB、完整包 140.7 MB 生成，许可扫描通过。
- **与 M12b 证据逐项对比（`evidence/dryrun/post_smoke/POST_SMOKE_VS_M12B.json`）：** VN / TH / LA 的 c(N − i) 原值、D8 加回额、c′(i)、Owen 对偶形式份额、容差差值**全部为 0.0 EUR**；余量 VN +1.1734、TH +0.1866、LA +0.8933 bn，与 M12B 报告表相同；C1 等级与 GATES_V6 标签相同。
- 耗时 341 s。

## 6. 资源、时长与上传量（INFERENCE，详见 `RUN_PLAN.md` 第 4–6 节）

- **时长：** 25 核实例约 19–23 h（区间约 17–26 h）：第 1 阶段 3.8–4.5 h，第 2 阶段 4.0–4.6 h（R3、R4 先后跑），第 3 阶段 9.5–12 h，批级 0.5 h，P1 1.1 h；最坏（全部跑到墙钟）约 47 h。依据 S4N / S4O-6 / S4Q 实测，两会话并行按 1.1–1.3 倍放慢估计。
- **内存：** 至少 72 GiB；两个 365×24h 会话各约 15 GiB + 另一通道后处理约 9 GiB。本机实测 365×24h LP 构建峰值 10.15 GiB；P1 的 2920×3h 构建粗估约 80 GiB，在 92 GiB 容器上可能在构建或预处理阶段超限——由 P1 实测。
- **磁盘：** 预计约 39 GiB，预检要求 ≥ 50 GiB（低于 60 GiB 警告）。
- **上传：** 单路上传约 284 MB，传后全量 `sha256sum -c`：36 KB/s 约 2.2 h；0.16 MB/s 约 0.5 h；4 MB/s 约 1 分钟。
- **下载：** 轻量包几十 MB；完整包约 1.8 GB。

## 7. 偏离与说明

1. **第 1.4 节停止条件触发：** 重建网络 SHA256 不同，按指令停下报告；用户决定 A 后继续（第 3 节）。
2. **玩具 LP 测试照常运行：** 指令允许，故全量测试未排除 5 个玩具求解用例（3 个运行，2 个因缺数据跳过）；未调用 Gurobi。
3. **干跑发现并修正了一个路径依赖（M08a 脚本）：** `m08a_variants.py` 把 `--costs` 的绝对路径写入分国 WACC 变体的元数据，使 R10 / R11 的变体 SHA256 随目录变化——第一版干跑（包 `be1ce466`）在第 0 阶段安全停止。改为只记文件名与 SHA256（只改元数据记录方式），补测试；第一版包作废并改名保留（`cloud_package_dist_v1_be1ce466/`，不上传），证据见 `evidence/dryrun_v1_be1ce466/`、`evidence/package_v1_be1ce466/`。
4. **`s2_solve.py` 新增 `--stop-before-solve`：** 不给该开关时求解路径不变。
5. **"其余运行两两并行"的实现：** 两条固定通道（任何时刻至多两个），而非严格成对等待（`RUN_PLAN.md` 第 8 节第 1 项）。
6. **R3、R4 在 25 核上先后跑：** 指令同时要求"1e-6 T16 用 Threads 16"与"两个会话合计不超过实例核数"，16 + 16 = 32 > 25，按后者先后跑（第 8 节第 2 项）。
7. **后处理脚本：** 逐运行与批级后处理是 `run_batch3.sh` 内的函数，单独重跑用 `POST_ONLY=1 bash run_batch3.sh`（本机干跑第 5.5 项即用此模式）；包内 `RUN_PLAN.md` 未写这一用法，见脚本头部说明与本报告。
8. **本机测量：** R1 的 LP 构建测量（M10P-4 前）在含未提交 `s2_solve.py` 改动的 worktree 上运行，只作资源测量；正式干跑在解包的部署包上运行。WSL 内存 10 GiB，365×24h 构建峰值约 10.1 GiB，使用了交换区。

## 8. 仍需用户决定的事项

> 本节各项已由 `M10P_SUPPLEMENT_01.md` 决定（第 1、2、3、5、6、7 项；第 4 项的两条固定通道沿用），落实情况见第 10 节。

1. **R3、R4 的并行方式：** 25 核实例上两者先后跑，第 2 阶段另一会话空闲约 3–4 h。可选：(a) 维持（本计划）；(b) 租 ≥ 32 核实例，R3 | R4 并行；(c) 允许 R3 与第 3 阶段的档案 A 运行同时跑（16 + 8 ≤ 25），省约 3 h，但改变指令写定的顺序。
2. **无返回解的运行是否停批：** 本计划按"C1 不可计算 = C1 (a) 不通过"停批，敏感性运行（R8–R11）也一样，会使其后运行与 P1 都不开始。是否对 R8–R11 改为"记录后继续"——须在看结果前决定。
3. **P1：** TimeLimit = 墙钟 = 3,600 s，只作计时与内存探针；按本机 365×24h 构建峰值 10.1 GiB × 8 粗估，2920×3h 仅构建就约 80 GiB，在 92 GiB 容器上可能在构建或预处理阶段超限（P1 前已打包 R1–R11 结果）。是否接受，或 P1 改在更大内存的实例上单独跑。
4. **第 3 阶段两条固定通道**（A = R5、R7、R9、R11；B = R6、R8、R10）是否接受（相对严格成对省约 1–2 h）。
5. **实例规格：** 内存 ≥ 72 GiB、核 ≥ 16（R3 | R4 并行需 ≥ 32）、数据盘可用 ≥ 50 GiB（建议 60；预计用 39 GiB）。克隆实例（已有同版本环境，用 `env/env_check.py` 核对）或新实例（`env/install_env.sh`，下载约 743 MB、约 5–15 分钟）。
6. **代码归档大小：** 按指令为整个分支的 `git archive`（153.5 MB，`research/` 目录占大头），36 KB/s 上行时上传约 2.2 h。是否瘦身（去掉 `research/`）由用户决定；运行时代码是否读取 `research/` 下的文件未逐一核实，瘦身需另做干跑。
7. **`m08a_variants.py` 的修正**（只记成本表文件名与 SHA256）是否接受；以及是否另修 `s2_network.py:344` 的同类路径依赖（会改变所有网络的 SHA256，需重新登记；本批不受影响，云端不重建网络）。

## 9. 交付

- **交付目录 `work/p1_m10p_20261022/`**（镜像到 `research/06_scope_redesign/p1_m10p_20261022/`）：
  - 本报告、`RUN_PLAN.md`、`M10P_PROGRESS.md`、指令及 SHA256、`M10P_LEDGER_ENTRY.md`、`PR_BODY.md`；
  - `evidence/`：PR 提交核对、测试日志、网络重建与内容比较、R1 构建测量、部署包清单（`package/`，第一版 `package_v1_be1ce466/`）、干跑（`dryrun/`，第一版 `dryrun_v1_be1ce466/`）；
  - `scripts/`：本步的 WSL 脚本（建分支、PR 核对、测试、重建、诊断、环境锁定、测量、干跑、对比、审阅 ZIP）。
- **仓库内包脚本：** `research/06_scope_redesign/p1_m10p_20261022/cloud_package/`（`run_batch3.sh`、`preflight.sh`、`pack_results.sh`、`make_package.sh`、`env/`）。
- **部署包（不入库）：** `work/p1_m10p_20261022/cloud_package_dist/`（提交 `eac6c3e0`）；作废的第一版 `cloud_package_dist_v1_be1ce466/` 保留，不上传。
- **未入库的本机产物：** 主检出 `results_project/m10p/`（重建网络 `builds/`、R1 测量 `measure_r1/`、打包变体 `package_variants*/`）；干跑目录 `/home/jin/m10p_dry/`（含 8.4 GB LP 数组）与 `/home/jin/m10p_dry_v1_be1ce466/`。均未删除。
- **提交链：** `b46fc23d`（M10P-1）→ `692c2cce`（M10P-2 停止证据）→ `be1ce466`（M10P-3 代码与脚本）→ `915b919b`（M10P-4 第一版包证据）→ `eac6c3e0`（M10P-5a 变体路径修正）→ M10P-5 干跑证据 → M10P-6 报告、台账、PR（见进度文件）。
- **台账：** `research/STAGE2_PROJECT_LEDGER.md` 末尾追加 M10P 条目（原文 `M10P_LEDGER_ENTRY.md`）。
- **draft PR：** [cyc292cycjin-oss/SGP-ESE5004-Stage2#49](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/49)（base `codex/m12b-loo-local-20261021`，叠在 #48 上）。
- **审阅 ZIP：** `M10P_REVIEW.zip`（work 目录不含部署包 + 本步改动的仓库代码与包脚本；逐成员 SHA256 + CRC32 清单 `M10P_REVIEW_MANIFEST.csv`，ZIP 的 SHA256 见 `M10P_REVIEW_ZIP_SHA256.txt`；ZIP 本身不入库）。

完成后停止，等待审阅；审阅通过后由用户租卡。

---

## 10. 补充 01（第 142 项）：第 8 节六项的决定与第二次干跑

**摘要（2026-10-22；`M10P_SUPPLEMENT_01.md` v1，SHA256 `49a4593d…9205` 与 `M10P_SUPPLEMENT_01_SHA256.txt` 一致；未连云、未上传、未调用 Gurobi）**
1. **六项决定全部落实**到 `run_batch3.sh`、`m10_batch3_summary.py`、`preflight.sh`、`make_package.sh` 与 `RUN_PLAN.md` v2：第 2 阶段 R3 | R5、R4 | R6 配对（16 + 8 = 24 核）；分级停批；P1 与 2920×3h 网络删除；实例规格进入预检；代码归档去掉 `research/`；路径问题按决定处理。
2. **`research/` 运行时依赖：无。** 静态检查（导入闭包 66 个模块）只有两处会打开 `research/` 文件，都在不被调用的 Gate5 / Gate6 旧函数里；带访问追踪的干跑中预检、构建、后处理对 `research/` 的访问为 0（阳性对照 3）。无需保留任何 `research/` 文件。
3. **部署包 v3（提交 `e0527cec`）：** 24 个文件 **148,587,335 B**（v2 为 283,737,685 B），`PACKAGE_MANIFEST.json` SHA256 `0fc6ab4f5a9281679738f45972affbc6410acab6b9d6c2a778fd255138e1bc32`。上传：36 KB/s 约 1.15 h、100 KB/s 约 25 分钟、318 KB/s 约 8 分钟。
4. **第二次干跑全部通过：** 预检 OK；7 个变体与期望 SHA256 逐字节相同；R1–R11 构建到求解前退出，LP 维数、参数、网络 SHA256 与 LP 数组字节数逐运行与第一次干跑相同；后处理演练与 M12b 证据差 0.0 EUR。
5. **测试：** `tests/research` 全量 **600 passed、67 skipped、0 failed**（新增 / 改写的运行脚本测试 17 项，含模拟失败）。
6. **请审阅确认（10.7）：** 阶段之间等两条通道都结束的取舍；无返回解时 G2 只核对输入部分的解释；不可用的去一国运行不进入去一国检查。

等级：测试、SHA256、干跑核对与访问追踪为 VERIFIED；时长、内存、磁盘与上传时间为 INFERENCE。

### 10.1 决定与实现

| 项 | 决定（补充 01） | 实现 | 验证 |
|---|---|---|---|
| 1 R3、R4 的线程 | R3 与 R5、R4 与 R6 同时跑（24 核），之后其余两两并行；只改顺序 | `m10_batch3_summary.py SCHEDULE`：第 1 阶段 [R1] \| [R2]；第 2 阶段 [R3 → R4] \| [R5 → R6]；第 3 阶段 [R7 → R9 → R11] \| [R8 → R10]。`run_batch3.sh phase()`：两条通道各自最大 Threads 之和 ≤ 容器核数时并行，否则合成一条通道轮流取运行。档案与参数不变 | 测试：25 核上 R3 / R5、R4 / R6 重叠，R3 与 R4 不重叠，任何时刻 ≤ 2 个会话且 ≤ 24 核；20 核时第 2 阶段为一条通道 R3 → R5 → R4 → R6 |
| 2 无返回解的停批 | R1、R2 无解 / C1 (a) / G2 不过 → 停批；R3–R11 无解或 C1 (a) 不过 → 不可用、继续；任何 G2 不过 → 停批 | `m10_batch3_summary.py stop-class` → `STOP_CLASS.json`（`g2` / `nosol` / `c1a` / `ref_dependent`）；`run_batch3.sh stop_check()`：停批写 `STOP`，不可用写 `UNUSABLE`；不可用的 R5–R7 不进入去一国检查，敏感性差额标为不可用，R3 / R4 不可用 → 档案 A | 测试：R3、R5 无解与 R8 C1 (a) 失败 → 三个记为不可用、11 个运行都跑完、退出码 0；R2 C1 (a)、R6 无解且配置子集不符、R7 有解但 G2.2 不符 → 停批（另一通道正在跑的 R4 / R8 跑完并后处理）；`stop-class` 单元测试 12 种情况 |
| 3 P1 内存 | P1 从第三批删除；第四批开始时 1 h 探针、超过可用内存 80 % 即止损 | 运行表、运行脚本、批级打包（不再有 `pre_p1`）、汇总中去掉 P1；2920×3h 网络不入包；`p1_summary` 解析函数保留供第四批；`RUN_PLAN.md` 第 9 节写明第四批做法 | 测试：运行表 11 个、无 P1 调用、只有 `final` 打包 |
| 4 实例规格 | ≥ 25 核、内存 ≥ 92 GiB、数据盘 ≥ 60 GB；推荐 1 卡 8481C / 8470Q | `preflight.sh` 资源一节按此判定（核与内存取容器 cgroup 配额；磁盘按 GB = 10⁹ B）；清单 `run.instance` | 本机干跑：16 核 / 11 GiB 判为不满足（预期，仅作信息） |
| 5 代码包瘦身 | 静态检查加干跑确认后剔除 `research/`；有依赖则保留并列出 | `make_package.sh`：按提交的跟踪文件清单打包，去掉顶层 `research/`，`RESEARCH_KEEP` 为空；打包后核对归档中 `research/` 文件数 = 保留数、文件数 = 清单数 | 10.2 |
| 6 路径问题 | 接受 `m08a_variants.py` 的修正；`s2_network.py:344` 暂不修，登记为已知小项 | 代码未改；`RUN_PLAN.md` 第 1 节与清单 `networks.known_item` 登记 | 网络、回执与 v2 逐字节相同（10.3） |

### 10.2 `research/` 运行时依赖（第 5 项）

- **静态检查**（`scripts/m10p_s01_static_research.py`，`evidence/s01/S01_STATIC_RESEARCH_RAW.json`）：入口为云端会启动的 8 个模块（`s2_solve`、`l23_violation_analysis`、`s4o_c1_precision`、`m12_allocation`、`m12_rhs_audit`、`m08a_variants`、`v5/gates_v6`、`m10_batch3_summary`），导入闭包含函数内导入共 66 个模块。逐条归类（`evidence/s01/S01_RESEARCH_DEPENDENCY.json`）：
  - 会真正打开 `research/` 文件的只有 2 处，都读 `research/04_model_assembly/final_validation/GATE5_RUN_HISTORY.json`：`gate5_resources.current_evidence()`（调用者都是 Gate5 工具与测试，不在闭包内）和 `run_gate6_baseline.make_lock()`（只被 Gate6 运行器自己的函数调用；闭包经 `gate6_execution_context` 只用到该模块的 `resource_admission()`）。
  - 其余 7 处是写进输出的标签（C1 缺省参照来源、GATES_V6 定义文件名、`s1_solve` 参数来源）或模块说明。
  - 配置中指向 `research/` 的值只在 `configs/research/gate6_baseline_3h.json`，只被 `run_gate6_baseline.py` 读取；包内 shell 脚本不引用仓库的 `research/`。
- **访问追踪干跑**（`scripts/m10p_s01_trace/sitecustomize.py`，只记录、不改变行为）：每个 Python 进程记录对 `<包>/repo/research/` 的 open、listdir、scandir、glob、stat、lstat。阳性对照（目录不存在时故意访问）记录 3 次；预检、`BUILD_ONLY`、`POST_ONLY` 记录 **0 次**（`evidence/s01/S01_TRACE_SUMMARY.json`、`dryrun/trace/`）。
- 追踪同时记录了包目录与环境以外的本机路径（信息项）：只有 matplotlib / dask / pip 的用户配置与缓存目录、环境前缀的上级目录、PyPSA 数据目录（库的通用行为，云端同样存在或可缺省），以及后处理演练按设计读取的 M12b / M08b 冒烟网络；没有 `/mnt/d` 或其他 worktree。
- **结论（VERIFIED）：** 运行时不读取 `research/`；部署包代码归档不含 `research/`，无需保留任何文件。

### 10.3 部署包 v3 与上传量

- `make_package.sh` 在提交 `e0527cec` 上生成 `work/p1_m10p_20261022/cloud_package_dist/`（不入库；95 s）：

| 内容 | 文件 | 字节 |
|---|---|---|
| 代码（不含 `research/`，1,432 个文件） | `code_e0527cec.tar.gz` | 82,477,631 |
| 365×24h 一体化 / 不互联网络（与 v2 逐字节相同） | `networks/*_365_24h_unsolved.nc` | 31,524,926 + 30,857,960 |
| 两份构建回执 | `networks/*_BUILD_RECEIPT.json` | 1,729,929 + 1,729,333 |
| 两份成本表、脚本、环境锁定、计划、清单等 19 个文件 | — | 267,556 |
| **合计 24 个文件** | | **148,587,335** |

- `PACKAGE_MANIFEST.json`：SHA256 `0fc6ab4f5a9281679738f45972affbc6410acab6b9d6c2a778fd255138e1bc32`（8,758 B）；`SHA256SUMS`：SHA256 `6f74f40e90a9244c7afaaad032d8f2987f59f01393a89567f5f0a47f272a1ea1`（22 个文件）。副本在 `evidence/s01/package/`，摘要 `evidence/s01/PACKAGE_SUMMARY.txt`。
- 7 个变体的期望 SHA256（`EXPECTED_VARIANTS.json`）、两个网络、构建回执与成本表都与 v2（`eac6c3e0`）逐字节相同；2920×3h 网络不再入包。
- **最终上传量 148,587,335 B（约 148.6 MB），单路上传、传后全量 `sha256sum -c`（KB = 1000 B；INFERENCE）：**

| 速率 | 时间 |
|---|---|
| 36 KB/s（S4O-6 AutoDL 克隆机上行） | 约 1.15 h（69 分钟） |
| 100 KB/s | 约 25 分钟 |
| 318 KB/s | 约 8 分钟 |

  v2 包（283.7 MB）在 36 KB/s 下约 2.2 h。代码归档中剩下的大头是 `research_inputs/`（未压缩约 96.7 MB）与 `data/`（约 47.2 MB），不在本次授权范围内，未动。
- 旧包均改名保留、不上传：`cloud_package_dist_v2_eac6c3e0/`（M10P v2）、`cloud_package_dist_v3a_619d7b46/`（见 10.6 第 1 项）。

### 10.4 第二次干跑（补充 01 第 2 节；脚本 `scripts/m10p_s01_dryrun.sh`，证据 `evidence/s01/dryrun/`）

全部在 WSL 中、移除 `GRB_LICENSE_FILE` 后运行；运行脚本的干跑模式把许可变量指向不存在的文件，求解调用 0 次；每个 Python 进程带访问追踪。

- **解包与预检：** 部署包复制到 `/home/jin/m10p_dry_s01/pkg`；`preflight.sh`（不含许可一节）**PREFLIGHT OK**——22 个文件 SHA256 全对；代码解包到 `./repo`（`e0527cec`，1,432 个文件，无 `research/`）；两个基础网络 = 构建回执；`EXPECTED_VARIANTS.json` 7 条；环境 284 / 284 个包版本相同；两档案参数与 Threads 8 / 16 正确；模块无许可可导入，运行表 11 个、排程 3 个阶段。资源一节本机不满足规格（16 核、11 GiB），仅作信息。
- **变体复现：** 运行脚本第 0 阶段生成的 7 个变体与期望 SHA256 逐字节相同（R5 `8a9c7136…` 至 R11 `85ade73c…`，同第 5.2 节表）。
- **R1–R11 构建到求解前退出（`BUILD_ONLY=1`，1,111 s）：** 每个运行 `BUILD_CHECK.json` 全部通过；顺序按排程（干跑模式为单通道：R1、R2 → R3、R5、R4、R6 → R7–R11）。与第一次干跑（包 `eac6c3e0`，含 `research/`）逐运行比较（`evidence/s01/S01_DRYRUN_BUILDS_VS_FIRST.json`）：LP 行、列、非零元、求解参数、档案、输入网络 SHA256 全部相同，LP 数组字节数也逐运行相同（合计 8,410,585,627 B）；峰值 7.6–10.1 GiB。
- **后处理演练（`POST_ONLY=1`，M12b 冒烟结果，320 s）：** 映射同第 5.4 节；全部 exit 0：R1、R2 临时判定 → 本批参照重评（ACCEPTED_LAYER2）；R5–R7 用本批参照、右端项检查通过；去一国 3 / 3 通过，B6 = 9.8985 bn；第二级因 R3 / R4 缺失 → 档案 A；批级汇总与 `final` 打包生成（轻量 2.3 MB、完整 140.7 MB）；不可用运行无。与 M12b 证据逐项对比（`dryrun/post_smoke/POST_SMOKE_VS_M12B.json`）：**最大差 0.0 EUR**，余量 VN 1.1734、TH 0.1866、LA 0.8933 bn。
- **配对顺序与分级停批：** 按补充 01 第 2 节用模拟失败的单元测试验证（10.5），不调用 Gurobi。

### 10.5 测试

| 时点 | 结果 | 日志 |
|---|---|---|
| 补充 01 代码（`619d7b46` 的内容，提交前工作树） | **600 passed、67 skipped、0 failed**（404.7 s） | `evidence/M10P_FULL_TESTS_s01_code.log` |

- 595 → 600：`test_m10p_batch3.py` 由 12 项改为 17 项（含 3 个参数化停批情形）。玩具 LP 测试照常运行（规则同 M10P），未调用 Gurobi。
- 运行脚本测试（替身流水线，无求解器）：运行表与排程（每个运行一次、T16 只在一条通道、各阶段最大并发核数 16 / 24 / 16）；完整批次（配对重叠、通道顺序与间隔、阶段屏障、任何时刻 ≤ 2 个会话且 ≤ 24 核、临时判定→重评、续跑不重解）；20 核时单通道；分级停批（不可用继续 / R2 C1 (a) / R6 无解且输入不符 / R7 G2）；`stop-class` 12 种情况；墙钟终止（R1 无解 → 停批）；变体 SHA256 安全停止；`BUILD_ONLY` 顺序；`POST_ONLY`；未登记时限；打包许可扫描；P1 解析（保留）；第二级缺运行。

### 10.6 偏离与说明

1. **`RUN_PLAN.md` 漏算构建回执：** 第一次在 `619d7b46` 上生成的 v3 包（148,587,312 B）显示计划第 6 节写的"其余不到 1 MB"漏了两份构建回执（各 1.73 MB；v1 的"约 281 MB"同样漏算）。计划在包内，故改正文字（`e0527cec`）后重建；第一次生成的包改名为 `cloud_package_dist_v3a_619d7b46/` 保留，证据 `evidence/s01/package_v3a_619d7b46/`。两版代码与网络内容相同。
2. **无返回解时的 G2：** G2.1 的回读与 G2.3 都需要解，无解时必然不过。按决定中"G2 不过（结构或输入问题）"的说明，无返回解的运行只核对不需要解的部分（输入网络 SHA256、配置子集哈希）；这两项不过才按 G2 停批（`RUN_PLAN.md` 3.3 第 3 项）。
3. **验收不可读：** v1 中 GATES_V6 验收崩溃（无标签）时不会停批；现在验收或分类不可读按 G2 不通过停批（更保守）。
4. **阶段屏障与通道：** 按"之后其余运行两两并行"的字面，第 3 阶段等第 2 阶段两条通道都结束才开始；各阶段两条通道各自依次推进、不严格成对等待（与 v1 第 3 阶段做法相同）。
5. **预检核数门槛：** 按规格写为 ≥ 25 核（配对实际需要 24 核）；24 核的容器会判为不满足。
6. **测试日志的提交点：** 全量测试在 `9bfe540a` 加上补充 01 的 6 个未提交改动上运行，随后原样提交为 `619d7b46`（其后只改了 `preflight.sh` 一行注释与文档）。

### 10.7 请审阅确认的事项

1. **阶段屏障（INFERENCE）：** 第 2 阶段由 R5 + R6（约 6 h）决定，R3 + R4（约 4 h）结束后通道 A 约 2 h 只用 8 核；若允许第 3 阶段的运行在任一通道空出时就开始（不等另一条通道），按历史时长约省 1 h。本计划未采用，按字面执行。
2. 10.6 第 2 项对"无返回解时 G2"的解释，以及第 3 项"验收不可读即停批"。
3. 记为不可用的 R5–R7 不作为 c(N − i) 进入去一国检查（`RUN_PLAN.md` 3.6 第 3 项）。

### 10.8 交付

- **提交链（补充 01）：** `619d7b46`（S01-1 代码、测试、`RUN_PLAN.md` v2、静态检查）→ `e0527cec`（S01-2a 计划第 6 节改正；v3 包的代码提交）→ `645349db`（S01-2 / S01-3 部署包与干跑证据）→ `b2829748`（S01-4 本节、台账、PR 说明）→ 收尾提交（审阅 ZIP 清单与 SHA256；见 `M10P_PROGRESS.md`）。
- **证据：** `evidence/s01/`（静态检查、判定、追踪摘要与日志、两次打包证据、干跑证据、构建对比）；全量测试日志 `evidence/M10P_FULL_TESTS_s01_code.log`。
- **脚本：** `scripts/m10p_s01_*`（静态检查、追踪器与自测、打包、干跑、判定、审阅 ZIP）。
- **部署包（不入库）：** `work/p1_m10p_20261022/cloud_package_dist/`（v3，`e0527cec`）。
- **台账：** `research/STAGE2_PROJECT_LEDGER.md` 末尾追加"M10P 补充 01"条目（原文 `M10P_S01_LEDGER_ENTRY.md`）。
- **PR：** [cyc292cycjin-oss/SGP-ESE5004-Stage2#49](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/49) 推送并更新说明。
- **审阅 ZIP：** `M10P_S01_REVIEW.zip`（自 `b2829748` 生成，418 个成员，845,305 B，SHA256 `77a2f6d9a3db67329216c9384de54bb8243c56cca869bb09f2665296ee062c2e`；逐成员 SHA256 + CRC32 清单 `M10P_S01_REVIEW_MANIFEST.csv`；不入库）。

完成后停止，等待审阅；审阅通过后由用户租卡。
