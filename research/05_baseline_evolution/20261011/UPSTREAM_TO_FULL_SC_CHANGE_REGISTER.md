# Upstream to Full-SC change register

2026-10-11；A-01：**COMPLETE_WITH_EXPLICIT_UNKNOWNS**。本账覆盖现有证据支持的结构、数据、约束和科学边界变化，不声称逐条重新认证全部原始统计数据。没有改动模型、重新构模、运行求解器或操作AutoDL。

## 1. 三个基准不能混用

| 基准 | 核实身份 | 正确解释 |
|---|---|---|
| 论文结果的实际历史代码 | `5bacad702ccfed17ad19ab510fa710651e966f2c`；两份结果网络配置均嵌入此commit | 100节点、3h、2013气象索引、myopic；2025与2050结果配置 `only_elec_network=true`。不能把较新的完整SC默认配置当作这两次实验配置。 |
| 论文发布源码 | `99159edb7298b847fea517bf05c3f388493501c9` | 发布节点，不取代结果内嵌的运行commit。原生求解器确切版本、完整论文实验矩阵尺寸及全阶段资源记录仍UNKNOWN；不以我们19.57m列推断论文相同规模。 |
| 上游SC参考 | `a3616a68ee44592af6527ca9024a90f1956646ae` | 2026-09-22合并的部门耦合实现；已有生物质、H2、SMR、FT、热、工业、农业、运输、CO₂机制。不能把这些概念整体记为Stage2发明。 |
| 本次源码审计基线 | `b9be7d0ab788a4151346c098d2e657c7e94a22da`，`research/full-sc-baseline` | 独立审计分支从此创建；不是Windows历史Git，也不是GitHub main。 |
| 实际Gate6物理对象 | NetCDF SHA `238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d`；构模Manifest code_sha=`4b5611dc2dbc3ebcc2ae69b3782b338d2a18b6ce` | 2050单年、2920×3h、3443 Bus、1737 Load、860 Generator、3358 Link、105 Line、1104 Store、43 StorageUnit；冻结LP为19,568,505列/48,301,938行/90,782,037非零元。源码HEAD与构模时刻须区分。 |

上述commit对象均本地存在，远端身份见[S0_STATE](evidence/S0_STATE.json)。[SOURCE_LINEAGE_INDEX](evidence/SOURCE_LINEAGE_INDEX.json)记录逐文件commit/blob/SHA256；[FROZEN_SOURCE_LINKAGE](evidence/FROZEN_SOURCE_LINKAGE.json)确认主要物理builder、carrier、fixed_accounts、原registry及配置与Gate4封存副本逐字节相同。`assembly_components.py`有后续执行授权门控变化（新增execution_context，94–101行），其物理hook调用和方程未随该差异改变；`fixed_inventory_scaling.py`/Gate6执行配置在Gate4归档中尚不存在，不能说它们也已逐字节匹配。

两个论文结果的有效配置均为 `biomass_transport=false`、`solid_biomass_potential=360 TWh/a`、`biogas_potential=0.5 TWh/a`、`international_bunkers=false`、`co2_network=false`。默认SC配置则可为40/0.5、biomass_transport=true；ASEAN覆盖配置为360。**默认、地域覆盖、结果有效配置分别记录，不拼成一次虚构运行。** `sector.enable`多项true也不等于所有最终组件保留：历史[final_asean_adjustment](https://github.com/pypsa-meets-earth/pypsa-asean/blob/5bacad702ccfed17ad19ab510fa710651e966f2c/scripts/final_asean_adjustment.py#L377)按carrier筛选，保留部分与电力相关的H2/燃料/CO₂组件。故“电力为主”不等于完全无耦合设备。安全摘录及配置SHA见[PRIOR_EVIDENCE_SUMMARY](evidence/PRIOR_EVIDENCE_SUMMARY.json)。

## 2. 差异总账

证据等级：V=原源码/配置/冻结元数据/已核验原件；D=列明条件的数学推导；R=待证明风险；U=UNKNOWN。表中“改变”指科学可行域或目标，与执行数值容差不是同一层。引用缩写在下一节均有固定commit和行位置。

| ID / 类别 | 上游原始实现 → 当前实现 | 修改原因及可行域/目标影响 | 代码/证据 | 已知边界与风险 |
|---|---|---|---|---|
| C01 继承/时空 | 作者100节点3h、2013索引 → 保留100地理节点与2920×3h；新增载能体和账户Bus | 保留电力输入边界；不是从小时降为3h的新增改动 | P、B29–49、E41–60 | V；同时间格不代表同LP规模或需求。 |
| C02 数据/规划 | 上游myopic多期、继承既有装机逻辑 → 单年2050，独立筛选存续设备、固定存量与新增容量分开 | 目标年与存量证据冻结；改变资产集合及容量可行域 | E84–164；Gate4_ASSET_INHERITANCE_DECISION；B135–145 | V；未继承论文最优容量/dispatch。缺失寿命的外部存量边界已作为科学限定保留。 |
| C03 覆盖/装配 | 上游prepare_sector_network与final_adjustment → 专用输入注册、allocation、无Load配方合并，再绑定一次 | 防止部门需求泄漏、旧Load双加；实质改变组装路径 | B15–19、135–168；Y72–88 | V；禁用旧builder不意味着每段旧代码已删除。 |
| C04 需求/数据 | 电力增长、部门原输入链 → A*终端用电父账户、2019重构、2050 AEO8 BAS与获批增长代理 | 终端用电不是发电量目标；燃料用电力年量节点份额与平坦时序代理；改变RHS | Y2–21、89–101；registry；Phase3 closeout | V；国家/载能体逐年直接预测不足处是明确代理，不是观测值。 |
| C05 需求/工业农业 | 上游已有工业与农业耦合 → 采用已接受最终能源账户；保留煤/生物质等非电义务，不把Mode B工艺内生替代当已实现 | 账户完整与需求所有权；改变需求/替代空间 | Y、E220–250、registry；Phase3 closeout | V；本Full-SC不是上游所有产业工艺的逐项复刻。 |
| C06 需求/热 | 上游热服务设备、供热profile → 未获批热服务继续嵌入原最终能源；禁止重复物化Load | 避免未经依据拆分及双计；改变可选技术/终端服务表达 | Y20、E231–250、Phase3 closeout | V；热服务技术可替代性不等同上游。 |
| C07 需求/道路 | 上游BEV/V2G/燃料电池及电动份额 → road EV嵌入A*，不单独建立EV用电；非电道路采用获批代理 | 保留总账所有权，不用路线总参考强制二次等式 | Y90–99、registry | V；新增EV灵活性不是当前已获准功能。 |
| C08 边界/航运航空bunker | 上游可设国际bunker，所引论文两结果false → 接受的国内航运航空及国际bunker常数2019边界 | 弥补研究边界而非冒称2050预测；改变需求RHS | Y96、100–101；Phase3 closeout、输入决策 | V/R；未来需求偏差仍是科学假设风险。 |
| C09 继承/转换 | 上游已有电解、SMR/CC、FT、燃料电池及储氢 → 当前重建获批本地端口和效率，100个H2 Store | 显式国家/节点所有权及成本来源；不应记为全新技术概念 | U344/384等函数；E185–213；B91–104 | V；实际允许集合受冻结配方限制，蓝图中的其他技术不是自动启用。 |
| C10 边界/共享池 | 上游部分network=false可使用Earth资源池 → 当前国家/节点独立燃料Bus，禁跨境H2/gas/CO₂/biomass/合成燃料 | 将电力互联与非电燃料共享解耦；改变可行域 | U1004–1070；C29–51；B53–68；Y24–44 | V；不同国家同价只共享元数据，不共享物理供给。 |
| C11 数据/化石供给 | 上游燃料源/池与参数化供给 → coal/lignite/oil/gas各节点独立外部Generator，获批无年度/容量上限 | 显式外部市场边界；改变/明确供应可行域及价格 | E185–188；C93–119；Y102 | V/R；是科学假设，不是已查明本地矿产量，也不是免费能源。 |
| C12 新增/固定资源 | 上游区域技术潜力有限Store，可去发电/产业等 → 807个需求派生、商品细分、节点独占Store，385组final obligation | 未知价格/CO₂因子暂外置，禁止挪去power/H2；明显改变资源含义/用途可行域 | U1118–1261；E214–249；F17–79；RESOURCE_STATIC_LINEAGE | V；不是360TWh潜力分摊、不是807项独立供给观测。详见A-02。 |
| C13 继承/新增方向约束 | 原生Store库存递推及上下界 → 同一机制 + 本项目逐Store p≥0方向hook | PyPSA Store无p_min_pu输入；防止有限账户充电造资源 | C250–256、289–303；F50–57；实际807 ResearchStoreDirection行块既有回执 | V；e≥0与p≥0不同；不把方向hook误称新增库存方程。 |
| C14 删除/替换 | 上游solid biomass/biogas潜力Store和利用路径 → 电力输入抽取只复制battery/home battery Store；再新建H2、账户及Atmosphere | 有意保留已接受技术/数据；更换生物质供应科学边界 | E130–134、214–249；静态1104 Store carrier计数 | V；冻结网络没有旧solid biomass/biogas供给Store与807并行。 |
| C15 网络/设备 | 源AC/DC/B2B、分布网、电池 → 继承输入拓扑、重新绑定2050成本、存量/资源占用，电池逆变器容量等式 | 防止充放电设备额定容量脱钩、重复潜力；改变/明确容量约束 | E64–140；H70–113；存量决策 | V；196个ResearchBatteryNominal属当前安装方式，配对概念上游已有，不宣称发明电池耦合。 |
| C16 碳政策/核算 | 上游CO₂ carrier因子−1及可配置预算/地质Store → ReportingCO₂与Power政策分离，实际policy=false，地质库存未启用 | 不混用全系统排放与电力政策归属；改变政策/技术边界 | U1408–1484；Y46–63、104；B69–90；碳矩阵审计 | V；100m t配置数值未激活；无实际CO₂ cap，也无Atmosphere年末归零隐限。 |
| C17 全局约束 | 上游可有碳、输电等GlobalConstraint → 当前仅lv_limit | 只保留获批输电扩建体积；约束仍为实际可行域的一部分 | E72–78；碳矩阵审计row45945301 | V；上限353,746,853.52332264 MW·km，115容量项，不是碳预算。 |
| C18 成本/价格 | 上游准备成本及技术燃料表 → 可用参数EUR2020、存量FOM固定项一次计；807未知价格与物理CO₂因子NULL | 防止虚构商品价、固定FOM双算；改变已计价目标与报告完整性 | E价格层、F58–65、97–108；price_basis；V3局部回执 | V；全部系统总成本/完整排放仍不具备，不把零实现系数称科学免费资源。 |
| C19 目标微扰 | 作者noisy_costs随机遍历 → 稳定资产映射AUTHOR_METHOD_ADAPTED_SCOPE_V3，有获批例外 | 改善数值且跨情景共同资产一致；**改变目标，不改变物理可行域** | V3目标SHA6dff…；SCOPE_V3_LOCAL_AUDIT；FINAL_LOCAL_CLOSEOUT | V；排除12 DC/B2B、98分布网、807 Store+807 meter、Atmosphere新增边际项；资本项保留。10,628,915系数相对原目标改变，offset−12,788,967.997821666 EUR。不保证原未扰动目标最优。 |
| C20 数值/执行 | 原始LP→旧D/R→P2_V1正对角幂二、α=1；HiGHS/Gurobi、精度参数与独立监督变化 | 数学等价表达/算法，不应归入新科学约束 | 既有P2全量及生产交接审计，S0引用 | V；原单位残差逐位保留，未证明当前模型可行；本轮不重扫9078万系数。 |
| C21 验收/报告 | 求解器状态/结果网络 → V4原单位、807/385、KKT、双成本、无Basis导出及封存 | 改变资格判断，非LP约束；不允许事后放宽 | 已批准V4 SHA955c…；两次真实回执及G6台账 | V；首轮OPTIMAL仍NOT_ACCEPTED；第二轮INF_OR_UNBD无候选。 |
| C22 上游直接修订 | 工业分配、热profile、services carrier、航运、GDP/OSM工程防护 → 国家内权重归一、正需求不静默归零、港口对齐与拼写修正 | 历史管线修复；只有进入实际输入链的部分影响冻结LP | pinned git diff：scripts/{build_industry_demand,prepare_heat_data,prepare_sector_network,final_asean_adjustment,build_shapes,download_osm_data,_shipping_allocation,_osm_download_retry}.py | V；8个上游脚本有差异，但当前专用assembler禁用旧部门需求builder，不能把每个历史修订都说成Gate6活跃方程。 |

## 3. 可定位源码与变更路径

- **P**：两份论文结果有效配置及既有原作者审计，路径/SHA见[PRIOR_EVIDENCE_SUMMARY](evidence/PRIOR_EVIDENCE_SUMMARY.json)。只发布安全字段，不提交含外部服务配置的完整JSON。
- **U**：[固定SC上游prepare_sector_network.py](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py)；生物质空间1004–1017、biogas1058–1070、有限资源1118–1238、CO₂1408–1484；函数add_industry1853、add_heat2614、add_agriculture3142、add_co2_budget3601支持“已有SC”判断。
- **E**：[build_research_assets.py](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/build_research_assets.py#L41)，重点214–249。
- **B**：[build_research_network.py](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/build_research_network.py#L26)。
- **C**：[carrier_architecture.py](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/carrier_architecture.py#L219)。
- **F**：[fixed_accounts.py](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/fixed_accounts.py#L17)。
- **H**：[assembly_components.py](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/assembly_components.py#L70)。
- **Y**：[baseline.yaml](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/configs/research/baseline.yaml#L1)。其中solver_allowed=false等是构模/输入门控，不拿它否定后来独立授权执行回执。checked-in gate6_baseline_3h.json的早期IPM参数也不是两次Gurobi实际参数。
- 当前输入：[registry](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/research_inputs/assembly_v1/registry.json)、[BASE_RECONSTRUCTION](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/research_inputs/assembly_v1/sources/BASE_RECONSTRUCTION.json)。行级SourceSHA/PhysicalLine/RowID保留，不用文件名猜测来源。

资源路径重要提交：`18eb5827e4e19588dc4f31b8355319818c5fb950`（2026-10-05，创建固定Store/meter配方）；`b21aa365a5ea750bc6a48b1424b09e9880caa07d`（10-06，外置待核固定账及EUR2020资格）；`cfc7b531c221647bffe8dda46b3c8ef5b4e954f9`（Animal waste限定批准）；`002f2a6dcbd4d57335653867e8f12a2b024c93ec`（旧固定库存数值归一化）。后者不是创建资源Q或放宽库存的科学提交。全部元数据见SOURCE_LINEAGE_INDEX。

文件级总账为[PINNED_PATH_CHANGE_INVENTORY](evidence/PINNED_PATH_CHANGE_INVENTORY.json)：在scripts/scripts_project/configs/rules/输入等指定范围内217条路径变化。它补足可查范围，不把每条新增文件都包装成科学变化；测试、工程脚本和数据表行的真实性不等于文件存在性。

## 4. 与物理违约的关系及尚缺内容

直接关联最强的是C12–C14：第一轮库存下界和final obligation平衡违规实际落在新建固定账结构上；源数量、端口、行号和候选值已接通[A-02详细溯源](RESOURCE_STORE_LINEAGE_AUDIT.md)。**这证明失败发生在哪里，不证明建立该结构必然使全LP不可行。** 旧D/R下绝对数值残差小而原单位很大的关系已经证明；“唯一根因就是缩放”没有证明。新增碳上限造成失败无证据，因实际无该上限。

尚缺/不能代填：论文全部实验的原生log、硬件及完整矩阵身份；上游技术潜力与当前终端固定义务可比的科学论证；未知商品供给价格/排放因子；所有增长代理与商品份额的独立实证优劣；第二次完整31文件归档尚未全同步（10份核心原件足够现有状态与交接判断）；全LP可行性证书/不可行或无界独立证书。以上不要求本轮新增优化或无限准备。

A-03可在用户审阅后开展**限定资源义务语义、商品份额和已有代表性行的静态核查**。须先决定是否继续把这批账户定义为固定消费核算边界，还是未来要研究独立资源供给/可替代技术；后者改变科学问题，不能以求解失败为由自动实施。G6-05保持暂停。
