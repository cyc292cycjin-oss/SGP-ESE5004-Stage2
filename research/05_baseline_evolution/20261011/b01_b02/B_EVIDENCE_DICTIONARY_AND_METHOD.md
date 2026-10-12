# B-01/B-02证据字典与复核方法

只读本地证据。没有连接AutoDL、导入PyPSA Network、加载CSC、读取X/Pi/RC或调用任何求解器。所有新文件只在b01_b02审计目录和本地work/output交付目录；科学源码及源数据未写入。

| 文件 | 内容 / 使用限制 |
|---|---|
| B01_B02_IDENTITY_AND_READ_SCOPE.json | 固定Git对象、Scheme A三SHA、复用文件SHA、NetCDF身份、默认值文件SHA、实际输入读取字段和大小。 |
| B01_SCHEME_A_SOURCE_BRIDGE.json | 385精确D/Q′/差、807资产新旧Q十六进制、180修改名单、四字段同步及既有静态回执。是源配方桥接，不是新网络。 |
| B01_RESOURCE_TOPOLOGY.json | 807个旧实际Store、唯一meter、最终Bus及方向/容量/库存界；同时单列新源Q′，不覆盖旧值。 |
| B01_LOAD_SUPPLY_PATHS.json | 1737条实际Load→Bus→源/转换资产ID，时序哈希、年度/峰值标量、分类。没有原始大时序或解向量。 |
| B01_CAPACITY_AND_PROFILE_CHECK.json | 5470条Link/Line/Generator/Store/StorageUnit名义界记录、460供给profile与40入流profile标量；安全白名单物理hook元数据。 |
| B_SHARED_CAPACITY_AND_STORAGE_NECESSARY_CHECKS.json | lv最低量精确Fraction、20电弱连通分量、43储能初值；existing_resource_groups当前为空，不把通用源码能力当实际行。 |
| B02_MULTIPORT_AND_CARBON_BALANCE.json | 300个CO₂/H₂/oil Bus全部非零入射Link、实际符号/效率/国家、挂载资产；100组捕集守恒精确比值；大气报告入射端口。 |
| B02_LOCAL_OIL_SINK_LIMITS.json | 100个油Bus有限消纳所导出的FT/CC必要上界，及4全零/6超1ULP的实际profile资产。 |
| B_FROZEN_SOURCE_FORMULAS.json | b9be科学源码和实际PyPSA0.30.3公式文件SHA及行号摘录，未执行这些建模函数。 |
| B_RESULTS_DIGEST.json | 从新JSON生成的家庭数目/上界/余量汇总，不能替代原件。 |
| B_INDEPENDENT_CHECK_RECEIPT.json | 独立Fraction求和、局部符号构造与CO₂消元，共15检查；无全LP证书。 |
| B_EVIDENCE_INDEX.json | 最终本轮文件SHA/大小；打包清单另含Git提交、ZIP成员CRC，不形成递归自哈希。 |

JSON中`Infinity`表示真实无有限上界；`null`表示缺失/未定，不自动视为零。端口系数按Link-p正向：输入负、输出正；不得以bus1/bus2位置或名字猜测输入输出。金额与能源单位不混合。

## 实际读取与内存

复用A03/A04/A05/A06及Scheme A已验收证据；本轮只新核必要的端口/界、Load峰值和供给profile。本地最初逐列压缩NetCDF读取效率不足，已核对该审计进程身份后结束，改为一次约40.6MB连续Load输入表、约10.75MB供给profile及约0.93MB入流表，释放后只保存标量/哈希。没有模型实验重跑。该读取方法调整记录保留在Windows work目录。未全量扫描9078万LP项、未构建稠密LP。

## 可复核顺序

方法文件在verification/：

1. `audit_b01_b02.py`：读取固定PR #4 Git对象和已存在NetCDF；重求源级精确Q、端口及容量/时序摘要。需本机已有原文件，脚本不获取新数据、不启动模型。
2. `supplement_b.py`：只读小型元数据和固定源码，求最低输电volume、储能初值。
3. `verify_b.py`：**仅消费上述JSON**，独立Fraction验证年度闭合和局部CO₂平衡。复核审阅包可优先检查此方法，无须源大文件。
4. `derive_local_oil_limits.py`、`summarize_results.py`：只消费新JSON，推导油消纳上界/摘要。

路径常量绑定当前D工作区和WSL研究仓库。重现时如复制到其他机器，只能显式改读取根路径，不能改身份/SHA/科学值；没有必要为本轮已通过检查自动再跑。

验证阈值不是V4替代物：源与消元用精确Fraction；Load/供给统计为binary64，未宣称年度报告求和是严格证书。条件性资源分配仅为公式，不持久生成新的2920调度解。

## 限定缺失证据

Scheme A完整网络、实际新LP及联合可行性证书尚不存在；这一点不是要求本轮构模的理由。未证明共享电网/KVL、所有其他跨期约束、数值精度或优化经济结论。历史旧LP证书仍成立，但不得归属新配方。仅这些明确边界留给下一次科学决策，不自动扩大审查。
