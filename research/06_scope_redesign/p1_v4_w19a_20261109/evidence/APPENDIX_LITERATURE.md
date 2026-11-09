# W19a 附录：文献读取记录

访问时间为本会话内的 UTC（2026-11-08，工具未返回逐次时间戳，记录精度约 ±5 分钟）。引文只取短句。

| id | 来源 | URL / 本机文件 | 访问 UTC | 读取方式 | 定位 | 要点（短引或转述） | 等级 |
|---|---|---|---|---|---|---|---|
| L1 | Mao, Yamada & Matsuoka (2014) IJGGC 30:19–33 | https://repository.kulib.kyoto-u.ac.jp/dspace/handle/2433/191190 ；PDF 见 DOWNLOAD_CANDIDATES DC1 | 23:30Z 前后 | WebSearch 摘要；WebFetch 机构库 PDF 抽不出正文；ScienceDirect 403 | 摘要 | 全国 90 Mt（构造圈闭）至 45 Gt（水动力圈闭），低 / 高情形；Khmer 盆地最适宜；结果为初步 | INFERENCE（未读原文） |
| L2 | OGCI/CSRC Cycle 5 Appendix B Asia (Aug 2025) | 本机 `work/p2_data_intake/raw2/CSRC_Cycle_5_Appendix_B_Asia-_August_2025.pdf`，SHA256 `ff21cd340a252fee43321740742f5267a03a868c9ecf558b30c297b6138c6d0f` | 23:38Z 前后 | pypdf 抽字（scratchpad 单独目录）；OGCI 网站 403 | PDF 第 24、27 页 | 第 27 页："~5Mt in total for all three basins"、咸水层"~85Mt"，来源 [1] = Mao et al. 2014；第 24 页摘要写"~65 Mt"；表 5-1（图像表）0.047 + 0.085 = 0.132 Gt 取自仓库提取记录 `CO2_STORAGE_OGCI_EXTRACTION.md` | VERIFIED（文字）/ 表值沿用 |
| L3 | ERIA / GCCSI (2024) Comprehensive CCUS Research Report, Ch.1 | https://eria.org/uploads/1_Chapter-1-Geological-Storage-Potential-of-CO2-in-Southeast_Asia.pdf（WebFetch 存入工具缓存，SHA256 `1c36f7b00222446e72a778ae9687963e2f179cca51b8d84955c12c7053a0ca6a`） | 23:35Z 前后 | pypdf 抽字 | PDF 第 56 页 §1.3.9；第 63 页表 1.19；第 53 页表 1.18；第 54 页 | KH、LA、MM："currently unknown as no analysis has been completed"；Panjang 离岸三项为 Ⅹ；PH 只评 Malampaya，净 67.2 Mt | VERIFIED |
| L4 | IEA Cost of Capital Observatory, dashboard (2025 update) | https://www.iea.org/reports/cost-of-capital-observatory/dashboard | 23:51Z 前后 | WebFetch | 页面说明 | "local currencies, nominal terms and after tax"；负债成本取税后；未注明口径的回答按近十年平均通胀与公司税假设换算 | VERIFIED |
| L5 | IRENA (2022) Scaling up biomass for the energy transition: Untapped opportunities in Southeast Asia | 本机 `work/p2_data_intake/raw/IRENA_Biomass_Energy_Transition_2022.pdf`，SHA256 `bf52f40b9ffafb65993c6593f1dca0010194f5f36fce7b753919ad11e3e60f17` | 23:45Z 前后 | pypdf 抽字 | 第 42 页脚注 10；第 65 页脚注 17；第 85 页脚注 21；第 41 页；附录 A 第 138–139 页 | 收获残余"limited to 25% of total harvest residues"，以保证土壤质量与生物多样性；附录 A 只给 4 %、140 株/ha、2 t、含水 80 % | VERIFIED |
| L6 | IRENA (2017) Biofuel Potential in Southeast Asia | 本机 `work/p2_data_intake/raw/IRENA_Biofuel_Potential_SE_Asia_2017.pdf`，SHA256 `53a30811bebd2eb7e62aed8d8d6e0b401a25a347cb807cfca1069d633f567b2f` | 23:45Z 前后 | pypdf 抽字 | PDF 第 6 页正文与脚注 1；PDF 第 27 页表 R-3 | 收获后田间残余中可持续收集的份额"between a quarter and a half"；表 R-3 收获残余 25 %、加工残余 90 % | VERIFIED |
| L7 | 东盟公司所得税率 | WebSearch（DFDL、ASEAN Briefing、Grant Thornton 等） | 23:53Z 前后 | WebSearch | — | 结果来源年份混杂；本步税率取值为 INFERENCE | INFERENCE |
| L8 | D2b 证据 E60–E70（IEA、PyPSA-Eur、Hirth 2013、Noothout 2016、technology-data） | `work/p1_v4_d2b_20261108/evidence/DATA_UPG_B.json` | D2b 读取于 2026-11-08T16:13–16:27Z | 沿用 | 见原条目 | 见报告第 3.1 节 | VERIFIED（D2b） |

用户下载目录在本步前后无新文件（本步核对）。scratchpad 中的 PDF 副本与抽字文本不入库。
