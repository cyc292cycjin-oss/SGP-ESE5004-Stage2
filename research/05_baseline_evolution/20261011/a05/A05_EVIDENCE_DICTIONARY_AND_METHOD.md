# A-05 数据字典、核验方法与复核边界

## 可复核文件

- `A05_CROSS_BORDER_ASSET_INVENTORY.json`：三份实际NetCDF的静态摘要、逐跨境资产端口/参数、载体参数分布、公共池接口、燃料供给与H2例子。约2.3MB，不包含NetCDF或调度。
- `A05_ELECTRICITY_INPUT_DIFF.json`：当前与论文2025的Line/DC/B2B静态输入身份和字段差。缺失的inactive efficiency3与实际端口系数分开解释。
- `A05_SAFE_EFFECTIVE_CONFIG.json`：两份论文配置的白名单字段及原配置SHA，不含服务凭据。
- `A05_REACHABILITY_AND_BOUNDARIES.json`：国家对汇总、100个H2节点终端端口联结、实际Store类别及燃料价格。
- `A05_SOURCE_AND_DECISION_EVIDENCE.json`：固定commit源码片段、行号、Git blob SHA、SHA256；有限关键字检索原输出；Phase3决策原文和SHA；冻结构模清单摘录；方案A既有回执原样引用。
- `A05_EVIDENCE_INDEX.json`：本轮文件完整SHA/大小和原版本绑定。自身哈希由Git及ZIP清单承载，避免自引用。
- `verification/capture_code.py`、`extract_a05.py`、`finish_evidence.py`：确定性只读方法；固定本机输入路径，复核者只需替换根路径。使用netCDF4/numpy读取静态字段，不导入PyPSA Network或Gurobi，不调用模型生成代码。
- `verification/verify_a05.py`：复核输出计数、国家/端口关联、参数差边界和来源SHA；不重跑此前工程或科学实验。

## 口径

Bus国家优先采用存储的`Bus.country`；缺失时只沿**完全相同的Bus.location引用**追溯已知Bus.country，禁止资产名前缀猜测。`Earth`/无归属Bus独立列入unresolved。当前唯一无国别Bus是ReportingCO2 atmosphere；两份论文另有co2 stored、Earth lignite、Earth solid biomass共同池。

Link正向flow下bus0系数−1，bus1为efficiency，其他端口为efficiencyN；空Bus或零系数不构成有效边。次端口负效率是共同输入。p_min_pu<0时另报告允许反向。跨国类型按**全部有效非大气端口**国别，而非仅bus0/bus1或资产名。Line/Transformer单独分类，电力载体集合为AC/DC/electricity/low voltage。

纯大气报告的两个版本载体标签`co2`/`co2 atmosphere`已由来源构造代码和Store检查确认；仅其国家为空时从物理运输图排除。上游`co2 stored`不能排除：它能供给FT/Sabatier，是跨国共享物质池。报告池不是有地理距离的CO₂管道。

多跳国家检查在非电端口上构建无向连通分量，只用于发现任何潜在共享路径；无向图不证明物质流可运行，亦不能替代带方向、容量、共同输入和逐时平衡的可行性检查。电力媒介的跨国耦合没有被否认。H2→FT→oil Load专项检查保留共同CO₂/电力输入警告。

所有网络均PyPSA0.30.3。静态字段未存储时按同版本`component_attrs/*.csv`默认值读取，记录CSV SHA及`defaulted_fields`；∞在严格JSON写成字符串`Infinity`，NaN写null。`p_nom_max=Infinity`必须与extendable一起解读；固定容量时不是无限容量。`e_cyclic`是年度循环库存约束，不是国际进口。论文两个网络有196条Link的时变p_max_pu索引，但与跨境资产交集为空；只读了这些索引，未读取动态值。当前分支资产无时变界字段。

容量：Link p_nom为输入侧MW，Store e_nom为MWh，AC Line s_nom字段单位MVA。发电/化石供给为MW，边际成本按输入能源EUR2020/MWh；资本为年化EUR2020/名义功率（或库存能量）。CO₂流/库存应依构造器排放因子按tCO₂理解，旧Bus默认unit=MWh或空字符串不是可靠碳单位；不据此把CO₂当能源。年度Q与固定账户复用A03精确证据，未重新积分或扫描CSC。

NetCDF参数是输入字段，不是优化后容量、实际流量或SCOPE_V3完整扰动目标。旧输入build_year等字段原样披露，本轮不重建活跃期掩码或认证现实资产寿命。跨境容量加和仅为标签化描述，不是输电可靠容量。

## 身份与不重复计算

大文件SHA来自已有验证清单/构模Manifest，本轮复用，并检查文件大小/版本。新小文件、指定Git blob、批准方案A回执实际计算SHA；没有虚称再做三个大文件全哈希。科学源码b9与构模代码4b的绑定复用原 `evidence/FROZEN_SOURCE_LINKAGE.json` 和 `SOURCE_LINEAGE_INDEX.json`。不是仅凭当前HEAD源码假设它生成了旧网络。

读取时间序列调度、优化容量、CSC、大向量、运行求解器及云端访问均为0。没有执行历史check_research_carriers.py（其早期模板检查语境与已物化网络不同）；仅阅读源代码，并独立静态核对实际网络。

## 局限

这是一份模型实现与边界谱系审计，不认证燃料产地/进口可用量，不证明2050项目数据真实性或全LP可行性。共同池可达性并不证明跨国流量曾实际发生；所有“作者实际”指文件里存在的结构，非依配置推断的实验行为。缺失跨境管网不等于无外部燃料供应；原科学边界及未来方案应由用户决定。

复核顺序：先将脚本根路径指向已有只读输入和独立输出目录；依次capture_code → extract_a05 → finish_evidence，然后verify_a05。只复核已交付JSON时直接运行verify_a05即可，不必重新读取网络。capture_code生成的中间CODE_CAPTURE不是另一个科学输入，其全部字段已进入最终SOURCE_AND_DECISION证据。
