# 碳约束等价性

**键和值的等价性通过；Full-SC排放范围的等价性未通过。** Baseline与DEC两组均保留；本轮未新增碳政策、未分配国家配额。

| 年 | 论文DEC MtCO2/年 | 混合键实际 Mt | 修复后 Mt |
|---|---:|---:|---:|
|2025|1000|77.5|1000|
|2030|820|63.55|820|
|2035|640|49.6|640|
|2040|460|35.65|460|
|2045|280|21.7|280|
|2050|100|7.75|100|

旧入口：`co2_budget.co2base_value`；正式新入口：`co2.budget.base_value`；当前ASEAN混合入口：`co2.budget.co2base_value`。`_helpers.migrate_config`迁移旧顶层入口，但不迁移混合入口；消费函数`prepare_sector_network.add_co2_budget`读取base_value，默认limit会引用co2.limit=77.5e6。修复只重命名ASEAN配置键，不改变1e9基数/系数/enable=false。

测试执行了实际迁移与实际budget/add_co2limit函数，创建PyPSA GlobalConstraint并核对六个年限额；另测8760h/144h缩放。`constant = base × year_factor × snapshot_weight_sum/8760`。旧legacy和修复后的新配置一致。混合用户自有配置仍须显式迁移；没有宣称改了helper以支持任意混合配置。

## 实际统计范围

作者网络中不为0的carrier因素是geothermal=0.12、co2=−1；CO2 atmosphere为非循环Store。电源CCGT/OCGT/coal/oil/lignite等通过多端Link排放到atmosphere，保留的SMR/SMR CC也在此记账；作者Baseline样本还含biomass Link。最终作者电力案例包括服务其电力/H2转换链的排放，因此不能把口径简化成“仅名字为coal/gas的Generator”。作者DEC2050实际GlobalConstraint为primary_energy/co2_emissions/100e6，Baseline没有CO2Limit。直接读取证据见 [PAPER_CARBON_ACCOUNTING.json](PAPER_CARBON_ACCOUNTING.json)。

当前add_co2建立共享大气Bus/Store；非电热锅炉、工业燃料、交通等部门也接入同一排放记账，燃料carrier因素可能置零避免重复计数。primary_energy约束对非循环Store末期碳变化及有非零carrier因素的Generator等计数，并不知道“电力研究口径”。关闭H2/CO2 network并不能阻止共享排放Store扩张范围。

单时段合成单元测试（HiGHS，非ASEAN实验）保持一单位电力服务：电力燃烧排0.4t；加入一单位非电热服务后同一GlobalConstraint记账为0.65t，+0.25t来自非电燃烧。两例optimal。见 [CARBON_SCOPE_TEST.json](CARBON_SCOPE_TEST.json)。此证据验证机制，未量化ASEAN新增排放。

## 保持电力口径的最小候选修复（未实施）

1. 在项目层为电力供应链建立独立排放ledger或独立线性约束，限额沿用上述区域轨迹；保留full-SC总排放账作报告，不将其直接用作原DEC预算。
2. 显式标识电力燃烧、地热、供电H2的制氢排放与capture credit；不得遗漏论文已有SMR/SMR CC链，也不得对燃料输入和大气Store重复计数。
3. CHP电/热联合产出、共享H2/合成燃料服务电与非电、DAC/CC信用如何归属，是保持原口径时必须阐明的边界。需要共同确定或恢复作者等价处理，不能凭技术carrier名称自动分摊。
4. 最小验收测试：paper裁剪网络预算表达相等；只增加非电服务不改变power账；燃料和CO2守恒；捕集/负排放不重复；Integrated与Disconnected拥有相同区域预算及排放定义。

这项范围修复没有执行。不能因所有六个数字一致就宣布DEC等价；也不能给每个standalone国家复制100Mt。未来Disconnected仍是同一个区域模型，保留区域CO2共享约束。Baseline无显式总碳上限，但其他CC/资源上限也需同样冻结。
