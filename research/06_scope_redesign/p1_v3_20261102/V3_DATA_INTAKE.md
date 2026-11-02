# V3 数据盘点（阶段 1.2）

- 上传目录 `work/p2_data_intake/v3_20261102/`（只读）：32 个文件，464,306,369 B。解压与中间表放在主检出 `results_project/v3/intake/`、`results_project/v3/phase1/`，均不进仓库。
- 本阶段新下载 1 个（在指令许可的第 (a) 类内）：IRENA 2022 氢载体报告，9,691,478 B，SHA256 见第 11 节。GADM 未下载（第 5 节：本机已有）。
- 证据等级：VERIFIED（实际读到的数或表）、INFERENCE（据此推断）。

## 0. 结论摘要

1. **APEC 表只有 2022、2021 两年**，没有 2019，且 **MY 100 %、SG 94 %、BN 98 % 未细分**；有用的只有 VN（未细分 13.6 %）、TH（4.8 %）、PH（4.0 %）和部分 ID（47.8 %）。
2. **USGS 印太 GIS 不含 ID、TH**（也不含 KH、LA）。第 164 项中"氨、炼油、镍按设施清单（USGS GIS）"对印尼镍这一最关键的部分不成立，要改用 USGS 印尼国别卷表 2（无坐标，只有省 / 地点文字，需要人工地理编码）。
3. **GEM 钢铁库里东盟的 `Ferronickel capacity` 全为 0**，NPI 产能不在 GEM。
4. **印尼镍冶炼确实藏在工业总量里**：HEESI 2025 脚注直接写明 2018 年冶炼厂投产、2019 年满负荷，工业用煤 2017→2019 从 58,800 升到 167,412 kBOE；APEC 2022 把 992 PJ 煤记在"钢铁"行（2021 年只有 288 PJ）。USGS 2019 年 NPI 320 万 t，2023 年 990 万 t。
5. **DOSE 有三个坑**：TH 2019 年只有 20 个 ADM1 且偏向东北部（要用 2018 年，77 个）；VN 只到 2018 年；PH 用的是 17 个大区编码，与 GADM 81 省**零交集**。
6. **RAMP `consumption` 是车队电池消耗（行驶用电），不是充电负荷**；时间戳是 UTC，但生成时用带夏令时的欧洲当地时钟。
7. 省级边界**不必下载**：GADM 4.1 的 11 国 ADM1 已在 `pypsa-asean/data/gadm/`；节点区域 `research_inputs/renewable_v5/regions_onshore.geojson` 96 个（只含 AC 节点）。

## 1. APEC 2022 能源平衡表（第 1 问）

单位 PJ，数据年 2022（ID 另列 2021）。表在 PDF 里是图片，目视读取（`p077/p095/p125/p137/p149/p161/p047`）。

| 行 | ID 2022 | ID 2021 | TH | VN | MY | PH | SG | BN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 工业合计 | 3,194 | 1,918 | 1,371 | 1,542 | 797 | 298 | 179 | 6.1 |
| 采矿 | — | — | 5.0 | 65 | — | 24 | — | — |
| 建筑 | — | — | 6.1 | 22 | — | 29 | 2.0 | — |
| 钢铁 | 1,012 | 308 | 68 | 177 | — | 25 | — | — |
| 化工 | 193 | 202 | 240 | 106 | — | 11 | 7.4 | 0.1 |
| 有色 | — | — | — | — | — | — | — | — |
| 非金属矿物 | 298 | 154 | 372 | 527 | — | 47 | — | — |
| 运输设备 | — | — | — | 9.3 | — | — | — | — |
| 机械 | — | — | 93 | 55 | — | 44 | — | — |
| 食品 | 23 | 24 | 374 | 130 | — | 90 | — | — |
| 造纸 | 139 | 41 | 70 | 60 | — | 12 | — | — |
| 木材 | — | 0.1 | 35 | 36 | — | 0.7 | — | — |
| 纺织 | 3.8 | 4.0 | 42 | 145 | — | 3.6 | — | — |
| 未细分 | 1,526 | 1,184 | 66 | 209 | 797 | 12 | 169 | 6.0 |
| **未细分占比** | **47.8 %** | **61.7 %** | **4.8 %** | **13.6 %** | **100 %** | **4.0 %** | **94.4 %** | **98 %** |

与 v2 "其他"桶对照（v2 口径：UNSD 2019，扣除钢铁、水泥实物路线后的 `other + construction + mining`，取自 `INDUSTRY_2050_OTHER_BUCKET.csv`）：

| 国家 | v2 工业 2019 TWh | v2 其他 2019 TWh | v2 其他占比（2019） | APEC 未细分 | 判断 |
|---|---:|---:|---:|---:|---|
| ID | 774.4 | 633.1 | 81.8 % | 47.8 % | APEC 的钢铁行含镍；能源口径与 2019 不可直接互换 |
| MY | 214.0 | 184.2 | 86.1 % | 100 % | APEC 帮不上忙 |
| VN | 396.6 | 226.1 | 57.0 % | 13.6 % | **APEC 可显著改善** |
| SG | 78.2 | 42.0 | 53.6 % | 94.4 % | v2（UNSD）更细 |
| TH | 294.9 | 21.8 | 7.4 % | 4.8 % | 两者都细 |
| PH | 69.2 | 11.8 | 17.1 % | 4.0 % | 两者都细 |
| MM | 59.2 | 48.2 | 81.3 % | 非 APEC 成员 | 无数据 |
| KH / LA / BN | 10.0 / 6.4 / 2.2 | 2.4 / 2.4 / 1.3 | 24 / 38 / 58 % | KH、LA 非成员 | 量小 |
| 11 国 | 1,905 | 1,173 | 61.6 % | | |

指令中的 68 %（ID 85 %、VN 75 %、MY 76 %）是 2050 年路线折算后口径（3,820 TWh 分母），上表是 2019 投入能源口径，两者都对，分母不同。

## 2. USGS 国别卷与亚太卷（第 2 问）

kt，取 2019 年；亚太卷（2017–18 版）取 2018 年。"—"＝表中无此行或为零。

| 国家 | 粗钢 | 水泥 | 镍（含量或毛重） | 铝 | 氨（N 含量） | 炼油 |
|---|---:|---:|---|---|---:|---|
| ID（2023 卷） | 8,565（生铁 2,900；DRI 120） | 71,900 | NPI 毛重 3,200、Ni 含量 380；镍铁毛重 129、Ni 含量 25.7；镍锍 Ni 含量 71.0；MHP 2022 年起 | 原铝 249.5；氧化铝 1,148 | 6,100 | 吞吐 367,000 kbbl |
| TH（2020–21 卷） | 4,246 | 40,261 | — | —（无原铝） | —（未见） | 分产品，表 2 有炼厂清单 |
| PH（2022 卷） | 1,915 | 27,700 | 矿 Ni 323.3；镍钴硫化物中间品 51.1（HPAL 两厂） | — | —（未见） | 59,500 kbbl |
| VN（2022 卷） | 17,469（生铁 9,836） | 105,533 | 矿，量小 | 氧化铝 1,365 | 1,150 | 91,200 kbbl |
| MY（亚太卷 2018） | 3,200（生铁 750） | 20,000 估 | — | 750 估（列位待核）；GIS 有 14 个设施 | 见 GIS | 见 GIS |
| MM（亚太卷 2018） | — | 6,000 估 | 见 GIS | — | 见 GIS | 见 GIS |
| KH / LA / BN | — | 4,900 / 4,800 / 290 | — | — | — | — |
| SG、TL | 亚太卷无行 | | | | | |

齐全度结论：钢、水泥覆盖最好（但亚太卷年份为 2018、部分为估计）；镍只有 ID、PH 有意义；铝 ID、VN（氧化铝）、MY；氨 ID、VN（MY、MM 在 GIS）；TH、PH 的氨未见。v2 已用的氨是 USGS 氮肥年鉴 T12（ID、MY、VN），比国别卷更一致。

注意：v2 M08b 的物理产出基年是水泥 2023、钢 2024、氨 2019；USGS ID 卷 2019 粗钢 8,565 kt，而 GEM 现役产能 21,400 kt，增长很快，基年选择影响大。

## 3. GEM 钢铁、水泥（第 3 问）

运营中设施（解压到 `results_project/v3/intake/gem/`；`Global-Energy-Ownership-Tracker` 未用）。

| 国家 | 水泥厂数 | 水泥产能 Mt/a | 熟料产能 Mt/a | 钢铁厂数 | 粗钢产能 kt/a | BOF | EAF | IF | 高炉 | DRI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ID | 46 | 130.38 | 50.95 | 8 | 21,400 | 11,980 | 9,420 | 0 | 10,560 | 0 |
| VN | 91 | 158.69 | 112.34 | 21 | 39,926 | 25,574 | 9,502 | 4,350 | 22,320 | 250 |
| MY | 21 | 31.21 | 23.64 | 9 | 11,920 | 6,200 | 4,920 | 800 | 6,400 | 900 |
| TH | 16 | 60.07 | 50.37 | 11 | 9,285 | 0 | 8,555 | 730 | 0 | 0 |
| PH | 25 | 46.44 | 17.64 | 4 | 4,100 | 2,000 | 2,100 | 0 | 1,790 | 0 |
| MM | 20 | 17.61 | 13.68 | 1 | 400 | 0 | 400 | 0 | 0 | 0 |
| LA | 17 | 16.20 | 4.50 | — | — | | | | | |
| KH | 6 | 10.20 | 3.33 | — | — | | | | | |
| SG | —（GEM 无） | | | 1 | 750 | 0 | 750 | 0 | 0 | 0 |
| BN | 1 | 0.50 | 0.00 | — | — | | | | | |
| TL | — | | | — | — | | | | | |
| 合计 | 243 | 471.3 | 276.5 | 55 | 87,781 | | | | | |

- 坐标完整率：水泥 243 / 243（`exact` 231、`approximate` 12）；钢铁 55 / 55（`exact` 53）。
- 产能字段：水泥 235 / 243 有值（PH 缺 4，LA、MM、MY、TH 各缺 1）。
- 落入节点区域：水泥 237 / 243（6 个在区域多边形外：ID 4、MY 1、PH 1，海岛或岸线），钢铁 54 / 55（MY 1）；**无一落入他国区域**。
- 单元表：EAF 57 台 35,647 kt，BOF 25 台 45,754 kt，IF 6 台 5,880 kt，高炉 29 座 41,070 kt，DRI 2 座 1,150 kt。
- 印尼钢铁 8 厂：Dexin Morowali 7,000 kt（中苏拉威西）、Krakatau 4,000、KS Posco 3,000、Master Steel 2,000、Gunung Raja Paksi 1,820、CNR Mandan 1,000（南加里曼丹）、Jakarta Prima 900、Ispat Indo 700。
- 印尼水泥熟料节点分布（点入多边形，只作预览）：`ID_Java-Bali1 0` 37.3 %、`ID_Sulawesi0 4` 21.2 %、`ID_Java-Bali1 1` 13.6 %。

## 4. USGS 印太 GIS（第 4 问）

`INDOPAC_GIS.gdb.zip` 解压到 `results_project/v3/intake/INDOPAC_GIS.gdb`，8 个图层；设施层 `INDOPAC_Mineral_Facilities` 1,573 点（另有 `Mineral_Development` 285、`Mineral_Exploration` 884，为矿山开发 / 勘探，本项目不用）。

- **覆盖国家（全部）：** Malaysia 346、Vietnam 247、Korea South 165、Philippines 152、Bangladesh 122、Burma 94、Mongolia 75、New Caledonia 68、Taiwan 63、Sri Lanka 54、New Zealand 53、Timor-Leste 35、Bhutan 32、PNG 30、Brunei 15、Fiji 8、Singapore 6、Solomon 6、Nauru 2。
- **不含 ID、TH、KH、LA。**

字段：`DsgAttr01` 商品、`DsgAttr02` 产品、`DsgAttr06` 年产能（−999＝无）、`DsgAttr07` 单位、`LocOpStat` 状态、`ADM1`、`Latitude`/`Longitude`、`LocConf`（E 精确 1,067、A 近似 506）。坐标 100 %。

东盟子集（设施数 / 有产能数）：

| 类别 | MY | VN | PH | MM | BN | SG | TL |
|---|---:|---:|---:|---:|---:|---:|---:|
| 水泥 | 18/18 | 62/62 | 23/23 | 19/19 | 1/1 | 1/1 | 0 |
| 钢铁与铁合金 | 37/34 | 43/43 | 11/11 | 11/11 | 0 | 1/1 | 0 |
| 镍 | 0 | 1/1 | 30/27 | 1/1 | 0 | 0 | 0 |
| 氮（氨） | 3/3 | 3/3 | 0 | 3/3 | 0 | 0 | 0 |
| 炼厂与石化 | 12/12 | 2/2 | 3/2 | 2/2 | 3/3 | 0 | 0 |
| 铝 | 14/13 | 4/4 | 2/0 | 0 | 0 | 0 | 0 |

镍 PH 30 条里 28 条是矿山、2 条是 HPAL 中间品厂；VN、MM 是矿。注意 GIS 单位混杂（kmt、mt、MMbbl、kbbl、mcm），且有 `Shared Capacity` 共享产能字段，使用时要防重复计算。

## 5. DOSE V2.11（第 5 问）

46,851 行，35 列；制造业字段 `man_grp_pc_usd`（人均，USD）等，乘 `pop` 得产出。

| 国家 | 总 ADM1 | 年份范围 | 制造业年份 | 最近可用整年 | 该年 ADM1 数 | 与 GADM 4.1 编码 |
|---|---:|---|---|---|---:|---|
| ID | 32 | 1979–2020 | 1979–2020 | **2019** | 32（2020 年 30，2017–18 年 31） | 31 个相同；`IDN.15_1` 不匹配；GADM 另有 3 个（共 34） |
| MY | 15 | 1970–2020 | 2005–2020 | **2019** | 15 | 15 个全在 GADM（GADM 16） |
| PH | 17 | 1975–2020 | 1975–2020 | **2019** | 17 | **0 个相同**：DOSE 用大区编码 `PHL.100_1…`，GADM 用 81 省 |
| TH | 77 | 1995–2019 | 1995–2019 | **2018** | 77（**2019 年只有 20 个**） | 77 全同 |
| VN | 63 | 1995–2018 | 1995–2018 | **2018** | 63 | 63 全同 |
| LA | 2 | 1995–2010 | 2006–2010 | 2010 | 2 | 不可用，视同无覆盖 |
| KH、MM、BN、SG、TL | — | — | — | — | 0 | 无数据 |

- TH 2019 的 20 个 ADM1 里 Nakhon Ratchasima 29.9 %、Khon Kaen 21.8 %，没有曼谷、罗勇，**直接用 2019 会把泰国工业搬到东北**；2015 年 Rayong 15.1 %、Bangkok 13.9 %、Chon Buri 11.0 % 才合理（2018 年待阶段 2 计算）。
- ID 2019 前五：Jawa Barat 16.9 %、Jawa Timur 15.9 %、Jakarta 10.6 %、Jawa Tengah 10.0 %、Kalimantan Timur 7.2 %（后者含油气制造业）。
- 省级边界：`pypsa-asean/data/gadm/gadm41_<ISO3>/gadm41_<ISO3>.gpkg` 11 国齐全，`ADM_ADM_1` 分别 BRN 4、KHM 25、IDN 34、LAO 18、MYS 16、MMR 15、PHL 81、SGP 5、THA 77、TLS 13、VNM 63。**这些文件在主仓库之外的同级 `pypsa-asean` 检出里**，需要把用到的 ADM1 层打包进 `research_inputs`（阶段 2，登记 SHA256，属于已有数据，不是新下载）。
- 与节点的对应：节点区域 `regions_onshore.geojson`（字段 `node`、`country`，96 个 AC 节点；PH 5、MY 7、TH 6，DC 换流节点无区域）。ADM1 与节点区域做多边形叠加即可。

## 6. RAMP EV 曲线（第 6 问）

| 文件 | 行数 | 列 | 时间 | 时区 | 国家 |
|---|---:|---|---|---|---|
| `ramp-ev-consumption-profiles.csv.gz` | 4,330,560 | `datetime, year, country_code, demand` | 2000-01-01 至 2018-12-31，逐时 | `+00:00` | 26 |
| `ramp-ev-plugin-profiles.csv.gz` | 4,330,560 | `datetime, year, country_code, plugin` | 同上 | 同上 | 26 |

国家：AUT、BEL、CHE、CZE、DEU、DNK、ESP、EST、FIN、FRA、GBR、HRV、HUN、IRL、ITA、LTU、LUX、LVA、NLD、NOR、POL、PRT、ROU、SVK、SVN、SWE。`ramp-cooking-profiles` 未用。

README（Euro-Calliope）要点（VERIFIED）：

- `demand` 是**车队电池消耗**（"fleet battery consumption"），不是充电功率。
- `plugin` 是"实时接入的电池容量 / 理论最大可接入容量"。
- 配合模型内生优化充放电使用，并以**月度**移动需求约束。
- 采用 `perfect foresight` 充电逻辑（面向 V2G）。

实测（2013 年，`results_project/v3/phase1/RAMP_*_2013_DIURNAL_UTC.csv`）：

- 时钟：DEU 峰值 1 月 15 UTC、7 月 14 UTC；ESP 17→16；GBR 17→16；PRT 18→17。**峰值在夏季提前 1 小时 → 生成时用当地时钟含夏令时**，标注为 UTC。
- 日内：峰/均 1.69–2.20（PRT 最低，NOR 最高）；26 国均值在 UTC 上有 06 时和 14–15 时两峰。
- 星期：周一至周五 ≈1.025，周六 0.989，周日 0.881。
- 季节：月度 / 年均 0.905–1.140（欧洲冷暖）。
- 接入率：年均 0.764–0.782（v2 用常数 0.8）；日内约 0.75–0.80。
- 年总量：`demand` 3,437（IRL）–7,010（LVA）（×10⁶，单位 README 未写），用前必须归一化，不能当绝对量。

## 7. OurAirports（第 7 问）

`airports.csv` 86,330 行。东盟 `large_airport` / `medium_airport` 且 `scheduled_service=yes`：**223 个**。

| 国家 | large | medium |
|---|---:|---:|
| ID | 19 | 52 |
| PH | 15 | 25 |
| TH | 10 | 23 |
| MY | 8 | 18 |
| VN | 8 | 12 |
| MM | 3 | 14 |
| KH | 4 | 1 |
| LA | 3 | 1 |
| TL | 2 | 2 |
| SG | 1 | 1 |
| BN | 1 | 0 |

- 点入节点区域：208 / 223；15 个在多边形外（PH 7、ID 5、MY 1、VN 1、MM 1，海岛机场，如 Mactan Cebu、Panglao），用同国最近节点。清单 `ASEAN_AIRPORTS_SCHEDULED_V3.csv`。
- **无客流量字段**；`airport-frequencies.csv`、`runways.csv` 只能作规模代理。
- `Assembly` 已有 `AIRPORT_SIZE_WEIGHTS` 节点份额（第 162 项可直接用，见设计）。

## 8. 现有跨境设施（第 8 问）

v2 一体化网络（`results_project/v3/phase1/V2_CROSS_BORDER_STOCK.csv`）：

| 国家对 | 类型 | 容量 MW | 组件 |
|---|---|---:|---|
| LA–TH | AC | 955 | 线路 49、52、53、55、56、58、61、62、66 |
| MY–SG | AC | 525 | 线路 92 |
| KH–LA | AC | 300 | 线路 43 |
| KH–TH | AC | 250 | 线路 47 |
| ID–MY | AC | 230 | 线路 23 |
| KH–VN | AC | 200 | 线路 39 |
| MY–TH | AC | 80 | 线路 91 |
| LA–MM | AC | 30 | `APG17_LA_MM` |
| MY–TH | DC | 300 | Khlong Ngae–Gurun |
| ID–SG | 气 | 8,794.7 | Gresik–Batam–Singapore 5,125.7（单向）、West Natuna 3,668.9（单向） |
| MM–TH | 气 | 13,844.9 | Yadana 5,611.3、Yetagun 4,424.3、Zawtika 3,809.2（单向） |
| MY–TH | 气 | 11,244.2 | TTM（双向） |
| **合计** | | AC 2,570、DC 300、气 33,883.7 | AC 16 条、DC 1 条、气 6 条 |

- 候选（前向）组件总数：AC 62、DC 5、H₂ 管 55、气管 61、CO₂ 管 55；存量 FOM 899 万 EUR/a（只含电力）。
- LA–VN 存量为 0：第 100 项（S4H-1）的决定，现实中有联网，属已定口径。

GEM GGIT 2025-11（`work/p1_s4r_downloads_20261020/F2_lng/gem-download (1).zip`）核对：

- 运营跨境气管没有超出现有 7 行表的项目。
- 容量：6 条有；**Malaysia–Singapore Gas Pipeline（P7105，1991 年，70 km）`Capacity`、`Diameter` 全空**，现模型不建该管，只有走廊候选。
- 在建项目主算不计（第 160 项）。

## 9. 只作对照的资料（第 9 问）

| 资料 | 可用内容 | 对照价值 |
|---|---|---|
| HEESI 2025（172 页） | 2015–2025 分部门、分燃料；**无工业子部门**。工业合计（kBOE）：2017 248,751、2018 308,101、2019 363,535、2020 317,800、2021 309,530、2022 537,280、2025 681,237。最终消费的煤：2017 58,800、2018 100,506、2019 167,412、2021 87,820、2022 299,191、2025 364,476。脚注"增加来自 2018 年冶炼厂投产、2019 年满负荷运行" | 镍冶炼证据；2021→2022 跳变（工业 +74 %）提示统计口径变动，APEC 2022 同步跳变 |
| EBT 2022（Malaysia，kt oe，2 页） | 工业 19,033 ktoe（气 8,278、油 1,941、煤 1,553、电 7,260），**无子部门**；非能源 7,183 | MY 工业总量对照（797 PJ） |
| DOSM `energy_consumption_sector.csv` | 马来西亚 8 个部门 1980–2024，单位 ktoe，**无工业子部门** | 时间序列对照 |
| 越南 EOR 技术报告 2024（158 页） | TIMES 模型工业子部门（钢铁、水泥、氨等）产量与需求预测（图 11–14，表 2） | VN 产量路径对照 |
| USGS 泰国 / 菲律宾 / 越南卷表 2 | 水泥、钢、炼厂设施清单、地点、产能 | 补 GIS 空白（TH）与核对 GEM |
| 泰国 EPPO 2021 统计报告（234 页，泰文） | 文本层有编码问题（泰文字符占比低），未抽取数值 | 登记；TH 已有 APEC 与 UNSD，不依赖 |

## 10. 缺口与处理

| 缺口 | 影响 | 处理 |
|---|---|---|
| 镍冶炼单位能耗 | 第 163 项 | **需用户提供文献**：JRC-IDEES 无镍，仓库与允许下载范围内没有。候选 Norgate & Jahanshahi (2011)、Wei et al. (2020)（均为凭记忆列出的候选，未核实）。仓库内只能做口径内反推（见 `V3_DESIGN.md` 第 4.4 节） |
| 印尼设施坐标（镍、氨、炼厂、铝） | 第 164 项 | USGS 印尼卷表 2 只有地点文字；可人工地理编码到省（阶段 2），无需新数据 |
| MY–SG 气管容量 | 第 160 项 | GEM 无；选项见设计 |
| 泰国氨、炼厂坐标 | 第 164 项 | USGS 泰国卷表 2 地点文字，人工编码 |
| 船速、港口时间 | 第 161 项 | technology-data 没有；登记假设或用替代公式，见设计 |
| ASEAN 车队规模 | 第 165 项 | 无；用能量比代理，见设计 |

## 11. 文件登记

SHA256 全文与大小（`evidence/INTAKE_FILES_SHA256.csv` 同内容）。

| 文件 | 大小 B | SHA256 | 内容 |
|---|---:|---|---|
| `01_industry/225_ewg_apec-energy-statistics-2022.pdf` | 23,637,538 | `459096300664a89feb9659d51e7eb56ab26eb2ff5c06af069ab4df96ab5218b0` | APEC Energy Statistics 2022：21 经济体，2022、2021 两年平衡表（表为图片） |
| `01_industry/2564_รายงานสถิติพลังงาน_สนพ.pdf` | 28,819,012 | `fd13813f75bb403ebd5ee17ac312f614075ca3232c79eacaf7ae1d3cfee82aed` | 泰国 EPPO 能源统计 2021（泰文） |
| `01_industry/Background_eor_technical_report_2024.pdf` | 3,152,065 | `e46f9458b3f495c43a3ebd91dca347885f7d09c0dc2efa75c8558e97f6fc316b` | 越南 EOR 技术报告 2024 |
| `01_industry/EBT 2022 Table.pdf` | 378,796 | `63b7fcf1f5ea2bb4545cd4a99a691aeb8c87df39e347167fff2a367e56afad99` | 马来西亚能源平衡表 2022 |
| `01_industry/content-handbook-of-energy-and-economic-statistics-of-indonesia-2025.pdf` | 10,962,809 | `7e4a75eb00b99208f3004b8b934b6cb304241699f6ffe97526f938c1738fdec2` | 印尼 HEESI 2025 |
| `01_industry/energy_consumption_sector.csv` | 10,009 | `d1c8b5ae0fed9398966a7c7fc62ef3af9770e53a2a0327f8e590f040d9cdd675` | DOSM 马来西亚分部门能耗 1980–2024 |
| `01_industry/myb3-2017-18-asia-pacific.pdf` | 637,550 | `8790c63664a665d0e3c7a96629557949e4484a430398a43d92d339e63377966d` | USGS 亚太卷 2017–18 |
| `01_industry/myb3-2020-21-thailand.pdf` | 338,493 | `418899e01fec86e7b33cee4abd69da78d2bc92ae3693298bda1b869237e37086` | USGS 泰国卷 |
| `01_industry/myb3-2022-philippines.pdf` | 345,811 | `9c74e2d6a695739e78304b5428bb964199a117cfa9307780741b75e50cf1c92d` | USGS 菲律宾卷 |
| `01_industry/myb3-2022-vietnam.pdf` | 359,394 | `e483e7bde6f44527fe5075cb4fd5822660f380521e27c6e79e2b0a8ae84de68e` | USGS 越南卷 |
| `01_industry/myb3-2023-indonesia.pdf` | 334,237 | `027a0ad5910c0085eb0d01cd7a93806c956d8021264d34865683d78bda6ada62` | USGS 印尼卷 |
| `02_facilities/INDOPAC_GIS.gdb.zip` | 40,056,082 | `1d7bccb8ab34340672f95cd12f43af2b38c2e386b5e0d80a49bcb4871ce48e7b` | USGS 印太 GIS 地理库 |
| `02_facilities/INDOPAC_GIS.png` | 793,090 | `c00d7bef68f16634445abc8415d8a1e88aa0100449485ca061533e6746f725f7` | GIS 图 |
| `02_facilities/INDOPAC_GIS_metadata.xml` | 193,783 | `500444701e8118c5101fdf2a0f9ba42b0c81f2c3534402cda89a8ee70d64ede5` | GIS 元数据 |
| `02_facilities/SI_INDOPAC_GIS_Data-Level_LayerPackages.zip` | 45,297,559 | `882e73ec01c35397fc10299a30044ca524bb1b08ff02eed71e26040cb0da25b4` | 分层图层包（未用） |
| `02_facilities/SI_INDOPAC_GIS_Data-Level_Metadata.zip` | 43,140 | `27bb8ceb48e4ac60051d71ffacf1af262eef2dbdef3f7ef5f8dd59e00eac8790` | 分层元数据 |
| `02_facilities/gem-download (1).zip` | 61,411,816 | `be5c0a3218f74e85c8fa077a55e09e14a0e4dc4a7e465679eba4eda784c1d4a7` | GEM 水泥（含不用的 Ownership Tracker） |
| `02_facilities/gem-download.zip` | 61,602,981 | `e824dbd6e17a8ee68ddd609e6369daa0a76d2bc3cb4b5269c35e1d20a4599dac` | GEM 钢铁（含不用的 Ownership Tracker） |
| `03_subnational/DOSE_V2.11.csv` | 15,925,733 | `c41b208418fe8198b79500fb76c34c70931d0784ced69507ea371f053e0c504a` | DOSE 省级产出 |
| `03_subnational/DoseV2p11_changes.pdf` | 1,269,573 | `f458772523fa9251fdb7dab49bb114284878a4bf00a26096666ed24d998bca54` | DOSE V2.11 变更说明 |
| `04_ev/README-ramp-cooking.pdf` | 253,147 | `337acc68b999ddd0c1744ce282b1137f111457747a3d18a8a795a7cd9233dae6` | RAMP 炊事说明（不用） |
| `04_ev/README-ramp-ev.pdf` | 543,679 | `f282ba8e736bcfcab3e53dde6706dc87d12e93dd5ebb8c8281a50b81b0be1d90` | RAMP EV 说明 |
| `04_ev/ramp-cooking-profiles.csv.gz` | 33,770,792 | `350cf5e28e33b265c2cebf83b5dac6b7e41b24d1a953e8cf56cb6b1b2d35ca7c` | RAMP 炊事曲线（不用） |
| `04_ev/ramp-ev-consumption-profiles.csv.gz` | 57,465,465 | `2dc37e6796ed2c0fe781fa6adc661482547a26547dfde6f8dd7a33c07a3ca115` | RAMP EV 电池消耗曲线 |
| `04_ev/ramp-ev-plugin-profiles.csv.gz` | 51,951,129 | `01bd14244be6969670024994ad6abb69f8e22b8a467a6316cf344fa769cf1bca` | RAMP EV 接入率曲线 |
| `05_airports/airport-comments.csv` | 4,686,107 | `c4fe1fbda6a2138aa14a8936ed20be741173031065ec126c0451726d6db28669` | OurAirports（不用） |
| `05_airports/airport-frequencies.csv` | 1,302,359 | `c13fa80fef069cce9e6b6f8ba4bd96a4088b4638782e49b938fe49d8c42e8414` | OurAirports 频率 |
| `05_airports/airports.csv` | 12,755,750 | `e869f2a5c500aa0a5c74c680559c4e3ab7e65c7a442daa7c92b7f99fb51613ca` | OurAirports 机场表 |
| `05_airports/countries.csv` | 24,583 | `2a9dbee691125b0cdb8ceb5fe227c48c903f99c488963b8e53e2ab366521c639` | OurAirports 国家（不用） |
| `05_airports/navaids.csv` | 1,524,931 | `d7292380662c33a95214945023ec0a5b13189599305fd18be739e167a97a9bd1` | OurAirports（不用） |
| `05_airports/regions.csv` | 485,265 | `9220d6582b804cfdec8432e5bb21456699c9df8969bf5d8886beb62ff0b1318b` | OurAirports 地区 |
| `05_airports/runways.csv` | 3,973,691 | `62a2c7a9979e63b1ceed2553aa8d2bc3ad012340e4cb330663578aa500a309e5` | OurAirports 跑道 |

| 新下载 | 来源 | 大小 B | SHA256 | 内容 |
|---|---|---:|---|---|
| `IRENA_Global_Trade_Hydrogen_2022.pdf` | [irena.org](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2022/Apr/IRENA_Global_Trade_Hydrogen_2022.pdf)，2026-11-02 下载，HTTP 200 | 9,691,478 | `de6af56fe62a1223d431d770e77180ae27e66f19cb674eb96f594f8bdcac45e5` | 氢载体贸易（156 页）。氨船投资范围图 2.8、回程燃料"约每 5,000 km 1 % 货物"（p.44）；**不含甲醇**（p.9 明确排除含碳载体），没有吨公里单价表 |

同时引用的已有文件：`research_inputs/renewable_v5/regions_onshore.geojson`、`research_inputs/co2_v5/{PORTS_ASEAN_TO_NODES_S4D1,CO2_SHIP_ROUTES_S4D2,COASTAL_NODES_S4D1_FINAL,LAO_TRANSIT_S4D1}.csv`、`research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv`、`work/p1_s4r_downloads_20261020/F2_lng/gem-download (1).zip`。

## 12. 阶段 2 补记（2026-11-02）

### 12.1 APEC 表两次独立读取（D163-1 附）

用到的 APEC 数只有 VN，表在 PDF 第 161 页（书页 148），`p161_0_Image20.png`。

| 项 | 结果 |
|---|---|
| 第一次读取 | 原图，读合计列 |
| 第二次读取 | 裁剪工业部分放大 2 倍，读全部载体列 |
| 合计列 | 两次完全一致 |
| 子部门行合计 | 1,541.3 PJ，印刷工业合计 1,542 PJ |
| 列合计 | 煤 687.7 / 687、油 152.3 / 152、气 41.0 / 41、其他可再生 215 / 214、电 447.2 / 448（读数 / 印刷） |
| 行内合计 | 与印刷总计差 ≤ 1 PJ（四舍五入） |

矩阵见 `research_inputs/industry_v3/APEC2022_VN_INDUSTRY_PJ.csv`。

### 12.2 Wei et al. 2020（D163-2）

MDPI 对 curl 返回 403，改用内置浏览器读取。

| 项 | 值 |
|---|---|
| 文献 | Wei et al., Energies 13(21):5664，CC BY 3.0 |
| PDF | 1,312,606 B，SHA256 `8695d6c485b6c9e17d3cb575c636250e8925035c9aa82aa80ff9e5e106640d36`（浏览器内取得字节后计算） |
| 本地 PDF | **未能落盘**（浏览器下载未保存），只保留 SHA256 与表 8 摘录 `research_inputs/industry_v3/NICKEL_ENERGY_WEI2020.csv` |

### 12.3 船速来源（D161-2）

查 technology-data 条目所引原文献，均未取得：Runge et al. 2020（SSRN，人机验证页，未绕过）；Cihlar et al. 2020（欧盟出版局，Azure WAF 拦截）。按决定用 15 节 / 8,000 h（C 级）。

### 12.4 其他输入

| 文件 | 内容 |
|---|---|
| `pypsa-asean/data/temp_hard_coded/transport_data.csv` | PyPSA-Earth 各国车辆数，东盟合计约 2.65 亿，只作车队代理的量级对照 |
| `research_inputs/corridors/CORRIDOR_APG_CROSSCHECK_2024.csv` | APG existing，存量核查基准 |
| iScience 2025 SI Table S8、PNAS Nexus SI Table S4 | 存量核查对照 |

USGS 亚太卷表 3 第一栏核对：列为氧化铝、铝土矿、原铝，MY 原铝 750 kt（估计），解决第 2 节"列位待核"。
