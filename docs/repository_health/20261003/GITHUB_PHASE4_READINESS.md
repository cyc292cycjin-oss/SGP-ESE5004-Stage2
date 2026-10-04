# GitHub Phase4 readiness（基础设施范围）

**REPOSITORY_HEALTHY = YES**

**CODEQL_HEALTHY = NO**

**PHASE1_3_SCIENTIFIC_INTEGRITY_AFFECTED = NO**

**GITHUB_READY_FOR_PHASE4 = NO**

**SCIENTIFIC_IMPACT = NONE**

最后一个NO采用“完整研究托管和安全检查已具备可用闭环”的口径。Git自身可fetch/commit/branch，最新测试有成功记录，并不阻止技术上开展本地开发；但当前安全扫描上传不可用，且主要研究分支未在目标GitHub托管。不能将这种PARTIAL状态自动当作全面就绪，也不将其反推成Phase3设计失败。

## Phase1–3影响核验

| 层/资产 | 身份 / 本轮状态 | 此CodeQL事件影响 |
|---|---|---|
| Paper Reference P | 5bacad702ccfed17ad19ab510fa710651e966f2c，工作树干净 | NONE；未改变或重新提取论文结果。 |
| Frozen Upstream U | a3616a68ee44592af6527ca9024a90f1956646ae，干净 | NONE；此SHA同时是失败run的main，代码可分析而上传不可用。 |
| Future Research Model R | 同U，干净且未组装 | NONE；本轮不开始Phase4。 |
| Phase1/2及Phase3审计链 | 本地f5853f0；WSL audit d1c2790 | 既有报告/证据未改；不把local commit说成GitHub已备份。 |
| Buildings验证V | 50a73d8f531132c5459174a55cac412d5f684462，干净 | NONE。 |
| Industrial GDP候选 | a7a8f06b43f0dcce0dbd7005b989d8f73d142b81，干净 | NONE；未合并/重跑。 |
| Carbon key候选 | 753ac81c23f8b9a1ca8ceed531d0630b56f6953d，干净 | NONE；未改变政策或约束。 |
| Shipping候选 | 85a32dc231458fd753445df38d422b78435b8aad，干净 | NONE；未合并/重跑。 |
| 已知topology候选 | 仍U身份，未应用fix | CodeQL不解决也不新增该科学工程缺口。 |

CodeQL安全静态分析不是科学模型验证；成功也不能批准输入数据，失败也不能自动否定已完成实验。本轮NONE仅针对本次基础设施故障及只读审计的直接影响，不表示原Full-SC的输入/碳scope/守恒门槛已经通过。

## 最少待处理事项

1. **Code-scanning外部决定**：当前是个人私有仓库，管理员API及日志均显示功能不可用，官方可用性列表不覆盖该类型。保留私有研究资产，先由用户决定是否以后在符合资格的组织/授权环境中启用，或正式接受当前扫描不可用这一基础设施例外。不能由Codex擅自公开仓库、转移归属、购买授权、关闭上传伪装PASS。[官方可用性](https://docs.github.com/en/code-security/concepts/code-scanning/code-scanning)
2. **研究托管范围决定**：远程仅main、教程归档及Dependabot分支；Paper固定引用、审计与候选分支尚不在远程分支/tag祖先链中。后续在明确清单下保存所需远程引用，保持数据/历史边界，不混入CodeQL修复。当前本地Git及交付包仍保留这些工作，不称资料已丢失。

Pages部署和conda-lock更新是独立维护项；不是要求它们先完美才允许科学设计继续。若下一阶段不用Pages、不更新环境，可明确记录暂不依赖。没有新增Phase3D，也没有改Phase4模型门槛。

## 外部阻断解决后的验证计划（本轮不执行）

在已获授权的合格仓库/服务边界下，重跑对应CodeQL job，等待最终completed/success，确认Analyze (python)、注释以及code-scanning analyses API中对应SHA/category的处理记录。仅workflow启动、SARIF文件生成或upload被关闭均不算通过。

此处没有可解决根因的最小YAML补丁，因此“修改后push分支再验证”的条件未触发。本轮不创建伪修复commit/PR，不重跑同一已确认受阻的扫描；按用户任务允许的“documented external blocker that cannot be fixed in repository code”完成审计。

## A–L明确回答

| 问题 | 回答 |
|---|---|
| A GitHub仓库本身健康？ | YES，版本控制/对象/引用健康；CI服务与托管覆盖仍PARTIAL。 |
| B 仅CodeQL失败？ | NO。Pages和环境锁更新独立失败，历史测试有下载失败；最新测试、Lint、Dependabot成功。 |
| C 最早根错误？ | code scanning功能不可用；初始化先警告，首次致命错误在step5的SARIF上传。 |
| D 10条注释是什么？ | 1 failure、8 warnings、1 notice；同一功能问题的重复警告/CLI fallback及未来runner通知，不是10个源码漏洞。 |
| E Action版本受支持？ | YES，主run为CodeQL v4.38.0和checkout v7（实际v7.0.1）；PR的v4.38.2也同样失败。 |
| F 权限正确？ | 本run正确，实际security-events:write、contents/actions/packages:read；无需扩权。 |
| G Python配置正确？ | YES，python＋none；manual占位被跳过；没有autobuild需求。 |
| H 分析还是上传失败？ | 分析/SARIF生成完成，上传失败。 |
| I 影响Phase1–3科学结果/来源？ | NO，此事件直接科学影响NONE；固定层和旧资产未变。 |
| J 需要仓库代码修复？ | 本根因不需要/无法靠YAML修复；需要外部资格/服务决定。其他维护问题独立记录。 |
| K 修复后干净重跑通过？ | 未实施修复、未重跑，不能称PASS；已有三次历史run及现时403足以证实外部阻断。 |
| L GitHub就绪支持Phase4？ | Git开发可用；完整托管/安全闭环NO，待上述最少决定。本轮不启动模型工作。 |

止于本次基础设施审计。没有科学文件修改、环境升级、数据替换、Git历史重写、分支删除、force-push、merge或正式求解。
