# GEM 全球天然气基础设施追踪：天然气管道（2025-11 版），东盟部分

**来源：**
- `raw9/GEM-GGIT-Gas-Pipelines-2025-11.xlsx`，表 "Pipelines"，53 列；
- `raw9/GEM-GGIT-Gas-Pipelines-2025-11.zip`，GIS 路由文件。

两者都来自 Global Energy Monitor（https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/），由用户于 2026-10-15 下载，SHA256 见 `SHA256SUMS_raw9.txt`。

**抽取：** `extraction/GEM_GGIT_GAS_PIPELINES_ASEAN.csv`，共 128 行。筛选条件是 `CountriesOrAreas` 中含有东盟国家，保留全部列。

| 状态 | 段数 |
|---|---|
| 运营 | 88 |
| 在建 | 1 |
| 拟建 | 15 |
| 搁置 | 8 |
| 取消 | 16 |

## 存量跨境管道（第 15 项起点容量）

| 管道 | 国家对 | 投运年份 | 容量（bcm/年） | 长度（km） | 说明 |
|---|---|---|---|---|---|
| Gresik–Batam–Singapore（Grissik） | ID → SG | 2003 | 4.75 | 468 | GEM 标为跨境 |
| West Natuna Transportation System | ID → SG | 2001 | 3.4 | 640 | GEM 标为跨境 |
| Malaysia–Singapore | MY → SG | 1991 | 未给出（"--"） | 70 | 容量缺失 |
| Trans Thailand–Malaysia（TTM） | MY ↔ TH | 2007 | 10.42 | 267 | GEM 标为跨境 |
| Yetagun | MM → TH | 2000 | 4.1 | 472 | GEM 标为跨境 |
| Yadana 1 | MM → TH | 1998 | 5.2 | 409 | GEM 标为 Myanmar 单国，终点 Daminseik 在边境，接泰国境内管段；实际为对泰出口 |
| Zawtika | MM → TH | 2014 | 3.53 | 300 | GEM 标为 Myanmar 单国，终点 Kanbauk，接入 Yadana 系统对泰出口 |
| JDA–Arthit | 马泰联合开发区 → TH | 2008 | 未给出 | 95 | GEM 标为 Thailand；联合开发区的气按两国分成 |

**注意：**
- 不能只按 `CountriesOrAreas` 判定是否跨境。Yadana 和 Zawtika 在 GEM 中按单国登记，但它们是缅甸对泰国出口的主干；判定时须结合地理位置（终点位于边境）和相连的泰国管段。由 S3-1 逐条核对，并写明判定依据。
- 中缅管道（Sino-Myanmar）通往东盟外部，不进入东盟内部网络。
- 缺失的容量（Malaysia–Singapore、JDA–Arthit）标 `DATA_PENDING`，不估算。
