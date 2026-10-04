# 首个Full-SC基准的最低可辩护Buildings范围

**先保证能量和比较边界正确；不再把11国完整热用途、设备和小时资料当作共同先决条件。** 本文按用户已冻结规则提出首次组装的账户表示方案，数值输入仍未获得新的接受。

## 表示规则

| 标签 | 实际含义 | 不意味着什么 |
|---|---|---|
| EXPLICIT | R/S直接电力与相应燃料分别有可追踪账户；若为热服务，还须能构造兼容服务量并完成原输入互斥转移 | 有源文件就自动可用；或本轮已经建入网络 |
| EMBEDDED | 用途仍包含在原部门direct electricity/direct fuel内，不拆出额外热Load | 该用途为零、不重要，或已表示其内生电气化/灵活性 |
| PENDING | 某项数值、映射或晋升显式服务的证据未满足；同时声明当前可用的embedded回退路径 | 必须从总能耗删除，或自动阻断所有其他部门工作 |

每个country×sector×end-use独立判断；没有共同ASEAN space/water比例。只有“来源强、地域/年/单位/部门兼容、useful服务可构造、原能耗已包含且能一次转移”的账户，才提出晋升显式热服务。直接报告useful服务也需核对覆盖和历史输入的会计关系，不强迫所有账户先收齐设备型号。

若不能构造服务量，保留父能耗和unclassified用途；不把未知值写零，不借未来DEA效率回填历史，不把Malaysia份额复制到其他国家。需进一步资料时，只针对可能改变研究结论的账户开展有界工作。

## 本次22行建议

`BUILDINGS_FIRST_FULLSC_BOUNDARY.csv`覆盖BN、KH、ID、LA、MM、MY、PH、SG、TH、TL、VN各自Residential/Services。依据Phase3A5的44组合及140候选、Phase3A6 Malaysia更新，**没有一个全国热服务账户已经达到可直接晋升标准**。因此建议：

- 22个R/S部门均保持独立的直接电力账户；有证据的直接燃料按燃料分别保留一次。缺燃料记录不是零，仍走共同数据核对。
- 44个space/water用途暂为EMBEDDED；其晋升证据为PENDING，不生成虚构useful量。
- Cooling保留在直接电力中，首基准不建内生制冷灵活性，不添加第二份cooling Load。
- Cooking保持NON-EXPLICIT + ACCOUNTING REQUIRED；电力和各燃料保留一次，不进入space/water热需求。
- District heating不自动激活；不制造ASEAN brownfield库存；BDEW仅作reference。未表示库存约束不等于真实库存为零，也不授权将所有设备当作新建资产。

Malaysia只保留已核验的方法原型：2016半岛water final-input明确，完整全国目标年服务值仍缺；不能为了让它成为EXPLICIT而跳过性能、地域或R/S分区。KH/SG/VN地区space线索也不等于国家量。国家差异和来源行定位随CSV保存。

## 嵌入回退怎样守恒

保留的是**经过共同final-energy边界审阅的原能量**，不是盲目复制现有workflow经过未来fuel-shift或generation校准后的Load。父账户、子项和其他部门必须互斥：R/S不能在A*外再额外叠加；cooling/cooking是子账；未分类能量不消失。

对当前未晋升热服务的账户，不执行电热扣除，也不为同一用途生成heat Load、HP/boiler服务或额外直接燃料。以后晋升哪一项，就只转移其兼容历史输入一次，未来供能技术输入内生。该方案不需要先实施全11国E3。

**CSV是研究表示契约，不是可执行config。** 冻结upstream默认热构造、R覆盖AC、S另加Load、generic0.97和generation缩放不会因写了报告而改变。未来组装必须证明它们与本契约一致，不能一面保留embedded能耗，一面沿默认路径再造热服务。本轮不写该实现。

## Materiality分流

判断记录必须写出：缺口→模型输入/约束/时序→成本、主要容量、跨境网流、国家投资、电气化或Integrated/Disconnected差额的可信路径。只有“也许有关”不构成无限搜索的理由；同样不能因缺数据就断言不重要。不设置数值阈值。

15项登记分为共享系统会计/接线门槛、显式热账户晋升条件、首基准范围限制和比较门槛。`FullSC_Blocker=SHARED_SYSTEM_GATES_ONLY`表示该country/sector没有新增“必须补齐热细节”的阻断，但共同总量/损耗/重叠等门槛仍在。M01–M06在数值组装前核对，M15在正式对比前核对；它们不阻断下一部门的边界审计。

独立设备参数、未使用的MY2016小差额、所有热用途专属小时曲线、统一库存和DH细节，当前不再阻断。若具体新证据显示某个被嵌入用途会实质改变关键比较，按该账户重新开启审查，不追求全11国同时达到同样细度。

首基准允许继续研究，但不能声称已经覆盖全部Buildings转型和灵活性。固定嵌入对互联收益差额的偏差方向未定，不能自动称为“收益下界”。相同表示和需求必须用于未来Integrated与Disconnected两侧。
