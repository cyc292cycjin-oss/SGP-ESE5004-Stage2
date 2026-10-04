# 输配损耗、自用电与统计边界

**现有代码不足以把AEO发电目标、住宅/服务业终端电量和网络损耗视为同一边界。** 本轮确认了实现位置；没有证据宣布正式模型已经发生一个确定数额的双重损耗。

## 来源中的损耗

| 来源 | 可直接确认 | 不能据此断言 |
|---|---|---|
| AEO8 PDF49/印刷47 | BAS发电满足需求，own-use/losses占比保持最新数据 | C.5发电与C.2终端差额全是输配损耗；或已有每国每年的可分离loss表 |
| Ember现行方法v1.6 | Demand以生产+净进口构造；gross目标有国家例外 | DemandCast指定历史导出的所有国家都同样定义 |
| MY NEB2016 PDF105–106 | final use为交付最终用户；gross在发电机端，net扣auxiliary；losses & own use合并外部损耗和设施自用 | 合并量可以全部放到配电Link；热力转换效率可以替代电网损耗 |
| MY NEB2019 Table29 PDF72–73 | 电力列发电转换产出15377、loss/own use−1311、统计差异−277、secondary13789、进口3、出口−146、final13647，单位ktoe | 统计差异是物理损耗，或可以造一个Load强制闭合 |

NEB2019公开平衡数15377−1311−277=13789；13789+3−146=13646，与打印final13647差1ktoe，保留原表舍入提示。表16的gross178492GWh与consumption158603GWh之间差19889GWh也不是单独的T&D观测。Table29分别列主发电171672和自备6821GWh，合计178493，与Table16差1GWh，同样保留而不修改。

## 固定代码中的损耗

1. `prepare_sector_network.add_electricity_distribution_grid`创建配电Link，`efficiency=1`。`efficiency_static=0.97`乘在AC负荷上，S未同样处理；之后增长调整可能重新改变这部分总量。它不等价于一个输送1MWh需要1/0.97MWh输入的物理Link。
2. 冻结U的`solve_network.py:1170–1209`未传`transmission_losses`；本地PyPSA0.30.3的优化入口默认`transmission_losses=0`。据此当前调用路径没有启用AC Line的分段线性损耗。线路阻抗存在本身不能证明优化损耗启用。该API身份记录是本地环境观察，不追认论文当时所有环境。
3. `add_lossy_bidirectional_link_constraints:1038–1088`只使成对Link扩容一致，并不自行创造损耗。`set_length_based_efficiency`的冻结调用点在`add_extra_components.py:387–390`，用于H2 pipeline；不能从帮助函数名字推定电力配电或DC损耗已设置。Link实际效率须按carrier另查，不能把AC结论泛化成全系统无损耗。
4. 热泵、阻热、储能、电解等转换效率是各自Link/Store的物理关系，不是上游统计T&D/auxiliary的替代值。

证据：复用Phase3A5 `DISTRIBUTION_CALLSITE_SEARCH.txt`，新增 `LOSS_CODE_IDENTITY.json`、固定U的`solve_network.py`/`prepare_network.py`/`_helpers.py`快照及已安装优化器源码。只导入接口读取签名，未运行求解；导入时PROJ资源诊断不影响已成功记录的签名，也不被作为环境全面就绪证明。

## 候选会计约定（尚未批准）

若A*选final-meter，R/S/历史h应在同一电表边界；上游输配与发电自用不得再次塞进这个终端量。可显式表示的网络/转换损耗应由其组件物理关系产生。源数据包含而当前模型省略的部分，需要另行批准“显式表示、外生独立账户、或明确省略”的边界方案，不能擅设统一补差系数。

若A*选distribution-input或高压bus，必须保存到终端电表的可审计映射：同地区、年、网络层级的自用/损耗与贸易口径。R/S和h同时转换到该边界；不能在bus总量直接减一组未经转换的meter热量。对已预加某段损耗的负荷，该段不得再重复在网络建模。

最简余额只是有条件的会计示意：gross + net imports = final use + auxiliary + grid losses + conversion/storage净消耗 + statistical difference。实际项必须由来源定义互斥划分，不能把这个式子当作填数模板。

本轮损耗判定：**双计风险存在；确定量未估计；当前0.97不是已接受的科学损耗桥。** 未改loss factor或优化参数。
