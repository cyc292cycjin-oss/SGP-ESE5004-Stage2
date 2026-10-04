# Cooling accounting trace

版本与 F/U/T/P 定义见 [README](README.md)。**已证实没有独立建筑 cooling service 模块；不能从总电力负荷反推出经验证的 cooling 年度量。**

## 当前到底在哪里

| 层 | 电力入口 | Cooling 的证据边界 |
|---|---|---|
| F | base electricity profile；UNSD households/services electricity；随后重标定 | 都是 aggregate electricity，不按 lighting/appliance/cooling 等 end use 列账；没有明确剥离 cooling 的代码 |
| U | `load_options.source=demcast`，DemandCast → base profile；居民模块覆盖 AC Load 年度量，再加 services electricity，final adjustment 重标定 | 最终曲线形状/总量经过多次处理，不能直接等同原 DemandCast；没有 cold service 技术选择 |
| T | 既有教程 profile/network；metadata 只保留部分配置，load_options 未在本轮抽取的 meta 中保存 | 保留总体 electricity 负荷，最终 only-electric；不声称已识别多少空调电力 |
| P | 作者 metadata：GEGIS/SSP 路径，2013 weather、2030 prediction；LA/TL 有替代 profile 与缩放 | paper 最终 electricity case 不能验证独立 cooling 服务；不把 U 的 DemandCast 倒写为 paper 输入 |

[DemandCast 原论文](https://arxiv.org/abs/2510.08000)描述总电力需求预测，结合历史需求、天气及社会经济变量；没有由此提供本仓库可使用的建筑 cooling end-use 分解。**推断**：有空调消费的总电力统计通常会承载该消费的影响，且冻结代码没有专门减去 cooling。因此当前 cooling 最多隐含在固定 aggregate electricity 中。**未证实**：11 国各自 cooling 的数量、温度响应及是否完整覆盖；也不能把数据集的“温度相关性”等同于物理 cooling service 模型。

## 组件与开关逐项核查

| 查询 | F/U 固定源码结果 | T/P 最终网络含义 |
|---|---|---|
| cooling Bus / Load | Buildings 路径没有 | 不存在可据此主张的独立 cooling case |
| electric chiller | 没有建筑 chiller 组件/开关 | 无相关优化选择 |
| reversible HP / heat-pump cooling | `add_heat` 的 Link electricity→heat 为单向供热；COP按 source→55°C | 不能把 heat pump 名称解释为可制冷 |
| district cooling | 没有；district heating 参数仅生成 heat demand | 不可借 DH=0.3 推算冷网潜力 |
| cold/ice storage | 没有；TES 是 hot-water heat storage | 不可算制冷灵活性 |
| residential/services 重生成 cooling | 没有显式 cooling 分支；新增的是 aggregate electricity/fuel Loads | services electricity 是否被最终裁剪见下一段 |

依据：[全冻结源码关键词核查](history/COOLING_CODE_SEARCH.txt)、[add_heat / add_residential / add_services](source_snapshot/upstream/scripts/prepare_sector_network.py)、[heat preparation](source_snapshot/upstream/scripts/prepare_heat_data.py)。检索命中的交通 cooling 不属于建筑，本轮不展开。

## 重复计数判断

1. **不能声称已发现“base cooling + explicit cooling Load”的实际重复**：后一个 Load 不存在。
2. **也不能据此宣告 Buildings electricity 无重复**：服务业新增 Load、居民 AC 覆盖、final national electricity 重标定、已有电热与内生热转换之间没有统一的 end-use 守恒表。[A–J audit](BUILDINGS_ELECTRICITY_DOUBLE_COUNT_AUDIT.md)
3. U `only_elec_network=true` 的保留列表写 `service electricity`，实际组件叫 `services electricity`，故服务电力被裁剪；而 AC 后续被重标定为总体电力的一部分。这会掩盖分部门核算问题，不是精确扣除了 cooling。
4. **未来若仅关闭 final electricity-only 裁剪而保留全部服务负荷**，final adjustment 仍运行，且其 `elec_carrier` 不含 services electricity。这样 aggregate total 校准部分再加服务电力，会失去一致的总体边界；重叠量需以独立的总量/分部门账核定，不能本轮凭猜测给出数值。

## 本轮状态与需要的决定

- 独立 cooling 代码不存在：SOURCE_RECOVERED。
- “隐含在固定电力负荷中”：有源码支持的边界解释；分量大小仍 ASEAN_VALIDATION_PENDING。
- 当前不新增 cooling 模块，也不从总负荷里扣一个假定空调比例。
- 用户已冻结的 heat-service 原则仍保留；**cooling 暂按嵌入直接电力处理，还是未来单独可替代冷服务**属于待共同决定的科学边界。只有后者需要冷量、设备效率、负荷曲线、存量与从电力基线扣减的独立证据。
