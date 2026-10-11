# Baseline evolution ledger

日期：2026-10-11。审计分支：`audit/stage2-baseline-lineage-20261011`；实际源仓库基线：`b9be7d0ab788a4151346c098d2e657c7e94a22da`。此提交来自research/full-sc-baseline，不是Windows历史文档副本，也不是当前GitHub main。

| 阶段 | 状态 | 本轮边界/证据 |
|---|---|---|
| S0 | COMPLETE_LOCAL_EVIDENCE | Git身份、干净源码工作区、上游提交对象/远端参考、两次终态与执行hold，见evidence/S0_STATE.json |
| A-01 | COMPLETE_WITH_EXPLICIT_UNKNOWNS | 上游论文、Sector Coupling及当前Full-SC差异总账 |
| A-02 | COMPLETE_WITH_EXPLICIT_UNKNOWNS | 807固定资源Store谱系与异常生成路径 |
| A-03 | COMPLETE_WITH_EXPLICIT_UNKNOWNS | 385组/807账户静态端口、111↔377逐组联结、精确源常数闭合；见FINAL_OBLIGATION_BUS_IMPLEMENTATION_AUDIT.md |
| A-03精确LP补证 | FULL_LP_EXACT_INFEASIBILITY_CERTIFIED | 一次CSC结构扫描闭合26,284行完整支撑；精确线性组合给出0≥513/34359738368>0；见A03_EXACT_ANNUAL_CLOSURE_PROOF.md |
| A-04 | COMPLETE_WITH_EXPLICIT_UNKNOWNS | 171需求账户→1737 Load、108 NULL边界、A*及部门需求谱系；见A04_DEMAND_LINEAGE_AUDIT.md |
| 精确源常数闭合修复设计 | DESIGN_COMPLETE_A_APPROVED | 历史A/B/C设计保留；方案A现获批准并完成独立实施，见下列新状态及implementation_a_v1证据 |
| 方案A受控实施 | SCHEME_A_STATIC_ACCEPTED | 独立源版本180Q×4字段；385/385精确D≤Q′、1737 Load不变；implementation_a_v1/报告及回执；未构模/求解 |
| A-05 / A-06 | PLAN_ONLY_SCOPE_TO_BE_CONFIRMED | 用户列为实施后剩余审计；本台账此前未明确细分定义，本轮不自行补造或启动 |
| B | PLAN_ONLY_NOT_AUTHORIZED | 物理约束与输入数据一致性审计；未执行 |
| C | PLAN_ONLY_NOT_AUTHORIZED | 365日时间分辨率诊断；未执行 |
| D | PLAN_ONLY_NOT_AUTHORIZED | 完整2920时段Gate6科学验收；未执行 |
| E | PLAN_ONLY_NOT_AUTHORIZED | 跨境氢气及其他能源载体扩展；未执行 |
| F | PLAN_ONLY_NOT_AUTHORIZED | 可比的互联与独立运行成本实验；未执行 |

证据等级：VERIFIED=原件/代码/已核SHA直接支持；DERIVATION=列明假设的解析推导；RISK=有路径但未证明发生；UNKNOWN=缺证据。不得将资源耗尽候选解解释为已经证明原模型不可行。

发布记录按S0、A-01、A-02分别提交与推送；commit自身不能含其尚未产生的commit SHA，最终发布回执及后一里程碑记录前一commit。禁止force-push、main直写、模型改动、上传大矩阵/向量/凭据。

## 已发布里程碑

- S0：`623e734658973dd438af96a4944f605befa9ec2e`，已推送审计分支；源码和历史结果未改。
- A-01：`97bf63d6b5a59f5f8410dabe12c73c6a39fd7424`，已推送；22类差异、217项指定范围路径清单及源文件SHA索引。
- A-02：本提交完成807/385来源、2条原始UNSD行SHA/数值核对、库存与Bus行的生成路径；复用既有完整残差，不重扫CSC。

## A-02历史结论与交接（保留当时状态）

1. 三个源基准、当前Git基线、冻结NetCDF构模版本与后续数值表达已分开；源码文件身份见证据索引。S0所记远端当前进程未复查的限制继续有效。
2. 807账户是61源行→33国家/部门输入→385节点义务组的展开；继承库存数学机制，但替换上游资源潜力与可选用途边界。原公共生物质Store未在冻结网络并行保留。
3. 277644库存下界行、324120Bus行与377失败账户的候选违约真实；最大Bus残差所在为生物质最终义务Bus，不是电力AC Bus。没有认定整个LP不可行，也没有找到可直接修改模型的已证实致因bug。
4. A-03：具备限定静态审计的证据基础，**NOT_STARTED_AWAITING_REVIEW**。需审议固定消费账户还是独立资源供给、商品/时空代理的适用范围，以及精确舍入闭合的处理原则。没有新优化授权。
5. 后续B—F未定义/未启动；G6-05暂停。第一次OPTIMAL / V4 NOT_ACCEPTED、第二次INF_OR_UNBD、历史消费标记及未全同步归档状态不改。

本轮验证边界：源码与小型JSON SHA、固定commit/代码位置、NetCDF静态元数据、2份合计约5.03MiB原始UNSD文件SHA及2行原值；未重建模型、未调用求解器、未重跑既有实验或全量数值审计、未连接AutoDL。新文件仅审计文档与小型证据，禁止自行合并PR。

## A-03完成记录（前轮，保留当时状态）

前一审计HEAD：`08d4d3a74d7844d9bcf8d3b3ae6db7796a32b3d8`，分支与工作区已核实干净；继续原PR #3。本次commit由最终发布回执记录，不捏造自身SHA。

- 385组均单Load、独占最终Bus，807个固定Store/meter逐项通过指定拓扑与字段核对；没有重复Load、旁路、方向或权重异常的直接证据。
- 111失败组恰好是67×3与44×4共377失败账户，其他274组430账户通过；111×2920=324120 Bus失败行。资源超用与过供是关联违规，不能相加。
- 冻结binary64常数精确闭合：180正差、205负差，最大绝对差9.816722013056278e-8 MWh，与先前精确源核算一致。未知完整LP精确可行性及第二次INF_OR_UNBD因果，未擅改Q。
- 作者两份真实结果网络的静态表已核对：均无最终生物质Load，保留360TWh公共solid biomass Store与电力EOP；与通用上游SC工业终端Load、当前Full-SC独占账户分开。
- 新报告：`FINAL_OBLIGATION_BUS_IMPLEMENTATION_AUDIT.md`。新增轻量证据含385组及807账户联结、作者结果拓扑、摘要及SHA来源索引。复用旧X/矩阵独立残差，无全矩阵或原始向量重扫。
- G6-05为PAUSED_BY_USER，未连接AutoDL、未调用求解器、未修改科学代码或历史消费标记；远端当前进程状态未重新检查，不能冒称实时确认。
- B—F范围按用户本次指令补齐，仅记录计划。A-04及任何后续阶段没有启动。
- 同轮提交推送审计分支，自动交付`A03_BASELINE_EVOLUTION_REVIEW.zip`，含报告/台账/轻量JSON及清单、大小、SHA；CRC和成员完整性检查，最终回执记录ZIP与commit身份。用户上传ChatGPT联合审阅后再决定下一阶段。

仍待科学判断：固定终端核算的适用结论、消费数据/商品与时空代理的一致性，以及精确源常数舍入差未来如何受控处理。本轮不授权任何相应变更或计算。

## A-03局部补证与A-04（前轮，保留当时证据边界）

前轮A-03提交`788257a647952685ac1c2007467cbf24d676a84f`已由用户审阅；本轮继续同一审计分支及PR #3，起始工作区干净。未改科学源码、输入或历史结果。

- VERIFIED：指定ID工业Java-Bali1 2组实际CSC局部列/行界给出精确`D−Q=513/34359738368 MWh`。读取35,040列、128,476项，未全矩阵扫描。
- DERIVATION/BLOCKED：若所列行没有遗漏项，动态+3资源Bus+3最终Bus导出`−Σe_T=D−Q>0`，与`e_T≥0`严格矛盾。但没有所选行完整支撑证据，不能宣称完整冻结LP严格不可行。最小缺项在A03_EXACT_ANNUAL_CLOSURE_PROOF.md；不需要新求解来补结构证据。
- VERIFIED：A04已批准171账户对应1737唯一Load，全部owner和实际目的Bus国家/carrier匹配；没有正账户缺失、单列电力子账或PRE_FINAL正目标被置0/NULL。年度最大绝对浮点差2.384185791015625e−7 MWh。
- SCIENTIFIC_ASSUMPTION/UNKNOWN：108未入模账户全部NULL，其中15缺报边界不能认作真实零；A*父账、增长/空间/时间代理及最终能源固定边界已溯源，但未证明全部统计覆盖或服务等价。
- 本轮交付A03_EXACT_ANNUAL_CLOSURE_PROOF.md、A04_DEMAND_LINEAGE_AUDIT.md及轻量JSON；更新差异总账。源commit/path/行号和文件SHA经发布核查。
- G6-05继续PAUSED_BY_USER。B—F仅PLAN_ONLY_NOT_AUTHORIZED；没有连接AutoDL、调用solver、构模、调整容差或清除消费标记。未重新核实远端当前状态，不冒称实时进程确认。
- 同轮commit/push及A03_EXACT_A04_DEMAND_REVIEW.zip；ZIP保留相对路径、附大小/SHA清单并验证CRC。最终发布回执记录新commit及ZIP身份；请用户上传ChatGPT联合审阅。

剩余事项限定为完整所选行支撑和科学代理适用性的审阅，不自行扩展实验或恢复旧求解授权。

## A-03完整支撑与证书（2026-10-11本轮）

前轮提交`f885725569b35515beee081e4d583ef774c03c55`；继续原审计分支和PR #3。用户本轮明确允许最多一次冻结CSC流式结构扫描以关闭唯一行支撑缺口；A-04不重复、不改动。

- VERIFIED：MATH/MAPPING/FIDELITY绑定及12个数组SHA、dtype/shape匹配；坐标SHA复用并核对。没有原始文件变化。
- VERIFIED：一次扫描90,782,037个CSC存储位置，提取26,284行完整70,080项；无额外变量、无公式不匹配。13份行支撑JSON逐行保存原生系数、界和R，另存D及SHA。无全模型残差复算或稠密矩阵。
- VERIFIED：独立Fraction计算全部实际非零项；26,280条等式组合只剩4个终期库存系数，加入4条非负下界后所有列精确抵消，RHS为513/34359738368 MWh>0。结论FULL_LP_EXACT_INFEASIBILITY_CERTIFIED，关闭BLOCKED_FULL_ROW_SUPPORT。
- 边界：此为冻结binary64约束的精确数学证书；不改写第一次OPTIMAL/V4 NOT_ACCEPTED与第二次INF_OR_UNBD记录，不宣称已解释10.24TWh违规或Presolve因果。其他179个正差组未生成新证书。
- 仅提出源常数共同闭合的选项；没有选择/实施ΔQ、ΔLoad、放宽容差、负库存或免费补给。修复一份局部证书不证明新全LP可行。
- G6-05仍PAUSED_BY_USER。B—F未授权，不调用solver、不构模、不操作AutoDL、不清除历史消费标记。
- 同轮提交推送并交付A03_FULL_LP_CERTIFICATE_REVIEW.zip：报告/台账、目标行轻量JSON、独立校验器及提取源码；没有完整矩阵或X/Pi/RC。包含大小/SHA清单和CRC核验。

下一决策是源常数闭合原则的科学审批，不自动恢复G6-05或其他优化。历史A03/A04文件的当时未知项由本节明确更新，仅本证明缺口关闭。

## 精确源常数闭合修复设计（2026-10-11，PROPOSED）

起始提交`aa9437a71dfe2538fea56fe6687a75171d4a706b`，同一审计分支和PR #3。用户只授权设计、核算和比较，**没有授权修复正式输入或新的优化**。

- VERIFIED：复用385/807轻量映射，全部有理数δ与既有记录一致；1组完整LP证书、179组正差但未逐组原生证书、205组无正差。其余约束/机制不在本轮重审范围，不能宣称没有其他风险。
- VERIFIED_SIMULATION：A保持所有Load位不变，180个Q各增1–7 ULP，合计1.600385921563e−7 MWh，最大2.235174179077e−8 MWh；最大份额绝对变化1.775575033016e−16。全部385组精确D≤Q，0组D=Q；有限余量明示。5个Animal waste账户不变。
- VERIFIED_SIMULATION：B仅减180组平坦Load，年量绝对变化合计1.703564266216e−7 MWh；C共同量化方案改384组Load及806个Q，385组D=Q。全部逐项变更仅存在分析JSON，未进入正式输入。
- DERIVATION：独立位邻居校验A/B指定规则最小性；C配额精确闭合；指定无旁路拓扑下局部库存轨迹满足年度和所有前缀必要关系。不是新完整LP可行证书，没有逐组扫描矩阵。
- PROPOSED：采用EXACT_SOURCE_CLOSURE_A_MAX_ACCOUNT_V1_DRAFT，符合先Load后派生Q的历史权威顺序。明确改变库存常数/有限精确可行域，不将其称为无科学影响的等价缩放；商品份额及余量须经用户与ChatGPT批准。
- 顺序：科学批准 → 独立实施分支及源版本 → 全385/807严格闭合与字段回读 → 检查新增矛盾 → 剩余A-05/A-06及B审计 → 再判断365日诊断和2920时段Gate6授权。后续全部未启动。
- 文件：EXACT_SOURCE_CLOSURE_REPAIR_OPTIONS.md、PROPOSED_MINIMAL_REPAIR_SPEC.md、CLOSURE_REPAIR_ANALYSIS_METHOD.md、evidence/closure_repair/ALL_385_GROUPS_CLOSURE_LEDGER.json及A/B/C模拟/独立检查/来源索引。
- 旧A03完整证书、A04和科学源码未改；G6-05为PAUSED_BY_USER；无CSC/大向量重扫、构模、solver或AutoDL操作。未修改Q、Load、V3/V4、参数及历史消费标记。
- 同轮commit/push及EXACT_CLOSURE_REPAIR_DESIGN_REVIEW.zip，包含相对路径清单、大小/SHA及CRC核验；完成即停止，等待科学审批。发布回执记录本次完整commit与ZIP身份。

## 方案A正式批准与受控实施（2026-10-11）

前轮设计提交 `53c2b28632cb577136d48ebb843823967f0b1c25` 经用户与ChatGPT批准，本轮允许的科学变化仅 EXACT_SOURCE_CLOSURE_A_MAX_ACCOUNT_V1 的180项派生Q。原PROPOSED报告保留其历史语境，不回写批准状态。

- 实施分支 `fix/stage2-exact-source-closure-a-v1`，源版本里程碑 `fe4be3d25b7a5a7283a608c580085b26fa6b1f1e` 已commit并push；本次验收里程碑完整SHA由发布回执记载。新实施PR单独关联审计PR #3，不修改原审计分支或main，不合并。
- VERIFIED：新unbound recipe、807账户导出及immutable Load引用已生成。180Q各同步Store.e_nom/e_initial、routecap、外置QuantityMWh；627Q和5个Animal waste逐位不变；720项差异全部命中批准清单。
- VERIFIED：独立源回读385/385精确D≤Q′、0组D=Q′；1737Load×2920及三套权重保持原位。旧Java-Bali证书组新Q′−D=255/34359738368；旧证书对旧LP仍有效，未覆盖。
- DERIVATION：所有组全部前缀通过精确积分；按不变独占无损结构得局部库存非负解析轨迹，不是完整LP可行性证明。
- UNCHANGED：原科学源码/registry、成本和碳政策、技术效率、拓扑、NULL语义、原NetCDF及矩阵、V3/V4/P2、历史结果/消费标记；仅新源版本含已批准Q修订。新完整LP目标/缩放界为NOT_CHECKED，未构建。
- 版本Manifest SHA：`a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720`。目录 `research_inputs/derived/exact_source_closure_a_max_account_v1_20261011`；报告/证据 `research/05_baseline_evolution/20261011/implementation_a_v1`。项目总台账 `research/STAGE2_PROJECT_LEDGER.md`。
- G6-05继续PAUSED_BY_USER；A-05/A-06仍PLAN_ONLY_SCOPE_TO_BE_CONFIRMED，B—F保持PLAN_ONLY_NOT_AUTHORIZED。未运行solver、365日模型、Gate6或AutoDL操作。
- 同轮强制交付 EXACT_SOURCE_CLOSURE_A_IMPLEMENTATION_REVIEW.zip，含新报告、更新台账、轻量组件/JSON、脚本及路径/大小/SHA清单和CRC记录；发布后停止，等待联合审阅。

### 方案A真实发布记录

- 源版本里程碑：`fe4be3d25b7a5a7283a608c580085b26fa6b1f1e`，已推送。
- 三层静态验收里程碑：`bfd619df747bd94559137ff4f32ef7254c89a58b`，已推送。
- 独立实施PR：[PR #4](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/4)，base为审计分支，关联PR #3，OPEN/DRAFT，未合并。审计分支远端仍为原53c2b28632cb577136d48ebb843823967f0b1c25。
- 最终交付commit及ZIP指纹见包内PACKAGE_MANIFEST及本地交付回执；不写不存在的自引用SHA。
