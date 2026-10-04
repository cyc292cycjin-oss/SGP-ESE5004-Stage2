# Agriculture首版边界

**冻结：农业电力EMBEDDED于A*，农业燃料按carrier FIXED并保留一次；不建农业技术模型。** 依据是当前表示机制和研究范围，不是凭猜测宣称农业规模小。

## 直接源码与数据证据

U `build_base_energy_totals.py:224–243`从UNSD基年交易汇总农业electricity/oil/biomass/coal最终能耗，单位转换为TWh/year；不含作物产量、灌溉服务、机械小时或useful heat。`prepare_energy_totals.py`使用growth/efficiency CAGR，当前ASEAN无专属行而回退DEFAULT；`prepare_heat_data.py:149–160`按人口权重分到节点。位于heat目录不表示其为热服务。

U `add_agriculture:3142–3199`只建固定电Load、固定oil Load及oil排放；无农业设备、H2终端或内生用能替代。当前CSV却另有biomass/coal，不能因构造器未消费或关sector开关而丢掉。

已保留2019非空缓存小计：电11.1532、油79.6796、生物质4.4466、煤0.2152 TWh。BN/SG/TL全缺，**这些不是完整ASEAN总量，也不是已接受模型输入**。原文本、4年176条观测与hash见 `evidence/AGRICULTURE_OBSERVATIONS.json`。VN正煤在未来因缺CAGR列及fillna(0)变零，不是煤退出情景证据。

## 保量与耦合

| 项目 | 首版处理 |
|---|---|
| 农业电力 | 完整A*中保留一次；不重复新建农业电Load。若命名子账户，必须作等量父账转移。 |
| 油/生物质/煤等燃料 | 保留接受的分载体固定义务或经证明包含的direct-fuel子账；不全部改成oil。 |
| 缺失子账户 | 已有可靠完整父账则保留其中、子份额未知；没有父账也不造零或新量，留共同输入范围记录。 |
| 供给替代 | 固定油需求可通过既有FT供应间接引起H2/电力需求；这是供给耦合，不是农业技术模型。 |
| 碳 | 直接燃烧进入FullSystem报告，供电发电留Power policy；不自动扩张原Power cap。 |
| 时间/空间 | 透明人口/既有节点权重与简单年度分配，逐国年度守恒；两情景相同。 |

农业已知燃料量及国家分布有影响燃料成本、FT/H2和电力供给的可信路径，所以应保留其能源义务。没有证据要求EXPLICIT农业设备优化；无需machinery/crop/irrigation分类。输入/增长、父账重复、未消费载体及碳scope由共同Phase4门槛处理，不另开农业深挖。

Framework enable、tutorial最终只留电Load与Research边界是三件事；旧教程统计不是本轮重新求解。来源和细节见 `evidence/AGRICULTURE_REVIEW.md`。
