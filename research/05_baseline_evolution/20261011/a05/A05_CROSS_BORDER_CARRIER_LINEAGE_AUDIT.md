# A-05 跨境能源载体与网络结构谱系审计

日期：2026-10-11。状态：**A05_COMPLETE_WITH_EXPLICIT_UNKNOWNS**。本轮仅代码取证、既有NetCDF静态表读取和轻量元数据计算；没有读取完整CSC、构模、求解、AutoDL操作或更改科学输入。G6-05继续PAUSED_BY_USER。

## 1. 结论与证据边界

1. **VERIFIED**：冻结Full-SC有19条跨国AC Line及5条跨国DC Link。完整资产端点、国家、区域节点、方向、容量及成本见 `evidence/A05_CROSS_BORDER_ASSET_INVENTORY.json` 的 `FROZEN_FULL_SC_2050.cross_border_assets`。全网为105条AC、10条DC、3条B2B；其中12条DC/B2B允许双向流，另1条DC单向，不能把“12条双向连接”误作全部DC/B2B数量。
2. **VERIFIED**：没有实际跨境H2、gas、CO₂、biomass、NH3或methanol运输资产。排除电力端口和纯大气报告Bus后，非电载体图784个连通分量均不跨国家，未发现共享燃料池绕过显式边界。该图检查只确认国家隔离，不证明供需可行。
3. **VERIFIED**：仍有400个独立外部化石燃料供给Generator，每个地理节点各有coal/gas/lignite/oil，允许非负、无有限容量上限的内生供给，按明确燃料价计费。没有国际燃料运输Link不意味着没有进口供给假设。这些组件也不提供真实进口国、港口、航线、运力或地缘供给证明。
4. **VERIFIED**：上游论文两份结果均保留全域solid biomass、lignite和co2 stored物理池；`biomass_transport=false`、`co2_network=false`没有消除共同池。当前国家/节点隔离是实质性的边界修改。固定生物质Q是终端消费核算派生量，不是独立资源潜力或国际贸易余量。
5. **VERIFIED**：100个本地H2 Bus均有电解、SMR/SMR CC、tank、fuel cell、FT；没有直接H2 Load、外部H2 Generator、H2管网、NH3或methanol链。100/100节点存在FT→oil→最终oil Load端口路径，也可经fuel cell回电；因此不能说氢气没有用途。FT须同时取得本地捕集CO₂和电力；未证明未来进口H2一定可行、被使用或有经济收益。
6. **VERIFIED / SCIENTIFIC_BOUNDARY_RISK**：当前电力输入集合与作者2025网络相同（118个Line/DC/B2B资产ID及端口一致），但不等于作者2050网络。后者另有7条AC、8条DC跨境资产记录。选择2025源文件的代码已确认，逐项排除2050未来项目的科学审批依据**UNKNOWN**。这影响候选可达性，不能推定造成旧库存违规或INF_OR_UNBD。

## 2. 四个版本必须分开

| 对象 | 身份 | 本轮如何使用 |
|---|---|---|
| 作者论文真实运行 | 两份2025/2050结果嵌入commit `5bacad702ccfed17ad19ab510fa710651e966f2c`；发布参考 `99159edb7298b847fea517bf05c3f388493501c9` | 读取输入组件/端口与有效配置，不采用优化后容量或调度作当前输入 |
| 上游SC参考 | `a3616a68ee44592af6527ca9024a90f1956646ae` | 证明通用功能存在，不冒称论文实际启用 |
| 冻结Full-SC | 科学源码 `b9be7d0ab788a4151346c098d2e657c7e94a22da`；NetCDF构模清单记录 `4b5611dc2dbc3ebcc2ae69b3782b338d2a18b6ce` | 2050需求、2920×3h；3443 Bus/3358 Link/1737 Load/1104 Store；不是新方案A网络 |
| 方案A派生源配方 | 实施交付 `8883de6fb3e15767c632ac92f535e8a423e90b69`，独立PR #4；Manifest SHA `a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720` | 复用静态验收：仅180Q的720个同步字段，拓扑未改；未组装新完整NetCDF/LP，更未求解 |

冻结NetCDF SHA：`238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d`。作者2025：`06152be56ee41f64bfdca42fd24aeaf363ab61f931fec7b5e4bc12f6d6456ecb`；作者2050：`3ac28875630cffbf8b7f3b1e80dbc7eb293d36e7f62efd1578beec457d54d745`。本轮复用已核大文件SHA及来源清单，记录当前大小，不冒称重新做了三份全文件哈希或LP回读。新轻量证据及指定源码blob实际重新核SHA。

所有以下代码位置按固定commit引用；精确片段、blob SHA及SHA256见 `evidence/A05_SOURCE_AND_DECISION_EVIDENCE.json`。两份有效配置安全摘录见 `A05_SAFE_EFFECTIVE_CONFIG.json`，没有复制服务密钥字段。

## 3. 电力：真实边界和限制

| 国家对 | 跨境AC记录数 | AC输入s_nom合计（MVA） | 跨境DC记录数 | DC输入p_nom合计（MW） |
|---|---:|---:|---:|---:|
| ID–MY | 1 | 230 | 0 | 0 |
| KH–VN | 1 | 200 | 0 | 0 |
| KH–LA | 1 | 300 | 0 | 0 |
| KH–TH | 1 | 250 | 0 | 0 |
| LA–TH | 9 | 约955 | 0 | 0 |
| LA–VN | 4 | 1 | 0 | 0 |
| MY–TH | 1 | 380 | 5 | 2265.6 |
| MY–SG | 1 | 525 | 0 | 0 |

这是静态输入容量汇总，不是同时可传输能力、最优投资或真实工程认证。AC采用`s_max_pu=0.7`且须服从电网约束；19条跨境Line均extendable，s_nom_min等于原s_nom，单资产max为默认∞。5条跨境DC均extendable、p_nom_min为原p_nom、max∞、efficiency=1；4条`250878579-*`双向，`Khlong Ngae – Gurun`方向为TH21 0→MY_Peninsular22 0，p_min_pu=0。3条B2B均在国内、固定2000MW，未被国家边界条件禁用。98条electricity distribution grid是国内连接，不是跨境。

全网唯一GlobalConstraint是`lv_limit`：AC/DC transmission_volume_expansion_limit，`≤353746853.52332264 MW·km`。它是共同输电容量-长度预算，不是碳约束，也不等于每条线路没有扩建限制。`p_nom=0`但extendable=true且max∞的候选不能判作禁用。

来源路径：`build_research_assets.py:49–84`从作者2025参考网络复制Line/DC/B2B输入并重定2050成本；`selected_closure.py`和已接受的`GATE4-20261006-CANONICAL-SELECTED-CLOSURE`清除继承的输电随机成本噪声。118个共同资产端点及已比较的容量、方向、阻抗等静态输入相同，资本成本118项不同、13条Link边际成本变为0；`efficiency3`缺失/default差发生于不存在bus3的资产，无有效端口改变。精确字段差在`A05_ELECTRICITY_INPUT_DIFF.json`。

跨境AC资本成本范围9698.870471864697–33557.96108877541 EUR2020/(MW·年)（PyPSA的Line名义量按MVA字段保存）；5条跨境DC均21323.01852311139 EUR2020/(MW·年)，输入边际成本0。完整逐项成本、长度、年份及端点见库存清单。这里记录NetCDF输入成本，**不是**SCOPE_V3扰动后LP逐系数成本；本轮不重扫目标数组，也不修改资本微扰。旧build_year或并列走廊数据如需现实工程资格核定，须另有原项目台账，不能凭名字判断重复。

作者2050比当前多的跨境记录包括MY–PH、SG–VN、KH–SG、ID–SG、BN–MY、LA–MM、MM–TH等；完整列表可由两份inventory逐ID比较。示例`Kudat – Palawan`的真实端点是MY_Sabah4 0→PH_Luzon5 0，不能用名称“Palawan”改写实际区域。当前BN/MM/PH/TL没有跨国电力边；同国异岛连接不能误归跨境。

## 4. 非电载体逐类核查

| 载体 | 上游能力 / 作者实际结果 | 当前Full-SC实际状态与机制 | 边界影响 |
|---|---|---|---|
| H2 | 论文源码prepare_sector_network.py:645–744与SC:807–912有新建/改造管道函数；有效hydrogen.network=false，两份结果0条H2 pipeline；gas_network_repurposing=true只是未进入分支的候选参数 | cross_border_h2=false；本地100组制氢/储氢/消费，没有国内节点间或跨国H2运输，也没有外部H2供给 | 非本轮新删除一张已启用论文氢网；当前增加国家/端口隔离，不能把未来跨境H2说成既有功能已跑通 |
| 天然气 | 论文gas.spatial_gas=true、network=false；每份98个本地gas供给。通用库有天然气管线数据预处理/棕地转换引用，但已查构造中gas数据主要用于H2改造；没有证据认定已运行跨国CH4运输 | 100独立gas Generator、当地gas消费/发电/SMR；不生成gas管道；国家共享价格而不共享物理池 | 有外部商品供给，未建边境运力；全球原产地与运输瓶颈UNKNOWN |
| CO₂ | co2_network=false却有`co2 stored`共同Bus/Store，393个接口跨11国；SC:1486–1542另支持实际CO₂管道 | 本地captured Bus仅接受本地捕集并供本地FT；无CO₂运输、无捕集CO₂ Store、无地质封存Store、无DAC资产。共用Atmosphere是报告汇，不是FT供料池 | 删除跨国捕集料共享是科学边界收紧；本地捕集/消费须即时闭合。报告账户国家空白不构成物理贸易漏洞 |
| 生物质 / 生物燃料 | biomass_transport=false→Earth solid biomass共同360TWh初始库存；可供多国EOP，不是385组固定最终Load。SC:1276–1358有运输Link生成逻辑 | 原公共Store和EOP不并存保留；807本地固定商品Store→807独占meter→385最终义务Bus；无贸易/能源转换替代路径 | Q派生于终端需求，不能视作可自由贸易资源潜力；禁跨境不是已证明导致10.24TWh超用的原因 |
| 石油 / 合成液体燃料 | 论文oil.spatial_oil=true，98本地供给；FT继承上游转换机制，不等于跨国oil管网 | 100独立外部oil供给＋100本地FT→819个最终oil Load；不生成跨境合成燃料运输 | 国内FT油和外部油共享本地oil Bus；终端燃料替代仅限该同载体链，非任意服务替代 |
| 煤 / 褐煤 | 论文coal本地98个；lignite.spatial_lignite=false，共同Earth lignite供给连接多国 | coal/lignite各100个本地供给；保留已接受煤/褐煤机组和163煤最终Load；无两类跨境运输 | 褐煤从共同物理池改独立供给；未知物理进口潜力不能由价格表证明 |
| 氨 | SC:2146–2235有Haber-Bosch、裂解、Load和Store，配置可共池或本地；论文5bac已查范围无氨构造/资产 | ammonia=deferred；0 NH3 Bus/Load/转换/运输 | 不能把上游氨转换支持等同已建设跨境氨链，未来需单独科学决定 |
| 甲醇 | 论文未见；SC唯一已查命中为电厂匹配燃料分类，未发现甲醇能流/运输构造证据 | methanol=deferred；0相关Bus/资产 | 候选燃料标签不构成供给/消费路径；完整其他未审分支能力UNKNOWN |
| 电池、其他终端载体 | 电池充放电为国内储能；论文EV/V2G等旧电需求表示不等于跨境运输 | battery/home battery各98 Store及配套Link，H2 tank100；7种生物质商品仅为固定核算账户 | 不把充放电、排放计量或国内转换Link混作运输；需求替换细节复用A04，不重审 |

冻结配置 `baseline.yaml:24–44,90–105` 和 `carrier_architecture.py:25–55,93–122`明确这不是仅把管网容量置0：构造器只接本国非电端口，外部供给只能是单输出非负Generator；`build_research_network.py:53–68`还检查非电多跳连通分量。`local_blueprint`中存在的Sabatier/helmeth等候选不等于实际配方：当前没有Sabatier、helmeth、NH3或methanol Link。

400个外部供给的静态价格分别为coal9.5542、gas24.568、lignite3.2985、oil52.9111 EUR2020/MWh；capital_cost=0，p_nom=0，p_nom_min=0，extendable=true，p_nom_max=∞，p_min/max_pu=0/1。价格共用成本来源SHA `bbcc639010a6775255730278eaa6e21ba56867d0610d3a011adc3eb60d0065f5`。并无年度有限化石资源Q、来源国或固定进口量约束；“外部市场无有限上限”不等于无成本或免费能源。807未知生物质商品成本的NULL科学语义不由本轮补价。

## 5. 氢气的生产—储存—终端关系

实际每节点：electricity→H2效率0.6994；gas→H2的SMR0.76、SMR CC0.69；H2→electricity燃料电池0.5；H2 tank为非负、可扩建、年度cyclic，初始库存0（cyclic时需按Store数学语义理解，不能当外生免费初始供给）。100组候选均容量初始0、可扩建、max∞、单向转换；成本/寿命逐载体表见inventory。

FT正向一单位H2输入的端口为oil +0.799、captured CO₂ −0.20542290000000002、电力 −0.005275056518462698；后两项是共同输入，不能当输出收益。当前SMR CC向本地捕集池提供+0.17820000000000003 tCO₂/input-MWh。没有跨国CO₂供料池或捕集库存缓冲，故不能仅沿H2→oil箭头宣称FT可运行。100节点的FT输出Bus都连到现有oil最终Load，fuel cell也都连回本地AC Bus：**有真实消费/转换接口，但没有直接终端H2需求**。

未来若讨论H2跨境，只能先依据用户研究问题决定管道/船运/进口端、共同输入和固定终端消费边界。现有H2可回电或制油，不可自动替代固定biomass、coal、gas义务；也没有NH3/methanol中介链。原上游add_export.py:65–151是H2节点→export Bus→出口Load，方向是出口，不能反用来证明已存在外部H2进口。两份论文有效h2export=0；当前新增进口与出口义务均未激活。

## 6. 修改理由、可行域与因果限制

**可证实历史理由**：Phase3 closeout条目G–J明确要求首版只比较电力跨境干预，H2/gas/CO₂及隐含物理池关闭，已有外部化石商品保留；`c6f4ebf...`实现国家归属、`1402948...`落实共享价格但独立供给；`96202b9...`组装器和`18eb582...`实际资产配方完成。完整commit及源SHA在证据JSON。候选范围与fixed-carrier Mode A有关，不是为本轮让模型更易求解而关闭。

**已证实的可行域变化**：从区域生物质公共潜力/可选发电转为本地固定终端账户；从共同lignite/CO₂池转为本地供给/捕集消费；只从2025集合构造2050电力候选；Sabatier等通用功能未进入接受路线。这些改变均可能约束跨国/跨载体调剂，不能称为纯数值变换。方案A仅修资源常数闭合，没有恢复这些路径。

**未证实因果**：已证明的旧微小年度D>Q矛盾仍属于源常数，旧候选377账户/111义务组、约10.24TWh超用不能因无贸易路径而直接归因；第二次INF_OR_UNBD也不是本轮能从静态拓扑解释的数值结论。未发现当前固定需求误连到已关闭H2/NH3/methanol端的直接证据；oil/gas/coal存在本地外部供给，biomass严格依赖自有Q。拓扑可达不证明年度/逐时能力或整体LP可行，扩大路径也不保证Gate6 PASS。

**明确未知项**：燃料原产国/海运港口/可用供应潜力、若干电力走廊记录的独立工程身份、未继承未来电力项目的逐项科学选择、缺失最终H2/NH3服务设计、全LP/调度可行性。没有新发现可直接宣称已经证实的模型实现bug；保留明确的科学边界风险，不无限追加本轮任务。

## 7. Integrated/Disconnected一致性与下一次用户判断

现有 `configs/research/integrated.yaml` 与 `disconnected.yaml`均为空对象，注释说明仅未来身份，电力干预延后；不能说已有两张正式可比网络或已执行断联。历史设计拟只改跨国AC/DC可用/扩建，国内网络及所有其他载体一致，当前Baseline实现了后者的共同边界，但尚未实施前者。

历史文档称Disconnected保留共同Power cap；**本冻结Baseline实际policy_enabled=false**，不得将历史条件性表述转成已生效碳上限。`lv_limit`仍为共同区域输电预算，即使未来切断跨境边，也不能不审共同约束就把成本结果说成11个独立国别优化之和。国别范围实际包含TL，经济比较口径必须明示。

用户后续需要判断的科学问题限定为：

1. 2050比较是否有意以2025电力候选集合为起点，或未来需单独审议作者2050额外项目；本轮不补线。
2. 是否继续保持固定终端燃料Mode A与独立外部化石市场边界，特别是固定生物质账户不作为独立资源潜力。
3. 若未来另行启动跨境H2研究，比较的是回电/FT替代还是新增直接H2服务；后者需要独立需求/技术审批。
4. 正式Integrated/Disconnected干预与共同约束的比较定义需独立批准；本轮不实现。

A-05结束。A-06及B—F未开始，无新的计算授权。独立A05 PR不合并、不混入方案A实施PR #4；Git发布和ZIP最终身份由交付清单记录。
