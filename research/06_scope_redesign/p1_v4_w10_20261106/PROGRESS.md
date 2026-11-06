# V4 W10 第一阶段 进度（C 级参数按影响排序）

指令：`V4_W10_INSTRUCTION.md`（SHA256 `14165bf102dbfcb25fa06255a4884474691515a33eb3b86866886d8542a160ed`，与 `V4_W10_SHA256.txt` 一致，2026-11-06 核对）。
分支 `codex/v4-w10-20261106`（从 `codex/v4-i2-20261106` 头 `aad8e476` 新开），worktree `/home/jin/wt_v4_w10`；交付镜像 `research/06_scope_redesign/p1_v4_w10_20261106/`。
只读：不改仓库代码、输入、注册表；求解器 0 次；不下载。

| 子步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| W10-0 | SHA 核对、分支与 worktree、口径对账（第 201 项 1,436 / 441 = 72083fde 注册表 REGISTERED+SENSITIVITY+DATA_PENDING） | 完成 | — |
| W10-1 | `C_GRADE_INVENTORY.csv`（462 行在用 C 级，含入网路径与一阶机制；`scripts/build_inventory.py`） | 完成 | `15c2b968` |
| W10-2 | 已解结果提取与一阶影响 `IMPACT_FIRST_ORDER.csv`、`UNRELIABLE_FIRST_ORDER.csv`（3 组 6 个网络；平稳性与价格核对 `evidence/CHECKS.json`） | 完成 | `fdcc3f91`（与 W10-3、W10-4 同一提交：三者由同一脚本链一次写出） |
| W10-3 | `TOP30.csv`、`W10_DOWNLOAD_CANDIDATES.csv`、`REMAINING_C_TREATMENT.csv` | 完成 | `fdcc3f91` |
| W10-4 | `rerank_with_results.py` 重排接口与自测（`evidence/SELFTEST.json`，3 项 PASS） | 完成 | `fdcc3f91` |
| W10-5 | `REPORT.md`、`EVIDENCE.json`、台账条目草稿 `LEDGER_ENTRY_DRAFT.md`、审阅包、推送 | 完成 | `3704ffef`（报告与证据）；审阅包清单与本文件最后一行在其后的最终提交 |

提交 `15c2b968`、`fdcc3f91` 时命令多带了 `-c core.hooksPath=.git/hooks`；已核实仓库未设置 `core.hooksPath`、hooks 目录只有 `.sample`、未安装 pre-commit，没有 hook 被跳过；之后的提交不带该参数。

缓存 `cache/`（6 个网络的提取，22 MB）只在工作目录，不入库；`rerank_with_results.py --cache` 指向它即可复用。
求解器 0 次；本机计算合计约 3 分钟（提取 61 s，各次重排 20 s）；磁盘新增约 25 MB。

## 续做起点
- 从上表第一个"进行中 / 待做"的子步继续；中间结果缓存在 `cache/`（按已解网络 SHA256 分目录，可直接复用）。

## 最后状态（2026-11-06）
- 审阅包 `work/p1_v4_w10_20261106/REVIEW_3704ffef.zip`（29 个成员、321,651 字节，SHA256 `7ae47e40461415f520fcf3bfe0f0c9b0741b57675642ce448773e773d1c140b6`，不入库）；逐成员 SHA256 与 CRC32 见 `REVIEW_MANIFEST.csv`（已解压校验）。
- 提交：`15c2b968`（W10-1）→ `fdcc3f91`（W10-2/3/4）→ `3704ffef`（W10-5 报告与证据）→ 最终提交（本行与审阅包清单，见 `git log -1`）。按指令推送后停止；不合并 main，不 force-push，没有跳过 hooks（仓库未配置 hooks）。
- 下一步（另行通知）：W08 合入后的第二阶段（实际替换数据）；v3.1 2920×3h F1 / F2 到位后用 `rerank_with_results.py --reference <新组>` 重排一次（REPORT.md 第 4 节）。
