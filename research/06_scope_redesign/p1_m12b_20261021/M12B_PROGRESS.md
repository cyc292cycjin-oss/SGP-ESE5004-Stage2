# M12B 进度（随进度更新）

- 指令：`M12B_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `252b211a52f9e39fa21bcdb9718cc5ed9ef8fb7c9d6fcd8d73057bf56436ec44`（与 `M12B_INSTRUCTION_SHA256.txt` 一致，2026-10-21 核对）。
- 前提：M08b 补充 01 已完成（用户确认；分支头 b018670c，最终网络在 ec80668f 上构建，再次冒烟通过 38c634ec）。
- 边界：不连云；本机 Gurobi 求解须在会话中取得用户授权后执行；许可只经 `GRB_LICENSE_FILE` 只读引用；本机无其他 Gurobi 进程、两次求解间隔 ≥ 5 分钟；不改模型、配置与网络，只改 M12 分析代码与阈值。
- 工作树：`/home/jin/wt_m12_20261021`，分支 `codex/m12b-loo-local-20261021`（自 M12 头 168bff80 + 普通 merge M08b 头 b018670c），draft PR 叠在 #46 上。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 1.1 | 新分支 + 普通 merge M08b 补充 01 头 b018670c：冲突仅 `research/STAGE2_PROJECT_LEDGER.md`（M12 与 M08b 条目各自追加），双方保留（M12 在前、M08b 在后，只删冲突标记）；合并后 `configs/`、模型脚本与 ec80668f 相同（差异只有 `m12_allocation.py`、`m12_rhs_audit.py`、`m08a_run_batch.sh`） | 完成 | 见 git log |
| 1.2 | 对偶形式验收阈值（第 138 项）改为 C1 同口径：`m12_allocation.dual_acceptance` / `c1_thresholds_eur`（恒等式 \|Σφ − c(N)\| ≤ 0.01 bn = C1 (a) 绝对标准；每个参与者残差影响 ≤ C1 (b) 阈值，燃料舱用 ASEAN 实体）；`owen_summary` 两项共同决定 `usable_for_allocation`；`_dual_alloc` 在重评（D9）后按当前参照复核；`m12_rhs_audit.py regrade`（不改输入）。测试 `test_dual_acceptance_c1_scale_item138`；`test_m12_allocation.py` + `test_m08a_a8.py` 34 passed。重评（`evidence/regrade_138/`）：S4O-6 不互联 false → **true**（差 +0.76 M EUR）；S4N 试点 true → true；56×3h 冒烟（S4M-1 网络）false → **false**（差 −18.07 M EUR > 0.01 bn） | 完成 | 见 git log |
| 2.1 | 不求解的准备（`scripts/m12b_prep.sh`）：**复用**补充 01 再次冒烟的一体化运行（`results_project/m08b/smoke_s01/integrated`：同一网络 bca20fc0…、档案 A formal_barrier、前 56 时段、optimal、ACCEPTED_LAYER2，已导出 lp/ 与 solution/；运行在 6c960ca7 上，模型代码与本分支相同）→ 求解减为 11 次；复用文件 SHA256 见 `evidence/M12B_REUSED_RUN_FILES.csv`。新目录 `results_project/m12b/full_{integrated,disconnected}`（符号链接 + M12 输出，不写 M08b 目录）：一体化对偶形式恒等式差 2.4 EUR（相对 1.2e-11），第 138 项验收通过、可用。11 个变体（`m08a_variants.py`，不加 stale 开关，各约 3.5 s，`stale_config: false`，回执 SHA256 与文件一致，`evidence/M12B_VARIANT_FILES.csv`）。KVL 回路（`scripts/m12b_loops.py`，`evidence/M12B_KVL_LOOPS.json`）：全网 71（= LP 中 KVL 行 3,976 / 56）；去一国后 BN 71、ID 53、KH 57、LA 43、MM 57、MY 61、PH 71、SG 71、TH 42、TL 71、VN 57；穿越国界的回路 ID 9、KH 11、LA 28、MM 9、MY 10、TH 28、VN 14，其余 0 | 完成 | 见 git log |
| 2.2 | 11 次去一国求解（用户 2026-10-21 13:29Z 授权，云端无运行经用户确认；`scripts/m12b_loo.sh`，提交 fcd19202 dirty 0）：13:29–15:34Z 串行，间隔 332–333 s；10 次 optimal、SG suboptimal（内点停滞后返回，C1 (a) 0.0021 bn）；11 次 C1 (a)(b)(c) 全过、GATES_V6 ACCEPTED_LAYER2、右端项检查通过 | 完成 | 结果随下一提交 |
| 3 | 检验（`scripts/m12b_analysis.py`，`evidence/M12B_RESULT.json`）：11 国违反量全为 0（φᵢ − c′(i) 最小 BN +0.002 bn），市场形式全部通过，不可分成本 +88.6 bn（11 国部分 +12.6 bn）；**事先登记的规则 → 维持现有建模** | 完成 | 同上 |
| 4 | 备选方案评估（`evidence/M12B_ALTERNATIVE_ASSESSMENT.md`）：62 条跨境交流线 / 2,570 MW；约 8–10 个文件、120–200 行；四网络重建；对 PyPSA-Eur 结构性偏离；不实施 | 完成 | 同上 |
| 5 | 报告 `M12B_REPORT.md`、台账 M12b 条目、draft PR（叠在 #46 上）、审阅 ZIP | 进行中 | — |

## 接续点

- 工具脚本（WSL）：`/home/jin/m12b_merge.sh`（第 1.1 步，已执行）、`/home/jin/m12b_commit.sh`（镜像 + 提交，消息 `/home/jin/m12b_msg.txt`）。
