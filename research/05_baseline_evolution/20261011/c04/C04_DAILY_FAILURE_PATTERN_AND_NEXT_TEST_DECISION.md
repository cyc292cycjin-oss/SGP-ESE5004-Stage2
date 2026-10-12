# C04 日模型失败模式与下一次单因素诊断决策

**结论：C04_READY_FOR_ONE_CONTROLLED_DAILY_TEST。仅表示本轮取证完成、可供审批；没有新的求解授权。**

日模型仍为 **OPTIMAL_BUT_NOT_ACCEPTED**。独立计算确认保存的返回点存在库存/Bus违约及局部KKT失败，所选点未发现D/R恢复或NetCDF映射差异。下一次只建议 **Aggregate=1→0**，其余算法与科学身份保持不变；不执行。G6-05继续PAUSED_BY_USER，2920时段和正式情景均未启动。

## 1. 对象、备份及证据等级

仅分析 `c02r_c03_daily122_20261012T044259Z_25e62c10`。生产代码提交 `a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7`，原交付提交 `decafc72d883293b23f7b5ae1db6355b6aad8ea6`；两者不是同一职责。沿用原生回执：2,450,005列、6,042,238行、11,403,496非零元，Status2、SolCount1、69次Barrier、155.370942831秒；本轮没有重新载入Gurobi。

新传输窗口始于 2026-10-12T06:17:28.442449+00:00，传输完成 2026-10-12T06:30:44.643532+00:00，用时 **796.201秒**，固定上限3600秒。云端完整SHA与239,468,544字节旧partial前缀SHA一致后，只接收75,400,372字节；没有网络重试。旧partial和云端原件均保留。

- 完整归档：314,868,916字节；SHA256 `d484db824ce041a81b000484dfe6298d32bfb16145e8dab26db3fd2a6c377019`。
- gzip完整流CRC、17,420个唯一普通文件成员及路径安全通过；BACKUP_INDEX的 **17,417/17,417** 项、1,946,512,966字节逐项大小/SHA通过。
- BACKUP_INDEX SHA：`eb80de5b50ff64d976d23066c514811fcc4f80f9b768f62ade1b6e1b4282d47d`；与原CLOUD_SEAL_COMPLETE一致。两项immutable references及Release清单内65文件全部核验。
- 新本地状态 **LOCAL_BACKUP_SHA_VERIFIED**，旧回执中的LOCAL_SYNC_PENDING保留为历史时点。Windows原生I/O接续时复核复用了6111个已完整副本，保留1个中断的本地解包副本；这不是重新下载或改写云端结果。细节见备份回执。
- 完整归档：`D:\ResearchWorkspaces\ASEAN\work\c04_daily_pattern_20261012\c02r_c03_daily122_20261012T044259Z_25e62c10_COMPLETE_EVIDENCE.tar.gz`。
- 独立解包目录：`D:\ResearchWorkspaces\ASEAN\outputs\c03_daily_diagnostic\c02r_c03_daily122_20261012T044259Z_25e62c10\cloud_run`。

证据类型在下文分为机器核验、精确局部推导、受限推断和提议。用户提供的辅助比较只作线索；本轮已读取实际回执及备份数组。科学解释仍待用户/ChatGPT审阅。

## 2. 失败集合和共同变化因素

**机器核验（实际PHYSICAL_CHECKS × A03资产ID对照）：** 两次均为377失败账户、111失败义务组，两个集合的对称差均为0。

| 每组账户数 | 组数 | 日模型失败组 |
|---:|---:|---:|
| 1 | 118 | 0 |
| 2 | 156 | 0 |
| 3 | 67 | 67 |
| 4 | 44 | 44 |

规模区间重叠：通过的1账户组年度需求最高43.646百万MWh，失败的3账户组最低27,112.861 MWh。MM/Buildings的1与3账户对照年需求仅差约0.29%，实际D均为4,194,304、R均为2^-22。ID/Buildings的2与3账户对照需求差约0.66%，也用于局部复算。全385组中有 **13个相同国家/部门/D分层** 同时出现通过和失败。仅用规模、国家或D大小不能充分解释此模式。

2与4账户组最接近的规模配对相差约0.029%，D相同，但国家/部门不同；没有同国家且同部门的2/4账户对照。子部门、商品组合、资源份额等仍有混杂。**关联不等于账户数量或某个软件缺陷的因果效应。**

复用已保存的行活动值发现：全部111失败组的“平均缩放Bus残差/账户数”均约 **7.7493401907e-9**；1/2账户组对应值为0。3账户组缩放残差约2.3248020572e-8，4账户组约3.0997360763e-8。全组这一统计来自保存的活动值；以下代表行另以实际CSR独立验证。规律支持开展聚合处理对照，但没有Presolve内部轨迹，不能声称已证明约束被如何消除。

## 3. 返回点的独立物理核算

直接读取7组、19账户的 **51,100个完整CSR行支撑**，覆盖Store递推/初值/上下界、资源方向、meter上下容量行、资源Bus和最终Bus；只涉及49个源块，不扫描旧全年矩阵。159个代表行另用Fraction精确核算binary64系数与值；包含独立的原单位和缩放空间内积。原始X×D与保存的X_original、所选NetCDF Store-e/Store-p/Link-p0逐值一致。

| 最终义务组（完整来源ID） | 账户数 | 年需求MWh | D | 年度超供MWh | 最大Bus违约MW |
|---|---:|---:|---:|---:|---:|
| ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Sulawesi0 0 | 4 | 4071331.49 | 4194304 | 1138.90822 | 0.130012354 |
| KH:2050:Buildings:ResidentialFuel:biomass@KH2 3 | 2 | 4072511.26 | 4194304 | 0 | 0 |
| MM:2050:Buildings:ResidentialFuel:biomass@MM2 15 | 3 | 3531857.62 | 4194304 | 854.181167 | 0.0975092657 |
| MM:2050:Buildings:ServicesFuel:biomass@MM2 0 | 1 | 3542105.07 | 4194304 | 0 | 0 |
| ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Java-Bali1 0 | 4 | 201045255 | 268435456 | 72890.1263 | 8.32079067 |
| ID:2050:Buildings:ServicesFuel:biomass@ID_Sumatra3 5 | 2 | 614195.208 | 1048576 | 0 | 0 |
| ID:2050:Buildings:ResidentialFuel:biomass@ID_Kalimantan4 5 | 3 | 618267.115 | 1048576 | 213.545292 | 0.0243773164 |

**精确局部推导：** Java-Bali1 0 Bagasse在2013-12-31的Store下界行（原生行3258844，列1984648）是 `e≥0`，完整支撑只有该库存列，系数+1。返回值为

`e = -1257456884281429/68719476736 = -18298.40598338966 MWh`。

D=2^28、R=2^-28，缩放违约为6.816687428723894e-5；原单位账户预算1.6193494888810167 MWh，约11,299.85倍。显式列界为自由界，但非负性由真实约束行实施；没有漏掉该下界，也不能把“列自由”解读为允许负库存。

Java-Bali1 0最终Bus在2013-01-01的原生行4259016、Linopy标签4263081，完整支撑为四个meter列357780—357783、各系数+1；RHS=22950.371582124517 MW。独立精确残差：

`585523590092411/70368744177664 MW ≈ 8.320790671125 MW`，

缩放后约3.09973607627e-8，原单位行预算0.00329586923728 MW，超预算约2524.61倍。与原验收最大值8.320790671128634 MW的约3.64e-12 MW差异来自浮点累加顺序；Fraction证据不依赖该顺序。**缩放解释两个空间的量级关系，不单独证明数值故障的起因。**

该组年超供72,890.12627905741 MWh与四账户负终库存相抵，扣除源年度余量后的闭合误差约3.72e-7 MWh；所选meter与Store释放相等，动态行接近成立。即：保存点通过“负库存+最终Bus超供”违反真实约束，而非出现未记录的新供应路径。局部系数、初始Q、24小时权重、目标零系数和边界均列于轻量证据；NULL科学价格仍是未知，目标中没有新增已认证资源价格。

11,299.85只是最大绝对库存违约账户相对于自身预算的比值，**不是全部账户最严重的相对比值**。实际回执的MM2 0 Biogases：Q=22.47972421082701 MWh、年度超用578.1232889158391 MWh、预算2.24797242108e-5 MWh，年度超用/预算约25,717,544。代表组MM2 15的类似超额另被原始X独立复现。

本轮未发现所选支撑中的D/R映射、端口符号、行界或NetCDF恢复错误。该结论范围限于定向样本与下述全部列KKT分类，不能升级为对整个生产实现的无错误证明；也不能证明新日LP不可行。

## 4. 独立KKT问题不能被资源模式取代

保存的KKT中间文件没有失败列索引，因此对**日CSC仅一次**有界流式计算c−Aᵀy−r；没有旧全年扫描，也没有再次调用生产V4。复现：

| 失败项目 | 独立结果 |
|---|---|
| stationarity | 4304列：3966 Line-s（26条AC Line），338 Link-p（5条DC Link）；这些列D=1 |
| 最大原单位stationarity | 0.03851123219624242；归一化最大1.869757959330463e-5，超过1e-6 |
| 自由列对偶符号 | 365项，全为Line 52的365日；RC最大3.802943433194802e-5 |
| 代表列精确复核 | Line2/2013-01-12列319581：1420813688572779553/36893488147419103232≈0.038511232196194；DC `1076672675-1_0+4`/2013-03-03列561578≈0.003868916711722 |

对Line52/2013-12-28，c−Aᵀy−r约−5.734e-7，而自由列RC约3.803e-5：一个列可通过stationarity但失败于自由RC，二者不能合并。所有代表列用完整原生列支撑、Pi、RC和R/D精确核算，符号与V4定义一致。另对13个相关行独立复算互补性，和保存活动值算出的差异最多约1.50e-9 EUR。没有把原生DualVio=0.02547632459915626当作相同指标；质量属性、stationarity等式残差、禁止的端点乘子及用户原单位缩放有不同定义。[Gurobi质量属性](https://docs.gurobi.com/projects/optimizer/en/12.0/reference/attributes/quality.html)

按批准的含固定offset归一化 `Z=max(1,|P|,|D_dual|)=428014262628.2893 EUR`，保存账本的以下三个**全局单项通过**：

| 指标 | 绝对EUR量 | 除以Z/相对值 | 1e-6门槛 |
|---|---:|---:|---|
| 互补性L1 | 189887.48498384244 | 4.436475640269749e-7 | PASS |
| 加权stationarity L1 | 101694.67655237838 | 2.3759646682777843e-7 | PASS |
| 原/对偶目标差 | 84271.25708007812 | 1.9688889936189775e-7 | PASS |

它们不抵消局部stationarity、自由RC及物理失败。较旧候选，物理年度超用从约10.2418 TWh降至0.338138 TWh，但原单位stationarity最大值0.0189233→0.0385112，自由RC约增29.045倍，绝对目标差19,784→84,271 EUR。两次还同时改变时间分辨率和Scheme A源Q版本，不能把差异全部归因于日聚合。

## 5. 已证明、尚未证明与唯一建议

**已核实：** 完整备份；失败ID重复与账户数模式；所选返回点真实违反实际日LP行；精确R/D关系、对应NetCDF值和KKT局部失败成立；存在与资源账户分离的AC/DC对偶问题。

**未证明：** Presolve聚合/消元是根因；某特定Gurobi/PyPSA bug；规模或D是唯一原因；整个日LP可行或不可行；调整一个参数必然通过V4。当前没有证据支持修补已保存解或修改验收阈值。

最多比较两个候选：

| 候选 | 可辨识的问题 | 限制 |
|---|---|---|
| **Aggregate=1→0（推荐）** | 保留Barrier停止精度，检验重复的3/4账户模式及原模型残差对聚合处理是否敏感 | 只关闭聚合，不关闭全部Presolve；可能增大保留矩阵和内存，未必改善AC/DC KKT |
| BarConvTol=1e-6→1e-9（本轮不推荐执行） | 检验继续Barrier迭代是否降低原单位残差 | 同时改变终止点与迭代历程，不能直接识别聚合相关机制；不保证残差改善1000倍 |

选择Aggregate=0的依据是跨国家/规模/D仍存在的离散结构关联、几乎恒定的每账户缩放Bus残差，以及独立核算未发现所选映射错误；这是**信息价值排序，不是根因证明**。官方12.0说明聚合在某些情况下可能积累数值误差；当前AggFill=0仅限制填充，**不等于Aggregate=0**。BarConvTol控制Barrier的相对质量停止条件，NumericFocus改变数值处理谨慎程度，FeasibilityTol与用户物理单位/缩放又属另一层；不将这些开关混成一个对照。[数值指南](https://docs.gurobi.com/projects/optimizer/en/12.0/concepts/numericguide/numeric_parameters.html)；[Aggregate及BarConvTol](https://docs.gurobi.com/projects/optimizer/en/12.0/reference/parameters.html#parameter:Aggregate)；[容差与缩放](https://docs.gurobi.com/projects/optimizer/en/12.0/concepts/numericguide/tolerances_scaling.html)

### 待用户单独批准的单次协议

- 直接复用现成日CSC、目标/offset、D/R、标签、Scheme A、C01R和日V4绑定，不重建网络/LP，不引入P2，不动碳政策/成本/需求。实际原生回读后的同一模型只允许一次optimize。
- 154项记录数值参数逐项回读并比较，**唯一算法差异Aggregate=0**；Method2、Crossover0、BarConvTol1e-6、NumericFocus0、FeasibilityTol1e-6、OptimalityTol1e-6、Threads4、Seed123、AggFill0、PreDual0、历史200、DualReductions1等全部保持。许可证和资源在下一次实际准入时核实，本轮不声称已重新验证。
- 提议原生TimeLimit仍3600秒、独立全流程7200秒：载入/回读900、原生3600、退出与TERM宽限150、RAW300、后处理1200、封存1050，启动时一次冻结绝对截止。无新建模预算，无自动延长/重试。
- SoftMemLimit65十进制GB；MemLimit保持已记录默认1e100；RSS≤75GiB、cgroup余量≥12GiB、启动盘余量≥20GiB/运行底线8GiB，独立监督与guard、一调用消费标记，RAW先保存后验收。不承诺增加矩阵后90GiB必定充足。
- 可检验预测：若聚合路径参与形成模式，111组的缩放残差/账户数结构、负库存和超供应变化；比较全377/111集合、807/385全部科学门槛及4304/365 KKT旧失败项。只降低目标差而局部仍失败不算成功。
- 若模式不变，只能降低对“聚合这一操作”的怀疑，不能排除其他Presolve操作或Barrier精度问题。若OPTIMAL，仍需全V4与保全通过；若TIME_LIMIT/MEM_LIMIT/NUMERIC则记录未决；INFEASIBLE或INF_OR_UNBD不当作严格数学证书。任何结果之后均停止，不自动下一参数。

## 6. 本轮范围与复核入口

核心方法用时约88.07秒、峰值RSS约1.013GiB；补充13行互补性和保存活动值统计单独列证据。定位脚本最初误假设全局行标签有序，在CSC扫描前停止；已改用持久化标签反向索引，未改生产代码。全程零solver导入、零新建模、零optimize；云端仅读取现成归档。

主要轻量复核文件：`C04_RECEIPT_PATTERN.json`、`C04_SCALE_CONFOUNDING.json`、`C04_SELECTED_PHYSICAL_RECOMPUTATION.json`、`C04_KKT_COLUMN_CLASSIFICATION.json`、`C04_TARGETED_CROSSCHECKS.json`、`C04_ACCOUNT_BUDGET_SEVERITY.json`、`C04_BACKUP_RECEIPT.json`；字段方法见`C04_METHOD.md`及methods目录，全部来源SHA见`C04_EVIDENCE_INDEX.json`。原始大数组仅以真实本地路径/大小/SHA引用，不进入GitHub或审阅ZIP。

独立分支 `codex/c04-daily-pattern-20261012`，关联[PR #13](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/13)。实际本轮commit/新PR/ZIP SHA由发布回执给出；不合并任何PR。

**C02R构建/静态交接完成；C03诊断已执行但科学NOT_ACCEPTED；C04取证与单因素建议完成。完成交付后停止，等待新的独立求解授权。**
