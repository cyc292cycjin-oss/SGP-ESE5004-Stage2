# C07：直接原文与V4适用性

核阅时间：2026-10-13（Asia/Singapore）。这是4—6项原文的有界方法核定，未开展求解器比较或新参数研究。网页由工具打开核阅；不冒称有人类逐条完成独立文献复核。

|原文|实际支持|版本/实验边界及本轮采用范围|
|---|---|---|
|[Gurobi：How do I scale my model to improve its numerical properties?](https://support.gurobi.com/hc/en-us/articles/26284047605521-How-do-I-scale-my-model-to-improve-its-numerical-properties)，2025-12-22更新，Column/Row Scaling段|先选列单位，再使输入残差在物理意义上可忽略；内部ScaleFlag不替代建模者判断|支持按物理预算设计行尺度；不是每行误差或Barrier收敛保证。|
|[Gurobi Parameter Reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html)，BarConvTol、Crossover|Barrier停止同时涉及相对原/对偶可行性、目标差和互补性；Crossover包含push及simplex cleanup，0关闭，−1自动|当前网页为13.0文档；12.0网页未取得，故不冒称12.0手册。12.0.3实际支持和154项设置由本轮原生回读单独证明。|
|[Gurobi：Tolerances and Ill Conditioning](https://docs.gurobi.com/projects/optimizer/en/current/concepts/modeling/tolerances.html)，正文第1—5段|有限精度、病态性与求解质量；建议检查原始和对偶违约及互补性|支持独立核算，不提供本项目807账户1ppm预算，也不把任何数值Status当严格证书。|
|[PyPSA Troubleshooting](https://docs.pypsa.org/latest/user-guide/troubleshooting/)，Optimisation convergence & infeasibility|Barrier/no crossover可用于快速近似解，给出method=2、crossover=0及Seed示例|latest版本的通用建议，不是Full-SC科学验收标准。未采用页面中的裁剪、load shedding或IIS建议。|
|[Bröchin, Pickering, Tröndle & Pfenninger (2024)](https://link.springer.com/article/10.1186/s13705-024-00458-z)，Energy, Sustainability and Society 14:27，DOI10.1186/s13705-024-00458-z；“Automatically improving scaling”、实验设置及式(2)—(3)|正对角等价缩放、幂二可避免表示损失；比较Barrier及Crossover的效率与返回结构|实际Gurobi9.0.0、4线程；BarConvTol1e−6、FeasibilityTol/OptimalityTol1e−5，192GB实验节点；模型/规模与本项目不同。未报告本项目相同逐账户/逐列V4验收：NOT_REPORTED，不推定没有验证。只继承等价缩放与算法区分依据，不照搬容差或性能结论。|

上述原文没有证明本项目一定收敛，也没有赋予放宽V4的授权。

## 当前V4项目的科学分类

正式契约：`AUTHOR_SCIENTIFIC_ACCEPTANCE_V4`，SHA `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f`。日绑定SHA `8c48d0735e6dcde870fdff589915aba57b55870994e75bc04b76d39e41c38459`。

|项目|分类、原单位、依据|预算/实现核定|
|---|---|---|
|Bus、Store/SU动态、库存/容量上下界、转换、方向、KVL、线路与lv_limit|A：直接LP；MW、MWh、tCO₂、MWkm按各行物理意义分开|一般原单位行预算0.001+1e−7×reference；reference取有限界和Σ|Aij xj|最大。列参考包括当前x及有限界。绝非测量精度主张。|
|807账户年度释放与终态余量|B：在本冻结独占、无损、定需求组内为派生条件；MWh|ΣeT=ΣQ−D=Sg且eT≥0，推出单账户0≤eT≤Sg。385组全部Sg<各Bi；不能将这一特定推论推广成所有资源上限都必须耗尽。|
|每步/前缀、库存下界、累计资源上限、meter|A/B物理约束与累积等式；MWh|Bi=min(0.001+1e−7Qi,1e−6Qi)，Q=0严格零；meter差、负释放和超容量按全年绝对量核算。每日不重新获得年度预算。|
|状态L1、组gross over/under与全部前缀|C：独立累计数值认证；MWh|分别约束累计误差和相互抵消；组预算ΣBi；不扣除C01R输入表示误差。逐期门槛min(组预算,0.001+1e−7|demand×hours|)。|
|每列stationarity|C：LP KKT；各变量的EUR/原单位|ρ=|c−Aᵀy−r|/max(1,|c|+Σ|Aij yi|+|r|)≤1e−6，正是生产V4现有定义，不是另起较松指标。|
|自由RC、缺失端点乘子符号|C：LP对偶可行性|自由变量r=0；不存在下界时不许正乘子，不存在上界时不许负乘子。固定变量/等式允许任意符号，按符号选择同一有限端点。实现显式掩码避开0×Inf。|
|互补L1、加权stationarity L1、原/对偶差|C：浮点数值最优性认证|沿用含固定项max(1,|P|,|D|)归一化与1e−6；披露绝对EUR误差。不是有理数下界；未有真正可行primal/dual时不能把数值gap当严格最优值区间。|
|映射、SHA、标签、完整向量、导出回读|D：身份/实现|要求完整、可逆、有限；数学语义允许±0相等，不允许非零1ULP偏差替代精确交接。|

## 核定结论与边界

`C07_V4_APPLICABILITY.json` 独立重新积分冻结日Load和权重，使用Fraction核对385组。最大Sg为9.816722013056278e−8 MWh；最大Sg/minBi为4.673060929996528e−5。C06的23个少用账户并非这项合法源余量所致：其可观正终态不能脱离同组负库存或供需残差单独解释。C06的85个失败账户应区分62个超用/负库存与23个少用/正终态。

目前未发现需要改变正式定义或阈值才能推进的矛盾。保留V4；不生成生效V5，不改历史C03/C06失败。V4是否是所有大型模型最优门槛不在本轮可证明范围。

标准浮点误差上界：在无溢出、无渐进下溢且采用通常逐项乘加时，长度k内积可用γ_(2k)Σ|aᵢyᵢ|估计绝对舍入上界，其中γ_n=nu/(1−nu)、u=2^-53、nu<1；再计目标/RC相减误差。它是特定运算图的保守算术上界，不是条件数，也不授权忽略实测残差。生产分块bincount的实际运算顺序不能被假定为任意重排都相同；代表性列用Fraction独立核算。

C06的Line-s样本D=R=1仍有局部stationarity违规，库存R导致的物理放大不能解释所有KKT误差。`C07_AFFINE_NORMALIZATION_DIAGNOSTIC.json`逐列核定两个固定目标列：objective_constant贡献−5,617,203,873.040445 EUR；Research-existing-FOM-constant贡献8,224,491,125.573893 EUR，加offset −12,788,967.997821666 EUR，合计2,594,498,284.5356255 EUR。C06正式归一化尺度428,014,208,554.3984 EUR，剔除全部固定项后425,419,710,269.86273 EUR；绝对gap117,699.0634765625 EUR不变。此对照仅诊断固定项对尺度的影响，正式V4未变，FOM仍一次计量。

所有未来通过仅涉及扰动V3目标的数值认证；原未扰动目标严格最优性仍NOT_PROVEN，NULL费用未填零，完整系统成本资格仍由既有边界限制。
