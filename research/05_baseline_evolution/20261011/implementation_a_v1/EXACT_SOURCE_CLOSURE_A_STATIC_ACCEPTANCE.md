# 方案A三层独立静态验收

**SCHEME_A_STATIC_ACCEPTED**。证据均为本次真实源派生/文件回读或明确列前提的解析推导。没有完整LP可行性认证。

| 层次 | 结果 | 直接证据 |
|---|---|---|
| 源精确闭合 | PASS：385/385 D≤Q′，0组D=Q′；180项匹配批准模拟、627项逐位不变、5项Animal waste不变 | evidence/EXACT_SOURCE_CLOSURE_A_ALL_GROUPS_CHECK.json |
| 派生字段回读 | PASS：从磁盘重读新配方与807外置账，四字段位相等；旧Q同时对照冻结NetCDF Store | 同上；STATIC_ACCEPTANCE_RECEIPT.json |
| 科学差异白名单 | PASS：720叶字段全部在批准180Q×4范围内；无新增/删除资产和非白名单变化 | evidence/EXACT_SOURCE_CLOSURE_A_WHITELIST_DIFF.json |
| Load与权重 | PASS：1737个Load源与冻结NetCDF逐位相同，新版按原SHA引用；三套权重同源 | evidence/LOAD_WEIGHT_READBACK.json |
| 有限负例 | PASS：13/13，见具体测试文件及回执 | FOCUSED_TEST_RECEIPT.json |

## 独立性与精确公式

生成器 `scripts_project/exact_source_closure_a.py` 与验收器 `scripts_project/verify_exact_source_closure_a.py` 分开，后者不导入生成器。验收器从文件读取旧/新Q，实际分配和冻结NetCDF逐Load核对，再独立有理数积分全部385组的2920个前缀。没有使用float总和或isclose作闭合判断。

每个账户沿用已核的独占、无损、放电单向Store→meter→最终Bus结构。对每个组，令 `P(k)=Σ_{t≤k} w_t d_t`、`f_i(t)=q′_i d_t/Q′`、`e_i(k)=q′_i(1−P(k)/Q′)`。实际所有前缀均有 `0≤P(k)≤D≤Q′`，因此807个账户全部2920个前缀满足 `0≤e_i(k)≤q′_i`。导出每账户终值/最小值和每组前缀检查次数。此为条件成立的**孤立子系统解析轨迹**；不是新的求解点，也不证明其他网络约束可行。未调整任何库存义务。

## 旧证书组专项

`ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Java-Bali1 2 :: final obligation`：

- 旧D−Q = `513/34359738368` MWh >0，旧完整LP不可行性证书永久保留。
- Fuelwood Q：`0x1.f92f089e9f889p+25` → `0x1.f92f089e9f88cp+25`，提高3 ULP。
- 新Q′−D = `255/34359738368` MWh >0；旧的年度正差矛盾在新源常数中已消除。
- 尚未构建新版实际LP，所以本轮不宣称新版LP的原始行乘子/缩放边界证书已经运行。源规则修复也不证明前两次数值失败全部由此引起。

## 已查与未查

| 对象 | 状态及适用范围 |
|---|---|
| 配方全部成本、资本/边际参数、效率、拓扑、碳字段、组件数量 | UNCHANGED：全结构差异白名单比较 |
| 807账户归属、未知价格NULL、物理排放因子NULL、SourceRow/InputID | UNCHANGED：四字段之外全量比较 |
| 全部Load、时间权重、源registry及原组装源码 | UNCHANGED：文件SHA或逐值回读 |
| V3/V4/P2、历史结果、消费标记 | 未写入；本轮不读取或重算大矩阵/大向量，复用冻结身份 |
| 新LP目标向量、FOM/offset实装、新D/R缩放边界、实际完整LP可行性 | NOT_CHECKED / NOT_PROVEN：没有构建新版LP；不得外推 |
| 807账户与资源潜力真实性 | 仍为固定终端核算边界，不新增潜力证明 |

差异白名单检验会拒绝漏同步、额外ULP、Animal waste改动、新Load/资产删除、端口变化、NULL价格置零，并区分正负零double位。非预期输入变化会阻断，不扩大修复。

真实机器回执由当前验收脚本生成并记录其SHA；代码里程碑为 `fe4be3d25b7a5a7283a608c580085b26fa6b1f1e`，验收里程碑commit由后一发布记录记载，避免伪造自引用。
