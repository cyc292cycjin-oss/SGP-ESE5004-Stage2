# V3 跨境输电存量核查（D160-2 附加项）

**只报告，不改网络。** 差异由审阅端决定。网络存量取 v2 一体化网络（`V2_CROSS_BORDER_STOCK.csv`），`no_new_xb` 与此相同。

## 1. 来源

| 代号 | 来源 | 性质 | 位置 |
|---|---|---|---|
| APG | ACE APG 表（S4E 登记） | **"existing"列**，2024 年口径 | `research_inputs/corridors/CORRIDOR_APG_CROSSCHECK_2024.csv`（`apg_existing_mw`），第 94 项 S4E-1 已用 |
| S8 | Zhong et al., iScience 2025 补充材料 Table S8 | **"currently operational as well as those that are under construction"**，数据主要来自 IEA 2019a/b、ERIA 2014，ID–SG 取 Chang et al. 2019 | `work/p1_s4r_downloads_20261020/F1_renewable_potential/mmc1.pdf` p.12 |
| S4 | Zhong et al., PNAS Nexus 2026 SI Table S4 | 同一组数；文字说明含"existing + under construction + planning"，合计规划 29.75 GW | `pgaf389_supplementary_data.pdf` p.11 |

**两个来源口径不同：** APG 是现状存量；S8 把运营、在建（S4 还把规划）混在一起，**不是单一的"现有容量"表**。仓库与 `work/` 中没有找到逐条列出现有容量且区分"运营专线"的单一来源，所以"现有容量"的权威值未能确定。

## 2. 逐条对照

单位 MW。"差异"＝S8 − 网络。

| 国家对 | 网络存量 | APG existing | APG 在建 / 规划 | S8（运营 + 在建） | 差异 | 判断 |
|---|---:|---:|---|---:|---:|---|
| **LA–TH** | 955 | 955 | 规划 TBC | **6,770** | **+5,815** | 网络 = APG；S8 大得多，见第 3 节 |
| **TH–MM** | 0 | 0 | 规划 365 | **14,860** | **+14,860** | 见第 3 节 |
| LA–VN | 0（第 100 项） | 无 | TBC | 540 | +540 | 第 100 项定为 0；S8 与现实联网方向一致 |
| KH–TH | 250 | 250 | +650 | 2,320 | +2,070 | 网络 = APG |
| MY–SG | 525 | 525 | +525（到 2024） | 1,050 | +525 | S8 = APG 存量 + 在建，相符 |
| MY–TH | 380（AC 80 + DC 300） | 380 | TBC | 780 | +400 | 网络 = APG（第 97 项） |
| ID–MY（Sarawak–西加里曼丹） | 230 | 230 | — | 230 | 0 | **三方一致** |
| ID–MY（半岛–苏门答腊） | 0 | 无 | 规划 600 | 600 | +600 | S8 列入，APG 为规划 |
| KH–VN | 200 | 200 | TBC | 200 | 0 | **三方一致** |
| KH–LA | 300 | 300 | TBC | 300 | 0 | **三方一致** |
| LA–MM | 30 | 30 | 规划 100–600 | 未列 | — | 网络 = APG |
| PH–MY（巴拉望–沙巴） | 0 | 无 | 规划 500 | 500 | +500 | S8 列入，APG 为规划 |
| MY–BN（Sarawak–文莱） | 0 | 无 | TBC | 400 | +400 | S8 列入，APG 无 |
| ID–SG（巴淡） | 0 | 无 | 规划 3,400（合并入 16 号） | 600 | +600 | S8 列入，APG 为规划 |
| ID–SG（苏门答腊） | 0 | 无 | TBC | 600 | +600 | 同上 |
| **合计** | **2,870** | 2,870 | | **29,750** | **+26,880** | S8 合计与 S4 文字的 29.75 GW 相符 |

网络 AC 16 条 2,570 MW + DC 1 条 300 MW = 2,870 MW。

**结论（VERIFIED）：** 网络存量与 APG existing **逐条完全一致**（8 对）。S8 与网络一致的只有 3 对。差异集中在 LA–TH 和 TH–MM，两者占总差额的 77 %。

## 3. 重点：LA–TH 与 TH–MM

- **LA–TH：** APG 955 MW 是联网线路口径。S8 的 6.77 GW 接近老挝对泰国电力购售协议规模（INFERENCE，本次未取得原始表），其中多数是电站专线（IPP dedicated lines），不是电网联络线。模型里这些水电站作为老挝境内机组，出力只能经 955 MW 走廊外送，所以**在 `no_new_xb` 下会低估老挝对泰出口能力**，也就可能高估一体化相对 `no_new_xb` 的 B6 和 LA、TH 的受益。
- **TH–MM：** S8 的 14.86 GW 与 PNAS SI 规划口径同一组数，APG 为 0（规划 365 MW）。这很可能是规划或潜在项目（如萨尔温江水电），不是现状存量（INFERENCE），不建议按现有存量对待。

## 4. 留给审阅端的问题

1. LA–TH 是否把专线计入 `no_new_xb` 存量。若计入，需要取得 IEA 2019a/b 或 EGAT / EDL 的原始项目表，并判定 2025 年运营口径（S8 含在建）。
2. MY–SG 的 525 MW 在建（APG 到 2024）是否算作存量。第 160 项写"在建项目主算不计"，当前不计。
3. 其余按 APG 现状。

**数据状态：** 专线口径的单一来源未找到，登记 `xb_stock_la_th_dedicated_lines = DATA_PENDING`；**不停工，网络不改。**
