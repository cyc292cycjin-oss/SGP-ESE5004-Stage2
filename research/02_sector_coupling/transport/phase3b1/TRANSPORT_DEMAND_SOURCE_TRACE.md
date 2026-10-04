# Transport demand来源：final energy，不是交通服务公里

**主要需求来自UNSD国家能源统计，经默认预测参数转成未来final-energy量；不来自AEO交通活动预测。** 车型、passenger-km、tonne-km、vehicle-km及occupancy/load factor没有在当前实际链中形成独立服务量。

## 端到端链

`Energy_Statistics_Database.xlsx链接 → 52个cached UNSD TXT（文件名20250502）→ 2019 ASEAN交易 → 单位换算 → energy_totals_base.csv → DEFAULT CAGR/份额 → energy_totals_<year>.csv → profile/人口/港口/机场 → Load或转换边界`。

直接缓存提取见`evidence/CACHED_DEMAND_EVIDENCE.json`：123条ASEAN2019交通关键词候选原行，含原文件路径/SHA、行号、单位、数量、脚注。其中含因燃料名称匹配而进入候选集的进口等非终端交易，不能将候选全量作为交通消费。107个非空base字段可按冻结的交易/commodity过滤及转换复算一致，14个字段为空。这只证明缓存与计算链一致，不证明统计完整、参数科学接受或作者运行采用同一输入。

| 模式 | 国家原交易/字段 | 转换及后续 | 当前主要缺口 |
|---|---|---|---|
| Road aggregate | road交易全燃料，total road及电/气/生物质/油子项 | TWh→增长/效率→含非电rail的陆运代理→时间曲线 | 没有客货服务拆分；燃油效率代理量纲不闭合 |
| Rail | diesel+biodiesel+electricity；electricity rail为子集 | TWh→DEFAULT增长/效率→人口份额→恒定MW | 覆盖/空值、land重叠、父电力扣除及油排放 |
| Shipping | domestic navigation / international marine bunkers分列 | TWh→油/H₂ share效率趋势→港口权重→恒定fuel MW | bunker责任、增长、节点NaN、效率定义 |
| Aviation | domestic aviation / international aviation bunkers，限kerosene-type jet fuel | TWh→DEFAULT增长→机场权重→恒定oil MW | 其他航空燃料覆盖、国际义务、增长及碳范围 |

源消费：`U/scripts/build_base_energy_totals.py:36–62,108–132,203–292,366–462`；`prepare_energy_totals.py:35–109,260–296`。百万kWh÷1000、TJ÷3600转TWh；千吨按`_helpers.get_conv_factors`；热值口径和燃料因子仍待科学确认。所有123条提取行有对应处理单位，没有借缺失数值补造服务量。

## 必须保留的缺失语义

- 11国road electricity=0，但原缓存没有这些国家的Electricity-road观测；这是空子集sum，并不能证明历史EV用电为零。
- rail electricity原行仅见ID/MY/PH/SG/TH。KH/MM的零也来自无电力子记录；BN/LA/TL/VN的rail字段原本为空。
- 14个空base字段：BN/LA/TL/VN两个rail字段共8格，BN/LA/TL两个navigation字段共6格。2030/2040/2050均被fillna(0)。
- road electricity/gas/biomass/oil四个子项在CAGR表缺列，列对齐后成为NaN再填零；未来表中这些零不表示燃料消失，因为total road另有公式。

这些问题影响历史转移和需求大小，应按账户处理，不要求为每种车辆重建统计。

## 预测、车辆与地理来源

所有11国均无国别growth/efficiency/fuel-share行，继承DEFAULT；DEFAULT与某些其他国家行相同不证明其地理来源是欧洲。分类为DEFAULT、校准来源UNKNOWN。DEC道路电动车份额是ASEAN config手工override，不能称优化器内生渗透率。

车辆表生产脚本优先WHO注册车辆，Wikipedia补充；2014World Bank运输排放占比被用作效率代理；下载失败可复制hard-coded表。当前tutorial资源目录未生成transport_data.csv（land=false），fallback小表存在并含11国，但没有逐行年份/来源。不能据此认定作者使用了该fallback。

BASt曲线为明确EUROPE_INHERITED。人口/温度和地理数据库是全球处理链。tutorial港口实际缓存来自2026-09-29用户导出的NGA WPI/GDB，记录明示tutorial engineering only，非paper输入身份。机场处理文件存在，原始OurAirports版本未恢复。原纸本模型输入manifest仍不完整；两份作者NC内嵌配置只固定输出身份。

新加坡2019缓存国际海运bunker为535.3418 TWh，国际航空bunker为103.2489 TWh；二者是单独交易，足以提示边界的系统影响通道，不能自动计入国家终端A*或归为国内运输。未计算其未来电力需求。

本轮无需广泛外搜：主要生成链、原缓存及已保存网络已足以达到边界审阅门槛。具体数值仍UNVERIFIED/PENDING；公开URL来自源码/既有来源登记，并非本轮在线刷新或版本升级。
