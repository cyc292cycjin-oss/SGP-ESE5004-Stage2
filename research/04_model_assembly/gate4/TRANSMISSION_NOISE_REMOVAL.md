# 连接扰动移除与风光显式费用

按本轮用户选择A，13条DC/B2B的marginal_cost已实际改为0。修改前每项精确匹配冻结run的noisy_costs：0.01+0.002×(RandomState(174)随机项−0.5)，使用原reference.links行序。12条双向连接原来按有符号Link-p计费；合成PyPSA0.30.3代数模型现已验证+f、−f及端口互换均不产生可变输送费用，未调用solver。

方法ASSEMBLY_V1_REMOVE_INHERITED_TRANSMISSION_NOISE，DecisionReference=GATE4-20261006-CANONICAL-SELECTED-CLOSURE#A。线路/DC资本费已由builder按2050来源成本重建，无需再次扣扰动。真实网络回读逐项核对资本费用、容量/上限/扩展标志、端口、效率、p_min/p_max，以及全部AC线路和合法系统约束均保留。未清零其他VOM，未采用绝对流量收费或新随机正则。

选择B：solar0.01、onwind/offwind0.015 EUR2020/MWh，共340个已适用组件保留。方法ASSEMBLY_V1_EXPLICIT_CONFIG_VARIABLE_COST，是新接受的显式模型假设，不冒充实测VOM。屋顶光伏等原不适用项未被强加费用。1780条价格记录的所有数值与前轮一致，来源路径表示由绝对改相对的变化有单独hash记录，不是二次平减。100个FT Link的既有VOM接线保留。

方法提交：b4b416663a5881b636484f86b5d803eb661382a1。费用资格由machine-readable variable_cost_method及component_price_qualification记录，不依靠Markdown标签放行。
