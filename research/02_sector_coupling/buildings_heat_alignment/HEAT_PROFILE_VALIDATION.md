# Heat profile：原实现、验证与限制

结论：年度服务量与逐时shape应分离，这个结构可保留；当前shape不能视为ASEAN已验证。E2候选使正需求遇到不可归一化shape时显式失败，**没有为热带节点创造替代曲线**。

## 冻结链与原始来源

U `build_heat_demand.py` → ERA5 cutout → atlite heat_demand日温度阈值；`prepare_heat_data.py` → BDEW24×8模板 → 每节点、每用途归一化 → annual TWh×1e6 → hourly MW。随后网络按3h等分辨率平均，权重求和。

| 核查点 | 已证实 | 状态 |
|---|---|---|
| BDEW年量还是shape | 只定日内/周内shape；年度量来自energy_totals | `ACCEPT_STRUCTURE` |
| 来源 | 与Eur-Sec v0.7.0数值一致；生成该CSV的demandlib版本/建筑类别未恢复 | `ASEAN_VALIDATION_PENDING` |
| HDD | 本地atlite0.4.1默认15°C阈值、constant0；日平均后得到space shape | `ASEAN_VALIDATION_PENDING` |
| water对HDD依赖 | water仅intraday，不乘HDD；原四列都是1，故恒定热水形状 | “不依赖HDD”可继承；恒定shape尚待ASEAN验证 |
| R/S是否共shape | space R/S weekday/weekend不同；water相同常数 | R/S差异确实存在，但无本地校准 |
| 时区 | country_timezones[ISO2][0]，多时区国家未按节点选；天气日平均仍UTC | `ASEAN_VALIDATION_PENDING` |
| 空间权重 | annual按人口分配；weather矩阵`I.T @ diag(I @ pop)`使用区域人口总量，不等价于格点人口加权温度 | `ASEAN_VALIDATION_PENDING`，不把它称为已验证人口加权shape |

精确快照：[build_heat_demand](../buildings_heat/source_snapshot/upstream/scripts/build_heat_demand.py)、[prepare_heat_data](../buildings_heat/source_snapshot/upstream/scripts/prepare_heat_data.py)、[installed atlite source](../buildings_heat/evidence/installed_atlite_convert_heat_demand.py)、[BDEW比较](../buildings_heat/evidence/BDEW_COMPARISON.json)。没有用已安装atlite版本反推作者原始环境版本。

## 已完成教程产物的再检查（没有重跑）

上一轮保存的[ACCOUNTING_VALIDATION](../buildings_heat/evidence/ACCOUNTING_VALIDATION.json)和[热曲线诊断](../buildings_heat/evidence/TUTORIAL_HEAT_PROFILE_DIAGNOSTIC.json)已足够，本轮直接复用：

| T规划年 | R assigned space TWh | R正年量但NaN的TWh | S assigned space TWh | S正年量但NaN的TWh |
|---|---:|---:|---:|---:|
| 2030 | 246.781827 | 232.864522 | 0.079546 | 0.079546 |
| 2040 | 241.927513 | 228.306976 | 0.088773 | 0.088773 |
| 2050 | 237.202494 | 223.870821 | 0.099070 | 0.099070 |

每个年R有41个正年量但全NaN节点、S有2个；这些年量是教程预处理中的默认生成量，不是测得的真实热需求。形状除以0产生NaN，`add_heat.fillna(0)`随后可将它清零。这关闭了故障机制，不验证这些正年量应不应该存在。

六天教程把年度量归一化到选中的六天；不能将这些热曲线作为全年建模的实际负荷水平，或把丢失量当作真实ASEAN缺供能。

## E2候选的失败—通过检查

见[E2原代码结果](evidence/E2_before.json)、[候选结果](evidence/E2_after.json)、[独立patch](patches/E2.patch)。均为真实冻结函数上的合成fixture，无求解。

| 合成输入 | 原代码 | 候选要求/结果 |
|---|---|---|
| positive annual=6、HDD shape=0 | NaN（无显式失败） | ValueError包含用途、节点；通过 |
| annual=0、shape=0 | NaN | 明确全0，允许0需求；通过 |
| annual=6、正常shape | 年量6 | 年量6保持；water=2保持；通过 |
| positive annual、NaN/负shape | 无有效guard | 显式失败；通过 |
| annual负值 | 可产生负负荷 | 显式失败；通过 |
| 导入heat CSV包含NaN | fillna0静默接受 | 消费者拒绝；通过 |

hourly MW积分容差1e−9级；fixture用于守恒，不是新ASEAN数据。补丁没有改变15°C、BDEW、0.6/0.4、热水shape或annual。测试限定原流程的小时输入约定；任意加权representative snapshots需另有归一化约定，不能从本测试推断已支持。

限制：原始annual读取前的fillna、国家缺失仍属于数据审查；E2不是全面数据质量修复。E2一旦应用，会使不合格shape的流程停止；应先确认需求用途与合理shape，不能为了跑通再改回fillna0。候选未合并R，原模型与全部已完成实验保持不变。
