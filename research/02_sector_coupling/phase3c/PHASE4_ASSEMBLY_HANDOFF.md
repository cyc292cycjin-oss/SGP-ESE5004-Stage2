# Phase4 — Full-SC Assembly & Validation交接

**这是执行计划，不是本轮启动指令。** Phase3设计已关闭，下一阶段可进入独立组装验证；首次正式求解尚未就绪。先完成用户＋ChatGPT最后一次Phase3科学复核。

## 模型身份与已保存候选

| 对象 | SHA / 状态 | Phase4使用方式 |
|---|---|---|
| Paper P | 5bacad702ccfed17ad19ab510fa710651e966f2c | 只作参考/退化等价性证据 |
| Frozen U | a3616a68ee44592af6527ca9024a90f1956646ae | 不追main；组装分支明确基点 |
| Buildings validation V | 50a73d8f531132c5459174a55cac412d5f684462 | 已有验证与候选，检查适用于本轮嵌入规则的部分，非自动整层合并 |
| Industrial GDP candidate | a7a8f06b43f0dcce0dbd7005b989d8f73d142b81 | 已有10国2019/48节点守恒，不重跑同一诊断；新真实组装分辨率需验收 |
| Carbon key candidate | 753ac81c23f8b9a1ca8ceed531d0630b56f6953d | 保原六年数值；另实施scope隔离，不能以key修复替代 |
| Shipping完整候选 | 85a32dc231458fd753445df38d422b78435b8aad | 2项功能修复＋字节保真，17项离线PASS；评审集成后核对实际11国节点/时段 |
| Future Research Model | 当前仍U身份，未组装 | 不称已经包含以上候选；新合并/配置须有清楚commit与manifest |

## 推荐工作顺序与退出条件

1. **接受最小输入接口（P4-01/03）**：同country/year/空间域的final A*、R/S/direct fuel、road energy-share、四燃料义务、工业年度/growth、资源/供给价与上限。仅确认实际消费的输入族；未参与首版技术的参数不成为门槛。TL工业用不显式构建＋父账保留规则，未知量不设0。服务块无合格证据就fixed，不新增过程研究。
2. **实现表示控制（P4-02/03/04）**：R/S分开、Buildings thermal既定嵌入、road新最终能耗式与固定EV曲线、rail嵌入、四类fuel独立账、工业/农业实际载体保量。同步需求生成与组件开关，尤其NH3缓存扣量；父子转移逐笔有ID和来源。消除旧AC覆盖、AEO generation重标与无依据0.97消费；不是只设置only_elec_network=false。
3. **接通合法供给并隔离国家物理载体（P4-05）**：H2/FT/热辅助/CO2来源有成本且可达；无新技术。跨国H2/gas/CO2/NH3/methanol off，所有fuel/CO2/biomass/process物理池无隐含跨国转移。全局大气仅记账。外部commodity单向、双方参数一致。
4. **Power与全系统碳两视图（P4-06）**：在项目层实现可追溯线性表达式/ledger，保原轨迹、paper供电链和信用；rail、工业煤/原料、农业、bunker报告完整。CHP/共享H2/碳信用实际映射需人审，不能随意比例分摊。
5. **拓扑、唯一干预和守恒（P4-07/08）**：核对既知bus765/766等版本问题的合法处理，不能仅消除警告；AC/DC跨国边清单、国内边保护、无KVL残余通道。逐国/载体/时段需求、资源、转换与碳保真，candidate组件未被白名单错误裁剪。两组输入差异只在允许的电力边干预。
6. **有界可行性与可复现性（P4-09）**：授权进入Phase4后先静态/小范围组装验证；需要求解的可行性测试须另有明确阶段授权与run manifest。负荷削减可帮助诊断，但不能把未报告的shed当需求已满足，optimal不等于物理/来源正确。未过门槛不跑正式全年对照。

## 必须留下的产物

一个有效配置快照（base＋project override＋合并后配置）、接受输入清单及hash、模型组件/国家端口清单、父子转移台账、跨境边mask与两组差异报告、九项gate结果、工程/数据/研究配置分开提交、环境与solver身份。

正式run manifest沿项目规范记录run_id、git_commit、config_files、input_data_hash、environment、solver、start_time/end_time、objective、solver_status、output_hash；包括snapshot物理与目标权重、cost年化和存量常数口径。当前交付的solver_runs=0，不填虚构objective或optimal状态。

## 不再作为先决条件的项目

完整钢铁/水泥/化工过程、TL工业全量微观数据库、农业机器/作物/灌溉类别、Buildings用途普查、车辆/船/飞机细分、V2G/DSM、marine H2/NH3/methanol、跨境非电基础设施、独立韧性/安全目标、国家收益或合作博弈。具体系统矛盾才进入共同验收，不追加Phase3D。

Disconnected保持同一11国区域政策模型，不预先拆成11个各用完整区域预算的独立问题。未来核心成本差是两个同边界SC系统的成本差；国家分布与政策归因留到正式结果阶段，本轮不开展。
