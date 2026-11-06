# V31 W15 进度（台账 W15；决策清单第 212、213 项）

- 指令：`V31_W15_INSTRUCTION.md` v1，SHA256 `9440bd7d6af1c4f7fb3e43c560be983a3e6e39f522cd22e7cc1d688282ee0f2d`，与 `V31_W15_SHA256.txt` 一致（2026-11-06 开工前核对，VERIFIED）。
- 分支 `codex/v31-w15-20261106`，从 `codex/v4-w10-20261106` 头 `1899c837` 新开；worktree `/home/jin/wt_v31_w15`；交付目录 = 仓库 `research/06_scope_redesign/p1_v31_w15_20261106/`。
- 本次范围：**只做阶段 A**（F1、F2、F4 中间导出已下载；F3 与批级结果包未到位）。阶段 B 等用户在本会话说"G2 已完成"。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| A0 | SHA256 核对、分支与 worktree | 完成 | — |
| A1 | 完整性：压缩包 SHA256、解包、许可扫描、回执核对 | 完成 | `aae325ec`（与 A2 同一提交） |
| A2 | 运行事实 `RUN_FACTS.csv`、`HPC_RUNTIME_FACTS.md` | 完成 | `aae325ec` |
| A3 | 分辨率分解 `RESOLUTION_DECOMP.csv`、`RESOLUTION_CAPACITY.csv` 与图 | 完成 | `c1b561be` |
| A4 | 已知问题：油棕树干、零成本排查、燃料舱 | 完成 | `48a0d1e3` |
| A5 | `STAGE_A_REPORT.md`、`EVIDENCE.json`、台账草稿 | 完成 | `558143e5` |
| A6 | 审阅包 `REVIEW_558143e5.zip`（28 个成员，SHA256 `9a47e948adc67f8e7ab03cde08bb99b3a7e71422796a38643c9da49bd7f1421b`，不入库）与 `REVIEW_MANIFEST.csv`（逐成员 SHA256、CRC32） | 完成 | 本提交 |

**最后状态（2026-11-06）：** 阶段 A 完成，本提交之后推送 `codex/v31-w15-20261106` 并停下。阶段 B 的起点：用户在本会话说"G2 已完成"后，从指令第 5 节开始（不需重新核对 SHA256）。
