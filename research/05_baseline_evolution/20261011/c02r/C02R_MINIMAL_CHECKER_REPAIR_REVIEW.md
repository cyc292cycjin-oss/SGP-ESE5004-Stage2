# C-02R最小语义检查器修复

状态：**C02R_CHECKER_PATCH_READY_FOR_REVIEW**。34项本地小型单元/接线检查通过；**没有新build-only运行授权、云端连接、网络/LP重建或求解**。原C02仍为C02_BLOCKED_WITH_SPECIFIC_EVIDENCE。另有一处确定的零行覆盖断言阻断，未越界修复，见第5节。

## 1. 固定父版本和候选身份

- 父提交 `2b3442826ddc2364f63e3bd44a4eab6aa94fc263`，继续独立分支 `codex/c02-controlled-daily-build-20261012`、PR #12，不改main、不合并。
- 原失败 `c02_model.py` SHA `676edc30c5860c4a6b52fe63a117d1a395e9230db0d58db3e6ff9bb5ba4934a1`；原运行 `c02_daily_build_20261012T025604Z_fcc0f784`、消费标记和部分产物不变。原文件未被替换；本轮候选位于 `c02r/candidate/`。
- 候选模型检查代码 SHA `fa8c3905dfc6bfd36b57cf7ceed8592b63dba7943d8d0c2babdee32f507e0f76`。
- 新语义检查模块 SHA `c05266882fa9f7122ceda9442be9c4d7a1b36ee02a4edea700c9c71cf508e891`。
- Scheme A、C01R协议/规则、V4固定Git对象SHA再次核实；不修改Q、Load、PyPSA、V3/V4/P2、成本或约束。源网络未读写，本轮只复用已核NetCDF身份回执。

## 2. 精确语义和位身份分离

有限binary64数学值采用**零容差精确相等**，没有isclose、epsilon、舍入、截断或nextafter修正源值。只有+0.0与−0.0被视作同一个数学零；任何非零1 ULP变化均失败。

| 检查位置 | 候选处理 | 严格拒绝项 |
|---|---|---|
| Store-energy_balance全部365个RHS | rhs_exact，预期方向= | NaN/Inf、非binary64、shape变化、非零差、错误方向 |
| Store-fix-e-lower/upper | rhs_exact，分别≥/≤ | 同上，包含原库存零下界 |
| 两类最终Bus RHS | rhs_exact，方向=，完整Bus ID | 同上；Load源数组本身不改变 |
| 导出后对应Store/Bus行上下界 | bounds_exact，精确端点和开口侧匹配 | 上下界颠倒、活跃端点变NaN/Inf、开口方向/符号错误、有限非零差 |
| 输入、权重、Scheme A、目标、缩放恢复、数组/标签保存回读 | **原bits与SHA保留** | 原位身份规则不放宽 |

行界表示中的 `−Inf` 下开口、`+Inf` 上开口是已有规范化哨兵，原检查也允许正确匹配；候选仅允许与明确预期的同侧同号哨兵完全一致。**不是允许Inf RHS或将有限边界放成无界**。两侧全开口的无效行及非法预期边界同样拒绝。其有限端点仍零容差检查。

原 `bits()` AST逐字逻辑不变，11个保留调用逐项列在 `C02R_PATCH_SCOPE_AND_IDENTITIES.json`。既有函数中仅export_model的四处语义调用及诊断路径变更；assemble_daily、add_hooks、objectives、canonical_rows、全部聚合/成本/缩放规则均AST不变。新模块不改变任何被检查数组。

## 3. 失败详情与保全

未来新运行发生语义失败时，写独立 `C02R_SEMANTIC_FAILURE.json`：完整asset_id、constraint_family、所有提供的行标签、数组shape/dtype、实际/预期hex、实际/预期方向及错误分类。非有限值以hex字符串`nan/inf/-inf`记录，JSON本身不含非法NaN数值。

文件以exclusive-create写入，flush/fsync，不覆盖任何已有失败回执。若磁盘/权限导致写出失败，证据仍附在SemanticCheckError中供既有worker异常日志保存；不能保证磁盘完全不可写时新增文件持久化。原supervisor/guard、窗口和消费标记均未改。

## 4. 本地验证与证据边界

`C02R_LOCAL_UNIT_TESTS.json`：**34项通过**。

- ±0通过；1+2^-52与1的精确Fraction差证实为1 ULP且拒绝；最小正subnormal不能当零。
- 实际侧和预期侧NaN/±Inf RHS全部拒绝；float32、shape/方向shape、方向变化拒绝。
- 有限界被Inf替代、无界侧符号错误、上下界交换及非零1 ULP界差拒绝；正确规范化开口侧通过。
- 用xarray属性替身直接执行候选Store与最终Bus检查循环，验证±0通过、非零差和错误Store下界方向拒绝；没有创建Linopy或PyPSA对象。
- 原bits仍拒绝±0位差；失败JSON的完整ID、行标签及hex已检查，已有文件未覆盖。
- 测试中nextafter仅构造反例，不修改科学输入。没有导入PyPSA、Linopy、Gurobi或其他solver，无模型/求解调用。

合成失败示例明确位于 `evidence/synthetic_failure_examples/`。不能将它们认作新生产失败，或称实际日LP/V4已经验收通过。

## 5. 新窗口之前必须知道的另一处阻断

**直接代码与既有证据支持**：父代码第247行要求 `counts[fam]>0`。第一次C02的持久化标签及边界审计已证明下列家族有效行数为0：

- Line-ext-s_nom-upper：105个扩建资产上界均+Inf；
- Link-ext-p_nom-upper：3263个扩建资产上界均+Inf；
- Store-ext-e_nom-upper：297个扩建资产上界均+Inf。

若前面导出步骤完成，这个无条件正行数断言将继续拒绝已知合法的零行家族。它是**覆盖判定逻辑**，不是±0的值比较，因此本轮没有静默放行或修改。原已证明的零行原因与代码位置见 `C02R_ZERO_ROW_COVERAGE_HOLD.json`。仅建议后续明确批准：对这三类已绑定+Inf上界和实际标签掩码的零行作严格例外；任何本应有限或未知缺失家族仍停止。不需要改模型方程或新增/删除资产。

当前不应仅因±0测试通过就启动新完整构建；需先处置这一有直接证据的阻断并取得新C02R窗口授权。这不是新的科学模型审查，也没有参数试验。

## 6. 未来获授权时的衔接（未执行）

优先复用已封存 `daily_365_unsolved.nc`，SHA `b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2`；本地和云端准确路径见机器清单。新入口须检查该SHA及Scheme A/C01R已通过网络身份，避免重新聚合和重新派生Q。

重新取得实际Linopy模型后，继续完整矩阵/行界、原科学与V3日目标、offset、D/R及DAILY_V4_BINDING检查；旧部分数组不能冒充完整LP。本轮没有准备可自动消费新授权的launcher，也没有把候选植入原payload；原payload SHA白名单仍将拒绝直接替换候选。

新Run/独立claim/完整资源保护/唯一1800秒build-only窗口必须在新的明确授权后建立，不能复用旧窗口、清除旧标记或延长旧截止。G6-05保持PAUSED_BY_USER，C03与任何优化均未获授权。

## 7. 交付

候选补丁、scope/SHA清单、34项测试、合成失败格式、原失败关键证据、台账与强制审阅ZIP同轮提交PR #12。真实commit/远端状态与ZIP清单、SHA/CRC由最终发布回执记录。ZIP不含NetCDF、大矩阵/标签数组、原始解、密钥或许可证。完成后停止，等待用户与ChatGPT复核。
