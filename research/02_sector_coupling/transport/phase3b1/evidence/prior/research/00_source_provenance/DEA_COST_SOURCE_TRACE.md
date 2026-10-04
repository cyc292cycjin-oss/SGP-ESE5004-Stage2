# DEA / technology-data v0.13.2 来源追踪

**已取回模型所引用的旧 sheet 86 工作簿，并锁定官方成本库 SHA。用户的 August 2026 / sheet 80 文件继续仅作为候选对照，未覆盖任何输入。所有参数仍为 UNVERIFIED/PENDING，来源恢复不是人工确认。**

## 固定版本与当前文件的闭合

`technology-data v0.13.2` → **`ec22a1843632fd28ecb9a139ee5156faf23324a3`**；release API 发布时间 2025-06-13。源码、输入工作簿、manual_input、Eurostat 通胀表和三个年度官方输出已保存至 `official/technology-data/`。

当前 2030/2040/2050 `pre_costs_*.csv` 与该 SHA 的 `outputs/costs_*.csv` **逐字节一致**，三个 SHA256 见 `DEA_WORKBOOK_EVIDENCE.json`。这是输入文件身份核对，未重新编译全成本库。作者两份网络 metadata 也指定 v0.13.2，但作者包没有原始 CSV，因此作者当时输入的字节身份仍缺独立 input hash。

入口：[固定成本库](https://github.com/PyPSA/technology-data/tree/ec22a1843632fd28ecb9a139ee5156faf23324a3)、[成本编译脚本](https://github.com/PyPSA/technology-data/blob/ec22a1843632fd28ecb9a139ee5156faf23324a3/scripts/compile_cost_assumptions.py)、[手工输入表](https://github.com/PyPSA/technology-data/blob/ec22a1843632fd28ecb9a139ee5156faf23324a3/inputs/manual_input.csv)。

## sheet 86 原始工作簿

`inputs/data_sheets_for_renewable_fuels.xlsx` 的 SHA256：

`efa1ce103b813a2a3d807d20c6cd05c937f80010320a38e51149d234b60cd086`

该工作簿有 `86 AEC 100 MW`。文件 properties.modified 为 2024-10-30；Git 中最后一次相关更新为 `bc3af053df72eaac47d320034aab9193b9137cc9`（2024-11-03，biochar pyrolysis and AEC at small scale）。再往前可见 2024-01-30 新数据更新和 2022-06-24 的 04/2022 版更新。**modified 时间不等于 DEA 正式发行名称**；可精确报告的是 Git 冻结字节、表名及单元格，不凭 properties 编造“October 2024 edition”。

当前 DEA 下载脚本扫描官网工作簿链接，并非每一份旧文件的独立下载日志；本轮从冻结 Git 输入取回旧表，原官网当年传输校验记录没有恢复。用户新版 sheet 80 的存在不能解释为旧 source 字段写错。

## 2030 年实例：原值 → 转换 → 当前值

以下均为审计读数，Final candidate 未选择，Human confirmation 未完成。

| 参数 | 固定来源位置 / 原值 | 上游转换与当前 pre_costs 值 | 尚需判断 |
|---|---|---|---|
| 电解效率 | sheet 86 AEC 100 MW，E14=62.1664814911% | %÷100，四位小数 → 0.6217 | 表注 B57 明确 LHV，包含 stack+BOP 电耗；不是 HHV 效率 |
| 电解寿命 | 同表 E22=25 年 | 25 年 | 技术适用性待共同确认 |
| 电解 FOM | 同表 E36=4%/年 | 4%/年 | 后续按最终投资额计 FOM，须注意投资来源已被覆盖 |
| DEA 电解投资 | 同表 E26=550 EUR2020/kW 总电输入 | **不是模型最终投资值** | 不能拿 550 替换当前 1500 |
| 模型电解投资 | manual_input.csv 的 electrolysis/investment/2030=1500 EUR2020/kW_e | add_manual_input 使用 combine_first 覆盖 DEA → 1500 | 来源写 private communications + IEA 报告；私有通信与数值拆解未提供 |
| H₂罐含压缩机投资 | storage 工作簿，151a Hydrogen Storage - Tanks，E24=0.047757294 M€/MWh | ×1000 → 47.7573 EUR/kWh | 区分能量容量与功率容量，不与另一个 tank type 1 无压缩机技术混用 |
| H₂罐寿命 | 同表 E18=30 年 | 30 年 | 来源已定位 |
| H₂罐 FOM | 同表 E28=531.7，表头标 €/MW/year | 编译后 1.1133%/年，可复算比值 531.7/(0.047757294×1e6)×100 | 原表 MW 与储能 MWh 标签需要核对说明/时长口径；复算相等不自动证明量纲正确 |
| 燃料电池 | el_and_dh，12 LT-PEMFC CHP，E30=1.1 M€/MW，E33=55000 €/MW/年，E13=10 年 | 2015→2020 通胀后 1164.0438 EUR/kW_e；FOM=5%，效率0.5，寿命10 | CHP 表抽取为 fuel cell 的边界与热利用需一致 |
| 天然气燃料 | manual_input.csv：21.6 EUR2010/MWh_th | EU27 通胀 2011–2020 乘积 1.1374088529 → 24.5680 EUR2020/MWh_th | 来源是 DIW2013 引用 IEA2011，不是 DEA；热值基准仍需原文核对 |
| 煤燃料 | manual_input.csv：8.4 EUR2010/MWh_th | 同通胀系数 → 9.5542 EUR2020/MWh_th | 同上，不能把上游价格当已确认的 ASEAN 到岸价 |

电解效率的 LHV/输入容量口径已从原表说明恢复；不能因此说所有氢、天然气、储能参数的热值/容量口径全部闭合。电解投资路径为 2020:2000、2025:1800、2030:1500、2040:1200、2050:1000 EUR/kW_e；中间年份由 manual_input 插值。来源字段指向 [IEA e-fuels 报告](https://iea.blob.core.windows.net/assets/9e0c82d4-06d2-496b-9542-f184ba803645/TheRoleofE-fuelsinDecarbonisingTransport.pdf)，但记录同时明确含 private communications；本轮没有证明该整条曲线可由公开报告单独重建。

storage 工作簿 SHA256 为 `5eaff3f3f242efabafc12ba5d556cf770bc2e569fde55dc0bf1a638a95f70911`；el_and_dh 为 `3ab3f61377f4b9026bf74aed95351ef5675c44d321bb9d05b5da05a45071b79f`。工作簿只读单元格摘录见 `DEA_WORKBOOK_EVIDENCE.json`。

## 编译与模型赋值链

1. technology-data 的 `dea_sheet_names` 把 electrolysis 映射到 sheet 86；`get_data_DEA` 读取年份列、插值、选择参数。`order_data`、`convert_units` 规范技术参数及单位；`add_manual_input` 在之后覆盖同名技术/参数。不能仅看最初 DEA sheet 决定最后来源。
2. 通胀函数使用冻结 Eurostat EU27 年率，把投资/VOM/fuel 转到配置 eur_year=2020；数值转换后输出的 currency_year 仍可保留原来源价格年。例如 fuel cell 值已变成 EUR2020，而字段仍为 2015。不要再次按该字段重复通胀。公式复算见 `RECOVERY_SUMMARY.json`。
3. ASEAN 工作流下载预处理成本 → `append_cost_data.py` 根据 AEO8 D15、D17 和配置决定的 D18 覆盖映射技术 CAPEX/FOM/VOM → `process_cost_data.py` 生成电力/部门版本。AEO8 表已从作者运行 SHA 取回，当前实际输入副本与之比较见同一 JSON；它们不等于 DEA 原表。
4. 模型成本处理将 /kW 或 /kWh 换成 /MW 或 /MWh，填默认值，并计算 `fixed=(annuity(lifetime,r)+FOM/100)×investment×Nyears`，`marginal=VOM+fuel/efficiency`。电解2030固定成本示例为 188715.7758309984 EUR/MW_e/年（当前教程读数）。
5. Link 通常按输入侧容量优化；输出侧报价的技术需要效率换算。Store 投资按能量容量，不能与 Link 功率投资相加后忽略单位。求解准备中的 noisy_costs 还可增加小扰动；网络最终成本与原表不必逐项完全相同。

原表储氢 round-trip 行不在当前该罐技术输出参数列表中；不能声称表中压缩损耗已自动完整进入 Store。具体组件效率/损耗映射需随已选 full-SC 技术逐项验收，而非从表名推断。

## 已关闭与残余

已关闭：旧 sheet 86 文件无法取得、v0.13.2 未知 SHA、当前成本来源是否同版、主要参数原始位置、DEA 与 manual override 的优先顺序、燃料价格通胀算法。无需用户再寻找这些旧工作簿。

仍待：电解投资私有通信的可公开说明/证据；储氢 FOM 的 MW/MWh 口径；相关燃料原始热值/地区含义；是否接受这些冻结值服务于 ASEAN full-SC 研究。这些问题未解决前不采用新值，也不把任何台账项改为 CONFIRMED。
