# 唯一核心干预：跨境AC/DC电力连接

## 冻结的对照

| 项目 | Integrated | Disconnected |
|---|---|---|
| ASEAN国家间AC/DC电力边 | 按接受的拓扑/容量/扩张规则启用 | 同一边集不能运行、不能扩张或重建 |
| 国内电网 | 同一拓扑、存量、候选与成本 | 完全相同的输入规则 |
| H2、gas、CO2、NH3、methanol跨国物理通道 | OFF | OFF |
| oil/biomass/coal等跨国隐含pool/Store/转换通路 | 不允许形成额外区域传输 | 相同规则 |
| 外部商品供给 | 同一外生price/availability/carbon/容量接口 | 相同；并非能源自给 |
| 需求、sector表示、技术/成本、天气、时空分辨率、储存、carbon | 同一接受清单 | 同一接受清单 |

“相同国内网络/技术集合”不要求最终国内投资、调度或容量结果相同；这些是可随电力互联变化的优化结果。不得同时切换燃料自给、关闭国内线路、换需求、改变碳预算或引入其他网络。

## 边的识别与禁用（Phase4实施规范，本轮未执行）

用接受的bus→country映射识别两端属于不同研究国家的电力边：AC Lines、承载AC/DC/B2B的Links，以及任何实际跨国电力等效组件。不能仅匹配名字或删所有Line；多岛国内电缆仍是国内边。Transformer跨国或国家标签不明作为异常需核对，不静默猜归属。

Disconnected必须使选定跨境边物理上无功率且无再扩张入口；可以移除相应边或通过受测的停用表示实现，但**仅把AC s_nom改0可能仍留下KVL/电纳耦合**，仅把Link p_nom设0也不能阻止p_nom_extendable重新扩张。实施须检查电气连通性、KVL和候选容量，保留审计用原边清单与输入成本。既有线路沉没资本不因删除组件凭空创造“福利”；成本比较沿相同年化/存量常数规则。

同一组政策需求/技术/国内候选作为base，项目override仅切换接受的跨境电力干预。建模后做白名单差异核对：除了该边的可用性/扩张入口和必要连通性派生结构，其余需求、输入参数、组件候选、资源与政策约束散列一致。实际调度/投资变量结果不作为输入散列比较对象。

## 网络开关之外的隐含通道

U network=false可能仍返回共享物理Bus：biomass_transport=false→Earth solid biomass；co2_network=false→co2 stored/location Earth；其他spatial=false分支有Earth fuel pool。工业process emissions还可能汇总到共同Bus再接不同地点capture。Phase4必须扫描**所有Link端口、共享Store及生产/消费可达路径**，不能只数pipeline名称。

允许全局大气报告账和固定区域Power预算；它们不是可运输commodity库存。物理captured CO2、碳原料与工业待捕集排放须国家/来源可追踪，不能借共同process pool在另一国家捕集/合成。国内CCS不构成跨国CO2管线许可。

## Disconnected仍是一个区域政策模型

原Power绝对预算为ASEAN共享约束，两组都保留。因此首版Disconnected宜在同一11国模型中关闭电力跨国边；它并不自动分解成11个独立求解问题。固定共同资源上限也可能造成非网络耦合。

首版可定义 `ΔC_SC = C_Disconnected,SC − C_Integrated,SC`，两者包含全部保留sector供给/转换/储存/网络成本。**不能未经预算/资源可分解性证明就写成Σ独立国家成本−区域成本**，更不能给每国复制区域1000→100 Mt上限。本轮不分配国家配额、不研究国家福利、不执行任何比较。

电力互联是唯一被改变的核心干预；共同碳政策产生的区域协调仍是双方相同背景。能耗保障/韧性维持既有约束或情景边界，不新增目标函数。
