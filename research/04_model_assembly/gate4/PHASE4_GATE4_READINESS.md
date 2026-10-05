# Gate4 — 水电实际接入与物理/政策资格分离

**FULLSC_NETWORK_NOT_COMPLETE；Gate5=NO；solver_runs=0。**

本轮在90b82d6b基准上实施新决定`GATE4-20261005-HYDRO-PHYSICAL-POLICY-SEPARATION`。已批准寿命、映射、增长、EV embedded、bunker、MY/TH去重、铁路/NEC方法均保留。

|技术|本轮实际新增MW|仍未接入MW|
|---|---:|---:|
|水库|38,552|797|
|径流式|5,944|657|
|抽蓄|2,686|0|

实际新增水电47,182 MW、197个源机组，形成58个资源组件；连同536个火电源机组139,404 MW，总接入733个源机组、186,586 MW。水库37组、径流式18组、抽蓄3组。未接入16个机组/1,454 MW保持显式待决，没有丢弃或分配到其他节点。

152项合格目标、实际数组和1,436个开发Load保持。原133项以及后来MY/TH与铁路/NEC成果未改；registry和152组数组hash与前轮相同。火电输入组件逐字段比较保持，105条线路和438个可再生候选容量上限保持。

物理报告与政策归属现有独立资格。实际碳映射1,595项物理组件通过端口与系数核对；其中200项SMR/SMR-CC政策权重仍为null。政策关闭时不安装约束；启用政策时任何待决归属明确失败。**这不表示生物商品未知物理碳或全系统排放已经合格。**

六类已物化生物商品通过固定量/独占用途检查：Bagasse、Biodiesel、Biogases、Biogasoline、Charcoal、Fuelwood。若采用时间不变单位供给价，它们的供给成本仅形成固定项；该数学结论不是未知价格或排放系数为零。Animal waste尚未物化，不能套用已建网络的证明。外置待核账方案只供审阅，本轮未放行完整出口。

成本链核验发现汇率和单位已转换，但不同真实价格年份没有统一：EUR2020与EUR2023参数并存。未二次通胀，未换成本。正式成本比较/求解前需统一基年及来源化平减方法。

20项新测试与111项相关回归通过，共131项。实际资源组输入、能量、效率、源机组容量、原成果保留、NetCDF回读及真实配方单次绑定已核验。新修复了权重列重排造成的误拒绝；真实权重变化仍拒绝。完整Research Full-SC未导出，两份NetCDF均仍为开发资产。

## 最少剩余水电原件范围

这些组没有唯一同节点参考输入，未使用跨节点兜底；需要相容的全年输入及原资产覆盖，或另行明确组归属。不需要逐台实测。

|国家|已有100节点|类型|待决MW|
|---|---|---|---:|
|ID|ID_Java-Bali1 0|Run-Of-River|47|
|ID|ID_Kalimantan4 8|Reservoir|110|
|ID|ID_Sulawesi0 0|Reservoir|90|
|ID|ID_Sumatra3 1|Run-Of-River|57|
|LA|LA2 0|Reservoir|70|
|MM|MM2 13|Run-Of-River|66|
|MM|MM2 7|Reservoir|54|
|MY|MY_Peninsular2 0|Run-Of-River|54|
|PH|PH_Mindanao6 0|Reservoir|213|
|PH|PH_Mindanao6 0|Run-Of-River|304|
|PH|PH_Mindanao6 1|Reservoir|260|
|VN|VN2 5|Run-Of-River|129|

此外，库存缺年份/父项容量差异、10项memo、33项来源覆盖/51项物理账户、生物商品与统一真实价格年份仍待闭合。SMR政策归属单列为关闭政策时不阻断物理报告的事项；没有批准新政策份额。
