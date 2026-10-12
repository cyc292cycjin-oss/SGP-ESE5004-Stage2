# B-01 资源—需求物理可行性必要条件审计

2026-10-12；状态 **B01_COMPLETE_WITH_EXPLICIT_LIMITS**。本轮已核范围未发现新增的确定供给断路、名义容量上下界矛盾或最低输电容量超预算；这不是新Full-SC LP可行性证明。

## 1. 四个身份与适用范围

| 对象 | 固定身份 | 本轮用途/限制 |
|---|---|---|
| 原冻结科学网络 | 科学源码`b9be7d0ab788a4151346c098d2e657c7e94a22da`；NetCDF SHA `238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d` | 读取实际静态表、端口及必要的现有输入时序。原Q仍为旧值，不写回。 |
| 原Gate6 LP/历史 | 19,568,505列/48,301,938行/90,782,037项；旧精确证书、第一次OPTIMAL/V4 NOT_ACCEPTED、第二次INF_OR_UNBD | 复用原证据，不重扫CSC或X，不改变消费标记。 |
| Scheme A独立源版本 | PR #4 commit `8883de6fb3e15767c632ac92f535e8a423e90b69`；Version Manifest SHA `a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720` | 从固定Git对象读取新配方及外置账户，绝不从当前审计分支旧Q推定新Q。 |
| 已审阅A阶段 | 起点A06 commit `85397fdfd587a4e0cda298139b3c8f43fbbc6d6a`；A01–A06文件及明确UNKNOWN保留 | 新独立B分支，不合并PR #3/#4/#5/#6；不组装Scheme A网络或LP。 |

新配方SHA `1b0ea897bc17d652a6ac5047935dc6af6c53536a51b197582b3567313d155e8e`，外置807账SHA `20d9d0dc2028f1ca4e07b8e4e02fe51fce3a4a357c0d86366076a528b9a2a8e0`均由实际Git内容核对。绑定及读取范围见[B01_B02_IDENTITY_AND_READ_SCOPE.json](evidence/B01_B02_IDENTITY_AND_READ_SCOPE.json)。完整NetCDF SHA复用A05/A06核验，不再次对历史大文件全量哈希。

证据等级：VERIFIED=直接文件/端口/数值；DERIVATION=说明假设的推导；RISK=具体但未证明发生；UNKNOWN/NOT_PROVEN=本轮不能确认。没有新增科学批准或求解授权。

## 2. Scheme A年度源常数与独占资源子系统

**VERIFIED：385/385组精确D≤Q′；180个账户修订，627个不变。** 使用binary64对应Fraction重求各组Q′，与原精确D交叉验证。四字段Store.e_nom、e_initial、route.annual_cap_mwh和外置QuantityMWh相等；807项NULL价格/排放资格保持。Load及权重不变的既有静态验收直接复用。新配方未装入旧NetCDF。

- 385组全部是严格D<Q′，没有声称D=Q′；总库存余量约`2.877903736275139e-7 MWh`，组最大`9.816722013056278e-8 MWh`、最小`1.8214596497756474e-16 MWh`。
- Java-Bali1 2工业生物质组：旧`D−Q=513/34359738368 MWh`；Scheme A源级变为`Q′−D=255/34359738368 MWh`。旧LP及其不可行性证书永久有效于旧版本。
- 807个旧实际Store仍为固定、非循环、无库存损失，初始库存=旧Q，库存比例界[0,1]；资源Bus仅接其Store和唯一meter，meter输入−1/最终Bus输出+1、p_min_pu=0、可扩建且无有限功率上限。冻结元数据为807条`discharge_only`；该属性由`ResearchStoreDirection`实际hook表达，不能只把Store的非原生p_min_pu字段当作约束。
- 385个最终Bus均只有所列商品meter及唯一Load，没有旁路或新增供应。所有三类snapshot权重均2920×3h。非电Load平坦且非负。

证据：[B01_SCHEME_A_SOURCE_BRIDGE](evidence/B01_SCHEME_A_SOURCE_BRIDGE.json)、[B01_RESOURCE_TOPOLOGY](evidence/B01_RESOURCE_TOPOLOGY.json)、[旧A03结构审计](../FINAL_OBLIGATION_BUS_IMPLEMENTATION_AUDIT.md)、[旧完整LP证书](../A03_EXACT_ANNUAL_CLOSURE_PROOF.md)。实际字段可按资产ID复核；route是派生核算/上限身份，不虚构一条单独的route年度LP行，实际有限库存由Store动态与非负界限制。

**DERIVATION：仅对已经列明的独占资源子系统**，设`Q′=Σq′_i`，平坦或一般非负需求`d_t`、正权重`w_t`，可取实数表达

`r_i,t = q′_i / Q′ × d_t`，`e_i,t = q′_i − q′_i / Q′ × Σ_{τ≤t} w_τ d_τ`。

于是Σr=d、0≤e≤q′、Σw r_i≤q′_i，所有前缀成立；可扩建无有限速率上限的meter不产生额外速率瓶颈。终期保留`q′_i(Q′−D)/Q′`而非强行清零。独立Fraction校验器核对385组年度/余量恒等式。**这是连续实数局部子系统的条件性构造，不是生成新LP解、逐组完整行支撑证书或V4结果。** 它不保证其他约束无矛盾，也不证明binary64求解器能在V4阈值内找到此类点。

## 3. 全部固定需求的实际供给路径

每条Load的实际Bus、国家、年度量、峰值、输入时序SHA及供给资产ID在[B01_LOAD_SUPPLY_PATHS](evidence/B01_LOAD_SUPPLY_PATHS.json)。年度汇总为普通binary64报告量；精确闭合仅上节385组采用Fraction。

| 最终载能体 | Load数 | 年度最终需求TWh（显示舍入） | 已核路径及必要条件 |
|---|---:|---:|---|
| biomass | 385 | 1607.166223 | Scheme A有限独占Store→单向效率1 meter→最终Bus；不能跨组挪用或转供发电/H₂。 |
| gas | 274 | 910.153285 | 同节点外部gas Generator→燃料Bus→效率1燃料/碳meter→最终Bus。 |
| oil | 819 | 4937.021496 | 外部oil→本地油Bus→meter；FT是同油Bus的可选供应，不是强制前置。 |
| coal | 163 | 1876.690209 | 外部coal→本地煤Bus→meter。 |
| electricity A* | 96 | 2617.760279 | 实际负荷节点均有外部gas→本地CCGT→电Bus路径，效率0.6；其余存量/可再生/输电为额外选择。 |

**VERIFIED：1737/1737有上述路径，未发现无路径Load。** 400外部Generator按100节点×coal/gas/lignite/oil部署：p_nom=0、extendable、p_nom_max=∞、p_min_pu=0、p_max_pu=1；冻结`external_annual_caps={}`，没有年度进口量上限。边际价分别9.5542、24.568、3.2985、52.9111 EUR2020/MWh，绝不称为免费供给。1256个化石最终meter与100个新CCGT均有合法正向、可扩建无有限上限且零最低出力。其非能量副产物进入大气核算Bus，见B02。

因此：在当前**模型边界**内，非电跨境关闭并没有切断这些固定需求的全部供应。市场供给不需要物理跨境Link；但无限外部市场能力不是现实可用进口能力证据。对96个电力Load，“本地输入容量未给出有限瓶颈”强于单纯名称匹配，仍不是全网络同时调度证明；KVL、共享约束、联动消耗未被忽略或假设放宽。

## 4. 固定存量、技术潜力、网络与时间界

实际nominal/static dispatch上下界已逐资产检查，未发现lower>upper或正最低出力强迫供给。数据在[B01_CAPACITY_AND_PROFILE_CHECK](evidence/B01_CAPACITY_AND_PROFILE_CHECK.json)、[B_SHARED_CAPACITY_AND_STORAGE_NECESSARY_CHECKS](evidence/B_SHARED_CAPACITY_AND_STORAGE_NECESSARY_CHECKS.json)。

| 对象 | VERIFIED事实 | 必要条件结论及边界 |
|---|---|---|
| 固定化石电厂 | 92条存量Link：coal42、CCGT34、lignite8、oil8；容量固定、p_min=0 | 固定资产存在不等于必须每时段运行；零出力在其单独运行界内允许。 |
| 可再生/径流 | 438个风光候选有有限p_nom_max；22个ROR固定；460列实际p_max_pu有限非负 | 没有发现名义下界超过上界；有限风光不能当成无穷供应，但当前CCGT路径并非依赖其正出力。 |
| 可再生profile例外 | 4个offwind-dc全年0；6个最大为1.0000000000000002（1上方1 ULP） | 0列不能计作可用电源；极小超1是已见输入值，不认定求解失败原因、不自动裁剪。具体资产见B02_LOCAL_OIL_SINK_LIMITS的profile_exceptions。 |
| 水电/PHS | 40个hydro、3个PHS StorageUnit均循环；初始库存落在0至p_nom×max_hours内；40列inflow非负 | 未发现初值直接矛盾；复用PyPSA储能平衡与spill变量公式，不把自然入流当强制发电。尚未证明联合时序可行。 |
| 电网 | 105 AC+10 DC可扩建，3 B2B固定；100电节点按实际电支路形成20个弱连通分量（13个单节点） | 弱连通不等于有向传输可行。存在孤立节点不自动等于失供，实际正电力Load各有本地路径。 |
| lv_limit | 115个AC/DC投资项最低容量×长度之和126,797,074.13498563 MWkm；上限353,746,853.52332264 MWkm | 最低容量不超限，约226,949,779.388337 MWkm余量。没有证明足以支持未来最优潮流，单条∞不消除共享cap。 |
| 共享资源hook | 冻结NetCDF `existing_resource_groups={}`；通用源码能加ResearchExistingResource，当前未登记此类组 | 不能把通用能力当成当前有行；有限候选上界仍在组件表，不能宣称无技术潜力限制。 |
| 时间 | 2920个三小时，objective/generators/stores均3；Link没有动态边界或效率覆盖 | 没有此范围权重或端口时变冲突；不扩张到未重建的LP全部行。 |

已核源代码：`carrier_architecture.py`供给/方向hook、`build_research_assets.py`最终账户与新CCGT、`integrate_surviving_assets.py`存量/资源包络、`assembly_components.py`需求唯一绑定/电池容量耦合；固定commit、行号、SHA和实际摘录在[B_FROZEN_SOURCE_FORMULAS](evidence/B_FROZEN_SOURCE_FORMULAS.json)。

## 5. 与历史Gate6违规的关系

旧277644条Store下界、324120条Bus平衡、377账户/111组约10.24TWh超用，是旧OPTIMAL候选未通过V4的直接证据；不是Scheme A新候选的违规，因为新候选不存在。旧精确证书是已证明的旧常数矛盾；Scheme A只关闭该源级矛盾。微小常数差与10.24TWh量级之间、与P2 Presolve INF_OR_UNBD之间没有足够因果证据。

本轮没有发现另一个可直接从所查供给/容量界推出的矛盾，也没有证明不存在其他矛盾。旧候选不能用作严格可行证书，INF_OR_UNBD不能改写为INFEASIBLE；原科学成本、NULL资格、V3/V4/P2及历史结论未变。

## 6. 完成边界

B01的有限静态必要条件检查完成；**全LP可行性NOT_PROVEN**、Scheme A新网络/LP **NOT_ASSEMBLED**。未启用任何新供应、跨境载体、碳旁路或松弛。下一步仅交由用户/ChatGPT审阅[B风险登记](B_PHYSICAL_FEASIBILITY_RISK_REGISTER.md)，不自动开始后续B、C—F或G6-05。
