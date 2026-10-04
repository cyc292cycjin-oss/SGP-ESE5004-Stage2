# Phase4 Git starting point — pending archive completion

**Branch creation=PENDING。`research/full-sc-baseline`本地/远程均未创建。实际parent SHA不存在。** 用户要求先完整冻结Phase1–3历史，目前完整报告链因4份原件的上传许可未关闭而暂缓，故没有跳过前置门槛。

## 两个候选基点的明确评估

| Candidate | SHA | Assessment |
| --- | --- | --- |
| Frozen U | a3616a68ee44592af6527ca9024a90f1956646ae | 与既有Phase3C PHASE4_ASSEMBLY_HANDOFF.md、Phase2 BASELINE_ARCHITECTURE.md一致：U为组装基点，后续选择性集成候选。当前推荐起点。 |
| 已验证Buildings源码 | 353dec3c83b859eab39bcf2dff79fe30d88a2ec0 | 仅Buildings组合验证，不是全部Full-SC工程集成；不能默认为包含GDP、carbon、shipping或最终研究需求边界。 |
| Buildings验证记录tip | 50a73d8f531132c5459174a55cac412d5f684462 | 上一行源码的子提交，仅附验证记录；也不是全系统已验证基点。 |

**完整备份后建议使用的base SHA：a3616a68ee44592af6527ca9024a90f1956646ae**。这是显式建议，不伪造已经创建的分支/parent。现有`codex/research-sc-main`仍在U。新开发ref创建时应直接指向U，不制造“空提交”；此时branch tip=chosen base，Git commit自身的parents仍是U原有parents。

## 未合入的候选

GDP a7a8f06b43f0dcce0dbd7005b989d8f73d142b81；carbon key 753ac81c23f8b9a1ca8ceed531d0630b56f6953d；Buildings E1/E2/E4源修复及组合验证；shipping 512c6cc2e53c579976d269486a7e328a0f372017、cf4b0f816086470dce40ec950e20c045044eec0c和字节保真85a32dc231458fd753445df38d422b78435b8aad。全部是Phase4选择性评审对象，不因远程备份就视为已验收/合入。

immutable tags：reference/tutorial-ce327bfa、reference/paper-run-5bacad70、reference/paper-publication-99159edb、reference/upstream-sc-a3616a68、reference/buildings-validation-50a73d8f。完整SHA见RESEARCH_MILESTONE_REF_PLAN.md和REMOTE_REF_VERIFICATION.csv。

远程archive ref：**尚无完整研究归档ref**；待保存的真实分支为codex/github-health-audit @ 753ff15b45ddb91c406a823f8252fc7b603f29c4。

远程main：a3616a68ee44592af6527ca9024a90f1956646ae，未改。CodeQL：**EXTERNAL_INFRASTRUCTURE_EXCEPTION / CODEQL_BLOCKS_PHASE4=NO**，沿用已核实的分析完成、SARIF因私有仓库功能不可用而上传失败结论。本轮未改workflow、账号套餐、仓库可见性或安全上传。

本轮scientific/model modifications=0，model assembly=0，solver runs=0，cherry-picks=0，merges=0。当前NO是远程存档门槛，不能据此否定Phase3科学设计关闭，也不能反过来宣称已经准备好正式求解。
