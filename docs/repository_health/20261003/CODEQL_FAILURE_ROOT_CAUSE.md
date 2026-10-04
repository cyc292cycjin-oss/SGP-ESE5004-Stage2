# CodeQL failure root cause

**结论：REPOSITORY_ELIGIBILITY / CODE_SCANNING_FEATURE_UNAVAILABLE，导致SARIF_UPLOAD失败。Python提取、数据库构建、查询分析和SARIF生成已完成。**

## 精确运行身份

| 字段 | 直接读取值 |
|---|---|
| Repository | https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2 |
| Workflow | `.github/workflows/codeql.yml`，CodeQL，ID 368257323 |
| Run | [37048744962](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37048744962)，attempt 1 |
| Job | [110976558784 — Analyze (python)](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37048744962/job/110976558784) |
| Event / branch | schedule / main；不是fork PR |
| Commit | a3616a68ee44592af6527ca9024a90f1956646ae |
| Job起止 | 2026-10-02 18:38:03–18:40:57 UTC，即10月3日02:38:03–02:40:57上海时间，2m54s |
| Result | completed / failure |

身份、时长及10条注释均与用户通知吻合；没有根据邮件文字推测根因。

## 第一项致命错误与因果顺序

第一个失败step为 **Perform CodeQL Analysis（step 5）**，其中失败子阶段为上传，不是查询分析。完整日志 `evidence/CODEQL_FULL_LOG.txt:1505` 的首个 `##[error]` 为：

> Please verify that the necessary features are enabled: Code scanning is not enabled for this repository. Please enable code scanning in the repository settings. - https://docs.github.com/rest

| UTC时间 / 全日志行号 | 事件 | 判断 |
|---|---|---|
| 18:38:26 / 137 | 读取CodeQL API/feature flags已报同一“code scanning not enabled”警告 | 最早可见根因征兆；当时未终止init。 |
| 18:38:41 / 139 | 使用Action附带CLI 2.27.0作为fallback | 可恢复后果；不是CLI缺失。 |
| 18:39:09 | Initialize CodeQL完成success | 初始化没有失败。 |
| 18:40:07 / 1496 | Exported results to SARIF | 查询结果已成功导出。 |
| 18:40:07 / 1498 | 9/9 Actions文件、77/77 Python文件的扫描摘要 | 本次分析完成；不是“没有发现代码”。 |
| 18:40:22 / 1505 | SARIF上传首次致命报错 | 决定本job失败。 |
| 18:40:37 / 1506、18:40:54 / 1530 | 状态/诊断接口继续报相同功能不可用警告 | 同一外部问题的后续影响，不是新源代码错误。 |

Post步骤中的诊断SARIF尝试不等于安全结果成功入库。run artifacts=0，code-scanning analyses API仍返回403。不能声明“已上传”或“没有安全漏洞”；本轮没有可据以评估漏洞清单的成功code-scanning结果。

## 全部10条注释

以下序号沿API返回顺序；原文见 `evidence/CODEQL_ANNOTATIONS.json`。注释中的`.github`及行号是Action注释位置，不应解读为10处Python源码缺陷。

| API序号 | Level / 位置 | 内容与归因 |
|---|---|---|
| 1 | warning / .github:23 | CodeQL API无访问能力；详细原因是code scanning未启用。重复能力/状态警告。 |
| 2 | warning / .github:504 | 同一API能力警告；包含通用fork/permission建议。 |
| 3 | failure / .github:503 | 上述SARIF上传致命错误。 |
| 4 | warning / .github:502 | 上传前的code scanning未启用警告。 |
| 5 | warning / .github:31 | 同一API能力警告。 |
| 6 | warning / .github:881 | 同一API能力警告。 |
| 7 | warning / .github:18 | feature flags未指定CLI，fallback到Action附带2.27.0；正常继续。 |
| 8 | warning / .github:17 | 无法读feature flags，因此不启用实验特性；同一外部原因。 |
| 9 | warning / .github:16 | 同一API能力警告，初始化阶段已经出现。 |
| 10 | notice / .github:1 | ubuntu-latest计划从2026-10-19迁移Ubuntu 26；本次实际Ubuntu24.04，不是此次失败。 |

共 **1 failure＋8 warnings＋1 notice**。其中6条API/feature-flags能力警告、1条CLI fallback、1条上传前警告；不是10项漏洞。

## 根因类别排除

| 候选类别 | 本次证据 |
|---|---|
| Workflow syntax | 不是；YAML解析通过，GitHub启动并执行到上传。 |
| Deprecated Action | 不是；init/analyze为v4.38.0，checkout为v7。 |
| Workflow token缺权限 | 不是此次原因；日志实际SecurityEvents: write、Contents/Actions/Packages: read。 |
| CodeQL initialization | success，API能力警告有fallback。 |
| Python build configuration | python＋none正确；manual占位step被跳过。 |
| Database creation | 完成，后续查询及SARIF输出有日志。 |
| Analysis | 完成；job名称包含Analysis不代表失败就在查询过程。 |
| SARIF upload | **直接失败阶段。** |
| Repository eligibility/security settings | **根因：当前仓库不具备可用code-scanning功能。** |
| Dependency/environment | 未观察到导致本CodeQL失败的依赖/环境错误。其他CI故障另报。 |
| Python语法/源代码错误 | 本run没有此类致命诊断，不应因此重构研究Python。 |

## 为何不是加权限或升级版本即可修好

API确认仓库为 **private，owner.type=User**。两项管理员只读code-scanning API均返回403、相同功能未启用信息。GitHub现行文档列出的可用类型为公开仓库，以及具备相应套餐和GitHub Code Security的组织仓库；当前“个人私有仓库”不在列出的支持类型内。[官方功能可用性](https://docs.github.com/en/code-security/concepts/code-scanning/code-scanning)

因此这不只是未经证实的“忘开一个开关”。仓库类型/授权是外部治理决定，不能靠YAML增加write权限修复。本轮未读取或推测具体账单、没有购买/转移仓库/公开资料/启用安全设置。

跨运行反证：9月27日main push同样在SARIF上传失败；Dependabot PR已使用 **v4.38.2** 仍出现同一错误。故再盲升Action不能解决此根因。现有3次CodeQL运行全部复现；不为重现已明确外部阻断额外消耗Actions运行。

**处置：DOCUMENTED_EXTERNAL_BLOCKER。未实现代码修复、未伪造PASS、未禁用upload来制造绿灯。**
