# v4 W19a：敏感性登记的只读准备（台账 W19；决策清单第 224、225 项）

- **指令：** `work/p1_v4_w19a_20261109/V4_W19A_INSTRUCTION.md` v2，SHA256 `e284f70ddd0d36e9c6cc3aaef45dc076bbfc9d4397abd29a7f21e251b5c5b9a5`，与同目录 `V4_W19A_SHA256.txt` 一致（开工前核对）。先读材料已读（W10 `REPORT.md` 第 0 节与 `C_GRADE_INVENTORY_META.json`；D2a `REPORT.md` 第 4.1 节 KH 封存上限与重排修正；D2b `DATA_UPGRADES.csv` 4.5、4.8 行；D2c `REPORT.md` 第 0.1 节第 3 条；W14 `REPORT.md` 第 0 节）。
- **执行：** Claude Code，模型 **Opus 5.5**（`claude-opus-5-5`），effort **xhigh**（会话元数据 `get_session self` 读到，满足指令）。开工时其他 Claude Code 会话均未运行，WSL 与 Windows 均无 Gurobi 进程，WSL 可用内存 9 GiB。
- **分支：** `asean/v4-w19a-20261109`，从 `asean/v4-w14-20261109` 头 `ac75354cf416cb811d7b446beb03ed6fbc030a83`（fetch 核过本地 = 远端）新开，worktree `/home/jin/wt_v4_w19a`。W14 包的 `COMMIT` `26c2e47d025fdd4e46cb278718d93aeddabbe984` 是头提交的祖先（其后只有 W14 交付目录的两个提交）。远端已无 `codex/` 分支（`ls-remote` 0 条），分支改名已完成。交付目录 `work/p1_v4_w19a_20261109/` = 仓库 `research/06_scope_redesign/p1_v4_w19a_20261109/`（`cache/` 与审阅 zip 不入库）。
- **性质：** 只读分析。没有改仓库中的模型代码、输入、配置与注册表；**求解器 0 次**；不连 HPC；没有下载数据文件（文献读取方式见第 2.3 节与 `EVIDENCE.json`）。本机计算合计约 3 分钟（直接读两张 v3.1 已解网络 20 s、峰值 0.88 GB；其余为 CSV / JSON 处理），磁盘新增约 15 MB（`cache/`）。不跳过 git hooks，不合并 main，不 force-push。没有读取许可文件。
- **标记：** VERIFIED（读到的数组、表、原文）、EXACT（可逐项复现的计算或严格的数学界）、INFERENCE（推断、外推、未读原文的来源）、PROPOSED（建议，未实施）。数据等级 A–E 沿用注册表。金额 EUR2020；"M" 百万，"bn" 十亿。ΔB6 = ΔZ(F2) − ΔZ(F1)。

## 0. 结论摘要

### 0.1 KH 封存上限（第 2 节）

1. **机制（VERIFIED / EXACT）：** v3.1 2920×3h 解中，KH 两个情景的 CO₂ 捕集量相同，约 14.4 Mt/a（DAC 5.8、生物质捕集 3.9、工业过程 4.6 Mt/a）。其中本国只能注入 1.8 Mt/a（上限用满），其余 12.6 Mt/a 运往 TH 封存：F1 走新建跨境管道，F2 走 CO₂ 船运（第 160 项：船运属 `maritime_trade`，两情景都有）。TH 封存不绑定（节点价 −30 EUR/t = 封存年金）。上限对偶的两处合计（第 219 项）：全局行 0，Store 上界 F1 **−10.402**、F2 **−12.810** EUR/t，**数值上恰好等于 KH2 0 这一边际吨的外运单价**：F1 为 KH2 0→KH2 2 管道 3.513 + KH2 2→TH2 3 管道 6.889 = 10.402 EUR/t（满负荷年金），F2 为 KH2 0→TH 船运 12.810 EUR/t。所以 F2 与 F1 的对偶差只有 −2.41 EUR/t，就是"管道比船便宜多少"。D2a 重排中的 ΔB6 −2.16 bn 之所以大，是因为把这 2.41 EUR/t 乘了 898.2 Mt/a 的一档。
2. **一阶外推不可靠（EXACT + INFERENCE）：** 一档取注册表高端 900 Mt/a（Mao et al. 2014 的水动力圈闭情形 45 Gt ÷ 50 年），是主值的 500 倍。上限在这一档内会**从绑定变为不绑定**：先吸收 KH 自己的 12.6 Mt/a 外运，再吸收 VN 的外运（VN 上限同样绑定），约在 **30 Mt/a（F1）/ 49 Mt/a（F2）** 处不再绑定（INFERENCE）。严格界（凸性给下界，"把 KH 出口改为本国注入"的可行解给上界，KH 封存链路可扩展、零成本、无上限）：上限放宽 12.65 Mt/a 时，ΔZ_F1 ∈ [−131.6, −96.0] M，ΔZ_F2 ∈ [−162.1, −157.4] M，**ΔB6 ∈ [−66.1, −25.8] M**（EXACT）。上限放宽到不绑定时（含 VN 改道：F1 走 VN2 0→KH2 0 管道 4.65 EUR/t、F2 走 VN2 0→KH 船运 11.83 EUR/t），ΔZ_F1 约 −0.19 至 −0.22 bn，ΔZ_F2 约 −0.20 至 −0.21 bn，**ΔB6 约 −0.02 至 +0.02 bn**（INFERENCE）。一阶值 ΔZ_F1 −9.34 bn、ΔZ_F2 −11.51 bn 高估约 42 倍、56 倍；**KH 第 3 名是一档过大造成的假象**。按右端类规则，一阶值是 ΔZ 的下界（成立，但极松）；ΔB6 无确定偏向，实际接近 0。Owen KH −9.3 bn 同理不可用：KH 自身相关的节约约 0.1 bn 量级。
3. **区间（第 2.3 节）：** 只有一个一手来源，即 Mao, Yamada & Matsuoka (2014) IJGGC 30:19–33。本步只取得其摘要（INFERENCE），全文列入下载候选。摘要给出全国 90 Mt（构造圈闭，低情形）至 45 Gt（水动力圈闭，高情形）。OGCI/CSRC Cycle 5 (2025) 附录 B 的 KH 数值引自该文：正文为咸水层约 85 Mt + 油气约 5 Mt = 90 Mt（VERIFIED，第 27 页）；表 5-1 合计 0.132 Gt（含 0.047 Gt 次商业类，与正文的 5 Mt 不一致）。ERIA/GCCSI 2024 未评估 KH（VERIFIED，第 56 页 §1.3.9、第 63 页表 1.19）。**数据区间（PROPOSED）：** 年上限 1.8（主值）至 2.64 Mt/a（CSRC 0.132 Gt ÷ 50），两份文件同源。**方法区间（PROPOSED，假设）：** 主值的 0.5–2 倍，即 0.9–3.6 Mt/a。900 Mt/a 是理论储量换算值，不是注入能力；在 v3.1 中与"无上限"等价。更可能的是低端到中段（INFERENCE）：资料少，ERIA 判为"未知"，水动力圈闭需要盆地级表征。
4. **PH（只给结论）：** 存在同类问题，即无登记区间、上限绑定（1.344 Mt/a，对偶 −16.19 EUR/t）、其余 42.5–42.9 Mt/a 船运到 MY。但两情景都走船运，F1、F2 对偶几乎相同（差 0.0004 EUR/t），所以**对 B6 的一阶影响约为 0**：上限放宽 42.9 Mt/a 时 ΔB6 ∈ [−59, +53] M。对 Z 与 Owen PH 的影响可达约 −0.64 至 −0.70 bn（下界为对偶×Δb，EXACT；上界为节省的运费 0.636 / 0.642 bn，VERIFIED，需 PH 封存链路可扩展，未逐一核对）。
5. **W19 登记建议（PROPOSED，第 2.5 节）：** ① 一阶清单中 KH 的高端一档由 900 改为 2.64 Mt/a（数据高端）。上限在此仍绑定，一阶可靠：ΔZ_F1 −8.7 M、ΔZ_F2 −10.8 M、ΔB6 −2.0 M，KH 退出前 30。② "前景封存（水动力圈闭）"另设一项情景，取不绑定的 50 Mt/a，只能直接求解，预期 ΔB6 ≈ 0（±0.05 bn）、两侧 ΔZ ≈ −0.2 bn。③ 按第 216 项第②条，KH、VN、PH 上限同机制、同方向（区域封存稀缺，放宽后 ΔZ ≤ 0），且 KH 与 VN 相互耦合（放宽 VN 时 KH 的 CO₂ 会改去 VN：F1 KH2 0→VN2 0 管道 4.65 EUR/t 比去 TH 便宜），**合并为一次"封存上限高端"**（KH 2.64 或 50 Mt/a + VN P10 186.07 Mt/a + PH 新登记的高端）与一次"封存上限低端"（ERIA P90 + KH 0.9 Mt/a）。不单列 KH。④ 预期方向：两侧 ΔZ ≤ 0；ΔB6 符号不定、量级小；对 Owen 的影响集中在 VN、PH、KH。注册表本步不改。

### 0.2 WACC 口径（第 3 节）

6. **统一 7 %（VERIFIED / INFERENCE）：** 注册表 `discount_rate_uniform_main` = 0.07，自注"real basis, INFERENCE"；第 90 项为社会规划者统一折现率；第 111 项为统一 0.07，S4P 列为"待核实"，S4R 指令 F7 写作"实际利率"。它的出处是 PyPSA-Eur v0.3.0 配置注释：来自 Hirth (2013)，并反映 Noothout et al. (2016) 的平均值。Hirth 未说明口径（模型用不变价）；Noothout 为**名义、税后**（D2b E64–E67）。technology-data 的成本是固定货币年（实际），但没有定义折现率口径（E68–E69）。**结论：7 % 的口径文件里没有明说，项目一直按"实际"使用，税前 / 税后从未说明。** LP 中没有税，按年金化逻辑它等同于"实际税前"门槛（INFERENCE）。巧合的是，名义税后 7 % 在欧盟式 τ = 25 %、π = 2 % 下折成实际税前为 7.19 %，两种读法相差很小（INFERENCE）。
7. **国别表（VERIFIED）：** `COUNTRY_WACC_REAL_M08A.csv` 的口径为实际、税后、本币。输入是 IEA 资本成本观察站 2024 年公用事业光伏的区间中点；IEA 口径今日重读为本币、名义、税后（VERIFIED）。BN、KH、LA、MM、SG 用"MY 中点 + Damodaran 国家风险溢价差"估算，TL 按规则取 KH、LA、MM 的均值。按 Fisher 式 (1 + n) / (1 + π) − 1 折实际，π 取 IMF WEO 2026 年 10 月 2028–2030 年 CPI 均值。表值与公式逐国一致（TH 差 0.8 个基点，为通胀取整所致）。
8. **统一方案（PROPOSED）：** 两张表都统一到"实际税前"：r = (1 + n/(1 − τ)) / (1 + π) − 1，需要的参数为各国法定公司税率 τ 与 π（π 已在表中）。若 7 % 读作实际税后，则保持国别表现状，但须在注册表写明读法。统一后（τ 为 INFERENCE 值，待核实）国别实际税前 WACC 为 3.9 %（SG）至 16.3 %（MM），**7 % 仍在区间内**：ID 9.8、KH 12.0、LA 11.5、MM 16.3、PH 7.05、TL 13.3 % 在其上，BN 6.0、MY 6.4、SG 3.9、TH 6.96、VN 6.8 % 在其下。τ ±5 个百分点时仍在区间内（3.6–14.9 % / 4.3–18.0 %）。按实际税后，区间为 2.9–11.0 %，同样在内。统一到税前后，MY、PH、TH、VN 由比 7 % 低 1.7–2.6 个百分点变为接近 7 %，W10 一阶 ΔB6 −3.51 bn 的量级预计变小（INFERENCE）。另：M10S1 曾在早期模型版本 365×24h 上直接求解过分国 WACC（R10 / R11，税后表），ΔB6 为 −0.79 bn（只作参照）。

### 0.3 收获上限 0.25（第 4 节）

9. **出处（VERIFIED）：** `scripts_project/d1_biomass.py:50` 的 `HARVEST_MAIN = 0.25`，注释"IRENA 2017 p.4-5; IRENA 2022 footnote 10"；注册表行 `biomass_constraint_harvest_residue_removal_max` = 0.25（"Harvest residues removable (soil quality/biodiversity)"）。原文出处：IRENA (2022)《Scaling up biomass for the energy transition: Untapped opportunities in Southeast Asia》第 42、65、85 页脚注 10、17、21，田间收获残余"limited to 25% of total harvest residues"，以保证土壤质量与生物多样性；IRENA (2017)《Biofuel Potential in Southeast Asia》第 6 页正文（PDF 页），收获后田间残余中可实际且可持续收集的份额"通常在四分之一到一半之间"，其余留田；第 27 页表 R-3 取 25 %。**IRENA 2022 附录 A（第 138 页）只给 4 % 翻种、140 株/ha、每株 2 t、含水 80 %，不含 0.25**，注册表树干行把两处来源写在了一起。
10. **含义与一致性：** 原文含义是"收获残余物质中可取走的份额（其余留田养土）"，按吨数作用，与质量基准（鲜重 / 干重）无关，**与第 224 项第③条的理解一致，未触发停止条件**。同一个 0.25 也用于全部作物的田间残余（稻、甘蔗、玉米、木薯、椰子、其他作物，`d1_biomass.py:281`；高情形 0.50）。树干沿用的是项目把作物规则推广到翻种时伐倒的树干（IRENA 2022 第 139 页把翻种伐倒的棕榈叶计入收获残余流，第 41 页提到伐倒的树干与叶通常留田作覆盖物）。IRENA 没有专门针对树干的取走上限，写入局限。IRENA 2017 给的范围（四分之一到一半）可作区间依据。另：注册表该行 sensitivity_low = 0.5 > 主值（低端应为更小值），属登记瑕疵，本步不改。

### 0.4 注册表等级构成（第 5 节）

11. **重数（EXACT，W10 同口径）：**

| 版本 | 行数 | 在用 | 在用 A | 在用 B | 在用 C | 全部 A / B / C |
|---|---:|---:|---:|---:|---:|---|
| `aad8e476`（W10 基线） | 2,321 | 1,464 | 134 | 868 | **462** | 283 / 1,408 / 630 |
| `26c2e47d`（W14 包 `COMMIT`） | 2,469 | 1,548 | 134 | 916 | **498** | 299 / 1,479 / 691 |

   等级列只有 A / B / C，没有 D / E（D 级只出现在两处描述文字中：TH PKS 自用份额、树干成本代理）。没有行被删除，也没有行改等级；只有 1 行改了状态（`co2_sequestration_cost_price_year` DATA_PENDING → REGISTERED）。基线 C 级分族与 W10 逐族相同（生物质 193、其他 107、工业 55、路线份额 43、潜力 27、CO₂ 22、WACC 15）。
12. **三类（互斥）：** (a) **v4 新增 148 行**：A 16 / B 71 / C 61；其中在用 84 行（B 48、C 36），其余多为 REFERENCE_ONLY 的表文件行。(b) **原在用 C 级行中主值已被 v4 开关值取代、保留为 v3.1 回退值的 33 行**：LNG 再气化加价 1 行（→ `v4_lng_regas_adder_asean_tariffs`，C）；甲醇化每 t CO₂ 产量 1 行（→ 化学计量 `ammonia_methanol_MWh_MeOH_per_tCO2_stoichiometric`，B）；油棕树干成本 5 行（→ `biomass_missing_cost_proxy`，C）；生物质潜力 26 行（→ T06 表 `v4_biomass_potential_2050_t06`，C，驱动行为树干、空果串、纤维、PKS、甘蔗渣的 v4 行，C / B）。(c) **只新增或修正区间、主值不变的 30 行**：木薯 / 椰子 / 其他作物低端 16 行、CO₂ 船运 2 行、液体船运按物理界 4 行、MY 屋顶光伏 1 行、`share_*` 按物理界或比值 6 行、VN 海上风 alpha 规则 1 行（区间登记在新行）。另：行内定值 1 行；需求侧 79 行（第 211 项归 I2，本步不重判）；未改 319 行。**v4 主算读法下在用 C = 498 − 33 = 465 行**。
13. **前 30 项现状（D2b 重排，`TOP30_STATUS.csv`）：** 已替换 3（LNG 再气化、ID 树干、ID 空果串），已核实并登记区间 8，方法或情景选择 5（WACC 模式、TH / MY 气田分配、船运甲醇份额、陆运电动份额），未处理 14（含 KH 封存上限：本步只给依据与建议，注册表未改）。**审阅端 11-09 05:00 的分类在工作区内没有找到**（检索 05:00 无结果），对照列记为"未提供"；本表的归类依据逐项写在 `basis` 与 `evidence` 列。

### 0.5 待决问题与指令写法差异

1. **KH 的"注册表无区间"与事实不符：** `co2_injection_cap_unified_KH` 登记了 1.8–900 Mt/a（低端 = 主值）；W10 / D2a / D2b 的一档正是这个高端。无区间的是 PH（`co2_injection_cap_unified_PH` 低、高均空）。请审阅端确认按第 0.1 节第 5 条改写一档与登记写法。
2. **KH 一档与合并：** 是否采纳"数据高端 2.64 Mt/a 进一阶清单 + 前景情形 50 Mt/a 另设情景 + KH、VN、PH 合并为封存高 / 低两次"的写法。
3. **WACC 目标口径：** 实际税前（推荐，与 LP 无税、成本不变价一致）还是实际税后（保持国别表现状）。由用户决定；税率需核实（DOWNLOAD_CANDIDATES 第 3 项）。
4. **0.25 的局限写法：** 建议注明"IRENA 作物收获残余规则推广到翻种树干；IRENA 2017 给 0.25–0.5"，区间登记为 0.25–0.5（W19 可选）。注册表该行低端 0.5 的瑕疵是否修正。
5. **决策清单原文：** 第 111 项、第 132 项第 5 条、第 160–162 项的原文不在工作区内，本报告引用的是各指令与规则文件中的转述（第 3.1 节）。
6. **前 30 项对照：** 审阅端 05:00 分类缺失，请提供后补对照。

## 1. 开工核对与分支（指令第 1 节）

| 项 | 结果 |
|---|---|
| 指令 SHA256 | 一致（见文首） |
| 模型 / effort | `claude-opus-5-5` / xhigh |
| 其他会话、Gurobi | 无运行中会话；WSL `ps`、Windows `tasklist` 均无 gurobi / s2_solve |
| 分支改名 | `git ls-remote --heads origin`：`codex/` 0 条、`asean/` 74 条；`asean/v4-w14-20261109` = `ac75354c`（远端 = 本地） |
| F1 / F2 已在 HPC 正式提交 | 本机不能核实（不连 HPC）；用户启动本步即视为满足 |
| 起点 / 新分支 | `ac75354c` → `asean/v4-w19a-20261109`，worktree `/home/jin/wt_v4_w19a`；`core.hooksPath` 未设 |
| 包 `COMMIT` | `26c2e47d` 是祖先（`merge-base --is-ancestor`）；`26c2e47d..ac75354c` 只有 W14-5/6、W14-6b 两个交付提交；`research_inputs`、`scripts_project`、`config*` 无差异 |
| 分析对象 | 包 `COMMIT` 上的注册表 `a9798b0c91b215920e57c388a0c90192a8119a85c9c379389b651c3b1c594c4c`（2,469 行），与包内代码包、W14 worktree 中的副本相同 |

## 2. KH 封存上限（指令第 2 节）

### 2.1 机制（`KH_CO2_ACCOUNT.csv`，`scripts/w19a_1_*.py`、`w19a_2_verify_nc.py`、`w19a_3_kh_bracket.py`）

数据：W10 / D2a 对 v3.1 已解网络的提取缓存（`work/p1_v4_d2a_20261107/cache/7508ec72…`、`4cc51892…`）。缓存元数据中的网络与对偶文件 SHA256 与 `hpc_results_v31/unpacked/export/F1|F2` 下的文件逐一相同（F1 `7508ec72…` / `bd60aa57…`，F2 `4cc51892…` / `b0eec1e9…`，VERIFIED）。另外**直接读两张已解网络**（xarray，整变量读一次，一次一张，读前 MemAvailable 9.8 GiB），用 `links_t_p0..p4` 复算端口流量，与缓存逐项一致（`evidence/KH_NC_CROSSCHECK.json`）。

| KH CO₂ 账（t/a） | F1 一体化 | F2 `no_new_xb` |
|---|---:|---:|
| DAC | 5,821,605 | 5,888,876 |
| 生物质捕集（工业生物质锅炉 CC + 工业生物质 CC） | 3,900,856 | 3,935,390 |
| 工业过程排放 CC | 4,628,991 | 4,628,991 |
| 其他（电力 CC、SMR CC、CO₂ 利用） | ≈ 0 | ≈ 0 |
| **净捕集** | **14,351,452** | **14,453,258** |
| 本国注入（上限 1,800,000，利用率 1.000） | 1,799,995 | 1,799,991 |
| 管道出口 → TH | 12,551,453 | 0（无跨境管道） |
| 船运出口 → TH | 0.9 | 12,653,261 |
| 其他国家进入 KH 的 CO₂ | < 10 t | < 10 t |
| 母线平衡余差 | −0.14 | −0.20 |
| 上限对偶：全局行 / Store 上界 / 合计 | 0 / −10.402 / **−10.402** | 0 / −12.810 / **−12.810** |
| KH 国家净零约束对偶 | −140.35 | −146.74 |

- **对偶的构成（EXACT）：** `co2 sequestered KH` 母线价 = −(30 + |对偶|)，即 −40.40 / −42.81 EUR/t。TH 各节点价为 −30.00（封存不绑定）。F1 的 10.402 = KH2 0→KH2 2 管道 30,773.1 / 8,760 = 3.513，加 KH2 2→TH2 3 管道 60,350.9 / 8,760 = 6.889（管道满负荷；KH2 4→TH2 3 利用率 1.000）。F2 的 12.810 = KH2 0→TH 船运边际成本 12.810（KH2 2 船运 12.284）。
- **为什么 F2 − F1 对偶差这么大：** 差值本身不大，−2.41 EUR/t（23 %），就是 KH 边际吨走船运与走管道的单价差。大的是 ΔB6 = −2.41 × 898.2 Mt/a，来自一档的规模。
- **哪些国家的 CO₂ 流向或本应流向 KH：** 两情景中都没有他国 CO₂ 进入 KH（< 10 t）。若 KH 上限放宽，按节点价与通往 KH 的路线单价判断（INFERENCE）：F1 中 VN（上限绑定，对偶 −10.81，现经 VN2 3→LA2 3→TH2 1 外运 14.63 Mt/a）会改经 VN2 0→KH2 0 管道（4.65 EUR/t），每吨省约 6.15 EUR；LA 的少量（≤ 1 Mt/a，每吨 ≤ 1.67 EUR）也会改道。F2 中 VN 现从 VN2 0 船运 34.45 Mt/a 到 TH（13.14 EUR/t），改运 KH（11.83 EUR/t）每吨省 1.30 EUR。PH、SG、MM、TL、ID、MY、BN、TH 不会改道（到 KH 的路线成本 + 30 高于其节点价绝对值）。
- **第 160–162 项口径下是否合理：** 合理。第 160 项删去全部非存量跨境链路（CO₂ 管道全是新建），船运属 `maritime_trade`，三情景相同（`V3_RULES.md` 第 2 节）；第 161 项（D161-7 a）液态 CO₂ 不设国家母线、按距离计价、两情景都有。所以 KH 在 F1 用管道、在 F2 用船，把 12.6 Mt/a 送往 TH 的 30 EUR/t 封存，这是规则的直接结果。v3.1 中 KH 上限对 B6 的真实含义是"KH 外运 CO₂ 用管道比用船省多少"，每年约 0.03–0.07 bn。

### 2.2 一阶外推的可靠性（`evidence/KH_CAP_BRACKET.json`）

- **W10 / D2b 所用一档（VERIFIED）：** 低 = 1,800,000（= 主值），高 = 900,000,000 t/a，依据"registered sensitivity range (EXACT)"，即注册表 `sensitivity_high` = Mao et al. 2014 水动力圈闭 45 Gt ÷ 50 年。W10 只读全局行对偶（0），判为"零余量退化"，排第 259；D2a 加读 Store 上界对偶后排第 3（D2b 同）：ΔZ_F1 −9.343、ΔZ_F2 −11.506、ΔB6 −2.163 bn，Owen KH −9.343 bn，标记 `large_change: notch 49900%`。
- **偏向（第 214 项第⑤条）：** 右端类。LP 值函数对右端凸，所以 ΔZ ≥ y·Δb，一阶值是 F1、F2 各自 ΔZ 的下界。ΔB6 是两个单侧界之差，无确定偏向。
- **会不会由绑定变为不绑定：会**（标出）。严格区间（EXACT）见下表，Δb 取 KH 两情景外运量的较大者 12,653,267 t/a：

| 上限放宽 | ΔZ_F1 | ΔZ_F2 | ΔB6 | 等级 |
|---|---:|---:|---:|---|
| +12.65 Mt/a（吸收 KH 自身外运） | [−131.6, −96.0] M | [−162.1, −157.4] M | **[−66.1, −25.8] M** | EXACT（下界：凸性；上界：可行解，改为本国注入，省去 KH2 2→TH2 3、KH2 4→TH2 3、KH2 1→TH2 1、KH2 0→KH2 2 管道年金 95.97 M / 船运运费 157.40 M；两侧封存年金同为 30 EUR/t，互相抵消） |
| 到不绑定（F1 约 30、F2 约 49 Mt/a） | 约 [−223, −186] M | 约 [−207, −202] M | **约 [−21, +21] M** | INFERENCE（另加 VN 改道 90.0 / 44.9 M、LA ≤ 1.7 M，线性估计） |
| 一阶 +898.2 Mt/a | −9,343 M | −11,506 M | −2,163 M | 一阶下界，高估约 42 / 56 倍 |

### 2.3 区间：文献（`EVIDENCE.json` lit_*；`DOWNLOAD_CANDIDATES.csv`）

| 来源 | KH 数值 | 读取方式 | 等级 |
|---|---|---|---|
| Mao, Yamada & Matsuoka (2014) IJGGC 30:19–33, doi:10.1016/j.ijggc.2014.08.016 | 全国 90 Mt（构造圈闭，低）至 45 Gt（水动力圈闭，高）；Khmer 盆地最适宜，其次 Kampong Saom、Tonle Sap；作者称结果为初步 | WebSearch 摘要。京都大学机构库 PDF（2433/191190）WebFetch 抽不出正文；ScienceDirect 403；Scribd 转载副本被拦截，未使用 | INFERENCE（未读原文）；全文列入下载候选 |
| OGCI/CSRC Cycle 5 (2025) Appendix B Asia（本机 `work/p2_data_intake/raw2/`，SHA256 `ff21cd34…` = 注册表） | 第 24 页摘要写咸水层"~65 Mt"、油气"~5 Mt"；第 27 页正文咸水层"~85Mt"、油气"~5Mt"（7 % 效率因子），来源 [1] = Mao et al. 2014；表 5-1 合计 0.132 Gt（次商业 0.047 + 未发现 0.085，仓库提取记录，图像表本步未重新渲染） | 本机原文 pypdf 抽字；OGCI 网站 403 | VERIFIED（文字）；与 Mao 2014 同源 |
| ERIA / GCCSI (2024) Comprehensive CCUS Research Report Ch.1 | 第 56 页 §1.3.9：KH、LA、MM 的封存潜力"currently unknown as no analysis has been completed"；第 63 页表 1.19：Cambodia Panjang（离岸）只列"Basic analysis of storage potential" | WebFetch 存入工具缓存，复制到单独目录后 pypdf 抽字（SHA256 `1c36f7b0…`） | VERIFIED |
| 注入能力（井数、注入率） | 未找到 KH 的数值；CCOP CCS-M 地图集中没有找到柬埔寨条目 | WebSearch | — |

**区间判断（PROPOSED）：** 可换算来源只有一个一手来源（CSRC 引自 Mao 2014），不满足"两个以上独立来源"。数据区间为潜力 0.09–0.132 Gt，即年上限 **1.8–2.64 Mt/a**。方法区间为 0.5–2 倍主值，即 **0.9–3.6 Mt/a**（假设）。45 Gt / 900 Mt/a 是理论储量，不是注入能力，只宜作"前景封存"情景。哪一端更可能（INFERENCE）：低端到中段。理由：ERIA 认为未知；作者自称初步；CSRC 表与正文的油气部分相差 9 倍（47 vs 5 Mt）；水动力圈闭需要盆地级表征与注入试验。作为参照，Mao 2014 摘要称 KH 八个主要点源合计 43.1 Mt/a（2008–2024 年估计，INFERENCE，摘要）。

### 2.4 PH（只给结论）

PH 上限 1,344,000 t/a（ERIA 只评 Malampaya 一个气田 67.2 Mt，第 53 页表 1.18，VERIFIED），注册表低、高均空。两情景都绑定，对偶 −16.190 / −16.190 EUR/t；PH 船运 42.49 / 42.94 Mt/a 到 MY（运费 0.636 / 0.642 bn）。**同类问题：有（无区间、绑定、对偶大）；对 B6：约为 0**（两情景都走船运；放宽 42.9 Mt/a 时 ΔB6 ∈ [−59, +53] M）。**对 Z 与 Owen PH：大**（约 −0.64 至 −0.70 bn）。可用于登记区间的来源：OGCI/CSRC Cycle 5 PH 合计 23.318 Gt；IEA 2021（引 ADB 2013）理论 22.3 Gt（注册表已有组件行）。

### 2.5 W19 登记写法（PROPOSED，不改注册表）

| 项 | 写法 |
|---|---|
| 变动幅度 | 一阶清单：KH 2.64 Mt/a（数据高端，CSRC 0.132 Gt ÷ 50）；直接求解情景"前景封存"：KH 50 Mt/a（不绑定，≥ F1 约 30、F2 约 49 Mt/a），只作直接求解。低端：0.9 Mt/a（方法区间，假设） |
| 合并（第 216 项第②条） | KH、VN、PH 三个绑定上限合并为"封存上限高端"一次（KH 高端 + VN P10 186.07 Mt/a + PH 高端）与"封存上限低端"一次（ERIA P90 各国 + KH 0.9 Mt/a + PH 不变）。理由：同一机制（区域封存稀缺），方向相同；KH 与 VN 相互耦合（单独放宽 VN 时，KH 的 CO₂ 会改去 VN） |
| 预期方向 | ΔZ_F1、ΔZ_F2 ≤ 0（高端）/ ≥ 0（低端）；ΔB6 符号不定，KH 部分量级 ≤ 0.07 bn；Owen 集中在 VN、PH、KH |
| 一阶标注 | 右端类，ΔZ 下界；一档超出绑定范围时标"一阶高估、只作排序"，不用于预测 |

## 3. WACC 口径（指令第 3 节；`evidence/WACC_BASIS.csv`、`WACC_BASIS.json`，`scripts/w19a_6_wacc_basis.py`）

### 3.1 统一 7 % 的口径

| 位置 | 内容 | 等级 |
|---|---|---|
| 注册表 `discount_rate_uniform_main` | 0.07，B 级，"technology-data / pypsa-asean fill value; real basis, INFERENCE"；分布式 0.04 | VERIFIED |
| `finance_wacc_mode`、`scenario_switch_wacc_mode` | 主算 `uniform`；`country_specific` 只作敏感性（第 90、133 项） | VERIFIED |
| 第 90 项 | 社会规划者视角，统一折现率（注册表描述） | VERIFIED（转述） |
| 第 111 项 | "折现率为统一 0.07"（L23 指令）；S4P 判"待核实"（F7）；S4R 指令 F7："主算用统一 WACC 0.07（实际利率）；分国 WACC 作重点敏感性" | VERIFIED（转述；决策清单原文不在工作区） |
| 第 132 项第 5 条 | 分国 WACC 敏感性，一体化 / 不互联两次（M10P R10 / R11） | VERIFIED（转述） |
| PyPSA-Eur | v2025.07.0 `costs.fill_values` 中 discount rate 0.07，文档无实际 / 名义说明（E64）；v0.3.0 注释称来自 Hirth 论文，并反映 Noothout 2016 平均值（E65） | VERIFIED（D2b，2026-11-08） |
| Hirth (2013) | 所有投资用 7 % 折现，未说明口径（第 16 页，E67） | VERIFIED（D2b） |
| Noothout et al. (2016) | 名义、税后，融资关闭时（E66） | VERIFIED（D2b） |
| technology-data | 成本为固定货币年（E68）；折现率口径未定义（E69） | VERIFIED（D2b） |

**结论：** 7 % 的口径在源头没有说明，项目一直按实际利率使用（INFERENCE，来自 S4R F7 与注册表自注），税前 / 税后没有写过。LP 中没有税，年金 = 资本回收，所以 7 % 起的是"实际税前"门槛的作用（INFERENCE）。

### 3.2 国别表的口径

`COUNTRY_WACC_REAL_M08A.csv`（= S4R `COUNTRY_WACC_SENSITIVITY_TABLE.csv` 的 real_wacc_mid）：实际、税后、本币。IEA 观察站口径今日重读为本币、名义、税后（VERIFIED，`https://www.iea.org/reports/cost-of-capital-observatory/dashboard`）；未注明口径的问卷回答，IEA 按近十年平均通胀与公司税假设换算；负债成本取税后。IEA 只覆盖 ID、MY、PH、TH、VN 的公用事业光伏（2024 FID），其余国家用 MY 中点加 Damodaran 风险溢价差，TL 用规则值。表值与 Fisher 式逐国一致（TH 差 0.8 个基点）。

### 3.3 统一方案与结果（PROPOSED）

- **推荐目标口径：实际税前。** 理由：成本是不变价 EUR2020，LP 中没有税。换算式（EXACT，在 WACC_post = E/V·r_E + D/V·r_D·(1 − τ) 的定义下精确成立）：n_pre = n_post / (1 − τ)，r_real,pre = (1 + n_post/(1 − τ)) / (1 + π) − 1。所需参数：τ = 各国法定公司所得税率（本步取 BN 18.5、KH 20、ID 22、LA 20、MY 24、MM 22、PH 25、SG 17、TH 20、TL 10、VN 20 %，**INFERENCE，待核实**）；π = IMF WEO 2026 年 10 月 2028–2030 年 CPI（已在表中）。另一种做法：7 % 读作实际税后，国别表不改，但注册表须写明读法。
- **统一后的区间（基于 INFERENCE 税率）：**

| 口径 | 最小 | 最大 | 7 % 是否在内 | 高于 7 % 的国家 | 简单均值 |
|---|---|---|---|---|---:|
| 实际税后（现表） | 2.9 % SG | 11.0 % MM | 是 | ID KH LA MM TL | 6.4 % |
| 实际税前 | 3.9 % SG | 16.3 % MM | 是 | ID KH LA MM PH TL | 9.1 % |
| 实际税前，τ − 5 个百分点 | 3.6 % | 14.9 % | 是 | ID KH LA MM TL | 8.3 % |
| 实际税前，τ + 5 个百分点 | 4.3 % | 18.0 % | 是 | 除 BN、SG 外 9 国 | 9.9 % |

- **对敏感性的含义（INFERENCE）：** 现在的 −3.51 bn 主要来自 MY、PH、TH、VN 的税后实际值（4.4–5.3 %）远低于 7 %。改为税前后，这四国为 6.4–7.05 %，接近 7 %，ΔB6 量级预计明显变小。正式敏感性应在口径统一后直接求解，不用一阶。
- 另需注意：IEA 数值只代表公用事业光伏，用于全部技术是简化。

## 4. 收获上限 0.25 的出处（指令第 4 节）

| 环节 | 位置 | 内容 |
|---|---|---|
| 树干潜力链 | `scripts_project/d1_biomass.py:309–313` | opt = 收获面积 × 0.04 × 140 × 2 t；m_main = opt × `HARVEST_MAIN`（0.25）；× 15 GJ/t（v4 再乘 T06 系数 0.1523） |
| 常数 | `d1_biomass.py:50` | `HARVEST_MAIN, HARVEST_HIGH, PROCESS = 0.25, 0.50, 0.90`，注释"IRENA 2017 p.4-5; IRENA 2022 footnote 10 (25 % cap)" |
| 注册表 | `biomass_constraint_harvest_residue_removal_max` = 0.25（A 级，"Harvest residues removable (soil quality/biodiversity)"，来源"IRENA 2022 footnotes 10/17/21; IRENA 2017 p.4-5"）；5 行 `biomass_potential_*_oil_palm_trunk` 描述含"harvest cap 0.25" | VERIFIED |
| IRENA 2022（本机原文，SHA256 前缀 `bf52f40b` = 代码登记） | 第 42 页脚注 10（另见第 65 页脚注 17、第 85 页脚注 21）：收获残余可用量限于总量的 25 %，以保证土壤质量与生物多样性；附录 A 第 138 页：4 %、140 株/ha、2 t/株、含水 80 %，**无 0.25** | VERIFIED |
| IRENA 2017（本机原文，SHA256 前缀 `53a30811`） | PDF 第 6 页：收获后田间残余中可实际且可持续收集的份额通常为四分之一到一半，其余留田养土（脚注 1 引 Muth 等的 25 %）；PDF 第 27 页表 R-3：收获残余收集 25 %、加工残余 90 % | VERIFIED |
| 是否也用于其他品类 | 是：稻、甘蔗、玉米、木薯、椰子、其他作物的田间残余（`d1_biomass.py:281`，高情形 0.50）；加工残余与棕榈厂残余用 0.90；树干的高情形为（树干 + 叶）× 0.25 | VERIFIED |

**含义判定：** 原文是"可取走（收集）的份额，其余留田"，与第 224 项第③条一致，不停止。局限：IRENA 的规则针对作物田间残余，树干沿用的是项目的推广，没有树干专属来源。

## 5. 注册表按等级重数（指令第 5 节；`REGISTRY_TIERS.csv`、`evidence/REGISTRY_C462_CLASSES.csv`、`REGISTRY_NEW_ROWS.csv`、`REGISTRY_TIERS_META.json`）

- 口径与 W10 相同（在用 = REGISTERED + SENSITIVITY + DATA_PENDING；分族规则同 W10）。基线 `aad8e476` 复算 2,321 / 1,464 / 462，与 W10 一致（EXACT）。
- 结果见第 0.4 节表。状态 × 等级的全部组合在 `REGISTRY_TIERS.csv` 中。
- **(b) 33 行的判定规则（EXACT，按开关集逐项对应，`configs/research/baseline.yaml` 第 515–535 行）：** `lng_regas_adder: asean_tariffs`；`meoh_per_tco2: stoichiometric`；`missing_cost_rule: proxy`（`biomass_missing_cost_proxy` 描述中点名的 5 行）；`biomass_potential: v4_adjusted_t06`（T06 调整表 `BIOMASS_POTENTIAL_ADJ_V4_T06.csv` 中 F3 / F4 / F5 任一非零的 26 行，逐行给出前后值与驱动行）。(c) 30 行：主值未变而区间列有变动，或追加说明点名了新增的 SENSITIVITY 行。
- **需求侧 79 行**（W10 机制 `demand_I2` 或 side = demand）：v4 主算的需求来自 `research_inputs/industry_v4/out_ras` 表集（`research.demand.v4.enabled`）。逐行是否仍进入计算属于 I2 的记录（第 211 项），本步不重判，单独列出。
- **前 30 项：** `TOP30_STATUS.csv`，逐项列出 D2b 名次、一阶 ΔB6、Owen 最大国、本步归类、依据、证据文件与注册表差异；"已替换"与 (b) 类一一对应（一致性检查 30 / 30）。

## 6. 额度、停止条件与局限

- **额度：** 求解器 0 次；本机计算约 3 分钟（上限 2 小时）；磁盘新增约 15 MB（上限 3 GB）；已解网络读取前检查无 Gurobi、可用内存 ≥ 8 GiB，一次一张。
- **停止条件逐项：** SHA256 一致；模型 Opus 5.5；分支改名已完成；`26c2e47d` 是祖先；无 Gurobi、无其他会话；没有需要改模型代码、输入、配置、注册表的地方；没有求解、没有连 HPC；0.25 的原文含义与第 224 项第③条一致；未读许可内容（只读了已清洗的导出与网络文件）。文献读不到的已列入下载候选，不是停止条件。
- **局限：** KH 的不绑定情形与 VN 改道是线性估计（INFERENCE），没有求解；PH 可行解上界未逐一核对 PH 封存链路是否可扩展；税率未核实；Mao 2014 只取得摘要；审阅端 05:00 分类与决策清单原文缺失；需求侧 79 行未重判。

## 7. 产出

| 文件 | 内容 |
|---|---|
| `REPORT.md` | 本报告 |
| `KH_CO2_ACCOUNT.csv` | KH CO₂ 账、对偶、边际路线、区间界、邻国改道、一阶对照、PH 结论（F1 / F2 并列，带等级） |
| `REGISTRY_TIERS.csv` | 两版注册表的行数、在用、等级、状态 × 等级、分族，以及 (a) 至 (u) 各类计数 |
| `TOP30_STATUS.csv` | D2b 前 30 项现状 |
| `DOWNLOAD_CANDIDATES.csv` | 读不到或需核实的来源 |
| `EVIDENCE.json` | 轻量证据（SHA、关键数值、文献 URL / 访问 UTC / 引文 / 页码） |
| `PROGRESS.md` | 进度与恢复点 |
| `LEDGER_ENTRY_DRAFT.md` | 台账条目草稿（台账本步不改） |
| `evidence/` | `KH_NC_CROSSCHECK.json`、`KH_LINK_LIMITS.json`、`KH_CAP_BRACKET.json`、`WACC_BASIS.csv/json`、`REGISTRY_C462_CLASSES.csv`、`REGISTRY_NEW_ROWS.csv`、`REGISTRY_TIERS_META.json`、`APPENDIX_LITERATURE.md`、`REVIEW_MANIFEST.csv` |
| `scripts/` | 方法脚本（`w19a_0`–`w19a_6`，以及探查脚本 `w19a_explore_*`） |
