# 配置边际费用的来源与方向语义

当前值未修改。共同EUR2020方法不重新批准；746条已为EUR2020的货币记录、FOM及100个FT VOM接线保持。

|费用规则|组件数|来源分类|当前证据|尚需的决定|
|---|---:|---|---|---|
|solar 0.01；onwind/offwind 0.015|340|EXPLICIT_MODEL_ASSUMPTION|冻结config.default.yaml的costs.marginal_cost（EUR/MWh），经process_cost_data覆盖；本研究builder直接沿用这些固定值|保留为明确建模费用并指定币值身份，或明确改作单列数值扰动；不能因小就当来源化VOM|
|DC/B2B约0.00910–0.01099|13|NUMERICAL_PERTURBATION|原run noisy_costs=true；所有13个值与原Link行序、seed174公式逐位一致；源Link默认零加扰动|去除继承扰动，或明确新的方向不变输送费用/数值正则方法|
|已冻结燃料、技术VOM及本轮前已修复FT|原有范围|SOURCE_BACKED_VOM|既有cost/source转换链|本轮保留，不再通胀或新增费用|

来源：official/author_run/scripts/solve_network.py:165–173，config.default.yaml costs.marginal_cost；参考network meta git_commit=5bacad702ccfed17ad19ab510fa710651e966f2c，run=baseline-aims-3H，wildcard2025/100clusters/3h/DEC；只读输入字段与meta，未读取p_nom_opt、dispatch或对偶。原费用为 `0.01 + 0.002*(RandomState(174).random_sample(len(reference.links))-0.5)`。这是数值扰动，不能写成EUR2020来源化可变运维。复制参考输入字段仍可能复制求解准备阶段改过的参数；本发现解释了该风险。

冻结PyPSA0.30.3 `optimization.optimize.define_objective` 对Link-p直接采用 `sum_t weight_t * marginal_cost_t * p_t`。12条Link的p_min_pu=-1、efficiency=1；另1条只能正向。故+100MWh和-100MWh费用符号相反，bus0/bus1互换会改变同一物理输送的扰动贡献；并非epsilon*abs(f)。相连的相反取向平行连接可能引入循环流的数值激励，是否发生依赖完整约束，本轮没有求解或声称实际发生。

待审方案：

|方案|表达式/实现|报告与容量含义|状态|
|---|---|---|---|
|T1 去除参考数值扰动，13条无损连接可变输送费为0|仅将这13条已溯源扰动去除；保留资本费用、FOM、效率、容量和拓扑|推荐首版候选；不等于删除输电成本|未批准|
|T2 对绝对输送量收费|单一有符号f与同一扩建K；g>=f,g>=-f,g<=K，费用c*g且c>0|需另外批准系数及经济/数值含义；不可虚构真实输送费|未批准|
|T3 保留方向不变数值正则|可采用T2结构但标为数值项；另行报告，不混作经济成本|仍会影响解，不能声称无影响；固定、可复现系数，不重新随机抽样|未批准|
|保留当前epsilon*f|含负向补贴并依赖端口命名|不推荐；不能只更换价格年标签掩盖方向问题|未批准|

若采用两个非负方向变量，两者必须共享一个K（例如f_plus+f_minus<=K），不能获得两份独立扩建容量。两方向费用方法未实施。
