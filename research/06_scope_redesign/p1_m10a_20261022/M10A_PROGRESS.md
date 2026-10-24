# M10A 进度（上云前独立审查；不连云、不上传、不调用 Gurobi、不求解）

指令 `M10A_CLAUDE_CODE_INSTRUCTION.md` SHA256 `d7db94976ea1cd24a33f75abc66cdf6add840c1ac2a605deb20672b06b17f98a`（核对一致，v2）。

| 步骤 | 状态 | 说明 / 续跑点 |
|---|---|---|
| 0 开始前核对 | 完成 | worktree `/home/jin/wt_m10p_20261022`，分支 `codex/m10-batch3-20261022`，头 `d71f599e`（e0527cec 之后只有 `research/` 下报告 / 证据与账本），工作树干净；无其他进程使用该 worktree。被审包 v3 `work/p1_m10p_20261022/cloud_package_dist/`（24 文件、148,587,335 B、清单 SHA256 `0fc6ab4f…`）；包内三个脚本与仓库 `cloud_package/` 逐字节相同。 |
| B1 代码审查 | 完成 | F1（S1，`busy()` 双计数，本机实证）、F2–F5（S2）、F6–F12（S3）、F13（需用户决定）；报告第 1 节。 |
| B2 故障演练 | 完成 | 28 项测试全过；修复前 v3 脚本上整批测试 `STOP_SAFE:SOLVER_BUSY_R2`（`evidence/tests/TESTS_before.log`）；全量 611 passed / 67 skipped / 0 failed（`TESTS_full3.log`）。 |
| B3 后处理资源 | 完成 | S4N 云端实测（VA 105 s / 9.3 GB，C1 72 s / 9.3 GB）+ 本机真实 365×24h 轻量步骤实测（`evidence/b3b4/`）+ 外推；每运行约 6–8 min、峰值约 11 GiB。 |
| B4 数值条件与时限 | 完成 | 无一类系数范围扩大一个量级（RHS 下限 2e-4 → 1e-4）；R1 估计 4.0–4.9 h（上限 > 4.5 h → 需用户决定）。 |
| B5 修复 | 完成（`BUILD_ONLY` 干跑除外） | 修复提交 **`03677123`**（7 个文件）；v4 包 24 文件 / 148,603,385 B / 清单 `2489f123…e15d`（固定文件与 v3 逐字节相同；v3 改名 `cloud_package_dist_v3_e0527cec/`）；变体在线程预算下 7/7 相同；干跑 pre 通过、post `DONE`（与 M12b 差 0.0 EUR）；**`BUILD_ONLY` 干跑未做**（本机计算约 66 min > 1 h 时间盒）。 |
| B6 可选 | 未做 | 时间盒已用尽。 |
| 报告 | 完成 | `M10A_REPORT.md`（GO 有条件）、`M10A_EVIDENCE.json`；仓库镜像 `research/06_scope_redesign/p1_m10a_20261022/`，v4 清单 `p1_m10p_20261022/evidence/m10a_v4/`；证据提交与推送见下。 |

提交链：`d71f599e`（M10P 补充 01 收尾）→ `03677123`（M10A B5：修复 + 测试 + RUN_PLAN v3）→ **`50efec7c`**（报告、证据、v4 清单、进度）→ `9297c423`（报告 F6 行措辞、进度）。已推送至 `9297c423`（`codex/m10-batch3-20261022 -> codex/m10-batch3-20261022`（origin = `cyc292cycjin-oss/SGP-ESE5004-Stage2`），PR #49（draft，base `codex/m12b-loo-local-20261021`）随之更新；未合并 main，未 force-push。仓库镜像里的本文件写于提交前（无此 SHA 行），以 work 侧本文件为准。

本机计算合计约 66 min（三轮测试链 42 min、B3/B4 2 min、打包 1.7 min、变体复现 0.6 min、干跑 pre ~1 min、post 5.7 min、探测）；磁盘新增约 3 GB（`/home/jin/m10a_dry` 2.1 GB、`m10a_b3` 0.6 GB、`m10a_varcheck` 0.2 GB、v4 包 0.15 GB）。未连云、未上传、未调用 Gurobi、未求解模型网络。

## 补充 01（第 145 项；`M10A_SUPPLEMENT_01.md` SHA256 `4abdff42…dd70`，与 `M10A_SUPPLEMENT_01_SHA256.txt` 一致；用户 2026-10-22 启动消息"同意第 145 项"）

| 子步 | 内容 | 状态 |
|---|---|---|
| D1 | 365×24h TimeLimit / 墙钟 21,600 / 22,500 → 28,800 / 30,000 s：`run_batch3.sh` `R_TL` / `R_WALL` 与注释、`preflight.sh` 档案检查参数、测试两处、`RUN_PLAN.md` 第 2 节表 / 3.1 / 4 / 10；S4O、M08a 的历史值不改 | 完成（提交 `e0a89f8e`） |
| D2 | 违反分析与 C1 失败后重做一次（`*.failed<n>` 保留、`POSTPROC_RETRY`）；替身钩子 `FAKE_FAIL_ONCE_VA/C1_*`、`FAKE_FAIL_VA/C1_*`；新测试 4 个参数化场景全过；RUN_PLAN 3.5 / 10 | 完成（`e0a89f8e`） |
| D3 | 预检硬下限 64 GiB / 45 GB（核 25 不变）；`make_package.sh` 清单字符串；RUN_PLAN 第 5 节租用建议与硬下限分开；新测试 `test_preflight_resource_floor`（首轮在 tmpfs 上自跳过，加 `PREFLIGHT_DISK_PATH` 后单独通过） | 完成（`e0a89f8e`） |
| 测试 | M10P 文件 32 passed / 1 skipped → 单补 2 passed；全量 **615 passed / 68 skipped / 0 failed**（`evidence/s01/TESTS_s01_*.log`） | 完成 |
| D4 | v5 包：提交 `e0a89f8e`、24 文件、148,612,515 B、清单 `6fb28a77…5f63`、`SHA256SUMS` `f54f0d69…cf09`，固定文件与 v3 / v4 逐字节相同（v4 改名 `cloud_package_dist_v4_03677123/`）；干跑 pre 通过（`guards` 正反两例正确）；`BUILD_ONLY` R1–R11 全部 `BUILD_CHECK` 通过（1,133 s），与 M10P 第二次干跑逐运行相同（TimeLimit / 墙钟除外，`evidence/dryrun_v5/BUILD_VS_S01.json`）；`POST_ONLY` `DONE`（324 s），与 M12b 差 0.0 EUR | 完成 |
| 报告 | `M10A_REPORT.md` "补充 01"一节（S1.1–S1.8）、`M10A_EVIDENCE.json` `supplement_01` 字段、仓库镜像、推送 | 完成：证据提交 **`1a08cf14`**，已推送 `9297c423..1a08cf14`（PR #49）；摘要行两处占位符的订正为后续小提交（SHA 见下） |

本机计算约 49 min（测试 21 min、打包 1.8 min、干跑 pre 1 min / build 18.9 min / post 5.5 min）；磁盘新增约 11.5 GB（`/home/jin/m10a_dry_v5` 11 GB）。

脚本：`/home/jin/m10a_s01_tests.sh`（测试链）、`m10a_s01_chain.sh`（D4 链）、`m10a_s01_buildcmp.py`（构建对比）、`m10a_dryrun_v5.sh`（由 `m10a_dryrun.sh` 派生）；日志 `/home/jin/m10a_evidence/TESTS_s01_*.log`。

## 续跑点 / 待用户决定

1. **补做 `BUILD_ONLY` 干跑（约 19 min、约 9 GB）：** `STEP=build bash /home/jin/m10a_dryrun.sh`（证据自动落到 `evidence/dryrun_v4/build_only/`），完成后把 `evidence/dryrun_v4/` 再复制到仓库镜像并提交。
2. R1 时长估计上限 4.9 h > 4.5 h：报告第 8 节第 1 项三个选项，由用户决定；本次未改任何登记值。
3. 报告第 8 节第 3、4 项为非必需提案。
