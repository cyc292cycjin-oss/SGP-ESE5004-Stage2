# 抽蓄存量对账与敏感性开关（V4 D2a 第 3.3、3.4 节；决策清单第 220 项）

- **问题（D1 待决第 5 条）：** 模型 2050 年存量抽蓄 5,406 MW 中 TH 2,310 MW 对 IHA 2024 在运 1,531 MW（多 779）、PH 856 对 729 MW（多 127）未解释；`TH2 4` 节点 950 MW 的冻结机组疑含常规水电。
- **规则（指令第 3.3 条）：** 至少两个独立来源（GEM、EGAT / NPC 年报、IHA）一致时修正（挂在 v4 开关后），否则保留并报告。
- **证据：** `evidence/PHS_STOCK_LITERATURE.json`（44 条：EGAT 电站特性页、ANDRITZ、IHA、GEM wiki、DOE、First Gen、CBK 等；只读子代理检索，本会话逐条过目）；GEM GIPT 2026-09 本地表（`research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv`）核实机组编号。

## 0. 结论

| 国 | 模型（D1） | 逐台核实 | 判定 |
|---|---:|---|---|
| **TH** | 2,310 MW = `TH2 4` 冻结组 950 + Lam Ta Khong（GEM G100000603605）1,000 + Srinagarind 抽蓄机组（S4A，G100001090152）360 | Lam Ta Khong 4 × 250 = 1,000（EGAT T-13）；Srinagarind 4–5 号 2 × 180 = 360（EGAT T-09）；**Bhumibol 8 号可逆机 171 MW**（EGAT T-01 / T-02；ANDRITZ T-03；Power Technology T-05）；合计 **1,531 MW = IHA 2024**（T-20；USTDA 二手 T-21） | **修正。** 冻结组 950 MW = GEM 两条 Bhumibol 记录之和（G100000603603 779 MW "conventional storage" 1964 + G100000604991 171 MW "pumped storage" 1996，PPM:264，`hydro_subtype` 被整组标为 Pumped Storage）；EGAT 合同容量 779.20 = 6 × 82.2 + 115 + 171 **已含 8 号机**，GEM 重复计入 171 MW。正确拆分：171 MW 抽蓄 + 608.2 MW 常规水库水电 + 170.8 MW 重复计数剔除。两个独立来源（EGAT、ANDRITZ）一致，IHA 合计旁证 |
| **PH** | 856 MW = Kalayaan 冻结组 736（G100000603193 366 + G100000603194 370）+ Pantabangan-Aya 120（S4B1，G100000603200） | Kalayaan I + II：GEM 366 + 370 = 736（P-01 / P-02）= DOE 2021 装机 736.0（可靠容量 720.0；P-08 二手）；业主口径 366 + 368.36（P-03）；CBK 保证容量 684.6（P-05）；IHA 729（P-11）与任一逐台口径不符，最接近 2000 年融资公告的 728 MW 复合体设计值（P-10）。Pantabangan-Aya 120 MW（2 × 60）是利用既有 Aya（上）/ Masiway（下）水库的**新建抽蓄**（First Gen；NIA 协议 2026-06-30；目标 2030 商运；P-12–P-18），不是 Pantabangan 常规机组（2 × 60，1977 / 2010 升级，P-19–P-22） | **不修正，报告。** 736 对 729 是额定口径差；120 MW 的抽蓄归类正确，GEM 的 "construction" 状态偏早（公开报道未见开工），但模型按决策 77 / 86 b 以 GEM 状态为 2050 存量依据，不改 |
| ID / VN | 1,040 / 1,200（在建，D1 已判合理） | 未重新核实 | 不变 |

修正后：TH 抽蓄 2,310 → **1,531 MW**（= IHA），TH 常规水库水电 +608.2 MW（`TH2 4`），东盟存量抽蓄 5,406 → 4,627 MW；PH 不变。

## 1. 实施（第 3.3 节）

| 项 | 内容 |
|---|---|
| 开关 | `research.fleet.phs_stock_reclass: null`（**null = 随 `research.demand.v4.enabled`**：v4 主算开、v3.1 关；也可显式 true / false）；`phs_reclass_table: research_inputs/fleet_v5/PHS_STOCK_RECLASS_V4.csv` |
| 表 | 一行：identity `GEM:G100000603603`，component `existing_survivor::TH2 4::Hydro::6b2ad09f452a`，GEM 779 MW → reclass_to `hydro existing` 608.2 MW，drop 170.8 MW，理由与来源 |
| 代码 | `s4a_fleet.reclassify_phs_stock(n, costs, cfg, repo)`，在 `s2_network` 中紧随 S4B-1 的移除步、在按投运年定价（m08a A3）与来水归一化（S4C-2）之前调用：抽蓄组件 `p_nom` 950 → 171（FOM、`source_unit_id`、`source_group_capacity_mw`、`retained_electric_capacity_mw` 同步）；新建 `existing_survivor::TH2 4::hydro existing::D2A`（StorageUnit，`p_nom` 608.2，水库表示 = S4A 新增机组规则：同节点既有水库（Sirikit 500 + S4A 70 MW）的每 MW 来水与 `max_hours` 代理，`efficiency_dispatch` 0.9，不抽水，`asset_role existing_survivor`，`capital_cost` 0，`build_year` 1964，寿命 100）；`existing_unit_components` 中 G100000603603 的身份改指新组件、容量 608.2；FOM 常数按 −PHS FOM × 779 + 水电 FOM × 608.2 调整（随后的 m08a 按投运年定价步重算两部分的 FOM 并重算常数） |
| 能量 | 来水归一化（`national_observed`）按容量份额把泰国观测来水（Ember 中位 × 1.1）分给全部水库机组：新增 608.2 MW **不增加泰国水电能量**（Bhumibol 的发电量已在 Ember 全国数中），只增加可调度容量；损失 779 MW 抽蓄容量 |
| 测试 | `tests/research/test_v4_d2a_supply.py`：表与 GEM / EGAT 算术一致；开关关（显式 false 或 v4 关）网络不变；拆分后容量、FOM、来水代理、身份记录、FOM-once 恒等式、容量恒等式；表与身份不符时拒绝 |
| 注册表 | `v4_phs_stock_bhumibol_pumped_mw` 171、`..._conventional_mw` 608.2、`..._gem_double_count_mw` 170.8、`v4_phs_stock_th_pumped_total_mw` 1,531（REGISTERED）；`v4_phs_stock_ph_kalayaan_mw` 736（REFERENCE_ONLY，含 PH 判定说明）；表文件行 |

### 1.1 网络差异（第 5 节 C8 核对，相对 D1 网络）

预期：`TH2 4` 的 `PHS existing` 组件 `p_nom` 950 → 171（及 FOM 列）；新增 `hydro existing::D2A` 组件 608.2 MW；泰国全部水库机组的 `inflow` 时间序列按新容量份额重新分配（国家总量不变）；`existing_unit_components`、`existing_annual_fixed_om_eur` 等元数据。实际差异见 `evidence/D2A_NETWORK_DIFF.json`。

## 2. 敏感性开关 `research.supply.phs_case`（第 3.4 节；不进主算）

| 项 | 内容 |
|---|---|
| 取值 | `main`（S4B-2 现状：GEM 管线上限 14,438 MW，固定 6 h，往返 0.75，technology-data 2,297 EUR2020/kW）\| `asean`（W19 敏感性） |
| 结构（`PHS_PROPOSAL.md` 5.1 方式 A，以不改主算网络为前提择简） | 每个候选节点三档时长 StorageUnit：6 h（沿用 `<node> PHS_new` 名）、`<node> PHS_new 12h`、`<node> PHS_new 24h`；年化成本 = 年金(7 %, 50 a) × (功率成本 + h × 能量成本) + FOM；往返 0.80（√ 每侧）；每档 `p_nom_max` = 国家能量上限 / h；国家能量上限 Σ p_nom × h ≤ E 由新钩子 `research_phs_energy_cap`（`assembly_components` 白名单与分派、`s4b_candidates.install_phs_energy_cap`）实现。选 A 而非 B（Store + 两条 Link）：A 只改候选参数与一条约束，B 需新约束钩子与双向容量耦合、改变组件集合 |
| 成本 | Lu et al. 2021 表 3：560 USD2020/kW + 50 USD2020/kWh，FOM 7 USD2020/kW/a，50 a → × `fx_usd_to_eur_2020` 0.877228632573 = **491.25 EUR2020/kW + 43.86 EUR2020/kWh + 6.14 EUR2020/kW/a**（EXACT）；年金 0.07246 → 6 h 60.8、12 h 79.9、24 h 118.0 kEUR/MW/a（主算 184.5） |
| 上限 | ANU 2025 短名单（TWh）：ID 103、LA 62、MY 62、MM 62、VN 62、PH 42、TH 16；KH / BN / SG / TL 无数据 → 保持现有上限（0）。MY、MM 无 GEM 管线候选：用本国有既有水库水电的节点的 `PHS_new` 结构（INFERENCE 代理，`PHS_PROPOSAL.md` 5.3） |
| 表 / 注册表 | `research_inputs/potentials_v5/PHS_ASEAN_CASE_V4.csv`；`phs_asean_power_cost_eur2020_per_kw` 等 5 行 + `phs_asean_energy_cap_<CC>` 7 行（SENSITIVITY） |
| 测试 | `test_v4_d2a_supply.py`：`main` 下网络逐组件不变、未知取值拒绝；`asean` 下三档、成本、`p_nom_max`、效率、钩子与能量上限元数据、无 ANU 国家保持 S4B-2、MY 节点规则；换算与注册表行 |
| 构建核对 | 第 5 节：`main` 网络与 D1 网络在抽蓄候选上逐组件相同（C8）；`asean` 网络按需构建核对（不求解） |

## 3. 待决（交审阅端）

1. 接受 TH 的拆分（171 抽蓄 + 608.2 常规 + 170.8 剔除）作为 v4 主算的数据修正。
2. PH：保留 736 + 120；Pantabangan-Aya 的 GEM 状态（construction）早于公开报道（2026-06 签约、2030 商运），是否按决策 77 / 86 b 继续沿用 GEM 状态。
3. `phs_case: asean` 是否纳入 W19 敏感性批次；能量上限用 ANU 短名单（选点）还是全量（需向 ANU 申请站点表，`DOWNLOAD_CANDIDATES.csv`）。
