# Full-SC carrier inventory

“国内生产”指模型内转换/发电，不替没有来源的燃料Generator证明国内开采；“价格内生”指求解后的节点平衡影子价格，并非外部燃料输入价格内生预测。当前不求解或计算价格/福利。

| Carrier | 国内生产/转换 | 外部供给 | 储存 | 跨境物理通道：首版 | 价格/供给边界 | 排放 | 首版状态 |
|---|---|---|---|---|---|---|---|
| Electricity | 既有候选风光/水/常规发电、合格H2回电 | 不新增未接受的外部电力贸易 | 既有电池/抽蓄等候选 | AC/DC为唯一核心干预 | 供给/转换成本外生；节点价内生 | 原Power政策范围＋报告一次 | EXPLICIT |
| Heat | 仅可靠显式服务/合法转换辅助热用已有技术供给 | 无新增热进口 | 仅合格节点既有热储存选项 | 不建立跨国热网 | 技术成本外生；有Bus时价格内生 | 直接燃烧按用途报告；供电排放仍Power | EXPLICIT |
| H2 | Electrolysis及接受的既有SMR/SMR CC等 | 外部H2/出口新业务首版不启用 | 既有节点H2 tank；地下储氢无数据不自动开 | 国家间OFF；首版管道默认不建 | 固定技术/燃料价；H2 Bus价格内生 | SMR/捕集用途追踪；电解发电留Power | EXPLICIT |
| Natural gas | 已有biogas upgrading/methanation/helmeth仅作合格供给候选 | 既有外生commodity供应候选 | 既有当地gas Store，费用/边界须接受 | 物理跨境gas连接与扩张均不建；不等于禁进口 | 源价/可用性外生；优化购入数量 | 燃烧/SMR按真实路径，不能燃料与大气双计 | EXTERNAL_SUPPLY |
| Oil / liquid fossil | 外部oil不是国内开采；FT可产共用液体供给 | 既有外生oil候选 | 当地oil Store | 无隐含共享Earth油池/新跨境油路 | fossil source price外生；oil节点价可内生 | 燃烧/原料碳/FT再排区别 | EXTERNAL_SUPPLY |
| Biomass / biogas | 既有power/heat/gas/industry转换 | 只保留明确接受的既有资源或commodity边界；不加免费进口 | 有限潜力Store或已声明无上限源，二者不混称 | 不设国家间运输；全球资源池须隔离 | 数量/来源/价格须显式；来源未知不称国内资源 | 沿接受的生物碳/捕集规则报告，不假设全为零 | FIXED |
| Coal / lignite（保留者） | 既有发电/合格转换；工业煤义务不能漏 | 既有外生燃料供应候选 | 当地fuel Store | 不设隐含跨国共享有限库存 | 不新增煤技术，只保留接受集合 | power燃烧与非电燃烧分视图 | EXTERNAL_SUPPLY |
| Synthetic hydrocarbons / FT | H2＋CO2＋AC→fuel；既有gas合成仅在接受集合内 | 不自动增加成品合成燃料进口 | 与实际当地oil/gas供给一致 | 无跨境燃料套利替代电网 | 成本由实际转换/供给决定，非固定零价 | 碳来源/利用/再排闭合 | EXPLICIT |
| CO2 physical captured/stored | 点源capture/DAC等已有合格路径 | 无跨国CO2进口 | 本国/本节点物理储存与封存 | 跨国OFF；不得共享物理CO2池 | CC/DAC/储存费用与资源约束显式 | 与atmosphere报告区分，利用不等于永久封存 | EXPLICIT |
| CO2 atmosphere / reporting | 汇总同一物理碳事件的报告视图 | 不适用 | 记账Store不解释成可交易实物仓库 | 可全局报告，但不得变成物理跨国供给通道 | 仅report无新增排放价；Policy单独受原cap | 见CARBON_SCOPE_FREEZE | REPORTING_ONLY |
| Ammonia | U有Haber-Bosch/裂解/储存能力 | 不自动添加进口 | 能力存在但首版不启用独立NH3系统 | OFF | 无接受需求/价格不建新业务 | 原化工能耗及碳账仍保留 | DEFERRED |
| Methanol | 本轮固定源码未发现专用路径 | 不添加新进口 | 不添加 | OFF | 不发明价格/技术数据 | 不添加未经来源支持的排放路径 | DEFERRED |

## 当前配置与首版设计不相同

当前ASEAN H2 network=false；default gas network=false且标NOT USED；oil/gas/coal空间化true，lignite=false，biomass_transport=false，CO2 network=false，ammonia.enable=true。只读取这些key不足以证明首版已实现。

U `define_spatial:1006–1111`在biomass_transport=false时返回Earth solid biomass，在co2_network=false时返回单个co2 stored（location Earth）。oil/gas/coal/lignite/NH3的非空间分支也可返回Earth池。**共同物理Bus或Store本身就是可共享资源/能流的通道，不需要显式跨境Link。** 第一版必须把物理生产、消费和库存限制在单一国家（最好保留既有节点），使国家间电网成为唯一改变的能流通道。

U `add_carrier_buses:270–315`为fuel添加可扩张供给Generator与循环Store，按costs fuel收费；没有由此给出供应原产国或可追溯开采上限。biomass `add_biomass`有无限Generator或有限潜力Store两分支；首版不把finite改成infinite、不把全球潜力复制给每国。全国分配/来源不明须由Phase4接受输入决定，并在两情景保持同一约束。

国家内部网络/储存候选在两情景相同，不要求优化结果相同。没有物理跨境通道仍可有共同Power碳预算；它是固定政策协调边界，不等于燃料跨国运输。

具体消费函数、网络/供给路径与默认值见 `evidence/CARRIER_NETWORK_REVIEW.md`；源码量化条件优先于框架描述。
