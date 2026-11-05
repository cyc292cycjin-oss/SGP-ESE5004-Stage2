# SG 需要用户决定的问题（G3，v4 W07）

数字均为 2050 年、口径 I，"主算"指全部合并情形（`T_v2` 121.84 TWh，"其他"44.03 TWh，36.1 %；v3 74.18 / 46.63 TWh，62.9 %）。SG 热值不变（UNSD = v3 = 25.8 GJ/t），自备电厂不等式成立且无自备煤电，生物质无工业用量。出处见 `REPORT.md` 第 4 节与 `SG_OTHER_SHARE_STEPS.csv`。

1. **乙烯 / HVC 显式化使 SG `T_v2` +47.64 TWh（+64 %）**：是否接受？这是三国中最大的单项变化。分解（INFERENCE，机制可复现）：(i) v3 把 SG 化工行（35.27 TWh，几乎全是裂解炉燃料：炼厂气 2,424 kt、燃料油 174 kt）按 EU27 权重拆分，HVC 只占 29 %，"氨"份额 10.85 TWh 在 2050 年按 DFX F2 直接丢弃；显式化后 HVC 2019 年 24.83 TWh（2,069 GWh 电从"其他"扣，"其他" −2.41 TWh）；(ii) 2050 年用 PyPSA-Eur HVC 6.10 MWh/t，是 2019 年能源用途强度 3.27 MWh/t 的 1.87 倍；(iii) 产品增长按 GDP 规则 1.455，而 SG 工业 ATS 倍数只有 1.166。若 2050 年仍用 3.27 MWh/t，`T_v2` 为 90.52 TWh（+16.3）。推荐：方法与 ID、TH 统一（S2 口径），但 2050 年 HVC 强度口径请用户在三国一起决定。
2. **SFI 乙烯名单疑似重复**：GEPDSGP0004"Petrochemical Corp of Singapore"（投产年不详）与 GEPDSGP0002"Singapore Essential Chemicals Complex"（GEM 把 PCS Ayer Merbau 对应到后者）各 1,100 kt。推荐主算去掉 GEPDSGP0004（4,161 kt），含它作敏感性（+12.63 TWh）。请用户用公司年报确认。
3. **化工行"炼厂气"超出供应 783 kt（10.76 TWh，2019）**：2019 年炼厂气产量 2,916 kt，炼厂自用 1,249 kt、自备电厂 27 kt，剩 1,641 kt，而化工行用了 2,424 kt。推断（INFERENCE）多出的部分是裂解炉尾气（来自同样记在非能源用途的石脑油 5,909 kt），即原料与燃料两处计入。在 v3 上移出这部分 `T_v2` −8.25 TWh；在主算上 −8.16 TWh。推荐 W08 按 IEA 返回流的惯例统一处理（需要 EMA 说明，`SG_MISSING_DATA.csv` 第 2 项）；本报告只量化，不进主算。
4. **"其他"桶的构成**：SG 工业的电（21.46 TWh）与天然气（13.87 TWh，GCV 55,477 TJ × 0.9）全部在 UNSD"未细分工业"，裕廊岛石化、电子、制药的用能都在里面。没有国家分行数据无法再拆。推荐：请用户提供 EMA《Singapore Energy Statistics》（第 1 项缺数），整合会话再决定是否继续拆分。
5. **玻璃（ETSAP 2020 年 99 kt）**：SG 没有非金属矿物行，从"其他"扣，第 7 步 +0.02 TWh、"其他" −0.19 TWh。量很小，推荐接受。
6. **GIPT 的"自备"标签**：GEM 把 Pulau Seraya、Keppel Merlimau、Sembcorp Sakra / Banyan 等公用热电厂也标为自备油气（7,164 MW），而 UNSD SG 自备装机只有 552 MW（埃克森美孚化工厂 444 MW 等）。这些厂的燃料都在转换项，不在工业。推荐不做处理，仅记录。
