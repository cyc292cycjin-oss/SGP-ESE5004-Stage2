# M10P 进度（第三批上云准备，本机；不连云、不上传、不调用 Gurobi）

- 指令：`M10P_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `bd2461e70ec5ff4f97ece77c0fd5c2faa4a4301c50bdf0116e63cbcbd516bbd1`，与 `M10P_INSTRUCTION_SHA256.txt` 一致（2026-10-22 核对）。
- 分支：`codex/m10-batch3-20261022`，自 M12b 头 `1f46517d`；worktree `/home/jin/wt_m10p_20261022`。
- 交付目录：`work/p1_m10p_20261022/`，镜像到 `research/06_scope_redesign/p1_m10p_20261022/`。

| 子步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| M10P-1 | 整合分支、PR 提交核对、全量测试 | **完成**：分支自 `1f46517d`；#45 23/23、#47 14/14、#46 20/20、#48 20/20、S4Q #41 5/5（含 `FIXED_RUNS` 提交 `84532e78`）全部已在 → 无需补 merge（`evidence/M10P_PR_COMMIT_CHECK.json`）；被忽略输入 2 个（`finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv`、`DISCOUNT_RATE_IN_USE.csv`）自 M12 worktree 复制；`tests/research` 全量 **582 passed、67 skipped、0 failed**（155.9 s，玩具 LP 按指令允许、照常运行：5 个玩具求解用例中 3 个通过、2 个因缺数据跳过；`evidence/M10P_FULL_TESTS_m10p1.log`） | 见下 |
| M10P-2 | 干净提交重建四个网络，与 `ec80668f` 构建比对 SHA256 | **停止（第 1.4 节）**：在 `b46fc23d` 上重建，四个 SHA256 都不同；原因（VERIFIED）= 元数据 `s2_layers.geothermal.bus_mapping_source.path` 记录了构建 worktree 的绝对路径（`s2_network.py:344`），网络数据逐项相同（`evidence/M10P_NETWORK_REBUILD.json`、`M10P_NETWORK_CONTENT_DIFF.json`、`M10P_BUILD_STATUS.txt`）；等用户决定入包网络 | 见下 |
| M10P-3 | 运行脚本 `run_batch3.sh`、求解前退出开关、批级汇总、测试 | **完成**：`s2_solve.py --stop-before-solve`；`scripts_project/m10_batch3_summary.py`（运行表唯一来源、基础网络 / 变体核对、干跑构建核对、P1 参数核对、第二级比较、B6 与敏感性差额、批级汇总、P1 计时解析）；`cloud_package/run_batch3.sh`（两会话、线程预算、许可间隔、临时→本批参照重评、D12 停批、安全停止、续跑、墙钟终止进程组、`BUILD_ONLY` / `POST_ONLY`）、`pack_results.sh`、`preflight.sh`、`make_package.sh`、`env/`（锁定、安装、核对）；测试 `test_m10p_batch3.py` 12 项通过（替身流水线，无求解器）；全量（加入前 11 项时）593 passed / 67 skipped / 0 failed；本机 R1 LP 构建测量（无求解）：159 s、峰值 10.15 GiB、LP 数组 0.80 GB；`RUN_PLAN.md` 初稿 | 见下 |
| M10P-4 | `RUN_PLAN.md`、部署包（代码、网络、环境、预检、打包脚本、清单） | **完成**：`make_package.sh` 在 `be1ce466` 上生成 `cloud_package_dist/`（不入库）：23 个文件 283,718,369 B（代码 `code_be1ce466.tar.gz` 153,514,617 B；`ec80668f` 原网络三个 126.5 MB，SHA256 与登记值相同；构建回执与成本表）；构建输入检查通过（`ec80668f` 之后只改了 5 个不在 `s2_network.py` 导入闭包内的脚本）；7 个变体两遍逐字节相同 → `EXPECTED_VARIANTS.json`；`PACKAGE_MANIFEST.json` SHA256 `fb90a509…`、`SHA256SUMS` `83fdafa3…`（副本在 `evidence/package/`）；上传估计 36 KB/s 2.19 h、0.16 MB/s 0.49 h、4 MB/s 1 分钟 | 见下 |
| M10P-5 | 本机干跑（变体复现、逐运行 LP 构建、后处理用 M12b 冒烟结果） | 未开始 | — |
| M10P-6 | `M10P_REPORT.md`、台账条目、draft PR | 未开始 | — |

提交：M10P-1 `b46fc23d`。

提交：M10P-2 `692c2cce`（停止证据与中途报告）。

**用户决定（2026-10-22，会话中）：** A——部署包用 `ec80668f` 原构建（主检出 `results_project/m08b/builds_s01/`），本次重建作为"内容相同"的复核证据。

**续跑点：** M10P-3。
