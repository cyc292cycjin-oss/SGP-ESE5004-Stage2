# SGP ESE5004 Stage2 — C-05 单因素 Aggregate=0 日模型对照

**状态：待用户明确授权。本文不是可消费的授权文件。**

生效条件：用户明确确认执行本文，授权一次新的日模型优化、下列计算/封存窗口，以及下列独立本地备份窗口。仅上传C04报告或审阅本文不构成授权。若尚未确认，不启动远端操作或优化。

## 1. 目标与范围

C04已完成定向取证。下一项拟登记为C-05：检验现成365日LP的返回点质量是否对Presolve中的代数聚合敏感。

唯一算法变化：`Aggregate: 1 → 0`。这不是时间聚合修改，不合并资源账户，不删除物理约束，不关闭全部Presolve。

不再进行A/B/C01R复盘、不生成新的PyPSA网络或Linopy模型、不重新导出数学问题。允许把已经冻结的完整日CSC装入一个新的原生Gurobi模型；该步骤是现有数学问题的载入，不是重新构模。

用户确认后，把必要的最小入口适配、源身份检查、原生载入回读、一次优化、全日V4、云端封存、本地备份、对照报告和GitHub/ZIP交付合并执行。成功步骤之间不再申请普通审批；实际阻断时停止并报告。

## 2. 基准身份

原日模型Run：
`c02r_c03_daily122_20261012T044259Z_25e62c10`

实际生产代码提交：
`a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7`

已核C04审阅包记录提交：
`4b76dc65662faef61ff429d3a299cc7db8bccd9b`

读取C04实际证据，不以聊天摘要替代：
- `C04_DAILY_FAILURE_PATTERN_AND_NEXT_TEST_DECISION.md`
- `C04_NEXT_TEST_PROPOSAL.json`
- `C04_BACKUP_RECEIPT.json`
- `C04_RECEIPT_PATTERN.json`
- `C04_SCALE_CONFOUNDING.json`
- `C04_KKT_COLUMN_CLASSIFICATION.json`
- C03实际参数、日CSC Manifest、映射、日V4绑定、完整封存索引。

基准实际参数文件SHA：
`9514025d6234626f26d0f7dca7f9cf8070de4d24360a64429edbed790b9432a2`

复用日CSC Manifest SHA：
`f70b2dc2dfc79e5b7caadc22beb30b82520a91b1aabf3dd720962af120302a70`

复用日cost文件SHA：
`c9a9717c664e2b3d5d4ca9b56848097f5231823465516113a13e00cb8f632d83`

日映射Manifest SHA：
`f5bdb465709c0840ad9c370f121b5f23d31f62310300ad7e47208b0b9d6d746e`

日未求解NetCDF SHA：
`b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2`

所有其他数组、边界、标签、D/R和日V4身份从上述可信Manifest取得并核对，不猜测路径或复用全年数组。不得将文件SHA与不含NPY头的数组payload SHA混用。

旧C03完整本地备份已经核验，无需重新下载旧归档。前两次Gate6和C03的未通过结论永久保留。

## 3. 执行入口与实例

使用已确认的122号实例及当前可用安全连接；重新核实例身份、实际cgroup、CPU配额、磁盘和工作目录。不得依赖旧截图宣称实时状态。

创建独立Run/Release/授权/调用消费标记，复用已成功运行的C03求解worker、日桥接、V4和监督框架。不要使用会再次运行C02构建的旧合并入口；必要时分离solve-from-frozen-CSC入口，改动范围限于入口、路径和Aggregate覆盖，另存代码SHA及白名单。

核对没有同目的活跃任务后才启动；禁止删除旧消费标记或重复执行旧启动器。

WLS路径安全传入，原生环境启动成功后继续。许可证内容、密钥和令牌不进入日志。实际参数和环境验证失败时停止，不重装、换许可或静默替换版本。

不自动开关机、克隆、迁移、扩容或释放实例。不切换到无卡低内存环境求解。

## 4. 单因素参数冻结

Gurobi版本保持12.0.3。逐项回读全部基准154项非秘密数值参数；唯一算法差异为Aggregate=0：

- Aggregate=0
- AggFill=0（不等于Aggregate；保持原值）
- Presolve=-1
- Method=2，Crossover=0
- BarConvTol=1e-6
- NumericFocus=0
- FeasibilityTol=1e-6，OptimalityTol=1e-6
- Threads=4，Seed=123，PreDual=0
- 历史GURO_PAR_BARDENSETHRESH=200
- DualReductions=1
- ScaleFlag=-1，ObjScale=0
- 其他参数，包括InfUnbdInfo和BarHomogeneous，使用C03原值。

TimeLimit保持3600秒上限；因共享绝对截止而减少剩余预算必须单列为运行保护差异。LogFile、Run路径、绝对时间和授权等元数据可变化，但不得混入第二个算法变化。

不引入P2，不改D/R、目标、offset、时间权重、Scheme A、C01R、物理需求/政策或日V4。不把旧解作为新warm start，不启动Crossover。

生成并校验机器可读参数差异表；除授权差异外出现任一不一致，优化前停止。

## 5. 原生交接与单次优化

从冻结日CSC读取2,450,005列、6,042,238行、11,403,496非零元，逐值核对矩阵、行列界、方向、目标、ObjCon、变量类型和标签映射。

允许一次实际原生载入及同模型精确回读。通过后直接在该句柄上执行一次GRBoptimize；不再加载另一份模型，不进行小模型测试优化、独立presolve、IIS、feasRelax或其他求解器计算。

内部Presolve属于此唯一一次optimize的正常过程。

## 6. 运行保护与固定窗口

独立计算/云端封存窗口：从实际启动t0起最多7200秒。

固定阶段上限及累计绝对截止：
- 载入和回读：900秒；累计900。
- 原生优化：3600秒；累计4500。
- 原生退出及TERM升级宽限：150秒；累计4650。
- RAW优先保存：300秒；累计4950。
- 原单位恢复、日V4及后处理：1200秒；累计6150。
- 云端封存和收尾：1050秒；累计7200。

每阶段采用阶段时长与累计绝对截止取早；不滚动延期，不为了新阶段复位总计时。原生中断先沿已验证的受控终止链请求返回；所有强制终止必须验证进程身份，并如实记录无法取得向量的情况。

保持SoftMemLimit=65十进制GB，MemLimit=1e100默认；RSS上限75GiB、cgroup余量至少12GiB、启动磁盘至少20GiB且核实际输出空间、运行磁盘底线8GiB。CPU配额至少4核；有效内存及现有90GiB资源配置按真实实例验证。

关闭聚合可能改变Presolve保留规模、因子填充、内存和耗时，不以C03的155秒或旧峰值作为保证。保留独立supervisor/guard与结果优先持久化，不能依赖Codex会话在线。

## 7. 结果保全及完整科学验收

先保存真实GRBoptimize返回码、Status、SolCount、Runtime、迭代、实际参数、原生日志及合法可用的X/Pi/RC，完成fsync和SHA。原生调用返回码0不能替代Status。

SolCount=0或属性不可用时标注NOT_AVAILABLE，不能把partial数组当候选解。无合法完整向量不得伪造V4结果。

有完整可用向量后，使用未放宽的日V4执行全部原单位矩阵、列界、807资源账户、385需求组、动态/前缀/L1、局部stationarity、自由RC/对偶符号、互补性、目标差、原/V3双账、FOM及NetCDF回读。

不要只检查原来失败的377/111或4304/365集合：必须检查全部行列，检测是否新增失败。

输出相对C03的对照表：
- Presolve删除/保留规模、算法时间、Barrier迭代和原生质量属性；
- 1/2/3/4账户组分别的通过数、缩放Bus残差/账户数分布；
- 807账户年度正超用、负库存及相对于各自预算的最大倍率；
- 385组逐期/全年交付、正超供和欠供；
- 全矩阵超限数、各家族极值、是否出现新失败资产；
- 局部KKT最大值、失败列ID集合、自由RC及全局误差账；
- 原目标/V3目标、绝对EUR差，均标注资格与成本覆盖限制。

数值改善不等于PASS。只有OPTIMAL、全部日V4及规定保全通过，才能报告日诊断科学通过；不能称完整2920 Gate6通过。

## 8. 本地备份另设新窗口

避免再次把网络传输挤进计算封存阶段：7200秒覆盖计算、验收和云端封存，不承诺它包含完整本地接收。

只有用户在生效确认中同时批准本节，才在云端封存完成后开启**本次新的独立60分钟传输窗口**。这不是复用已经消费的C04传输授权，也不是延长优化期限。

先核已有完整本地文件；无需下载的内容复用其SHA证明。只接收本次新增状态、日志、向量、验收和封存文件；旧矩阵、未求解网络、D/R、目标等通过不可变引用复用，不重复复制旧大数据。

使用已可信连接，允许经源完整SHA与partial前缀核验的一次安全续传；不得盲目拼接或无限重试。完整接收后核SHA/CRC、安全路径及每份文件索引。传输窗口截止时保存partial并报告LOCAL_SYNC_PENDING，不删除云端原件，不重算。

本地离线核验可在传输结束后完成；不得因为备份未完成改写已经确定的科学失败。科学验收与备份状态分列。

## 9. 结论与下一步解释边界

- 全日V4通过：说明Aggregate=0在此固定实例上获得合格结果；支持该设置的实用性，不证明Gurobi存在bug或唯一根因。
- 资源模式明显改善但KKT仍失败：报告分层结果，日模型仍不合格；不自动收紧BarConvTol。
- 模式基本不变：该试验没有支持关闭聚合即可改善的假设；不外推为全部Presolve或数值处理无关。
- TIME_LIMIT/MEM_LIMIT/NUMERIC/INFEASIBLE/INF_OR_UNBD等：保存真实状态和合法结果，说明对照未取得合格解；不自动切换参数或恢复G6-05。

任何终态后停止，不自动第二次优化、其他精度组合、全年模型或正式情景。

## 10. GitHub、台账与完整ZIP

在正确的C03生产基线上建立独立C-05分支，引用C04审计结果；不得用审计分支代替未经核实的生产依赖。关联PR #13与#14，不合并main，不force-push，不改历史结果。

更新BASELINE_EVOLUTION_LEDGER、research/STAGE2_PROJECT_LEDGER及日模型GO/NO-GO表。记录实际Run、各阶段状态、SHA、资源和是否发生唯一调用。

同轮commit、push、创建或更新独立PR，返回真实commit SHA/链接；推送失败如实记录。

同一任务自动交付：
- `C05_AGGREGATE0_DAILY_DIAGNOSTIC_RESULT.md`
- `C05_SINGLE_FACTOR_PARAMETER_DIFF.json`
- `C05_BASELINE_RESULT_COMPARISON.json`
- 原生/日V4/封存及本地备份回执、最新台账、必要代码和轻量证据
- `C05_AGGREGATE0_DAILY_DIAGNOSTIC_REVIEW.zip`

ZIP包含相对路径、大小、SHA256及CRC清单；给出真实本地绝对路径。大型矩阵/NetCDF/向量不放入GitHub或审阅ZIP，使用实际产物路径及SHA引用。不含许可证、密钥、令牌或云端秘密。

本轮成功交付应是一次实际优化及其结果，或阻止其开始/完成的具体证据，不以PREPARED/PATCH_READY/LAUNCH_DISPATCHED作为最终求解成果。

---

## 用户可发送的生效确认

> 我批准按本文件执行C-05：复用现成日LP，唯一算法变化Aggregate=0；一次optimize，原生上限3600秒，计算与云端封存7200秒；另批准封存后的独立60分钟本地传输窗口。必要检查通过后连续执行，不重建、不重复审批、不自动重试。保留Scheme A、C01R、日V4及其他参数，GitHub和审阅ZIP同轮交付。旧G6-05、2920时段Gate6及其他实验仍暂停。
