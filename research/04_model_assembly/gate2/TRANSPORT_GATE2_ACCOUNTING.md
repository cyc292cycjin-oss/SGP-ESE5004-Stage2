# Transport Gate2

Road aggregate EXPLICIT 的表示原则保持；能量来源和 electrification share 尚未接受，因此未来 EV/fuel 实例不生成。实现 `road_energy` 接口和反例测试：final-energy share、明确 R、明确 residual oil/gas/biomass vector；拒绝车辆占比、kWh/km 量纲、无接受标记或 fuel weights 不守恒。

基年 RoadParentFinalEnergy 缓存只作独立参考，不叠加一个额外总能量 Load。正 road gas/biomass/oil 逐 carrier 保留；缓存 road electricity=0 没有精确 raw road-electricity 观测支持，保留 missing。任何历史 EV 仍归 A*；没有真实 EV transfer。接受历史 subset 后，通用 parent-transfer 接口执行一次转移；其合成测试通过不等于已知 2019 EV 数值。

未来 EV 属于独立 final-electricity obligation，未来 direct A* 演变须明确排除这部分；没有 EV service-efficiency 代理或 passenger/freight 拆分。V2G/DSM 不实现。

Rail electricity EMBEDDED 在 A*，无独立 rail electricity Load。原 total rail 混合 diesel/biodiesel/electricity；不把 total rail−rounded electricity 猜成全 oil。Rail fuel 留在唯一、未量化的 TransportEmbeddedFuelParent（UNCLASSIFIED）；原总量作为 reference，父燃料和去向仍 blocker，不能称真实 rail fuel accounting 已闭合。

source→ledger 可核查缓存正值，真实 EV 路径、future R、residual carrier shares、fuel parent、节点与时序接受仍待关闭。Exactly-once 机制 PASS；真实 transport 数值闭合 PARTIAL。
