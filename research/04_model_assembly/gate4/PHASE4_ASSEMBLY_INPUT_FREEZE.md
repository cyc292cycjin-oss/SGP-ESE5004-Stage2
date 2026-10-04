# Assembly V1：部分冻结，目标年门禁未通过

**45 条 ASSEMBLY_V1_ACCEPTED，531 条 PENDING，共576条登记。** 接受状态严格区别于 HUMAN_ACCEPTED；原 Gate2 状态/文件不改。45条包含11个2019电力父账数值、4个2050电解参数、6个原Power年度限额、22个R/S表示控制、2个供给可用性控制；不是45个已就绪2050需求。

## 可冻结内容

2019 A* 来自现有 UNSD 原文件 `UNdata_Export_20250502_110820872.txt`，SHA256 `12c99b3c40927449d9a4d0402f255a8b84b24917ff58e54efd4ec43b2125fe6b`。精确 transaction=`Electricity - Final energy consumption`，million kWh ×1000=MWh。原始十进制转换与 Gate2 浮点文本差值均≤1e-6 MWh，差值单列，不做 residual correction。

| 国家 | 2019 A*（MWh/year） |
|---|---:|
| BN | 3906135.000 |
| ID | 258092000 |
| KH | 10191090.00 |
| LA | 6595540.00 |
| MM | 18681010.00 |
| MY | 158709264.000 |
| PH | 87118300.0 |
| SG | 51730200.0 |
| TH | 193175999.000 |
| TL | 384247.000 |
| VN | 207048888.888889000 |

这些是基年锚点。没有将2019值改名为2050，没有设定零增长，没有从A*减去所有UNSD sector rows；未证明互斥的子账户留在父账。未来 EV/电解/FT/HP 电量不能预载到 direct A*。AEO8 generation 继续不作为目标；这不是对实际网络已经验证的声明。

2050 电解参数沿用原 v0.13.2：efficiency=0.6994（LHV H2/electric input）、lifetime=25年、FOM=4%/年、investment=1000 EUR2020/kW_e。现有 pre_costs_2050 与已恢复官方 SHA `ec22a184…` 输出逐字节相同，未更新DEA。前三项已有旧sheet86链；投资为公开冻结 manual override 所载原情景假设，按本轮优先级3沿用，原 private communications 无独立实证核验作为限制保留，不能称为“私人来源已恢复”。未激活组件。

Power原限额 2025/2030/2035/2040/2045/2050=1000/820/640/460/280/100 MtCO2/year，baseline enable=false；预算年份不是需求预测来源。

地质库采用本轮明确允许的无储存资产 fallback，潜力数值仍 unknown，不创建无限储存；biomass无接受分配的资源暂不可用，不复制360 TWh，也不引入无上限进口。二者是可用性控制，不是观测到自然资源=0。未来正生物质义务仍必须保留；该供给限制可能使验证模型不可行，不能静默删除需求。无地质库会排除永久封存但不自动禁止有来源的本地CO2→FT原料回用。

## 2050 阻断与最低资料

现有通用增长/工业增长文件只有 DEFAULT、MA、NA、US（效率文件 DEFAULT、MA、US），无 ASEAN 专属行；Git 历史显示通用默认值，不提供所需的 ASEAN growth 依据。`prepare_energy_totals` 又有列对齐后 fillna(0)；旧未来缓存不能充当合格预测。`FUTURE_INDUSTRY_GROWTH_BLOCKER` 保留。

旧 DEC_2050 EV share=1 同时参与车种效率/车辆处理，未证明是本轮要求的最终能耗份额。不得仅改名为 s_E；R 和 s_E 必须联合定义，使 EV=R*s_E 与各残余燃料同一基准。原无量纲/里程混用道路链未启用。

2050需要的275个物理需求记录均未接受（11电力、88 Buildings、77 Transport、44 Industry、33 Agriculture、22国际bunker）；这是依赖账本计数，**不是要求用户分别找275份新资料**。需要的是一套相容的目标年 direct A*、道路最终能耗/份额、各主要部门增长/燃料义务；可采用已有可靠数据或明确来源的简约方法，不能由程序默认补值。空间/时序分配也尚未被物化，空 allocation_missing 仅因无 accepted 2050需求，绝不等于分配已通过。

煤/气/油价格原输出分别为9.5542、24.568、52.9111 EUR2020/MWh_th；source currency_year 仍保留2010/2015，不能再通胀。热值匹配、国家容量/年可用量尚未闭合，数值保留 PENDING。外部供给不等于跨国物理通道或能源自给。

TL无来源独立工业子账户不单列为阻断整个 ASEAN 的原因；保留A*与未知覆盖限制。当前主要阻断来自所有国家目标年父账和主要部门数值，不是要求完整TL工业微观调查。

## Buildings 国家×部门表示矩阵（冻结设计，实际网络未构建）

| Country | Residential | Services | Explicit heat |
|---|---|---|---|
| BN | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| ID | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| KH | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| LA | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| MM | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| MY | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| PH | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| SG | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| TH | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| TL | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |
| VN | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |

Cooling嵌入；Cooking仅核算；space/water heat未有合格服务量时保持嵌入；不造stock、uniform district heating或BDEW需求。R/S分开标识并不意味数据完整或有新增Load。农业油/biomass/煤、工业煤实际能源量、四类国内/国际船/航空义务均保留输入门禁，未以只有排放的Load替代燃料。
