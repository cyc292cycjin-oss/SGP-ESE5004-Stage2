# Phase3C：载体、外部供给与跨境通路有界复核

状态：只读源码与已有网络证据；无下载、组装、求解、参数替换或模型修改。用户已冻结：**唯一核心干预为跨境AC/DC电力互联；H2/CO2/gas扩张/NH3/MeOH跨境关闭；两组外部供给完全一致。** 本文件提供可执行的Phase4检查要求，不开启新的研究阶段。

固定U=`a3616a68ee44592af6527ca9024a90f1956646ae`。`U/prepare_sector_network.py`、`U/_helpers.py`、`U/config.default.yaml`及`U/configs/config.asean.yaml`指保留在`../../transport/phase3b1/evidence/source/U/`的文件；新增只读冻结文件`U/add_export.py`、`U/solve_network.py`、`U/build_industry_demand.py`在本轮`evidence/source/U/scripts/`，身份见`EXTRA_SOURCE_MANIFEST.json`。P/U/V/R不互相替代。

## 1. 主要结论：网络开关与物理池不是一回事

**`network=false`不充分。** `define_spatial`把若干“网络关闭”情况实现成全区共同Bus，多个国家可在同一商品/碳池取用或注入，而无需显式跨境Link。尤其CO2与生物质，这不是假设性其他配置：ASEAN override明确`co2_network=false`、`biomass_transport=false`，对应共享池代码直接存在。

| 载体/池 | 冻结源码行为 | 关闭网络仍可能发生的通路 | 第一版目标 |
|---|---|---|---|
| CO2 stored | `define_spatial:1023–1032`：true为节点CO2；false为单一`co2 stored`、location Earth | 一国SMR-CC/DAC捕集，可由另一国FT利用/共同储存；不是纯报告账 | 物理CO2池/Store国家或节点隔离，禁止跨国取用；global atmosphere另作报告例外 |
| Solid biomass | `:1006–1015`：biomass_transport=false→`Earth solid biomass` | 全区库存可供应各国用途；工业需求还在`:1897–1898`被全区求和，丢掉国家用途身份 | 物理资源/库存国家或节点隔离；不把地区潜力冒充每国同额供应 |
| Oil | `:1042–1047`：spatial_oil=false→Earth oil；当前default true | 若切成共同油Bus，一国FT可无运输成本供另一国shipping/aviation | 节点/国家油池；进口边界与国内合成油流分开 |
| Natural gas | `:1055–1070`：spatial_gas=false→Earth gas/biogas；当前default true | 一国Sabatier/biogas产出进入共同池可供另一国SMR/发电 | 节点/国家gas池；外部进口不得成为国内互换中转站 |
| Coal / lignite | `:1078–1098`：spatial=false→Earth池；default coal=true、lignite=false | 共同商品供应/库存没有国内产地归属，可能被误报为国家开采/贸易 | 国家/节点供给和库存；共同价格不等于共用物理池 |
| NH3 | `:1104–1111`：spatial_ammonia=false→Earth NH3；default true | A国Haber-Bosch→Earth NH3→B国cracker→H2，绕开H2管网关闭 | 第一版独立NH3按冻结决定defer/保持化工账；绝不开放共同NH3池或跨国网络 |

上述共享池会消除地理输送约束，或允许区域资源重新分配，但本轮**不声称已有优化实际使用某条通路**。已有网络计数仅证明结构：Phase3B1 `NETWORK_TRANSPORT_EVIDENCE.json`中tutorial pre-strip有1个co2 stored、1个biomass Bus、1个lignite Bus；oil/gas/H2/NH3各48个。作者final2025/2050也各有1个co2 stored/biomass/lignite池，oil/gas/H2各98个；不能把作者power裁剪网络自动当Research Full-SC。

全局`co2 atmosphere`是排放报告与环境记账，不是点源捕集CO2的免费运输网络。允许全局报告账不等于允许全局**stored CO2**商品池；原区域Power政策预算也可保持共同约束，不要求复制成国家额度。

## 2. 11类carrier inventory：能力、供给语义与第一版状态

以下是源码能力与本轮边界的映射，未确认数值仍不成为正式输入。状态词采用用户允许集合；有组件不等于已接受需求、产能或来源。

| Carrier | 国内产生/转换 | 外部供给含义 | 储存及网络 | 成本/价格与排放 | 第一版表示/Phase4动作 |
|---|---|---|---|---|---|
| Electricity | 继承电力Generator/水电与燃烧Link；H2 Fuel Cell/turbine等现有转换可用性按已接受集合 | 本段构造器没有独立“所有电力外部进口”开关；跨境电网不是商品Generator | AC Lines/DC Links；电池、PHS等国内集合两组一致；低压Link本地 | 技术成本和燃料成本进objective；发电排放进入Power政策与FullSystem报告 | EXPLICIT；仅跨境AC/DC是核心干预，国内设施不删除 |
| Heat | HP、resistive、boilers、CHP、solar thermal等按证据显式；Buildings未闭合用途留direct账户 | 未见通用外部热商品Generator | 本地heat Bus/水罐及充放热Link，无本函数构造跨国heat grid | 转换资本/运行成本与COP/效率；燃料排放报告，供电排放仍在Power | EMBEDDED或已接受服务EXPLICIT；不自动加ASEAN DH/存量 |
| Hydrogen | 节点电解、SMR/SMR CC默认生产；更多技术只是可选能力 | 默认函数无H2进口商品Generator；export模块是出口，不是进口证据 | 本地H2 tank；UHS另开且需场址；pipeline可选而第一版跨境OFF | 生产/储罐成本；用电内生；SMR上游排放不能按终端无碳省略 | EXPLICIT国内/节点供给；接受的工业/FT等需求；禁止跨境与共享中转 |
| Natural gas | Sabatier、helmeth、biogas upgrading可输入gas池；国内加工不证明国内天然气开采 | `add_carrier_buses`普通可扩张gas Generator按燃料边际价供给，无矿井/进口码头来源区分 | cyclic gas Store；gas.network注释NOT USED；独立节点gas池 | 固定输入fuel price；SMR/燃烧Link碳流；不是内生世界气价 | EXTERNAL_SUPPLY + 已接受转换EXPLICIT；跨境gas优化OFF；两组同来源/上限/价格 |
| Oil / liquid fossil fuels | FT可供同一oil Bus，不能称所有油均化石或均国内开采 | 普通oil Generator按fuel price供给，无独立油田/炼厂/进口量身份 | cyclic oil Store；未见独立oil pipeline builder | 外部供应价格固定参数；终端燃烧报告；合成碳循环需闭合 | EXTERNAL_SUPPLY；节点/国家池，保留直接与bunker固定终端义务 |
| Biomass / biogas | 升级、发电/热、工业等转换；不从Generator名字推断产地 | 无限潜力用Generator；有限潜力用初始库存Store；现有ASEAN solid biomass360TWh为地区技术潜力配置，非每国观测或已批准进口 | biomass_transport=false共同资源池；true才节点化且自动构造运输Link | fuel marginal cost或Store放出成本；生物碳取/放及capture按实际链报告，非自动生命周期零排放 | FIXED资源/EXTERNAL_SUPPLY候选必须标来源；国家/节点物理库存隔离，不复制地区总量 |
| Coal / lignite if retained | 保留电力/工业燃烧；没有证明国内矿业过程 | 普通商品Generator，仅说明供给边界，不证明国内开采/真实进口 | cyclic fuel Store；coal默认节点、lignite默认Earth | fuel price固定；燃烧CO2经Link或专用报告事件 | EXTERNAL_SUPPLY/FIXED已接受需求；与gas/oil同一供给镜像要求 |
| Synthetic hydrocarbons / FT fuel | 节点H2+CO2+AC→共同oil carrier；Sabatier/helmeth另为gas | 当前未见独立“进口synthetic fuel”Generator；不能把oil供应自动标绿色燃料 | 借用本地oil储存/供应账，无独立FT跨国网络 | FT容量/效率与最小负荷成本，H2和AC用电内生；CO2利用与燃烧回排 | EXPLICIT SUPPLY OPTION；禁止Earth oil/CO2池绕国；不新增固定H2义务重复同一FT服务 |
| CO2 | 过程/燃烧排放、SMR-CC/点源capture、DAC；不是能源商品产量 | 未见通用外购CO2源；不能免费填补FT碳输入 | atmosphere报告Store与physical stored CO2分开；pipeline第一版跨境OFF | capture/DAC/storage成本；Power政策与FullSystem报告不同视图；储存限额另有全区约束 | REPORTING_ONLY大气；已接受国内capture/storage EXPLICIT；物理池隔离为SYSTEM_LEVEL_BLOCKER |
| Ammonia | Haber-Bosch消耗H2+AC；cracker回H2；工业NH3 Load | 当前函数未建普通NH3进口Generator；若以后外购需价格/碳/可得性证据，不能自动新增 | 本地NH3 tank，spatial=false会共同池；未见显式NH3管网函数 | HB/cracker/storage成本；upstream SMR/电力排放不可省；终端carrier0不是全链零碳 | DEFERRED独立新基准用途/跨境；原化工电/气账须保留，见第6节 |
| Methanol | 冻结sector constructor中未发现生产/终端需求路径 | 未找到已启用进口来源，不能凭可能性造price/Load | 未见Store/network实现 | 无足够来源，不构造参数 | DEFERRED；不新增技术、进口或跨国网络 |

定位：fuel supply `prepare_sector_network.py:271–316`；FT`:344–380`；H2`:384–803`；heat`:2624–2948`，储热`:2770–2824`；biomass`:1140–1274`；CO2`:1408–1542`；gas synthesis`:1631–1680`；oil fallback`:1829–1850`；NH3`:2146–2235`；distribution`:3431–3449`。不同来源/价口径须用已接受成本台账，不在此更新DEA或燃料价。

## 3. 网络入口与有效关闭条件

### H2

- `sector.hydrogen.network`控制`:875–908`。true时可重用gas路线或沿电网greenfield；新/重用Link均extendable、可双向（`:807–872`）。这些函数**没有自动按国家过滤**。default true，ASEAN override `config.asean.yaml:210–211` false。
- 本地电解/SMR、tank不依赖pipeline开关。第一版可保持这些供需组件，跨国H2 pipeline必须无有效容量/扩张，不只检查配置文本。
- 若将来确需保留国内H2管线，须从同一冻结候选集按端点国家过滤；不能因关闭跨境电网而重新生成不同的国内H2拓扑。当前第一版不要求开启国内管线。

### Gas

- `config.default.yaml:734–745`：spatial_gas=true；network=false且注释`NOT USED`；GGIT/IGGIELGN是路线来源。`Snakefile:1377–1396`准备gas路线，`:1499–1507`将其作为**H2 network**输入，不等于已建优化gas传输网。
- 冻结`prepare_sector_network.py`未出现gas pipeline建设函数；不可因此跳过继承网络/后续脚本的最终组件检查。第一版gas import为相同外部供给边界，不能擅自删掉燃料供应变成自给问题。

### CO2

- `co2_network=true`既把stored池节点化，也在`:1486–1542`调用`create_network_topology`构造CO2 pipeline；false仅去掉显式管道并合并池。**现有单一开关不能同时表达“本地CO2池 + 无跨国CO2运输”**。
- `_helpers.create_network_topology:1523–1579`复制电力Lines/DC Links并按端点合并，没有国家筛选。简单先删跨境电网再重建CO2拓扑会把非电网络也随干预改变，违反“只差跨境电力”。Phase4须独立建立同一非电候选集并实施国家隔离/国界过滤。
- `solve_network.py:939–954`还对所有co2 stored Store最后时刻总量加区域封存上限，来源`sector.co2_sequestration_potential`（default200Mt Europe，`config.default:995–998`）。因此不能仅看单Store的`e_nom_max=inf`就说完全没有碳储存限额。物理池国家隔离不自动把原区域资源预算复制到每国；限额与来源必须显式登记，两组完全相同。本轮不更改该值。

### NH3 / methanol / biomass

- NH3开关是`sector.ammonia.enable`与`spatial_ammonia`；不存在本次源码发现的显式NH3跨国network switch。Earth NH3经HB/cracker可绕开H2管道；物理池也需检查。
- Methanol未发现相应构造能力，不以“network=false”虚构已经存在的模块。
- biomass_transport同时控制空间池与运输Link（`:1006–1015,1276–1348`），国内外运输无自动分离。Phase4需使资源池节点/国家化但禁止新增自由跨境生物质交换；不能靠关运输开关保留Earth池。地区360TWh不能整额复制给11国；任何国家分配/外部供给数量仍是输入决定，不能编造。

## 4. 外部供给边界与价格必须分开

`add_carrier_buses:297–315`只创建carrier、Bus、cyclic Store和`p_nom_extendable=True`的商品Generator，`marginal_cost=costs.at[carrier,'fuel']`。没有国家开采曲线、进口港口、原产国或进口价格分解；默认供给也没有在此设置有限`p_nom_max`。所以：

- 可将其**定义为第一版外部商品供应边界**并明确来源抽象，但不能追溯宣称上游已经真实区分了国内开采与进口。
- “固定外部供给”通常指固定供给规则/价格/上限，而不是固定每小时采购量；Generator dispatch可以内生。两组采购数量与结果可变化，不要求相同。
- 固定fuel marginal price是objective输入；`buses_t.marginal_price`是供需平衡约束的内生影子价。二者含义不同，前者不是研究计算的国家市场价，后者也不直接等于welfare/市场收入。未运行模型就没有新nodal price结果。
- 同样的gas/oil fuel price可以分别赋给11国本地进口源，**无需连接成Earth商品Bus**。同价不等于物理跨国可转运。
- 外部边界应只允许从已命名外部来源进入本国商品池；本国FT/gas/H2产出不可反向回流到“外部供应池”后再进入另一国，形成隐藏转运。进口cap/可得性/碳因子/成本/时间剖面和任何共同资源预算，两组必须完全同值同范围。
- 用户允许的H2衍生燃料外购是候选边界，不是授权本轮新增无价格/碳来源的进口Generator；首版保持已存在并接受的外部供给。

### H2 export共享池的限定结论

`U/add_export.py:82–100`创建Earth位置H2 export Bus和本地H2→export Links；`:107–129`可建共享出口Store；`:134–154`是负号Generator收入或固定出口Load。名为`endogenous_price`的参数被直接乘−1作为marginal_cost，是**外生出口销售价、内生出口量**，不是优化产生世界氢价。

该构造没有显式设置负向Link下限；不能仅因有共享出口Bus就断言存在A国→B国回流。Phase4需核对最终Link方向/上下限及出口Store是否有返回国内的通路。ASEAN YAML有export.enable=false、h2export=[0]（`:191–193`），但Snakefile `add_export:1535–1564`及脚本主程序`:217–232`仍可创建零量出口结构；已有tutorial pre-strip确有1个H2 export Bus/Load。这说明“开关名看起来关闭”仍需核对有效组件。第一版不引入额外出口研究或H2共享网络；零量结构须按合同审查，而不是拿它证明已发生氢贸易。

## 5. 国家标签、内部流与核心电力干预

`prepare_sector_network.py:3906–3907`给已有Bus填location；新增carrier Bus多只有location、无country。`_helpers.sanitize_locations:2430–2448`仅用location映射补空country。location=`Earth`或悬空引用不会自动得到有效国家，不能把空值当“国内相同国家”。

最小country contract：

1. 所有物理电力、热、H2、gas、oil、biomass、coal/lignite、NH3、stored CO2母线/Store都有明确country或可验证的宿主node映射。唯一允许的全局记账例外是明示的atmosphere/报告对象；外部供应来源另有明确`EXTERNAL`身份与单向边界。
2. 不只看Link名字或`bus0`/`bus1`。多端Link的bus2/3/4可能是电力、heat或物理CO2输入；FT、SMR-CC、HB/CHP等应逐个**物理端口**核对宿主国家。atmosphere报告端不当成跨境管道；stored CO2端不能按报告例外放行。
3. 国内Link/Line：所有物理端点country相同。跨境电力候选：经接受拓扑标记的AC/DC电力联接，端点country不同；不能对所有不同country的Link一刀切，误删本地转换或把报告端当输送。B2B/转换设施应按其在AC/DC通道中的实际角色处理，不能只靠carrier字符串漏掉有效跨境电通路。
4. Disconnected只禁用已识别的跨境AC/DC通道，并防止容量扩张重新打开；国内线路、转换设备、发电、储能候选、成本和约束保持相同。不能按国家拆出11个独立绝对碳预算，也不能顺带去掉外部燃料源。
5. 两组网络差分须有白名单：只允许跨境电力有效容量/可用性/允许扩张差异及其必要拓扑表示变化；非电物理池、线路、库存、供给与资源限制不得因场景而改变。只是把两组开关设相同不足以发现各自重建过程带来的漂移。

## 6. NH3 deferred必须与工业需求生成一致

补充源码核实：本轮冻结`U/build_industry_demand.py:294–344`说明只有`ammonia_enable=true`才从chemical/petrochemical的gas与electricity中扣除按NH3生产估算的输入，并建立ammonia能量输出。false跳过`:331–344`扣减；`:299`把新ammonia列设0表示不显式拆NH3，**不是化工原需求为0**。

因此第一版不显式NH3时，可以在非custom原始生成链保留原工业电/气账户；但必须同时关掉需求拆分和`prepare_sector_network.py:3976–3977`组件添加，并从未扣减源链生成或核对输入。若只关闭HB/NH3组件而复用之前已扣减的nodal CSV，会丢失原工业电/气。custom行业输入分支`:70–100`不执行这一拆分段，必须检查其历史是否已扣减，不能以当前开关自动认定恢复。

这仅证明**NH3这处扣减条件**；不证明整张工业账已经完整。`build_industry_demand.py:365–371`另有将non-fuel等列归入other的过程；其保持/嵌入按Industry专项边界对账。Phase4守卫应核对国家×carrier在defer前后包含原能耗一次，不能移除产业需求来满足“defer技术”。

## 7. Phase4最小guard清单

| ID | 必须验证的条件 | 防止的具体问题 |
|---|---|---|
| CN-01 | 每个物理Bus/Store有国家/节点身份；共享Earth燃料与stored CO2池不得服务多个国家 | 无显式管道的隐含跨国交换/资源重分配 |
| CN-02 | 非电Link全物理端口同国；跨境H2/gas/CO2/NH3/MeOH输送没有有效通路/扩张 | 只检查network=false或carrier名称导致漏网 |
| CN-03 | 外部供应分别接入本国、无国内产出回流再转运；同价但不共用物理库存 | FT/合成gas绕过电力断开实验 |
| CN-04 | 地区资源总量不复制，国家配额/外供上限/储存规则两组完全相同 | 11次360TWh或11次区域CO2封存额度等重复资源 |
| CN-05 | 非电国内候选拓扑独立冻结；禁止从各场景删边后的电网重新生成不同非电网络 | 干预同时改变H2/CO2/biomass国内网络 |
| CN-06 | AC/DC跨境白名单准确；同国电线保持；有效扩张不可恢复已禁用跨境通路 | Disconnected顺带删国内网或被优化重新接通 |
| CN-07 | 物理carbon pool国家化，global atmosphere仅报告；Power/FullSystem双账与信用守恒 | 免费跨国CO2供FT、政策范围碰撞与信用重复 |
| CN-08 | NH3需求生成/组件开关/缓存版本一致，化工电/气完整保留一次 | defer独立NH3后误扣工业能耗 |
| CN-09 | 供应Generator参数与nodal price分别登记，国内生产/进口来源标签可追溯 | 把抽象供给量误报国内开采或真实贸易/福利 |

这些是Phase4组装前后的有界工程检查，不要求本轮组装、找11国完整商品物流或运行正式求解。用户已冻结载体/跨境架构，仍待数值输入决定与工程实现的项目进入Phase4，不再开启Phase3D。
