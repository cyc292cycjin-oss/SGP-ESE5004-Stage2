# A-05 上游—冻结网络差异登记

证据等级：VERIFIED为实际文件/固定commit；DERIVATION为有假设的结构推导；RISK为已知路径上的潜在问题；UNKNOWN为缺少证据。精确源码片段和SHA见 `evidence/A05_SOURCE_AND_DECISION_EVIDENCE.json`；资产数来自静态NetCDF，不是配置猜测或优化输出。

固定源码简称：P=`5bacad702ccfed17ad19ab510fa710651e966f2c`（论文真实运行）；S=`a3616a68ee44592af6527ca9024a90f1956646ae`（通用SC）；F=`b9be7d0ab788a4151346c098d2e657c7e94a22da`（冻结科学源码）。当前NetCDF来源见主报告。

| 编号 / 科学影响 | 上游实际或功能 | 当前机制与代码 | 理由及证据等级 | 对可行域 / 风险的含义 |
|---|---|---|---|---|
| A05-01 电力拓扑继承 | 作者2025：105 Line+10 DC+3 B2B；19 AC/5 DC跨国 | F build_research_assets.py:49–84，从固定2025 SHA复制输入，不取p_nom_opt/s_nom_opt；118 ID/端口完全对应 | VERIFIED；避免混用已解容量是构造器明确约束 | 不是删掉所有电力跨境；单资产扩建仍允许且有共同lv_limit |
| A05-02 2050未来项目未继承 | 作者2050多7 AC/8 DC跨境记录；includes MY–PH/SG–VN等；不是15个必然独立走廊 | 当前没有这些ID；继承2025源文件而非运行上游myopic未来项目追加 | 机制VERIFIED；是否逐项科学批准排除UNKNOWN | 改变2050候选可达性；不证明需求因此不可行 |
| A05-03 输电成本来源 | 作者已解文件输入含原噪声/年份成本 | F selected_closure.py及GATE4-20261006决定；118资本项重定、13边际项归结构零 | VERIFIED，决策HUMAN_ACCEPTED；不修改现有成本 | 可影响投资最优解，不直接改变静态端口；SCOPE_V3另有已冻结成本微扰，本审计未重扫LP系数 |
| A05-04 氢运输关闭 | P prepare_sector_network.py:645–744、S:807–912支持双向管道；两份实际配置hydrogen.network=false，结果无管道 | F baseline.yaml:24–44和carrier_architecture.py:29–51、本地配方175–214，实际0管道 | VERIFIED；Phase3 G/J规定首版无跨境H2 | 延续论文未启用状态并强化无隐藏通道，不能声称删除了作者已经运行的氢网 |
| A05-05 本地氢用途 | 作者98组电解/SMR/SMRCC/FT/Sabatier与tank；实际未见fuel cell | 当前100组电解/SMR/SMRCC/FT/fuel cell与tank；Sabatier/helmeth不在实际配方 | VERIFIED；F build_research_assets.py:175–214，接受路线清单 | gas替代路径收窄；FT和回电仍有H2用途；未来进口不能任意替代其他固定燃料 |
| A05-06 化石供给国家隔离 | gas/oil/coal各98个本地供给；共同Earth lignite连接多国 | 4×100独立外部Generator；F carrier_architecture.py:93–122；只有共价元数据 | VERIFIED；`140294807bffe5cc172d5226ee0af3d4f548d180`明确独立可用性 | 无有限进口运力/原产国表示；不等于无国际进口，也不等于本国资源自给 |
| A05-07 天然气网络能力边界 | P/S有管线数据及棕地引用，gas.network=false；实际结果无gas pipeline | 当前cross_border_gas=false、0管道；保留当地gas源/消费/SMR | VERIFIED实际缺席；通用CH4运输生成范围未充分证明，不能由数据文件推启用 | 外部本地gas源使多数需求不依赖邻国管道；总体可行性仍未证明 |
| A05-08 CO₂共同池移除 | P/S define_spatial使network=false退化为共同co2 stored；论文393接口/11国 | 本地captured Bus + SMRCC/FT，多跳检查；无地质/捕集Store；大气纯报告 | VERIFIED；F build_research_network.py:53–68、assets175–214，Phase3 H | 本地共输入和即时CO₂守恒约束真实收紧；并非新增碳排放政策上限 |
| A05-09 生物质边界替换 | 论文Earth solid biomass 360TWh及EOP；S另支持运输、工业需求等 | 807账户/7商品→385独占义务组；F assets225–265，原pool/EOP不并存 | VERIFIED；复用A02/A03的Q需求派生决定 | 从可分配资源潜力转固定终端核算，是科学边界变化；不能把NULL来源或Q说成可交易国内潜力 |
| A05-10 氨/甲醇延后 | S有Haber-Bosch、裂解、NH3Store/Load，论文无；methanol只有匹配词，未证实运输代码 | baseline.yaml明确deferred；实际相关Bus/Link/Store/Load为0 | VERIFIED当前缺席；未审分支功能UNKNOWN | 没有错误地给固定H2/NH3终端断供的直接证据，因为相应Load亦不存在；不能声称全真实需求覆盖 |
| A05-11 进出口方向 | 上游add_export.py将H2送出口Bus并设Load；有效h2export=0 | 外部H2进口deferred，出口义务deferred；原化石供给独立保留 | VERIFIED；不能将出口脚本反用作进口证据 | 新增H2进口/出口会改变科学可行域，本轮不实施 |
| A05-12 场景控制未实施 | Phase3定义仅跨境电力差异；论文不是当前Full-SC两组实验 | integrated/disconnected配置仍{}；baseline保留电网、非电共同边界off | VERIFIED；F configs/research/*.yaml；check_research_carriers.py:27–30只是历史模板一致性检查 | 不能凭配置名声称已经做断联；未来需明确定义容量下界与共同lv_limit/政策比较 |
| A05-13 方案A不是新网络 | 旧冻结LP有精确源常数矛盾，旧证书永久保留 | PR #4静态源配方180Q×4字段；385/385 D≤Q′，Load及拓扑保持；未组装 | VERIFIED复用既有静态回执；recipe SHA `1b0ea897bc17d652a6ac5047935dc6af6c53536a51b197582b3567313d155e8e` | 本轮网络计数属于旧NetCDF；修常数不证明整体可行，也不恢复任何跨境载体 |

## 未继承的作者2050跨境记录

AC：`0` BN–MY、`29` ID–SG、`42` KH–LA、`65` LA–MM、`67` LA–VN、`7` ID–MY、`89` MM–TH。

DC：`250878579-2_0_upgraded` MY–TH；`Plentong - Woodlands` MY–SG；`Khlong Ngae – Gurun 2` MY–TH；`Telok Gong – Perawang` ID–MY；`Kudat – Palawan` MY–PH（实际PH_Luzon5 0）；`Peranap – Singapore` ID–SG；`Singapore – Vietnam` SG–VN；`Singapore – Cambodia` KH–SG。

均按实际Bus国家定类，名称仅标识。没有据项目名字修正端点或去重。输入年份/容量/边界/成本与完整端点在inventory。当前的源网络ID、118项字段差另存 `A05_ELECTRICITY_INPUT_DIFF.json`；没有导入任何论文2050优化后容量。

## 原因与结论的界限

目前已证实的是结构和研究边界修改，不是新的求解失败根因。旧D>Q证书针对常数、旧10.24TWh异常针对未被V4接受的候选点、P2 INF_OR_UNBD针对数值求解终态，三者不得混为“关掉跨境就导致不可行”。新增运输/进口不是本轮结论，也不能据此擅改需求或资源Q。
