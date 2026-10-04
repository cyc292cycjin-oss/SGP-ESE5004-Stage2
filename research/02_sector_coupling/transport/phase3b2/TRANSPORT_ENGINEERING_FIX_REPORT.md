# Shipping allocation engineering candidate

类型：**engineering fix candidates**。基于U `a3616a68ee44592af6527ca9024a90f1956646ae`；完整候选 `codex/transport-shipping-reviewable-patch` / `85a32dc231458fd753445df38d422b78435b8aad`。未合并Future Research Model，P/U/Buildings验证/R的HEAD和文件不变。

## Evidence → failing test

旧 `add_shipping`先按节点groupby.sum，将重复port的country字符串合成IDID等，再用该字符串映射全国oil需求；还将所有AC节点拼到ports并混合聚合，产生对齐/非有限问题。保留tutorial pre-strip有39/48个shipping-oil Load为NaN，H2有1个NaN；后者不是仅靠油字符串map可以解释。

对真实`add_shipping`函数AST的离线测试，使用明确测试夹具（两国、重复port、无port节点，非研究输入），修复前15项：1 PASS、13 FAIL、1 ERROR。重复port案例产生ID0=NaN、ID1=NaN、SG0=12 TWh；原表不被修改这一项原本通过。不是声称每个守卫测试都独立证明一个已发生的真实模型缺陷。

## Minimal patch

新增 `_shipping_allocation.py`严格分配器，输入为尚未合并的两列全国国内/国际年量。先验证国家量完整有限非负、port权重/覆盖和节点国别，**先按港口计算数值，再按节点汇总**。每个国内/国际账户分别核对国家总量。最后才对旧构造器合成物理总需求，并对完整AC节点索引提供值。

无port节点仅在全国源量完整、该国有合法分配覆盖或源明确为0后得到结构零；源缺失、非法权重、正量无port、跨国/未知node必须失败。没有silent fillna，也不将无数据国家归零。新helper不重新归一错误权重、不改源量、不改share/效率/成本。

旧构造器仍按原8760年化、合计oil/H2输入行为与旧carbon逻辑工作。候选只修分配，不证明原share/成本已接受，也不实现正式四账户Load或碳隔离。首版直接marine H2=DEFERRED；测试使用share0验证无非有限H2对齐，没有新增H2情景。

## Passing test与范围

第一项分配修复后**相同15项全部PASS**，包括重复节点、国内/国际各自守恒、原表未修改、源缺失/无限/负量、坏权重、未知/跨国node、重复国家、正量无port失败以及明确源零的无port国家。

最终复核发现，AC分配索引与实际Load使用的spatial.nodes若不一致，后续reindex仍可能产生NaN或丢量。增加“多出目标节点”“遗漏目标节点”两项测试：第一候选上二者FAIL，增加目标集合一致性/唯一性守卫后**17项全部PASS**；顺序差异则显式reindex，集合差异拒绝执行。该修正另有独立分支/提交，不掩盖首次候选的测试范围。

| 保存分支 | 提交 | Why |
|---|---|---|
| codex/transport-shipping-allocation | 512c6cc2e53c579976d269486a7e328a0f372017 | 数值分配先于节点汇总；15项初始回归 |
| codex/transport-shipping-target-guard | cf4b0f816086470dce40ec950e20c045044eec0c | 防止实际Load目标与分配集合不一致；新增2项回归 |
| codex/transport-shipping-reviewable-patch | 85a32dc231458fd753445df38d422b78435b8aad | Git按text=auto将原CRLF源码归一，造成整文件diff；文件专用-text保真恢复最小可审阅diff，Python AST未变 |

最终相对U的实际constructor改动仅12行增加/25行删除；另有helper、测试和2行Git属性。保留两项功能修复历史，没有重写既有研究/教程提交。第三项是字节保真，不是新增物理模型变化；复用已通过17项的相同AST测试证据。

测试抽取冻结构造器函数，网络采用记录器、GIS采用明确夹具；使用既有numpy/pandas环境，不导入PyPSA、不建solver。它验证实际函数中p_set对齐和源量守恒，**没有验证真实GIS、完整11国输入、PyPSA序列化或求解可行性**。绝不将其写作完整Full-SC PASS。

证据：初始 `evidence/SHIPPING_TEST_BEFORE.json` / `SHIPPING_TEST_AFTER.json`，目标守卫 `SHIPPING_TARGET_GUARD_BEFORE.json` / `SHIPPING_TARGET_GUARD_AFTER.json`，最终 `SHIPPING_CANDIDATE_IDENTITY.json`；逐项CSV的BeforeSource明确区分U和第一候选，不将17项都伪称已在原U上运行。完整diff见 `candidate/SHIPPING_ALLOCATION.patch`，原15项与最终17项测试源均附包。未force-push。

## 尚未修复的问题与归属

Road量纲链：新规范明确，未改生产函数。国内shipping by/in原行遗漏：在输入清单中独立暴露，未修数据/筛选器。Carbon shared-store collision及bunker比例错误：本轮只设计合同，禁止正式改约束。真实全ASEAN分配/时间总量：未生成新网络。这些纳入最终三个系统门槛，不再开Transport深挖轮次。

候选是可供人审阅的独立修复，不是自动批准合并。原始可复现输入与模型层未因本测试而改变。
