# 东盟新建抽蓄（PHS）：潜力、成本与加入模型的方式（V4 D1 第 6 节；只做研究与建议，不改模型）

- **性质：** 研究与建议。本次不改网络、不改注册表中的抽蓄行、不改存量抽蓄的处理；是否加入、按哪种方式加入由用户决定。
- **标记：** VERIFIED（读到的原文、网络或注册表中的数）、EXACT（可复现的算术）、INFERENCE（推断、换算）、PROPOSED（建议，未实施）。
- **证据：** `evidence/PHS_LITERATURE.json`（47 条：URL、访问 UTC、原文短引文、页码 / 表号；检索子代理整理，本会话逐条过目）；`evidence/PHS_MODEL.json`（从 W08 主算网络 `integrated_365_24h_unsolved.nc` 读出的抽蓄组件与成本行，脚本 `scripts/d1_phs_model.py`）。货币换算用注册表口径：`deflator_usd_2024_to_2020` = 0.839076、`fx_usd_to_eur_2020` = 0.877229，USD2024 → EUR2020 = 0.736061（EXACT）。

## 0. 结论摘要

1. **模型现状（VERIFIED）：** 网络中已有抽蓄两类组件。(a) 存量 `PHS existing` 合计 **5,406 MW**（ID 1,040、PH 856、TH 2,310、VN 1,200），这就是"存量抽蓄 5.4 GW"；(b) 新建候选 `PHS_new` 共 13 个节点、上限合计 **14,438 MW**（ID 2,400、LA 100、PH 7,958、TH 2,480、VN 1,500），上限取 GEM 管线中"已宣布 + 前期"项目（第 78、86 b 项），其余 6 国上限为 0。两类都是 `StorageUnit`，**固定 6 h**、充放电各 √0.75（往返 0.75），候选年化成本 184,507.76 EUR/MW/a = technology-data v0.15.0 的 2,297.34 EUR2020/kW（只有功率成本，80 年，FOM 1 %，贴现 7 %；EXACT 复算）。
2. **存量对账（VERIFIED / INFERENCE）：** IHA 给出的 2024 年在运抽蓄只有 **2,260 MW**（TH 1,531、PH 729），Rystad 2024 为 2.3 GW。模型的 5,406 MW 是 **2050 年存量**，含在建的 Upper Cisokan（ID 1,040 MW，世界银行项目关账 2028）与 Bac Ai（VN 1,200 MW，EVN 计划 2029–2031 年投产），这两项计入 2050 年存量是合理的（INFERENCE）。**未解释的差额：TH 模型 2,310 对 IHA 1,531 MW（多 779 MW），PH 856 对 729 MW（多 127 MW）**。TH 中 `TH2 4` 节点 950 MW 的冻结存量机组（原为 Hydro）可能把 Bhumibol 等坝的常规机组算成了抽蓄（INFERENCE，未核实）。按指令，存量处理不变；列为待决第 1 条。
3. **潜力（VERIFIED）：** 资源量不是约束。Lu et al. (2021) 写东南亚离河抽蓄（STORES）总潜力约 200 万 GWh，其 100 % 可再生情景所需仅占 0.8–2.2 %；新加坡、文莱没有站点。ANU 2025 综述（Blakers, Weber & Silalahi）给出 A/AA/AAA 级短名单（不是全量）：ID 103、LA 62、MY 62、MM 62、VN 62、PH 42、TH 16 TWh；KH、BN、SG、TL 不在表中。全量逐国数据需向 ANU 申请（下载候选）。
4. **成本（VERIFIED / INFERENCE）：** 东盟专门研究的成本远低于模型现用值。Lu 2021：560 USD2020/kW + 50 USD2020/kWh，FOM 7 USD/kW/a，50 年，往返 0.80；ANU 2025 基准（A/B 级分界）：658 USD2024/kW + 58 USD2024/kWh，往返约 0.80。折成 EUR2020：**6 h 约 740–754 EUR/kW，24 h 约 1,509–1,544 EUR/kW**；模型现用 2,297 EUR/kW（6 h），是东盟研究 6 h 值的约 3.1 倍（INFERENCE）。美国 NREL ATB 2024 的 10 h 闭环抽蓄为 1,730–4,501 USD2021/kW，量级接近 technology-data（欧洲 DIW 数据）。
5. **建议（PROPOSED）：** 方式 B（下文第 5 节：能量与功率分开建模的 Store + 两条 Link，或三档时长的 StorageUnit）+ 成本取东盟研究值（Lu 2021 或 ANU 基准，technology-data 作敏感性）+ 上限取 ANU 短名单（能量）与国家规划（功率，近期）两档，节点按 ANU 站点坐标就近分配（暂用现有候选节点分配）。往返效率 0.80。是否加入、成本口径与上限口径由用户决定（待决第 2–4 条）。加入会改变 2920×3h 下电池与抽蓄的分工（W15：3 h 分辨率使电池放电 484 GW，INFERENCE：便宜的长时抽蓄可能替代其中一部分）。

## 1. 模型现状（VERIFIED，`evidence/PHS_MODEL.json`）

| 组件 | 国家 | 节点（台数） | p_nom / 上限 MW | 时长 h | 往返效率 | 年化成本 EUR/MW/a | 来源 |
|---|---|---|---:|---:|---:|---:|---|
| PHS existing | ID | ID_Java-Bali1 0（1） | 1,040 | 6 | 0.75 | 0 | S4A 增补（Upper Cisokan，在建，2050 存量） |
| PHS existing | PH | PH_Luzon5 0（2） | 736 + 120 = 856 | 6 | 0.75 | 0 | 冻结存量（Kalayaan）+ S4B-1 增补 |
| PHS existing | TH | TH2 4、GEM、TH2 2（3） | 950 + 1,000 + 360 = 2,310 | 6 | 0.75 | 0 | 冻结存量 + GEM（Lam Ta Khong）+ S4A |
| PHS existing | VN | VN2 4（1） | 1,200 | 6 | 0.75 | 0 | S4A 增补（Bac Ai，在建，2050 存量） |
| **存量合计** | | | **5,406** | | | | |
| PHS_new | ID | Java-Bali1 0 / 1、Sumatra3 5 | 2,400 | 6 | 0.75 | 184,507.76 | `candidate_cap_PHS_ID`（GEM 管线） |
| PHS_new | LA | LA2 4 | 100 | 6 | 0.75 | 184,507.76 | `candidate_cap_PHS_LA` |
| PHS_new | PH | PH5 0、Luzon5 0、Visayas7 0 | 7,958 | 6 | 0.75 | 184,507.76 | `candidate_cap_PHS_PH` |
| PHS_new | TH | TH2 2、TH2 5 | 2,480 | 6 | 0.75 | 184,507.76 | `candidate_cap_PHS_TH` |
| PHS_new | VN | VN2 1、VN2 4 | 1,500 | 6 | 0.75 | 184,507.76 | `candidate_cap_PHS_VN` |
| **候选上限合计** | | | **14,438** | | | | 节点分配 `research_inputs/potentials_v5/CANDIDATE_CAPS_S4B2_BY_NODE.csv` |

- 成本行 `cost_C_PHS_*`（technology-data v0.15.0 → EUR2020）：investment 2,297.34 EUR/kWel、FOM 1 %/a、efficiency 0.75、lifetime 80 a；年化 = 2,297,342 × (0.070314 + 0.01) = 184,507.76 EUR/MW/a（EXACT，与网络中的 `capital_cost` 相同）。
- 结构：`StorageUnit` 的能量 = p_nom × max_hours，时长不能由模型选择；功率与能量没有分开计价。

## 2. 存量对账（第 0 节第 2 条）

| 国家 | 模型 2050 存量 MW | IHA 2024 在运 MW | 在建 / 已定项目 | 差额与读法 |
|---|---:|---:|---|---|
| ID | 1,040 | 0 | Upper Cisokan 1,040（世界银行 P172256，2028 关账） | 一致：2050 存量含在建项目（INFERENCE） |
| VN | 1,200 | 0 | Bac Ai 1,200（EVN：2029-12 至 2030-12 逐台投产） | 一致（同上） |
| TH | 2,310 | 1,531 | 新增约 2.47 GW 规划（首台约 2034，未定） | **多 779 MW 未解释**；`TH2 4` 950 MW 的冻结存量机组疑含常规水电（INFERENCE） |
| PH | 856 | 729 | GEA-3 抽蓄标段 4,250 MW（2028–2035 交付） | 多 127 MW（Kalayaan 维基 684.6 MW，IHA 729 MW，模型 736 + 120） |
| 合计 | 5,406 | 2,260 | | |

## 3. 逐国潜力、需求量级与规划（VERIFIED 原文数；时长为 GWh / GW 的 INFERENCE）

| 国家 | ANU 2025 A–AAA 短名单（站点数 1500/500/50 GWh；TWh） | Lu 2021 孤立系统储能需求 GW / GWh（低 / 中 / 高） | 隐含时长 h | 国家规划 / 管线 | 模型候选上限 MW |
|---|---|---|---|---|---:|
| ID | 50/50/50；103 | 331 / 4,172；742 / 12,278；1,188 / 20,534 | 12.6 / 16.5 / 17.3 | RUPTL 2025–2034 抽蓄 4.3 GW（Cisokan 1,040、北苏 500、Matenggeng 943、Grindulu 1,000、Jatiluhur 760） | 2,400 |
| PH | 20/20/30；42 | 121 / 1,544；300 / 5,645；480 / 9,179 | 12.8 / 18.8 / 19.1 | GEA-3 目标 4,250 MW，授标 > 6 GW | 7,958 |
| VN | 30/30/30；62 | 25 / 360；98 / 2,068；184 / 5,466 | 14.4 / 21.1 / 29.7 | 修订 PDP8：2030 年 2,400–6,000 MW，2050 年 20,691–21,327 MW（二手摘要） | 1,500 |
| TH | 3/20/30；16 | 15 / 125；37 / 464；107 / 1,905 | 8.3 / 12.5 / 17.8 | EGAT 三座坝扩建 2,472 MW，首座约 2034 | 2,480 |
| MY | 30/30/30；62 | 63 / 341；72 / 384；123 / 933 | 5.4 / 5.3 / 7.6 | 未找到具体项目（INFERENCE） | 0 |
| MM | 30/30/30；62 | 60 / 1,321；139 / 2,955；216 / 4,580 | 22.0 / 21.3 / 21.2 | — | 0 |
| KH | 不在表中 | 22 / 414；46 / 1,056；71 / 1,625 | 18.8 / 23.0 / 22.9 | Upper Tatay 1,000 MW 已开工（IHA） | 0 |
| LA | 30/30/30；62 | 1 / 11；6 / 63；16 / 264 | 11.0 / 10.5 / 16.5 | 未找到具体项目 | 100 |
| TL | 不在表中 | 2 / 37；4 / 123；6 / 220 | 18.5 / 30.8 / 36.7 | — | 0 |
| BN、SG | 不在表中（无站点） | 用电池（BN 0.2 GW / 1 GWh） | — | — | 0 |

- ANU 短名单是"从 A、AA、AAA 级中挑选、分散布置"的一部分站点，按人口与可得性大致配比，**全量远大于此**（东南亚约 200 万 GWh）。表中东盟七国短名单合计 409 TWh，远超同表所列的 2050 年需求（七国合计 38.4 TWh，按约 50 kWh / 人估；ANU 第 3 表的经验值为东盟约 26 h 年均负荷）。
- Lu 2021 的需求量是 100 % 风光、各国孤立运行的结果，只作量级参照，不是潜力。

## 4. 时长、效率与成本（VERIFIED；换算 INFERENCE）

| 来源 | 功率成本 | 能量成本 | 6 h 合计 EUR2020/kW | 24 h 合计 EUR2020/kW | FOM | 寿命 | 往返效率 |
|---|---|---|---:|---:|---|---|---|
| Lu et al. 2021 Table 3（USD2020） | 560 /kW | 50 /kWh | 754.4 | 1,543.9 | 7 USD/kW/a（6.14 EUR） | 50 a | 0.80 |
| ANU 2025 基准（A/B 级分界，USD2024） | 658 /kW | 58 /kWh | 740.5 | 1,508.9 | — | 60 a（ANU 2021 综述计价用） | ≈ 0.80 |
| ANU 等级 E（≈ 2 × 基准） | | | ≈ 1,481 | ≈ 3,018 | | | |
| technology-data v0.15.0（模型现用，DIW） | 2,297.34 EUR/kW（只有功率） | — | 2,297.3 | —（模型固定 6 h） | 1 %/a | 80 a | 0.75 |
| NREL ATB 2024 美国 10 h 闭环（USD2021） | 1,730–4,501 /kW（按资源等级） | 含在内 | — | — | — | — | 0.80（文献 0.70–0.87） |

- 时长：ANU 地图集按 6 / 18 / 50 / 168 / 504 h 档搜索；在建项目约 6–7 h（Upper Cisokan 按 1,000 万 m³、276 m 水头、0.9 推得约 6.8 GWh、6.5 h，INFERENCE）；Lu 2021 最优解 0–38 h，多数国家 12–23 h。
- 效率：ANU、Lu、NREL 都取往返约 0.80；technology-data 0.75（PyPSA-Eur 把它拆成充放电各 √0.75）。

## 5. 加入模型的方式（PROPOSED，三项选择，均需用户决定）

**5.1 结构（推荐 B）**
- **A（最小改动）：** 保留 `StorageUnit`，把每个候选拆成 6 / 12 / 24 h 三档，年化成本 = 年金 × (功率成本 + h × 能量成本)，往返 0.80；模型在三档之间选择。实现只改 `apply_candidate_caps` 的候选生成与成本行。
- **B（推荐）：** 与 PyPSA-Eur 电池相同的写法——每个候选节点一个可扩展 `Store`（能量，EUR/MWh 年化）+ 两条可扩展 `Link`（抽水 √0.80、发电 √0.80，功率成本记在发电链路，抽水链路与之容量相等的约束复用现有双向同步钩子的写法）。时长由优化决定；需新增一个约束钩子与测试。
- 两种结构都与现有存量 `PHS existing` 并存，存量不变。

**5.2 成本（三选一，另两项作敏感性）**
1. Lu 2021（东盟专门研究，2020 美元，有 FOM 与寿命）：功率 491.25 EUR2020/kW、能量 43.86 EUR2020/kWh、FOM 6.14 EUR/kW/a、50 a；
2. ANU 2025 基准：484.33 EUR2020/kW + 42.69 EUR2020/kWh（等级 E 加倍作上界敏感性）；
3. technology-data（现用，与 PyPSA-Eur 一致）：2,297.34 EUR2020/kW、6 h。
- 推荐 1 作主算、3 作敏感性：东盟研究的站点条件（高水头、闭环）与成本口径（功率 + 能量）都更适合本模型；technology-data 值来自欧洲 DIW 旧数据，且不区分时长。

**5.3 上限与节点**
- 上限两档：(i) 近期可建 = 现行 GEM 管线上限（14,438 MW，主算现状）；(ii) 资源 = ANU 短名单能量（TWh）、功率不另设上限（或按 Lu 2021 高情景 GW 作上界）。KH 加入 Upper Tatay 1,000 MW 与 Lu 2021 量级；SG、BN 为 0。
- 节点：按 ANU 站点坐标就近分配到 AC 节点（需 ANU 逐国站点表，向 ANU 申请，见 `DOWNLOAD_CANDIDATES.csv`）；在拿到之前沿用 `CANDIDATE_CAPS_S4B2_BY_NODE.csv`，无候选的国家按该国存量水库水电的节点份额（INFERENCE 代理）。

**5.4 实施与验证（若用户同意）：** 新开关 `research.s4b.phs_candidates: gem_pipeline (现状) | anu_cost_storage`；注册表登记 Lu / ANU 成本行与上限行；单元测试（开关关时与现状逐字节相同）；56 时段冒烟比较电池与抽蓄的分工；不在 2920×3h 正式批次前未经冒烟加入。

## 6. 待决问题（交用户 / 审阅端）

1. **存量对账：** TH 模型 2,310 MW 比 IHA 1,531 MW 多 779 MW、PH 多 127 MW——是否核查 `TH2 4` 950 MW 冻结存量机组的抽蓄 / 常规属性（不改存量处理，只核数）。
2. **是否加入新建抽蓄的改进候选**（5.1 结构 A 或 B）。
3. **成本口径**（Lu 2021 / ANU / technology-data）。现用值约为东盟研究 6 h 值的 3.1 倍，可能低估抽蓄、高估电池的作用（INFERENCE）。
4. **上限口径**（GEM 管线 / ANU 资源）与是否加入 KH、MM、MY 的资源候选。

## 7. 来源（访问时间见 `evidence/PHS_LITERATURE.json`）

- Lu, B., Blakers, A., Stocks, M., Do, T.N. (2021). Energy 236:121387（ANU 仓库正式排版版，Table 3、Table A）。
- Blakers, A., Weber, T., Silalahi, D. (2025). Progress in Energy 7:022004（第 2.2 节、Table 4、7、8、9）。
- ANU RE100 全球抽蓄地图集网页与 2019 年地图集 PDF；ANU `PHES_Searching` 代码（GitHub）。
- IHA East Asia & Pacific 区域概况（2024 年装机）；Rystad Energy 2024；世界银行 P172256；EVN 2025-02-13；Vietnam Briefing（第 768/QĐ-TTg 号决定摘要）；Reccessary 2024；Power Philippines 2025；Kontan 2025；Infobanknews 2026；Enerdata 2020。
- PyPSA technology-data（costs_2050.csv PHS 行）；PyPSA-Eur `add_electricity.py`；NREL ATB 2024 抽蓄页；Blakers et al. (2021) Progress in Energy 3:022003。
