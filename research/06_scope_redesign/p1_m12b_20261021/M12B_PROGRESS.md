# M12B 进度（随进度更新）

- 指令：`M12B_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `252b211a52f9e39fa21bcdb9718cc5ed9ef8fb7c9d6fcd8d73057bf56436ec44`（与 `M12B_INSTRUCTION_SHA256.txt` 一致，2026-10-21 核对）。
- 前提：M08b 补充 01 已完成（用户确认；分支头 b018670c，最终网络在 ec80668f 上构建，再次冒烟通过 38c634ec）。
- 边界：不连云；本机 Gurobi 求解须在会话中取得用户授权后执行；许可只经 `GRB_LICENSE_FILE` 只读引用；本机无其他 Gurobi 进程、两次求解间隔 ≥ 5 分钟；不改模型、配置与网络，只改 M12 分析代码与阈值。
- 工作树：`/home/jin/wt_m12_20261021`，分支 `codex/m12b-loo-local-20261021`（自 M12 头 168bff80 + 普通 merge M08b 头 b018670c），draft PR 叠在 #46 上。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 1.1 | 新分支 + 普通 merge M08b 补充 01 头 b018670c：冲突仅 `research/STAGE2_PROJECT_LEDGER.md`（M12 与 M08b 条目各自追加），双方保留（M12 在前、M08b 在后，只删冲突标记）；合并后 `configs/`、模型脚本与 ec80668f 相同（差异只有 `m12_allocation.py`、`m12_rhs_audit.py`、`m08a_run_batch.sh`） | 完成 | 见 git log |
| 1.2 | 对偶形式验收阈值（第 138 项）改为 C1 同口径 + 单元测试 + 重评 S4O-6 与冒烟 | 进行中 | — |
| 2.1 | 网络与档案：复用补充 01 再次冒烟的一体化运行（同一网络 bca20fc0…、档案 A、前 56 时段，已导出 lp/ 与 solution/）；11 个去一国变体由 `m08a_variants.py` 从同一 2920×3h 基础网络生成 | 待做 | — |
| 2.2 | 11 次去一国求解（**须用户授权**），每次 C1 + GATES_V6 | 待授权 | — |
| 3 | 检验：c′(i)、φᵢ（对偶形式）、市场形式、违反量、容差、KVL 回路数 | 待做 | — |
| 4 | 备选方案（跨境线改可控联络线）评估，只评估不实施 | 待做 | — |
| 5 | 报告、台账、draft PR | 待做 | — |

## 接续点

- 工具脚本（WSL）：`/home/jin/m12b_merge.sh`（第 1.1 步，已执行）、`/home/jin/m12b_commit.sh`（镜像 + 提交，消息 `/home/jin/m12b_msg.txt`）。
