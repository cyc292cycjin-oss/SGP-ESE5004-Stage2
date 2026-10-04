# Industry Gate2

固定 final-energy core，暂无合格 service substitution 数值。工业 direct electricity 只归 A*；原 cache industry electricity 另列 REFERENCE_ONLY，不产生第二个 Load。未知归属保留父账，不伪造工业服务。

基年 source：`base_industry_totals_2030.csv`，实际是 **2019** country/carrier×13 industries、NH3 扣除之前的表。SHA256 `c62e8edab8451f93a4273f9214e6259306ea7e01a6ba9c85e7b7db48978aa404`。44 个 country/carrier 原行固定在来源切片；按 carrier 汇总，不消费带 DEFAULT CAGR 或 NH3 扣除的未来节点文件。数值为 FROZEN_UPSTREAM，单位 MWh/year；原始热值、非能源原料边界仍须接受。

正煤候选覆盖 ID, KH, LA, MM, MY, PH, SG, TH, VN；都保留能源 MWh 与 owner，同时登记 `MISSING_ENERGY_OBLIGATION`。这是源码中 `add_industry` 将 coal 用于 CO2 而无相应能源 Load 的缺口；本轮未修复 carrier/network。不能把它说成已解决，不能拿 tCO2 替代 MWh。油/气/biomass 也按原始 carrier 保留。

H2/heat 不凭空创建：没有 accepted H2 final obligation 或 qualified heat-service 来源的行只保留 pending 接口、不 posting。没有把 heat 改名直接视为低温服务、没有模型化全部工业为 useful service；NH3 deferred 时原化工父能耗保留。

TL 工业载体缺失不补零；其 A* 有 2019 原始父账，未知工业电归属留在父账。工业燃料父账也缺时明确承认覆盖未闭合，不因 11 国形式统一补数。

`build_industry_demand.py:109–138` 仍能定位 upstream 未来增长：DEFAULT 国家/单元填充后 `(1+g)^(y-base_year)`。Research builder 不调用它；2030/40/50 为 `PENDING_FUTURE_GROWTH`，不默认 g=0。验证对各个正源 carrier 汇总独立核对，不把缓存零当成已报告零。
