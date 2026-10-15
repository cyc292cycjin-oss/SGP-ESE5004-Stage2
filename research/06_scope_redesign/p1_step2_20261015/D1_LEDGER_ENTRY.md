## D1 数据加工与数据登记 — 2026-10-15

- **范围：** S2 前置数据步骤（D1_DATA_INSTRUCTION.md）。只读 `work/p2_data_intake/`，新增 `research_inputs/{registry_v5,demand_v5,biomass_v5,cost_layers_v5,lng_terminals_v5}/`、10 个 `scripts_project/d1_*.py` 与 `tests/research/test_d1_registry.py`；不改原始数据、不构建、不求解。分支 `codex/d1-data-registry-20261015`（自 S1 929c35c7）。
- **登记表：** `DATA_REGISTRY.csv` 669 行（A 201 / B 206 / C 262；DATA_PENDING 98），每行带来源定位、SHA256、脚本、敏感性区间；18 个单位换算系数单独登记（UNSD 2014、IPCC 2006、NIST SP 811、FRED、ECB）。
- **CO₂ 封存（Gt，主算 / 低 / 高）：** MY 128.77 / 80 / 198.8；ID 51.28 / 8.4 / 77.3；PH 22.3 / 0.07 / 23.3；BN 18.58 / 0.56 / 25.6；TH 16.02 / 10 / 23.0；VN 11.8 / 5.3 / 21.75；TL 0.25；KH 0.085；LA/MM/SG 0；年注入上限 = 潜力 ÷ 50。
- **价格与供给上限：** WEO 2025 NZE 2050 → EUR2020/MWh(NCV) 原油 11.62、LNG 13.67、煤 5.17（STEPS 2050 为高价敏感性）；GEM LNG 现有能力 TH 19.0、PH 14.7、ID 11.75、SG 11.0、MY 7.3、VN 4.0 Mtpa，上限 2.5×，已映射节点；UNSD 2019 国内煤/气/油产量上限按国登记（气为 gross production 上界）。
- **成本口径（决定 46 方案 A）：** 作者 `append_cost_data.py` 规则逐行解码并复现（51 值相对差 1.9e-15）：ECB 2020 年均 FX 0.877229；D.17 衰减只在标签相同处生效，"Solar PV"≠"Solar" 致光伏零衰减，FOM% 以衰减后资本为分母被放大。A 层 technology-data v0.13.2 2050（主算）与 B 层 AEO8 作者规则（敏感性）通过 `research.cost_layer` 切换；SMR 8,421 EUR2020/kW、FOM 1.146 %/a、VOM 1.93 EUR/MWh（C 级 ±30 %）；存量地热 FOM 2.0 %/a、寿命 30 年（B 级），效率/VOM/投资在 v0.13.2 中缺失。technology-data v0.13.4 仅 4 行变化、v0.15.0 改为 2025 年价（+25.7 %）并大改核燃料/HVDC/FT，不升级，交用户决定。
- **需求 2050：** 基年 UNSD 2019 冻结重建 + 电力分部门；东盟十国分部门合计 = AEO8 BAS 2050（相对误差 2e-16）；国别按 GDP 乘数分配并校准（k：工业 1.206、交通 1.417、居民 0.295、商业 0.923、农业其他 1.014），人口法作敏感性；电力行标记为已在 Astar 2,617.8 TWh 中（表内 2,395.8 TWh，比值 0.915，未调参）；非能源按工业乘数、舱燃料 2019 常数，BN/KH/LA/TL 航运舱燃料 DATA_PENDING。
- **份额与生物质：** PyPSA-Eur v2025.07.0 47 项份额按行号登记（采暖 3 项不适用）；IRENA 2017 R-3→R-1a 复现误差 ≤1.6 %，FAOSTAT 当前版复现 −2～−18 %；11 国 2050 潜力约 8,670 PJ（ID 4,068、TH 1,410、MY 1,069、PH 687、VN 663、MM 453、KH 220、LA 90），成本 C 级 ±50 %（NRI/NEDO 2024、ERIA/IEEJ 2024）。
- **待下载：** EDGAR_2025_GHG、USGS MCS 2025 水泥/钢、UNSD 四国舱燃料、伐木残余系数、油棕树干价格、WaW 老挝成分、LA/MM 封存评估、GEM 无容量单元、LNG 再气化费、地热发电参数（11 项）。
- **交付：** `research/06_scope_redesign/p1_step2_20261015/`（D1_REPORT.md、DATA_REGISTRY.csv、DATA_PENDING_LIST.csv、DOWNLOAD_LIST.csv、D1_EVIDENCE.json、D1_TEST_RUN.json、测试日志）。
