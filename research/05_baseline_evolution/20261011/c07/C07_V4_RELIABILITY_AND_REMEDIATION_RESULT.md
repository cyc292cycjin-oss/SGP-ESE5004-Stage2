# C07 V4可靠性核定与有限数值补救结果

**C07A：ORIGINAL_V4_FAIL；C07B：NO_QUALIFIED_SOLUTION。两次新增调用均已结束，全部新增原件及C06补齐归档为LOCAL_BACKUP_SHA_VERIFIED。** 没有修改正式V4或科学模型，没有第三次优化。仍为C阶段365日日诊断，不是2920时段Gate6通过。

证据等级：VERIFIED为原始机器回执/实际数组计算；DERIVED为明示假设下的恒等式；INFERENCE为机制解释；PROPOSED为未执行后续方向。主索引、逐账户/逐列数据及复核脚本均在本目录，原始大文件留在独立证据目录。

## 1. 真实调用与终态

- C07A：`c07a_daily122_20261012T162928Z_0d9301f2`；C07B：`c07b_daily122_20261012T163744Z_4250e585`。每次GRBoptimize返回码0、调用计数1，各自独立授权、Run、消费标记和固定7200秒窗口。
- A先合法OPTIMAL并保存完整X/Pi/RC，源SHA、154参数、精确交接、坐标映射、契约和NetCDF回读通过，仅原单位物理/局部KKT失败，且所有生产进程退出/封存完成，才启动B。条件证据包含在B的AUTHORIZATION及本轮调用台账。
- B在同一次原生调用内完成153次Barrier后进入Crossover：dual pushes与primal pushes完成，cleanup/uncrush后最终Status=3 INFEASIBLE、SolCount=0。Barrier中间“Optimal objective”不是最终状态；511,564次IterCount也不等于511,564次新增优化。无合法X/Pi/RC，不运行虚构V4。

| 指标 | C06 | C07A | C07B |
|---|---|---|---|
| Status / SolCount | 2 / 1 | 2 / 1 | 3 / 0 |
| Barrier迭代 | 143 | 153 | 153 |
| Simplex迭代 | 0 | 0.0 | 511564.0 |
| Runtime秒 | 282.17975401878357 | 281.12807297706604 | 343.2634060382843 |
| 算法变化（相对C06） | 基准 | 无；仅D/R变化 | Crossover 0→−1；D/R与A相同 |

B日志末尾显示push后Dinf约11.263173，cleanup从509,766迭代到511,562时出现PInf约9.69117e−4、DInf约1.9929e11，另有2次uncrush迭代。它是本次返回过程的直接证据，不能单凭该日志定位哪条科学约束不可行。Status3为数值求解器分类，本轮未取得严格Farkas/有理数证书；A也不是严格可行点，二者不能据此认定为Gurobi逻辑自相矛盾。

## 2. V4科学含义与原文核定

**当前V4定义在此冻结模型范围内有明确依据；本轮没有发现必须改变科学定义/阈值的实现冲突。主要未达标点仍是返回解的局部数值质量。** 这不宣称V4是所有能源模型的普适最优精度。详细A/B/C/D分类、单位、代码位置见V4_REQUIREMENT_TO_MODEL_REGISTER.json和LITERATURE_AND_VERSION_EVIDENCE.md。

|原文|实际支持|版本/实验边界及本轮采用范围|
|---|---|---|
|[Gurobi：How do I scale my model to improve its numerical properties?](https://support.gurobi.com/hc/en-us/articles/26284047605521-How-do-I-scale-my-model-to-improve-its-numerical-properties)，2025-12-22更新，Column/Row Scaling段|先选列单位，再使输入残差在物理意义上可忽略；内部ScaleFlag不替代建模者判断|支持按物理预算设计行尺度；不是每行误差或Barrier收敛保证。|
|[Gurobi Parameter Reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html)，BarConvTol、Crossover|Barrier停止同时涉及相对原/对偶可行性、目标差和互补性；Crossover包含push及simplex cleanup，0关闭，−1自动|当前网页为13.0文档；12.0网页未取得，故不冒称12.0手册。12.0.3实际支持和154项设置由本轮原生回读单独证明。|
|[Gurobi：Tolerances and Ill Conditioning](https://docs.gurobi.com/projects/optimizer/en/current/concepts/modeling/tolerances.html)，正文第1—5段|有限精度、病态性与求解质量；建议检查原始和对偶违约及互补性|支持独立核算，不提供本项目807账户1ppm预算，也不把任何数值Status当严格证书。|
|[PyPSA Troubleshooting](https://docs.pypsa.org/latest/user-guide/troubleshooting/)，Optimisation convergence & infeasibility|Barrier/no crossover可用于快速近似解，给出method=2、crossover=0及Seed示例|latest版本的通用建议，不是Full-SC科学验收标准。未采用页面中的裁剪、load shedding或IIS建议。|
|[Bröchin, Pickering, Tröndle & Pfenninger (2024)](https://link.springer.com/article/10.1186/s13705-024-00458-z)，Energy, Sustainability and Society 14:27，DOI10.1186/s13705-024-00458-z；“Automatically improving scaling”、实验设置及式(2)—(3)|正对角等价缩放、幂二可避免表示损失；比较Barrier及Crossover的效率与返回结构|实际Gurobi9.0.0、4线程；BarConvTol1e−6、FeasibilityTol/OptimalityTol1e−5，192GB实验节点；模型/规模与本项目不同。未报告本项目相同逐账户/逐列V4验收：NOT_REPORTED，不推定没有验证。只继承等价缩放与算法区分依据，不照搬容差或性能结论。|



固定资源Q是上限，不被改写成普遍“必须耗尽”的科学原则。但在当前独占、无损、非循环且终端Load固定的组内，完整平衡/库存等式给出ΣeT=ΣQ−D=Sg；eT≥0推出0≤e_iT≤Sg。Fraction核算385组均Sg≥0且Sg小于每个Bi，最大Sg=9.816722013056278e−8 MWh，最大Sg/minBi=4.673060929996528e−5。因此本模型近零终态/近Q年度释放是派生结果，不是临时添加eT=0。C06的23项少用不能由Scheme A源舍入余量解释，也不能独立忽略同组负库存。

一般原单位预算仍0.001+1e−7×reference；807账户仍Bi=min(0.001+1e−7Qi,1e−6Qi)，前缀、逐期和全年L1不每日重置，也不扣除C01R表示误差。局部stationarity归一化正是原V4的|c−Aᵀy−r|/max(1,|c|+Σ|Aijyi|+|r|)，没有另造宽松指标。固定变量/等式允许任意符号乘子；不存在端点须零对应乘子，自由RC须零；代码掩码避免0×Inf。

须区分物理等式与数值预算的依据：精确LP要求零残差，但不能从物理等式本身推导0.001 MWh或1e−6恰为唯一合理的工程精度。这些是已批准的项目数值质量要求，不是原始数据测量精度或文献普适标准。本次失败库存行的一般预算约为该账户Q的2.26e−10，明显严于账户Bi/Q约1.00e−7；这种双重门槛值得在未来科学决策中明示，却不构成实现自相矛盾。本轮仍执行两者的交集。即使单独讨论该库存行的精度，另有3353列stationarity及12045自由RC未达标，不能仅放宽这一条就宣布科学通过；没有启用任何替代阈值。

全局目标差、互补L1和加权stationarity L1仍以含固定项max(1,|P|,|D|)归一化，门槛1e−6，并披露绝对EUR值。这是浮点认证，不是严格最优区间。C06两个固定目标列加offset合计2,594,498,284.5356255 EUR，去全部固定项尺度425,419,710,269.86273 EUR，正式尺度428,014,208,554.3984 EUR；绝对差不变。不存在通过改offset稀释误差的处理；未建立或启用V5。

## 3. 同一数学问题、唯一D/R表达与原生交接

日模型2,450,005列、6,042,238行、11,403,496非零；CSC、行列次序、科学目标及V3微扰、Scheme A、C01R、父V4均不变。原数学Manifest SHA `f70b2dc2dfc79e5b7caadc22beb30b82520a91b1aabf3dd720962af120302a70`，日V3 cost `c9a9717c664e2b3d5d4ca9b56848097f5231823465516113a13e00cb8f632d83`，日V4 `8c48d0735e6dcde870fdff589915aba57b55870994e75bc04b76d39e41c38459`，父V4 `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f`。

唯一表达C07_DAILY_RESOURCE_BUDGET_POW2_V1，绑定SHA `5561a91045ca9196183e6d4ae61c9dde76d85343e8397d880b5c4652a6b5e77f`；α=1，offset −12,788,967.997821666 EUR不变。D指数SHA `e1b8ae22033efd37737b99c77d05d91b73fc868e5787ceef4dc76347b1971ba3`；R指数SHA `cba72671b366f0e0cfbc7941ac36dea7896eb5ef10378d167a07d136ec41d2c5`。改884,472个D和2,203,217个R，指数范围分别[−17,12]/[−12,17]。

以τ=1e−6、N=365、H=8760、设计安全因子8，资源能量行R_e=2^ceil(log2(8τN/Bi))，流量/Bus行R_p=2^ceil(log2(8τH/Bi))；对应Store-e与Store-p/meter/capacity列D分别取倒数，组Bus按最小Bi选择。覆盖全部807/385，不只改历史失败资产。普通列D≤64、普通行R≥1/64，两个固定目标列不变；这是一套数学等价坐标，不是更改算法参数或科学预算。

全量binary64反变换逐值通过，保持±0/无穷语义、自由界、行方向、无非零下溢或溢出，结构与索引原样；新系数非零绝对值0.0012500829394132243—32768。目标固定项仍达8.22449e9，最大固定列界5.61720e9，未为缩小范围做消元。设计预算RBi与τ的比较只是输入表达参考，不能保证Barrier相对停止或累计残差必过V4。

本机静态接口10项正反例和全量恢复通过；真实12.0.3 WLS环境启动通过。A/B各自同一原生模型完整载入与逐值回读，耗时6.289524/6.408310秒；17,369项不可变输入SHA核验。154项参数A对C06差异0，B唯一Crossover0→−1；TimeLimit3600、SoftMemLimit65十进制GB、MemLimit1e100。全部基底参数表随包公开，不只列7项。

新RAW原生X/Pi/RC先fsync/SHA，再以z_old=(Dnew/Dold)znew、pi_old=(Rnew/Rold)pinew、rc_old=(Dold/Dnew)rcnew映射到独立旧V4坐标目录。未覆盖原生数组或重贴旧质量属性；原V4代码和阈值复用。没有重建网络/LP、CSR→CSC、warm start、独立presolve、IIS或feasRelax。

## 4. 原V4结果与C06定量对照

| 原V4门槛 | C07A | C07B |
|---|---|---|
| native_optimal | PASS | FAIL: Status=3 |
| complete_primal_dual | PASS | NOT_AVAILABLE: SolCount=0; V4未执行 |
| full_matrix_and_column_bounds | FAIL | NOT_AVAILABLE: SolCount=0; V4未执行 |
| independent_KKT | FAIL | NOT_AVAILABLE: SolCount=0; V4未执行 |
| physical_dynamics | FAIL | NOT_AVAILABLE: SolCount=0; V4未执行 |
| 807_inventory | PASS | NOT_AVAILABLE: SolCount=0; V4未执行 |
| 385_obligations | PASS | NOT_AVAILABLE: SolCount=0; V4未执行 |
| FOM_once | PASS | NOT_AVAILABLE: SolCount=0; V4未执行 |
| NetCDF_exact_readback | PASS | NOT_AVAILABLE: SolCount=0; V4未执行 |
| daily_binding | PASS | NOT_AVAILABLE: SolCount=0; V4未执行 |

| 原单位/原V4指标 | C06 | C07A | C07B |
|---|---|---|---|
| 矩阵失败行 | 243 | 1 | NOT_AVAILABLE |
| 矩阵最大库存违约 MWh | 54.83195485051556 | 0.008419696565397317 | NOT_AVAILABLE |
| 列界失败 | 0 | 0 | NOT_AVAILABLE |
| 资源失败账户 /807 | 85 | 0 | NOT_AVAILABLE |
| 义务失败组 /385 | 0 | 0 | NOT_AVAILABLE |
| 年度正向账户超用 MWh | 307.6417865795645 | 0.008435466259000712 | NOT_AVAILABLE |
| 年度少用绝对量 MWh | 304.6236235408966 | 0.007735670746664036 | NOT_AVAILABLE |
| 最大账户误差/自身预算 | 见C06原表 | 0.018995553597027242 | NOT_AVAILABLE |
| stationarity失败列 | 3336 | 3353 | NOT_AVAILABLE |
| stationarity最大归一化 | 2.7573625480333517e-05 | 2.2800298682587562e-05 | NOT_AVAILABLE |
| 自由RC失败 | 0 | 12045 | NOT_AVAILABLE |
| 全部对偶符号失败 | 0 | 12045 | NOT_AVAILABLE |
| 互补L1 EUR | 29.53246018208337 | 30.351564361038676 | NOT_AVAILABLE |
| 最大互补项 EUR | 1.0581741502357782 | 13.203852825433314 | NOT_AVAILABLE |
| 加权stationarity L1 EUR | 120113.44151863272 | 118539.95025643983 | NOT_AVAILABLE |
| 原对偶绝对差 EUR | 117699.0634765625 | 116267.10968017578 | NOT_AVAILABLE |
| 相对目标差 | 2.749886829086506e-07 | 2.7164310744169275e-07 | NOT_AVAILABLE |

| 组内账户数 | 组数/账户数 | C06失败账户 | C07A失败账户/组 |
|---|---|---|---|
| 1 | 118/118 | 0 | 0/0 |
| 2 | 156/312 | 0 | 0/0 |
| 3 | 67/201 | 61 | 0/0 |
| 4 | 44/176 | 24 | 0/0 |

C06的85个失败账户（62超用/负库存、23少用/正终态）在A全部通过，原377/111集合没有新增账户或义务失败；1/2/3/4账户组均无失败。年度总的微小gross误差仍如表披露，不能把它们写成精确零或与少用相互抵消。A仍有一条非合格库存行：row=3455225，label=3459290，资产/时间`{'snapshot': '2013-12-31 00:00:00', 'Store': 'TH:2050:Industry:IndustryFinalEnergy:biomass@TH2 3 Biogases fixed resource'}`，违约0.00841969656539732 MWh，预算0.00100000084196966 MWh。该账户Q=4,422,461.756462411 MWh、Bi=0.4432461756462411 MWh；同一库存值可通过账户Bi门槛，却不通过约0.001 MWh的一般行门槛。两项是正式V4并存的独立检查，没有把更宽的Bi覆盖一般行规则。不是“其他非固定Store”的失败。

stationarity分类：{'Line-s': 3024, 'Link-p': 329}；相对C06保留3316列、解除20列、新增37列。全部对偶符号分类{'Store-p': 12045}，其中自由RC 12045项。不能只报告旧失败消失而忽略新失败。明细含完整列号/资产/时段，不输出大向量。

本轮独立核算只遍历一次现成11.4M日CSC来分类全部返回列，未扫描历史全年矩阵；用保存activity/预算分类全部行。另对533个局部完整CSR行、7个完整CSC列使用Fraction核验原单位、旧坐标与新坐标残差恒等；均精确相等。代表列给出γ_(2k+4)算术误差上界，假定无溢出/渐进下溢及通常binary64运算，不是模型条件数或求解误差保证。见C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json，不把浮点差异归咎于坐标回映射。 审阅JSON保留全部533行的精确结果摘要、7列核算及关键库存/各家族最大残差行的完整支撑；其余完整支撑留在12,737,224字节的本地原始核算记录，附准确路径、SHA和逐支撑哈希。此处仅压缩公开表示，未重算、改变或省略失败结论。

A的已知范围原科学成本427765321341.481689453 EUR，V3复算428014092431.824890137 EUR，扰动贡献248771090.343081653 EUR，FOM一次计量复算差0.000119030475616 EUR；均为未合格候选，不是正式系统成本。原未扰动目标最优性NOT_PROVEN，NULL费用未填零，FullSystemCostComplete=false。B没有候选成本或双账数值，NOT_AVAILABLE。

## 5. 证据支持的解释与剩余阻断

VERIFIED：同一数学问题的表达变化改善了资源库存/年度数值质量；全部807/385通过，但局部KKT及同一固定账户的一般库存行仍失败。该行Rnew=1/128，0.008419696565397317 MWh对应新坐标6.577887941716654e−5，恰与原生ConstrVio对应。账户预算匹配没有保证更严格的一般行预算或Barrier返回点本身达到全部门槛。

原生DualVio=9.661775763684332e-07属于新坐标，不能直接与原单位比较。最坏自由RC位于Store-p列2047858，MM2 3住宅Biogases、1月1日；Dnew=2^−14，原生RC=6.6060390710395024e−9，原单位RC=1.0823334413991121e−4，精确乘2^14而得。实际表明这套偏重原始物理预算的表达并不同时保证自由RC原单位预算。不能用求解器小于1e−6的输入空间质量值替代V4。全局相对gap通过也不蕴含每个局部物理/KKT通过。

VERIFIED：A/B打印精度下的Barrier轨迹（除秒数）相同=True；B增加Crossover/cleanup后最终分类发生变化。没有B合法向量，因此不能断言它修复了A的库存或KKT，也不能将日志PInf0当作完整可行证书。

INFERENCE：预算匹配表达能改善一部分原单位误差，而原生停止/原模型恢复及cleanup仍有数值敏感性。当前证据不足以区分其他精确不可行性、预处理/恢复敏感性或某实现Bug；未找到可以只改验收代码就获得科学PASS的证据。旧Scheme A之前的严格证书不得移作当前日LP的证书。

**唯一下一步建议：以当前冻结日LP及A/B同表达、同参数除Crossover的成对原生回执，开展有明确目标的供应商数值复核。** 问题限定为“Barrier候选未达局部原单位门槛，Crossover/uncrush为何最终Status3”。不要再盲试1e−10/1e−12、NumericFocus等网格。现成原始数组、表达代码、154参数表、原生日志、完整回读/RAW和局部有理数残差构成最小重现资料规范；大模型为私有数据，未经用户批准不得对外上传。支持方若需重跑、写MPS或第三次优化，须新的明确授权，本轮不执行。

复现定位资料：源CSC三维及SHA如第3节；`release/c07_native.py`的唯一原生调用与`c07_expression_runtime.py`的输入覆盖；`release/expression/c07_expression.py`的精确幂二变换；A/B实际参数差异、日志cleanup段、A失败行/列及各坐标残差见本包。只读本地提取已完成；不把局部支撑子块单独冒称为等价可求解的缩小模型。

## 6. 资源、备份与最终停止

实际122号机12有效CPU、90GiB cgroup，Python3.11.13、Gurobi12.0.3。严格可信ED25519验证，WLS只绑定路径，未读取或公开密钥。独立supervisor/guard覆盖载入、RAW、验收与封存；RSS75GiB、余量12GiB、盘8GiB不变，启动盘≥20GiB并预留4GiB新增输出。A/B各固定7200秒，不滚动延期，均正常提前结束。

| Run | RSS采样峰值GiB | cgroup最小余量GiB | 磁盘最小余量GiB | 生产到封存秒 | 保护触发 |
|---|---|---|---|---|---|
| A | 4.045090 | 82.794861 | 26.219334 | 421.797037 | [] |
| B | 4.384937 | 81.819275 | 26.032654 | 362.053974 | [] |

RSS是进程树采样峰值；cgroup样本/生命周期峰值含同容器其他进程和缓存，不能当成Gurobi独占峰值。终态核实worker/supervisor/guard全部退出，sealguard退出0，无保护事件。122实例保持运行，未关机/释放，实例开机继续计费。

| Run | 归档字节 | SHA256 | 新增索引文件 | 本地状态 |
|---|---|---|---|---|
| A | 179260518 | 068c68e0ad0996391f86010815459b9659be8eac35bcaa38f210f06f24d1e594 | 61 | LOCAL_BACKUP_SHA_VERIFIED |
| B | 581722 | 4b80800da99e54c165ed0b28728c3c3ec98192eeab8f5e948b75adeef0886bc4 | 38 | LOCAL_BACKUP_SHA_VERIFIED |
| C06 | 153715959 | fcfb61920d094aec9cf84b755a25d5b589097d4842656fbc863b5e901cb56c07 | 53 | LOCAL_BACKUP_SHA_VERIFIED |

C06用新获批60分钟窗口在源SHA与140,640,256字节前缀一致后补收13,075,703字节；旧partial/过期窗口保留。C07另一个60分钟窗在最后云端封存后开始，只接收现成A/B新增归档；大小、整包SHA、gzipCRC、tar安全路径及逐文件BACKUP_INDEX全部核验。17,369项旧输入按C04已SHA验证索引及原绑定/大小/存在性复用，未重复拷贝。云端封存中的历史LOCAL_SYNC_PENDING字段不改写，新本地回执提供当前状态。

本地原件：`D:\ResearchWorkspaces\ASEAN\outputs\c07_daily_diagnostic\<run_id>\cloud_run`；云端：`/root/autodl-tmp/SGP/runs/<run_id>`。完整精确路径与SHA见C07_FINAL_BACKUP_STATUS.json和公开大文件索引。审阅ZIP只含轻量证据/代码，不是大向量归档。

本轮实际优化总数2，无第三次授权。原V4没有通过，不进入2920时段Gate6或Integrated/Disconnected/DEC；G6-05仍PAUSED_BY_USER。待用户与ChatGPT审阅后再决定唯一后续动作。
