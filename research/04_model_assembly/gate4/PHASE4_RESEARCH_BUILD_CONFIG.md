# Research 配置：已加防护，尚不是可运行完整构网配置

沿用 base config + project overrides。`research_demand`、`research_carrier_architecture`、`research_carbon` 的 Gate2/Gate3 控制块保持逐字段一致；Integrated/Disconnected overlays 无改变。

新增 Research override：

- `demand_data.update_data=false`：不刷新已经冻结的数据。
- `final_adjustment.only_elec_network=false`：解除已知只留电力的最终裁剪设置。
- `research_assembly.target_year=2050`，新状态 ASSEMBLY_V1_ACCEPTED，固定registry路径。
- `legacy_final_adjustment=forbidden`、`legacy_sector_demand_builders=forbidden`：旧最终校准还可能重写电力量，不能仅关裁剪就直接复用整个旧函数。
- `network_export_enabled=false`、`solver_allowed=false`、scenario_switching=false；目标年fallback禁止。

配置不能以“开关写成true”代替输入通过。本轮预检已实际执行：

```text
python scripts_project/check_assembly_inputs.py --year 2050 --output <review.json>
```

返回码2、状态BLOCKED_INPUT_FREEZE；没有调用Snakefile构网、任何solve rule、n.optimize/lopf或solver CLI。`composition.runnable_workflow=false` 明确保留，并解释为何阻断。没有提交名为“assemble first network”的虚假实现或空网络占位文件。用户要求的完整可运行baseline/网络导出尚未达成。

既有完整配置的2013天气、全年快照、100 clusters与3h选项仅是请求规格；未验证实际网络的snapshot数量、weight sum或空间归属。以后必须运行独立国家→节点→时间守恒，并检查objective与physical权重，不把tutorial六天50clusters网络改名当本次成果。

Policy baseline仍关闭预算；六年原DEC轨迹保留，未引入新的whole-system cap。无地质储存和不支持biomass资源的可用性fallback不会激活负Load或伪造零需求；两者真正组件效果尚未执行。
