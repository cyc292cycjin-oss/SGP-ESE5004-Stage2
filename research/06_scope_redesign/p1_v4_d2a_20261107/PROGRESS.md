# D2a 进度（V4_D2A_INSTRUCTION.md v1，SHA256 4920db63…38fa 已核对，与 V4_D2A_SHA256.txt 一致；开工 2026-11-07 14:45 SGT）

- 分支 `codex/v4-d2a-20261107`，起点 `4026c1c84d8d349e9bb8c11f3e6da8f82588d621` = `codex/v4-d1-20261107` 头（fetch 核过，本地 = 远端）；`6142d8ac`（D1 审阅包）是其祖先，二者之间只改了 `research/06_scope_redesign/p1_v4_d1_20261107/` 下 3 个文件（PROGRESS.md、evidence/REVIEW_ZIP_MANIFEST_6142d8ac.txt、scripts/leak_scan.sh），交付目录之外 0 个。
- worktree `/home/jin/wt_v4_d2a`；临时目录 `/home/jin/v4d2a`；主检出 `results_project/v4d2a/`（构建与冒烟输出，不入库）。
- 交付目录 `work/p1_v4_d2a_20261107/` = 仓库 `research/06_scope_redesign/p1_v4_d2a_20261107/`（zip 不入库）。
- 求解额度：至多 6 次（第 6 节 2 次、第 7 节至多 4 次）；**已用 6 / 6**（第 6 节 2 次 2026-11-07 16:11–16:30 SGT，第 7 节 4 次 16:30–17:12 SGT；全部 optimal，无重试）。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| D2a-1 | 第 1 节：分支、worktree、祖先核实 | 完成 | （随 D2a-2 提交） |
| D2a-2 | 第 2 节：Fable 修复 F-01 / F-02 / F-05 / F-06 / F-07，F-03 / F-04 口径说明，S4 顺手修复（F-11 / F-12 / F-14） | 完成：`residue_literal` 开关值与表目录（ID +36.889854 TWh = Fable EXACT）；溢出列在守恒层后重算（VN 29.95 → 41.10 / 20.93 → 32.07 TWh = 网络台账，网络不变）；参照引擎同规则重跑，检查点 33 步 0 差；BN NEU 2019 基数扣减；注册表 tier 说明与 `file:` 定位；m08b 收敛记录入表目录；A2 扩展到 56 文件；`test_v4_d2a_fixes.py` 11 项；F-14 差额实为尘埃清理（文档） | `f90bba46` |
| D2a-3 | 第 3 节：甲醇 / 氢（3.1）、EFB 热值基准 T04（3.2）、抽蓄存量对账（3.3）、抽蓄 `asean` 开关（3.4） | 完成：`meoh_per_tco2` 开关键（主集化学计量 4.02481710559）接入 s3_layers；T04：EFB / 纤维基准不一致 → 新主集潜力 `v4_adjusted_t04`（EFB × 0.48，东盟固体潜力 1,618.48 → 1,448.09 TWh），PKS 一致保留，树干无法判定保留 + 区间；Bhumibol 950 → 171 抽蓄 + 608.2 常规 + 170.8 剔除（EGAT / ANDRITZ / IHA），`research.fleet.phs_stock_reclass`；`research.supply.phs_case: asean`（三档时长、Lu 2021 成本、ANU 能量上限钩子）；注册表 +32 行；测试 11 项；T04 参照检查点 0 差 | `50dfdcf7` |
| D2a-4 | 第 4 节：重排修正与 W19 候选表 | 完成：`rerank_with_results_d2a.py`（封存上限 = 全局行 + Store `e_nom` 上界对偶；S-B 船运 6 行退出排序；偏向列；10 对区间按物理界刷新；读网络前的守卫）；276 行排序，KH 封存上限第 259 → 3（ΔB6 −2.16 bn），与 W15 前 30 重合 27、Spearman 0.945；`RERANK_D2A_TOP30.csv`、`RERANK_D2A_OWEN_TOP10.csv`、`RERANK_D2A_VS_W15.csv`、`W19_CANDIDATES.csv` | 随 D2a-3 / D2a-8 提交 |
| D2a-5 | 第 5 节：重建 56 时段网络、静态检查、检查点 | 完成：一体化 `334904c4…`、`no_new_xb` `9ec39333…`；C1–C6、C10 通过；C8 对 D1 只含预期差异（9 个池、`TH2 4` 拆分、泰国来水重分配、30 条甲醇化链路系数）；零松弛门通过；检查点 0 差 | `63651f19` |
| D2a-6 | 第 6 节：登记报警线后 2 次冒烟 | 完成：登记（下界 F1 +6,563 M / F2 +6,095 M；报警线 +6,516 / +6,049 M EUR）；2 次求解 optimal、ACCEPTED_LAYER2、失败门在 v3.1 并集内、ΔV +9,526.7 / +8,974.0 M 高于报警线（`SMOKE56_D2A.md` 第 2 节、`tables/D2A_SMOKE56_RESULTS.csv`、`evidence/D2A_smoke56.json`）；56 时段 B6 12.3311 bn（D1 12.8839） | 登记 `63651f19`；结果随 D2a-6b/7b 提交 |
| D2a-7 | 第 7 节：成本上升归因（至多 4 次求解） | 完成：角点表集与网络（`d4p31`、`d31p4`）；4 次求解全部 optimal、ACCEPTED_LAYER2、失败门在并集内（`tables/D2A_ATTRIB56_RESULTS.csv`、`evidence/D2A_attrib56.json`）；两因素 Shapley（`ATTRIBUTION_56.md`）：F1 总变化 +17.67 bn = D −7.46 + P +25.13（交互 −12.33）；(D31,P31) 用 v3.1 冒烟 + 其他改动近似（INFERENCE） | 表集 `8e94bbe5`；结果随 D2a-6b/7b 提交 |
| D2a-8 | 第 8 节：报告、证据、审阅包、推送 | 待做 | |

续做点：第 6、7 节求解与评估已完成（求解器 6 / 6 次用尽）→ 提交 D2a-6b/7b → 第 8 节：`REPORT.md` 第 7 节与第 0 节、`scripts/d2a_evidence.py` → `EVIDENCE.json`、`scripts/d2a_review_zip.py <提交>`、`scripts/leak_scan.sh`、最终提交 D2a-8 → 推送 `codex/v4-d2a-20261107`（不开 PR，推送后停止）。
