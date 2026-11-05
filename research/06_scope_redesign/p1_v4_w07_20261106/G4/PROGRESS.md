# G4 进度（v4 W07，B-G4：缅甸 MM、柬埔寨 KH、老挝 LA、文莱 BN、东帝汶 TL）

- 指令：`../V4_W07_INSTRUCTION.md` v1，SHA256 `20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf`（与 `../V4_W07_SHA256.txt` 一致，2026-11-06 核对）。
- 分支 `codex/v4-w07-g4-20261106`（起点 `07e08f38` = `codex/v4-data-20261105` 当前头），worktree `/home/jin/wt_v4_g4`；临时副本 `/home/jin/v4w07_g4/`。
- 仓库内交付目录：`research/06_scope_redesign/p1_v4_w07_20261106/G4/`（与本目录同步）。
- 只读：S0、S1、S2（`work/p1_v4_data_20261105/`）与 W11（`work/p1_v4_ncv_20261106/`）的交付；不碰 G0–G3、G5、W12 的目录、worktree 与分支。
- 额度：求解器 0 次；本机计算上限 2 小时；磁盘新增上限 3 GB；不下载新数据（只按 A5 查询 UNSD SDMX）。

| 子步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| G4-0 | SHA256 核对、读 A 部分与 A2 前置文档、worktree、进度文件 | 完成 | — |
| G4-1 | 国家统计基数（UNdata 导出与 SDMX 对照）、SDMX 热值（`g4_sdmx.py`、`g4_sdmx_parse.py`、`g4_facts.py`） | 完成 | 见 G4-A |
| G4-2 | 自备不等式与 GIPT 核查、MM 低/中/高估算（`g4_facts.py`） | 完成 | 见 G4-A（与 G4-1、G4-3 事实部分同一脚本写成，同一提交） |
| G4-3 | 水泥熟料比、生物质口径、新增产品的事实与链输入（`g4_usgs_text.py`、`g4_facts.py`） | 完成 | 见 G4-A |
| G4-4 | 合并量化（两套热值，`g4_chain.py`；复现逐字节通过）、A6 表格（`g4_outputs.py`）、`EVIDENCE.json` | 完成 | 见 G4-B |
| G4-5 | 五国 `<CC>_DECISIONS.md`、`REPORT.md`、`LEDGER_ENTRY_DRAFT.md`；审阅包与推送 | 报告完成，审阅包与推送见最后一行 | 见 G4-C、G4-D |

续做起点：无（G4-C 提交后只剩审阅包、最后一行与推送）。
