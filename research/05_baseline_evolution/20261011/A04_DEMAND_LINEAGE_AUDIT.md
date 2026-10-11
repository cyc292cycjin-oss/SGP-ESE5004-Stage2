# A-04 其他需求系统谱系审计

2026-10-11。状态：**COMPLETE_WITH_EXPLICIT_UNKNOWNS（现有证据范围）**。当前已接受需求的注册→分配→冻结Load链没有发现重复入账、正账户丢失或被归零；这不证明所有原始统计需求均完整覆盖，也不证明全LP可行。未修改科学模型、未运行builder/solver、未连接AutoDL；G6-05继续暂停。

证据等级：VERIFIED=固定版本源码、真实冻结输入或本轮轻量计算；DERIVATION=明确假设的推导；SCIENTIFIC_ASSUMPTION=已采用但仍有适用性边界的科学选择；RISK=未证明发生的风险；UNKNOWN=证据不足。

## 1. 身份、范围和本轮直接核对

源码基准`b9be7d0ab788a4151346c098d2e657c7e94a22da`；网络SHA`238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d`，历史构模commit`4b5611dc2dbc3ebcc2ae69b3782b338d2a18b6ce`。二者与冻结源码关系沿用[FROZEN_SOURCE_LINKAGE](evidence/FROZEN_SOURCE_LINKAGE.json)，不混同审计HEAD和构模时间。原论文两份结果使用`5bacad702ccfed17ad19ab510fa710651e966f2c`，通用SC参考`a3616a68ee44592af6527ca9024a90f1956646ae`，前轮已辨明差别。

本次核对registry SHA与实际allocation_manifest绑定，读取冻结NetCDF的Load名称、所有权、源账户及非生物质1352条Load时序；385条生物质年度值复用已接受A-03。实现为一次连续读取约40MiB负荷表后只核算新范围，避免压缩文件逐列随机读取；未读原始解或扫描CSC。首次未完成的随机读取已停止并换为连续读取，不是模型实验重跑。

| 本轮VERIFIED检查 | 结果 |
|---|---:|
| 2050 DEMAND注册记录 | 279 |
| 已批准且实际入模的国家/部门/载能体账户 | 171 |
| 实际Load / 唯一名称 / 有效owner | 1737 / 1737 / 1737 |
| 已批准正账户缺Load / owner不匹配 | 0 / 0 |
| 已批准原始行ID同时归属多个入模账户 | 0（有BaseSourceRows的记录范围） |
| 当前未入模记录Value>0 | 0 |
| PRE_FINAL_REGISTRY已知正目标被改为0或NULL | 0 |
| 已物化非生物质时序负数/非有限值 | 0 |
| 国家账户年度Load与注册值最大绝对差 | 2.384185791015625e−7 MWh |
| 同项最大相对差 | 5.060702485506641e−15 |

最后两项为binary64年度汇总校验，不是“精确实数闭合证明”，不放宽V4。171账户逐条来源、源行SHA/行号、目标、Load清单、年度量和分配方法见[A04_DEMAND_ACCOUNT_REGISTER](evidence/A04_DEMAND_ACCOUNT_REGISTER.json)；汇总见[A04_DEMAND_LINEAGE_SUMMARY](evidence/A04_DEMAND_LINEAGE_SUMMARY.json)。实际Load→Bus的1737条静态映射另外确认国家/carrier不匹配均为0，见[A04_FROZEN_LOAD_DESTINATIONS](evidence/A04_FROZEN_LOAD_DESTINATIONS.json)。没有重做A-03全部807账户与旧X残差。

| 实际固定需求分类 | 国家账户数 | Load数 | 注册年度最终能源（TWh，显示舍入） |
|---|---:|---:|---:|
| A*全部终端用电 | 11 | 96 | 2617.760279 |
| Buildings非电 | 43 | 479 | 974.521109 |
| Industry非电 | 34 | 365 | 4467.291303 |
| Transport非电（国内） | 44 | 436 | 2806.553879 |
| Agriculture非电 | 11 | 114 | 266.271863 |
| 国际bunker | 18 | 130 | 797.973595 |
| OtherNEC非电 | 10 | 117 | 18.419465 |

非电部门行不再含已经入A*的电力；这些是固定最终能源量，不是有用服务量，也不是优化所得能源消耗。

## 2. 上游→当前的继承、替换和排除

原论文两份网络均有488个Load：96个AC基础Load以及各98个industry electricity、EV、rail electricity、agriculture electricity，见已接受[A03_UPSTREAM_RESULT_TOPOLOGY](evidence/A03_UPSTREAM_RESULT_TOPOLOGY.json)。这不能当作通用SC的全部需求清单；当时`only_elec_network=true`会删除许多非电载荷。

| 系统 | 通用SC实际机制 | 当前冻结Full-SC表达 | 数学/科学影响及证据等级 |
|---|---|---|---|
| A*与各部门电力 | 原始AC profile、单独工业/农业/铁路/EV Load；SC还有住宅电力重标定及分布网迁移 | 11个A*国家父账户分配为96个Load；没有单独Electricity子账户再次入模；作者2025基础Load只提供相对形状 | VERIFIED替换了绝对需求及所有权；不是沿用论文总负荷。对子部门细分、EV时移/充电可控性的刻画不等价。 |
| Buildings | SC已有住宅/服务热Bus、热Load、热泵等；住宅还可按能源总表分拆oil/gas/biomass及剩余热 | ResidentialFuel、ServicesFuel的非电最终能源分别入账；住宅/服务电力及未拆热服务留在父账户，不额外建立有用热Load | VERIFIED。避免从同一最终燃料再造有用热义务；但不是上游热服务替代技术问题。燃料结构与替代空间由当前边界固定。 |
| Industry | SC读取工业表，添加biomass、gas、H2、heat、电力等；coal存在排放核算路径 | IndustryFinalEnergy用2019报告工业父项，非电coal/oil/gas/biomass形成真实最终能源义务；电力嵌入A*；未批准H2/热工艺不新增Load | VERIFIED。13子行业表用于核对而不叠加父项；从工艺可替代需求变为已接受最终能源载能体义务，改变RHS及可替代性。 |
| Transport | SC有EV电池Load/充电器、油/H2份额；铁路油为total rail−electricity rail；航运航空有单独路径 | RoadResidualFuel只增长非电2019分量；EV/铁路电力嵌入A*；铁路非电只保留资格明确源项，不将不明父项减电力后任意当油；国内/国际四类油分开 | VERIFIED。不是完整道路车辆活动模型；不保证各类出行服务量相同。固定燃料和电力父账不是自由技术份额优化。 |
| Agriculture | SC已存在农业electricity、oil等需求；不是本项目新增部门概念 | 农业电力留A*；已批准oil、biomass、coal最终量入模，无已批准gas条目 | VERIFIED。农业-and-others增长代理及商品份额继承是SCIENTIFIC_ASSUMPTION。 |
| OtherNEC及bunker | 原源表与上游配置可能不同范围；论文国际bunker关闭 | 当前保留获批OtherNEC、TransportNEC及国际bunker，且不并入居民/工业父项 | VERIFIED边界变化；不能把所有差值归为重复需求。 |

上游定位：[SC工业1853起](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L1853)、[工业电力2080起](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L2080)、[EV Load2440起](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L2440)、[热Load2703起](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L2703)、[农业3142起](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L3142)、[住宅电力3404起](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L3404)、[铁路3718起](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L3718)。只说明代码能力/条件分支，不声称所引论文全部运行了这些分支。

## 3. exactly-once及最终/有用能源

当前[build_research_network.py](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/build_research_network.py#L15)拒绝带Load的组件配方和旧需求；[bind_loads49–67](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/assembly_components.py#L49)在空Load集合上按InputID@node唯一绑定、校验国家和carrier，仅跳过全年全零节点分量。实际1737个owner/source_account_id与注册账户一一归属，171个正账户全部保留，故这里的零节点跳过没有丢失国家正量。

`demand_accounting.py`将单位定义为最终能源MWh，拒绝缺失/负数/非有限值；EMBEDDED_IN_ASTAR记录不能另post；父账户转移与子和必须核对。`demand_buildings.py`、`demand_transport.py`和`demand_industry_agriculture.py`是早期账本/待接受表达，不能把其中PENDING模板当作最终冻结目标；实际采用的是registry内`NUMERIC_INPUT_READY`与后续批准方法，并由allocation/NetCDF验证其落地。

**DERIVATION边界**：电力A*加非电燃料是不同载能体的最终需求并列，不因两者服务同一部门就算重复；用于制氢/FT等的电力是转换Link内生消耗，不应再作为A*的外生Load增加。当前不将终端燃料MWh机械转换成有用热/牵引MWh，也未批准相应效率后的服务需求等式。因此能够证明账户不重复，不能证明服务水平或2050技术份额与上游相同。

## 4. 2019源数据、2050代理与空间/时间链

源路径均位于固定commit的`research_inputs/assembly_v1/sources/`；文件SHA见[A04_SOURCE_INDEX](evidence/A04_SOURCE_INDEX.json)。本轮不重新爬取全部统计宇宙。

1. **2019重构（VERIFIED代码）**：`reconstruct_base_accounts.py`按国家、商品、transaction、单位识别末端行；精确alias去重，冲突值报错。工业使用报告父项，子行业只是审计对照；hard/brown coal父项替代子项而非相加。电力million kWh×1000；TJ以3600MJ/MWh转换；源NaturalGas GCV只在对应源类用0.9转NCV；固体/液体商品及fuelwood使用冻结热值/体积因子。TH道路使用获批本地源版本，未全局覆盖其他国家。
2. **A*（VERIFIED数值、SCIENTIFIC_ASSUMPTION预测）**：ASEAN10总量225 Mtoe×11,630,000=**2,616,750,000 MWh/a**，按2019各国最终用电父项份额分配。TL以同一增长比额外外推**1,010,278.750596059 MWh/a**，不挤占ASEAN10总额；合计11国。11.63TWh/Mtoe为已批准统一换算约定，原AEO源单位元数据未完整恢复这一历史限定仍保留。A*不是电厂发电目标，也不是经验证的国别部门2050预测。
3. **非电增长代理**：住宅`68.2/63.0`，服务`75.9/29.5`，工业`561/185.6`，农业`27.8/8.8`；将AEO2022→2050比例应用于合格2019基量，保留基年商品份额。道路非电`374.9/145.2`；道路总量参考350.5315 Mtoe不再作为第二个强制父等式，EV嵌入A*且没有独立获批数值。以上均为明确代理，不是2019与2022自然相同。
4. **常数边界**：国内航运/航空、国际bunker、已批准RailNonElectric、TransportNEC、OtherNEC沿用2019常数量；未自动给予增长。改变这些选择会改变真实RHS，不能用数值调参名义实施。
5. **混合燃料**：`final_closure_inputs.py`采用批准的max-overlap：`Z=min(P,B)`，化石部分`(P−Z)×h_p`，生物部分`B×h_b`；两个热值不混用，先去可能嵌入的生物燃料再分别增长。原P/B保留。这是有记录的重叠假设，不是仅凭代码已证明每个源表的嵌入规则正确。
6. **空间与时序**：[allocate_assembly_inputs18–82](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/allocate_assembly_inputs.py#L18)只选作者2025网络中名称等于地理节点且carrier=AC的基础Load，排除EV/industry等子Load。11个A*沿用归一化基础输入时序；128个其他账户按基础电力年量节点份额、全年平坦；12个航运账户按同国最近节点港口size权重，20个航空账户按机场size权重、均平坦。无同国点则报错，不任意均分。港口/机场size不是交通或燃料消耗观测。
7. **权重**：实际2013气象/时序索引，2050需求目标，2920×3h=8760h。非电`p_t=年量×节点份额/8760`；电力按实际基础profile归一。没有把2920当8760重复累计。年度浮点守恒通过不代表每一个供需binary64常数与资源库存在有理数意义精确一致，A-03补证单独处理这一点。

上述增长表达代码见[rebuild_assembly_targets.py](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/rebuild_assembly_targets.py#L15)，本轮只读，未执行重建函数。完整账户数量、载能体、年度量在轻量证据中，避免用一个部门总数掩盖边界。

## 5. 未物化、已知正量与覆盖限制

108个未入模2050 DEMAND条目的**Value全部为NULL，不是0**：86个SOURCE_SUPPORTED_NOT_APPLICABLE、7个SOURCE_SCOPE_NO_ADDITIONAL_FINAL_LOAD、15个UNREPORTED_OUTSIDE_ASSEMBLY_V1_FIXED_DEMAND。逐条国家、源行、原因和批准边界在[A04_NONPOSTED_DEMAND_BOUNDARIES](evidence/A04_NONPOSTED_DEMAND_BOUNDARIES.json)。

- 7个source-scope条目为BN煤4项（住宅/服务/工业/农业）、TL气3项（住宅/服务/道路）。`source_scope.py`核实源范围含供给/转化层级，不能重复当末端消费；若找到真实末端/国际bunker行则拒绝排除。它没有证明未知末端需求等于零。
- 15个未报告项按明确科学批准排除在assembly-v1固定需求边界之外；其中部分气、煤及国际航运缺报。不应把“未发现当前已知正Value丢失”扩大成“这些国家真实需求为零”。
- 86个NOT_APPLICABLE含源支持范围内的零/不适用资格，最终仍以非数值边界表达；不能用空单元格机械补0。没有重新审计每条原始报告覆盖面的完整性。

VERIFIED：从PRE_FINAL_REGISTRY到当前registry没有正Value变成0/NULL；当前171个正已批准账户全部实际存在。**UNKNOWN：全部底层统计源和未来部门需求是否完备，以及被排除未知项真实正值是多少。** 两个结论并不矛盾。

## 6. 分类结论与停止边界

| 分类 | 本轮结论 | 可行域影响/尚需判断 |
|---|---|---|
| 已证明的当前实现错误 | 在上述已接受链中未发现重复Load、正账户消失、错误权重或额外电力子账 | 不能外推为所有代码无bug。旧上游及早期PENDING模板不等于当前活跃方程。 |
| 已确认的科学假设变化 | A*父账、固定最终载能体义务、非电增长代理、2019常数bunker、独占生物质账户及排除未知需求边界 | 改变RHS、服务含义或技术替代空间；不是数学等价缩放。 |
| 数据/科学风险 | 2022比例施于2019、农业-and-others代理、TL外推、max-overlap、平坦燃料时序与电力/设施size空间代理、15项缺报排除 | 可能改变峰值能力要求、空间瓶颈和年度义务；本轮没有证明造成已见求解失败。 |
| 数值问题 | 385组精确binary64源闭合差及选定组真实LP正差已验证 | 严格全LP矛盾证书仍缺完整所选行支撑；见[A-03补证](A03_EXACT_ANNUAL_CLOSURE_PROOF.md)。 |
| 仍未知 | 全LP可行性、Presolve状态的具体触发路径、各科学代理的实证误差 | 无新增求解证据，不下因果断言；不授权自动修正。 |

本轮只更新谱系和证据。未启动B—F；不因识别科学假设而修改源需求/资源Q/载能体边界。后续由用户与ChatGPT判断当前“固定终端能源核算”是否满足研究问题，以及是否、何时允许补齐严格证明的结构证据。G6-05与其他优化授权均不恢复。
