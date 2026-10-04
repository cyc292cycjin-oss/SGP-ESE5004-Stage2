# H2 国家与节点归属

已验证：当前配置 `sector.hydrogen.network=false`；上游 `add_hydrogen` 支持电解、SMR/SMR CC、燃料电池、H2 储存和配置允许的 H2 turbine。能力、配置候选、已接受数值三者分开。

`local_blueprint` 为每个明确 country/node 创建独立 H2 Bus，转换端口只能连接本国节点；本轮不新增任何管线。候选方向进入可达图，但缺少人工接受的参数时 `to_pypsa_fragment` 拒绝物化。真实 Load 必须经过 Gate2，载体构造器直接拒绝 Load。

同国不同节点也没有隐式 H2 pooling。今后若需要国内 H2 网络，须明确节点与接受的物理资产；它不是本轮默认连接。NH3、methanol 与外部 H2 导入均 deferred；不会因旧配置中 ammonia=true 自动加入首版。跨国 H2/gas/CO2/NH3/MeOH 为 OFF。

历史 tutorial 的 H2 export bus 是单向汇集出口：14 条 export Link 的 p_min_pu=0、没有返送路径，不能把名称含 global 的节点直接称为跨国 H2 传送。真实出口义务尚未接受，首版不自动激活。

证据：`source/scripts/prepare_sector_network.py:add_hydrogen`、EFFECTIVE_CONFIG、TUTORIAL_COMPONENTS 与 `REFERENCE_GRAPH_AUDIT`。新模板的可达性已测试；历史 NetCDF 未修改，完整 Research 网络尚未建立。
