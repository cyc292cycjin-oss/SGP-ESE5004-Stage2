# Gate4限定来源范围决定执行

本轮新增DecisionReference：`GATE4-20261006-BOUNDED-SOURCE-SCOPE`。批准依据为用户本轮A/B决定；这是统计范围解释，不是实测零、2050预测或追溯性批准。原始文件未修改。

## BN已报告煤炭转换范围

方法`ASSEMBLY_V1_BN_REPORTED_COAL_TRANSFORMATION_SCOPE`。冻结源中Brown coal与Lignite在进口、供给、转换、电力/CHP/热转换、自备电厂转换各层级均341.064千吨。两种商品名称对应父子范围，不相加；转换总项和转换子项是同一流量的层级，不能再加。消费叶节点和FEC没有被恢复，仍为null。

执行结果仅为：这条已报告流量保留转换身份，不再为其创建额外终端煤炭Load或固定电厂燃料义务。未来发电组件按其实际能源输入消耗燃料；本次没有新增/删除电厂。未报告其他煤种或其他终端用途保持`UNKNOWN_OUTSIDE_COVERAGE`，不得称全国煤炭最终用途为实测零。

## TL已报告天然气平衡范围

方法`ASSEMBLY_V1_TL_REPORTED_GAS_BALANCE_SCOPE`。冻结原行：总产量245171.17188TJ；回注60209.403TJ；燃烧放空1650.5883TJ；净产量183311.18058TJ，与出口同量；总能源供给原报告0。总产量−回注−燃烧放空=净产量；燃烧行是燃烧放空子项，不重复扣减；出口不是另一项终端负荷。完整已恢复交易集合没有正终端用途或反向供给。

`REPORTED_ZERO`只用于源中明确为0的TES。缺FEC不变成0；本限定范围不额外构造最终用气Load。上游生产/出口、回注、燃烧放空保留独立原RowID，不声称上游排放为0。2050国家独立天然气供给接口及未来使用资格不变。

## 实际匹配和保护

实际源匹配得到7项新非数值范围解释，未将数量硬编码为验收目标：

- `BN:2050:Agriculture:AgricultureFinalEnergy:coal`
- `BN:2050:Buildings:ResidentialFuel:coal`
- `BN:2050:Buildings:ServicesFuel:coal`
- `BN:2050:Industry:IndustryFinalEnergy:coal`
- `TL:2050:Buildings:ResidentialFuel:gas`
- `TL:2050:Buildings:ServicesFuel:gas`
- `TL:2050:Transport:RoadResidualFuel:gas`

原TL工业天然气的既有Phase3C表示规则保持不动，没有重复计为本轮闭合。当前原来源组合15项、待决物理目标33项，其中另有18个掺混影响目标。

机器身份分开记录：`OBSERVED_QUANTITY`（原非零流量）、`REPORTED_ZERO`（原明确0）、`SOURCE_SCOPE_NO_ADDITIONAL_FINAL_LOAD`（本轮非数值解释）、`UNKNOWN_OUTSIDE_COVERAGE`（未覆盖范围）。Registry中范围项Value/RawValue/BaseValueMWh均null，RequiredPhysical=false、Posting=false，原SourceQualified=false不伪造为数值合格。Required=true保留所有权记录。没有创建零Load。广义coal不等于其他未报告商品已被纳入；当前解释的原料、来源hash和允许交易集合受严格保护，若有新增其他煤种/终端正值/版本变化则拒绝旧解释，重新核验。

来源链见`research_inputs/assembly_v1/sources/BOUNDED_SOURCE_SCOPE_APPLICATION.json`与`BOUNDED_SOURCE_SCOPE_DECISIONS.json`：冻结源hash→原行身份/单位→层级核验→范围决定→当前目标。核验代码拒绝其他国家/燃料/年份/国际bunker及未知正终端用途。

## 本轮新原件及其限度

已取得[UN2019 Energy Balances原件](https://unstats.un.org/unsd/energystats/pubs/balance/documents/2019balance.pdf)，SHA256 `978dd77c11d0eaf606ada3275fb7f6e029d048b4b5743fb924113c1791d6c034`，本地`evidence/source_scope/UN_2019_balance_official.pdf`，384页。BN PDF80/印刷51支持煤炭转换范围；TL PDF343/印刷314的天然气净生产与出口164980TJ按NCV报出，与冻结GCV数值乘既有0.9系数后164980.062522TJ在整TJ显示精度内相容。未将新版年鉴数值替换冻结父账，未再次转换。

KH天然气PDF86/印刷57，LA天然气PDF212/印刷183，TL煤炭PDF343/印刷314均为`..`。四国同页国际海运bunker也是`..`。PDF25/印刷xxiv明确该符号同时表示不可用或不适用，不能区分、更不能当零。完整燃料列和bunker行已取得；数值/范围歧义尚未关闭。精确请求现为原问卷/脚注/交付原表的澄清，而非重找已经缓存的父项或UN PDF。
