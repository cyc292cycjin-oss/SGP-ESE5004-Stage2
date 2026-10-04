# Malaysia E3 研究侧原型

**PARTIAL_SOURCE_ACCOUNTING_ONLY。** 两个真实水热电力投入已恢复，完整全国E3年会计未闭合；不能标ANNUAL_CLOSURE_ONLY，更不能称小时闭合。所有数值仍为UNVERIFIED/PENDING。

## 原始输入和有限计算

| 变量 | 2016半岛来源候选 | 能做什么 |
|---|---|---|
| T_R | Table42电力2333ktoe，按本版定义为27114.644444GWh | 同表用途加总检查 |
| h_R,water | 70ktoe =813.555556GWh终端电 | 只代表h_R的water部分 |
| T_R−h_R,water | 2263ktoe =26301.088889GWh | `R_without_water`，不能命名为完整B，因为space仍未知 |
| T_S | Table47商业39106GWh | 待Services映射，且原用途子项有0.43GWh差异 |
| h_S,water | 1034.62GWh终端电 | 只代表h_S的water部分 |
| T_S−h_S,water | 38071.38GWh | `S_without_water`，不是获批完整C |
| h_R,space / h_S,space | UNKNOWN | 空白不等于0 |
| A*_MY / O_MY | 尚未共同接受 | 不从异年、异地区或不一致总量倒造O |

在同一父账户内 `(2333−70)+70=2333` 和 `(39106−1034.62)+1034.62=39106`可直接验证。它们只证明**部分water转移的代数恒等式**，不是统计上完整的E3通过，也没有修复S来源子项不一致。

保留的完整结构仍是 `A*=O+T_R+T_S`，`B=T_R−h_R`，`C=T_S−h_S`，`D=O+B+C=A*−h_R−h_S`。本轮A*、O和完整h保持符号态，未创建residual correction。全国2019的Table17、Table29与UNSD是三组分别保存的候选，不能拼接制造闭合。

## Useful heat

已接受的方法：`Q = FinalEnergy × EndUseShare × Σ_j(DeviceInputShare_j × HistoricalEfficiency_or_COP_j)`。若输入已经是water电量，EndUseShare=1；不能再乘70/2333或1034.62/39106。

因此R水热候选公式系数为813555.555556MWh电，S为1034620MWh电；**设备输入份额、历史效率/COP和最终useful值都留空**。对非电热用途也没有擅造份额。water的数值输入已具备，完整useful heat数值尚未具备；space连可量化投入也未具备。

官方GP/ST/No.6/2016（2017发布）可证明即热、储热、太阳能水热器的范围和安全安装定义；不能提供2016/2019R/S按输入电量加权的设备效率。Energy Malaysia Volume9 PDF29–31/印刷27–29的41/338为进口/本地新续CoA数量，不是存量，更不是电量份额。NEB notes明确不报告设备输出侧useful energy。没有自动设eta=1、COP或DEA未来值。本轮不提出没有可校准边界的数值工程替代。

## 空间与时间方案（PROPOSED TEST）

住宅可比较人口、城乡人口分层、住房/建筑面积与热水设备证据；服务业应比较各类服务活动、商业楼面、住宿床位等用途相关权重，以及服务GDP。不同权重须先统一到被接受地域并说明分母。人口/GDP本身不能验证热水强度；不默认R=S=人口分配。

只有全国年度会计先通过，才进入以下小时可行性检查：分别以来源支持的形状和物理snapshot权重积分恢复年度T/h，检查每个节点/时刻 `A*_t−h_R,t−h_S,t≥0`，并保存最小值与失败位置。归一化仅允许作为具有同域年度总量和形状证据的明确单位步骤；不通过clip/smooth/cap或任意缩放掩盖负残差。本轮没有满足年度先决条件，也未生成小时序列或分配到真实模型节点。

## 验证范围

`MALAYSIA_E3_CLOSURE_TEST.csv`记录17项来源算术、差异、边界及可行性门槛。通过项是源码/原表核对或同表部分转移；blocked项真实保留。prototype脚本仅写研究目录JSON，CSV由artifact-tool导出。没有输入覆盖、正式E3 patch、求解或新技术。
