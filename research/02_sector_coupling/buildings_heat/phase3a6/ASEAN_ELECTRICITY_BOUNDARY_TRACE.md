# ASEAN 电力计量边界追踪

Phase 3A-6 · 2026-10-02 · 只读源码审计及研究侧会计原型。

**直接核实：六个未来 `total_elec_demand` 值逐一等于 AEO8 BAS 发电量，而非其终端电力消费表。** 这是来源与代码的匹配结果，不是本轮求解结果，也不意味着整张网络的最终年负荷恰好等于该目标。当前载荷筛选和后续工业重分配有额外条件。

## 固定模型身份

| 层 | SHA | 本轮含义 |
|---|---|---|
| Paper Reference P | `5bacad702ccfed17ad19ab510fa710651e966f2c` | GEGIS 入口；论文参照，只读 |
| Upstream SC U | `a3616a68ee44592af6527ca9024a90f1956646ae` | DemandCast 入口；框架能力不等于正式 Full-SC 情景 |
| Buildings validation V | `50a73d8f531132c5459174a55cac412d5f684462` | 已接受 E1/E2/E4 工程修正；E3 未实施 |
| Future research model R | 目前仍为 U 的 SHA | 尚未冻结新的科学输入与电力边界 |

本轮重新核查四个工作树均干净。身份见 `evidence/LOSS_CODE_IDENTITY.json`；33 份已有配置/源码快照复用 `../phase3a5/evidence/CODE_IDENTITY.json`。E1/E2/E4 的 1062/1062 测试记录复用 Phase3A4，不重跑，也不当作 E3 数据通过。

## 从来源到网络

| 环节 | 固定代码中的实际动作 | 计量含义及证据 |
|---|---|---|
| P 原始曲线 | GEGIS SSP2-2.6、预测2030、ERA5天气2013；LA用KH、TL用ID替代曲线 | `P/configs/bundle_config.yaml`、`P/scripts/build_demand_profiles.py`。年度来源的各国 gross/net/final 定义未闭合 |
| U/V 原始曲线 | `demcast`读取 `Forecast load (MW)`，以2013 UTC筛选 | `U/scripts/build_demand_profiles.py`。不是把2013天气年等同于2019统计年 |
| DemandCast 年量来源 | 已恢复 v0.9.0 ETL 选 Ember `Demand`/人均需求；模型 bundle指向Zenodo18374352 version1.0.0 | 旧代码tree `fe8454093c776138df78ae59b30db8e3c89ec7fa`；导出parquet与该tree的精确关系仍未证实。Ember现行定义生产+净进口不能追认当时各国为final-meter |
| 预处理/空间 | 国家scale及总量曲线分配，多节点权重 GDP0.6+population0.4 | `build_demand_profiles`。这是总电力分配，不是获批的住宅/服务业用途权重 |
| 写入Load | `add_electricity.attach_load` 将曲线写入 `p_set` | 此时是综合电力，不是纯住宅 |
| R/S 构造 | R按UNSD衍生 `electricity residential` 覆写AC；S另建 `services electricity` 并沿用归一化R形状 | `prepare_sector_network.add_residential/add_services`。未建立有证据的 O 分区；能源总量仍不等于热服务 |
| 热数据 | 构造的 `electric_heat_supply`含未来燃料转电假设；原扣电语句被注释 | `prepare_heat_data.py:177–212`。不得直接取消注释作为历史扣电 |
| 配电 | Link初值效率1；0.97乘AC Load，再移到低压bus；S不经过同样乘法 | `prepare_sector_network.py:3402–3469`。不是已核实的统一ASEAN损耗桥 |
| 未来总量 | 人口×人均用电得到国家权重，再按AEO区域目标归一 | `final_asean_adjustment.include_electricity_growth:175–236`。**发电量作为需求目标在此进入Load缩放** |
| 工业重分配 | 按国家行业份额重新分配被选Load | `redistribute_industrial_load:239–293`。仅在相应Load存在、分母非零和权重一致等条件下守恒 |
| 最终网络/优化 | `only_elec_network: true` 的当前P/U配置会去除部分SC；最终增长仍执行。优化读取网络Load与转换Link | 不能把框架中建过某组件当成论文最终保留该组件。模型物理损耗另见 `ELECTRICITY_LOSS_ACCOUNTING.md` |

本地教程DemandCast parquet SHA `ade3a79fa50602434adcf6bc2954a297cd229165659263089ab073337466ef8c`，11国×8760行；其来源包完整文件为390,009,152 bytes，MD5 `be6b47c118d547fccf22245ec7cd8323`。已有小文件并未被验证成完整包的精确子集。详细原件、版本和代码blob见 Phase3A5 的 `SOURCE_REGISTRY.json`、`LOCAL_DEMANDCAST_METADATA.json`，本轮没有重下完整大包。

## 不可忽略的代码条件

`elec_carrier`实际只有 `AC`、`industry electricity`、`agriculture electricityrail transport electricity`。末项由两个缺逗号的字符串拼接而成；`services electricity`不在该增长列表。V的E4保留Services修正不等于这张增长列表也已修改。本轮只报告。

动态年量使用objective权重，但新曲线用未加权均值归一；静态项使用8760。均匀全年权重下的选中载荷守恒不能推广到不均匀代表时段或截短年。最终验收仍需用已接受的物理snapshot权重逐项核查，不能把变量名或代数目标当成运行闭合。

## 本轮关闭与保留的结论

**已关闭：** AEO六年发电目标原表；六年终端电力Mtoe原表；代码的需求缩放消费点；配电0.97的位置；当前优化器AC损耗默认值。**尚未关闭：** 共同A*统计边界、DemandCast/GEGIS历史各国meter bridge、ASEAN10到11含TL的范围桥、未来各用途电气化的剥离。

解释是源码观察与统计定义的对照；“可能重复”属于条件性推断。本轮未量化任何正式 Full-SC 成本误差。
