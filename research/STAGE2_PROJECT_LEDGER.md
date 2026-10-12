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
