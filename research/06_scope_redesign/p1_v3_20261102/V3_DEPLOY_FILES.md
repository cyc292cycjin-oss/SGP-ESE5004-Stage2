# V3 部署包文件清单（HPC / AutoDL）

只列清单：未打包、未上传、未连 AutoDL 或 HPC。指令第 5 条要求到此为止。

打包时以最终提交为准。网络文件取自 `results_project/v3/builds`（提交 `85095e7a` 构建），SHA256 见 `RUN_PLAN_V3.md` 第 1 节。

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

运行脚本以 `p1_dfx_20261026/cloud_package_dfx/` 为底，**下面这些改动尚未做**，它们不属于本指令，须随筛查授权一起定：

| 文件 | 要改的内容 |
|---|---|
| `scripts_project/dfx_batch.py` | `RUNS` 的 V2 改为 `no_new_xb`（底网络 `no_new_xb_365_24h`，成本表 integrated）；`REGISTERED_SHA`、`REGISTERED_BYTES`、`BUILD_COMMIT`；`TIME_LIMIT_S`；网络核对对 `no_new_xb` 改读 `VARIANT_RECEIPT`；B6 的情景名 |
| `run_dfx.sh`、`preflight_dfx.sh`、`make_package_dfx.sh` | 情景名、网络文件名、GATES_V6 对 `no_new_xb` 用 `--registered-sha256` |
| `BATCH3_REFERENCE_VALUES.json` | 换成 v2 筛查（V1 / V2）或 v3 冒烟的参照值，由筛查的运行计划决定 |

## 3. HPC：2920×3h 正式运行（另行授权）

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `networks/integrated_2920_3h_unsolved.nc` | 71,397,150 | `0d31054b…` |
| `networks/no_new_xb_2920_3h_unsolved.nc` | 70,770,713 | `43e79c8e…` |
| `networks/integrated_BUILD_RECEIPT.json` | 1,728,645 | `3c8c1d48…` |
| `networks/no_new_xb_2920_3h_VARIANT_RECEIPT.json` | 2,392 | `63165f9d…` |
| `networks/integrated_costs_active_research.csv`（两情景共用） | 42,518 | `7cee9c1a…` |

运行脚本以 `p1_hpr_20261027/hpc_package_src/` 和 `p1_b4p_20261026/cloud_package_b4/` 为底，**下面这些改动尚未做**：

| 文件 | 要改的内容 |
|---|---|
| `scripts_project/b4_batch4.py` | `RUNS` 的 F2 改为 `no_new_xb`；`REGISTERED_SHA`、`REGISTERED_BYTES`、`BUILD_COMMIT`；TimeLimit 按 LP 规模 +4–5 % 复核 |
| `run_batch4.sh`、`preflight.sh` | 情景名、网络文件名、`no_new_xb` 的收据读取、GATES_V6 的登记方式 |
| `hpc/`（`hpr_job.sh`、`make_pbs.sh`、`hpr_install_env.sh`、`hpr_preflight_login.sh`、`hpr_submit.sh`、`hpr_status.sh`、`hpr_consistency.py`） | 情景名和 `RUN_PLAN_HPC.md` 中的 v2 登记值 |
| `make_hpc_package.sh`、`make_reference_values.py` | 网络核对和参照值 |
| `RUN_PLAN_HPC.md`、`HPC_OPERATOR_GUIDE.md`、`REFERENCE_VALUES.json` | 换成 v3 的登记内容；`HPC_FACTS_20261026.md` 原样带上 |
| `pbs/` | 由 `make_pbs.sh` 重新生成 |

内存和时长的估计也要重算：2920×3h 的 v3 LP 比 v2 大约 4 %（外推，见 `RUN_PLAN_V3.md` 第 2 节）。

## 4. 任何情况下都不进包

许可文件、cutout、LP 和解的数组、`results_project` 下的结果、账号和主机信息、`solve.log`、`solve.err`、完全隔离版本网络（只用于开关测试）、不属于该批分辨率的网络文件。
