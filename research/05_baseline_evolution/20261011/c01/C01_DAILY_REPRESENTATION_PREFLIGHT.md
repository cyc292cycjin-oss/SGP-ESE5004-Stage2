# C-01：365日输入聚合的精确表示预检

2026-10-12。结论：**C01_REPRESENTATION_DECISION_REQUIRED**。

输入身份、全部实际动态属性和Scheme A年度关系通过。1737条Load中95条在精确日均转为最近binary64后产生非零年度有理数差，因此**当前C-00聚合不能直接放行日模型构建**。误差很小，但没有改写“严格相等”标准。本轮只读模拟，没有构建新PyPSA网络/LP，没有求解或操作AutoDL，G6-05仍PAUSED_BY_USER。

## 1. 冻结身份与读取范围

| 对象 | 实际身份 |
|---|---|
| C-00提交 / PR #8 | `5d757c5a4a9dad965d9c7cbe6e55d486d167ff93` |
| C-00审阅ZIP | SHA `4aee43d3cb4a0cc908848a965c9ba0f50fec9be3159461cea27ea20df7244796`，成员SHA及CRC复核通过 |
| Scheme A / PR #4 | `8883de6fb3e15767c632ac92f535e8a423e90b69`；Manifest SHA `a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720` |
| 冻结科学源码 | `b9be7d0ab788a4151346c098d2e657c7e94a22da`，所引科学源文件与Scheme A Manifest绑定逐项核对 |
| 冻结NetCDF | `research_fullsc_2050_assembly_v1_unsolved.nc`，72,082,285字节；SHA `238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d` |
| 原allocation NPZ | SHA `931c24aac84be29eda6b2a1906a8e85ca0f3876b90c26cdb3b40e84ad8d3b2b9` |
| allocation manifest | SHA `4e2cc08c6671635ccd1cc472ccabf06bad630650cd948678c042205607703d06` |

源位置：`D:\ResearchWorkspaces\ASEAN\outputs\phase4_gate4_final_closure_20261006\complete_network\`及同父目录`actual_allocation\`。Scheme A从固定Git对象读取，不从当前分支猜Q，也没有合并PR #4。完整路径、文件/代码SHA见[C01_SOURCE_IDENTITY_AND_SCOPE.json](evidence/C01_SOURCE_IDENTITY_AND_SCOPE.json)。旧NetCDF仍含旧Q；本轮只取它的**未改动时序**，另从Scheme A原件取新Q。未将其冒称Scheme A新网络。

流式核文件SHA后，以NetCDF只读模式分属性读取，最大单表40,576,320字节；没有PyPSA导入、CSC或X/Pi/RC读取。主核算约17.11秒，进程峰RSS约196.88MiB。源文件大小/mtime前后未变；无原件写操作。日均数组仅在内存中用于binary64打包/回读和SHA，**没有输出可用于组装的派生时序文件**。

## 2. 全部动态属性及源输入

| 组件.属性 | 资产×原时段 | 原数据规范字节SHA256 |
|---|---:|---|
| Load.p_set | 1737×2920 | `251ddd1fa9acda348fe36b197242a010328d793576f8eb09de59240957779416` |
| Generator.p_max_pu | 460×2920 | `9f59f79166db52bcd2449e9fa08a86123d6ac987b5982c734c5c07d9be2f7925` |
| StorageUnit.inflow | 40×2920 | `68de7aaa23bc0a90af00014379e2df3082a43276ee3a1772ebcbbe3bd18951f0` |

上述是逐一枚举NetCDF中所有含snapshots维度、排除坐标/权重的非空变量，数据SHA采用little-endian float64、C-order；每列资产的SHA与顺序标签SHA另存。**未发现额外时变成本、效率、运行义务、e_set或边界表，BLOCKED_PROTOCOL_EXTENSION=false。** 没有把不存在的动态表与静态默认属性混淆。

原日历从2013-01-01 00:00至2013-12-31 21:00，2920个唯一连续3h点、365完整日桶、每桶8点；无缺日/重复时段，三权重列全部为3、精确和8760。仍是2050情景采用2013形状。相关NPZ有171个需求数组、weights和snapshots共173项，全部列1898，其中1737映射实际Load且逐列SHA匹配。其余161列为Scheme A已登记的原有全零分配列，无实际Load；本轮独立核对全零，不是新删负荷。

原NetCDF三表和NPZ需求数组均无实际NULL/NaN/Inf、负值；所有实际Load均严格正。NetCDF `_FillValue=NaN`只是格式元数据，不代表缺失观测。详见[C01_DYNAMIC_ATTRIBUTE_INVENTORY.json](evidence/C01_DYNAMIC_ATTRIBUTE_INVENTORY.json)及[C01_SOURCE_ARRAY_COMPLETENESS.json](evidence/C01_SOURCE_ARRAY_COMPLETENESS.json)。

## 3. 精确算法与独立交叉验证

每桶计算 `m_d=Σ_{t∈d} Fraction(float(P_t))×3/24`，再用最近值、ties-to-even转为binary64，并通过字节pack/unpack模拟序列化。相同8值桶只复用同一个有理数结果，所有日桶归属仍逐一检查。没有用NumPy mean、isclose、nextafter修正、末日补差或Q重新派生。

原年度和以独立的共同二进制分母整数累加计算；同时断言 `E_original=24Σm_d`。模拟年度为 `E_daily=24ΣFraction(serialized(m_d))`。逐日检查最近值距离与偶数中点，逐资产记录误差、位图、ULP及年度差；这是精确有理数关系，不是浮点近似比较。

独立复核器不再读原时序：对2237条资产保存的代表桶用**整数有效位舍入**重算最近值；复核全部年度Fraction差、分类、累计半ULP界及385组关系。16类检查通过，见[C01_INDEPENDENT_CHECK_RECEIPT.json](evidence/C01_INDEPENDENT_CHECK_RECEIPT.json)。这些不是新LP或求解器验收。

## 4. Load结果：95条实际年度漂移

| 类别 | 数量 |
|---|---:|
| 实际Load总数 |1737|
| 原序列逐位恒定 |1641|
| 时变电Load |96|
| EXACT_ANNUAL_PRESERVED |1642|
| 年度正漂移 |52|
| 年度负漂移 |43|
| 无法单个binary64精确表示的日均 |31542 / 634005|

1641条平坦Load全部精确守恒。唯一年度恰好守恒的时变Load为`LA:2050:Electricity:Astar:electricity@LA2 5`；它仍有326个日均发生舍入，只是年度有理数差恰好抵消。不能把它称为逐日精确表示。

95条漂移全部为A*电Load。全年有符号差合计 `293007/281474976710656 ≈ 1.0409699768842984e-9 MWh`；逐Load绝对差之和 `1442325/281474976710656 ≈ 5.1241677567759325e-9 MWh`。不能用跨节点正负抵消放行。

最大绝对差位于`ID:2050:Electricity:Astar:electricity@ID_Java-Bali1 0`，Bus `ID_Java-Bali1 0`：

- `E_original=33440698944305344863/137438953472 MWh`；
- `E_daily=522510921004771011/2147483648 MWh`；
- `E_daily−E_original=−159/137438953472 ≈ −1.1568772606551647e-9 MWh`。

两者转换成常用浮点显示均为243313108.10743412 MWh，却并不严格相等。此差为原年度binary64 ULP的−159/4096（约−0.03881836）倍。最大相对年度差在`TH:2050:Electricity:Astar:electricity@TH2 0`，为`187/34974792847380916853 ≈ 5.346707865176204e-18`。

各Load的节点/国家、原/新精确年量、每日非表示位图、最大误差及半ULP、年度ULP尺度、原值SHA和模拟日数组SHA全部保存在[C01_LOAD_ANNUAL_EXACT_CHECK.json](evidence/C01_LOAD_ANNUAL_EXACT_CHECK.json)。未保存整份原始或新日时序。

### 为什么不能默认“最后一天加一两个ULP”

保持各日值原binade（相同二进制数量级区间）时，所有binary64改变量都必须是该日spacing的整数倍。这些spacing为2的幂，因此总功率改变量必须是最小spacing `u_min` 的整数倍。目标修正必须满足 `(E_original−E_daily)/(24 u_min)`为整数，这是必要条件而非充分条件。

95条漂移中86条不满足此条件。上述最大差组要求53/4=13.25个最小日ULP，故任何保持日值binade的普通ULP调整都不能精确闭合；其余9条仅通过该必要条件，**没有证明存在合法最小修正，也没有实施调整**。改变binade可能大幅改变日形状，不能当作无科学影响的舍入修复。

## 5. CF和水电入流表示预算

定义逐日半ULP界 `b_d=ulp(serialized(m_d))/2`，逐资产年界 `B=24Σb_d`。原年量、日年量、实际差和B均为精确有理数，满足`|ΔE|≤B`。该界只解释序列化，不追加给物理/V4容差。

| 项目 | CF（460资产） | 水电inflow（40资产） |
|---|---:|---:|
| 精确年量保持 |4（均全零曲线）|0|
| 正/负年度漂移 |232 / 224|20 / 20|
| 不可精确表示日均 |137328 / 167900|13264 / 14600|
| 最大绝对年度差 |1.990074771640593e-14等效满负荷小时|1.2014389483283594e-10 MWh|
| 最大相对年度差 |1.108510589192983e-17|1.0678731057640608e-17|
| 半ULP累计预算 |460/460通过|40/40通过|

CF年量用等效满负荷小时（即每1MW容量的MWh潜力）表述；容量决策未变，不能把它写成实际发电量。最大CF年差资产为`existing_survivor::LA2 4::Hydro::0d66b994afb2`；最大入流年差为`existing_survivor::VN2 4::Hydro::496c66207529`。精确分数、每资产数据及单位见[C01_CF_INFLOW_ROUNDING_CHECK.json](evidence/C01_CF_INFLOW_ROUNDING_CHECK.json)。

所有CF非负；6条offwind-dc曲线共44个原值为`1.0000000000000002=1+2^-52`，已知源范围风险原样保留；最近日均无>1值是实际聚合结果，**不是裁剪**。曲线为ID_Java-Bali1 1（1个）、ID_Kalimantan4 12（8个）、ID_Nusa-Tenggara14 0（1个）、VN2 3（8个）、VN2 4（18个）、VN2 5（8个）。全部入流非负，没有增补、截断或替换源数据。

## 6. Scheme A 385/807年度闭合

固定生物质Load均为平坦序列，365×24=2920×3使年度值逐组精确不变。直接读取已批准807个Q′，验证与Store.e_nom、e_initial、route cap及外置账一致，没有新积分再派生Q。

385/385保持精确年度D、385/385满足D≤ΣQ′；没有组成为新D>Q′，也没有把不等式写成等式。最小余量`105/576460752303423488 MWh≈1.82146e-16`，最大`3373/34359738368 MWh≈9.81672e-8`。180项修订值和其他627账户均未改。**生物质源常数无需新的表示决定；当前阻断来自95条电Load日均的严格年量要求。** 这仍不是新LP可行性证明。

## 7. 仅提出一个确定性候选：非负双字常数表示

状态：**PROPOSED_NOT_APPLIED**。不提出放宽年度相等、不把Kahan求和当LP修复，也不提供未经证明的末日补差。候选规则见[C01_PROPOSED_REPRESENTATION_RULE.json](evidence/C01_PROPOSED_REPRESENTATION_RULE.json)。

对真实日均精确二进制有理数`m=N/2^k≥0`，约分后令p为N的位长：p≤53时直接存m；否则q=p−53，定义

`H=floor(N/2^q)×2^(q−k)`，`L=(N mod 2^q)×2^-k`。

这是确定性整数除法：H、L均非负，且**H+L=m严格成立**。本次96条时变电Load日均最多57个有效位，因此L最多4个有效位。其原功率范围24.829192545449292—37475.48025016492 MW，源binary64指数≥4，均值量子不小于2^-51；H/L无上溢或下溢，两项均可精确binary64表示。没有改变日均科学值、原时段来源、年度需求、商品Q或时间权重。

影响范围：96条时变电Load、35040个日电Load格，其中31542个不可单字精确表示格需低位项（包含那条年度偶然守恒Load的326格）；1641条平坦Load及所有807 Q不变。至多新增31542个**固定数值辅助项**，不是新增物理Load、资源或自由供应；本轮没有创建它们。

数学上，令S为原Bus所有实际供应/流量的净和，可用`v=L`的固定上下界和`S−v=H`表达。消去v得到`S=H+L=m`，再按24小时累加得`24Σm=3ΣP_t`；投影后的精确日需求与科学年度量不变。目标对纯固定表示变量不加研究成本，原目标及FOM口径仍需独立身份校验。

**实现边界不可省略**：简单新增两个同Bus PyPSA Load并不保证有效，现有float64 groupby可能把H+L重新舍入为单字RHS。未来必须让两个常数在CSC/原生交接中保持分离，并让NetCDF/旁车元数据、原单位验收和V4维度绑定识别其精确和；不能只导出H并宣称它就是全部需求。辅助项必须固定为非负消费，不得成为负Load、可调松弛或免费供给。

该方法需要用户批准新的**数值常数表达规则及对应身份/验收适配**，不在C01实施。它只证明精确数学常数可表示，不保证原生presolve保留细小低位、实际求解精度、整体可行性或V4 PASS。若不接受新增数值表示，则保持NO-GO，不自动换成近似年量标准。

## 8. 决策及交付

输入身份无阻碍、动态属性无协议扩展缺口；CF/入流满足既定表示预算、Scheme A固定生物质保持精确闭合。95条Load的非零年量差触发C-00已批准检查线，故最终为**C01_REPRESENTATION_DECISION_REQUIRED**，不能直接进入日模型构建或求解。

建议联合审阅上述唯一候选的数学表示及工程影响后再决定是否批准实施。这里没有优化授权、网络/LP构建、源数据修改、Q修订、AutoDL控制或G6-05恢复。旧C-00及Scheme A原件、V3/V4/P2、历史结果与消费标记保留。任务在GitHub与ZIP交付后停止。
