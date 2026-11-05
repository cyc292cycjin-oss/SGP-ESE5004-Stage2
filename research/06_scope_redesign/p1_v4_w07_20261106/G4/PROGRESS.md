# G4 进度（v4 W07，B-G4：缅甸 MM、柬埔寨 KH、老挝 LA、文莱 BN、东帝汶 TL）

- 指令：`../V4_W07_INSTRUCTION.md` v1，SHA256 `20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf`（与 `../V4_W07_SHA256.txt` 一致，2026-11-06 核对）。
- 分支 `codex/v4-w07-g4-20261106`（起点 `07e08f38` = `codex/v4-data-20261105` 当前头），worktree `/home/jin/wt_v4_g4`；临时副本 `/home/jin/v4w07_g4/`。
- 仓库内交付目录：`research/06_scope_redesign/p1_v4_w07_20261106/G4/`（与本目录同步）。
- 只读：S0、S1、S2（`work/p1_v4_data_20261105/`）与 W11（`work/p1_v4_ncv_20261106/`）的交付；不碰 G0–G3、G5、W12 的目录、worktree 与分支。
- 额度：求解器 0 次；本机计算上限 2 小时；磁盘新增上限 3 GB；不下载新数据（只按 A5 查询 UNSD SDMX）。

| 子步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| G4-0 | SHA256 核对、读 A 部分与 A2 前置文档、worktree、进度文件 | 完成 | — |
| G4-1 | 国家统计基数（UNdata 导出与 SDMX 对照）、SDMX 热值（`g4_sdmx.py`、`g4_sdmx_parse.py`、`g4_facts.py`） | 完成 | G4-A `f8d6b8a8` |
| G4-2 | 自备不等式与 GIPT 核查、MM 低/中/高估算（`g4_facts.py`） | 完成 | G4-A `f8d6b8a8`（与 G4-1、G4-3 事实部分同一脚本写成，同一提交） |
| G4-3 | 水泥熟料比、生物质口径、新增产品的事实与链输入（`g4_usgs_text.py`、`g4_facts.py`） | 完成 | G4-A `f8d6b8a8` |
| G4-4 | 合并量化（两套热值，`g4_chain.py`；复现逐字节通过）、A6 表格（`g4_outputs.py`）、`EVIDENCE.json` | 完成 | G4-B `27d0368a` |
| G4-5 | 五国 `<CC>_DECISIONS.md`、`REPORT.md`、`LEDGER_ENTRY_DRAFT.md`；审阅包与推送 | 完成 | G4-C `4c1ccbcb`（报告）；G4-D（本行，收尾） |

续做起点：无。G4 完成，等待审阅端审阅；未开 PR，未合并 main，未 force-push；共用台账未改（条目草稿在 `LEDGER_ENTRY_DRAFT.md`）。

最终状态（2026-11-06）：报告提交 `4c1ccbcbb8b0acdaaffbc7fa54641c3c2ccf3926`（G4-C）已推送，`origin/codex/v4-w07-g4-20261106` 与本地一致；审阅 ZIP `REVIEW_4c1ccbcb.zip`（`git archive` 该提交的交付目录，86 个成员，SHA256 `8dd185af73c50bfc017bffcbce0452281b5e6835984782f9645ad484c5b0c019`，逐成员 SHA256 与 CRC 见 `REVIEW_ZIP_MANIFEST_4c1ccbcb.txt`；ZIP 本身只在工作目录，不进仓库）；工作目录与已提交 blob 86 个文件逐字节一致（Windows python 写出的 6 个文件已改为 LF，与仓库 `.gitattributes` 归一化后的内容相同）；本行与清单所在的收尾提交见 `git log` 头。求解器 0 次，本机计算约 2 分钟，新增磁盘约 0.11 GB，未触发停止条件。
