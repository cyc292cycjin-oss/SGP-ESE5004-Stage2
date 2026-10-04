# 第一版Transport最低可辩护基准

日期：2026-10-03。研究问题为ASEAN renewable energy transition under sector coupling。第一版比较给定同一运输能源义务时，区域互联如何改变供给、转换、储能和投资。它不优化车辆购买、船舶或飞机选择，也不推断消费者福利。

## 已冻结的表示

| 对象 | 第一版表示 | 明确不代表 |
|---|---|---|
| Road aggregate / EV | 显式外生最终能耗账；EV为固定充电电量 | 车辆购买或交通服务优化 |
| Road residual fuel | 固定分载体燃料义务，含油/气/生物燃料身份 | 把所有剩余能量改成化石油 |
| Rail电与燃料 | EMBEDDED，父账户各保留一次后取消独立重复项 | 关闭rail后需求和排放自动消失 |
| 国内shipping / aviation | 两个固定终端燃料账户 | 新建船型/机型竞争 |
| 国际marine / aviation bunkers | 两个独立固定bunker账户，保留报告国 | 普通国内最终消费、航线或船旗责任分配 |
| FT / synthetic fuel | 已有显式供给选项；H2、CO2和AC平衡内生 | 新增同服务H2/电力需求 |
| Road FCEV、EV DSM/V2G、直接marine H2、marine NH3/methanol | DEFERRED | 首版不可缺少的技术 |

这些为**本轮用户决定**，不是数据已获接受的结论。A*继续表示终端电力父账户；AEO8 generation仅作paper comparator，AEO8 final electricity仅作一致性benchmark。

## 最小物理闭合

1. 每国每目标年：`RoadParent = EVFinalElectricity + Σ ResidualRoadFuel_k`，统一final-energy单位、计量端及年份。EV energy share与该年parent共同定义，不沿用未证实的车辆share。
2. 历史EV若已在A*中，先移出同一量、再显式加入一次；未来direct账剔除同一未来EV服务，不能保留其增长后再加整份EV。Rail保持父账户内，不能另加同一Load。
3. 四个shipping/aviation账户各自保持source/year/country/commodity/单位/国内国际身份；共享油Bus不消除账户ID。
4. 终端燃料需求固定，化石油与既有FT供给可竞争。FT和制氢用电由Link流量产生，不预装在A*。
5. PolicyCO2_Power沿用原电力范围与1000→100 Mt轨迹；完整物理报告账含交通。供EV/FT的发电排放仍属power。两种账是同一碳流的视图，不能相加。
6. 国家→节点→时段分配需年度守恒、无非有限值。缺失不能补0。有效权重须有明确来源/版本，按国归一；不能重新归一非法数据来掩盖丢量。

详见对应会计文档和 `TRANSPORT_FIRST_FULLSC_BOUNDARY.csv`。相同输入/计量端/权重必须用于未来Integrated与Disconnected，区域网络规则另属全模型边界，不在本轮求解。

## 本轮完成与实际限制

**完成：** 能量规范、exactly-once契约、四类燃料账户、碳双账契约、17项独立shipping工程回归、44项缓存国别燃料账户重新分类。源码/缓存/推导/拟议实现分别标注。

**仍未完成：** 接受全部年度输入，替换road错误链，实际父子电/燃料账转移，真实11国网络守恒，power碳范围分离。没有把规范推导冒充真实模型验证。

现有港口测试证明候选修复的计量与索引行为，不证明GIS、paper输入版本或完整研究网络正确。国内导航原始`in`行被`by`筛选遗漏的证据已单列；本轮未修数。

Transport topic可关闭并交给Human Scientific Review；进入可执行Full-SC assembly仍有三个系统门槛，见[最终收口](TRANSPORT_PHASE3_CLOSEOUT.md)。
