# Hydrogen与fuels首版冻结

## H2

生产允许已有、经过输入接受的节点电解及SMR/SMR CC等路线；不是只因成本表有技术名称就自动启用。当前default production_technologies为H2 Electrolysis、SMR、SMR CC（U config.default.yaml:787–790）；ASEAN关闭H2 network。首版不新增生产技术或国内资源假设。

消费仅有：被接受的工业H2义务、已有FT/合成燃料输入、既有被接受的H2回电技术。Road FCEV与直接shipping H2仍DEFERRED；这些模态为零组件/不构建，不额外生成同服务H2 Load。FT从Bus取氢已是需求，不能再预加等量氢终端义务。

储存采用已有节点H2 tank候选（容量与成本口径不改）；地下储氢无接受输入不自动启用。所有库存、制氢、用氢端口必须同国家、与节点映射相容。首版H2管道不建，**跨境H2 pipeline/network=OFF**，国内新增H2网也不由本轮要求启动。

不得用共同H2 pool/出口Bus绕过OFF。U add_export有独立出口机制，不等于进口：其端口方向及收益模式要核对，不能见“共享Bus”就断言能倒流。本首版保留无新增H2出口业务的研究边界，export需求/内生收益/附带公共储存不得形成未接受义务或套利。双情景均一致。

## Gas与液体燃料

**外部commodity供给与物理管网分开。** 既有gas/oil供应候选可以作为外生供给边界保留，优化的是购买/使用数量；输入价格、碳因素和可用性不由本轮决定。首版不建跨境gas管网，也不扩张它。冻结U的gas network=false/NOT USED不构成“网络不可避免必须保留”的证据。

既有gas→H2、H2/CO2→gas、H2/CO2/AC→FT fuel等只在同国合法供给链内活动。oil/gas生产与需求不能通过Earth池无成本跨国搬运。煤/褐煤若在既有集合中保留，按同样规则处理；不借保量新增发电技术。

## NH3/methanol

首版独立NH3与methanol系统及跨境设施 **DEFERRED/OFF**。U支持NH3不意味着首版必须启用。关闭NH3生成和消费须同步缓存/原化工电气燃料账，不得继续使用已扣除NH3 feedstock的旧工业需求。Methanol专用路径本轮未发现，不新增。外部H2衍生燃料仅列未来候选，不因用户举例“possibly”就自动加入首版。

## Carbon与辅助能源

为H2/FT供电的发电排放仍计Power policy。共享SMR供电与非电用途要守恒归属，不能全部豁免或全部扩入Power；完整物理排放进入报告一次。

捕集CO2、DAC、合成路径的辅助热/电有实际代价和合法可达端口。Buildings thermal服务嵌入并不允许给DAC免费热，也不允许为了DAC虚构Buildings终端热需求：可以在Phase4保留有成本的转换辅助热接口，但不制造额外最终服务。配置开关、需求缓存、网络组件与排放视图必须一致。
