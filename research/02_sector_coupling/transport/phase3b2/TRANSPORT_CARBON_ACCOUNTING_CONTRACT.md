# Carbon accounting contract — only, no policy patch

## 两个视图，不是两个可相加的总量

**PolicyCO2_Power**：保持作者电力案例范围，DEC 2025/2030/2035/2040/2045/2050区域绝对轨迹为1000/820/640/460/280/100 MtCO2/year。Baseline沿用原预算关闭语义。不向每国机械复制区域预算，不设计新政策。

**ReportingCO2_FullSystem**：实际建模系统的物理CO2报告，包含power与非电燃烧、供给、捕集/储存/再排；国内与国际bunker分列。不额外施加统一cap。此报告包含Policy对应的物理事件，不能将两个数再相加。未建模进口燃料生命周期排放标为范围外，不虚构CO2e。

| 碳流/对象 | 来源与去向 | Policy视图 | 全系统报告 |
|---|---|---|---|
| Road EV、embedded rail、FT、电解用电 | 供电端发电/既有供电转换链→大气 | 仍受Power cap | 同一发电事件一次，不另加电网因子排放 |
| Road分载体残余燃料 | 真实燃料→道路燃烧 | 直接交通燃烧不自动纳入 | 保留油/气/生物碳身份及来源，燃烧一次 |
| Rail embedded fuel | retained direct-fuel→rail燃烧 | 不自动纳入 | 父账报告包含rail一次，无独立Load也不能漏 |
| Domestic shipping / aviation | 国内固定fuel→燃烧 | 不自动纳入 | 各自domestic报告行 |
| International shipping / aviation | 独立bunker fuel→燃烧 | 不自动纳入 | 各自bunker报告行，不移成国内 |
| SMR/SMR CC共享H2 | 天然气→H2+排放/捕集 | 原power供给链份额保留；非电份额不可整批并入 | 完整实际排放/捕集一次 |
| FT carbon recycling | stored CO2→fuel→燃烧回排 | 供电排放保留；信用归属不可任意抵Power | 来源、使用、再排、永久封存分别守恒 |
| DAC/点源捕集/封存 | 大气或点源→储存/利用 | 原边界允许的可追溯信用 | 同一碳流不可重复减排 |

“交通相关”不等于全部report-only：**为EV、制氢和FT发电的排放仍在Power cap**。共享H2服务发电时原SMR链也不得整类剔除。共同燃料/CO2池须用守恒用途标签或等效线性账户追踪；具体共享来源/信用分摊要在Phase4科学复核，不能悄设固定比例。物理供给不因两种视图复制两套。

## 已核实的scope collision

U `prepare_sector_network.py:1426–1446`为共同co2 atmosphere Bus/非循环Store；road、shipping、aviation直接燃烧与SMR等汇入同一账。`add_co2_budget:3626–3662`调用`prepare_network.py:149–156`，按co2_emissions建全局约束，没有Power选择器。因此恢复Full-SC后直接给共同atmosphere绑定原cap会扩大范围：**SYSTEM_LEVEL_BLOCKER**。

U ASEAN `co2.budget.co2base_value`与consumer `base_value`键疑点另存，数值相同也不代表边界相同。必须复用前轮版本/有效值证据，不更改年度限额。关闭H2/CO2跨境网络不能隔离排放账。

另外，旧rail无直接燃烧回排，在oil carrier因子被置0后有遗漏结构；shipping/aviation的international_bunkers=false分支使用`I (Σq)(Σr)`，不能替代逐国`I Σ(qr)`。新分账应直接按国内/国际数量计算，避免旧比例分支。本轮不修这些正式约束/排放公式。

## Phase4最低验收（提出，不在本轮执行）

1. 每个物理碳事件有唯一ID、来源组件、载体/原始碳来源、目的用途、时间权重及tCO2单位；报告一次。
2. 固定同一电力调度，仅加非电直接燃烧时Power账不变、FullSystem增加对应量；新增用电诱发发电变化时Power账正常变化，不能视为污染。
3. 退化到paper电力边界时原预算表达式/数值/供电SMR与capture链等价；新增非电义务不偷偷改变其范围。
4. rail燃料和FT碳燃烧回排闭合；捕集转燃料不是永久封存；国内/国际分项和等于完整燃烧报告。
5. 共享SMR/H2/CO2流的归属总和等于同一实际流，不重复供给、不重复信用。

详细源码定位与有限依赖见[evidence/CARBON_FUEL_REVIEW.md](evidence/CARBON_FUEL_REVIEW.md)。此合同是表示决定和实施验收要求，**当前U未实现**。
