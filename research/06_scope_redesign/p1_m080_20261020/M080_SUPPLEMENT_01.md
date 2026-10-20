# M08-0 补充 01：审阅修正（第 131 项）

**版本：** v1，2026-10-20 23:40 SGT，由 Claude（审阅端）写入。开始前核对本文件 SHA256，与同目录 `M080_SUPPLEMENT_01_SHA256.txt` 一致才执行。
**会话与模型（原则 10）：** 在原 M08-0 会话中执行（对正在进行的指令的补充）。若原会话已关闭或上下文超过约 60 %，就新建会话，先读 `M080_CLAUDE_CODE_INSTRUCTION.md` 与 `M080_REPORT.md`。模型用 Opus 5.5，强度 Xhigh。**所有过程说明、进度汇报和思考要点一律用中文输出。**
**用户授权：** 第 131 项已确认（2026-10-20 23:38）。规则同 M08-0：只改注册表与 `work/` 下的清单；不改配置、构建或求解脚本、网络与既有结果；不求解，不连云，不调用 Gurobi。

## 1. 屋顶光伏改为 C 级

- 理由：B 级要求"脚本 + 输入哈希、可复现"。建筑原始数据（Microsoft Global ML Building Footprints）不在本机，我们无法复现，所以不够 B 级。
- 敏感性区间：0.5× – 1.5×。
- 在描述中注明对照来源：AEO8 p.140（ID 194–655 GWp、MY 34 GWp、VN 370 GWp）、PDP8 屋顶 48.2 GW、MyRER 屋顶 42 GW。同时给出模型各国屋顶候选上限与这些数字的比值；只作记录，不改数值。

## 2. 基础负荷曲线来源（GEGIS）补文献

- 对照 PyPSA-Earth 文档或代码（负荷数据说明、`Asia.nc` 的数据来源说明），核实 GEGIS 负荷曲线的原始文献。审阅端推测为 Mattsson, Verendel, Hedenus, Reichenberg (2021), "An autopilot for energy models", *Energy Strategy Reviews* 33, 100606，**须核实，不得直接照抄**。
  - 核实一致：登记该文献，写明 DOI。
  - 不一致：按查到的来源登记。
  - 查不到：写"原始文献待补（DATA_PENDING）"，并登记 PyPSA-Earth 文档中的出处。
- LA 借用 KH 曲线、TL 借用 ID 曲线：登记为例外（C 级），写明规则。

## 3. 登记用户新下载的 4 个文件

文件位于 `work/p1_s4r_downloads_20261020/`。每个文件登记文件名、SHA256、机构、版本或发布日期、用途；状态用 REFERENCE_ONLY，描述写"M08 实施时使用"。

| 文件 | 内容 | 用途 |
|---|---|---|
| `R1_demand/myb1-2023-cemen-ERT.xlsx` | USGS Minerals Yearbook 2023 Cement 年表提前发布，表 T22 世界产量 2019–2023，千吨；带 e 的为估计值 | 水泥基年 2023，11 国同一来源；SG、TL 不在表中，按 0 |
| `R1_demand/exp-2026-10-20_15_02_22.xlsx` | worldsteel Steel Data Viewer 导出，粗钢产量 2021–2025，千吨 | 钢铁基年 2024，11 国同一来源；KH、LA、BN、TL 不在表中，按 0 |
| `R1_demand/unpopulation_dataportal_20261020224306.csv` | UN WPP 2024，Timor-Leste 中位预测，2050 年 1,889,249.5 人 | TL 锚定规则的人口，替代二手引述 |
| `R6_costs/prc_hicp_aind$defaultview_spreadsheet.xlsx` | Eurostat prc_hicp_aind，Sheet 1 全项 HICP 年均指数 2016–2025，EU27 与欧元区 | M08-1 回算 |

**HICP 的一项核对：** EU27 的 2025/2020 = 132.86 / 105.76 = 1.256，与 technology-data v0.15.0 的升通胀系数（+25.7 %）一致；EA20 只有 1.226。请用 technology-data 源码或其文档核实它用的是 EU27 HICP，在描述中写明核实结果。

以下两个文件不登记，在报告中注明"误下或无效，未使用"：`mis-202606-cemen.*`（美国月报）、`ESTAT_PRC_HICP_AIND$DEFAULTVIEW_1.0.xml.gz`（只有数据结构）。

## 4. 存量机组成本表版本（只登记，不改模型）

- 存量机组成本与效率来自作者的 v0.13.2 成本表。在注册表与报告中登记为"统一性问题，M08 处理"。
- 拟定的处理方向：改用 technology-data v0.15.0 中对应投运年份的数值（例如 `costs_2020`），使来源、版本统一，同时保留老机组效率较低的事实。写入 `REGISTRY_ROWS_PROPOSED_v2.csv`（add 一行规则）。

## 5. 更新精简版附件 B

重跑清单脚本，生成 `DATA_INVENTORY_v3.*` 与 `DATA_INVENTORY_BRIEF.*`。精简版覆盖为最新版，旧版改名保留为 `_v2`。

- **表 4：**
  - 第 17、21、22、23 行改为"已获取（文件名），M08 实施"；
  - 水泥基年写 USGS 2023，钢铁基年写 worldsteel 2024；
  - 删去"过渡值"表述。
- **表 1：**
  - 第 9 行屋顶光伏等级随第 1 节改为 C；
  - 第 2 行注明 GEGIS 文献（按第 2 节结论）；
  - 第 20 行"修正方向"补"存量机组改用 v0.15.0 对应年份"。
- **统计：** 等级分布等统计随之重算。

## 交付

- **报告：** 在 `M080_REPORT.md` 末尾追加"补充 01"一节，写明新增与修改的行、GEGIS 核实结论、HICP 核实结论，以及统计的变化。
- **提交：** 在原分支提交，更新 PR #44 正文。在 `STAGE2_PROJECT_LEDGER.md` 的 M08-0 条目中注明"`d1_registry.py` 的改动超出原指令范围，用户 10-20 23:38 认可"。
- 完成后停止，等待审阅。
