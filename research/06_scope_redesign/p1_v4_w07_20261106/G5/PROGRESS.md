# G5 小时曲线 — 进度

- 指令：`../V4_W07_INSTRUCTION.md` v1，SHA256 `20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf`，与 `../V4_W07_SHA256.txt` 一致（2026-11-06 核对）。只执行 B-G5。
- 分支 `codex/v4-w07-g5-20261106`，起点 `07e08f38`（`codex/v4-data-20261105` 当前头）；worktree `/home/jin/wt_v4_g5`；临时目录 `/home/jin/v4w07_g5/`（只放运行脚本与提交说明，无数据副本）。
- 仓库镜像：`research/06_scope_redesign/p1_v4_w07_20261106/G5/`（本目录逐文件复制；审阅 zip 不入库，只入库清单）。
- 求解器 0 次；不改网络、代码、配置、注册表、`T_v2`；没有下载数据（只读了 NREL 与 FfE 数据集网页上的许可说明）。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 0 | SHA 核对、建分支与 worktree | 完成 | — |
| 1 | 网络时间索引（UTC / 本地）核实 | 完成 | `bb7f0262` |
| 2 | 曲线映射、FfE 时钟检验、去季节周型、节点时区表 | 完成 | `8827b149` |
| 3 | 8,760 曲线（主算 + 9 个敏感性变体） | 完成 | `8827b149` |
| 4 | 峰值影响估计、许可登记、报告、证据、缺口 | 完成 | `5aecb537` |
| 5 | 审阅包 `REVIEW_5aecb537.zip`（33 个成员，SHA256 `37aadcec9ad4152cd563c86bece043132bab29c0dda03ab558fca89cf5eeb9eb`，清单 `evidence/REVIEW_ZIP_MANIFEST_5aecb537.txt`） | 完成 | 本提交 |

**恢复点：** 全部完成；本提交后推送 origin，停止，等待审阅端审阅。待决问题见 `REPORT.md` 第 0.2 节；共享台账未改，条目草稿在 `LEDGER_ENTRY_DRAFT.md`。
