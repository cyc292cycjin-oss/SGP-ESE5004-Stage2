## M08b：需求锚定、工业有用热、生物质溢出；重建网络与冒烟（第 126、129–134 项）

叠在 #45（M08a）上；draft，不合并 main。报告：`research/06_scope_redesign/p1_m08b_20261021/M08B_REPORT.md`。

**B1 需求锚定**
- 新需求表键 `aeo8_ats_anchor`（`research.demand.growth_method: ats_anchor`）：AEO8 ATS 人均 × 人口；TL 按 KH / LA / MM 均值 × UN WPP 2024。
- 基础负荷 11 国 966.9 TWh（旧 1,032），全部非负；交通锚 1,700 TWh（旧 2,991）；构建期逐国核对锚值。
- 物理产量规则 `sqrt_gdp_capped`：VN 水泥 107.0 Mt、VN 粗钢 40.64 Mt；11 国水泥 417 Mt、粗钢 98 Mt。

**B2 有用热与生物质溢出**
- "其他工业"桶拆成三档有用热（JRC-IDEES OIS），每节点低 / 中 / 高温母线。
- 只用 technology-data v0.15.0 有条目的技术：高温档没有电加热，三档都没有氢（v0.15.0 无对应行，待审）。
- 溢出改为有用热，删除"溢出转甲烷"与第 115 项 0.98。

**B3 注册表与测试**
- 注册表 2,121 → 2,184 行，拟增的 16 行全部写入。
- `tests/research` 550 passed / 64 skipped / 0 failed（5 个玩具求解用例排除）。

**第 3 节**
- 四个网络在 `ef01ceac` 上重建。
- 静态检查：B5 / B8 / B11 路线 / B13 / B16 / G2.1 / G2.2 与 M08b 专项全部通过；B11 完整性（S1 旧检查）在修正前网络上同样失败。
- 6 个变体两遍生成，网络逐字节相同。

**第 4 节冒烟（用户授权）**
- 56×3h、档案 A，两情景都是 optimal，GATES_V6 都是 ACCEPTED_LAYER2。
- B6 = +10.05 bn EUR（冒烟口径）；第 4 节通过标准全部满足。

**待审阅：** 氢供热、中温档上段覆盖、`gates_v6 accept` 对截断运行的 SHA 选择，详见报告开头与 §6。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
