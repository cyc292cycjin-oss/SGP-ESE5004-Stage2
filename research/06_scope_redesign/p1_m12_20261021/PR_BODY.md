M12（第 133 项）：分摊分析流程——Owen 分配、线路净租金区间、燃料舱参与者、去一国检查、右端项审计。**不求解、不调用 Gurobi、不连云**；只新增分析代码、测试与文档（C3 在 `m08a_run_batch.sh` 中加 M12 步骤）。叠在 #45（M08a）上。

**⚠ 醒目发现（VERIFIED）：** 指令 §0 的成本形式（= 现行账本：资产成本 + 节点对偶结算 ± 走廊净租金）不等于 Owen 的 y′b。差额来自 KVL 回路约束（右端项 0、回路跨国）的乘子在线路所有者之间的转移：S4N 试点 365×24h VN +0.257、LA −0.257、MM +0.042 bn 等（56×3h 冒烟：KH −0.91、TH +0.84 bn；精确分解偏差 15 EUR）。右端项归属前提成立；已实现 Owen 对偶形式，主值口径待决定（报告 §6 D1）。

- **C1** `scripts_project/m12_allocation.py`：`run` / `benefit` / `loo`——12 个参与者（11 国 + 燃料舱）EUR2020 / USD2020，B16，α 0 / 0.5 / 1、按长度与分国区间，逐走廊净租金，与现行账本逐实体对账，S4P 规则 (ii)(iii) 同比例对照（结论：不同比例），受益与 5 种比例权重，去一国 c′(i) / 不可分成本 / SCRB。
- **C2** `scripts_project/m12_rhs_audit.py`：365×24h 一体化 LP 只构建（9,017,345 行，42 s，8.05 GiB）：非零右端项无主 0、无法归属 0；唯一耦合族 = KVL；Owen 对偶形式闭合 −6.4 万 EUR（相对 −1.2e-7）；11 国去一国变体右端项一致。
- **C3** `m08a_run_batch.sh`：每个运行 C1 之后、GATES_V6 验收之前做分摊（+ 对偶形式）并登记 `EXPORTS.json`；重评后生成批级受益对照；去一国目录存在时做去一国检查。
- **C4** 玩具 3 国 LP（scipy HiGHS，7 个联盟）与对偶退化例；修正前结果（S4N + S4O-6）跑通：S4P 第 8 方面表复现到 1.5e-13 bn，B6 69.243 bn，Owen 受益为负仅燃料舱。
- 测试：`tests/research` 全量 544 passed / 64 skipped / 0 failed（排除其他步骤 5 个玩具求解用例）。

报告：`research/06_scope_redesign/p1_m12_20261021/M12_REPORT.md`；待决定事项 D1–D10 见其 §6。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
