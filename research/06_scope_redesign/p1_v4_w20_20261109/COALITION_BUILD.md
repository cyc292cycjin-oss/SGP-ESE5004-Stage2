# v4 W20：联盟子集网络的构建规则与 17 个网络（指令第 2 节；决策清单第 228 项）

- **工具：** `scripts_project/v4_coalition.py`（新模块，独立命令行入口；主构建路径 `s2_network.py`、`m08a_variants.py`、`s2_solve.py` 等不导入它，测试 (d) 逐文件核对）。
  - 函数：`coalition_subnetwork(network, members, include_bunker=False, *, inplace=False)` → `(S-only 网络, 台账)`；不求解。
  - 命令行：`PYTHONHASHSEED=0 python scripts_project/v4_coalition.py build --base <2920×3h 网络> --coalition <名称> --out <目录> --truncate 56`；`list` 列出 17 个联盟与求解顺序。输出 `<名称>_56_unsolved.nc` 与 `<名称>_56_COALITION_RECEIPT.json`（输入 / 输出 SHA256、逐规则台账、保留的跨境设施、过境链路、死端组件）。
- **输入：** W14 包的 v4 主算一体化网络 `integrated_2920_3h_unsolved.nc`，SHA256 `86f6d6a0fce2f0e04d12ee7993aee885256fcaadadaeeca308414017738c801d`（`results_project/v4w14/builds/main/integrated/` 中的同一文件；构建脚本按前 16 位核对）。
- **截取：** `--truncate 56` 与 D2c / W14 冒烟同一规则（前 56 个时段 + `s2_solve.set_representative_weights`，权重 8760/56，年度量不缩放）；先构建后截取与先截取后构建逐组件相同（测试 (a)）。
- **标记：** VERIFIED（测试 / 回执 / 数组）、INFERENCE（解释）。

## 1. 定义（第 228 项第 0 节，转述第 133 项第 (2)a 条）

非成员国整体移出：其需求、资源、设施、潜力、存量与新建候选、液体母线与船运接入、CO₂ 船运、管道与线路；跨越联盟边界的一切线路、管道、专线、船运链路移除；成员国之间的存量跨境设施与新建跨境候选保留；成员国各自的净零约束保留。燃料舱是第 12 个参与者，不属于任何国家联盟：`include_bunker=False` 时移除燃料舱负荷与燃料舱账户。不是第 91 项 (b) 的"只断走廊"开关（`cross_border.coalition`），也不是 `m08a_layers.apply_remove_countries`（v2 结构，保留燃料舱参与者，且不处理 v3/v4 的分国液体母线、节点燃料舱与专线源母线）。

## 2. 逐类处理（每个被移除的组件只记在一条规则下）

| 规则 | 依据 | 组件类 | 处理 |
|---|---|---|---|
| **R1 按母线国家归属移除** | 母线 `country` ∈ 非成员国 | Bus；其上的 Load、Generator、Store、StorageUnit、ShuntImpedance；各端口都在被移除母线上的支路（非成员国内部线路、链路） | 全部移除。覆盖：需求（负荷）、资源与潜力（可再生发电机及其 `p_nom_max`、生物质池等有限资源 Store）、设施（转换链路）、存量（`existing_survivor`）与新建候选、国家大气账户、国家 CO₂ 封存与区外封存账户、国家液体母线（`XX oil / oil non-fossil / methanol / ammonia`）及其进口发电机、专线源母线 |
| **R2 按两端任一端在外移除（边界）** | 支路（Line、Transformer、Link 的 bus0…bus4）有一端在被移除母线、另一端在保留母线 | 跨境交流线、直流链路（正反两向）、专线、气 / 氢 / CO₂ 管道、液体船运、液体过境铁路、CO₂ 船运与过境链路（进入非成员国封存账户）、非成员国液体池的接入 | 全部移除，按载体计数（第 4 节表）。多端口链路任一端口在外即移除 |
| **R3 按参与者移除（燃料舱）** | 母线 `country` = `ASEAN` | 143 个燃料舱终端母线与账户母线 `co2 bunkers ASEAN`、130 个燃料舱负荷、账户 Store、225 条计量 / 燃料舱船用甲醇链路 | `include_bunker=False`：全部移除，并从 `required_constraint_hooks` 删去 `research_bunker_net_zero`、删去 `n.meta['research_bunkers']`。`include_bunker=True` 且为真子集：只移除位于非成员国节点（母线 `location`）的燃料舱母线，账户在仍有计量链路时保留（本步 17 个联盟都不用） |
| **R4 全局约束与钩子行** | 约束随网络重建 | GlobalConstraint（v4 主算网络为 0 行；若出现则拒绝构建）；钩子行 | 净零行 `research_country_co2_limit-<c>` 只对 `n.meta['research_countries']` = 成员国建立；封存上限行 `research_co2_storage_cap-<c>` 只对有封存账户的成员国；`ResearchImportAnnual-<发电机>`（国产气上限）、`ResearchStoreDirection-<Store>`、电池充放对、新水库来水约束只对保留组件；既有资产 FOM 常数与既有跨境 FOM 常数按保留组件重算；`research_lossy_bidirectional_sync` 与 `research_ac_loss_proxy` 由保留链路 / 线路导出（不变式：保留的反向链路都有正向孪生） |
| **R5 清理** | 移除后状态 | 悬空母线（基网中有组件、移除后无任何组件）；不再被引用的载体；只剩一端的支路 | 悬空母线移除并计数（17 个网络均为 0）；新出现的无引用载体移除并计数（基网中已有的 11 个无引用载体不动）；只剩一端的支路由 R2 移除，构建后不变式核对不存在指向缺失母线的端口。**新出现的死端成员组件保留**（母线无单端组件且只连一条支路，基网中不是死端；成员国存量仍是成员国资产）并列出其固定成本常数：17 个网络中均只有燃料舱计量链路移除后的节点油母线，固定成本 0 EUR |
| **R6 元数据** | 只删本次移除的组件 | `existing_unit_components`、`existing_cross_border_fom_ledger`、`existing_resource_groups`、`battery_inverter_pairs`、`store_power_rules`、`external_annual_caps`、`demand_owners`、`demand_identity`、`research_new_hydro_inflow_tie`、`physical_carbon_map`、`existing_carbon_components`、`research_dedicated_lines`；按国家键的 `research_co2_storage`、`research_carbon.country_cap_tco2`、`research_extra_asean_storage.countries`、`research_nuclear_caps` | 引用本次移除组件的条目删去（基网中已悬空的条目不动，例如 `existing_carbon_components` 中 2 个基网缺失组件）；国家键只留成员国；写入 `research_countries` 与 `research_coalition`（成员、规则版本、逐规则计数）。`scenario` 保持 `integrated`、`research_config` 不变 |

**过境（如实说明，INFERENCE 的取舍）：** 端口都在联盟内、但路径经过非成员国的链路按端口规则**保留**——老挝经越南沿海节点的 CO₂ 过境船运（`via_coastal_node`）与经越南出海的区外封存出口（`CO2 transit export extra-ASEAN`，经由点取 `research_lao_vn_store.table` 的同一陆段）。依据：第 132 项 b1 补充 01 对内陆国过境走廊的先例（`test_m08a_a7.py::test_b1_landlocked_transit_kept_and_checked`）。这类链路出现在 LTMS（18 条）与去 VN（42 条），逐条列在回执的 `transit_via_non_member`。**方向：** 移除更多选项只会使 c(S) 升高或不变，所以按端口规则检验核心条件是更严格的一侧；若审阅端改判为随越南一并移出，这两个联盟的核心条件只会更容易成立。

**D8 加回（并列报告，不作判据）：** 被 R2 移除的边界存量设施（交流线、专线、直流）的既有跨境 FOM 不再计入 c(S)，而 x(S) 含成员国按 α 0.5 应承担的一半；M12 补充 01 D8 的加回额 = 0.5 × 边界存量 FOM，逐联盟 0–10.60 M EUR（`tables/W20_XS_PRE.csv`），远小于 0.01 bn。

## 3. 测试（`tests/research/test_v4_coalition.py`，先于任何求解；不调用求解器）

- **结果：25 passed（31 s）**（`logs/tests_v4_coalition.txt`）；另 (d) 现有回退测试 `test_v4_a2_fallback.py` + `test_m08a_a7.py`：**10 passed**。
- **(a) 恒等：** `members = 全部 11 国, include_bunker=True` → 与 W14 包一体化网络逐组件、逐列、逐时间序列、快照与权重、元数据（除新增的 `research_coalition`）相同：**2920×3h 相同、56 时段与 W14 `trunc56/w14_integrated_56.nc` 相同**；LTMS 先构建后截取 = 先截取后构建；全体国家、不含燃料舱只移除燃料舱（R3）且两个 FOM 常数不变。
- **(b) 11 个去一国：** 以基网"母线→国家"映射在测试中独立归属每个组件：被移除国的任何组件、任何跨越边界的支路、国家液体母线、船运 / 过境链路（名称模式）、大气 / 封存 / 区外封存账户、元数据中的国家键、既有跨境 FOM 台账行都不存在；第 133 项 (2)a 列举的 8 类（需求、资源与潜力、存量设施、新建候选、液体母线与船运、CO₂ 船运、管道、线路 / 直流 / 专线）逐类核对为 0。
- **(c) 三个集团：** 国家集合等于集团；保留的存量跨境设施（交流线 `s_nom > 0`，直流 / 专线 / 管道 `p_nom > 0`）与测试中独立推导的清单逐项相同，国家对都在地理预期之内；电网类存量对：GMS {KH|LA, KH|TH, KH|VN, LA|MM, LA|TH, LA|VN}、LTMS {LA|TH, MY|TH, MY|SG}、BIMP {ID|MY}。清单见第 5 节。
- **(d) 默认构建路径不变：** 主构建与求解脚本不导入本模块；现有 A2 式回退测试通过。本分支在 `research/` 之外只新增 `scripts_project/v4_coalition.py` 与 `tests/research/test_v4_coalition.py` 两个文件（W14 包网络本身未重建：输入直接取包内同一 SHA256 的文件）。
- **其他：** 玩具网络 6 项（规则、元数据、悬空母线、死端、过境、燃料舱子集、拒绝路径）；命令行两次构建逐字节相同（确定性）。

## 4. 17 个网络（`tables/W20_COALITION_BUILD.csv`；回执 `results_project/v4w20/nets56/*_COALITION_RECEIPT.json`，SHA256 见 `evidence/STATIC_CHECKS_W20.json`）

| 联盟 | 成员 | 母线 | 线路 | 链路 | 发电机 | Store | 负荷 | R1 母线 / 组件 | R2 边界 | R3 燃料舱 | R5 悬空母线 / 载体 | 保留跨境（其中存量） | 经非成员过境保留 | 新死端（固定成本） | 网络 SHA256 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GMS | KH LA MM TH VN | 1233 | 93 | 3517 | 708 | 284 | 831 | 1679 / 7522 | 410 | 500 | 0 / 3 | 349 (22) | 0 | 1 (0 EUR) | `ad864f04fc7e0773…` |
| LTMS | LA MY SG TH | 564 | 35 | 1543 | 372 | 154 | 311 | 2348 / 10424 | 571 | 500 | 0 / 8 | 127 (20) | 18 | 2 (0 EUR) | `886e52f1234dcd39…` |
| BIMP | BN ID MY PH | 1622 | 51 | 4432 | 1189 | 330 | 1173 | 1290 / 5788 | 435 | 500 | 0 / 10 | 269 (1) | 0 | 3 (0 EUR) | `fb9fe1e5eeb9b694…` |
| nonGMS | BN ID MY PH SG TL | 1679 | 53 | 4634 | 1233 | 359 | 1192 | 1233 / 5517 | 410 | 500 | 0 / 10 | 354 (4) | 0 | 3 (0 EUR) | `f9dd8abdc74f1b4a…` |
| nonLTMS | BN ID KH MM PH TL VN | 2348 | 77 | 6481 | 1569 | 489 | 1712 | 564 / 2454 | 571 | 500 | 0 / 7 | 415 (1) | 0 | 2 (0 EUR) | `b7a0cda2a7b513d2…` |
| nonBIMP | KH LA MM SG TH TL VN | 1290 | 93 | 3696 | 752 | 313 | 850 | 1622 / 7226 | 435 | 500 | 0 / 3 | 409 (22) | 0 | 1 (0 EUR) | `bcabafc34e103160…` |
| minusBN | 去 BN | 2879 | 147 | 8355 | 1915 | 627 | 2009 | 33 / 119 | 142 | 500 | 0 / 1 | 971 (31) | 0 | 4 (0 EUR) | `d53a44e7663085be…` |
| minusID | 去 ID | 1690 | 104 | 5023 | 1084 | 430 | 1084 | 1222 / 5221 | 398 | 500 | 0 / 1 | 715 (28) | 0 | 4 (0 EUR) | `86d04e4cd675b004…` |
| minusKH | 去 KH | 2776 | 129 | 7984 | 1860 | 600 | 1938 | 136 / 603 | 208 | 500 | 0 / 1 | 905 (28) | 0 | 4 (0 EUR) | `62b53a97c300473e…` |
| minusLA | 去 LA | 2737 | 114 | 7970 | 1852 | 602 | 1934 | 175 / 677 | 184 | 500 | 0 / 7 | 929 (14) | 0 | 4 (0 EUR) | `65fd267601ce9afc…` |
| minusMM | 去 MM | 2423 | 117 | 7112 | 1702 | 545 | 1680 | 489 / 2027 | 154 | 500 | 0 / 1 | 959 (27) | 0 | 4 (0 EUR) | `f291424e87744400…` |
| minusMY | 去 MY | 2726 | 129 | 7824 | 1782 | 591 | 1914 | 186 / 816 | 265 | 500 | 0 / 1 | 848 (24) | 0 | 3 (0 EUR) | `7dfa3d2d5a330578…` |
| minusPH | 去 PH | 2731 | 146 | 7913 | 1794 | 594 | 1912 | 181 / 801 | 168 | 500 | 0 / 1 | 945 (31) | 0 | 2 (0 EUR) | `f3b107e358c6ff6b…` |
| minusSG | 去 SG | 2884 | 147 | 8424 | 1920 | 630 | 2011 | 28 / 104 | 78 | 500 | 0 / 1 | 1035 (28) | 0 | 4 (0 EUR) | `b68e7f6c47d9f03a…` |
| minusTH | 去 TH | 2737 | 112 | 7832 | 1838 | 595 | 1922 | 175 / 730 | 298 | 500 | 0 / 1 | 815 (8) | 0 | 3 (0 EUR) | `9e93f5ed4f5a7b7c…` |
| minusTL | 去 TL | 2883 | 147 | 8432 | 1918 | 627 | 2016 | 29 / 107 | 67 | 500 | 0 / 1 | 1046 (31) | 0 | 4 (0 EUR) | `c50309c6345b631b…` |
| minusVN | 去 VN | 2654 | 126 | 7670 | 1745 | 589 | 1810 | 258 / 1131 | 264 | 500 | 0 / 4 | 849 (29) | 42 | 4 (0 EUR) | `12a9ff878955bea3…` |

基网（W14 56 时段）：母线 3,056、线路 148、链路 8,784、发电机 1,941、Store 644、负荷 2,153。"保留跨境"含船运等贸易链路（其 `p_nom` 是贸易容量上界，不算存量）；"存量"只计交流线与直流 / 专线 / 管道。边界移除按载体见 `tables/W20_COALITION_BUILD.csv` 的 `boundary_by_carrier` 列。

**静态检查（第 2.4 条，VERIFIED，`evidence/STATIC_CHECKS_W20.json`，`scripts/w20_static.py`，170 s，不调用求解器）：17 / 17 通过。**
- 零松弛门（V3.1 `zero_slack_check.check_network`：按求解路径建模型 = `create_model` + 全部钩子，前 3 个时段）：全部通过，无强制零余量行；燃料舱钩子已随 R3 移除（`bunker.present = false`）。
- 各成员国净零行 `research_country_co2_limit-<c>` 存在、判定 `removal_ports_present`（大气账户有移除或双向端口），无非成员国的净零行。
- NaN：LP 相关静态属性与全部时间序列中没有基网之外的 NaN 属性（基网自身只有未用端口的 `Link.efficiency3` / `efficiency4` 为 NaN，1,197 / 2,672 个，联盟网络同样只在这两列）。
- 权重均为 8760/56；钩子集合 = 基网减去 `research_bunker_net_zero`。

**LP 等价（VERIFIED，`logs/lpcheck.txt`，`scripts/w20_lpcheck.sh`）：** 用 `s2_solve.py --stop-before-solve`（建模、导出 LP、不调用求解器）分别处理 W14 2920×3h 网络 + `--truncate 56`（冒烟路径）与"全体 + 燃料舱"预截取 56 时段网络 + `--truncate 56`（本步求解路径）：导出的 LP 12 个数组与 `MATH_PROBLEM.json` 逐字节相同（729,105 列、1,604,504 行、3,722,003 非零元），钩子与求解参数相同。

## 5. 三个集团及补集保留的存量跨境设施（测试 (c) 的清单）

见 `evidence/W20_RETAINED_STOCK.md`（17 个联盟全部列出）。三个集团：
- **GMS（22 项）：** KH|LA 交流 `43` 300 MW；KH|TH `47` 250 MW；KH|VN `39` 200 MW；LA|MM `APG17_LA_MM` 30 MW；LA|TH 交流 9 条（`49 52 53 55 56 58 61 62 66`，69.9–203.3 MW）；LA|TH 专线 5 条（1,220 / 866 / 1,388 / 480 / 1,473 MW）；LA|VN 专线 1 条（572 MW）；MM|TH 存量气管 3 条（Yetagun、Yadana 1、Zawtika）。
- **LTMS（20 项）：** LA|TH 交流 9 条 + 专线 5 条；MY|SG 交流 `92` 525 MW；MY|TH 交流 `91` 80 MW、直流 Khlong Ngae–Gurun 300 MW（正反两向）、TTM 气管（正反两向）。
- **BIMP（1 项）：** ID|MY 交流 `23` 230 MW（BN|MY 与 MY|PH 的连接在基网中为零容量候选，保留为新建候选）。
