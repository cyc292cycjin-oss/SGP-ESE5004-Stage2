# Stage2项目总台账

2026-10-12，当前审计分支 `audit/stage2-b01-b02-physical-feasibility-20261012`；方案A实施分支仍为 `fix/stage2-exact-source-closure-a-v1`。本文件汇总已有阶段状态，不替代历史验收或授权新实验；详细证据见 [Baseline台账](05_baseline_evolution/20261011/BASELINE_EVOLUTION_LEDGER.md)。

| 工作 | 当前状态 | 证据/边界 |
|---|---|---|
| Gate5历史验证 | 保留旧结论，未重跑 | 不因源修复回写旧结果 |
| 第一次Gurobi Gate6 | OPTIMAL / V4 NOT_ACCEPTED | 历史不改 |
| 第二次P2 Gate6 | INF_OR_UNBD / SolCount=0 | 历史不改 |
| G6-05 | PAUSED_BY_USER | 无新优化授权、未恢复 |
| S0/A-01/A-02/A-03/A-04 | 已完成对应有限审计 | 详见Baseline台账，UNKNOWN保留 |
| 旧完整LP证书 | FULL_LP_EXACT_INFEASIBILITY_CERTIFIED | 对旧binary64模型仍成立 |
| 方案A科学批准 | USER_AND_CHATGPT_APPROVED | 仅批准180项最小派生Q修订 |
| 方案A源实施 | SCHEME_A_STATIC_ACCEPTED | 385/385 D≤Q′；新源Version Manifest SHA `a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720` |
| 新源版本求解 | NOT_RUN / NOT_AUTHORIZED | 未组装新完整NetCDF或LP |
| A-05 | A05_COMPLETE_WITH_EXPLICIT_UNKNOWNS | 跨境载体/静态端口/上游共同池/未来电力候选谱系；新独立PR |
| A-06 | A06_COMPLETE_WITH_EXPLICIT_UNKNOWNS | 政策/成本/资源六身份对照，17项静态核验；独立PR |
| B-01/B-02 | B01_B02_COMPLETE_WITH_EXPLICIT_LIMITS | 本地供给必要条件、CC/FT/油消纳联动，15项独立轻量核验；未构模/求解 |
| B后续 | PLAN_ONLY_NOT_AUTHORIZED | 本轮结束后等待联合审阅 |
| C/D | PLAN_ONLY_NOT_AUTHORIZED | 365日诊断/2920时段Gate6 |
| E/F | PLAN_ONLY_NOT_AUTHORIZED | 跨境载体扩展/互联独立成本实验 |

实施里程碑 `fe4be3d25b7a5a7283a608c580085b26fa6b1f1e` 已推送；验收及交付提交记录在本轮发布回执。没有将本地成功冒称正式模型求解成功。

验收里程碑 `bfd619df747bd94559137ff4f32ef7254c89a58b` 已推送；独立实施 [PR #4](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/4) 已创建，未合并。原审计PR #3保持不变。

## A-05发布与科学边界

从原审计commit `53c2b28632cb577136d48ebb843823967f0b1c25`分出，单独提交文档和轻量JSON；未向方案A PR #4、main或冻结科学文件写入。最新方案A状态来自真实交付commit `8883de6fb3e15767c632ac92f535e8a423e90b69`。

已核19AC+5DC跨境、400独立外部化石供给、无非电跨国物理共享路径、100本地H2节点的FT/回电用途。当前电网沿论文2025，论文2050新增15项跨境记录未继承；科学取舍待用户判断。Integrated/Disconnected仍未执行正式网络干预。

报告与证据：`research/05_baseline_evolution/20261011/a05/`。16项轻量一致性核验PASS。强制ZIP `A05_CROSS_BORDER_CARRIER_AUDIT_REVIEW.zip`附相对路径、大小/SHA和CRC。实际commit、远端与PR/ZIP指纹见发布回执。A-05结束即停止；不自动进入A-06/B—F，不恢复G6-05。

### A-05真实发布里程碑

- 已commit并push：`b6b914c0eef684a6e8d8d385b307848580e01fe6`。
- 独立审计分支：`audit/stage2-a05-cross-border-20261011`；[PR #5](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/5)为OPEN/DRAFT，base为原审计分支，未合并。
- PR #3/原审计HEAD仍`53c2b28632cb577136d48ebb843823967f0b1c25`；PR #4/方案A HEAD仍`8883de6fb3e15767c632ac92f535e8a423e90b69`。
- 最终交付commit及ZIP指纹见包内PACKAGE_MANIFEST与本地发布回执。当前工作到此停止，等待联合审阅。


## A-06发布与A阶段综合状态（2026-10-12）

用户已联合审阅A-05后授权；本轮起点为A05交付`4e00897199d28c72b35f6cff550b30ba94337e06`，独立分支`audit/stage2-a06-policy-cost-resource-20261012`。A05 PR #5及方案A PR #4未追加提交，main未改。

- **A06_COMPLETE_WITH_EXPLICIT_UNKNOWNS**：作者2025仅lv_limit；作者2050另有100MtCO₂/年cap；当前Baseline只有lv_limit、policy关闭。三网络均2920×3h。当前不能称net-zero；运行时封存hook与NetCDF表区别明确。
- VERIFIED：400个有价外部化石源无有限供应上限；807固定终端商品价仍NULL；共同生物质/褐煤/CO₂池与本地核算边界不等同。未知全系统价格/排放不置零。
- VERIFIED：V3最终有效台账SHA核对，10,628,915列扰动、offset−12788967.997821666；固定FOM8224491125.573893一次计费。P2只坐标变换，V3改变目标排序；不把旧失败候选作为经济结论。
- VERIFIED/UNKNOWN：作者2050额外15跨境资产兼有项目输入和历史优化容量；新建/升级/考虑中分类按原CSV与源码，7AC逐行来源及升级容量中间链尚缺。当前2025电网选择机制明确，15项逐项科学取舍理由UNKNOWN。
- 17项本轮静态证据一致性检查PASS；复用A03/A05、Scheme A及Gate6真实回执，未重跑旧实验或大矩阵/大向量扫描。报告在`a06/`，新增成本可比性和科学决策登记表。
- A阶段已完成各自授权的证据审计，不代表全LP可行或全部科学边界终审。方案A仍SCHEME_A_STATIC_ACCEPTED/未组装；旧证书及两次Gate6历史不改。G6-05 PAUSED_BY_USER，B—F未启动。
- 下一步只建议用户审批B阶段物理/输入必要条件审计；候选电网、外部供给、NULL成本和未来政策范围列为科学决策，不实施。独立PR与ZIP发布身份由真实发布记录给出。


### A-06真实发布里程碑

- 审计/17项新静态检查里程碑 `f88230d6bb6bd44631fa12f586857848173baa37` 已commit并push。
- 独立分支 `audit/stage2-a06-policy-cost-resource-20261012`；[PR #6](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/6)为OPEN/DRAFT，base为已审阅A05分支；未合并，没有对PR #4/#5追加提交。
- 原审计/方案A/A05远端身份分别仍为`53c2b28632cb577136d48ebb843823967f0b1c25`、`8883de6fb3e15767c632ac92f535e8a423e90b69`、`4e00897199d28c72b35f6cff550b30ba94337e06`。
- 最终交付commit和ZIP整体SHA见包内PACKAGE_MANIFEST与外置A06_FINAL_DELIVERY_RECEIPT.json。ZIP名A06_POLICY_COST_RESOURCE_AUDIT_REVIEW.zip，含当前报告、台账、轻量证据/方法、相对路径大小/SHA及实际CRC记录，不含大科学文件或凭据。
- A阶段审计完成但UNKNOWN保留；G6-05仍PAUSED_BY_USER；本轮到此停止，B—F需后续单独授权。

## B-01/B-02资源与转换路径审计（2026-10-12）

本轮独立于Scheme A PR #4和A06 PR #6，起始A06提交`85397fdfd587a4e0cda298139b3c8f43fbbc6d6a`。Scheme A固定对象仍`8883de6fb3e15767c632ac92f535e8a423e90b69`，新源配方仅作为审计输入，不擅自合并或组装。

385组新源精确年度条件全部通过；1737个实际Load均有已核本地路径，未发现本轮范围内供给断路/单体界矛盾；未证明全LP联合可行。100节点SMR CC捕集必须跟随FT，需额外H₂和电力，并受有限本地油消纳限制。当前无CO₂ cap/地质库不等于无碳守恒，也不能直接解释历史求解失败。

风险/科学决定见`05_baseline_evolution/20261011/b01_b02/B_PHYSICAL_FEASIBILITY_RISK_REGISTER.md`，继承A06的无限外部市场、2025电网候选、NULL成本/排放和未来政策待决边界。没有新的科学修改、优化授权、AutoDL操作或G6-05恢复。B后续及C—F保持未执行。

交付B01/B02报告、风险登记、轻量证据、独立方法及`B01_B02_PHYSICAL_FEASIBILITY_REVIEW.zip`，含清单/大小/SHA/CRC。实际commit、远端及独立PR由发布里程碑记录，不把本地结果冒称已推送。


### B-01/B-02真实发布里程碑

- 审计及15项独立轻量核验提交`b83a0f215bacdba83e34ba226d9b82d99b608786`已commit并push。
- 分支`audit/stage2-b01-b02-physical-feasibility-20261012`；独立[PR #7](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/7)为OPEN/DRAFT，base为已审阅A06分支。没有合并任何PR。
- A06远端仍`85397fdfd587a4e0cda298139b3c8f43fbbc6d6a`，Scheme A远端仍`8883de6fb3e15767c632ac92f535e8a423e90b69`；未把新源配方冒充已运行网络。
- 最终交付commit和ZIP整体SHA见包内PACKAGE_MANIFEST和外置`B01_B02_FINAL_DELIVERY_RECEIPT.json`。同次交付`B01_B02_PHYSICAL_FEASIBILITY_REVIEW.zip`，保留相对路径，逐成员大小/SHA/CRC核验，不含矩阵、原始向量、NetCDF或凭据。
- 当前B-01/B-02完成即停止；全LP可行性NOT_PROVEN，G6-05保持PAUSED_BY_USER，后续B/C—F未启动。


## B-03收口与C-00日诊断设计（2026-10-12）

本轮从已审阅B01/B02交付`14baa96de5778ab487cbe9017d660825dc0a9a62`创建`audit/stage2-b03-c00-daily-protocol-20261012`。状态**B03_C00_DESIGN_COMPLETE**；不修改PR #4源版本或PR #7历史结果，不合并任何PR。

- B03最终12项风险使用PROVEN / NECESSARY_CHECK_PASS / RISK / UNKNOWN；旧精确矛盾与Scheme A源修复分开，1737供给路径/807账户是必要条件，不证明新LP可行。未发现本轮必须先实施其他物理修复的直接证据。
- C00设计365×24h三权重与8760年量；保持Scheme A Q、所有原需求年度身份、技术/网络/政策边界。时变Load的binary64年度相等未实际验证，设NO-GO硬门槛，禁止静默补Q/减Load。CF/入流表示规则待联合批准。
- 首次真实154项参数小回执已对备份SHA核对；基准含NumericFocus0/FeasibilityTol1e-6/DualReductions1，非P2/非G6-05。建议新TimeLimit≤3600、全流程9150秒，仅设计无授权。原固定组缩放规则重绑日维度，旧V3/D/R向量不可复制。
- V4科学阈值保持；原合同含旧维数，日适配需独立binding和实现验证，未虚报通过。未来一次流程涵盖身份、组装、原生交接、唯一调用、raw优先、全部验收和备份；无新准备实验。
- 新日模型与旧Gate6同时存在Q版本和时序差异；日PASS不等于2920可行或原始目标严格最优。师哥建议尚未动态验证。
- G6-05继续PAUSED_BY_USER；新网络/LP/solver/AutoDL操作均0，C实际测试及D—F未启动。交付三份主报告、轻量证据/方法、最新台账和强制ZIP；最终commit/PR/ZIP SHA见发布记录。

实际报告目录：`research/05_baseline_evolution/20261011/b03_c00`。


### B-03/C-00真实发布里程碑

- 报告、协议及37项轻量设计核验提交`40331c99d208c66d6c283df4397831f712dba90d`已commit并push。
- 分支`audit/stage2-b03-c00-daily-protocol-20261012`；独立[PR #8](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/8)为OPEN/DRAFT，base为已接受B01/B02分支；未合并任何PR。
- B01/B02远端仍`14baa96de5778ab487cbe9017d660825dc0a9a62`，Scheme A远端仍`8883de6fb3e15767c632ac92f535e8a423e90b69`。没有对科学源码/方案A或旧结果追加修改。
- 最终提交与ZIP SHA/CRC由PACKAGE_MANIFEST及本地B03_C00_FINAL_DELIVERY_RECEIPT.json记录。设计完成不等于实际测试获准；日构模/求解尚未执行，G6-05继续暂停。交付后停止，等待联合审阅。


## C-01日聚合表示预检（2026-10-12）

从已核C-00提交`5d757c5a4a9dad965d9c7cbe6e55d486d167ff93`建立独立`audit/stage2-c01-daily-representation-20261012`。**C01_REPRESENTATION_DECISION_REQUIRED**，不是日模型构建/优化授权。

- VERIFIED：冻结NetCDF只有3类非空动态属性（1737 Load、460 CF、40 inflow），2920×3h完整日历；源NPZ/各实际Load SHA与Scheme A引用吻合，无实际NaN/Inf/负值或缺桶。161既存零源列保持原状。
- EXACT：Load1642条年度相等，52正漂移、43负漂移；95条均时变电Load；最大绝对差159/137438953472≈1.1568772606551647e-9 MWh。31542个日Load均值不可单字精确表示，不能用isclose放行。
- VERIFIED：460 CF和40入流的全部序列化误差均在半ULP累计表示界；6条CF的44个原值1+1ULP未裁剪。385生物质组年度精确不变且D≤Q′，807 Q不改不重新派生。
- PROPOSED_NOT_APPLIED：仅提出一个非负双字常数表示方案，数学上保留每日精确均值及科学年度量；31542格可能需固定数值辅助项，必须保留至CSC/验收，普通同Bus拆Load再浮点求和不足。等待用户批准，不实施。
- 独立16类轻量证据检查及2237代表桶整数舍入复核通过；未重复旧LP审计、未构模/求解、未操作AutoDL。G6-05继续PAUSED_BY_USER，C执行门槛保持NO-GO直到表示决策；D—F未启动。
- 报告与证据目录`research/05_baseline_evolution/20261011/c01`；同轮commit/push/独立PR和强制C01_DAILY_REPRESENTATION_REVIEW.zip，最终发布记录给出真实SHA/CRC。交付后停止。


### C-01真实发布里程碑

- 实际聚合、轻量独立验证及报告提交`0a93200588fd193a727e5939acea199a154821de`已commit并push。
- 分支`audit/stage2-c01-daily-representation-20261012`；[PR #9](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/9)为OPEN/DRAFT，base为已审阅C-00分支，未合并。
- 原C-00远端仍`5d757c5a4a9dad965d9c7cbe6e55d486d167ff93`，Scheme A仍`8883de6fb3e15767c632ac92f535e8a423e90b69`。没有改写原始输入、旧结果或消费标记。
- 最终commit、C01_DAILY_REPRESENTATION_REVIEW.zip大小/SHA/CRC由包内清单及本地C01_FINAL_DELIVERY_RECEIPT.json记录。C01_REPRESENTATION_DECISION_REQUIRED，日构模/求解仍NO-GO，唯一候选未实施。交付后停止，等待联合验收。


## C-01迁移至122：证据复用与最小只读入口（2026-10-12）

- 科学状态保持 **C01_REPRESENTATION_DECISION_REQUIRED**：95条时变电Load有非零年度表示差；385/807 Scheme A精确关系保持；候选修订仍未批准/未实施。
- 已核原C01提交 `efb0ddb5b66c0305715d285c9d622ed65228b728` 的轻量证据SHA和旧ZIP CRC；Scheme A PR #4固定Git对象仍匹配。没有因迁移重做时序积分。
- 122环境为USER_REPORTED；尚未连接实例或取得新云端身份回执。提供独立 `c01/instance122/c01_122_readonly_identity.py`，只核迁移NetCDF SHA及动态元数据并生成新JSON。可选核已存在的Scheme A四文件，不假定配方已部署。
- 122状态 **AWAITING_USER_JUPYTER_READONLY_RECEIPT**；当前无GO。入口本地合成测试不等同于云端执行。报告 `c01/instance122/C01_INSTANCE122_READONLY_HANDOFF.md`。
- 本轮独立分支 `audit/stage2-c01-instance122-handoff-20261012`；commit/PR见发布记录及交付Manifest。新ZIP保留原C01 ZIP，放在独立实例交接目录；无NetCDF、大向量或凭据。
- G6-05仍PAUSED_BY_USER；新网络/LP/求解/AutoDL操作均0，不自动进入C模型构建或后续阶段。


### C-01 / 122只读交接发布里程碑

- 交接入口、16项本地检查及报告提交 `c872806117aebb8216c8b5f883e71ca8d6d648a4` 已push。
- 分支 `audit/stage2-c01-instance122-handoff-20261012`；独立 [PR #10](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/10) 为OPEN/DRAFT，base为原C01审计分支；未合并或改写旧分支。
- 122实际身份回执仍待用户Jupyter返回；当前仅复用原C01证据，科学结论仍DECISION_REQUIRED。新交付的最终commit和ZIP SHA/CRC记录在PACKAGE_MANIFEST及本地最终回执中；旧ZIP保留。G6-05保持暂停，无构模/求解/AutoDL操作。


## C-01R受限binary64准入及协议冻结（2026-10-12）

- 用户与ChatGPT明确批准方案一，仅修改365日时变电Load输入表示准入。**C01R_REPRESENTATION_ACCEPTED**；不是科学需求、物理阈值、C02构建或求解授权。
- VERIFIED：1737 Load，1642年量精确；95漂移（52正43负）全部通过日最近值/年度半ULP/绝对2e-9MWh/相对1e-15 AND；源数据与原C01结果一致。Scheme A 385/807精确关系及四字段不变，V4 SHA不改；无新动态属性。
- 独立验证从原NetCDF重读，以整数dyadic加总/IEEE754舍入复核35,040时变日格及598,965平坦格恒定证明；3492实际中点和9组边界/拒绝检查通过。未构模/求解/连接AutoDL。CF/入流复用已核证据，既有44个CF>1一个ULP不裁剪。
- 新协议 `C00_DAILY_365_PROTOCOL_C01R_V1` SHA `661a81e532184003938213a3e81ad35bd4a687108332d14b3582bf7a8eac2856`；机器规则SHA `49d85c8449b32bb1fbf972b564dacb70a12e918dee58e4678efc36f0c736b140`。原C00文档逐字保留，旧GO清单存history，原C01决定及双字候选保留历史；双字方案未实施。
- 目录`research/05_baseline_evolution/20261011/c01r`；独立分支`audit/stage2-c01r-bounded-binary64-20261012`。Git真实commit/PR见发布记录，强制ZIP同轮交付；没有改main、Scheme A或合并旧PR。
- 仅具备申请C-02受控构建审查的表示前提；C02/C03未授权/未执行。G6-05继续PAUSED_BY_USER，后续阶段不自动启动。等待联合验收。


### C-01R真实发布里程碑

- 受限binary64规则、独立源级验收及版本化协议提交 `4db15881c40875b4385790c88382c664faad977b` 已push。
- 分支 `audit/stage2-c01r-bounded-binary64-20261012`；独立 [PR #11](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/11) 为OPEN/DRAFT，基于已核C01/122审计分支，未合并任何PR。
- 当前C01R_REPRESENTATION_ACCEPTED，95条漂移全部AND通过，385/807精确关系和V4不变。只具备申请C02审查的表示前提；无构模/求解/AutoDL操作，G6-05暂停。
- 本轮最终commit和ZIP整体SHA/CRC在PACKAGE_MANIFEST及外置C01R_FINAL_DELIVERY_RECEIPT.json记录。旧C00和C01历史保留；交付后停止。


## C-02受控构建真实交付（2026-10-12）

**C02_BLOCKED_WITH_SPECIFIC_EVIDENCE**。用户授权仅build-only，已在122执行唯一一次365日日网络组装和Linopy模型创建，未调用任何优化/原生Gurobi/WLS。

- 固定C01R基线68ebb96b7d48318654e9ca3f2b2780a0133bc889；Scheme A PR #4对象8883de6fb3e15767c632ac92f535e8a423e90b69。未合并旧PR或修改原科学源码。
- 新未求解NetCDF真实导出/回读，365×24h三权重各8760h；1737 Load/460 CF/40入流全部匹配已接受日值SHA；180Q/627不变及385精确D≤Q′在网络层通过。
- 实际Linopy持久化标签2,450,005列、6,042,238行，807资源方向块及196电池耦合已生成。Store动态RHS位比较停止；完整稀疏矩阵、NNZ、全部行界/R与日V4绑定没有完成。
- 新检查器对±0的误拒绝由冻结PyPSA表达式及微型算术证实；原失败RHS未逐元素保存，其他差异不能完全排除。没有将此异常称为数学不可行，没有重建/重试。
- Run c02_daily_build_20261012T025604Z_fcc0f784；1800秒固定窗口，约60.24秒失败、61.17秒轻量封存；worker/supervisor/guard已退出。90GiB/12核准入，cgroup峰值约2.91GiB，未触发保护。
- 新NetCDF及轻量回执本地SHA/CRC通过；部分列/标签数组云端保留、本地LOCAL_SYNC_PENDING；报告/逐产物SHA见c02目录。云端封存成功不等于完整LP存在。
- C03 NO-GO；G6-05继续PAUSED_BY_USER；后续完整build-only重新执行需用户审阅后另行批准。未进入任何求解或D—F。
- 独立分支codex/c02-controlled-daily-build-20261012。真实发布commit/PR/ZIP身份见后续发布记录；代码、回执、台账与强制C02_DAILY_BUILD_STATIC_REVIEW.zip同轮交付。失败版本和旧报告原件保留。


### C-02真实发布里程碑

- 实际受控构建、部分产物SHA和阻断证据提交 `e89f96814fabf11826ca6f365b871e8f70a5c3e0` 已push。
- 分支 `codex/c02-controlled-daily-build-20261012`；独立 [PR #12](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/12) 为OPEN/DRAFT，base为已核C01R分支；未合并main或任何历史PR。
- C02_BLOCKED_WITH_SPECIFIC_EVIDENCE：新网络回读通过，完整LP导出和日V4绑定未完成；没有重试或求解。失败版本和实例均保持，G6-05暂停，C03未授权。
- 同轮审阅ZIP包含报告/最新台账/轻量证据/代码及成员SHA、大小与CRC记录；最终提交和ZIP整体SHA由本地 `C02_FINAL_DELIVERY_RECEIPT.json` 记录。用户上传ChatGPT联合审阅后再决定修复及新窗口。


## C-02R最小检查器修复准备（2026-10-12）

- C02R_CHECKER_PATCH_READY_FOR_REVIEW：只在c02r/candidate创建新SHA版本；原C02失败代码/Run/消费标记/部分产物不变。本轮无云端连接、无网络/LP构建、无solver。
- Store动态/库存界、最终Bus RHS及对应导出行界采用零容差精确语义比较；±0相等，非零1 ULP、NaN/Inf异常、shape/方向/界错误拒绝。原bits函数与11个保留位检查不变；Scheme A/C01R/V3/V4/成本不改。
- 34项独立小型与候选循环接线测试通过；仅NumPy/pandas/xarray替身，没有PyPSA/Linopy对象。失败记录完整资产/家族/行号/hex且不覆盖。
- 另有确定的既有counts[fam]>0覆盖断言，会拒绝3个已核+Inf上界的零行家族；不属本轮±0修复，未擅改。新完整构建仍需明确处置此阻断和取得独立C02R运行授权。
- 优先复用封存日NetCDF的方案仅记录未执行。C02整体仍BLOCKED，完整矩阵/目标offset/日V4绑定未完成；C03未授权，G6-05保持PAUSED_BY_USER。
- 继续独立codex/c02-controlled-daily-build-20261012分支和PR #12，不改main/旧PR；本轮真实commit和ZIP身份由发布回执记录。


### C-02R真实发布里程碑

- 候选补丁、34项小型检查、未修复零行覆盖阻断及台账提交 `6270883d679108e4af7aaaf655a6655ecc0e2d49` 已push。
- 继续 `codex/c02-controlled-daily-build-20261012`，已更新 [PR #12](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/12)，仍OPEN/DRAFT，未合并。
- 状态C02R_CHECKER_PATCH_READY_FOR_REVIEW；C02整体仍BLOCKED，未获新的C02R运行授权；没有云端连接/模型构建/求解，G6-05仍暂停。
- 强制ZIP为C02R_MINIMAL_CHECKER_REPAIR_REVIEW.zip；最终Git提交、大小、SHA与完整CRC记录由本地C02R_FINAL_DELIVERY_RECEIPT.json给出。等待用户与ChatGPT复核。


## C-02R→C-03合并授权的真实终态（2026-10-12）

**C02_BUILD_STATIC_ACCEPTED_NO_SOLVE；C03 OPTIMAL_BUT_NOT_ACCEPTED。** 以下是后续新增授权与实际执行，不改写前述C02失败、未授权时点或旧Gate6记录。

- 用户确认合并附件后，独立分支`codex/c02r-c03-daily-diagnostic-20261012`实施两项限定检查器修复、CSR→CSC桥接、365日实际标签恢复及冻结V4调用链。生产代码里程碑`a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7`已push；独立PR #13，未合并main/历史PR。
- 122唯一Run `c02r_c03_daily122_20261012T044259Z_25e62c10`。复用SHA匹配日NetCDF，不重聚合或派生Q；Scheme A 180改/627不变、385精确D≤Q′。±0语义和三类经证实+Inf零行检查通过，45项局部接口测试通过。
- 实际日LP2,450,005列/6,042,238行/11,403,496非零；完整CSR反向重排与原生逐值回读通过。同一原生模型只调用一次GRBoptimize；154项参数回读，较首次Gate6只有授权TimeLimit变为3600秒。WLS真实启动通过，未使用P2/G6-05。
- 真实Status=2、返回码0、SolCount1，69次Barrier，Runtime155.370943秒；X/Pi/RC完整合法保存。日V4失败：48,298矩阵行、4,304 stationarity列、365对偶符号项；377/807账户、111/385义务组失败，年度超用约0.338138TWh，Bus最大8.320791MW。1849工程检查1470PASS/379FAIL。FOM一次计量与NetCDF逐值回读通过，不能抵消物理/KKT失败。
- 旧2920目标/物理和新Scheme A日模型必须区分；当前结果不证明LP数学不可行，也未定位全部根因。原科学未扰动目标最优性NOT_PROVEN、完整系统成本仍不齐全。不能转入2920或Integrated/Disconnected。
- worker/supervisor/guard全部退出，无遗留PID；RSS采样最大4.309GiB，cgroup峰值6.149GiB，计算保护无触发，固定总9150秒未延长。云端17,417文件/1,946,512,966字节封存。完整本地同步LOCAL_SYNC_PENDING：239,468,544/314,868,916字节保留partial，收尾截止后5秒轮询产生3.313344秒停止延迟，已明确披露；没有重试或改deadline。轻量证据SHA/CRC通过，不能替代完整本地备份。
- 报告及真实机器证据：`research/05_baseline_evolution/20261011/c02r_c03/C03_DAILY_DIAGNOSTIC_RESULT.md`。同轮强制ZIP `C02R_C03_DAILY_DIAGNOSTIC_REVIEW.zip`含成员SHA/大小/CRC，大型数组不提交。结果发布的完整commit/ZIP SHA见FINAL_DELIVERY_RECEIPT.json。
- 实例122保持运行，未关机/释放；G6-05继续PAUSED_BY_USER。已消费本次唯一诊断授权；没有自动重试、参数改变、容差放宽、后续实验或第二次optimize。交付后停止，等待联合审阅。


## C-04日模型定向失败模式与完整备份（2026-10-12）

**C04_READY_FOR_ONE_CONTROLLED_DAILY_TEST；下一次求解未授权。** C02R构建与交接完成，C03仍OPTIMAL_BUT_NOT_ACCEPTED。

- 仅针对 c02r_c03_daily122_20261012T044259Z_25e62c10。独立60分钟文件窗口实际传输796.201秒；前缀SHA核验后接收剩余75,400,372字节，旧partial保留，无网络重试。完整归档SHA d484db824ce041a81b000484dfe6298d32bfb16145e8dab26db3fd2a6c377019；17,417项/1,946,512,966字节、CRC、安全路径和immutable references通过，LOCAL_BACKUP_SHA_VERIFIED。旧PENDING回执保留。
- 两次377账户/111义务组失败集合一致；1/2账户组全通过、3/4全失败。13个同国家/部门/D分层仍同时有成败；规模匹配不能消除子部门、商品组合混杂，不作因果断言。
- 7组19账户51,100个完整CSR行、159个精确局部行复算；负库存18,298.406 MWh和Bus超供8.320791 MW真实存在。所选原始X/D、原单位与NetCDF一致。日CSC仅单遍确认4304 stationarity失败（3966 AC Line-s、338 DC Link-p），365自由RC失败为Line52；未扫历史全年矩阵。
- 唯一提议为下一次日模型Aggregate=1→0，其余算法/科学身份不变；提议原生3600秒、全流程7200秒。当前未执行，不能把现有数据写成新对照结果或科学PASS。
- 报告、独立方法、轻量证据和备份回执见 c04/C04_DAILY_FAILURE_PATTERN_AND_NEXT_TEST_DECISION.md。独立codex/c04-daily-pattern-20261012分支关联PR #13；实际commit/push/新PR及强制C04_DAILY_PATTERN_REVIEW.zip由交付回执绑定。
- 未改变Scheme A/C01R/V3/V4/日LP/参数/旧解/消费标记；未操作实例电源或云端进程，G6-05持续PAUSED_BY_USER，2920时段及正式情景未授权。交付后停止。

- C04首个审计里程碑已提交并核实远端：`662d1de6037f4f8615eff61219e65ea3062fbcf6`；[独立PR #14](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/14)，基于PR #13交付分支，未合并。最终交付提交与ZIP身份见独立交付回执及包内清单。


## C-05 单因素Aggregate=0真实诊断终态（2026-10-12）

**C05_NUMERIC_NO_SOLUTION_NOT_ACCEPTED；云端及本地保全完成。** 此项为用户后续明确授权，C04提议时的未授权状态与旧结果原件保留。

- 独立Run `c05_aggregate0_daily122_20261012T074925Z_a39647d9`；生产commit `d6c48dbd95d12f0354561372e9a65d6e92511754` 已push。复用C03现成日CSC，2,450,005列/6,042,238行/11,403,496非零；17,369输入SHA通过，构建0、CSR→CSC转换0。WLS原生启动和同模型完整EXACT_READBACK_PASS通过。
- 154项实际数值参数只有Aggregate 1→0；TimeLimit3600、SoftMemLimit65GB、MemLimit1e100不变。唯一调用返回码0、Status12 NUMERIC、SolCount0、24Barrier、81.595145秒。无重试；不是数学不可行/无界证明。
- 无合法完整X/Pi/RC；真实状态/质量属性/日志已先保存。日V4、377/111模式、4304 stationarity及365自由RC变化均NOT_AVAILABLE，不记零、不伪造PASS。没有新NetCDF解或合格双账成本。
- 固定总7200秒未延长；实际至封存guard退出96.067秒。RSS采样3.444138GiB，cgroup lifetime peak6.249012GiB，保护无触发，所有本次进程退出；122实例仍运行/计费。
- 云端新增32项封存；新独立60分钟窗口传输6.526404秒。394,606字节新归档SHA `4b78d58396be73378ede9589a3bf3db56ad671a9643d82d50da7dd7b1e1bac63`，大小/SHA/CRC/安全路径/逐项BACKUP_INDEX核验通过，LOCAL_BACKUP_SHA_VERIFIED。旧17,369项输入按不可变引用复用；历史LOCAL_SYNC_PENDING不覆盖。
- 报告、参数差异、完整条件验收状态和方法见 `research/05_baseline_evolution/20261011/c05/`。独立分支codex/c05-aggregate0-daily-20261012，关联PR #13/#14；真实结果commit/PR及同轮C05_AGGREGATE0_DAILY_DIAGNOSTIC_REVIEW.zip由发布回执记录。
- 科学结果NOT_ACCEPTED；不能进入2920/Integrated/Disconnected/DEC。G6-05保持PAUSED_BY_USER。用户本次唯一优化授权已消费；不自动改变第二个参数或再求解。交付后停止。

- C05结果与全部索引脱敏日志已push并核实远端提交 `869d72a90376b1862cf2058576b01917131f0a12`；独立[PR #15](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/15)为OPEN/DRAFT，关联#13/#14，未合并。生产提交为`d6c48dbd95d12f0354561372e9a65d6e92511754`。最终审阅包导出提交和ZIP SHA见包内GIT_PUBLICATION及外部C05_FINAL_DELIVERY_RECEIPT。

## C06 final comparative closeout — 2026-10-12

- **C06_EXECUTION_ACCEPTED_SCIENCE_NOT_ACCEPTED**；Run `c06_barconvtol_daily122_20261012T095705Z_321aa0f1`，真实Status2/SolCount1/143 Barrier/282.179754秒，唯一optimize已结束，生产提交`34a34b69ef752d7809487ca609cd91e12f75bffd`。
- C03单因素BarConvTol 1e-6→1e-9，Aggregate1；154项实际参数核验。C05 NUMERIC/SolCount0，无可比较返回解。
- 资源账户377→85（无新增），义务组111→0；矩阵48298→243（均库存下界，无新增）；stationarity4304→3336（保留3291/新增45），自由RC365→0；目标差与加权stationarity L1恶化，不能宣称科学PASS。
- 原单位/原生三向量由已接收数据与D/R逆映射核得一致云端SHA；163局部行/5列精确核算支持真实返回点违规。科学模型、阈值及旧结果未修改。
- 云端封存完成；**LOCAL_SYNC_PENDING**：已收140640256/153715959字节，缺13075703，原60分钟窗过期且未重开。完整gzipCRC/BACKUP_INDEX待新传输授权；审阅ZIP不替代原始备份。
- 唯一建议为预算匹配等价坐标的受控日模型对照，PROPOSED/未执行，须另行批准。仍在C阶段，D及2920时段未获授权；G6-05 PAUSED_BY_USER。
- 详细报告：`research/05_baseline_evolution/20261011/c06/C03_C05_C06_COMPARATIVE_FORENSICS.md`；本轮独立分支`codex/c06-barconvtol-daily-20261012`，关联#13/#14/#15。真实结果提交与PR在Git发布回执绑定，不自动合并。


## C07 V4可靠性与有限补救收口 — 2026-10-13

- **A ORIGINAL_V4_FAIL；B NO_QUALIFIED_SOLUTION；C06/A/B LOCAL_BACKUP_SHA_VERIFIED。** 本轮新增调用恰好2，全部结束，未改科学模型或V4。方法/代码及初始终态里程碑提交`6a65bea3a92aa9fa9c209b911c9a4654c25c58aa`已push。最终交付提交见包内GIT_PUBLICATION。
- A `c07a_daily122_20261012T162928Z_0d9301f2`：Status2、SolCount1、153 Barrier、281.128073秒；807/385全部通过；剩1矩阵库存下界、3353 stationarity、12045对偶符号项失败。完整X/Pi/RC先保存后映射，NetCDF/FOM通过不替代V4。
- B `c07b_daily122_20261012T163744Z_4250e585`：仅Crossover0→−1；Status3、SolCount0、153 Barrier/511564 simplex、343.263406秒；向量及V4 NOT_AVAILABLE，未伪造零残差，也不称严格不可行证明。
- 同一日CSC、Scheme A/C01R/V3/V4，唯一D/R表达SHA5561a91045ca9196183e6d4ae61c9dde76d85343e8397d880b5c4652a6b5e77f；全量反变换及同模型真实回读通过，154参数A无差异、B仅Crossover。没有重建、warm start或额外presolve。
- V4在此冻结组内语义可推导，未发现必须放宽的冲突；合法Scheme A余量小于各预算，未启用V5。独立局部Fraction核算支持真实残差，详细剩余数值阻断见c07主报告。
- 两个Run均资源保护无触发并全退出封存。C06旧备份缺口已依新授权补齐；A/B全部新增文件SHA/CRC/索引通过，云端原件/历史消费标记保留。122实例未关机/释放。
- 唯一建议为成对原生回执和冻结表达的供应商定点复核；不自动对外提交私有模型或第三次优化。G6-05 PAUSED_BY_USER，仍C阶段，2920及新情景未授权。


## C08 日模型根因核实：零成本解耦资源块（2026-10-13）

**C08_ROOT_CAUSE_IDENTIFIED_READ_ONLY。** 由 Claude 在用户授权的只读范围内完成；新增优化、构模、AutoDL 操作均为 0；V4/Scheme A/C01R/D/R/成本及历史结果均未改动。G6-05 PAUSED_BY_USER。

- EXACT：807 个 fixed resource Store 与 807 个 final-energy meter Link 组成块：884,472 列、2,203,217 行。该块与其余 LP 完全解耦，块内成本全为 0；系数仅 ±1/−24，无列级界。块内 V4 失败与求解器无关。
- EXACT：块可行性证书。用 LP 的 binary64 数据逐行有理数核验全部 2,203,217 行，违约为 0。385 组 D≤Q；LP 坐标下的余量为 1.08e−19 至 4.13e−16，物理值 = 2^k × LP 值（k∈[0,28]），与 SCHEME_A_DAILY_EXACT_GROUPS 精确一致。
- VERIFIED：以下失败全部在块内——C06 的 243 条与 C07A 的 1 条矩阵失败行；C07A 的 12,045 项对偶符号/自由 RC；|y|>1e9 的 316,102 行（块内最大 4.3e14，块外最大 8.2e5）。C03/C06/C07A 的 stationarity 失败（4304/3336/3353 列）全部在块外。C07 实际改变的 884,472 个 D 和 2,203,217 个 R（新指数减原指数）全部位于块内，块外为 0。
- VERIFIED（非证书）：主 LP 对偶修复后，残差列为 5,326 列（Line-s 3376、Link-p 1931、p_nom 19），有限部分相对差距约 4.8e−7；严格下界未取得。
- INFERENCE：块余量远低于 FeasibilityTol 1e−6，是巨大对偶、多账户组敏感性的成因，也可能是 C07B Status 3 的成因（未证明）。
- PROPOSED（待授权）：方案 (a) 精确分解。块用精确有理数解，只对主 LP 做一次 Barrier+Crossover 求解，合并后按原 V4 全量验收，并预先写定判定规则。方案 (b)（修改 Scheme A 的余量）严格劣于 (a)。建议暂缓 C07 分层准入指令。
- 交付：`work/c08_block_decomposition_20261013/`，以及 `outputs/C08_BLOCK_DECOMPOSITION_REVIEW.zip`（含成员 SHA/CRC 清单）。GitHub 尚未推送：本会话 GitHub 账户待关联。
- 补记（2026-10-13）：C08 报告、证据和方法随分支 `codex/c09-exact-decomposition-20261013` 入库于 `research/05_baseline_evolution/20261011/c08/`，成员字节与 PACKAGE_MANIFEST 中的 SHA 逐个一致；以上条目原文未改。


## C09 精确分解后主 LP 单次求解 — 2026-10-13

- **R1：C09_DAILY_BASELINE_ACCEPTED（仅限日诊断，不是 Gate6/2920 通过）。** 本轮优化调用恰好 1 次，没有重试；V4、Scheme A、C01R、D/R、成本及科学约束均未改动。原始结果为 LOCAL_BACKUP_SHA_VERIFIED。
- run `c09_daily122_20261012T185116Z_b867e3d3`：只求主 LP（1,565,533 列 / 3,839,021 行 / 7,868,836 非零，冻结 C03 CSC 的纯限制），154 项参数中相对 C06 只改 Crossover 0→−1，与 C07B 相同。结果 Status 2、SolCount 1、145 次 Barrier（Barrier 以 sub-optimal 结束）、481,420 次 simplex、378.51 秒，ObjVal 428,014,041,779.74。
- 块（884,472 列 / 2,203,217 行）使用预构造的精确原始解，对偶取 0；运行时复核了解耦、零成本、行集合和残差（1.106e−16）。合并时主向量逐位拷贝。
- 原 V4 的 10 项门槛全部 PASS：矩阵失败行 0、列失败 0、stationarity 失败 0（最大归一化值 5.23e−14）、对偶符号失败 0；807/385 失败为 0；1,849 项物理检查通过；FOM 一次；NetCDF 精确回读；daily binding。相对目标差 2.85e−16。本地用冻结 CSC 独立重算，结果与云端逐项相同。
- 与 C07B（Status 3）相比，唯一区别是去掉了零成本块，结果与"块导致 C07B Status 3"一致（INFERENCE，单次运行，不是证明）。C07A 遗留的 3,353 列 stationarity 失败由 Crossover 基解清除；807/385 通过来自精确块解，与求解器无关。
- 资源：进程 RSS 峰值 3.53 GiB，cgroup 最小余量 82.64 GiB，保护未触发，所有进程已退出并封存。归档 59,076,784 字节，SHA `6209efc5…1104`。122 实例未关机或释放。
- 下一步（R1）：用同一分解准备 D 阶段，需要另行授权，本轮不执行。G6-05 仍为 PAUSED_BY_USER；2920 时段和情景未授权。报告见 `c09/C09_RESULT.md`。


## C10 日基线严格下界证书 — 2026-10-13

- **C10_RIGOROUS_LOWER_BOUND_ESTABLISHED。** 日 LP（含 V3 微扰的求解目标）的真实最优值 v* ≥ 428,014,041,321.65 EUR，无条件成立；C09 返回解的目标比它最多高 458.45 EUR（相对 1.07e−9）。本轮只读，求解调用 0 次，V4 和科学模型均未改动。
- 方法：弱对偶安全下界，使用 C09 的对偶，把 15,313 个符号错误的对偶置 0；r 按区间计算；对 3,839,021 行做界传播（全部向外舍入），并加入目标截断行，以及一条精确的按储能伸缩求和聚合行（296 个有成本的储能均为循环型，贡献为 0）。1,565,533 列全部获得有限界，无交叉。
- 截断值 U 只影响紧度：U = 2P̂ 时差距为 970 EUR。v* ≥ L 对 v* ≤ U 和 v* > U 两种情况都成立。完整性检查：C09 的解全部落在界内（最大越界 8.6e−11）。
- 边界：x̂ 的严格可行性未证明（V4 容差内可行，最大行违约 2.4e−7）；原未扰动科学目标仍为 NOT_PROVEN；FullSystemCostComplete 仍为 false。
- 补记（2026-10-13）：C10 报告、证据与方法随分支 `codex/d-stage-2920-20261013` 入库于 `research/05_baseline_evolution/20261011/c10/`；成员字节与 PACKAGE_MANIFEST 一致（界数组 npz 不入库）；以上条目原文未改。


## D 阶段：2920×3h 方案 A 模型的精确分解求解 — 2026-10-13

- **DR1：GATE6_2920_BASELINE_ACCEPTED。** 构建 1 次（D-1），优化调用 1 次（D-5），没有重试，没有使用 D-5b。V4、方案 A（180 项修订 / 627 项不变）、成本和科学约束均未改动。G6-05 仍为 PAUSED_BY_USER；没有运行情景；122 实例未释放。
- D-1：基于冻结的 2920 网络（`238262c9…`）应用方案 A，未做日聚合，未使用 C01R。模型 19,568,505 列 / 48,301,938 行 / 90,782,037 非零，与 Gate6 首次运行逐数字相同。385 组 D≤Q′ 精确成立，1,737 个 Load 逐值一致，标签覆盖完整，CSC 回读 EXACT；V4 binding 只按维度重新绑定，阈值不变。
- D-2（只读）：块 7,070,127 列 / 17,620,087 行；807 个 store、807 个 meter、385 组；跨块元素 0；块成本 0；精确残差 1.11e−16。主 LP 12,498,378 列 / 30,681,851 行 / 62,504,757 非零。
- D-5：参数为 C06 加 Crossover −1、TimeLimit 14,400、Threads 4。结果 Status 2、SolCount 1，Barrier 294 次（以 sub-optimal 结束），simplex 2,524,770 次，Runtime 12,753 s，ObjVal 431,077,792,553.95。
- 原 V4 10/10 通过：行失败 0，stationarity 失败 0（最大 6.05e−13），对偶符号失败 0，807/385 全部通过，1,849 项物理检查通过，NetCDF 精确回读，相对目标差 1.55e−13。在 122 独立进程复核、并在本机用 SHA 核验过的 CSC 复核，结果均与云端逐项一致。
- D-6：严格下界 v* ≥ 431,077,787,628.55 EUR（δ=1e−3），差距 4,924 EUR（相对 1.14e−8）。296 个有成本储能均为循环型且无损，权重 k=1/3 从实际行读取。同一脚本在 C09 日数据上复现了 C10 的结果。
- D-7（只读）：与日模型相比，已知范围科学成本 +0.71%（+30.6 亿 EUR），资本 −26.8%，运行 +3.0%。屋顶光伏 260 GW → 0，集中式光伏 0 → 41.5 GW，电池 0 → 27.6 GWh，气电 +105 GW，跨境输电 +32.5%。机制判断（INFERENCE）：日均处理抹平了光伏的昼夜曲线。日模型只用于流程筛选。
- 偏差记录：第一次 D-1 deploy 因源路径是符号链接被准入拒绝（未构建）；状态文件在 09:16–14:28 SGT 未按时更新（监控脚本解析错误）。
- 报告见 `d_stage/D_STAGE_RESULT.md`。下一步需另行授权：情景研究要在用户审阅、并与师哥确认决策备忘之后再进行。


## P0 部门耦合现状只读审计 — 2026-10-14

- **只读审计，未构建、未求解。** 依据用户 2026-10-14 18:01 SGT 确认的新研究口径：只比较互联 vs 完全不互联；2050 年每国净零；跨境载体扩展到 7 种；分子类载体可从东盟外进口。本轮对照的是 Gate6/D 阶段实际使用的代码（提交 2adde292）和 Phase3 记录（提交 d1c27902）。
- **需求侧：** 除电力外，所有终端部门都是按载体外生固定的终端能源量。oil/gas/coal 共 7,724 TWh，由 `build_research_assets.build_fragment()` 生成，靠固定 Load 加拓扑锁定；上游各部门函数一个都没有调用。制冷嵌在 Astar 里。
- **氢路径：** 已建好但结果为 0。原因是没有 H2 需求、没有 CO₂ 约束、化石燃料无限量、没有封存、没有 H2 网络。`only_elec_network` 和 `final_asean_adjustment` 只作用于原作者参考网络，研究配置已把它们覆盖并禁用。
- **碳相关：** CCS、DAC、BECCS、过程排放都没有建，状态为 DEFERRED。国际燃料舱按 2019 常数固定，排放全额报告。
- **供给侧：** 807 个生物质账户是需求推导的义务量，不是资源潜力，仓库里没有东盟潜力数据。400 项化石供应价格固定、数量无上限，没有 LNG 接收站，lignite 缺 registry 登记。
- **口径冲突：** 新口径与 Phase3 冻结决定对照 26 条，其中冲突 21 条，性质改变或待定 3 条，兼容 2 条。根本冲突在碳范围（只管电力 vs 全系统每国净零）。差距表 21 行，标注了工作量和数据类别。
- **规模估算（INFERENCE）：** 全部门、100 节点的中档约 4,170 万列，求解内存约 71–77 GiB，顶到 122 的 75 GiB 保护线；高档超过 90 GiB。非电部门只建在 11 个国家枢纽上时约 1,280 万列、约 24 GiB。
- **下一步：** 由用户与师哥决定。主要决定项有四个：碳范围、需求口径（服务需求还是终端能源）、空间与时间分辨率、生物质和接收站等外部数据的来源。报告见 `research/06_scope_redesign/p0_sector_coupling_audit/P0_LOCAL_SECTOR_COUPLING_AUDIT.md`。

## S1 部门耦合骨架、电力与氢 — 2026-10-15

- **范围：** 第一步（S1-1 至 S1-7）在本机完成；S1-8 日分辨率正式求解等待新云端实例（122 已到期，补充指令 02）。所有产物标注 `INTERIM_S1_SKELETON`，只有电力需求，结果无科学含义。分支 `codex/s1-coupling-skeleton-20261015`，基线 345fc30f。
- **适配层：** `scripts_project/sector_adapter.py` 调用上游 `add_hydrogen`（电解、燃料电池、H2 轮机、储氢罐、greenfield 管道），注入值来源逐项登记；不调用 `convert_conventional_generators_to_links`、`average_every_nhours`、`add_co2_budget`、`add_heat`、`add_residential`、`add_services`。母线命名统一为上游 `node carrier`（92 个燃料母线改名）。
- **退役：** 807 固定账户、1,256 计量 Link、`build_research_assets.py:214-250` 删除；`fixed_accounts` 一族与 `check_research_carriers`、`build_diagnostic_network` 移至 `scripts_project/retired/`；15 处守卫逐条写明替代（V5 B1/B5/B11/B12）。
- **存量：** 地热寿命 15→30 年（technology-data costs_2050.csv:1025，B 级）；ID 186 MW 按年龄存续但无性能合同未并入；Bataan 621 MW 按 GEM 原始记录（mothballed、无投运日期）排除；水电分国差异列出未改。
- **候选：** 核电大型堆（除 SG）/SMR（`p_nom_max=0`，DATA_PENDING）、地热/新水电/抽蓄站址候选（DATA_PENDING 共 485）、氢链与电池确认可扩展；成本缩放层全 1.0 时网络哈希一致（文件 + 内容）。
- **碳与情景：** 11 国大气 Store + `research_country_net_zero` 钩子；U4 结构性避免；`research.cross_border.*` 开关；integrated 保留 24 条跨境电力边（2025 下限、不计 CAPEX、FOM 常数 18.97 M EUR/a），disconnected 移除 24 条电力边与 20 条跨境氢管道。
- **构建与冒烟：** 两情景 2920×3h 与 365×24h 网络构建通过静态验证（峰值 RSS 0.50 GiB）；HiGHS 56×3h 冒烟：integrated 可解，V5 A1–A6、B1、B11、B12 通过，B5 通过；disconnected **不可行**，定位为新加坡在每国净零 + 无互联 + 无 SMR 数据 + 无进口下零排放供给仅为需求 5%，未放宽约束，B6 不可评估。
- **待用户决定：** B6 的"拆分存量跨境线路"前提与 PyPSA 0.30.3 `objective_constant` 不符且会改变基尔霍夫分流，本步改为 FOM 常数不拆分；SG 不可行的处理；作者 AEO8 成本覆盖是否沿用；决定 45 输电上限模式。
- **R12A：** D 阶段风电为 0 属经济合理（资源差 + 无碳约束 + 便宜化石/光伏）；作者参考模型风电 9.1 GW；外部容量因子未核实。
- **交付：** `research/06_scope_redesign/p1_step1_20261015/`（S1_REPORT.md、S1_EVIDENCE.json、CLOUD_RESOURCE_ESTIMATE.md、S1_CLOUD_DEPLOYMENT_PLAN.md、R12A、证据 JSON/CSV、测试记录）；云端部署包已打包未上传（`S1_RELEASE.tar.gz` SHA256 `615c9925…`）。

## D1 数据加工与数据登记 — 2026-10-15

- **范围：** S2 前置数据步骤（D1_DATA_INSTRUCTION.md）。只读 `work/p2_data_intake/`，新增 `research_inputs/{registry_v5,demand_v5,biomass_v5,cost_layers_v5,lng_terminals_v5}/`、10 个 `scripts_project/d1_*.py` 与 `tests/research/test_d1_registry.py`；不改原始数据、不构建、不求解。分支 `codex/d1-data-registry-20261015`（自 S1 929c35c7）。
- **登记表：** `DATA_REGISTRY.csv` 669 行（A 201 / B 206 / C 262；DATA_PENDING 98），每行带来源定位、SHA256、脚本、敏感性区间；18 个单位换算系数单独登记（UNSD 2014、IPCC 2006、NIST SP 811、FRED、ECB）。
- **CO₂ 封存（Gt，主算 / 低 / 高）：** MY 128.77 / 80 / 198.8；ID 51.28 / 8.4 / 77.3；PH 22.3 / 0.07 / 23.3；BN 18.58 / 0.56 / 25.6；TH 16.02 / 10 / 23.0；VN 11.8 / 5.3 / 21.75；TL 0.25；KH 0.085；LA/MM/SG 0；年注入上限 = 潜力 ÷ 50。
- **价格与供给上限：** WEO 2025 NZE 2050 → EUR2020/MWh(NCV) 原油 11.62、LNG 13.67、煤 5.17（STEPS 2050 为高价敏感性）；GEM LNG 现有能力 TH 19.0、PH 14.7、ID 11.75、SG 11.0、MY 7.3、VN 4.0 Mtpa，上限 2.5×，已映射节点；UNSD 2019 国内煤/气/油产量上限按国登记（气为 gross production 上界）。
- **成本口径（决定 46 方案 A）：** 作者 `append_cost_data.py` 规则逐行解码并复现（51 值相对差 1.9e-15）：ECB 2020 年均 FX 0.877229；D.17 衰减只在标签相同处生效，"Solar PV"≠"Solar" 致光伏零衰减，FOM% 以衰减后资本为分母被放大。A 层 technology-data v0.13.2 2050（主算）与 B 层 AEO8 作者规则（敏感性）通过 `research.cost_layer` 切换；SMR 8,421 EUR2020/kW、FOM 1.146 %/a、VOM 1.93 EUR/MWh（C 级 ±30 %）；存量地热 FOM 2.0 %/a、寿命 30 年（B 级），效率/VOM/投资在 v0.13.2 中缺失。technology-data v0.13.4 仅 4 行变化、v0.15.0 改为 2025 年价（+25.7 %）并大改核燃料/HVDC/FT，不升级，交用户决定。
- **需求 2050：** 基年 UNSD 2019 冻结重建 + 电力分部门；东盟十国分部门合计 = AEO8 BAS 2050（相对误差 2e-16）；国别按 GDP 乘数分配并校准（k：工业 1.206、交通 1.417、居民 0.295、商业 0.923、农业其他 1.014），人口法作敏感性；电力行标记为已在 Astar 2,617.8 TWh 中（表内 2,395.8 TWh，比值 0.915，未调参）；非能源按工业乘数、舱燃料 2019 常数，BN/KH/LA/TL 航运舱燃料 DATA_PENDING。
- **份额与生物质：** PyPSA-Eur v2025.07.0 47 项份额按行号登记（采暖 3 项不适用）；IRENA 2017 R-3→R-1a 复现误差 ≤1.6 %，FAOSTAT 当前版复现 −2～−18 %；11 国 2050 潜力约 8,670 PJ（ID 4,068、TH 1,410、MY 1,069、PH 687、VN 663、MM 453、KH 220、LA 90），成本 C 级 ±50 %（NRI/NEDO 2024、ERIA/IEEJ 2024）。
- **待下载：** EDGAR_2025_GHG、USGS MCS 2025 水泥/钢、UNSD 四国舱燃料、伐木残余系数、油棕树干价格、WaW 老挝成分、LA/MM 封存评估、GEM 无容量单元、LNG 再气化费、地热发电参数（11 项）。
- **交付：** `research/06_scope_redesign/p1_step2_20261015/`（D1_REPORT.md、DATA_REGISTRY.csv、DATA_PENDING_LIST.csv、DOWNLOAD_LIST.csv、D1_EVIDENCE.json、D1_TEST_RUN.json、测试日志）。

## S2 CO₂、生物质、需求 — 2026-10-15

- **范围：** S2-0（补充指令 01 数据补齐）与 S2-1 至 S2-7 在本机完成；没有正式求解（第 47 项）。分支 `codex/s2-co2-biomass-demand-20261015`（自 D1 8f977156），draft PR 叠在 D1 的 PR #22 之上。所有网络标注 `S2_SECTOR_COUPLED_SMOKE`；冒烟 `SMOKE_TEST_ONLY`；诊断 `GAP_DIAGNOSTIC_NOT_FOR_INTERCONNECTION_VALUE`。
- **S2-0（f0ad4070、f64e1fd0）：** technology-data v0.15.0 层（EUR2025 → EUR2020，ECB EA20 GDP 平减 0.833196；海底 HVDC +121%、铀 +82%、FT 单位重构）；城市垃圾有机部分改走沼气（IPCC 2006 产率，湿基，约 303 PJ）；EDGAR 2025 过程排放（2.A/2.C 入过程母线，2.B/2.D/4.C 归原料碳口径）；四国海运舱燃料 0（A 级）；伐木残余主算 0（ZERO_BY_DECISION），高生物质敏感性与 7 国木材加工残余推导；registry 937 行（A 204 / B 471 / C 262），DATA_PENDING 98 → 22。
- **S2-1：** 主算成本层切换到 v0.15.0（燃料价按第 33 项取 WEO 2025 NZE：气 13.67、油 11.62、煤 5.17 EUR2020/MWh）；SMR 启用（AEO8 C 级，11 国）；存量地热 186 MW 并入（GEM 3 台 2021/2022 投运，30 年寿命；9 台无投运年份 DATA_PENDING）；lvopt（2.79 倍为敏感性）；B6 按第 48 项；`gap_diagnostic` 模式（全部国家电力 + CO₂ 松弛，惩罚 10,000 EUR/MWh、10,000 EUR/t，默认关闭）。
- **S2-2：** 每节点 `co2 stored` 缓冲 + 每国 `co2 sequestered {ISO2}`（上限 = 潜力/50，8 国；LA/MM/SG 不建）；109 条 CO₂ 管道（19 条跨境受开关控制）；CCGT CC、SMR CC、BECCS、工业生物质 CC、过程排放 CC、DAC（电供热 COP 1）；第 20 项分国核算用跨境封存算例验证（TH → MY 13.7 Mt/168 h，TH 记减排、MY 只占上限）。
- **S2-3：** 每国固体生物质/沼气母线，107 个品类 Store（2,120.7 TWh/a），发电(+CC)/工业(+CC)/沼气提纯/BtL 全部内生；360 TWh 全区池配置删除。
- **S2-4/5：** D1 需求表 → 1,906 个 Load，归属表唯一绑定；EV 1,175.9 TWh、Astar 交通用电扣除 11.08 TWh（SG 7.26）；铁路燃油计量（U2）、航空国内/国际（开关）、工业聚合载体（U1）+ 20% 低温热母线（97 个，5 种供给）、原料碳按 PyPSA-Eur 口径（方法问题待确认）、清洁炊事（第 23 项）、农业；航运 670 TWh 推迟到 S3。
- **S2-6：** V5 新增 B2、B3、B8、B11；B1 覆盖全部排放端口（2,949 个）。
- **S2-7：** 两情景 2920×3h 与 365×24h 构建通过静态校验（峰值 RSS 0.58 GiB）；56×3h HiGHS 冒烟**两情景均不可行**。原因（未放宽约束）：① SG、VN 固定生物质终端需求超过本国固体生物质潜力（0.18 vs 0.03；208 vs 125.8 TWh/a）；② MM 无封存潜力且无跨境 CO₂ 管道（两情景）；③ 不互联下 LA/SG 无封存、KH/VN 封存上限不足（需 34.0 vs 1.7；598 vs 236 Mt/a）。`gap_diagnostic` 第 1 轮（仅电力 + CO₂ 松弛）仍不可行，第 2 轮加生物质松弛后最优：不互联 CO₂ 缺口（168 h）VN 7.79、SG 2.16、TH 2.02、ID 1.54、KH 0.83、MM 0.62、LA 0.24 Mt；一体化只剩 MM 0.62 与 VN 4.17 Mt（后者为截断时域资本成本放大的经济性缺口，结构上可行）。截断时域未缩放目标函数权重是诊断的已知局限，修正方案 PROPOSED。
- **待用户决定：** 原料碳口径（PyPSA-Eur 全量最终排放 vs EDGAR 2.B）；SG/VN 生物质需求与潜力冲突的处理；VN 2050 工业煤 962 TWh 的需求链核对；诊断运行的目标函数权重缩放；B11 对 3 个无负荷辅助节点气母线的判定；地热不凝气 CO₂ 忽略。
- **交付：** `research/06_scope_redesign/p1_step2_20261015/`（S2_REPORT.md、S2_0_DATA_TOPUP.md、S2_PROGRESS.md、S2_EVIDENCE.json、S2_TEST_RUN.json、CLOUD_RESOURCE_ESTIMATE.md §6、evidence/）；测试 364 通过 / 4 失败（基线即失败的 gate4 旧测试）。

## S2B 修正轮（补充指令 02，第 55–60 项）— 2026-10-15

- **范围：** 在 S2 分支上追加 R3 → R1 → R2 → R5 → R6 → R4 → R7 → 构建与冒烟，每节一个提交（bd6debcd、cff39662、ab85b7ce、09a517c7、182bce70、d337d986、47ce2e15 + 构建/报告两个提交）；draft PR #23 同步更新。无正式求解。
- **R3（57）：** 分国分配改用 AEO8 C.8 人均终端能源 × D.1 人口的相对因子 r_c（Σ人均×人口 431.96 / 746.07 Mtoe vs 432.2 / 746.2）；TH 2,325 → 3,399 TWh，PH 1,447 → 999，VN 2,900 → 2,559；GDP/人口分配为敏感性表；`research.demand.country_allocation`。
- **R1（55）：** `s2b_industry.py`：钢铁（worldsteel 2019 + PyPSA-Eur 0.3/1.0 + H₂ 1.7、电 0.322 + technology-data 电炉 0.6395）、水泥（EDGAR 2.A.1/0.52 熟料 + technology-data 窑炉/粉磨比率，窑炉燃料→甲烷）；其余子部门 2019 载体份额 × 乘数，PyPSA-Eur 比率待 JRC-IDEES-2021（DATA_PENDING，已入下载清单）；低温热行 0；生物质超潜力→甲烷（VN 23.6、SG 0.14 TWh）；工业氢 73.7 TWh；工业电力显式并从 Astar 扣除；VN 工业煤 995 → 513 TWh。
- **R2（56）：** `s2b_feedstock.py`：EDGAR 2.B+2.D × 乘数入过程母线；废塑料焚烧（What a Waste 3.0 × IPCC 表 2.4）入大气；出口/填埋不计；属地 vs 全量释放（Mt/a）：ID 73.8 vs 63.8、TH 39.8 vs 104.6、MY 23.4 vs 79.2、SG 21.5 vs 16.0；LA 塑料份额、KH/TH/VN 露天焚烧份额 DATA_PENDING。
- **R5（59）：** 氢/CO₂ 候选 = 电力拓扑（PyPSA-Eur create_network_topology）：109 条、跨境 19 对（与 S2 相同节点对；氢 20 → 19，去掉 via HVDC 重复；MY–TH 长度 132.6 → 275.4 km）；MM 无跨境电力走廊 → 数据缺口。
- **R6（60）：** DAC 热 1.4 MWh_th/t 取自节点工业低温热母线（technology-data 第 938–942 行，PyPSA-Eur add_dac 组合）；电 0.55 MWh/t；electric_cop1 为敏感性。
- **R4（58）：** 截断运行权重 8760/N、年度上限不缩放，B12 登记权重与哈希。**R7：** B11 只判有负荷母线（辅助母线单列）；A3/A5 把松弛×罚款计入已知项。
- **构建与冒烟：** 两情景构建通过（RSS 0.58 GiB）；冒烟两情景不可行（MM 过程 + 塑料无去向；不互联 KH/LA/SG/VN）；gap_diagnostic（全年口径）最优：一体化只剩 MM 5.13 Mt/a，不互联 VN 234.5 / KH 16.5 / SG 12.8 / LA 8.6 / MM 5.1 Mt/a，电力与生物质缺口 0；MM 的化石终端能源由 FT（生物质 CC 碳 + 电解氢）与 BtL 替代；结构上界（化石供给不变）与诊断缺口的差额即合成燃料碳循环。门槛 A1–A6、B2、B3、B8、B12 通过，B11 细化后通过；B1/B5/B6 不可评估。测试 371 通过 / 4 基线失败。
- **待用户决定：** JRC-IDEES-2021 下载授权；钢铁/水泥替代比率是否接受；MM 跨境走廊（TH–MM/LA–MM）；R2 数据缺口代理；KH 交通链；子部门拆分缺口；full_release 敏感性是否正式运行。
- **交付：** `research/06_scope_redesign/p1_step2_20261015/`（S2B_REPORT.md、S2_EVIDENCE.json v2、S2B_TEST_RUN.json、CLOUD_RESOURCE_ESTIMATE.md §7、evidence/s2b/、S2_PROGRESS.md）；镜像 `work/p1_step2_20261015/`。

## S4B 第 70–81 项、冒烟、云端部署包 — 2026-10-16

- **说明：** S3、S3B、S4A 三轮没有在本台账追加条目，其结果见各自报告（`p1_step3_20261015/`、`p1_step4_20261016/`）；本条只记 S4B。
- **范围：** 指令 `S4B_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 52f1b758…dbc51 核对一致）；分支 `codex/s4b-fixes-calibration-20261016`（自 S4A a58ca3fa），draft PR #26 叠在 #25 上；每个子步骤一个提交；无云端操作，无 365×24h / 2920×3h 求解。
- **S4B-0（70–73）：** PyPSA-Eur 部门开关对齐（含 Sabatier、电制生物燃料、FT 最低负荷），79 行对照表；验收容差挂钩 FeasibilityTol/OptimalityTol（k = 10，净零行用国家 CO₂ 毛流量，生物质池用容量）；LNG 按 7,018 EUR/MW/a 扩建；诊断加分国气松弛。冒烟：一体化 OPTIMAL 6.6598e11，不互联诊断 OPTIMAL（CO₂ 缺口 KH/LA/MM/SG）。
- **S4B-1（77）：** 在建与无投运年在建计入、GIPT 2026 非在运 11 台移出；存量 261,101 → 267,491 MW。**S4B-2（78、79）：** 新建水电 195.2 GW、地热 25.8 GW、抽蓄 14.4 GW 国家上限与节点分配；核电规划上限开关只实现。
- **S4B-3（74、75）：** Ember 观测 CF 校准 ERA5 风速（α PH 0.910、TH 1.294、VN 0.995，其余 1.046），DEA 2050 引用版机型（6 MW / 165 m / 110 m）；`calibrated_modern` + 3 级资源分级为主算。**S4B-4（76）：** IBTrACS 台风暴露与 +25% 开关只实现；raw12 核对；完整 WDPA 未下载。
- **S4B-5：** 一体化 OPTIMAL 5.9438e11（S4A 7.1200e11），不互联主算 NUMERIC（预期），不互联诊断 OPTIMAL（CO₂ 缺口 KH 13.42、LA 7.10、MM 4.64、SG 22.66 Mt/a），一体化诊断 SUBOPTIMAL（只记录）；一体化门槛新旧口径均未通过（数值残差，barrier 精度下降）；SMR 241.5 → 96.6 GW；ID 新建水电 77 GW（入流代理偏高）。
- **S4B-6：** 365×24h 每运行约 21 GiB（上限 30），串行 2.3–3.3 h、并行 1.7–2.6 h；部署包代码 949163f3 + 三个日网络，上传 193,276,010 B（只准备）。
- **待用户决定：** 14 项（S4B 报告 §8），其中求解精度（是否用 crossover）、ID 新建水电入流代理、风光候选成本层、云端运行方式与授权最关键。
- **交付：** `research/06_scope_redesign/p1_step4b_20261016/`（S4B_REPORT.md、S4B_EVIDENCE.json、S4B_PROGRESS.md、DOWNLOAD_LIST.csv、CLOUD_RESOURCE_ESTIMATE.md §11、CLOUD_DEPLOY_STEPS.md、cloud_package/、evidence/）；镜像与审阅 ZIP 在 `work/p1_step4b_20261016/`；测试 430 通过 / 4 失败（test_gate4_activation 既有）。

## S4C 第 82–90 项（含补充 01）、求解设置对比、云端部署包 — 2026-10-17

- **范围：** 指令 `S4C_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 e1bad922…1dcdd3 核对一致）、补充 01（e0bc1743…a8340a，第 16 项）；分支 `codex/s4c-allocation-fixes-20261016`（自 S4B 819ade64），draft PR #27 叠在 #26 上；每个子步骤一个提交；无云端操作，无 365×24h / 2920×3h 求解。两次按规则停下请用户决定（停止 01 海底份额、停止 02 水电）。
- **S4C-0（85、86、90）：** 化石燃料价格改 WEO 2025 STEPS（气 27.07、油 35.32、煤 8.86 EUR2020/MWh；NZE 敏感性、CPS 可选，构建时断言同一情景）；BtL 乘效率（PyPSA-Eur 第 4230–4231 行）；gate4 测试改断言已接受状态；折现率统一 0.07，`wacc_mode: country_specific` 只实现（11 国实际值 DATA_PENDING）。
- **S4C-1（82 + 16）：** 风光与电力底座候选改用成本层（光伏 −57 %、陆风 −14 %、海上风 −9~−17 % 含按 PyPSA-Eur 公式的并网成本、DC 链路 ×2.5）；全组件审计 84 组无法判断 0；走廊海底份额按用户决定"同陆块按陆上 + 非陆地口径"（东盟特有处理"群岛海底通道"）。
- **S4C-2（83）：** 诊断与推断机理只部分吻合（作者链路按上游径流分配，单元 CF 最高 4.6）；用户决定 B（Ember 2019–2025 中位 × 1.1，按容量分配），存量入流 232.8 → 230.2 TWh；S4B §8 第 12 项前提更正为冒烟口径产物。
- **S4C-3（88）：** 燃料舱 `asean_pool`：东盟负荷 + 单独净零燃料舱账户（拒绝负排放端口）；冒烟中化石航煤 0。另查实 `cost_layer.registry` 键误挪（077ebd0b–9a5ea111）无影响，已挪回。
- **S4C-4（89）：** 东盟外 CO₂ 封存 40.75 EUR2020/t（IEAGHG 2004 PH4/30 船运 4,500 km + ZEP 2011 海上咸水层，C 级 ±50 %）；下载第 1 类 6 个 PDF 18.2 MB。
- **S4C-5（84）：** 基尔霍夫行归一化（矩阵上界 1e3 → 2e2，目标差 2.8e-11）；A、C 最优，B crossover INF_OR_UNBD；三档均未过新口径（A 只剩 33 个 `Line-s` 列平稳性残差）；推荐 A；365×24h 单运行外推 A 28–39 min、C 60–85 min。
- **S4C-6：** 冒烟三项均 OPTIMAL（一体化 6.5118e11、不互联 6.9830e11、NZE 5.5692e11）；B6 真实差 4.71e10 EUR/a；部署包代码 c5a33851 + 四个日网络，上传 220,953,139 B，`--solver-profile` 必填（只准备）。
- **待用户决定：** 10 项（S4C 报告 §8），其中云端求解档案、东盟外封存单价口径、云端运行方式与授权最关键。
- **交付：** `research/06_scope_redesign/p1_step4c_20261016/`（S4C_REPORT.md、S4C_EVIDENCE.json、S4C_PROGRESS.md、DOWNLOAD_LIST.csv、CLOUD_RESOURCE_ESTIMATE.md §12、CLOUD_DEPLOY_STEPS.md、cloud_package/、evidence/、两份停止报告）；镜像与审阅 ZIP 在 `work/p1_step4c_20261016/`；测试 457 通过 / 0 失败。

## S4D 第 91–93 项：分国成本账本与子集互联、东盟内 CO₂ 船运、出口节点与老挝过境、云端部署包 — 2026-10-17

- **范围：** 指令 `S4D_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 a35fa7d5…3b2586，已核对）；分支 `codex/s4d-allocation-ledger-20261017`（自 S4C afec19e6），draft PR #28 叠在 #27 上；每个子步骤提交。无云端操作，无 365×24h / 2920×3h 求解。停下 1 次请用户决定（停止 01：沿海节点判定）。
- **S4D-0：** 登记对 S4C §8 十项的答复（云端档案 A `formal_barrier` 等）与工作原则第 8 条；盘点 CO₂ 链路。
- **S4D-1（93）：** 沿海判定按用户决定（方案 A + 物理海岸线，含内水与群岛水域；只有河港的不算）：73 / 100 个节点沿海，带缓冲节点 71 沿海 / 26 内陆，TH2 2、KH2 4 判内陆。东盟外出口链路 97 → 71 条，内陆 CO₂ 经国内管道到沿海。老挝铁路过境到最近的越南海岸：Stolaroff 2021 表 2，0.044 $/t-km + 2 $/t，C 级 ±50 %，陆运段 9.7–24.6 EUR/t。
- **S4D-2（92）：** 东盟内 CO₂ 船运 504 条链路，`border_class = maritime_trade`，两个情景都有，B5 不计入。IEAGHG 2004 分项 11.42 + 0.00295 EUR/(t·km) × 大圆 km × 航线系数 1.091（模型几何推导，±25 %）。成本排序：船运 + 国内封存 ≥ 41.4，高于东盟外 40.75，冒烟中船运量为 0（列为用户决定）。
- **S4D-3（91a）：** 分国成本账本（A5 分解按组件归属；跨主体流量按端口母线对偶价格结算；跨境走廊两端各半，按境内长度作敏感性；燃料舱单列），门槛 `B16_LEDGER` 纳入两套验收集合，求解后导出账本与节点价格（按日）。S4C 三个解只读试算，相对误差 ≤ 1e-11；修正了国家氨负荷挂在区域母线上被错记给区域池的问题。
- **S4D-4（91b）：** `--override cross_border.coalition=[…]`。11 国 = 一体化、[] = 不互联，目标相对差 0.0；{MY, SG} 最优，{LA, TH} SUBOPTIMAL（未重试）。成员 ≥ 2 的连通联盟 81 个；BN、PH、TL 没有跨境走廊。
- **S4D-5：** 冒烟三项均最优（一体化 6.51296e11、不互联 6.98615e11、NZE 5.57055e11，较 S4C +0.02–0.05 %）。B5、B6（差 47.32 bn EUR）、B16 通过；不互联 − 一体化的分国差额：VN 20.3、MY 11.8、TH 5.2、LA 3.0、SG 2.8、KH 2.1 bn EUR 等。
- **S4D-6：** 敏感性键 `co2.extra_asean_cost_scale`；第一批敏感性只登记（东盟外 ±50 %、航线系数 ±25 %、LNG 上限）。部署包重建到 c45f1448：四个日网络与冒烟网络逐组件一致，上传 228,863,868 B，运行命令 `--solver-profile formal_barrier`（只准备）。365×24h 单运行 25–59 min，串行 1.6–2.2 h。
- **待用户决定：** 8 项（S4D 报告 §9）：老挝港口口径与运输方式、LA 是否可船运进东盟封存、封存单价统一口径、航线系数口径、BN / PH / TL 走廊、{LA, TH} 次优结果的处理、LNG 上限取值。
- **交付：** `research/06_scope_redesign/p1_step4d_20261017/`（S4D_REPORT.md、S4D_EVIDENCE.json、S4D_PROGRESS.md、DOWNLOAD_LIST.csv、CLOUD_RESOURCE_ESTIMATE.md §13、CLOUD_DEPLOY_STEPS.md、cloud_package/、evidence/、停止报告 01）；镜像与审阅 ZIP 在 `work/p1_step4d_20261017/`；测试 479 通过 / 0 失败。

## S4E 第 94–95 项：补齐相邻跨境走廊、统一 CO₂ 封存单价与船运细节、冒烟、云端部署包 — 2026-10-17

- **范围：**
  - 指令 `S4E_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 e5c184c1…bb7e9db，已核对），开头为用户对 S4D §9 八项的答复。
  - 分支 `codex/s4e-corridors-storage-20261017`（自 S4D 0429a0eb），draft PR #29 叠在 #28 上；每个子步骤提交。
  - 无云端操作，无 365×24h / 2920×3h 求解，无下载；没有触发停止条件。
- **S4E-0：** 登记 §9 八项答复，以及联盟运行规则（第 95 项 f：档案 A 非最优 → 档案 C 重跑一次 → 仍非最优标 UNVERIFIED）。
- **S4E-1（94）：**
  - 陆上相邻按共享边界 ≥ 1 km（1 km 对齐容差）判定，共 49 对，新增 31 条交流候选。
  - APG AIMS III 跨海 #4 / #7 / #16 为直流候选；国内 #3 / #18a / #18b 为直流候选，两个情景都有。
  - 存量只有 TH–MY 不一致（2,645.6 vs 380 MW），已列出，未改动。
  - 走廊图 11 → 14 条边，BN、PH、TL 接入；连通联盟 81 → 383。
  - 开关 `research.corridors.adjacency_completion`，`off` 与 S4D 网络逐组件一致。
- **S4E-2（95）：**
  - 统一封存 30 EUR/t，东盟外 54.70 EUR2020/t（对第 89 项单价构成的修改，±50 % 作用于它）；ZEP 16.05 作敏感性。
  - 船运按逐对海上距离计价，单一系数 1.091 作对照。
  - 老挝过境后船运进东盟各国国内封存，共 42 条 `CO2 transit ship`。
  - 过境口径（现有海港 / 罐车）与 LNG 不设上限（7,018 EUR/MW/a）两项敏感性已构建核对。
- **S4E-3：** 冒烟三项均最优：一体化 6.30166e11、不互联 6.76828e11、NZE 5.30241e11，较 S4D 低 3.1–4.8 %。
  - 东盟外封存降为 0，东盟内船运 144 / 284 / 153 Mt。
  - 新走廊在一体化中全部建设，约 301 GW，远超 APG 规划；#18a 国内直流 40.5 / 79.3 GW。
  - B5、B6（46.66 bn EUR）、B16 通过。
  - 分国差额：VN 20.4、MY 7.5、TH 4.8、SG 3.1、LA 2.6、KH 2.3、ID 2.1、MM 0.8、BN 0.6、TL 0.14、PH −0.6 bn EUR。
- **S4E-4：**
  - 部署包重建到 a3d58a46，四个网络与冒烟网络逐组件一致；上传 232,117,286 B。
  - 预检内存下限 36 / 72 / 104 GiB；365×24h 单运行 25–52 min，串行 1.6–2.3 h。
  - 联盟研究 383 个，约 160–330 h 串行。
  - 第一批敏感性 5 项只登记。
- **待用户决定：** 7 项（S4E 报告 §7）：
  - 新候选走廊的容量上限；
  - TH–MY 存量；
  - #4 印尼端点；
  - 联盟研究范围；
  - LA 经越南海岸进入越南国内封存；
  - SG–VN / SG–KH 可选候选；
  - PH 负互联价值与 `adjacency_completion=off` 对照。
- **交付：** `research/06_scope_redesign/p1_step4e_20261017/`，内容为 S4E_REPORT.md、S4E_EVIDENCE.json、S4E_PROGRESS.md、DOWNLOAD_LIST.csv、CLOUD_RESOURCE_ESTIMATE.md §14、CLOUD_DEPLOY_STEPS.md、cloud_package/、evidence/。镜像与审阅 ZIP 在 `work/p1_step4e_20261017/`；测试 `tests/research` 488 通过 / 0 失败。

## S4F 第 96–97 项：单条输电扩建上限、TH–MY 存量与 S4E 其余事项、冒烟、云端部署包与上云前清单 — 2026-10-17

- **范围：**
  - 指令 `S4F_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 28d7458d…7216f03，已核对），开头为用户对 S4E §7 七项的答复。
  - 分支 `codex/s4f-extension-caps-20261017`（自 S4E bcda8001），draft PR #30 叠在 #29 上；每个子步骤提交。
  - 无云端操作，无 365×24h / 2920×3h 求解，无下载。
  - 停下 1 次请用户决定：停止 01，线路 91 不是 Sadao–Chuping → 用户选方案 1。
- **S4F-0：** 登记 §7 七项答复（`s4f_0`）；核查 PyPSA-Eur v2025.07.0 的 `lines.max_extension` 与 `links.max_extension`。
- **S4F-1（96）：**
  - PyPSA-Eur 的实际做法：`prepare_sector_network.py` 只读 `lines.max_extension` = 20,000 MW，以新增量口径同时作用于交流线与 DC 链路；`links.max_extension`（30,000）不使用（用户同意）；管道不设上限。
  - 开关 `research.network.max_extension`：pypsa_eur | none | apg_plans；`apg_plans` 为 18 组 APG 上限，钩子 `research_apg_corridor_cap`。
  - `none` 构建与 S4E 网络逐组件一致。
- **S4F-2（97）：**
  - TH–MY：线路 91 = 80 MW（C 级，聚类伪影），Khlong Ngae–Gurun 300 MW，删除 4 条 OSM 250878579 重复直流，合计 380 MW = APG；开关 `research.network.th_my_stock`。
  - 作者 readjust 改过的 19 条跨境交流线清单（只记录）。
  - #4 印尼端改为北干巴鲁（432 km，DC）。
  - 老挝经铁路进入越南国内封存（6 条，贸易类）。
  - SG–VN / SG–KH 第二批开关。
  - `tests/transport` 在 pytest 下可运行（整个 `tests/` 516 项通过）。
- **S4F-3：** 冒烟三项均最优：一体化 6.39063e11、不互联 6.93191e11、NZE 5.38893e11，较 S4E 高 1.4–2.4 %。
  - 新走廊 263 GW，单条最大 20 GW；触及上限的组件：一体化 11 个、不互联 6 个。
  - B5、B6（54.13 bn EUR，7.8 %）、B16 与全部求解器容差门槛通过。
  - 分国差额：VN 22.0、ID 9.6、TH 6.2、MY 5.1、LA 4.0、KH 2.3、SG 2.0、PH 1.05、MM 1.0、BN 0.8、TL 0.27 bn EUR。
- **S4F-4：**
  - 部署包重建到 7e09744d，四个网络与冒烟网络逐组件一致；上传 232,095,769 B。
  - 365×24h 单运行 34–67 min（悲观 98），串行 2.0–2.8 h；预检下限 36 / 72 / 104 GiB 不变。
  - 第二批敏感性 7 项只登记。
- **S4F-5：** 上云前清单（报告 §10）：部署包哈希、实例规格、用户需提供的信息、首次正式运行授权原文模板。
- **待用户决定：** 4 项（S4F 报告 §7）：
  - 作者 readjust 改过的 19 条线如何处理；
  - `apg_plans` 取值规则；
  - `existing_port` 敏感性中泰国港口节点是否进入泰国封存；
  - 上云前信息与授权。
- **交付：** `research/06_scope_redesign/p1_step4f_20261017/`，内容为 S4F_REPORT.md、S4F_EVIDENCE.json、S4F_PROGRESS.md、S4F_STOP_01_LINE91.md、DOWNLOAD_LIST.csv、CLOUD_RESOURCE_ESTIMATE.md §15、CLOUD_DEPLOY_STEPS.md、cloud_package/、evidence/。镜像与审阅 ZIP 在 `work/p1_step4f_20261017/`；测试 `tests/research` 499 通过、整个 `tests/` 516 通过。

## S4G 第 98–99 项：作者 readjust 跨境交流线的电气参数、S4F 其余事项、冒烟、云端部署包与上云前清单 — 2026-10-17

- **范围：**
  - 指令 `S4G_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 2fd959e9…a0d915c，已核对），开头为用户对 S4F §7 四项的答复。
  - 分支 `codex/s4g-readjust-impedance-20261017`（自 S4F 04681769），draft PR #31 叠在 #30 上；每个子步骤提交。
  - 无云端操作，无 365×24h / 2920×3h 求解，无下载；没有触发停止条件。
- **S4G-0：** 登记 §7 四项答复（`s4g_0`）。
- **S4G-1（98）：**
  - 依据：PyPSA-Earth `base_network.py` 680–701 与 `simplify_network.py` 181，PyPSA 0.30.3 `apply_line_types` 与 `calculate_dependent_values`。
  - 19 条线按 `num_parallel = s_nom / (√3·v_nom·i_nom)` 修正，`x`、`r`、`b` 按线型重算，PyPSA 实际使用重算值。
  - 开关 `research.network.readjust_impedance`：pypsa_eur | author（与 S4F 逐组件一致）。
  - LA–VN 电抗 558,762 Ω；基尔霍夫系数跨度 943 → 2.3e5。
  - 只记录：国内存量线一致；APG17 比值 0.0137；零容量候选沿用模板线 43；库内 OSM 有 LA–VN 500 / 220 kV 跨境线（按线型约 13 GW），作者记为 1 MW。
- **S4G-2（99）：** `apg_plans` 规则确认；`existing_port` 敏感性中 LA2 1 / 2 / 3 / 5 经是拉差进入泰国封存；S4F 部署包作废。
- **S4G-3：** 冒烟三项均最优，求解器容差门槛全部通过。
  - 目标值：一体化 6.40080e11（+0.16 %）、不互联与 S4F 相同、NZE 5.39913e11（+0.19 %）。
  - LA–TH 61、LA–VN 60 不再触及上限，湄公河潮流转到新候选走廊。
  - B6 为 53.11 bn EUR（7.7 %）；LA 互联价值 3.96 → 3.26 bn EUR。
- **S4G-4：**
  - 部署包重建到 ed6af79c，四个网络与冒烟网络逐组件一致；上传 232,464,773 B。
  - 365×24h 单运行 30–56 min（悲观 83），串行 1.8–2.5 h；预检下限 36 / 72 / 104 GiB 不变。
  - 第二批敏感性 8 项只登记。
- **S4G-5：** 上云前清单（报告 §10），格式同 S4F，填入 ed6af79c。
- **待用户决定：** 4 项（S4G 报告 §7）：
  - LA–VN 存量；
  - APG17 与零容量候选线的电抗口径；
  - 数值风险的处置；
  - 上云前信息与授权。
- **交付：** `research/06_scope_redesign/p1_step4g_20261017/`，内容为 S4G_REPORT.md、S4G_EVIDENCE.json、S4G_PROGRESS.md、DOWNLOAD_LIST.csv、CLOUD_RESOURCE_ESTIMATE.md §16、CLOUD_DEPLOY_STEPS.md、cloud_package/、evidence/。镜像与审阅 ZIP 在 `work/p1_step4g_20261017/`；测试 `tests/research` 506 通过、整个 `tests/` 523 通过。

## S4H 第 100–101 项：LA–VN 存量、候选线参考电抗、冒烟、云端部署包与上云前清单 — 2026-10-17

- **范围：**
  - 指令 `S4H_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 a029bd64…1fd33bd，已核对），开头为用户对 S4G §7 四项的答复；本步只实现第 100、101 项，其他发现只记录。
  - 分支 `codex/s4h-lavn-candidates-20261017`（自 S4G 78c95a75），draft PR #32 叠在 #31 上；每个子步骤提交。
  - 无云端操作，无 365×24h / 2920×3h 求解，无下载；没有触发停止条件。
- **S4H-0：** 登记 §7 四项答复与本步范围规则（`s4h_0`）。
- **S4H-1（100）：**
  - LA–VN 存量按 AIMS 电网间口径记为 0（`la_vn_grid_stock_2025`，B 级）；线路 59 / 60 / 63 / 64 改为零容量候选线（可扩建，单条上限 20,000 MW，长度、单位成本、海底份额不变）。
  - 开关 `research.network.la_vn_stock`：aims_zero | author（与 S4G 逐组件一致）。
  - 独立电站专用出口线估算：572 MW × 230.9–515.1 km × 46.497 EUR/MW/km/a = 6.1–13.7 M EUR/a（C 级，不建模）。
- **S4H-2（101）：**
  - 46 条零容量交流候选线 `num_parallel` = 1（开关 `research.corridors.candidate_num_parallel`：one_circuit | template43）；PyPSA 读回的电抗与新回路数一致。
  - APG17 按第 98 项关系修正：回路数 1.286 → 0.017667，x 67.8 → 4,939 Ω（`READJUST_IMPEDANCE_S4H2.csv`）。
  - KH–LA、LA–MM、LA–TH（7 个节点对）、MY–SG（直流）、MY–TH 补参考候选，共 10 条交流线 + 1 条直流链路（`CORRIDORS_S4H2.csv`）。
  - 基尔霍夫系数跨度 2.3e5 → 2,034；复现 S4G 的构建与 S4G 逐组件相同。
- **S4H-3：** 冒烟三项均最优，求解器容差门槛全部通过。
  - 目标值：一体化 6.39881e11（−0.03 %）、不互联与 S4G 相同、NZE 5.39724e11（−0.03 %）。
  - 老挝方向扩建转到参考候选线：LA–TH 10 → 54 GW、LA–VN 65 → 81 GW、KH–LA 2 → 8 GW、LA–MM 9.5 → 4.6 GW。
  - B6 为 53.31 bn EUR（7.7 %）；LA 互联价值 3.26 → 2.50 bn EUR。
- **S4H-4：**
  - 部署包重建到 6eead675，四个网络与冒烟网络逐组件一致；上传 232,939,289 B；S4G 部署包作废。
  - 365×24h 单运行 37–52 min（悲观 76），串行 1.9–2.6 h；预检下限 36 / 72 / 104 GiB 不变。
  - 第二批敏感性 10 项只登记（加 `la_vn_stock=author`、`candidate_num_parallel=template43`）。
- **S4H-5：** 上云前清单（报告 §10），格式同 S4G，填入 6eead675。
- **待用户决定：** 2 项（S4H 报告 §7）：
  - MY–SG 的参考候选按陆块规则为直流；
  - 是否把参考候选扩到每个有存量交流线的节点对。
  - 另需上云前信息与授权。
- **用户决定（2026-10-18）：** §7 两项维持现状——MY–SG 保持直流候选，参考候选不扩到节点对；首批正式运行用当前 S4H 部署包（6eead675），上云前信息由用户另行提供。
- **交付：** `research/06_scope_redesign/p1_step4h_20261017/`，内容为 S4H_REPORT.md、S4H_EVIDENCE.json、S4H_PROGRESS.md、CLOUD_RESOURCE_ESTIMATE.md §17、CLOUD_DEPLOY_STEPS.md、cloud_package/、evidence/。镜像与审阅 ZIP 在 `work/p1_step4h_20261017/`；测试 `tests/research` 514 通过、整个 `tests/` 531 通过。

## S4I 第 103 项：上云前静态审查（只查不改）— 2026-10-18

- **补记说明：** 本条由 S4K-0 补记（2026-10-18；S4J 报告 §11 第 10 条），S4I 交付时没有写台账。
- **范围：**
  - 指令 `S4I_CLAUDE_CODE_INSTRUCTION.md`（SHA256 5a220e7a…3507c）与续行文件 `S4I_RESUME_01.md`（6edcbb96…2424）。
  - 审查对象：S4H 部署包（代码 6eead675），`sha256sum -c SHA256SUMS` 15 个文件全部 OK。
  - 分支 `codex/s4i-preflight-audit-20261018`（自 PR #32 的 1545067b），draft PR #33。
  - 没有修改模型代码、配置、数据、网络或 SHA 定点；没有求解、下载或连接云端。
- **A 节（四个网络的表面错误扫描）：** 时间、成本、效率、拓扑、松弛、单位、净零、情景差异都未发现错误。阻塞项 K1：VN 非工业电力负荷只有 30.0 TWh（需求表 2050 为 197.2 TWh）。
- **B 节：** 跨境输送没有任何损耗（U1）；TH–MY 直流单向，并受两端固定 2,000 MW B2B 限制（U2）。
- **C 节：** `SOLVER_NOTES.md`：一律用 Gurobi 档案 A；基尔霍夫系数跨度 2,034；右端项最大 6.1e8（R9）。
- **许可与脚本：** 阻塞项 K2：`lanes3` 必然超过学术 WLS 的 2 个会话；U3：预检不检查 `/usr/bin/time`。
- **D 节（INFERENCE）：** 383 个连通联盟；365×24h 串行 235–332 h，两通道 146–216 h；2920×3h 串行 139–297 天。
- **登记：** R1–R11。
- **提交：** 6c88856f、9be3abc1、74315bf0、21ffe8e3，交付 09ffb727（PR #33 最新）。
- **用户决定（2026-10-18 19:44 SGT）：** K1 → 第 104 项；U1、U2 → 第 105 项；K2、U3 → 第 106 项 a、b；R1–R11 → 第 106 项 c；联盟算力估算 → 第 106 项 d（均在 S4J 实施）。
- **交付：** `research/06_scope_redesign/p1_step4i_20261018/`，内容为 S4I_REPORT.md、SOLVER_NOTES.md、S4I_EVIDENCE.json、S4I_PROGRESS.md、evidence/{static,followups,lp,coalition}/；审查脚本 `s4i_static_audit.py`、`s4i_followups.py`、`s4i_lp_ranges.py`、`s4i_coalition_estimate.py`。

## S4J 第 104–107 项：非工业电力负荷、输送损耗、TH–MY 直流与换流器、S4I 其余事项、冒烟、云端部署包与上云前清单 — 2026-10-18

- **范围：**
  - 指令 `S4J_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 c2095744…f348f）与补充 `S4J_SUPPLEMENT_01.md`（188743eb…fac55，第 107 项），都已核对；只实现第 104–107 项，其他发现只记录。
  - 分支 `codex/s4j-demand-losses-20261018`（自 S4I 09ffb727），draft PR #34 叠在 #33 上；每个子步骤提交。
  - 无云端操作，无 365×24h / 2920×3h 求解，无下载；档案 A 参数未改，没有重试。
- **S4J-0：** 登记 S4I §5 答复（K1 → 104，U1 / U2 → 105，K2 / U3 → 106 a、b，R1–R11 → 106 c，联盟算力估算 → 106 d；`s4j_0`）。
- **S4J-1（104）：** 基础负荷 = 需求表居民 + 商业 + 农业及其他 + 交通电力，Astar 只给形状（开关 `research.demand.nonindustrial_electricity`：table_sectors | astar_residual）；东盟 1,079.4 → 1,032.4 TWh，VN 30.0 → 197.2 TWh。
- **S4J-2（105 a）：** PyPSA-Eur 输送损耗（开关 `research.network.transmission_losses`：pypsa_eur | none）：交流线损 2 条切线（PyPSA 0.30.3 `define_loss_constraints`）、直流 0.98 × 0.977^(L/1000)、H₂ / 气压缩耗电 0.018 / 0.01、双向链路拆分 + 反向容量同步（322 对）、CO₂ 无损。
- **S4J-3（105 b）→ 补充 01 (a)（107）：** TH–MY 直流双向；旧写法（零成本 B2B 变量 + 联动等式）使冒烟非最优，改为两台 B2B 双向、不可扩建、固定 20,300 MW（开关 `research.network.th_my_hvdc`：bidirectional_fixed_b2b | s4h）。
- **S4J-4（106 a、b）：** 撤下 `lanes3`，`lanes2` 加 330 秒许可间隔，预检检查 `/usr/bin/time`，首批推荐串行。
- **S4J-5：** S4I 审查脚本重跑，差异全部可归因，无新增问题。
- **S4J-6：**
  - 首次冒烟一体化 SUBOPTIMAL，停止（`S4J_STOP_01_SMOKE_SUBOPTIMAL.md`）；用户授权两次诊断：关闭损耗仍 SUBOPTIMAL；S4H + 旧 S4J-3 最优但门槛不过。
  - 补充 01 (b)：完整 S4J 网络三项全部最优，求解器容差门槛全部通过（(c) 未执行）；目标值相对 S4H +2.65 / +1.91 / +3.07 %，LP +4.1 % 列、+6.7 % 非零元；B6 49.61 bn EUR（7.0 %）；B16 ≤ 1.2e-11；跨境电力损耗 1.48 %。
  - TH–MY 直流 9.3 GW（TH→MY 19.2、MY→TH 2.3 TWh）；交流候选线 20 → 5 GW，额定正好等于交流线损切线的零损耗上限。
- **S4J-7：**
  - 部署包重建到 bcfb2d0a，四个网络与冒烟网络逐组件一致；上传 236,518,964 B；S4H 部署包作废。
  - 365×24h 单运行 37–51 / 41–57 / 52–72 min（悲观 105），串行 2.2–3.0 h；预检下限 36 / 72 GiB 不变。
  - 第二批敏感性 12 项只登记（加 `astar_residual`、`transmission_losses=none`）。
- **待用户决定：** 3 项（S4J 报告 §12）：
  - 交流线损近似与候选线电阻（零损耗上限效应）；
  - 不互联中两台 TH–MY B2B 是否也移除；
  - `th_my_hvdc=s4h` 是否加入第二批敏感性。
  - 另需上云前信息与授权（报告 §10，授权模板填入 bcfb2d0a）。
- **交付：** `research/06_scope_redesign/p1_step4j_20261018/`，内容为 S4J_REPORT.md、S4J_EVIDENCE.json、S4J_PROGRESS.md、S4J_STOP_01_SMOKE_SUBOPTIMAL.md、CLOUD_RESOURCE_ESTIMATE.md §18–§19、CLOUD_DEPLOY_STEPS.md、cloud_package/、evidence/。镜像与审阅 ZIP 在 `work/p1_step4j_20261018/`；测试 `tests/research` 523 通过、整个 `tests/` 540 通过。
- **用户决定（2026-10-18，S4K 指令 S4K-0）：** §12 第 1 项 → 第 108 项（交流线性损耗代理）；第 2 项：不互联中两台 B2B 维持 S4H 状态；第 3 项：`th_my_hvdc=s4h` 只保留开关、不列入第二批。

## S4K 第 108 项：交流线损改用线性损耗代理、冒烟、云端部署包与上云前清单 — 2026-10-18

- **范围：**
  - 指令 `S4K_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 a803f165…25d5，已核对）；只实现第 108 项，其他发现只记录。
  - 分支 `codex/s4k-ac-loss-proxy-20261018`（自 S4J 36b8195b），draft PR #35 叠在 #34 上；每个子步骤提交。
  - 无云端操作，无 365×24h / 2920×3h 求解，无下载；档案 A 参数未改，没有重试；没有触发停止条件。
- **S4K-0：** 登记第 108 项与 S4J §12 第 2、3 项的处理（`s4k_0`）；本台账补记 S4I 条目。
- **S4K-1（108）：**
  - 开关 `research.network.ac_losses`：linear_proxy | pypsa_tangent（S4J 状态）| none；`ac_loss_reference_loading` 0.5（敏感性 1.0）。
  - 损耗 ≥ λ × |潮流|、≤ λ × 允许负载，两端各计一半；λ = √3 × α × s_max_pu × i_nom × r × L / v_nom（一回线，按线型），148 条线 0.77–13.7 %，中位 3.5 %；100 km 核对 1.235 % / 2.470 %。
  - 保留 PyPSA 0.30.3 损耗结构，只把切线换成线性下界，求解 `transmission_losses` = 0；建模核对：代理模型减去损耗项与无损模型逐行相同（EXACT）。
  - 登记为对 PyPSA-Eur 的偏离（理由：候选线扩建幅度远超常见情形、回路数随潮流增加时损耗约与潮流成正比、迭代更新电阻对联盟研究不可行）。
- **S4K-2：** S4I 审查脚本重跑，只多新钩子与 λ 列，无新增问题。
- **S4K-3：** 冒烟三项都最优，求解器容差门槛全部通过（未触发条件诊断）。
  - 目标值相对 S4J −1.30 / −1.10 / −1.52 %；B6 50.42 bn EUR（S4J 49.61，S4H 53.31）；B16 ≤ 1.3e-10。
  - S4J 的 16 条零损耗上限线不再聚集；跨境交流送电 992 TWh（S4H 1,272，S4J 610），交流损耗 4.5 %。
  - 差额（不互联 − 一体化）TH 6.11、LA 2.77、KH 1.89、VN 24.80、MY 4.09、MM 0.72 bn EUR。
- **S4K-4：**
  - 部署包重建到 2d4aaac3，四个网络与冒烟网络逐组件一致；上传 237,121,367 B；S4J 部署包作废。
  - 365×24h 单运行 47–65 / 38–52 / 66–94 min（NZE 悲观 138），串行 2.5–3.5 h；峰值上限 35.1 GiB，预检下限未改。
  - 第二批敏感性 14 项只登记（加 `ac_loss_reference_loading=1.0`、`ac_losses=none`）。
- **S4K-5：** 上云前清单（报告 §10），格式同 S4J（重新打包后填入 56d28358）。
- **用户决定（2026-10-18，S4K 报告 §8 第 1 项）：** 串行预检内存下限 36 → 40 GiB。已改 `preflight.sh`（提交 56d28358）并重新打包：代码 56d28358，上传 237,192,471 B；网络与回执与第一次打包逐字节相同；第一次打包（2d4aaac3）作废，保留为 `cloud_package_dist_2d4aaac3_superseded/`。授权模板改填 56d28358。
- **待用户决定：** 无；另需上云前信息与授权（报告 §10）。
- **交付：** `research/06_scope_redesign/p1_step4k_20261018/`，内容为 S4K_REPORT.md、S4K_EVIDENCE.json、S4K_PROGRESS.md、CLOUD_RESOURCE_ESTIMATE.md §20、CLOUD_DEPLOY_STEPS.md、cloud_package/、evidence/。镜像与审阅 ZIP 在 `work/p1_step4k_20261018/`；测试 `tests/research` 529 通过、整个 `tests/` 546 通过。

## L23 首批云端正式运行（365×24h 日分辨率筛选，部署包代码 56d28358）— 2026-10-19

- **范围：** 指令 `L23_RUN1_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 2c6d9dca…90d2，已核对）；AutoDL 西北 B 区 144 机（12 核 Xeon Silver 4214R，90 GiB），S4K 部署包（代码 56d28358），档案 A（`formal_barrier`），串行，每运行 TimeLimit 10,500 s、墙钟上限 3 h，不重试、不改参数。分支 `codex/l23-run1-20261019`（自 S4K ca5eb801），draft PR #36 叠在 #35 上。本条目由 S4L-0 补记（L23 交付未写台账；S4L 注册表片段 `s4l_0`）。
- **结果（VERIFIED，`L23_RUN1_REPORT.md`）：** 整批 7 h 00 min；一体化 STEPS SUBOPTIMAL（6,722 s）、不互联 STEPS SUBOPTIMAL（5,297 s）、不互联诊断 SUBOPTIMAL（2,311 s）、一体化 NZE 到 Gurobi TimeLimit 后被墙钟上限标记终止（10,814 s）。四个运行 `all_passed_solver_tolerances` 都是 False；B2、B14、B15（无容差）因 1e-8 量级超出而不通过。
  - B6 = 68.97 bn EUR（不互联比一体化高 11.8 %）；NZE 比一体化低 90.46 bn EUR（−17.5 %）；B16 账本恒等式四个运行都通过（4.7e-9–2.9e-7）。
  - 分国差额（不互联 − 一体化，bn EUR）：VN 51.32、TH 7.51、MY 3.21、LA 2.74、KH 2.43、MM 1.13、SG 0.93、ID 0.67、TL 0.12、BN 0.11、PH 0.01，燃料舱 −1.22；方向与 S4K 冒烟全同。
  - 原始违反集中在储能水平上下限（SG / BN / TL 的小生物质池、各国东盟外 CO₂ 储存年末水平）、近零容量 FT 链路与 H₂ 母线平衡；一阶影响 ≤ 4e-7（INFERENCE）；对偶侧未量化。
- **标签（第 112 项 a，S4L-0 登记）：** 四个运行标为 **`SCREENING_UNVERIFIED`**。可用的是原始侧总量（目标值、B6、NZE 差值）；依赖节点电价的分国结算（拥堵租金、跨境结算、按科目分解）与小国差额（PH、BN、TL）不用于结论。
- **NZE 来源（第 112 项 b）：** 接受另行回收的 `nze_late_outputs_20261018T180030Z_5623.tar.gz`（21 个文件，74,285,069 B，SHA256 78a6ea15…c33b；存于 `work/p1_step4k_20261018/cloud_results/20261018T180030Z_5623/nze_late/`，不进 git，与结果包 39b9c9dd…ae7f 分开存放）为本批 NZE 结果；来源为墙钟终止后 `s2_solve.py` 继续写出的求解后文件（报告 §1.3）。
- **实测校正（供 S4L-3 用）：** 实例速度相对本机 0.23–0.30（按 Gurobi work unit）；每次 barrier 迭代 14.9–43.4 s；峰值 RSS 13.8–15.3 GiB（约为 §20 中值的 60 %）；一体化、不互联、NZE 墙钟为 §20 估计上沿的 1.7–1.9 倍。
- **发现但未处理 12 条（报告 §7）：** 含 `preflight.sh` 与监控读宿主机资源（第 1、2 条）、3 h 墙钟上限没有终止 Python 孙进程（第 3 条）——第 112 项 c 交 S4L-3 处理。
- **费用：** 开机到 `DONE` 8 h 20 min，约 ¥9.00；实例许可文件已删除；关机由用户在控制台操作。
- **交付：** `research/06_scope_redesign/p1_l23_run1_20261019/`（报告、证据 JSON、进度、`evidence/c9`、`evidence/c9_summary`）；结果包与 NZE 回收包在 `work/p1_step4k_20261018/cloud_results/`（不进 git）。

## S4L 第 112、113 项：近零量清理、crossover 复测、部署脚本修正、L23 标签 — 2026-10-19

- **范围：** 指令 `S4L_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 03508400…529b，已核对）；第 112 项 a、b、c 与第 113 项 (1)、(2)；其他发现只记录。分支 `codex/s4l-numerics-20261019`（自 L23 efb37fc2），draft PR #37 叠在 #36 上；每个子步骤提交。
- **资源：** 无云端操作、无下载、无 365×24h 求解；本机 56×3h 求解 8 次（用户授权的 8 个，串行，单次 ≤ 375 s、≤ 4.2 GiB，不重试）；档案 A 未改，新档案只新增。触发停止条件一条（清理删除了有经济意义的组件），处理：规则修正、重建、停止求解、报告。
- **S4L-0（112 a、b）：** 注册表 `s4l_0`：L23 四个运行 `SCREENING_UNVERIFIED`（可用原始侧总量；价格结算科目与小国差额不用于结论）；接受 `nze_late_outputs_…tar.gz`（78a6ea15…c33b）为本批 NZE 结果；本台账补记 L23 条目。
- **S4L-1（113 (1)）：** `scripts_project/s4l_layers.py`，开关 `research.numerics.dust_cleanup: off`（缺省，S4K 状态）| `on`（主算候选）；阈值 `dust_capacity_mw` 1（PyPSA-Eur `renewable.hydro.clip_min_inflow` 1.0 MW，配置第 300 行）、`dust_energy_mwh` 1000（项目自定）。清单 818 行（两个情景相同）：删除 597（零上限候选 295、单侧燃料母线 128 + 死端组件 128、全零负荷 38、全零出力 3、小容量 offwind 3、生物质池 2 共 1,456 MWh）、合并 86（`biomass-to-methanol` 97 → 11）、保留只记录 127（FT 链路 100、东盟外 CO₂ 储存 11、塑料废弃物固定源 11、被固定需求锁定的池 5）。清理后 LP 行数约 −7 %（56×3h）。存留组件逐列相同。
  - **发现（§7 第 1 条）：** BN、SG、VN 的固体生物质池总量恰好等于固定生物质终端需求（115,935.8 / 31,510.2 MWh / 125.77 TWh，零余量）；第一版规则删除了 SG、BN 的 5 个小池使两个情景不可行；规则加固定需求守护（`s4l1_pool_fixed_demand_guard`），清理后断言池余量 ≥ 0；修正规则的网络已重建（2983d951），**未求解**。
- **S4L-2（113 (2)）：** 新档案 `formal_barrier_crossover` = 档案 A + Gurobi `Crossover` 缺省 −1（注册表 `s4l_2`，含事先固定的比较标准：目标相对差 ≤ 1e-5、B16 ≤ 1e-6、分国差额变化 ≤ max(1 %, 0.01 bn EUR)）。矩阵 8 个运行：S4K 网络 + A 两个情景最优且与 S4K-3 逐位相同（目标值 648,262,253,996.03 / 698,679,222,969.73，124 / 117 次迭代；`all_passed_solver_tolerances` 仅因 B12 配置哈希为 False）；S4K 网络 + crossover：barrier 与 A 相同，crossover 推进完成后单纯形清理报 `Infeasible or unbounded`（Markowitz 容差收紧，Dinf 1.6e5 / 2.8e7），crossover 用时 0.38–0.54 × barrier，无解返回，不调参；第一版清理网络 4 个运行不可行（原因同上）。标准未改；清理后网络的判定未完成。
- **S4L-3（112 c）：** `p1_step4l_20261019/cloud_package/`：`run_365x24h.sh`（`setsid` 进程组、组终止 + 宽限 + KILL、等待组退出再导出、`RECEIPT_<run>:post_solve|pre_solve`、`killed_pre_solve`、cgroup 内存监控、接受新档案、测试用环境变量）、`preflight.sh`（容器 cgroup v1/v2 CPU 与内存配额、`setsid` 检查）；本机测试 28/28（假求解器、假 cgroup，不用 Gurobi）。`CLOUD_RESOURCE_ESTIMATE.md` §21：L23 校正（实例速度 0.23–0.30、每次迭代 15–43 s、RSS 为中值 0.61；同类实例校正估计 1.7–3.1 h / 0.6–1.5 h）与选机建议 6 条。`make_package.sh` S4L 版准备、未运行；部署包未重建。
- **其他：** `v5_gates.gate_b12_hash` 与 `s2_network.py` 布尔覆盖值接受 `on`；S4L-2 汇总另给 `failed_gates_excluding_B12`。
- **待用户决定（报告 §9）：** 是否授权清理后（修正规则）网络的 4 个 56×3h 运行并据此决定是否采用清理；crossover 档案不建议作为正式档案（可放弃，或另行授权带参数变化的变体，或先看清理后网络上的结果）；第二批云端方案（档案 A、S4L 版脚本重建部署包、TimeLimit / 墙钟按 §21 放大或换更快 CPU、速度探针）；BN / SG / VN 零余量的处理。
- **交付：** `research/06_scope_redesign/p1_step4l_20261019/`（`S4L_REPORT.md`、`S4L_EVIDENCE.json`、`S4L_PROGRESS.md`、`CLOUD_RESOURCE_ESTIMATE.md`、`cloud_package/`、`evidence/s4l_{1,2,3}/`）；`research_inputs/numerics/`；注册表片段 `s4l_{0,1,2}`；镜像 `work/p1_step4l_20261019/`。测试 `tests/research` 534 通过、0 跳过。
- **补记（2026-10-19，用户在 S4L 报告交付后追加授权）：**
  - **S4L-2 续：** 修正规则（固定需求守护）的清理后网络 4 个 56×3h 运行（`results_project/s4l/s4l2b/`）：档案 A 一体化 / 不互联最优（136 / 138 次迭代），目标值相对参照 7.3e-8 / 6.8e-8、B16 ≤ 8e-12、分国差额变化全为 0.0000 bn、交流电价逐母线相同——事先固定的标准全部满足；LP 行数 −7.1 % / −7.4 %；目标值比参照高 4.7e4 EUR（删除的 MY / TL 小池在参照中被使用）。crossover 档案两个情景仍 `infeasible_or_unbounded`（同失败形态）。零余量三国的生物质影子价格在两次最优解之间不同（对偶不唯一）。
  - **S4L-5（只作诊断，未并入主算）：** 各国固体生物质潜力 / 固定终端需求表——BN、SG、VN 比值 1.000，来源为第 36 项 / R1.6 规则（第 55 项 R1 内）把超出潜力的固定生物质需求改由甲烷供给（规则前为潜力的 5.05 / 599 / 2.85 倍）。新开关 `research.s2.industry.biomass_overflow_cap_share` 1.0（主算）| 0.98（诊断）：三国需求设为潜力的 98 %，2 % 按同一规则改气，只改 6 个负荷。档案 A 两个情景最优、门槛全通过：目标 +1.8e-4 / +4.3e-4（+0.12 / +0.30 bn EUR），B6 50.60 bn（参照 50.42）；分国差额变化 PH +0.021、燃料舱 −0.037 bn 超出标准（实质变化），VN +0.156 在容差内；三国生物质影子价格 159–309 → 57–81 EUR/MWh（不互联 155–280 → 68–76），其余国家不变。报告 §10，决定事项 §9 第 4 项。
  - **本机求解合计 14 次**（8 + 4 + 2，56×3h，串行，无重试）；测试 `tests/research` 534 通过（S4L-5 代码后）。
- **补记 2（2026-10-19，S4L-6）：** 用户决定（约 12:00 SGT）采用清理、档案 A、放弃 crossover、零余量维持现状 → `dust_cleanup` 缺省改 on（1655e623），注册表 `s4l_6`；4 个部署网络在 1655e623 构建通过（与 S4L-1 逐组件相同），**未打包**：S4M 指令（12:20 SGT，第 115 项 cap_share 0.98）接手打包；S4K 部署包 56d28358 仍是最后打包版本。

## S4M 第 114–116 项：第二批主算设置、本机冒烟、部署包重建、本机资源核对与分摊输出完整性 — 2026-10-19

- **范围：** 指令 `S4M_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 e791015e…c567c，已核对）与补充 01（8743abd0…7d1e，已核对）；分支 `codex/s4m-mainline-pilot-20261019`（自 PR #37 头 4b4eb92c），提交 921e050b、b15ea69c、8aa2fea0、f50c8850 + 报告提交；draft PR 叠在 #37 上。未上云、未下载；本机求解 4 次 56×3h（档案 A，无重试）。
- **S4M-0：** 注册表片段 `s4m_0`（第 114–116 项、问题来源、范围规则）。
- **S4M-1：** `biomass_overflow_cap_share` 1.0 → 0.98（`dust_cleanup` 自 S4L-6 为 on）；四个网络静态校验通过（921e050b）；S4I 审查与 S4K-2 对照 413 行差异全为预期。**发现：** 0.98 的 2 % 余量解除 BN、SG 小池的固定需求锁定，清理删除 BN 3 个、SG 2 个 < 1 GWh 的池，清理后需求 / 剩余潜力 BN 0.9877、SG 0.9949（VN 0.9800）；余量仍 > 0；待用户决定（报告 §9 第 1 项）。
- **S4M-2：** 冒烟 ×3 最优、门槛全通过（一体化 141 次 / 235 s / 4.10 GiB，不互联 151 / 197 s，NZE 174 / 278 s）；LP 行 −7.2 % / −7.5 %；目标值相对 S4K-3 +1.8e-4 / +4.3e-4 / +2.1e-4，B6 50.60 bn；分国差额 PH +0.021、燃料舱 −0.037 bn 超出 S4L-2 标准（0.98 上限的实质效果，与 S4L-5 诊断逐项相同）。
- **补充 01（只改导出）：** 清单之前 1b / 1c / 1d 缺、3 部分 → 之后四项全部已保存：`s2_solve.py` `assign_all_duals=True` + `s4m_duals.write_duals`（逐约束对偶 `DUALS_BY_CONSTRAINT.nc`，`m.dual` 在本模型上抛 MergeError）、`--costs-table` → `COMPONENT_COST_BREAKDOWN.csv`（9,392 个可扩展组件全部复原 ≤ 1e-6，复合成本按各层公式）、`EXPORTS.json`；授权重跑一次一体化冒烟：最优、目标值与 S4M-2 相对差 0.0、141 次迭代相同；对偶文件离线重建需 PYTHONHASHSEED=0（强网状母线顺序随哈希种子变化；已加拒绝与精确交叉核对，2,516 + 270 条母线相对差 0.0）；新增导出 365×24h 每运行 3.2 GB（< 20 GB）。
- **S4M-3：** S4L 版脚本 + TimeLimit / 墙钟缺省 14,400 / 15,300 s 为运行参数、`speed_probe.sh`（探针网络 + 本机参照 0.537 s/WU，建议 TimeLimit = 14,400 × max(1, 0.25 / r)）、敏感性 16 项；四个网络在 f50c8850 重建与 S4M-1 构建 SHA256 逐一相同；包 22 个文件 260,720,379 B（`cloud_package_dist/`，不进 git）；SHA256SUMS、预检分节、干跑、许可扫描通过；脚本测试 30/30、探针 9/9；`CLOUD_RESOURCE_ESTIMATE.md` §22；S4K 包 56d28358 作废。
- **S4M-4：** WSL `MemTotal` 10.7 GiB（物理 15.7 GiB）不满足 ≥ 24 GiB → 本机试点未执行；`.wslconfig` 未改。
- **待用户决定（报告 §9）：** BN / SG 比值处理；云端探针与试点授权（实例、TimeLimit）；对偶与成本拆分口径；是否保留 `assign_all_duals`；PR 合并顺序。
- **交付：** `research/06_scope_redesign/p1_step4m_20261019/`（`S4M_REPORT.md`、`S4M_EVIDENCE.json`、`S4M_PROGRESS.md`、`CLOUD_RESOURCE_ESTIMATE.md`、`CLOUD_DEPLOY_STEPS.md`、`cloud_package/`、`evidence/s4m_{1,2,3,s2}/`）；镜像 `work/p1_step4m_20261019/`。
- **补记（2026-10-19 约 13:50 SGT，报告交付后）：** 用户决定接受 BN / SG 清理后比值现状（0.9877 / 0.9949，余量 > 0），第二批照 f50c8850 的部署包运行；规则、网络、部署包不改（报告 §9 第 1 项已决定）。云端连接与运行仍待另行授权。
- **补记 2（2026-10-19，注册表第 118 项，用户决定）：** 报告 §9 第 2 项——上云由后续 S4N 指令在新会话执行，本会话不做云端动作；第 3 项——对偶与成本拆分口径接受（对偶文件存原始 LP 行对偶，`marginal_price` 按 PyPSA 约定除以时段权重）；第 4 项——保留 `assign_all_duals=True`（部署包 f50c8850 现状）；第 5 项——#37、#38 保持 draft、暂不合并。§9 五项至此全部有决定；S4M 会话结束。第 118 项的注册表行本会话未新增（如需登记由 S4N 处理）。

## S4N 第 118–119 项：运行内对偶导出验证、云端速度探针、一体化 365×24h 试点与求解档案标定 — 2026-10-19

- **范围：** 指令 `S4N_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 78a6a86c…a39da）、补充 01（e5c6b0d6…d180）、补充 02（9ccd0bfa…0f3d，第 119 项），均已核对；分支 `codex/s4n-calibration-20261019`（自 #38 头 b3b3e5d2），提交 7c4f97fe（标定档案）；draft PR [#39](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/39) 叠在 #38 上（S4O-1 推送）。求解：本机 56×3h 档案 A 2 次、`pypsa_eur_default` 3 次；云端探针 1 次、试点 1 次；全部一次、无重试、无 warm start。
- **S4N-1：** 部署包 f50c8850 本机 56×3h 运行内对偶导出：optimal，目标与 S4M-2 相对差 0.0，756 个约束与离线重建逐值相同，母线交叉核对 0.0；未改代码。
- **实例：** AutoDL 西北 B 区 D58 机（L23 克隆），Xeon Platinum 8470Q，容器 25 核 / 120 GiB；环境 284 个包与本机逐一相同；部署包 22/22 SHA256 OK（中途多路 rsync 中断 `--partial` 覆盖一文件，单路 `--checksum` 重传修复）；预检 OK。
- **速度探针：** r = 0.741（≥ 0.5），探针目标相对差 −2.5e-12；TimeLimit / 墙钟 14,400 / 15,300 s。
- **试点（一体化 STEPS 365×24h，档案 A）：** **optimal**，408 次迭代、barrier 11,470 s、墙钟 3.3 h、峰值 15.1 GiB；第 156 次迭代无提示重启后第二轮收敛；目标 516,252,148,340.37 EUR；运行内对偶 76.7 MB，母线交叉核对 0.0；项目门槛 `all_passed_solver_tolerances` False（A1_A2_S4B 2,371 行超预算、A3_S4B、B3_S4B、B15）。
- **第 119 项 C1：** (a) 原始 / 对偶差 6.4e4 EUR（1.24e-7）、(b) 分国一阶影响 ≤ 1.1e-5 bn、(c) B16 7.2e-9 与 KKT 残差影响 ≤ 6.7e-5 bn，全部通过 → 第一层 + 节点电价结算可用；BN / SG / VN 生物质池行不再主导。
- **C2 档案标定：** `pypsa_eur_default`（PyPSA-Eur v2025.07.0 `gurobi-default` 第 1056–1064 行原样）三次 56×3h 全部 optimal，第 107 项标准全部通过（目标 ≤ 6.2e-6、B16 ≤ 1.0e-8、分国最大为容差 23 %），迭代约为档案 A 的 45 %；其解不通过 A1_A2_S4B / A3_S4B；小写 `crossover` 改变门槛路径识别（发现第 10 条）。
- **回收：** 轻量包 2.08 MB 已下载核对、无许可串；完整结果包 158.9 MB（SHA256 cb4927da…7480）留在实例数据盘；许可 18:56:27 删除，已告知关机。
- **交付：** `research/06_scope_redesign/p1_step4n_20261019/`（`S4N_REPORT.md`、`S4N_EVIDENCE.json`、`S4N_PROGRESS.md`、指令与补充、`ENV_LOCK_LOCAL.txt`、`evidence/`、`scripts/`、试点轻量包），S4O-1 入库（f28772e6，许可串与登录信息模式扫描无命中）；镜像 `work/p1_step4n_20261019/`。
- **用户决定：** 第 118 项（S4M §9 第 2–5 项）、第 119 项（16:37 SGT）、第 120 项（19:40 SGT：以 `pypsa_eur_default` 作生产档案，键名大写、`Threads 8` 两处适配；每次运行验收 = optimal + 第 119 项 (a)(b)(c)）——注册表片段 `s4o_0`（S4O-1 补登）。后续由 S4O 指令承接。

## S4O 第 120 项：生产档案定稿与本机标定复核（S4O-3 停止）— 2026-10-19

- **范围：** 指令 `S4O_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 b5f4d099…af6aa，已核对）；授权 S4O-1 至 S4O-5 本机部分（含 3 次本机 56×3h），S4O-6 云端未授权。分支 `codex/s4o-production-20261019`（自 #39 头 46135c52）。本机求解 1 次（56×3h），无重试；云端无动作。
- **S4O-1：** 标定分支推送，draft PR #39；S4N 交付物入库（f28772e6）；注册表第 118–120 项、台账 S4N 条目（46135c52）。
- **S4O-2：** `pypsa_eur_default` 定稿（键名大写、`Threads 8`，其余原样）并设为缺省档案，档案 A 不改；`s2_solve.py` 拒绝只差大小写的档案键名；C1 并入运行流水线 `scripts_project/s4o_c1_precision.py`（验收 = optimal + (a)(b)(c)，门槛作数值信息；本批参照与重评）；测试 543 通过；S4O 版 `run_365x24h.sh` / `preflight.sh` 脚本测试 50/50、探针 9/9（d5b4eb96、18f55488）。
- **S4O-3（停止）：** 一体化 STEPS（定稿档案，Threads 8）optimal，58 次迭代 / 78 s；目标与 S4M-2 档案 A 相对差 **2.13e-5 > 1e-5**（第 107 项标准不通过）；C1 (a) 不通过（−0.018 bn，相对 2.79e-5），(b)(c) 通过。按 S4O-3 第 4 点在不互联求解启动前停止；不互联、NZE 未运行。只读对照：S4N C2（threads 32）目标差 6.2e-6，补算 C1 三次全过——同一 BarConvTol 1e-5 下结果随线程路径落在标准两侧（INFERENCE）。
- **未做：** S4O-4（打包脚本已写未运行）、S4O-5、S4O-6。
- **待用户决定（S4O 报告 §7）：** 生产档案处理（保留并调整标准 / 收紧 BarConvTol / 回到档案 A / 其他）；是否补做 2 次未执行的本机运行；S4O-4 / S4O-5 是否继续。
- **交付：** `research/06_scope_redesign/p1_step4o_20261019/`（`S4O_REPORT.md`、`S4O_EVIDENCE.json`、`S4O_PROGRESS.md`、`cloud_package/`、`evidence/`）；镜像 `work/p1_step4o_20261019/`。
- **补充 01（2026-10-19，第 121 项，用户决定）：** 生产档案回到档案 A（`formal_barrier`），`pypsa_eur_default` 保留为非生产档案；不补做 S4O-3 的两次运行；第 107 项与第 119 项 (a) 标准不放宽（注册表片段 `s4o_1`）。
  - **S4O-2′（87e28e3b）：** 缺省档案改回 A；部署脚本缺省运行"不互联 + NZE"、TimeLimit / 墙钟 21,600 / 22,500 s、试点一体化作 C1 参照（`PILOT_INTEGRATED` / `PILOT_PRECISION`，副本重评，`PILOT_CONSISTENCY.json`）；`tests/research` 544 通过，脚本测试 59/59、探针 9/9。
  - **S4O-3′（本机 1 次 56×3h，已授权）：** S4O 版 `run_365x24h.sh` 端到端（档案 A，自动 C1）optimal，目标与 S4M-2 相对差 0.0，C1 写入 `EXPORTS.json`，分级与等价核对一致；B12 按构造不通过（配置哈希）。
  - **S4O-4（126110ff）：** 部署包重建，`networks/` 13 个文件与 f50c8850 包逐一相同；`PACKAGE_DELTA.json` 上传 124.3 MB；预检、干跑、许可扫描、脚本测试通过；包在 `work/p1_step4o_20261019/cloud_package_dist/`（不进 git）。
  - **S4O-5：** `CLOUD_RESOURCE_ESTIMATE.md` §23：2920×3h 72.1 M 行、峰值 106–165 GiB、8470Q 上单运行约 15–35 h、2 卡、数据盘 ≥ 100 GB；更正 S4M §22.5 的 365×24h 导出高估。
  - **S4O-6 云端整批未授权，停下等待。**
