# V3 部署包文件清单（HPC / AutoDL）

只列清单：未打包、未上传、未连 AutoDL 或 HPC。指令第 5 条要求到此为止。

打包时以最终提交为准。网络文件取自 `results_project/v3/builds`（提交 `85095e7a` 构建），SHA256 见 `RUN_PLAN_V3.md` 第 1 节。

**补充 01 更新（2026-11-02）：** 两套运行器已能跑 `no_new_xb`，定义文件在 `batch_def/`，复制到包内命名为 `BATCH_DEF.json`，运行器自动读取；没有该文件时保持 v2 表。**X1b 会改变网络：下列 SHA256、字节数和定义文件的登记值在 X1b 之后都要重做。** flat 网络只用于本机对照，不进任何部署包。

**补充 02 更新（2026-11-03）：** X1b 已实施，下面第 2、3 节的字节数和 SHA256 都是 X1b 之前的，已作废。现行登记值见 `RUN_PLAN_V3.md` 第 15.1 节和 `batch_def/`。AutoDL 筛查包改为 5 个网络，由 `screen_package/make_package_v3.sh` 打包，清单见 `V3_REPORT_SUPPLEMENT02.md`。HPC 的打包脚本和 v3 版 `RUN_PLAN_HPC.md` 仍未做，放到筛查之后。

**补充 03 更新（2026-11-03）：** 专线改单向后网络全部重建，现行登记见 `RUN_PLAN_V3.md` 第 17 节，现行筛查包是 `work/p1_v3_20261102/screen_package_v3_oneway/`，`screen_package_v3/` 已作废。

## 1. 两边共用

| 文件 | 来源 | 说明 |
|---|---|---|
| `code_<commit8>.tar.gz` | 最终提交的 `git archive`，不含顶层 `research/` | 现在约 1,479 个文件、156 MB（未压缩）；含 v3 脚本、`configs/research/no_new_xb.yaml`、`research_inputs/{industry_v3,transport_v3,liquids_v3}`、注册表 v3 |
| `env/`（`ENV_LOCK.txt`、`conda_explicit_linux64.txt`、`pip_only.txt`、`ENV_DOWNLOAD.json`、`install_env.sh`、`env_check.py`） | `p1_m10p_20261022/cloud_package/env/` | 不变，v3 没有在求解和后处理路径上新增依赖 |
| `pack_results.sh` | `p1_m10p_20261022/cloud_package/` | 不变 |
| `RUN_PLAN_V3.md`、`V3_RULES.md` | 本目录 | 登记文件；筛查和正式运行另需各自的运行计划，尚未写 |
| `COMMIT`、`SHA256SUMS`、清单 JSON | 打包脚本生成 | |

## 2. AutoDL：365×24h 筛查（另行授权）

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `networks/integrated_365_24h_unsolved.nc` | 32,929,223 | `b484fd52…` |
| `networks/no_new_xb_365_24h_unsolved.nc` | 32,302,786 | `c6702cbf…` |
| `networks/integrated_BUILD_RECEIPT.json` | 1,728,645 | `3c8c1d48…` |
| `networks/no_new_xb_365_24h_VARIANT_RECEIPT.json` | 2,392 | `5a84ffa4…` |
| `networks/integrated_costs_active_research.csv`（两情景共用） | 42,518 | `7cee9c1a…` |

运行脚本：`p1_dfx_20261026/cloud_package_dfx/` 的 `run_dfx.sh`、`preflight_dfx.sh`（已支持 `BATCH_DEF.json`），加 `batch_def/BATCH_DEF_365x24h.json`。

| 文件 | 状态 |
|---|---|
| `scripts_project/dfx_batch.py`、`scripts_project/batch_def.py`、`run_dfx.sh`、`preflight_dfx.sh` | **已改**：运行表、登记值、变体收据、GATES_V6 的登记方式、B6 情景名 |
| `dfx_batch.py` 的 `TIME_LIMIT_S` | 未改，沿用 V1 21,600 s、V2 10,800 s，由筛查的运行计划定 |
| `make_package_dfx.sh` | **未改**：内含 v2 的 SHA256、`BUILD_COMMIT` 和文件名，还要带上 `BATCH_DEF.json` 和变体收据；它的构建输入检查把 `v5/` 下的改动判为拒绝，也要处理 |
| `BATCH3_REFERENCE_VALUES.json` | 未定：换成 v2 筛查（V1 / V2）或 v3 冒烟的参照值，由筛查的运行计划决定；没有这个文件时运行器跳过对比 |

## 3. HPC：2920×3h 正式运行（另行授权）

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `networks/integrated_2920_3h_unsolved.nc` | 71,397,150 | `0d31054b…` |
| `networks/no_new_xb_2920_3h_unsolved.nc` | 70,770,713 | `43e79c8e…` |
| `networks/integrated_BUILD_RECEIPT.json` | 1,728,645 | `3c8c1d48…` |
| `networks/no_new_xb_2920_3h_VARIANT_RECEIPT.json` | 2,392 | `63165f9d…` |
| `networks/integrated_costs_active_research.csv`（两情景共用） | 42,518 | `7cee9c1a…` |

运行脚本：`p1_b4p_20261026/cloud_package_b4/` 的 `run_batch4.sh`、`preflight.sh`，`p1_hpr_20261027/hpc_package_src/` 的 HPC 脚本，加 `batch_def/BATCH_DEF_2920x3h.json`。

| 文件 | 状态 |
|---|---|
| `scripts_project/b4_batch4.py`、`scripts_project/batch_def.py`、`run_batch4.sh`、`preflight.sh`、`hpr_job.sh` | **已改**：运行表、登记值、变体收据、GATES_V6 的登记方式、B6 情景名 |
| `b4_batch4.py` 的 TimeLimit、迭代参照 | 未改，沿用 864,000 s、450 / 250；v3 LP 大约 4 %，由 v3 的 HPC 运行计划复核 |
| `hpr_submit.sh`、`hpr_status.sh`、`hpr_preflight_login.sh`、`make_pbs.sh`、`hpr_consistency.py` | 脚本本身不含情景名的部分未动；`hpr_consistency.py` 比对 `RUN_PLAN_HPC.md` 与登记值，要等 v3 版运行计划写好才能通过 |
| `make_hpc_package.sh`、`make_reference_values.py` | **未改**：同 AutoDL 的打包脚本 |
| `RUN_PLAN_HPC.md`、`HPC_OPERATOR_GUIDE.md`、`REFERENCE_VALUES.json` | **未写 v3 版**，放到 X1b 之后；`HPC_FACTS_20261026.md` 原样带上 |
| `pbs/` | 打包时由 `make_pbs.sh` 重新生成 |

内存和时长的估计也要重算：2920×3h 的 v3 LP 比 v2 大约 4 %（外推，见 `RUN_PLAN_V3.md` 第 2 节）。

## 4. 任何情况下都不进包

许可文件、cutout、LP 和解的数组、`results_project` 下的结果、账号和主机信息、`solve.log`、`solve.err`、完全隔离版本网络（只用于开关测试）、不属于该批分辨率的网络文件。
