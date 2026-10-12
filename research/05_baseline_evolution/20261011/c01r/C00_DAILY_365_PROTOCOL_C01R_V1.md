# C-00：365日诊断协议 C01R V1

2026-10-12；版本 **C00_DAILY_365_PROTOCOL_C01R_V1**。仅电力Load有界binary64输入表示规则已获用户与ChatGPT批准；本协议实际表示验收 **C01R_REPRESENTATION_ACCEPTED**。**network_build_authorized=false / solver_authorized=false**。

父协议为提交`5d757c5a4a9dad965d9c7cbe6e55d486d167ff93`的C00_DAILY_365_DESIGN_V1，原文件SHA `8530ea85ac087c89adafa594f885d3fa83d54d5f0a4fdd87e643f4b2d8e9ec86`。原文和严格相等的历史决定保留在[原C00协议](../b03_c00/C00_DAILY_365_DIAGNOSTIC_PROTOCOL.md)。本版本完整继承其物理/成本/数值/运行设计；仅替换§3电力Load表示准入及相关验收说明，其他未来构建、原生/资源建议均不因此获得执行授权。

独立机器规则：[C01R_RULE.json](evidence/C01R_RULE.json)，SHA `49d85c8449b32bb1fbf972b564dacb70a12e918dee58e4678efc36f0c736b140`。C01曾提出的非负双字辅助表示**未被选用、未实施**；本协议不加入辅助变量、补偿供给或新的需求。


## 1. 四种对象与控制变量

| 对象 | Q及时间轴 | 现有资格 |
|---|---|---|
| 旧Gate6网络/LP | 旧Q、2920×3h | 旧精确不可行证书；首次Gurobi OPTIMAL/V4 NOT_ACCEPTED；P2 INF_OR_UNBD |
| Scheme A源配方 | 180Q获批微调、原2920 Load及全部权重未改 | SCHEME_A_STATIC_ACCEPTED；PR #4固定提交，未组装新网络 |
| 本协议未来日模型 | Scheme A Q、365×24h、下述受控聚合 | 未构建、未求解、未验收 |
| 未来完整模型 | Scheme A Q、原2920×3h | 另行授权，不在本轮执行 |

日模型相对旧Gate6同时改变Q源版本和时间离散；这不是时间分辨率的纯单因素实验。相对未来Scheme A2920模型才具备同源时间比较基础，本轮不安排其对照运行。目标仍为同一资产扰动**规则**而不是旧cost.npy逐位同一；尺寸和时间权重必然不同。节点、资产、供需归属、技术效率、成本单位、政策和跨境范围固定。日模型新原生维数不得声称等于19.57M/48.30M，也不硬猜等于八分之一。

## 2. 输入及日历

以Scheme A固定提交`8883de6fb3e15767c632ac92f535e8a423e90b69`及Manifest SHA `a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720`提取独立只读输入；不把审计分支缺少新源文件当作旧Q可用。新运行记录源配方、固定科学源码、依赖和派生适配器的SHA，保留旧文件。

保留现有非闰2013气象/形状索引服务于2050科学情景：2013-01-01至12-31，每日00:00代表完整24小时，365个有序无时区跳变快照。每个日桶恰有连续8个3h来源快照，不能用取样、丢弃或典型日替代。`objective=generators=stores=24`，三列各和8760，逐值写入NetCDF后回读。Bus瞬时功率平衡仍以MW或tCO₂/h表达，不能再乘24；能量累计和成本按所属权重乘一次。

## 3. 动态输入与精确年度量

对任一功率/流率序列v，定义有理数日目标 `v*_d=Σ(t∈d) Fraction(3)Fraction(v_t)/24`。容量因子同理；不能先舍入加总再称精确。日均不是每日总能量，MW与MWh不可混用。

**权威量与适用范围**：每条Load科学年度需求为原冻结2920时段的 `E=Σ Fraction(3)Fraction(p_t)`，保持权威且不修改。每日精确目标 `m_d=Σ Fraction(p_t)/8`。仅实际96条非平坦Electricity/Astar/electricity Load允许将m_d表示为最近有限binary64、round-to-nearest ties-to-even；以实际365日值计算 `E′=Σ24Fraction(p′_d)`。科学E、实装E′、逐日/年度表示差ΔE=E′−E及未来求解残差为四种独立账目。

**批准的三重AND门槛（逐资产）**：

1. A：逐日用精确有理数及相邻binary64值验证最近值；中点选有效位偶数。非精确m位于相邻L<U时，预算为(U−L)/2；精确可表示m采用左右相邻距离中较小值的一半，误差为0。在二进制数量级边界、subnormal及零处也按实际相邻值处理，不依赖isclose。
2. B：`|ΔE|≤Σ_d24b_d`，b_d为上述日预算。全程有理数，不能浮点累加估计界；不同节点的正负误差不能抵消后验收。
3. C：同时 `|ΔE|≤2e-9 MWh=1/500000000 MWh` 且 `|ΔE|/|E|≤1e-15=1/1000000000000000`。指定十进制阈值按精确分数比较。E=0时需ΔE=0且源序列有限、非负、合法；本次实际零年度Load为0条。

禁止任何向上/向下偏置、nextafter年度补偿、末日修正、跨Load转移误差、重算Q、减少需求、改权重或添加slack。每次未来日输入实际导出/回读必须满足同一值/身份和AND门槛；新增异常、SHA改变、超限立即C01R_NO_GO，不扩大阈值。

**本轮真实准入**：1737条Load中1641平坦、96时变电力；原本年度严格相等的1642条保持相等（其中1条电Load存在逐日舍入但全年恰好抵消）。95条有界漂移（52正43负）全部通过A/B/C，最大绝对差`159/137438953472 MWh≈1.1568772606551647e-9`。这取代父协议“所有电Load E′=E”的表示硬门槛，**没有把E′近似值重新定义成科学年度E**。

**不适用例外的对象**：全部1641平坦Load保留原binary64，年度E′=E；385生物质组继续逐组精确D≤Q′，807账户及180项Scheme A修订不变；Store.e_nom/e_initial、route cap、外置账四字段保持。不得给它们套电力表示预算。原本精确保持的Load不能出现新增漂移。生物质Load平坦，所以365×24=2920×3使年度量精确不变；日实际导出若改变相关常数即停止。本轮未组装Scheme A新网络。

**范围与解释**：本版本是365日诊断的输入表示准入，不是原2920时段LP的数学等价变换；时间粗化和受限舍入均需在日结果解释中披露。表示PASS不证明日模型或全年LP可行。只可申请C-02受控构建审查，不自动进入C-02/C-03。

**风光/ROR**：容量不改；日CF采用上述时间加权均值，记录每资产全年潜在发电小时Σ3CF与Σ24CF′。有理数聚合严格守恒；binary64序列化误差必须逐资产报告，且不得超过已计算的Σ24×半ULP(日精确均值)界。该界仅解释最邻近表示误差，不是放宽V4或更改科学潜力；不允许人为裁剪1+1ULP、删除全零候选或重标定总发电量。若要求每资产严格binary64等量而不接受该有界表示，应按Load同样NO-GO；本次继续沿用C00规定、C01已检查的表示预算，不机械套用电力Load的绝对/相对上限。

**水电**：40个SU inflow按流率日均，保持年度输入能量，使用同一可核算表示误差规则；22个ROR保留原容量/上界机制。spill仍为独立非负流率，保留实际PyPSA变量上界（原实现按入流约束）和`24×spill`能量项，不能把多余入流忽略、允许负spill或取消库存/发电界。原始efficiency、max_hours、固定/扩建容量、pmin/pmax保持；入流/CF是可用量，不能当必须发电量。

**其他动态参数**：未来预构建清单必须枚举所有非空time-series属性。只有Load.p_set、Generator.p_max_pu、StorageUnit.inflow已获上述聚合规则；若发现额外时变效率、边界、成本、e_set或运行义务，NO-GO并报告确切属性，不能用通用mean猜测。静态值及空表默认值原样。C01已对同一NetCDF的460 CF与40入流完成表示核算；本轮复用已核SHA证据。6条CF共44个源值1+2^-52的既有范围偏差仍明确记录，未裁剪；不得把表示预算PASS写成所有源CF严格≤1。

## 4. 跨日物理方程与粗化局限

按已核PyPSA0.30.3 `constraints.py:769–929`（源SHA及全文片段见B_FROZEN_SOURCE_FORMULAS）保留公式：

- Store：`e_d=(1−λ)^24 e_prev−24 p_d`；p正为向Bus放能。非循环首行按库实际实现使用e_initial常数，**不是凭空对初始常数再乘standing_loss**；后续行使用前状态衰减。807资源λ=0、非循环、e_initial=e_nom=Q′、库存[0,Q′]、discharge-only；不加e_last=0新义务，有限剩余按真实年度差保留。
- StorageUnit：`soc_d=(1−λ)^24 soc_prev+24(η_store p_store−p_dispatch/η_dispatch+inflow−spill)`；首行非循环常数处理同实际实现。40hydro+3PHS保持原cyclic标志、initial语义、max_hours×p_nom能量界、充放效率与非负流。hydro η_store=0仍为0，不能当作可充电库。
- 循环资产首日连接末日；非循环资产首日连接原初值。循环属性使初值不作为另加终态等式，不擅自强制两者。H₂/电池Store保留本来循环状态与Link端效率，避免Store和Link双计损耗。
- 全部Link多端口、Line/KVL、lv_limit、807方向、196电池容量耦合及其他实际约束家族保留；CO₂单位单独为tCO₂/h和tCO₂，不能与MWh求和。

标准24h离散不是旧8步递推的数学消元：非零standing_loss下，旧步内流的衰减几何权重与24×日均流不同；即使λ=0，也只控制日末库存，丢失日内峰值、充放顺序与各3h库存界。故日模型PASS不保证2920可行，也不保证储能/网络容量投资充分。不能补上新“修正效率”、删除约束或声称新可行域严格包含旧域；复杂时变/二进制舍入下不作该集合包含承诺。

## 5. 成本、FOM与原数值表达

复用经核的稳定资产扰动注册表及SCOPE_V3范围：12条双向DC/B2B、98 distribution grid的新增边际扰动为0；Atmosphere、807 Store+807 meter新增边际扰动为0，NULL商品价仍NULL；其他资产复用已分配delta，不能因时间数或排序重抽随机数。年度capital_cost/年化参数、真实燃料价格与单位不改；流率目标项为`24×(原marginal_cost+已冻结asset_delta)`，固定年度资本项不乘365或24；不再以每时段独立随机数生成噪声。

新日模型需重新生成原科学目标与V3规则派生目标，并分别按原单位复算；**禁止复制旧2920 V3 cost向量**。固定存量FOM参考8224491125.573893 EUR2020/年，通过原固定常数/固定列机制恰计一次；不能在capital_cost已有项目外重加FOM。历史V3 offset为−12788967.997821666 EUR；日版只有在相同资本资产、基准容量、扰动及公式逐项重算一致后才采用该值，不能无条件硬编码。Scheme A调Q涉及零价/被排除噪声账户，不填造资源价格。日模型与旧结果成本差同时包含Q、时序和求解精度因素，旧NOT_ACCEPTED成本只能作未合格候选参照。

数值坐标采用首次Gate6的固定库存组幂二归一化规则（非P2）：从已核历史group→scale清单按稳定组/资产身份绑定原scale；日版D/R按新行列标签生成，非组项1，α=1。`A_s=RAD, z=D^-1x, c_s=Dc, y=Ry_s, r=r_s/D`，原单位界和目标可逆验证，禁止直接复用2920数组。原`inventory_audit.py`含旧Q源链与日均形状假设，**不得原样运行并通过改Q来迎合它**；未来轻量适配器改用Scheme A版本引用与日索引，保留全部原物理检查，不使用历史source-roundoff预算覆盖V4。若历史group scales不能可信绑定，停止，不能自动改用P2或新尺度。适配代码与逐值原生交接尚未实现/执行，本设计不虚报其通过。

## 6. 实际参数与环境冻结

第一次真实`EFFECTIVE_MODEL_PARAMETERS.json`共154个数值项已逐字节核对BACKUP_INDEX，SHA `0a7875a902b6671b67e2b8707bdfa81b3407574e70aac32f4fb79d56f6d2dca1`；原件副本见[FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json](../b03_c00/evidence/FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json)。

| 参数组 | 日模型建议值（审批后才生效） |
|---|---|
| 作者基准 | Method=2, Crossover=0, BarConvTol=1e-6, Threads=4, Seed=123, AggFill=0, PreDual=0, GURO_PAR_BARDENSETHRESH=200 |
| LP数值/预处理 | NumericFocus=0, FeasibilityTol=1e-6, OptimalityTol=1e-6, Presolve=-1, Aggregate=1, ScaleFlag=-1, ObjScale=0, DualReductions=1, InfUnbdInfo=0 |
| Barrier及预处理细项 | BarHomogeneous=-1, BarCorrectors=-1, BarOrder=-1, BarIterLimit=1000; PrePasses=-1, PreSparsify=-1, PreCrush=0, PreDepRow=-1 |
| 其余LP/执行 | LPWarmStart=1（本次无warm start）、MarkowitzTol=.0078125、ConcurrentMethod=-1、IterationLimit/WorkLimit=1e100、ThreadLimit=0、UpdateMode=1 |
| 资源/日志 | SoftMemLimit=65十进制GB、MemLimit=1e100；OutputFlag=1、LogToConsole=0、DisplayInterval=5；独立持久LogFile |
| 唯一拟改保护量 | TimeLimit≤3600秒，取3600与剩余固定native截止的较小值；首次实际43199.999811410904秒作为历史，不复用旧绝对时间 |

上述全部在同一原生模型实际设置/回读。完整154项作默认快照对照：MIP/QP/tuning等非LP参数仍保留同版本默认，不把它们列为算法实验；TSPort等运行服务端口/新日志路径属环境元数据，记录实际值及差异，不强行绑定旧端口。任何其他LP相关值不同则NO-GO，不静默沿用P2的1e-9/NumericFocus3或未执行的G6-05 DualReductions0。没有另行参数试验或独立presolve。

环境建议固定Python3.11.13、Gurobi12.0.3（动态库SHA `af7c367e21efc6fe9d273f84cdc5dda3bf62edf8ddcb273be50be3b37a0cec3c`）、PyPSA0.30.3及历史生产依赖清单，记录实际NumPy/SciPy/Linopy等版本和源码SHA；版本差异先停止，不安装升级。WLS需未来生产worker安全绑定已批准路径并合法启动，当前仅复用历史成功，未访问许可证或云端。本轮未操作任何AutoDL；迁移后122资源与导入状态仅为用户陈述，本地C01R表示验收不依赖云端WLS，未来实际运行仍须新的现场准入。

## 7. 一次性执行预算建议（本轮不执行）

执行前需新授权明确允许一次日模型构建和最多一次GRBoptimize，不继承旧Gate6/G6-05授权。新RunID例模式`c01_scheme_a_daily365_<UTC>_<nonce>`，实际开始时生成，独占消费标记在调用前持久化。构建、原生载入、回读通过后在同一模型调用一次；不得先另做一次完整载入/优化。模型对象/源码/输入与参数Manifest绑定。

建议固定总上限9150秒（2h32m30s），从真实t0起一次冻结：

| 阶段 | 上限秒 | t0+绝对截止偏移秒 |
|---|---:|---:|
| Scheme A日组件组装、网络/LP构建及回读 |1800|1800|
| CSC载入/精确原生回读/参数 |900|2700|
| 原生optimize |3600|6300|
| 原生退出宽限 |120|6420|
| TERM升级宽限 |30|6450|
| 原始状态和合法向量保存 |300|6750|
| V4全部物理/KKT和NetCDF回读 |1200|7950|
| 封存/本地同步 |1200|9150|

提前完成某段不向后滚动增加后段预算；每段实际最长持续时间与表中绝对截止取更早者，剩余绝对总预算不延长。原生TimeLimit仅3600；非合格终态先保存，不自动retry、改参、改缩放、IIS或feasRelax。保护参数/阶段预算不同于首轮属于**资源控制差异**，须列入审批，不当作完全同环境试验。

建议复用已验证资源级别而不盲目缩容：有效cgroup至少90GiB、CPU配额至少4核、Threads4；RSS≤75GiB、余量≥12GiB、SoftMemLimit65GB、MemLimit保留默认；启动磁盘≥20GiB且根据估计构建文件/三向量/NetCDF/备份额外需要量复核，运行底线8GiB。文件规模若预算不足停止，不自动扩机或删旧档。首轮原生约3424秒，历史采样cgroup峰31.475GiB、进程树RSS采样和峰33.223GiB（共享页可能重复计数）、载入40.737秒是参考，**不证明日模型一定更快、内存恰为1/8或90GiB必够**。实际准入在未来本机cgroup全部祖先、CPU/磁盘/工具/独立保护链核查后才成立。无新费用门槛，记录单价×时间估算；不采购或操作实例。

独立supervisor+guard必须覆盖构建至封存，PID/ctime/PGID/SID/cmdhash身份校验、租约及总绝对deadline；浏览器/SSH失联不使云端计算失去保护；监督失效按已测E1–E4停止。异常先请求正常终止，宽限到点后仅对核实进程组升级，记录是否来得及合法返回向量，不保证SIGKILL后能取回解。RAW持久化后再进入独立后处理，验收失败不重算。云端原件、消费标记和日志保留；本地失败LOCAL_SYNC_PENDING，不覆盖历史。

## 8. V4在365日的绑定和最终验收

原批准V4 SHA `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f`不改。该JSON硬绑定旧48,301,938行/19,568,505列和V3向量，**不能原样当新模型验收身份**。未来新增独立`DAILY_V4_BINDING`：parent原SHA、Scheme A SHA、新维数/所有行列标签/365索引/目标身份及适配器SHA；仅尺寸/身份重绑，阈值、单位、reference和方程不得改变。需随日模型授权明确认可此身份适配；本轮未自动批准新契约。

**表示预算与V4隔离**：未来对实装日模型直接计算原单位物理残差（例如S−P_installed），按原V4阈值检查；另独立报告科学年需求E、实装年需求E′和ΔE。不得将ΔE从Bus/库存违约中扣除、和不同资产或日期的求解残差相抵，或给V4物理预算加上半ULP/2e-9/1e-15额度。对照科学年量的总差也需披露，不得藏在“修正后残差”里。原V4公式/阈值、807专用预算、385义务组和KKT均未改变；本轮不开发正式V4适配器。

先fsync原生返回码、Status/SolCount/质量/参数/日志及合法X/Pi/RC，独立SHA后再映回原单位。仅有Status=2不能PASS；SolCount=0或属性不可取时如实NOT_AVAILABLE，不造解、不启动无意义V4。

原单位全部矩阵/列界与工程方程使用`.001+1e-7×reference`，能量MW/MWh、碳tCO₂/h/tCO₂、输电MWkm各自检查；不合并不同单位。807账户`B_i=min(.001+1e-7Q'_i,1e-6Q'_i)`MWh；每期状态/所有365前缀、年度、终期、累计绝对状态残差、meter、负释放与超容量累积全部检查，不给每一天额外一份年度预算。385组过供/欠供分开累计，仅使用组内ΣB_i；保留资源商品间时序自由，不加新的固定逐日配额。counts与SHA严格相等；全部动态/静态物理家族、KVL、lv_limit、电池耦合、CO₂端口、储能/水电均覆盖，未知家族拒绝。旧1849项是覆盖参考，日版本按原资产家族重绑，不能未经运行声称同数测试已过。

KKT完全沿V4：`s=c−Aᵀy−r`；每列`|s|/max(1,|c|+Σ|Aij yi|+|r|)≤1e-6`，自由RC/非法端点乘子单独检查；`Σ|x s|/M≤1e-6`。数值对偶目标以有限行/列端点乘子构造，包含同一固定常数；互补L1/M及`|p−d|/M≤1e-6`，`M=max(1,|p|,|d|)`，所有绝对EUR误差同时报告。无限界不做∞×0。原/V3双成本及FOM/offset独立复算。此为浮点数值资格，不是严格有理数最优证明，也不证明未扰动目标最优。

NetCDF全部导出值及元数据逐值回读，对照保存向量、D/R与资产标签；BACKUP_INDEX包含全部实际新文件及旧大文件immutable references；逐文件SHA、云端seal、可用本地同步。科学门槛通过但保全未完成只报SCIENCE_PASS_DELIVERY_PENDING，不提前报完整日诊断PASS，更不叫2920 Gate6 PASS。

## 9. 结果解释与停止

日模型OPTIMAL+全部验收+保全只支持新日模型的数值科学资格；仍需另行决定2920原始时序是否值得测试。INFEASIBLE/INF_OR_UNBD等是该新表达的原生数值分类，不自动当严格证明；TIME_LIMIT/NUMERIC/MEM_LIMIT及验收失败也不等于数学不可行。必须先检查输入/适配是否符合本协议，再报告原单位违约家族，禁止通过减需求/补源/改阈值事后PASS。即使通过，也不得把旧Q模型和新日模型的差异全归因于时间分辨率。测试结束即停止，不自动进入2920、Integrated、Disconnected或DEC。

## 10. 版本与停止条件

本版本的Load表示修改来源为用户2026-10-12 C-01R明确批准；批准原文摘要/SHA及来源绑定见C01R_BOUNDED_BINARY64_APPROVAL.md和evidence。原协议未覆盖改写，旧严格相等NO-GO及95条漂移事实仍保留。独立验证器已从原NetCDF另读待检查量，用整数共同分母累加和整数IEEE754舍入复核；不是生成器自证。

当前唯一状态：**C01R_REPRESENTATION_ACCEPTED**。C-02构建未授权/未执行，C-03或任何Gurobi调用未授权/未执行；G6-05保持PAUSED_BY_USER。任何后续执行需用户单独批准，不能复用已消费Gate6或暂停的诊断授权。
