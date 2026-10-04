# Shipping与Aviation：不能因缺数据直接关闭

**两者有明确燃料需求构造、ASEAN开关开启，但作者最终电力案例将其终端删除。** Future Research中二者均建议暂标`SYSTEM_RELEVANT_PENDING`；不是已决定关闭或已完成Full-SC接线。

## 需求与供给

| 问题 | Shipping | Aviation |
|---|---|---|
| 原始需求 | UNSD domestic navigation、international marine bunkers，国家TWh final fuel | UNSD domestic/international aviation，仅Kerosene-type Jet Fuel匹配，国家TWh |
| 最终义务 | 国内+国际相加，平坦oil/H₂ Load | 国内+国际相加，平坦kerosene-labelled Load接oil Bus |
| 技术选择 | H₂ share外生，剩余oil；ASEAN DEC H₂ share全0 | 无飞机端燃料竞争，无直接航空H₂路径 |
| 空间 | WPI港口类别1/2/3权重→节点 | OurAirports中/大机场1/3权重→节点 |
| 燃料供应 | oil供应Generator/Store，H₂生产、可选液化；FT可供共同oil | oil供应与FT共享；不是单独验证的synthetic kerosene产品系统 |
| NH₃/methanol | 未发现直接交通终端；工业NH₃/裂解制H₂不等于氨船 | 未发现直接终端 |

源码：`U/scripts/build_base_energy_totals.py:262–292`；`prepare_sector_network.py:1545–1628,1683–1850`；`prepare_ports.py:21–31,120–137`；`prepare_airports.py:19–77,125–137`。

`international_bunkers=false`是**排放开关，不是燃料需求开关**。国际燃料仍进入上述Load；源码并未证明这些bunker已包含在哪个外部国家final-energy总量中。未来需明确报告国供油、国内义务和国际bunker的研究责任，不能未经选择直接并入国家A*或其他direct fuel。

需求从2019 UNSD经DEFAULT CAGR预测，非AEO交通预测。缺失会被fillna(0)。Shipping另以外生H₂ share加权效率趋势，再以`shipping_average_efficiency/fuel_cell_efficiency`转换H₂需求；0.4参数注释为2011油船推进效率，配置文档却称H₂船效率。年份、定义及热值口径尚未获接受。

## 实际文件暴露的系统问题

教程2030裁剪前有48 shipping oil Load，其中39个p_set为NaN；48 H₂ shipping Load中1个NaN、47个0。**47个结构零不代表历史H₂调查，更不能用有限油节点小计当国家总量。** H₂ share为0也不能消除对齐造成的NaN。oil在港口按节点groupby后再country.map，可能因国家字符串聚合导致缺值；这是源码支持的原因线索，未把它当作所有NaN的已证明根因。

同期航空48个Load均finite，加权421.489329 TWh；这是既有模型预测/分配值，不是原始航空统计通过验收。终态均被删除。因此教程能成功求解不能验证被删除的航运量。

见`NETWORK_SUMMARY.json`与原值记录；港口风险定位`prepare_sector_network.py:1743–1746,1790–1796`。国家和节点需求守恒及NaN处理必须在后续采用前关闭，不靠删部门绕过。

## 对互联问题的意义（推断）

如果保留这些燃料义务并允许FT/制氢供给，可能改变电解、合成、风光、储能与港口/机场附近网络投资；影响大小和方向需未来经批准的模型确认。固定燃料需求不意味着其生产用电必须平坦，燃料库存可以分离生产与消费时间。无需船型/飞机型数据库作为本轮前置。

候选为FIXED聚合燃料义务+EXPLICIT供给转换，保留`SYSTEM_RELEVANT_PENDING`直至总量/增长、bunker责任、节点守恒、父燃料排重与carbon范围确认。不添加新燃料技术，不自动设氢化比例，不做敏感性实验。
