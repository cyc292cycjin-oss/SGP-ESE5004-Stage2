# Phase 3B-2 — Road / rail 收口独立核查

审阅日期：2026-10-03。范围：只读复用Phase3B-1冻结源码、缓存证据和报告；未修改配置/模型、未下载、未运行工作流或求解。此文件是主任务综合报告的支撑审阅，不能代替最终用户接受记录。

冻结身份：Paper P=`5bacad702ccfed17ad19ab510fa710651e966f2c`；Current U=`a3616a68ee44592af6527ca9024a90f1956646ae`；Buildings validation=`50a73d8f531132c5459174a55cac412d5f684462`。下文U/P路径均相对于`../../phase3b1/evidence/source/`，不是正在跟踪的main。

用户新指令已决定第一版Road aggregate/EV显式、residual fuel固定、Rail嵌入、FCEV/DSM/V2G推迟。以下**不重开这些选择**；只区分会计规范成立、现有实现情况及Phase4集成所需验收。

## 1. Road final-energy identity：成立，但需要正确的分母与计量端

**分析推导／本轮规范，非新数值输入：** 对同一国家c、同一目标年y及同一final-energy口径，定义：

- `RoadTotalFinalEnergy = R[c,y]`，统一MWh/year（或TWh/year，记录确定转换）；不包括rail、不包括shipping/aviation、不包括上游制氢/FT生产用电。
- `RoadElectricShare = sE[c,y]`，定义为该年road **最终电能占道路最终能耗的份额**，不是EV车辆存量份额、销量份额、里程份额或useful-traction份额。
- `RoadFuelShare = 1 − sE`，在首版不含直接FCEV的边界内成立。
- `EVFinalElectricity = sE × R`，本规范计量于最终用户充电电力输入端；它与A*使用相容计量点。
- `ResidualRoadFuel = (1 − sE) × R = Σ_k F_road,k`，k为实际保留的非电燃料类别。
- 恒等式：`R = EVFinalElectricity + Σ_k F_road,k`。检查0≤sE≤1、R/F均非负且单位/年份/覆盖一致；缺失不能变零、不能靠clip修正。

这是一套**energy-based aggregate accounting**，没有构造passenger-km、tonne-km或牵引服务量。它不声称一MWh燃油与一MWh电力提供相同交通服务。若比较两种电气化路径，R与sE必须作为联合一致的外生最终能耗情景；不能将历史R固定不变并声称由份额变化已经正确模拟了电气化节能。Integrated与Disconnected比较可共同使用完全相同的R、sE、燃料向量和曲线，以保持共同义务，不需要为此新增车型模型。

**旧参数不能直接改名复用：** U/configs/config.asean.yaml:216–231的DEC EV share是上游外生share；U/scripts/prepare_sector_network.py:2430–2453又把它同时乘需求和车辆数量。该代码没有证明它就是本规范sE。因此不把DEC_2030=0.2等值自动重新标为accepted EV energy share。U/scripts/prepare_energy_totals.py:260–270已以车种share加权效率趋势来生成total road；也不能未审查就把该预测量作为新R、再重复计入同一效率收益。

**旧量纲错误的准确状态：** U/scripts/prepare_transport_data_input.py:115–140从CO₂百分比得到无量纲数；U/scripts/prepare_transport_data.py:128–180与config注明kWh/km的0.2组合，不能闭合真实能源转换。本规范完全不使用该链，故“替代规范的定义已闭合”；本次只读审阅没有替换正在运行的实现，也没有确认任何R/sE数值，故不能说“原生产代码已修好／真实数值已验证”。

## 2. Residual fuel必须保留gas/biomass，不能悄悄全部变oil

**直接证据：** U/scripts/build_base_energy_totals.py:203–222分别生成road electricity/gas/biomass/oil。Phase3B-1 `CACHED_DEMAND_NOTES.md`和`CACHED_DEMAND_EVIDENCE.json`记录2019缓存中ID、MM、MY、TH的road gas为正；ID、MY、PH、TH、VN的road biomass为正。它们仍是未接受的缓存值，但足以否定“全部road final energy都是液体化石油”的默认归类。

旧`add_land_transport`把所有残余都接oil（U/scripts/prepare_sector_network.py:2520–2533）；这不能成为研究接受的燃料分类。新规范中`ResidualRoadFuel`应为有carrier标签的向量，`ResidualRoadLiquidFuel`只是其中子项。若生物燃料可与液体燃料合并做能量平衡，仍须保留其来源/碳标签，不能自动当化石油。

允许两种等价的**账本实现表达**，不自动选择数值：

1. 接受一个非负燃料份额向量b_k，Σb_k=1，`F_k=(1−sE)R b_k`；每个b_k需明确为该目标年的外生账户。
2. 若现有gas/biomass/other已有被接受的固定目标量，保留它们，再令liquid成为剩余；须验证liquid≥0，否则情景不一致而失败，不能减成负数后裁零。

不要求新增天然气车辆/生物燃料车辆技术竞争；只要求原能源义务不消失、不改换燃料身份。上游未来CSV的gas/biomass/oil子项曾因列对齐缺失后fillna(0)而消失（Phase3B-1缓存审计）；因此不能使用这些未来零值证明可以忽略上述账户。

## 3. Historical EV 与 A*：概念包含已明确，数值包含没有证实

**逻辑边界：** 同国家、年份、统计范围和计量端的完整end-user final electricity parent应包括历史道路电力。若把被明确识别且已包含的历史道路电量h_EV单列，则：

`DirectElectricity = A* − h_Buildings_explicit − h_EV`

`DirectElectricity + h_Buildings_explicit + h_EV = A*`。

Rail本轮保持embedded，因此不再扣h_rail，不再创建一份rail电Load。h_EV应覆盖新显式账户所替代的同一历史电量集合，不能把现有总road electricity中的未知其他电力运输自动当成全部电池EV。

**直接证据的限度：** Phase3B-1缓存11国`road electricity=0`都来自空Electricity-road子集求和；原始2019缓存未发现任何Electricity-road记录。它们不能证实h_EV=0。且旧网络AC受Residential重写（U/scripts/prepare_sector_network.py:3405–3409）、通用损耗乘数（3452–3462）及final校准影响，不能只凭名字宣称是已闭合A*。

**未来处理：** 一旦采用外生R/sE得到目标年EVFinalElectricity，就应让未来direct电力账户排除同一EV目标需求，再由显式EV电账户加入一次。基年转移的h_EV用于历史闭合，不能把目标年EV电量从历史A*中直接减去；也不能把历史EV继续随direct账户增长后，又叠加完整未来EV总量。所需是共同的base→future父子账户追踪，不是新的车队微观数据研究。

**真实数值门槛：** 每国所用A*的覆盖证明及匹配的历史/目标年EV包含量未确认前，exactly-once只能作为已定义验收契约，不能宣称已对真实11国数据通过。若不知道，保留PENDING并拒绝生成重复负荷；不利用缓存空集零值绕过。

## 4. V2G=false、bev_dsm=false：可以关闭移峰，但不是完整安全组装证明

**直接源码结论：** U/scripts/prepare_sector_network.py:2471–2482仅在v2g=true时创建逆向Link；2484–2502仅在bev_dsm=true时创建EV Store。因此在**新构建网络**中同时关闭两者，可不创建这两类组件。修改config不会自动删除已经存在于旧保存网络中的组件，Phase4必须检查最终组装对象。

若EV Bus仅有正向charger和固定EV Load q_t、没有Store/其他流入流出，则每时刻能量平衡强制：`eta_charge × p_charge,t = q_t`。因此charger的调度变量没有可自由移峰的维度；没有DSM/V2G电池套利。这个结论有明确连接拓扑条件，不代表系统发电和其他储能也不优化。

**仍有两个工程条件：**

- Charger仍固定p_nom=车数×0.011×share，受availability上界（2449–2464）。必须满足`q_t/eta ≤ p_nom×availability_t`；关闭储能后可能暴露不可行。未经接受的车辆数/接入率不能成为首版aggregate transport的隐性新增约束。
- q_t仍由旧量纲错误链产生；关闭两个开关不修复它，也不去除三步平均。不能把“开关可关”写成旧模型可直接接受。

**与本轮选择一致的最小组装规范（不实施patch）：** 首版可以直接将接受的网侧EVFinalElectricity按简单非负归一曲线形成固定AC/low-voltage Load。这样不依赖车辆数、charger型式及availability容量约束，也不产生EV时间优化。若保留正向charger用于明确电池端计量，则必须让`q_battery,t = eta × p_EV_final,t`；否则把已经定义为网侧的EVFinalElectricity当电池侧Load，会再次除以eta而夸大网侧需求。0.9不是自动获批参数；直接网侧Load规范无需额外选择该效率。

故回答D：**可以在设计上安全defer；上游构造开关可关闭。** 真实组装仍要验证无EV Store/V2G、正确计量端和固定曲线守恒。没有证据支持“上游无法关闭，所以必须研究智能充电”。

## 5. Rail embedded：正确条件是保留总量，而非只有rail开关=false

U/scripts/build_base_energy_totals.py:203–222的road按road交易抽取，不含rail；rail在246–260另列。旧U/scripts/prepare_transport_data.py:172–180才把非电rail加入land proxy。新road-only R不应再复制这个合并。

本轮rail embedded规范可以成立，需要同时满足：

1. Rail electricity保留在被证明完整的A*父电账户一次，不转移、不新增独立rail电Load。
2. Rail各非电燃料保留在被接受的generic direct-fuel/transport-fuel父账户一次，并保留mode标签供碳及全系统报告追踪。**这个父账户不是新road-only R。** 若road与rail在源统计中本就分开，构造一个透明的合并父账户并显式记录各子项；此合并不代表新增一份能源。
3. Phase4不再调用新增独立rail Load的构造，或对已存在对象执行受测的互斥转移；只有核实父账户已经保留相同量，才删除独立对象。不能机械`rail_transport=false`导致rail fuel一起消失。
4. 原rail总量含diesel/biodiesel/electricity（U/build_base_energy_totals.py:246–260）；不得将biodiesel无标签化成化石油。缺原始rail字段仍PENDING，不当零。

旧`add_rail_transport`固定创建电/油Load（U/scripts/prepare_sector_network.py:3721–3739），但没有证明原父账户里已有它们；作者final删除oil也不能证明“fuel自动已嵌入”。当前证据足以冻结embedded的表示规范，不能确认全部真实国家已通过保量检查。无需铁路电气化、线路、列车或客货运竞争模型。

## 6. 可交接的最少门槛，不再新开Transport轮次

对本子任务范围，合并为两个Phase4系统门槛即可：

1. **共同年度父子账本与接受输入门槛：** R/sE的最终能耗定义与数值、EV历史/未来A*包含关系、road gas/biomass/other及rail电/燃料保留去向。每个非零或缺失义务有唯一身份，禁止默认零与燃料改名。现有材料尚未使真实11国数值闭合。
2. **采用新规范的组装验收门槛：** 旧代理转换不被调用；无重复独立rail；EV为固定正确计量端负荷且无DSM/V2G存储优化；相同输入在Integrated/Disconnected一致；国家年度电/燃料总量守恒。当前只定义了契约，未实施/验证实际研究网络。

这些门槛可以与主任务的航运航空守恒、power-policy碳scope隔离合并进入一个Phase4集成清单，不意味着继续Phase3B-3，也不要求更精细交通资料。车型、客货、charger型式、接入行为、轨道细节、DSM/V2G潜力均可留为明确限制。

最终口径应拆开：**Transport representation/specification可按用户决定冻结；实际数值/实现完全就绪不能由规范推导冒充。** 若项目定义`TRANSPORT_CLOSED_FOR_FULLSC_ASSEMBLY`表示所有实数据及工程八条标准已经通过，则当前证据不足给YES；若仅表示科学范围关闭并将指定集成门槛交接Phase4，必须另设明确字段，不能用一个YES掩盖未通过项。本子任务不替主任务修改全项目门控定义。
