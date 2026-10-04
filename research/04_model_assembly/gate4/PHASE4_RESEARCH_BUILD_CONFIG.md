# Gate4 Research配置

configs/research/baseline.yaml包含独立builder/allocation/DAG入口。network_export_enabled=true表示用户授权通过门禁后导出，不表示当前输入通过；solver_allowed=false。三层门分别校验数值资格、实际数组、实际网络静态验收。TargetReady或SpatialEvidence文字不能替代数组。

目标2050、气象2013、3h全年8760h。政策carbon.policy_enabled=false；预算表定义未变。外部化石市场在explicit unlimited_capacity_accepted时用零固定容量、可扩张且无数量上限的供应Generator，不用任意巨大有限容量；国家物理接口独立。既有有限接口仍保留原行为并通过回归。

原上游脚本、Gate2历史观察源、DEA/燃料价格和拓扑均未改动。未开启scenario switching、技术强制使用或求解。
