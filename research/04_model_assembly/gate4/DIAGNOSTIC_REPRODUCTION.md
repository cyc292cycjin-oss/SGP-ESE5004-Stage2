# 联合诊断复现与资格边界

构网实现版本：`5739aea3401f6f5715251ab6336e4f6c304c3be7`。环境仍为冻结PyPSA0.30.3；本轮验证输入组装与NetCDF，不声明求解环境已就绪。

在现有研究仓库及原冻结输入可访问时：

```sh
python scripts_project/refresh_nec_alias_inputs.py --folder research_inputs/assembly_v1 --output <source-recovery-receipt.json>
python scripts_project/allocate_assembly_inputs.py --registry research_inputs/assembly_v1/registry.json --reference <frozen-reference.nc> --ports <ports.csv> --airports <airports.csv> --output results_project/assembly_v1/allocation --reuse <previous-delivery/actual_allocation>
snakemake --snakefile workflow/research_assembly.smk --cores 1 --scheduler greedy --configfile <PRODUCTION_SOURCE_PATHS.json> -- research_build_diagnostic_network
python scripts_project/audit_residual_sources.py --repo . --output <residual-audit-directory>
python scripts_project/validate_diagnostic_preservation.py --repo . --prior <phase4_gate4_selected_20261006> --output <validation-directory>
```

前两步只有源/registry变动时才运行；本包既有数组及对应hash可复用。独立诊断规则不输出research_fullsc_2050_unsolved.nc，原完整门禁未变。配置路径见交付validation_logs/PRODUCTION_SOURCE_PATHS.json。构网不调用solver；required hooks仅挂接、资格校验，未执行优化约束。直接绕过研究入口调用第三方库不属于本验证保证。

NETWORK_STATICALLY_VALIDATED等完整状态不能由诊断成功推导。诊断meta保留缺失需求ID、逐源库存分组/ID及当前readiness hash；未知不是零。导出前对非必需字符串标签空值做NetCDF规范化，绝不将未知数值/外置null转换为零。实际账户/容量/权重和输入时序仍逐项严格比较。

KnownFixedCost未来若已经通过hook纳入PricedObjective，报告不再次相加；当前未安装模型、PricedObjective=null。471未知固定价/物理系数继续外置，六类商品资格在组合网重新验证；全成本与全排放完成状态均false。

原始资产生命周期/资源组、成本层和需求方法沿用已批准决定。新增2条LPG来源叶节点只修正既有用途映射；2项GPD水电重复关系只影响未决库存，不改变实际已接入容量。首次失败日志及最终执行结果均保留。代码换行的执行字节/Git blob差异另行记hash，原始研究输入保持精确字节。
