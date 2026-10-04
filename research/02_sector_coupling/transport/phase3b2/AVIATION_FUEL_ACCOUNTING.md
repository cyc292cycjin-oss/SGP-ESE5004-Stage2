# Aviation：国内与国际bunker分别核算

`DomesticAviationFuel[c,y,k]`与`InternationalAviationBunker[c,y,k]`为两个固定终端燃料义务，保留统计报告国，不推断航线、旅客或航空公司责任。首版没有aircraft competition；已有FT可为共用油品供应路径，需保留其合成燃料质量/用途聚合限制。

## 当前数据的实际含义

U `build_base_energy_totals.py:262–275`选择Kerosene-type Jet Fuel及`Consumption by domestic aviation`/`International aviation bunkers`两类交易。当前保留数据为2019；经原单位换算到TWh/year。UNdata导出日期、文件hash、行号、quantity/footnote见[evidence/COUNTRY_ACCOUNT_OBSERVATIONS.json](evidence/COUNTRY_ACCOUNT_OBSERVATIONS.json)。

国内航空是国内消费子项，但其是否已被研究direct-fuel父账户包含须逐账证明；国际bunker单列，不自动塞进普通国家final energy。两者与shipping四账户不可互相抵消或混入电力A*。

当前kerosene过滤**不是所有航空燃料**。证据池还有少量Aviation gasoline的国内/国际消费，另有Imports/Exports/stock等非终端交易；不能把关键词匹配池都加成需求。首版可明确采用kerosene范围，把小额其他航空油品作为范围限制；不得声称已覆盖全部燃料。无需为这些小额项目重开机型研究。

11国缓存四账完整列表见[源复核](evidence/ACCOUNT_SOURCE_REVIEW.md)。BN、SG、TL国内aviation的缓存零没有对应exact row，不能冒充经观测确认的零。未来DEFAULT增长/效率不是已接受预测。数据/单位/热值和年份仍保持UNVERIFIED/PENDING。

## 最小供需与分配合同

- 固定义务可由化石油或已存在FT供给满足，不能在终端fuel Load之外再附加同服务H2 Load或预计算制燃料电量。
- 节点优先现有airports，size权重属于空间代理；本轮缓存11国fraction各和为1，不能据此宣布真实网络country/year已守恒。若采用透明country节点权重也可，但需共同接受且守恒。
- 原U `add_aviation:1546–1630`先合并国内/国际、以TWh×10^6/8760生成静态MW。首版保留两个账户ID，允许共用物理供给Bus；不混淆“共享供给”与“重复需求”。
- 年度义务按明确snapshot物理权重分配；不能假定平坦终端fuel意味着电解/FT电力也平坦。具体峰值、储能和成本可能受时序影响，作为基准限制记录。
- 国内/国际燃烧分别入FullSystem，原Power cap范围不随恢复aviation扩张。FT、电解所需发电仍受Power cap；carbon循环按实际来源/再排核对。

本轮未实施aviation候选补丁、未生成新Load、未运行求解。缓存pre-strip的45正/3零有限Load只是旧网络观察，不是新规范实证验收。
