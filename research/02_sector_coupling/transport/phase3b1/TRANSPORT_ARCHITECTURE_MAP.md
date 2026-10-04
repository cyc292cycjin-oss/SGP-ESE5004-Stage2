# Transport architecture：先构造，再裁剪

**当前框架具备陆运电力/油/H₂、铁路电力/油、航运油/H₂及航空油需求构造器；现有作者最终网络只保留EV和电铁路交通终端。** Full-SC Research 尚未建立，不能用作者电力案例代替验证。

本轮固定 P=`5bacad702ccfed17ad19ab510fa710651e966f2c`，U=`a3616a68ee44592af6527ca9024a90f1956646ae`；V=`50a73d8f531132c5459174a55cac412d5f684462`；R仍为U。`evidence/MODEL_IDENTITY.json`核对四层。下文 `U/...:行`、`P/...:行` 指 `evidence/source/` 中按Git原字节保存的源码；来源URL及SHA见 `evidence/SOURCE_MANIFEST.json`。这些是直接代码证据，不是参数科学验收。

## 工作流

`UNSD登记工作簿 → cached commodity transactions → build_base_energy_totals → 2019 national TWh → prepare_energy_totals（growth/efficiency/share）→ future national TWh`

随后分流：

| 路径 | 时间/空间处理 | 网络构造 | carrier与组件 |
|---|---|---|---|
| Land | 人口份额、气温、德国BASt周曲线、车辆表 → transport/availability/DSM/nodal四表 | add_land_transport | Li ion Bus；EV Load；固定BEV/V2G Link与EV Store；按外生份额增加oil/H₂ Load |
| Rail | prepare_heat_data同时输出人口加权nodal_energy_totals；年量/8760 | add_rail_transport | 固定electricity/oil Load，无线路/车辆服务网络 |
| Shipping | 国家domestic+international；WPI港口类别权重和节点映射；平坦燃料需求 | add_shipping | oil/H₂ Load；可选液化Bus/Link；oil supply Generator/Store |
| Aviation | 国家domestic+international；OurAirports机场类别权重和节点映射；平坦燃料需求 | add_aviation | kerosene-labelled Load，连接共同oil Bus |

规则入口：`U/Snakefile:1301–1332,1402–1413,1449,1474–1495,1583–1613,1670–1748`。调用顺序见 `U/scripts/prepare_sector_network.py:3949–4040`：燃料供给/转换 → 各部门 → Residential/Services → 配电接线 → 时间聚合 → 碳预算。交通构造并非工作流终点。

`prepare_sector_network → add_export → final_asean_adjustment → existing/brownfield → saved/solved network`。U的 `final_adjustment.only_elec_network=true`；`strip_network`对组件实际使用全局白名单（`U/scripts/final_asean_adjustment.py:18–80,124–143,419–421`）。它删除运输油/H₂终端与EV Store，却保留EV Load、charger/V2G、rail electricity。因此“V2G=true”不等于最终有跨时EV储能。

## 四种状态不混用

| 证据范围 | 可确认内容 | 不可推出 |
|---|---|---|
| Framework U | 上述构造器、供给转换及开关存在 | 输入有效、所有技术参与求解 |
| U ASEAN配置 | land/rail/shipping/aviation=true；最后only_elec=true；DEC道路份额外生 | 新U full-SC final network已经建成；本轮没有运行它 |
| Tutorial已保存2030前后网络 | land=false；裁剪前有rail、shipping、aviation；final只保留rail electricity | 道路链验证成功或完整交通模型通过 |
| 作者P两个保存样本 | 2025 Baseline与2050 DEC各98 EV Load、98 rail-electric Load、98 charger、98 V2G；EV Store=0 | 所有44个作者结果均已检查；下载结果是独立复现 |
| Future Research | A*概念及Buildings最低边界已冻结；Transport候选待人审 | 任何本轮分类已经成为生产配置 |

作者样本EV电池侧加权Load为14.928884/68.846262 TWh，rail为5.111434/12.857958 TWh。两行跨年、跨scenario，不能作因果比较。EV Load不是网侧充电量。教程2030为六天代表时段、48个快照，权重年化8760；其rail为6.147076 TWh，这是保存模型的加权量，不是全年观测。证据：`NETWORK_TRANSPORT_EVIDENCE.json`及`NETWORK_SUMMARY.json`。

## 成本和物理边界

上游电力、制氢、FT、燃料供给、储存及网络投资/运行费用可进energy-system objective。当前道路汽车、固定charger与EV Store不是内生购买车队的完整资本成本模型；航空/船舶投资不在这些需求函数中。未来国家结果应称能源系统成本与供能投资，不能直接称全社会交通成本或福利。各比较侧必须使用相同外生份额、需求、资产表示及成本范围。

`TRANSPORT_MODE_INVENTORY.csv`分别给构造支持、U配置、U最终预测和已观测文件状态；`UNKNOWN`不被强行改为不存在。物理及数据缺口见重要性登记，不修源码。
