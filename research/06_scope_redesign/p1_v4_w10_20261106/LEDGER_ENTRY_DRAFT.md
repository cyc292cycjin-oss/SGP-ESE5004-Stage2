### W10 第一阶段：C 级参数按影响排序（第 201、211 项；2026-11-06；草稿，待并入共享台账）

- **指令：** `work/p1_v4_w10_20261106/V4_W10_INSTRUCTION.md` v1（SHA256 `14165bf1…160ed`，核对一致）。只读；求解器 0 次；没有构建、没有下载。
- **分支：** `codex/v4-w10-20261106`（从 `aad8e476`），worktree `/home/jin/wt_v4_w10`；交付 `research/06_scope_redesign/p1_v4_w10_20261106/` = `work/p1_v4_w10_20261106/`。提交见 `PROGRESS.md` 最后一行。
- **口径（VERIFIED）：** 第 201 项 1,436 / 441 = DFX F4 注册表 `72083fde` 的 REGISTERED + SENSITIVITY + DATA_PENDING；分族逐族复现。当前头 462 行 C 级（+21 行 v3），共有 441 行逐列相同。
- **方法（EXACT / INFERENCE）：** 包络定理一阶估计，三组已解结果（补充 07 365×24h 为参照；筛查 365×24h；v3.1 56×3h 冒烟），ΔB6 = ΔZ(F2) − ΔZ(F1)，Owen 按国汇总 ΔZ(F1)。容量平稳性残差 ≤ 5.6e-9，对偶价格与导出价格差 ≤ 4.5e-6。排序稳定性 Spearman 0.991 / 0.872。
- **结果（INFERENCE）：** 前 30 占可排序 |ΔB6| 之和 96 %；前 5：WACC 模式切换 −3.51 bn、MY 屋顶光伏上限 −2.06、EV 效率 +1.50、陆路交通转 ICE −1.42、ICE 效率 −1.18 bn。生物质 193 行对 B6 只有 0.43 bn，但对 ID / MY 的 Owen 分摊有数十亿欧元影响。129 行一阶不可靠（地热与 SMR 处在进入边缘、变动过大、KH CO₂ 上限零余量零对偶、DATA_PENDING 潜力无候选、原料碳全释放口径量级大）。
- **新发现（VERIFIED）：** 油棕树干成本 DATA_PENDING 在网络中按 0 进入；3 行登记但构建不读；区外封存旧口径两行不在主算。
- **交付：** `REPORT.md`、`C_GRADE_INVENTORY.csv`、`IMPACT_FIRST_ORDER.csv`、`TOP30.csv`、`W10_DOWNLOAD_CANDIDATES.csv`（来源 INFERENCE 待核实）、`UNRELIABLE_FIRST_ORDER.csv`、`REMAINING_C_TREATMENT.csv`、`rerank_with_results.py`（自测 3 项 PASS）、`EVIDENCE.json`、审阅包。
- **待决：** `REPORT.md` 第 0.1 节 9 问（参照组、交通参数归属、WACC 主算模式、生物质按 Owen 另排、油棕树干成本代理、地热 / SMR 直接求解、原料碳口径、KH 上限复查、来源核实）。
