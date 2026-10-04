# Research 电力概念边界冻结

决定编号：`HDEC-P3A7-ELEC-001`。日期：2026-10-02（Asia/Shanghai）。权威来源：用户本轮 Phase3A-7 指令第1–2节，原文与SHA见 `evidence/USER_PHASE3A7_REQUEST.txt`、`evidence/INPUT_MANIFEST.json`。**状态：HUMAN_FROZEN_CONCEPT。** 此处记录已经作出的人类研究决定，不把它重新降回待选候选。

## 已冻结的定义

**A* = 最终用户电力消费父账户，在明确表示的历史电热用途转入热服务账户之前计量。** 它不是发电量，也不是已扣电热后的direct electricity。通用输配损耗不自动预加到A*；显式建模的损耗由相应网络物理关系表示。当前generic 0.97 treatment为 **NOT SCIENTIFICALLY ACCEPTED**，本轮不修改、替换或取消该参数。

未来显式转换技术的电输入——HP、阻热、EV充电、电解以及其他转换——由部门耦合优化生成，不预加到固定direct Load。若某个服务在首基准被声明为embedded，则其原能耗仍属于固定direct账户，且不能同时生成该服务的显式转换需求。固定嵌入是建模范围选择，不是已经表示了该用途的未来技术替代。

## AEO角色锁定

| 来源 | Research角色 | 禁止的自动操作 |
|---|---|---|
| AEO8 C.5 generation轨迹 | `PAPER_REFERENCE / COMPARATOR` | 自动作为Research Full-SC最终用户Load或对其做总量强制校准 |
| AEO8 C.2 reported final-electricity轨迹 | `CONSISTENCY / VALIDATION BENCHMARK` | 在部门重叠未厘清前自动成为direct electricity输入或硬约束 |
| DemandCast/GEGIS原始曲线 | 来源及形状候选，保留原身份 | 因变量名/网络位置就认定已经是共同final-meter总量 |

以上角色来自人类决定；支持证据复用 Phase3A6 的 `AEO8_ELECTRICITY_SOURCE_TRACE.md`、`ASEAN_ELECTRICITY_BOUNDARY_TRACE.md` 和损耗审计。本轮没有寻找新版数据，也没有数值替换。

## 保留E3契约，按实际显式范围应用

在共同国家、年份、计量点和时间网格上，`A*=O+T_R+T_S`。令 `X_R,X_S` 为**实际获准显式表示**的历史space/water用途集合，`h_R^X,h_S^X` 是这些用途在同一父账户中已包含的历史电输入。于是：

`B=T_R−h_R^X`，`C=T_S−h_S^X`，`D_accepted=O+B+C=A*−h_R^X−h_S^X`。

必须有 `D_accepted+h_R^X+h_S^X=A*`，历史电热恰好转移一次。新增非电燃料热服务时，对应原direct fuel也须一次性互斥转移，不能保留全量燃料再为同一服务增加一份输入。

若显式集合为空，转移操作为空，direct账户保留其父能量。这是**未执行热用途扣除**，并非测量得到 `historical heating=0`。原观测缺失字段仍UNKNOWN。没有原始总量/包含关系的证据，也不能仅凭空集合就宣布真实网络已经数值闭合。

此限定沿用 Phase3A4 中“excluding explicit space/water”的契约，没有解除共同边界、不得造残差、不得clip等要求。`O`需要真实分区或可解释的未分类原能量，不是为平衡添加的correction。

## 冻结范围与尚未冻结的内容

| 已冻结 | 未由本指令自动接受 |
|---|---|
| A*概念计量点、AEO角色、损耗原则、显式转换不可预加 | 任何国家的A*、R/S、直接燃料、历史电热或useful服务数值 |
| 证据不足保留embedded、missing不等于零/虚构服务 | 2016→2019、半岛→全国、ASEAN10→11/TL的数值映射 |
| R/S分开；cooling固定嵌入；cooking只会计；不自动DH/stock | 全国热设备性能、spatial/temporal profile或模型默认份额 |
| 不再要求通用11国E3才能推进研究 | 已经运行/接线成功的Full-SC模型，或正式比较的科学数据验收 |

本文件取代Phase3A6“候选A*尚未选择”的**当前决策状态**；不改写旧阶段报告或数据历史，也不把旧source PENDING改成CONFIRMED。

模型身份保持：P `5bacad702ccfed17ad19ab510fa710651e966f2c`；U/R `a3616a68ee44592af6527ca9024a90f1956646ae`；V `50a73d8f531132c5459174a55cac412d5f684462`。将来变更本概念边界需新的明确人类决定及影响说明，不能由配置继承隐式漂移。
