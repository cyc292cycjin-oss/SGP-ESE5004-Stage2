# C-00：Scheme A 365日受控诊断协议

2026-10-12；设计版本`C00_DAILY_365_DESIGN_V1`，**PROPOSED / execution_authorized=false**。本文件及机器配置[evidence/C00_PROTOCOL_DESIGN.json](evidence/C00_PROTOCOL_DESIGN.json)供联合审批；不是启动脚本、求解授权或新的科学输入。本轮模型构建/求解/AutoDL操作均0。

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

**Load硬门槛**：逐Load保留权威年度量 `E=Σ Fraction(3)Fraction(p_t)`；新文件回读后计算 `E'=Σ Fraction(24)Fraction(p'_d)`，要求E'=E。385生物质组的平坦Load直接复用原binary64标量，`365×24=2920×3`，精确E不变；Q′不再重算或再次上调，385/807精确闭合、全部前缀与四字段同步必须重绑。所有其他平坦非电Load同样处理。96个时变电Load使用精确日均并检查序列化。

这里有真实的**表示门槛**：8个binary64值的精确均值未必能用一个binary64表示，甚至365个邻近日均值也未必能保持原年度精确和。不能把普通mean/isclose当守恒证明。本协议不预先加入需求缩减、末日补差、自动nextafter或归一化。如果逐日精确均值可以表示，则直接采用；若需要舍入，列明每日日均的精确差及半ULP界，并以实际回读的年度精确相等为放行条件。任何年度非零漂移为**NO-GO_REPRESENTATION**，输出受影响Load和Fraction差，等待一个具体的源表示决定，不启动优化、不调Q。此条件尚未对新数组执行，不能承诺所有时变Load已通过；这是一次组装门槛，不要求现在另开大规模实验。

**风光/ROR**：容量不改；日CF采用上述时间加权均值，记录每资产全年潜在发电小时Σ3CF与Σ24CF′。有理数聚合严格守恒；binary64序列化误差必须逐资产报告，且不得超过已计算的Σ24×半ULP(日精确均值)界。该界仅解释最邻近表示误差，不是放宽V4或更改科学潜力；不允许人为裁剪1+1ULP、删除全零候选或重标定总发电量。若要求每资产严格binary64等量而不接受该有界表示，应按Load同样NO-GO；此最邻近表示处理须随本协议联合批准。

**水电**：40个SU inflow按流率日均，保持年度输入能量，使用同一可核算表示误差规则；22个ROR保留原容量/上界机制。spill仍为独立非负流率，保留实际PyPSA变量上界（原实现按入流约束）和`24×spill`能量项，不能把多余入流忽略、允许负spill或取消库存/发电界。原始efficiency、max_hours、固定/扩建容量、pmin/pmax保持；入流/CF是可用量，不能当必须发电量。

**其他动态参数**：未来预构建清单必须枚举所有非空time-series属性。只有Load.p_set、Generator.p_max_pu、StorageUnit.inflow已获上述聚合规则；若发现额外时变效率、边界、成本、e_set或运行义务，NO-GO并报告确切属性，不能用通用mean猜测。静态值及空表默认值原样。当前B证据中的500个profile摘要是历史输入范围，不等同于新序列验证。

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

第一次真实`EFFECTIVE_MODEL_PARAMETERS.json`共154个数值项已逐字节核对BACKUP_INDEX，SHA `0a7875a902b6671b67e2b8707bdfa81b3407574e70aac32f4fb79d56f6d2dca1`；原件副本见[evidence/FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json](evidence/FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json)。

| 参数组 | 日模型建议值（审批后才生效） |
|---|---|
| 作者基准 | Method=2, Crossover=0, BarConvTol=1e-6, Threads=4, Seed=123, AggFill=0, PreDual=0, GURO_PAR_BARDENSETHRESH=200 |
| LP数值/预处理 | NumericFocus=0, FeasibilityTol=1e-6, OptimalityTol=1e-6, Presolve=-1, Aggregate=1, ScaleFlag=-1, ObjScale=0, DualReductions=1, InfUnbdInfo=0 |
| Barrier及预处理细项 | BarHomogeneous=-1, BarCorrectors=-1, BarOrder=-1, BarIterLimit=1000; PrePasses=-1, PreSparsify=-1, PreCrush=0, PreDepRow=-1 |
| 其余LP/执行 | LPWarmStart=1（本次无warm start）、MarkowitzTol=.0078125、ConcurrentMethod=-1、IterationLimit/WorkLimit=1e100、ThreadLimit=0、UpdateMode=1 |
| 资源/日志 | SoftMemLimit=65十进制GB、MemLimit=1e100；OutputFlag=1、LogToConsole=0、DisplayInterval=5；独立持久LogFile |
| 唯一拟改保护量 | TimeLimit≤3600秒，取3600与剩余固定native截止的较小值；首次实际43199.999811410904秒作为历史，不复用旧绝对时间 |

上述全部在同一原生模型实际设置/回读。完整154项作默认快照对照：MIP/QP/tuning等非LP参数仍保留同版本默认，不把它们列为算法实验；TSPort等运行服务端口/新日志路径属环境元数据，记录实际值及差异，不强行绑定旧端口。任何其他LP相关值不同则NO-GO，不静默沿用P2的1e-9/NumericFocus3或未执行的G6-05 DualReductions0。没有另行参数试验或独立presolve。

环境建议固定Python3.11.13、Gurobi12.0.3（动态库SHA `af7c367e21efc6fe9d273f84cdc5dda3bf62edf8ddcb273be50be3b37a0cec3c`）、PyPSA0.30.3及历史生产依赖清单，记录实际NumPy/SciPy/Linopy等版本和源码SHA；版本差异先停止，不安装升级。WLS需未来生产worker安全绑定已批准路径并合法启动，当前仅复用历史成功，未访问许可证或云端。本轮也没有确认379是否可用。

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

先fsync原生返回码、Status/SolCount/质量/参数/日志及合法X/Pi/RC，独立SHA后再映回原单位。仅有Status=2不能PASS；SolCount=0或属性不可取时如实NOT_AVAILABLE，不造解、不启动无意义V4。

原单位全部矩阵/列界与工程方程使用`.001+1e-7×reference`，能量MW/MWh、碳tCO₂/h/tCO₂、输电MWkm各自检查；不合并不同单位。807账户`B_i=min(.001+1e-7Q'_i,1e-6Q'_i)`MWh；每期状态/所有365前缀、年度、终期、累计绝对状态残差、meter、负释放与超容量累积全部检查，不给每一天额外一份年度预算。385组过供/欠供分开累计，仅使用组内ΣB_i；保留资源商品间时序自由，不加新的固定逐日配额。counts与SHA严格相等；全部动态/静态物理家族、KVL、lv_limit、电池耦合、CO₂端口、储能/水电均覆盖，未知家族拒绝。旧1849项是覆盖参考，日版本按原资产家族重绑，不能未经运行声称同数测试已过。

KKT完全沿V4：`s=c−Aᵀy−r`；每列`|s|/max(1,|c|+Σ|Aij yi|+|r|)≤1e-6`，自由RC/非法端点乘子单独检查；`Σ|x s|/M≤1e-6`。数值对偶目标以有限行/列端点乘子构造，包含同一固定常数；互补L1/M及`|p−d|/M≤1e-6`，`M=max(1,|p|,|d|)`，所有绝对EUR误差同时报告。无限界不做∞×0。原/V3双成本及FOM/offset独立复算。此为浮点数值资格，不是严格有理数最优证明，也不证明未扰动目标最优。

NetCDF全部导出值及元数据逐值回读，对照保存向量、D/R与资产标签；BACKUP_INDEX包含全部实际新文件及旧大文件immutable references；逐文件SHA、云端seal、可用本地同步。科学门槛通过但保全未完成只报SCIENCE_PASS_DELIVERY_PENDING，不提前报完整日诊断PASS，更不叫2920 Gate6 PASS。

## 9. 结果解释与停止

日模型OPTIMAL+全部验收+保全只支持新日模型的数值科学资格；仍需另行决定2920原始时序是否值得测试。INFEASIBLE/INF_OR_UNBD等是该新表达的原生数值分类，不自动当严格证明；TIME_LIMIT/NUMERIC/MEM_LIMIT及验收失败也不等于数学不可行。必须先检查输入/适配是否符合本协议，再报告原单位违约家族，禁止通过减需求/补源/改阈值事后PASS。即使通过，也不得把旧Q模型和新日模型的差异全归因于时间分辨率。测试结束即停止，不自动进入2920、Integrated、Disconnected或DEC。
