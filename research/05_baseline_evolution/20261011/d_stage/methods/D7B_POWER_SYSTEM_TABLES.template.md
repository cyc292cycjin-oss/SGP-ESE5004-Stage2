# D-7b 电力系统口径补表

**只读后处理，未求解。** 本任务没有修改任何模型、结果或回执，也没有连接 122。输入与 D-7 完全相同：

- C09 日模型：`daily_candidate_UNQUALIFIED.nc`（SHA256 `{{SHA_D}}`）
- D-5 2920：`gate6_2920_candidate_UNQUALIFIED.nc`（SHA256 `{{SHA_H}}`）

以及两者的后处理目录。结构化数据见 `evidence/D7B_POWER_SYSTEM_TABLES.json`，方法脚本为 `methods/d7b_power_tables.py`，表格由 `methods/d7b_render_md.py` 直接从 JSON 生成。

符号约定按 PyPSA：Link 端口 k 的 p_k 是从母线 k 取出的功率，注入母线的功率为 −p_k。电力母线按实际 `buses.carrier` 判定，为 AC、DC、low voltage 三类。

## 1. Generator 挂接核对

{{T1}}

**结论（VERIFIED）：** coal、gas、oil、lignite 四类 Generator 全部挂在同名的**燃料母线**上（各 100 个，一个节点一个），不在电力母线上。它们是燃料供应（MW_th），不是电厂。真正的发电设备是第 2 节的 Link：燃料母线 → AC，bus2 接 co2 atmosphere。直接挂在电力母线上的 Generator 只有光伏、风电和径流水电。

## 2. 发电 Link 表

只列输出端在电力母线上、输入端不在电力母线上的 Link，即发电设备。电输出容量 = p_nom_opt × 输出端 efficiency；容量因子 = 年发电量 /（电输出容量 × 8,760 h）。

{{T2}}

本模型里没有生物质发电和 CHP 的发电 Link。生物质只经 obligation metering 进入终端用能，不发电。燃料电池的容量和出力在两个模型里都是 0。

## 3. 分国家电力平衡

按国家汇总全部电力母线：Generator、发电/耗电 Link 的各端口、StorageUnit、电力 Load、Line。各国残差都在 1e−9 TWh 以内（数值为 0），所以没有对数据做任何调整。

{{T3D}}

{{T3H}}

## 4. 一次能源供应（化石燃料供应 Generator）

{{T4}}

一次供应里既包含发电用的燃料（第 2 节的输入能量），也包含 final-energy accounting Link 输送给终端用能的燃料。

## 5. CO₂ 排放（报告值，不是约束）

{{T5}}

两种算法相差不到 1 吨。这是模型 2050 年的年排放报告值。表中把原作者 2050 年 100 MtCO₂/年的 cap 并列列出，只作参照，**不作结论，也没有加任何约束**。

## 6. 按资产所在国的成本拆分（仅为描述）

{{T6}}

**口径说明：** 这里按"资产所在地"汇总。Generator、Store、StorageUnit 按所在母线计；Link 按 bus0 计；电力端口分属不同国家的线路和 Link 单列为 CROSS_BORDER；挂在无国家母线上的资产列为 NONE。这只是描述性汇总，**不是成本分摊结论**。资本成本按 capital_cost ×（p_nom_opt − p_nom）计，与官方对账的口径一致。

## 7. D-7 中需要更正的表述

D-7 原文件 `evidence/D7_COMPARISON.json` 和 `D_STAGE_RESULT.md` 第 6 节**不改**，更正写在这里：

| D-7 原表述 | 更正 |
|---|---|
| "气电装机 454.9 GW → 559.8 GW（+104.9 GW，+23.1%）" | 这是 **gas 燃料供应 Generator** 的 p_nom_opt（MW_th），不是电厂装机。真正的燃气发电装机按电输出口径（CCGT + CCGT existing + OCGT）计，从 **204.8 GW_e 增至 262.9 GW_e（+58.0 GW_e，+28.3%）**；按输入侧计，从 352.3 GW 增至 456.9 GW。数字见第 2 节。 |
| "气电发电量 3,298 TWh → 3,756 TWh（+13.9%）" | 这是 **gas 一次供应量（TWh_th）**，其中包含终端用气。燃气发电量（电）实为 **1,422.2 TWh → 1,695.4 TWh（+273.2 TWh，+19.2%）**。 |
| "煤电 / 油电装机 442.8 / 568.6 GW → 443.7 / 568.6 GW" | 这同样是**燃料供应**能力。煤电（coal existing）电输出容量两个模型都是 90.4 GW_e，年发电约 702.7 TWh；油电（oil existing）2.0 GW_e，几乎不发电。 |
| D-7 中"生成量 by carrier"里的 coal、gas、oil、lignite 各项 | 都是燃料供应量（TWh_th），不是发电量。 |

D-7 的以下结论**不受影响**：成本对比（总额、资本、运行）、光伏（屋顶 260 GW → 0、集中式 0 → 41.5 GW；两者都直接挂在电力母线上，已在本表第 1 节核实）、电池与抽水蓄能、跨境输电、水电弃水。机制解释（日均处理抹平光伏昼夜曲线）仍属 INFERENCE。本表的补充证据是：日模型 CCGT 的容量因子为 0.952，接近基荷运行；2920 为 0.900，同时新增 OCGT 调峰（13.4 TWh）和电池放电（7.8 TWh）。

## 8. 范围与边界

- 只做后处理，没有求解，没有改变任何结果或回执；所有数字都来自 D-5 和 C09 已封存的求解结果。
- CO₂ 是报告值；成本按国家拆分只是描述；没有加任何约束，也没有做成本分摊。
- 原未扰动科学目标的最优性仍为 NOT_PROVEN；FullSystemCostComplete 仍为 false。
