# 燃料外部供给与物理隔离

上游 `add_carrier_buses:272–317` 使用带 fuel marginal_cost 的供给 Generator、Bus、可扩张 Store。它表示外生供给接口，不能证明国内气田、现实进口来源或无限世界市场。

新接口为 gas/oil/coal/lignite 各国节点建立独立、单向 source Generator。共用价格标识只包含 price、unit、source hash/year、热值口径等元数据；国家容量及年度可用量独立保留。允许同价、不同国别供给上限，禁止把本国 FT 产油返送到共同市场再进入外国。

价格输入要求 EUR/MWh_fuel 与明确 HHV/LHV 等 basis；容量、年度上限必须显式给出，若无年上限须有明确接受标记。本轮真实参数均未据此批准。有限年度供给通过已建 Linopy 变量上的 `ResearchImportAnnual-*` 约束计入，必须调用 `install_fragment_constraints`；当前没有组装/求解 workflow 入口。

燃料成本只在源 Generator 计一次；转换 Link 承担自身转换成本与燃料消耗，不再加同份燃料源价。固定或可扩张供给/储存的实际数值必须后续接受，不能为消除不可行擅自放宽。

`combustion_accounting_interface` 是最终燃料计量接口：1 MWh_fuel 输入对应 1 MWh 最终燃料义务输出，另一个端口按已接受因子报告 CO2。它不推定有用能效率、不添加新服务技术、不创建 Load；工业煤的能流和排放来自同一 Link-p，不能只有 CO2 Load 而没有煤消费。

历史 Earth lignite 为共享供给/库存访问，需隔离；不是所有路径都代表 A 国向 B 国注入。当前 gas/oil spatial=true 已分节点，仍需用所有转换端口而非配置名称核验。Integrated/Disconnected 未来使用完全相同的这些输入；本轮 overlays 未变。
