# W12 进度（V4_W07_INSTRUCTION.md B-W12，SHA256 20d03b69…7baf 已核对）

- 分支 `codex/v4-w07-w12-20261106`（起点 07e08f38 = `codex/v4-data-20261105` 头），worktree `/home/jin/wt_v4_w12`，临时目录 `/home/jin/v4w07_w12/`。
- 早先（2026-11-06 02:21–02:22 SGT）有一次 W12 尝试只建了 worktree 与 4 个探查脚本（`/home/jin/v4w07_w12/scripts/`），无输出、无提交、无进程；本会话（03:14 起）沿用。
- v3.1 代码 d3b9a3bc 与分支头 07e08f38 在 `research/` 以外 0 个文件差异；13ebce95（冒烟演练包）与 d3b9a3bc 在 `scripts_project`、`configs` 无差异。
- 只读；求解器 0 次；不改仓库模型代码、配置、网络、注册表、`T_v2`。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| W12-1 | 天然气产量上限（毛产量 vs 商品气） | 完成（`scripts/w12_gas.py`，表 `tables/W12_1_*.csv`） | 2fe21e8d |
| W12-2 | 铁路非电燃料重复加载 | 完成（`scripts/w12_rail.py`、`w12_rail_b6.py`，表 `tables/W12_2_*.csv`；临时副本 `/home/jin/v4w07_w12/chain` 未改动时 8 个输出逐字节复现） | a8744e95 |
| W12-3 | 蔗渣两端热值 | 完成（`scripts/w12_bagasse.py`，表 `tables/W12_3_*.csv`；s3_0 未改动副本 4 个输出逐字节复现） | 6dc598c6 |
| W12-4 | UNdata 导出缺品种（覆盖缺口） | 完成（`scripts/w12_sdmx.py`、`w12_coverage.py`、`w12_coverage_chain.py`；SDMX 11 个原始响应 `sdmx/`，登记 `DATA_REGISTRY_W12_SDMX.csv`；表 `tables/W12_4_*.csv`） | 0728ca4c |
| W12-5 | 同类排查 | 完成（`scripts/w12_scan.py`，表 `tables/W12_5_*.csv`，疑点清单 `W12_5_SUSPECTS.csv` 11 条） | 本提交 |
| W12-6 | 报告、证据、审阅包 | 进行中 | |

续做点：W12-6（报告 REPORT.md、合并 EVIDENCE.json、MISSING_DATA.csv、台账草稿、审阅包）。
