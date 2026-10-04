# 当前 CO2 实现链

直接证据来自 Gate2 HEAD `ad5e81e75882704ac9e33a6eac96c5c79717c5e1` 的三个源码字节副本及当前安装的 PyPSA 0.30.3 `define_primary_energy_limit`。副本位于 `evidence/source/scripts/` 与 `evidence/PYPSA_PRIMARY_ENERGY_FUNCTION.py`；不拿旧文档行号代替当前快照。

| 链条 | 当前实现与风险 |
|---|---|
| prepare_sector_network.add_co2_budget:3578–3639 | annual=base_value*year factor，再乘 sum(objective weights)/8760；没有 power 用途过滤 |
| prepare_network.add_co2limit:149 | CO2Limit、carrier_attribute=co2_emissions，默认 primary_energy |
| PyPSA define_primary_energy_limit | Generator 加权 p*因子/效率 + 非循环 Store 的末期/初始库存项；不是 sector 标签筛选 |
| add_co2 | atmosphere carrier co2_emissions=-1，因此大气末期增量进入旧总账 |
| convert_conventional_generators_to_links:3720–3809 | 燃烧 Link 的 atmosphere 端口报告排放；fuel 源 carrier 因子设0，避免源+燃烧双计 |
| solve_network:939–954 | stored CO2 总库存上限，属于物理资源，不能替代政策预算 |

当前 baseline `co2.budget.enable=false` 保持不变。已有 DEC 年度限额不变：2025/2030/2035/2040/2045/2050 = 1000/820/640/460/280/100 MtCO2。不能为本轮测试将 baseline 自动打开，也不引入国家配额。

恢复非电部门后沿用 aggregate atmosphere cap 会让非电燃烧消耗 Power cap。新接口只接受明确的发电/原供电用途系数表达式，不以“与电网连通”或“名字像化石发电”替代边界。供电 H2/SMR、CHP 分摊与 geothermal 等原因子均不能遗漏。

参考映射 1354 条：283 标作 Power 候选，638 非 Power，288 共享用途待定，145 捕集/来源待定。所有行 `NumericAccepted=false`；True 是范围候选分类，不是参数确认。缺少 emission factor 的行保留空缺。该表来自历史 tutorial + 当前源码角色比对，不是 paper 复现，也不是新 Research 组件清单。

`install_power_policy` 拒绝未完成 scope、非电权重、重复组件以及遗留 aggregate cap 共存；以物理 generators snapshot weights 计算排放，要求与原 objective hours 总和一致，保留 /8760 缩放。安装只作用于已有变量，不调用 create_model 或 solve。本轮 Linopy 仅合成变量，检查 RHS 与实际变量标签，无优化。
