# Buildings 国家 → 区域/节点分配候选

Material Passport: academic-research-suite / proposed method; Phase3A5 v1; 2026-10-02。方法契约可执行，权重数据和方案未获接受；未生成节点热需求。

固定规则：R与S、space与water各自分配；仅使用本国节点；权重非负且有限；每国/部门/用途归一；国家总量守恒。正总量但权重和≤0必须停止。不能自动uniform fallback，也不能把MY Peninsular样本扩散到Sabah/Sarawak或所有ASEAN。

对已接受服务Q_c,s,u，候选权重a_c,n,s,u满足coverage后：`Q_c,n,s,u=Q_c,s,u×a_c,n,s,u/Σ_n∈c a_c,n,s,u`。这只是数学分配恒等式，不是权重合理性的证据。

| 权重候选 | 合适用途与优点 | 风险/所缺证据 |
|---|---|---|
| population / households | R water的潜在人口/家庭活动基础 | 必须有接入率/使用率、城乡/收入差异；人口不自动等于热水使用。|
| Residential floor area | R space结合气候/建筑存量 | 需占用、保温及供暖普及率；全国面积不能抹平气候区。|
| commercial floor area by class | S按服务业建筑类别 | 酒店/医院水热强度异于办公室；须有分类与node交叉表。|
| service activity | 床位/入住夜数/就餐/就业等分用途 | 需类别能量强度及2019活动版本；不能不加权把不同单位相加。|
| GDP | 部分商业活动的代理对照 | GDP包含非建筑活动，不能默认作为S唯一权重。|
| urbanisation | R/S结构的分层变量 | 城镇率本身不是负荷值，需与用途调查覆盖一致。|
| climate zones / degree-hours | 已有正space service地区的空间限制 | 须有真实区域范围/阈值；不能将热带无列的国家直接设零。|

最接近可进一步执行的来源是MY商业12类别与住宅4区域/房型；尚缺这些类别/区域对全国总量及模型节点的加权映射。VN northern/local heating证据仅可限定后续调查地域，不能据此把全国电热集中到Hanoi。现有总电力GDP0.6+人口0.4分配来自另一负荷口径，不自动继承。

需保留Region、节点国家映射版本/哈希、coverage、各类权重分母、年份与人工选择。候选比较可先评估覆盖率和可复现性；本轮不替用户选择数据驱动与代理方案，也不默认用人口填所有Services。
