# V4 W11 进度：燃料热值审计（台账 W11，决策清单第 204 项第 3 条）

- 指令：`V4_W11_NCV_INSTRUCTION.md` v1，SHA256 `30a83f0cca9111ea9c25e01c9a84a932b2a8a3affc82ab186fa7f2459d31b19a`（与 `V4_W11_SHA256.txt` 一致，2026-11-06 核对）。
- 分支 `codex/v4-ncv-20261106`，worktree `/home/jin/wt_v4_ncv`，起点 `b94d245f`（S1 收尾提交；按指令不跟随 S2 的新提交）。
- 仓库内交付目录：`research/06_scope_redesign/p1_v4_ncv_20261106/`（与本目录同步）。
- 不碰 `/home/jin/wt_v4_data` 与 `work/p1_v4_data_20261105/`（只读引用 S1 报告与脚本）。
- 额度：求解器 0 次；本机计算上限 2 小时；磁盘新增上限 3 GB；不下载新数据。临时副本在仓库外 `/home/jin/v4ncv/`。

| 子步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| NCV-0 | SHA256 核对、worktree、进度文件 | 完成 | — |
| NCV-1 | 第 1 节：折算系数清单、出处、调用链（`v4ncv_inventory.py`；24 个常数、6 步调用链的 文件:行 全部自动核验） | 完成 | `b5f07508`（与 NCV-2 同一提交，两步同时写成） |
| NCV-2 | 第 2 节：国别参照值（UN 2019 平衡表解析与 UNSD 隐含热值、UNSD 2014 国别表、HEESI 2019、NEB 2019、EPPO 2564、APEC 2022 图片转录、IPCC 表 1.2、GIPT 煤种） | 完成 | `b5f07508` |
| NCV-3 | 第 3 节：临时副本量化（a）–（d），口径 I（倍数不变）与 II（锚绝对量不变），未改动副本逐字节复现 | 完成 | `6d22f68b` |
| NCV-4 | 第 4 节：显著性、推荐、与 S1 合并量化（复现 S1 选项 (b) ≤ 4.2e-7 TWh）、报告 `V4_NCV_AUDIT.md`、证据 `V4_NCV_EVIDENCE.json`（1,051 项）、台账条目 | 完成 | `8ac76f58` |
| NCV-5 | 审阅包（`git archive` 报告提交）、成员清单、推送 | 完成 | 见最后一行 |

临时副本：`/home/jin/v4ncv/chain`（仓库外；脚本结束时输入已还原）。PDF 文本与 APEC 图片在 `extracted/`（不进仓库，只提交 `extracted/PDF_TEXT_INDEX.csv`）。

续做起点：无。W11 完成，等待审阅端审阅；未开 PR，未合并 main，未 force-push。

最终状态（2026-11-06）：报告提交 `8ac76f58b193c023034297d76b4d0c3587ac9d2f`（NCV-4）已推送，`origin/codex/v4-ncv-20261106` 与本地一致；审阅 ZIP `work/p1_v4_ncv_20261106/V4_NCV_REVIEW_8ac76f58.zip`（53 个成员 = 交付目录 52 个文件 + 台账，SHA256 `880d32c479dd446c5c43979be7d099f7de9ae5a5abd857baacc46f6121b93d44`，成员清单 `V4_NCV_REVIEW_ZIP_MANIFEST.txt` = `evidence/REVIEW_ZIP_MANIFEST_8ac76f58.txt`）；交付目录与工作目录 52 个文件逐一一致；本行与清单所在的收尾提交见 `git log` 头。求解器 0 次，本机计算约 10 分钟以内，新增磁盘约 0.13 GB，未触发停止条件。
