# 方案A受控源常数实施报告

结论：**SCHEME_A_STATIC_ACCEPTED**。用户与ChatGPT已批准 `EXACT_SOURCE_CLOSURE_A_MAX_ACCOUNT_V1`，本轮只实施这份180项清单并静态验收。

## 新版本与历史保护

独立实施分支：`fix/stage2-exact-source-closure-a-v1`。源版本里程碑 `fe4be3d25b7a5a7283a608c580085b26fa6b1f1e` 已推送。父审计提交 `53c2b28632cb577136d48ebb843823967f0b1c25`，冻结科学代码 `b9be7d0ab788a4151346c098d2e657c7e94a22da`；关联审计PR #3及旧 `A03_EXACT_ANNUAL_CLOSURE_PROOF.md`。

新Version ID：`EXACT_SOURCE_CLOSURE_A_MAX_ACCOUNT_V1_20261011`。
实际源目录：`research_inputs/derived/exact_source_closure_a_max_account_v1_20261011/`。
Version Manifest SHA256：`a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720`。

已从冻结 **UNBOUND_CARRIER_RECIPE** 派生新配方和新807账户导出账，不是对LP边界打补丁。完整旧配方、源分配、NetCDF、CSC、旧Q/Load、旧证书、P2/V3/V4、前两次结果和消费标记均未写入。原生成代码未改；新代码为显式选择的源派生器，旧默认入口不会自动采用此版本。

| 新文件 | SHA256 |
|---|---|
| carrier_fragment.json | 1b0ea897bc17d652a6ac5047935dc6af6c53536a51b197582b3567313d155e8e |
| external_pending_fixed_accounts.json | 20d9d0dc2028f1ca4e07b8e4e02fe51fce3a4a357c0d86366076a528b9a2a8e0 |
| EXACT_SOURCE_CLOSURE_A_CHANGESET.json | cb001d73a4214f1be03ce4235d41f11338778f289cf23b8f4352f8651449ae32 |
| LOADS_AND_WEIGHTS_REFERENCE.json | a5abcbfdd03a66d5b8bb16457b99eb5c860a32544a671440e1f5a97de2a467cd |

其余来源与派生文件指纹见Manifest；其输入同时绑定批准Git blob和实际源文件SHA，不仅检查文件名。新约4.70MiB配方是轻量组件JSON，没有大型矩阵或解向量。

## 实际修改

- 385组逐组用存储double的精确有理数积分D、求和Q。180个正差组各选最大Q账户；并列按完整ID Unicode顺序。
- 精确目标转为最小向上binary64；独立复核前一相邻数不足。180项before/after hex及ΔQ与批准模拟完全一致，其余627账户逐位不变。
- 每项同步 `Store.e_nom`、`Store.e_initial`、`route.annual_cap_mwh`、外置 `QuantityMWh`，共720个标量字段差异。没有增删组件或端口；5个Animal waste原样保留。
- ΔQ合计 `45046859/281474976710656 ≈ 1.60038592156297e-07` MWh；最大单账户 `3/134217728 ≈ 2.23517417907715e-08` MWh。
- 最大实际商品份额绝对改变量 `1.7755750330162e-16`。不是份额逐位不变，也不是数学等价缩放；这是已批准的有限源常数修订。
- 385/385严格D≤Q′，0组D=Q′。总有限余量 `2.87790373627514e-07` MWh；最大 `9.81672201305628e-08` MWh。该源舍入余量与未来解残差分开报告。

## 需求、源语义与接口

新版本按SHA引用原分配和原Load数据，无任何Load再生成。独立读取全部1737×2920个Load值，与实际冻结NetCDF逐位对照，并核三套2920项权重。原161个全零分配列不生成Load的行为按旧 `bind_loads` 继承；没有把正负荷归零或删除Load。

4070组件与3149Bus配方全部结构字段比较，除上述Q字段无实质差异：原非循环性、方向、效率、端口、SourceRow/InputID、NULL价格及排放因子、碳政策和配方成本保留。源固定账户与独占资源边界的物理含义不变；仍不是独立资源潜力估计。

未来如获授权组装，必须将新配方、新外置账与原分配同时绑定，生成新的组装Manifest，检查Q到实际缩放LP边界的传递。**旧Gate3/Gate4 Manifest和accounting_qualification不能作为新版证书复用。** 本次未生成新完整NetCDF或LP，不能声称未来矩阵目标、所有缩放界或全LP可行性已经通过。

## 工程记录与停止

开发时两项接口问题已修正并保全记录：Load数量检查最初误计既有全零分配列；严格JSON写入曾拒绝源配方既有Infinity容量值。保留部分新输出SHA与失败记录，未改物理边界或原件；最终沿用原配方Infinity表示。没有发生超出批准范围的科学修订。

独立验收与13项有限负例均通过，见 `EXACT_SOURCE_CLOSURE_A_STATIC_ACCEPTANCE.md`。没有构建LP、调用求解器、调整V3/V4或操作AutoDL。G6-05继续PAUSED_BY_USER。

下一步：联合审阅本次源修复，随后按另行明确范围进入A-05/A-06及B阶段静态审计；365日和新的2920时段Gate6仍需独立授权。不得凭本结果给历史解事后PASS。
