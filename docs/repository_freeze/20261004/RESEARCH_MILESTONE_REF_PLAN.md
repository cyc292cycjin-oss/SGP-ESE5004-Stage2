# Research milestone ref plan and execution

**已执行5个注释tag和7个原有分支推送，12/12精确核验。** 注释tag的object SHA与其指向commit SHA不同，验收使用peeled commit。

| Milestone | Commit SHA | Class | Durable remote reachability |
| --- | --- | --- | --- |
| tutorial | ce327bfae2abe5526d4c1976173f0f8d08366ba5 | IMMUTABLE_REFERENCE | refs/tags/reference/tutorial-ce327bfa |
| paper_run | 5bacad702ccfed17ad19ab510fa710651e966f2c | IMMUTABLE_REFERENCE | refs/tags/reference/paper-run-5bacad70 |
| paper_publication | 99159edb7298b847fea517bf05c3f388493501c9 | IMMUTABLE_REFERENCE | refs/tags/reference/tutorial-ce327bfa; refs/tags/reference/paper-publication-99159edb; refs/tags/reference/upstream-sc-a3616a68; refs/tags/reference/buildings-validation-50a73d8f; refs/heads/codex/fix-industrial-gdp; refs/heads/codex/fix-carbon-config; refs/heads/codex/buildings-e1; refs/heads/codex/buildings-e2; refs/heads/codex/buildings-e4; refs/heads/codex/buildings-accounting-validation; refs/heads/codex/transport-shipping-reviewable-patch |
| upstream | a3616a68ee44592af6527ca9024a90f1956646ae | IMMUTABLE_REFERENCE | refs/tags/reference/tutorial-ce327bfa; refs/tags/reference/upstream-sc-a3616a68; refs/tags/reference/buildings-validation-50a73d8f; refs/heads/codex/fix-industrial-gdp; refs/heads/codex/fix-carbon-config; refs/heads/codex/buildings-e1; refs/heads/codex/buildings-e2; refs/heads/codex/buildings-e4; refs/heads/codex/buildings-accounting-validation; refs/heads/codex/transport-shipping-reviewable-patch |
| industrial_gdp | a7a8f06b43f0dcce0dbd7005b989d8f73d142b81 | CANDIDATE_FIX | refs/heads/codex/fix-industrial-gdp |
| carbon_key | 753ac81c23f8b9a1ca8ceed531d0630b56f6953d | CANDIDATE_FIX | refs/heads/codex/fix-carbon-config |
| buildings_e1_source | 92e9118be20f0b3802f385adac2f56650d57299d | CANDIDATE_FIX | refs/heads/codex/buildings-e1 |
| buildings_e2_source | 31037d60d69fa762c9ed8ec9ce8289d95bd6a181 | CANDIDATE_FIX | refs/heads/codex/buildings-e2 |
| buildings_e4_source | 5d761eceeeb0d0519208d760224a41ff50ec1e30 | CANDIDATE_FIX | refs/heads/codex/buildings-e4 |
| buildings_validation | 50a73d8f531132c5459174a55cac412d5f684462 | IMMUTABLE_REFERENCE | refs/tags/reference/buildings-validation-50a73d8f; refs/heads/codex/buildings-accounting-validation |
| buildings_tested_source | 353dec3c83b859eab39bcf2dff79fe30d88a2ec0 | IMMUTABLE_REFERENCE | refs/tags/reference/buildings-validation-50a73d8f; refs/heads/codex/buildings-accounting-validation |
| shipping_allocation | 512c6cc2e53c579976d269486a7e328a0f372017 | CANDIDATE_FIX | refs/heads/codex/transport-shipping-reviewable-patch |
| shipping_target_guard | cf4b0f816086470dce40ec950e20c045044eec0c | CANDIDATE_FIX | refs/heads/codex/transport-shipping-reviewable-patch |
| shipping_final | 85a32dc231458fd753445df38d422b78435b8aad | CANDIDATE_FIX | refs/heads/codex/transport-shipping-reviewable-patch |

## 最小ref选择

| Remote ref | Expected commit | Purpose |
| --- | --- | --- |
| refs/tags/reference/tutorial-ce327bfa | ce327bfae2abe5526d4c1976173f0f8d08366ba5 | Immutable tutorial reference; not paper reproduction |
| refs/tags/reference/paper-run-5bacad70 | 5bacad702ccfed17ad19ab510fa710651e966f2c | Immutable author paper actual-run source reference |
| refs/tags/reference/paper-publication-99159edb | 99159edb7298b847fea517bf05c3f388493501c9 | Immutable later paper publication/cleanup reference |
| refs/tags/reference/upstream-sc-a3616a68 | a3616a68ee44592af6527ca9024a90f1956646ae | Immutable upstream SC baseline; not assembled Full-SC |
| refs/tags/reference/buildings-validation-50a73d8f | 50a73d8f531132c5459174a55cac412d5f684462 | Immutable combined validation record; tested source is parent 353dec3c83b859eab39bcf2dff79fe30d88a2ec0 |
| refs/heads/codex/fix-industrial-gdp | a7a8f06b43f0dcce0dbd7005b989d8f73d142b81 | Isolated industrial GDP candidate; not merged into research model |
| refs/heads/codex/fix-carbon-config | 753ac81c23f8b9a1ca8ceed531d0630b56f6953d | Isolated carbon-key engineering candidate; no new policy |
| refs/heads/codex/buildings-e1 | 30bafa420e5cd639e696cbdd56de0e7df36c0e47 | Preserve E1 source fix 92e9118be20f0b3802f385adac2f56650d57299d and validation records |
| refs/heads/codex/buildings-e2 | 070db2918186829908a02a0b72a7b4426711c653 | Preserve E2 source fix 31037d60d69fa762c9ed8ec9ce8289d95bd6a181 and validation records |
| refs/heads/codex/buildings-e4 | 9342893fcf467eadbbc410f59c3dbe817d123aa9 | Preserve E4 source fix 5d761eceeeb0d0519208d760224a41ff50ec1e30 and validation records |
| refs/heads/codex/buildings-accounting-validation | 50a73d8f531132c5459174a55cac412d5f684462 | Preserve real combined buildings validation history; no new merges |
| refs/heads/codex/transport-shipping-reviewable-patch | 85a32dc231458fd753445df38d422b78435b8aad | Preserve two shipping functional candidates and byte-fidelity commit |

E1/E2/E4保留原codex分支名，分支tip包含源修复之后的验证/环境说明；未创建重复fix/*别名。shipping只推最终reviewable分支，其祖先包含两项功能修复。combined validation tag指向记录50a73d8f，源353dec3c作为直接父提交可达；没有把记录SHA冒充被测源码。

注释tag消息包含目的、完整source SHA、2026-10-04上下文和不可重定向要求。未碰撞或移动任何tag。没有设置GitHub服务端tag保护规则；这里的immutable是项目引用政策，不是宣称管理员技术上不能删除它们。

## 另外两类ref

- **RESEARCH_ARCHIVE**：已有coherent分支`codex/github-health-audit` @ 753ff15b45ddb91c406a823f8252fc7b603f29c4可覆盖全部报告族，无需合成三条漂亮历史。但它继承SAFETY_REVIEW.md的4份原件，暂缓推送。未另造archive/*分支，也未把候选fix分支称为全部报告归档。
- **FUTURE_DEVELOPMENT**：`research/full-sc-baseline`保持PENDING。项目既有设计支持从a3616a68ee44592af6527ca9024a90f1956646ae出发，但用户规定必须先完整冻结Phase1–3历史；当前此门槛未过。

本地codex/paper-reference-5bacad70已有等价immutable tag，本轮不再重复推branch；U的research-sc-main、upstream-sc-baseline与未实施修复的fix-topology亦不重复推送。临时/旧草稿/未命名dangling提交未推送。
