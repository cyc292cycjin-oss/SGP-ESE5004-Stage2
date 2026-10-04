# Transport空间与时序最小规范

| 对象 | 空间 | 时间 | 最小成立条件 |
|---|---|---|---|
| Road EV / fuel | 国家→现有节点，透明且被接受的权重 | EV简单外生曲线；fuel简单年度分配 | 同一country/year/载体总量守恒 |
| Rail | 随direct parent分配，保留rail子标签 | 随相应父账户 | 不另生成相同义务的rail Load |
| Shipping国内/国际 | 优先ports/coastal；无可用点不暗补 | 固定年fuel加简单归一形状 | 国内/国际分别守恒；缺值报错 |
| Aviation国内/国际 | 优先airports；透明country分配亦可 | 同上 | 两账户与节点索引无静默丢量 |
| FT / H2生产 | 按已有合法供给/网络可达节点 | 内生调度与现有储能约束 | 不能把终端fuel的简单形状当制燃料电力形状 |

全国年量E[MWh]、节点权重a_n、非负时间形状q_t、代表小时w_t：`P_nt = E a_n q_t / Σ(w q)`，且Σa=1。按Load物理时间权重检查Σ_n,t w_t P_nt=E；目标函数权重与物理小时若不同须分别记录。多期模型应逐规划年/period核对，不能用全period权重总和一并年化。

旧TWh×10^6/8760静态MW只有在代表全年8760小时的使用条件下对应全年总量。候选shipping保留旧年化不改变时间模型；Phase4须验证实际snapshot权重，不能同时套两次年度缩放。

## 当前通过的有限证据

1. 缓存ports：10个有记录ASEAN国家的fraction有限、非负、各和1；LA无记录。airports：11国fraction各和1。[支持复核](evidence/ACCOUNT_SOURCE_REVIEW.md)。
2. 独立shipping候选在明示GIS夹具下，重复港口到同节点不会丢量，零港口节点的结构零与源缺失区分，国家/国内/国际各项守恒；非法权重、跨国或未知节点、正需求无港口均失败。
3. 旧真实pre-strip shipping oil 39/48非有限值仍是旧网络事实；本轮未重新构建或修写这个网络。航空旧有限Load亦不是本轮11国新组装通过。

因此不能给真实全ASEAN国家年度守恒PASS。待接受源账与实际节点映射后，在Phase4作静态组装验收，无须正式Integrated/Disconnected求解。

## 不再阻塞的精细度

不细分客货/车辆/charger、船型/航线、机型/航班；不优化DSM/V2G；港口/机场size或country透明权重是首版代理。简单时序须在两种区域网络情形共同使用并披露。年度量相同**不能证明**峰值、燃料储能、合成燃料成本和互联收益对形状完全不敏感；这是限制，非本轮新增敏感性实验。
