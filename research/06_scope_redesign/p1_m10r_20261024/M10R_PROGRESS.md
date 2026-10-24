# M10R 进度（第三批收尾修复；本机；不连云）

指令 `M10R_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `4a6ce9360643d47d32110d34fef402f5577b8b7d4fa05e430746bec255ec2e9e`（与 `M10R_INSTRUCTION_SHA256.txt` 一致，2026-10-24 核对）。
会话：Fable 5.1；worktree `/home/jin/wt_m10p_20261022`，分支 `codex/m10-batch3-20261022`，起点 `efef93bf`（工作树干净；v5 包提交 `e0a89f8e`）。
用户授权（2026-10-24）：本机最多 3 次 56×3h Gurobi 求解（档案 A，每次 30 分钟止损，不重试，间隔 ≥ 5 分钟）；不连云、不上传；不求解 365×24h / 2920×3h。
本机 tmux `m10dl`（完整包续传）未触碰。本机辅助脚本：`/home/jin/m10r/`（solve1.sh、solve23.sh、regress.sh、regress_all.sh、compare_dirs.py、inspect_xb.py、xb_check_all.py、variants365.sh）；中间结果：主检出 `results_project/m10r/`。

| 子步骤 | 状态 | 提交 | 说明 |
|---|---|---|---|
| 0 核对 SHA256 / worktree | 完成 | — | 分支头 efef93bf，干净；tmux m10dl 在跑 rsync（未触碰） |
| B1.1–B1.2 诊断（只读） | 完成 | — | 零容量候选跨境线路留在 `existing_cross_border_fom_ledger` meta；保留存量变体删线不过滤 meta；账本 / Owen 审计常数无保护地查归属表 |
| B1.3 56×3h 复现（求解 1/3） | 完成 | — | `results_project/m10r/keepstock_v5/`：341 s optimal 4.19 GiB；B16 KeyError '59'、C1 (c) 不可计算、M12 退出 1、NOT_ACCEPTED（与 R9 相同） |
| B2.1–B2.2 修复 + 测试 | 完成 | `40ecdf57` | `s4d_ledger.py`、`m12_rhs_audit.py`、`s4d_ledger_redo.py`、`tests/research/test_m10r_keepstock_ledger.py`（9 passed） |
| B2.3 回归 | 完成 | — | `results_project/m10r/regress_{pre,post,compare}/`：5 个无缺陷数据集全部 all_equal；保留存量修复后 ACCEPTED_LAYER2；365×24h 结构核对 `variants365/XB_LEDGER_CHECK_365.json` |
| B2.4 燃料舱 WACC 解释 | 完成（写入报告） | — | 数量不变、池价下降（甲醇 −6.40、非化石油 −6.87 EUR/MWh） |
| B3.1 `--only` / `--repost` / `--summary-s1` + 测试 | 完成 | `ae7e3f6e` | `run_batch3.sh`、`pack_results.sh`、`preflight.sh`、`m10_batch3_summary.py`、替身、`test_m10r_s1_modes.py`（8 passed） |
| B3.2 RUN_PLAN S1 节 | 完成 | `ae7e3f6e` | 第 11 节 |
| B3.3 演练（求解 2、3 + 合成解） | 完成 | `ae7e3f6e`、`cddc3f95`、`2a77f1b8` | 求解 2/3 optimal（ACCEPTED_LAYER2）；`results_project/m10r/drill/DRILL_POSTPROC.json`：9 类型 all_types_ran |
| B4.1 全量测试 | 进行中 | | `/home/jin/m10r/tests_full.sh` → `evidence/tests/TESTS_full.log` |
| B4.2 v6 打包 | 完成 | 包提交 `2a77f1b8` | `work/p1_m10p_20261022/cloud_package_dist`（24 文件 / 148,650,102 B，清单 `4113db64…`，SHA256SUMS `c2d77c49…`）；v5 改名 `cloud_package_dist_v5_e0a89f8e`；登记输入 7 项与 v5 逐字节相同 |
| B4.1 全量测试 | 完成 | `2a77f1b8` | 631 passed / 67 skipped / 0 failed（`evidence/tests/TESTS_full.log`） |
| B4.3 干跑 | 完成（BUILD_ONLY 批次除外） | | `pre` PREFLIGHT OK；`only R11` 构建与 v5 相同；`repost R9` 跑通（ACCEPTED_LAYER2，原目录不变）；**BUILD_ONLY（R1–R11）未做**：本机计算约 71 min，再做会触及 1.5 h 上限，待用户授权（`STEP=build bash /home/jin/m10r/dryrun.sh`） |
| 报告 / 证据 / 推送 | 完成 | `0d9c22a3`（已推送 origin） | `M10R_REPORT.md`、`M10R_EVIDENCE.json`；镜像到 `research/06_scope_redesign/p1_m10r_20261024/`；分支头 `0d9c22a3` |

| 补充（用户 2026-10-24 授权约 40 min）：365×24h 回归 | 完成（约 2 min） | 见下 | 不做 BUILD_ONLY；完整包核对通过后对 R1–R8、R10 用 `s4d_ledger_redo.py` + `m12_allocation.py run` 重算：账本三表 / LEDGER_IDENTITY / V5_GATES / ALLOCATION 与云端逐项相同，NODAL_PRICES 对齐后相同（`evidence/regression_365x24h/`） |

**本指令结束状态（2026-10-24 04:2x SGT）：** 全部子步骤完成，唯一未做的是批次模式 BUILD_ONLY 干跑（约 19 min 本机计算，触及 1.5 h 上限，待用户授权：`STEP=build bash /home/jin/m10r/dryrun.sh`，然后 `scripts/m10r_evidence.py` 重新生成证据 JSON 并补报告 4.3 节）。完整包续传（`m10dl`）仍在进行，未触碰。

## Gurobi 使用记录（本机）

| 次 | 内容 | 开始（UTC） | 结束（UTC） | 与上次间隔 | 结果 |
|---|---|---|---|---|---|
| 1 | 保留存量变体 56×3h，档案 A | 2026-10-23 18:32:58 | 18:38:39 | — | optimal，341 s，4.19 GiB，目标 318.480 bn |
| 2 | 分国 WACC 不互联 56×3h（R11 类型） | 2026-10-23 19:19:51 | 19:25:46 | 2,472 s | optimal，356 s，4.38 GiB，目标 302.022 bn；修复后代码 ACCEPTED_LAYER2 |
| 3 | b1 不互联 56×3h（R8 类型） | 2026-10-23 19:30:50 | 19:35:55 | 303 s | optimal，306 s，4.09 GiB，目标 319.683 bn；ACCEPTED_LAYER2 |

3 次授权全部用完（`results_project/m10r/.solves_used` = 3）。

## 续做点

从上表第一个"进行中 / 待做"的子步骤继续；求解结果与中间文件在主检出 `results_project/m10r/`；运行模式测试用 `pytest tests/research/test_m10r_s1_modes.py`（不能与真实求解同时跑：`busy()` 会互相看到 `s2_solve.py` 进程）。
