# Rail：固定终端能耗，非内生铁路系统

**Rail有显式electricity/oil Load构造；作者最终网络保留电铁路，删除油铁路。** 没有铁路网、客货服务、列车技术选择、铁路扩容或内生电气化。

`U/scripts/build_base_energy_totals.py:246–260`的total rail只加Diesel/Biodiesel/Electricity；electricity rail为其电力子项。UNSD原单位转换后为TWh。`Snakefile:1670–1706`经prepare_heat_data输出人口加权nodal_energy_totals，再由`prepare_sector_network.py:3696–3739`建平坦负荷：电=E_e×10^6/8760；油=(E_total−E_e)×10^6/8760。空间按人口节点，不是实际轨道或牵引变电站。

Rail电力属于最终用户A*的子项，但当前实际父Load的来源/变换尚未证明含有多少。此构造器没有从父Load扣除；另一处land需求中的`−electricity rail`并不是该扣除。非电rail同时进入land aggregate，若两模块都保留，会产生重复路径。不能将缺失rail原记录被填0解释为国家无铁路能耗。

作者选定2025/2050输出各98电铁路Load，加权5.111434/12.857958 TWh；教程2030前后各48电铁路Load、6.147076 TWh，裁剪前另有48油铁路Load、11.755899 TWh。教程是代表时段加权结果，不能作为国家统计验证。来源：`NETWORK_TRANSPORT_EVIDENCE.json`。

首基准候选为 **EMBEDDED或FIXED，二选一并互斥转移**。这里没有证据证明铁路在全部国家都“小到可忽略”；候选依据是当前需求固定、尚无需要内生化线路/车队的已确立问题。保留总电/燃料数量、地域和正确账户比精确列车类型更重要。独立固定rail可提高可追踪性，但不得为结构完整就额外添加一份用电。油铁路排放路径还需与共同CO₂账核对，见碳审计。

铁路网/车辆/时刻表细化暂列后续限制；只有具体峰值、区位或电气化证据显示影响跨国投资/网流时局部重开。不改变rail开关或输入。
