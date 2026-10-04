# Buildings + Heat readiness：未达到 DATA ACCEPTED

本轮完成源代码对齐、官方候选核验、99行需求诊断表、42项来源登记及E1/E2/E4独立候选补丁。没有正式Integrated/Disconnected求解、没有数据替换、没有合并R。Buildings边界暂不能最终冻结；本轮结束后不进入其他部门。

## A–K 回答

| 问题 | 回答 | 状态 |
|---|---|---|
| A 原模型模式 | 固定fuel需求、外生fuel shifting和局部heat-service内生供给竞争并存；不是全建筑fuel自由替代 | 目标结构 `ACCEPT_STRUCTURE`；当前数据 `ASEAN_VALIDATION_PENDING` |
| B R/S保持到最终network？ | 原分布式heat分开，central先合并；R随后覆盖S/central；最终power filter又删heat且错误删services electricity。E1/E4候选分别解决相应局部故障，尚未合并 | `ENGINEERING_FIX_REQUIRED` |
| C 真实量 vs 默认量 | UNSD 2019提供最终燃料/电力与少量直接热商品；不是完整useful heat。base R热全0、S只有TH太阳热；未来R大部由DEFAULT拆分/转换生成 | `ASEAN_VALIDATION_PENDING` |
| D 无重复会计能否构建？ | 原则可构建：direct residual+显式direct sector；热服务独立能量账户，conversion用电内生。11国2019算术恒等式已建，但实际network桥接未关闭 | `ENGINEERING_FIX_REQUIRED` + `SCIENTIFIC_DECISION_REQUIRED` |
| E Cooling留在direct可行？ | 结构可行且不新增模块；代码无独立重复cooling load。国家电量校准/既有电热拆分未闭合，不能宣称现有Full-SC已满足无重复 | `ACCEPT_STRUCTURE`；数量 `ASEAN_VALIDATION_PENDING` |
| F Cooking不独立是否无损主结论？ | 不建模块已冻结；**目前不能保证影响很小**。官方用途证据及居民oil分类风险要求共同确认归属和保留方式，不自动扩大范围 | `SCIENTIFIC_DECISION_REQUIRED`；独立cooking模块 `NOT_IN_SCOPE` |
| G 首版必须DH？ | 物理结构不必须；零DH份额合成例仍保留分布式heat和HP。但potential=0不自动删除central Bus/technology。统一0.3/1/0.15无ASEAN依据 | `SCIENTIFIC_DECISION_REQUIRED`；本轮开关修改 `NOT_IN_SCOPE` |
| H Stock足够brownfield？ | 不足。现有EU2012文件无ASEAN、导入调用注释。可提议“未显式表示existing stock”，是否greenfield由用户决定 | `SCIENTIFIC_DECISION_REQUIRED` |
| I 必修工程 | Full-SC前E1/E2/E3；E4必须在使用power-filter或相关对照时处理。三个局部候选测试通过，不代表组合流程或数据已接受 | `ENGINEERING_FIX_REQUIRED` |
| J 需ASEAN-specific数据 | R/S燃料用途及same-year电热桥接、space/water份额、合理shape/效率；若选DH或真实brownfield，还需相应地区网络/stock | `ASEAN_VALIDATION_PENDING`；已核实官方候选 `DATA_UPDATE_CANDIDATE` |
| K 可DATA ACCEPTED？ | **不可以**。来源可读、计算可追、候选能下载均不等于科学输入被共同接受 | 数据UNVERIFIED，human PENDING |

证据入口：[原模型链](BUILDINGS_HEAT_BASELINE_MAP.md)、[官方候选](BUILDINGS_ASEAN_DATA_CANDIDATES.md)、[shape验证](HEAT_PROFILE_VALIDATION.md)、[独立补丁](BUILDINGS_ENGINEERING_FIX_PLAN.md)。本轮没有授予新数据 `ACCEPT_SOURCE_FAMILY`；那需要明确的人类决定。

## 最少还差四组事项

1. **同年R/S用途与转换证据**：先解释印尼UNSD居民油品与ESDM统计的数值/部门差异；确定11国来源策略及缺失处理，冻结final fuel→useful heat链。用户不必再找已缓存的AEO8、ESDM2019、MME/ERIA报告；若拥有对应原始部门能源平衡/端用途表、上报说明或版本说明才请提供。没有全覆盖源时需共同选择异质数据或缩小显式用途，不能补数。
2. **国家电力会计桥接**：将DemandCast/GEGIS等原base与R/S meter、历史电热、保留cooling及loss对齐。至少同年国家×部门×用途的来源/数量/是否已在base表及转换说明。Q默认列不能代替该证据。
3. **热量分摊与时间曲线接受**：国家/用途space-water依据，热带零HDD处理的科学解释，服务业与居民曲线/效率。E2只会正确停止，不会给出缺失数据。
4. **边界与补丁审查决定**：是否接受历史stock未显式表示、首版DH范围、cooking既有燃料归属；分别审查E1/E2/E4，再依据accepted bridge实现E3并验证组合流程。Stock/DH若不进入首版，相应详细资料不是必须强行补齐的输入。

前三项主要是证据缺口，第四项主要是研究边界/工程接受决定。本轮不要求用户重新搜集已经恢复的全部材料。

## 可继续到哪一步

可以讨论Buildings约束下的实验设计草案；**不能冻结Full-SC科学输入，也不能据此启动正式Integrated vs Disconnected成本比较**。全系统是否就绪还受既有其他部门/碳版本审计门槛约束，本轮未重开这些议题。待共同确认之后，“包含cooling electricity但不含cooling flexibility”才可作为相应Full-SC结果的准确边界描述。

验证类型：原始文件/代码为直接读取；CSV残差和转换式为解析核算；气候/用途对结论的风险为推断；未来数据替代和E3实现为待确认方案。未把任一推断写成模型求解结果。
