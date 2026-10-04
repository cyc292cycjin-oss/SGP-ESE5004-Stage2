# Gate3 pre-integration exact diff review

Base: `ad5e81e75882704ac9e33a6eac96c5c79717c5e1`. Review completed before integration; no commit created by this inventory.

A carrier isolation; B carbon architecture; C test/validation; D documentation; E unrelated.

| Draft | Class | Exact patch |
|---|---|---|
| configs/research/baseline.yaml | A+B | evidence/resume_diffs/baseline.yaml.patch |
| scripts_project/carbon_architecture.py | B | evidence/resume_diffs/carbon_architecture.py.patch |
| scripts_project/carrier_architecture.py | A | evidence/resume_diffs/carrier_architecture.py.patch |
| scripts_project/check_research_carriers.py | C | evidence/resume_diffs/check_research_carriers.py.patch |
| scripts_project/run_gate3_validation.py | C | evidence/resume_diffs/run_gate3_validation.py.patch |
| tests/research/test_carrier_carbon.py | C | evidence/resume_diffs/test_carrier_carbon.py.patch |

E unrelated: NONE in the six implementation drafts. New files are represented as complete additions. baseline.yaml preserves every research_demand value; it adds carrier/carbon contracts only.

Review follow-ups before integration: enforce nonnegative directed Link dispatch; retain geological storage investment cost in the objective with an extendable, capped Store; strengthen shared-event transfer guards; add missing Buildings/Shipping/manifest regression invocations. Final draft patches and hashes will be recorded before copying.

## 集成前审阅落实与窄修复

地质 Store 改为有明确上限的投资变量，禁止 Link 反向流，分摊后内部碳转移仍不能产生负信用；均经合成测试。集成使用六文件 allowlist。最终精确差异在 evidence/final_diffs。额外窄修复只将价格元数据与各国可用量解耦（独立 commit），无参数变更。没有 E 类内容合入。
