# 本轮复现规则与运行manifest

1. 固定完整模型SHA，paper/upstream/research严格分层；修复与研究变化分开commit。不要force-push，不要覆盖原教程/作者输出。
2. 正式配置由base + project override合并，保留最终有效配置、修改来源、文件hash；数据下载刷新要关闭或严格固定文件身份。仅改配置的路径不证明物理边界不变。
3. 正式run在清洁模型工作区启动，结果输出到独立run目录。登记所有实际输入（含component overrides）、config、环境锁/完整freeze、solver/version、时间/权重、场景/规划年、输出hash。
4. run_manifest.py已实现并用合成命令验证：成功、命令失败、旧输出拒绝、dirty checkout拒绝。它不自动选择实验、不批准数据、不把命令exit0当成optimal。见RUN_MANIFEST_TEMPLATE.json和RUN_MANIFEST_TESTS.json。
5. solver adapter必须输出JSON字段`objective`、`solver_status`、`constraint_residual`。residual定义为同一约束单位下最大绝对违反值（等式abs(lhs-rhs)，<=为max(lhs-rhs,0)，>=反向）；应另报类别/尺度与采用容差。工具记录有限测量值，但**不代定科学容差**；COMPLETED表示执行与记录完整，不等于实验验收。
6. 声明的input清单完整性仍需workflow审查；工具可检测清单内输入被改写，无法证明调用程序没有读未声明文件。正式运行前需从完整DAG生成输入清单并核对。
7. 守恒/约束/目标差异比逐文件hash更适合验证重新生成的NetCDF语义；压缩或时间戳差异可导致相同物理内容但不同hash，需同时保留两类证据。

## 重新执行本次工程核验

在已固定的官方源码上，分别应用patches中的两个git format-patch（独立分支，不混成一个提交）；使用既有pypsa-earth环境运行各分支tests/test_*.py。真实数据复算由validate_industrial_recovery.py执行，需要原始GDP、基年表、地区/设施/人口文件，路径可通过ASEAN_PHASE2_ROOT、ASEAN_TUTORIAL_ROOT配置。该脚本仅对48节点已有几何做诊断，不启动求解。

engineering_review.py是首次在干净官方worktree创建补丁及before/after证据的一次性脚本，带HEAD/dirty保护；不要在已修复分支再次运行。保存的tests可反复运行。prepare_model_layers.py和commit_fixes.py保留首次建层/提交痕迹；已经存在的交付分支优先复用，不重新造重复分支。

数据台账的确定性提取在prepare_registry.py，CSV由export_registry.mjs通过artifact-tool生成；大GDP派生文件留在fix工作区，节点量/误差在便携JSON/CSV。报告由write_reports.py从证据生成。所有再生工作都应先核对输入hash，发现漂移停止对应步骤。
