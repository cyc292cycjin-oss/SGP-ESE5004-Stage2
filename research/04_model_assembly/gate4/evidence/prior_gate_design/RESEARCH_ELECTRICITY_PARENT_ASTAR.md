# Research electricity parent A*

**实现：PARTIAL（会计接口已实现、11 国基年候选已恢复，尚无数值接受）。**

直接从现有 UNSD 文件读取 2019 年 `Electricity - Final energy consumption`。不是 Gross demand、Gross/Net production、AEO8 generation 或 DemandCast。

源文件：`/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/demand/unsd/data/UNdata_Export_20250502_110820872.txt`。
SHA256：`12c99b3c40927449d9a4d0402f255a8b84b24917ff58e54efd4ec43b2125fe6b`。
原单位 million kWh，×1000→MWh；不乘 .97，不做 AEO 标定或未接受的损耗调整。

| Country | 原始 million kWh | 候选 MWh/year |
|---|---:|---:|
| BN | 3906.135 | 3,906,135.000000 |
| ID | 258092 | 258,092,000.000000 |
| KH | 10191.09 | 10,191,090.000000 |
| LA | 6595.54 | 6,595,540.000000 |
| MM | 18681.01 | 18,681,010.000000 |
| MY | 158709.264 | 158,709,264.000000 |
| PH | 87118.3 | 87,118,300.000000 |
| SG | 51730.2 | 51,730,200.000000 |
| TH | 193175.999 | 193,175,999.000000 |
| TL | 384.247 | 384,247.000000 |
| VN | 207048.888888889 | 207,048,888.888889 |

以上均为 `PENDING / NumericAccepted=false`。统计标签支持 final-consumption 边界；不额外宣称逐国原始调查的所有 meter/自备电定义已审定。11 国覆盖不等于所有部门拆分覆盖。

75 条精确原始记录（含父账及相关部门）固定于 `research_inputs/demand/sources/electricity.json`；原文件行号、单位、字符串数值与哈希可追溯。R/S/I/transport/agriculture 拆分只作 embedded 身份/参考；不通过相减伪造 O 残差 Load。`BUILD_REPORT.json` 保留可用部门和父账的独立诊断，差额不自动修正。

A* 唯一 owner；接受某显式历史电力子账后，`apply_astar_transfers` 批量执行一次 ParentBefore/TransferredChild/ParentAfter/IndependentReference，要求数值与包含关系均被接受。伪造 transfer flag、超额、重复、父账未扣减均失败。当前没有执行任何真实转移；TransferredChild=0 仅表示无转移事务，不表示历史 EV/热需求为零。

2030/2040/2050：`FUTURE_DIRECT_ELECTRICITY_PENDING`。`electric_evolution` 无 accepted factor 或无法确认排除未来转换电则报错。future EV 以外生 final-energy share 形成独立义务，不能同时藏在未来 direct A*；HP/electrolysis/FT/resistive 的电输入为 endogenous contract。

Research 配置与 `check_research_demand.py` 禁止 AEO8 generation target 和 legacy demand builders。AEO8 final electricity 只声明 validation role，本轮没有捏造或读入新的 benchmark 数值。上游原函数仍保留以供追溯；Gate2 不调用它们，也尚未把需求层接到完整网络。
