# S4F 停止报告 01：线路 91 不是 Sadao–Chuping（第 97 项 a）

**时间：** 2026-10-17 09:40:21–09:43:55 UTC（限时核查约 3.5 分钟，上限 15 分钟）。
**性质：** 只读，只用已入库数据，没有修改任何模型、底网或 SHA 固定点。

**触发的规则（用户 2026-10-17 指示）：** 若线路 91 不是 Sadao–Chuping（端点或电压不符），停下报告，不要修改。

## 1. 冻结底网中的线路 91（VERIFIED）

来源：`results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc`。

| 属性 | 值 |
|---|---|
| bus0 / bus1 | MY_Peninsular2 0（101.54E, 4.98N）/ TH2 0（100.79E, 6.82N），两端都是聚类母线，v_nom 380 |
| type | Al/St 240/40 4-bundle 380.0（i_nom 2.58 kA） |
| num_parallel | 6.561513 |
| length | 275.36 km（聚类中心之间） |
| s_nom / s_nom_min | 380 / 380 MW |
| OSM 编号、几何 | 聚类线没有这两项；需经 pypsa-asean 的 `busmap` / `linemap` 回溯（见第 3 节） |

冻结底网中 TH–MY 交流线只有这一条。

## 2. s_nom 公式检查（VERIFIED）

- 按公式 √3 × v_nom × i_nom × num_parallel = √3 × 380 × 2.58 × 6.561513 = **11,142.1 MW**，不是 380 MW。
- 用默认线型或默认电压也推不出 380：
  - 380 kV 单回为 1,698 MW；
  - Sadao–Chuping 的 AIMS 线型（132 kV × 0.35 kA）为 80 MW；
  - OSM 244715547 的 4 条记录合计 884.8 MW。
- **380 MW 的来源已查明（VERIFIED）：** 作者原始运行的脚本 `research/00_source_provenance/official/author_run/scripts/final_asean_adjustment.py`。
  - `readjust_existing_interconnections`（第 296–347 行）把各国家对的存量跨境**交流线** `s_nom` / `s_nom_min` 改为 AIMS 2024 存量总量，并按长度分摊。其中 `("MY", "TH", 380)` 在第 309 行。
  - 配置开关 `readjust_existing_interconnections: true`（`configs/config.asean.yaml` 第 208 行）。
  - 这一步只改 `lines`，不改直流链路。所以 APG 的 380 MW（含 300 MW 直流）全部记在交流线 91 上，而直流链路仍保留 4 × 491.4（OSM）+ 300（AIMS），共 2,265.6 MW，形成重复计算。

## 3. 线路 91 的组成：不是 Sadao–Chuping

证据来自 pypsa-asean 本地运行 `baseline-aims-3H-tutorial` 的 `base.nc`、`elec_s.nc`、`elec_s_50.nc`、`busmap_elec_s*.csv`、`linemap_elec_s_50.csv`。各项为 VERIFIED；它与冻结底网的对应关系为 INFERENCE（见第 3 点）。

1. **Sadao–Chuping 本身：** 聚类前（`base.nc`）只有 OSM 244715547 的 4 条拆分记录跨越 TH–MY。
   - 132 kV，线型 243-AL1/39-ST1A，`num_parallel` 各 1.5，各 221.2 MW，17.4 km。
   - TH 端是 Sadao（100.43E, 6.68N），MY 端在 Chuping 附近（100.22E, 6.43N）。
   - 与 AIMS `new_lines.csv` 的 Sadao – Chuping（存量、132 kV、单回、24.7 km）是同一走廊。简化后为线路 1408（884.8 MW）。
2. **聚类时 Sadao–Chuping 被丢掉了：**
   - `busmap_elec_s_50.csv` 把 Chuping 一端的母线 844（MY）分进了泰国聚类 TH2 1，于是线路 1408 成为泰国聚类内部的线，在聚合时被丢弃（`linemap` 中没有 1408）。
   - 聚类后的 TH–MY 线（线路 31）由两条简化线组成：
     - **1599：** 马来西亚国内线，母线 844 → 857（Kedah），10,949.4 MW，`num_parallel` 6.448026。它因为 844 被归入泰国聚类而变成"跨境"。
     - **1393：** 泰国 115 kV 线 OSM 234442756，止于 Sungai Kolok / Rantau Panjang 边境变电站，192.7 MW，`num_parallel` 0.113487。简化时它的泰国端母线 563 被并进马来西亚母线 564，因此也变成"跨境"。
3. **与冻结底网的对应（INFERENCE）：**
   - 6.448026 + 0.113487 = 6.561513，与冻结底网线路 91 的 `num_parallel` 完全一致（6 位小数）。
   - 但冻结底网的聚类母线命名和坐标与教程运行不同，聚类线长度也不同（275 km 对 666 km）。可见是另一次聚类，但跨境成员集合相同。
   - 已入库资料中没有冻结底网自己的 `busmap`：作者运行目录只有配置、脚本和 `data/AEO8-input`。所以这一对应只能凭 `num_parallel` 推断。

**结论：** 线路 91 是聚类伪影下的 TH–MY 交流代表线。它的成员是一条马来西亚国内线和一条泰国 115 kV 边境线，端点和电压都与 Sadao–Chuping（132 kV 单回，Sadao–Chuping 两端）不符。按规则停下，**没有修改**线路 91、直流链路或 SHA 固定点。

## 4. 直流部分（已核实，未修改）

- **AIMS** `data/transmission_projects/AIMS/new_links.csv`：Khlong Ngae – Gurun，existing，2002 年，110 km，300 MW（VERIFIED）。
- **OSM 250878579-1_0 … -4_0：**
  - 4 条记录的 way id 相同，几何相同（100.45E 6.71N → 100.54E 5.81N，约 111 km），都是 300 kV、单回、`dc=True`；
  - 与 Khlong Ngae – Gurun 是同一条直流线的重复记录（VERIFIED）；
  - 在底网中各 491.4 MW，与 Khlong Ngae – Gurun 连在同样的两个母线 TH21 0 / MY_Peninsular22 0 上。

## 5. 需要用户决定

1. **推荐：** 线路 91 视为 TH–MY 交流的代表线，设为 80 MW。
   - 依据：AIMS 线型 94-AL1/15-ST1A（0.35 kA），√3 × 132 kV × 0.35 kA ≈ 80 MW；等价于 APG 总量 380 − 300。
   - 数据等级 C，注明"聚类伪影：成员线不是 Sadao–Chuping"。
   - 直流按 AIMS 记为 300 MW，删除 4 条 OSM 重复记录，TH–MY 合计 380 MW。
   - 原值作对照开关，更新 SHA 固定点。
2. 保留作者口径：线路 91 仍为 380 MW（APG 总量全部记在交流上），删除 4 条 OSM 重复记录**和** Khlong Ngae – Gurun，合计 380 MW，全部是交流。
3. 只删除 4 条 OSM 重复记录：线路 91 380 + 直流 300 = 680 MW，与 APG 不一致。
4. 暂不改动，TH–MY 存量维持 2,645.6 MW。

在用户答复之前，S4F-1 的实现与 S4F-2 以后各步都暂停。S4F-1 的口径已获同意（`lines.max_extension` = 20,000 MW，新增量口径，作用于交流线与 DC 链路），但还没有改代码。
