# C-01R：受限binary64聚合正式批准记录

2026-10-12；最终 **C01R_REPRESENTATION_ACCEPTED**。本记录落实用户和ChatGPT对“方案一：受限binary64舍入”的明确批准，来源为本轮用户粘贴请求，原文SHA `ae4a968ef1e2082f254bdaf36b844f990a84276271196a48b92165516eea9fd9`。不扩大为科学Load、资源、物理阈值、构模或求解授权。

批准只适用于365日诊断中的96条时变电力Load：精确8×3h日均转最近binary64/ties-to-even，逐日相邻值半ULP、年度加权半ULP累计界及每资产绝对`2e-9 MWh`/相对`1e-15`四项必须同时通过。零年度量须零差并核合法源序列。无人工偏置、nextafter补差、跨资产抵消、补偿资源或slack。

科学年度量仍为冻结2920输入的精确积分；日实装量是另有身份的数值表示。差额必须独立记账，不是新科学需求，不是原LP等价变换，不是未来V4残差豁免。原本精确的1642条Load保持年度精确，所有平坦值逐位不变。Scheme A 385/807、180项Q、所有归属及四字段不变。

V4原件SHA `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f`本轮实读匹配，未修改；源NetCDF和Scheme A身份实核。CF/入流沿原预算，不套电力上限、不裁剪。源CF既有44个超1一个ULP值继续披露。

新协议 [C00_DAILY_365_PROTOCOL_C01R_V1.md](C00_DAILY_365_PROTOCOL_C01R_V1.md) SHA：`661a81e532184003938213a3e81ad35bd4a687108332d14b3582bf7a8eac2856`。
机器规则 [C01R_RULE.json](evidence/C01R_RULE.json) SHA：`49d85c8449b32bb1fbf972b564dacb70a12e918dee58e4678efc36f0c736b140`。
原C00严格年度相等决定和C01 DECISION_REQUIRED历史保留，旧双字辅助变量候选未被选用；本轮未实现它。

这次准入允许**申请C-02受控构建审查**，不代表C-02/C-03获准或已执行。用户仍需联合验收本交付，再单独授权后续构建；没有其他自动科学修订、AutoDL操作、模型或求解。G6-05继续PAUSED_BY_USER。
