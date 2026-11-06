### W08：v4 定稿写进仓库（第 203–211 项；2026-11-06；草稿，待并入共享台账）

- **指令：** `work/p1_v4_w08_20261106/V4_W08_INSTRUCTION.md` v1（SHA256 `17fdf2f1…c077c0`，与 `V4_W08_SHA256.txt` 核对一致）。实施；求解器 4 次（第 5 节授权的 56 时段冒烟），没有下载新数据，没有连 HPC。
- **分支：** `codex/v4-w08-20261106`（从 `aad8e476` = I2 头），worktree `/home/jin/wt_v4_w08`；交付 `research/06_scope_redesign/p1_v4_w08_20261106/` = `work/p1_v4_w08_20261106/`。提交见 `PROGRESS.md` 最后一行；已推送，没有开 PR。
- **实施（VERIFIED / EXACT）：** 清单第 1–10 节进仓库，开关 `research.demand.anchor_mode`（ras / iid / iib / external）与 `research.demand.v4.*`（默认关 = v3.1）；新模块 `v4_common`、`v4_base_sdmx`、`v4_industry_cache`、`v4_industry`（`run_case` 供 W10）、`v4_products`、`v4_biomass_potential`、`v4_gas_caps`、`v4_profiles`、`v4_outputs`、`v4_registry`；m08b / s3_0 只加选项。A0 / A1：33 个检查点与参照引擎差 0；A2：开关全关 8 个输出与 v3.1 逐字节相同；A3：注册表 +69 行（原有 2,321 行不变），全量测试见 `PROGRESS.md`。
- **参照值（EXACT）：** 东盟 2050 `T_v2` 主算（IIa、造纸木材 (a)）3,490.34 TWh（"其他" 45.0 %），IId 3,166.52；相对 I2 +162.00 = 造纸木材 −161.81 + 锚 IIa +323.82。
- **网络与冒烟（VERIFIED）：** 网络 `cbe051d8…`（主算一体化）、`aa2bab39…`（主算不互联）、`09480713…`（IId）；静态检查全过。4 次 optimal；R0 = v3.1 冒烟逐位相同；v4 − v3.1：+8.138 / +8.459 / +2.592 bn；B6（只作回归）12.884 bn（v3.1 12.563）。判据 4（一阶 ± 50 %）三对都不满足；数据链无错；结果在 LP 凸性上下界内；原因为工业热价随需求大降（ID 47.7 → 25.2 EUR/MWh，INFERENCE 为二阶项）。按指令停下汇报。
- **交付：** `REPORT.md`、`REFERENCE_V4_MAIN.csv`、`REFERENCE_V4_IID.csv`、`CHECKPOINTS.csv`、`STATIC_CHECKS.md`、`SMOKE56_V4.md`、`DATA_TO_REPLACE.csv`、`HPC_V4_PLAN_DRAFT.md`（草案）、`EVIDENCE.json`、`PROGRESS.md`、审阅包（逐成员 SHA256 + CRC32）。
- **待决：** `REPORT.md` 第 0.1 节 9 问（第 211 项第 2 条读法 +36.89 TWh、残渣扣减与 C.3、VN 溢出口径、门判据字面、成本判据改用上下界与否、过程排放按 v4 倍数、与清单写法不同处、HPC 打包前两项改动、小项）。
