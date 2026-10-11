# Baseline evolution ledger

日期：2026-10-11。审计分支：`audit/stage2-baseline-lineage-20261011`；实际源仓库基线：`b9be7d0ab788a4151346c098d2e657c7e94a22da`。此提交来自research/full-sc-baseline，不是Windows历史文档副本，也不是当前GitHub main。

| 阶段 | 状态 | 本轮边界/证据 |
|---|---|---|
| S0 | COMPLETE_LOCAL_EVIDENCE | Git身份、干净源码工作区、上游提交对象/远端参考、两次终态与执行hold，见evidence/S0_STATE.json |
| A-01 | COMPLETE_WITH_EXPLICIT_UNKNOWNS | 上游论文、Sector Coupling及当前Full-SC差异总账 |
| A-02 | IN_PROGRESS | 807固定资源Store谱系与异常生成路径 |
| A-03 | NOT_STARTED_AWAITING_REVIEW | 本轮结束后由用户与ChatGPT决定科学检查问题 |
| B | NOT_STARTED_SCOPE_NOT_PROVIDED | 用户要求保留A—F台账，但尚未给出本阶段具体任务；不擅自命名实验 |
| C | NOT_STARTED_SCOPE_NOT_PROVIDED | 同上 |
| D | NOT_STARTED_SCOPE_NOT_PROVIDED | 同上 |
| E | NOT_STARTED_SCOPE_NOT_PROVIDED | 同上 |
| F | NOT_STARTED_SCOPE_NOT_PROVIDED | 同上 |

证据等级：VERIFIED=原件/代码/已核SHA直接支持；DERIVATION=列明假设的解析推导；RISK=有路径但未证明发生；UNKNOWN=缺证据。不得将资源耗尽候选解解释为已经证明原模型不可行。

发布记录按S0、A-01、A-02分别提交与推送；commit自身不能含其尚未产生的commit SHA，最终发布回执及后一里程碑记录前一commit。禁止force-push、main直写、模型改动、上传大矩阵/向量/凭据。

## 已发布里程碑

- S0：`623e734658973dd438af96a4944f605befa9ec2e`，已推送审计分支；源码和历史结果未改。
- A-01：本提交建立22类差异、217项指定范围路径清单及源文件SHA索引；上游运行配置/默认配置/当前物理对象分开。A-02详细解释待下一里程碑。
