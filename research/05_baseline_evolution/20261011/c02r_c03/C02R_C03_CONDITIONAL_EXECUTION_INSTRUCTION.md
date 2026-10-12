# SGP ESE5004 Stage2 — C-02R → C-03 合并执行补充授权

## 0. 生效方式与任务终点

本条由用户确认并转发给Codex后，构成新增的条件式授权：完成C-02R检查器修复和静态构建；全部规定门槛通过后，允许在122号机对365日诊断模型调用最多一次GRBoptimize，并完成日V4、结果保全及交付。

本条覆盖先前“构建成功后必须等待另一轮普通审批”“C-03一律禁止”的流程条款；不覆盖科学约束、身份核验、资源保护和失败即停条款。旧的build-only授权本身不构成求解授权。旧G6-05继续暂停。

本轮目标是实际运行结果或有具体证据的阻断，不是再次仅交付PATCH_READY、BUILD_READY或READY_TO_REQUEST_SOLVE。

## 1. 接续现状，不重复启动

先核对当前Codex任务、云端构建进程、run、claim和回执。若C-02R正在执行，等待其在原窗口内完成，不另启并行构建、不终止正常任务；已存在静态验收合格的完整日LP则核SHA后复用。仍需构建时，最多执行一次新的受控完整构建。

不得清除旧消费标记、覆盖旧Run、延长旧截止或以新目录规避已消费授权。本次唯一C-03调用标记放在持久的独占位置，并绑定本次诊断身份，复制入口不得产生第二次优化权利。

复用经SHA核实的daily_365_unsolved.nc：
`b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2`

保留Scheme A、C-01R和365×24小时权重，不重新聚合Load或派生Q，不重建2920时段模型。

## 2. 两项检查器修复一起收口

保留已通过的正负零语义补丁：数学语义检查允许±0相等；非零1 ULP、NaN、错误维数、方向和有限边界变化继续拒绝；输入/SHA/序列化位身份检查不全局放宽。

仅在实际资产边界、默认值来源和Linopy标签掩码共同证明成立时，接受这三类有效零行：
- Line-ext-s_nom-upper
- Link-ext-p_nom-upper
- Store-ext-e_nom-upper

有限上界本应有行却缺失、未知家族缺失、NaN被当作+Inf仍须拒绝。运行容量约束与807个固定资源库存界不得遗漏。完成既有回归测试及上述正反例测试，不再扩大科学审计。

## 3. 在大构建前补齐日LP接口与日V4调用链

不能假定旧Gate6入口直接读取新C02产物。

实际差异：新产物是`C02_DAILY_CHUNKED_CSR_LP`、rows/columns/sense="min"/V3_offset；随包旧adapter读取全局CSC的start/index/value、num_col/num_row/sense=1/offset。旧后处理还读取MAPPING_MANIFEST.json、vlabels.npy、全局D/R；新日模型产物使用LABELS.json及分块R。

请首先检查是否已有经过验证的日模型桥接；有则复用，没有则本轮实现最小格式/标签适配。优先复用成熟的原生载入和验收函数，不重新设计优化框架。

允许分块CSR到既有CSC输入格式的确定性稀疏重排、全局行序及逆映射、metadata转换、D/R拼接及日目标绑定。不得改变任何系数数值、边界、目标经济含义或物理方程，不得稠密化；保证额外存储符合预算。

使用原科学与V3日目标分别核对，原生实际求解绑定`cost_V3_scaled`和重算后的`V3_offset`。不得误读科学成本、复制旧3h向量或沿用旧行列维数。

完整日V4调用链须能够接收本次新维数、行列标签、日NetCDF和原始向量，执行原单位全矩阵/列界、807账户、385组、动态物理、KKT、双成本、FOM及NetCDF回读。只有DAILY_V4_BINDING.json不算已实现验收器；不得直接调用仍硬绑定旧Q/2920维度的历史函数。

在正式优化之前，用小型无求解数据验证格式、标签、正负零、无穷界、offset、D/R、向量散射及日V4拒绝明显违规的能力。合成测试不可伪称真实物理PASS。不得额外调用测试optimize。

## 4. 分离构建保护与求解权限

C02 build worker保留原no-solve防护，不通过删除其禁用函数或改旧授权文件偷渡求解。新建独立C03 worker，由合并控制器在实际C02_STATIC_PASS和本条授权齐备后派发。

C02原launcher为t0+1800且solver_calls_allowed=0；原guard是TERM后约3秒升级KILL。不能只改一个False为True或延长一个数字就把它当求解入口。

复用此前原生求解的独立supervisor/guard和RAW优先保存链，为新C03身份及阶段预算绑定。日NetCDF里的旧solver_allowed=false和静态绑定的optimization_authorized=false属于原产物 provenance，原样保留；新授权放独立记录，不篡改已验收NetCDF以改变SHA。

核对122号机已有可信SSH端点和主机指纹，不重复要求用户提交已验证信息；出现真实变化才停止。不得使用379旧身份或跳过SSH验证。

确认实际有效内存至少90GiB、CPU配额至少4核、启动磁盘至少20GiB且足够覆盖桥接/原始向量/备份峰值。保留RSS 75GiB、cgroup余量12GiB、磁盘底线8GiB。不得自行扩容、换机或清理历史文件。

在昂贵构建/载入前尽早从正式生产环境验证Gurobi12.0.3及WLS可启动，不打印密钥、不改许可证、不升级软件；import成功或文件存在不算许可验证。可创建/释放原生环境，不允许额外测试优化。

## 5. 冻结日模型参数，不混入P2或G6-05

采用C00_DAILY_365_PROTOCOL_C01R_V1规定的首次Gate6基准：

- Method=2，Crossover=0，Threads=4
- BarConvTol=1e-6，Seed=123，AggFill=0，PreDual=0
- 历史GURO_PAR_BARDENSETHRESH=200（通过已验证接口）
- NumericFocus=0，FeasibilityTol=1e-6，OptimalityTol=1e-6
- Presolve=-1，Aggregate=1，ScaleFlag=-1，ObjScale=0
- DualReductions=1，InfUnbdInfo=0
- 其余LP相关参数按已核FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS及协议冻结
- SoftMemLimit=65十进制GB，MemLimit保持已记录默认
- 原生TimeLimit最多3600秒，并受剩余固定native截止限制

使用日模型按首次Gate6规则生成的D/R，不切换P2。所有实际参数在同一原生模型设置、回读；运行服务端口和LogFile按新身份记录，不强行匹配旧端口。任何非授权LP参数差异停止。

## 6. 真实生产门槛通过后直接优化

顺序为：
已验收日NetCDF → 两项补丁及接口测试 → 完整日LP静态验收 → 原生环境/参数 → 一次载入与完整精确回读 → 独占调用记录 → 同一原生模型GRBoptimize一次 → RAW保存 → 日V4 → 封存。

必须在优化前验证实际全矩阵、行列边界、变量类型、目标方向、V3目标、offset、D/R及标签映射，不仅检查维数。稀疏存储顺序改变时按同一规范化数学条目核验，不误把合法重排当系数变化，也不放过遗漏或重复条目。

日V4、结果恢复及失败保全路径也须在优化之前准备完毕。不得先算完再发现没有365日验收入口。

上述门槛通过后，不再停在普通审批。保存C03_NATIVE_OPTIMIZE_ENTERED，包含run_id、模型fingerprint、实际参数/输入SHA及时间；然后在同一模型执行唯一优化。单有claim文件不能作为已实际调用的证明，须结合调用链、日志及返回回执。

失败不得为了进入优化而关掉检查。遇到新的实质阻断，保存准确阶段/错误/必要证据后停止；不自动第二次完整构建或优化。

## 7. 沿用C00的有界执行预算

本轮新合并运行从真实t0一次冻结总上限9150秒，不含此前历史运行；禁止重置旧deadline。阶段顺序上限为：

- 构建/静态回读1800秒
- 格式桥接、原生载入/回读/参数900秒
- 原生优化3600秒
- 原生退出宽限120秒
- TERM升级宽限30秒
- RAW保存300秒
- 日V4和NetCDF回读1200秒
- 封存/本地同步1200秒

每段持续时间和累计绝对截止取较早者，不把提前结束时间追加到优化预算。复用已验收完整LP时不得为凑流程重建。正在进行的旧构建仍遵守自己的原授权窗口，不因本条扩展。

正常计算由独立进程监督，不依赖Codex会话或浏览器常开。无已取消的费用门槛，不自动关机或释放实例。

## 8. 原生返回、科学验收与保全

记录GRBoptimize返回码与模型Status为两个独立字段，附run_id、采集时间、模型身份、SolCount、Runtime、迭代数及可用质量属性。

先保存合法可取得的原生X/Pi/RC及SHA，再转换原单位并验收。SolCount=0且属性不可用时记录NOT_AVAILABLE，不把预分配partial文件当有效解。非最优终态如有合法向量也应保全，但不能因此称最优。

日V4阈值/公式不变；不把C01R输入舍入预算加进物理残差容差。Scheme A源修订、输入表示差与求解残差分别报告。

终态分别处理：
- OPTIMAL且日V4与规定保全全部通过：DAILY_DIAGNOSTIC_PASS；不是2920时段Gate6 PASS。
- OPTIMAL但验收失败：OPTIMAL_BUT_NOT_ACCEPTED。
- INFEASIBLE、INF_OR_UNBD、TIME_LIMIT、NUMERIC、MEM_LIMIT等：如实分类，保存证据，不自动改参或恢复DualReductions诊断。
- 科学检查通过而同步未完成：SCIENCE_PASS_DELIVERY_PENDING。

后处理失败只能处理已存解和证据；不能重新求解。无法本地同步则保留云端原件、文件大小/SHA和LOCAL_SYNC_PENDING。

## 9. GitHub、ZIP与完成边界

使用核实后的独立分支，保留C02/C02R及前两次Gate6历史，不改main、不force-push、不自动合并。更新项目台账，将构建、实际优化、科学验收、备份分列，不能把“拟执行”写成“已执行”。

同一任务提交并push代码、测试及轻量证据；GitHub临时不可用标记GITHUB_SYNC_PENDING，不中断正常云端求解，不伪称推送成功。

交付主报告C03_DAILY_DIAGNOSTIC_RESULT.md，附本轮两项补丁、接口测试、构建/原生交接、参数、真实终态、日V4、资源与备份回执。合并打包C02R_C03_DAILY_DIAGNOSTIC_REVIEW.zip，含相对路径、文件大小、SHA256和CRC清单，给出实际本地路径；仅有云端副本须明确标注。

大矩阵/NetCDF/大向量保留在指定产物目录，提供SHA和备份状态，不塞进审阅ZIP或推送GitHub；不提交许可证、令牌或凭据。

若未进入优化，报告必须说明是哪个具体门槛失败，并给出证据，不能再仅因“C02完成，应等待普通审批”结束。

本条只授权一个365日诊断，不授权完整2920时段Gate6、其他情景、新的科学模型修订、IIS、feasRelax、独立presolve或第二次优化。正式optimize内部的正常Presolve仍按冻结配置执行。

完成结果与交付后停止。
