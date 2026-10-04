# Phase 3B-2 — Transport minimum baseline and closeout

2026-10-03 · SGP ESE5004 Stage2 · Human Scientific Review 交付。

先读 [收口结论](TRANSPORT_PHASE3_CLOSEOUT.md)，再读 [最低基准](TRANSPORT_MINIMUM_DEFENSIBLE_BASELINE.md) 和 [组装交接](NEXT_FULLSC_HANDOFF.md)。本目录包含用户要求的15项产物（12个Markdown、3个CSV），以及原行证据、候选补丁、测试和交付复核记录。

**Transport研究范围关闭；表示规范按用户决定冻结；真实数值和模型组装尚未通过全部门槛。** `TRANSPORT_CLOSED_FOR_FULLSC_ASSEMBLY=NO`。不继续Transport深入轮次，不运行正式模型。

模型源码候选仅涉及shipping分配及Load目标守卫。完整候选位于独立分支 `codex/transport-shipping-reviewable-patch`，提交 `85a32dc231458fd753445df38d422b78435b8aad`，基于冻结U版本。两项功能修复及换行保真分别保留独立分支/提交；没有合入Research Model。本审计目录与候选模型分支分开提交。

证据优先级：本轮用户决定 → 固定SHA源码/保留原行 → 已保存网络静态证据 → 标注的推导/组装建议。上一轮证据见 [Phase3B1](../phase3b1/README.md)；不是重新下载或独立复现实验。单元测试中的数值是明确标注的测试夹具，不是新ASEAN输入。数据接受状态继续UNVERIFIED/PENDING。

源码引文约定：`U/file:line` 对应 `../phase3b1/evidence/source/U/file`，固定SHA `a3616a68ee44592af6527ca9024a90f1956646ae`；P固定SHA `5bacad702ccfed17ad19ab510fa710651e966f2c`；Buildings验证层固定SHA `50a73d8f531132c5459174a55cac412d5f684462`。支持文件及源哈希见 `evidence/DEPENDENCY_MANIFEST.json`、上一轮 `SOURCE_MANIFEST.json`。

离线测试复查：在有numpy/pandas的既有环境运行 `candidate/test_shipping_allocation.py <isolated-checkout> <result.json>`（最终17项）。第一阶段原15项另存 `candidate/test_shipping_allocation_initial.py`。补丁见 `candidate/SHIPPING_ALLOCATION.patch`；测试不导入PyPSA、不调用solver、GIS用明确夹具替代。不要把测试通过解释为真实11国网络通过。install/finalize/sync脚本是本轮一次性执行痕迹，含版本保护；不要在冻结模型上重跑。

审阅使用academic-research-suite的证据核查流程；3个有界子任务仅审阅已有证据，未访问外部模型或新增文献。CSV由artifact-tool导出并核对。候选源码保留其AGPL许可；原始材料权利归其来源。本包未公开发布。
