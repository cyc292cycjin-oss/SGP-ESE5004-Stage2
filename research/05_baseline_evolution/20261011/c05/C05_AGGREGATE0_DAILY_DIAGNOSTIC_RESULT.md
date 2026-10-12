# C05 Aggregate=0 日模型单因素诊断：真实终态

**结论：C05_NUMERIC_NO_SOLUTION_NOT_ACCEPTED。唯一一次优化已完成；云端封存和本地备份均通过。**

Run `c05_aggregate0_daily122_20261012T074925Z_a39647d9`。Gurobi 12.0.3 返回码0、模型 **Status=12 NUMERIC**、SolCount=0、24次Barrier、Runtime **81.595145秒**。没有合格日模型解；没有执行第二次优化、独立presolve、IIS或feasRelax。G6-05继续PAUSED_BY_USER；2920时段Gate6及其他情景未启动。

## 1. 科学与执行身份

本次实际生产代码为 `d6c48dbd95d12f0354561372e9a65d6e92511754`，独立分支 `codex/c05-aggregate0-daily-20261012`。基准C03代码 `a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7`，C04父提交 `4b76dc65662faef61ff429d3a299cc7db8bccd9b`；关联PR #13、#14，历史结果不改写。

实际复用17,369项、1,488,811,247字节的冻结输入，生产SHA检查通过；新网络构建0、CSR→CSC转换0、旧解warm start=false。`BUILD_RESULT.json`只是历史构建回执副本，其来源由IMMUTABLE_INPUTS明确标识，不表示本次重建。

| 身份 | SHA256 |
|---|---|
| 日CSC MATH_PROBLEM | `f70b2dc2dfc79e5b7caadc22beb30b82520a91b1aabf3dd720962af120302a70` |
| 日V3 cost | `c9a9717c664e2b3d5d4ca9b56848097f5231823465516113a13e00cb8f632d83` |
| 日D/R映射Manifest | `f5bdb465709c0840ad9c370f121b5f23d31f62310300ad7e47208b0b9d6d746e` |
| DAILY_V4_BINDING | `8c48d0735e6dcde870fdff589915aba57b55870994e75bc04b76d39e41c38459` |
| 父V4 | `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f` |
| 未求解日NetCDF | `b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2` |
| C05 Release Manifest | `9ad443c84c4a8271a153114f47bac496853181ee422c7d7dcf34ef2bf974787a` |
| C05实际参数 | `349d8ca34cc5f0e882a368d8bd239bc590950a004cc94eddce3dbcac71b20c42` |

实际规模2,450,005列、6,042,238行、11,403,496非零元。完整载入/逐值回读 **EXACT_READBACK_PASS**，耗时3.774589秒；交接与唯一调用记录为同一原生模型句柄。Scheme A、C01R、全部矩阵/界/标签、日目标offset和D/R保持原身份；未引入P2、科学变更或容差放宽。

154项原生数值参数逐项回读，仅Aggregate由1变0。TimeLimit3600、SoftMemLimit65十进制GB、MemLimit默认1e100均与C03相同。Method2/Crossover0/BarConvTol1e-6/NumericFocus0/FeasibilityTol1e-6/OptimalityTol1e-6/Threads4/Seed123/AggFill0/PreDual0/Presolve−1/DualReductions1/ScaleFlag−1/ObjScale0/历史200不变。完整差异表见[C05_SINGLE_FACTOR_PARAMETER_DIFF.json](C05_SINGLE_FACTOR_PARAMETER_DIFF.json)，不是只检查列出的参数。

## 2. 准入、唯一调用与保护

已核122实际容器身份、公钥、Python3.11.13及原生Gurobi12.0.3；有效CPU配额12核、cgroup90GiB（可见祖先与内核hierarchical限制）、开跑前磁盘27.349GiB。WLS文件只核元数据及绑定；生产GRBstartenv真实返回0。未读取或复制密钥/许可证内容，未重新安装环境。

独立Run/Release/授权/消费标记；准入时无同目的活跃任务，旧C03标记保留。同一模型仅执行一次GRBoptimize（NATIVE_TRANSFER→C05_NATIVE_OPTIMIZE_ENTERED→NATIVE_CALL_EXIT）。原生返回码0表示调用正常返回，不代表优化成功。

独立supervisor、guard及封存guard覆盖全程，不依赖浏览器/Codex；RSS75GiB、cgroup余量12GiB、盘8GiB保护有效。唯一必要控制兼容修订：原生截止后仅在原生已返回且RAW完整持久化时允许进入独立后处理预算；原STOP_REQUEST保留，资源/身份/其他异常仍停止。本次未触发此路径。12项局部无求解接口测试与实际运行分开记录。

| 阶段 | 固定预算/证据 |
|---|---|
| 生产t0 | 2026-10-12T07:49:25.860620Z |
| 载入、原生 | ≤900秒、≤3600秒；原生内TimeLimit实际回读3600 |
| 退出/TERM宽限、RAW、日V4、封存 | 150、300、1200、1050秒；共享7200秒固定上限 |
| 总绝对截止 | 2026-10-12T09:49:25.860620Z（未延长） |
| 实际载入与精确回读 | 3.774589秒 |
| 实际原生Runtime | 81.595145秒 |
| t0至封存guard退出 | 96.067453秒 |
| worker进程树RSS采样最大 | 3.444138GiB |
| cgroup lifetime peak | 6.149261→6.249012GiB |
| 最小cgroup余量 / 磁盘余量 | 83.969620 / 27.340099GiB |

RSS为采样峰值，可能漏掉采样间短峰；cgroup峰值包含同组其他进程及既往运行，不能冒称Gurobi独占峰值。memory.events的max/oom/oom_kill均0；无资源/截止保护触发或受控终止。终态独立观察确认worker、supervisor、guard均退出，封存guard也退出。122仍保持运行，实例持续计费；未读取新账单，不以约96秒执行时长冒充整个实例费用。

## 3. 数值轨迹与C03对照

| 指标 | C03 Aggregate=1 | C05 Aggregate=0 |
|---|---:|---:|
| 模型指纹（辅助） | 0xadbe9ee0 | 0xadbe9ee0 |
| Presolve秒 | 10.79 | 8.06 |
| Presolve后行/列/非零 | 1,060,244/925,765/3,201,818 | 1,798,093/1,720,242/4,827,272 |
| Free vars / Dense cols | 77,015 / 1,826 | 185,055 / 2,022 |
| 日志Factor NZ（近似） | 2.545e7 | 3.474e7 |
| Barrier次数 / Runtime秒 | 69 / 155.370943 | 24 / 81.595145 |
| 原生Status / SolCount | 2 OPTIMAL / 1 | 12 NUMERIC / 0 |
| 科学结果 | OPTIMAL_BUT_NOT_ACCEPTED | NOT_ACCEPTED；无合法完整解 |

C05第7次日志原始残差1.06e5、对偶残差2.72e3；第9次原始残差升为6.72e7。第14–24次日志停在原始残差7.07e5、对偶残差1.25e4、互补性5.56e10，随后“Numerical trouble encountered”。这些是日志四舍五入的求解器内部尺度指标，**不能替代原单位MW/MWh残差**。两次日志都有大目标系数/大边界警告。完整逐次提取见[evidence/C05_LOG_TRAJECTORY_COMPARISON.json](evidence/C05_LOG_TRAJECTORY_COMPARISON.json)。

**已验证：** 单一Aggregate改变了本次预处理后的规模及数值轨迹，关闭聚合没有产生可验收的解。**推论边界：** 本次不支持“单独关闭聚合即可解决C03失败”的预期；也没有证据把C03失败唯一归因于聚合、资源账户数或某个物理实现错误。NUMERIC不是INFEASIBLE(3)或INF_OR_UNBD(4)或UNBOUNDED(5)。日志的“may be infeasible or unbounded”及参数建议保留为原始文字，未作为数学结论或后续执行授权。[Gurobi12参考手册](https://docs.gurobi.com/_/downloads/optimizer/en/12.0/pdf/)、[原生模型Status/SolCount说明](https://docs.gurobi.com/projects/optimizer/en/12.0/reference/attributes/model.html)。

## 4. RAW与完整日V4的条件分支

先持久保存NATIVE_RETURN、RAW_RECEIPT、实际参数、日志及其SHA。SolCount0时生产安全门不提取数组，X/Pi/RC记为NOT_AVAILABLE/NO_LEGAL_SOLUTION_COUNT；这不表示逐个数组getter实际返回了10005。DualVio/ComplVio的属性查询实际返回10005，已原样保留。RAW_DURABLE明确native_state_preserved=true、complete=false。

ObjVal原始返回标量4.6484251002308625e14仅作为**未认证诊断值**保全；BoundVio=−1、ConstrVio=−1、MaxVio=0不能被解释为可行或零违规。没有合法完整向量，因此没有映射、独立残差计算、V4或NetCDF解导出；POSTPROCESS_NOT_RUN理由为NO_COMPLETE_LEGAL_PRIMAL_DUAL。此为用户批准的条件分支，不造partial解、不伪造验收失败计数。

| 日V4项目 | C03历史结果 | C05 |
|---|---|---|
| 全矩阵/列界 | 48,298行失败、列界0失败 | NOT_AVAILABLE |
| 807资源账户/385义务组 | 377/111失败 | NOT_AVAILABLE |
| 动态、前缀、累计绝对残差、Bus/转换/储能 | 物理验收失败 | NOT_AVAILABLE |
| stationarity | 4,304列失败（Line-s3,966、Link-p338） | NOT_AVAILABLE |
| 自由RC/对偶符号 | 365项失败，Line52 | NOT_AVAILABLE |
| 互补性/双目标差/KKT | 局部KKT不通过；相对双目标差1.968889e-7 | NOT_AVAILABLE |
| 原/V3双成本、FOM、NetCDF回读 | FOM/回读通过但科学失败 | NOT_AVAILABLE |
| 旧失败消失/新增失败资产 | 旧集合由C04核实 | 无法评估，不记为0 |

| 每组账户数 | 组数 | C03失败组数 | C05失败组数 |
|---|---:|---:|---|
| 1 |118|0|NOT_AVAILABLE|
| 2 |156|0|NOT_AVAILABLE|
| 3 |67|67|NOT_AVAILABLE|
| 4 |44|44|NOT_AVAILABLE|

C03原科学已知口径427,765,450,088.104 EUR，V3目标428,014,262,628.28937 EUR，均来自**未通过科学验收的旧候选**，并非完整已认证系统成本。C05没有可复算的合格原/V3成本，不能宣称成本改善、资源超用减少、Line/Link问题解决或日V4通过。没有对历史全年大矩阵或当前日矩阵开展额外扫描。

## 5. 云端与本地保全

云端Run：`/root/autodl-tmp/SGP/runs/c05_aggregate0_daily122_20261012T074925Z_a39647d9`；本地完整新证据：`D:\ResearchWorkspaces\ASEAN\outputs\c05_daily_diagnostic\c05_aggregate0_daily122_20261012T074925Z_a39647d9\cloud_run`。32项新增结果、195,688字节均按BACKUP_INDEX核SHA；另有索引与封存回执。原17,369项数学输入通过不可变引用复用；本地引用与此前C04已核SHA索引完全一致并核存在/大小，未重复旧大文件下载或全量重哈希。

现成新结果归档394,606字节，SHA256 `4b78d58396be73378ede9589a3bf3db56ad671a9643d82d50da7dd7b1e1bac63`。新独立60分钟窗口接收用时6.526404秒，下载次数1、重试0；大小、SHA、gzip CRC、成员/路径安全及全部新增文件SHA通过，**LOCAL_BACKUP_SHA_VERIFIED**。原云端LOCAL_SYNC_PENDING标记是封存时点历史记录，未改写；其后本地C05_LOCAL_BACKUP_RECEIPT构成已完成同步的新增证据。

原日志完整保留于云端与本地证据目录；GitHub/审阅ZIP中的日志副本仅移除一行许可证注册元数据，保留全部数值内容。发布来源、原始SHA、公开副本SHA及唯一删改项由C05_PUBLIC_EVIDENCE_PROVENANCE记录。未把矩阵、NetCDF、X/Pi/RC、许可证或凭据放入审阅ZIP/Git。

## 6. 交付与停止边界

证据级别：运行终态/交接/参数/资源/备份为真实回执验证；C03资产模式为复用已验收证据；唯一根因、原单位改善、完整LP可行性均未证明。诊断执行完成但科学验收NOT_ACCEPTED，Gate6 PASS=false。

保持现有科学输入、V3/V4、Scheme A及历史结论。后续唯一行动是用户与ChatGPT审阅本次结果后作出新的科学决策；**没有授权或执行第二个参数、更长预算、第二次optimize或其他情景**。G6-05暂停。实例不关机/释放，任务在GitHub和ZIP交付后停止。

逐文件证据见[C05_EVIDENCE_INDEX.json](C05_EVIDENCE_INDEX.json)；完整机器对照见[C05_BASELINE_RESULT_COMPARISON.json](C05_BASELINE_RESULT_COMPARISON.json)。实际最终提交、PR及审阅ZIP整体SHA由同轮发布/交付回执绑定，不能把生产代码提交误写成最终报告提交。

真实发布里程碑：结果及全部脱敏日志已推送 `869d72a90376b1862cf2058576b01917131f0a12`；[独立PR #15](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/15)已建立（OPEN/DRAFT，关联#13/#14，未合并）。最终导出提交及ZIP整体SHA以交付回执为准。
