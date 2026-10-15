# 东南亚 CO2 地质封存：OGCI CO2 Storage Resource Catalogue（CSRC）Cycle 3 / Cycle 5 Appendix B Asia + Santos Bayu-Undan 新闻稿 数据提取

> 用途：ASEAN 11 国（BN, KH, ID, LA, MY, MM, PH, SG, TH, TL, VN）PyPSA 模型（各国 2050 净零）CO2 封存约束输入的补充来源。
> 原则：只记录文件中出现的数字，均附 文件 + 页码。凡提取者自行加总/比对/推断，一律标注 **【提取者核算】** 或 **【提取者判读】**，不得作为文献值引用。文献未给出的内容写 "not reported"。
> 页码约定：**C5 p.N** = Cycle 5 PDF 第 N 页（= 页脚 "Page N of 110"）；**C3 p.N** = Cycle 3 PDF 第 N 页（= 页脚 "Page N of 66"）；**Santos p.N** = 新闻稿 "Page N of 2"。
> 核对方式：文本用 `pdftotext -layout` 逐页提取；以图片嵌入的汇总表（C5 柬埔寨 Table 5-1、菲律宾 Table 16-1、东帝汶 Table 19-1）及饼图/柱状图已渲染为图像目视核对。

## 0. 输入文件与 SHA256

| 简称 | 文件 | SHA256 |
|---|---|---|
| C5 | `raw2/CSRC_Cycle_5_Appendix_B_Asia-_August_2025.pdf`（110 页；Date of Issue 20/08/2025；Halliburton + GCCSI 编写，C5 p.2） | `ff21cd340a252fee43321740742f5267a03a868c9ecf558b30c297b6138c6d0f` |
| C3 | `raw2/CSRC_Cycle_3_Appendix_B_Asia.pdf`（66 页；封面 "Cycle 3 Report March 2022"；Date of Issue 28/02/2022，Rev A01 28/03/2022；Storegga 编写，C3 p.1–2） | `bd68a1c1a0fc79f213e225196671bb36f1ebdb9b9d7e0610847a80ff33f839b1` |
| Santos | `raw2/210914_MOU-signed-on-Bayu-Undan-Carbon-Capture-and-Storage.pdf`（2 页，ASX/Media Release 14 September 2021） | `a08fffab3203ab70f100e91b5b318f8e33d894172911d7d32367d10d0791bfd5` |
| 对照 | `extraction/CO2_STORAGE_EXTRACTION.md`（ERIA 2024 / ADB 2013 / IEA 2021 提取） | `df6c9ac9721e0dc0e78b0fc93e290f070beaf115a8f5461c89876314feb29eba` |

（`raw2/` = `/mnt/user-data/outputs/p2_data_intake/raw2/`。同目录另有 Santos 新闻稿的德顿语版本 `210914-Bayu-Undan-...-Kampu-Bayu-Undan.pdf`，未纳入本提取。）

---

## 1. 通用说明（SRMS 类别、覆盖范围）

- **表格类别（原文印刷）**：每国汇总表行名为 `Stored / Capacity / Sub-Commercial / Undiscovered / Aggregated*`，两列为 `Project and no project` 与 `Project specified only`，单位一律为 **Gt**（"CO2 storage resource (Gt)"）。
- **与 SPE SRMS 的对应**（本附录未印出定义，以下对应来自任务说明，**非本文件内容**）：Stored = 已封存；Capacity = 商业级（封面称 "Commercial"）；Sub-Commercial = 已发现未商业化（Contingent）；Undiscovered = 未发现（Prospective）；Aggregated = 各成熟度类别之和。
- **Aggregated 脚注（每表原文）**："The aggregated resource represents the summed storage resource across all maturity classes and as such should not be viewed as representative of the potential of [country]."
- 图标题显示表值为 **"Mid-Case Storage Resource"**（例：C5 p.25、p.71、p.85 饼图标题）。
- 无 CCS 法规时资源被归为 "Inaccessible"（例：C5 p.43、p.94、p.105）；印尼 2024-01-30 法规后"can be re-classified"，但 C5 表值未改（C5 p.43）。
- **亚洲合计（封面）**：C5 p.1：Stored 0.001 Gt / Commercial 0 Gt / Sub-commercial 57 Gt / Undiscovered 4332 Gt；C3 p.1：Stored 0.0006 Gt / Commercial 0 Gt / Sub-commercial 57 Gt / Undiscovered 4275 Gt。
- **覆盖**：
  - C3 封面国家：Bangladesh, Brunei, China, India, Indonesia, Japan, Kazakhstan, Malaysia, Pakistan, South Korea, Sri Lanka, Thailand, Vietnam（C3 p.1）。**C3 不含 KH, LA, MM, PH, SG, TL**（全文检索仅在泰国 Fang 油田段落提到 "Myanmar" 作地名，C3 p.54）。
  - C5 覆盖全部 11 国（C5 p.1）。BN、ID、MY、TH、VN 在 C5 中的表值与 C3 **完全相同**（评估周期分别标为 Cycle 3 / 2 / 2 / 3 / 3）；KH、LA、MM、PH、SG、TL 为 **Cycle 5 新评估**。
  - C5 中文莱位于第 3 章（Bangladesh…）下的 3.6–3.12 节，目录未单列（C5 p.3, p.18）。

---

## 2. 分国提取

### 2.1 汇总总表（Project and no project 列；括号内为 Project specified only 列；单位 Gt）

| 国家 | 评估周期（原文） | 出现于 | Stored | Capacity | Sub-Commercial | Undiscovered | Aggregated* | 页码 |
|---|---|---|---|---|---|---|---|---|
| Brunei | Cycle 3 | C3, C5 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.558 (0.558) | 0.558 (0.558) | C5 p.18 Table 3-2；C3 p.13 Table 2-1 |
| Cambodia | Cycle 5 | C5 | 0.000 (0.000) | 0.000 (0.000) | 0.047 (0.000) | 0.085 (0.000) | 0.132 (0.000) | C5 p.24 Table 5-1（图片表，已目视核对） |
| Indonesia | Cycle 2 | C3, C5 | 0.00 (0.00) | 0.00 (0.00) | 2.46 (0.00) | 13.40 (4.39) | 15.86 (4.39) | C5 p.39 Table 8-1；C3 p.22 Table 4-1 |
| Laos | Cycle 5 | C5 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | C5 p.61 Table 12-1 |
| Malaysia | Cycle 2 | C3, C5 | 0.0 (0.0) | 0.0 (0.0) | 0.0 (0.0) | 149.6 (0.1；C3 印为 0.10) | 149.6 (0.1；C3 0.10) | C5 p.62 Table 13-1；C3 p.39 Table 7-1 |
| Myanmar | Cycle 5 | C5 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | C5 p.21 Table 4-1（与 Bhutan、Nepal 合表） |
| Philippines | Cycle 5 | C5 | 0.000 (0.000) | 0.000 (0.000) | 0.318 (0.000) | 23.000 (0.000) | 23.318 (0.000) | C5 p.70 Table 16-1（图片表，已目视核对） |
| Singapore | Cycle 5 | C5 | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | C5 p.76 Table 17-1 |
| Thailand | Cycle 3 | C3, C5 | 0.00 (0.00) | 0.00 (0.00) | 1.571 (0.011) | 8.9 (0.070) | 10.471 (0.011) | C5 p.89 Table 20-1；C3 p.50 Table 9-1 |
| Timor-Leste | Cycle 5 | C5 | 0.000 (0.000) | 0.000 (0.000) | 0.250 (0.000) | 0.000 (0.000) | 0.250 (0.000) | C5 p.84 Table 19-1（图片表，已目视核对） |
| Vietnam | Cycle 3 | C3, C5 | 0.00 (0.00) | 0.00 (0.00) | 0.924 (0.00) | 20.826 (0.076) | 21.750 (0.076) | C5 p.101 Table 22-1；C3 p.56 Table 10-1 |

所有 11 国 **Stored = 0、Capacity = 0**；无任何资源达到商业级。

### 2.2 Brunei（BN）
- **类型拆分**：全部为 Undiscovered（saline aquifer）。正文："only injection into the saline aquifer located below offshore gas discoveries is considered"（C5 p.18；C3 p.13）。CO2 资源量 = 多次模拟中注入咸水层的 CO2 体积（C5 p.19）。
- **盆地/层位**：Baram Delta B basin 的 Cycle V formation，在 17 个层位中 CO2-EOR 潜力排第 6（C5 p.19；C3 p.14）。无盆地级数值。
- **方法注意**："this is a very high-level study which was focused on providing an indication of the costs of CO2 capture and storage to allow monetisation of the gas discoveries across the APEC region. The technical evaluation of the actual storage resource is limited"（C5 p.19）。"Significant additional technical evaluation will be required"（C5 p.18）。
- **来源（Bibliography 原文）**：
  - [2] J. Shaw and S. Bachu, "Screening, Evaluation, and Ranking of Oil Reservoirs Suitable for CO2-Flood EOR and Carbon Dioxide Sequestration," J Can Pet Technol 41 (09), 2002.（C5 p.107；C3 p.62）
  - [3] CO2CRC Technologies Pty Ltd, "Assessment of the capture and storage potential of CO2 co-produced with natural gas in South-East Asia," Asia-Pacific Economic Cooperation, Sydney, Australia, 2010.（C5 p.107；C3 p.62）

### 2.3 Cambodia（KH）——表/文不一致的核对
- **表（C5 p.24 Table 5-1，图片表，高分辨率核对）**：Sub-Commercial **0.047 Gt**；Undiscovered **0.085 Gt**；Aggregated **0.132 Gt**；Project specified only 全为 0.000。
- **Summary 要点原文（C5 p.24）**："Three main formations within saline aquifers were discovered during this research as potential sites (**~65 Mt in total**). These formations also have hydrocarbon exploration but very little potential storage capacity upon depletion is cited (**~5 Mt in total**)."
- **Resource Review 原文（C5 p.27）**："the hydrocarbon reservoirs have storage capacity of **~5Mt in total for all three basins**, and a total of **~85Mt in saline aquifers**, making saline aquifers more viable for CO2 storage in Cambodia.[1]"
- **油气（C5 p.27）**："There are no depleted oil and gas field option in Cambodia." "Research performed by [1] using a storage efficiency factor of 7%, calculated that Cambodia's oil fields collectively have a potential to store approximately 5Mt of CO2"；Khmer Basin（45% 储量）**2 Mt**，Tonle Sap（35%）**2 Mt**，offshore Kampong Saom（20%）**1 Mt** "upon depletion"。
- **咸水层分盆地（C5 p.28）**：Khmer basin "~22Mt"（面积 ~8600 km²）；offshore Kampong Saom "~33 Mt"；onshore Tonle Sap "~30 Mt"（孔隙度平均 10%，局部 >20%，net 假设 20%）。
- **图**：Figure 5-1（C5 p.25）饼图：Undiscovered 64.4% / Sub-Commercial 35.6%；Saline 64.4% / Petroleum 35.6%。Figure 5-2（C5 p.26）"Mid Case Storage Resource by Site"：3 个 Undiscovered 站点（11418, 11419, 11417）+ 3 个 Sub-Commercial 站点（11420, 11422, 11421）；线性轴上 3 个 Sub-Commercial 柱均明显大于 5 Mt【提取者判读：目视，不读数】。
- **结论【提取者核算/判读】**：
  - **咸水层：85 Mt 正确，"~65 Mt" 为摘要笔误**。依据：22 + 33 + 30 = 85 Mt（与 p.27 "~85Mt" 一致）；= 表中 Undiscovered 0.085 Gt；0.085/0.132 = 64.4%，与 Figure 5-1 一致。65 Mt 在文件中无任何其他支持。
  - **油气：文件内部存在无法调和的两套数**——表/图 = **47 Mt**（Sub-Commercial 0.047 Gt；0.047/0.132 = 35.6%，与饼图一致），正文 = **~5 Mt**（2 + 2 + 1，7% 效率因子）。两者相差约 9 倍，附录未解释。且正文称"no depleted oil and gas field option"，却在表中以 Sub-Commercial（已发现类）列出 47 Mt。**需回查原始文献 Mao et al. (2014)**；在此之前建模宜视为不确定（保守取 ~5 Mt 或 0）。
  - 无论取哪一值，柬埔寨合计 ≤ 0.132 Gt（mid-case），对 2050 模型而言量级很小。
- **方法注意**："The resource reported for CO2 storage should be regarded as preliminary because of the limited available data"；地下数据受油气勘探政策限制（C5 p.28）。
- **来源（C5 p.29 原文）**：1. Mao, C., Yamada, Y. and Matsuoka, T. 2014. A preliminary assessment of geological CO2 storage in Cambodia, International Journal of Greenhouse Gas Control, 30, 19-33, DOI:10.1016/j.ijggc.2014.08.016,

### 2.4 Indonesia（ID）
- **类型拆分**：Summary 称 "saline aquifers accounting for 89% of Indonesia's storage resource"，33 个站点，6 个为 projects（C5 p.39；C3 p.22）；Figure 8-1c 饼图 Saline 89% / Petroleum 11%（C5 p.40；C3 p.23 相同）。但 C3 正文另称 "Saline aquifers account for the majority (**84%**) of Indonesia's resource"（C3 p.25；C5 删去此句）。"The only discovered resource for Indonesia is in oil and gas fields"（C5 p.39）。
- **油气田（盆地级，C5 p.42–43；C3 p.25–26）**：South Sumatra 13 个气田合计 **875 Mt**（占已发现资源 49%）；West Java Basin（离岸+陆上）**395 Mt**（22%）；其他盆地（油田：East Kalimantan, North Sumatra, South Sumatra, Barito；气田：Salawati, North East Java）合计 **528 Mt**（29%）。
- **咸水层**：basin-wide 资源仅 South Sumatra 与 West Java（采用 Hedriana et al. 2017 数值）；与高 CO2 气田相关的小型咸水层（CO2CRC 2010）占 Undiscovered 的 **31%**，分布于 5 个盆地（C5 p.43）。C3 另列小型盆地：Bintuni, East Natuna, South and North Sumatra, Kutai（C3 p.25）。无分盆地咸水层数值。
- **方法注意**：West Java 咸水层用 15 个气田体积数据 ×3 外推全盆地，"different method"（C5 p.44）；CO2CRC 站点"may not be in a good location"（C5 p.43）；Gundih 试点低于 10 Mt 阈值未列入（C5 p.42）；2024-01-30 CCS 法规后可重新分类（C5 p.43），但表值仍为 Cycle 2。
- **来源（Bibliography 原文，C5 p.107–108；C3 p.62–63）**：
  - [3] CO2CRC Technologies Pty Ltd, "Assessment of the capture and storage potential of CO2 co-produced with natural gas in South-East Asia," Asia-Pacific Economic Cooperation, Sydney, Australia, 2010.
  - [12] O. Hedriana, Sugihardjo and Usman, "Assessment of CO2-EOR and Storage Capacity in South Sumatera and West Java Basins," Energy Procedia, vol. 114, pp. 4666-4678, 2017.
  - [13] World Bank, "The Indonesia Carbon Capture Storage (CCS) Capacity Building Program: CCS for Coal-fired Power Plants in Indonesia," International Bank for Reconstruction and Development, Washington DC, 2015.
  - [14] U. P. Iksandar, Usman and S. Sofyan, "Ranking of Indonesia sedimentary basin and storage capacity estimates for CO2 geological storage," Energy Procedia, vol. 37, pp. 5172-5180, 2013.（正文拼作 "Iskandar"）
  - [15] Asian Development Bank, "Prospects for Carbon Capture and Storage in Southeast Asia," Mandaluyong City, Philippines, 2013.

### 2.5 Laos（LA）
- 全部 0.000 Gt（C5 p.61）。"There are no published reports or research to support that Laos has areas suitable for geological storage of CO2." Khorat Plateau Basin "may have potential suitable formations for CO2 storage, but this requires further research"；国家偏好农林碳汇（C5 p.61）。"Due to a preference to nature-based CO2 sequestration, Laos will not need future updates"（C5 p.61）。
- **来源（C5 p.61 原文）**：1. Lao People's Democratic Republic, 2021. Nationally Determined Contribution (NDC). https://unfccc.int/sites/default/files/NDC/2022-06/NDC%202020%20of%20Lao%20PDR%20%28English%29%2C%2009%20April%202021%20%281%29.pdf

### 2.6 Malaysia（MY）
- **类型拆分**："All storage resources assessed in this region are saline aquifers"（C5 p.65；C3 p.42）；Figure 13-1c Saline 100% / Petroleum 0%（C5 p.63）。全部 Undiscovered、Inaccessible（C5 p.62）。
- **盆地**：两个 basin-wide 咸水层（Junin & Hasbollah 从 14 个盆地筛选出 2 个，US-DOE 体积法；后文提及 Malay Basin 与 Greater Sarawak Basin）+ 与高 CO2 气田相关的项目站点（CO2CRC，Tangga Barat cluster, Malay basin）（C5 p.65–66）。**分盆地数值 not reported**（Figure 13-2 柱图仅以站点编号 10340–10345 标注，C5 p.64）。
- **方法注意**："basic volumetric calculations ... resource estimates having low confidence"；所有站点假设同一组储层参数；单值记为 'Mid-Range'（仅项目寿命排放量记为 'Low-Range'）（C5 p.65–66）。
- **来源（Bibliography 原文）**：
  - [29] R. Junin and D. Z. Abang Hasbollah, "CO2 Storage Capacity Assessment of Deep saline Aquifers in Malaysia," in World Academy of Science, Engineering and Technology, WASET 2016, London, U.K., 2016.（C5 p.109；C3 p.64 拼作 "malaysia"）
  - [30] "North American Carbon Storage Atlas," 2012.（C5 p.109）
  - APEC/CO2CRC (2010)（正文提及，MY 节未标编号；即 [3]）。

### 2.7 Myanmar（MM）
- 全部 0.000 Gt（与 Bhutan、Nepal 合表，C5 p.21）。
- 原文（C5 p.21–22）："the country was included in a review of the ASEAN countries to evaluate opportunities for a CCS industry in the region. **Myanmar was not selected as an option for CO2 storage [3]**. The country was also reviewed by the GCCSI in 2024 with a similar conclusion regarding storage potential in the country [4]." 未来："the country does have an oil and gas industry so may have potential in the future if depleted fields become of interest"（C5 p.22）。
- **来源（C5 p.22–23 原文）**：
  - 3. Zhang, K., Lau, H.C. 2022. Regional opportunities for CO2 capture and storage in Southeast Asia , International Journal of Greenhouse Gas Control, 116, 103628
  - 4. GCCSI, 2024. ERIA Research Project Report 2024, No. 16, Comprehensive CCUS Research Report: Storage, Value Chain, Policy & Regulation and Financing. https://www.eria.org/uploads/Comprehensive-CCUS-Research-Report.pdf
  - 6. Htun Kyaw Khine Sein, 2023, Low-Carbon Energy Sector Development in Myanmar. https://mekonginstitute.org/wp-content/uploads/2023/08/C4_Myanmar-Presentation_Breakout-Session-C_Mr.-Htun-Kyaw-Khine-Sein.pdf
  - （5. 为红树林碳汇文献，非地质封存。）
- 【提取者判读】ERIA 2024 原文是 "unknown as no analysis has been completed"，Central Myanmar 为 "Possible"（见对照文件 §2.9），OGCI 将其概括为 "similar conclusion"（即不选为封存选项），措辞上比 ERIA 更否定。

### 2.8 Philippines（PH）
- **类型拆分**：Figure 16-1B Saline 98.6% / Petroleum 1.4%；16-1A Undiscovered 98.6% / Sub-Commercial 1.4%（C5 p.71）。
- **站点（C5 p.70 原文）**："All reported Philippines hydrocarbon field storage resources were hosted in one unidentified field, (estimated storage capacity of about **251 Mt** CO2), one near- depleted gas field (estimated storage capacity of about **67.2 Mt**), and two saline aquifers of about **23 Gt** storage capacity in total." 站点：Malampaya gas field、Cagayan 与 Central Luzon Basins（咸水层）。
- **细节**：Malampaya（North Palawan Basin）67.2 Mt，其中 57.1 Mt "currently available today for injection"（引 GCCSI & ERIA 2024，C5 p.73）；ADB (2013) "one unidentified field, 251 Mt CO2 (total of 307 Mt CO2). This is included in the CRSC as a country wide entry. Caution should be applied ... possibly a collation of many small fields"（C5 p.73–74）；咸水层 "It cites a theoretical storage of 23 Gt"（ADB，C5 p.74）。Figure 16-2 仅显示 1 个 Undiscovered 站点（11423）与 2 个 Sub-Commercial 站点（11424, 11425）（C5 p.72）。
- 【提取者核算】251 + 67.2 = 318.2 Mt ≈ 表中 Sub-Commercial 0.318 Gt。
- **方法注意**：23 Gt 在 ADB 原文为 **theoretical** 容量，但 OGCI 将其作为 Undiscovered mid-case 直接入表（C5 p.74）；"Research on Philippines CO2 capacity is preliminary"（C5 p.70）。
- **来源（C5 p.74–75 原文）**：
  - 1. Global CCS Institute and Economic Research Institute for ASEAN and East Asia (ERIA). 2024. Comprehensive CCUS Research Report: Storage, Value Chain, Policy & Regulation and Financing. ERIA Research Project Report No. 16. Jakarta: ERIA
  - 2. Philippines Department of Energy. Philippine Presentation On Carbon Capture And Storage, http://www.ccop.or.th/eppm/projects/42/docs/Philippines_CCS_presentation_CCOP.pdf
  - 3. ADB, Global CCS Institute, Department of Energy & Climate Change. 2013. Prospects for Carbon Capture and Storage in Southeast Asia. ISBN 978-92-9254-290-0 (Print), 978-92-9254-291-7 (PDF) Publication Stock No. RPT135683-2

### 2.9 Singapore（SG）
- 全部 0.000 Gt（C5 p.76）。"The geology of Singapore is not suitable for geological storage of CO2. As such, there are no assessments in the public domain that have reviewed storage site potential."（C5 p.76）
- 跨境：2020 澳新 MoU；2022 与 Chevron、Mitsui O.S.K. Lines 研究液态 CO2 运往澳大利亚离岸封存；2023 英新 MoU；2024 与印尼签 Letter of Intent（跨境 CCS）；2024 选定 ExxonMobil 与 Shell 组成 S-Hub Consortium（C5 p.76）；EMA 为 Asia CCUS Network 成员（C5 p.77）。
- **来源（C5 p.77 原文）**：
  - 1. Seah, S., 2024. Carbon Capture, Utilisation and Storage (CCUS): A Singapore Perspective. Accessed 23/05/2025. https://www.twobirds.com/en/insights/2024/singapore/carbon-capture-utilisation-and-storage-ccus-a-singapore-perspective（原 URL 后附文本片段参数）
  - 2. Srivastav, P., Schenkel, M., Goher Ur Rehman Mir, Berg, T., and Staats, M. Carbon Capture, Utilisation and Storage, (CCUS): Decarbonisation Pathways for Singapore's Energy and Chemicals Sectors https://file.go.gov.sg/carbon-capture-utilisation-and-storage-decarbonisation-pathway-for-singapore-energy-and-chemical-sectors-pdf.pdf

### 2.10 Thailand（TH）
- **类型拆分**：39 个站点，2 个咸水层、37 个油气（C5 p.89）；Figure 20-1C Saline 85% / Petroleum 15%；20-1B Undiscovered 85% / Sub-Commercial 15%（C5 p.90）。【提取者核算】8.9/10.471 = 85%，与饼图一致。
- **来源分配**：油气田资源采用 ADB 2013（逐田值，替代重复的 Choomkong 2017）（C5 p.92）；咸水层 = ADB 2013 对 94 个盆地中 10 个盆地、>1000 m 地层的估算（C5 p.94）；CO2CRC 2010：Pattani Basin 高 CO2 气田附近咸水层 "a single site with **70Mt** resource"，模拟 20 年注入 70 Mt（C5 p.92, p.94）。
- **站点级数值**：Fang oil field **16 Mt**（Maneeintr 2017；模拟注入 1000/2000/4000 t/day，35/17/9 年）（C5 p.93）；Songkhla basin Bua-Ban **10.8 Mt**（Choomkong 2020，唯一 project 站点）（C5 p.93–94）；Bua-Ban lower Miocene 2.71 Mt、Rawangphai 2018 最多 2 Mt、Maneeintr 2018 6 Mt 均因 <10 Mt 阈值未列入（C5 p.93）。Pattani 与 Malay 盆地占油气站点 75%（C5 p.93）。分盆地合计 not reported。
- **方法注意**：ADB 咸水层 "estimated using rough pore volumes of all formations"（C5 p.92）；ADB 与 Choomkong 2017 可能重复计算（C5 p.94）；全部 Inaccessible（C5 p.94）。
- **来源（Bibliography 原文，C5 p.107–110；C3 p.62–65）**：[3]（见 BN）；[15]（见 ID）；
  - [45] A. Choomkong, "A study of CO2 Emission Sources and Sinks in Thailand," 2017.
  - [46] K. Maneeintra, "Evaluation for offshore carbon dioxide geological storage potential in the Gulf of Thailand," 9th International Conference on Applied Energy, Cardiff, 2017.
  - [47] A. Choomkong, "3D Modeling of CO2 Geological Storage of Songkhla Sub- Basins in the Lower Gulf of Thailand," International Journal of Integrated Engineering, 12, 2020.
  - [48] M. Rawangphai and K. Maneeintr, "Potential of carbon dioxide storage from petroleum industries in the Gulf of Thailand for green production," 2018.
  - [49] K. Maneeintr and Y. Hutthapong, "Simulation of CO2 Geological Storage Together with a Water Alternating Gas Process for Oil Production in Fang Oilfield (Thailand)," 2018.
  - 【提取者判读】正文将 Fang 油田研究归于 "Maneeintr 2017 [46]"，但 [46] 标题为 Gulf of Thailand 离岸评估，[49] 才是 Fang Oilfield；编号疑似错位。

### 2.11 Timor-Leste（TL）
- **类型拆分**：100% Petroleum、100% Sub-Commercial（Figure 19-1，C5 p.85）；Figure 19-2 仅 1 个站点（C5 p.86）。
- **原文（C5 p.87）**："The recently depleted Bayu-Undan field has been identified and secured for CCS project. The field has estimated storage capacity of **>250Mt CO2**, with potential for **>10Mtpa**. This field has 20 years of storage modelled, with potential for additional upside [1]."
- 咸水层："There is an absence of any literature in the public domain that reports on Timor-Leste's saline aquifer storage."（C5 p.87）
- 项目：2022-03 进入 FEED；2023 与 TIMOR GAP 签 MoU；Santos 43.4% operated interest（C5 p.87）。
- 【提取者判读】表中 0.250 Gt 对应文中 ">250Mt" 的下限值。尽管已进入 FEED，"Project specified only" 列仍为 0.000（C5 p.84）。
- **来源（C5 p.88 原文）**：
  - 1. National Authority for Petroleum and Minerals, Carbon capture and storage (CCS) , Presentation
  - 2. Govt Announces Ambitious Plan to Convert Bayu Undan Field into Major CCS Hub - TATOLI Agência Noticiosa de Timor-Leste
  - 3. Globally Significant Carbon Capture and Storage Project a Step Closer Globally significant carbon capture and storage project a step closer | Santos
  - （原文 [2]、[3] 标题各重复两次，此处去重；均无年份/URL；[1] 为演示文稿，非同行评审。）

### 2.12 Vietnam（VN）
- **类型拆分**：28 个站点，9 个咸水层、19 个油气（C5 p.101）；Figure 22-1B Undiscovered 96% / Sub-Commercial 4%；**Figure 22-1C Saline 48% / Petroleum 52%**（C5 p.102；C3 p.57 相同）。
- **油气田**：仅 Cuu Long 与 Nam Con Son 盆地，355 Mt 至 10 Mt；ADB 2013 给出 Cuu Long 12 个、Nam Con Son 2 个枯竭油气田；最大 CL16 **355 Mt**；Nam Vang field（Cuu Long，裂缝基岩）**43.2 Mt**（Vo Thanh 2019，E = 0.1–0.9）（C5 p.104–105）。
- **咸水层**：大型 basin play 资源（ADB 2013）"represent over 90% of the country's total resource"；小型咸水层（CO2CRC 2010）<1% 咸水层资源，3 个均为 project（C5 p.105），每个 "~25Mt"（C5 p.106）。分盆地数值 not reported。
- **方法注意**：basin play "only considering storage by structural/ stratigraphic trapping at depths greater than 1000m"，"estimation approach appears to be volumetric, although no methodology was given"（C5 p.104）；缺乏效率因子、孔隙度等数据（C5 p.105–106）；全部 Inaccessible（C5 p.105）。
- **来源（Bibliography 原文，C5 p.110；C3 p.66）**：[3]、[15]（同上）；
  - [50] V. Thanh, "Integrated workflow in 3D geological model construction for evaluation of CO2 storage capacity of a fractured basement reservoir in Cuu Long Basin, Vietnam," International Journal of Greenhouse Gas Control, 2019.

---

## 3. Santos 新闻稿（Bayu-Undan）

- 标题："Bayu-Undan Joint Venture and Timor-Leste's ANPM sign MOU on Bayu-Undan Carbon Capture and Storage"，14 September 2021（Santos p.1）。
- **原文（Santos p.1，Kevin Gallagher 引语）**："CCS at Bayu-Undan has potential capacity to safely and permanently store **approximately 10 million tonnes per annum of CO2** and could build a new job-creating and revenue-generating industry for Timor-Leste."
- **注意**：这是 **年注入/封存速率（Mt/yr）**，**不是总封存容量**；新闻稿中无总容量（Mt 或 Gt）数字。总容量见 OGCI C5 p.87 的 ">250Mt CO2"（来源为 ANPM 演示文稿）。
- 【提取者核算】10 Mt/yr × 20 年（C5 p.87 "20 years of storage modelled"）= 200 Mt，低于 >250 Mt，两者不矛盾。
- 股权（Santos p.2）：Santos 43.4%（operator）、SK E&S 25%、INPEX 11.4%、Eni 11%、Tokyo Timor Sea Resources 9.2%。

---

## 4. 对照表（ERIA 2024 / ADB 2013 / OGCI）

单位：Gt CO2（除另注）。ERIA、ADB 数值取自 `CO2_STORAGE_EXTRACTION.md`（页码为该文件所记原文页）；OGCI 为 mid-case，"Project and no project" 列。

| 国家 | ERIA 2024 P50 storage resource | ADB 2013 | OGCI（周期；Aggregated；类别构成） | 备注 |
|---|---|---|---|---|
| BN | O&G net 0.579；Saline 18（Tables 1.10, 1.12, p.35） | 未研究 | Cycle 3（C3/C5 相同）；**0.558**；全部 Undiscovered（saline）（C5 p.18） | OGCI 仅基于 CO2CRC 2010 单一层位；ERIA 咸水层高约 30 倍【提取者核算】 |
| KH | 未评估（"unknown as no analysis has been completed"，p.56） | 未研究 | Cycle 5；**0.132**；Sub-Commercial 0.047 + Undiscovered 0.085（C5 p.24） | 来源 Mao et al. 2014，ERIA 未采用；油气 47 Mt（表）vs ~5 Mt（正文）矛盾，见 §2.3 |
| ID | O&G net 2.275；Saline 49（Tables 1.4, 1.6） | 仅 South Sumatra：Saline 7.7（theoretical）；Oil 0.1、Gas 0.8（effective）；CBM 2.7（Fig 4.2 p.26） | Cycle 2（C3/C5 相同）；**15.86**；Sub-Commercial 2.46 + Undiscovered 13.40（C5 p.39） | OGCI 咸水层仅 South Sumatra、West Java + CO2CRC 小站点；ERIA 覆盖 Kutei/East Java/Central Sumatra |
| LA | 未评估（Greater Korat = Suitable，Table 1.19） | 未研究 | Cycle 5；**0.000**（C5 p.61） | OGCI 仅提及 Khorat Plateau "may have potential" |
| MY | O&G net 1.773；Saline 127（Tables 1.7, 1.9） | 未研究 | Cycle 2（C3/C5 相同）；**149.6**；全部 Undiscovered（saline）（C5 p.62） | OGCI 不含油气田；【提取者核算】ID 15.86 + MY 149.6 = 165.46，与 IEA 2021 所引 "some 165 Gt"（OGCI Cycle 2）一致 |
| MM | 未评估（Central Myanmar = Possible） | 未研究（仅提及向泰国供气） | Cycle 5；**0.000**（C5 p.21） | "not selected as an option for CO2 storage"（Zhang & Lau 2022） |
| PH | O&G net 0.067（Malampaya）；咸水层无数据（Table 1.18） | Saline 22.7（Fig 4.2）/ 23（App.2，theoretical）；Gas 0.3、Oil 0.0（effective） | Cycle 5；**23.318**；Sub-Commercial 0.318 + Undiscovered 23.000（C5 p.70） | OGCI = ADB 23 Gt theoretical + ADB "251 Mt" + ERIA 67.2 Mt，非独立评估 |
| SG | "no storage potential"（p.56） | 未研究 | Cycle 5；**0.000**（C5 p.76） | 三源一致：无国内封存 |
| TH | O&G net 1.024；Saline 15（Tables 1.13, 1.14） | Saline 8.9（theoretical）；Gas 1.3、Oil 0.1（effective）（Fig 4.2） | Cycle 3（C3/C5 相同）；**10.471**；Sub-Commercial 1.571 + Undiscovered 8.9（C5 p.89） | OGCI Undiscovered 8.9 与 ADB 咸水层 8.9 相同 |
| TL | 无国别分析 | 未研究 | Cycle 5；**0.250**；全部 Sub-Commercial（Bayu-Undan）（C5 p.84） | 唯一来源为 ANPM 演示文稿；Santos 只给 ~10 Mt/yr 速率 |
| VN | O&G net 0.303；Saline 5（Tables 1.15, 1.17） | Saline 10.4（theoretical，6 盆地）；Oil 0.6、Gas 0.7（effective）；CBM 0.5（Fig 4.2）；去除圈闭限制 >300（App.4 p.112） | Cycle 3（C3/C5 相同）；**21.750**；Sub-Commercial 0.924 + Undiscovered 20.826（C5 p.101） | OGCI 称 basin play 来自 ADB 且占 >90%，但 20.8 Gt 约为 ADB 咸水层 10.4 Gt 的 2 倍，附录未解释【提取者判读】 |

---

## 5. 不一致与注意事项

**OGCI 内部**
1. **KH 咸水层**：摘要 "~65 Mt"（C5 p.24）vs 正文 "~85Mt"（C5 p.27）、分盆地 22+33+30（C5 p.28）、表 0.085 Gt。→ 85 Mt 正确。
2. **KH 油气**：表 Sub-Commercial 0.047 Gt（C5 p.24）、饼图 35.6%（C5 p.25）vs 正文 ~5 Mt（2+2+1）（C5 p.24, p.27）；正文又称"no depleted oil and gas field option"。→ 文件内无法调和，需查 Mao et al. 2014。
3. **TH Project specified only 列**：Sub-Commercial 0.011 + Undiscovered 0.070 ≠ Aggregated 0.011（C5 p.89；C3 p.50 相同）；正文称唯一 project 为 Bua-Ban（C5 p.94），Figure 20-1A project 饼图 100% Sub-Commercial（C5 p.90）。→ 0.070（应为 CO2CRC 70 Mt 站点）在该列的归属存疑【提取者判读】。
4. **ID 咸水层占比**：89%（摘要 C5 p.39、饼图 C5 p.40）vs 84%（C3 p.25 正文）；【提取者核算】表值 13.40/15.86 = 84.5%，支持 84%。若咸水层占 89%，油气仅 11%，与 Sub-Commercial（全为油气）2.46/15.86 = 15.5%（饼图 b "16%"）矛盾。
5. **ID 已发现资源**：正文 875 + 395 + 528 = 1,798 Mt【提取者核算】（三者百分比 49/22/29 自洽），但表 Sub-Commercial = 2.46 Gt（C5 p.39, p.42–43）。
6. **VN 类型饼图**：Saline 48% / Petroleum 52%（C5 p.102）vs 表 Sub-Commercial 仅 4%（0.924/21.750）及正文 basin play ">90%"（C5 p.105）。VN 站点数：28（C5 p.101）vs 图注 "(24)"（C5 p.102）；basin play 数："six"（C5 p.104）vs "seven"（C5 p.106）。
7. **MY 站点**：正文"six sites: two basin scale saline aquifers ... and one project"（C5 p.62），而 Figure 13-2 显示 4 个 project 站点 + 2 个 basin 站点（C5 p.64）。
8. **BN**：摘要称潜力"present in both saline aquifers and oil and gas fields"，但表仅有 Undiscovered，正文称只考虑咸水层注入（C5 p.18–19）。
9. **PH**：正文"two saline aquifers"，但 Figure 16-2 只有 1 个 Undiscovered 站点（C5 p.70, p.72）——按国家级单条录入。

**跨文献**
10. **PH "251 Mt (total of 307 Mt)"**：OGCI（C5 p.73）沿用了 ERIA p.54 的表述；对照文件 §6 第 2 条记录 ADB 原文为油藏 35 Mt + 气田 287 Mt，最大离岸气田 251 Mt。【提取者判读】若 ADB 未命名的 251 Mt 大型离岸气田即为 Malampaya，OGCI 的 0.318 Gt 存在重复计算风险（ADB 251 Mt + ERIA Malampaya 67.2 Mt）；附录未说明，需核实。
11. **PH 23 Gt** 在 ADB 为 theoretical 容量，OGCI 记为 Undiscovered mid-case（C5 p.74）；ERIA 不认可该数（无咸水层数据，Possible/Unlikely）。
12. **VN**：OGCI CL16 = 355 Mt（C5 p.105）vs 对照文件中 ADB CL16 = 357 Mt（ADB p.113）；OGCI Undiscovered 20.826 Gt vs ADB 咸水层 10.4 Gt。
13. **BN**：OGCI 0.558 Gt（仅 1 个层位）vs ERIA 咸水层 P50 18 Gt + 油气 0.579 Gt——差 1–2 个数量级。
14. **MM**：ERIA "unknown"/Possible vs OGCI 引 GCCSI 2024 为 "similar conclusion"（不选为选项）。
15. **KH**：ERIA 称"no analysis has been completed"，但 OGCI 引用了 2014 年已发表的 Mao et al. 评估。

**建模提示（提取者意见，非文献内容）**
- OGCI 值为跨方法汇编的 mid-case，大部分为 Undiscovered 且全部 Inaccessible；Aggregated 脚注明确"should not be viewed as representative of the potential"。不宜直接作为可用封存上限。
- ID/MY/TH/VN/BN 在 C5 中未更新（仍为 Cycle 2/3 值），时效上不比 ERIA 2024 新。
- 对 KH、TL，OGCI 是目前文件中唯一有数值的来源（KH ≤ 0.132 Gt；TL 0.250 Gt + ~10 Mt/yr 速率）。LA、MM、SG = 0。
