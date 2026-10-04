# Phase 3A-3 readiness and human acceptance handoff

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Mode: validate; Version: Phase3A3-1; Date: 2026-10-01 Asia/Shanghai
- Verification Status: engineering regressions VERIFIED; source interpretation ANALYZED; DATA ACCEPTED = NO
- Review mode: same-session assistant validation, not independent peer review or paper reproduction

## 本轮交付结论

完成 E1/E2/E4 独立修复的强化验证、隔离组合验证和 B1–B3 有界数据恢复。沿用已有最小源码补丁，各分支新增单独验证提交；没有重复改写上游，没有合并 R。原桌面交付包及其 177 个有效载荷哈希已核验一致。[交付包核验](evidence/HANDOFF_VERIFICATION.json)

| 问题 | 回答 |
|---|---|
| **A E1 failing→passing？** | 是。U 308/777 项失败；E1 777 项全部通过。11 国标识、22 节点、R/S 服务与 DH loss 分开核对。 |
| **B E2 failing→passing？** | 是。U 43/417 项失败；E2 197 项全部通过。行数因正确提前 raise 而不同，完整记录保留。正年度+无效形状不再生成静默丢量网络。 |
| **C E4 failing→passing？** | 是。U 22/88 项失败；E4 88 项全部通过。Services carrier 过滤正确，需求数值未改。 |
| **D 哪些 patch 建议人工合并？** | E1、E2、E4 三个独立源码提交，连同各自验证提交；见下表。E3 未实施，不建议将本次合并等同 Full-SC 已就绪。 |
| **E 高质量 thermal/end-use 来源族？** | 有：马来西亚官方 NEB 的 R/S final-energy/end-use 表尤其具体；区域试点/国家调查补充覆盖。尚非 11 国同年 useful heat 数据集。 |
| **F ASEAN-specific space/water 证据？** | 有国家/地区样本依据；没有被接受的统一比例。不能把某表缺采暖列或样本零当全国零。 |
| **G 比 BDEW 更合适的 temporal basis？** | 找到河内局地用水观测和区域调查方法线索；尚无可直接替代 BDEW 的已核实全年 R/S 热曲线。 |
| **H Cooling only direct + no double count？** | 无显式 cooling module / 二次 cooling Load 的结构已核实；完整 11 国数量无重复尚不能确认，E3和历史电热桥接未闭合。无内生制冷技术灵活性。 |
| **I Cooking 可非显式？** | 可以按用户冻结边界继续非显式；不能以“影响很小”为理由。新官方用途表足以要求共同确认其燃料保留及不得误归 space/water 的规则。 |
| **J Buildings + Heat 达到 DATA ACCEPTED？** | **否。** 8 项新候选、更新登记的全部50项仍 UNVERIFIED/PENDING。工程通过不授予科学接受。 |
| **K 最少缺什么？** | 以下五项；其中第四项与部分第一项是接受/边界决定，不只是下载缺失。 |

## 最小五项验收条件

1. **R/S 用途与 useful-service 转换链**：同年 final fuel/electricity→space/water 的依据、效率/COP、热值与容量口径；先关闭印尼商品/部门冲突，并决定马来西亚旧年/半岛数据仅作核验还是允许经明确方法转换。未覆盖国必须有明确且共同接受的处理方式，不能代填。
2. **国家电力桥接与 E3 后续授权**：冻结 base、R/S meter、历史电热和 residual 的同年数量桥接，明确 cooling/cooking 只保留一次；随后才讨论独立 E3 实施。本轮不做该修改。
3. **地区 space/water 与时序证据**：采暖存在范围和阈值、R/S 热水曲线、季节和weekday/weekend差异；若没有全覆盖来源，应先共同接受研究方法/范围。零 HDD 的工程报错不能当科学填补。
4. **边界与工程接受**：人工分别审查 E1/E2/E4；记录 DH 地区范围、未显式建立 heating stock 的准确表述，以及 cooking 燃料与 heat 的排除/保留规则。用户已冻结不新增 cooking/cooling 模块，本轮不重新要求确认这一点。
5. **原始文件与版本的有限缺口**：菲律宾 HECS 原表、适用地区/部门的 end-use 微观或原始小时数据，以及调查上推/参考期说明。只有选择采用这些来源时才需要相应文件；不要求用户重复提供已缓存 NEB、ERIA、BELDA 或上轮资料。TuyHoa全文可作为补充，并非冻结边界的唯一必需条件。

## 可审查提交

| Fix / branch | 源码 commit | 本轮验证 commit |
|---|---|---|
| E1 / `codex/buildings-e1` | `92e9118be20f0b3802f385adac2f56650d57299d` | `59dbd34880bcdb367fed54cdee39a2ace40182fd` |
| E2 / `codex/buildings-e2` | `31037d60d69fa762c9ed8ec9ce8289d95bd6a181` | `1f9405720a873918614df5aad361580cff7cedde` |
| E4 / `codex/buildings-e4` | `5d761eceeeb0d0519208d760224a41ff50ec1e30` | `78b23e7804ca05f2fd1f5ee5ec90f3fa6f8bbf7c` |

每项保留源码 patch 与 validation patch。[完整记录](evidence/FIX_COMMITS.json)。组合测试使用 U 文件加三个源码 diff 的独立副本，无 Research Model merge；[组合源码身份](evidence/COMBINED_SOURCE_RECEIPT.json)。

严格数值判据为 `1e−6 MWh + 1e−12 × |expected|`；有效年度积分最大误差约 `1.86e−9 MWh`。上轮报告“1e−9级容差”而测试沿用 NumPy 默认容差的问题，本轮以显式阈值与实际误差报告澄清，未重写旧交付记录。

## 能继续到哪一步

可以把上述候选、补丁和最小证据清单交给用户与 ChatGPT 做科学验收。可以讨论实验设计框架；**尚不能冻结 Full-SC 科学输入/完整可执行边界，更不能启动 Integrated / Disconnected 成本比较**。本轮不处理其他部门既有门槛，不能用 Buildings 局部通过代表全系统就绪。

直接读取：冻结源码、旧交付 hash、公开原始表/元数据。解析核算：合成国家积分、DH loss、原表内 cooking 比率。推断：默认燃料拆分的误归风险、局地曲线的适用性。待接受方案：新的 final→useful 转换、时序方法、E3及边界选择。没有把后三类写成求解结果。

无正式大模型、无新技术/数据采用、无碳政策调整、无其他部门推进、无远端推送。完成本轮后停止。

## 统计解释检查

本轮没有假设检验或推断统计。11/11 checked：Simpson's paradox（按国/R/S核对，不只看总量）；ecological fallacy（不将国家或样本结果外推个体/全区域）；Berkson's paradox（记录便利样本限制，不估计相关）；collider bias（无回归控制，N/A）；base-rate neglect（无诊断概率，N/A）；regression to the mean（确定性工程输入，非观测干预，N/A）；survivorship bias（保留失败、访问失败及样本排除限制）；look-elsewhere effect（完整断言记录，无显著性筛选）；garden of forking paths（夹具修正有记录、版本固定）；correlation/causation（来源/工程回归不作为政策因果效应）；reverse causality（不作方向性社会因果推断）。断言数不当独立样本，不提供不存在的p值或置信区间。
