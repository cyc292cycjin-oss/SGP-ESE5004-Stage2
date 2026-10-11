# Readable method and reproduction — exact closure design

本方法只读既有轻量JSON，不打开CSC、NetCDF、大向量，不导入PyPSA/Gurobi或调用优化器。只允许输出到独立新目录，不能覆盖正式输入。

## 输入及证据边界

- `evidence/A03_GROUP_CROSSWALK.json`：385组平坦Load、source account及已核精确δ。
- `evidence/A03_ACCOUNT_CROSSWALK.json`：807个Store/meter、Q及组归属。
- `evidence/A03_OBLIGATION_AUDIT_SUMMARY.json`：385/807静态拓扑、3h权重和无旁路检查，原摘要保持历史结论。
- `evidence/a03_full_lp/EXACT_CERTIFICATE.json`：只复用1组已完成完整LP证书；本轮不再读取其70,080项或生成新的证书。
- `evidence/closure_repair/SOURCE_BINDINGS.json`：从固定科学commit读取33个源账户、61条商品源行和8项代码/文件身份；原科学文件未改。

所有输入SHA保存在`ANALYSIS_VALIDATION.json`与`CLOSURE_REPAIR_SUMMARY.json`。先验证历史交叉表SHA及逐组δ精确匹配，再模拟，不以文件名假定身份。NetCDF与大矩阵身份引用先前已核证据，本轮不重新散列它们。

## 算术与确定性

Python标准库`Fraction`把binary64值解析为精确有理数；显示浮点不参与判断。JSON保留`numerator/denominator`形式及before/after十六进制double，结果可重算而无文本十进制往返损失。

- A：正差→最大Q→精确目标→最小不低于目标的double；验证前一double不可用。
- B：正差→Q/8760→最大不超过该值的double；验证下一double不可用。
- C：年量q0格点、1095整数倍、ties-to-even；源商品精确有理份额的Hamilton最大余数分配；用完整资产ID打破并列。
- 各方案均同时报告单组年量变更、各账户变更、绝对变化和有符号变化。`Σ|ΔQ_i|`与`Σ|Σ_iΔQ_i|`分列，避免抵消。
- 份额变化是`Q'_i/ΣQ'−Q_i/ΣQ`的绝对比例；另列与源商品目标份额差。不是百分数单位。
- 年度ULP以round64(D)为参照，Q最小ULP格点论证仅适用于不跨当前binade的小幅改动。
- 在相同独占拓扑假设下，用`p_i=q_i d/Σq`、库存递推端点和单调性检查全部前缀的局部存在性。没有产生完整模型、模拟调度优化或全局可行证书。

## 复现命令与独立检查

在解包后的`research/05_baseline_evolution/20261011`目录运行：

```text
python verification/analyze_exact_closure_options.py --output <一个尚不存在的新分析目录>
python verification/verify_closure_design.py <该目录>
```

第一条仅复制分析结果为小JSON，不写科学文件；已有输出目录会被拒绝。第二条只读输出，逐组重算Q/D/差异，并通过IEEE-754正double的整数位模式前后邻位独立检查A/B最小性。它不调用第一条的ceil/floor函数。校验器另验证A的Load不变、B的Q不变、C的全部精确等号及局部库存解析关系。

实际已完成回执：`evidence/closure_repair/INDEPENDENT_DESIGN_CHECK.json`。这不是求解或新生产矩阵交接测试。不能把设计副本中的新值当作已批准输入；方案A/B/C均为`PROPOSED_NOT_APPLIED`。

## 轻量文件阅读顺序

1. `EXACT_SOURCE_CLOSURE_REPAIR_OPTIONS.md`：比较、量化、证据等级和推荐。
2. `PROPOSED_MINIMAL_REPAIR_SPEC.md`：待批准变更规范及实施边界。
3. `evidence/closure_repair/ALL_385_GROUPS_CLOSURE_LEDGER.json`：385组、807账户来源和当前风险。
4. `OPTION_A/B/C_SIMULATION.json`：每组拟变常数、余量及份额变化。
5. `CLOSURE_REPAIR_SUMMARY.json`：全385组精确汇总和输入/方法SHA。
6. `ANALYSIS_VALIDATION.json`、`INDEPENDENT_DESIGN_CHECK.json`、`DESIGN_EVIDENCE_INDEX.json`：复核和来源完整性。

此前A03/A04报告与证书原样保留；阅读历史“不足以证明”文字时，应结合后续完整LP证书的时间顺序。本轮不改写历史报告来造成此前已经取得证书的假象。
