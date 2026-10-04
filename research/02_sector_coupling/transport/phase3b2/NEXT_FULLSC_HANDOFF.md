# Full-SC assembly交接（计划，不在本轮执行）

Transport研究范围已关闭，表示规范按用户本轮决定冻结。可执行模型尚有G1–G3门槛；先Human Scientific Review。本轮不启动Phase4、不求解Integrated/Disconnected、不新增交通深入轮次。

## 固定身份与可复用成果

- P paper reference：`5bacad702ccfed17ad19ab510fa710651e966f2c`。
- U current SC：`a3616a68ee44592af6527ca9024a90f1956646ae`。
- Buildings validation：`50a73d8f531132c5459174a55cac412d5f684462`。
- Future Research Model当前仍U身份；不能把它当已有Buildings+Transport合并模型。
- Shipping完整候选：`85a32dc231458fd753445df38d422b78435b8aad`，独立 `codex/transport-shipping-reviewable-patch`，17项离线回归PASS；其历史包含分配修复`512c6cc2`及Load目标守卫`cf4b0f81`两项独立功能分支/提交。需要审阅后再决定集成；本轮未合并。
- 本轮三张CSV分别记录首版边界、逐项候选测试、materiality收口；44项四类燃料原值及精确源行在证据JSON。旧原始大文件/网络不重算。

## 最小后续工作顺序

**G1：一份接受输入清单。** 使用现有原行和缓存，逐国逐目标年给每个账户唯一ID：source/raw/unit/year/currency（如适用）/HHV-LHV（燃料适用）/转换/当前值/候选值/接受人及记录。先处置shipping by/in漏筛、缺失和空集零，明确aviation kerosene覆盖；再接受联合R与EV energy-share、分载体残余及父电/父燃料包含关系。表示决定已冻结，不再问车型或船型。真正缺文件只请求对应缺失账户的原记录/版本，不能要求用户重找全套数据。

**G2：在独立组装验证层实现。** 采用项目配置/脚本覆盖；road使用最终能耗规范、固定EV曲线；rail能源并入被证明的direct账户一次；四个fuel obligation ID与共享供给分开；评审shipping候选。构建后只做源账→节点→时间守恒、组件互斥、无NaN、无EV灵活性、FT/CO2/热/H2连接和供给可达检查。禁止把可用源量缺失改为零。工程修复、数据纠正、研究配置分别提交，带why与受影响约束。

**G3：统一碳会计。** 保持原Power绝对轨迹及有效配置值，实现Policy/Reporting两个守恒视图；处理共享SMR/H2/CO2信用，保留rail燃烧。回归paper范围等价与新增非电义务不污染power约束的静态测试。使用同一实际物理流，不复制一套能源系统。这是范围保持工程，不是新增国家碳政策。

三门槛通过并获科学复核后，才能声称首版Transport可用于Full-SC组装。是否进入全年实验，仍由全模型其他部门、碳范围、外部commodity边界及共同确认状态决定，不因Transport单模块通过而自动授权正式求解。

## 接口与最低验收清单

| 接口 | 验收数据 |
|---|---|
| account→source | 同country/year/commodity单位，缺失/零区分，版本hash与接受记录 |
| A*→direct+explicit | historical与target年各自exactly-once；不预装未来EV/制燃料电力 |
| direct fuel→road/rail/domestic obligations | 转移前后逐燃料守恒；bunker单独记录；rail保量/保排放 |
| annual→nodes→snapshots | 所有数量/权重有限非负；国别和/两类bunker各自守恒；时间权重可追溯 |
| fuel demand→FT/H2/CO2供给 | 同服务无额外H2或电Load；合法来源、辅助能源、成本和网络可达 |
| emissions→Policy/Reporting | 同一事件一份物理量；发电留Power；transport直接燃烧报告；信用不重领 |

未来正式run manifest沿项目规范记录run_id、git_commit、config_files、input_data_hash、environment、solver、start/end、objective、status、output_hash；本轮manifest明确solver_runs=0、正式模型修改=0、候选功能修复=2、候选提交=3（含Git换行保真）。Integrated/Disconnected需共用同一接受义务并另行冻结关闭哪些跨境carrier、保留哪些外部imports；不在Transport任务内擅自决定。

主要限制：aggregate energy场景不是服务优化；港口/机场/国家权重和简单时序不是活动观测；固定年度fuel不证明系统价值对时序完全不变；燃料规格聚合、生命周期范围外项公开披露即可。不追加微观研究或新的Transport阶段。
