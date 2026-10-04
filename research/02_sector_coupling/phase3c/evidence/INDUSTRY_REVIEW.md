# Phase 3C — Industry有限复核与冻结建议

日期：2026-10-03。只读复用已有证据；没有下载、重跑实验、修改模型或运行求解。此审阅区分直接证据、分析推导和首版架构建议。它不把任何新数值标为CONFIRMED。

代码身份：U=`a3616a68ee44592af6527ca9024a90f1956646ae`，P=`5bacad702ccfed17ad19ab510fa710651e966f2c`。本轮`source/U/scripts/build_industry_demand.py`、`build_base_industry_totals.py`、`build_industrial_distribution_key.py`由固定U Git blob取得，身份见`EXTRA_SOURCE_MANIFEST.json`；本次确认其文本与`research/00_source_provenance/current_source/`同名旧审计副本一致。下文网络构造行号引用`research/02_sector_coupling/transport/phase3b1/evidence/source/U/scripts/prepare_sector_network.py`。

## 1. 当前U最接近Mode A，附带供给与有限服务端选择

**直接证据：** `add_industry`从节点CSV读入MWh/year，将各列除8760生成固定Load。没有钢铁、水泥、化学品等完整生产过程的共同产品约束，也没有让优化器在各工艺间选择全国生产量的约束。因此当前整体最接近**Mode A：fixed carrier demand，加上若干供给/捕集选择**，不是Mode B。局部热端与H2/NH3供给具有Mode C式构件，但不足以把全部工业输入称为已验证的activity/service model。

| 输入或功能 | 直接源码行为 | 正确分类 |
|---|---|---|
| Solid biomass | 1890–1916固定能量Load；可扩张供给Link；1917–1935可选CC | 固定载体义务＋同载体CC选择；不是gas/electricity/biomass共同服务替代 |
| Gas | 1954–1997固定gas义务，普通/CC Link接同一个gas-for-industry端 | 固定gas义务＋capture供给选择 |
| Industrial H2 | 2002–2012固定H2 Load，受reference移除开关影响 | 固定H2商品需求，制氢路径可内生；不等于钢铁工艺选择 |
| Oil | 2016–2022全部industrial oil进入名为naphtha的固定Load；2029–2042计回排 | 载体聚合；组件名不证明所有工业油都是石化原料或具有相同碳滞留期 |
| Coal | 2045–2057只根据工业煤量生成CO2负Load | 工业煤能源义务未见相应Load消费；详见第6节 |
| Heat | 2062–2075固定heat义务连到urban central或services urban decentral heat Bus | 有潜在热供给替代接口，但输入温度/有用热口径尚未由列名证明 |
| Electricity | 2090–2098固定industrial electricity Load | 固定终端用电，必须同A*父账排重 |
| Process emissions | 2101–2142固定tCO2/year义务，普通/CC可选 | 固定排放及处理，不是能源需求或生产活动量 |
| NH3（配置开启时） | 2146–2207固定NH3输出Load、可扩张Haber-Bosch，以H2和电作输入 | 已有具体产品供给机制；首版是否需要必须服从DEFER边界，不能自动采用 |

一般heat模块已有热泵（2744–2767）、电阻热（2826–2838）、gas boiler（2841–2854）可扩张Link。它们的存在证明可复用的技术接口，不证明其Buildings参数/温度可直接代表任意工业过程。

## 2. 已有工业量是什么，不能变成什么

**直接证据：** 本轮U `build_base_industry_totals.py:28–87`把千吨/GWh/TJ等燃料/电力记录变成TWh后乘10^6为MWh；按country、carrier、UNSD工业交易分类聚合（:54–64）。这是工业**final energy**，不是产量吨、活动指数或useful heat。`build_industry_demand.py:129`的production_base只是全1表，后续乘增长因子、空间权重，再与能源表dot（:375–381）；变量名production不产生新的物理产量证据。

旧源码将heat列重命名为low-temperature heat（`build_industry_demand.py:384–389`），并不能证明原UNSD交付热量的温度等级。通用final fuel也不能不经过转换依据直接改成工业useful heat。原料用途、过程热、驱动电力应保留来源标签，不能为实现Mode C而任意重新分类。

工业过程排放另由设施capacity、利用率0.7及简化排放因子等估计（`build_industry_demand.py:164–177,194–291`）。它们的单位是tCO2/year；不得混进MWh能源守恒。此方法已知而非新发现的完整过程模型；参数接受与碳报告界限留Phase4输入决定，不本轮深挖工艺。

## 3. 第一版Mode C应冻结为“合格服务块可替代＋其余载体固定”接口

**架构冻结建议，不是已实现或已数值接受：** 采用有限Mode C目标；允许对少数可证明口径的工业服务块使用已有技术竞争，其余保持FIXED/EMBEDDED能源账户。这不要求完整工艺重建，也不要求本轮把未接受服务块强行激活。

### 最小共享服务端

每个可替代服务块至少带：`country / year / service_id / service_type / quantity / unit / delivery_point / temperature_or_quality / source_parent_ids / historical_inputs_transferred / allowed_existing_technologies / efficiency_cost_refs / evidence_status`。

以已接受热服务块为例（**公式推导，不提供数值**）：

`Σ_j Q_j[n,t] = Q_service[n,t]`，`Q_j = eta_j[n,t] × F_j[n,t]`。

Q统一为同温度/品位交付端的MWh_th，F为相应final electricity/fuel输入。优化器只在被接受、物理相容的现有技术集合中分配Q_j；不优化工业产品产量或虚构高温热泵/H2燃烧器。HP/电阻热/gas boiler仅在温度、成本和效率适配获接受时进入集合；现有低温热候选优先审阅，不等于默认将全部工业热归低温。

若Q由历史final fuel推得，必须记录被转移输入与其已接受基准效率/服务份额，`Q_base=Σ_k eta_base,k×F_transfer,k`；若来源本就是合格交付热量，则保留该交付端，不再重复乘末端效率。转出输入不再作为另一份固定义务。**这种服务守恒不是final-input MWh守恒**：未来不同技术的最终输入允许变化，物理输出服务应守恒。

### 哪些部分首版固定或嵌入

- 未分解的工业电力、油/气/煤/生物质及原料能耗：保留FIXED载体义务或经证实的父账户，不能未经证据全变heat或H2。
- 已接受的既有industrial H2商品需求：固定终端H2义务，由允许的国内制氢路径供给；同一服务不得再另造一份H2或预装制氢电力。只有源记录确实定义为产品/服务时才称相应envelope。
- 未有合格服务拆分的过程：继续fixed，不以完整steel/cement/chemical process model作为首版前提。
- NH3首版若DEFER：`build_industry_demand.py:301–344`仅在ammonia_enable=true时从chemical/petrochemical扣gas/electricity并新增NH3输出。应使需求生成和网络模块共同关闭显式NH3，让原chemical父能耗保留一次；不能删除整个化工需求，也不能扣了原能耗却不创建替代服务。该分支有max(0,current−deduction)剪裁；本轮不以剪裁结果作为守恒证据。

**防止Mode C标签误导：** 如果Phase4接受的可替代服务块为空，实际工业实现仍是Mode A＋供给侧选择，须如实报告。可以冻结Mode C接口目标并关闭Phase3设计，而不能宣称此时已实现非空、实证支持的工业服务替代。首次solve前只需确认哪些服务块真实激活或明确接受固定fallback，不要求重开工业研究阶段。

## 4. 增长公式与最小处理

**直接证据：** `build_industry_demand.py:21–22,103–130`使用

`G[c,i,y]=(1+g[c,i])^(y−base_year)`，`production_base=1`。

缺国家使用DEFAULT整行，缺列值使用DEFAULT对应值（:110–119）。当前`industry_growth_cagr.csv`只有DEFAULT、MA、NA、US，没有ASEAN国家行。DEFAULT中chemical=0.03、construction=0.015、food=0.02、iron/steel=0.017，多数其他行业=0.03；这些只是当前参数的直接读取，**没有变成已接受ASEAN预测**。

在归一化空间权重正确时，节点载体量应为：`E[n,k,y]=Σ_i alpha[n,c,i]×G[c,i,y]×E_base[c,k,i]`。未修旧权重不是自动归一；GDP候选修复解决分配，不验证G。

**最小Phase4接口决定：** 输入一份有来源或明确外生校准说明的country/industry/year增长因子表；或直接接受目标年载体/服务总量，绕开重复增长。已接受上游、AEO行业benchmark或透明校准均可作为候选，不能无说明采用DEFAULT；把基年平推也视为须接受的外生假设，不能装作“没有作假设”。具体选择标`PHASE4_INPUT_DECISION_REQUIRED`，两种电网实验共享同一输入；本轮不搜寻“完美增长预测”。

## 5. A*与工业exactly-once

**直接源码证据：** `prepare_sector_network.py:2080–2088`虽有移除today's industry electricity注释，但循环只选择并检查load集合，未执行减量；2090–2098随后新增工业电力。`final_asean_adjustment`后续按行业份额重分配不能充当Research A*原始父子包含证明。

**共同契约：** 若h_ind是确实已包含A*且被显式工业账户替代的同域历史电量：

`Direct_retained = A* − h_Buildings_explicit − h_EV_explicit − h_ind_explicit`。

保留direct＋全部明确转移子账户应恢复原A*；Rail和Agriculture若嵌入则不另扣。工业服务转换产生的未来用电、制氢/FT用电不提前装入Direct。固定industrial electricity与heat/H2服务拆分必须有互斥source_parent_ids；历史电热若已纳入服务块，要从工业fixed electricity中转出一次，不能同时从A*和已经排除该量的工业父账各再扣一次。

工业燃料同理：转成服务块后不能原fixed fuel与service输入同时保留；未拆出的油/气/煤/生物质继续完整记账。物理能源计量和工艺排放分别验证。现有数据只支持建立这个验收合同，不证明11国数值已闭合。

## 6. 复用GDP候选、煤义务和重复热列：Phase4的同一守恒门槛

已有`research/01_baseline_construction/INDUSTRIAL_DEMAND_FIX_REPORT.md`及`INDUSTRIAL_RECOVERY_EVIDENCE.json`已经确认：旧GDP TIFF不覆盖ASEAN；同一全球NC可恢复有效空间数据；候选提交`a7a8f06b43f0dcce0dbd7005b989d8f73d142b81`在10国2019基年、572个数值单元格、48个既有节点上通过国家/载体/行业守恒，未施加growth。GDP实际年2015，不伪称2020；TL未分配。这些结果本轮直接复用，未重跑；它不是完整11国未来工业网络验证，也未自动合并Future Research Model。

**本次有界源码确认工业煤能量缺口：** 网络构造全文件对`industrial_demand["coal"]`唯一实际消费是2046–2057的排放计算；`spatial.coal.industry`仅在1081/1085定义，没有相应工业煤能源Load/Link。制氢coal-gasification与发电煤输入不替代此独立工业煤义务。`shift_to_elec`由Snakefile:1723传入`build_base_energy_totals`，config.default.yaml:807注明Residential/Services用途；本轮固定`build_base_industry_totals`、`build_industry_demand`未将工业煤转电。故不能假定“工业煤能源已自动被其他账户供给”。

首版保留工业煤时，Phase4须把该接受量明确接入固定燃料义务，并使燃烧报告恰好一次；不能只保留CO2排放而不购买燃料。该问题可纳入统一carrier-energy conservation验收，无需新增研究问题。

旧节点表重复`low-temperature heat`列、NaN传播与零填补已有`INDUSTRIAL_DEMAND_TRACE.md`证据；应在同一个组装接口要求唯一country/carrier/service键、有限非负量、缺失显式化、时空守恒，避免因为行业字段重命名覆盖另一列。本轮不修生产源，不重跑已有候选。

## 7. Timor-Leste：不默认零，不据未知量声称小

**已知：** 旧审计发现TL2019共79条UNSD记录，但没有当前工业分类所需条目；这不是国名完全失败，也不是证明工业消费为零。无法仅凭这些记录或GDP比例可靠判断其工业负荷对互联结果的影响方向和大小。故不作“TL规模小所以可忽略”的结论。

**最低首版处理建议：** TL工业显式分项保持MISSING、不开无依据的工业服务拆分；若被接受的完整TL direct electricity/fuel父账户已经覆盖未知工业用途，继续保留父账户一次并标`INDUSTRY_UNALLOCATED`。这使工业分类缺口不自动变成全ASEAN设计阻断。要证明的是父账户包含关系，而非强行估工业份额；不能将other随意改为工业。

若父账户覆盖也未确认，标`PHASE4_INPUT_DECISION_REQUIRED`：共同决定明确的不确定性处理/透明估计候选，而不自动填最终值。已验证GDP候选的missing-country报错应在显式工业子集上使用；TL排除显式模块须有记录的mask和保留父账户，不能删国家、填0或关闭报错后静默遗漏。这个合同可在Phase3冻结，数值选择交Phase4；不要求本轮证明TL影响小，也不要求重新搜集11国完整工业资料。

## 8. 最少交接门槛与设计收口

只需把本范围并入Phase4以下共同门槛，不形成新的Phase3D：

1. **输入决定与父子包含：** 已有10国原始能源量、增长处理、服务块资格及TL保留父账户决定；只激活有明确数量/单位/来源/允许技术的块，其余fixed fallback。技术成本库与工业需求统计分开，DEA不能代替工业需求。
2. **实际组装的能源/空间/重复验收：** 审阅集成GDP候选；唯一热列；煤及各燃料义务不丢失；A*/工业电/热/H2互斥转移；国家年度和节点守恒。旧工业输入全空必须修，但已有候选不必重新研究。
3. **共同碳与国家边界验收：** 工业直接燃烧/过程排放进入FullSystem报告，不自动污染原Power cap；工业增量用电引起的发电排放仍在Power cap。国家内载体供给不能通过全球共同工业/燃料Bus绕过首版跨境网络关闭。这与主报告碳/载体门槛合并，不另开工业政策研究。

这些均有影响电量、主要供能投资、燃料成本或国家互联比较的直接路径。设施精确位置、all_touched分配细节、全面工艺拆分、完美增长预测和TL行业细分不单独卡住Phase3。**Phase3可以关闭并进入Phase4 Assembly & Validation；这不宣称Mode C已经数值实例化或首个正式solve已就绪。**
