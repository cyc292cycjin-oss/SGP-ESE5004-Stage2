# SGP ESE5004 Stage2 — C-06：以C03为基准的Barrier停止精度对照

**状态：USER_AUTHORIZED_C06_SINGLE_SOLVE。**

用户已明确回复：“同意建议，给我codex指令”。据此，将前一版待批准方案落实为本次独立C06执行授权：一次C06优化、原生最多3600秒、生产全流程最多7200秒，以及云端封存后另行最长60分钟的本次结果传输窗口。本文件是供用户转交Codex的执行规范；本聊天没有连接实例或启动求解。

本版仅替代旧C06条件指令中的待授权/再确认条款；旧提案、C03/C05授权、结果及消费标记永久保留。收到用户转交后，在身份、原生交接、WLS及资源保护全部通过时直接执行，成功步骤之间无需常规再确认。不得扩大为第二次优化、更多参数组合或新模型构建。

**对照基准是C03，而不是C05。Aggregate必须为1；相对C03的唯一算法变化是BarConvTol=1e-9。**

## 1. 对照目标与基准

C03：`c02r_c03_daily122_20261012T044259Z_25e62c10`，Aggregate=1、BarConvTol=1e-6；Status=2、SolCount=1，物理及局部KKT未通过日V4。

C05：`c05_aggregate0_daily122_20261012T074925Z_a39647d9`，仅Aggregate=0；Status=12 NUMERIC、SolCount=0，无合法完整返回解。C05的物理/KKT失败数量是NOT_AVAILABLE，不是0。其证据与备份已收口，不再补下载或重复全量取证。

本次研究问题：**保留能返回候选解的C03聚合与数值表达，只收紧Barrier停止请求，能否改善返回点的原单位物理和局部KKT精度？**

唯一算法差异必须相对于C03计算：`BarConvTol: 1e-6 -> 1e-9`，Aggregate保持C03的1。
相对于C05有两项参数差异（Aggregate回到1、BarConvTol到1e-9），须同时披露，不能把C05当成单因素基准。

这不是从C03保存向量继续Barrier迭代；不使用warm start，不声称旧向量是检查点。不是证明1e-9必然满足V4，也不是处理C05 NUMERIC的已证实修复。

## 2. 冻结对象与来源

优先复用现有C03冻结日输入及C05已经运行成功的solve-from-frozen-CSC执行/保全框架，不调用PyPSA或Linopy重建，不重做CSR/CSC转换，不新建完整2920模型。

C03生产提交：`a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7`。
C05生产提交：`d6c48dbd95d12f0354561372e9a65d6e92511754`。
C05报告发布里程碑：`869d72a90376b1862cf2058576b01917131f0a12`。
C05交付包记录的最终导出提交：`54f23fdc7d78c3ef087806798b27d30369c6d961`。以上角色不同，不混写；实际使用前以Git/Manifest核对。

原云端输入目录：
`/root/autodl-tmp/SGP/runs/c02r_c03_daily122_20261012T044259Z_25e62c10`

既有本地完整C03：
`D:\ResearchWorkspaces\ASEAN\outputs\c03_daily_diagnostic\c02r_c03_daily122_20261012T044259Z_25e62c10\cloud_run`

关键身份：

| 对象 | SHA256 |
|---|---|
| 日CSC MATH_PROBLEM | f70b2dc2dfc79e5b7caadc22beb30b82520a91b1aabf3dd720962af120302a70 |
| 日V3 cost | c9a9717c664e2b3d5d4ca9b56848097f5231823465516113a13e00cb8f632d83 |
| 日D/R mapping | f5bdb465709c0840ad9c370f121b5f23d31f62310300ad7e47208b0b9d6d746e |
| DAILY_V4_BINDING | 8c48d0735e6dcde870fdff589915aba57b55870994e75bc04b76d39e41c38459 |
| 父V4 | 955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f |
| 日未求解NetCDF | b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2 |

日模型规模：2,450,005列、6,042,238行、11,403,496非零元。
Scheme A、C01R、Load/Q、端口、全部物理约束、NULL价格、日科学/V3目标、offset、D/R和日V4不变。不得引入P2。

## 3. 唯一参数配置

以C03真实`EFFECTIVE_MODEL_PARAMETERS.json`为底表生成新配置，禁止仅从C05配置改BarConvTol而遗漏Aggregate恢复。

```text
Method=2
Crossover=0
Threads=4
Seed=123
Aggregate=1
AggFill=0
PreDual=0
Presolve=-1
BarConvTol=1e-9
NumericFocus=0
FeasibilityTol=1e-6
OptimalityTol=1e-6
DualReductions=1
BarHomogeneous=-1
ScaleFlag=-1
ObjScale=0
GURO_PAR_BARDENSETHRESH=200
TimeLimit=3600
SoftMemLimit=65
MemLimit=1e100
```

其余记录参数按C03逐项保持。实际原生模型回读154项数值参数，输出相对C03和相对C05两张完整差异表。相对C03的唯一算法差异应为BarConvTol；RunID、日志路径、日期等运行元数据另表记录。无法设置、回读不符或出现其他参数改变则在optimize前停止。

不启用BarHomogeneous、NumericFocus等其他对照。C05日志中的建议不能直接充当新增算法授权。

## 4. 一项任务完成实际执行

按本次已确认授权，一次完成以下流程，不在正常步骤之间重新申请常规批准：

1. 核实122实例当前可用性、可信主机身份、资源及WLS生产绑定。此前成功不代替当前核查；不输出许可证内容。不擅自开关机、克隆、扩容或换机。
2. 检查无同目的活跃任务或已消费的新授权。新建独立Release、Run、代码白名单及一次消费标记。保留C03、C05和暂停的G6-05。
3. 复用C05监督、原生worker、日V4及封存框架。仅做参数比较基准、Run命名和必要绑定的最小修改。用少量不调用求解器的正反例验证参数防串用；不重新开展全部工程测试。
4. 校验冻结输入及新参数。创建一个新的Gurobi原生模型，载入原有CSC；完整逐值回读系数、索引、行方向/RHS、列界/目标、ModelSense、ObjCon及标签绑定。
5. 精确回读和资源保护通过后，在同一模型中调用**唯一一次GRBoptimize**。不额外调用独立presolve、IIS、feasRelax或优化器测试。
6. 正常返回或受控停止后，先保存真实终态和合法可得向量，再执行日V4、云端封存及本地同步。

不要以PATCH_READY、PREPARED或LAUNCH_DISPATCHED作为本轮正常终点；应交付真实求解及验收结果，或阻止执行的具体证据。

若发现已有同目的C06运行或本次授权已消费，先读取并报告其真实状态，不重启、不终止、不删除标记。初始无关任务不能被本次监护误杀。保持既有非秘密参数和凭据绑定；不得为解决访问问题跳过主机身份验证。

无合法完整向量时，照常完成状态、日志和备份交付，不把缺少向量视为重新优化的理由。GitHub推送或本地传输失败也不得触发优化重跑。

## 5. 本次已批准的窗口与保护

原生优化最多3600秒；生产全流程最多7200秒。建议沿用C05固定阶段预算：载入/回读900、原生3600、原生退出及TERM宽限合计150、RAW300、日V4后处理1200、封存1050秒。以实际t0冻结总截止和各阶段截止，按既有经核实现落实，不运行中滚动延期，不因提前结束重新分配无限预算。

原生达到TimeLimit后可能仍需返回处理时间，必须保留既定宽限和原始结果保存链；资源/身份异常仍应受控停止，不能以保存结果为由越过安全限。

保持有效90GiB内存准入、至少4核CPU配额、RSS上限75GiB、cgroup余量至少12GiB、启动盘至少20GiB并核算真实产物需求、运行盘底线8GiB。SoftMemLimit按十进制GB，不与GiB混同。构建或原生内存峰值不得从上次结果保证。

独立监督不得依赖Codex会话在线；禁止盲目杀死身份未核进程。费用记录与运行窗分开，不恢复已取消的费用阻断规则。

## 6. 原始结果与完整科学验收

保存GRBoptimize返回码、Status、SolCount、迭代、Runtime、完整日志、实际参数、输入身份、模型句柄关联、质量属性及错误。

只有属性合法可取才保存X/Pi/RC；区分未查询、查询错误和完整保存成功。若SolCount=0，遵守现有安全分支，不伪造数组或根据ObjVal标量宣称存在可行点。已有合法但非最优的点可如实保全，其资格仍不得自动升级。

先fsync/哈希原始结果，再按冻结日D/R映射，执行**完整日V4**：全矩阵及列界、807资源账户、385义务组、年度/前缀/状态L1、Bus/转换/储能、每列stationarity、自由RC、对偶符号、互补L1、加权stationarity L1、目标差、原/V3已知成本账、FOM及NetCDF回读。

不得只检查历史失败资产。源表示差与返回点残差分别报告，不用C01R的输入舍入预算抵消物理误差；不截断负库存，不补偿Bus，不放宽V4。

只有Status=2、完整原始/对偶结果且全部日V4通过，才可报告日模型科学通过。备份状态另列；未完成规定保全时不能宣布整体交付完成。日通过不等于2920时段Gate6通过，不等于原未扰动目标严格最优。

## 7. 明确的对照指标与解释规则

以C03为科学/数值对照，C05只作失败分支记录。

输出：
- 154项参数双对照及全部数学文件身份；
- 原生日志轨迹、Presolve前后规模、显示精度下的残差/互补变化；不假定前69步必然完全一致；
- 807账户全部误差、各账户误差/自身预算、385组正负交付、1/2/3/4账户分层；
- 377/111旧失败集合的解决/保留以及新失败资产；
- 4,304个stationarity、365个自由RC旧失败项与全变量新检查；
- 原单位绝对违约、归一化误差、目标差和互补性，而不只是GurobiStatus；
- 资源、保护、封存与同步状态。

参数严格1000倍只是请求值变化，不能预测残差按比例下降。若更多迭代及各类实际残差改善，支持结果对停止精度敏感；不证明停止条件是唯一原因。若只有目标差改善而局部物理或KKT仍失败，不接受。NUMERIC/TIME_LIMIT不能用作不可行证明。

无论结果如何，本次停止后不得再自动尝试1e-10、1e-12、NumericFocus、BarHomogeneous、P2或其他算法。若仍不能合格，保全现有小规模复现材料供新的方法决策，不安排没有明确假设的连续参数网格。

## 8. 本次已批准的新增结果传输窗口

云端封存完成后，为本次新增结果设独立60分钟传输窗口，从实际开始传输计时。它不延长原生或7200秒生产窗，也不复用旧C04/C05授权。

仅传新增文件；旧数学数据保持不可变引用。已核同SHA文件不重复下载；partial仅在源SHA及前缀核验后安全接续，不无限重试。

验证归档大小、SHA、压缩流CRC、路径安全及BACKUP_INDEX。未完成如实标LOCAL_SYNC_PENDING，保留云端和partial，不重新求解。日志公开副本脱敏时必须保留原始SHA、公开SHA和变换记录。

## 9. GitHub与同轮ZIP交付

独立C06分支，关联已有PR #13、#14、#15；核实实际仓库/HEAD/未提交更改，不改main、不force-push、不自动合并。旧实验不覆盖。

更新BASELINE_EVOLUTION_LEDGER.md、research/STAGE2_PROJECT_LEDGER.md及日模型准入台账。明确C05是NUMERIC无完整解，C06尚须真实结果判定，旧G6-05继续暂停。

同轮交付：
- `C06_BARCONVTOL_DAILY_DIAGNOSTIC_RESULT.md`
- `C06_C03_C05_PARAMETER_COMPARISON.json`
- `C06_COMPLETE_V4_AND_BASELINE_COMPARISON.json`
- 真实调用/状态/参数/资源/封存/本地备份回执
- 新增少量必要代码及测试、最新台账
- `C06_BARCONVTOL_DAILY_DIAGNOSTIC_REVIEW.zip`

commit/push后给出实际完整SHA和PR信息，失败如实记录。审阅ZIP附相对路径、大小、SHA和CRC；提供真实本地绝对路径。不要将完整矩阵、向量、NetCDF、许可证或凭据放进GitHub或审阅ZIP。

最终状态应区分日科学资格和工程/备份状态；没有合法解时物理与KKT计数是NOT_AVAILABLE，不是0。任务结束后停止。本次授权到C06结果、完整日V4的条件分支及规定保全/发布交付为止；之后任何新优化都需要新的明确授权。
