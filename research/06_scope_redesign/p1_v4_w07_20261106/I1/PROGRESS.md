# I1 进度（V4_I1_INSTRUCTION.md v1，SHA256 be5687e2…63d0 已核对，与 V4_I1_SHA256.txt 一致）

- 分支 `codex/v4-i1-20261106`（起点 `07e08f38` = `codex/v4-data-20261105` 头，2026-11-06 核对远端一致），worktree `/home/jin/wt_v4_i1`，临时副本 `/home/jin/v4i1/`。
- 只读；求解器 0 次；不改仓库模型代码、配置、网络、注册表、`T_v2`；不下载（SDMX 原始响应沿用 W12 的 11 个文件，只读核对）。
- 交付目录 `work/p1_v4_w07_20261106/I1/` = 仓库 `research/06_scope_redesign/p1_v4_w07_20261106/I1/`（zip 不入库）。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| I1-1 | 2019 基年 SDMX 重建、四类差异、截断扫描、链路量化 | 完成（`scripts/i1_sdmx.py`、`i1_base.py`、`i1_trunc.py`、`i1_chain.py`；复现关 G1/G2/G3 与链路逐字节复现均通过） | 见 git log（I1-1） |
| I1-2 | RAS 与增长锚机制、跨国耦合、AEO8 基数、修正分类 | 完成（`RAS_MECHANISM.md`、`CORRECTION_CLASSIFICATION.csv`、`scripts/i1_aeo8.py`、`i1_classify.py`；链路变体 IIa–IId 在 `i1_chain.py`） | 见 git log（I1-2/3/4） |
| I1-3 | HVC / 甲醇 2050 单耗 | 完成（`HVC_VECTOR_CHECK.csv`、`scripts/i1_hvc.py`，临时副本中运行 PyPSA-Eur 原函数，分量复现登记表） | 同上 |
| I1-4 | ID / MM 家庭汽油 | 完成（`ID_GASOLINE_CHECK.csv`、`scripts/i1_gasoline.py`；2050 年量化来自链路情形 GASmove） | 同上 |
| I1-5 | 报告、证据、审阅包 | 报告 `REPORT.md`、`EVIDENCE.json`、`LEDGER_ENTRY_DRAFT.md` 完成；审阅包与收尾提交见下一行 | 见 git log（I1-5） |

| 收尾 | 审阅包 `REVIEW_2d5e1c4a.zip`（59 个成员，474,904 B，SHA256 `5dae9e8a…75c0`，testzip OK；zip 不入库，清单 `evidence/REVIEW_ZIP_MANIFEST_2d5e1c4a.txt` 入库）；本进度最终行 | 收尾提交 |

提交：`5beef54b`（I1-1）、`9e81c034`（I1-2/3/4）、`2d5e1c4a`（I1-5 报告）、收尾提交（本行）。续做点：若会话中断，`scripts/i1_*.py` 均可单独重跑（输出覆盖写入本目录；链路副本在 `/home/jin/v4i1/chain`）。

**最终状态（2026-11-06 SGT）：I1 全部完成，只读，求解器 0 次，已推送 `codex/v4-i1-20261106`，未建 PR；等待审阅端审阅。未改共享台账（草稿见 `LEDGER_ENTRY_DRAFT.md`）。**
