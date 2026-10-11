# 静态复核方法

1. 所有科学输入SHA、批准文档的Git blob、父代码及新派生文件见版本Manifest。批准文档绑定父审计提交53c2b28632cb577136d48ebb843823967f0b1c25；不能把后续更新的台账当作原批准输入。
2. 源生成从旧unbound recipe和实际allocations.npz开始，只在内存副本中计算180项最小向上binary64。使用Fraction精确积分/比较；最多一次nextafter，无epsilon、isclose或求解循环。
3. 如要独立复现生成器，请在源版本里程碑fe4be3d25b7a5a7283a608c580085b26fa6b1f1e的文件视图中读取批准输入，输出到另一空目录。生成器故意拒绝覆盖；交付目录无需再次运行。后续台账更新后，不能以当前台账替换父提交批准文件。
4. 已执行命令（路径前缀为仓库根）：

```text
python -B scripts_project/exact_source_closure_a.py --repo . --frozen-source /mnt/d/ResearchWorkspaces/ASEAN/outputs/phase4_gate4_final_closure_20261006 --out research_inputs/derived/exact_source_closure_a_max_account_v1_20261011
python -B scripts_project/verify_exact_source_closure_a.py --repo . --frozen-source /mnt/d/ResearchWorkspaces/ASEAN/outputs/phase4_gate4_final_closure_20261006 --version research_inputs/derived/exact_source_closure_a_max_account_v1_20261011 --evidence research/05_baseline_evolution/20261011/implementation_a_v1/evidence
python -B scripts_project/test_exact_source_closure_a.py
```

5. 原始外部输入通过现有SHA引用，ZIP不复制NetCDF或allocations.npz。独立复核需要有这些授权原件；仅ZIP可以复核180项hex/Fraction及四字段白名单，但不能冒称已重新验证未携带的源文件。
6. 内存方式：NPZ按InputID块读取、NetCDF按Load列读取，约100MiB本地RSS；无CSC读取、PyPSA实例化、LP构建、优化或AutoDL操作。报告中资源数字为观察值，不声称严格全程峰值。
7. 385组有理数D/Q/份额/终期余量、807账户及720个具体字段差异均见JSON。全部前缀积分并与Q′比较；账户前缀由明确解析式得到，不把它称为完整LP解。
8. 开发检查失败记录保留；13项有限负例针对新实现，没有重复旧实验或已有全量矩阵审计。未来完整LP装配及界传递检查需要另行授权，不能从本静态验收启动求解。
