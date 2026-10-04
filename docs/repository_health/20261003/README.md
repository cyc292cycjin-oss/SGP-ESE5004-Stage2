# GitHub Repository & CodeQL Health Audit

日期：2026-10-03，Asia/Shanghai。范围仅仓库基础设施；不是Phase4模型工作。

**仓库版本控制可用；CodeQL分析已完成，但GitHub code-scanning上传因仓库功能不可用而失败。没有发现需要修改Python或CodeQL YAML的根因。**

| 最终状态 | 值 | 口径 |
|---|---|---|
| REPOSITORY_HEALTHY | YES | Git对象、fetch、默认分支、引用与现有有效工作树可用；不表示所有Actions全绿。 |
| CODEQL_HEALTHY | NO | Analyze (python)最终失败；SARIF未成功上传。 |
| PHASE1_3_SCIENTIFIC_INTEGRITY_AFFECTED | NO | 此故障未更改模型/数据/既有结果；固定身份核对一致。 |
| GITHUB_READY_FOR_PHASE4 | NO | 按完整托管/安全检查闭环口径，code scanning外部阻断和研究分支托管决定未关闭；Git本身可用于开发。 |
| SCIENTIFIC_IMPACT | NONE | 指本次CodeQL事件的直接科学影响；不撤销既有Phase4输入和工程门槛。 |

报告入口：

1. [仓库健康](GITHUB_REPOSITORY_HEALTH.md)
2. [CodeQL根因与全部10条注释](CODEQL_FAILURE_ROOT_CAUSE.md)
3. [其他Actions健康](GITHUB_ACTIONS_HEALTH.md)
4. [CodeQL配置审计](CODEQL_WORKFLOW_AUDIT.md)
5. [Phase4托管就绪与A–L回答](GITHUB_PHASE4_READINESS.md)

没有实现修复，因此没有CODEQL_FIX_REPORT.md、修复分支/PR或修复后PASS声明。保存的是独立基础设施审计记录。未push、merge、修改设置、购买授权、改变可见性、执行模型或重新运行Actions。

证据包括失败run/job/check原始JSON、完整日志及逐行摘录、其他失败日志、固定HEAD的9份workflow、Git身份/对象检查和官方来源登记。API当前可见运行共21次，10个workflow注册项（9个文件＋Dependabot动态workflow）；本轮完整覆盖这个可见范围。无运行记录不等于PASS。

源`.gitignore`和`.gitattributes`分别保存为`evidence/source/ROOT_GITIGNORE.txt`和`ROOT_GITATTRIBUTES.txt`，内容字节不变；避免它们在证据目录生效、改变快照换行或跟踪规则。原路径及snapshot_path映射见REPOSITORY_GIT_AUDIT.json。

`capture_github_evidence.py`、`capture_other_failures.py`只读取历史API/日志；`audit_git_state.py`在已有WSL对象库中fetch（不prune、不checkout）并检查Git/YAML；`summarize_evidence.py`只汇总证据。避免将这些工具当作模型workflow执行。包含私有仓库日志，交付包保持本地；未公开发布。
