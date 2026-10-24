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
| M10P-5 | 本机干跑（变体复现、逐运行 LP 构建、后处理用 M12b 冒烟结果） | **完成**：第一版（包 `be1ce466`）第 0 阶段 R10 变体 SHA256 不同 → 安全停止 → 修正 `m08a_variants.py`（提交 `eac6c3e0`）→ 第二版包（`eac6c3e0`，23 个文件 283,737,685 B，清单 `f36a4b6c…`）：预检 OK；7 个变体三遍逐字节相同；R1–R11 `BUILD_ONLY` 全部 `BUILD_CHECK` 通过（1,129 s，峰值 7.8–10.2 GiB，LP 数组合计 8.4 GB），P1 参数核对通过；`POST_ONLY` 后处理演练（R1/R2/R5–R7 ← M12b 冒烟）全部 exit 0，临时判定 → 本批参照重评，去一国 3/3 通过，B6 9.8985 bn，与 M12b 证据差 0.0 EUR；全量测试 595 passed / 67 skipped / 0 failed（`eac6c3e0`） | 见下 |
| M10P-6 | `M10P_REPORT.md`、台账条目、draft PR | **完成**：报告第 1–9 节；台账条目追加到 `research/STAGE2_PROJECT_LEDGER.md`（`69f15506`）；分支推送，draft PR [#49](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/49)（base `codex/m12b-loo-local-20261021`）；审阅 ZIP `M10P_REVIEW.zip`（SHA256 见 `M10P_REVIEW_ZIP_SHA256.txt`，不入库） | 见下 |

提交：M10P-1 `b46fc23d`。

提交：M10P-2 `692c2cce`（停止证据与中途报告）。

**用户决定（2026-10-22，会话中）：** A——部署包用 `ec80668f` 原构建（主检出 `results_project/m08b/builds_s01/`），本次重建作为"内容相同"的复核证据。

提交链：`b46fc23d`（M10P-1）→ `692c2cce`（M10P-2）→ `be1ce466`（M10P-3）→ `915b919b`（M10P-4，第一版包）→ `eac6c3e0`（M10P-5a 变体路径修正；第二版包的代码提交）→ `1e7e22f9`（M10P-5 干跑）→ `69f15506`（M10P-6 台账）→ 收尾提交（PR 链接、审阅 ZIP 清单）。

**续跑点（M10P v1）：** 全部完成，等待审阅；审阅通过后由用户租卡，按另一份执行指令上云。

## 补充 01（第 142 项；`M10P_SUPPLEMENT_01.md` v1，SHA256 `49a4593dfa5c9714891f0275a76b6a38ba771efebe0d4a28997bc8d5f4279205`，与 `M10P_SUPPLEMENT_01_SHA256.txt` 一致，2026-10-22 核对）

规则同 M10P：不连云，不上传，不调用 Gurobi（玩具 LP 测试允许）。

| 子步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| S01-1 | 六项决定的代码与文档：静态检查 `research/` 运行时依赖；`run_batch3.sh` 配对排程（`SCHEDULE`）、分级停批（`stop-class`、`UNUSABLE`）、删 P1；`preflight.sh` 实例规格；`make_package.sh` 瘦身（不含 `research/`、不含 2920×3h 网络、上传按 36 / 100 / 318 KB/s）；测试；`RUN_PLAN.md` v2 | **完成**：静态检查（导入闭包 66 个模块）只有两处会打开 `research/` 文件，都在 Gate5/Gate6 旧流程、不在运行路径上（`evidence/s01/S01_STATIC_RESEARCH_RAW.json`）；`test_m10p_batch3.py` 17 项通过；全量 **600 passed、67 skipped、0 failed**（404.7 s，玩具 LP 照常运行；`evidence/M10P_FULL_TESTS_s01_code.log`）；瘦身代码归档试算 82.5 MB（原 153.8 MB） | 见下 |
| S01-2 | 部署包 v3（瘦身）生成与清单 | **完成**：第一次在 `619d7b46` 上生成（v3a，95 s）后发现 `RUN_PLAN.md` 第 6 节漏算两份构建回执（各 1.73 MB，v1 起即漏）→ 改正（`e0527cec`）后重建；v3a 改名为 `cloud_package_dist_v3a_619d7b46/` 保留（不上传，证据 `evidence/s01/package_v3a_619d7b46/`）。**v3（`e0527cec`）：24 个文件 148,587,335 B**（代码归档 82,477,631 B、`research/` 文件 0 个；两个网络、回执、成本表与 7 个变体期望 SHA256 与 v2 逐字节相同；不含 2920×3h 网络）；`PACKAGE_MANIFEST.json` SHA256 `0fc6ab4f5a9281679738f45972affbc6410acab6b9d6c2a778fd255138e1bc32`，`SHA256SUMS` SHA256 `6f74f40e90a9244c7afaaad032d8f2987f59f01393a89567f5f0a47f272a1ea1`；v2 包改名为 `cloud_package_dist_v2_eac6c3e0/` 保留（`evidence/s01/package/`、`PACKAGE_SUMMARY.txt`） | 与 S01-3 一起提交（见下） |
| S01-3 | 第二次干跑：解包与预检、7 个变体复现、R1–R11 构建到求解前退出、访问追踪（`research/`）、后处理批级汇总（M12b 冒烟） | **完成**：预检 OK（22 个文件 SHA256、无 `research/` 的代码 1,432 个文件、环境 284/284、两档案、运行表 11 个与排程 3 个阶段）；7 个变体与期望逐字节相同；R1–R11 `BUILD_CHECK` 全过（1,111 s），LP 维数、参数、网络 SHA256 与第一次干跑逐运行相同；后处理演练 exit 0（320 s），去一国 3/3、B6 9.8985 bn、与 M12b 差 0.0 EUR；访问追踪：阳性对照 3 次，预检 / 构建 / 后处理对 `research/` 的访问 **0 次** → 判定"运行时不读取 `research/`"（`evidence/s01/S01_RESEARCH_DEPENDENCY.json`） | 与 S01-2 一起提交（见下） |
| S01-4 | 报告"补充 01"一节、台账、PR 更新、审阅 ZIP | **完成**：`M10P_REPORT.md` 第 10 节（摘要第 8 条、第 8 节注明已决定）；台账追加"M10P 补充 01"条目（原文 `M10P_S01_LEDGER_ENTRY.md`）；`PR_BODY.md` 补充 01 一节，推送并更新 PR #49；审阅 ZIP `M10P_S01_REVIEW.zip`（自 `b2829748` 生成，418 个成员，845,305 B，SHA256 `77a2f6d9a3db67329216c9384de54bb8243c56cca869bb09f2665296ee062c2e`；清单 `M10P_S01_REVIEW_MANIFEST.csv`；ZIP 不入库） | `b2829748` + 收尾提交 |

提交（补充 01）：S01-1 `619d7b46` → S01-2a `e0527cec`（计划第 6 节改正；v3 包的代码提交）→ S01-2/3 证据 `645349db` → S01-4 `b2829748`（报告、台账、PR 说明）→ 收尾提交（审阅 ZIP 清单与 SHA256）。

**续跑点（补充 01）：** 全部完成，等待审阅；审阅通过后由用户租卡，按另一份执行指令上云。
