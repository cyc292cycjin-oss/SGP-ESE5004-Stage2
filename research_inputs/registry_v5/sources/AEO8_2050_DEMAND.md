# AEO8 2050 终端能源需求 / 电力提取

- 输入文件：`/mnt/user-data/outputs/p2_data_intake/raw2/8th ASEAN Energy Outlook_SInO1OrPHSdovI5igUIm1SVQHgSGYPAkyoE6aL7R.pdf`（ASEAN Centre for Energy, 8th ASEAN Energy Outlook 2023–2050，204 页）
- SHA256：`48c2a81913ed785cb0e14a55e332ea7bc87f912f7fabfbc8c654e09b66b11c06`
- 页码约定：**PDF 页码 = 印刷页码 + 2**（例：C.2 位于 PDF p183，页脚印刷 "181"）。下文写作 "PDF p183 / 印 p181"。
- 机读版（同目录）：`AEO8_2050_ASEAN_TOTALS.csv`（C.2/C.3/C.5 的 2022 与 2050 值）、`AEO8_2050_BY_COUNTRY.csv`（C.8 人均指标 + D.1 人口）。
- 原则：仅抄录印刷值；未出现者写 "not reported"；换算值单独标注为 "派生"。

## 1. 情景（原文名称）

| 缩写 | 原文全称 | 出处 |
|---|---|---|
| BAS | Baseline Scenario | PDF p18 / 印 p16；p47 / 印 p45 |
| ATS | **AMS Targets Scenario**（p18、C.8 表头）；p47 写作 "ASEAN Member States Target Scenario (ATS)"；p47 情景框写 "ASEAN Member State Targets Scenario (ATS)" — 原文名称不统一 | PDF p18, p47, p189 |
| RAS | Regional Aspiration Scenario（AEO6/AEO7 的 APAEC Targets Scenario (APS) 的更新版） | PDF p47 / 印 p45 |
| CNS | Carbon Neutrality Scenario（新增） | PDF p47 / 印 p45 |

- RAS、CNS 电力部门采用 least-cost optimisation（LCO, NEMO）；BAS、ATS 不采用（Table 2.1, PDF p48 / 印 p46）。
- 建模工具：LEAP（需求侧）+ NEMO（供给侧优化）（PDF p17, p55）。
- 注意：AEO8 **没有** "APS" 情景（APS 是 AEO6/7 名称）。

## 2. 基准年与数据来源

- 基准（参考）年：**2022**；历史数据 2005–2022，预测期 2023–2050（PDF p18 / 印 p16；p47 / 印 p45；p9 "The reference year of 2022"）。
- 数据来源：**"Data and information were collected primarily from AMS National Focal Points, complemented by various datasets, as part of the ASEAN Energy Database System (AEDS)"**；电力数据与 ASEAN Interconnection Masterplan Study (AIMS) III 同步（PDF p6 / 印 p4）。
- 文档中 **未提及 UNSD** 作为数据源（not reported）。
- GDP：constant 2017 USD PPP，ADB 估计的 Covid 影响（PDF p190 / 印 p188）。
- TFEC 定义（Appendix E, PDF p202）："sum of energy consumption by end-use sectors, **excluding non-energy use and international transportation**"，终端部门含 agriculture, commercial, industrial, residential, transportation。→ 非能源用途（non-energy）**不在 TFEC 内**，不单列：**not reported**。

## 3. ASEAN 合计 TFEC by sector（Mtoe）— Table C.3, PDF p184 / 印 p182

| 部门 | 2022（历史） | BAS 2050 | ATS 2050 | RAS 2050 | CNS 2050 |
|---|---|---|---|---|---|
| Industry | 185.6 | 561.0 | 387 | 296.4 | 202.8 |
| Transport | 145.2 | 374.9 | 228.2 | 173.3 | 172.8 |
| Residential | 63.0 | 68.2 | 52.8 | 42.6 | 38.0 |
| Commercial | 29.5 | 75.9 | 50.4 | 37.6 | 29.1 |
| Agriculture and Others | 8.8 | 27.8 | 27.8 | 27.8 | 27.8 |
| **Total** | **432.2** | **1,107.9** | **746.2** | **577.7** | **470.5** |

- ATS 面板的 Industry 行以整数印刷（2022 = "186"，2050 = "387"），其他面板 2022 为 185.6。
- "Agriculture and Others" 四情景 2050 均为 27.8（印刷如此）；无单独 Non-energy 行。
- 部门加总核对（算术检查，非新数据）：ATS/RAS/CNS 精确吻合；BAS 部门和 = 1,107.8，与印刷总计 1,107.9 差 0.1（舍入）。

## 4. ASEAN 合计 TFEC by fuel（Mtoe）— Table C.2, PDF p183 / 印 p181

| 燃料 | 2022 | BAS 2050 | ATS 2050 | RAS 2050 | CNS 2050 |
|---|---|---|---|---|---|
| Coal | 71.4 | 222.2 | 145.8 | 107.2 | 20.6 |
| Oil | 182.1 | 448.8 | 245.6 | 184.8 | 57.2 |
| Natural Gas | 30.5 | 84.0 | 68.5 | 53.9 | 12.8 |
| Bioenergy | 37.0 | 115.3 | 105.5 | 79.7 | 104.8 |
| Traditional Biomass | 17.3 | 11.9 | 6.1 | 0.2 | 0.2 |
| Other heat（含 solar thermal） | 0.3 | 0.7 | 0.9 | 1.2 | 1.4 |
| **Electricity** | **93.7** | **225.0** | **172.7** | **149.7** | **217.6** |
| Hydrogen | 0.0 | 0.0 | 0.7 | 0.7 | 50.3 |
| SAF | 0.0 | 0.0 | 0.3 | 0.3 | 5.6 |
| **Total** | **432.2** | **1,107.9** | **746.2** | **577.7** | **470.5** |
| Electricity share of TFEC（印刷） | 21.7% | 20.3% | 23.2% | 25.9% | 46.2% |

## 5. 电力：终端电力消费与发电量（2050）

| 指标 | 2022 | BAS 2050 | ATS 2050 | RAS 2050 | CNS 2050 | 出处 |
|---|---|---|---|---|---|---|
| 终端电力消费（TFEC 中 Electricity, Mtoe） | 93.7 | 225.0 | 172.7 | 149.7 | 217.6 | C.2, PDF p183 / 印 p181 |
| 终端电力消费（TWh） | not reported | not reported | not reported | not reported | not reported | 文档未以 TWh 给出终端电力消费 |
| 发电量 Electricity generation（TWh） | 1,270.3 | 3,036.3 | 2,768.9 | 2,920.5 | 3,528.1 | C.5, PDF p186 / 印 p184 |
| 发电量（C.8 取整, TWh） | 1,270 | 3,036 | 2,769 | 2,920 | 3,528 | C.8, PDF p189 / 印 p187 |
| 装机容量（GW, C.8） | 315 | 818 | 1,115 | 1,436 | 1,586 | C.8, PDF p189 |

- 正文佐证：执行摘要 "3,036 TWh under the BAS, 2,769 TWh under the ATS, and 2,920 TWh under the RAS"（PDF p19 / 印 p17，未提 CNS）；"Under the ATS, the electricity demand will reach 173 Mtoe in 2050, surging by 73% from 2023"（PDF p95 / 印 p93）。
- 正文 TFEC 佐证：BAS 1,107.9 Mtoe（PDF p61 / 印 p59）；RAS 577.7 Mtoe，较 BAS −47.9%（PDF p62 / 印 p60）；ATS 较 BAS −32.7%（PDF p18, p61）。
- C.8 汇总（PDF p189 / 印 p187）TFEC：2022 = 432；BAS 2030/2050 = 587/1,108；ATS 513/746；RAS 467/578；CNS 436/471（与 C.2/C.3 一致）。

## 6. "BAS 2050 final electricity consumption = 225 Mtoe" 核查

- **确认存在**：Table C.2 TFEC by Fuel (Mtoe)，Baseline Scenario 面板，Electricity 行，2050 列 = **225.0**（PDF p183 / 印 p181）；同行 2050 share = 20.3%，CAGR 2022–2050 = 3.2%。正文 PDF p61："followed by electricity and coal, each accounting for 20.3%"。
- 派生换算（非文档数值）：225.0 Mtoe × 11.63 TWh/Mtoe = **2,616.75 TWh**，**不是 2,618 TWh**。即使考虑 0.05 Mtoe 的舍入区间（224.95–225.05），换算结果为 2,616.2–2,617.3 TWh，2,618 不在区间内 → 建议更正为 ≈2,617 TWh（派生）。
- 文档本身未印刷任何 "2,618" 或 "2,617" 数值。
- 说明：225.0 Mtoe 是**终端**电力消费（不含网损、自用），BAS 2050 发电量为 3,036.3 TWh（C.5），二者口径不同。

## 7. 分国（AMS）数据可得性

| 数据 | 是否存在 | 说明 / 出处 |
|---|---|---|
| 分国 2050 绝对 TFEC（Mtoe） | **not reported** | Appendix C 全部表格仅为 ASEAN 合计 |
| 分国 2050 终端电力消费 / 发电量（绝对值） | **not reported** | 同上；图表目录亦无 2050 分国电力图 |
| 分国人均指标（Primary energy / Final energy / Electricity consumption per capita） | **存在，但仅 ATS**，年份 2022、2030、2050 | C.8, PDF p189 / 印 p187 → `AEO8_2050_BY_COUNTRY.csv` |
| 分国人口 2005–2050 | 存在（情景间相同） | Table D.1, PDF p190 / 印 p188 → 已并入 CSV |
| BAS / RAS / CNS 分国数据 | **not reported** | — |

C.8 分国 ATS 指标摘录（单位按原文抄录，见下方警示）：

| 国家 | 人口 2050 (M, D.1) | Final energy/cap 2022 | Final energy/cap ATS 2050 | Elec. cons./cap 2022 | Elec. cons./cap ATS 2050 |
|---|---|---|---|---|---|
| Brunei Darussalam | 0.5 | 2,202.13 | 1,463.53 | 10,921 | 8,915 |
| Cambodia | 20.3 | 407.40 | 772.37 | 742 | 1,087 |
| Indonesia | 317.2 | 586.45 | 901.77 | 1,055 | 1,757 |
| Lao PDR | 9.8 | 537.17 | 569.71 | 1,289 | 2,133 |
| Malaysia | 41.0 | 1,404.75 | 1,659.92 | 4,835 | 6,742 |
| Myanmar | 59.9 | 241.24 | 223.94 | 250 | 463 |
| Philippines | 157.9 | 299.16 | 346.72 | 790 | 1,101 |
| Singapore | 5.9 | 2,242.04 | 2,149.37 | 9,861 | 11,324 |
| Thailand | 67.9 | 1,144.02 | 1,996.20 | 2,880 | 5,191 |
| Vietnam | 107.0 | 698.56 | 1,435.44 | 2,446 | 4,734 |

**单位警示**：原文标签为 "Final energy per capita (TFEC/Pop; ktoe/1000 persons)" 与 "Electricity consumption per capita (kWh/1000 persons)"。按字面单位，数值量级不合理（例如 Indonesia 586.45 ktoe/1000 人 = 0.586 ktoe/人），更可能为 kgoe/人 和 kWh/人，但**文档未说明**，本文件不做更正。若用 "人均 × 人口" 推算分国绝对量，属于派生估算，须另行标注并与 ASEAN 合计核对后方可使用。C.8 同块中的 "Emission per capita" 数值（如 Indonesia 0.09）亦存在明显量级问题，未纳入。

## 8. 文档内部数据质量问题（发现即记录，未修正）

1. **C.6 "Emission by Sector (MtCO2-eq)"（PDF p187 / 印 p185）**：表体与 C.5 发电量表逐值完全相同（Coal 2050 BAS = 946.3 等），属排版复制错误；不可作排放数据使用。
2. **C.1 TPES by Fuel（PDF p182 / 印 p180）**：BAS 面板 "Electricity" 行 2050 = 1,822.6（与 C.8 的 BAS TPES 1,823 一致，疑为 Total 错放），"Total" 行 = 1,219.5（与 ATS 的 C.8 TPES 1,220 相同）；ATS 面板 Total 同为 1,219.5；RAS 面板 Total 2050 = 577.7（= RAS 的 TFEC，而 C.8 给 RAS TPES = 1,012）。TPES 不在本次范围，仅提示 C.1 总计行不可直接引用，应以 C.8 为准并标注不一致。
3. C.3 中 "Agriculture and Others" 四情景完全相同（27.8 Mtoe），可能为该部门未做情景差异化建模；文档未解释。
4. ATS 名称在文档内有三种写法（见 §1）。
