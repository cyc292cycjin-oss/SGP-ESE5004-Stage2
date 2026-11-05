# I2 进度（V4_I2_INSTRUCTION.md v1，SHA256 36c3a2bd…fdd5 已核对，与 V4_I2_SHA256.txt 一致）

- 分支 `codex/v4-i2-20261106`（起点 `07e08f38` = `codex/v4-data-20261105` 头，开工时本地与远端一致），worktree `/home/jin/wt_v4_i2`，临时副本 `/home/jin/v4i2/`。
- 只读：求解器 0 次；不改仓库模型代码、配置、网络、注册表、`T_v2`；不跳过 git hooks（仓库未启用 hooks，只有 `.sample`）。
- 交付目录 `work/p1_v4_w07_20261106/I2/` = 仓库 `research/06_scope_redesign/p1_v4_w07_20261106/I2/`（zip 不入库）。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| I2-1 | 合并 9 个分支（合并提交，不变基）；台账条目并入 | 合并完成：`7c23e456`（ncv，台账冲突保留双方）→ `80961534`（G0）→ `ed9f967b`（G1）→ `ac05af91`（G2）→ `bdb04eab`（G3）→ `913d86b6`（G4）→ `c49531a0`（G5）→ `a180b8b0`（W12）→ `a2daeaca`（I1）；`research/` 以外 0 个文件改动 | 合并提交如左；台账条目见 git log（I2-1） |
| I2-2 | 统一重算链（临时副本、复现关） | 完成：`scripts/i2_base.py`（复用 I1 重建代码，S0–S4 与 I1 逐位一致，S5p 只在 ID 非能源焦炭一行 +1.759 TWh）、`i2_engine.py`（未改副本 8 个输出逐字节复现，v3 11 国 `T_v2` 与"其他"偏差 0）、`i2_repro.py`（I1 12 情形 ≤ 2.3e-13 TWh；G0/G1/G2/G3 ≤ 5e-7；G4 MM 1.07e-4 TWh） | 见 git log（I2-2） |
| I2-3 | 11 国逐步重算、可加性、生物质潜力 | 完成：`i2_chain.py`（16 步 + 14 单步 + 30 敏感性，每次约 2.2 分钟）、`i2_biomass.py`；东盟 `T_v2` 3,820.05 → 3,328.34 TWh；可加性差 +15.03 TWh；潜力 1,990.82 → 1,618.48 TWh | 见 git log（I2-3） |
| I2-4 | 结果对照、图、小时曲线、敏感性前 10 | 完成：`i2_tables.py`、`i2_peaks.py`（G5 对照组 0 GW；主算 +21.52 GW）、`i2_sens.py` | 同上 |
| I2-5 | W08 实施清单、验证计划、缺失数据汇总 | 完成：`W08_IMPLEMENTATION_SPEC.md`、`W08_VALIDATION_PLAN.md`、`i2_missing.py`（24 个主题） | 同上 |
| I2-6 | 报告、证据、台账、审阅包、推送 | 报告 `REPORT.md`、`EVIDENCE.json`、台账条目（`LEDGER_ENTRY_DRAFT.md`，并写入台账）完成；审阅包与收尾见下一行 | 见 git log（I2-6） |

续做点：若会话中断，按 `scripts/i2_base.py` → `i2_chain.py` → `i2_biomass.py`（S7 用的潜力文件）→ `i2_chain.py` → `i2_tables.py` → `i2_peaks.py` → `i2_sens.py` → `i2_missing.py` → `i2_repro.py` → `i2_evidence.py` 重跑（临时副本 `/home/jin/v4i2/`，输出覆盖写入本目录）。
