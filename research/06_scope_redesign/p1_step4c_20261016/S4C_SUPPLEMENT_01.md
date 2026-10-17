# S4C 补充 01：走廊海底份额与走廊成本（台账 L18，落实第 16 项）

**版本：** v1，2026-10-16 22:00 SGT，由 Claude（审阅端）写入。与 `S4C_CLAUDE_CODE_INSTRUCTION.md` 一起执行，作为 S4C-1 的第 5 条（在 S4C-1 的提交中完成，或紧随其后单独提交）。开始前核对本文件 SHA256（`S4C_SUPPLEMENT_01_SHA256.txt`）。

**背景：** S1 报告第 156 行写明，走廊表 `research_inputs/corridors/cross_border_corridors.csv` 的 `subsea_share` 全为 0（冻结底座没有 `underwater_fraction`），"新走廊待 L18"；S2B（R5）、S3 的氢、CO₂、气管道候选也取这一列。因此所有跨境候选（电、氢、CO₂、气）目前都按陆上成本计价，包括明显跨海的走廊。technology-data v0.15.0 中海底直流电缆比架空线贵得多，这会系统性高估互联的经济性，直接影响互联价值与成本分摊。第 16 项（已确认）要求海底段单独计价；本补充是落实，不是新决定。

## 任务

1. **海底份额的计算（按 PyPSA-Eur 做法）：** 先引用 PyPSA-Eur v2025.07.0 中计算 `underwater_fraction` 的代码与所用形状（引用文件与行号）。对走廊表每条走廊、以及电网拓扑上的全部候选管道（跨境与国内，含 S3 的连通性补全候选），按两端节点间的路径（与长度计算同一路径：大圆 × 长度系数）与作者的陆地/海上形状求交，得到海底份额。不需要下载任何数据（形状在 pypsa-asean 本机已有）；若形状不足以判定，停下报告。
2. **应用：**
   - 电力候选（跨境直流/交流链路及线路，若有扩建成本）：年化成本 =（1 − 海底份额）× 陆上单价 + 海底份额 × 海底单价，单价取 technology-data v0.15.0（`HVDC overhead` / `HVDC submarine` / `HVAC overhead` / `HVAC submarine` / 换流站，以实际存在的行为准），引用 PyPSA-Eur 相应代码行；
   - 氢、CO₂、气管道候选：同理用陆上与海底管道行（如 `H2 (g) pipeline` / `H2 (g) submarine pipeline`、`CO2 pipeline` / `CO2 submarine pipeline`、`CH4 (g) pipeline` / `CH4 (g) submarine pipeline`）；
   - 国内跨岛候选（如 ID 各岛之间、PH 各岛之间、MY 半岛与沙巴/砂拉越）同样适用。
3. **存量走廊：** 存量容量不计新投资（第 48 项），只更新海底份额字段用于报告。
4. **核对：** 列出全部跨境走廊的海底份额与修正前后的年化成本；用常识核对几条明显的海底走廊（如 SG–ID 巴淡、MY 半岛–沙巴/砂拉越、PH–MY、ID 苏门答腊–MY 半岛），以及几条明显的陆上走廊（如 LA–TH、KH–VN），结果不合理时停下报告。
5. **开关：** `research.corridors.subsea_share: geometric`（主算）| `zero`（原状，对照）。
6. **报告：** 写入 S4C 报告单独一节；台账 L18 的完成依据。
