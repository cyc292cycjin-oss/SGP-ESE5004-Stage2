# 下一阶段就绪性与A–F回答

**目前不能冻结Full-SC可执行实验设计，也不能启动Integrated/Disconnected正式研究求解。** 可以继续已有方向下的边界讨论、来源家族验收和单元/守恒验证。

| 用户问题 | 回答 |
|---|---|
| A Paper SHA真正可运行？ | 尚未证明。源码解析/DAG部分展开成功，但原始输入未齐且作者input身份不完整；正式reference未求解 |
| B 官方SC baseline冻结？ | 官方源码、branch、完整SHA `a3616a68ee44592af6527ca9024a90f1956646ae`已冻结；“可信Full-SC物理/数据基准”未冻结 |
| C 哪些fix通过？ | GDP缓存重建/十国基年工业分配守恒；碳配置键/六年轨迹/时间权重兼容；另有碳范围与manifest单元测试。均不等同于完整模型通过 |
| D sector/data blockers？ | TL工业、增长/工艺、热/住户/服务与交通需求、共享资源/commodity及key costs；final电力裁剪/缩放；拓扑损失 |
| E 能冻结Integrated SC vs Disconnected SC设计？ | 干预概念已冻结为跨境AC/DC电力；可执行配置与数据/碳边界尚未冻结，故否 |
| F 最少剩余blockers？ | 以下五项 |

## 最少五项闭合条件

1. **正式参考输入/环境身份**：取回并核对完整气象、土地覆盖等原始输入；接收作者input manifest或明确“可重建但非字节级同一”的复现标准；完成2025单一reference及正式solver资格验证。
2. **Full-SC服务需求边界**：解决TL工业缺项（提供可信资料或共同决定并明确标记范围处理）；确认增长/工艺、热住户服务需求不重复、交通/航运/航空及现有能力来源。不填假设零。
3. **Power-sector碳等价表达**：专属排放账/约束与SMR、CHP、共享燃料、capture信用归属；Baseline/DEC均保留，预算值不改，不扩为社会全部门限额。
4. **网络与终端需求守恒**：作者对766删除的后续意图/可信修正网络；验证765负荷/容量保留、连通性、正式分辨率。同时对final_adjustment需求缩放/载能名称和取消电力裁剪后的需求总账做回归。
5. **来源家族验收与研究边界表**：冻结成本/手工覆盖/燃料口径、共享生物质等资源与外部commodity边界；对新上游已有ammonia/H2 turbine能力明确是否纳入；Integrated/Disconnected除跨境AC/DC外相同。

## 已经不需要用户重新找的材料

- 官方SC/论文完整SHA、代码历史与作者有效配置。
- 旧DEA sheet86和technology-data v0.13.2 SHA、manual override处理链。
- 原全球GDP、十国工业基年量、设施/空间分配失败机制；正确缓存与守恒修复已形成。
- 旧/新碳键与错误限额来源；独立修复及测试。
- bus766旧坐标、国家/电压及0.1.1明确删除记录；缺的是删除后的网络意图。
- 官方全年亚洲气象包入口、文件清单与可下载性；缺的是完整取回/作者字节对应。

## 真正需要用户资料或共同决定的事项

原始资料：若已有作者完整input manifest/全年输入/环境运行记录，可缩短核验；TL工业原始分项；bus766修改意图或作者修正版本。用户无需再重找已恢复DEA旧表。private communications拿不到时遵从用户要求保留作者电解值、SOURCE_PARTIALLY_VERIFIED。

共同决定：来源家族接受；TL数据不足的透明研究范围处理；工业增长；热/服务定义；共享资源与commodity供应；电力碳账中联合技术归属；复现误差/残差容差。它们不是可以由Codex“补齐”的数字。

已经决定、无须再问：先Integrated vs Disconnected（单一区域模型），只变跨境AC/DC；Baseline和DEC都保留；standalone靠后；不做博弈、延迟、新技术研究或新碳政策。本轮没有正式科学求解，没有CONFIRMED数据条目，没有采用DEA2026。
