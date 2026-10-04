# 生物质有限资源隔离

已验证：`biomass_transport=false` 仍可能生成 Earth solid biomass 共享库存；它给多国访问同一资源的能力。上游原候选 solid biomass=360 TWh、biogas=0.5 TWh，不是人工接受的 ASEAN 国家资源表，也不能逐国复制。

新接口 `allocate_finite_resource` 只接受明确来源、国家/节点分配、总量与成本。分配和必须回到唯一总量，否则报错。各节点有限 Store 的 e_nom/e_initial 固定，不能自行扩张；`Store-p >= 0` 保证资源只可消耗。PyPSA 0.30.3 的 Store 没有 p_min_pu/p_max_pu，方向依赖显式 Linopy hook，不能把无效属性当约束。

国家间资源没有共享 Bus/Store，也没有贸易 Link。全局价格信息可以共享，物理库存不可以。实际国家分配仍 PENDING，合成测试 30+70=100 只是守恒 fixture，绝不是研究输入。

历史审计把 110 条 biomass 多国访问记录标为 SHARED_RESOURCE_ACCESS_NOT_A_TO_B_INJECTION，不伪称直接双向流。biogas 的 location=Earth 也不能单凭字符串判定共享，审计使用真实 bus country/location 映射。

碳口径：biogas upgrading 的负大气端口在原源码中存在；biomass EOP 部分原 CO2 端口被注释。没有明确因子不能把缺失视为0，也不能默加生物碳中和。模型内 uptake/stack 与生命周期排放分别陈述。
