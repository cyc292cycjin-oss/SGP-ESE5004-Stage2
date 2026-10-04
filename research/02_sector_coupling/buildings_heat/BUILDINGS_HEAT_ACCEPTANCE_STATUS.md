# Buildings + Heat acceptance status

**本轮结论：不能直接用于 Buildings + Heat scientific baseline，不能冻结 full-SC boundary，也不能启动正式 Integrated / Disconnected。** 可以继续有条件的实验设计与局部工程验收；数据和科学边界仍待用户+ChatGPT共同确认。

固定U/P SHA与T来源见 [README](README.md)。以下状态是审计判断；CSV所有输入保持UNVERIFIED/Human_Acceptance=PENDING。

| 项目 | 状态 | 证据与含义 |
|---|---|---|
| 固定热服务、内生技术选择、R/S单列 | ACCEPT_STRUCTURE | 用户冻结原则，可作为目标；不是现有全部代码已符合 |
| UNSD原始建筑燃料源→base | SOURCE_RECOVERED | 11国92行，原函数12列精确对账；服务完整性仍待证据 |
| 完整useful heat年度量 | ASEAN_VALIDATION_PENDING；SCIENTIFIC_DECISION_REQUIRED | 燃料、heat商品、默认用途/效率混合，服务端尤其不完整 |
| space_heat_share与fuel split=0.6 | SOURCE_RECOVERED；REJECT_DEFAULT | 历史可追，没找到ASEAN数值依据；两个独立入口 |
| BDEW fixed profile | SOURCE_RECOVERED；ASEAN_VALIDATION_PENDING | Eur-Sec历史文件数值相同；原24×8生成配置未完全恢复；不是地区验证 |
| 暖区zero-HDD与年度量映射 | ENGINEERING_ISSUE | T已观测正年度量落在NaN曲线；U有相同零分母机制 |
| R/S/central热量覆盖 | ENGINEERING_ISSUE | 固定原函数合成测试证实跨部门覆盖 |
| 人口布局、UNCTAD城市化率 | SOURCE_RECOVERED；ASEAN_VALIDATION_PENDING | 全球源含地区，不等于按建筑用途验证；版本与分配假设待锁定 |
| DH potential/progress/loss | REJECT_DEFAULT；SCIENTIFIC_DECISION_REQUIRED | 无ASEAN支撑，progress=1强制城市目标；loss分母需澄清 |
| 欧洲现有供热设备替ASEAN | REJECT_DEFAULT | EC EU28+3、2012年；ASEAN缺行落0，不是实际无设备 |
| 既有设备接入与urban字段 | ENGINEERING_ISSUE | 调用注释；分配代码字段不符；当前不应宣称brownfield约束 |
| Cooling current placement | SOURCE_RECOVERED；SCIENTIFIC_DECISION_REQUIRED | 无独立冷服务；隐含aggregate电力是推断，不能给出已验证冷量 |
| HP/boiler/CHP/TES形式 | ACCEPT_STRUCTURE | 剩余热负荷上的优化接口可继承；菜单/成本/适用区未被科学接受 |
| Fuel shifting DEFAULT | REJECT_DEFAULT | 提前固定份额和燃料负荷限制技术替代；没有ASEAN依据 |
| 直接电力账与final adjustment | ENGINEERING_ISSUE | AC覆盖、服务命名裁剪、总量调校与电热扣减无统一桥接 |
| U/T/P heat switches=true | SOURCE_RECOVERED | 三者最终only-electric，不能作为full-SC科学证据 |

## A–J 最终回答

**A. 年度量真实来源？** UNSD 2019 households/services 的燃料与heat商品统计，经默认增长/效率和居民燃料用途/电气化份额构造。不是直接测得的完整ASEAN useful-heat表。原始92行可精确核回base，未来热服务量仍不能接受。

**B. BDEW是否用、承担什么？** U规则确实绑定该文件，用于裁剪前热模块的日内/周内shape；T有实际输出证据。它不决定年度量；最后only-electric裁剪掉热。P开关存在同样不能等同于paper full-SC case。

**C. 0.6有ASEAN依据？** 没找到。追到Earth-Sec 2023年的参数化提交，原来是硬编码0.6/0.4；另有fuel CSV中的0.6。分类DEFAULT_WITHOUT_ASEAN_EVIDENCE，数值未改。

**D. DH有ASEAN依据？** 0.3/1/0.15没有找到地区支撑，DEFAULT当前份额0也未验证。城市比例有UNCTAD入口，但真实城市化率不能证明30%供热集中化适用。配置与CSV potential不是同一个消费路径。

**E. Cooling已在base吗？** 模型把它留在未分解的总电力边界；未见专门扣除。实际空调用电隐含于总统计是推断，11国分量未恢复，不能无条件回答“已完整计量”。无独立cooling Load/chiller/reversible HP/cold store。

**F. 有电力double counting吗？** 未通过守恒验收，但不能笼统说“A+R+S”简单三重计数：R会覆盖AC。明确缺陷为热量覆盖/丢失、服务carrier被错误裁剪、电热扣减未实施；若只放开裁剪，final aggregate缩放与服务Load会有重叠风险。当前没有“base + explicit cooling”的已证实重复，因为后者不存在。

**G. 固定fuel还是固定heat？** **混合**：居民部分燃料外生转为剩余heat服务，其余fuel固定；服务燃料固定，少量heat商品另成热Load；DH份额外生。居民函数又跨部门覆盖heat。这不满足所有供热燃料内生竞争的目标。

**H. 有多少技术真正竞争？** F/U裁剪前五类热系统可扩张HP、gas/resistive、hot-water TES、solar thermal；urban central加gas/biomass CHP及启用时的捕集版本。它们只竞争模型留下的heat Load，不替代全部固定建筑fuel。micro CHP关闭，oil-boiler新建键未实际接通，cooling不存在；最终U/T/P-only-electric不保留完整热竞争。

**I. 能直接用吗，最少改什么？** 不能。工程：隔离R/S覆盖、零shape保护、端用电力守恒及final carrier处理；数据：可信的R/S服务年度量、适用时间形状及电热桥接；科学：nonthermal/cooking、cooling、DH、存量边界。修复需另轮，当前仅记账。

**J. 用户要提供什么？** 无需重找源码、BDEW文件或UNSD下载链接。若已有非公开建筑端用统计/小时测量/设备存量或导师指定表，提供原文件和版本；未来许可数据库需授权导出。公开源恢复由代理继续，边界选择由用户与ChatGPT共同决定。[精简缺口与责任](BUILDINGS_HEAT_DATA_GAPS.md)

## 复现与风险边界

本轮直接读取固定Git源码、既有raw/intermediates、作者metadata；仅对原函数做隔离合成核算，无solver。教程的41/48 NaN节点是T层观察，不冒充U全年误差；合成TWh也不是科学输入。未新增任何技术或政策，未展开其他部门、合作博弈或construction delay。原模型与冻结参考工作树保持不变。未经数据共同确认不启动正式实验。
