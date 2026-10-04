# Buildings 工程修复候选

三个候选分别从固定 U `a3616a68ee44592af6527ca9024a90f1956646ae` 分支，互不叠加，没有合并Research Model。Patch携带独立测试和before/after结果；不含数据替换。准确commit与工作树在[候选提交记录](evidence/CANDIDATE_COMMITS.json)。

| 项目 | 证据→失败 | 最小候选与边界 | 验证→守恒 | 状态 |
|---|---|---|---|---|
| E1 R覆盖S/central | 原`add_heat` central合并R/S；`add_residential`最终国家循环改写所有heat | central仍共享同一Bus/技术，但分R/S两个Load；只对R按remaining/total比例缩放，保留节点分布和DH损耗；删最后全heat重标 | 5组合成fixture，含零R、零S、零DH份额、全urban DH、非单位snapshot权重。S时间序列不变，R剩余服务+损耗守恒，固定燃料和R/S直接电力守恒 | `ENGINEERING_FIX_REQUIRED`；候选待审 |
| E2 positive annual丢失 | shape总和0→NaN，consumer fillna0吞掉 | 归一化前校验正需求有有限非负且和>0的shape；0年量可0shape；consumer拒绝NaN/负值 | 7组合成fixture；非法输入明确失败、正常年量/热水保持 | 同上 |
| E3 电热/残余电力不闭合 | 扣减代码注释；Q不是测得的既有电热；services不在末端总量校准集合 | **本轮不提交猜测性数值补丁**。需要accepted national/direct/old-electric-heat bridge，才可指定按年/国/部门的残余计算及最终校准入口 | 原函数合成target=1、S=3→总计4，证明校准集合缺口；暂无可接受expected scientific input，因而没有虚构passing test | `ENGINEERING_FIX_REQUIRED` + `SCIENTIFIC_DECISION_REQUIRED` |
| E4 service命名 | allowlist`service electricity`不匹配实际`services electricity`，power filter删S | 单字符串修复；不改另一个electric-growth集合，避免与E3混在一起 | 合成过滤前AC20+S3，原过滤后20；补丁后23，S保留 | `ENGINEERING_FIX_REQUIRED`；候选待审 |

## 可审查提交

| Fix | Branch | Commit | Patch |
|---|---|---|---|
| E1 | `codex/buildings-e1` | `92e9118be20f0b3802f385adac2f56650d57299d` | [E1.patch](patches/E1.patch) |
| E2 | `codex/buildings-e2` | `31037d60d69fa762c9ed8ec9ce8289d95bd6a181` | [E2.patch](patches/E2.patch) |
| E4 | `codex/buildings-e4` | `5d761eceeeb0d0519208d760224a41ff50ec1e30` | [E4.patch](patches/E4.patch) |

每个候选commit只对应一个工程问题，包含Why、源码差异、合成测试。提交在本地，未push。早期本地候选的测试文件整理为独立名称；superseded SHA保留在receipt。Paper/U/R工作树未被这些commit修改。

## 测试证据与实际影响

- E1 [before](evidence/E1_before.json) / [after](evidence/E1_after.json)。R=6、S=4、urban=.6、DH potential=.3、loss=.15时，构网heat=10.27；R竞争余量=2，候选后R=2.054、S=4.108。多出来的0.162不是新增年服务，而是保留原损耗乘数所需的供热侧量。固定R油品=5、direct R=7、direct S=3保持。以上全部是fixture标签，不能用于ASEAN数据表。
- E2 [before](evidence/E2_before.json) / [after](evidence/E2_after.json)。没有插值、没有热带虚构曲线。失效应在正式求解前停止。
- E3 [未修复证据](evidence/E3_ACCOUNTING_DEMONSTRATION.json)。单改E4会暴露services仍被额外加到总量之上的问题，所以E4通过过滤测试≠整体网络守恒。
- E4 [before](evidence/E4_before.json) / [after](evidence/E4_after.json)。这是power-filter路径修复；`only_elec_network=false`的未来Full-SC不执行此过滤，但E3仍适用。P复现必须保留原作者行为，候选不能无说明回写P。

运行环境：PyPSA0.30.3、pandas2.3.1（结果JSON记录）。导入环境出现既有PROJ数据库警告；本轮不调用GIS功能，不修改环境。所有测试没有调用optimizer，不能替代未来小规模构网/运行的集成验证。

E1保留原有固定fuel与竞争heat的混合结构，**不自动实现完整BH-1服务边界**。分开central的Load账也不等于共享CHP/热源成本可按国家/部门唯一归因。补丁触及同一源文件的不同片段；本轮分别测试，未进行合并后的全流程验证。待数据边界接受后再审查组合应用。

## E3可实施条件（未执行）

先给每国每年同口径的gross/final meter、R/S direct、历史电热、其它已显式账户及loss位置；按集合确保每个终端用途只出现一次。再以该表为expected result，测试负残差、重复sector、missing-year、shape积分、末端growth重新分配是否保持国家总账。不以默认Q冒充历史电热，不把HP/电解槽优化用电预装入base。没有这套accepted bridge就不能提交“通过”的需求修复。
